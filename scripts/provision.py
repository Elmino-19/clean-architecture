"""Provision everything the app needs to boot, in dependency order.

    postgres role + database  ->  alembic migrations  ->  admin user
    redis connectivity check

Every step is idempotent: re-running skips whatever already exists, so this is
safe to call on each clone and after every `make migrate`.

Why the sudo dance: on a Linux box, `pg_hba.conf` usually grants the
`postgres` superuser `peer` authentication, and refuses password logins over
TCP for it. Creating a role therefore has to go through `sudo -u postgres
psql`. When the role and database are missing and sudo is unavailable, this
script prints the exact commands to paste into a root shell instead of failing
with an opaque authentication error.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(
    os.environ.get("FASTDDD_PROJECT_ROOT", Path(__file__).resolve().parent.parent)
).resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run(
    args: list[str],
    *,
    env: dict[str, str] | None = None,
    timeout: int = 30,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args, capture_output=True, text=True, env=env, timeout=timeout, check=False
    )


def step(title: str) -> None:
    print(f"\n=== {title} ===")


def ok(message: str) -> None:
    print(f"  [ok]   {message}")


def skip(message: str) -> None:
    print(f"  [skip] {message}")


def fail(message: str) -> None:
    print(f"  [FAIL] {message}")


def warn(message: str) -> None:
    print(f"  [warn] {message}")


def sql_literal(value: str) -> str:
    return value.replace("'", "''")


def query_as_app_user(settings, sql: str) -> subprocess.CompletedProcess[str]:
    """Run a read-only query using the credentials from .env."""
    return run(
        ["psql", "-d", "postgres", "-tAc", sql],
        env={
            "PGPASSWORD": settings.POSTGRESQL_PASSWORD,
            "PGHOST": settings.POSTGRESQL_HOST,
            "PGPORT": str(settings.POSTGRESQL_PORT),
            "PGUSER": settings.POSTGRESQL_USERNAME,
        },
    )


def sudo_blocked(result: subprocess.CompletedProcess[str]) -> bool:
    stderr = (result.stderr or "").lower()
    return "password is required" in stderr or "a terminal is required" in stderr


def run_as_postgres(sql: str, *, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    """Run one SQL statement as the postgres superuser.

    `sudo -n` is tried first so non-interactive callers fail fast instead of
    hanging. When that is refused because a password is needed, sudo is retried
    *with* the terminal attached so it can prompt on an interactive run.
    """
    args = [
        "-u",
        "postgres",
        "psql",
        "-v",
        "ON_ERROR_STOP=1",
        "-d",
        "postgres",
        "-c",
        sql,
    ]

    non_interactive = run(["sudo", "-n", *args], timeout=timeout)
    if not sudo_blocked(non_interactive):
        return non_interactive

    if not sys.stdin.isatty():
        return non_interactive

    print("  sudo needs your password to create the Postgres role and database.")
    return run(["sudo", *args], timeout=timeout)


# --------------------------------------------------------------------------
# Postgres
# --------------------------------------------------------------------------
def role_exists(settings) -> bool:
    result = query_as_app_user(
        settings,
        f"SELECT 1 FROM pg_roles WHERE rolname='{settings.POSTGRESQL_USERNAME}'",
    )
    return result.returncode == 0 and result.stdout.strip() == "1"


def database_exists(settings) -> bool:
    result = query_as_app_user(
        settings,
        f"SELECT 1 FROM pg_database WHERE datname='{settings.POSTGRESQL_DATABASE}'",
    )
    return result.returncode == 0 and result.stdout.strip() == "1"


def create_role_and_database(settings) -> tuple[bool, str]:
    """Create the role then the database via the postgres superuser.

    Returns (ok, error_detail). When sudo is unavailable the error detail
    contains ready-to-paste commands.
    """
    user = settings.POSTGRESQL_USERNAME
    database = settings.POSTGRESQL_DATABASE
    password = sql_literal(settings.POSTGRESQL_PASSWORD)

    statements = [
        f"CREATE ROLE \"{user}\" WITH LOGIN PASSWORD '{password}' CREATEDB;",
        f'CREATE DATABASE "{database}" OWNER "{user}";',
    ]

    for index, sql in enumerate(statements):
        verb = "role" if index == 0 else "database"
        result = run_as_postgres(sql)
        if result.returncode == 0:
            ok(f"{verb} created")
            continue

        stderr = result.stderr or ""
        if "already exists" in stderr:
            skip(f"{verb} already exists")
            continue
        if sudo_blocked(result):
            # Single-quote the whole -c argument so the inner double quotes
            # survive the shell.
            commands = "\n".join(
                "    sudo -u postgres psql -c '" + s.replace("'", "'\\''") + "'"
                for s in statements[index:]
            )
            return False, (
                f"sudo needs a password. Run these manually, then re-run:\n{commands}"
            )
        return False, stderr.strip()

    return True, ""


def provision_postgres(settings) -> bool:
    has_role = role_exists(settings)
    has_database = database_exists(settings)

    if has_role and has_database:
        skip(
            f"role '{settings.POSTGRESQL_USERNAME}' and database "
            f"'{settings.POSTGRESQL_DATABASE}' already exist"
        )
        return True

    if has_role:
        skip(f"role '{settings.POSTGRESQL_USERNAME}' already exists")
    if has_database:
        skip(f"database '{settings.POSTGRESQL_DATABASE}' already exists")

    created, detail = create_role_and_database(settings)
    if not created:
        fail(detail)
        return False
    return True


# --------------------------------------------------------------------------
# Redis
# --------------------------------------------------------------------------
def check_redis(settings) -> None:
    try:
        import redis
    except ImportError:
        skip("redis package not installed — skipping (run: uv sync)")
        return

    client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        username=settings.REDIS_USERNAME,
        password=settings.REDIS_PASSWORD,
        db=settings.REDIS_DB,
        socket_connect_timeout=5,
    )
    try:
        client.ping()
    except Exception as e:
        warn(f"redis not reachable at {settings.REDIS_HOST}:{settings.REDIS_PORT}: {e}")
        warn("start the stack with: make dependencies-up-silent")
        return
    ok(f"redis reachable at {settings.REDIS_HOST}:{settings.REDIS_PORT}")


# --------------------------------------------------------------------------
# Migrations
# --------------------------------------------------------------------------
def run_migrations() -> bool:
    result = run(["uv", "run", "alembic", "upgrade", "head"], timeout=300)
    if result.returncode == 0:
        ok("schema is at head")
        return True
    fail(f"alembic upgrade head failed:\n{(result.stderr or result.stdout).strip()}")
    return False


# --------------------------------------------------------------------------
# Admin user
# --------------------------------------------------------------------------
def seed_admin(settings, *, name: str) -> bool:
    from sqlalchemy import select

    from app.core.database import PGSession
    from app.core.security import hash_password
    from app.modules.shared.domain.enums import Role
    from app.modules.user.infrastructure.models import UserModel

    email = settings.SECURITY_ADMIN_EMAIL
    first, _, last = name.partition(" ")
    first = first or "Admin"
    last = last or "User"

    with PGSession() as session:
        existing = session.scalar(select(UserModel).where(UserModel.email == email))
        if existing is not None:
            skip(f"admin '{email}' already exists (id={existing.id})")
            return True

        session.add(
            UserModel(
                first_name=first[:100],
                last_name=last[:100],
                preferred_name=first[:100],
                gender="other",
                birthdate=date(1990, 1, 1),
                email=email,
                phone=None,
                hashed_password=hash_password(settings.SECURITY_ADMIN_PASSWORD),
                role=Role.ADMIN,
            )
        )
        session.commit()
        new_id = session.scalar(select(UserModel.id).where(UserModel.email == email))

    ok(f"admin '{email}' created (id={new_id}, role=ADMIN)")
    return True


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------
def provision(
    *,
    admin_name: str = "Admin User",
    skip_redis: bool = False,
    skip_migrations: bool = False,
    skip_admin: bool = False,
) -> int:
    """Run every provisioning step. Returns the number of failed steps.

    Importable so `scripts/install.py` can drive it after writing .env.
    """
    # Importing Settings validates .env and raises before any step runs.
    from app.core.settings import settings

    failures = 0

    step("Postgres")
    if not provision_postgres(settings):
        failures += 1

    if not skip_redis:
        step("Redis")
        check_redis(settings)

    if not skip_migrations:
        step("Migrations")
        if not run_migrations():
            failures += 1

    if not skip_admin:
        step("Admin user")
        try:
            if not seed_admin(settings, name=admin_name):
                failures += 1
        except Exception as e:
            fail(f"admin seeding failed: {e}")
            failures += 1

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Provision Postgres, Redis, migrations and the admin user."
    )
    parser.add_argument("--skip-redis", action="store_true")
    parser.add_argument("--skip-migrations", action="store_true")
    parser.add_argument("--skip-admin", action="store_true")
    parser.add_argument(
        "--admin-name", default="Admin User", help="name for the admin user"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report status only; never create anything",
    )
    args = parser.parse_args()

    # Importing Settings validates .env and raises before any step runs.
    from app.core.settings import settings

    if args.check:
        step("Status")
        has_role = role_exists(settings)
        has_database = database_exists(settings)
        ok(
            f"role      : {'exists' if has_role else 'MISSING'} ({settings.POSTGRESQL_USERNAME})"
        )
        ok(
            f"database  : {'exists' if has_database else 'MISSING'} ({settings.POSTGRESQL_DATABASE})"
        )
        return 0 if has_role and has_database else 1

    failures = provision(
        admin_name=args.admin_name,
        skip_redis=args.skip_redis,
        skip_migrations=args.skip_migrations,
        skip_admin=args.skip_admin,
    )

    print()
    if failures:
        print(f"{failures} step(s) failed.")
        return 1
    print("Provisioning complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

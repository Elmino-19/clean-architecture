"""Report whether this checkout is ready to run.

Read-only: checks .env completeness, service reachability, JWT key files, and
whether the admin user exists. Never creates or changes anything, so it is safe
to run at any time. Exit code is 0 when every check passes.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(
    os.environ.get("FASTDDD_PROJECT_ROOT", Path(__file__).resolve().parent.parent)
).resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

ENV_FILE = PROJECT_ROOT / ".env"

failures: list[str] = []


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def passed(message: str) -> None:
    print(f"  [ok]   {message}")


def failed(message: str) -> None:
    print(f"  [FAIL] {message}")
    failures.append(message)


def warned(message: str) -> None:
    print(f"  [warn] {message}")


def check_env() -> bool:
    section("Environment")
    result = subprocess_run([sys.executable, "scripts/setup_env.py", "--check"])
    for line in result.stdout.splitlines():
        print(f"  {line}")
    return result.returncode == 0


def subprocess_run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args, capture_output=True, text=True, cwd=PROJECT_ROOT, check=False
    )


def tcp_open(host: str, port: int, timeout: float = 2.0) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(timeout)
        return probe.connect_ex((host, port)) == 0


def check_services(settings) -> None:
    section("Services")
    for label, host, port, hint in (
        (
            "postgres",
            settings.POSTGRESQL_HOST,
            int(settings.POSTGRESQL_PORT),
            "make dependencies-up-silent",
        ),
        (
            "redis",
            settings.REDIS_HOST,
            int(settings.REDIS_PORT),
            "make dependencies-up-silent",
        ),
    ):
        if tcp_open(host, port):
            passed(f"{label:9} reachable at {host}:{port}")
        else:
            failed(f"{label:9} NOT reachable at {host}:{port}  ->  {hint}")


def check_jwt_keys(settings) -> None:
    section("JWT keys")
    for label, key in (
        ("signing private", settings.JWT_SIGNING_PRIVATE_KEY_PATH),
        ("signing public", settings.JWT_SIGNING_PUBLIC_KEY_PATH),
        ("encryption private", settings.JWT_ENCRYPTION_PRIVATE_KEY_PATH),
        ("encryption public", settings.JWT_ENCRYPTION_PUBLIC_KEY_PATH),
    ):
        path = Path(key)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        if path.exists():
            passed(f"{label:20} {path.name}")
        else:
            warned(f"{label:20} missing — generated automatically on first boot")


def check_database(settings) -> None:
    section("Database")
    result = subprocess_run([sys.executable, "scripts/provision.py", "--check"])
    for line in result.stdout.splitlines():
        print(f"  {line}")
    if result.returncode != 0:
        failed("role/database missing  ->  make provision")


def check_admin(settings) -> None:
    section("Admin user")
    try:
        from sqlalchemy import select

        from app.core.database import PGSession
        from app.modules.user.infrastructure.models import UserModel

        with PGSession() as session:
            admin = session.scalar(
                select(UserModel).where(
                    UserModel.email == settings.SECURITY_ADMIN_EMAIL
                )
            )
        if admin is None:
            failed(
                f"admin '{settings.SECURITY_ADMIN_EMAIL}' not seeded  ->  make provision"
            )
        else:
            passed(
                f"admin '{settings.SECURITY_ADMIN_EMAIL}' (id={admin.id}, role={admin.role.value})"
            )
    except Exception as e:
        failed(f"could not query users: {e}")


def main() -> int:
    if not ENV_FILE.exists():
        print("[FAIL] .env not found. Run: make setup")
        return 1

    check_env()

    from app.core.settings import settings  # raises if .env is invalid

    check_services(settings)
    check_jwt_keys(settings)
    check_database(settings)
    check_admin(settings)

    print()
    if failures:
        print(f"{len(failures)} check(s) failed.")
        return 1
    print("Everything looks ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

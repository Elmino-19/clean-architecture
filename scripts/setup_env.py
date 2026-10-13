"""Fill .env from .env.example so a fresh clone boots without hand-editing 64 keys.

Three tiers of values, in order of precedence:

1. Generated  — secrets nobody should type: HMAC fingerprints, key passwords,
   the seeded admin password.
2. Derived   — computed from the project slug: table prefix, cache namespace,
   database name, cookie names. One slug drives all of them.
3. Preserved — anything already set in .env is left untouched, so re-running is
   safe and never rotates a live database password.

Two entry points share this module:

* the CLI (`python scripts/setup_env.py`) for standalone use, and
* `apply(EnvConfig(...))`, called by `scripts/install.py` after it has collected
  answers from the user.
"""

from __future__ import annotations

import argparse
import ast
import getpass
import os
import re
import secrets
import string
import sys
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(
    os.environ.get("FASTDDD_PROJECT_ROOT", Path(__file__).resolve().parent.parent)
).resolve()
ENV_FILE = PROJECT_ROOT / ".env"
ENV_EXAMPLE = PROJECT_ROOT / ".env.example"

DEFAULT_SLUG = "my-project"


@dataclass
class EnvConfig:
    """Everything needed to produce a complete .env.

    Blank optional fields fall back to a value derived from the slug, so a
    caller only has to supply what the user actually answered.
    """

    project: str
    environment: str = "development"
    host: str = "localhost"
    cookie_samesite: str = "lax"
    title: str = ""
    contact_phone: str = ""

    admin_name: str = "Admin User"
    admin_email: str = "admin@example.com"
    admin_password: str = ""

    db_name: str = ""
    db_user: str = ""
    db_password: str = ""
    db_host: str = ""
    db_port: int | None = None

    redis_host: str = ""
    redis_port: int | None = None
    redis_password: str = ""

    force: bool = False


@dataclass
class AppliedEnv:
    changed: list[str] = field(default_factory=list)
    slug: str = ""
    admin_email: str = ""
    admin_password: str = ""
    db_name: str = ""
    db_user: str = ""
    db_host: str = ""
    db_port: int = 0
    environment: str = "development"


class EnvFile:
    """Read/write .env while preserving comments, blank lines and ordering."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.lines: list[str] = []
        self.index: dict[str, int] = {}

    def load(self) -> None:
        if not self.path.exists():
            raise FileNotFoundError(f"{self.path} not found.")
        self.lines = self.path.read_text(encoding="utf-8").splitlines()
        self.index = {}
        for number, line in enumerate(self.lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key = stripped.split("=", 1)[0].strip()
            self.index[key] = number

    def get(self, key: str) -> str:
        if key not in self.index:
            return ""
        _, _, value = self.lines[self.index[key]].partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        return value

    def set(self, key: str, value: str) -> bool:
        """Return True when the stored value actually changed."""
        rendered = f"{key}={quote(value)}"
        if key in self.index:
            if self.lines[self.index[key]] == rendered:
                return False
            self.lines[self.index[key]] = rendered
            return True
        self.lines.append(rendered)
        self.index[key] = len(self.lines) - 1
        return True

    def save(self) -> None:
        self.path.write_text("\n".join(self.lines) + "\n", encoding="utf-8")


def quote(value: str) -> str:
    """Wrap in double quotes unless the value is a JSON list.

    python-dotenv leaves `KEY=["a","b"]` unquoted so pydantic-settings parses it
    as a real list; quoting it yields a single string that fails list[str].
    """
    if value.startswith("["):
        return value
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def normalize_slug(raw: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", raw.strip().lower()).strip("_")
    return slug or DEFAULT_SLUG


def random_password(length: int = 24) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#%^&*-_=+"
    while True:
        candidate = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(c.islower() for c in candidate)
            and any(c.isupper() for c in candidate)
            and any(c.isdigit() for c in candidate)
        ):
            return candidate


def prompt(label: str, default: str, *, secret: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        raw = (getpass.getpass if secret else input)(f"{label}{suffix}: ")
        value = raw.strip() or default
        if value:
            return value
        print("  a value is required")


def unique_port(preferred: int, taken: set[int]) -> int:
    port = preferred
    while port in taken or not (1024 <= port <= 65535):
        port += 1
    return port


def port_is_free(port: int) -> bool:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("", port))
        except OSError:
            return False
    return True


def pick_port(env: EnvFile, key: str, preferred: int, taken: set[int]) -> int:
    current = env.get(key)
    if current.isdigit():
        chosen = int(current)
        if chosen not in taken:
            return chosen
    port = unique_port(preferred, taken)
    while not port_is_free(port):
        print(f"  port {port} is busy, trying the next one...")
        port += 1
    return port


FINGERPRINT_KEYS = {
    "API_KEY_HASH_FINGERPRINT",
    "JWT_HASH_FINGERPRINT",
}


def apply(config: EnvConfig) -> AppliedEnv:
    """Write a complete .env and return what was decided.

    This is the single code path used by both the CLI and the installer.
    """
    if not ENV_EXAMPLE.exists():
        raise FileNotFoundError(f"{ENV_EXAMPLE} not found.")

    if not ENV_FILE.exists():
        ENV_FILE.write_text(ENV_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")

    env = EnvFile(ENV_FILE)
    env.load()

    slug = normalize_slug(config.project)
    changed: list[str] = []

    def set_key(key: str, value: str) -> None:
        if env.set(key, value):
            changed.append(key)

    # PORTS -----------------------------------------------------------------
    # Our own listeners (dev server, admin UIs) may shift to a free port; the
    # database and cache ports must NOT, because if something is already on
    # 5432/6379 it is almost certainly the Postgres/Redis we want to talk to.
    taken: set[int] = set()

    def resolve_port(key: str, preferred: int, override: int | None) -> int:
        if override:
            taken.add(override)
            set_key(key, str(override))
            return override
        chosen = pick_port(env, key, preferred, taken)
        taken.add(chosen)
        set_key(key, str(chosen))
        return chosen

    def standard_port(key: str, default: int, override: int | None) -> int:
        if override:
            set_key(key, str(override))
            return override
        existing = env.get(key)
        if existing.isdigit():
            return int(existing)
        set_key(key, str(default))
        return default

    app_port = resolve_port("APPLICATION_PORT", 8000, None)
    db_port = standard_port("POSTGRESQL_PORT", 5432, config.db_port)
    standard_port("REDIS_PORT", 6379, config.redis_port)
    resolve_port("PGADMIN_PORT", 8080, None)
    resolve_port("REDISINSIGHT_PORT", 8081, None)

    host = config.host
    db_host = config.db_host or host
    redis_host = config.redis_host or host
    application_url = f"http://{host}:{app_port}"

    # IDENTITY --------------------------------------------------------------
    db_name = config.db_name or slug
    db_user = config.db_user or slug.split("_")[0] or "app"

    admin_email = config.admin_email or "admin@example.com"

    def resolve_secret(explicit: str, key: str, length: int) -> str:
        """Explicit value wins; otherwise keep what is set unless --force."""
        if explicit:
            return explicit
        existing = env.get(key)
        if existing and not config.force:
            return existing
        return random_password(length)

    admin_password = resolve_secret(
        config.admin_password, "SECURITY_ADMIN_PASSWORD", 16
    )
    db_password = resolve_secret(config.db_password, "POSTGRESQL_PASSWORD", 20)
    redis_password = resolve_secret(config.redis_password, "REDIS_PASSWORD", 20)

    values = {
        # PROJECT IDENTITY
        "APPLICATION_TITLE": config.title or slug.replace("_", " ").title(),
        "APPLICATION_ENVIRONMENT": config.environment,
        "APPLICATION_URL": application_url,
        "APPLICATION_TABLE_PREFIX": slug,
        "LOGS_NAME": slug,
        # API KEY
        "API_KEY_PREFIX": slug.split("_")[0][:8] or "app",
        "API_KEY_HASH_FINGERPRINT": secrets.token_hex(32),
        # COOKIES
        "COOKIES_TOKEN_TYPE_KEY": "token_type",
        "COOKIES_ACCESS_TOKEN_KEY": "access_token",
        "COOKIES_ACCESS_TOKEN_PATH": "/api/v1/",
        "COOKIES_REFRESH_TOKEN_KEY": "refresh_token",
        "COOKIES_REFRESH_TOKEN_PATH": "/api/v1/authentication/refresh/",
        "COOKIES_DEVICE_KEY": "device_id",
        "COOKIES_SAME_SITE": config.cookie_samesite,
        "COOKIES_DOMAIN": host,
        "COOKIES_MAX_AGE_SECONDS": str(
            int(env.get("JWT_REFRESH_TOKEN_EXPIRE_DAYS") or 90) * 86400
        ),
        # JWT
        "JWT_ISSUER": application_url,
        "JWT_AUDIENCE": f"api://{slug}",
        "JWT_HASH_FINGERPRINT": secrets.token_hex(32),
        "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "JWT_REFRESH_TOKEN_EXPIRE_DAYS": "90",
        "JWT_AUTO_GENERATE_KEYS": "true",
        "JWT_KEYS_DIR": "secrets/keys",
        "JWT_SIGNING_PRIVATE_KEY_PATH": "secrets/keys/signing-private.pem",
        "JWT_SIGNING_PUBLIC_KEY_PATH": "secrets/keys/signing-public.pem",
        "JWT_ENCRYPTION_PRIVATE_KEY_PATH": "secrets/keys/encryption-private.pem",
        "JWT_ENCRYPTION_PUBLIC_KEY_PATH": "secrets/keys/encryption-public.pem",
        # POSTGRESQL
        "POSTGRESQL_DATABASE": db_name,
        "POSTGRESQL_USERNAME": db_user,
        "POSTGRESQL_PASSWORD": db_password,
        "POSTGRESQL_HOST": db_host,
        # REDIS
        "REDIS_HOST": redis_host,
        "REDIS_PASSWORD": redis_password,
        "REDIS_USERNAME": "default",
        "REDIS_DB": "0",
        "REDIS_SSL": "false",
        "REDIS_CONNECTION_TIMEOUT_SECONDS": "10",
        "REDIS_SOCKET_TIMEOUT_SECONDS": "5",
        "REDIS_DEFAULT_TTL_SECONDS": "3600",
        "REDIS_SESSION_TTL_SECONDS": "1800",
        "REDIS_TOMBSTONE_TTL_SECONDS": "30",
        "REDIS_MAX_CONNECTIONS": "50",
        "REDIS_KEY_PREFIX": slug,
        "REDIS_CACHE_VERSION": "1",
        "REDIS_FLUSH_ON_STARTUP": "true",
        "REDIS_DATABASES": "16",
        "REDIS_MAX_MEMORY": "256mb",
        "REDIS_MAX_MEMORY_POLICY": "allkeys-lru",
        # REDISINSIGHT
        "REDISINSIGHT_REDIS_ALIAS": f"{slug} cache",
        # PGADMIN
        "PGADMIN_EMAIL": admin_email,
        # CONTACT
        "APPLICATION_CONTACT_PHONE": config.contact_phone or "+000 000 0000",
        # SECURITY
        "SECURITY_ADMIN_EMAIL": admin_email,
        "SECURITY_ADMIN_PASSWORD": admin_password,
        "SECURITY_ALLOW_ORIGINS": '["http://localhost:3000"]',
        "SECURITY_ALLOW_HEADERS": (
            '["Accept","Authorization","Content-Type","X-Request-ID","X-API-Key"]'
        ),
        "SECURITY_ALLOW_METHODS": '["GET","POST","PATCH","PUT","DELETE","OPTIONS"]',
        "SECURITY_EMAIL_ALLOWED_DOMAINS": "[]",
    }

    for key, value in values.items():
        if key in FINGERPRINT_KEYS and env.get(key) and not config.force:
            # Keep existing fingerprints unless a rotation was forced.
            continue
        set_key(key, value)

    # Password-protect the PEM keys before the app generates them.
    for key in ("JWT_SIGNING_KEY_PASSWORD", "JWT_ENCRYPTION_KEY_PASSWORD"):
        if (not env.get(key) or config.force) and env.set(key, random_password(24)):
            changed.append(key)

    if config.environment == "production":
        env.set("NGROK_AUTH_TOKEN", "")

    env.save()

    return AppliedEnv(
        changed=changed,
        slug=slug,
        admin_email=admin_email,
        admin_password=admin_password,
        db_name=db_name,
        db_user=db_user,
        db_host=db_host,
        db_port=db_port,
        environment=config.environment,
    )


def required_keys() -> set[str]:
    """Derive the required set from Settings so this can never drift.

    Falls back to a static list when the app's dependencies are not installed,
    because --check must work before `uv sync`.
    """
    source = (PROJECT_ROOT / "app" / "core" / "settings.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "Settings":
            required = {
                statement.target.id
                for statement in node.body
                if isinstance(statement, ast.AnnAssign)
                and isinstance(statement.target, ast.Name)
                and statement.value is None
            }
            if required:
                return required

    return set(STATIC_REQUIRED_KEYS)


STATIC_REQUIRED_KEYS = {
    "APPLICATION_ENVIRONMENT",
    "APPLICATION_PORT",
    "APPLICATION_URL",
    "APPLICATION_TABLE_PREFIX",
    "API_KEY_PREFIX",
    "API_KEY_HASH_FINGERPRINT",
    "JWT_ISSUER",
    "JWT_AUDIENCE",
    "JWT_HASH_FINGERPRINT",
    "JWT_SIGNING_KEY_PASSWORD",
    "JWT_ENCRYPTION_KEY_PASSWORD",
    "JWT_KEYS_DIR",
    "JWT_SIGNING_PRIVATE_KEY_PATH",
    "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
    "JWT_REFRESH_TOKEN_EXPIRE_DAYS",
    "COOKIES_ACCESS_TOKEN_KEY",
    "COOKIES_REFRESH_TOKEN_KEY",
    "COOKIES_SAME_SITE",
    "POSTGRESQL_DATABASE",
    "POSTGRESQL_USERNAME",
    "POSTGRESQL_PASSWORD",
    "POSTGRESQL_HOST",
    "POSTGRESQL_PORT",
    "REDIS_HOST",
    "REDIS_PORT",
    "REDIS_PASSWORD",
    "REDIS_DB",
    "REDIS_KEY_PREFIX",
    "REDIS_CACHE_VERSION",
    "SECURITY_ALLOW_ORIGINS",
    "SECURITY_ADMIN_EMAIL",
    "SECURITY_ADMIN_PASSWORD",
}


def check_env() -> int:
    """Validate .env the way Settings does, without booting the app."""
    if not ENV_FILE.exists():
        print("Error: .env not found. Run: make setup", file=sys.stderr)
        return 1

    env = EnvFile(ENV_FILE)
    env.load()

    required = required_keys()
    empty = sorted(k for k in required if not env.get(k))

    if empty:
        print(f"{len(empty)} required key(s) still empty in .env:")
        for key in empty:
            print(f"  - {key}")
        print("\nRun: make setup")
        return 1

    problems: list[str] = []

    environment = env.get("APPLICATION_ENVIRONMENT")
    if environment not in {"development", "homolog", "production"}:
        problems.append(
            f"APPLICATION_ENVIRONMENT={environment!r} is invalid; "
            "expected development | homolog | production"
        )

    samesite = env.get("COOKIES_SAME_SITE").lower()
    if samesite not in {"lax", "strict", "none"}:
        problems.append(
            f"COOKIES_SAME_SITE={samesite!r} is invalid; expected lax | strict | none"
        )

    for key in (
        "APPLICATION_PORT",
        "POSTGRESQL_PORT",
        "REDIS_PORT",
        "PGADMIN_PORT",
        "REDISINSIGHT_PORT",
    ):
        value = env.get(key)
        if value and not value.isdigit():
            problems.append(f"{key}={value!r} is not a number")
        elif value and not 1 <= int(value) <= 65535:
            problems.append(f"{key}={value} is outside 1-65535")

    if not env.get("POSTGRESQL_HOST"):
        problems.append("POSTGRESQL_HOST is empty")

    if problems:
        print(f"{len(problems)} problem(s) found:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(f".env looks complete: {len(env.index)} keys.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Auto-fill .env from .env.example so the app boots unattended."
    )
    parser.add_argument("--project", help="Project slug (default: prompt)")
    parser.add_argument("--title", help="APPLICATION_TITLE override")
    parser.add_argument("--host", default="localhost", help="Host used for URLs")
    parser.add_argument(
        "--environment",
        choices=["development", "homolog", "production"],
        default="development",
    )
    parser.add_argument(
        "--cookie-samesite", choices=["lax", "strict", "none"], default="lax"
    )
    parser.add_argument("--admin-email", help="Skip the admin email prompt")
    parser.add_argument("--admin-password", help="Skip the admin password prompt")
    parser.add_argument("--contact-phone", help="OpenAPI contact phone")
    parser.add_argument("--db-name", help="Database name")
    parser.add_argument("--db-user", help="Database user")
    parser.add_argument("--db-password", help="Database password")
    parser.add_argument("--db-host", help="Database host")
    parser.add_argument("--db-port", type=int, help="Database port")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Never prompt; derive everything and use defaults for credentials.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rotate generated secrets even when they are already set.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report empty/invalid keys and exit 1 if any required key is missing.",
    )
    args = parser.parse_args()

    if args.check:
        return check_env()

    if args.yes:
        project = args.project or DEFAULT_SLUG
    else:
        project = args.project or prompt("Project slug", DEFAULT_SLUG)

    admin_email = args.admin_email
    admin_password = args.admin_password
    if not args.yes:
        admin_email = admin_email or prompt("Admin email", "admin@example.com")
        admin_password = admin_password or prompt(
            "Admin password (empty = generate)", "", secret=True
        )

    config = EnvConfig(
        project=project,
        environment=args.environment,
        host=args.host,
        cookie_samesite=args.cookie_samesite,
        title=args.title or "",
        contact_phone=args.contact_phone or "",
        admin_email=admin_email or "",
        admin_password=admin_password or "",
        db_name=args.db_name or "",
        db_user=args.db_user or "",
        db_password=args.db_password or "",
        db_host=args.db_host or "",
        db_port=args.db_port,
        force=args.force,
    )

    result = apply(config)

    print(f"\nWrote {ENV_FILE} ({len(result.changed)} keys updated).")
    print(
        f"  database : {result.db_name} (user {result.db_user} @ {result.db_host}:{result.db_port})"
    )
    print(f"  admin    : {result.admin_email} / {result.admin_password}")
    print("\nNext: make provision")
    return 0


if __name__ == "__main__":
    sys.exit(main())

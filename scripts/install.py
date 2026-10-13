"""One command to go from a fresh clone to a ready coding environment.

    uv run setup-project          # or: make install

It asks a handful of questions (project name, database credentials, admin
account) and then, without further input:

    1. configures opencode  (skills, commands, opencode.jsonc)
    2. writes a complete .env
    3. generates the JWT token key pairs
    4. creates the Postgres role + database, runs migrations, seeds the admin
    5. reports what is ready

Every step is idempotent, so running it again only fills what is missing. Pass
`--yes` to accept every default and never prompt (useful for scripts and CI).
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(
    os.environ.get("FASTDDD_PROJECT_ROOT", Path(__file__).resolve().parent.parent)
).resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import opencode_setup  # noqa: E402
import provision as provisioner  # noqa: E402
import setup_env  # noqa: E402
from setup_env import EnvConfig  # noqa: E402

TOTAL_STEPS = 5


def banner() -> None:
    print()
    print("=" * 62)
    print("  Project installer")
    print("=" * 62)
    print("  A few questions, then everything is set up for you.")
    print()


def ask(
    label: str,
    default: str = "",
    *,
    secret: bool = False,
    auto_hint: bool = False,
) -> str:
    """Prompt with a default. Empty input accepts the default (or generates)."""
    if default:
        suffix = f" [{default}]"
    elif auto_hint:
        suffix = " [auto-generate]"
    else:
        suffix = ""

    reader = getpass.getpass if secret else input
    while True:
        raw = reader(f"  {label}{suffix}: ").strip()
        if raw:
            return raw
        if default:
            return default
        if auto_hint:
            return ""  # caller generates
        print("    a value is required")


def collect_answers(args: argparse.Namespace) -> tuple[EnvConfig, bool] | None:
    """Run the wizard. Returns None when the user aborts."""
    if args.project:
        project = args.project
    elif args.yes:
        project = setup_env.DEFAULT_SLUG
    else:
        project = ask("Project name", setup_env.DEFAULT_SLUG)

    slug = setup_env.normalize_slug(project)
    print(f"\n  (slug: {slug})\n")

    if args.yes:
        db_name = args.db_name or slug
        db_user = args.db_user or slug.split("_")[0]
        db_password = args.db_password or ""
        db_host = args.db_host or "localhost"
        db_port = args.db_port
        admin_name = args.admin_name or "Admin User"
        admin_email = args.admin_email or "admin@example.com"
        admin_password = args.admin_password or ""
        global_assets = args.global_assets
    else:
        db_name = args.db_name or ask("Database name", slug)
        db_user = args.db_user or ask("Database user", slug.split("_")[0])
        db_password = args.db_password or ask(
            "Database password", secret=True, auto_hint=True
        )
        host_default = args.db_host or "localhost"
        db_host = ask("Database host", host_default)
        db_port = args.db_port
        admin_name = args.admin_name or ask("Admin name", "Admin User")
        admin_email = args.admin_email or ask("Admin email", "admin@example.com")
        admin_password = args.admin_password or ask(
            "Admin password", secret=True, auto_hint=True
        )
        global_assets = args.global_assets or ask_yes_no(
            "Install opencode skills globally too", default="n"
        )

    return EnvConfig(
        project=project,
        environment=args.environment,
        host=db_host,
        admin_name=admin_name,
        admin_email=admin_email,
        admin_password=admin_password,
        db_name=db_name,
        db_user=db_user,
        db_password=db_password,
        db_host=db_host,
        db_port=db_port,
        force=args.force,
    ), global_assets


def ask_yes_no(label: str, default: str = "n") -> bool:
    hint = " [y/N]" if default.lower() == "n" else " [Y/n]"
    raw = input(f"  {label}{hint}: ").strip().lower()
    if not raw:
        raw = default
    return raw in {"y", "yes"}


def step_header(number: int, title: str) -> None:
    print(f"\n[{number}/{TOTAL_STEPS}] {title}")


def ensure_tokens() -> bool:
    """Generate the JWT signing/encryption key pairs if they are missing."""
    from app.core.settings import settings

    settings.generate_authentication_keys()

    keys = [
        settings.JWT_SIGNING_PRIVATE_KEY_PATH,
        settings.JWT_SIGNING_PUBLIC_KEY_PATH,
        settings.JWT_ENCRYPTION_PRIVATE_KEY_PATH,
        settings.JWT_ENCRYPTION_PUBLIC_KEY_PATH,
    ]
    present = [k for k in keys if Path(k).exists()]
    print(
        f"  [ok]   {len(present)}/{len(keys)} key file(s) present in {settings.JWT_KEYS_DIR}"
    )
    return len(present) == len(keys)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Set up this project end to end with a few questions."
    )
    parser.add_argument("--project", help="Project name")
    parser.add_argument("--db-name", help="Database name")
    parser.add_argument("--db-user", help="Database user")
    parser.add_argument("--db-password", help="Database password (blank = generate)")
    parser.add_argument("--db-host", help="Database host")
    parser.add_argument("--db-port", type=int, help="Database port")
    parser.add_argument("--admin-name", help="Admin display name")
    parser.add_argument("--admin-email", help="Admin email")
    parser.add_argument("--admin-password", help="Admin password (blank = generate)")
    parser.add_argument(
        "--environment",
        choices=["development", "homolog", "production"],
        default="development",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Accept every default; never prompt.",
    )
    parser.add_argument(
        "--global-assets",
        action="store_true",
        help="Also copy opencode skills/commands to ~/.config/opencode.",
    )
    parser.add_argument("--force", action="store_true", help="Rotate secrets.")
    parser.add_argument("--skip-opencode", action="store_true")
    parser.add_argument(
        "--skip-database",
        action="store_true",
        help="Only write .env and tokens; do not touch Postgres.",
    )
    args = parser.parse_args()

    banner()

    answers = collect_answers(args)
    if answers is None:
        print("Aborted.")
        return 1
    config, global_assets = answers

    print("\n  Summary:")
    print(f"    project   : {config.project}")
    print(f"    database  : {config.db_name} (user {config.db_user})")
    print(f"    admin     : {config.admin_email}")
    print(f"    environment: {config.environment}")

    if not args.yes and not ask_yes_no("Continue", default="y"):
        print("Aborted.")
        return 1

    failures = 0

    if not args.skip_opencode:
        step_header(1, "Configure opencode")
        if opencode_setup.setup(global_install=global_assets) != 0:
            failures += 1
    else:
        step_header(1, "Configure opencode (skipped)")

    step_header(2, "Write .env")
    result = setup_env.apply(config)
    print(f"  [ok]   .env written ({len(result.changed)} keys updated)")

    step_header(3, "Generate tokens")
    try:
        if not ensure_tokens():
            failures += 1
    except Exception as e:
        print(f"  [FAIL] token generation failed: {e}")
        failures += 1

    if not args.skip_database:
        step_header(4, "Create database, migrate, seed admin")
        provision_failures = provisioner.provision(admin_name=config.admin_name)
        if provision_failures:
            failures += 1
    else:
        step_header(4, "Create database (skipped)")

    step_header(5, "Summary")
    print(f"  project    : {config.project}  (prefix: {result.slug})")
    print(f"  database   : {result.db_name} @ {result.db_host}:{result.db_port}")
    print(f"  admin login: {result.admin_email} / {result.admin_password}")
    print("  opencode   : .opencode/ assets + opencode.jsonc")
    print()
    print("  Next steps:")
    print("    make test          # run the test suite")
    print("    make dev           # start the API")
    print("    make doctor        # verify everything is reachable")

    print()
    if failures:
        print(f"Finished with {failures} step(s) needing attention.")
        return 1
    print("All set. Happy coding.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

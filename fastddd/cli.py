"""Command-line entry point for the ``fastddd`` toolkit.

The tool itself carries no business logic: it locates the bundled scripts
(shipped inside the wheel under ``fastddd/data/scripts``) and runs them against
the current project. Commands that import the project's own code (``db``,
``doctor``, ``install``) run through ``uv run`` so the project's dependencies are
used; every other command runs with the tool's own interpreter.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from fastddd import __version__

COMMANDS: dict[str, tuple[str, str, bool]] = {
    "install": (
        "install.py",
        "end-to-end wizard: opencode + .env + tokens + database",
        True,
    ),
    "opencode": ("opencode_setup.py", "install opencode skills/commands/agents", False),
    "setup": ("setup_env.py", "write .env from .env.example", False),
    "db": ("provision.py", "create Postgres role/db, run migrations, seed admin", True),
    "doctor": ("doctor.py", "verify environment, services, keys and admin user", True),
    "rebrand": ("rebrand.py", "rename the project away from the template", False),
    "new-module": (
        "create_module.py",
        "scaffold a new module (four layers + tests)",
        False,
    ),
    "tree": (
        "directory_tree.py",
        "write the project tree to scripts/directory_tree.txt",
        False,
    ),
    "secret": ("generate_secret.py", "print a fresh application secret", False),
    "fernet": ("generate_fernet.py", "print a fresh Fernet key", False),
}


def _data_dir() -> Path:
    here = Path(__file__).resolve().parent
    installed = here / "data"
    return installed if installed.is_dir() else here.parent


def _scripts_dir() -> Path:
    return _data_dir() / "scripts"


def _bundled_opencode() -> Path:
    return _data_dir() / "opencode"


def _project_root() -> Path:
    override = os.environ.get("FASTDDD_PROJECT_ROOT")
    if override:
        return Path(override).resolve()
    cwd = Path.cwd().resolve()
    for candidate in (cwd, *cwd.parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    return cwd


def _python_and_script(script: Path, root: Path, needs_project_env: bool) -> list[str]:
    if needs_project_env and shutil.which("uv") and (root / "pyproject.toml").is_file():
        return ["uv", "run", "python", str(script)]
    return [sys.executable, str(script)]


def _run(script_name: str, args: list[str], needs_project_env: bool) -> int:
    script = _scripts_dir() / script_name
    if not script.is_file():
        print(f"fastddd: bundled script not found: {script}", file=sys.stderr)
        return 1

    root = _project_root()
    env = os.environ.copy()
    env["FASTDDD_PROJECT_ROOT"] = str(root)
    if not (root / ".opencode").is_dir() and _bundled_opencode().is_dir():
        env["FASTDDD_OPENCODE_DIR"] = str(_bundled_opencode())

    command = [*_python_and_script(script, root, needs_project_env), *args]
    return subprocess.call(command, cwd=str(root), env=env)


def _print_help() -> None:
    print(f"fastddd {__version__} — FastAPI Clean Architecture + DDD toolkit\n")
    print("usage: fastddd <command> [options]\n")
    print("commands:")
    width = max(len(name) for name in COMMANDS)
    for name, (_, help_text, _) in COMMANDS.items():
        print(f"  {name:<{width}}  {help_text}")
    print("\n  list                       show this list")
    print("  version                    show the version")
    print("\nRun 'fastddd <command> --help' for a command's own options.")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    if not args or args[0] in {"-h", "--help", "help", "list"}:
        _print_help()
        return 0
    if args[0] in {"-v", "--version", "version"}:
        print(f"fastddd {__version__}")
        return 0

    name, rest = args[0], args[1:]
    if name not in COMMANDS:
        print(f"fastddd: unknown command '{name}'", file=sys.stderr)
        _print_help()
        return 2

    script_name, _, needs_project_env = COMMANDS[name]
    return _run(script_name, rest, needs_project_env)


if __name__ == "__main__":
    sys.exit(main())

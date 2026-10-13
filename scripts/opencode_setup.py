"""Install this project's opencode assets into the user's opencode config.

Two scopes:

* Project-scoped (default, always on): the assets live in the repo under
  `.opencode/`, which opencode auto-loads whenever the project is the working
  directory. Nothing to install — they travel with the clone.
* Global (`--global`): copy the same skills and commands to
  `~/.config/opencode/` so they are available in every project on the machine.

Also guarantees `opencode.jsonc` is present and valid, because opencode refuses
to start on a malformed config.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(
    os.environ.get("FASTDDD_PROJECT_ROOT", Path(__file__).resolve().parent.parent)
).resolve()
GLOBAL_DIR = Path.home() / ".config" / "opencode"

CANONICAL_CONFIG = {
    "$schema": "https://opencode.ai/config.json",
    "mcp": {
        "codegraph": {
            "type": "local",
            "command": ["codegraph", "serve", "--mcp"],
            "enabled": True,
        }
    },
}

SKILL_GLOBS = ("skills/*/SKILL.md", "skill/*/SKILL.md")
COMMAND_GLOBS = ("command/*.md", "commands/*.md")
AGENT_GLOBS = ("agent/*.md", "agents/*.md")


def strip_jsonc(text: str) -> str:
    """Remove // and /* */ comments plus trailing commas so json.loads accepts it."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"(^|\s)//[^\n]*", r"\1", text)
    return re.sub(r",(\s*[}\]])", r"\1", text)


def config_is_valid(path: Path) -> bool:
    try:
        json.loads(strip_jsonc(path.read_text(encoding="utf-8")))
        return True
    except json.JSONDecodeError, OSError:
        return False


def ensure_config(*, fix: bool = True) -> tuple[str, str]:
    """Return (status, message) for opencode.jsonc."""
    path = PROJECT_ROOT / "opencode.jsonc"
    if not path.exists():
        path.write_text(json.dumps(CANONICAL_CONFIG, indent=2) + "\n", encoding="utf-8")
        return "created", str(path)

    if config_is_valid(path):
        return "ok", str(path)

    if fix:
        backup = path.with_suffix(".jsonc.bak")
        shutil.copy2(path, backup)
        path.write_text(json.dumps(CANONICAL_CONFIG, indent=2) + "\n", encoding="utf-8")
        return "fixed", f"{path} (backup: {backup.name})"

    return "invalid", str(path)


def collect_assets() -> list[tuple[Path, str]]:
    """Return (source, kind) for every skill, command and agent in the project."""
    assets: list[tuple[Path, str]] = []
    base = Path(os.environ.get("FASTDDD_OPENCODE_DIR", PROJECT_ROOT / ".opencode"))
    if not base.exists():
        return assets

    for pattern in SKILL_GLOBS:
        for path in base.glob(pattern):
            assets.append((path, "skill"))
    for pattern in COMMAND_GLOBS:
        for path in base.glob(pattern):
            assets.append((path, "command"))
    for pattern in AGENT_GLOBS:
        for path in base.glob(pattern):
            assets.append((path, "agent"))
    return assets


def install_globally() -> list[str]:
    """Copy skills, commands and agents to ~/.config/opencode."""
    installed: list[str] = []
    for source, kind in collect_assets():
        # skills/<name>/     ->  ~/.config/opencode/skills/<name>/   (whole folder)
        # command/<name>.md  ->  ~/.config/opencode/command/<name>.md
        # agent/<name>.md    ->  ~/.config/opencode/agent/<name>.md
        if kind == "skill":
            name = source.parent.name
            destination = GLOBAL_DIR / "skills" / name
            # Mirror the whole skill folder so SKILL.md and its references/
            # stay together; remove any previous copy first.
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(source.parent, destination)
        else:
            name = source.stem
            destination = GLOBAL_DIR / kind / source.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        installed.append(f"{kind}:{name}")
    return installed


def setup(*, global_install: bool = False, fix: bool = True) -> int:
    """Ensure config + optionally install assets globally. Returns exit code."""
    print("=== opencode configuration ===")

    status, detail = ensure_config(fix=fix)
    labels = {
        "ok": "[ok]   config valid",
        "created": "[new]  config created",
        "fixed": "[fix]  config repaired",
        "invalid": "[FAIL] config is invalid",
    }
    print(f"  {labels.get(status, status)}  {detail}")

    assets = collect_assets()
    if assets:
        print(f"  [ok]   {len(assets)} project asset(s) in .opencode/ (auto-loaded)")
    else:
        print("  [warn] no assets under .opencode/ to install")

    if global_install:
        try:
            installed = install_globally()
        except OSError as e:
            print(f"  [FAIL] global install failed: {e}")
            return 1
        for item in installed:
            print(f"  [inst]  {item} -> {GLOBAL_DIR}")
        print("  restart opencode to pick up newly installed skills/commands")

    return 0 if status != "invalid" else 1


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Install this project's opencode skills and commands."
    )
    parser.add_argument(
        "--global",
        dest="global_install",
        action="store_true",
        help="also copy skills/commands to ~/.config/opencode",
    )
    parser.add_argument(
        "--no-fix",
        dest="fix",
        action="store_false",
        help="report an invalid opencode.jsonc instead of repairing it",
    )
    args = parser.parse_args()
    return setup(global_install=args.global_install, fix=args.fix)


if __name__ == "__main__":
    sys.exit(main())

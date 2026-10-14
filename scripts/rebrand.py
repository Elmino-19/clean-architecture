"""Rename this template into your own project, in place.

The upstream template hardcodes its own name in four flavours: the dashed slug
(used by Docker), the underscored slug (used by table names), the Title Case
display name, and the author's contact details. This script rewrites all of
them, plus the package name in `pyproject.toml`, so a fresh clone reads as
yours from the first commit.

Documentation is left alone by default. Prose files (README, docs/) are long and
the mentions are mostly historical attribution you probably want to keep, so
pass --docs to rewrite them too.

Safe to re-run: it only replaces exact known strings.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(
    os.environ.get("FASTDDD_PROJECT_ROOT", Path(__file__).resolve().parent.parent)
).resolve()

SLUG_DASHED = "clean-architecture"
SLUG_UNDERSCORED = "clean_architecture"
TITLE = "Clean Architecture"
AUTHOR = "Erfan Mohamadnia"
AUTHOR_EMAIL = "zelzeleh.19@gmail.com"
AUTHOR_URL = "https://github.com/Elmino-19"

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    ".codegraph",
    "node_modules",
    "__pycache__",
    ".ruff_cache",
    ".pytest_cache",
    "secrets",
    ".me",
}
BINARY_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".pdf",
    ".zip",
    ".gz",
    ".db",
    ".pem",
    ".pyc",
}
DOC_SUFFIXES = {".md", ".txt", ".rst"}

CODE_TARGETS = [
    "pyproject.toml",
    "alembic.ini",
    "docker-compose.yaml",
    "Makefile",
    ".env.example",
    "app/app.py",
    "app/core/settings.py",
]


def to_dashed(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")


def to_underscored(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")


def to_title(name: str) -> str:
    return " ".join(
        part.capitalize() for part in re.split(r"[^A-Za-z0-9]+", name) if part
    )


def build_replacements(
    project: str, author: str, email: str, url: str
) -> list[tuple[str, str]]:
    """Ordered longest-first so the underscored slug wins over the dashed one."""
    pairs = [
        (SLUG_UNDERSCORED, to_underscored(project)),
        (SLUG_DASHED, to_dashed(project)),
        (TITLE, to_title(project)),
        (AUTHOR_EMAIL, email),
        (AUTHOR_URL, url),
        (AUTHOR, author),
    ]
    # Longest source first prevents a short pattern from eating a longer one.
    return sorted(pairs, key=lambda kv: len(kv[0]), reverse=True)


def iter_files(include_docs: bool) -> list[Path]:
    files: list[Path] = []
    this_file = Path(__file__).resolve()
    for path in sorted(PROJECT_ROOT.rglob("*")):
        if not path.is_file():
            continue
        if path.resolve() == this_file:
            # Never rewrite the replacement table inside this script.
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in BINARY_SUFFIXES:
            continue
        if path.suffix.lower() == ".md" and not include_docs:
            continue
        files.append(path)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rename the template into your own project, in place."
    )
    parser.add_argument("project", help="Project name, e.g. 'Acme CRM'")
    parser.add_argument("--author", default="", help="Your name")
    parser.add_argument("--email", default="", help="Your email")
    parser.add_argument("--url", default="", help="Your project URL")
    parser.add_argument(
        "--docs",
        action="store_true",
        help="also rewrite README and other markdown prose",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show what would change without writing",
    )
    args = parser.parse_args()

    if not args.project.strip():
        print("Error: project name is required.", file=sys.stderr)
        return 1

    author = args.author or "Your Name"
    email = args.email or "you@example.com"
    url = args.url or "https://example.com"

    replacements = build_replacements(args.project, author, email, url)

    changed: list[tuple[Path, int]] = []

    for path in iter_files(include_docs=args.docs):
        try:
            original = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError:
            continue

        updated = original
        hits = 0
        for old, new in replacements:
            if old and old in updated:
                hits += updated.count(old)
                updated = updated.replace(old, new)

        if hits and updated != original:
            changed.append((path, hits))
            if not args.dry_run:
                path.write_text(updated, encoding="utf-8")

    relative_total = 0
    for path, hits in changed:
        relative = path.relative_to(PROJECT_ROOT)
        relative_total += hits
        marker = "would update" if args.dry_run else "updated"
        print(f"  [{marker}] {relative} ({hits})")

    print()
    verb = "would replace" if args.dry_run else "replaced"
    print(f"{verb} {relative_total} occurrence(s) across {len(changed)} file(s).")

    if args.dry_run:
        print("\nRe-run without --dry-run to apply.")

    print("\nRemaining references (informational):")
    for path in iter_files(include_docs=True):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError:
            continue
        left = sum(text.count(old) for old, _ in replacements)
        if left:
            print(f"  {path.relative_to(PROJECT_ROOT)}: {left}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

import os

IGNORED_DIRS = {".venv", ".git", ".idea", ".ruff_cache", ".codegraph", ".me"}

PROJECT_ROOT = os.environ.get("FASTDDD_PROJECT_ROOT") or os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
)


def write_tree(path, file, prefix=""):
    entries = sorted(os.listdir(path))
    for index, entry in enumerate(entries):
        full_path = os.path.join(path, entry)
        connector = "└── " if index == len(entries) - 1 else "├── "
        file.write(prefix + connector + entry + "\n")
        if os.path.isdir(full_path) and entry not in IGNORED_DIRS:
            extension = "    " if index == len(entries) - 1 else "│   "
            write_tree(full_path, file, prefix + extension)


if __name__ == "__main__":
    root_name = os.path.basename(PROJECT_ROOT.rstrip(os.sep))
    output_path = os.path.join(PROJECT_ROOT, "scripts", "directory_tree.txt")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(root_name + "\n")
        write_tree(PROJECT_ROOT, f)

    print(f"Directory tree saved to: {output_path}")

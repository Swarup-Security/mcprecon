"""
scanner/tools.py
----------------
Scans for supporting developer tools that AI agents commonly need:
  git, curl, jq, sqlite3, psql, redis-cli, docker, podman, VS Code, Cursor.

Detection method: shutil.which() to find the binary,
then run --version to get the installed version string.
"""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from utils import which, run, make_item
from report.terminal import ok, miss, print_header


# (binary_name, display_label)
TOOLS = [
    ("git",       "Git"),
    ("curl",      "curl"),
    ("jq",        "jq"),
    ("sqlite3",   "SQLite"),
    ("psql",      "PostgreSQL client"),
    ("redis-cli", "Redis client"),
    ("docker",    "Docker"),
    ("podman",    "Podman"),
    ("code",      "VS Code CLI"),
    ("cursor",    "Cursor CLI"),
]


def scan() -> dict:
    print_header("Supporting Tools")
    items = []

    for binary, label in TOOLS:
        path = which(binary)
        if path:
            ver_raw = run([binary, "--version"], timeout=3)
            ver     = ver_raw.splitlines()[0][:60] if ver_raw else "found"
            print(ok(f"{label:<22}: {ver}"), flush=True)
            items.append(make_item("ok", label, ver))
        else:
            print(miss(f"{label:<22}: not found"), flush=True)
            items.append(make_item("miss", label, "not found"))

    return {"title": "Supporting Tools", "items": items}

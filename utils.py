"""
utils.py
--------
Shared helper functions used by every scanner and report module.
Nothing here does any scanning — these are pure utilities.
"""

import shutil
import subprocess
from pathlib import Path
from typing import Optional


def which(name: str) -> Optional[str]:
    """
    Check if a binary/executable exists on the system PATH.
    Same as typing `which ollama` in your terminal.
    Returns the full path if found, None if not.
    """
    return shutil.which(name)


def run(cmd: list[str], timeout: int = 6) -> Optional[str]:
    """
    Run a shell command and return its stdout as a string.
    Returns None if the command fails or times out.
    Example: run(["ollama", "list"]) -> "llama3  ...\\ngemma ..."
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def pkgver(package: str) -> Optional[str]:
    """
    Check if a Python package is installed and return its version.
    Uses Python's own import system — no subprocess, no pip call.
    Returns version string if installed, None if not installed.
    """
    import importlib.util as U
    import importlib.metadata as M

    # pip uses hyphens (mcp-agent) but Python imports use underscores (mcp_agent)
    module_name = package.replace("-", "_").replace(".", "_")

    if U.find_spec(module_name) is None:
        return None
    try:
        return M.version(package)
    except Exception:
        return "installed"


def http_ok(url: str, timeout: int = 3) -> bool:
    """
    Check if an HTTP endpoint is reachable.
    Used to verify local services are actually running
    (e.g. Ollama on localhost:11434).
    Does NOT send any data — just checks reachability.
    """
    try:
        import urllib.request
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except Exception:
        return False


def dir_count_gb(path: Path, extensions: list[str]) -> tuple[int, float]:
    """
    Walk a directory and count files matching given extensions.
    Returns (file_count, total_size_in_GB).
    Used to measure model caches (HuggingFace, LM Studio, etc.)
    """
    count, total_gb = 0, 0.0
    if not path.exists():
        return count, total_gb
    for ext in extensions:
        for f in path.rglob(f"*{ext}"):
            count += 1
            total_gb += f.stat().st_size / 1_073_741_824  # bytes -> GB
    return count, total_gb


def make_item(status: str, label: str, detail: str = "", children: list = None) -> dict:
    """
    Create a structured data item consumed by both terminal and HTML renderers.
    status: "ok" | "warn" | "miss" | "info"
    """
    return {
        "status": status,
        "label": label,
        "detail": detail,
        "children": children or []
    }


def make_risk(level: str, label: str, detail: str = "") -> dict:
    """
    Create a risk item for the permissions audit.
    level: "high" | "med" | "low" | "info"
    """
    return {
        "status": f"risk_{level}",
        "label": label,
        "detail": detail,
        "children": []
    }

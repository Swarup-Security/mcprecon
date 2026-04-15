"""
permissions/system_caps.py
--------------------------
Reports what the underlying machine is physically capable of.

This is the ground-truth baseline — not what any specific agent
has configured, but what ANY process running on this machine
can do by default.

Key insight: Read/write files and Make HTTP requests are always True
because every Python process can do those things without any opt-in.
"""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import platform
from pathlib import Path

from utils import which, make_risk
from report.terminal import print_subheader, print_risk


def scan_capabilities() -> list[dict]:
    """
    Return a list of risk items describing what this machine can do.
    """
    print_subheader("System Capabilities Summary")
    print()

    capabilities = {
        "Run shell commands":     any(which(b) for b in ["bash", "zsh", "sh", "powershell"]),
        "Read/write files":       True,   # every process can do this — no opt-in needed
        "Access home directory":  Path.home().exists(),
        "Make HTTP requests":     True,   # urllib is always available in Python
        "Access local databases": bool(which("sqlite3") or which("psql") or which("mysql")),
        "Run Docker containers":  bool(which("docker")),
        "Access GPU":             bool(which("nvidia-smi") or platform.system() == "Darwin"),
        "Read env vars/secrets":  True,   # os.environ is always accessible
        "Execute Python code":    True,   # always true in any Python process
        "Access clipboard":       platform.system() in ("Darwin", "Windows"),
    }

    items = []
    for capability, available in capabilities.items():
        level  = "med" if available else "low"
        status = "yes" if available else "no"
        print_risk(level, capability, status)
        items.append(make_risk(level, capability, status))

    return items

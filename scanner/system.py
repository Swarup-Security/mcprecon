"""
scanner/system.py
-----------------
Scans basic system information:
  - Operating system and architecture
  - Python version and executable path
  - Python environment type (venv, conda, system)
"""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import os
import sys
import platform

from utils import make_item
from report.terminal import ok, info, print_header


def scan() -> dict:
    print_header("System")
    items = []

    # OS
    os_str = f"{platform.system()} {platform.release()} ({platform.machine()})"
    print(info(f"OS        : {os_str}"), flush=True)
    items.append(make_item("info", "OS", os_str))

    # Python
    py_str = f"{sys.version.split()[0]} @ {sys.executable}"
    print(info(f"Python    : {py_str}"), flush=True)
    items.append(make_item("info", "Python", py_str))

    # Environment type
    if os.environ.get("VIRTUAL_ENV"):
        env_str = f"virtualenv ({os.environ['VIRTUAL_ENV']})"
    elif os.environ.get("CONDA_DEFAULT_ENV"):
        env_str = f"conda ({os.environ['CONDA_DEFAULT_ENV']})"
    else:
        env_str = "system Python (no venv/conda detected)"

    print(info(f"Env       : {env_str}"), flush=True)
    items.append(make_item("info", "Env", env_str))

    return {"title": "System", "items": items}

"""
report/terminal.py
------------------
Everything related to printing coloured output to the terminal.
All other modules import from here — no ANSI codes anywhere else.
"""

import sys

# Force UTF-8 output — prevents silent crashes on macOS terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ANSI colour codes
G = "\033[92m"   # green
Y = "\033[93m"   # yellow
C = "\033[96m"   # cyan
R = "\033[91m"   # red
B = "\033[1m"    # bold
D = "\033[2m"    # dim
Z = "\033[0m"    # reset

# Status line prefixes
def ok(msg):   return f"{G}[OK]{Z}  {msg}"
def warn(msg): return f"{Y}[~]{Z}   {msg}"
def miss(msg): return f"{R}[X]{Z}   {msg}"
def info(msg): return f"{C}[i]{Z}   {msg}"

# Risk level prefixes
RISK = {
    "high": f"{R}[HIGH]{Z}",
    "med":  f"{Y}[MED] {Z}",
    "low":  f"{G}[LOW] {Z}",
    "info": f"{C}[INFO]{Z}",
}

def print_risk(level: str, label: str, detail: str = ""):
    print(f"  {RISK.get(level, RISK['info'])}  {B}{label}{Z}  {D}{detail}{Z}", flush=True)

def print_header(title: str):
    bar = "-" * 60
    print(f"\n{B}{bar}{Z}\n{B}  {title}{Z}\n{B}{bar}{Z}", flush=True)

def print_subheader(title: str):
    print(f"\n  {B}{title}{Z}\n  {'─' * 50}", flush=True)

def print_item(item: dict, depth: int = 0):
    """Recursively print a structured item and its children."""
    status  = item.get("status", "info")
    label   = item.get("label", "")
    detail  = item.get("detail", "")
    children = item.get("children", [])

    indent = "  " * depth

    if status.startswith("risk_"):
        level = status.replace("risk_", "")
        print_risk(level, label, detail)
    elif status == "ok":
        print(f"{indent}{ok(label + ('  ' + D + detail + Z if detail else ''))}", flush=True)
    elif status == "warn":
        print(f"{indent}{warn(label + ('  ' + D + detail + Z if detail else ''))}", flush=True)
    elif status == "miss":
        print(f"{indent}{miss(label + ('  ' + D + detail + Z if detail else ''))}", flush=True)
    else:
        print(f"{indent}{info(label + ('  ' + D + detail + Z if detail else ''))}", flush=True)

    for child in children:
        print_item(child, depth + 1)

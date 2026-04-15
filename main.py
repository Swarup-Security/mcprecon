"""
main.py
-------
Entry point. Run this file:

    python3 main.py

This file does nothing itself except call each module in order
and collect their results for the HTML report.
"""

import sys
import datetime
from pathlib import Path

# Force UTF-8 output — prevents silent crashes on some terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add the project root to Python's module search path so all
# submodules (scanner/, permissions/, report/) can import utils.py
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ── Scanner modules ───────────────────────────────────────────────────────────
from scanner import (
    system, claude, gpu, llm_runtimes,
    agent_frameworks, mcp, api_keys, tools,
    remote_mcp,
)

# ── Permissions modules ───────────────────────────────────────────────────────
from permissions import mcp_audit, framework_audit, system_caps

# ── Report modules ────────────────────────────────────────────────────────────
from report import html
from report.terminal import print_header, B, G, C, Z


def main():
    scan_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{'='*60}", flush=True)
    print(f"  AI / MCP Ecosystem Scanner", flush=True)
    print(f"  {scan_time}", flush=True)
    print(f"{'='*60}\n", flush=True)

    # ── Run all scanners ──────────────────────────────────────────────────────
    results = [
        system.scan(),
        claude.scan(),
        gpu.scan(),
        llm_runtimes.scan(),
        agent_frameworks.scan(),
        mcp.scan(),
        remote_mcp.scan(),       # ← checks remote MCP servers
        api_keys.scan(),
        tools.scan(),
    ]

    # ── Run permissions audit ─────────────────────────────────────────────────
    print_header("Permissions Audit")

    permissions = {
        "title": "Permissions Audit",
        "sections": [
            {
                "subtitle": "MCP Server Permissions",
                "items": mcp_audit.scan_all_configs(),
            },
            {
                "subtitle": "Agent Framework Capabilities",
                "items": framework_audit.scan_installed(),
            },
            {
                "subtitle": "System Capabilities Summary",
                "items": system_caps.scan_capabilities(),
            },
        ]
    }

    # ── Write HTML report ─────────────────────────────────────────────────────
    html_path = Path(__file__).resolve().parent / "scan_report.html"
    try:
        html_path.write_text(
            html.build(results, permissions, scan_time),
            encoding="utf-8"
        )
        print(f"\n{'='*60}", flush=True)
        print(f"{B}{G}  Scan complete.{Z}", flush=True)
        print(f"  HTML report  ->  {B}{html_path}{Z}", flush=True)
        print(f"  Open it with:    open scan_report.html", flush=True)
        print(f"{'='*60}\n", flush=True)
    except Exception as e:
        print(f"\nERROR writing HTML report: {e}", flush=True)


if __name__ == "__main__":
    main()

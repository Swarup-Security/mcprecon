"""
permissions/mcp_audit.py
------------------------
Reads MCP server config files and analyses what each server can do.

For each server it reads:
  - command  → what runtime launches it (npx, python, uvx, docker)
  - args     → what arguments are passed (paths, flags, server names)
  - env      → what environment variables (secrets, config) it gets

Then runs keyword matching to infer capabilities and risks.
Nothing is executed — this is purely static analysis of the config.
"""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import json
import os
from pathlib import Path

from utils import make_item, make_risk
from report.terminal import print_subheader, print_risk, C, D, Z, B


# All places where MCP server configs can live
CONFIG_LOCATIONS = [
    # Claude Desktop
    Path.home() / "Library/Application Support/Claude/claude_desktop_config.json",
    Path(os.environ.get("APPDATA", "")) / "Claude/claude_desktop_config.json",
    Path.home() / ".config/Claude/claude_desktop_config.json",
    # Cursor editor
    Path.home() / ".cursor/mcp.json",
    Path.home() / ".cursor/settings.json",
    # Continue VSCode extension
    Path.home() / ".continue/config.json",
    # Windsurf editor
    Path.home() / ".codeium/windsurf/mcp_config.json",
    # Project-local configs
    Path.cwd() / ".mcp.json",
    Path.cwd() / "mcp.json",
    Path.cwd() / ".cursor/mcp.json",
]

# Third-party APIs to detect by keyword in server name or args
THIRD_PARTY_APIS = {
    "github":     "GitHub API (repos, code, PRs)",
    "slack":      "Slack workspace (messages, channels)",
    "google":     "Google services",
    "drive":      "Google Drive (files)",
    "gmail":      "Gmail (read/send emails)",
    "notion":     "Notion workspace",
    "jira":       "Jira (issues, projects)",
    "stripe":     "Stripe (payment data)",
    "aws":        "AWS cloud resources",
    "gcp":        "Google Cloud resources",
    "azure":      "Azure cloud resources",
    "figma":      "Figma (design files)",
    "brave":      "Brave Search API",
    "linear":     "Linear (issues)",
}


def _audit_one_server(name: str, conf: dict) -> list[dict]:
    """
    Analyse a single MCP server config and return a list of risk items.

    Strategy:
      1. Detect the runtime from `command`
      2. Keyword-scan `args` for dangerous capabilities
      3. Check `env` for embedded secrets
    """
    risks = []
    cmd      = conf.get("command", "")
    args     = conf.get("args", [])
    env      = conf.get("env", {})
    all_args = " ".join(str(a) for a in args).lower()
    cmd_low  = str(cmd).lower()

    # ── Runtime ───────────────────────────────────────────────────────────────
    if "npx" in cmd_low or "node" in cmd_low:
        runtime = "Node.js / npx"
    elif any(x in cmd_low for x in ["uvx", "python", "uv"]):
        runtime = "Python / uvx"
    elif "docker" in cmd_low:
        runtime = "Docker container"
    else:
        runtime = str(cmd) or "unknown"
    risks.append(make_risk("info", "Runtime", runtime))

    # ── Shell / code execution ────────────────────────────────────────────────
    # If the server name or args contain these words, it can run arbitrary commands
    shell_kw = ["shell", "bash", "exec", "terminal", "run-command",
                "computer-use", "subprocess", "powershell", "cmd"]
    if any(s in all_args or s in cmd_low for s in shell_kw):
        risks.append(make_risk("high", "Shell execution",
                               "Can run arbitrary commands on your machine"))

    # ── Filesystem access ─────────────────────────────────────────────────────
    # Check for filesystem-related keywords, then extract explicit paths from args
    fs_kw = ["filesystem", "files", "file-system", "read-file", "write-file", "directory"]
    if any(s in all_args or s in cmd_low for s in fs_kw):
        exposed_paths = [
            str(a) for a in args
            if Path(str(a)).is_absolute() or str(a).startswith("~")
        ]
        if exposed_paths:
            for path in exposed_paths:
                # Paths inside home dir or sensitive system dirs = HIGH
                is_sensitive = any(s in path for s in [
                    str(Path.home()), "/etc", "/var", "C:\\Users"
                ])
                level = "high" if is_sensitive else "med"
                risks.append(make_risk(level, "Filesystem access", f"Path exposed: {path}"))
        else:
            risks.append(make_risk("med", "Filesystem access",
                                   "Filesystem server (no explicit path scope in args)"))

    # ── Network / HTTP access ─────────────────────────────────────────────────
    net_kw = ["fetch", "http", "browser", "web", "internet", "search",
              "crawl", "request", "url", "brave", "puppeteer", "playwright"]
    if any(s in all_args or s in cmd_low for s in net_kw):
        risks.append(make_risk("med", "Network / HTTP access",
                               "Can make outbound requests or browse the web"))

    # ── Database access ───────────────────────────────────────────────────────
    db_kw = ["sqlite", "postgres", "mysql", "database", "db", "sql", "mongo"]
    if any(s in all_args or s in cmd_low for s in db_kw):
        db_files = [str(a) for a in args if str(a).endswith((".db", ".sqlite", ".sqlite3"))]
        detail   = f"DB file: {db_files[0]}" if db_files else "Database access"
        risks.append(make_risk("med", "Database access", detail))

    # ── Third-party API access ────────────────────────────────────────────────
    # Check server name + args for known service keywords
    for keyword, label in THIRD_PARTY_APIS.items():
        if keyword in all_args or keyword in cmd_low or keyword in name.lower():
            risks.append(make_risk("med", "Third-party API", label))

    # ── Environment variables / secrets ───────────────────────────────────────
    # The `env` block in an MCP config passes env vars to the server process.
    # If they contain words like "key", "token", "secret" — they're credentials.
    if env:
        secret_kw = ["key", "token", "secret", "password", "api", "auth", "credential"]
        for var_name, var_value in env.items():
            if any(k in var_name.lower() for k in secret_kw):
                # Mask the value — show only that it exists
                risks.append(make_risk("high", "Secret in env",
                                       f"{var_name} = ****"))
            else:
                risks.append(make_risk("low", "Env var",
                                       f"{var_name} = {var_value}"))

    # ── Clipboard / memory / screen ───────────────────────────────────────────
    system_kw = ["memory", "clipboard", "keychain", "screenshot", "screen"]
    if any(s in all_args or s in cmd_low for s in system_kw):
        risks.append(make_risk("high", "System access",
                               "Clipboard / memory / screen access"))

    # ── No elevated permissions ───────────────────────────────────────────────
    non_trivial = [r for r in risks if r["status"] not in ("risk_info", "risk_low")]
    if not non_trivial:
        risks.append(make_risk("low", "No elevated permissions detected",
                               "Review args manually if unsure"))

    return risks


def scan_all_configs() -> tuple[list[dict], list[dict]]:
    """
    Read all known MCP config files, audit each server, and return:
      - items: list of structured items for the report
      - terminal output is printed as a side effect
    """
    print_subheader("MCP Server Permissions")

    items   = []
    seen    = set()
    found   = False

    for cfg_path in CONFIG_LOCATIONS:
        if not cfg_path.exists():
            continue
        try:
            data = json.loads(cfg_path.read_text())
        except Exception:
            continue

        servers = data.get("mcpServers", {})
        if not servers:
            continue

        found = True
        print(f"\n  {D}Config: {cfg_path}{Z}", flush=True)

        for server_name, server_conf in servers.items():
            if server_name in seen:
                continue
            seen.add(server_name)

            print(f"\n  {C}>> {server_name}{Z}", flush=True)
            risks = _audit_one_server(server_name, server_conf)

            for r in risks:
                level = r["status"].replace("risk_", "")
                print_risk(level, r["label"], r["detail"])

            items.append(make_item("info", server_name, str(cfg_path), risks))

    if not found:
        print(f"\n  {D}No MCP server configs found.{Z}", flush=True)
        items.append(make_item("warn", "No MCP server configs found",
                               "Install Claude Desktop or add an mcp.json"))

    return items

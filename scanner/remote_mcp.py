"""
scanner/remote_mcp.py
---------------------
Detects remote MCP servers from config files and analyses
what LOCAL permissions they have been granted.

"Remote" means the server runs on an external host (has a url field,
SSE/HTTP transport, or a URL in its args) — but it can still be
configured with local access: filesystem paths, env secrets,
database files, shell commands, etc.

No network calls are made. Pure static analysis of the config.
"""

import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import json
import os

from utils import make_item, make_risk
from report.terminal import ok, warn, miss, info, print_header, G, Y, R, C, D, B, Z


CONFIG_LOCATIONS = [
    Path.home() / "Library/Application Support/Claude/claude_desktop_config.json",
    Path(os.environ.get("APPDATA", "")) / "Claude/claude_desktop_config.json",
    Path.home() / ".config/Claude/claude_desktop_config.json",
    Path.home() / ".cursor/mcp.json",
    Path.home() / ".cursor/settings.json",
    Path.home() / ".continue/config.json",
    Path.home() / ".codeium/windsurf/mcp_config.json",
    Path.cwd() / ".mcp.json",
    Path.cwd() / "mcp.json",
]

# Known remote MCP server names/keywords → what service they connect to
KNOWN_REMOTE_SERVICES = {
    "github":      "GitHub (repos, code, PRs, issues)",
    "gitlab":      "GitLab (repos, pipelines)",
    "slack":       "Slack (messages, channels, files)",
    "notion":      "Notion (pages, databases)",
    "jira":        "Jira (issues, projects, boards)",
    "confluence":  "Confluence (wiki pages)",
    "linear":      "Linear (issues, projects)",
    "asana":       "Asana (tasks, projects)",
    "google":      "Google services",
    "gmail":       "Gmail (read/send emails)",
    "drive":       "Google Drive (files)",
    "calendar":    "Google Calendar (events)",
    "sheets":      "Google Sheets (spreadsheets)",
    "dropbox":     "Dropbox (files)",
    "figma":       "Figma (design files)",
    "stripe":      "Stripe (payments, customers)",
    "salesforce":  "Salesforce (CRM data)",
    "hubspot":     "HubSpot (CRM, marketing)",
    "zendesk":     "Zendesk (support tickets)",
    "aws":         "AWS cloud resources",
    "gcp":         "Google Cloud resources",
    "azure":       "Azure cloud resources",
    "brave":       "Brave Search (web search)",
    "tavily":      "Tavily (web search)",
    "browserbase": "Browserbase (remote browser)",
    "puppeteer":   "Puppeteer (browser automation)",
    "playwright":  "Playwright (browser automation)",
    "postgres":    "PostgreSQL database",
    "mysql":       "MySQL database",
    "mongo":       "MongoDB database",
    "redis":       "Redis (cache/queue)",
    "supabase":    "Supabase (database + auth)",
    "airtable":    "Airtable (spreadsheet database)",
}


def _is_remote(conf: dict) -> tuple[bool, str]:
    """
    Determine if a server config is remote.
    Returns (is_remote, url).

    Remote indicators:
      1. Has a `url` field                    → SSE or HTTP transport
      2. Has `transport.type` = sse/http      → explicit transport config
      3. Args contain an http:// or https://  → URL passed as argument
    """
    # Most common: direct url field
    if "url" in conf:
        return True, conf["url"]

    # Explicit transport block
    transport = conf.get("transport", {})
    if isinstance(transport, dict):
        t_type = transport.get("type", "")
        if t_type in ("sse", "http", "streamable_http"):
            return True, transport.get("url", "")

    # URL inside args list
    for arg in conf.get("args", []):
        s = str(arg)
        if s.startswith("http://") or s.startswith("https://"):
            return True, s

    return False, ""


def _get_transport_type(conf: dict, url: str) -> str:
    transport = conf.get("transport", {})
    if isinstance(transport, dict) and transport.get("type"):
        return transport["type"].upper()
    if "sse" in url.lower():
        return "SSE"
    return "HTTP"


def _audit_local_permissions(name: str, conf: dict, url: str) -> list:
    """
    Analyse what LOCAL machine access this remote server has been granted
    through its config — filesystem paths, env secrets, shell access, etc.

    This is identical logic to local server auditing because even remote
    servers can be given local access via their config.
    """
    risks = []
    args     = conf.get("args", [])
    env      = conf.get("env", {})
    headers  = conf.get("headers", {})
    all_args = " ".join(str(a) for a in args).lower()
    name_low = name.lower()

    # ── What remote service does this connect to ──────────────────────────────
    for keyword, service_label in KNOWN_REMOTE_SERVICES.items():
        if keyword in name_low or keyword in url.lower() or keyword in all_args:
            risks.append(make_risk("info", "Remote service", service_label))
            break

    # ── Transport ─────────────────────────────────────────────────────────────
    risks.append(make_risk("info", "Transport", _get_transport_type(conf, url)))
    risks.append(make_risk("info", "URL", url))

    # ── Data sent to external host ────────────────────────────────────────────
    # This is always true for any remote server — your prompts leave your machine
    risks.append(make_risk("high", "Data leaves your machine",
                           "Prompts and responses are sent to an external server"))

    # ── Filesystem access ─────────────────────────────────────────────────────
    fs_kw = ["filesystem", "files", "file-system", "read-file", "write-file", "directory"]
    if any(s in all_args for s in fs_kw):
        exposed = [str(a) for a in args
                   if Path(str(a)).is_absolute() or str(a).startswith("~")]
        if exposed:
            for ep in exposed:
                is_sensitive = any(s in ep for s in [
                    str(Path.home()), "/etc", "/var", "C:\\Users"
                ])
                level = "high" if is_sensitive else "med"
                risks.append(make_risk(level, "Local filesystem access",
                                       f"Path exposed to remote server: {ep}"))
        else:
            risks.append(make_risk("med", "Local filesystem access",
                                   "Filesystem access configured (no explicit path scope)"))

    # ── Shell / code execution on local machine ───────────────────────────────
    shell_kw = ["shell", "bash", "exec", "terminal", "subprocess", "powershell"]
    if any(s in all_args for s in shell_kw):
        risks.append(make_risk("high", "Local shell execution",
                               "Remote server can run commands on YOUR machine"))

    # ── Local database access ─────────────────────────────────────────────────
    db_kw = ["sqlite", "postgres", "mysql", "database", "mongo"]
    if any(s in all_args for s in db_kw):
        db_files = [str(a) for a in args if str(a).endswith((".db", ".sqlite", ".sqlite3"))]
        detail   = f"Local DB file: {db_files[0]}" if db_files else "Local database access"
        risks.append(make_risk("high", "Local database access", detail))

    # ── Secrets in env block ──────────────────────────────────────────────────
    # Env vars are passed to the server process — if they contain credentials,
    # those credentials are accessible to the remote server
    secret_kw = ["key", "token", "secret", "password", "api", "auth", "credential"]
    all_env = {**env}
    if headers:
        all_env.update(headers)

    for var, val in all_env.items():
        if any(k in var.lower() for k in secret_kw):
            risks.append(make_risk("high", "Secret passed to remote server",
                                   f"{var} = **** (value sent to external host)"))
        else:
            risks.append(make_risk("low", "Config var passed to remote server",
                                   f"{var} = {val}"))

    # ── Clipboard / screen access ─────────────────────────────────────────────
    sys_kw = ["clipboard", "screenshot", "screen", "keychain"]
    if any(s in all_args for s in sys_kw):
        risks.append(make_risk("high", "System access",
                               "Clipboard / screen data sent to remote server"))

    # ── No elevated local permissions ─────────────────────────────────────────
    non_trivial = [r for r in risks
                   if r["status"] not in ("risk_info", "risk_low")
                   and r["label"] not in ("Data leaves your machine",)]
    if not non_trivial:
        risks.append(make_risk("low", "No local permissions granted",
                               "Server connects remotely but has no local machine access"))

    return risks


def scan() -> dict:
    print_header("Remote MCP Servers")
    items        = []
    seen         = set()
    found_any    = False
    found_remote = False

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

        found_any = True
        print(f"\n  {D}Config: {cfg_path}{Z}", flush=True)

        for server_name, server_conf in servers.items():
            if server_name in seen:
                continue
            seen.add(server_name)

            is_remote, url = _is_remote(server_conf)

            if not is_remote:
                print(f"  {D}[local] {server_name} — skipped (local server){Z}", flush=True)
                continue

            found_remote = True
            print(f"\n  {C}{B}>> {server_name}{Z}  {Y}[REMOTE]{Z}", flush=True)
            print(f"     {D}URL: {url}{Z}", flush=True)

            risks = _audit_local_permissions(server_name, server_conf, url)

            for r in risks:
                level = r["status"].replace("risk_", "")
                icon  = (f"{R}[HIGH]{Z}" if level == "high"
                         else f"{Y}[MED] {Z}" if level == "med"
                         else f"{G}[LOW] {Z}" if level == "low"
                         else f"{C}[INFO]{Z}")
                print(f"     {icon}  {B}{r['label']}{Z}  {D}{r['detail']}{Z}", flush=True)

            items.append(make_item("warn", server_name, url, risks))

    if not found_any:
        print(miss("No MCP config files found"), flush=True)
        items.append(make_item("miss", "No MCP config files found", ""))
    elif not found_remote:
        print(info("No remote MCP servers found — all configured servers are local"), flush=True)
        items.append(make_item("info", "No remote MCP servers configured",
                               "All servers run locally on your machine"))

    return {"title": "Remote MCP Servers", "items": items}

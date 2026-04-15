"""
scanner/claude.py
-----------------
Scans everything Claude/Anthropic related:
  - Claude Code CLI (the `claude` binary)
  - Claude Desktop app installation
  - Claude Desktop MCP config file and configured servers
  - Anthropic Python SDK
  - ANTHROPIC_API_KEY environment variable
  - Claude models pulled into Ollama (community ports)
"""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import os
import json
import platform
from pathlib import Path

from utils import which, run, pkgver, http_ok, make_item
from report.terminal import ok, warn, miss, info, print_header, G, D, Z


def scan() -> dict:
    print_header("Claude (Anthropic)")
    items = []

    # ── Claude Code CLI ───────────────────────────────────────────────────────
    # Checks if the `claude` binary exists on PATH
    claude_bin = which("claude")
    if claude_bin:
        ver = run(["claude", "--version"])
        print(ok(f"Claude Code CLI : {ver or 'found'} @ {claude_bin}"), flush=True)
        items.append(make_item("ok", "Claude Code CLI", f"{ver or 'found'} @ {claude_bin}"))
    else:
        print(miss("Claude Code CLI : not installed  ->  npm install -g @anthropic-ai/claude-code"), flush=True)
        items.append(make_item("miss", "Claude Code CLI", "npm install -g @anthropic-ai/claude-code"))

    # ── Claude Desktop app ────────────────────────────────────────────────────
    # Checks known install paths per OS using Path.exists()
    desktop_paths = {
        "Darwin":  [Path("/Applications/Claude.app"),
                    Path.home() / "Applications/Claude.app"],
        "Windows": [Path(os.environ.get("LOCALAPPDATA", "")) / "AnthropicClaude/Claude.exe"],
        "Linux":   [Path("/opt/Claude/claude"),
                    Path.home() / ".local/share/applications/claude.desktop"],
    }
    desktop_found = next(
        (p for p in desktop_paths.get(platform.system(), []) if p.exists()), None
    )
    if desktop_found:
        print(ok(f"Claude Desktop : installed ({desktop_found})"), flush=True)
        items.append(make_item("ok", "Claude Desktop", str(desktop_found)))
    else:
        print(miss("Claude Desktop : not installed  ->  https://claude.ai/download"), flush=True)
        items.append(make_item("miss", "Claude Desktop", "https://claude.ai/download"))

    # ── Claude Desktop MCP config ─────────────────────────────────────────────
    # Claude Desktop stores its MCP server list in a JSON config file
    # This reads that file and lists every configured server
    cfg_path = {
        "Darwin":  Path.home() / "Library/Application Support/Claude/claude_desktop_config.json",
        "Windows": Path(os.environ.get("APPDATA", "")) / "Claude/claude_desktop_config.json",
        "Linux":   Path.home() / ".config/Claude/claude_desktop_config.json",
    }.get(platform.system())

    if cfg_path and cfg_path.exists():
        try:
            data    = json.loads(cfg_path.read_text())
            servers = data.get("mcpServers", {})
            children = [
                make_item("info", name, str(conf.get("command", "")))
                for name, conf in servers.items()
            ]
            print(ok(f"Claude Desktop config : {cfg_path}  ({len(servers)} MCP servers)"), flush=True)
            for name in servers:
                print(f"      {G}*{Z} {name}", flush=True)
            items.append(make_item("ok", "Claude Desktop config", str(cfg_path), children))
        except Exception as e:
            print(warn(f"Claude Desktop config : could not parse ({e})"), flush=True)
            items.append(make_item("warn", "Claude Desktop config", str(e)))
    else:
        print(miss("Claude Desktop config : not found"), flush=True)
        items.append(make_item("miss", "Claude Desktop config", "not found"))

    # ── Anthropic Python SDK ──────────────────────────────────────────────────
    # Uses importlib to check if the `anthropic` package is installed
    ver = pkgver("anthropic")
    if ver:
        print(ok(f"Anthropic Python SDK : {ver}"), flush=True)
        items.append(make_item("ok", "Anthropic Python SDK", ver))
    else:
        print(miss("Anthropic Python SDK : not installed  ->  pip install anthropic"), flush=True)
        items.append(make_item("miss", "Anthropic Python SDK", "pip install anthropic"))

    # ── ANTHROPIC_API_KEY ─────────────────────────────────────────────────────
    # Reads os.environ — same as `echo $ANTHROPIC_API_KEY` in your terminal
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key:
        masked   = api_key[:7] + "****" + api_key[-4:]
        children = []
        if http_ok("https://api.anthropic.com"):
            children.append(make_item("ok", "api.anthropic.com", "reachable"))
        else:
            children.append(make_item("warn", "api.anthropic.com", "not reachable"))
        print(ok(f"ANTHROPIC_API_KEY : {masked}"), flush=True)
        items.append(make_item("ok", "ANTHROPIC_API_KEY", masked, children))
    else:
        print(miss("ANTHROPIC_API_KEY : not set  ->  export ANTHROPIC_API_KEY=sk-ant-..."), flush=True)
        items.append(make_item("miss", "ANTHROPIC_API_KEY", "not set"))

    # ── Claude models in Ollama ───────────────────────────────────────────────
    # Runs `ollama list` and filters for any model with "claude" in the name
    if which("ollama") and http_ok("http://localhost:11434"):
        raw = run(["ollama", "list"])
        if raw:
            claude_models = [l for l in raw.splitlines() if "claude" in l.lower()]
            if claude_models:
                children = [make_item("info", m.split()[0], "") for m in claude_models]
                print(info(f"Claude models in Ollama: {len(claude_models)} found"), flush=True)
                items.append(make_item("ok", "Claude models in Ollama",
                                       f"{len(claude_models)} found", children))
            else:
                items.append(make_item("warn", "Claude models in Ollama", "none pulled locally"))

    return {"title": "Claude (Anthropic)", "items": items}

"""
scanner/mcp.py
--------------
Scans the MCP (Model Context Protocol) ecosystem:
  - MCP Python SDK
  - Node.js and npx  (most MCP servers are Node-based)
  - uv / uvx         (fast Python MCP server runner)
  - Docker           (some MCP servers run in containers)
  - Known MCP server packages (npm globals)
"""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import json

from utils import which, run, pkgver, make_item
from report.terminal import ok, warn, miss, print_header


# Well-known MCP server npm packages to check for
KNOWN_MCP_SERVERS = [
    "@modelcontextprotocol/server-filesystem",
    "@modelcontextprotocol/server-fetch",
    "@modelcontextprotocol/server-sqlite",
    "@modelcontextprotocol/server-github",
    "@modelcontextprotocol/server-brave-search",
    "mcp-server-git",
]


def scan() -> dict:
    print_header("MCP Ecosystem")
    items = []

    # ── MCP Python SDK ────────────────────────────────────────────────────────
    ver = pkgver("mcp")
    if ver:
        print(ok(f"MCP Python SDK : {ver}"), flush=True)
        items.append(make_item("ok", "MCP Python SDK", ver))
    else:
        print(miss("MCP Python SDK : not installed  ->  pip install mcp"), flush=True)
        items.append(make_item("miss", "MCP Python SDK", "pip install mcp"))

    # ── Node.js + npx ─────────────────────────────────────────────────────────
    # Most MCP servers ship as npm packages and run via npx.
    # Without Node.js you can only use Python-based MCP servers.
    node_ver = run(["node", "--version"])
    npx_path = which("npx")
    if node_ver:
        print(ok(f"Node.js : {node_ver}"), flush=True)
        items.append(make_item("ok", "Node.js", node_ver))
        items.append(make_item(
            "ok" if npx_path else "warn",
            "npx",
            npx_path or "not found"
        ))
    else:
        print(miss("Node.js : not installed  (most MCP servers need it)"), flush=True)
        items.append(make_item("miss", "Node.js", "not installed — most MCP servers need it"))

    # ── uv / uvx ─────────────────────────────────────────────────────────────
    # uvx lets you run Python MCP servers without installing them first.
    # Example: uvx mcp-server-git  (runs directly from PyPI)
    uv_ver = run(["uv", "--version"])
    if uv_ver:
        print(ok(f"uv / uvx : {uv_ver}"), flush=True)
        items.append(make_item("ok", "uv / uvx", uv_ver))
    else:
        print(miss("uv / uvx : not installed  ->  https://docs.astral.sh/uv/"), flush=True)
        items.append(make_item("miss", "uv / uvx", "not installed"))

    # ── Docker ────────────────────────────────────────────────────────────────
    docker_ver = run(["docker", "--version"])
    if docker_ver:
        print(ok(f"Docker : {docker_ver}"), flush=True)
        items.append(make_item("ok", "Docker", docker_ver))
    else:
        print(miss("Docker : not installed"), flush=True)
        items.append(make_item("miss", "Docker", "not installed"))

    # ── Known MCP server packages ─────────────────────────────────────────────
    # Check which well-known MCP servers are globally installed via npm.
    # `npm list -g --json` returns installed global packages as JSON.
    npm_globals: set = set()
    npm_raw = run(["npm", "list", "-g", "--depth=0", "--json"], timeout=10)
    if npm_raw:
        try:
            npm_globals = set(json.loads(npm_raw).get("dependencies", {}).keys())
        except Exception:
            pass

    server_children = []
    for pkg in KNOWN_MCP_SERVERS:
        if pkg in npm_globals:
            print(ok(f"  {pkg}"), flush=True)
            server_children.append(make_item("ok", pkg, "npm global install"))
        elif npx_path:
            print(warn(f"  {pkg}  (can run via npx, not pre-installed)"), flush=True)
            server_children.append(make_item("warn", pkg, "available via npx on demand"))
        else:
            print(miss(f"  {pkg}"), flush=True)
            server_children.append(make_item("miss", pkg, ""))

    items.append(make_item("info", "Known MCP server packages", "", server_children))

    return {"title": "MCP Ecosystem", "items": items}

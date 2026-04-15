"""
scanner/agent_frameworks.py
---------------------------
Scans for installed Python AI agent frameworks.
Detection method: importlib.find_spec() + importlib.metadata.version()
— no subprocess, no pip call, just Python's own package registry.
"""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from utils import pkgver, make_item
from report.terminal import ok, miss, print_header


# All frameworks to check: (pip_package_name, display_label)
FRAMEWORKS = [
    ("langchain",          "LangChain"),
    ("langchain-core",     "LangChain Core"),
    ("langgraph",          "LangGraph"),
    ("crewai",             "CrewAI"),
    ("autogen",            "AutoGen (AG2)"),
    ("pyautogen",          "PyAutoGen"),
    ("mcp-agent",          "mcp-agent"),
    ("mcp",                "MCP Python SDK"),
    ("openai-agents",      "OpenAI Agents SDK"),
    ("pydantic-ai",        "PydanticAI"),
    ("haystack-ai",        "Haystack"),
    ("llama-index",        "LlamaIndex"),
    ("llama-index-core",   "LlamaIndex Core"),
    ("smolagents",         "smolagents (HuggingFace)"),
    ("agno",               "Agno"),
    ("dspy-ai",            "DSPy"),
    ("semantic-kernel",    "Semantic Kernel"),
    ("upsonic",            "Upsonic"),
]


def scan() -> dict:
    print_header("Agent Frameworks (Python)")
    items = []
    found = False

    for pkg, label in FRAMEWORKS:
        ver = pkgver(pkg)
        if ver:
            found = True
            print(ok(f"{label:<30}: {ver}"), flush=True)
            items.append(make_item("ok", label, ver))

    if not found:
        print(miss("No agent frameworks detected"), flush=True)
        items.append(make_item(
            "miss",
            "No agent frameworks installed",
            "pip install mcp-agent  OR  pip install langgraph"
        ))

    return {"title": "Agent Frameworks (Python)", "items": items}

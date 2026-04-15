"""
permissions/framework_audit.py
-------------------------------
Documents what each AI agent framework can do by design.

This is NOT based on reading a config file.
It's a curated knowledge base of each framework's built-in capabilities.

The logic is: if CrewAI is installed on your machine, then by default
an agent using it CAN execute shell commands — because that's what
CrewAI's CodeInterpreterTool does out of the box, whether you
intended it or not.
"""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from utils import pkgver, make_item, make_risk
from report.terminal import print_subheader, print_risk, C, Z


# Knowledge base: framework name -> list of (risk_level, capability, explanation)
FRAMEWORK_CAPABILITIES = {
    "LangChain": [
        ("med",  "Tool use",         "Agents can call any tool registered at runtime"),
        ("med",  "Code execution",   "PythonREPLTool / BashTool available as built-ins"),
        ("med",  "File I/O",         "FileManagementToolkit: read, write, delete files"),
        ("med",  "Network",          "RequestsTool, WebBrowserTool, Tavily, SerpAPI built-in"),
        ("low",  "Memory",           "ConversationBufferMemory / VectorStore (local only)"),
    ],
    "LangGraph": [
        ("med",  "Tool use",         "Graph nodes can call any LangChain tool"),
        ("high", "Persistence",      "Checkpointing writes agent state to disk or DB across runs"),
        ("med",  "Human-in-loop",    "interrupt() can pause for human approval (opt-in)"),
    ],
    "CrewAI": [
        ("high", "Shell execution",  "CodeInterpreterTool runs Python/bash by default"),
        ("med",  "File I/O",         "FileReadTool / FileWriteTool in default toolkit"),
        ("med",  "Network",          "SerperDevTool, BrowserBaseTool built-in"),
        ("med",  "Multi-agent",      "Agents can delegate tasks to other agents"),
    ],
    "AutoGen / AG2": [
        ("high", "Code execution",   "UserProxyAgent executes LLM-generated code by default"),
        ("med",  "File I/O",         "Code execution implies full filesystem access"),
        ("med",  "Docker sandbox",   "Can isolate execution in Docker (opt-in only)"),
    ],
    "mcp-agent": [
        ("med",  "MCP tool use",     "Capabilities = sum of all connected MCP servers"),
        ("low",  "No built-in tools","All capabilities come from MCP servers (audited separately)"),
    ],
    "OpenAI Agents SDK": [
        ("med",  "Tool use",         "Any Python function or MCP server can be a tool"),
        ("med",  "Hosted tools",     "Code interpreter and file search run in OpenAI cloud"),
        ("low",  "Approval policy",  "Per-tool human approval available (opt-in)"),
    ],
    "PydanticAI": [
        ("med",  "Tool use",         "Type-safe tools — any Python function can be registered"),
        ("low",  "Human approval",   "Tool call approval hooks available"),
        ("med",  "MCP support",      "Can connect MCP servers — permissions inherit from server"),
    ],
    "LlamaIndex": [
        ("med",  "Tool use",         "QueryEngineTools, FunctionTools can call anything"),
        ("med",  "File I/O",         "SimpleDirectoryReader, document stores"),
        ("med",  "Code execution",   "CodeInterpreterTool available"),
    ],
    "smolagents": [
        ("high", "Code execution",   "CodeAgent writes and executes Python by default"),
        ("med",  "Tool use",         "ToolCallingAgent calls registered tools"),
        ("med",  "Network",          "VisitWebpageTool, SearchTool built-in"),
    ],
}

# Map pip package name -> display name in FRAMEWORK_CAPABILITIES
PACKAGE_TO_FRAMEWORK = {
    "langchain":        "LangChain",
    "langgraph":        "LangGraph",
    "crewai":           "CrewAI",
    "autogen":          "AutoGen / AG2",
    "pyautogen":        "AutoGen / AG2",
    "mcp-agent":        "mcp-agent",
    "openai-agents":    "OpenAI Agents SDK",
    "pydantic-ai":      "PydanticAI",
    "llama-index-core": "LlamaIndex",
    "llama-index":      "LlamaIndex",
    "smolagents":       "smolagents",
}


def scan_installed() -> list[dict]:
    """
    For each installed agent framework, print and return its capability profile.
    """
    print_subheader("Agent Framework Capabilities")

    items   = []
    audited = set()
    found   = False

    for pkg, framework_name in PACKAGE_TO_FRAMEWORK.items():
        if framework_name in audited:
            continue
        if not pkgver(pkg):
            continue

        audited.add(framework_name)
        found = True

        caps  = FRAMEWORK_CAPABILITIES.get(framework_name, [])
        risks = [make_risk(lvl, lbl, det) for lvl, lbl, det in caps]

        print(f"\n  {C}>> {framework_name}{Z}", flush=True)
        for lvl, lbl, det in caps:
            print_risk(lvl, lbl, det)

        if not caps:
            risks = [make_risk("info", "No detailed profile", "Review framework docs")]

        items.append(make_item("info", framework_name, "", risks))

    if not found:
        print(f"\n  No agent frameworks installed.", flush=True)
        items.append(make_item("warn", "No agent frameworks installed", ""))

    return items

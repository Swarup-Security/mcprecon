"""
scanner/api_keys.py
-------------------
Checks which AI provider API keys are set in your environment.

Detection method: os.environ.get(KEY_NAME)
  — same as typing `echo $ANTHROPIC_API_KEY` in your terminal.
  — never contacts any server to validate the key.
  — shows a masked version (first 4 + last 4 chars) if set.
"""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import os

from utils import make_item
from report.terminal import ok, miss, print_header


# (environment_variable_name, display_label)
API_KEYS = [
    ("ANTHROPIC_API_KEY",     "Anthropic (Claude)"),
    ("OPENAI_API_KEY",        "OpenAI"),
    ("GOOGLE_API_KEY",        "Google (Gemini)"),
    ("MISTRAL_API_KEY",       "Mistral"),
    ("GROQ_API_KEY",          "Groq"),
    ("COHERE_API_KEY",        "Cohere"),
    ("HUGGINGFACE_HUB_TOKEN", "HuggingFace Hub"),
    ("TOGETHER_API_KEY",      "Together AI"),
    ("BRAVE_SEARCH_API_KEY",  "Brave Search (MCP)"),
    ("GITHUB_TOKEN",          "GitHub (MCP)"),
]


def scan() -> dict:
    print_header("API Keys (environment)")
    items = []

    for env_var, label in API_KEYS:
        value = os.environ.get(env_var)
        if value:
            # Mask the key — show enough to identify it, not enough to steal it
            masked = value[:4] + "****" + value[-4:] if len(value) > 8 else "****"
            print(ok(f"{label:<30}: {masked}"), flush=True)
            items.append(make_item("ok", label, masked))
        else:
            print(miss(f"{label:<30}: not set"), flush=True)
            items.append(make_item("miss", label, "not set"))

    return {"title": "API Keys (environment)", "items": items}

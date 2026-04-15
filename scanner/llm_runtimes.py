"""
scanner/llm_runtimes.py
-----------------------
Scans local LLM runtimes and model caches:
  - Ollama  (binary + running API + pulled models)
  - LM Studio (app + running API + model cache)
  - Jan (app + running API)
  - GPT4All (Python package + model cache)
  - llama.cpp (Python bindings or binary)
  - vLLM (Python package + running API)
  - HuggingFace Transformers (package + hub cache)
  - Cloud SDKs: OpenAI, Google Gemini, Mistral
"""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import os
from pathlib import Path

from utils import which, run, pkgver, http_ok, dir_count_gb, make_item
from report.terminal import ok, warn, miss, info, print_header, G, D, Z


def scan() -> dict:
    print_header("Local LLM Runtimes & SDKs")
    items = []

    # ── Ollama ────────────────────────────────────────────────────────────────
    # 1. which("ollama")  → is the binary on PATH?
    # 2. http_ok(...)     → is the API server actually running?
    # 3. run(["ollama","list"]) → what models are pulled?
    ollama_bin = which("ollama")
    if ollama_bin:
        ver = run(["ollama", "--version"])
        children = []
        print(ok(f"Ollama : {ver or 'found'} @ {ollama_bin}"), flush=True)

        if http_ok("http://localhost:11434"):
            children.append(make_item("ok", "API", "running on http://localhost:11434"))
            raw = run(["ollama", "list"])
            if raw:
                lines = [l for l in raw.splitlines() if l and not l.startswith("NAME")]
                model_items = []
                for l in lines:
                    parts = l.split()
                    name  = parts[0] if parts else l
                    size  = " ".join(parts[2:4]) if len(parts) > 3 else ""
                    model_items.append(make_item("info", name, size))
                    print(f"      {G}*{Z} {name}  {D}{size}{Z}", flush=True)
                children.append(make_item("ok", f"Models ({len(lines)})", "", model_items))
        else:
            children.append(make_item("warn", "API not running", "run: ollama serve"))
            print(warn("  Ollama API not running  ->  ollama serve"), flush=True)

        items.append(make_item("ok", "Ollama", ver or "found", children))
    else:
        print(miss("Ollama : not installed"), flush=True)
        items.append(make_item("miss", "Ollama", "not installed"))

    # ── LM Studio ─────────────────────────────────────────────────────────────
    # LM Studio is a GUI app — check known install paths per OS
    lms_paths = [
        Path.home() / "Applications/LM Studio.app",  # macOS
        Path("/opt/LM Studio"),
    ]
    if any(p.exists() for p in lms_paths) or which("lms"):
        children = []
        print(ok("LM Studio : installed"), flush=True)

        if http_ok("http://localhost:1234/v1/models"):
            children.append(make_item("ok", "API", "running on http://localhost:1234 (OpenAI-compatible)"))
            print(ok("  LM Studio API running on http://localhost:1234"), flush=True)
        else:
            children.append(make_item("warn", "API not running", "enable in LM Studio -> Local Server tab"))

        # Model cache
        model_dir = Path.home() / ".cache/lm-studio/models"
        if not model_dir.exists():
            model_dir = Path.home() / ".lmstudio/models"
        if model_dir.exists():
            n, gb = dir_count_gb(model_dir, [".gguf", ".bin", ".safetensors"])
            children.append(make_item("info", "Models", f"{n} files, {gb:.1f} GB"))
            print(info(f"  LM Studio models: {n} files, {gb:.1f} GB"), flush=True)

        items.append(make_item("ok", "LM Studio", "installed", children))
    else:
        print(miss("LM Studio : not installed"), flush=True)
        items.append(make_item("miss", "LM Studio", "not installed"))

    # ── Jan ───────────────────────────────────────────────────────────────────
    jan_paths = [Path.home() / "Applications/Jan.app"]
    if any(p.exists() for p in jan_paths) or which("jan"):
        children = []
        print(ok("Jan : installed"), flush=True)
        if http_ok("http://localhost:1337/v1/models"):
            children.append(make_item("ok", "API", "running on http://localhost:1337"))
        items.append(make_item("ok", "Jan", "installed", children))
    else:
        print(miss("Jan : not installed"), flush=True)
        items.append(make_item("miss", "Jan", "not installed"))

    # ── GPT4All ───────────────────────────────────────────────────────────────
    ver = pkgver("gpt4all")
    if ver:
        children = []
        cache = Path.home() / ".cache/gpt4all"
        if cache.exists():
            n, gb = dir_count_gb(cache, [".gguf", ".bin"])
            children.append(make_item("info", "Models", f"{n} files, {gb:.1f} GB"))
        print(ok(f"GPT4All : {ver}"), flush=True)
        items.append(make_item("ok", "GPT4All", ver, children))
    else:
        print(miss("GPT4All : not installed"), flush=True)
        items.append(make_item("miss", "GPT4All", "not installed"))

    # ── llama.cpp ─────────────────────────────────────────────────────────────
    # Either the Python bindings (llama-cpp-python) or the compiled binary
    lv = pkgver("llama-cpp-python")
    lb = which("llama-cli") or which("llama-server")
    if lv:
        print(ok(f"llama-cpp-python : {lv}"), flush=True)
        items.append(make_item("ok", "llama-cpp-python", lv))
    elif lb:
        print(ok(f"llama.cpp binary : {lb}"), flush=True)
        items.append(make_item("ok", "llama.cpp binary", lb))
    else:
        print(miss("llama.cpp : not installed"), flush=True)
        items.append(make_item("miss", "llama.cpp", "not installed"))

    # ── vLLM ──────────────────────────────────────────────────────────────────
    ver = pkgver("vllm")
    if ver:
        children = []
        if http_ok("http://localhost:8000/v1/models"):
            children.append(make_item("ok", "API", "running on http://localhost:8000"))
        print(ok(f"vLLM : {ver}"), flush=True)
        items.append(make_item("ok", "vLLM", ver, children))
    else:
        print(miss("vLLM : not installed"), flush=True)
        items.append(make_item("miss", "vLLM", "not installed"))

    # ── HuggingFace Transformers + model cache ────────────────────────────────
    # When you download models via HuggingFace, they go into ~/.cache/huggingface/hub/
    # Each model is stored as a folder named  models--author--modelname
    ver = pkgver("transformers")
    if ver:
        children = []
        hf_home  = Path(os.environ.get("HF_HOME", str(Path.home() / ".cache/huggingface")))
        hub_dir  = hf_home / "hub"

        if hub_dir.exists():
            model_dirs = [d for d in hub_dir.iterdir()
                          if d.is_dir() and d.name.startswith("models--")]
            total_gb   = sum(
                f.stat().st_size for d in model_dirs
                for f in d.rglob("*") if f.is_file()
            ) / 1_073_741_824

            model_items = [
                make_item("info", d.name.replace("models--", "").replace("--", "/"), "")
                for d in model_dirs[:15]
            ]
            children.append(make_item(
                "info",
                f"HF Hub cache ({len(model_dirs)} models, {total_gb:.1f} GB)",
                str(hub_dir),
                model_items
            ))
            print(info(f"  HF cache: {len(model_dirs)} models, {total_gb:.1f} GB"), flush=True)

        print(ok(f"HuggingFace Transformers : {ver}"), flush=True)
        items.append(make_item("ok", "HuggingFace Transformers", ver, children))
    else:
        print(miss("HuggingFace Transformers : not installed"), flush=True)
        items.append(make_item("miss", "HuggingFace Transformers", "not installed"))

    # ── Cloud provider SDKs ───────────────────────────────────────────────────
    for pkg, label in [
        ("openai",              "OpenAI SDK"),
        ("google-generativeai", "Google Gemini SDK"),
        ("mistralai",           "Mistral SDK"),
    ]:
        ver = pkgver(pkg)
        if ver:
            print(ok(f"{label} : {ver}"), flush=True)
            items.append(make_item("ok", label, ver))

    return {"title": "Local LLM Runtimes & SDKs", "items": items}

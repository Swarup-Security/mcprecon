"""
scanner/gpu.py
--------------
Scans hardware acceleration:
  - NVIDIA GPU via nvidia-smi
  - CUDA via nvcc
  - AMD ROCm via rocminfo
  - Apple Silicon (Metal/MPS) via sysctl
  - PyTorch and its CUDA/MPS availability
"""
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import platform

from utils import run, which, pkgver, make_item
from report.terminal import ok, miss, print_header


def scan() -> dict:
    print_header("GPU / Hardware Acceleration")
    items = []

    # ── NVIDIA GPU ────────────────────────────────────────────────────────────
    # `nvidia-smi` is NVIDIA's System Management Interface — always present
    # if NVIDIA drivers are installed. We ask it for GPU name + memory.
    smi = run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"])
    if smi:
        for gpu in smi.splitlines():
            print(ok(f"NVIDIA GPU : {gpu.strip()}"), flush=True)
            items.append(make_item("ok", "NVIDIA GPU", gpu.strip()))
        # CUDA version from nvcc (NVIDIA compiler)
        nvcc = run(["nvcc", "--version"])
        if nvcc:
            ver = next((l for l in nvcc.splitlines() if "release" in l.lower()), "")
            items.append(make_item("ok", "CUDA", ver.strip()))
            print(ok(f"CUDA : {ver.strip()}"), flush=True)
    else:
        print(miss("NVIDIA GPU / CUDA : not detected"), flush=True)
        items.append(make_item("miss", "NVIDIA GPU / CUDA", "not detected"))

    # ── Apple Silicon ─────────────────────────────────────────────────────────
    # On macOS, `sysctl -n machdep.cpu.brand_string` returns the chip name.
    # Apple Silicon chips (M1/M2/M3/M4) support Metal Performance Shaders (MPS)
    # which PyTorch uses for GPU acceleration on Mac.
    if platform.system() == "Darwin":
        chip = run(["sysctl", "-n", "machdep.cpu.brand_string"])
        if chip and "Apple" in chip:
            print(ok(f"Apple Silicon (MPS) : {chip}"), flush=True)
            items.append(make_item("ok", "Apple Silicon (MPS)", chip))
        else:
            print(miss("Apple Silicon : Intel Mac (no MPS)"), flush=True)
            items.append(make_item("miss", "Apple Silicon", "Intel Mac — no MPS"))
    else:
        # ── AMD ROCm (Linux/Windows only) ─────────────────────────────────────
        rocm = run(["rocminfo"])
        if rocm and "Agent" in rocm:
            print(ok("AMD ROCm : detected"), flush=True)
            items.append(make_item("ok", "AMD ROCm", "detected"))
        else:
            print(miss("AMD ROCm : not detected"), flush=True)
            items.append(make_item("miss", "AMD ROCm", "not detected"))

    # ── PyTorch ───────────────────────────────────────────────────────────────
    # PyTorch is the most common ML framework. We check:
    #   - Is it installed at all?
    #   - Can it see a CUDA GPU?
    #   - Can it use Apple's MPS?
    try:
        import torch
        cuda = torch.cuda.is_available()
        detail = f"{torch.__version__}  CUDA={cuda}"
        print(ok(f"PyTorch : {detail}"), flush=True)
        items.append(make_item("ok", "PyTorch", detail))

        if platform.system() == "Darwin":
            mps = torch.backends.mps.is_available()
            status = "ok" if mps else "warn"
            items.append(make_item(status, "PyTorch MPS", str(mps)))
    except ImportError:
        print(miss("PyTorch : not installed"), flush=True)
        items.append(make_item("miss", "PyTorch", "not installed"))

    return {"title": "GPU / Hardware Acceleration", "items": items}

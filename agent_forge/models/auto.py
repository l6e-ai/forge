from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Tuple
import os
import platform
import re
import shutil
import socket
import subprocess
import json
from pathlib import Path


@dataclass
class SystemProfile:
    os: str
    cpu_cores: int
    ram_gb: float
    vram_gb: float
    has_gpu: bool
    has_internet: bool
    has_ollama: bool


def _bytes_to_gb(b: int) -> float:
    return round(b / (1024**3), 1)


def _get_ram_gb(sys_name: str) -> float:
    # Prefer psutil if available
    try:
        import psutil  # type: ignore

        return _bytes_to_gb(psutil.virtual_memory().total)
    except Exception:
        pass
    # macOS via sysctl
    if sys_name == "darwin":
        try:
            out = subprocess.check_output(["/usr/sbin/sysctl", "-n", "hw.memsize"], stderr=subprocess.DEVNULL)
            return _bytes_to_gb(int(out.strip()))
        except Exception:
            return 0.0
    # Linux via /proc/meminfo
    if sys_name == "linux":
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(re.findall(r"(\d+)", line)[0])
                        return round(kb / (1024**2), 1)
        except Exception:
            return 0.0
    return 0.0


def _detect_gpu(sys_name: str, ram_gb: float) -> Tuple[bool, float]:
    # NVIDIA (Linux/macOS with CUDA)
    try:
        if shutil.which("nvidia-smi"):
            out = subprocess.check_output(
                [
                    "nvidia-smi",
                    "--query-gpu=memory.total",
                    "--format=csv,noheader,nounits",
                ],
                stderr=subprocess.DEVNULL,
            ).decode().strip()
            # Take the max across GPUs
            vals = [int(v) for v in out.splitlines() if v.strip().isdigit()]
            if vals:
                return True, round(max(vals) / 1024.0, 1)
    except Exception:
        pass

    # macOS: use system_profiler to detect Metal GPU and unified memory VRAM report
    if sys_name == "darwin":
        try:
            out = subprocess.check_output([
                "/usr/sbin/system_profiler",
                "-json",
                "SPDisplaysDataType",
            ], stderr=subprocess.DEVNULL)
            data = json.loads(out.decode())
            displays = data.get("SPDisplaysDataType", [])
            # Look for VRAM fields
            vram_gb = 0.0
            for d in displays:
                for key in ("spdisplays_vram", "spdisplays_vram_shared"):
                    val = d.get(key)
                    if isinstance(val, str):
                        m = re.search(r"(\d+)\s*GB", val)
                        if m:
                            vram_gb = max(vram_gb, float(m.group(1)))
            if displays:
                # If VRAM not explicitly reported (common on Apple Silicon), estimate
                if vram_gb <= 0.0 and platform.machine().lower() in ("arm64", "aarch64"):
                    # Unified memory: assume ~75% of RAM can be used by GPU
                    est = round(max(ram_gb * 0.75, 0.0), 1)
                    return True, est
                return True, vram_gb if vram_gb > 0 else 0.0
        except Exception:
            # On Apple Silicon, assume Metal-capable integrated GPU even if VRAM unknown
            if platform.machine().lower() in ("arm64", "aarch64"):
                est = round(max(ram_gb * 0.75, 0.0), 1) if ram_gb > 0 else 0.0
                return True, est
    return False, 0.0


def _has_internet_quick(timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection(("1.1.1.1", 53), timeout=timeout):
            return True
    except Exception:
        return False


def get_system_profile() -> SystemProfile:
    sys_name = platform.system().lower()
    cores = os.cpu_count() or 1
    ram_gb = _get_ram_gb(sys_name)
    has_gpu, vram_gb = _detect_gpu(sys_name, ram_gb)
    has_internet = _has_internet_quick()
    has_ollama = shutil.which("ollama") is not None
    return SystemProfile(sys_name, cores, ram_gb, vram_gb, has_gpu, has_internet, has_ollama)


@dataclass
class AutoHints:
    provider_order: list[str]
    task: Literal["assistant", "coder", "tool-use"] = "assistant"
    quality: Literal["speed", "balanced", "quality"] = "balanced"
    context: int = 8192


def recommend_models(sys: SystemProfile, hints: AutoHints) -> dict[str, str]:
    # Very basic matrix for thin slice
    chat = "llama3.2:3b"
    embed = "nomic-embed-text:latest"
    if sys.has_gpu and sys.vram_gb >= 8:
        chat = "llama3.1:8b-instruct"
    return {"chat": chat, "embedding": embed}


def _ollama_list_models(endpoint: str = "http://localhost:11434") -> list[str]:
    try:
        import httpx

        resp = httpx.get(f"{endpoint.rstrip('/')}/api/tags", timeout=5.0)
        resp.raise_for_status()
        items = resp.json().get("models", [])
        names: list[str] = []
        for it in items:
            n = it.get("name") or it.get("model")
            if isinstance(n, str):
                names.append(n)
        return names
    except Exception:
        return []


def _maybe_pull_model(name: str) -> None:
    try:
        subprocess.run(["ollama", "pull", name], check=True)
    except Exception:
        pass


def ensure_ollama_models(models: dict[str, str], endpoint: str = "http://localhost:11434") -> dict[str, str]:
    """Ensure models exist; return possibly adjusted names that actually exist.

    For example, if "llama3.1:8b-instruct" is unavailable but "llama3.1:8b" exists,
    this returns {"chat": "llama3.1:8b", ...} and pulls that tag.
    """
    resolved: dict[str, str] = {}
    existing = set(_ollama_list_models(endpoint))

    def candidates(name: str) -> list[str]:
        c = [name]
        # Common alternates
        if name.endswith(":8b-instruct"):
            c.append(name.replace(":8b-instruct", ":8b"))
        if name.endswith(":3b-instruct"):
            c.append(name.replace(":3b-instruct", ":3b"))
        # If name has no explicit tag, try ":latest"
        if ":" not in name:
            c.append(name + ":latest")
        return c

    for role, name in models.items():
        found = None
        for cand in candidates(name):
            if cand not in existing:
                _maybe_pull_model(cand)
                existing = set(_ollama_list_models(endpoint))
            if cand in existing:
                found = cand
                break
        resolved[role] = found or name
    return resolved


# -----------------------------
# Config application utilities
# -----------------------------

def _quote_toml(v: object) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, list):
        return "[" + ", ".join(_quote_toml(x) for x in v) + "]"
    return '"' + str(v).replace('\\', '\\\\').replace('"', '\\"') + '"'


def _write_toml(data: dict) -> str:
    lines: list[str] = []

    def emit_table(path: list[str], obj: dict) -> None:
        # Emit header for non-root tables
        if path:
            lines.append("[" + ".".join(path) + "]")
        # First scalars
        for k, v in obj.items():
            if not isinstance(v, dict):
                lines.append(f"{k} = {_quote_toml(v)}")
        # Then subtables
        for k, v in obj.items():
            if isinstance(v, dict):
                lines.append("")
                emit_table(path + [k], v)

    # Top-level: iterate keys to keep sections grouped
    scalars_top = {k: v for k, v in data.items() if not isinstance(v, dict)}
    tables_top = {k: v for k, v in data.items() if isinstance(v, dict)}
    # Emit top-level scalars if any
    for k, v in scalars_top.items():
        lines.append(f"{k} = {_quote_toml(v)}")
    if scalars_top and tables_top:
        lines.append("")
    for k, v in tables_top.items():
        emit_table([k], v)
    return "\n".join(lines) + "\n"


def apply_recommendations_to_agent_config(agent_dir: Path, provider: str, recs: dict[str, str]) -> None:
    cfg_path = Path(agent_dir) / "config.toml"
    data: dict = {}
    if cfg_path.exists():
        try:
            import tomllib

            with cfg_path.open("rb") as f:
                data = tomllib.load(f) or {}
        except Exception:
            data = {}
    # Ensure sections
    model = data.get("model") or {}
    memory = data.get("memory") or {}
    # Update selections
    model["provider"] = provider
    model["model"] = recs.get("chat")
    memory["embedding_model"] = recs.get("embedding")
    # Persist
    data["model"] = model
    data["memory"] = memory
    # Write with minimal TOML emitter
    content = _write_toml(data)
    cfg_path.write_text(content, encoding="utf-8")



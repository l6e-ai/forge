from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal, Tuple, Optional, List, Dict
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
            out = subprocess.check_output(
                ["/usr/sbin/sysctl", "-n", "hw.memsize"], stderr=subprocess.DEVNULL
            )
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
            out = (
                subprocess.check_output(
                    [
                        "nvidia-smi",
                        "--query-gpu=memory.total",
                        "--format=csv,noheader,nounits",
                    ],
                    stderr=subprocess.DEVNULL,
                )
                .decode()
                .strip()
            )
            # Take the max across GPUs
            vals = [int(v) for v in out.splitlines() if v.strip().isdigit()]
            if vals:
                return True, round(max(vals) / 1024.0, 1)
    except Exception:
        pass

    # macOS: use system_profiler to detect Metal GPU and unified memory VRAM report
    if sys_name == "darwin":
        try:
            profiler_output = subprocess.check_output(
                [
                    "/usr/sbin/system_profiler",
                    "-json",
                    "SPDisplaysDataType",
                ],
                stderr=subprocess.DEVNULL,
            )
            data = json.loads(profiler_output.decode())
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
                if vram_gb <= 0.0 and platform.machine().lower() in (
                    "arm64",
                    "aarch64",
                ):
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
    return SystemProfile(
        sys_name, cores, ram_gb, vram_gb, has_gpu, has_internet, has_ollama
    )


class AutoHintTask(StrEnum):
    ASSISTANT = "assistant"
    CODER = "coder"
    TOOL_USE = "tool-use"


class AutoHintQuality(StrEnum):
    SPEED = "speed"
    BALANCED = "balanced"
    QUALITY = "quality"


class AutoHintQuantization(StrEnum):
    AUTO = "auto"
    Q4 = "q4"
    Q5 = "q5"
    Q8 = "q8"
    MXFP4 = "mxfp4"
    BIT = "8bit"


@dataclass
class AutoHints:
    provider_order: list[str]
    task: AutoHintTask = AutoHintTask.ASSISTANT
    quality: AutoHintQuality = AutoHintQuality.BALANCED
    context: int = 8192
    quantization: AutoHintQuantization = AutoHintQuantization.AUTO


def recommend_models(sys: SystemProfile, hints: AutoHints) -> dict[str, str]:
    # Very basic matrix for thin slice
    chat = "llama3.2:3b"
    embed = "nomic-embed-text:latest"
    if sys.has_gpu and sys.vram_gb >= 8:
        chat = "llama3.1:8b-instruct"
    return {"chat": chat, "embedding": embed}


# -----------------------------
# Model catalog and estimation
# -----------------------------


@dataclass
class ModelCatalogEntry:
    model_key: str  # canonical name, e.g., "llama3.2-3b", "gpt-oss-20b"
    display_name: str  # human-friendly
    role: Literal["chat", "embedding"]
    params_b: Optional[float] = None  # total params in billions
    active_params_b: Optional[float] = None  # for MoE
    context_length: int = 8192
    # Approx artifact size in GB if known (quantized). If provided, we prefer using this.
    artifact_size_gb: Optional[float] = None
    # Provider mapping: provider -> tag/id used by that provider
    providers: Dict[str, str] = field(
        default_factory=dict
    )  # e.g., {"ollama": "llama3.2:3b"}
    notes: Optional[str] = None
    # Optional quantized artifact sizes (GB) if known
    quantized_artifacts_gb: Optional[Dict[str, float]] = (
        None  # e.g., {"q4": 5.0, "q8": 9.5}
    )
    # Optional provider-specific quantized sizes (GB), e.g., {"lmstudio": {"mxfp4": 63.4}}
    provider_quantized_artifacts_gb: Optional[Dict[str, Dict[str, float]]] = None


def get_model_catalog() -> List[ModelCatalogEntry]:
    """Return a curated list of common OSS models, including new GPT-OSS models.

    Notes:
    - artifact_size_gb values are rough and may vary by quantization.
    - gpt-oss models are MoE; active_params_b reflects per-token active parameters.
    """
    catalog: List[ModelCatalogEntry] = [
        ModelCatalogEntry(
            model_key="llama3.2-3b",
            display_name="Llama 3.2 3B Instruct",
            role="chat",
            params_b=3.2,
            context_length=8192,
            artifact_size_gb=2.5,  # ~Q4 estimate
            providers={"ollama": "llama3.2:3b"},
            notes="Good baseline for CPUs/AS chips",
            quantized_artifacts_gb={"q4": 2.2, "q5": 2.8, "q8": 3.6},
        ),
        ModelCatalogEntry(
            model_key="llama3.1-8b",
            display_name="Llama 3.1 8B Instruct",
            role="chat",
            params_b=8.0,
            context_length=8192,
            artifact_size_gb=5.5,  # ~Q4 estimate
            providers={"ollama": "llama3.1:8b-instruct"},
            notes="Faster on GPUs; okay on M-series",
            quantized_artifacts_gb={"q4": 4.8, "q5": 6.1, "q8": 9.7},
        ),
        ModelCatalogEntry(
            model_key="gpt-oss-20b",
            display_name="GPT-OSS 20B (MoE)",
            role="chat",
            params_b=21.0,
            active_params_b=3.6,
            context_length=8192,
            artifact_size_gb=None,  # derive from active params
            providers={"lmstudio": "gpt-oss-20b", "ollama": "gpt-oss:20b"},
            notes="MoE: ~3.6B active params; good quality for local high-end",
            # From LM Studio (screenshot): MXFP4 ~12.11GB, 8BIT ~22.26GB
            quantized_artifacts_gb={"mxfp4": 12.1, "8bit": 22.3},
            provider_quantized_artifacts_gb={
                "ollama": {"mxfp4": 14.0},  # page lists ~14GB
            },
        ),
        ModelCatalogEntry(
            model_key="gpt-oss-120b",
            display_name="GPT-OSS 120B (MoE)",
            role="chat",
            params_b=117.0,
            active_params_b=5.1,
            context_length=8192,
            artifact_size_gb=None,  # derive; typically needs high-end GPU
            providers={"lmstudio": "gpt-oss-120b", "ollama": "gpt-oss:120b"},
            notes="MoE: ~5.1B active params; requires powerful GPU",
            # From LM Studio (screenshot): MXFP4 ~63.39GB, 8BIT ~124.20GB
            quantized_artifacts_gb={"mxfp4": 63.4, "8bit": 124.2},
            provider_quantized_artifacts_gb={
                "ollama": {"mxfp4": 65.0},  # page lists ~65GB
            },
        ),
        ModelCatalogEntry(
            model_key="nomic-embed-text",
            display_name="Nomic Embed Text",
            role="embedding",
            params_b=None,
            context_length=8192,
            artifact_size_gb=0.5,
            providers={"ollama": "nomic-embed-text:latest"},
            notes="Solid general-purpose embedding model",
        ),
        # # Additional chat models with quantized size approximations
        # ModelCatalogEntry(
        #     model_key="mistral-7b",
        #     display_name="Mistral 7B Instruct",
        #     role="chat",
        #     params_b=7.0,
        #     context_length=8192,
        #     providers={"ollama": "mistral:7b-instruct"},
        #     notes="Well-rounded 7B; strong CPU/GPU performance",
        #     quantized_artifacts_gb={"q4": 4.1, "q5": 5.4, "q8": 9.5},
        # ),
        # ModelCatalogEntry(
        #     model_key="mixtral-8x7b",
        #     display_name="Mixtral 8x7B Instruct (MoE)",
        #     role="chat",
        #     params_b=46.7,
        #     active_params_b=12.0,
        #     context_length=8192,
        #     providers={"ollama": "mixtral:8x7b-instruct"},
        #     notes="MoE: high quality; larger on disk; 2 experts active",
        #     # Disk artifacts are large despite MoE; estimates reflect typical q-sizes
        #     quantized_artifacts_gb={"q4": 26.0, "q5": 33.0, "q8": 55.0},
        # ),
        # ModelCatalogEntry(
        #     model_key="qwen2.5-7b",
        #     display_name="Qwen2.5 7B Instruct",
        #     role="chat",
        #     params_b=7.0,
        #     context_length=8192,
        #     providers={"ollama": "qwen2.5:7b-instruct"},
        #     notes="Competitive 7B with good reasoning for its size",
        #     quantized_artifacts_gb={"q4": 4.5, "q5": 6.0, "q8": 10.5},
        # ),
        # ModelCatalogEntry(
        #     model_key="qwen2.5-14b",
        #     display_name="Qwen2.5 14B Instruct",
        #     role="chat",
        #     params_b=14.0,
        #     context_length=8192,
        #     providers={"ollama": "qwen2.5:14b-instruct"},
        #     notes="Higher quality; prefers GPU with >12GB VRAM",
        #     quantized_artifacts_gb={"q4": 9.0, "q5": 11.5, "q8": 19.0},
        # ),
        # ModelCatalogEntry(
        #     model_key="gemma2-2b",
        #     display_name="Gemma 2 2B Instruct",
        #     role="chat",
        #     params_b=2.0,
        #     context_length=8192,
        #     providers={"ollama": "gemma2:2b-instruct"},
        #     notes="Tiny footprint; great for constrained environments",
        #     quantized_artifacts_gb={"q4": 1.5, "q5": 1.9, "q8": 3.1},
        # ),
        # ModelCatalogEntry(
        #     model_key="gemma2-9b",
        #     display_name="Gemma 2 9B Instruct",
        #     role="chat",
        #     params_b=9.0,
        #     context_length=8192,
        #     providers={"ollama": "gemma2:9b-instruct"},
        #     notes="Balanced quality; good on modern GPUs",
        #     quantized_artifacts_gb={"q4": 5.5, "q5": 7.2, "q8": 11.5},
        # ),
    ]
    return catalog


def estimate_memory_gb(
    entry: ModelCatalogEntry,
    quantization: AutoHintQuantization = AutoHintQuantization.AUTO,
    overhead_ratio: float = 0.25,
    provider: Optional[str] = None,
) -> float:
    """Estimate runtime memory footprint in GB.

    Strategy:
    - If artifact_size_gb provided, use: size * (1 + overhead_ratio)
    - Else, base on active_params_b (for MoE) or params_b (full) with bytes/param
      determined by weight_precision_bits (8 -> 1 byte, 16 -> 2 bytes, 4 -> 0.5 bytes).
      Then multiply by (1 + overhead_ratio).
    This is a rough estimate; actual memory will vary by runtime.
    """
    # Prefer quantized artifact size if provided
    if (
        quantization != "auto"
        and entry.provider_quantized_artifacts_gb
        and provider
        and quantization in entry.provider_quantized_artifacts_gb.get(provider, {})
    ):
        base = entry.provider_quantized_artifacts_gb[provider][quantization]
    elif (
        quantization != "auto"
        and entry.quantized_artifacts_gb
        and quantization in entry.quantized_artifacts_gb
    ):
        base = entry.quantized_artifacts_gb[quantization]
    elif quantization == "auto" and (
        entry.provider_quantized_artifacts_gb or entry.quantized_artifacts_gb
    ):
        # Choose a sensible default based on provider or smallest known quant
        preferred_order = ["mxfp4", "q4", "q5", "q8", "8bit"]
        source_map = None
        if (
            provider
            and entry.provider_quantized_artifacts_gb
            and provider in entry.provider_quantized_artifacts_gb
        ):
            source_map = entry.provider_quantized_artifacts_gb[provider]
        else:
            source_map = entry.quantized_artifacts_gb or {}
        for q in preferred_order:
            if q in source_map:
                base = source_map[q]
                break
    elif entry.artifact_size_gb is not None:
        base = entry.artifact_size_gb
    else:
        params_b = entry.active_params_b or entry.params_b or 0.0
        # Map quantization to bytes/param (rough)
        if quantization == "q4":
            bytes_per_param = 0.5
        elif quantization == "q5":
            bytes_per_param = 0.625
        elif quantization in ("q8", "8bit"):
            bytes_per_param = 1.0
        elif quantization == "mxfp4":
            bytes_per_param = 0.5  # treat similar to q4 for rough estimate
        else:  # auto fallback when no catalog sizes
            bytes_per_param = 1.0
        base = params_b * bytes_per_param  # rough GB since params_b is in billions
    return round(base * (1.0 + overhead_ratio), 1)


@dataclass
class ModelSuggestion:
    entry: ModelCatalogEntry
    provider: str
    provider_tag: Optional[str]
    est_memory_gb: float
    fits_local: bool
    reason: str
    estimate_source: Literal["installed", "catalog", "estimate"]
    is_installed: bool
    provider_available: bool
    mem_capacity_gb: float
    mem_capacity_type: Literal["vram", "ram"]
    mem_pct: int


def suggest_models(
    sys: SystemProfile, hints: AutoHints, top_n: int = 5
) -> List[ModelSuggestion]:
    """Return a list of suggested models with rough memory estimates and fit.

    We filter by role=chat for now and order by a simple score that prefers
    models that fit local hardware and align with quality hints.
    """
    suggestions: List[ModelSuggestion] = []
    # Detect installed/available providers
    installed_ollama_sizes: Dict[str, float] = {}
    ollama_available = False
    try:
        installed_ollama_sizes = _ollama_list_models_with_sizes()
        ollama_available = True
    except Exception:
        installed_ollama_sizes = {}

    installed_lmstudio: List[str] = []
    lmstudio_available = False
    try:
        installed_lmstudio = _lmstudio_list_models()
        lmstudio_available = True
    except Exception:
        installed_lmstudio = []

    for entry in get_model_catalog():
        if entry.role != "chat" or not entry.providers:
            continue
        # Consider all providers for this entry
        for provider_name, provider_tag in entry.providers.items():
            provider_up = (provider_name == "ollama" and ollama_available) or (
                provider_name == "lmstudio" and lmstudio_available
            )
            if not provider_up:
                continue

            # Base suggestion using catalog tag
            base_tag = provider_tag
            base_est = estimate_memory_gb(
                entry, quantization=hints.quantization, provider=provider_name
            )
            base_source: Literal["installed", "catalog", "estimate"] = "estimate"
            base_installed = False
            if provider_name == "ollama" and base_tag in installed_ollama_sizes:
                base_est = round(installed_ollama_sizes[base_tag] * 1.1, 1)
                base_source = "installed"
                base_installed = True
            elif provider_name == "lmstudio" and base_tag in installed_lmstudio:
                base_installed = True
                if (
                    entry.provider_quantized_artifacts_gb
                    and entry.provider_quantized_artifacts_gb.get("lmstudio")
                ):
                    base_source = "catalog"
            elif entry.quantized_artifacts_gb and (
                hints.quantization in (entry.quantized_artifacts_gb or {})
                or hints.quantization == "auto"
            ):
                base_source = "catalog"

            capacity = sys.vram_gb if sys.has_gpu and sys.vram_gb > 0 else sys.ram_gb
            base_fits = base_est <= max(capacity - 1.0, 0)
            base_reason = "fits GPU VRAM" if sys.has_gpu else "fits system RAM"
            if not base_fits:
                base_reason = "may exceed local memory"
            mem_pct = int(round((base_est / capacity) * 100)) if capacity > 0 else 0

            suggestions.append(
                ModelSuggestion(
                    entry=entry,
                    provider=provider_name,
                    provider_tag=base_tag,
                    est_memory_gb=base_est,
                    fits_local=base_fits,
                    reason=base_reason,
                    estimate_source=base_source,
                    is_installed=base_installed,
                    provider_available=provider_up,
                    mem_capacity_gb=capacity,
                    mem_capacity_type="vram"
                    if (sys.has_gpu and sys.vram_gb > 0)
                    else "ram",
                    mem_pct=mem_pct,
                )
            )

            # Additional installed variants for Ollama (do not overwrite base)
            if provider_name == "ollama":
                for cand in _ollama_candidate_tags(base_tag):
                    if cand == base_tag:
                        continue
                    if cand in installed_ollama_sizes:
                        est2 = round(installed_ollama_sizes[cand] * 1.1, 1)
                        fits2 = est2 <= max(capacity - 1.0, 0)
                        reason2 = "fits GPU VRAM" if sys.has_gpu else "fits system RAM"
                        if not fits2:
                            reason2 = "may exceed local memory"
                        mem_pct2 = (
                            int(round((est2 / capacity) * 100)) if capacity > 0 else 0
                        )
                        suggestions.append(
                            ModelSuggestion(
                                entry=entry,
                                provider=provider_name,
                                provider_tag=cand,
                                est_memory_gb=est2,
                                fits_local=fits2,
                                reason=reason2,
                                estimate_source="installed",
                                is_installed=True,
                                provider_available=provider_up,
                                mem_capacity_gb=capacity,
                                mem_capacity_type="vram"
                                if (sys.has_gpu and sys.vram_gb > 0)
                                else "ram",
                                mem_pct=mem_pct2,
                            )
                        )

    # Simple scoring: prefer fit, then by params (quality hint)
    def score(s: ModelSuggestion) -> tuple:
        installed_score = 2 if s.is_installed else 0
        available_score = 1 if s.provider_available else 0
        fit_score = 1 if s.fits_local else 0
        params = s.entry.active_params_b or s.entry.params_b or 0.0
        if hints.quality == "speed":
            params_score = -params
        elif hints.quality == "quality":
            params_score = params
        else:
            params_score = -abs(params - 8.0)
        try:
            prov_rank = len(hints.provider_order) - hints.provider_order.index(
                s.provider
            )
        except ValueError:
            prov_rank = 0
        return (installed_score, available_score, fit_score, prov_rank, params_score)

    suggestions.sort(key=score, reverse=True)
    return suggestions[:top_n]


def _ollama_list_models(endpoint: str | None = None) -> list[str]:
    if not endpoint:
        endpoint = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
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


def _ollama_list_models_with_sizes(endpoint: str | None = None) -> Dict[str, float]:
    """Return a mapping of model tag -> size in GB for installed models (best effort)."""
    if not endpoint:
        endpoint = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    sizes: Dict[str, float] = {}
    try:
        import httpx

        resp = httpx.get(f"{endpoint.rstrip('/')}/api/tags", timeout=5.0)
        resp.raise_for_status()
        items = resp.json().get("models", [])
        for it in items:
            name = it.get("name") or it.get("model")
            size_bytes = it.get("size") or it.get("size_bytes") or 0
            if isinstance(name, str) and isinstance(size_bytes, int):
                sizes[name] = round(size_bytes / (1024**3), 1)
    except Exception:
        return {}
    return sizes


def _lmstudio_list_models(endpoint: str | None = None) -> List[str]:
    """Return list of model IDs visible to LM Studio's OpenAI-compatible API."""
    if not endpoint:
        endpoint = os.environ.get("LMSTUDIO_HOST", "http://localhost:1234/v1")
    try:
        import httpx

        resp = httpx.get(f"{endpoint.rstrip('/')}/models", timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("data", [])
        names: List[str] = []
        for it in items:
            mid = it.get("id") or it.get("name")
            if isinstance(mid, str):
                names.append(mid)
        return names
    except Exception:
        return []


# -----------------------------
# Provider helpers
# -----------------------------


def _ollama_candidate_tags(tag: str) -> List[str]:
    """Return reasonable alternate tags for an Ollama model name.

    Examples:
    llama3.1:8b-instruct -> [llama3.1:8b-instruct, llama3.1:8b]
    llama3.2:3b -> [llama3.2:3b, llama3.2:3b-instruct, llama3.2:latest]
    """
    candidates: List[str] = [tag]
    # Drop -instruct suffix
    if tag.endswith("-instruct"):
        candidates.append(tag.replace("-instruct", ""))
    # Add instruct variant if base provided
    parts = tag.split(":", 1)
    if len(parts) == 2 and not parts[1].endswith("-instruct"):
        candidates.append(parts[0] + ":" + parts[1] + "-instruct")
    # Add :latest if no explicit tag
    if ":" not in tag:
        candidates.append(tag + ":latest")
    # Ensure uniqueness
    out: List[str] = []
    for c in candidates:
        if c not in out:
            out.append(c)
    return out


def _match_installed_ollama_tag(
    desired_tag: str, installed_sizes: Dict[str, float]
) -> Optional[tuple[str, float]]:
    """Return (installed_tag, size_gb) if any candidate of desired_tag is installed."""
    for cand in _ollama_candidate_tags(desired_tag):
        if cand in installed_sizes:
            return cand, installed_sizes[cand]
    return None


def _maybe_pull_model(name: str) -> None:
    try:
        subprocess.run(["ollama", "pull", name], check=True)
    except Exception:
        pass


def ensure_ollama_models(
    models: dict[str, str], endpoint: str | None = None
) -> dict[str, str]:
    """Ensure models exist; return possibly adjusted names that actually exist.

    For example, if "llama3.1:8b-instruct" is unavailable but "llama3.1:8b" exists,
    this returns {"chat": "llama3.1:8b", ...} and pulls that tag.
    """
    resolved: dict[str, str] = {}
    if not endpoint:
        endpoint = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
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
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'


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


def apply_recommendations_to_agent_config(
    agent_dir: Path, provider: str, recs: dict[str, str]
) -> None:
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

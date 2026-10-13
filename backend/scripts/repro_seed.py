"""Seed und model_config_dict für OASIS-Simulationsskripte (ohne Flask-Stack)."""

from __future__ import annotations

import hashlib
import os
import random
from typing import Any, Dict, Optional, Tuple


def apply_python_seeds(seed: int) -> None:
    """random / numpy / torch (falls vorhanden) setzen."""
    random.seed(seed)
    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def platform_seed(seed: int, platform: str) -> int:
    """Stabiler 31-Bit-Seed aus Lauf-Seed und Plattformname."""
    digest = hashlib.sha256(f"{int(seed)}:{platform}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % (2**31)


def make_platform_rng(seed: int, platform: str) -> random.Random:
    """Eigener random.Random-Strom je Plattform (vor asyncio-Verzahnung anlegen)."""
    return random.Random(platform_seed(seed, platform))


def make_platform_numpy(seed: int, platform: str):
    """Eigener NumPy-Generator je Plattform; None wenn NumPy fehlt."""
    try:
        import numpy as np

        return np.random.default_rng(platform_seed(seed, platform))
    except ImportError:
        return None


def build_model_config_dict(
    seed: Optional[int] = None,
    temperature: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """camel model_config_dict: seed, Temperatur, reasoning_effort für lokale Anbieter."""
    cfg: Dict[str, Any] = {}
    if seed is not None:
        cfg["seed"] = int(seed)
    if temperature is not None:
        cfg["temperature"] = float(temperature)
    provider = os.environ.get("LLM_PROVIDER", "openai").lower()
    if (
        provider in ("ollama", "lmstudio", "local")
        and os.environ.get("LOCAL_LLM_REASONING", "none").lower() != "on"
    ):
        cfg["reasoning_effort"] = "none"
    return cfg or None


def resolve_seed_and_temperature(
    cli_seed: Optional[int] = None,
) -> Tuple[int, float]:
    """Seed aus CLI/Umgebung/Zufall; Temperatur aus OASIS_LLM_TEMPERATURE (Standard 0.7)."""
    if cli_seed is not None:
        seed = int(cli_seed)
    elif os.environ.get("MIROFISH_SIM_SEED"):
        seed = int(os.environ["MIROFISH_SIM_SEED"])
    else:
        seed = random.randint(0, 2**31 - 1)
    temperature = float(os.environ.get("OASIS_LLM_TEMPERATURE", "0.7"))
    return seed, temperature

"""Entrada/salida: inputs.yaml es la única fuente de entradas."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "inputs.yaml"
RESULTS_DIR = ROOT / "resultados"
FIG_DIR = ROOT / "figuras"


def load_inputs(path: Path | str | None = None) -> dict:
    """Carga inputs.yaml (o la ruta dada, o $P1_INPUTS) y devuelve un dict."""
    import os
    p = Path(path) if path else Path(os.environ.get("P1_INPUTS", INPUTS))
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_json(obj: dict, name: str) -> Path:
    RESULTS_DIR.mkdir(exist_ok=True)
    p = RESULTS_DIR / name
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, default=_default)
    return p


def load_json(name: str) -> dict:
    with open(RESULTS_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


def _default(o):
    try:
        import numpy as np
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.bool_,)):
            return bool(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
    except ImportError:  # pragma: no cover
        pass
    raise TypeError(f"no serializable: {type(o)}")

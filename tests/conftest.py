import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "04_diseno"))


@pytest.fixture(scope="session")
def root():
    return ROOT


@pytest.fixture(scope="session")
def sizing():
    with open(ROOT / "resultados" / "sizing.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def manifest():
    with open(ROOT / "resultados" / "manifest.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def inp():
    from p1calc.io import load_inputs
    return load_inputs()

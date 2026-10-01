"""Cambiar un valor en inputs.yaml regenera la geometría (sin tocar resultados/ del repo)."""
import importlib.util
import os

import yaml


def test_transom_thickness_changes_clamp(root, tmp_path, monkeypatch):
    with open(root / "inputs.yaml", encoding="utf-8") as f:
        d = yaml.safe_load(f)
    d["boat"]["transom"]["thickness_range_mm"] = [20, 80]
    alt = tmp_path / "inputs_alt.yaml"
    with open(alt, "w", encoding="utf-8") as f:
        yaml.safe_dump(d, f, allow_unicode=True)
    import params as P
    p0 = P.load()
    p1 = P.load(inputs_path=alt)
    assert p1.clamp_gap == p0.clamp_gap + 15
    spec = importlib.util.spec_from_file_location("b", root / "04_diseno" / "piezas" / "P1-MNT-01_clamp_bracket.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    b0, b1 = m.build(p0).bounding_box(), m.build(p1).bounding_box()
    assert abs((b1.max.X - b1.min.X) - (b0.max.X - b0.min.X) - 15) < 1e-6

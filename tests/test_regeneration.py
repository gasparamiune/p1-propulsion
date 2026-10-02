"""Cambiar un valor en inputs.yaml regenera la geometría (sin tocar resultados/ del repo)."""
import importlib.util

import yaml


def test_bottom_thickness_changes_intake(root, tmp_path):
    """El espesor del fondo del casco cambia la placa base de la toma."""
    with open(root / "inputs.yaml", encoding="utf-8") as f:
        d = yaml.safe_load(f)
    d["boat"]["bottom_thickness_mm"] = d["boat"]["bottom_thickness_mm"] + 2.0
    alt = tmp_path / "inputs_alt.yaml"
    with open(alt, "w", encoding="utf-8") as f:
        yaml.safe_dump(d, f, allow_unicode=True)
    import params as P
    p0 = P.load()
    p1 = P.load(inputs_path=alt)
    assert p1.bottom_t == p0.bottom_t + 2.0
    spec = importlib.util.spec_from_file_location("ref", root / "04_diseno" / "piezas" / "P1-REF-01_casco.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    v0, v1 = m.build(p0).volume, m.build(p1).volume
    assert v1 > v0


def test_axis_height_moves_jet(root, tmp_path):
    """La altura del eje en el impulsor mueve todo el jet (marco JET) y la tobera en el espejo."""
    with open(root / "inputs.yaml", encoding="utf-8") as f:
        d = yaml.safe_load(f)
    d["waterjet"]["axis_height_m"] = d["waterjet"]["axis_height_m"] + 0.010
    alt = tmp_path / "inputs_alt.yaml"
    with open(alt, "w", encoding="utf-8") as f:
        yaml.safe_dump(d, f, allow_unicode=True)
    import params as P
    p0, p1 = P.load(), P.load(inputs_path=alt)
    assert abs((p1.z_noz - p0.z_noz) - 10.0) < 1e-6

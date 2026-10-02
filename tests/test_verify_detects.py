"""verify_parts.py debe pasar con el diseño real y FALLAR ante fallas inyectadas."""
import copy
import json

import numpy as np
import pytest
import trimesh


@pytest.fixture(scope="module")
def ctx(root):
    import params as P
    from build_all import load_parts
    p = P.load()
    mods = load_parts()
    with open(root / "resultados" / "manifest.json", encoding="utf-8") as f:
        man = json.load(f)
    return p, mods, man


def test_real_design_passes(ctx):
    import verify_parts as V
    p, mods, man = ctx
    res = V.run(p, mods, man, quiet=True)
    assert res["ok"], res["fails"]


def test_detects_oversize(ctx):
    import verify_parts as V
    p, mods, man = ctx
    m2 = copy.deepcopy(man)
    for r in m2["parts"]:
        if r["id"] == "P1-INT-04":
            r["print_bbox_mm"] = [250.0, 120.0, 80.0]
    res = V.run(p, mods, m2, steer_list=[0.0], quiet=True)
    assert not res["ok"]
    assert any("envolvente" in f for f in res["fails"])


def test_detects_interference(ctx):
    import verify_parts as V
    p, mods, man = ctx
    # bloque fijo en el barrido de la boquilla direccional (afuera del espejo)
    import params as P
    blk = trimesh.creation.box(extents=(40, 40, 40))
    blk.apply_translation(P.jet_to_boat(p, p.X_steer_pivot + 0.5 * p.L_steer, p.D_noz / 2 + 3.0, 0))   # pared de la boquilla
    res = V.run(p, mods, man, steer_list=[0.0], quiet=True, extra_fixed=[("OBSTACULO", blk)])
    assert not res["ok"]
    assert any("OBSTACULO" in f for f in res["fails"])


def test_detects_non_manifold(ctx, root, tmp_path):
    import verify_parts as V
    p, mods, man = ctx
    m2 = copy.deepcopy(man)
    broken = trimesh.creation.box(extents=(10, 10, 10))
    broken.update_faces(np.arange(len(broken.faces) - 2))       # quita 2 triángulos → no estanca
    f = tmp_path / "roto.stl"
    broken.export(f)
    for r in m2["parts"]:
        if r["id"] == "P1-CTL-02":
            r["files"] = [r["files"][0], str(f)]
    res = V.run(p, mods, m2, steer_list=[0.0], quiet=True)
    assert not res["ok"]
    assert any("manifold" in x for x in res["fails"])


def test_detects_failed_critical_dim(ctx):
    import verify_parts as V
    p, mods, man = ctx
    m2 = copy.deepcopy(man)
    m2["parts"][0]["checks"].append({"name": "cota inyectada", "value": 1, "ref": 2, "op": ">=", "ok": False})
    res = V.run(p, mods, m2, steer_list=[0.0], quiet=True)
    assert not res["ok"]

"""Consistencia de parámetros y del CAD exportado."""
from pathlib import Path

import trimesh


def test_params_consistent_with_sizing(sizing):
    import params as P
    p = P.load()
    lay = sizing["layout"]
    assert abs((p.u_shaft_bot - p.u_shaft_top) - lay["shaft_length_mm"]) < 1e-6
    assert abs(p.s_prop - lay["s_prop_mm"]) < 1e-9
    assert p.clamp_gap >= p.tr_t_max + 4
    assert p.guard_ri - p.prop_D / 2 >= 8
    assert abs(p.center_dist - (p.motor_v + p.e)) < 1e-9


def test_printed_parts_files_envelope_manifold(manifest, root, inp):
    env = inp["printer"]["envelope_mm"]
    printed = [r for r in manifest["parts"] if r["process"] == "impresa"]
    assert len(printed) >= 15
    for r in printed:
        for f in r["files"]:
            assert (root / f).exists(), f
        bb = r["print_bbox_mm"]
        assert bb[0] <= env[0] and bb[1] <= env[1] and bb[2] <= env[2], (r["id"], bb)
        m = trimesh.load(root / r["files"][1], force="mesh")
        assert m.is_watertight and m.is_winding_consistent and m.volume > 0, r["id"]


def test_all_critical_dims_ok(manifest):
    bad = [(r["id"], c["name"]) for r in manifest["parts"] for c in r.get("checks", []) if not c["ok"]]
    assert not bad, bad


def test_naming_convention(manifest):
    import re
    pat = re.compile(r"^P1-(MNT|HSG|DRV|PRP|STR|ELE|SAF)-\d{2}$")
    for r in manifest["parts"]:
        assert pat.match(r["id"]), r["id"]

"""Consistencia de parámetros y del CAD exportado (waterjet)."""
import math

import trimesh


def test_params_consistent_with_sizing(sizing):
    import params as P
    p = P.load()
    sel = sizing["selection"]
    assert p.D == sel["D_imp_mm"] and abs(p.D_noz - sel["D_noz_mm"]) < 1e-9
    assert abs(p.D_hub - sel["hub_d_mm"]) < 1e-9
    assert abs(p.D_bore - (p.D + 2 * p.tip_clr)) < 1e-9
    # la salida de la tobera fija está en el plano del espejo (x = 0)
    x, _, z = P.jet_to_boat(p, p.X_noz1, 0, 0)
    assert abs(x) < 1e-6 and abs(z - p.z_noz) < 1e-6
    # la toma está entera a proa de la cara del impulsor (comentario de Jorge)
    assert p.x_if < p.x_lip < p.x_tan
    # el sello sale por el techo de la toma a proa del impulsor, el motor detrás del acople
    assert 0 < p.S_seal < p.S_brg0 < p.S_brg1 < p.S_cpl1 < p.S_motor0 < p.S_motor1
    # el soporte de rodamientos apoya fuera de la abertura de la toma
    assert all(abs(y) > p.W_open / 2 + 20 for _, y in p.brg_bracket_holes)


def test_printed_parts_files_envelope_manifold(manifest, root, inp):
    env = inp["printer"]["envelope_mm"]
    printed = [r for r in manifest["parts"] if r["process"] == "impresa"]
    assert len(printed) >= 4
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


def test_all_parts_single_valid_solid(manifest):
    bad = [r["id"] for r in manifest["parts"] if not r["valid_solid"]]
    assert not bad, bad


def test_naming_convention(manifest):
    import re
    pat = re.compile(r"^P1-(INT|PMP|DRV|MOT|STE|REV|CTL|ELE|BAT|REF)-\d{2}$")
    for r in manifest["parts"]:
        assert pat.match(r["id"]), r["id"]
        assert r.get("group") in ("jet", "drive", "motor", "ele", "bat", "ref"), r["id"]


def test_jet_mass_feeds_sizing(manifest, sizing, inp):
    """La masa de la unidad de jet del CAD es la que usa sizing (iteración CAD → sizing)."""
    m_jet = [i for i in sizing["masses"]["items"] if i["id"] == "jet"][0]["kg"]
    assert math.isclose(m_jet, manifest["totals"]["jet_unit_mass_kg"], rel_tol=0.05)

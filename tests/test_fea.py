"""Tests del FEA (04_diseno/fea): solver contra casos analíticos, verificación cruzada con
scikit-fem, malla gruesa rápida de una pieza real (P1-CTL-02), estática del bucket y FS > 0 en
resultados_fea.json para las piezas del waterjet."""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
FEA = ROOT / "04_diseno" / "fea"
sys.path.insert(0, str(FEA))

gmsh = pytest.importorskip("gmsh")

E, NU = 1900.0, 0.38
L, B, H, F = 100.0, 10.0, 10.0, 10.0          # viga en voladizo [mm, N]


@pytest.fixture(scope="module")
def beam(tmp_path_factory):
    from build123d import Align, Box, export_step
    import fea_core as fc
    path = tmp_path_factory.mktemp("viga") / "viga.step"
    export_step(Box(L, B, H, align=(Align.MIN, Align.CENTER, Align.CENTER)), str(path))
    X, T, _ = fc.mesh_step(path, 5.0, curv_n=0)
    return X, T


def _cantilever(fc, X, T):
    S = fc.P2Space(X, T)
    K = S.stiffness(E, NU)
    root = np.flatnonzero((S.fnormal[:, 0] < -0.99) & (S.fcent[:, 0] < 1e-6))
    tip = np.flatnonzero((S.fnormal[:, 0] > 0.99) & (S.fcent[:, 0] > L - 1e-6))
    nodes = S.facet_nodes(root)
    fixed = (3 * nodes[:, None] + np.arange(3)).ravel()
    A = S.farea[tip].sum()
    f = S.traction_load(tip, lambda Xq, n: np.broadcast_to(np.array([0.0, 0.0, -F / A]), Xq.shape))
    u, info, _ = fc.solve_spd(K, f, fixed, S.coarse_prolongation())
    return S, u, info, tip


def test_cantilever_analytic(beam):
    """Flecha de punta y tensión de flexión a L/2 dentro del 10 % de Timoshenko/Navier."""
    import fea_core as fc
    X, T = beam
    S, u, info, tip = _cantilever(fc, X, T)
    assert info["cg_flag"] == 0 and info["rel_res"] < 1e-6
    U = u[:S.ndof_fem].reshape(-1, 3)
    I = B * H ** 3 / 12
    G = E / (2 * (1 + NU))
    d_an = F * L ** 3 / (3 * E * I) + F * L / (5 / 6 * G * B * H)
    d_fe = -U[S.facet_nodes(tip), 2].mean()
    assert abs(d_fe / d_an - 1) < 0.10, (d_fe, d_an)
    Sn = S.nodal_average(S.vertex_stress(u, E, NU))
    top = np.flatnonzero((np.abs(S.X[:, 0] - L / 2) < 6) & (S.X[:, 2] > H / 2 - 1e-6))
    s_fe = np.polyval(np.polyfit(S.X[top, 0], Sn[top, 0, 0], 1), L / 2)
    s_an = F * (L / 2) * (H / 2) / I
    assert abs(s_fe / s_an - 1) < 0.10, (s_fe, s_an)


def test_cross_check_scikit_fem(beam):
    """El ensamble P2 propio coincide con scikit-fem (ElementTetP2) en la misma malla."""
    skfem = pytest.importorskip("skfem")
    from skfem import Basis, ElementTetP2, ElementVector, FacetBasis, LinearForm, MeshTet, asm, condense, solve
    from skfem.models.elasticity import lame_parameters, linear_elasticity
    import fea_core as fc
    X, T = beam
    S, u, _, tip = _cantilever(fc, X, T)
    d_own = -u[:S.ndof_fem].reshape(-1, 3)[np.unique(S.ftri[tip]), 2].mean()       # vértices de la punta
    m = MeshTet(np.ascontiguousarray(X.T), np.ascontiguousarray(T.T))
    ib = Basis(m, ElementVector(ElementTetP2()), intorder=2)
    K = asm(linear_elasticity(*lame_parameters(E, NU)), ib)
    tipf = m.facets_satisfying(lambda x: np.isclose(x[0], L))
    fb = FacetBasis(m, ElementVector(ElementTetP2()), facets=tipf)
    A = B * H

    @LinearForm
    def load(v, w):
        return -F / A * v[2]
    f = asm(load, fb)
    D = ib.get_dofs(lambda x: np.isclose(x[0], 0.0)).all()
    us = solve(*condense(K, f, D=D))
    d_sk = -np.mean(us[ib.get_dofs(lambda x: np.isclose(x[0], L)).nodal["u^3"]])
    assert abs(d_own / d_sk - 1) < 0.01, (d_own, d_sk)


def test_rigid_coupling_and_winkler(beam):
    """Bloque apoyado en Winkler unilateral y cargado por un cuerpo rígido: equilibrio y
    flecha = F/(k·A) + F·h/(E·A) (columna corta, ν pequeño en el promedio)."""
    import fea_core as fc
    from fea_model import Interface, Model, force_of
    X, T = beam
    S = fc.P2Space(X, T)
    M = Model(S, E, NU, (0, 0, 1))
    rd = M.add_rigid("placa", (L, 0, 0), fixed_local=(1, 2, 3, 4, 5))
    M.assemble()
    k = 50.0
    root = np.flatnonzero((S.fnormal[:, 0] < -0.99) & (S.fcent[:, 0] < 1e-6))
    tip = np.flatnonzero((S.fnormal[:, 0] > 0.99) & (S.fcent[:, 0] > L - 1e-6))
    M.add_interface(Interface("suelo", root, k, k_t=0.5))
    M.add_interface(Interface("placa", tip, 1e4, kind="rigid", rigid="placa", k_t=1.0))
    f = np.zeros(S.ndof)
    f[rd[0]] = -F * 100                                     # compresión axial de 1000 N
    u, info = M.solve(f)
    R = M.interface_forces(u)
    assert abs(R["suelo"]["F_N"][0] - F * 100) < 1e-3 * F * 100
    A = B * H
    d_an = F * 100 / (k * A) + F * 100 * L / (E * A) + F * 100 / (1e4 * A)
    assert abs(-u[rd[0]] / d_an - 1) < 0.03, (-u[rd[0]], d_an)


PIEZAS = ("P1-DRV-03", "P1-REV-01", "P1-STE-01", "P1-INT-02", "P1-CTL-02")


@pytest.fixture(scope="module")
def ctl02_quick():
    import fea_run
    pid, res = fea_run.run_part("P1-CTL-02", quick=True, no_img=True)
    return res


def test_part_quick_mesh(ctl02_quick):
    """Malla gruesa de P1-CTL-02 (PETG) de punta a punta: FS finito y > 0, σZ evaluada, comparación a mano."""
    r = ctl02_quick
    assert r["mallas"]["gruesa"]["n_tets"] > 1000
    assert 0 < r["FS_min"] < 999
    for cid, c in r["casos"].items():
        s = c["gruesa"]["resumen"]
        assert s["vm"]["p99"] <= s["vm"]["max"] + 1e-9
        assert s["vm"]["max_excl"] <= s["vm"]["max"] + 1e-9
        assert c["FS"]["gobernante"] > 0 and "Z" in c["FS"]
        assert c["gruesa"]["regiones"]["tapa"]["vm"]["max_excl"] > 0
    # equilibrio: la carga de la mano (150 N) la reacciona la consola + tornillos
    assert r["comparacion_mano"] and all(c["FS_FEA"] > 0 for c in r["comparacion_mano"])


def test_bucket_statics_matches_hand():
    """La estática del bucket (traba solo tangencial) reproduce la fuerza de traba de structural_direccion."""
    import fea_parts as fp
    p, _, est = fp.load_project()
    st = fp.bucket_statics(p, p.REV_F_design)
    F_lock = float(np.linalg.norm(st["F_traba_sobre_boquilla_N"]))
    ref = est["loads"]["structural_direccion"]["F_lock_pin_N"]
    assert abs(F_lock / ref - 1) < 0.03, (F_lock, ref)
    # equilibrio de fuerzas sobre el bucket
    tot = np.array(st["F_N"]) + sum(-np.array(st[k]) for k in ("F_traba_sobre_boquilla_N", "F_pivote_mas_y_sobre_boquilla_N",
                                                                "F_pivote_menos_y_sobre_boquilla_N"))
    assert np.allclose(tot, 0, atol=1e-6)


def test_resultados_fea_json():
    """Entregable: resultados_fea.json con FS > 0 para cada pieza, malla gruesa y fina, comparación e imágenes."""
    p = FEA / "resultados_fea.json"
    assert p.exists(), "correr: python 04_diseno/fea/fea_run.py"
    res = json.loads(p.read_text(encoding="utf-8"))
    for pid in PIEZAS:
        r = res["piezas"][pid]
        assert r["FS_min"] is not None and r["FS_min"] > 0, pid
        assert {"gruesa", "fina"} <= set(r["mallas"]), pid
        for c in r["casos"].values():
            fs = c["FS"]["gobernante"]
            assert fs > 0 and math.isfinite(fs), pid
            assert "convergencia" in c
        assert r["comparacion_mano"], pid
        for img in r["imagenes"]:
            assert (ROOT / img).exists(), img

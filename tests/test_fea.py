"""Tests del FEA (04_diseno/fea): solver contra casos analíticos, verificación cruzada con
scikit-fem, malla gruesa rápida de una pieza real (P1-CTL-02), estática del bucket, carga aplicada del
bucket = estática (setup con malla muy gruesa), traba única con M_h completo, bordes de agujeros cargados
y cumplimiento en resultados_fea.json para las piezas del waterjet (ronda 4). Ronda 5: regla de la σ de diseño sin
convergencia (FEA-R5-01), pivote de STE-01 como apoyo lineal del piloto Ø20 y precarga de los émbolos (FEA-R5-02)."""
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
    """La estática del bucket es la de structural_direccion (ronda 4: cantidad de movimiento del chorro, criterio de traba
    única): con M_h completo en una traba, esa traba lleva M_h/r = F_lock_pin_N y la otra cero; equilibrio de fuerzas; la
    mayor reacción de pivote es R_bucket_pivot_design_N; y el momento con signo coincide con |M_h| de la fila a mano."""
    import fea_parts as fp
    p, _, est = fp.load_project()
    sd = est["loads"]["structural_direccion"]
    ks = ("F_traba_sobre_boquilla_N", "F_traba_menos_y_sobre_boquilla_N", "F_pivote_mas_y_sobre_boquilla_N",
          "F_pivote_menos_y_sobre_boquilla_N")
    Rmax = 0.0
    for side in (1, -1):
        st = fp.bucket_statics(p, p.REV_F_design, share={side: 1.0})
        Fl = {s_: float(np.linalg.norm(st[k])) for s_, k in ((1, ks[0]), (-1, ks[1]))}
        assert abs(Fl[side] / sd["F_lock_pin_N"] - 1) < 0.01, (side, Fl, sd["F_lock_pin_N"])
        assert Fl[-side] < 1e-9, (side, Fl)
        tot = np.array(st["F_N"]) + sum(-np.array(st[k]) for k in ks)
        assert np.allclose(tot, 0, atol=1e-6), side
        assert abs(abs(st["M_y_chorro_Nm"]) / sd["M_hinge_Nm"] - 1) < 0.01, (st["M_y_chorro_Nm"], sd["M_hinge_Nm"])
        assert abs(st["F_N"][2] / sd["F_z_bucket_N"] - 1) < 0.01, (st["F_N"], sd["F_z_bucket_N"])
        Rmax = max(Rmax, *(float(np.linalg.norm(st[k])) for k in ks[2:]))
    assert abs(Rmax / sd["R_bucket_pivot_design_N"] - 1) < 0.01, (Rmax, sd["R_bucket_pivot_design_N"])
    stn = fp.bucket_statics(p, p.sz["loads"]["F_bucket_N"], share={1: 1.0})
    assert abs(float(np.linalg.norm(stn[ks[0]])) / sd["F_lock_pin_sizing_N"] - 1) < 0.01


@pytest.mark.parametrize("pid,h", [("P1-REV-01", 10.0), ("P1-STE-01", 12.0)])
def test_applied_load_matches_statics_coarse(pid, h, tmp_path):
    """Setup con malla MUY gruesa (sin resolver): la carga del bucket que se aplica tiene la resultante y el momento de
    la estática (REV-01: bucket_reactions, 2 %; STE-01: reacciones sobre las orejas, 1 %; auditoría ronda 4, F1/F5). El
    setup ya lo verifica (RuntimeError si no); acá se controla lo que guarda en los checks. STE-01: el agujero del
    pivote existe solo en las orejas (sin el festón de la torre del yugo)."""
    import fea_parts as fp
    p, mods, est = fp.load_project()
    st = fp.SETUPS[pid](p, mods, est, h, 6, str(tmp_path), log=None, hmin=2.0)
    ck = st["checks"]
    if pid == "P1-REV-01":
        recs = {"R12": ck["resultante_R12"]}
        tol = fp.TOL_STATICS_REV
        sd = est["loads"]["structural_direccion"]
        assert abs(abs(ck["resultante_R12"]["M_y_estatica_Nm"]) / sd["M_hinge_Nm"] - 1) < 0.01
    else:
        recs = ck["resultante_bucket"]
        tol = fp.TOL_STATICS_STE
        assert set(recs) == {"R12_+Y", "R12_-Y", "sz_+Y", "sz_-Y"}, sorted(recs)
        assert ck["facetas_agujero_pivote_fuera_de_las_orejas"] == 0
        # ronda 5 (P1-REV-02 rediseñado): piloto = muñón Ø20 h6 en el Ø20 H7 de la oreja de STE_ear_t; el pivote apoya con
        # presión lineal a lo largo del agujero (par de aplastamiento) cuya resultante pasa por la mitad del buje
        assert ck["d_agujero_piloto_mm"] == p.REV_sp_pilot_d == p.REV_pin_d == 20.0, ck["d_agujero_piloto_mm"]
        for s_, L_ in ck["largo_agujero_piloto_malla_mm"].items():
            assert abs(L_ - p.STE_ear_t) < 0.05, (s_, L_, p.STE_ear_t)
        lev = (p.REV_y_in - p.STE_ear_y1) + p.REV_bush_L / 2
        assert abs(ck["brazo_pivote_desde_cara_exterior_mm"] - lev) < 1e-9
        assert abs(ck["excentricidad_pivote_desde_plano_medio_mm"] - (lev + p.STE_ear_t / 2)) < 1e-9
        for k, r in recs.items():
            assert r["err_M3_rel"] <= tol, (k, r["M_pivote_aplicado_Nm"], r["M_pivote_estatica_Nm"])
            for hn, lb in r["apoyo_lineal_piloto"].items():
                assert abs(lb["excentricidad_aplicada_mm"] / lb["excentricidad_mm"] - 1) < 0.005, (k, hn, lb)
                assert lb["ell_extremos"][0] < 0 < lb["ell_extremos"][1], (k, hn, lb)   # el piloto apoya en las dos paredes
        # precarga máxima del cuerpo del émbolo (FEA-R5-02) = la de structural_direccion
        pre = ck["precarga_embolo"]
        F_max = p.REV_lock_T_Nm * 1000 / (min(p.REV_lock_K) * p.REV_lock_thread_d)
        assert abs(pre["F_max_N"] / F_max - 1) < 1e-9
        assert abs(pre["p_radial_MPa"] - math.tan(math.radians(30)) * F_max / (math.pi * p.REV_lock_thread_d * p.STE_ear_t)) < 1e-9
        assert {"c", "c2", "f", "f2"} <= set(pre["casos"])
    for k, r in recs.items():
        assert r["err_F_rel"] <= tol and r["err_M_rel"] <= tol, (k, r)
        F_a, F_s = np.array(r["F_aplicada_N"]), np.array(r["F_estatica_N"])
        assert np.linalg.norm(F_a - F_s) <= tol * np.linalg.norm(F_s), (k, F_a, F_s)
    assert st["holes"], "faltan los agujeros cargados de la verificación de borde (F3)"


def _summ(mx, p99=None, mvol=None, at=(0.0, 0.0, 0.0)):
    return {"vm": {"max_excl": mx, "max": mx * 1.5, "p99": p99 or mx / 2, "max_vol": mvol, "at_max_excl_mm": list(at),
                   "at_max_vol_mm": list(at)}, "u_max_mm": 0.1}


def test_design_sigma_never_lowered_when_not_converged():
    """FEA-R5-01: si el máx* no converge (|cambio gruesa → fina| > CONV_TOL) la σ de diseño es máx(máx* fino,
    Richardson), nunca el promedio en volumen (salvo una arista viva nombrada); y «cumple» es falso si la extrapolación
    de un caso de diseño queda bajo el objetivo aunque el FS de la malla fina cumpla."""
    import fea_run as fr
    mallas = {"gruesa": {"h_mm": 8.0, "refine": []}, "fina": {"h_mm": 4.5, "refine": []}}
    fine, coarse = _summ(100.0, mvol=60.0), _summ(70.0)
    s_, m_, d_ = fr.design_sigma(fine, "vm", coarse)                          # sin mallas: el máx* fino
    assert abs(d_) > fr.CONV_TOL and s_ >= 100.0 and not fr.is_vol_method(m_), (s_, m_)
    s_, m_, _ = fr.design_sigma(fine, "vm", coarse, mallas)                   # con mallas: Richardson (> fina)
    ext = fr.richardson(70.0, 100.0, 8.0, 4.5)
    assert ext > 100.0 and abs(s_ - ext) < 1e-9 and m_.startswith("Richardson"), (s_, ext, m_)
    s_, m_, _ = fr.design_sigma(fine, "vm", coarse, mallas, {"canto": {"c": [0, 0, 0], "r": 2.0}})
    assert abs(s_ - 60.0) < 1e-9 and "arista viva «canto»" in m_, (s_, m_)   # solo en la arista viva nombrada
    s_, m_, _ = fr.design_sigma(fine, "vm", coarse, mallas, {"otra": {"c": [50, 0, 0], "r": 2.0}})
    assert s_ >= 100.0, (s_, m_)
    s_, m_, _ = fr.design_sigma(fine, "vm", _summ(95.0), mallas)               # convergido: máx*
    assert s_ == 100.0 and m_ == "máx*"
    # fs_block: σ de diseño ≥ máx* fino con cambio > 20 %
    A = {"tipo": "metal", "S_short": 240.0, "S_sust": 240.0, "fs_target": 2.0}
    fb = fr.fs_block(fine, "short", A, coarse, ({}, {}), mallas)
    assert fb["sigma_vm_diseno_MPa"] >= fine["vm"]["max_excl"] and fb["richardson_vm"]["sigma_ext_MPa"] > 100.0
    # postprocess: FS fino 240/115 = 2,09 cumple, pero la extrapolación (cambio 13 %) da FS < 2 → no cumple
    out = {"pid": "X", "nivel_reportado": "fina", "mallas": mallas, "comparacion": [],
           "casos": {"a": {"tipo": "short", "diseno": True,
                           "gruesa": {"resumen": _summ(100.0), "regiones": {}, "bordes": {}},
                           "fina": {"resumen": _summ(115.0), "regiones": {}, "bordes": {}}}}}
    fr.postprocess(out, A, False)
    assert out["FS_min"] >= 2.0 and out["casos"]["a"]["FS"]["metodo_vm"] == "máx*"
    assert out["richardson_bajo_objetivo"] and not out["cumple"], out["richardson_bajo_objetivo"]


def _fea_part(pid):
    p = FEA / "resultados_fea.json"
    assert p.exists(), "correr: python 04_diseno/fea/fea_run.py"
    return json.loads(p.read_text(encoding="utf-8"))["piezas"][pid]


def test_bucket_single_lock_carries_full_moment():
    """Ronda 4 (criterio de traba única, F5 no tautológico): en los casos de diseño d/e (R12) y f/g (sizing) del FEA del
    bucket, la ÚNICA traba activa lleva M_h/r (± 3 %) con M_h de structural_direccion.jet_momentum, el momento que toma
    equilibra el aplicado y la resultante aplicada es la de la estática (2 %)."""
    import fea_parts as fp
    p, _, est = fp.load_project()
    sd = est["loads"]["structural_direccion"]
    r = _fea_part("P1-REV-01")
    lv = r["nivel_reportado"]
    assert {"a", "d", "e", "f", "g"} <= set(r["casos"]), sorted(r["casos"])
    assert {"d", "e", "f", "g"} <= set(r["casos_diseno"]) and "a" not in r["casos_diseno"]
    want = {"d": ("traba", "F_lock_pin_N"), "e": ("traba_menos_y", "F_lock_pin_N"),
            "f": ("traba", "F_lock_pin_sizing_N"), "g": ("traba_menos_y", "F_lock_pin_sizing_N")}
    for cid, (lk, key) in want.items():
        ex = r["casos"][cid][lv]["extra"]
        assert ex["trabas_activas"] == [lk], (cid, ex["trabas_activas"])
        assert abs(ex["F_traba_M_h_sobre_r_N"] / sd[key] - 1) < 0.01, (cid, ex["F_traba_M_h_sobre_r_N"], sd[key])
        Ft = ex["F_traba_tangencial_N"][lk]
        assert abs(Ft / ex["F_traba_M_h_sobre_r_N"] - 1) < 0.03, (cid, Ft, ex["F_traba_M_h_sobre_r_N"])
        assert abs(ex["M_traba_por_lado_Nm"][lk] + ex["M_pivote_Nm"]) < 0.02 * abs(ex["M_pivote_Nm"]), (cid, ex["M_traba_por_lado_Nm"])
        res = ex["resultante"]
        assert res["err_F_rel"] <= fp.TOL_STATICS_REV and res["err_M_rel"] <= fp.TOL_STATICS_REV, (cid, res)
    # con las dos trabas sin desfase (a), entre las dos llevan M_h/r
    ex = r["casos"]["a"][lv]["extra"]
    assert abs(sum(ex["F_traba_tangencial_N"].values()) / ex["F_traba_M_h_sobre_r_N"] - 1) < 0.03, ex["F_traba_tangencial_N"]


def test_lug_edges_checked():
    """F3: en REV-01 y STE-01 cada caso de diseño evalúa el borde de sus agujeros cargados (traba/rosca y pivote) a ±90°
    de la carga, con FS ≥ objetivo; el agujero de una traba deshabilitada no se evalúa como cargado."""
    for pid, need in (("P1-REV-01", {"d": {"traba", "pivote_mas_y"}, "e": {"traba_menos_y", "pivote_menos_y"}}),
                      ("P1-STE-01", {"c": {"rosca_mas_y", "pivote_mas_y"}, "c2": {"rosca_menos_y", "pivote_menos_y"}})):
        r = _fea_part(pid)
        for cid, holes in need.items():
            fb = r["casos"][cid]["FS_bordes"]
            assert holes <= set(fb), (pid, cid, sorted(fb))
            for hn, b in fb.items():
                assert b["FS"] >= r["FS_objetivo"], (pid, cid, hn, b["FS"])
        if pid == "P1-REV-01":
            assert "traba_menos_y" not in r["casos"]["d"]["FS_bordes"] and "traba" not in r["casos"]["e"]["FS_bordes"]


def test_fea_json_design_sigma_rule():
    """FEA-R5-01 sobre el entregable: ningún caso de diseño con |cambio gruesa → fina| > CONV_TOL tiene una σ de diseño
    menor que el máx* de la malla fina (cuerpo y bordes), salvo una arista viva nombrada en `aristas_vivas`."""
    import fea_run as fr
    for pid in PIEZAS:
        r = _fea_part(pid)
        lv = r["nivel_reportado"]
        for cid in r["casos_diseno"]:
            c = r["casos"][cid]
            fs = c["FS"]
            if fs.get("dif_conv_vm") is not None and abs(fs["dif_conv_vm"]) > fr.CONV_TOL:
                ok_edge = "arista viva" in fs["metodo_vm"] and any(f"«{a}»" in fs["metodo_vm"] for a in r.get("aristas_vivas", {}))
                assert ok_edge or fs["sigma_vm_diseno_MPa"] >= c[lv]["resumen"]["vm"]["max_excl"] - 1e-6, (pid, cid, fs["metodo_vm"])
            for hn, b in (c.get("FS_bordes") or {}).items():
                if b.get("dif_conv") is not None and abs(b["dif_conv"]) > fr.CONV_TOL:
                    assert b["sigma_theta_diseno_MPa"] >= b["sigma_theta_MPa"] - 1e-6, (pid, cid, hn)
        if r.get("richardson_bajo_objetivo"):
            assert not r["cumple"], pid


def test_ste01_preload_and_pivot_model():
    """Ronda 5 en el entregable de STE-01: casos de reversa con la precarga de los émbolos superpuesta (FEA-R5-02), caso
    p (precarga sola) informativo, fatiga f/f2 con la precarga como media (Goodman) y la carga del pivote como apoyo
    lineal del piloto Ø20 (resultante y vector momento = estática, 1 %)."""
    import fea_parts as fp
    r = _fea_part("P1-STE-01")
    lv = r["nivel_reportado"]
    assert "p" in r["casos"] and "p" not in r["casos_diseno"] and not r["casos"]["p"]["diseno"]
    for cid in ("c", "c2", "d", "d2", "f", "f2"):
        ex = r["casos"][cid][lv]["extra"]
        assert ex["precarga_embolo"]["F_N"] > 0, cid
        res = ex["resultante_bucket"]
        assert max(res["err_F_rel"], res["err_M_rel"], res["err_M3_rel"]) <= fp.TOL_STATICS_STE, (cid, res)
    for cid in ("f", "f2"):
        assert r["casos"][cid].get("media_goodman"), cid
        assert all(b.get("goodman") for b in r["casos"][cid]["FS_bordes"].values()), cid
    assert r["verificacion_mano"]["d_agujero_piloto_mm"] == 20.0


def test_resultados_fea_json():
    """Entregable: resultados_fea.json con FS > 0 para cada pieza, malla gruesa y fina, comparación e imágenes; cada
    pieza cumple su FS objetivo en los casos de diseño."""
    p = FEA / "resultados_fea.json"
    assert p.exists(), "correr: python 04_diseno/fea/fea_run.py"
    res = json.loads(p.read_text(encoding="utf-8"))
    for pid in PIEZAS:
        r = res["piezas"][pid]
        assert r["FS_min"] is not None and r["FS_min"] > 0, pid
        assert r["cumple"], (pid, r["FS_min"], r["FS_objetivo"], r["caso_gobernante"])   # FS ≥ 2 metal / ≥ 3 PETG
        assert {"gruesa", "fina"} <= set(r["mallas"]), pid
        for c in r["casos"].values():
            fs = c["FS"]["gobernante"]
            assert fs > 0 and math.isfinite(fs), pid
            assert "convergencia" in c
        assert r["comparacion_mano"], pid
        for img in r["imagenes"]:
            assert (ROOT / img).exists(), img

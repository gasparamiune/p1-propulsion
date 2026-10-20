"""J-FWD disc spring under the head: paper scoping (lead 12:09Z item 4 (iii); lead 12:52Z item 4).  No CAD change, no hardware.
Mechanical, 2026-10-20, v2 (v1 7e7a15777f1e33b0 / json 6fd6420cdc529306 ACCEPTED by the lead 13:20Z, kept as jfwd_spring_v352_v1.py):
re-run on relaxation v6 ((a'') joins, k_b lo on (a'') SOAK70) and rows v3; otherwise v1.  CALC / DERIVED on relaxation v6 and catalogue data;
not physical approval.

Spring in series with the screw, OUTSIDE the joint's strength path when flat: the spring is flat (solid) from its flat load up, so at the
installation (2250..4096 N) and at every soak frame the joint is the v5 joint and every strength row is unchanged.  Only where the stiff
joint's screw force would fall below the (derated) flat load does the spring lift off flat by y and hold the screw force on its own
characteristic.  Bolt side with the spring (y = lift above flat, F_spr(y) = the derated catalogue force at deflection h0 - y):
    F_S = F_V + k_b (d_w - f + u - u0 + y),   F_S = F_spr(y) when y > 0,   y = 0 when F_V + k_b (d_w - f + u - u0) >= F_spr(0)
and the v5 equilibrium F_S = F_sh(u) + F_c(u) is solved for u (1-D root; exact piecewise-linear inner solve for y).  Everything else is v5
(wall cap, screw set, tilt, two firings, 24 cases, both k_b ends, seat and ring c).  The installed u0 is v5's (the spring is flat at F_V).

Catalogue characteristics (piecewise linear through the catalogue points, F = 0 at s = 0; no as-recalled formula):
 - A: DIN 2093 A 10 (10 x 5.2 x 0.5, l0 0.75, h0 0.25, group 1) in 17-7 PH: McMaster-Carr 96475K215 (maker not named) 'Deflection @
   Working Load 0.19 mm', 'Working Load 79 lb.', 'Flat Load 100 lbf', '17-7 PH Stainless Steel', 'DIN 2093'.  The same DIN size in
   Schnorr's 2024 brochure (001 500 A, spring steel) lists F 325 N at s 0.188: 7.5 % below McMaster's 351 N, so the basis takes McMaster's
   points x 325 / 351.4 (the lower catalogue value of the size).
 - B: Lesjofors 7909 DSS 10X5.2X0.4 (EN 10151 1.4310): F1 81 N / 0.075, F2 143 / 0.15, F3 192 / 0.225, Fn 236 / 0.3; F3 tol +48.0 / -14.4 N.
Derating to the characteristic used (phi multiplies the whole curve; the stroke is h0):
   phi = 0.925 (DIN EN 16983 / DIN 2093 group 1 load tolerance -7.5 %, Schnorr brochure p. 10 and Lesjofors 7909 F3 tol)
       x E(160 C) / E(20 C) = 0.946 (PROXY: engmat SS316L E 189.2 / 200 GPa; the spring maker's E(T) is TO-SOURCE)
       x (1 - R) with R the maker's relaxation at the flat stress after the soak (TO-SOURCE): R swept 0 / 10 / 20 / 40 / 60 / 80 %;
       the threshold R at which the 24-case first unseats is solved.
 Lift y versus the stroke h0: the 24-case lift is microns against h0 = 250 / 300 um, so only the curve near flat matters.
Sensitivity: one more interface (head / spring / spot face instead of head / spot face): embedding +3 and +8 um on both v5 levels
(sensitivity values, not sourced).
Geometry and bearing (lead 12:52Z items 3 and 4): screw length 10.2 + t; tip clearance with the TC-01 wall seated on the plug at the hole
(local gap 0: wall_min + t_min + 8.0 - L_max, the plug size drops out) and the engagement at local gap 0 and at the 0.078 gap bound with the
thread row at SOAK (rows v2 basis); head-on-spring and spring-on-flat bearing at SOAK N max; the under-head fillet against the spring ID;
the spring's centring on the d10.5 flat (CAD: checks/test_spring_r4s_v1.json, also the FD-04 envelope with the raised head).
Inputs: relax v5 and rows v2 (modules, sha recorded); no FE run."""
import json, math, hashlib, importlib.util, time
from pathlib import Path
import numpy as np

J = Path("/home/claude/work/mechanical/v352/jfwd")
OUT = J / "jfwd_spring_v352_v2.json"
_spec = importlib.util.spec_from_file_location("jfwd_relax_v352_v6", str(J / "jfwd_relax_v352.py"))
R = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(R)
assert "v6 (v5 95409d512c83bb44" in R.__doc__
sha = R.sha
STATE0 = R.state_s
K_C = R.K_C
LBF = 4.4482216152605
IN = "IN718 M5 x10 (RULED, ENG-HW-101-IN718)"
V5J = J / "jfwd_relax_v352_v6.json"


class Spring:
    def __init__(self, key, pts, t, l0, De, Di, material, part, src, scale=1.0, scale_note=""):
        self.key, self.t, self.l0, self.De, self.Di, self.material, self.part, self.src = key, t, l0, De, Di, material, part, src
        self.s = np.array([p[0] for p in pts], float)
        self.F = np.array([p[1] for p in pts], float) * scale
        self.h0 = float(self.s[-1])
        self.scale, self.scale_note = scale, scale_note
        assert abs(self.h0 - (l0 - t)) < 1e-9 and self.s[0] == 0.0 and self.F[0] == 0.0

    def F_flat(self, phi):
        return phi * float(self.F[-1])

    def bolt(self, FV, kb, D, phi):
        """screw force with the spring in series: (F_S, lift y).  F_S may be <= 0 (slack) only when the spring is fully free."""
        Flin = FV + kb * D
        if Flin >= self.F_flat(phi):
            return Flin, 0.0
        n = len(self.s) - 1
        for i in range(n, 0, -1):                       # segments from the flat end down: s in [s_{i-1}, s_i], y in [h0 - s_i, h0 - s_{i-1}]
            m = phi * (self.F[i] - self.F[i - 1]) / (self.s[i] - self.s[i - 1])
            yi, yim1 = self.h0 - self.s[i], self.h0 - self.s[i - 1]
            y = (phi * self.F[i] + m * yi - FV - kb * D) / (kb + m)
            if yi - 1e-12 <= y <= yim1 + 1e-12:
                return FV + kb * (D + y), y
        return FV + kb * (D + self.h0), self.h0             # spring free and the screw still short: slack (virtual)


SPRINGS = {
    "A_DIN2093_A10_17-7PH": Spring(
        "A_DIN2093_A10_17-7PH", [(0.0, 0.0), (0.19, 79.0 * LBF), (0.25, 100.0 * LBF)], 0.5, 0.75, 10.0, 5.2, "17-7 PH stainless steel",
        "McMaster-Carr 96475K215 (DIN 2093; maker not named by McMaster) = DIN 2093 A 10 (Schnorr 001 500 A in spring steel)",
        "https://www.mcmaster.com/product/96475K215/ (accessed 2026-10-20); Schnorr SCHNORR_Produktbroschuere_EN_2024-02.pdf p. 11 row "
        "'001 500 A 10,00 5,20 0,50 0,75 0,25 1 0,214 0,188 325 0,563' (https://www.schnorr-group.com/fileadmin/4_Downloads/Brochures/"
        "SCHNORR_Produktbroschuere_EN_2024-02.pdf, accessed 2026-10-20)",
        scale=325.0 / (79.0 * LBF), scale_note="McMaster points x 325 / 351.4: Schnorr's F(0.75 h0) for the same DIN size is 7.5 % lower"),
    "B_Lesjofors_7909_1.4310": Spring(
        "B_Lesjofors_7909_1.4310", [(0.0, 0.0), (0.075, 81.0), (0.15, 143.0), (0.225, 192.0), (0.30, 236.0)], 0.4, 0.7, 10.0, 5.2,
        "EN 10151 1.4310 (AISI 301)", "Lesjofors 7909 DSS 10X5.2X0.4",
        "https://shop.lesjofors.com/no/en-US/all-products/disc-springs-washers/dss-10x52x04-7909/ (accessed 2026-10-20): F1 81 N s1 0.075, "
        "F2 143 / 0.15, F3 192 / 0.225, Fn 236 / 0.3, F3 tol +48.0 / -14.4 N, Di tol +0.12, Do tol -0.15, L0 tol +0.10 / -0.05"),
}
PHI_TOL = 0.925
PHI_E = R.tab("SS316L", "E", 160.0) / R.tab("SS316L", "E", 20.0)
R_SWEEP = (0.0, 0.10, 0.20, 0.40, 0.60, 0.80)


def make_state(sp, phi):
    def st(FV, g, dw, dr, f, s, ksh, kb):
        FS, u, Fc, Fsh = STATE0(FV, g, dw, dr, f, s, ksh, kb)
        if FS >= sp.F_flat(phi):
            return FS, u, Fc, Fsh
        u0 = R.u_install(FV, g, ksh)

        def h(uu):
            B, _ = sp.bolt(FV, kb, dw - f + uu - u0, phi)
            return B - ksh * (g - s + dr - uu) - (K_C * (-uu) if uu < 0.0 else 0.0)
        lo, hi = u - 1.0, u
        assert h(hi) >= -1e-6 and h(lo) < 0.0
        for _ in range(120):
            mid = 0.5 * (lo + hi)
            lo, hi = (lo, mid) if h(mid) >= 0.0 else (mid, hi)
        uu = hi
        B, _ = sp.bolt(FV, kb, dw - f + uu - u0, phi)
        return B, uu, (K_C * (-uu) if uu < 0.0 else 0.0), ksh * (g - s + dr - uu)
    return st


def lift_of(sp, phi, FS):
    if FS >= sp.F_flat(phi):
        return 0.0
    if FS <= 0.0:
        return sp.h0
    return sp.h0 - float(np.interp(FS, phi * sp.F, sp.s))


def run_cfg(sp, phi, end, fam, emb_add=0.0):
    scr, ksh, kb, c = R.opt_params(IN, end, fam)
    R.state_s = make_state(sp, phi) if sp is not None else STATE0
    try:
        cases = {}
        for gn, g in R.GAPS.items():
            for iname, FV in R.INSTALL.items():
                for en, f0 in R.EMB.items():
                    f = f0 + emb_add
                    for gv, fr in R.ROWS4.items():
                        rec1, s1, d1 = R.fire(FV, g, f, fr, 0.0, 0.0, c, ksh, kb, scr, True, True)
                        rec2, s2, d2 = R.fire(FV, g, f, fr, s1, d1, c, ksh, kb, scr, True, True)
                        allr = rec1 + rec2
                        j = min(range(len(allr)), key=lambda k: allr[k]["FS"])
                        Ff = sp.F_flat(phi) if sp is not None else 0.0
                        hot = [q["FS"] for q in allr if q["T01"] >= 140.0]
                        j2 = max(range(len(rec2)), key=lambda k: rec2[k]["fib"])
                        rng = rec2[j2]["fib"] - min(q["fib_lo"] for q in rec2)
                        cases[f"{gn}|{iname}|{en}|{gv}"] = {
                            "F_S_min_N": round(allr[j]["FS"], 1), "at": ("firing_1" if j < len(rec1) else "firing_2", allr[j]["t"]),
                            "T01_T02_at_min_C": [round(allr[j]["T01"], 1), round(allr[j]["T02"], 1)],
                            "fit_at_min": "closed" if allr[j]["Fc"] > 0 else "open",
                            "slack_frames": int(sum(1 for q in allr if q["FS"] <= 0.0)),
                            "spring_active_frames": int(sum(1 for q in allr if q["FS"] < Ff)) if sp is not None else 0,
                            "lift_max_um": round(max(lift_of(sp, phi, q["FS"]) for q in allr) * 1e3, 3) if sp is not None else 0.0,
                            "cold_end_F_S_N": round(rec2[-1]["FS"], 1), "F_S_max_N": round(max(q["FS"] for q in allr), 1),
                            "hot_frames_T01_ge_140C": len(hot), "hot_F_S_min_N": round(min(hot), 1) if hot else None,
                            "solid_at_every_hot_frame": (min(hot) >= Ff) if hot else None,
                            "wall_set_end_um": round(s2 * 1e3, 3), "screw_set_end_um": round(d2 * 1e3, 3),
                            "shakedown_MS": round(2.0 * rec2[j2]["Rp"] / max(rng, 1e-9) - 1.0, 3)}
    finally:
        R.state_s = STATE0
    return cases, {"k_sh_N_mm": round(ksh), "k_b_N_mm": round(kb), "c": round(c, 5)}


def verdict(cases):
    j = min(cases, key=lambda k: cases[k]["F_S_min_N"])
    jc = min((k for k in cases if "2250" in k), key=lambda k: cases[k]["cold_end_F_S_N"])
    hot = [x["hot_F_S_min_N"] for x in cases.values() if x["hot_F_S_min_N"] is not None]
    return {"all_seated": all(x["slack_frames"] == 0 for x in cases.values()), "n_unseated": sum(1 for x in cases.values() if x["slack_frames"] > 0),
            "F_S_min_N": cases[j]["F_S_min_N"], "min_case": j, "min_at": cases[j]["at"], "fit_at_min": cases[j]["fit_at_min"],
            "n_cases_spring_active": sum(1 for x in cases.values() if x["spring_active_frames"] > 0),
            "lift_max_um": max(x["lift_max_um"] for x in cases.values()),
            "cold_end_F_S_min_2250_N": cases[jc]["cold_end_F_S_N"],
            "hot_F_S_min_N": min(hot) if hot else None, "solid_at_every_hot_frame_all_cases": all(x["solid_at_every_hot_frame"] in (True, None) for x in cases.values()),
            "F_S_max_N": max(x["F_S_max_N"] for x in cases.values()), "max_wall_set_um": max(x["wall_set_end_um"] for x in cases.values()),
            "max_screw_set_um": max(x["screw_set_end_um"] for x in cases.values()), "shakedown_min_MS": min(x["shakedown_MS"] for x in cases.values())}


def geometry_and_bearing():
    """screw length 10.2 + t, tip clearance with the TC-01 wall seated on the plug at the hole (lead 12:52Z item 3), engagement, thread
    shear at SOAK, head / spring / spot-face bearing at SOAK N max, fillet and centring geometry.  Uses the rows v2 module (published)."""
    _sw = importlib.util.spec_from_file_location("jfwd_in718_rows_v352", str(J / "jfwd_in718_rows_v352.py"))
    W = importlib.util.module_from_spec(_sw)
    _sw.loader.exec_module(W)
    R_FLAT_MIN, R_FLAT_MAX = W.R_FLAT_RANGE                     # d10.5 +/-0.2 (ISO 2768-m ASSUMED) on R31.75
    R_PLUG = W.R_PLUG_DWG                                        # f7 plug d57.140-57.170
    GAP_MIN, GAP_MAX = R.GAPS["H8f7_min"], R.GAPS["H8f7_max"]    # 239 (3): buildable radial gaps 0.040-0.078
    R_BORE = (R_PLUG[1] + GAP_MIN, R_PLUG[0] + GAP_MAX)          # TC-01 bore radius 28.625-28.648 (d57.25 H8)
    WALL = (R_FLAT_MIN - R_BORE[1], R_FLAT_MAX - R_BORE[0])      # TC-01 wall at the hole, flat to bore (local gap 0)
    T_TOL = (+0.02, -0.06)                                        # DIN EN 16983 / DIN 2093 thickness t 0.20-0.60 (Schnorr brochure 2024-02 p. 10)
    st = "SOAK"
    th = W.CELLS[st]["TC-02"]["thread_shear_An"]
    fsy = 0.577 * R.tab("AL6061-T6", "Fty", th["T_C"])
    henv = max(W.HS, key=lambda h: W.n_in(st, h))
    NS = {f"{FV:.0f}": W.n_in(st, henv, FV) for FV in (W.FV0, W.FVMAX)}
    # lead 13:20Z item 3 (rev 5 drawing rule): each J-FWD flat defined by its depth from the bore axis, wall at the hole >= 2.665
    # (r_flat >= 31.313 at the H8 maximum bore); tolerance proposed here: r_flat 31.313 +0.020 / 0 (milled in the hole set-up, depth
    # referenced to bore A, CMM-verified)
    RF5 = (31.313, 31.333)
    WALL5 = (RF5[0] - R_BORE[1], RF5[1] - R_BORE[0])
    BASES = {"v1: d10.5 +/-0.2 on the nominal OD (ASSUMED)": WALL, "rev 5: r_flat 31.313 +0.020/0 from the bore axis": WALL5}
    cases = {}
    for bname, WB in BASES.items():
        for name, L, tol, t_nom in (("no spring, 10.2 +/-0.1 (RULED 12:52Z)", 10.2, 0.1, 0.0),
                                    ("spring A t 0.5: 10.7 +/-0.1", 10.7, 0.1, 0.5), ("spring B t 0.4: 10.6 +/-0.1", 10.6, 0.1, 0.4)):
            tmin, tmax = (t_nom + T_TOL[1], t_nom + T_TOL[0]) if t_nom > 0 else (0.0, 0.0)
            clr0 = WB[0] + tmin + W.FULL_THREAD - (L + tol)                     # wall seated on the plug at the hole (local gap 0)
            clr_cad = W.eng_case(L, tol, (tmin, tmax))["tip_clearance_to_full_thread_end_min_mm"]
            Le0 = (L - tol) - (WB[1] + tmax)                                    # local gap 0 (the FE state: seat force > 0 at every step)
            LeG = (L - tol) - (WB[1] + GAP_MAX + tmax)                          # the largest buildable gap at the hole (bound)
            rows = {}
            for nm_, Le in (("local_gap_0", Le0), ("gap_0.078_bound", LeG)):
                An = W.strip_area(W.TH, Le - W.MOUTH)
                rows[nm_] = {"L_e_min_mm": round(Le, 3), "A_n_mm2": round(An, 2),
                             **{f"MS_y_{k}": round(fsy / (N / An) - 1.0, 3) for k, N in NS.items()}}
            cases[f"{bname} | {name}"] = {"wall_at_hole_mm": [round(x, 4) for x in WB], "L_nom_mm": L, "L_tol_mm": tol,
                                          "t_solid_min_max_mm": [round(tmin, 3), round(tmax, 3)],
                                          "tip_clearance_local_gap_0_mm": round(clr0, 3), "tip_ok_ge_0.2": clr0 >= W.TIP_CLEAR_MIN - 1e-9,
                                          "tip_clearance_v2_concentric_basis_mm": clr_cad, "engagement_and_thread_SOAK": rows}
    # flat completeness under the rev-5 rule: the flat's tangential chord 2 sqrt(R_OD^2 - r_flat^2) (the axial extent is the cutter, d10.5 +0.2/0)
    chord = lambda Rod, rf: 2.0 * math.sqrt(Rod ** 2 - rf ** 2)
    need = {"head dk 9.5 centred": 9.5, "head dk 9.5 + 2 x 0.337 (screw at the 5.5 hole wall)": 9.5 + 2 * 0.337, "spring OD 10 + 2 x 0.20 (route (i))": 10.4}
    comp = {"chord_at_r_flat_max_31.333_nominal_OD_63.5_mm": round(chord(31.75, RF5[1]), 3),
            "chord_at_r_flat_min_31.313_nominal_OD_mm": round(chord(31.75, RF5[0]), 3),
            "OD_min_for_complete_flat_at_r_flat_max_mm": {k: round(2.0 * math.sqrt(RF5[1] ** 2 + (v / 2.0) ** 2), 3) for k, v in need.items()},
            "r_flat_max_for_complete_flat_at_nominal_OD_mm": {k: round(math.sqrt(31.75 ** 2 - (v / 2.0) ** 2), 4) for k, v in need.items()},
            "note": ("tangentially the cylinder falls away beyond the chord (no wall, about 9.5 deg), so a part wider than the chord loses a sliver of "
                     "support there but is not tilted; axially the pocket wall (up to 0.437) bounds the flat at the cutter diameter")}
    geo_rule = {"proposal": "r_flat 31.313 +0.020/0 from the bore axis A (each J-FWD flat; profile 0.01 to be confirmed with the shop)",
                "wall_at_hole_mm": [round(x, 4) for x in WALL5], "flat_completeness": comp}
    geo = {"basis": {"wall_at_hole_flat_to_bore_mm": [round(x, 4) for x in WALL], "r_flat_mm": [round(R_FLAT_MIN, 4), round(R_FLAT_MAX, 4)],
                     "r_bore_mm_d57.25H8": [round(x, 4) for x in R_BORE], "full_thread_mm": W.FULL_THREAD, "mouth_mm": W.MOUTH,
                     "t_tol_mm": T_TOL, "t_tol_src": "Schnorr SCHNORR_Produktbroschuere_EN_2024-02.pdf p. 10 (DIN EN 16983, previously DIN 2093): t 0.20-0.60 +0.02 / -0.06",
                     "thread_row": f"tau = N / A_n at SOAK (N {LBL_(henv)} IN718, {', '.join(f'{k}: {v:.1f} N' for k, v in NS.items())}); Fsy = 0.577 Fty "
                                   f"(AL6061-T6, {th['T_C']} C) = {fsy:.1f} MPa; A_n = jfwd_v352 strip area at L_e - 0.5 mouth",
                     "tip_rule": "tip >= 0.2 mm short of the 8.0 full-thread end; local gap 0 = wall_min + t_min + 8.0 - L_max (independent of the plug size)",
                     "OD_tolerance_note": "R_flat from the d10.5 +/-0.2 spot face on the nominal OD R31.75 (the drawing OD tolerance moves the wall 1:1)"},
           "cases": cases, "rev5_flat_depth_rule": geo_rule}
    # bearing at SOAK N max (flat spring = flat washer): head on spring, spring on the anodised 6061 flat
    dk_min, dk_max = 9.14, 9.5                  # ISO 7380-1 M5 dk (fasten.it DIN EN ISO 7380-1 table, accessed 2026-10-20)
    hole = 5.5
    bear = {}
    N4096, N3750 = NS["4096"], NS["3750"]
    Fty_in = R.tab("IN718", "Fty", 127.0)       # screw at SOAK (FEA3D jfwd_deck: screw 127.0 C)
    for d_in, tag in ((5.2, "spring ID 5.2 (fillet cleared, da <= 5.2)"), (5.7, "da 5.7 (ISO 4762-like, AS RECALLED, TO-VERIFY for ISO 7380-1)")):
        A = math.pi / 4.0 * (dk_min ** 2 - d_in ** 2)
        bear[f"head_on_spring|{tag}"] = {"A_mm2": round(A, 2), "sigma_3750_MPa": round(N3750 / A, 1), "sigma_4096_MPa": round(N4096 / A, 1),
                                         "MS_vs_IN718_Fty_127C": round(Fty_in / (N4096 / A) - 1.0, 3), "IN718_Fty_127C_MPa": round(Fty_in, 1),
                                         "spring_side": "17-7 PH condition / Fty: TO-SOURCE from the maker (the spring temper is far above 0.2 GPa)"}
    for od, tag in ((9.85, "spring OD min 9.85"), (10.0, "spring OD max 10.0")):
        A = math.pi / 4.0 * (od ** 2 - hole ** 2)
        bear[f"spring_on_flat|{tag}"] = {"A_mm2": round(A, 2), "sigma_4096_MPa": round(N4096 / A, 1),
                                         "area_ratio_vs_head_annulus_47.12": round(A / (math.pi / 4.0 * (9.5 ** 2 - hole ** 2)), 4)}
    bear["TC01_flat_bearing_row"] = ("NO CREDIT TAKEN for load spreading through the 0.44-0.52 mm flat spring: the rows-v2 TC-01 flat bearing stands "
                                     "(SOAK +0.386 / +0.329); the spring annulus on the flat is 1.11-1.16 x the head annulus (information)")
    bear["spring_stress_at_flat"] = ("TO-SOURCE: the maker's sigma_OM at s = h0 for DIN 2093 A 10 and its static limit (McMaster gives none; Schnorr's 2024 "
                                     "brochure p. 11 lists F and s at 0.75 h0 only); a flattened spring carries the excess load as a flat washer")
    # fillet and centring
    major = (4.826, 4.976)                      # M5 6g major (jfwd_v352 thread table basis)
    Di = (5.2, 5.32)                            # H12 per Lesjofors 7909 'Di tol +0.12' and Schnorr p. 10 (3-6 mm: +0.12 / 0)
    fil = {"spring_ID_mm": Di,
           "fillet_from_full_major_neck": {"r_min_mm": 0.2, "da_min_mm": round(major[1] + 2 * 0.2, 3),
                                           "verdict": "da >= 5.376 > ID 5.2: the spring inner edge would sit on the fillet"},
           "fillet_from_rolled_blank_neck": {"neck_d_mm": "<= 4.75 (rolled-thread blank about d2 4.48)", "r_mm": "0.2-0.3", "da_max_drawn_mm": 5.15,
                                             "verdict": "clears ID 5.2 with r kept >= 0.2: the ENG-HW-101-IN718 drawing must state neck d <= 4.75, r 0.2-0.3, da max 5.15"},
           "ISO_7380-1_r_min_and_da_max": "TO-VERIFY (AS RECALLED r min 0.2; da max 5.7 is the ISO 4762 M5 value); fasten.it's ISO 7380-1 table lists dk 9.5/9.14, k 2.75/2.5, s 3, t 1.56, w 0.38 only"}
    e_spring = (Di[1] - major[0]) / 2.0
    e_hole = (hole - major[0]) / 2.0
    cen = {"spring_play_on_thread_max_mm": round(e_spring, 3), "screw_float_in_5.5_hole_max_mm": round(e_hole, 3),
           "worst_eccentricity_mm": round(e_spring + e_hole, 3),
           "tolerable_eccentricity_mm": {"CAD nominal d10.5 sharp": round((10.5 - 10.0) / 2.0, 3),
                                         "drawing d10.3 min, R0.1 corner (ASSUMED)": round((10.3 - 0.2 - 10.0) / 2.0, 3),
                                         "d10.5 +0.2/0, R <= 0.05": round((10.5 - 0.1 - 10.0) / 2.0, 3)},
           "CAD_check": "checks/test_spring_r4s_v1.json: spring d10 x 0.5 on the d10.5 flat, common volume with TC-01 0.002 mm3 (noise) up to e 0.25; "
                        "0.345 mm3 at e 0.40 and 0.886 mm3 at e 0.584 along z (the pocket wall, 0.437 deep at the z extremes); 0.049 / 0.181 mm3 tangential",
           "verdict": "FOUND: with an OD 10 spring centred on the thread, the worst stack puts its rim on the pocket wall (tilt); the d10.5 spot face holds it "
                      "only if the screw float in the hole (drawing positional tolerances, TO-DEFINE) plus the spring play stays <= 0.05 mm at the drawing "
                      "minimum (0.25 at the CAD nominal)"}
    return {"geometry_length_tip_engagement": geo, "bearing_SOAK_N_max": bear, "fillet": fil, "centring_on_the_d10.5_flat": cen,
            "rows_module": {"path": str(J / "jfwd_in718_rows_v352.py"), "sha256_16": sha(J / "jfwd_in718_rows_v352.py")}}


def LBL_(h):
    return R.LABEL[h]


if __name__ == "__main__":
    t0 = time.time()
    res = {"id": "jfwd_spring_v352", "version": "v2", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
           "inputs": {"relax_v6_module": {"path": str(J / "jfwd_relax_v352.py"), "sha256_16": sha(J / "jfwd_relax_v352.py")},
                      "relax_v6_json": {"path": str(V5J), "sha256_16": sha(V5J)}},
           "k_b_bracket_N_mm": {k: round(v) for k, v in R.KB.items()},
           "springs": {k: {"part": sp.part, "material": sp.material, "De_Di_t_l0_h0_mm": [sp.De, sp.Di, sp.t, sp.l0, sp.h0],
                           "catalogue_points_s_mm_F_N": [[round(a, 3), round(b, 1)] for a, b in zip(sp.s, sp.F / sp.scale)],
                           "basis_scale": round(sp.scale, 4), "basis_scale_note": sp.scale_note, "F_flat_basis_N": round(float(sp.F[-1]), 1),
                           "slope_near_flat_basis_N_per_mm": round(float((sp.F[-1] - sp.F[-2]) / (sp.s[-1] - sp.s[-2])), 1), "src": sp.src}
                       for k, sp in SPRINGS.items()},
           "derating": {"phi_tol": PHI_TOL, "phi_E_160C_proxy": round(PHI_E, 4), "relaxation_R": "TO-SOURCE (maker's data at the flat stress, ~160 C)",
                        "R_swept": list(R_SWEEP)}}
    # harness check: no spring reproduces v5 (IN718, both ends, both families)
    v5 = json.loads(V5J.read_text())["verdict_24"]
    chk = {}
    for end in R.KB:
        for fam in ("seat", "ring"):
            cs, prm = run_cfg(None, 1.0, end, fam)
            v = verdict(cs)
            ref = v5[f"{IN}|{end}|{fam}"]
            chk[f"{end}|{fam}"] = {"F_S_min_N": v["F_S_min_N"], "n_unseated": v["n_unseated"], "v5_F_S_min_N": ref["F_S_min_N"], "v5_n_unseated": ref["n_unseated"],
                                   "cold_end_2250_N": v["cold_end_F_S_min_2250_N"], "v5_cold_end_2250_N": ref["cold_end_F_S_min_2250_N"], **prm}
            assert abs(v["F_S_min_N"] - ref["F_S_min_N"]) <= 1.0 and v["n_unseated"] == ref["n_unseated"], (end, fam, v["F_S_min_N"], ref["F_S_min_N"])
    res["harness_check_no_spring_vs_v6"] = chk
    print("harness ok", {k: (x["F_S_min_N"], x["n_unseated"]) for k, x in chk.items()}, round(time.time() - t0, 1), flush=True)
    # spring runs
    runs, cases_keep = {}, {}
    for sk, sp in SPRINGS.items():
        for Rr in R_SWEEP:
            phi = PHI_TOL * PHI_E * (1.0 - Rr)
            for end in R.KB:
                for fam in ("seat", "ring"):
                    cs, prm = run_cfg(sp, phi, end, fam)
                    v = verdict(cs)
                    v.update({"phi": round(phi, 4), "F_flat_derated_N": round(sp.F_flat(phi), 1), **prm})
                    runs[f"{sk}|R{Rr:.2f}|{end}|{fam}"] = v
                    if Rr in (0.0, 0.20):
                        cases_keep[f"{sk}|R{Rr:.2f}|{end}|{fam}"] = cs
            print(sk, Rr, {f"{e}|{fm}": (runs[f"{sk}|R{Rr:.2f}|{e}|{fm}"]["F_S_min_N"], runs[f"{sk}|R{Rr:.2f}|{e}|{fm}"]["lift_max_um"],
                                         runs[f"{sk}|R{Rr:.2f}|{e}|{fm}"]["cold_end_F_S_min_2250_N"]) for e in R.KB for fm in ("seat", "ring")},
                  round(time.time() - t0, 1), flush=True)
    res["runs"] = runs
    res["cases_24_R0_and_R20"] = cases_keep
    # threshold relaxation: the largest R with all 24 seated at both ends, seat family (the governing one), per spring
    thr = {}
    for sk, sp in SPRINGS.items():
        ok = lambda Rr: all(verdict(run_cfg(sp, PHI_TOL * PHI_E * (1.0 - Rr), e, "seat")[0])["all_seated"] for e in R.KB)
        lo, hi = 0.80, 0.9999
        if not ok(lo):
            thr[sk] = {"R_max": None, "note": "unseats already at R 0.80"}
            continue
        if ok(hi):
            thr[sk] = {"R_max": ">= 0.9999", "note": "seated down to a spring with 0.01 % of its derated flat load"}
            continue
        for _ in range(30):
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if ok(mid) else (lo, mid)
        thr[sk] = {"R_max": round(lo, 5), "F_flat_at_R_max_N": round(sp.F_flat(PHI_TOL * PHI_E * (1.0 - lo)), 2)}
    res["relaxation_threshold_seat_family"] = thr
    print("threshold", thr, round(time.time() - t0, 1), flush=True)
    # embedding sensitivity (one more interface), spring A at R 0.20, both ends, both families
    emb = {}
    spA = SPRINGS["A_DIN2093_A10_17-7PH"]
    for add in (0.003, 0.008):
        for end in R.KB:
            for fam in ("seat", "ring"):
                v = verdict(run_cfg(spA, PHI_TOL * PHI_E * 0.80, end, fam, emb_add=add)[0])
                emb[f"+{add * 1e3:.0f}um|{end}|{fam}"] = {k: v[k] for k in ("all_seated", "F_S_min_N", "min_case", "lift_max_um", "cold_end_F_S_min_2250_N")}
        nos = {}
        for end in R.KB:
            v = verdict(run_cfg(None, 1.0, end, "seat", emb_add=add)[0])
            nos[end] = {"F_S_min_N": v["F_S_min_N"], "n_unseated": v["n_unseated"], "cold_end_F_S_min_2250_N": v["cold_end_F_S_min_2250_N"]}
        emb[f"+{add * 1e3:.0f}um|no_spring_seat"] = nos
    res["embedding_sensitivity_spring_A_R0.20"] = emb
    print("emb", {k: (v.get("F_S_min_N"), v.get("cold_end_F_S_min_2250_N")) for k, v in emb.items() if "no_spring" not in k}, round(time.time() - t0, 1), flush=True)
    res.update(geometry_and_bearing())
    CK = Path("/home/claude/work/mechanical/v352/checks/test_spring_r4s_v1.json")
    ck = json.loads(CK.read_text())
    res["cad_envelope_check"] = {"path": str(CK), "sha256_16": sha(CK),
                                 "min_FD04_mm": {k: v["min_FD04_all_poses_mm"] for k, v in ck["envelopes"].items()},
                                 "min_other_mm": {k: v["min_other_all_poses_mm"] for k, v in ck["envelopes"].items()},
                                 "note": ("FD-04 clearance is axial (foil top 1 mm below the head edge): the head stays 1.000 mm at every pose for "
                                          "t 0.40-0.52; the spring (d10) is 1.648-1.755 mm from FD-04; no FD-04 trim, no new RC-04 input "
                                          "(the RC-04 re-check of the earlier trim stays TO-DO)")}
    print("geometry", json.dumps({k: (v["tip_clearance_local_gap_0_mm"], v["engagement_and_thread_SOAK"]) for k, v in res["geometry_length_tip_engagement"]["cases"].items()}),
          flush=True)
    res["t_run_s"] = round(time.time() - t0, 1)
    s = json.dumps(res, indent=1, default=float)
    OUT.write_text(s)
    print(OUT.name, hashlib.sha256(s.encode()).hexdigest()[:16], res["t_run_s"])

"""J-FWD disc spring under the head (route (i), lead 16:53Z R2), v4: RE-STATED AT THE J-F1 BAND CAPPED AT 3750 N (lead 17:55:55Z F1:
'Re-state the rows that depend on the minimum at the new minimum: about 2060 N with today's K range scaled by 3750 / 4096, or the J-F1
lot result.  That covers the cold-after-embedding seating and the K_js5 rows.  If any turns negative, stop and tell me.').  Mechanical,
2026-10-20, v4 (v3 04f3079e634c77da / json 150900bd77dc5fc9 kept as jfwd_spring_v352_v3.py).  CALC / DERIVED; not physical approval.
v4: the harness check (no spring) still reproduces relax v7 at its own installation keys (2250 / 4096 N); every spring run after it is at
the J-F1 band 2057.6 / 3750 N (torque 3750 x 0.1465 x 5 = 2746.9 N mm on today's K window 0.1465-0.267; the J-F1 lot result replaces the
band when it exists): the R sweep, the lead-16:07Z table, the relaxation threshold and the embedding sensitivity; the cold end is quoted
at the J-F1 minimum (2057.6 N); v3's 2250 / 4096 N values are carried as information and the stop test (lead F1) compares them.
Geometry and bearing are re-based on rows v7 (THE ROW route (i): M5 x 10.7 +/-0.1 over spring A, A_n 67.93 mm2; spring B on 10.6; the
3750 N column governs, 4096 N is information); the head-on-spring bearing uses the adopted head form (F3: da 5.55-5.80, dk 9.14 min);
the route-(i) centring / overhang block is SUPERSEDED by rows v7 route_i_spring_footprint and the CAD check test_rev5_jfwd_v2 (F2
registered stack 0.4865, F4 axial 0.3705, full float 0.557), carried here by reference; the fillet text is the adopted F3 form (the v3
'rolled-blank neck, da max 5.15' text is withdrawn); the CAD envelope is the rev-5 check v2 (c) (the r4s v1 check is kept as record).
v3 notes follow.
J-FWD disc spring under the head: paper scoping (lead 12:09Z item 4 (iii); lead 12:52Z item 4).  No CAD change, no hardware.
Mechanical, 2026-10-20, v3 (v2 6301f56f42d4a7ae / json 1df11254a2965d56 kept as jfwd_spring_v352_v2.py; v1 7e7a15777f1e33b0 / json
6fd6420cdc529306 ACCEPTED by the lead 13:20Z, kept as jfwd_spring_v352_v1.py).  CALC / DERIVED on relaxation v7 and catalogue data; not
physical approval.
v3 (lead 15:37Z order item 1 'spring v3', lead 16:07Z item 5): re-run on relax v7 (FEA3D's ADOPTED envelope v3 0872de4ea7e3601d, 'worst
computed instance, not a proven bound'; (b2) and '(b2) rep' join; IN718 k_b hi 1,100,023 N/mm on (b2) SOAK70, lo 418,365) and rows v6
(THE ROW thread basis: drawn M5 x 10.2 +/-0.1 on the rev-5 flat, TC-01 wall seated, 0.078 gap bound).  Shows, per spring, R 0 / 0.2 / 0.4
(and the full sweep), both k_b ends and both families: all 24 seated or not, the minimum screw force, the lift, and whether the spring is
solid (flat) at every hot frame (T01 >= 140 C).  Geometry on the rev-5 basis (length 10.2 + t, tip with the wall seated, engagement at
the gap bound, the thread row at every soak state), bearing at the largest soak screw force, and route (i) (drawn pilot) re-stated with
the C1 (g) / (h) rulings (hole 5.5 +0.12/0, position 0.10 dia to A|B, spot face coaxial 0.10): the z-direction centring stack and the
14:01Z tangential overhang finding (input), with geometry PROPOSALS where route (i) needs one (propose, do not apply).
v2 notes follow (re-run on relaxation v6 ((a'') joins, k_b lo on (a'') SOAK70) and rows v3; otherwise v1).

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
OUT = J / "jfwd_spring_v352_v4.json"
ROWS7J, ROWS7_SHA16 = J / "jfwd_in718_rows_v352_v7.json", "6113d28b64d0dba5"
V3J, V3J_SHA16 = J / "jfwd_spring_v352_v3.json", "150900bd77dc5fc9"
CK5, CK5_SHA16 = Path("/home/claude/work/mechanical/v352/checks/test_rev5_jfwd_v2.json"), "32c41e1e207f9d64"
_spec = importlib.util.spec_from_file_location("jfwd_relax_v352_v7", str(J / "jfwd_relax_v352.py"))
R = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(R)
assert "v7 (v6 9465eaeac9af407f" in R.__doc__
sha = R.sha
STATE0 = R.state_s
K_C = R.K_C
LBF = 4.4482216152605
IN = R.IN_KEY
V5J = J / "jfwd_relax_v352_v7.json"


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
    jc = min((k for k in cases if k.split("|")[1].startswith("J-F1_min")), key=lambda k: cases[k]["cold_end_F_S_N"])
    hot = [x["hot_F_S_min_N"] for x in cases.values() if x["hot_F_S_min_N"] is not None]
    return {"all_seated": all(x["slack_frames"] == 0 for x in cases.values()), "n_unseated": sum(1 for x in cases.values() if x["slack_frames"] > 0),
            "F_S_min_N": cases[j]["F_S_min_N"], "min_case": j, "min_at": cases[j]["at"], "fit_at_min": cases[j]["fit_at_min"],
            "n_cases_spring_active": sum(1 for x in cases.values() if x["spring_active_frames"] > 0),
            "lift_max_um": max(x["lift_max_um"] for x in cases.values()),
            "cold_end_F_S_min_at_J_F1_min_N": cases[jc]["cold_end_F_S_N"], "cold_end_case": jc,
            "hot_F_S_min_N": min(hot) if hot else None, "solid_at_every_hot_frame_all_cases": all(x["solid_at_every_hot_frame"] in (True, None) for x in cases.values()),
            "F_S_max_N": max(x["F_S_max_N"] for x in cases.values()), "max_wall_set_um": max(x["wall_set_end_um"] for x in cases.values()),
            "max_screw_set_um": max(x["screw_set_end_um"] for x in cases.values()), "shakedown_min_MS": min(x["shakedown_MS"] for x in cases.values())}


def seg_area(R_, d):
    """area of the circle of radius R_ beyond a straight edge at distance d from its centre (0 if d >= R_)"""
    if d >= R_:
        return 0.0
    if d <= -R_:
        return math.pi * R_ ** 2
    return R_ ** 2 * math.acos(d / R_) - d * math.sqrt(R_ ** 2 - d ** 2)


def geometry_and_bearing():
    """v3: rev-5 basis (rows v6 eng_rev5 = THE ROW basis): screw length 10.2 + t, tip with the TC-01 wall seated (wall min), engagement at
    local gap 0 and at the 0.078 gap bound (THE ROW), the thread row at every soak state on the envelope; head / spring / flat bearing at
    the largest soak screw force; fillet; route (i) centring with C1 (g) / (h); the 14:01Z tangential overhang."""
    _sw = importlib.util.spec_from_file_location("jfwd_in718_rows_v352", str(J / "jfwd_in718_rows_v352.py"))
    W = importlib.util.module_from_spec(_sw)
    _sw.loader.exec_module(W)
    assert W.A_THE_ROW == 67.93 and W.THE_ROW_NS["A_n_gap_bound_mm2"] == 68.13 and W.THE_ROW_B["A_n_gap_bound_mm2"] == 67.93, W.A_THE_ROW
    assert sha(J / "jfwd_in718_rows_v352.py") == "880ffe58c8af05e6", "rows v7 module"
    T_TOL = (+0.02, -0.06)                                        # DIN EN 16983 / DIN 2093 thickness t 0.20-0.60 (Schnorr brochure 2024-02 p. 10)
    SOAK = ("SOAK70", "SOAK", "SOAK52")
    NS, FSY, HENV = {}, {}, {}
    for st in SOAK:
        th = W.CELLS[st]["TC-02"]["thread_shear_An"]
        FSY[st] = (0.577 * R.tab("AL6061-T6", "Fty", th["T_C"]), th["T_C"])
        HENV[st] = max(W.R.H_at(st), key=lambda h: W.n_in(st, h))
        NS[st] = {f"{FV:.0f}": W.n_in(st, HENV[st], FV) for FV in (W.FV0, W.FVMAX)}
    cases = {}
    for name, L, tol, t_nom in (("no spring, 10.2 +/-0.1 (RULED 12:52Z, THE ROW)", 10.2, 0.1, 0.0),
                                ("spring A t 0.5: 10.7 +/-0.1", 10.7, 0.1, 0.5), ("spring B t 0.4: 10.6 +/-0.1", 10.6, 0.1, 0.4)):
        tt = (t_nom + T_TOL[1], t_nom + T_TOL[0]) if t_nom > 0 else (0.0, 0.0)
        e = W.eng_rev5(L, tol, tt)
        rows = {}
        for st in SOAK:
            fsy, T2 = FSY[st]
            rows[st] = {"N_from": R.LABEL[HENV[st]], "T_C": T2, "Fsy_MPa": round(fsy, 1),
                        **{f"MS_y_{k}_gap_bound_ROW": round(fsy / (N / e["A_n_gap_bound_mm2"]) - 1.0, 3) for k, N in NS[st].items()},
                        **{f"MS_y_{k}_gap0_info": round(fsy / (N / e["A_n_gap0_mm2"]) - 1.0, 3) for k, N in NS[st].items()}}
        gmin = min((rows[st][f"MS_y_{k}_gap_bound_ROW"], st, k) for st in SOAK for k in ("3750",))
        gmin4 = min((rows[st]["MS_y_4096_gap_bound_ROW"], st, "4096") for st in SOAK)
        cases[name] = {"t_solid_min_max_mm": [round(x, 3) for x in tt], **e, "thread_row_soak_states": rows,
                       "thread_row_min": {"MS_y": gmin[0], "state": gmin[1], "preload_N": gmin[2], "column": "GOVERNING (J-F1 cap 3750 N)"},
                       "thread_row_min_4096_info": {"MS_y": gmin4[0], "state": gmin4[1], "column": "INFORMATION (superseded maximum)"}}
    geo = {"basis": {"rule": "rows v7 eng_rev5 (as v6): r_flat 31.313 +0.020/0 from the bore axis (rev 5), TC-01 bore 28.625-28.648 (d57.25 H8 on the "
                             "f7 plug with the 0.040-0.078 radial gaps), wall at the hole 2.665-2.708; L_e min = L_min - wall_max - t_max (local "
                             "gap 0) and - 0.078 more at the gap bound (THE ROW); tip = wall_min + t_min + 8.0 - L_max >= 0.2",
                     "t_tol_mm": T_TOL, "t_tol_src": "Schnorr SCHNORR_Produktbroschuere_EN_2024-02.pdf p. 10 (DIN EN 16983, previously DIN 2093): t 0.20-0.60 +0.02 / -0.06",
                     "thread_row": "tau = N_IN718 (envelope instance per state) / A_n; Fsy = 0.577 Fty (AL6061-T6, FEA3D's TC-02 thread temperature)",
                     "soak_N_IN718_N": {st: {k: round(v, 1) for k, v in NS[st].items()} for st in SOAK}},
           "cases": cases}
    # bearing at the largest soak N (flat spring = flat washer): head on spring, spring on the anodised 6061 flat
    stmax = max(SOAK, key=lambda st: NS[st]["3750"])
    N4096, N3750 = NS[stmax]["4096"], NS[stmax]["3750"]
    dk_min = 9.14                               # ISO 7380-1 M5 dk min (fasten.it DIN EN ISO 7380-1 table, accessed 2026-10-20)
    hole = 5.62                                 # C1 (g) Option A: d5.5 +0.12/0 (H12), lead 14:34Z
    Fty_in = R.tab("IN718", "Fty", 127.0)       # screw at SOAK (FEA3D jfwd_deck: screw 127.0 C)
    bear = {"state": stmax, "N_from": R.LABEL[HENV[stmax]], "N_3750_N": round(N3750, 1), "N_4096_N": round(N4096, 1)}
    for d_in, tag in ((W.DA_HEAD_MAX, "da 5.80 max (F3 ADOPTED: undercut fillet r 0.2-0.3 into the head, da 5.55-5.80)"),
                      (5.55, "da 5.55 min (F3), information")):
        A = math.pi / 4.0 * (dk_min ** 2 - d_in ** 2)
        bear[f"head_on_spring|{tag}"] = {"A_mm2": round(A, 2), "sigma_3750_MPa": round(N3750 / A, 1), "sigma_4096_MPa_info": round(N4096 / A, 1),
                                         "MS_vs_IN718_Fty_127C_3750": round(Fty_in / (N3750 / A) - 1.0, 3),
                                         "MS_vs_IN718_Fty_127C_4096_info": round(Fty_in / (N4096 / A) - 1.0, 3), "IN718_Fty_127C_MPa": round(Fty_in, 1),
                                         "spring_side": "1.4568 (17-7 PH) condition / Fty: TO-SOURCE from the maker (TO-QUOTE DK-6400)"}
    assert abs(math.pi / 4.0 * (dk_min ** 2 - W.DA_HEAD_MAX ** 2) - W.A_HEAD_SPRING) < 1e-9
    # ---- route (i) centring / overhang: SUPERSEDED by rows v7 route_i_spring_footprint and the CAD check v2 (carried by reference)
    route_i = {"SUPERSEDED_by": {"rows_v7": {"path": str(ROWS7J), "sha256_16": sha(ROWS7J), "block": "route_i_spring_footprint"},
                                 "cad_check_v2": {"path": str(CK5), "sha256_16": sha(CK5), "items": "(e) supported area, (h) positional stack"}},
               "rulings": "lead 17:55:55Z CAD CHECK accepted; F2 registration ADOPTED (tangential basis = registered stack 0.4865); F4 axial basis "
                          "0.3705 ACCEPTED (margin 0.18 to the tolerable 0.55); full float 0.557 is the under-head basis (F1)",
               "A_supp_mm2_by_basis": dict(W.A_SPR), "offsets_t_z_mm_by_basis": {k: v for k, v in W.UH_BASES.items()},
               "quoted_flat_basis": W.QUOTED_FLAT_BASIS, "quoted_under_head_basis": W.QUOTED_UH_BASIS,
               "PROPOSALS_status": {"P(i)-1 cutter d11.2": "taken into rev 5 and CAD-checked (test_rev5_jfwd_v2 (a)-(d)): accepted 17:55:55Z",
                                    "P(i)-2 overhang accepted": "carried: the supported area at each basis is in rows v7 (no spreading credit)",
                                    "P(i)-3 smaller custom spring": "not taken (route (i) baseline: Schnorr 001 500 A in 1.4568, R2)"}}
    # fillet / pilot: the adopted head form (F3, lead 17:55:55Z); the v3 'rolled-blank neck, da max 5.15' text is WITHDRAWN
    fil = {"spring_ID_mm": (5.2, 5.32),
           "F3_adopted": {"fillet": "undercut fillet r 0.2-0.3 into the head, entirely above the bearing face",
                          "pilot": "5.15 h9 x 0.25-0.30 long, coaxial to the pitch cylinder within d0.02 (TO-CONFIRM)",
                          "da_mm": [5.55, 5.80], "da_note": "stated on the drawing (F3)",
                          "lengths": "spring A on L 10.7 +/-0.1, spring B on L 10.6 +/-0.1: L_e 7.294 (THE ROW)",
                          "pilot_vs_flat": "the pilot clears the flat by >= 0.04 with spring B (t 0.34 min) and >= 0.14 with spring A (t 0.44 min)"},
           "head_fillet_rows": "the screw's own head-to-shank fillet: static and LCF rows on the FE head-end moment (F3 ADD), in jfwd_head_fillet v1",
           "WITHDRAWN_v3": "fillet_from_rolled_blank_neck (neck d <= 4.75, da max 5.15) and the 16:46Z pilot text: superseded by F3"}
    return {"geometry_length_tip_engagement": geo, "bearing_max_soak_N": bear, "fillet": fil, "route_i_pilot_centring_and_overhang": route_i,
            "rows_module": {"path": str(J / "jfwd_in718_rows_v352.py"), "sha256_16": sha(J / "jfwd_in718_rows_v352.py")}}


def LBL_(h):
    return R.LABEL[h]


if __name__ == "__main__":
    t0 = time.time()
    res = {"id": "jfwd_spring_v352", "version": "v4", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
           "inputs": {"relax_v7_module": {"path": str(J / "jfwd_relax_v352.py"), "sha256_16": sha(J / "jfwd_relax_v352.py")},
                      "relax_v7_json": {"path": str(V5J), "sha256_16": sha(V5J)},
                      "fea3d_soak_envelope": {"path": str(R.F_ENV), "sha256_16": sha(R.F_ENV)}},
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
            chk[f"{end}|{fam}"] = {"F_S_min_N": v["F_S_min_N"], "n_unseated": v["n_unseated"], "relax_v7_F_S_min_N": ref["F_S_min_N"],
                                   "relax_v7_n_unseated": ref["n_unseated"], "cold_end_2250_N": v["cold_end_F_S_min_at_J_F1_min_N"],
                                   "relax_v7_cold_end_2250_N": ref["cold_end_F_S_min_2250_N"], **prm}
            assert abs(v["F_S_min_N"] - ref["F_S_min_N"]) <= 1.0 and v["n_unseated"] == ref["n_unseated"], (end, fam, v["F_S_min_N"], ref["F_S_min_N"])
            assert abs(v["cold_end_F_S_min_at_J_F1_min_N"] - ref["cold_end_F_S_min_2250_N"]) <= 1.0, (end, fam, v["cold_end_F_S_min_at_J_F1_min_N"])
    res["harness_check_no_spring_vs_v7"] = chk
    print("harness ok", {k: (x["F_S_min_N"], x["n_unseated"]) for k, x in chk.items()}, round(time.time() - t0, 1), flush=True)
    # v4: the J-F1 band capped at 3750 N (lead 17:55:55Z F1)
    K_WIN, D_NOM, F_CAP = (0.1465, 0.267), 5.0, 3750.0
    T_JF1 = F_CAP * K_WIN[0] * D_NOM
    F_MIN = T_JF1 / (K_WIN[1] * D_NOM)
    assert sha(ROWS7J) == ROWS7_SHA16 and sha(V3J) == V3J_SHA16
    _r7 = json.loads(ROWS7J.read_text())
    assert abs(F_MIN - _r7["J_F1"]["minimum_N_today_K_window"]) < 0.05 and _r7["J_F1"]["maximum_N"] == F_CAP, "rows v7 J_F1 band"
    INSTALL_V3 = dict(R.INSTALL)
    R.INSTALL = {"J-F1_min_2058": F_MIN, "J-F1_max_3750": F_CAP}
    res["J_F1_band"] = {"cap_N": F_CAP, "min_N": round(F_MIN, 1), "torque_Nmm": round(T_JF1, 1), "K_window": list(K_WIN),
                        "rule": "lead 17:55:55Z F1: J-F1 sets the flight-lot torque so the lot's K_min gives <= 3750 N; the minimum is the lot's "
                                "K_max result (today's K window: 2057.6 N); every spring run below is at this band",
                        "harness_install_relax_v7": INSTALL_V3, "runs_install": R.INSTALL}
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
                                         runs[f"{sk}|R{Rr:.2f}|{e}|{fm}"]["cold_end_F_S_min_at_J_F1_min_N"]) for e in R.KB for fm in ("seat", "ring")},
                  round(time.time() - t0, 1), flush=True)
    res["runs"] = runs
    res["cases_24_R0_and_R20"] = cases_keep
    # lead 16:07Z item 5: spring A (and B) at R 0 / 0.2 / 0.4, both ends and families: all seated? solid at every hot frame?
    l5 = {}
    for sk in SPRINGS:
        for Rr in (0.0, 0.20, 0.40):
            for end in R.KB:
                for fam in ("seat", "ring"):
                    v = runs[f"{sk}|R{Rr:.2f}|{end}|{fam}"]
                    l5[f"{sk}|R{Rr:.2f}|{end}|{fam}"] = {k: v[k] for k in ("all_seated", "n_unseated", "F_S_min_N", "min_case", "lift_max_um", "hot_F_S_min_N",
                                                                         "solid_at_every_hot_frame_all_cases", "F_flat_derated_N", "k_b_N_mm",
                                                                         "cold_end_F_S_min_at_J_F1_min_N")}
    res["lead_16_07Z_item5_seated_and_solid"] = l5
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
                emb[f"+{add * 1e3:.0f}um|{end}|{fam}"] = {k: v[k] for k in ("all_seated", "F_S_min_N", "min_case", "lift_max_um", "cold_end_F_S_min_at_J_F1_min_N")}
        nos = {}
        for end in R.KB:
            v = verdict(run_cfg(None, 1.0, end, "seat", emb_add=add)[0])
            nos[end] = {"F_S_min_N": v["F_S_min_N"], "n_unseated": v["n_unseated"], "cold_end_F_S_min_at_J_F1_min_N": v["cold_end_F_S_min_at_J_F1_min_N"]}
        emb[f"+{add * 1e3:.0f}um|no_spring_seat"] = nos
    res["embedding_sensitivity_spring_A_R0.20"] = emb
    print("emb", {k: (v.get("F_S_min_N"), v.get("cold_end_F_S_min_at_J_F1_min_N")) for k, v in emb.items() if "no_spring" not in k}, round(time.time() - t0, 1), flush=True)
    # v4: v3 (2250 / 4096 N) as information, and the stop test (lead F1: 'If any turns negative, stop and tell me')
    v3 = json.loads(V3J.read_text())
    cmp3, turned = {}, []
    for k, v in runs.items():
        o = v3["runs"][k]
        cmp3[k] = {"v4_2058_3750": {"all_seated": v["all_seated"], "F_S_min_N": v["F_S_min_N"], "cold_end_N": v["cold_end_F_S_min_at_J_F1_min_N"],
                                    "lift_max_um": v["lift_max_um"], "hot_F_S_min_N": v["hot_F_S_min_N"], "solid_hot": v["solid_at_every_hot_frame_all_cases"]},
                   "v3_2250_4096_info": {"all_seated": o["all_seated"], "F_S_min_N": o["F_S_min_N"], "cold_end_N": o["cold_end_F_S_min_2250_N"],
                                         "lift_max_um": o["lift_max_um"], "hot_F_S_min_N": o["hot_F_S_min_N"], "solid_hot": o["solid_at_every_hot_frame_all_cases"]}}
        if (not v["all_seated"]) or v["F_S_min_N"] <= 0.0 or v["cold_end_F_S_min_at_J_F1_min_N"] <= 0.0:
            turned.append(f"{k}: all_seated {v['all_seated']}, F_S min {v['F_S_min_N']} N, cold end {v['cold_end_F_S_min_at_J_F1_min_N']} N")
        if v["solid_at_every_hot_frame_all_cases"] is False and o["solid_at_every_hot_frame_all_cases"] is True:
            turned.append(f"{k}: no longer solid at every hot frame")
    for k, v in emb.items():
        if "no_spring" in k:
            continue
        if (not v["all_seated"]) or v["F_S_min_N"] <= 0.0 or v["cold_end_F_S_min_at_J_F1_min_N"] <= 0.0:
            turned.append(f"emb {k}: all_seated {v['all_seated']}, F_S min {v['F_S_min_N']} N")
    res["v4_vs_v3_2250_4096_info"] = cmp3
    res["stop_test_lead_F1"] = {"turned_negative": turned, "verdict": "NONE TURNED NEGATIVE" if not turned else "STOP: TELL THE LEAD",
                                "scope": "every spring run (A and B, R 0-0.80, both k_b ends and families) and the embedding sensitivity at 2057.6 / 3750 N"}
    print("STOP-TEST", res["stop_test_lead_F1"]["verdict"], turned, flush=True)
    res.update(geometry_and_bearing())
    CK = Path("/home/claude/work/mechanical/v352/checks/test_spring_r4s_v1.json")
    ck = json.loads(CK.read_text())
    res["cad_envelope_check"] = {"path": str(CK), "sha256_16": sha(CK),
                                 "min_FD04_mm": {k: v["min_FD04_all_poses_mm"] for k, v in ck["envelopes"].items()},
                                 "min_other_mm": {k: v["min_other_all_poses_mm"] for k, v in ck["envelopes"].items()},
                                 "note": ("FD-04 clearance is axial (foil top 1 mm below the head edge): the head stays 1.000 mm at every pose for "
                                          "t 0.40-0.52; the spring (d10) is 1.648-1.755 mm from FD-04; no FD-04 trim, no new RC-04 input "
                                          "(the RC-04 re-check of the earlier trim stays TO-DO)")}
    ck5 = json.loads(CK5.read_text())
    assert sha(CK5) == CK5_SHA16
    c5 = ck5["c_raised_head_and_spring_vs_parts"]
    res["cad_envelope_check_rev5_v2"] = {"path": str(CK5), "sha256_16": sha(CK5),
                                         "by_config": {k: {"head_dz_mm": v["head_dz_mm"], "spring_dz_mm": v["spring_dz_mm"],
                                                           "min_FD04_head_mm": min(p["min_FD04_head_mm"] for p in v["poses"].values()),
                                                           "min_FD04_spring_mm": min(p["min_FD04_spring_mm"] for p in v["poses"].values()),
                                                           "min_other_mm": min(p["min_other_than_FD04_mm"] for p in v["poses"].values())}
                                                       for k, v in c5.items() if isinstance(v, dict) and "poses" in v},
                                         "note": "rev 5 (V352_R5): head 1.000 nominal, 0.789 at the 0.2105 axial offset toward FD-04; spring >= 1.528; "
                                                 "all other parts >= 2.714 at every pose (accepted 17:55:55Z)"}
    res["cad_envelope_check"]["status"] = "RECORD (rev 4s); superseded by cad_envelope_check_rev5_v2"
    print("geometry", json.dumps({k: (v["tip_clearance_to_full_thread_end_min_mm"], v["L_e_gap_bound_mm"], v["A_n_gap_bound_mm2"], v["thread_row_min"]) for k, v in res["geometry_length_tip_engagement"]["cases"].items()}),
          json.dumps(res["route_i_pilot_centring_and_overhang"]["A_supp_mm2_by_basis"]), json.dumps(res["bearing_max_soak_N"]),
          flush=True)
    res["t_run_s"] = round(time.time() - t0, 1)
    s = json.dumps(res, indent=1, default=float)
    OUT.write_text(s)
    print(OUT.name, hashlib.sha256(s.encode()).hexdigest()[:16], res["t_run_s"])

"""J-FWD joint sizing at FA1S (lead CHANGELOG 231 (1), INTERIM on REV-MECH-2 RM2-01; replaces line 230 (1)'s '22 % less stress at the hole').
Basis: FA1S 151.04 bar abs (gauge 150.03 bar), FA-1 factor SF 1.0 on yield AND ultimate (line 188 (9) -> line 177 rule), both members
(TC-01 case 6061-T6, TC-02 head 6061-T6) and the screw.  T = 45 C for all members (the FEA3D FA-1 field at TC-02 node 25946; the engine
is at ambient soak at ignition); screws also at 20 C (the reviewer's basis).  Every number DERIVED unless tagged.  Mechanical, 2026-10-20.
Checks: (i) SCL-type primary stress (hand): TC-01 net ligament Pm (axial, F / A_net) and Pm+Pb (through-wall bending from the bearing
resultant at t/3 from the bore: triangular bearing pressure across the wall, ASSUMED), TC-01 shear-out path Pm = sqrt(3) tau on the two
planes from the hole to the case end; TC-02 net ligament at the tap row (compression, F / A_net, upper bound) and a conservative shear-out
path from the tap to the gland g2 groove (taken as a free edge although it is backed by the plug body below the groove bottom).
(ii) joint checks: bearing on the case (Fbry = 1.4 Fty(T), Fbru = 1.6 Ftu(T) at e/D 2.0, engmat ratios; actual e/D 2.4 >= 2.0), shear-out,
net tension, screw shear yield (0.577 Rp0.2) and ultimate (0.6 Rm) on the thread minor area (fully threaded screw; the stress area shown
for information), TC-02 tapped-thread bearing (V / (D1 L_e,eff), first 0.5 mm of the mouth not credited), TC-02 internal-thread shear
under the maximum preload (FED-STD-H28 area form as in joints_v352), screw tension (max preload) + shear interaction at ultimate
(Rt^2 + Rs^2 <= 1, NASA-STD-5020A form, AS RECALLED, TO-VERIFY).
(iii) hole-edge peaks by Neuber (sigma eps = sigma_el^2 / E) on a Ramberg-Osgood curve eps = s/E + 0.002 (s/Fty)^n, n 15 and 30 (6061-T6,
ASSUMED range), against the local strain limit eps_L = m2 = 0.52 (0.98 - R), R = Fty/Ftu, at uniaxial triaxiality (free hole edge; ASME BPVC
VIII-2 Part 5 5.3.3 / Table 5.7 aluminium row, AS RECALLED, TO-VERIFY); elastic peaks: TC-01 hole edge = FEA3D fa1_c71 R3 all-node 399 MPa
(SIM, full-bore RBE3, not converged; REV-MECH-2) scaled by the per-screw load, and K_tb x bearing stress with K_tb = K_tn / (W/D - 1),
K_tn 4.0 (pin-loaded lug, W/D 4-5, ASSUMED from the Peterson pinned-joint chart range, TO-VERIFY); TC-02 tap mouth = max(FEA3D all-node
280.6 MPa at node 25946 scaled, beam-on-elastic-foundation bearing peak 2 V beta / D1, beta = (k / 4 EI)^0.25, k = E_Al, ASSUMED).
Equal load sharing between the screws is ASSUMED (holes match-drilled through TC-01 into TC-02, drawing note)."""
import json, math, hashlib, sys
import numpy as np
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/04-fea/src")
import engmat
MAT = engmat.MATERIALS
P_FA1S_ABS, P_AMB = 151.04, 1.01325           # bar abs (line 230 / 231), ambient
PG = (P_FA1S_ABS - P_AMB) * 0.1                # MPa gauge
D_SEAL = 57.25                                 # case bore at the plug O-rings (TC-01 seal land 57.25 H8): pressure area
F_TOT = PG * math.pi / 4.0 * D_SEAL ** 2       # N
F_TOT_ABS = P_FA1S_ABS * 0.1 * math.pi / 4.0 * D_SEAL ** 2   # N, absolute-pressure basis (v2 rows, lead 10:28Z)
T_C = 45.0
GEO = {"case_OD": 63.5, "case_bore": 57.25, "plug_OD": 57.20, "e_mm": 12.0, "gap": 0.025, "bolt_z": 127.513, "g2_fwd_wall_z": 114.363 + 4.85,
       "zf": 103.513, "manifold_bore_d": 10.0}
TH = {"M5": dict(d=5.0, P=0.8, d2=4.480, d3=4.019, As=14.18, D1=4.134, Ds_min=4.826, En_max=4.605, dk=9.5, k=2.75, tap=4.2, hole=5.5),
      "M6": dict(d=6.0, P=1.0, d2=5.350, d3=4.773, As=20.12, D1=4.917, Ds_min=5.794, En_max=5.500, dk=10.5, k=3.3, tap=5.0, hole=6.6)}
# ISO 261/724 basic dims, ISO 965-1 6g/6H limits and ISO 7380-1 head (dk, k): AS RECALLED, TO-VERIFY (same class as hardware_v351 HEAD)
GRADES = {"A4-80": (600.0, 800.0, "ISO 3506-1 class 80 minima (engmat SS-A4-80, LITERATURE)"),
          "A4-70": (450.0, 700.0, "ISO 3506-1 class 70 minima (LITERATURE)"),
          "Rp800": (800.0, 1000.0, "ISO 3506-1:2020 class 100 minima (A4-100) or an equivalent >= 800 / 1000 MPa stainless: availability and "
                                   "datasheet TO-VERIFY (e.g. BUMAX 109 class) - not a standard stock item in ISO 7380-1 M5")}
K_NUT, SCAT = 0.20, 0.25


def tab(m, k, T):
    d = MAT[m][k]
    return float(np.interp(T, d["T_C"], d["v"])) / 1e6 if "T_C" in d else d["v"] / 1e6


def kT(T):
    return tab("SS316L", "Fty", max(T, 20.0)) / tab("SS316L", "Fty", 20.0)


def kTu(T):
    return tab("SS316L", "Ftu", max(T, 20.0)) / tab("SS316L", "Ftu", 20.0)


def strip_area(th, L_e):
    n = 1.0 / th["P"]
    return math.pi * n * L_e * th["Ds_min"] * (1.0 / (2.0 * n) + 0.57735 * (th["Ds_min"] - th["En_max"]))


def ro_neuber(s_el, E, Fty, n):
    """local stress / strain from Neuber's rule on eps = s/E + 0.002 (s/Fty)^n (bisection)."""
    target = s_el ** 2 / E
    lo, hi = 1e-3, max(s_el, Fty) * 1.5
    for _ in range(200):
        s = 0.5 * (lo + hi)
        e = s / E + 0.002 * (s / Fty) ** n
        if s * e > target:
            hi = s
        else:
            lo = s
    s = 0.5 * (lo + hi)
    return s, s / E + 0.002 * (s / Fty) ** n


def ms(cap, dem):
    return round(cap / dem - 1.0, 3)


def option(key, n, size, grade, L_screw, t_case=None, T=T_C, torque=None, spot_face=False, note="", l_bear=None, F=None):
    th = TH[size]
    Rp20, Rm20, gsrc = GRADES[grade]
    Rp, Rm = Rp20 * kT(T), Rm20 * kTu(T)
    Fty, Ftu = tab("AL6061-T6", "Fty", T), tab("AL6061-T6", "Ftu", T)
    E = tab("AL6061-T6", "E", T)
    Fbry, Fbru = MAT["AL6061-T6"]["Fbry_over_Fty_eD2"]["v"] * Fty, MAT["AL6061-T6"]["Fbru_over_Ftu_eD2"]["v"] * Ftu
    Fsu = MAT["AL6061-T6"]["Fsu_over_Ftu"]["v"] * Ftu
    Fsy = 0.577 * Fty
    t0 = (GEO["case_OD"] - GEO["case_bore"]) / 2.0
    sag = GEO["case_OD"] / 2.0 - math.sqrt((GEO["case_OD"] / 2.0) ** 2 - (th["dk"] / 2.0) ** 2)
    t = t_case if t_case else (t0 - sag if spot_face else t0)
    V = (F if F else F_TOT) / n
    D, Dh, e = th["d"], th["hole"], GEO["e_mm"]
    r = {"option": key, "n": n, "size": size, "grade": grade, "grade_src": gsrc, "L_screw_mm": L_screw, "T_C": T, "spot_face": spot_face,
         "t_case_at_hole_mm": round(t, 3), "V_per_screw_N": round(V, 1), "note": note}
    # ---- (ii) screw
    A3, As_ = math.pi / 4.0 * th["d3"] ** 2, th["As"]
    tau = V / A3
    r["screw_shear_minor"] = {"A_mm2": round(A3, 2), "tau_MPa": round(tau, 1), "Fsy_MPa": round(0.577 * Rp, 1), "Fsu_MPa": round(0.6 * Rm, 1),
                              "MS_y": ms(0.577 * Rp, tau), "MS_u": ms(0.6 * Rm, tau),
                              "MS_y_20C": ms(0.577 * Rp20, tau), "MS_u_20C": ms(0.6 * Rm20, tau)}
    r["screw_shear_stress_area_info"] = {"A_mm2": As_, "MS_y_20C": ms(0.577 * Rp20 * As_, V), "MS_u_20C": ms(0.6 * Rm20 * As_, V)}
    T_Nm = torque if torque else round(K_NUT * 0.65 * Rp20 * As_ * D * 1e-3, 2)
    Fp = T_Nm * 1e3 / (K_NUT * D)
    Fmax = (1 + SCAT) * Fp
    Rt, Rs = Fmax / (Rm * As_), V / (0.6 * Rm * A3)
    r["preload"] = {"T_Nm": T_Nm, "F_nom_N": round(Fp, 0), "F_max_N": round(Fmax, 0)}
    r["screw_interaction_ult"] = {"Rt_max_preload": round(Rt, 3), "Rs": round(Rs, 3), "Rt2_Rs2": round(Rt ** 2 + Rs ** 2, 3),
                                  "MS": round(1.0 / math.sqrt(Rt ** 2 + Rs ** 2) - 1.0, 3)}
    # ---- (ii) case TC-01
    sbr = V / (D * (l_bear if l_bear else t))
    r["case_bearing"] = {"e_over_D": round(e / D, 2), "L_bearing_mm": round(l_bear if l_bear else t, 3), "sigma_br_MPa": round(sbr, 1), "Fbry_MPa": round(Fbry, 1), "Fbru_MPa": round(Fbru, 1),
                         "MS_y": ms(Fbry, sbr), "MS_u": ms(Fbru, sbr)}
    A_so = 2.0 * t * (e - Dh / 2.0)
    tso = V / A_so
    r["case_shear_out"] = {"A_mm2": round(A_so, 2), "tau_MPa": round(tso, 1), "MS_y": ms(Fsy, tso), "MS_u": ms(Fsu, tso)}
    A_g = math.pi / 4.0 * (GEO["case_OD"] ** 2 - GEO["case_bore"] ** 2)
    A_n = A_g - n * Dh * (GEO["case_OD"] - GEO["case_bore"]) / 2.0
    s_net = F_TOT / A_n
    w_lig = math.pi * (GEO["case_OD"] + GEO["case_bore"]) / 2.0 / n - Dh
    Pb = 6.0 * V * (t0 / 6.0) / (w_lig * t0 ** 2)
    r["case_net_tension"] = {"A_net_mm2": round(A_n, 1), "Pm_MPa": round(s_net, 1), "MS_y": ms(Fty, s_net), "MS_u": ms(Ftu, s_net)}
    # ---- (i) SCL-type primary
    r["i_TC01_net_ligament"] = {"Pm_MPa": round(s_net, 1), "Pb_MPa": round(Pb, 1), "PmPb_MPa": round(s_net + Pb, 1), "ligament_w_mm": round(w_lig, 2),
                                "MS_Pm_y": ms(Fty, s_net), "MS_Pm_u": ms(Ftu, s_net), "MS_PmPb_y": ms(Fty, s_net + Pb), "MS_PmPb_u": ms(Ftu, s_net + Pb)}
    r["i_TC01_shear_out_path"] = {"Pm_vm_MPa": round(math.sqrt(3.0) * tso, 1), "MS_y": ms(Fty, math.sqrt(3.0) * tso), "MS_u": ms(Ftu, math.sqrt(3.0) * tso)}
    L_e = L_screw - t - GEO["gap"]
    L_eff = L_e - 0.5
    A_pl = math.pi / 4.0 * (GEO["plug_OD"] ** 2 - GEO["manifold_bore_d"] ** 2) - n * th["tap"] * 9.0
    s_pl = F_TOT / A_pl
    dz = GEO["bolt_z"] - GEO["g2_fwd_wall_z"] - D / 2.0
    tso2 = V / (2.0 * dz * L_eff)
    r["i_TC02_net_ligament"] = {"Pm_MPa_compression_upper_bound": round(s_pl, 1), "MS_y": ms(Fty, s_pl), "MS_u": ms(Ftu, s_pl)}
    r["i_TC02_shear_out_path"] = {"ligament_to_g2_mm": round(dz, 2), "Pm_vm_MPa": round(math.sqrt(3.0) * tso2, 1),
                                  "MS_y": ms(Fty, math.sqrt(3.0) * tso2), "MS_u": ms(Ftu, math.sqrt(3.0) * tso2),
                                  "note": "conservative: the g2 groove is taken as a free edge; the bearing load on the tap's aft wall goes into the plug body"}
    # ---- (ii) TC-02 tapped thread
    sbt = V / (th["D1"] * L_eff)
    r["TC02_tapped_thread_bearing"] = {"L_e_mm": round(L_e, 3), "L_eff_mm": round(L_eff, 3), "sigma_br_MPa": round(sbt, 1), "MS_y": ms(Fbry, sbt), "MS_u": ms(Fbru, sbt)}
    An = strip_area(th, L_eff)
    r["TC02_thread_shear_max_preload"] = {"A_n_mm2": round(An, 1), "tau_MPa": round(Fmax / An, 1), "MS_u": ms(Fsu, Fmax / An), "MS_y": ms(Fsy, Fmax / An)}
    # ---- (iii) Neuber
    m2 = 0.52 * (0.98 - Fty / Ftu)
    I = math.pi * th["d3"] ** 4 / 64.0
    beta = (E / (4.0 * 193000.0 * I)) ** 0.25
    s_bef = 2.0 * V * beta / th["D1"]
    V8 = F_TOT / 8.0
    W_D = math.pi * GEO["case_OD"] / n / D
    s_case = max(399.0 * V / V8, 4.0 / (W_D - 1.0) * sbr)
    s_tc02 = max(280.6 * V / V8, s_bef)
    neu = {}
    for nm, sel in (("TC01_hole_edge", s_case), ("TC02_tap_mouth", s_tc02)):
        worst = None
        for nn in (15.0, 30.0):
            s, eps = ro_neuber(sel, E, Fty, nn)
            if worst is None or eps > worst[1]:
                worst = (s, eps, nn)
        neu[nm] = {"sigma_el_MPa": round(sel, 1), "sigma_local_MPa": round(worst[0], 1), "eps_local": round(worst[1], 5), "n_RO": worst[2],
                   "eps_limit": round(m2, 4), "MS_strain": ms(m2, worst[1])}
    neu["TC01_hole_edge"]["sources"] = (f"max(FEA3D R3 all-node 399 MPa x {V / V8:.3f}, K_tb {4.0 / (W_D - 1.0):.3f} x bearing {sbr:.1f}); W/D {W_D:.2f}")
    neu["TC02_tap_mouth"]["sources"] = (f"max(FEA3D all-node 280.6 MPa x {V / V8:.3f}, BEF 2 V beta / D1 = {s_bef:.1f} MPa, beta {beta:.3f} /mm)")
    r["iii_neuber"] = neu
    # onset of local yield (elastic peak = Fty) in bar abs
    r["iii_onset_local_yield_bar_abs"] = {"TC01": round(P_AMB + (P_FA1S_ABS - P_AMB) * Fty / s_case, 1), "TC02": round(P_AMB + (P_FA1S_ABS - P_AMB) * Fty / s_tc02, 1)}
    allms = []
    for k_, v_ in r.items():
        if isinstance(v_, dict):
            for kk, vv in v_.items():
                if kk.startswith("MS") and isinstance(vv, (int, float)) and "info" not in k_ and "20C" not in kk:
                    allms.append((vv, f"{k_}.{kk}"))
            for kk, vv in v_.items():
                if isinstance(vv, dict) and "MS_strain" in vv:
                    allms.append((vv["MS_strain"], f"{k_}.{kk}.MS_strain"))
    allms.sort()
    r["min_MS"] = {"value": allms[0][0], "where": allms[0][1], "passes_all": allms[0][0] >= 0.0}
    return r


OPTS = [option("O0 v3.5.1: 8x M5 A4-80 x 10, no spot face", 8, "M5", "A4-80", 10, note="v3.5.1 frozen (reviewer basis)"),
        option("O0s v3.5.1 + spot face for the head", 8, "M5", "A4-80", 10, spot_face=True, note="the v3.5.1 HW-101 action 'spot face TO-DEFINE'"),
        option("O1 10x M5 A4-80 x 10 at 18 + 36k deg, no spot face", 10, "M5", "A4-80", 10, note="count change (recommended)"),
        option("O2 12x M5 A4-80 x 10", 12, "M5", "A4-80", 10, note="count change; 12-pitch clashes with the Pc passage (142 deg) or the torch passage (0 deg)"),
        option("O3 8x M6 A4-80 x 12", 8, "M6", "A4-80", 12, note="size change: 6.6 holes, M6 taps 5.0 drill deeper than the M5 taps"),
        option("O1s O1 + spot face for the head (information)", 10, "M5", "A4-80", 10, spot_face=True, note="not adopted: the wall at the hole drops to 2.765"),
        option("O4 8x M5 Rp0.2 >= 800 MPa stainless x 10 (5.53 N m kept)", 8, "M5", "Rp800", 10, torque=5.53,
               note="grade change: 0 g, no part change; procurement / datasheet risk; torque kept at the A4-80 value (a 0.65 Rp0.2 torque, 7.37 N m, gives TC-02 thread shear yield -0.06)"),
        option("O5 (withdrawn) interim land: 8x M5 A4-80 x 12, wall 4.40", 8, "M5", "A4-80", 12, t_case=4.40, note="line 230 FA1S option, withdrawn by 231"),
        option("O1v2 10x M5 A4-80 x 10, head seat (a): nominal wall 2.688, L_eff 2.388, CALC V abs", 10, "M5", "A4-80", 10, t_case=2.688, l_bear=2.388,
               F=F_TOT_ABS, T=45.6, note="v2 (lead 10:15Z O1 FIX): spot-face wall 2.688 at the hole, bearing length 2.688 - 0.2 (bore-side R0.2 hard max) - 0.1 (flat-side 0.1 x 45); V 3888.1 (lead 10:28Z)"),
        option("O1v2L 10x M5 A4-80 x 10, head seat (a): drawing-limit wall 2.665, L_eff 2.365, CALC V abs (governing)", 10, "M5", "A4-80", 10, t_case=2.665,
               l_bear=2.365, F=F_TOT_ABS, T=45.6, note="v2: bore 57.296 / flat at its low end; the datasheet quotes this row (lead 10:15Z). Only the case-bearing row is the O1 fix; the other TC-01 rows of this table keep the v1 method (Pb on the 3.125 wall) and are superseded by the jfwd_seat_v352_v1 / jfwd_fix_v352_v1 seat cells")]
out = {"id": "jfwd_v352", "version": "v2", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
       "v2": ("lead 10:15Z O1 FIX accepted: O1v2 / O1v2L rows on the adopted head seat (a) (spot-face wall 2.688 nominal / 2.665 drawing limit, effective bearing length wall - 0.3) at CALC V 3888.1 (lead 10:28Z); v1 (jfwd_v352_v1.py / jfwd_v352_v1.json) kept, SUPERSEDED: its O1 row used the v3.5.1 wall 3.125 (+0.338 / +0.649); its screw rows (shear on the minor area, Rt^2 + Rs^2 AS RECALLED) are superseded by the NASA-STD-5020A Eq. 22 cells in jfwd_fix_v352_v1.json (lead 10:24Z / 10:47Z: preload omitted governing, included beside it)"),
       "superseded": {"O1 (wall 3.125, no spot face)": "by O1v2 / O1v2L", "screw rows of every option": "by jfwd_fix_v352_v1 (5020A Eq. 22)",
                      "recommended O1 / why / mass_O1_g (v1 text)": "kept as the v1 record; the FA1S fix is ruled on jfwd_fix_v352_v1"},
       "load": {"FA1S_bar_abs": P_FA1S_ABS, "p_gauge_MPa": round(PG, 4), "D_seal_mm": D_SEAL, "F_total_N": round(F_TOT, 0), "SF_y": 1.0, "SF_u": 1.0},
       "geometry": GEO, "options": OPTS,
       "recommended": "O1",
       "mass_O1_g": {"screws": "+2 x 2.028 = +4.06 (CALC, hardware_v352 HW-101)", "holes": "TC-01 2 x 5.5 x 3.125 and TC-02 2 x 4.2 x 9.0: about -0.7 (CAD)",
                     "net": "about +3.4 g"},
       "why": ("cheapest change that passes (i)-(iii) on both members with a stock fastener: +2 screws (CALC +4.06 g) and 2 more holes in TC-01 / "
               "TC-02 (-0.7 g), no case-wall change; O4 (0 g) needs a >= 800 MPa stainless M5 button head that is not a stock item (datasheet and "
               "availability TO-VERIFY) and keeps the case bearing at +0.08; O3 (M6) costs ~+8 g and deeper taps; O2 has no free 12-pitch "
               "pattern (Pc 142 deg / torch 0 deg passages); O0s shows a spot face for the head would make the case bearing negative, so the "
               "button head stays on the cylinder (line contact; preload is not a strength item in this bearing-type joint)"),
       "inspect_or_replace_rule": ("after any Pc excursion above 60 bar abs recorded by the Pc channel (FA-1 class; below the ~66 bar abs onset of "
                                   "local yield at the TC-02 tap mouth estimated here): replace all J-FWD screws (HW-101), inspect the TC-01 "
                                   "holes (pin gauge 5.50 go / 5.55 no-go: elongation <= 0.05 mm, no edge cracks under 10x) and the TC-02 taps "
                                   "(M5-6H go / no-go); scrap TC-01 or TC-02 on a failed gauge.  Needs a Pc channel that resolves sub-ms "
                                   "peaks (Electronics: sampling rate TO-CONFIRM)")}
s = json.dumps(out, indent=1)
open("/home/claude/work/mechanical/v352/jfwd/jfwd_v352_v2.json", "w").write(s)
print("jfwd_v352_v2.json", hashlib.sha256(s.encode()).hexdigest()[:16], "F_total", round(F_TOT), "N")
for o in OPTS:
    print(f"{o['option'][:58]:58s} V {o['V_per_screw_N']:7.1f} | scr {o['screw_shear_minor']['MS_y']:+.3f}/{o['screw_shear_minor']['MS_u']:+.3f} "
          f"(20C {o['screw_shear_minor']['MS_y_20C']:+.3f}) | brg {o['case_bearing']['MS_y']:+.3f}/{o['case_bearing']['MS_u']:+.3f} | "
          f"PmPb {o['i_TC01_net_ligament']['MS_PmPb_y']:+.2f} | so {o['case_shear_out']['MS_y']:+.2f} | tap {o['TC02_tapped_thread_bearing']['MS_y']:+.2f} "
          f"| int {o['screw_interaction_ult']['MS']:+.3f} | N01 {o['iii_neuber']['TC01_hole_edge']['MS_strain']:+.2f} N02 {o['iii_neuber']['TC02_tap_mouth']['MS_strain']:+.2f} "
          f"| min {o['min_MS']['value']:+.3f} {o['min_MS']['where']}")

"""J-FWD screw preload re-check on the CHANGELOG 234 (1)(b)/(c) basis (lead 2026-10-20, REV-MECH-2 RM2-01 addenda).  Hand calc, no FE.
Mechanical, 2026-10-20.  Every number DERIVED unless tagged.
v2 (2026-10-20, after the lead's 'J-FWD 3.0 N m ACCEPTED'): the selected torque is the lead's 3.0 N m (the v1 rule on the uniform joint
temperature still gives 4.0 N m, kept as rule_selection_uniform_T_Nm; at 4.0 N m the GVLO gap-variant soak fails the screw tension,
jfwd_variant_v352_v1 / v2); the sweep adds 3.0 and 2.5 N m; the J-F1 acceptance is the lowest allowed installation preload over the LC2
uniform-temperature checks below and every check of jfwd_variant_v352_v2.json (every B1 frame, merged / GVLO / GVHI); the 2.5 N m
fallback rows; the intervals at the selected torque.  v1 = jfwd_preload_v352_v1.py -> jfwd_preload_v352_v1.json 5dbcb3597d009b0e (kept).

Joint: v3.5.2 J-FWD = 10x ISO 7380-1 M5 x 10 A4-80 (HW-101) radial, TC-01 case (6061-T6) to TC-02 head (6061-T6), az 18 + 36k deg
(jfwd_v352_v1.json 790e379ef3c00179, option O1).  Bearing-type joint (234 (1)(c): friction below the joint load at LC2 and FA1S).
Loads: head axial load F = p x pi/4 x 57.25^2 (case bore at the O-rings = the pressure diameter; vacuum outside, i.e. p absolute),
shared equally by the 10 screws (match-drilled holes, ASSUMED): LC2 chamber MEOP 4.5 MPa (loadcases_v1 LC2) -> 11.58 kN; FA1S 151.04 bar abs
-> 38.88 kN (v1 used the gauge value 38.62 kN; the absolute value is used here, +0.7 %).
Ruled checks (234 (1)(b), NASA-STD-5020A form, AS RECALLED, TO-VERIFY):
  LC2 (SF 1.5 / 2.0, part temperature): yield  sigma_vm = sqrt((F_max / A_s)^2 + 3 (SF_y V / A_3)^2) <= k_T Rp0.2;
                                        ultimate Rt^2 + Rs^2 <= 1, Rt = F_max / (k_Tu Rm A_s), Rs = SF_u V / (0.6 k_Tu Rm A_3);
  FA1S (FA-1 rule SF 1.0 / 1.0, 188 (9) -> 177): ultimate interaction with F_max must pass; yield shear-only on the minor area with
                                        the preload-relaxation argument and the 233 (4) inspect-or-replace rule.
F_max = 1.25 F_nom (ruled maximum installation preload), F_min = 0.75 F_nom (ASSUMED symmetric scatter), F_nom = T / (K d), K = 0.20
(ASSUMED; thread locker torque-tension coefficient not stated in the Henkel TDS -> TO-VERIFY by a torque-tension test on HW-101 in a
6061-T6 tap coupon; the +25 % bound holds for K >= 0.16).
Sensitivity added by Mechanical (not in the ruled basis): thermal preload rise of the steel screw clamping the aluminium case wall,
dF_th = (alpha_Al - alpha_A4) dT L_grip k_b k_m / (k_b + k_m) (CALC; k_b, k_m ASSUMED stiff-member estimates below).  The case bore at the
screw row is not pressurised (the plug O-rings g1/g2 are 15-21 mm below the row; shell decay length ~7.5 mm), so no pressure term.
Screw temperature (SIM, B1 v352_NF2b merged thermal, TC-01/TC-02 nodes r 21.5-31.75 within +/- 2.6 mm of the screw row): 78.6 C at the end
of the B1 burn (21.65 s; LC2 'part temperature'), 54.2 C end of A1 burn 2, 45.6 C at the A1 relight (FA1S), 119.7 C soak maximum (166.7 s,
no pressure).  The gap-conductance variant (fit J1 open) can raise TC-02 at the row: LC2 is also evaluated at 100 C (bound pending the variant).
k_T, k_Tu: hot factors of A4-80 = engmat SS316L Fty(T)/Fty(20), Ftu(T)/Ftu(20) (ASSUMED proxy; the reviewer's 'hot' 0.875 = this
factor at 79 C).  A4-80 RT minima Rp0.2 600 / Rm 800 MPa (ISO 3506-1 class 80, LITERATURE via engmat SS-A4-80).
Thread locker (method M-T1L): Henkel LOCTITE 243 (medium strength) or equivalent, service -55 to +180 C (Hoffmann Group 083301 243 listing,
https://www.hoffmann-group.com/MT/en/mbbridge/p/083301-243, accessed 2026-10-20, DATASHEET-distributor); Henkel TDS 'new formulation'
March 2010 (https://static.rapidonline.com/pdf/12-4132o_v1.pdf, accessed 2026-10-20): M10 steel breakaway 26 N m, M10 stainless breakloose
17 N m (pre-torque 5 N m, 1 week 22 C), works on passive substrates (stainless) [DATASHEET]; hot strength / heat ageing only as charts
(values TO-VERIFY); no K value stated."""
import json, math, hashlib, sys
import numpy as np
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/04-fea/src")
import engmat
MAT = engmat.MATERIALS
D_SEAL = 57.25
A_P = math.pi / 4.0 * D_SEAL ** 2
TH = dict(d=5.0, P=0.8, d3=4.019, As=14.18, D1=4.134, Ds_min=4.826, En_max=4.605, dk=9.5, hole=5.5, d_nom_area=math.pi / 4.0 * 5.0 ** 2)
A3 = math.pi / 4.0 * TH["d3"] ** 2
RP20, RM20 = 600.0, 800.0
K_NUT, SCAT = 0.20, 0.25
T_WALL, GAP_FIT = 3.125, 0.025
L_EFF = 10.0 - T_WALL - GAP_FIT - 0.5            # engaged length credited in TC-02 (first 0.5 mm of the mouth not credited), as v1


def tab(m, k, T):
    d = MAT[m][k]
    return float(np.interp(T, d["T_C"], d["v"])) / (1e6 if k in ("Fty", "Ftu", "E") else 1.0) if "T_C" in d else d["v"] / (1e6 if k in ("Fty", "Ftu", "E") else 1.0)


def kT(T):
    return tab("SS316L", "Fty", max(T, 20.0)) / tab("SS316L", "Fty", 20.0)


def kTu(T):
    return tab("SS316L", "Ftu", max(T, 20.0)) / tab("SS316L", "Ftu", 20.0)


def strip_area(L_e):
    n = 1.0 / TH["P"]
    return math.pi * n * L_e * TH["Ds_min"] * (1.0 / (2.0 * n) + 0.57735 * (TH["Ds_min"] - TH["En_max"]))


# stiffness estimates (ASSUMED): screw = free thread over the grip (A_s) + 0.4 d under the head + 0.33 d in the tapped hole (A_nom, VDI 2230-style);
# member = the case wall under the button head, A_eff = pi/4 ((dk + t/2)^2 - D_h^2)
E_S = 193000.0
L_over_A = (T_WALL + GAP_FIT) / TH["As"] + 0.4 * TH["d"] / TH["d_nom_area"] + 0.33 * TH["d"] / TH["d_nom_area"]
K_B = E_S / L_over_A
A_M = math.pi / 4.0 * ((TH["dk"] + T_WALL / 2.0) ** 2 - TH["hole"] ** 2)


def k_m(T):
    return tab("AL6061-T6", "E", T) * A_M / T_WALL


def dF_th(T):
    """thermal preload rise (N) at a uniform joint temperature T (C) from 20 C (secant CTEs)."""
    da = tab("AL6061-T6", "alpha", T) - tab("SS316L", "alpha", T)
    km = k_m(T)
    return max(0.0, da * (T - 20.0) * (T_WALL + GAP_FIT) * K_B * km / (K_B + km))


def ms(cap, dem):
    return round(cap / dem - 1.0, 4)


def checks(n, torque, p_MPa, sfy, sfu, T, thermal=True, label=""):
    V = p_MPa * A_P / n
    Fn = torque * 1e3 / (K_NUT * TH["d"])
    dth = dF_th(T) if thermal else 0.0
    Fmax, Fmin = (1.0 + SCAT) * Fn + dth, (1.0 - SCAT) * Fn + dth
    Rp, Rm = RP20 * kT(T), RM20 * kTu(T)
    st = Fmax / TH["As"]
    tf = sfy * V / A3
    svm = math.sqrt(st ** 2 + 3.0 * tf ** 2)
    Rt = Fmax / (Rm * TH["As"])
    Rs = (sfu * V) / (0.6 * Rm * A3) if sfu else None
    out = {"label": label, "n": n, "torque_Nm": torque, "p_MPa_abs": p_MPa, "T_C": T, "SF_y": sfy, "SF_u": sfu, "V_per_screw_N": round(V, 1),
           "F_nom_N": round(Fn, 0), "dF_thermal_N": round(dth, 0), "F_max_N": round(Fmax, 0), "F_min_N": round(Fmin, 0),
           "kT": round(kT(T), 4), "kTu": round(kTu(T), 4), "kT_Rp_MPa": round(Rp, 1),
           "yield_combined": {"sigma_t_MPa": round(st, 1), "tau_factored_MPa": round(tf, 1), "sigma_vm_MPa": round(svm, 1), "MS_y": ms(Rp, svm)},
           "yield_shear_only_minor": {"tau_MPa": round(tf, 1), "allow_MPa": round(0.577 * Rp, 1), "MS_y": ms(0.577 * Rp, tf)}}
    if sfu:
        out["ult_interaction"] = {"Rt": round(Rt, 4), "Rs": round(Rs, 4), "Rt2_Rs2": round(Rt ** 2 + Rs ** 2, 4),
                                  "MS_u": round(1.0 / math.sqrt(Rt ** 2 + Rs ** 2) - 1.0, 4)}
    return out


def tc02_thread(torque, T, thermal=True):
    """TC-02 internal-thread shear (FED-STD-H28 area form, as joints_v352 / jfwd v1) under the maximum preload alone (unfactored:
    installation preload is not an external load), at the joint temperature T."""
    Fn = torque * 1e3 / (K_NUT * TH["d"])
    F = (1.0 + SCAT) * Fn + (dF_th(T) if thermal else 0.0)
    An = strip_area(L_EFF)
    Fty, Ftu = tab("AL6061-T6", "Fty", T), tab("AL6061-T6", "Ftu", T)
    tau = F / An
    return {"T_C": T, "F_max_N": round(F, 0), "A_n_mm2": round(An, 1), "tau_MPa": round(tau, 1), "Fsy_MPa": round(0.577 * Fty, 1),
            "Fsu_MPa": round(MAT["AL6061-T6"]["Fsu_over_Ftu"]["v"] * Ftu, 1), "MS_y": ms(0.577 * Fty, tau),
            "MS_u": ms(MAT["AL6061-T6"]["Fsu_over_Ftu"]["v"] * Ftu, tau)}


T_LC2, T_LC2B, T_FA1, T_SOAK = 78.6, 100.0, 45.6, 119.7
P_LC2, P_FA1S, P_LC1 = 4.5, 15.104, 2.501
out = {"id": "jfwd_preload_v352", "version": "v2", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
       "stiffness_ASSUMED": {"k_b_N_mm": round(K_B, 0), "A_m_eff_mm2": round(A_M, 1), "k_m_20C_N_mm": round(k_m(20.0), 0),
                             "dF_th_N": {f"{t:g}C": round(dF_th(t), 0) for t in (T_FA1, 54.2, T_LC2, T_LC2B, T_SOAK)}},
       "reviewer_reproduction_v351_8xM5_5.53Nm": {
           "nominal_RT": checks(8, 5.53, P_LC2, 1.5, 2.0, 20.0, thermal=False, label="v3.5.1 8x M5, F_nom (no scatter), RT")["yield_combined"],
           "nominal_hot": None, "plus25_hot": checks(8, 5.53, P_LC2, 1.5, 2.0, T_LC2, thermal=False, label="v3.5.1 8x M5 +25 % at 78.6 C")["yield_combined"]},
       "torque_sweep_10xM5": [], "tc02_thread_shear": [], "retention": []}
# nominal (no scatter) hot for the reproduction
Fn = 5.53e3 / (K_NUT * 5.0)
st, tf = Fn / TH["As"], 1.5 * (P_LC2 * A_P / 8) / A3
out["reviewer_reproduction_v351_8xM5_5.53Nm"]["nominal_RT"]["MS_y_nominal_preload"] = ms(RP20, math.sqrt(st ** 2 + 3 * tf ** 2))
out["reviewer_reproduction_v351_8xM5_5.53Nm"]["nominal_hot"] = {"sigma_vm_MPa": round(math.sqrt(st ** 2 + 3 * tf ** 2), 1),
                                                                 "kT_Rp_MPa": round(RP20 * kT(T_LC2), 1),
                                                                 "MS_y": ms(RP20 * kT(T_LC2), math.sqrt(st ** 2 + 3 * tf ** 2))}
for tq in (5.53, 5.0, 4.5, 4.0, 3.5, 3.0, 2.5):
    row = {"torque_Nm": tq}
    for nm, (p, sfy, sfu, T, th) in {"LC2_78.6C_ruled": (P_LC2, 1.5, 2.0, T_LC2, False), "LC2_78.6C_thermal": (P_LC2, 1.5, 2.0, T_LC2, True),
                                     "LC2_100C_ruled": (P_LC2, 1.5, 2.0, T_LC2B, False), "LC2_100C_thermal": (P_LC2, 1.5, 2.0, T_LC2B, True),
                                     "FA1S_45.6C_thermal": (P_FA1S, 1.0, 1.0, T_FA1, True), "FA1S_45.6C_ruled": (P_FA1S, 1.0, 1.0, T_FA1, False)}.items():
        row[nm] = checks(10, tq, p, sfy, sfu, T, thermal=th, label=nm)
    out["torque_sweep_10xM5"].append(row)
    out["tc02_thread_shear"].append({"torque_Nm": tq, "LC2_78.6C": tc02_thread(tq, T_LC2), "soak_119.7C": tc02_thread(tq, T_SOAK),
                                     "FA1S_45.6C": tc02_thread(tq, T_FA1)})
    Fn = tq * 1e3 / (K_NUT * 5.0)
    out["retention"].append({"torque_Nm": tq, "F_min_N": round(0.75 * Fn, 0), "F_nom_N": round(Fn, 0),
                             "friction_capacity_kN_mu0.2_Fmin": round(10 * 0.2 * 0.75 * Fn / 1e3, 2),
                             "friction_capacity_kN_mu0.2_Fnom": round(10 * 0.2 * Fn / 1e3, 2),
                             "joint_load_kN": {"LC1_Pc_max_25.01bar": round(P_LC1 * A_P / 1e3, 2), "LC2_45bar": round(P_LC2 * A_P / 1e3, 2),
                                               "FA1S_151bar": round(P_FA1S * A_P / 1e3, 2)}})
# selection: the highest torque in the sweep with LC2 yield >= 0 at the 100 C bound INCLUDING the thermal rise, and every ruled check >= 0
sel = None
for row, thr in zip(out["torque_sweep_10xM5"], out["tc02_thread_shear"]):
    ok = (row["LC2_100C_thermal"]["yield_combined"]["MS_y"] >= 0.0 and row["LC2_78.6C_ruled"]["yield_combined"]["MS_y"] >= 0.0
          and row["LC2_100C_thermal"]["ult_interaction"]["MS_u"] >= 0.0 and row["FA1S_45.6C_thermal"]["ult_interaction"]["MS_u"] >= 0.0
          and row["FA1S_45.6C_thermal"]["yield_shear_only_minor"]["MS_y"] >= 0.0 and thr["soak_119.7C"]["MS_y"] >= 0.0)
    if ok and sel is None:
        sel = row["torque_Nm"]
out["rule_selection_uniform_T_Nm"] = sel
# ---- v2: the lead's decision and the gap-variant results (jfwd_variant_v352_v2.json, every B1 frame of merged / GVLO / GVHI)
from pathlib import Path as _P
JVF = _P("/home/claude/work/mechanical/v352/jfwd/jfwd_variant_v352_v2.json")
JV = json.loads(JVF.read_text())
JVSHA = hashlib.sha256(JVF.read_bytes()).hexdigest()[:16]
SUMV = {(r["bound"], r["torque_Nm"], r["k_sh_factor"]): r for r in JV["summary_rows"]}
SEL_LEAD = 3.0
sel = SEL_LEAD
out["selected_torque_Nm"] = sel
out["selection_basis"] = (
    "lead decision 2026-10-20 ('J-FWD 3.0 N m ACCEPTED': HW-101 at 3.0 N m, M-T1L, LOCTITE 243). The v1 rule (highest torque in the sweep "
    f"with every uniform-temperature check >= 0) gives {out['rule_selection_uniform_T_Nm']:g} N m; at 4.0 N m the GVLO gap-variant soak takes "
    f"the screw tension to MS {SUMV[('GVLO', 4.0, 1.0)]['soak_MS_y_min']:+.3f} (t {SUMV[('GVLO', 4.0, 1.0)]['soak_at_t_s']:g} s, TC-01 / TC-02 row "
    f"{SUMV[('GVLO', 4.0, 1.0)]['soak_T01_T02_C'][0]:.1f} / {SUMV[('GVLO', 4.0, 1.0)]['soak_T01_T02_C'][1]:.1f} C; jfwd_variant_v352_v2.json {JVSHA}); "
    f"at 3.0 N m it is {SUMV[('GVLO', 3.0, 1.0)]['soak_MS_y_min']:+.3f} (k_sh x0.5 {SUMV[('GVLO', 3.0, 0.5)]['soak_MS_y_min']:+.3f}, "
    f"x1.5 {SUMV[('GVLO', 3.0, 1.5)]['soak_MS_y_min']:+.3f}, shown as found)")
# ---- consequences at the selected torque (234 (1)(b) 'state the preload range and its effect on the TC-02 internal-thread shear and on
# retention'; (c) hole bearing / fretting / wear in the sizing and the inspection rule)
Fn_s = sel * 1e3 / (K_NUT * TH["d"])
R = next(r for r in out["torque_sweep_10xM5"] if r["torque_Nm"] == sel)
Rthr = next(r for r in out["tc02_thread_shear"] if r["torque_Nm"] == sel)
Rp_s, Rp_f = RP20 * kT(T_SOAK), RP20 * kT(T_FA1)
# soak (no pressure): screw tension only, maximum preload + thermal rise at the soak maximum
st_soak = ((1.0 + SCAT) * Fn_s + dF_th(T_SOAK)) / TH["As"]
# FA1S: chamber pressure at which the combined (max preload + thermal 45.6 C, SF 1.0) check reaches k_T Rp0.2
st_f = ((1.0 + SCAT) * Fn_s + dF_th(T_FA1)) / TH["As"]
tau_on = math.sqrt(max(Rp_f ** 2 - st_f ** 2, 0.0)) / math.sqrt(3.0)
p_on = tau_on * A3 * 10 / A_P


def k_min(T, thermal):
    """lowest nut factor K at the selected torque that keeps the LC2 combined yield check >= 0 (the +25 % bound = K 0.16)."""
    Rp = RP20 * kT(T)
    tf = 1.5 * (P_LC2 * A_P / 10) / A3
    Fmax = math.sqrt(Rp ** 2 - 3.0 * tf ** 2) * TH["As"] - (dF_th(T) if thermal else 0.0)
    return round(sel * 1e3 / (Fmax * TH["d"]), 4), round(Fmax, 0)


def bearing(V, sf, T):
    Fty, Ftu = tab("AL6061-T6", "Fty", T), tab("AL6061-T6", "Ftu", T)
    Fbry, Fbru = MAT["AL6061-T6"]["Fbry_over_Fty_eD2"]["v"] * Fty, MAT["AL6061-T6"]["Fbru_over_Ftu_eD2"]["v"] * Ftu
    sb = V / (TH["d"] * T_WALL)
    stb = V / (TH["D1"] * (L_EFF))
    return {"T_C": T, "SF_y": sf[0], "SF_u": sf[1], "V_N": round(V, 0), "case_bearing_MPa": round(sb, 1), "Fbry_MPa": round(Fbry, 1),
            "Fbru_MPa": round(Fbru, 1), "case_MS_y": ms(Fbry, sf[0] * sb), "case_MS_u": ms(Fbru, sf[1] * sb),
            "TC02_tap_bearing_MPa": round(stb, 1), "tap_MS_y": ms(Fbry, sf[0] * stb), "tap_MS_u": ms(Fbru, sf[1] * stb)}


V_LC1, V_LC2 = P_LC1 * A_P / 10, P_LC2 * A_P / 10
c60 = checks(10, sel, 6.0, 1.0, 1.0, T_LC2, thermal=True, label="60 bar abs, SF 1.0, 78.6 C, max preload + thermal")
FBRY_LC2 = MAT["AL6061-T6"]["Fbry_over_Fty_eD2"]["v"] * tab("AL6061-T6", "Fty", T_LC2)
KV = {"LC2_78.6C_ruled": k_min(T_LC2, False), "LC2_78.6C_thermal": k_min(T_LC2, True), "LC2_100C_thermal": k_min(T_LC2B, True)}


def t_limit(thermal, key="yield_combined", ms_key="MS_y"):
    """highest uniform joint temperature (C, 0.1 K steps) at which the LC2 check at the selected torque keeps MS >= 0."""
    T = 20.0
    while T < 200.0 and checks(10, sel, P_LC2, 1.5, 2.0, T + 0.1, thermal=thermal)[key][ms_key] >= 0.0:
        T += 0.1
    return round(T, 1) if T < 200.0 else ">= 200 (not reached in the joint range)"


TLIM = {"LC2_yield_combined_thermal_C": t_limit(True), "LC2_yield_combined_ruled_C": t_limit(False),
        "LC2_ult_interaction_thermal_C": t_limit(True, "ult_interaction", "MS_u"),
        "note": ("uniform joint temperature at which the LC2 check at the selected torque reaches MS 0 (k_T, k_Tu from the SS316L "
                 "proxy table; thermal rise per dF_th): the gap-conductance variant J-FWD-row temperature at the end of the burn is "
                 "compared with these limits")}
out["selected"] = {
    "torque_Nm": sel, "method": "M-T1L", "thread_locker": ("LOCTITE 243 (Henkel, medium strength) or an equivalent medium-strength anaerobic "
                                                           "thread locker rated -55..+180 C; J-FWD row maxima (SIM, B1 v352_NF2b, "
                                                           "jfwd_variant_v352_v2): TC-01 wall "
                                                           f"{max(v['row_T_max_C']['TC01'][0] for v in JV['sources_SIM'].values()):.1f} C, "
                                                           "TC-02 tap zone (where the locker is) "
                                                           f"{max(v['row_T_max_C']['TC02_tap'][0] for v in JV['sources_SIM'].values()):.1f} C, "
                                                           "screw mean "
                                                           f"{max(v['row_T_max_C']['Ts'][0] for v in JV['sources_SIM'].values()):.1f} C: "
                                                           "below the 180 C rating"),
    "preload_N": {"F_nom": round(Fn_s, 0), "F_min_-25pc": round(0.75 * Fn_s, 0), "F_max_+25pc": round(1.25 * Fn_s, 0),
                  "thermal_rise_CALC": {f"{t:g}C": round(dF_th(t), 0) for t in (T_FA1, 54.2, T_LC2, T_LC2B, T_SOAK)},
                  "v3.5.1_5.53Nm_for_reference": {"F_nom": 5530, "F_min": 4148, "F_max": 6912}},
    "K_validity": dict(KV, note=(f"[K_min, F_max allowed (N)]: the LC2 combined yield check at {sel:g} N m stays >= 0 for an actual nut factor at "
                            "or above K_min (preload = T / (K d)); the ruled +25 % bound equals K 0.16 at K_nom 0.20. The Loctite 243 wet-locker "
                            "K is NOT stated in the TDS: TO-VERIFY by a torque-tension test of HW-101 in a 6061-T6 M5-6H coupon with the locker "
                            f"(acceptance: the highest measured preload at {sel:g} N m <= {KV['LC2_78.6C_thermal'][1]:.0f} N, the 78.6 C LC2 check "
                            f"with the thermal rise; <= {KV['LC2_100C_thermal'][1]:.0f} N for the 100 C bound)")),
    "LC2_temperature_limit": TLIM,
    "LC2_margins": {k: {"MS_y_combined": R[k]["yield_combined"]["MS_y"], "MS_u_interaction": R[k]["ult_interaction"]["MS_u"]}
                    for k in ("LC2_78.6C_ruled", "LC2_78.6C_thermal", "LC2_100C_ruled", "LC2_100C_thermal")},
    "FA1S_margins": {"MS_u_interaction_maxpreload_thermal": R["FA1S_45.6C_thermal"]["ult_interaction"]["MS_u"],
                     "MS_y_shear_only_minor": R["FA1S_45.6C_thermal"]["yield_shear_only_minor"]["MS_y"],
                     "MS_y_combined_info": R["FA1S_45.6C_thermal"]["yield_combined"]["MS_y"],
                     "combined_yield_onset_bar_abs": round(p_on * 10.0, 1)},
    "FA1S_preload_relaxation_argument": (
        "The installation preload is a displacement-controlled, self-relieving load (set by the screw stretch at tightening), not an "
        "external load. At FA1S (abnormal, one event, SF 1.0) the combined check with the +25 % preload reaches k_T Rp0.2 at about "
        f"{p_on * 10.0:.0f} bar abs; above that the screw yields in tension over its free thread, which lowers the preload and does not "
        "lower the shear capacity: the shear on the minor area alone stays below 0.577 k_T Rp0.2 at 151.04 bar abs (MS "
        f"{R['FA1S_45.6C_thermal']['yield_shear_only_minor']['MS_y']:+.3f}) and the ultimate interaction with the full +25 % preload passes "
        f"(MS {R['FA1S_45.6C_thermal']['ult_interaction']['MS_u']:+.3f}). So the joint carries FA1S without shear yield or rupture; "
        "what it may lose is preload, and the screws may carry a small permanent stretch. Hence the 233 (4) rule: all 10 HW-101 are "
        "replaced (new screws, fresh locker) and the holes and taps gauged after any recorded Pc above 60 bar abs. At 60 bar abs the "
        f"combined check with the +25 % preload and the 78.6 C thermal rise has MS {c60['yield_combined']['MS_y']:+.3f} (no yield below the rule's threshold)."),
    "check_60bar_abs_SF1_78.6C": c60,
    "soak_tension_only_119.7C": {"sigma_t_MPa": round(st_soak, 1), "kT_Rp_MPa": round(Rp_s, 1), "MS_y": ms(Rp_s, st_soak)},
    "TC02_internal_thread_shear": {"basis": "FED-STD-H28 strip area, L_eff 6.35 mm, max preload + thermal rise, unfactored (installation load)",
                                   "LC2_78.6C": Rthr["LC2_78.6C"], "soak_119.7C": Rthr["soak_119.7C"], "FA1S_45.6C": Rthr["FA1S_45.6C"],
                                   "at_5.53Nm_soak_MS_y": next(r for r in out["tc02_thread_shear"] if r["torque_Nm"] == 5.53)["soak_119.7C"]["MS_y"]},
    "retention": {
        "friction_mu0.2_ASSUMED_kN": {"F_min_cold": round(10 * 0.2 * 0.75 * Fn_s / 1e3, 2), "F_nom_cold": round(10 * 0.2 * Fn_s / 1e3, 2),
                                      "F_min_78.6C": round(10 * 0.2 * (0.75 * Fn_s + dF_th(T_LC2)) / 1e3, 2)},
        "joint_load_kN": {"LC1_25.01bar": round(P_LC1 * A_P / 1e3, 2), "LC2_45bar": round(P_LC2 * A_P / 1e3, 2), "FA1S_151bar": round(P_FA1S * A_P / 1e3, 2)},
        "statement": (
            f"At {sel:g} N m the friction capacity (mu 0.2 ASSUMED) is {10 * 0.2 * 0.75 * Fn_s / 1e3:.2f} kN at the minimum preload and "
            f"{10 * 0.2 * Fn_s / 1e3:.2f} kN at the nominal preload with a cold joint, "
            + ("both below" if 10 * 0.2 * Fn_s < P_LC1 * A_P else "the minimum below")
            + f" the LC1 joint load ({P_LC1 * A_P / 1e3:.2f} kN): "
            + ("the head is expected to slip into bearing at the first pressurisation of a normal firing" if 10 * 0.2 * Fn_s < P_LC1 * A_P
               else "at the low end of the scatter the head can slip into bearing at the first pressurisation of a normal firing")
            + " (at 5.53 N m it held, 8.29 kN). LC2 and FA1S were bearing-type at any torque (234 (1)(c)). "
            "Once in bearing the screws are shear pins at LC1 too: case bearing "
            f"{V_LC1 / (TH['d'] * T_WALL):.1f} MPa per screw at LC1 (unfactored) against Fbry {FBRY_LC2:.0f} MPa (78.6 C), so hole damage per firing is not "
            "expected; the slip (up to the 0.26 mm radial hole clearance, match-drilled) is a one-way settle to bearing, then a small "
            "cyclic bearing load each firing: fretting and wear are covered by the gauge interval. Loosening: the thread locker, not the "
            "preload, retains the screw (M-T1L); the bore O-rings g1/g2 are radial seals and do not depend on the axial position within "
            "the hole clearance (FEA3D's 231 (3) contact sub-model with preload at nominal and +25 % confirms the slip and bearing)")},
    "hole_bearing_sizing": {"LC1_unfactored": bearing(V_LC1, (1.0, 1.0), T_LC2), "LC2_SF1.5_2.0": bearing(V_LC2, (1.5, 2.0), T_LC2),
                            "LC2_SF1.5_2.0_100C": bearing(V_LC2, (1.5, 2.0), T_LC2B),
                            "FA1S": "jfwd_v352_v1.json O1: case bearing +0.338 / +0.649, tap bearing +1.248 / +1.771 (45 C, SF 1.0; preload-independent)"},
    "intervals_ASSUMED_until_test": {
        "HW101_replacement": (f"replace all 10 HW-101 (new screws, fresh LOCTITE 243, M-T1L at {sel:g} N m) at every J-FWD disassembly (the "
                              "locker is single-use) and at the latest every 10 firings; immediately after any recorded Pc above 60 bar abs "
                              "(233 (4)). 10 firings ASSUMED until a test: torque-tension plus breakaway / prevailing torque of HW-101 in a "
                              "6061-T6 M5-6H coupon after 10 thermal cycles 20 -> 120 C"),
        "gauge_TC01_holes_TC02_taps": ("gauge all 10 TC-01 holes (plain pin gauges GO 5.50 / NO-GO 5.68, i.e. Phi 5.5 H13 per ISO 273 medium / "
                                       "ISO 286, drawing tolerance TO-DEFINE) and all 10 TC-02 taps (ISO 1502 M5-6H GO / NO-GO thread plug "
                                       "gauges) after firing 1, then every 5 firings and at every HW-101 replacement, and after any recorded "
                                       "Pc above 45 bar abs (MEOP exceeded). Reject: hole NO-GO enters or visible elongation / fretting "
                                       "on the bearing side; tap GO does not run to depth or NO-GO enters more than 2 turns -> part to "
                                       "MRB (a helical-coil repair is NOT pre-approved: it changes the strip area and needs a re-check). "
                                       "5 firings ASSUMED until the first gauge results")},
    "fea3d_contact_submodel_parameter": {"HW101_preload_N_per_screw": {"nominal": round(Fn_s, 0), "plus25": round(1.25 * Fn_s, 0),
                                                                      "minus25_info": round(0.75 * Fn_s, 0)},
                                         "thermal_rise": "not added to these numbers: CALC +215 N at 45.6 C / +501 N at 78.6 C if the "
                                                         "sub-model does not carry the screw / case differential expansion itself",
                                         "torque": f"{sel:g} N m, K 0.20 (ASSUMED), method M-T1L"}}
# ---- v2: J-F1 acceptance (allowed installation preload = the max measured preload at the selected torque), all checks
AV = JV["allowed_installation_preload_N"]
Rp_soak = RP20 * kT(T_SOAK)
JF1_CAND = {"LC2_78.6C_uniform_thermal": KV["LC2_78.6C_thermal"][1], "LC2_100C_uniform_thermal": KV["LC2_100C_thermal"][1],
            "soak_119.7C_uniform_thermal": round(Rp_soak * TH["As"] - dF_th(T_SOAK), 0)}
for b in ("merged", "GVLO", "GVHI"):
    a = AV[f"{b}_ksh_x1"]
    JF1_CAND[f"variant_{b}_ksh_x1 ({a['governing_check']}, t {a['frame_t_s']:g} s, TC-01 / TC-02 {a['T01_C']} / {a['T02_C']} C)"] = a["F_inst_max_N"]
jk = min(JF1_CAND, key=lambda k: JF1_CAND[k])
F_JF1 = JF1_CAND[jk]
F_JF1_15 = AV["ALL_BOUNDS_ksh_x1.5"]["F_inst_max_N"]
F_MIN_JF1 = round(0.75 * Fn_s, 0)
out["J-F1_acceptance"] = {
    "torque_Nm": sel, "max_preload_N": F_JF1, "K_min": round(sel * 1e3 / (F_JF1 * TH["d"]), 4), "governing": jk,
    "candidates_N": JF1_CAND, "k_sh_x1.5_sensitivity": {"max_preload_N": F_JF1_15, "K_min": round(sel * 1e3 / (F_JF1_15 * TH["d"]), 4),
                                                       "note": "if the case shell is 50 % stiffer than estimated (k_sh ASSUMED +/-50 %)"},
    "min_preload_N": F_MIN_JF1, "K_max": round(sel * 1e3 / (F_MIN_JF1 * TH["d"]), 4),
    "statement": (f"J-F1 at {sel:g} N m passes when every reading is <= {F_JF1:.0f} N (K >= {sel * 1e3 / (F_JF1 * TH['d']):.4f}; governing: {jk}) "
                  f"and >= {F_MIN_JF1:.0f} N (K <= {sel * 1e3 / (F_MIN_JF1 * TH['d']):.3f}, the -25 % scatter bound used for the retention "
                  f"statement). With k_sh x1.5 the limit is {F_JF1_15:.0f} N (K >= {sel * 1e3 / (F_JF1_15 * TH['d']):.4f}); the ruled +25 % "
                  f"preload at K 0.20 is {1.25 * Fn_s:.0f} N")}
# ---- v2: 2.5 N m fallback rows (lead: 'soak x0.5 / x1 / x1.5 (k_sh), LC2, FA1S, LC1 bearing, J-F1 limit')
TQF = 2.5
RF = next(r for r in out["torque_sweep_10xM5"] if r["torque_Nm"] == TQF)
RFt = next(r for r in out["tc02_thread_shear"] if r["torque_Nm"] == TQF)
FnF = TQF * 1e3 / (K_NUT * TH["d"])
out["fallback_2.5Nm"] = {
    "torque_Nm": TQF, "use": (f"fallback if J-F1 at {sel:g} N m gives a reading above {F_JF1:.0f} N, or if the lead lowers the torque: the "
                              f"allowed preload is the same {F_JF1:.0f} N, so at {TQF:g} N m J-F1 needs K >= {TQF * 1e3 / (F_JF1 * TH['d']):.4f}"),
    "preload_N": {"F_nom": round(FnF, 0), "F_min_-25pc": round(0.75 * FnF, 0), "F_max_+25pc": round(1.25 * FnF, 0)},
    "LC2_margins": {k: {"MS_y_combined": RF[k]["yield_combined"]["MS_y"], "MS_u_interaction": RF[k]["ult_interaction"]["MS_u"]}
                    for k in ("LC2_78.6C_ruled", "LC2_78.6C_thermal", "LC2_100C_ruled", "LC2_100C_thermal")},
    "FA1S_margins": {"MS_u_interaction_maxpreload_thermal": RF["FA1S_45.6C_thermal"]["ult_interaction"]["MS_u"],
                     "MS_y_shear_only_minor": RF["FA1S_45.6C_thermal"]["yield_shear_only_minor"]["MS_y"],
                     "MS_y_combined_info": RF["FA1S_45.6C_thermal"]["yield_combined"]["MS_y"]},
    "LC1_bearing_retention": {"friction_mu0.2_kN": {"F_min_cold": round(10 * 0.2 * 0.75 * FnF / 1e3, 2), "F_nom_cold": round(10 * 0.2 * FnF / 1e3, 2)},
                              "LC1_joint_load_kN": round(P_LC1 * A_P / 1e3, 2),
                              "LC1_case_bearing": bearing(V_LC1, (1.0, 1.0), T_LC2),
                              "statement": ("bearing-type at LC1 as at 3.0 N m (friction below the LC1 joint load at the nominal preload); "
                                            "the case and tap bearing margins do not depend on the preload")},
    "soak_variant_screw_tension_MS_y": {b: {f"k_sh_x{f:g}": SUMV[(b, TQF, f)]["soak_MS_y_min"] for f in (0.5, 1.0, 1.5)} for b in ("merged", "GVLO", "GVHI")},
    "LC2_variant_MS_y_min": {b: SUMV[(b, TQF, 1.0)]["LC2_MS_y_min"] for b in ("merged", "GVLO", "GVHI")},
    "TC02_internal_thread_shear": {"uniform": {"LC2_78.6C": RFt["LC2_78.6C"]["MS_y"], "soak_119.7C": RFt["soak_119.7C"]["MS_y"]},
                                   "variant_MS_y_min": {b: SUMV[(b, TQF, 1.0)]["thread_MS_y_min"] for b in ("merged", "GVLO", "GVHI")}},
    "J-F1_limit": {"max_preload_N": F_JF1, "K_min": round(TQF * 1e3 / (F_JF1 * TH["d"]), 4), "min_preload_N": round(0.75 * FnF, 0),
                   "K_max": round(TQF * 1e3 / (0.75 * FnF * TH["d"]), 4)}}
out["selected_variant_rows"] = {
    "source": f"jfwd_variant_v352_v2.json {JVSHA}",
    "rows": {f"{b}_ksh_x{f:g}": SUMV[(b, sel, f)] for b in ("merged", "GVLO", "GVHI") for f in (0.5, 1.0, 1.5)}}
out["selected"]["K_validity"]["note"] = (out["selected"]["K_validity"]["note"] + f" | v2: J-F1 acceptance = the lowest of these and the "
                                         f"gap-variant limits: <= {F_JF1:.0f} N (K >= {sel * 1e3 / (F_JF1 * TH['d']):.4f}), see J-F1_acceptance")
s = json.dumps(out, indent=1)
open("/home/claude/work/mechanical/v352/jfwd/jfwd_preload_v352_v2.json", "w").write(s)
print("jfwd_preload_v352_v2.json", hashlib.sha256(s.encode()).hexdigest()[:16], "k_b", round(K_B), "k_m", round(k_m(20)), "dF_th", out["stiffness_ASSUMED"]["dF_th_N"])
r = out["reviewer_reproduction_v351_8xM5_5.53Nm"]
print("reviewer v351 8x M5: nominal RT", r["nominal_RT"]["MS_y_nominal_preload"], "nominal hot", r["nominal_hot"]["MS_y"], "+25 % hot", r["plus25_hot"]["MS_y"])
for row, thr, ret in zip(out["torque_sweep_10xM5"], out["tc02_thread_shear"], out["retention"]):
    f = lambda k: f"{row[k]['yield_combined']['MS_y']:+.3f}/{row[k]['ult_interaction']['MS_u']:+.3f}"
    print(f"T {row['torque_Nm']:4.2f} Fnom {row['LC2_78.6C_ruled']['F_nom_N']:6.0f} | LC2 78.6 ruled {f('LC2_78.6C_ruled')} th {f('LC2_78.6C_thermal')} | "
          f"LC2 100 ruled {f('LC2_100C_ruled')} th {f('LC2_100C_thermal')} | FA1S u {row['FA1S_45.6C_thermal']['ult_interaction']['MS_u']:+.3f} "
          f"y-shear {row['FA1S_45.6C_thermal']['yield_shear_only_minor']['MS_y']:+.3f} y-comb {row['FA1S_45.6C_thermal']['yield_combined']['MS_y']:+.3f} | "
          f"TC02 thr soak {thr['soak_119.7C']['MS_y']:+.3f}/{thr['soak_119.7C']['MS_u']:+.3f} LC2 {thr['LC2_78.6C']['MS_y']:+.3f} | "
          f"fric Fmin {ret['friction_capacity_kN_mu0.2_Fmin']} kN")
print("selected torque", sel)

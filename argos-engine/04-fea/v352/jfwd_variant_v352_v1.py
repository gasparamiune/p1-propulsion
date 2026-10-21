"""J-FWD HW-101 at the gap-conductance variant temperatures (lead 2026-10-20 (2) variant; CHANGELOG 234 (1)(b) basis kept).  Mechanical,
2026-10-20, v1.  CALC on SIM temperatures; stiffnesses ASSUMED as in jfwd_preload_v352.py.
What the variant adds to jfwd_preload_v352_v1.json (uniform joint temperature): TC-01 and TC-02 at different temperatures at the screw row.
  (a) through-wall term: dF_w = (alpha_Al(T01) dT01 - alpha_A4(Ts) dTs) L_grip k_bm  (L_grip 3.15 mm, k_bm = k_b k_m / (k_b + k_m));
  (b) ring-growth mismatch: the case ring (T01) grows radially against the plug (T02) by d = alpha_Al (T01 - T02) r_fit at r_fit 28.6 mm
      (> 0: the case moves away from the plug and stretches the screws; < 0 unloads them), resisted by the case shell at the 10 screws
      (long thin cylinder, ring-load mode + local point-load mode: k_sh about 21 kN/mm per screw, CALC (Roark-type, ASSUMED +/-50 %)) in
      series with the screw: dF_r = d k_sh k_b / (k_sh + k_b).
  Screw temperature Ts = mean of the TC-01 wall mean and the TC-02 tap-zone mean at the row (ASSUMED; the 2D model has no screw).
Checks: LC2 (45 bar, SF 1.5 / 2.0) combined yield / ultimate interaction at the end of the burn (21.65 s) with the max preload; soak
(no pressure) screw tension only, and the TC-02 internal-thread shear, at every frame time given."""
import json, math, hashlib, sys
import numpy as np
sys.path.insert(0, "/home/claude/work/mechanical/v352/jfwd")
sys.argv = [sys.argv[0]]
import importlib.util
spec = importlib.util.spec_from_file_location("jp", "/home/claude/work/mechanical/v352/jfwd/jfwd_preload_v352.py")
# re-use the constants / functions of the ruled-basis script without re-writing its output: exec its top part only
src = open("/home/claude/work/mechanical/v352/jfwd/jfwd_preload_v352.py").read().split("T_LC2, T_LC2B, T_FA1, T_SOAK")[0]
ns = {}
exec(compile(src, "jfwd_preload_v352.py(head)", "exec"), ns)
tab, kT, kTu, strip_area, TH, A3, RP20, RM20, K_B, k_m = (ns[k] for k in ("tab", "kT", "kTu", "strip_area", "TH", "A3", "RP20", "RM20", "K_B", "k_m"))
A_P, L_EFF, T_WALL, GAP_FIT, MAT = ns["A_P"], ns["L_EFF"], ns["T_WALL"], ns["GAP_FIT"], ns["MAT"]
K_SH = 21000.0
R_FIT = 28.6
L_G = T_WALL + GAP_FIT


def sec_alpha(m, T):
    return tab(m, "alpha", T)


def dF(T01, T02):
    Ts = 0.5 * (T01 + T02)
    kbm = K_B * k_m(T01) / (K_B + k_m(T01))
    dw = (sec_alpha("AL6061-T6", T01) * (T01 - 20.0) - sec_alpha("SS316L", Ts) * (Ts - 20.0)) * L_G * kbm
    d = sec_alpha("AL6061-T6", 0.5 * (T01 + T02)) * (T01 - T02) * R_FIT
    dr = d * K_SH * K_B / (K_SH + K_B)
    return Ts, dw, dr


def check(torque, T01, T02, p=0.0, sfy=1.5, sfu=2.0):
    Ts, dw, dr = dF(T01, T02)
    Fmax = 1.25 * torque * 1e3 / (0.20 * TH["d"]) + dw + dr
    V = p * A_P / 10
    st, tf = Fmax / TH["As"], sfy * V / A3
    Rp, Rm = RP20 * kT(Ts), RM20 * kTu(Ts)
    o = {"T01_C": round(T01, 1), "T02_C": round(T02, 1), "Ts_C": round(Ts, 1), "dF_wall_N": round(dw), "dF_ring_N": round(dr), "F_max_N": round(Fmax),
         "MS_y_combined": round(Rp / math.sqrt(st ** 2 + 3 * tf ** 2) - 1, 4)}
    if p > 0:
        Rt, Rs = Fmax / (Rm * TH["As"]), sfu * V / (0.6 * Rm * A3)
        o["MS_u_interaction"] = round(1 / math.sqrt(Rt ** 2 + Rs ** 2) - 1, 4)
    else:
        o["MS_u_tension"] = round(Rm * TH["As"] / Fmax - 1, 4)
    An = strip_area(L_EFF)
    o["TC02_thread_MS_y"] = round(0.577 * tab("AL6061-T6", "Fty", T02) / (Fmax / An) - 1, 4)
    o["TC02_thread_MS_u"] = round(MAT["AL6061-T6"]["Fsu_over_Ftu"]["v"] * tab("AL6061-T6", "Ftu", T02) / (Fmax / An) - 1, 4)
    return o


# SIM row temperatures (thermal frame z 134.06 +/- 2.6 mm; TC-01 wall mean, TC-02 tap-zone r >= 19.5 mean), v352_NF2b B1 runs
ROW = {"v352_NF2b_merged": {21.65: (75.8, 75.9), 64.7: (110.7, 110.6), 166.7: (119.6, 119.6)},
       "v352_NF2b_GVLO": {21.65: (60.0, 81.2), 37.7: (126.4, 92.2), 51.7: (152.6, 93.7), 64.7: (158.0, 96.0), 100.0: (147.1, 101.6),
                          166.7: (129.1, 106.5), 266.7: (117.3, 108.2)}}
if len(sys.argv) > 1:
    pass
out = {"id": "jfwd_variant_v352", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
       "k_sh_N_mm_ASSUMED": K_SH, "row_temperatures_SIM": {k: {str(t): v for t, v in d.items()} for k, d in ROW.items()}, "results": {}}
for fld, d in ROW.items():
    for tq in (4.0, 3.5, 3.0):
        r = {}
        for t, (a, b) in sorted(d.items()):
            r[f"t{t:g}"] = check(tq, a, b, p=(4.5 if t == 21.65 else 0.0))
        out["results"][f"{fld}_{tq:g}Nm"] = r
s = json.dumps(out, indent=1)
open("/home/claude/work/mechanical/v352/jfwd/jfwd_variant_v352_v1.json", "w").write(s)
print("jfwd_variant_v352_v1.json", hashlib.sha256(s.encode()).hexdigest()[:16])
for k, r in out["results"].items():
    print(k)
    for t, o in r.items():
        print("  ", t, o)

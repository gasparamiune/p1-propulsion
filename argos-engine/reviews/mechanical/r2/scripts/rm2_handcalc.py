"""REV-MECH-2 (independent reviewer): hand checks cited in REVIEW-MECHANICAL-R2 (own arithmetic; DERIVED unless tagged).

A  J-FWD joint (8 x M5 radial, TC-01 case wall / TC-02 head) at FA1S (SF 1.0, line 188 (9)) and at LC2 (MEOP 45 bar, SF 1.5 / 2.0,
   ENG-09): per-screw shear from FEA3D's stored connector forces (SIM) and from p x bore area / 8; case net-section Pm, bearing,
   shear-out; screw shear on the thread minor area; screw combined with the installation preload of HW-101.
B  TC-01 membrane at z -60 (FEA3D's own hand check, re-done) and the FA1S section force.
C  Mounting resultants: equilibrium of the published ring totals.
D  F4 J-FD01 / J-FD09: bolt-yield margins re-computed from the published per-case loads, torque windows, A4-80 option.
E  Allowable requirements implied by the LC2 re-post: NZ-03 char Sc, TC-02 Ftu(T) (T-F1).
F  Servo inertia J and the servo-in-series rocking frequencies.

Inputs (read-only): 04-fea/assembly3d/results/{f1_post_fa1_c71, f4_secondary, engine_mount_data_v351}.json, 04-fea/src/engmat.py,
03-cad/src/data/hardware_v351.json, FEA3D deck cache (TC-01 forward end), reviewer results rm2_repost_lc2_lc1v351_c71.json.
usage: python -I rm2_handcalc.py <out.json>
"""
from __future__ import annotations
import sys, json, math
from pathlib import Path
import numpy as np

HUB = Path("/home/claude/work/shared-fallback/engine")
A3 = HUB / "04-fea/assembly3d/results"
R2 = HUB / "reviews/mechanical/r2/results"
sys.path.insert(0, str(HUB / "04-fea/src"))
import engmat  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
import rm2_repost as RP  # noqa: E402

M = engmat.MATERIALS
G = 9.81                      # FEA3D solver gravity constant (REPORT 2.1)
OP_NET = 202.92487            # N/MPa, FE pressure resultant (reviewer rm2_op_resultant: 202.925 at L1)


def al(mat, key, T):
    d = M[mat][key]
    return float(np.interp(T, d["T_C"], d["v"])) / 1e6


def kT_ss(T):                 # A4 bolt hot-strength proxy, as FEA3D f4_secondary.k_T_bolt (EN 10088 1.4404 Rp0.2(T)/Rp0.2(20); ASSUMED proxy)
    return al("SS316L", "Fty", max(T, 20.0)) / al("SS316L", "Fty", 20.0)


def ms(cap, dem):
    return cap / dem - 1.0


out = {}

# ---------------------------------------------------------------------------------------------------------- A  J-FWD
fa1 = json.loads((A3 / "f1_post_fa1_c71.json").read_text())
cs = fa1["states"]["A1_22.2"]["cases"]
jf = {}
for cid in ("FA1Q", "FA1S"):
    f = cs[cid]["connectors"][0]["forces"]
    jf[cid] = {"op_MPa": cs[cid]["subcases"][0]["OP"], "shear_N": [f[f"JF{k}"]["shear_resultant_N"] for k in range(8)],
               "screw_axial_N": [f[f"JF{k}"]["screw_axial_N"] for k in range(8)]}
per_MPa = {c: float(np.mean(v["shear_N"]) / v["op_MPa"]) for c, v in jf.items()}
r_i, r_o = 57.15 / 2, 63.5 / 2
t = r_o - r_i
A_bore = math.pi * r_i ** 2
A_gross = math.pi * (r_o ** 2 - r_i ** 2)
D_hole, D_scr, n_scr = 5.5, 5.0, 8          # HW-101 / hole census: case hole 5.5, M5 screw
A_net = A_gross - n_scr * D_hole * t
d3, As = 4.019, 14.18                        # M5 thread minor diameter and stress area (ISO 724 / 898, AS RECALLED; as FEA3D f4 TH table)
A_d3 = math.pi / 4 * d3 ** 2
hw = json.loads((HUB / "03-cad/src/data/hardware_v351.json").read_text())
hw101 = next(r for r in hw["lines"] if r["id"] == "HW-101")
F_pre = 0.65 * 600.0 * As                    # HW-101 torque basis: 0.65 Rp0.2,min x As (K 0.2 ASSUMED) = 5531 N
# TC-01 forward end above the J-FWD hole row (mesh, L1 deck of fa1_c71)
z, meta = RP.load_deck("fa1_c71", "A1_22.2")
mesh = RP.Mesh(z, meta)
X1 = mesh.X[mesh.bodies["TC-01"]["nodes"]]
z_end = float(X1[:, 2].max())
z_hole = 127.51
e_edge = z_end - z_hole
jfwd = {"inputs": {"r_i": r_i, "r_o": r_o, "t_mm": t, "A_bore_mm2": A_bore, "A_gross_mm2": A_gross, "A_net_mm2": A_net, "D_hole": D_hole,
                   "D_screw": D_scr, "A_minor_mm2": A_d3, "As_mm2": As, "F_preload_nom_N": F_pre, "HW-101_torque_Nm": hw101["torque_Nm"],
                   "TC01_z_end_mm": z_end, "z_hole_mm": z_hole, "e_mm": e_edge, "e_over_D": e_edge / D_scr,
                   "shear_per_screw_per_MPa_N": per_MPa, "FE_connectors": jf}}
for case, P, sfy, sfu, T_case, T_scr in (("FA1S", 15.1038, 1.0, 1.0, 45.9, 45.9), ("LC2_MEOP45", 4.5, 1.5, 2.0, 79.4, 79.4)):
    V_mean = per_MPa["FA1S"] * P
    V_max = max(jf["FA1S"]["shear_N"]) / jf["FA1S"]["op_MPa"] * P
    V_hand = A_bore * P / n_scr
    F_tot = sum(jf["FA1S"]["shear_N"]) / jf["FA1S"]["op_MPa"] * P
    Fty, Ftu = al("AL6061-T6", "Fty", T_case), al("AL6061-T6", "Ftu", T_case)
    Fbry, Fbru = M["AL6061-T6"]["Fbry_over_Fty_eD2"]["v"] * Fty, M["AL6061-T6"]["Fbru_over_Ftu_eD2"]["v"] * Ftu
    Fsu = M["AL6061-T6"]["Fsu_over_Ftu"]["v"] * Ftu
    Pm = F_tot / A_net
    sig_br = V_max / (D_scr * t)
    A_so = 2.0 * (e_edge - 0.5 * D_hole) * t          # two shear planes from the hole edge to the free end (conservative length)
    tau_so = V_max / A_so
    kT = kT_ss(T_scr)
    tau_y, tau_u = 0.577 * 600.0, 0.6 * 800.0          # A4-80 ISO 3506-1 minima x shear factors (0.577 von Mises, 0.6 Rm; ASSUMED)
    tau = V_max / A_d3
    sig_pre = F_pre / As

    def comb(fp, kt, sf):                              # von Mises of preload tension (stress area) + factored shear (minor area) vs kT Rp0.2
        return ms(kt * 600.0, math.sqrt((fp / As) ** 2 + 3.0 * (sf * V_max / A_d3) ** 2))
    jfwd[case] = {"P_MPa": P, "SF": [sfy, sfu], "T_case_C": T_case, "T_screw_C": T_scr,
                  "V_per_screw_mean_N": V_mean, "V_per_screw_max_N": V_max, "V_hand_pA_over_8_N": V_hand, "F_total_N": F_tot,
                  "case_Fty_Ftu_MPa": [Fty, Ftu],
                  "case_net_section_Pm_MPa": Pm, "MS_case_Pm": [ms(Fty, sfy * Pm), ms(Ftu, sfu * Pm)],
                  "case_bearing_MPa": sig_br, "Fbry_Fbru_MPa": [Fbry, Fbru], "MS_case_bearing": [ms(Fbry, sfy * sig_br), ms(Fbru, sfu * sig_br)],
                  "case_shear_out_MPa": tau_so, "MS_case_shear_out_u": ms(Fsu, sfu * tau_so),
                  "screw_tau_minor_MPa": tau, "screw_tau_stress_area_MPa": V_max / As, "kT_screw_proxy": kT,
                  "MS_screw_shear_minor_RT": [ms(tau_y, sfy * tau), ms(tau_u, sfu * tau)],
                  "MS_screw_shear_minor_hot": [ms(kT * tau_y, sfy * tau), ms(kT * tau_u, sfu * tau)],
                  "MS_screw_shear_stressarea_RT": [ms(tau_y, sfy * V_max / As), ms(tau_u, sfu * V_max / As)],
                  "screw_preload_tension_MPa": sig_pre,
                  "MS_screw_combined_yield_preload_nom_RT": comb(F_pre, 1.0, sfy),
                  "MS_screw_combined_yield_preload_nom_hot": comb(F_pre, kT, sfy),
                  "MS_screw_combined_yield_preload_plus25_hot": comb(1.25 * F_pre, kT, sfy),
                  "MS_screw_combined_yield_no_preload_RT": comb(0.0, 1.0, sfy),
                  "friction_capacity_total_N_mu0.2_nom_preload": n_scr * 0.2 * F_pre}
out["A_JFWD"] = jfwd

# ---------------------------------------------------------------------------------------------------------- B  TC-01 membrane
sec = cs["FA1S"]["section_force_case_mid"]
Fz_hand = (A_bore - OP_NET) * 15.1038
pc = RP.PC_MAX
sh, sz, sr = pc * r_i / t, (A_bore - OP_NET) * pc / A_gross, -pc / 2
vm_l = math.sqrt(0.5 * ((sh - sz) ** 2 + (sz - sr) ** 2 + (sr - sh) ** 2))
out["B_TC01_membrane"] = {"FA1S_section_force_FE_N": sec["Fz_total_N"], "FA1S_section_force_hand_N": Fz_hand,
                          "ratio_FE_over_hand": sec["Fz_total_N"] / Fz_hand,
                          "LC1_hoop_axial_radial_MPa": [sh, sz, sr], "LC1_vm_hand_MPa": vm_l,
                          "note": "FEA3D REPORT 5: FE membrane vM 20.29-20.36 MPa at z -60, LC1 B1_21.65; axial uses (bore area - net thrust area)"}

# ---------------------------------------------------------------------------------------------------------- C  mounting resultants
md = json.loads((A3 / "engine_mount_data_v351.json").read_text())
m_model = 2.8862523457090568 + 0.2170077993130549 + 0.9705783879185009 + 0.029234192964360223    # runs/fa1_c71/mass.json groups
expect = {"FA1Q": OP_NET * 9.0, "FA1S": OP_NET * 15.1038, "FA1T": 3600.0, "LC1": OP_NET * pc - m_model * 4.04 * G,
          "F2 LC6 hard landing 10 g": m_model * 10.0 * G, "F2 LC2F stuck pintle": 907.7}
out["C_mount_equilibrium"] = {"m_model_kg": m_model, "expected_axial_N": expect,
                              "note": "published 'total F' z column of tables/engine_mount_data_v351.md: LC1 345, FA1Q 1826, FA1S 3065, FA1T 3600, "
                                      "LC6 402, LC2F 908 N; lateral LC1 25 (0.61 g x m 24.55), LC6 120 (3 g x m 120.75)",
                              "lateral_expected_N": {"LC1": m_model * 0.61 * G, "LC6": m_model * 3.0 * G}}

# ---------------------------------------------------------------------------------------------------------- D  F4 joints
f4 = json.loads((A3 / "f4_secondary.json").read_text())


def bolt_y(size_As, F_max, P, sfy, kT, Rp, phi=None):
    add = sfy * P if phi is None else phi * sfy * P
    return ms(kT * Rp * size_As, F_max + add)


dres = {}
for jn, As_, Rp in (("J-FD01", 5.03, 450.0), ("J-FD09", 8.78, 450.0)):
    J = f4["joints"][jn]
    pre = J["preload"]
    rows = []
    for c in J["cases"]:
        kT = kT_ss(c["T_bolt_C"])
        rows.append({"case": c["case"], "variant": c.get("seal_area", c.get("hose_EI_Nm2")), "P_N": c["P_N"], "SF": c["SF"], "T_C": c["T_bolt_C"],
                     "kT": kT, "MS_bolt_y_bounding_FEA3D": c["MS_bolt_y"], "MS_bolt_y_bounding_reviewer": bolt_y(As_, pre["F_max_N"], c["P_N"], c["SF"][0], kT, Rp),
                     "MS_bolt_y_phi02_FEA3D": c["MS_bolt_y_phi02"], "MS_bolt_y_phi02_reviewer": bolt_y(As_, pre["F_max_N"], c["P_N"], c["SF"][0], kT, Rp, 0.2),
                     "MS_preload_only_hot": ms(kT * Rp * As_, pre["F_max_N"])})
    worst = min(rows, key=lambda r: r["MS_bolt_y_bounding_reviewer"])
    dres[jn] = {"preload": pre, "As": As_, "Rp": Rp, "n_cases": len(rows),
                "max_abs_diff_vs_FEA3D": max(max(abs(r["MS_bolt_y_bounding_reviewer"] - r["MS_bolt_y_bounding_FEA3D"]),
                                                 abs(r["MS_bolt_y_phi02_reviewer"] - r["MS_bolt_y_phi02_FEA3D"])) for r in rows),
                "worst_bounding": worst, "worst_phi02": min(rows, key=lambda r: r["MS_bolt_y_phi02_reviewer"])}
# J-FD01 options at the governing case (10 g envelope, bounding R7 area): RT, torque window (phi 0.2, separation + bolt yield), A4-80
w = dres["J-FD01"]["worst_bounding"]
P, sfy, kT = w["P_N"], w["SF"][0], w["kT"]
Fnom = dres["J-FD01"]["preload"]["F_nom_N"]
Tq = 1.0
lo = (1 - 0.2) * sfy * P / 0.75 * 0.2 * 3.0e-3          # T (N m) for MS_sep_phi02 = 0 at F_min = 0.75 F_nom, F = T / (K d)
hi = (kT * 450.0 * 5.03 - 0.2 * sfy * P) / 1.25 * 0.2 * 3.0e-3
dres["J-FD01"]["options"] = {"MS_bolt_y_bounding_RT": bolt_y(5.03, 1.25 * Fnom, P, sfy, 1.0, 450.0),
                             "MS_bolt_y_phi02_RT": bolt_y(5.03, 1.25 * Fnom, P, sfy, 1.0, 450.0, 0.2),
                             "torque_window_phi02_sep_and_bolt_y_Nm": [lo, hi],
                             "A4-80_at_1.0Nm_bounding_hot": bolt_y(5.03, 1.25 * Fnom, P, sfy, kT, 600.0),
                             "A4-80_at_1.0Nm_phi02_hot": bolt_y(5.03, 1.25 * Fnom, P, sfy, kT, 600.0, 0.2)}
out["D_F4"] = dres

# ---------------------------------------------------------------------------------------------------------- E  LC2 allowable requirements
lc2 = json.loads((R2 / "rm2_repost_lc2_lc1v351_c71.json").read_text())
req = {}
for stn, st in lc2["states"].items():
    p = st["cases"]["LC2_MEOP45_SF1.5/2.0"]["parts"]
    for s in ("regular", "all"):
        r = p["NZ-03"][s]
        req.setdefault("NZ-03", {})[f"{stn}_{s}"] = {"MS": r["MS"], "Sc_needed_MPa_for_MS0": 20.0 / (1.0 + r["MS"]), "node": r["node"],
                                                     "T_C": r["T_C"], "dist_mm": r["dist_to_singular_mm"], "class": r["nearest_singular_class"]}
    r = p["TC-02"]["regular"]
    vm_ = r["vm"]
    req.setdefault("TC-02", {})[stn] = {"MS_u": r["MS_u"], "vm_MPa": vm_, "T_C": r["T_C"], "Ftu_needed_MPa": 2.0 * vm_,
                                        "ratio_to_Ftu_RT_min_260": 2.0 * vm_ / 260.0, "Ftu_used_MPa": al("AL6061-T6", "Ftu", r["T_C"])}
req["TC-02_LC1_REPORT_4.1"] = {"vm_MPa": 102.4, "T_C": 159.0, "ratio_needed": 2.0 * 102.4 / 260.0,
                               "line_212_thresholds": "Ftu(149 C) >= 0.765, Ftu(181 C) >= 0.661 of Ftu,RT,min (S-AX basis)"}
for k, v in (("LC1_tie_edge_B1_19", -0.071), ("FA1S_tie_edge_SF1", -0.126)):
    req.setdefault("NZ-03_other", {})[k] = {"MS": v, "Sc_needed_MPa": 20.0 / (1.0 + v)}
out["E_requirements"] = req

# ---------------------------------------------------------------------------------------------------------- F  servo inertia / rocking
mm = {m["dof"]: m for m in md["engine_mount_modes"]}
n2 = (53.47 / 11.139) ** 2 if False else 23.04          # gear-ratio^2 at neutral (n = 4.8, GNC 'n48' convention)
F_ = {}
for dof in ("r_y", "r_x"):
    m = mm[dof]
    I = m["I_eff_kgm2"]
    f58, f174 = m["f_with_servo_k58_Hz_DERIVED"], m["f_with_servo_k174_Hz_DERIVED"]
    F_[dof] = {"I_eff": I, "f_rigid_servo_Hz": m["f_FE_rigid_servo_Hz"], "f_scaled_pose_K_Hz": m["f_scaled_to_pose_model_K_Hz"],
               "f_servo_k58_k174_Hz": [f58, f174],
               "check_f58": math.sqrt(m["K_with_servo_k58_Nm_per_rad"] / I) / (2 * math.pi),
               "J_added_1to1_ratio": {str(J): math.sqrt(I / (I + J)) for J in (0.76e-3, 1.6e-3, 2.7e-3)},
               "J_reflected_n2_ratio": {str(J): math.sqrt(I / (I + n2 * J)) for J in (0.76e-3, 1.6e-3, 2.7e-3)}}
out["F_modal_J"] = F_

Path(sys.argv[1]).write_text(json.dumps(out, indent=1, default=float))


def r3(x):
    return None if x is None else round(x, 3)


print("A J-FWD inputs:", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in jfwd["inputs"].items() if k != "FE_connectors"})
for case in ("FA1S", "LC2_MEOP45"):
    j = jfwd[case]
    print(f"A {case}: V mean/max/hand {j['V_per_screw_mean_N']:.0f}/{j['V_per_screw_max_N']:.0f}/{j['V_hand_pA_over_8_N']:.0f} N; "
          f"Pm net {j['case_net_section_Pm_MPa']:.1f} MPa MS {r3(j['MS_case_Pm'][0])}/{r3(j['MS_case_Pm'][1])}; "
          f"bearing {j['case_bearing_MPa']:.1f} vs {j['Fbry_Fbru_MPa'][0]:.1f}/{j['Fbru_MPa'] if 'Fbru_MPa' in j else round(j['Fbry_Fbru_MPa'][1], 1)} "
          f"MS {r3(j['MS_case_bearing'][0])}/{r3(j['MS_case_bearing'][1])}; shear-out {j['case_shear_out_MPa']:.1f} MS_u {r3(j['MS_case_shear_out_u'])}")
    print(f"   screw tau minor {j['screw_tau_minor_MPa']:.1f} MPa: MS RT {r3(j['MS_screw_shear_minor_RT'][0])}/{r3(j['MS_screw_shear_minor_RT'][1])}, "
          f"hot (kT {j['kT_screw_proxy']:.3f}) {r3(j['MS_screw_shear_minor_hot'][0])}/{r3(j['MS_screw_shear_minor_hot'][1])}, "
          f"stress area RT {r3(j['MS_screw_shear_stressarea_RT'][0])}/{r3(j['MS_screw_shear_stressarea_RT'][1])}; "
          f"combined with preload {j['screw_preload_tension_MPa']:.0f} MPa: nom RT {r3(j['MS_screw_combined_yield_preload_nom_RT'])}, "
          f"nom hot {r3(j['MS_screw_combined_yield_preload_nom_hot'])}, +25% hot {r3(j['MS_screw_combined_yield_preload_plus25_hot'])}; "
          f"friction capacity {j['friction_capacity_total_N_mu0.2_nom_preload']:.0f} N vs total {j['F_total_N']:.0f} N")
b = out["B_TC01_membrane"]
print(f"B FA1S section force FE {b['FA1S_section_force_FE_N']:.0f} vs hand {b['FA1S_section_force_hand_N']:.0f} (ratio {b['ratio_FE_over_hand']:.4f}); "
      f"LC1 hoop/axial/radial {[round(x, 2) for x in b['LC1_hoop_axial_radial_MPa']]} vM {b['LC1_vm_hand_MPa']:.2f}")
print("C expected axial:", {k: round(v, 1) for k, v in expect.items()}, "lateral:", {k: round(v, 1) for k, v in out["C_mount_equilibrium"]["lateral_expected_N"].items()},
      "m", round(m_model, 3))
for jn, v in dres.items():
    wb, wp = v["worst_bounding"], v["worst_phi02"]
    print(f"D {jn}: max |diff| vs FEA3D {v['max_abs_diff_vs_FEA3D']:.4f}; worst bounding {r3(wb['MS_bolt_y_bounding_reviewer'])} ({wb['case']}, {wb['variant']}); "
          f"worst phi0.2 {r3(wp['MS_bolt_y_phi02_reviewer'])} ({wp['case']}, {wp['variant']}); preload-only hot {r3(wb['MS_preload_only_hot'])}")
print("D J-FD01 options:", {k: ([round(x, 3) for x in v] if isinstance(v, list) else round(v, 3)) for k, v in dres["J-FD01"]["options"].items()})
print("E NZ-03:", {k: (round(v["MS"], 3), round(v["Sc_needed_MPa_for_MS0"], 2), v["class"], v["dist_mm"]) for k, v in req["NZ-03"].items()})
print("E NZ-03 other:", {k: (v["MS"], round(v["Sc_needed_MPa"], 2)) for k, v in req["NZ-03_other"].items()})
print("E TC-02:", {k: (round(v["MS_u"], 3), v["vm_MPa"], v["T_C"], round(v["Ftu_needed_MPa"], 1), round(v["ratio_to_Ftu_RT_min_260"], 3)) for k, v in req["TC-02"].items()},
      "LC1:", round(req["TC-02_LC1_REPORT_4.1"]["ratio_needed"], 3))
for dof, v in F_.items():
    print(f"F {dof}: f rigid {v['f_rigid_servo_Hz']:.2f}, pose-K {v['f_scaled_pose_K_Hz']:.2f}, servo 58/174 {v['f_servo_k58_k174_Hz'][0]:.2f}/{v['f_servo_k58_k174_Hz'][1]:.2f} "
          f"(check {v['check_f58']:.2f}); J 1:1 {[round(x, 4) for x in v['J_added_1to1_ratio'].values()]}; J n2 {[round(x, 3) for x in v['J_reflected_n2_ratio'].values()]}")

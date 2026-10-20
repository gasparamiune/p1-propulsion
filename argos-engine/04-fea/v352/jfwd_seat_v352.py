"""J-FWD 3.0 N m FA1S hand rows at the ADOPTED head seat (a) (lead 07:21Z: d10.5 spot face, flats at r 31.313, wall 2.688 at the hole),
stated beside FEA3D's FE values (lead 07:21Z item 4).  Mechanical, 2026-10-20, v1.  CALC; every number DERIVED unless tagged.

Why this file: the TC-01 case cells of jfwd_preload_v352_v2 / jfwd_v352_v1 O1 use the v3.5.1 wall 3.125 (no spot face), and the
jfwd_v352_v1 'O1s' information row used t 2.768 (an earlier spot-face definition, 'wall drops to 2.765').  The adopted flat gives
2.688 at the hole (nominal: 31.313 - 28.625) and 2.665 at the drawing limit (bore 57.296, flat at r 31.313 +0.03/0 at its low end).

Basis (as jfwd_preload_v352_v2 'selected' FA1S rows): FA1S 151.04 bar abs, SF 1.0 / 1.0, 45.6 C, 10x M5 A4-80, 3.0 N m (F_nom 3000 N,
+/-25 %, K 0.20 ASSUMED), V per screw = p_abs x pi/4 x 57.25^2 / 10 = 3888.1 N (absolute-pressure basis, 0.7 % above the gauge basis
V 3862.0 N that FEA3D and jfwd_v352_v1 use; both are shown).  Joint is bearing-type at FA1S (234 (1)(c)): the case cells do not depend on
the preload.  Allowables: 6061-T6 Fty / Ftu (T) from engmat (LITERATURE tables of the project); Fbry = 1.4 Fty(T), Fbru = 1.6 Ftu(T) at
e/D 2.0 (engmat ratios; actual e/D 2.4), Fsy = 0.577 Fty, Fsu = engmat Fsu/Ftu x Ftu, exactly as jfwd_v352_v1.

Cells (TC-01, the adopted seat):
 (1) hole bearing sigma = V / (d t), t = the wall at the bearing line (y = 0, the hole's forward / aft generators) = r_flat - r_bore;
 (2) shear-out on two planes from the hole to the case end, A = 2 t (e - D_h / 2) with the same minimum t along the whole path
     (conservative: along the paths the wall is 2.820 under the flat for 4.47 mm, then >= 3.138 to the case end);
 (3) net section Pm = F / A_net, A_net integrated exactly over the ring section through the hole row (bore r_i, OD R31.75) minus
     the 10 holes (D_h 5.5 strips) and the 10 flat segments outside the holes (segment between the chord x = r_flat and the OD);
 (4) ligament Pm + Pb, Pb = V / (w_lig t) (bearing resultant at t/3 from the bore, triangular pressure, ASSUMED as jfwd_v352_v1)
     with t = the wall at the hole (conservative: the ligament carries the full 3.125 wall over 8.47 of its 13.47 mm);
 (5) hole-edge Neuber as jfwd_v352_v1 (iii) (sigma_el = max(FEA3D R3 399 MPa x V / V8, K_tb x bearing), Ramberg-Osgood n 15 / 30,
     local strain limit 0.52 (0.98 - R)), information beside FEA3D's band Neuber;
 (6) flat-seat head bearing p = F_S / (pi/4 (dk^2 - D_h^2)), dk 9.5 (ISO 7380-1 M5, AS RECALLED, TO-VERIFY; the button-head bearing face
     may be smaller than dk), against Fbry(T) (FEA3D's stated basis); FA1S with F_S = F_max + the 45.6 C thermal rise (3965 N, v2),
     the soak with the js4-consistent first-firing maximum (jfwd_embed_v352_v1: 4676 N at the GVLO soak, T01 158.0 C);
 (7) TC-02 engagement with the head on the flat: L_e = 10 - t - gap (CAD 7.287; drawing 7.257-7.272 with the f7 plug) against the
     8.0 full thread; internal-thread shear and tapped-thread bearing at FA1S at the v2 L_eff 6.35 (kept, conservative) and, for
     information, at L_e - 0.5 of the drawing minimum.
Screw rows are unchanged by the seat (fully threaded M5 x 10: the shear plane at the fit interface is in the thread either way): quoted
from jfwd_preload_v352_v2 'selected' FA1S_margins / TC02_internal_thread_shear."""
import json, math, hashlib
from pathlib import Path
import numpy as np

J = Path("/home/claude/work/mechanical/v352/jfwd")
OUT = J / "jfwd_seat_v352_v1.json"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
# the option() helpers and constants of jfwd_v352 (source up to its module-level option table; no side effects)
SRC = (J / "jfwd_v352.py").read_text()
NS = {}
exec(compile(SRC.split("\nOPTS = [")[0], str(J / "jfwd_v352.py"), "exec"), NS)
tab, MAT, ro_neuber, strip_area, TH = NS["tab"], NS["MAT"], NS["ro_neuber"], NS["strip_area"], NS["TH"]["M5"]
P2 = json.loads((J / "jfwd_preload_v352_v2.json").read_text())
EM = json.loads((J / "jfwd_embed_v352_v1.json").read_text())
SEL = P2["selected"]

T = 45.6
P_ABS, P_AMB = 151.04, 1.01325
D_SEAL, N = 57.25, 10
A_P = math.pi / 4.0 * D_SEAL ** 2
F_ABS = P_ABS * 0.1 * A_P
F_GAUGE = (P_ABS - P_AMB) * 0.1 * A_P
R_O, R_FLAT, D_FLAT = 63.5 / 2.0, 31.3129, 10.5
DH, D, E_EDGE, GAP_CAD = 5.5, 5.0, 12.0, 0.025
Fty, Ftu = tab("AL6061-T6", "Fty", T), tab("AL6061-T6", "Ftu", T)
E_AL = tab("AL6061-T6", "E", T)
Fbry, Fbru = MAT["AL6061-T6"]["Fbry_over_Fty_eD2"]["v"] * Fty, MAT["AL6061-T6"]["Fbru_over_Ftu_eD2"]["v"] * Ftu
Fsy, Fsu = 0.577 * Fty, MAT["AL6061-T6"]["Fsu_over_Ftu"]["v"] * Ftu
ms = lambda cap, dem: round(cap / dem - 1.0, 3)


def net_area(r_i):
    """ring section through the hole row minus 10 hole strips and 10 flat segments (outside the strips), exact quadrature."""
    A_ring = math.pi * (R_O ** 2 - r_i ** 2)
    y = np.linspace(-DH / 2.0, DH / 2.0, 20001)
    strip = np.trapezoid(np.sqrt(R_O ** 2 - y ** 2) - np.sqrt(r_i ** 2 - y ** 2), y)
    hc = math.sqrt(R_O ** 2 - R_FLAT ** 2)                    # half-chord of the flat at the OD (= the flat radius when it runs out on the OD)
    yy = np.linspace(DH / 2.0, min(hc, D_FLAT / 2.0), 20001)
    seg = 2.0 * np.trapezoid(np.clip(np.sqrt(R_O ** 2 - yy ** 2) - R_FLAT, 0.0, None), yy)
    return A_ring - N * strip - N * seg, strip, seg, hc


def cells(V, F_TOT, r_i, label):
    t = R_FLAT - r_i
    sbr = V / (D * t)
    A_so = 2.0 * t * (E_EDGE - DH / 2.0)
    tso = V / A_so
    A_n, strip, seg, hc = net_area(r_i)
    Pm = F_TOT / A_n
    w_lig = math.pi * (2.0 * R_O + 2.0 * r_i) / 2.0 / N - DH
    Pb = V / (w_lig * t)
    V8 = F_GAUGE / 8.0
    W_D = math.pi * 2.0 * R_O / N / D
    K_tb = 4.0 / (W_D - 1.0)
    s_el = max(399.0 * V / V8, K_tb * sbr)
    m2 = 0.52 * (0.98 - Fty / Ftu)
    worst = None
    for nn in (15.0, 30.0):
        s, eps = ro_neuber(s_el, E_AL, Fty, nn)
        if worst is None or eps > worst[1]:
            worst = (s, eps, nn)
    return {"label": label, "V_per_screw_N": round(V, 1), "r_bore_mm": r_i, "t_wall_at_hole_mm": round(t, 4),
            "hole_bearing": {"sigma_br_MPa": round(sbr, 1), "Fbry_MPa": round(Fbry, 1), "Fbru_MPa": round(Fbru, 1), "MS_y": ms(Fbry, sbr), "MS_u": ms(Fbru, sbr)},
            "shear_out": {"A_mm2": round(A_so, 2), "tau_MPa": round(tso, 1), "Fsy_MPa": round(Fsy, 1), "Fsu_MPa": round(Fsu, 1), "MS_y": ms(Fsy, tso), "MS_u": ms(Fsu, tso)},
            "net_section": {"A_net_mm2": round(A_n, 2), "hole_strip_mm2_each": round(strip, 3), "flat_segment_outside_hole_mm2_each": round(seg, 4),
                            "flat_half_chord_at_OD_mm": round(hc, 4), "Pm_MPa": round(Pm, 1), "MS_y": ms(Fty, Pm), "MS_u": ms(Ftu, Pm)},
            "ligament_PmPb": {"w_lig_mm": round(w_lig, 2), "Pb_MPa": round(Pb, 1), "PmPb_MPa": round(Pm + Pb, 1), "MS_y": ms(Fty, Pm + Pb), "MS_u": ms(Ftu, Pm + Pb)},
            "hole_edge_neuber_info": {"sigma_el_MPa": round(s_el, 1), "K_tb": round(K_tb, 3), "sigma_local_MPa": round(worst[0], 1), "eps_local": round(worst[1], 5),
                                      "n_RO": worst[2], "eps_limit": round(m2, 4), "MS_strain": ms(m2, worst[1])}}


R_I_NOM, R_I_MAX = 57.25 / 2.0, 57.296 / 2.0
V_ABS, V_G = F_ABS / N, F_GAUGE / N
rows = {"abs_nominal_wall": cells(V_ABS, F_ABS, R_I_NOM, "3.0 N m rows basis (p abs), wall 2.688 nominal"),
        "abs_drawing_limit_wall": cells(V_ABS, F_ABS, R_I_MAX, "3.0 N m rows basis (p abs), wall 2.665 (bore 57.296, flat r 31.313 low limit)"),
        "gauge_nominal_wall_FE_basis": cells(V_G, F_GAUGE, R_I_NOM, "FE basis (p gauge, V 3862), wall 2.688 nominal")}
# (6) flat-seat head bearing
A_HEAD = math.pi / 4.0 * (TH["dk"] ** 2 - DH ** 2)
F_FA1S = SEL["preload_N"]["F_max_+25pc"] + SEL["preload_N"]["thermal_rise_CALC"]["45.6C"]
ff = EM["torque_rows_3.0_4.0Nm"]["3Nm|CAD_nominal_js4"]["first_firing"]
Fbry_soak = MAT["AL6061-T6"]["Fbry_over_Fty_eD2"]["v"] * tab("AL6061-T6", "Fty", ff["T01_C"])
head = {"A_head_mm2": round(A_HEAD, 2), "dk_mm": TH["dk"], "dk_src": "ISO 7380-1 M5 dk 9.5 AS RECALLED, TO-VERIFY",
        "FA1S": {"F_S_N": F_FA1S, "p_MPa": round(F_FA1S / A_HEAD, 1), "Fbry_MPa": round(Fbry, 1), "MS_y": ms(Fbry, F_FA1S / A_HEAD)},
        "soak_first_firing_js4_consistent": {"F_S_N": ff["F_S_N"], "T01_C": ff["T01_C"], "p_MPa": round(ff["F_S_N"] / A_HEAD, 1),
                                             "Fbry_MPa": round(Fbry_soak, 1), "MS_y": ms(Fbry_soak, ff["F_S_N"] / A_HEAD),
                                             "source": f"jfwd_embed_v352_v1.json {sha(J / 'jfwd_embed_v352_v1.json')} torque_rows 3Nm|CAD_nominal_js4 first_firing"}}
# (7) TC-02 engagement and thread at FA1S
r_plug_cad, r_plug_dwg = 57.20 / 2.0, (57.140 / 2.0, 57.170 / 2.0)
r_tip = R_FLAT - 10.0
L_e_cad = r_plug_cad - r_tip
L_e_dwg = (r_plug_dwg[0] - r_tip, r_plug_dwg[1] - r_tip)
thr = {}
for nm, Leff in (("v2_basis_L_eff_6.35", 6.35), ("info_drawing_min_L_eff", round(L_e_dwg[0] - 0.5, 3))):
    An = strip_area(TH, Leff)
    tau = F_FA1S / An
    sbt = V_ABS / (TH["D1"] * Leff)
    thr[nm] = {"L_eff_mm": Leff, "A_n_mm2": round(An, 1), "internal_thread_shear": {"F_N": F_FA1S, "tau_MPa": round(tau, 1), "MS_y": ms(Fsy, tau), "MS_u": ms(Fsu, tau)},
               "tapped_thread_bearing": {"sigma_br_MPa": round(sbt, 1), "MS_y": ms(Fbry, sbt), "MS_u": ms(Fbru, sbt)}}
eng = {"r_flat_mm": R_FLAT, "screw_tip_r_mm": round(r_tip, 4), "L_e_CAD_mm": round(L_e_cad, 3), "L_e_drawing_mm": [round(x, 3) for x in L_e_dwg],
       "full_thread_end_r_mm_CAD": round(r_plug_cad - 8.0, 3), "tip_short_of_full_thread_end_mm_CAD": round(r_tip - (r_plug_cad - 8.0), 3),
       "v351_L_e_mm": 6.85}
fa = SEL["FA1S_margins"]
screw = {"source": f"jfwd_preload_v352_v2.json {sha(J / 'jfwd_preload_v352_v2.json')} selected (3.0 N m)",
         "V_per_screw_N": round(V_ABS, 1), "F_max_N": F_FA1S, "ult_interaction_MS": fa["MS_u_interaction_maxpreload_thermal"],
         "shear_only_yield_minor_MS": fa["MS_y_shear_only_minor"], "combined_yield_info_MS": fa["MS_y_combined_info"],
         "combined_yield_onset_bar_abs": fa["combined_yield_onset_bar_abs"],
         "TC02_internal_thread_FA1S": SEL["TC02_internal_thread_shear"]["FA1S_45.6C"],
         "unchanged_by_seat": "fully threaded M5 x 10: the shear plane at the fit interface is in the thread with or without the flat"}
FE = {"source": "FEA3D, relayed by the lead 07:21Z / 07:25Z and CHANGELOG 236 (3) / (12) (SIM, [DERIVED]); TO-CONFIRM against FEA3D's report",
      "basis": "js4 mu 0 at 3750 N (screw) and the FA1S seat checks on the spot-face seat; V 3862 N (5.53 N m comparison basis)",
      "screw_js4_FA1S": {"N_N": 4036, "V_N": 3618, "ult_interaction_MS": 0.431, "shear_only_yield_MS": 0.148, "combined_vM_info_MS": -0.005},
      "TC02_thread_FA1S": [1.144, 1.404],
      "TC01_seat_FA1S": {"hole_bearing_MPa": 268.2, "hole_bearing_MS": [0.232, 0.519], "flat_seat_head_bearing_MS": 2.86,
                         "seat_ligament_PmPb_MS": [0.798, 0.939], "shear_out_bound_MS": 0.644, "band_neuber_MS_membrane_bending2": [0.416, 0.061]},
      "TC01_seat_soak": {"flat_seat_bearing_vs_Fbry_MS_min": 1.40, "seat_PQ_vs_2Fty_MS_min": 0.577},
      "TC02_SCL_node13503_FA1S": {"Pm_MPa": 68.9, "Pm_MS": [2.424, 2.693], "PmPb_MPa": 177.6, "PmPb_MS": [0.329, 0.434], "soak_PmPb_MS_min": 2.20}}
out = {"id": "jfwd_seat_v352", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
       "inputs": {"jfwd_v352.py": sha(J / "jfwd_v352.py"), "jfwd_preload_v352_v2.json": sha(J / "jfwd_preload_v352_v2.json"),
                  "jfwd_embed_v352_v1.json": sha(J / "jfwd_embed_v352_v1.json"),
                  "TC-01 STEP (hub 03-cad/v3.5.2/parts/ENG-TC-01.step)": "1ad07e472709b1b2", "T_C": T, "p_abs_bar": P_ABS,
                  "allowables_MPa_45.6C": {"Fty": round(Fty, 1), "Ftu": round(Ftu, 1), "Fbry": round(Fbry, 1), "Fbru": round(Fbru, 1), "Fsy": round(Fsy, 1), "Fsu": round(Fsu, 1)}},
       "tc01_seat_cells": rows, "flat_seat_head_bearing": head, "tc02_engagement": eng, "tc02_thread_FA1S": thr, "screw_FA1S_3Nm": screw,
       "FE_beside": FE,
       "superseded_hand_rows": {"jfwd_v352_v1 O1 (wall 3.125, no spot face)": {"hole_bearing_MS": [0.338, 0.649]},
                                "jfwd_v352_v1 O1s (t 2.768, an earlier spot-face definition)": {"hole_bearing_MS": [0.185, 0.461]}}}
s = json.dumps(out, indent=1)
OUT.write_text(s)
r = rows["abs_nominal_wall"]
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16])
for k, v in rows.items():
    print(k, "t", v["t_wall_at_hole_mm"], "brg", v["hole_bearing"]["MS_y"], v["hole_bearing"]["MS_u"], "so", v["shear_out"]["MS_y"], v["shear_out"]["MS_u"],
          "Pm", v["net_section"]["Pm_MPa"], v["net_section"]["MS_y"], "PmPb", v["ligament_PmPb"]["PmPb_MPa"], v["ligament_PmPb"]["MS_y"], v["ligament_PmPb"]["MS_u"],
          "neu", v["hole_edge_neuber_info"]["MS_strain"], "seg", v["net_section"]["flat_segment_outside_hole_mm2_each"], "hc", v["net_section"]["flat_half_chord_at_OD_mm"])
print("head", head["FA1S"], head["soak_first_firing_js4_consistent"]["p_MPa"], head["soak_first_firing_js4_consistent"]["MS_y"])
print("eng", eng)
print("thr", json.dumps(thr))
print("allow", out["inputs"]["allowables_MPa_45.6C"])

#!/usr/bin/env python3
"""REV-MECH-1 independent hand checks (own code, no author module imported), 2026-10-13.  Units: mm, N, MPa.

C5(a) TC-01 case and TC-09 barrel membrane at FA-1 90 bar (thick-wall Lame + axial force from the free body), plain wall,
      relief groove at the FA1Q governing section, collar groove; compared with the author's S-AX SCL / section forces.
C5(b) J-FWD 8 x M5 radial screws at 92 bar (yield) and 102 bar (ultimate): end load, per-screw shear at the thread root, A4-70 and
      A4-80 allowables (ISO 3506-1 minimum Rp0.2 / Rm, AS RECALLED by the reviewer: A4-70 450/700, A4-80 600/800 MPa), shear
      allowable 0.577 Rp0.2 (von Mises) / 0.6 Rm (author's convention, kept for comparability) -> compared with joints_v1p1 and the
      scaled A4-80 claim (+0.29 / +0.61).
C5(c) 608 deep-groove ball bearings under the FA-1 thrust spike: 1.8 kN x DLF 2.0 and Combustion SDOF 3.05 kN, 2 bearings per
      axis, 8 deg stop geometry, ISO 76 static equivalent load P0 = max(Fr, 0.6 Fr + 0.5 Fa); C0 1.37 kN (author's AS RECALLED value).
C5(d) S-3D LC1 governing margin (GM-03 gimbal ring): statics of the bearing loads (exact) + local pin-seat bearing stress with a
      pin-loaded-hole peak factor band (Kt 2-4, ASSUMED) -> independent estimate of the peak and MS band.
EXTRA  bounding estimate of the TC-09 / NZ-02 radial interference the S-AX reports (0.137 mm, LC1 B1_21.65) that the linear model
      does not carry: three-ring compound cylinder (plane stress), ASSUMED carbon-phenolic modulus band 7-20 GPa (engmat stand-in).
Every number printed is tagged: DERIVED (hand formula on stated inputs), SIM (author FE value quoted), ASSUMED, AS RECALLED.
"""
import json
import math
import sys

import numpy as np

OUT = {}


def lame(p, ri, ro, r):
    k = ri * ri / (ro * ro - ri * ri)
    return p * k * (1 + ro * ro / (r * r)), p * k * (1 - ro * ro / (r * r))   # hoop, radial (internal pressure p)


def vm3(s1, s2, s3):
    return math.sqrt(0.5 * ((s1 - s2) ** 2 + (s2 - s3) ** 2 + (s3 - s1) ** 2))


# ------------------------------------------------------------------ C5(a)
p = 9.0                                   # MPa, FA1Q 90 bar abs (vacuum outside: author's convention, conservative)
ri = 28.575                               # TC-01 bore (deck nodes)
F_ax_closed = p * math.pi * ri ** 2       # closed-end bound
thrust_per_MPa = 197.36                   # N/MPa: author's own RF check (OP pressure integral); used only to show the operating split
F_ax_oper = p * (math.pi * ri ** 2 - thrust_per_MPa)
a = {}
for name, ro in (("plain_wall_z-60", 31.75), ("relief_groove_z-132.46", 30.5), ("collar_groove_z0", 31.25)):
    A = math.pi * (ro ** 2 - ri ** 2)
    sth_mean = p * ri / (ro - ri)                 # exact mean hoop of Lame over the wall
    sth_in, sr_in = lame(p, ri, ro, ri)
    for lab, F in (("closed_end_bound", F_ax_closed), ("operating", F_ax_oper)):
        sz = F / A
        a[f"{name}|{lab}"] = {"ro": ro, "A_mm2": A, "F_axial_N": F, "hoop_mean": sth_mean, "hoop_inner": sth_in, "sz": sz,
                              "sr_mean": -p / 2, "vm_membrane_mean": vm3(sth_mean, sz, -p / 2),
                              "vm_inner_surface": vm3(sth_in, sz, sr_in), "tag": "DERIVED"}
# Author SIM values for comparison (sax_results_L1_TC09IN718_thJ1revB_TC09IN_v1.json scl_governing FA1Q, A1_22.2)
a["author_SIM_case_mid_FA1Q"] = {"Pm_vm": 73.9, "membrane_r_z_theta_rz": [-4.253, 35.195, 80.996, 0.002], "Fz_section_N": -21177}
a["author_SIM_collar_groove_FA1Q"] = {"Pm_vm": 84.2, "membrane": [-4.361, 26.02, 90.78, -0.141], "Fz_section_N": -13102,
                                      "note": "collar band: the gimbal collar clamps here; Fz lower because the thrust is reacted at the groove band support (author BC)"}
a["author_SIM_governing_node_FA1Q"] = {"at_r_z": [30.114, -132.46], "vm": 125.54, "MS": 0.908, "note": "node 1.10 mm from the "
                                       "relief-groove corner (30.5, -133.487): just outside the 1.0 mm exclusion radius"}
# TC-09 IN718 barrel at 90 bar
ri9, ro9 = 30.53, 33.03
A9 = math.pi * (ro9 ** 2 - ri9 ** 2)
F9_closed = p * math.pi * ri9 ** 2
F9_oper = p * (math.pi * ri9 ** 2 - thrust_per_MPa)
a["tc09_barrel_z-180.6"] = {"ri": ri9, "ro": ro9, "hoop_mean": p * ri9 / (ro9 - ri9), "sz_closed": F9_closed / A9,
                            "sz_oper": F9_oper / A9, "F_oper_N": F9_oper,
                            "vm_membrane_oper": vm3(p * ri9 / (ro9 - ri9), F9_oper / A9, -p / 2), "tag": "DERIVED",
                            "author_SIM_FA1Q": {"Pm_vm": 105.3, "membrane_r_z_theta_rz": [-4.578, 48.716, 117.792, -0.063],
                                                "Fz_section_N": -24122, "T_C": 119.4,
                                                "note": "combined thermal + mechanical membrane; hoop 7 % above the mechanical Lame mean"}}
OUT["C5a_membranes_90bar"] = a

# ------------------------------------------------------------------ C5(b) J-FWD
r_seal = math.sqrt(6438.0 / 2.5 / math.pi)    # radius implied by the author's F_end at 25 bar (6438 N): check vs bore 28.625
d3 = 5.0 - 1.22687 * 0.8                      # ISO 724 minor diameter of the external thread M5x0.8
As = math.pi / 4 * d3 ** 2
share = 1.15                                  # author's load-sharing factor (ASSUMED by the author; reviewer keeps it)
mats = {"A4-70": (450.0, 700.0), "A4-80": (600.0, 800.0)}   # ISO 3506-1 minimum Rp0.2 / Rm, AS RECALLED (reviewer)
jf = {"r_from_author_F_end_mm": r_seal, "bore_r_deck_mm": 28.625, "d3_mm": d3, "A_root_mm2": As, "sharing_factor": share}
for P_bar in (90.0, 92.0, 102.0):
    F = P_bar / 10.0 * math.pi * r_seal ** 2
    V = F / 8 * share
    tau = V / As
    row = {"F_end_N": F, "V_per_screw_N": V, "tau_root_MPa": tau}
    for m, (rp, rm) in mats.items():
        row[f"MS_y_{m}"] = 0.577 * rp / tau - 1
        row[f"MS_u_{m}"] = 0.6 * rm / tau - 1
    jf[f"{P_bar:g}bar"] = row
jf["author"] = {"A4-70_FA1Q_90bar_tau_MPa": 262.5866, "A4-70_MS_y_90": -0.0112, "A4-80_claim_MS_y_92": 0.29, "A4-80_claim_MS_u_102": 0.61,
                "tag": "SIM/DERIVED author (joints_v1p1.json, BOM TC-02 note)"}
OUT["C5b_J_FWD"] = jf

# ------------------------------------------------------------------ C5(c) 608 under the spike
th = math.radians(8.0)
C0 = 1.37                                     # kN (author: 'C 3.45 kN, C0 1.37 kN (SKF, verify)'): AS RECALLED
br = {}
for lab, Feq in (("1.8kN_x_DLF2.0", 3.6), ("SDOF_3.05kN", 3.05)):
    Fax, Flat = Feq * math.cos(th), Feq * math.sin(th)
    # case A: lateral component along the bearing axis -> one bearing of the pair takes it as Fa (cross-located pair)
    FrA, FaA = Fax / 2, Flat
    P0A = max(FrA, 0.6 * FrA + 0.5 * FaA)
    # case B: lateral component radial to the bearing -> shared by the pair
    FrB = math.hypot(Fax / 2, Flat / 2)
    P0B = FrB
    P0 = max(P0A, P0B)
    br[lab] = {"F_axial_kN": Fax, "F_lateral_kN": Flat, "P0_caseA_kN": P0A, "P0_caseB_kN": P0B, "P0_kN": P0, "C0_kN": C0,
               "MS_static": C0 / P0 - 1, "tag": "DERIVED (C0 AS RECALLED)"}
br["author"] = {"MS_DLF2": -0.24, "MS_SDOF": -0.10, "per_bearing_kN": 1.80}
OUT["C5c_608_spike"] = br

# ------------------------------------------------------------------ C5(d) GM-03 LC1
T = 500.0
P_seat = T / 2                                # statics: two inner bearings / two outer pins share the axial thrust
d_pin, L_seat = 8.0, 49.0 - 38.5              # outer pin 8 P7 pressed radially through the ring band (r 38.5..49 at az 0, STL slice)
s_br = P_seat / (d_pin * L_seat)
Fty60 = 233.9                                 # author's AL6061-T6 Fty at the ASSUMED 60 C
g = {"P_seat_N": P_seat, "author_SIM_pin_bearing_radial_N": 250.0, "bearing_stress_MPa": s_br, "Kt_band_ASSUMED": [2.0, 4.0],
     "peak_band_MPa": [2.0 * s_br, 4.0 * s_br], "MS_band_SF1.5": [Fty60 / (1.5 * 4.0 * s_br) - 1, Fty60 / (1.5 * 2.0 * s_br) - 1],
     "author_SIM": {"vm_outside_1.5mm": [10.33, 11.07], "vm_all": [13.47, 14.52], "MS_y": [14.095, 13.089], "poses": ["centre", "betam7"]},
     "tag": "DERIVED (Kt band ASSUMED)"}
OUT["C5d_GM03_LC1"] = g

# ------------------------------------------------------------------ EXTRA TC-09 / NZ-02 interference bound
def compound(radii, E, nu, delta_at, delta):
    """n rings, plane stress, u = A r + B / r per ring; sigma_r(inner) = sigma_r(outer) = 0; continuity of sigma_r at every
    interface; u_outer - u_inner = delta at interface index delta_at (0 elsewhere).  Returns contact pressures at the interfaces."""
    n = len(E)
    M = np.zeros((2 * n, 2 * n))
    b = np.zeros(2 * n)

    def sr(i, r):   # coefficients of sigma_r for ring i in (A_i, B_i)
        c = E[i] / (1 - nu[i] ** 2)
        return {2 * i: c * (1 + nu[i]), 2 * i + 1: -c * (1 - nu[i]) / r ** 2}

    def u(i, r):
        return {2 * i: r, 2 * i + 1: 1.0 / r}
    row = 0
    for k, v in sr(0, radii[0]).items():
        M[row, k] = v
    row += 1
    for k, v in sr(n - 1, radii[-1]).items():
        M[row, k] = v
    row += 1
    for j in range(1, n):
        r = radii[j]
        for k, v in sr(j - 1, r).items():
            M[row, k] += v
        for k, v in sr(j, r).items():
            M[row, k] -= v
        row += 1
        for k, v in u(j, r).items():
            M[row, k] += v
        for k, v in u(j - 1, r).items():
            M[row, k] -= v
        b[row] = delta if j == delta_at else 0.0
        row += 1
    x = np.linalg.solve(M, b)
    pc = []
    for j in range(1, n):
        s = sum(v * x[k] for k, v in sr(j, radii[j]).items())
        pc.append(-s)
    # hoop stress at the inner surface of the outer ring (holder bore)
    i = n - 1
    c = E[i] / (1 - nu[i] ** 2)
    r = radii[n - 1]
    st = c * ((1 + nu[i]) * x[2 * i] + (1 - nu[i]) * x[2 * i + 1] / r ** 2)
    return pc, st


ext = {"delta_mm": 0.137, "where": "TC-09 bore / NZ-02 OD at r 25.0, z -210.75 (S-AX LC1 B1_21.65, author interfaces_governing)",
       "rings": "NZ-01 graphite 6.862-22.0 (E 9.8 GPa, nu 0.2) / NZ-02 carbon-phenolic 22-25 (E ASSUMED band) / TC-09 IN718 25-27.5"
                " (E 187 GPa at ~280 C, nu 0.29)", "tag": "ESTIMATE (linear, plane stress, ASSUMED carbon-phenolic E)", "cases": []}
for Ecp in (7000.0, 12000.0, 20000.0):
    pc, st = compound([6.862, 22.0, 25.0, 27.5], [9800.0, Ecp, 187000.0], [0.2, 0.3, 0.29], 2, 0.137)
    ext["cases"].append({"E_carbon_phenolic_MPa": Ecp, "p_contact_r22_MPa": pc[0], "p_contact_r25_MPa": pc[1],
                         "added_hoop_TC09_bore_MPa": st})
OUT["EXTRA_TC09_NZ02_interference_bound"] = ext

json.dump(OUT, open(sys.argv[1], "w"), indent=1)
print(json.dumps(OUT, indent=1))

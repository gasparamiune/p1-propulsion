"""MV-P balanced poppet main valve, detailed design v1.1 for CAD v3.4 (Mechanical, 2026-10-13).

v1 (mv_actuator_v1.py, block B) sized the concept with a seat bore 11.0 and a balance piston 11.4 and no stem through the seat.
The CAD layout (FS-01 module at the zone top, lead Option A) puts the poppet disc in the OUTLET chamber below the seat, the stem up
through the seat orifice and the inlet chamber to the balance piston, and the actuator ON TOP (spring, follower, cam, latch):
  opening = stem DOWN (cam pushes the follower), closing = stem UP (compression spring under the follower + pressure bias).
Pressure bias (closing, up): P1 acts up on the piston underside (A_b - A_stem) and down on the disc inside the seat line (A_s - A_stem);
net P1 (A_b - A_s) toward CLOSED when the outlet is vented; the space above the piston is at P2 through the hollow stem (balance hole).
Changes v1 -> v1.1 (DESIGN): seat 11.0 -> 11.5 and piston 11.4 -> 11.9 because the 3 mm stem passes through the orifice (net area);
second dynamic seal (4 mm rod seal to the dry actuator housing) added to the friction; spring designed (EN 10270-3 1.4310).
The segment side (outlet chamber) is at the BOTTOM of the module and its ceiling (seat-web underside) carries the S1 back-relief check
to the inlet chamber: the module is the top of the MV-to-seat segment, so vapour that reaches it can leave to the tank side.
All values DESIGN unless tagged; friction, seat stress and Cd ASSUMED as in v1.  Output: calcs/mvp_v1p1.json.
"""
from __future__ import annotations
import json, math
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "mvp_v1p1.json"

D = {
    "d_seat": (11.5, "DESIGN: seat line diameter (land 11.5-12.5)"),
    "seat_land": (0.5, "DESIGN"),
    "d_stem": (3.0, "DESIGN: stem through the orifice, 17-4PH H1150, hollow 1.2 (balance hole)"),
    "d_hole": (1.2, "DESIGN: balance hole"),
    "d_piston": (11.9, "DESIGN: A_b - A_s = 7.3 mm2 -> closing bias"),
    "d_rod": (4.0, "DESIGN: upper stem through the PTFE rod seal into the dry actuator housing"),
    "lift": (2.8, "DESIGN: curtain >= orifice net area"),
    "disc_od": (14.0, "DESIGN"), "disc_t": (3.0, "DESIGN"),
    "Cd": (0.65, "ASSUMED (v1)"),
    "P1_open": (6.5e6, "Electronics MV spec v1: pad first prepress, cold"),
    "f_piston": (30.0, "ASSUMED PTFE spring-energised piston seal 11.9 at 6.5 MPa (v1 value)"),
    "f_rod": (10.0, "ASSUMED PTFE spring-energised rod seal 4 mm"),
    "seat_stress_target": (7.0, "ASSUMED PCTFE soft seat 5-10 MPa (v1)"),
    "spring_d": (1.8, "DESIGN wire EN 10270-3 1.4310"), "spring_Dm": (12.0, "DESIGN mean diameter"),
    "spring_G": (70e3, "LITERATURE EN 10270-3 G 70 GPa (engmat SS-SPRING)"), "spring_Rm": (1850.0, "LITERATURE-approx EN 10270-3 NS 1.8 mm Rm ~1850 MPa"),
    "spring_F0": (85.0, "DESIGN preload at CLOSED (v1)"),
    "servo_angle": (45.0, "Electronics MV spec v1"), "servo_stall": (2.16, "Electronics: SB-2292SG 2.157 N m DATASHEET"),
    "latch_ratio": (10.0, "DESIGN (v1)"), "latch_factor": (2.0, "Electronics MV spec v1"),
    "moving_mass": (0.018, "ESTIMATE stem+disc+piston+follower"),
}
v = {k: x[0] for k, x in D.items()}
A = lambda d: math.pi / 4 * d * d
A_s, A_b, A_st, A_rod = A(v["d_seat"]), A(v["d_piston"]), A(v["d_stem"]), A(v["d_rod"])
A_orif = A_s - A_st
A_curt = math.pi * v["d_seat"] * v["lift"]
A_flow = min(A_orif, A_curt)
Cv = 1.156 * v["Cd"] * A_flow * 1e-6 * math.sqrt(2e5 / 1000.0) * 3600.0
F_bias = v["P1_open"] * (A_b - A_s) * 1e-6
# spring
d, Dm, G = v["spring_d"], v["spring_Dm"], v["spring_G"]
k1 = G * d ** 4 / (8 * Dm ** 3)                       # N/mm per active coil
k_target = 8.0
n_a = round(k1 / k_target, 1)
k = k1 / n_a
F0 = v["spring_F0"]
F1 = F0 + k * v["lift"]
C = Dm / d
Kw = (4 * C - 1) / (4 * C - 4) + 0.615 / C
tau1 = Kw * 8 * F1 * Dm / (math.pi * d ** 3)
tau_allow = 0.45 * v["spring_Rm"]
n_t = n_a + 2
L_solid = n_t * d
x0 = F0 / k
L_free = round(L_solid + x0 + v["lift"] + 2.5, 1)    # 2.5 mm clash allowance at OPEN
L_closed = L_free - x0
L_open = L_closed - v["lift"]
# forces, cam, latch
F_seat = F0 + F_bias
seat_area = math.pi / 4 * ((v["d_seat"] + 2 * v["seat_land"]) ** 2 - v["d_seat"] ** 2)
F_open_max = F1 + F_bias + v["f_piston"] + v["f_rod"]
th = math.radians(v["servo_angle"])
r_eff = v["lift"] / th
T_peak = F_open_max * r_eff * 1e-3
F_hold = (F1 + F_bias) / v["latch_ratio"] * v["latch_factor"]
F_close = F1 + F_bias - v["f_piston"] - v["f_rod"]
t_free = math.sqrt(2 * v["lift"] * 1e-3 * v["moving_mass"] / F_close)
cam = {"base_r_mm": 6.0, "lift_mm": v["lift"], "rise_deg": v["servo_angle"], "dwell_deg": 15.0, "width_mm": 5.0,
       "profile": "constant-velocity rise r(phi) = 6.0 + 2.8 phi/45deg, 15 deg dwell at full lift; 17-4PH H1150 + roller-less flat follower (hardened insert)"}
out = {"id": "mvp", "version": "v1.1", "date": "2026-10-13", "owner": "mechanical", "script": "03-cad/src/calcs/mvp_v1p1.py",
       "supersedes": "mv_actuator_v1.json block B (concept) for the CAD dimensions; v1 kept as the concept record",
       "method": __doc__.split("\n\n")[1], "inputs": {kk: {"v": x[0], "tag": x[1]} for kk, x in D.items()},
       "areas_mm2": {"seat": round(A_s, 2), "piston": round(A_b, 2), "stem": round(A_st, 2), "orifice_net": round(A_orif, 2), "curtain": round(A_curt, 2)},
       "Cv": round(Cv, 2), "Cv_req": 3.0, "F_bias_closed_N": round(F_bias, 1),
       "spring": {"wire_mm": d, "Dm_mm": Dm, "OD_mm": Dm + d, "n_active": n_a, "n_total": n_t, "rate_N_mm": round(k, 2), "F_closed_N": F0, "F_open_N": round(F1, 1),
                  "L_free_mm": L_free, "L_closed_mm": round(L_closed, 1), "L_open_mm": round(L_open, 1), "L_solid_mm": round(L_solid, 1),
                  "tau_open_MPa": round(tau1, 0), "tau_allow_MPa": round(tau_allow, 0), "MS_tau": round(tau_allow / tau1 - 1, 2),
                  "material": "EN 10270-3 1.4310 (302) NS, passivated; dry side (actuator housing), not N2O-wetted"},
       "seat": {"F_closed_P1_N": round(F_seat, 1), "F_closed_P0_N": F0, "land_area_mm2": round(seat_area, 2),
                "stress_P1_MPa": round(F_seat / seat_area, 1), "stress_P0_MPa": round(F0 / seat_area, 1), "target_MPa": v["seat_stress_target"]},
       "opening": {"F_open_max_N": round(F_open_max, 1), "cam_r_eff_mm": round(r_eff, 2), "T_cam_peak_Nm": round(T_peak, 3),
                   "servo_use_of_stall": round(T_peak / v["servo_stall"], 2), "limit": 0.50},
       "cam": cam, "latch_hold_force_N_incl_2x": round(F_hold, 1),
       "closing": {"F_close_N": round(F_close, 1), "t_undamped_s": round(t_free, 4), "dashpot_target_s": 0.030},
       "pockets": {"balance_chamber": "above the piston, P2 via the 1.2 mm hollow stem: Eotvos(1.2 mm) ~3 at 8 m/s2 -> a dead pocket (~0.5 cm3); "
                                      "reported in the trap table"},
       "tag": "DESIGN numbers; friction, seat stress, Cd ASSUMED (B-MV-1 bench gates them)"}
OUT.write_text(json.dumps(out, indent=1))
if __name__ == "__main__":
    print(json.dumps({kk: out[kk] for kk in ("areas_mm2", "Cv", "F_bias_closed_N", "spring", "seat", "opening", "latch_hold_force_N_incl_2x", "closing")}, indent=1))

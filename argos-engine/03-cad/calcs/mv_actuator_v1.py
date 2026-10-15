"""NC main valve (MV) body and actuator check (Mechanical, v1, 2026-10-13).

Question (lead relay 2026-10-13, Electronics MV ACTUATOR SPEC v1): select an MV body (N2O, O2-clean, MAWP >= 8.42 MPa,
proof >= 10.5 MPa, Cv >= 3, vented ball) and design spring, latch and linkage for the spring-closed, servo-cocked,
magnet-latched concept, with the opener (Savox SB-2292SG, about 45 deg of horn for the 90 deg quarter turn) loaded to
<= 50 % of 2.16 N m.

A. COTS body: Swagelok 60 series 3/8 in (62 series), reinforced PTFE seats.  Torque from Swagelok MS-02-136 Table 7.
B. Buildable alternative that fits the opener budget: balanced poppet MV-P (Mechanical concept, numbers ESTIMATE).

Every input carries its tag.  Run: python mv_actuator_v1.py  ->  mv_actuator_v1.json
"""
from __future__ import annotations
import json, math, hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
INLB = 0.112985                     # N m per in-lb
PSI = 6894.757

# ---------------------------------------------------------------- requirements (lead / Electronics MV ACTUATOR SPEC v1)
REQ = {
    "MAWP_Pa": (8.42e6, "LEAD 2026-10-13: tank fire-case relieving 8.35 MPa + check crack 0.07"),
    "proof_Pa": (10.5e6, "LEAD 2026-10-13: tank proof"),
    "Cv_min": (3.0, "combustion.json isolation_valve.Cv_min (line budget)"),
    "dP_open_Pa": (6.5e6, "Electronics MV spec v1: pad first prepress, cold, O2-clean and dry"),
    "servo_stall_Nm": (2.16, "Electronics: SB-2292SG at 6.0 V (DATASHEET 2.157 N m)"),
    "servo_use_frac": (0.50, "Electronics MV spec v1: <= 50 % of stall"),
    "servo_angle_deg": (45.0, "Electronics MV spec v1: about 45 deg of horn"),
    "valve_angle_deg": (90.0, "quarter turn"),
    "spring_factor": (2.0, "Electronics MV spec v1: spring torque >= 2x running torque at the closing dP"),
    "close_time_s": (0.10, "Electronics MV spec v1: latch release to CLOSED switch"),
    "latch_factor": (2.0, "Electronics MV spec v1: holding force >= 2x spring force at the latch radius"),
}
v = {k: x[0] for k, x in REQ.items()}
T_servo_allow = v["servo_stall_Nm"] * v["servo_use_frac"]

# ---------------------------------------------------------------- A. Swagelok 62T (3/8 in, reinforced PTFE seats)
SW62 = {
    "body": "Swagelok 60 series, 3-piece, 316 SS, 3/8 in (62 series), reinforced PTFE seats, e.g. SS-62TS6 (3/8 in tube ends)",
    "Cv": (3.8, "DATASHEET products.swagelok.com SS-62TS6"),
    "orifice_mm": (7.1, "DATASHEET MS-01-146 (0.281 in)"),
    "rating_psig_by_F": ({"-20..100": 2200, "150": 1850, "200": 1500, "250": 1150}, "DATASHEET MS-01-146 (2-way, reinforced PTFE)"),
    "vent": ("internal upstream ball vent NUV (e.g. SS-62TNUVS6); rated as the standard 2-way valve", "DATASHEET MS-02-28 rev D (ordering NUV / NDV / UV / DV)"),
    "cleaning": ("SC-11 per MS-06-63, ASTM G93 Level C", "DATASHEET MS-01-146; combination with NUV TO-VERIFY with the distributor"),
    "torque_inlb_start_end": ({0: (18, 16), 1000: (22, 20), 1500: (25, 22), 2200: (26, 23)}, "DATASHEET Swagelok MS-02-136 Table 7 (62T), temperature factor 1.0 at -20..100 F, media factor 1.0 (water, N2)"),
    "price": "TO-QUOTE (Swagelok authorised distributor, delivery Sonderborg DK-6400)",
}


def interp_torque(psig):
    tab = SW62["torque_inlb_start_end"][0]
    ks = sorted(tab)
    for a, b in zip(ks[:-1], ks[1:]):
        if a <= psig <= b:
            f = (psig - a) / (b - a)
            return tuple(INLB * (tab[a][i] + f * (tab[b][i] - tab[a][i])) for i in (0, 1))
    raise ValueError(psig)


psig_open = v["dP_open_Pa"] / PSI
T_start, T_run = interp_torque(psig_open)
T_spring_closed = v["spring_factor"] * T_run                  # at the closed end of the closing stroke
k_rel = 0.20                                                   # ASSUMED: low-rate preloaded torsion spring, +20 % over 90 deg
T_spring_open = T_spring_closed * (1 + k_rel)
T_valve_max = max(T_spring_closed + T_start, T_spring_open + T_run)
ratio = v["valve_angle_deg"] / v["servo_angle_deg"]           # servo torque = valve torque x (valve angle / servo angle), ideal linkage
T_servo_req = T_valve_max * ratio
A = {
    "spec": SW62,
    "psig_at_open_dP": round(psig_open, 1),
    "T_start_Nm": round(T_start, 2), "T_run_Nm": round(T_run, 2),
    "T_spring_closed_Nm": round(T_spring_closed, 2), "T_spring_open_Nm": round(T_spring_open, 2),
    "T_valve_stem_max_Nm": round(T_valve_max, 2),
    "linkage_ratio_valve_over_servo_angle": ratio,
    "T_servo_required_Nm": round(T_servo_req, 1), "T_servo_allowed_Nm": T_servo_allow,
    "excess_factor": round(T_servo_req / T_servo_allow, 1),
    "servo_angle_needed_for_budget_deg": round(v["valve_angle_deg"] * T_valve_max / T_servo_allow, 0),
    "opener_needed_rated_Nm_at_1to1": round(2 * T_valve_max, 1),
    "verdict": "body meets MAWP/proof (151 bar at 37 C, 103 bar at 93 C), Cv 3.8, vent and SC-11; NOT openable by the SB-2292SG within 50 % of 2.16 N m",
    "tag": "DERIVED from DATASHEET torques; ideal linkage (no losses), so the shortfall is a lower bound",
}

# ---------------------------------------------------------------- B. balanced poppet MV-P (buildable, ESTIMATE)
Bp = {
    "d_seat_mm": (11.0, "DESIGN: curtain area at full lift = seat bore area"),
    "lift_mm": (2.75, "DESIGN: d/4"),
    "Cd": (0.65, "ASSUMED poppet discharge coefficient (0.6-0.7)"),
    "d_balance_mm": (11.4, "DESIGN: balance piston slightly larger than the seat -> pressure bias toward CLOSED (fail-safe)"),
    "seal_friction_N": (30.0, "ASSUMED PTFE spring-energised balance seal at 6.5 MPa (10-30 N class); TO-VERIFY vendor / bench B-MV-1"),
    "seat_land_mm": (0.5, "DESIGN: PCTFE seat insert land width"),
    "seat_stress_MPa": (7.5, "ASSUMED PCTFE soft-seat sealing stress (5-10 MPa)"),
    "spring_rate_N_mm": (8.0, "DESIGN compression spring, 17-7PH or 302 SS, outside the wetted path"),
    "moving_mass_kg": (0.015, "ESTIMATE poppet + stem + follower"),
    "latch_lever_ratio": (10.0, "DESIGN over-centre latch lever: magnet force = spring load / 10"),
    "a_N2O_m_s": (350.0, "ASSUMED liquid N2O sound speed near saturation (300-400 m/s), TO-VERIFY"),
    "L_tank_to_MV_m": (0.30, "ASSUMED feed line length"),
    "mdot_kg_s": (0.26, "combustion.json max flow"),
    "rho_kg_m3": (785.1, "CoolProp 20 C (inlet_e1m)"),
    "d_line_mm": (7.75, "3/8 x 0.035 tube ID"),
}
b = {k: x[0] for k, x in Bp.items()}
A_seat = math.pi / 4 * b["d_seat_mm"] ** 2
A_curt = math.pi * b["d_seat_mm"] * b["lift_mm"]
A_eff = b["Cd"] * min(A_seat, A_curt) * 1e-6
Kv = A_eff * math.sqrt(2 * 1e5 / 1000.0) * 3600.0
Cv = 1.156 * Kv
dA = math.pi / 4 * (b["d_balance_mm"] ** 2 - b["d_seat_mm"] ** 2)
F_bias = v["dP_open_Pa"] * dA * 1e-6                          # toward CLOSED
F_seat_need = math.pi * b["d_seat_mm"] * b["seat_land_mm"] * b["seat_stress_MPa"]
F_s0 = max(F_seat_need - F_bias, 2 * b["seal_friction_N"])
F_s0 = 5.0 * math.ceil(F_s0 / 5.0)
F_s1 = F_s0 + b["spring_rate_N_mm"] * b["lift_mm"]
F_open_max = F_s1 + b["seal_friction_N"] + F_bias
W_open = ((F_s0 + F_s1) / 2 + b["seal_friction_N"] + F_bias) * b["lift_mm"] * 1e-3
theta = math.radians(v["servo_angle_deg"])
T_cam_avg = W_open / theta
r_eff_mm = b["lift_mm"] / theta
T_cam_peak = F_open_max * r_eff_mm * 1e-3                      # constant-rise cam (lift linear in angle)
F_close = F_s1 + F_bias - b["seal_friction_N"]
t_close_free = math.sqrt(2 * b["lift_mm"] * 1e-3 * b["moving_mass_kg"] / F_close)
F_hold = (F_s1 + F_bias) / b["latch_lever_ratio"] * v["latch_factor"]
v_line = b["mdot_kg_s"] / (b["rho_kg_m3"] * math.pi / 4 * (b["d_line_mm"] * 1e-3) ** 2)
dP_jouk = b["rho_kg_m3"] * b["a_N2O_m_s"] * v_line
t_2La = 2 * b["L_tank_to_MV_m"] / b["a_N2O_m_s"]
t_damped = 0.030                                               # DESIGN: dashpot so that closing takes ~30 ms (<= 0.10 s)
dP_damped = dP_jouk * t_2La / t_damped
B = {
    "spec": {k: {"v": x[0], "tag": x[1]} for k, x in Bp.items()},
    "A_seat_mm2": round(A_seat, 1), "A_curtain_mm2": round(A_curt, 1), "Cv": round(Cv, 2),
    "F_bias_closed_N": round(F_bias, 1), "F_seat_need_N": round(F_seat_need, 1),
    "spring_closed_N": F_s0, "spring_open_N": F_s1,
    "F_open_max_N": round(F_open_max, 1), "W_open_J": round(W_open, 3),
    "cam_r_eff_mm": round(r_eff_mm, 2), "T_servo_avg_Nm": round(T_cam_avg, 2), "T_servo_peak_Nm": round(T_cam_peak, 2),
    "T_servo_allowed_Nm": T_servo_allow, "servo_use_of_stall": round(T_cam_peak / v["servo_stall_Nm"], 2),
    "latch_hold_force_N_incl_2x": round(F_hold, 1),
    "t_close_undamped_s": round(t_close_free, 4), "closing_with_dashpot_s": t_damped,
    "water_hammer": {"v_line_m_s": round(v_line, 2), "dP_Joukowsky_instant_MPa": round(dP_jouk / 1e6, 2), "2L_over_a_s": round(t_2La, 4),
                     "dP_with_30ms_closing_MPa": round(dP_damped / 1e6, 2),
                     "note": "an undamped poppet closes in ~1 ms: the tank-side surge would reach ~P_tank + 1.9 MPa (at the 8.42 MPa MAWP); a dashpot stretching the closing to ~30 ms cuts it to ~0.1 MPa"},
    "verdict": "fits the SB-2292SG budget (peak cam torque <= 50 % of 2.16 N m) with Cv >= 3; needs design, machining and bench test B-MV-1 (leak, Cv, opening force, closing time)",
    "tag": "ESTIMATE (Mechanical concept, ASSUMED friction/seat/sound-speed inputs)",
}

res = {"id": "mv_actuator", "version": "v1", "date": "2026-10-13", "owner": "mechanical", "script": "03-cad/src/calcs/mv_actuator_v1.py",
       "requirements": {k: {"v": x[0], "tag": x[1]} for k, x in REQ.items()}, "A_swagelok_62T_ball": A, "B_balanced_poppet_MVP": B}
out = HERE / "mv_actuator_v1.json"
out.write_text(json.dumps(res, indent=1, default=str))
print(json.dumps({"A": {k: A[k] for k in ("T_start_Nm", "T_run_Nm", "T_spring_closed_Nm", "T_valve_stem_max_Nm", "T_servo_required_Nm",
                                          "T_servo_allowed_Nm", "excess_factor", "servo_angle_needed_for_budget_deg", "opener_needed_rated_Nm_at_1to1")},
                  "B": {k: B[k] for k in ("Cv", "F_bias_closed_N", "spring_closed_N", "spring_open_N", "F_open_max_N", "W_open_J", "cam_r_eff_mm",
                                          "T_servo_avg_Nm", "T_servo_peak_Nm", "latch_hold_force_N_incl_2x", "t_close_undamped_s", "water_hammer")}},
                 indent=1))
print(out, hashlib.sha256(out.read_bytes()).hexdigest()[:16])

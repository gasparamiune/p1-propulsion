"""Stand-only head-end DN32 rupture disc: feasibility, location, reaction and discharge path (Mechanical, v1, 2026-10-13).

Lead relay 2026-10-13 item 1: an aft DN32 disc alone allows 9.1-14.8 g (grain port chokes the path); a head-end DN32 disc gives
20.6-20.8 g; both 24.7-30.7 g (Combustion two-volume relief, hard_start_multivolume_v2p4).  Is a stand-only head-end DN32 disc
feasible (stand-only head/bulkhead variant or an adapter on the injector head, flight head unchanged)?  If not, the fallback is
shorter stand windows with a rounded grain-port entrance (r >= 4 mm).

Inputs: CAD v3.4 build stations (head plug, pre-chamber), Combustion hard_start_multivolume_v2p4 inputs (P_bd 5.5 MPa, DN32 MNFA
792 mm2, K_D 0.62 -> 491 mm2 effective, L_pre 30 mm, D_pre 49.9 mm; mirrored with sha256 in iface_snapshot), lead LC-TB-S 63.1 bar.
Reaction: sonic orifice thrust F = C_F P0 A*, C_F = Gamma sqrt(2 g/(g+1)) + p*/P0 - pa/P0 with g 1.2 (ASSUMED products), DERIVED.
"""
from __future__ import annotations
import json, math
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "stand_headend_disc_v1.json"

G = 1.20                                   # ASSUMED ratio of specific heats of the chamber gas (N2O/ABS products 1.15-1.25)
PA = 1.013e5
A_MNFA = 792e-6                            # m2, DN32 minimum net flow area (Combustion)
KD = 0.62                                  # Combustion flow-resistance basis -> effective 491 mm2
P_BD = 5.5e6                               # Pa, Combustion burst basis
P_TBS = 63.1e5                             # Pa abs, lead LC-TB-S
L_PRE, D_PRE = 30.0, 49.9                  # mm (TC-06 3.6 mm, accepted)
D_CASE_ID = 57.15                          # mm
PLUG_D = 57.20                             # mm, head plug


def cf_sonic(g=G, p0=P_BD):
    gam = math.sqrt(g) * (2 / (g + 1)) ** ((g + 1) / (2 * (g - 1)))
    mom = gam * math.sqrt(2 * g / (g + 1))
    pstar = (2 / (g + 1)) ** (g / (g - 1))
    return mom + pstar - PA / p0, {"Gamma": gam, "momentum_term": mom, "p*/P0": pstar}


def main():
    import sys
    sys.path.insert(0, str(HERE.parent))
    import build, config
    P, S, reg, clog = build.build(include=("engine", "gimbal"), iterate_cg=True, overrides=config.V34_ON)
    zf, zt = float(S["inj_face"]), float(S["head_top"])
    z_pre_mid = zf - L_PRE / 2
    out = {"script": "03-cad/src/calcs/stand_headend_disc_v1.py", "date": "2026-10-13", "cad": "v3.4 build (config.V34_ON), pivot frame",
           "stations_mm": {"inj_face": round(zf, 2), "head_top": round(zt, 2), "pre_chamber": [round(zf - L_PRE, 2), round(zf, 2)]}}
    # ---------------------------------------------------------------- A. through the flight head (axial path)
    occupied = {"seat insert counterbore (flange 20.2) + M14x1": 20.2, "manifold bore": 10.0, "E1-M filter bore (radial 14, az 180)": 14.0,
                "E1-M axial 8 at r 16": 8.0, "Pc passage 2 mm (r 20.5-25)": 2.0, "torch passage 5.2/3 (r 17-25)": 5.2,
                "2 AS568-226 glands (r 25.8-28.6)": None, "8x M5 radial (r 22.1-28.6)": None, "4x M4 bonnet (r 16.5)": None}
    A_annulus_free = math.pi / 4 * (2 * 21.5) ** 2 - math.pi / 4 * 20.2 ** 2        # r 10.1-21.5 between the insert flange and the M5/gland zone
    out["A_through_flight_head"] = {
        "verdict": "NOT FEASIBLE",
        "why": ("a DN32 path needs >= 792 mm2 (one 32 mm bore, or e.g. 6x 13 mm holes) from the pre-chamber through the head plug to a disc "
                "holder above it; the plug is 57.2 mm with the seat insert (20.2 counterbore) on the axis, the M5 row and 2 glands at r 22-28.6, "
                "and the r 10-21.5 annulus already carries the manifold bore, the E1-M filter/axial drillings, the Pc and torch passages and the "
                "4 bonnet screws; any 792 mm2 of new holes there removes the injector features or the face-disc support: a different injector, "
                "not a flight-representative head"),
        "annulus_r10-21.5_gross_mm2": round(A_annulus_free, 0), "occupied_features": list(occupied)}
    # ---------------------------------------------------------------- B. stand-only case section with a radial window in the pre-chamber
    lands = 2 * 5.5                                                                     # mm, sealing land each side of a round port (ASSUMED)
    win_axial = L_PRE - 6.0                                                             # keep 3 mm to the face disc and 3 mm to the grain lip
    win_circ = A_MNFA * 1e6 / win_axial                                                 # mm (rectangle of the same area)
    arc_deg = math.degrees(win_circ / (D_CASE_ID / 2))
    V_pre = math.pi / 4 * D_PRE ** 2 * L_PRE * 1e-3                                     # cm3
    V_dead = (win_axial * win_circ * 3.175 + 0.25 * math.pi * 32 ** 2 * 20) * 1e-3      # window through the wall + 20 mm DN32 neck to the disc
    out["B_stand_case_section_window"] = {
        "verdict": "GEOMETRICALLY POSSIBLE, stand-only, NOT representative",
        "round_DN32_port_needs_axial_mm": 32 + lands, "available_axial_mm": L_PRE,
        "oblong_window_mm": [round(win_axial, 1), round(win_circ, 1)], "window_arc_deg": round(arc_deg, 0),
        "hardware": ("TC-01S: stand-only 316L case (or 316L forward section) with the window at the pre-chamber station; saddle disc holder "
                     "(oblong-to-round transition, DN32 disc) welded/bolted on the OD; TC-06S insulator with the same window; a sacrificial "
                     "phenolic or graphite heat shield in front of the disc (ASSUMED necessity: the disc face otherwise sees the pre-chamber gas "
                     "on every burn)"),
        "pre_chamber_volume_cm3": round(V_pre, 1), "added_dead_volume_cm3": round(V_dead, 1),
        "added_dead_volume_pct": round(100 * V_dead / V_pre, 0),
        "consequences": [f"pre-chamber +{V_dead:.0f} cm3 (+{100 * V_dead / V_pre:.0f} %, window through the 3.175 mm wall + a 20 mm DN32 neck, "
                         "ESTIMATE) and asymmetric (Combustion: the stand test then differs from flight in the head-end volume and mixing)", "disc exposed to hot gas -> premature-burst / fragment risk unless shielded (shield adds delay and "
                         "changes the relief area)", "TC-06/TC-01 joint and insulation changed at the hottest metal station"]}
    # ---------------------------------------------------------------- C. spacer ring between head and case (stand-only)
    out["C_spacer_ring"] = {"verdict": "POSSIBLE, changes L_pre", "L_pre_increase_mm": 32 + lands,
                            "note": "a 43 mm stand-only spacer with a radial DN32 port lengthens the pre-chamber 30 -> ~73 mm (Combustion change)"}
    # ---------------------------------------------------------------- reaction and discharge
    cf, parts = cf_sonic()
    rows = {}
    for lab, p0, A in (("burst 55 bar, A_eff 491 mm2", P_BD, KD * A_MNFA), ("LC-TB-S 63.1 bar, A_eff 491 mm2", P_TBS, KD * A_MNFA),
                       ("bound 63.1 bar, full MNFA 792 mm2", P_TBS, A_MNFA)):
        c, _ = cf_sonic(p0=p0)
        F = c * p0 * A
        rows[lab] = {"C_F": round(c, 3), "F_N": round(F, 0), "M_about_pivot_Nm": round(F * z_pre_mid * 1e-3, 0)}
    out["reaction"] = {"model": "sonic orifice, F = C_F P0 A*, g 1.2 ASSUMED", "C_F_parts": {k: round(v, 4) for k, v in parts.items()},
                       "z_pre_mid_above_pivot_mm": round(z_pre_mid, 1), "cases": rows,
                       "servo_reference": "SB-2292SG stall 2.16 N m (Electronics) through the TVC levers: the gimbal cannot react a lateral 3-6 kN "
                                          "at the head; the stand must lock the gimbal (rigid stand adapter) or the outlet must be a balanced tee"}
    out["discharge_path"] = ("radial at the disc; on the stand: DN32 elbow on the holder turning the jet aft (or a balanced tee with two opposed "
                             "outlets, net lateral load ~0) and ducted out of the test cell; never into a vehicle bay")
    out["recommendation"] = ("head-end DN32 not feasible on the flight head or as an adapter on it; possible only as a stand-only case section (B) "
                             "or spacer (C) that changes the pre-chamber Combustion is testing.  Mechanical recommends the fallback: shorter stand "
                             "windows with a rounded grain-port entrance (r >= 4 mm) and the aft TC-09S DN32 disc; reconsider B only if Combustion "
                             "accepts the changed pre-chamber on the stand")
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()

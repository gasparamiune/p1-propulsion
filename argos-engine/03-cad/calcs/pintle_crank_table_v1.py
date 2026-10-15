"""HV69 toggle-crank kinematics and needle force / servo torque vs stroke for Electronics (ENG-03 rate check), v1
(03-cad/src/calcs, 2026-10-13, Mechanical).

Coordinator 2026-10-13: ENG-03 is now >= 5 F_max/s (2500 N/s) under load; Electronics checks the HV69 rate through the toggle
crank and needs the crank kinematics and the L0/L1/L2 force-vs-stroke that Mechanical holds.  This script tabulates, from the
pintle v2.3/v2.4 model (pintle_v2p3.py, imported read-only; baseline configuration of pintle_inline_v34_v2p4.json: MGN09H rolling
guide mu 0.010, end-seal drag 2 N, plain DU link pins mu 0.15, stem seal 18.75 N, spring 0.25 N m + 0.12 N m/rad +/-10 %):
  per crank degree from the commanded-closed 10 deg (seated at 15 deg) to the stop 113.09 deg:
    lift x (mm), dx/dphi (mm/rad), link angle psi (deg), pin-friction factor, spring torque (N m, nominal);
    needle pressure force F (N, + = OPENING) for L0 (P1 3.5 / 5.5 / 7.0 MPa, P_down = ambient), L1 and L2 at the start states
    (P1 5.05 / 7.0 MPa, P_down 1.5 bar torch), and the opening servo torque (+10 % spring) and closing spring surplus (-10 %
    spring) for each (N m, at the servo spline; + = the servo must drive / the spring assists).
  hot-fire throttle line (Combustion needle_force_bounds_v2p3.csv, D_port 25 mm, 3 mm stem): per state the lift, P1, Pc,
    F_L0/L1/L2 and the opening / closing servo torques at that lift.
Laws (Combustion needle_force_v2p3, converted to + opening): L0 seated dp (A_seat - A_stem) closing blending to dp A_stem opening
over the first 0.1 mm; L1 geometric throat area; L2 seated area persists; A_seat = pi/4 5.5^2, A_stem = pi/4 3.0^2 mm2.
Everything is DERIVED from ASSUMED friction values (B-PNT-1 measures them); Electronics owns the HV69 torque-speed model.
Outputs: calcs/pintle_crank_table_v1.csv (per degree), calcs/pintle_crank_table_v1.json (meta + hot-fire rows).
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import pintle_v2p3 as p3

OUT_CSV = HERE / "pintle_crank_table_v1.csv"
OUT_JSON = HERE / "pintle_crank_table_v1.json"
BASE = dict(name="v2.3/v2.4 baseline: MGN09H + plain DU pins", mu_g=p3.MU_GUIDE["design"], s_eff=p3.GUIDES["MGN09H"]["L1_mm"],
            S=p3.S_END_SEAL["design_N"], mu_p=0.15, r_p=1.5, y_l=11.0, f_seal=p3.F_SEAL["design"])


def main():
    c = p3.Cfg(**BASE)
    phis = list(np.arange(p3.CRANK["phi_cmd_closed"], 113.0 + 1e-9, 1.0)) + [113.09]
    cases = [("L0", 3.5e6, p3.PA), ("L0", 5.5e6, p3.PA), ("L0", 7.0e6, p3.PA),
             ("L1", 5.05e6, p3.P_TORCH), ("L1", 7.0e6, p3.P_TORCH), ("L2", 5.05e6, p3.P_TORCH), ("L2", 7.0e6, p3.P_TORCH)]
    hdr = ["phi_deg", "lift_mm", "dx_dphi_mm_per_rad", "psi_link_deg", "pin_factor", "T_spring_nom_Nm"]
    for law, P1, Pd in cases:
        tag = f"{law}_P{P1/1e6:.2f}MPa"
        hdr += [f"F_{tag}_N", f"Topen_{tag}_Nm", f"Tclose_assist_{tag}_Nm"]
    rows = []
    for ph in phis:
        x = max(0.0, p3.lift(ph))
        r = [round(ph, 2), round(x, 4), round(p3.dxdphi(ph) if ph >= p3.CRANK["phi_closed"] else 0.0, 4),
             round(math.degrees(p3.psi_of(ph)), 3), round(p3.pin_factor(ph), 4), round(c.T(ph), 4)]
        for law, P1, Pd in cases:
            F = p3.F_L0(x, P1) if law == "L0" else p3.F_law(law, x, P1, Pd)
            if ph < p3.CRANK["phi_closed"]:                       # seated: the crank is not loaded by the needle (preload zone)
                r += [round(F, 2), None, None]
                continue
            to, _ = p3.servo_torque(c, ph, (1 + c.tol) * c.T(ph), F, True)
            tc, _ = p3.servo_torque(c, ph, (1 - c.tol) * c.T(ph), F, False)
            r += [round(F, 2), round(to, 4), round(tc, 4)]
        rows.append(r)
    with open(OUT_CSV, "w") as f:
        f.write("# HV69 toggle crank r 3 / link 28 mm, seated 15 deg, stop 113.09 deg (x 4.2 mm); needle force + = opening; servo torque at "
                "the spline (+10 % spring opening, -10 % spring closing surplus); calcs/pintle_crank_table_v1.py\n")
        f.write(",".join(hdr) + "\n")
        for r in rows:
            f.write(",".join("" if v is None else str(v) for v in r) + "\n")
    hot = []
    for hr in p3.hot_rows():
        x = hr["lift_mm"]
        ph = p3.phi_at_lift(x)
        rec = {"P_tank_MPa": round(hr["P_tank_Pa"] / 1e6, 2), "frac": hr["frac"], "F_thrust_N": hr["F_N"], "Pc_MPa": round(hr["Pc_Pa"] / 1e6, 4),
               "P1_MPa": round(hr["P1_Pa"] / 1e6, 4), "lift_mm": x, "phi_deg": round(ph, 2), "dx_dphi_mm_per_rad": round(p3.dxdphi(ph), 4)}
        for law in ("L0", "L1", "L2"):
            F = -hr[f"F_{law}_3mm_N"]                                 # Combustion + = closing
            to, _ = p3.servo_torque(c, ph, (1 + c.tol) * c.T(ph), F, True)
            tc, _ = p3.servo_torque(c, ph, (1 - c.tol) * c.T(ph), F, False)
            rec[f"F_{law}_open_N"] = round(F, 2)
            rec[f"Topen_{law}_Nm"] = round(to, 4)
            rec[f"Tclose_assist_{law}_Nm"] = round(tc, 4)
        hot.append(rec)
    meta = {"id": "pintle_crank_table", "version": "v1", "date": "2026-10-13", "owner": "mechanical", "script": "03-cad/src/calcs/pintle_crank_table_v1.py",
            "for": "Electronics ENG-03 HV69 rate check (coordinator 2026-10-13)", "method": __doc__.split("\n\n")[1],
            "crank": p3.CRANK, "config": BASE, "spring": p3.SPRING, "stall_Nm_HV69": p3.HV69["stall_Nm"],
            "kinematics": {"s(phi) = r cos phi + sqrt(L^2 - r^2 sin^2 phi)": "slider position from the crank axis", "lift": "s(15 deg) - s(phi)",
                           "dx_dphi_at_15deg_mm_per_rad": round(p3.dxdphi(15.0), 4), "dx_dphi_max_mm_per_rad": round(max(p3.dxdphi(p) for p in phis[5:]), 4),
                           "phi_at_dx_dphi_max_deg": round(max(phis[5:], key=p3.dxdphi), 1)},
            "csv": "03-cad/src/calcs/pintle_crank_table_v1.csv", "hot_fire_line_rows": hot,
            "hot_src": "Combustion needle_force_bounds_v2p3.csv (mirror iface_snapshot/mirror/engine/02-combustion/data/v2), D_port 25 mm, 3 mm stem columns",
            "tag": "DERIVED (pintle v2.3/v2.4 model; friction ASSUMED, B-PNT-1 measures)"}
    OUT_JSON.write_text(json.dumps(meta, indent=1))
    print(json.dumps({k: meta[k] for k in ("kinematics",)}, indent=1))
    mx = max(max(v for v in r[7::3] if v is not None) for r in rows if r[7] is not None)
    print("max opening torque over the table cases", round(mx, 3), "rows", len(rows), "hot", len(hot))


if __name__ == "__main__":
    main()

"""ENG FEA load cases (Mechanical) -- loadcases v1, 2026-10-12.

Single definition of every structural/thermal load case used by the CalculiX models (04-fea), the hand
calculations (03-cad/src/calcs/hand_calcs.py v2) and the Ansys cross-check package.  Numbers come from
03-cad/src/config.py (interface files + lead decisions); nothing is typed twice.

History
  * 2026-10-12 lead decision: chamber MEOP 31 -> 45 bar (Combustion pintle full-stroke failure case,
    data/v2/full_stroke_failure_case_v2.json: 30 C tank, Cd 0.8).  LC2 at 45 bar, LC4 hydrostatic proof at
    1.5 x 45 = 67.5 bar, new bound BN (blocked nozzle: chamber at tank pressure 63.1 bar at 30 C) checked
    against yield (SF 1.0) at temperature.  The 31 bar values of hand_calcs v1 (2026-10-11) are superseded.

Criteria (ENG-09 pressure parts, ENG-10 structure): MS = allowable / (SF x applied) - 1 >= 0 with
SF 1.5 on yield and 2.0 on ultimate at the part temperature; proof: no yield (SF 1.0 on yield) at room
temperature; BN: no yield (SF 1.0 on yield) at temperature, ultimate margin reported for information.
Graphite and phenolic have no yield: their allowables are the datasheet strengths with the ultimate SF.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAD_SRC = HERE.parents[1] / "03-cad" / "src"
sys.path.insert(0, str(CAD_SRC))

THERMAL_BC = {   # Combustion v1 Bartz BC tables (h_g(x), T_aw(x)); mirrored with sha256 in iface_snapshot (PROVENANCE.txt)
    "max": "02-combustion/data/thermal_bc_max_v1.csv",
    "50pct": "02-combustion/data/thermal_bc_50pct_v1.csv",
    "floor12p5": "02-combustion/data/thermal_bc_floor12p5_v1.csv",
}


def load_cases(P):
    v = lambda k: P[k]["v"]
    meop, proof, pbn = v("MEOP_chamber"), v("proof_factor") * v("MEOP_chamber"), v("P_blocked_nozzle")
    sfy, sfu = v("SF_yield"), v("SF_ult")
    g0 = 9.80665
    cases = [
        {"id": "LC1", "title": "Steady max thrust, gimbal neutral",
         "chamber_Pa": v("Pc_max"), "manifold_Pa": v("MEOP_tank"), "thrust_N": v("F_max"),
         "thermal": {"bc": THERMAL_BC["max"], "state": "end of the longest max-thrust burn (LC5 critical instant)"},
         "criterion": {"SF_y": sfy, "SF_u": sfu, "T": "part temperature"},
         "src": {"Pc_max": P["Pc_max"]["tag"], "thrust": P["F_max"]["tag"]}},
        {"id": "LC2", "title": "Chamber MEOP + thermal state at the critical time",
         "chamber_Pa": meop, "manifold_Pa": v("MEOP_tank"), "thrust_N": None,
         "thermal": {"bc": THERMAL_BC["max"], "state": "LC5 critical instant (hottest pressure-carrying structure)"},
         "criterion": {"SF_y": sfy, "SF_u": sfu, "T": "part temperature"},
         "src": {"MEOP": P["MEOP_chamber"]["src"]},
         "focus": ["forward closure (head) + 8 x M5 radial screws", "aft closure M63x1.5 thread + retaining lip (nozzle retention)",
                   "graphite insert", "liner / insulators", "case tube incl. collar groove and aft land"]},
        {"id": "LC2F", "title": "Pintle full-stroke failure thrust (structure)",
         "chamber_Pa": meop, "thrust_N": 907.7, "thermal": {"state": "as LC2"},
         "criterion": {"SF_y": 1.0, "SF_u": 1.5, "T": "part temperature", "note": "failure case: no yield, 1.5 on ultimate (Mechanical choice, lead to confirm)"},
         "src": {"thrust": "Combustion data/v2/full_stroke_failure_case_v2.json max F_N 907.7 N (v1 helix, 30 C, Cd 0.8)"}},
        {"id": "LC3", "title": "Max thrust + max gimbal (both axes) + lateral and angular acceleration limit loads",
         "chamber_Pa": v("Pc_max"), "thrust_N": v("F_max"), "gimbal_deg": {"commanded_norm": v("gimbal_range_deg"), "stop": v("gimbal_stop_deg")},
         "lateral_g": 1.5, "gimbal_accel_rad_s2": 519.0, "body_accel_rad_s2": 8.59,
         "criterion": {"SF_y": sfy, "SF_u": sfu}, "src": {"loads": "gnc.json v1 design_limit_loads (limit values)"},
         "outputs": ["actuator (pushrod) reactions", "inner/outer pin and 608 bearing loads", "frame ring bolt loads"]},
        {"id": "LC4", "title": "Hydrostatic proof 1.5 x MEOP, room temperature (chamber and tank)",
         "chamber_Pa": proof, "tank_Pa": v("proof_factor") * v("MEOP_tank"), "T_C": 20.0,
         "fixture": "exit blanked by a solid dummy insert (no throat) so the retaining lip carries P x pi r_bore^2 (bounds the flight insert)",
         "criterion": {"SF_y": 1.0, "SF_u": None, "note": "no yield at proof"}},
        {"id": "BN", "title": "Blocked-nozzle bound: chamber at tank pressure (30 C), hot",
         "chamber_Pa": pbn, "thrust_N": 0.0, "thermal": {"state": "as LC2 (blockage during a burn)"},
         "load_on_insert": "P x pi r_bore^2 (throat blocked: no divergent relief)",
         "criterion": {"SF_y": 1.0, "SF_u": None, "note": "stays below yield (lead 2026-10-12); ultimate margin reported"},
         "src": {"P": P["P_blocked_nozzle"]["src"]}},
        {"id": "LC5", "title": "Transient thermal over the flight duty cycle, structural at the critical instants",
         "thermal": {"bc": THERMAL_BC, "duty_cycles": "gnc.json v1 duty_cycles (DC-A1 baseline, DC-B1 longest flight burn 20.7 s, DC-D static-fire 49 s)"},
         "criterion": {"SF_y": sfy, "SF_u": sfu}},
        {"id": "LC6", "title": "Landing shock and handling/transport",
         "axial_g": 10.0, "lateral_g": 3.0, "transport_g": 3.0, "criterion": {"SF_y": sfy, "SF_u": sfu},
         "src": {"loads": "gnc.json v1 design_limit_loads"}},
        {"id": "MODAL", "title": "Gimballed engine on its actuators: first modes vs ENG-11",
         "servo_stiffness_Nm_per_rad": P["tvc_servo_stiffness"]["v"], "requirement_Hz": 25.0,
         "src": {"req": "gnc.json v1 engine rocking mode >= 25 Hz", "stiffness": P["tvc_servo_stiffness"]["tag"]}},
    ]
    for c in cases:
        for k in ("chamber_Pa", "manifold_Pa", "tank_Pa"):
            if c.get(k) is not None:
                c[k.replace("_Pa", "_bar")] = round(c[k] / 1e5, 2)
    return cases


def write(out=None):
    import config
    P, _ = config.build()
    doc = {"id": "ENG-FEA-LOADCASES", "version": "v1", "date": "2026-10-12", "owner": "mechanical",
           "history": __doc__.split("History")[1].split("Criteria")[0].strip(),
           "cases": load_cases(P)}
    out = Path(out) if out else HERE.parent / "loadcases_v1.json"
    out.write_text(json.dumps(doc, indent=1, default=str))
    return doc


if __name__ == "__main__":
    d = write(sys.argv[1] if len(sys.argv) > 1 else None)
    for c in d["cases"]:
        print(c["id"], c["title"], {k: c[k] for k in c if k.endswith("_bar")})

"""M1 gimballed mass-property ESTIMATE (2026-10-12) for mechanical.json v1, superseded by the CAD v3 ledger
(03-cad/mass_properties.json) in mechanical.json v2.

Method: the engine parts already modelled in CAD v2 (parts_engine) give mass/CG/inertia from their solids
(DERIVED); the CG-pivot architecture adds/moves items that are not yet modelled -> itemised point masses or
boxes with stated positions (ASSUMED estimate, +/-30 % each).  Frame: CAD v2 build frame (z = 0 at the head
mid-plane, +z forward, mm); the pivot is then placed at the mid-burn CG of the engine group."""
from __future__ import annotations
import sys, json, math
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parent.parents[1] / "04-fea" / "src")); sys.path.insert(0, str(HERE))
import config, layout, engmat
from partlib import Registry
from geom import parallel_axis
from gimbal_trade import engine_props


def box_I(m, d):
    d = np.array(d) * 1e-3
    return m / 12 * np.diag([d[1]**2 + d[2]**2, d[0]**2 + d[2]**2, d[0]**2 + d[1]**2])


def polar(r, a, z):
    a = math.radians(a)
    return [r * math.cos(a), r * math.sin(a), z]


def main(out=None):
    P, _ = config.build()
    S = layout.stations(P)
    reg = Registry()
    import parts_engine
    parts_engine.build_engine_parts(P, S, reg, engmat)
    E = engine_props(reg)
    drop = {"ENG-GM-06", "ENG-TC-13", "ENG-TC-14", "ENG-TC-15", "ENG-EL-05"}
    items = [(pn, m, np.array(c), np.array(I), "DERIVED CAD v2 solid") for pn, m, c, I in E["items"] if pn not in drop]
    zt = S["head_top"]
    z_p_guess = -120.0
    add = [  # pn, mass kg, centre mm (CAD v2 frame), box dims mm, note
        ("ENG-TC-12 pintle actuator bracket (6061)", 0.060, [0, 8, zt + 60], [32, 40, 105], "ASSUMED estimate"),
        ("ENG-TC-13 pintle servo standing on axis", P["pintle_servo_mass"]["v"], [0, 0, zt + 81], [20.2, 38.7, 40.3], "DATASHEET mass, position per v3 layout"),
        ("ENG-TC-14/15/16/17 crank, link 28, carriage, guide pin", 0.021, [0, 18, zt + 55], [20, 30, 40], "ASSUMED estimate"),
        ("ENG-EL-05 pintle encoder", 0.008, [0, 28, zt + 71], [25, 4, 25], "ASSUMED"),
        ("ENG-GM-01 engine collar + 2 TVC levers (6061)", 0.095, [0, 6, z_p_guess - 6], [76, 76, 30], "ASSUMED estimate"),
        ("ENG-GM-02 inner pins x2 (17-4PH)", 0.024, [0, 0, z_p_guess], [6, 80, 8], "DERIVED 8 x 30 steel"),
        ("ENG-GM-12 ball studs x2 + half pushrods x2", 0.022, polar(52, 109, z_p_guess - 23), [10, 10, 10], "ASSUMED"),
        ("ENG-FD hose share: JIC elbow + half hose + liquid", 0.066, polar(30, 250, zt + 40), [20, 20, 60], "ASSUMED (elbow 45 g, hose 0.13 kg/m)"),
        ("ENG-FD sense/torch line shares + Pc fitting", 0.030, polar(24, 200, zt + 15), [20, 20, 20], "ASSUMED"),
    ]
    for pn, m, c, d, note in add:
        items.append((pn, m, np.array(c, float) * 1e-3, box_I(m, d), note))
    grain = [it for it in items if it[0].startswith("ENG-GR")]

    def props(its):
        m = sum(i[1] for i in its); cg = sum(i[1] * i[2] for i in its) / m
        I = sum(parallel_axis(i[3], i[1], i[2] - cg) for i in its)
        return m, cg, I

    m_w, cg_w, I_w = props(items)
    dry = [i for i in items if not i[0].startswith("ENG-GR")]
    m_d, cg_d, I_d = props(dry)
    z_piv = 0.5 * (cg_w[2] + cg_d[2])            # pivot at the mid-burn CG
    piv = np.array([0, 0, z_piv])

    def about_pivot(m, cg, I):
        return parallel_axis(I, m, cg - piv)

    ring = {"m": 0.14 + 0.024 + 0.024 + 0.008, "I_xx": 0.14 * 0.046**2 / 2 + 0.048 * 0.046**2, "note": "ring 0.14 + outer pins + inner-axis bearings + encoder (ASSUMED)"}
    res = {
        "frame": "pivot at the mid-burn CG; z_engine = z_CADv2 - z_pivot_CADv2",
        "z_pivot_in_CADv2_frame_mm": round(z_piv * 1e3, 1),
        "wet": {"m_kg": round(m_w, 3), "cg_from_pivot_mm": np.round((cg_w - piv) * 1e3, 1).tolist(),
                "I_about_pivot_kgm2": np.round(about_pivot(m_w, cg_w, I_w), 5).tolist()},
        "dry_grain_burnt_out": {"m_kg": round(m_d, 3), "cg_from_pivot_mm": np.round((cg_d - piv) * 1e3, 1).tolist(),
                                "I_about_pivot_kgm2": np.round(about_pivot(m_d, cg_d, I_d), 5).tolist()},
        "ring_alpha_axis_only": ring,
        "added_items": [(pn, m, c, note) for pn, m, c, d, note in add],
        "stations_from_pivot_mm": {k: round(S[k] - z_piv * 1e3, 1) for k in ("head_top", "inj_face", "grain_top", "grain_bot", "throat", "exit", "aft_bottom", "bonnet_top")},
        "head_stack_top_from_pivot_mm": round(zt + 106 - z_piv * 1e3, 1),
    }
    if out:
        Path(out).write_text(json.dumps(res, indent=1, default=float))
    return res


if __name__ == "__main__":
    r = main(sys.argv[1] if len(sys.argv) > 1 else None)
    print(json.dumps({k: v for k, v in r.items() if k != "added_items"}, indent=1, default=float))

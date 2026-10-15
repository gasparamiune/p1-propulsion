"""Mass ledger for interfaces/mechanical.json v2 (2026-10-12, Mechanical).

Builds the CAD v3.3 engine + gimbal registry (build.build, pivot iterated onto the mid-burn CG of the 'engine' group),
then writes calcs/massprops_v2.json with
  * gimballed ('engine' group) mass, CG and inertia tensor about the pivot at wet / mid / burnout (grain scaled by
    build.mass_ledger: port growth axisymmetric, fuel burnt = config fuel_burnt_max),
  * ring (alpha axis only), horn and pushrod groups, fixed group by part,
  * the v3.3 pintle stack items (TC-11..17) with mass and CG so that the v3.4 in-line HV69 stack can be swapped in
    by pintle_stack_v34() (itemised estimate until CAD v3.4 exists),
  * per-part rows (pn, qty, material, mass each, tag) for the BOM cross-check.
CAD v3.3 has no feed or misc parts (parts_feed / parts_misc not written): the hose and line shares are added in
write_mechanical_json_v2.py as tagged estimates, not here.
"""
from __future__ import annotations
import sys, json, time, math
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2] / "04-fea" / "src"))
import build

OUT = HERE / "massprops_v2.json"
PINTLE_STACK = ("ENG-TC-11", "ENG-TC-12", "ENG-TC-13", "ENG-TC-14", "ENG-TC-15", "ENG-TC-16", "ENG-TC-17")


def _f(x, n=6):
    return [round(float(v), n) for v in x]


def main():
    t0 = time.time()
    P, S, reg, log = build.build(include=("engine", "gimbal"), iterate_cg=True)
    out = {"version": "v2", "date": "2026-10-12", "script": "03-cad/src/calcs/massprops_v2.py",
           "cad": "CAD v3.3 (config.py / parts_engine.py / parts_gimbal.py), engine + gimbal groups; feed/misc not modelled",
           "aft_section_material": P["aft_section_material"]["v"], "z_head_mid_mm": P["z_head_mid"]["v"] * 1e3,
           "cg_iteration": S["cg_iteration"], "t_build_s": round(time.time() - t0, 1),
           "fuel_burnt_max_kg": P["fuel_burnt_max"]["v"], "fuel_burnt_max_tag": P["fuel_burnt_max"].get("tag", ""),
           "fuel_burnt_max_src": P["fuel_burnt_max"].get("src", ""),
           "stations_mm": {k: float(S[k]) for k in ("head_top", "head_bot", "inj_face", "grain_top", "grain_bot", "tube_fwd", "tube_aft",
                                                    "aft_bottom", "throat", "exit", "bonnet_top", "z_seat")},
           "states": {}, "groups": {}, "pintle_stack_v33": {}, "parts": []}
    for st in ("wet", "mid", "burnout", "nograin"):
        rows, mg0 = build.mass_ledger(reg, P, st, S)
        g = build.group_props(rows, ("engine",))
        gr = [r for r in rows if r["group"] == "engine" and r["pn"].startswith("ENG-GR-")]
        out["states"][st] = {"m_kg": g["m"], "cg_mm": _f(g["cg_mm"], 4), "I_about_pivot_kgm2": [_f(r, 8) for r in np.asarray(g["I_about"])],
                             "I_about_cg_kgm2": [_f(r, 8) for r in np.asarray(g["I_cg"])], "grain_mass_kg": sum(r["m"] for r in gr)}
        # split for the analytic re-centring in write_mechanical_json_v2.py: items that stay on the pivot plane vs items that
        # move with the head when z_head_mid is iterated (build._on_pivot)
        for nm, sel in (("on_pivot", [r for r in rows if r["group"] == "engine" and build._on_pivot(r["pn"])]),
                        ("moving", [r for r in rows if r["group"] == "engine" and not build._on_pivot(r["pn"])])):
            gg = build.group_props(sel, ("engine",))
            out["states"][st][nm] = {"m_kg": gg["m"], "cg_mm": _f(gg["cg_mm"], 4), "I_about_cg_kgm2": [_f(r, 9) for r in np.asarray(gg["I_cg"])]}
        if st == "wet":
            out["grain_mass_initial_kg"] = mg0
            for grp in sorted(set(r["group"] for r in rows)):
                gg = build.group_props(rows, (grp,))
                out["groups"][grp] = {"m_kg": gg["m"], "cg_mm": _f(gg["cg_mm"], 3), "I_about_pivot_kgm2": [_f(r, 8) for r in np.asarray(gg["I_about"])],
                                      "I_about_cg_kgm2": [_f(r, 8) for r in np.asarray(gg["I_cg"])], "n_instances": gg["n"]}
            seen = {}
            for r in rows:
                k = (r["pn"], r["group"])
                d = seen.setdefault(k, {"pn": r["pn"], "group": r["group"], "qty": 0, "m_total_kg": 0.0, "m_each_kg": r["m"], "tag": r["tag"],
                                        "cg_mm_first": _f(r["cg"], 2)})
                d["qty"] += 1
                d["m_total_kg"] += r["m"]
            for (pn, grp), d in sorted(seen.items()):
                p = reg.get(pn)
                d.update({"name": p.name, "material": p.material, "process": p.process, "cots": p.cots})
                out["parts"].append(d)
            stack = [r for r in rows if r["pn"] in PINTLE_STACK]
            sp = build.group_props(stack, ("engine",))
            out["pintle_stack_v33"] = {"m_kg": sp["m"], "cg_mm": _f(sp["cg_mm"], 3), "I_about_pivot_kgm2": [_f(r, 8) for r in np.asarray(sp["I_about"])],
                                       "I_about_cg_kgm2": [_f(r, 9) for r in np.asarray(sp["I_cg"])],
                                       "items": {pn: round(sum(r["m"] for r in stack if r["pn"] == pn), 5) for pn in PINTLE_STACK}}
    OUT.write_text(json.dumps(out, indent=1, default=float))
    print("wrote", OUT, "in", round(time.time() - t0, 1), "s")
    for st, v in out["states"].items():
        print(st, round(v["m_kg"], 4), v["cg_mm"], [round(v["I_about_pivot_kgm2"][i][i], 5) for i in range(3)], "grain", round(v["grain_mass_kg"], 4))
    for g, v in out["groups"].items():
        print("group", g, round(v["m_kg"], 4), v["cg_mm"])
    print("pintle stack v3.3", out["pintle_stack_v33"])


if __name__ == "__main__":
    main()

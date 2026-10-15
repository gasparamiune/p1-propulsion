"""Mass of one build variant per part and per group (v3.5.1 fix mass deltas, coordinator CHANGELOG 184), v1, 2026-10-13, Mechanical.

usage: mass_variant_v351.py OUT.json [KEY=VALUE ...]
Builds config.V34_ON plus the KEY=VALUE overrides (json-parsed values), iterates the pivot onto the mid-burn CG as make_all does,
and writes per-part totals (mass x quantity, split by group: engine = gimballed body, ring, horn, pushrod, fixed, flexible halves
already split by build.mass_ledger), group totals at the 'wet' state (fresh grain, the landing-mass relevant figure is 'burnout'),
solid validity and volume of every non-COTS part.  Deltas between two variants: mass_delta_v351.py A.json B.json.
Evidence class of every mass: CAD (volume x engmat rho) or the part's COTS mass tag (DATASHEET / ESTIMATE / ASSUMED).
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "src"))   # hub layout: 03-cad/calcs next to 03-cad/src
import config, build          # noqa: E402


def main():
    out = Path(sys.argv[1])
    ov = dict(config.V34_ON)
    extra = {}
    for a in sys.argv[2:]:
        k, v = a.split("=", 1)
        try:
            v = json.loads(v)
        except Exception:
            pass
        ov[k] = v
        extra[k] = v
    t0 = time.time()
    P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=True, overrides=ov)
    res = {"id": "mass_variant", "version": "v1", "date": "2026-10-13", "owner": "mechanical", "overrides_extra": extra,
           "z_head_mid_mm": P.get("z_head_mid", {}).get("v"), "states": {}, "parts": {}}
    import numpy as np
    for state in ("wet", "mid", "burnout", "nograin"):
        rows, m_g0 = build.mass_ledger(reg, P, state=state, S=S)
        groups = {}
        for r in rows:
            groups[r["group"]] = groups.get(r["group"], 0.0) + r["m"]
        res["states"][state] = {"groups_kg": {g: round(m, 5) for g, m in sorted(groups.items())}, "total_kg": round(sum(groups.values()), 5)}
        for name, grps in (("engine", ("engine",)), ("fixed", ("fixed",)), ("ring", ("ring",)), ("horn", ("horn",)), ("pushrod", ("pushrod",)),
                           ("all", ("engine", "fixed", "ring", "horn", "pushrod"))):     # same structure as make_all.stage_mass
            gp = build.group_props(rows, grps)
            res["states"][state][name] = {"m_kg": round(gp["m"], 5), "cg_mm": [round(x, 3) for x in gp["cg_mm"]], "n": gp["n"],
                                          "I_cg_kgm2": np.round(gp["I_cg"], 7).tolist(), "I_pivot_kgm2": np.round(gp["I_about"], 7).tolist()}
        if state == "wet":
            for r in rows:
                d = res["parts"].setdefault(r["pn"], {"m_by_group_kg": {}, "tag": r["tag"]})
                d["m_by_group_kg"][r["group"]] = round(d["m_by_group_kg"].get(r["group"], 0.0) + r["m"], 6)
    for p in reg:
        d = res["parts"].setdefault(p.pn, {"m_by_group_kg": {}, "tag": ""})
        d.update({"name": p.name, "material": p.material, "qty": p.qty, "cots": p.cots})
        if not p.cots and p.mass_each_kg is None:
            try:
                d["valid"] = bool(p.shape.isValid())
                d["volume_mm3"] = round(float(p.shape.Volume()), 3)
            except Exception as e:     # noqa: BLE001
                d["valid"] = f"ERR {e}"
    res["t_s"] = round(time.time() - t0, 1)
    out.write_text(json.dumps(res, indent=1))
    print(f"{out.name}: {res['t_s']} s; z_head_mid {res['z_head_mid_mm']}; wet {res['states']['wet']['groups_kg']} total {res['states']['wet']['total_kg']}; "
          f"burnout total {res['states']['burnout']['total_kg']}; engine wet m {res['states']['wet']['engine']['m_kg']} cg {res['states']['wet']['engine']['cg_mm']}")
    bad = [pn for pn, d in res["parts"].items() if d.get("valid") not in (None, True)]
    print("invalid solids:", bad)


if __name__ == "__main__":
    main()

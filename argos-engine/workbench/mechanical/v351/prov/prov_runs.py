"""Provenance of every S-AX run directory behind a hub table (lead relay 17:1xZ): mesh file + sha, CAD/geometry, material map,
thermal runs per state with dz and the part-aware mapping statistics recorded by sax.py in each state's run.json."""
import json, hashlib, sys
from pathlib import Path
import numpy as np
RS = Path("/home/claude/work/mechanical/runs/structural")
RT = Path("/home/claude/work/mechanical/runs/thermal")
OUT = Path("/home/claude/work/mechanical/v351/prov")
def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]
res = {}
for d in ["L1", "L1_TC09IN718", "L1_TC09IN718_thJ1revB_TC09IN", "L1_bonded", "L1_NZ03ZIRCONIA_thJ2revB", "L2", "L0.5", "L1_thv351_TB1GC_cad351"]:
    rd = RS / d
    z = np.load(rd / "mesh.npz", allow_pickle=True)
    meta = json.loads(str(z["meta"]))
    pn, mat = z["pn"], z["mat"]
    matmap = {p: sorted(set(mat[pn == p].tolist())) for p in sorted(set(pn.tolist()))}
    e = {"mesh_file": str(rd / "mesh.npz"), "mesh_sha16": sha16(rd / "mesh.npz"), "mesh_mtime": __import__("time").strftime("%H:%M:%SZ", __import__("time").gmtime((rd / "mesh.npz").stat().st_mtime)),
         "nodes": int(len(z["X"])), "elements": int(len(z["E"])), "conforming_mesh_from": meta.get("conforming_mesh_from"),
         "ties": meta.get("ties"), "cad": meta.get("cad", "(not recorded: pre-v3.5.1 sax.py, geometry cache geom_v341revB)"),
         "material_overrides_screening": meta.get("material_overrides_screening"), "material_map_in_mesh": matmap, "overlaps": meta.get("overlaps"),
         "states": {}}
    # node coordinate signature: is the conforming mesh identical to L1's (same X of the conforming part)?
    e["X_sha16"] = hashlib.sha256(np.ascontiguousarray(z["X"]).tobytes()).hexdigest()[:16]
    e["E_sha16"] = hashlib.sha256(np.ascontiguousarray(z["E"]).tobytes()).hexdigest()[:16]
    for sd in sorted(p for p in rd.iterdir() if p.is_dir() and (p / "run.json").exists()):
        r = json.loads((sd / "run.json").read_text())
        pv = r.get("prov", {})
        inp = sd / "sax.inp"
        st = {"thermal_run": pv.get("thermal_run", pv.get("source")), "t_frame_s": pv.get("t_frame_s"), "dz_mm": pv.get("dz_frame_mm"),
              "outside_nodes": pv.get("nodes_outside_own_part_thermal_mesh"), "max_nearest_mm": pv.get("max_nearest_distance_mm"),
              "per_part": {k: (v["outside_part_thermal_mesh"], v["max_nearest_distance_mm"]) for k, v in pv.get("per_part", {}).items()},
              "deck_sha16": sha16(inp) if inp.exists() else None, "ties": r.get("deck", {}).get("ties"),
              "mesh_conf_from": r.get("mesh", {}).get("conforming_mesh_from"), "matov": r.get("mesh", {}).get("material_overrides_screening")}
        e["states"][sd.name] = st
    res[d] = e
# thermal runs used: config + material overrides, envelope mesh sha
th = {}
for d, e in res.items():
    for s, st in e["states"].items():
        t = st["thermal_run"]
        if t and (RT / t).exists() and t not in th:
            m = json.loads(next((RT / t).glob("*_meta.json")).read_text())
            th[t] = {"config_overrides": m.get("config_overrides"), "material_overrides": m.get("material_overrides"), "aft_material": m.get("aft_material"),
                     "level": m.get("level"), "envelope_nodes_sha16": sha16(RT / t / "envelope_nodes.npz"), "head_top_monitor_z": m["case"]["monitors"]["head_top_r12"][1],
                     "inp_sha16": sha16(next((RT / t).glob("*.inp"))), "overlaps": m.get("overlaps")}
json.dump({"runs": res, "thermal": th}, open(OUT / "prov_runs_v1.json", "w"), indent=1)
for d, e in res.items():
    print(f"== {d}: mesh {e['mesh_sha16']} ({e['mesh_mtime']}) X {e['X_sha16']} E {e['E_sha16']} n {e['nodes']}/{e['elements']} from {e['conforming_mesh_from']} ties {e['ties']} cad {e['cad'][:20]} matov {e['material_overrides_screening']}")
    print("   matmap", {k.replace('ENG-', ''): v for k, v in e["material_map_in_mesh"].items()})
    runs = {}
    for s, st in e["states"].items():
        runs.setdefault((st["thermal_run"], st["dz_mm"]), []).append(s)
    for (t, dz), ss in runs.items():
        st0 = e["states"][ss[0]]
        print(f"   {t} dz {dz}: {len(ss)} states {ss[:3]}..; outside {st0['outside_nodes']} max {st0['max_nearest_mm']}; per part " +
              " ".join(f"{k.replace('ENG-', '')}:{v[0]}/{v[1]}" for k, v in st0["per_part"].items()))
print()
for t, v in th.items():
    print(t, json.dumps(v["config_overrides"]), v["material_overrides"], v["aft_material"], "ht", round(v["head_top_monitor_z"], 4), "env", v["envelope_nodes_sha16"])

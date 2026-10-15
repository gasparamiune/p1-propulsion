import sys, json, numpy as np
sys.path.insert(0, "/home/claude/work/fea3d/scripts")
lvl = sys.argv[1]
for name in sys.argv[2:]:
    z = np.load(f"/home/claude/work/fea3d/mesh/L{lvl}/{name}.npz")
    ent = json.loads(str(z["ent"]))
    print(f"== {name}")
    rows = []
    for k, v in ent.items():
        if v["type"] == "Cylinder" and "R" in v:
            ax = np.round(v["axis"], 3); ap = np.round(v["axis_pt"], 2)
            rows.append((round(v["R"], 3), k, ax.tolist(), ap.tolist(), [round(x, 2) for x in v["s_range"]], round(v["area"], 1), round(v.get("fit_err", 0), 3)))
    rows.sort()
    for r in rows:
        print("  R %-7s ent %-4s ax %-22s pt %-26s s %-18s A %-8s err %s" % r)

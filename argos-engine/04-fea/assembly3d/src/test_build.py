import sys, time, json
sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import numpy as np
import asm_build as AB
lvl = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
t0 = time.time()
M = AB.Asm(level=lvl)
print("bodies loaded", round(time.time() - t0, 1), "s; nodes", M.n_mesh, "elems", M.e_mesh, flush=True)
AB.define(M)
print("define", round(time.time() - t0, 1), "s", flush=True)
for t in M.ties:
    print("TIE", json.dumps(t))
for k, v in M.rbe.items():
    print("RBE3", k, v)
for lab, nodes, ref, rot in M.rigid:
    print("RIGID", lab, len(nodes))
for it in M.items:
    a = it["attach"]
    if a[0] == "faces":
        n = sum(int(np.asarray(s).sum()) for _, s in a[1])
        print("ITEM", it["label"], round(it["m_kg"] * 1e3, 2), "g faces", n, [(b, int(np.asarray(s).sum())) for b, s in a[1]])
print("AF", {k: len(v) for k, v in M.af_sets.items()})
print("notes", M.notes, "skipped", M.C.skipped)
print(json.dumps(AB.mass_check(M)["group_model_kg"]), json.dumps(AB.mass_check(M)["group_massprops_wet_kg"]))

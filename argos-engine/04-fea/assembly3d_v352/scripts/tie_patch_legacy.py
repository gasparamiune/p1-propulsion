"""Rigid-rotation / uniform-strain patch test of the tie equations (no solve): residual of each *EQUATION for an imposed field."""
import os, sys, json, numpy as np
sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import post_f1 as PF
run = sys.argv[1]
M, meta = PF.load_model(run)
nn = M.next_n
X = np.zeros((nn + 1, 3))
for nm, b in M.bodies.items():
    X[b.noff:b.noff + len(b.X0)] = M.Xp[nm]
for nid, (x0, g) in M.extra.items():
    X[nid] = M.posed(np.asarray(x0)[None], g)[0]
fields = {"rotX": lambda x: np.cross(np.array([1.0, 0, 0]), x), "rotY": lambda x: np.cross(np.array([0, 1.0, 0]), x),
          "rotZ": lambda x: np.cross(np.array([0, 0, 1.0]), x), "strain_iso": lambda x: x.copy()}
U = {k: f(X) for k, f in fields.items()}
tie_labels = set(t["label"] for t in M.ties)
res = {}
for lab, terms in M.C.eqs:
    if lab not in tie_labels:
        continue
    for k, u in U.items():
        r = sum(c * u[n, d - 1] for n, d, c in terms)
        a = res.setdefault(lab, {}).setdefault(k, [])
        a.append(abs(r))
out = {}
for lab, d in res.items():
    out[lab] = {k: {"max": float(np.max(v)), "rms": float(np.sqrt(np.mean(np.square(v)))), "n": len(v)} for k, v in d.items()}
    print(f"{lab:22s} " + "  ".join(f"{k} max {v['max']:.4f} rms {v['rms']:.4f}" for k, v in out[lab].items()) + f"  (mm per rad / per unit strain; n {out[lab]['rotX']['n']})")
json.dump(out, open(sys.argv[2], "w"), indent=1)

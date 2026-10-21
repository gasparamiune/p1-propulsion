"""Patch test of tie equations on a freshly built model (no deck, no solve).  usage: tie_patch2.py tiex(0|1) out.json"""
import os, sys, json, time, numpy as np
sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import asm_build as AB, asm3d as A3, run_f1 as RF
t0 = time.time()
tiex = sys.argv[1] == "1"
pl = {p[0]: p for p in AB.pose_list()}
_, a_, b_, stp = pl["stop045"]
variant = {"conn": "v12", "pose": (a_, b_), "posename": "stop045", "stop": stp, "tiex": tiex,
           "levels": {bn: RF.COARSE_FALLBACK.get((A3.CAD, bn, 2.0), 2.0) for bn in RF.COARSE_BODIES}}
M = AB.Asm(level=1.0, variant=variant)
AB.define(M)
print("built", round(time.time() - t0, 1), "s; eqs", len(M.C.eqs), flush=True)
nn = M.next_n
X = np.zeros((nn + 1, 3))
for nm, b in M.bodies.items():
    X[b.noff:b.noff + len(b.X0)] = M.Xp[nm]
for nid, (x0, g) in M.extra.items():
    X[nid] = M.posed(np.asarray(x0)[None], g)[0]
rnd = np.random.default_rng(1)
A_ = rnd.normal(size=(3, 3))
fields = {"rotX": lambda x: np.cross(np.array([1.0, 0, 0]), x), "rotY": lambda x: np.cross(np.array([0, 1.0, 0]), x),
          "rotZ": lambda x: np.cross(np.array([0, 0, 1.0]), x), "strain_iso": lambda x: x.copy(), "affine_rand": lambda x: x @ A_.T}
U = {k: f(X) for k, f in fields.items()}
tie_labels = set(t["label"] for t in M.ties)
res = {}
for lab, terms in M.C.eqs:
    if lab not in tie_labels:
        continue
    nd = np.array([n for n, d, c in terms]); dd = np.array([d - 1 for n, d, c in terms]); cc = np.array([c for n, d, c in terms])
    for k, u in U.items():
        res.setdefault(lab, {}).setdefault(k, []).append(abs(float(cc @ u[nd, dd])))
out = {"tiex": tiex, "ties": M.ties, "patch": {}}
for lab, d in res.items():
    out["patch"][lab] = {k: {"max": float(np.max(v)), "rms": float(np.sqrt(np.mean(np.square(v)))), "n": len(v)} for k, v in d.items()}
    print(f"{lab:22s} " + "  ".join(f"{k} {v['max']:.2e}/{v['rms']:.2e}" for k, v in out["patch"][lab].items()))
print("tie rows:", [(t["label"], t["n_eq"], t.get("n_tiex_fallback")) for t in M.ties])
json.dump(out, open(sys.argv[2], "w"), indent=1, default=float)

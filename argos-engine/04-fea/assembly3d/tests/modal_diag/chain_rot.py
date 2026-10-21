"""Diagnostic: best-fit rigid rotation of each body (and rigid refs) in a mode vs a static unit step, normalised to the engine rotation."""
import sys, json
import numpy as np
sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import post_f1 as PF
import post_modal as PMd

def body_rot(M, U, X, nm):
    b = M.bodies[nm]; ids = b.noff + np.arange(len(b.X0)); ids = ids[::max(1, len(ids)//3000)]
    A = PMd.rigid_fit_op(X[ids], np.full(len(ids), 1.0/len(ids)))
    return A @ U[ids].ravel()

def table(run, field, mode=None):
    M, meta = PF.load_model(run)
    Z = np.load(PF.RUNS / run / "B1_21.65" / "fields.npz")
    U = Z[field].astype(np.float64)
    if mode is not None:
        U = U[mode]
    N1 = M.next_n + 1
    U = U[:N1]
    X = np.zeros((N1, 3))
    for nm, b in M.bodies.items():
        X[b.noff:b.noff + len(b.X0)] = M.Xp[nm]
    out = {}
    for nm in M.bodies:
        out[nm] = body_rot(M, U, X, nm)
    return out

ax = int(sys.argv[1])   # 0 = x (alpha), 1 = y (beta)
mode = int(sys.argv[2]) - 1
step = sys.argv[3]
a = table(sys.argv[4] if len(sys.argv) > 4 else "modal_v351ca2_c71", "U_FREQ", mode)
b = table("pose_neutral_c71", f"U_{step}")
ref_a, ref_b = a["TC-01"][3 + ax], b["TC-01"][3 + ax]
print(f"axis {'xy'[ax]}: rotation / TC-01 rotation   (modal mode {mode+1}  |  static {step} pose_neutral_c71)")
for nm in a:
    print(f"  {nm:8s} {a[nm][3+ax]/ref_a:+8.3f}   {b[nm][3+ax]/ref_b:+8.3f}")

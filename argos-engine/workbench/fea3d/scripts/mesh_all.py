"""Mesh every FEA3D body at a level (cached).  usage: mesh_all.py LEVEL [body ...]"""
import sys, json, time
sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import numpy as np
import asm_def as A
import mesh3d

def mesh_body(name, level, force=False, balls=None, tag=""):
    """balls: local refinement [(x, y, z, r, h)] (neutral frame, mm); tag: cache sub-folder suffix for refined variants."""
    stem, si, grp, mat, trule, role = A.BODIES[name]
    hmax, hmin, curv = A.MESH[name]
    out = A.MESH_DIR / f"L{level:g}{tag if balls else ''}" / f"{name}.npz"
    return mesh3d.cached_mesh(A.brep_of(name), out, round(hmax * level, 4), round(hmin * level, 4), curv, si, force=force, balls=balls)

if __name__ == "__main__":
    level = float(sys.argv[1])
    names = sys.argv[2:] or list(A.BODIES)
    tot = 0
    for n in names:
        t0 = time.time()
        d = mesh_body(n, level)
        m = json.loads(str(d["meta"]))
        tot += m["n_nodes"]
        print(f"{n:7s} nodes {m['n_nodes']:7d} tets {m['n_tets']:7d} V {m['volume_mm3']:9.0f} qmin {m['q_min']:.3f} q<0.1 {m['n_q_below_0.1']:4d} inv {m['n_inverted']} unmatched {m['unmatched_surface_tris']} t {time.time()-t0:.1f}s", flush=True)
    print("TOTAL nodes", tot)

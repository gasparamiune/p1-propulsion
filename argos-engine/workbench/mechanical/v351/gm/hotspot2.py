"""Collar GM-01/02 LC3 hot spots in ENGINE-LOCAL coordinates (r, az, z) at every available S-3D pose (diagnostic v3.5.1).
usage: hotspot2.py RUNS_DIR pose [pose ...]   (RUNS_DIR = .../runs/structural/s3d or the v3.5.1 dir)"""
import sys, json, math
import numpy as np
sys.path.insert(0, "/home/claude/work/mechanical/engine/04-fea/structural")
sys.path.insert(0, "/home/claude/work/mechanical/engine/04-fea/src")
sys.path.insert(0, "/home/claude/work/mechanical/engine/03-cad/src")
import gimbal_strength as gs
import tvc_kinematics as tk


def R4(alpha, beta):
    T = np.eye(4)
    T[:3, :3] = tk.R_pose(alpha, beta)
    return T
runs = sys.argv[1]
mp = gs.mass_props()
for pose in sys.argv[2:]:
    z = np.load(f"{runs}/{pose}/unit.npz", allow_pickle=True)
    S_u = z["S"].astype(np.float64); XYZ = z["XYZ"]
    sets = {k: np.array(v) for k, v in json.loads(str(z["sets"])).items()}
    E = {k: np.array(v) for k, v in json.loads(str(z["E"])).items()}
    meta = json.loads(str(z["meta"])); sm = meta["stiff_meta"]; ab = (sm["alpha"], sm["beta"])
    Rinv = R4(ab[0], ab[1])[:3, :3].T
    elem_nodes = {}
    for body, arr in E.items():
        for row in arr:
            elem_nodes[int(row[0])] = row[1:]
    for part in ("P_GM01_0", "P_GM02_0"):
        nodes = np.unique(np.concatenate([elem_nodes[int(e)] for e in sets[part]]))
        Xl = XYZ[nodes] @ Rinv.T
        vm_env = np.zeros(len(nodes)); arg = [None] * len(nodes)
        for phi in np.arange(0, 360, 15.0):
            for rel in (0.0, 90.0, 180.0, 270.0):
                M, F = gs.case_loads("LC3", ab, mp, -88.8, phi, rel)
                c = gs.unit_vectors((M, F))
                vm = gs.vm6(np.tensordot(c, S_u[:, nodes, :], axes=(0, 0)))
                upd = vm > vm_env
                vm_env[upd] = vm[upd]
                for k in np.nonzero(upd)[0]:
                    arg[k] = (phi, rel)
        order = np.argsort(-vm_env)
        print(f"== {pose} {ab} {part}: envelope LC3 vm max {vm_env[order[0]]:.1f}")
        seen = []
        for k in order:
            x, y, zz = Xl[k]
            if any(np.linalg.norm(Xl[k] - Xl[q]) < 2.0 for q in seen):
                continue
            seen.append(k)
            d = np.linalg.norm(Xl - Xl[k], axis=1)
            r075 = vm_env[(d > 0.35) & (d < 1.15)].max(); r15 = vm_env[(d > 1.1) & (d < 1.9)].max()
            print(f"  {vm_env[k]:7.1f} (0.75: {r075:6.1f}, 1.5: {r15:6.1f}) local {Xl[k].round(2)} r {math.hypot(x, y):6.2f} az {math.degrees(math.atan2(y, x)):7.2f} phi/rel {arg[k]}")
            if len(seen) >= 8:
                break

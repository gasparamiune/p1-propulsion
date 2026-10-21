"""TC-02 at the instant of the S-AX TC-02 maximum (fea3d 2026-10-20 ~15:25Z; REV-MECH-2 RM2-13 correction 5, CHANGELOG 234 (7)).

The S-AX TC-02 thermal maximum (GVLO 187.7 C / GVHI 181.3 C, both at t = 21.5 s, forward-face OD corner by the TC-10 contact; Mechanical
gapvar_fields_v352_v2 envelope_parts) is not an S-AX L1 state: the L1 states nearest it are B1_19 and B1_21.65, both among the four mapped
states of the 3-D re-posts (repost_5b_v352.py).  This script reads the 21.501 s frame of Mechanical's thermal result (and, as a check, the
19.001 and 21.651 s frames, which are the S-AX L1 states B1_19 / B1_21.65) and interpolates T at the 3-D TC-02 governing nodes of the
re-post (seat all-node, seat regular, forward face), on the TC-02 part of the thermal mesh (6-node triangles split in 4 linear ones, as
fit_dT_sax.py; thermal z = S-AX z + 6.544 mm, index basis).  Then a constant-stress row per node: the vM of that node held at the larger
of its two bracketing states (B1_19, B1_21.65) and of LC1 / LC2, with the 6061-T6 allowables at T(21.5 s) [DERIVED; assumption: the
stress at 21.5 s does not exceed the larger bracketing state; the 3-D model has no 21.5 s state, so this is not a solved value].
Read-only on Mechanical's files (thermal frd.gz, envelope_nodes.npz, frames.npz).  Evidence: SIM (Mechanical S-AX thermal) + DERIVED.
usage: FEA3D_CAD=v352 python -I -B tc02_t215_v352.py -> results/v352/tc02_t215_v352.json"""
from __future__ import annotations
import sys, json, gzip, hashlib, time
from pathlib import Path
import numpy as np
import matplotlib.tri as mtri
from scipy.spatial import cKDTree

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
RES = Path("/home/claude/work/fea3d/results/v352")
TH = Path("/home/claude/work/mechanical/runs/thermal")
RUNS = {"GVLO": ("DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_GVLO", "lc1v352g"),
        "GVHI": ("DC-B1v3p99_tg711_hi_SS316L_L2.5_v352_NF2b_GVHI", "lc1v352h")}
T_WANT = [19.001, 21.501, 21.651]
DZ = 6.544
REGIONS = ["TC-02 seat (r <= 12, z 105-118)", "TC-02 forward face (z 103.513, 12 < r < 28.6)"]


def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()[:16]


def read_frames(frd, want):
    """nodal T (K) of the frames whose time is within 1e-3 s of a wanted time; fixed-width frd records."""
    out, cur, keep, vals = {}, None, False, None
    with gzip.open(frd, "rt") as f:
        for line in f:
            if line.startswith("  100CL"):
                t = float(line[12:25])
                hit = [w for w in want if abs(w - t) < 1e-3]
                keep, cur, vals = bool(hit), (hit[0] if hit else None), {}
                continue
            if keep:
                if line.startswith(" -1"):
                    vals[int(line[3:13])] = float(line[13:25])
                elif line.startswith(" -3"):
                    out[cur] = vals
                    keep = False
                    if len(out) == len(want):
                        break
    return out


def main():
    import post_f1 as PF
    res = {"id": "tc02_t215_v352", "date": time.strftime("%Y-%m-%d"), "owner": "fea3d", "doc": __doc__.split("usage:")[0].strip(),
           "evidence": "SIM (Mechanical S-AX thermal frames) + DERIVED (interpolation, constant-stress rows)", "bounds": {}}
    for b, (run, lc1) in RUNS.items():
        d = TH / run
        frd = d / f"{run}.frd.gz"
        env = np.load(d / "envelope_nodes.npz", allow_pickle=True)
        X, E, pn = env["X"], env["E"], env["pn"]
        fr = np.load(d / "frames.npz", allow_pickle=True)
        F = read_frames(frd, T_WANT)
        nn = len(X)
        T = {t: np.array([F[t][i + 1] for i in range(nn)]) for t in F}
        chk = {}
        for t in (19.001, 21.651):
            k = int(np.argmin(np.abs(fr["t_act"] - t)))
            chk[str(t)] = float(np.abs(fr["T"][k] - T[t]).max())
        Ep = E[pn == "ENG-TC-02"]
        used = np.unique(Ep)
        rm = -np.ones(nn, np.int64)
        rm[used] = np.arange(len(used))
        sub = rm[np.vstack([Ep[:, [0, 3, 5]], Ep[:, [3, 1, 4]], Ep[:, [5, 4, 2]], Ep[:, [3, 4, 5]]])]
        tri = mtri.Triangulation(X[used, 0], X[used, 1], sub)
        kd = cKDTree(X[used])
        ent = {"thermal_run": str(d), "frd_sha16": sha16(frd), "frames_npz_sha16": sha16(d / "frames.npz"),
               "frame_check_max_abs_K_vs_frames_npz": chk, "TC02_part_max_C": {}, "nodes": {}}
        for t in T_WANT:
            v = T[t][used]
            i = used[int(np.argmax(v))]
            ent["TC02_part_max_C"][str(t)] = {"T_C": round(float(T[t][i]) - 273.15, 2), "r_z_thermal_mm": [round(float(X[i, 0]), 3), round(float(X[i, 1]), 3)]}
        # governing nodes: from this bound's own re-post if it exists, else from GVLO's (temperatures only)
        rp = RES / f"repost_5b_{lc1}.json"
        src = rp if rp.exists() else RES / "repost_5b_lc1v352g.json"
        R = json.loads(src.read_text())
        ent["governing_nodes_from"] = src.name + ("" if rp.exists() else " (this bound's re-post pending: temperatures only)")
        for rg in REGIONS:
            for w in ("all", "regular"):
                rows = {(st, cs): R["states"][st]["cases"][cs]["regions"][rg][w] for st in ("B1_19", "B1_21.65") for cs in ("LC1", "LC2")}
                nodes = sorted({r["node"] for r in rows.values()})
                for nd in nodes:
                    rr = [(k, r) for k, r in rows.items() if r["node"] == nd]
                    r0 = rr[0][1]
                    rad, zz = float(np.hypot(*_xy(r0["r_theta_z"]))), float(r0["r_theta_z"][2])
                    interp, how = {}, None
                    for t in T_WANT:
                        val = mtri.LinearTriInterpolator(tri, T[t][used])(np.array([rad]), np.array([zz + DZ]))
                        val = float(np.asarray(val.filled(np.nan))[0]) if hasattr(val, "filled") else float(val[0])
                        how = "linear (inside the TC-02 thermal triangulation)"
                        if not np.isfinite(val):
                            # boundary node just outside the thermal TC-02 domain: nearest TC-02 thermal node (as asm_build.SaxThermal)
                            dd, ii = kd.query([rad, zz + DZ])
                            val = float(T[t][used][ii])
                            how = f"nearest TC-02 thermal node (outside the triangulation; distance {dd:.3f} mm)"
                        interp[str(t)] = round(val - 273.15, 2)
                    e = {"region": rg, "node_set": w, "r_theta_z": r0["r_theta_z"], "node_class": r0["node_class"],
                         "T_thermal_interp_C": interp, "interp": how,
                         "T_3D_mapped_C": {f"{k[0]} {k[1]}": r["T_C"] for k, r in rr},
                         "posted": {f"{k[0]} {k[1]}": {"MS_y": r["MS_y"], "MS_u": r["MS_u"], "vm_MPa": r["vm_MPa"]} for k, r in rr}}
                    if rp.exists() and interp["21.501"] is not None:
                        vmax = max(r["vm_MPa"] for _, r in rr)
                        kmax = [k for k, r in rr if r["vm_MPa"] == vmax][0]
                        Fty, Ftu = (float(x) for x in PF.allowables(R["states"]["B1_19"]["cases"]["LC1"]["regions"][rg]["material"],
                                                                     np.array(interp["21.501"] + 273.15)))
                        e["at_21.5s"] = {"T_C": interp["21.501"], "vm_held_MPa": vmax, "vm_from": f"{kmax[0]} {kmax[1]}",
                                         "Fty_MPa": round(Fty, 1), "Ftu_MPa": round(Ftu, 1),
                                         "MS_y": round(Fty / (1.5 * vmax) - 1, 3), "MS_u": round(Ftu / (2.0 * vmax) - 1, 3)}
                    ent["nodes"][f"n{nd} ({rg}; {w})"] = e
        res["bounds"][b] = ent
        print(b, "frame check", chk, "TC-02 max", ent["TC02_part_max_C"], flush=True)
        for k, e in ent["nodes"].items():
            print("  ", k, e["T_thermal_interp_C"], e["T_3D_mapped_C"], e.get("at_21.5s"), flush=True)
    out = RES / "tc02_t215_v352.json"
    out.write_text(json.dumps(res, indent=1))
    print("wrote", out, sha16(out))


def _xy(rtz):
    r, th = rtz[0], np.radians(rtz[1])
    return r * np.cos(th), r * np.sin(th)


if __name__ == "__main__":
    main()

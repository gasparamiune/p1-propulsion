"""Plug-to-bore dT at the TC-01 / TC-02 f7 / H8 fit on the S-AX thermal fields (fea3d 2026-10-20; brief item 5b, REV-MECH-2 RM2-13 (5)).

For each S-AX run (GVLO, GVHI, merged NF2b) and each state: T of TC-02 at the plug OD (r 28.6; nodes outside the S-AX TC-02 domain, i.e. in
Mechanical's GAP-J1 strip r 28.325-28.625, take the nearest S-AX TC-02 node, as the FEA3D mapping does) and T of TC-01 at the bore
(r 28.625), sampled every 0.05 mm along the fit segments of gapvar_fields_v352_v2 J1 (z_overlap 110.0575-113.0575, 117.9075-120.9075,
125.7575-143.0575 in the THERMAL frame; the S-AX mesh, res.npz and the 3-D model are in the S-AX frame, thermal z = S-AX z + 6.544 mm
(index basis), so the sampled S-AX z are 103.5135-106.5135, 111.3635-114.3635, 119.2135-136.5135: the three plug lands; fea3d 10:12Z fix,
the 09:2xZ v1 of this script sampled the thermal-frame z on the S-AX mesh, 6.544 mm too far aft); dT = T_plug - T_bore (positive = plug
hotter = closing).  Closure (ring formula, REV-MECH-2 RM2-13 (c)): dT >= gap /
(r alpha), r 28.6, alpha 23.6e-6 /K: 37.0 K (0.025 CAD), 59.3 K (0.040 drawing min), 115.6 K (0.078 drawing max); and against
Mechanical's hot gaps g_hot (GVLO 0.09, GVHI 0.031 mm).  Also the z-weighted mean dT (ring growth follows the section-mean temperature;
the local maximum is the conservative reading).  Evidence: SIM (Mechanical S-AX thermal) + DERIVED (this sampling; same interpolation
as asm_build.SaxThermal).
usage: fit_dT_sax.py -> results/v352/fit_dT_sax_v352.json"""
import json, hashlib
from pathlib import Path
import numpy as np
import matplotlib.tri as mtri
from scipy.spatial import cKDTree

IDX = Path("/home/claude/work/shared-fallback/engine/04-fea/v352/gapvar_fields_v352_v2.json")
OUT = Path("/home/claude/work/fea3d/results/v352/fit_dT_sax_v352.json")
R_PLUG, R_BORE, ALPHA = 28.6, 28.625, 23.6e-6
SEG_THERMAL = [(110.0575, 113.0575), (117.9075, 120.9075), (125.7575, 143.0575)]   # J1 z_overlap, thermal frame (index)
Z_THERMAL_MINUS_SAX = 6.544                                                          # index basis: thermal z = S-AX z + 6.544 mm
SEG = [(a - Z_THERMAL_MINUS_SAX, b - Z_THERMAL_MINUS_SAX) for a, b in SEG_THERMAL]   # S-AX frame (= 3-D frame)
GAPS = {"0.025 CAD": 0.025, "0.040 drawing min": 0.040, "0.078 drawing max": 0.078}


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


class Sax:
    def __init__(self, d):
        self.d = Path(d)
        m = np.load(self.d / "mesh.npz", allow_pickle=True)
        self.X, self.E, self.pn = m["X"], m["E"], m["pn"]
        self.tri = {}
        for p in ("ENG-TC-01", "ENG-TC-02"):
            Ep = self.E[self.pn == p]
            used = np.unique(Ep)
            rm = -np.ones(len(self.X), np.int64)
            rm[used] = np.arange(len(used))
            sub = rm[np.vstack([Ep[:, [0, 3, 5]], Ep[:, [3, 1, 4]], Ep[:, [5, 4, 2]], Ep[:, [3, 4, 5]]])]
            Xu = self.X[used]
            self.tri[p] = (used, mtri.Triangulation(Xu[:, 0], Xu[:, 1], sub), cKDTree(Xu))

    def at(self, p, T, r, z):
        used, tri, kd = self.tri[p]
        v = mtri.LinearTriInterpolator(tri, T[used])(r, z)
        v = np.asarray(v.filled(np.nan) if hasattr(v, "filled") else v, float)
        miss = ~np.isfinite(v)
        if miss.any():
            dd, ii = kd.query(np.column_stack([r[miss], z[miss]]))
            v[miss] = T[used][ii]
        return v, int(miss.sum())


def main():
    I = json.loads(IDX.read_text())
    z = np.concatenate([np.arange(a, b + 1e-9, 0.05) for a, b in SEG])
    out = {"id": "fit_dT_sax_v352", "date": "2026-10-20", "owner": "fea3d", "index": str(IDX), "index_sha16": sha16(IDX),
           "r_plug_mm": R_PLUG, "r_bore_mm": R_BORE, "alpha_per_K": ALPHA, "segments_z_thermal_frame_mm": SEG_THERMAL,
           "z_thermal_minus_sax_mm": Z_THERMAL_MINUS_SAX, "segments_z_sax_frame_mm": [[round(a, 4), round(b, 4)] for a, b in SEG],
           "version": "v2 (10:12Z: S-AX-frame segments; v1 sampled the thermal-frame z on the S-AX mesh)",
           "self_consistent_closure": "GVLO is the drawing-max end (cold radial 0.078: closure 115.6 K), GVHI the drawing-min end (cold 0.040: 59.3 K); NF2b merged = perfect contact (no gap)",
           "closure_dT_K": {k: round(g / (R_PLUG * ALPHA), 1) for k, g in GAPS.items()},
           "evidence": "SIM (Mechanical S-AX thermal fields) + DERIVED (sampling, ring closure formula)", "fields": {}}
    for key, f in I["fields"].items():
        d = f["sax_run"]["dir"]
        S = Sax(d)
        gv = f.get("gap_variant") or {}
        g_hot = ((gv.get("joints") or {}).get("J1") or {}).get("g_hot_mm")
        g_cold = {"GVLO": 0.078, "GVHI": 0.040}.get(gv.get("name"))
        fo = {"sax_dir": d, "mesh_sha16": sha16(Path(d) / "mesh.npz"), "J1_g_hot_mm": g_hot, "J1_cold_gap_of_variant_mm": g_cold,
              "closure_dT_at_variant_cold_gap_K": (round(g_cold / (R_PLUG * ALPHA), 1) if g_cold else None),
              "closure_dT_at_g_hot_K": (round(g_hot / (R_PLUG * ALPHA), 1) if g_hot else None), "states": {}}
        for st in f["sax_run"]["states"]:
            p = Path(d) / st / "res.npz"
            if not p.exists():
                continue
            T = np.load(p)["T"]
            tp, mp = S.at("ENG-TC-02", T, np.full(len(z), R_PLUG), z)
            tb, mb = S.at("ENG-TC-01", T, np.full(len(z), R_BORE), z)
            dT = tp - tb
            k = int(np.argmax(dT))
            rec = {"dT_max_K": round(float(dT.max()), 2), "z_at_max_mm": round(float(z[k]), 3), "T_plug_C_at_max": round(float(tp[k] - 273.15), 1),
                   "T_bore_C_at_max": round(float(tb[k] - 273.15), 1), "dT_min_K": round(float(dT.min()), 2), "dT_mean_K": round(float(dT.mean()), 2),
                   "T_plug_mean_C": round(float(tp.mean() - 273.15), 1), "T_bore_mean_C": round(float(tb.mean() - 273.15), 1),
                   "n_plug_nearest": mp, "n_bore_nearest": mb, "res_sha16": sha16(p)}
            rec["closes_by_max"] = {kk: bool(dT.max() >= g / (R_PLUG * ALPHA)) for kk, g in GAPS.items()}
            if g_cold:
                rec["closes_variant_cold_gap_by_max"] = bool(dT.max() >= g_cold / (R_PLUG * ALPHA))
                rec["closure_left_mm_at_max"] = round(g_cold - R_PLUG * ALPHA * float(dT.max()), 4)
            segm = {}
            for (a, b) in SEG:
                kk = (z >= a - 1e-9) & (z <= b + 1e-9)
                j = int(np.argmax(np.where(kk, dT, -1e9)))
                segm[f"{a:.4f}-{b:.4f}"] = {"dT_max_K": round(float(dT[j]), 2), "z_mm": round(float(z[j]), 3), "dT_mean_K": round(float(dT[kk].mean()), 2)}
            rec["per_segment"] = segm
            if g_hot:
                rec["closes_g_hot_by_max"] = bool(dT.max() >= g_hot / (R_PLUG * ALPHA))
                rec["closes_g_hot_by_mean"] = bool(dT.mean() >= g_hot / (R_PLUG * ALPHA))
            fo["states"][st] = rec
        out["fields"][key] = fo
    OUT.write_text(json.dumps(out, indent=1))
    for key, fo in out["fields"].items():
        print(key, "g_hot", fo["J1_g_hot_mm"], "closure at g_hot", fo["closure_dT_at_g_hot_K"])
        for st, r in sorted(fo["states"].items(), key=lambda kv: float(kv[0].split("_")[1]) if kv[0].startswith("B1_") else 1e9):
            print(f"   {st:9s} dT max {r['dT_max_K']:7.2f} K at z {r['z_at_max_mm']:7.2f} (plug {r['T_plug_C_at_max']:6.1f} / bore {r['T_bore_C_at_max']:6.1f} C) "
                  f"mean {r['dT_mean_K']:7.2f} min {r['dT_min_K']:7.2f} | closes {r['closes_by_max']} own-cold-gap {r.get('closes_variant_cold_gap_by_max')} "
                  f"left {r.get('closure_left_mm_at_max')} | nearest plug {r['n_plug_nearest']} bore {r['n_bore_nearest']}")
    print("wrote", OUT, sha16(OUT))


if __name__ == "__main__":
    main()

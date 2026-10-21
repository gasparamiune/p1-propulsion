"""Hot-bound all-node rows on lc3_bound's part-max branch: the rigorous PART-WIDE bound, unrounded (fea3d 2026-10-20, written after the
21:50:58Z date -u reading; lead 21:47:29Z: "Wherever the rigorous part-wide bound is lower than the stored all-node value at 3 decimals,
it replaces that value in the cell, with the stored value beside it and the method named per cell").  Python only, no solve.

Same inputs and the same formula as hb_singular_check_v352.py (its JSON 7d4ab97c0d7d3e75 stays as written; it rounds the part-wide value
to 4 decimals, which can flip a 3-decimal comparison, e.g. a 0 MPa delta read 0.7385 against a stored 0.73846).  Per hot-bound file
(LC3 / F2 x GVLO / GVHI), state and part on the part-max branch (engine parts outside lc3_bound's SAME_MESH_ENGINE list: lc3_bound adds
the part's REGULAR-node maximum of the increment envelope to every node, which does not bound a singular node's own increment):
  delta      max over ALL the part's nodes of the increment envelope - the regular maximum (vM; brittle: max(s1 excess, -s3 excess) beyond
             the regular extremes),
  a_min      the lowest allowable over the part's nodes at that state (base T.npz; brittle: the lower of the two brittle allowables),
  pw_MS      1 / (1 / (1 + MS_min) + SF delta / a_min) - 1 with MS_min = the stored all-node minimum of that state (SF 1.5 / 2.0; brittle
             2.0): every node m of the part has MS(m) >= pw_MS (MS_stored(m) >= MS_min, stress(m) <= stored bound(m) + delta).
Per case and part: the minimum over bases and states, unrounded, with its row, and the stored minimum beside it.  The check column
reproduces hb_singular_check_v352's 4-decimal corrected_all_node_MS row by row.  Tags: DERIVED on SIM inputs.  Not physical approval.
usage: FEA3D_CAD=v352 hb_partwide_v352.py -> results/v352/hb_partwide_v352.json"""
from __future__ import annotations
import sys, json, hashlib
from pathlib import Path
import numpy as np

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import post_f1 as PF                       # noqa: E402
import hb_singular_check_v352 as HS        # noqa: E402  (constants and corr(); its main() is not run)

RES, RUNS = HS.RES, HS.RUNS


def main():
    env = {"LC3": [np.load(RES / f"lc3_env_{p}.npz") for p in HS.STOPS], "F2": [np.load(RES / f"s3d_env_{p}.npz") for p in HS.CONES]}
    E = {}
    for c, L in env.items():
        E[c] = {"vmD_all": np.max([e["vmD"] for e in L], axis=0), "vmD_reg": np.max([np.where(e["reg"], e["vmD"], -np.inf) for e in L], axis=0),
                "s1D_all": np.max([e["s1D"] for e in L], axis=0), "s3D_all": np.min([e["s3D"] for e in L], axis=0)}
    chk = json.loads((RES / "v352" / "hb_singular_check_v352.json").read_text())
    ref = {(r["case"], r["base"], r["state"], r["part"]): r for r in chk["rows"]}
    out = {"doc": __doc__.split("usage:")[0].strip(), "files_sha16": {"v352/hb_singular_check_v352.json": HS.sha16(RES / "v352" / "hb_singular_check_v352.json")},
           "rows": [], "per_part_case": {}}
    for (tag, case), (fn, base) in HS.HB.items():
        hb = json.loads((RES / fn).read_text())
        out["files_sha16"][fn] = HS.sha16(RES / fn)
        bodies = json.loads((RUNS / base / "model.json").read_text())["bodies"]
        for st, rows in hb["states"].items():
            Tz = np.load(RUNS / base / st / "T.npz")
            for r in rows:
                if r["set"] != "all" or "part-max" not in r["method"]:
                    continue
                nm = r["part"]
                b = bodies[nm]
                sl = slice(b["noff"], b["noff"] + b["n"])
                pm = hb["part_max_increment"][nm]
                Tn = np.asarray(Tz[nm], dtype=float)
                a1, a2 = PF.allowables(b["mat"], Tn + 0.0 if Tn.max() > 200 else Tn + 273.15)
                rec = {"case": case, "base": tag, "state": st, "part": nm, "stored_node": r["node"], "stored_class": f"{r['node_class']} {r['node_class_detail']}",
                       "stored_MS": [r["MS_bound"], r["MS_ult_bound"]]}
                if r["MS_ult_bound"] is None:      # brittle (Weyl s1 / s3 part maxima), SF 2.0 on the lower brittle allowable
                    d1 = max(float(np.max(E[case]["s1D_all"][sl])), 0.0) - max(pm["s1D"], 0.0)
                    d3 = min(float(np.min(E[case]["s3D_all"][sl])), 0.0) - min(pm["s3D"], 0.0)
                    amin = float(min(np.min(a) for a in (a1, a2) if a is not None))
                    dp = max(d1, -d3, 0.0)
                    rec.update({"brittle": True, "delta_MPa": dp, "a_min_MPa": amin, "pw_MS": [HS.corr(r["MS_bound"], HS.SFU, dp, amin), None]})
                else:
                    delta = float(np.max(E[case]["vmD_all"][sl])) - pm["vmD"]
                    rec.update({"brittle": False, "delta_MPa": delta, "a_min_MPa": [float(np.min(a1)), float(np.min(a2))],
                                "pw_MS": [HS.corr(r["MS_bound"], HS.SFY, delta, float(np.min(a1))), HS.corr(r["MS_ult_bound"], HS.SFU, delta, float(np.min(a2)))]})
                h = ref.get((case, tag, st, nm)) or {}
                rec["reproduces_hb_singular_check_4dp"] = all((p is None and q is None) or (p is not None and q is not None and abs(round(p, 4) - q) < 1e-9)
                                                              for p, q in zip(rec["pw_MS"], h.get("corrected_all_node_MS") or [None, None]))
                out["rows"].append(rec)
    for rec in out["rows"]:
        k = f"{rec['case']}|{rec['part']}"
        o = out["per_part_case"].setdefault(k, {"stored_min": [None, None], "stored_at": [None, None], "pw_min": [None, None], "pw_at": [None, None],
                                                "delta_max_MPa": 0.0, "rows": 0})
        o["rows"] += 1
        o["delta_max_MPa"] = max(o["delta_max_MPa"], rec["delta_MPa"])
        at = f"{rec['base']} {rec['state']}"
        for j in (0, 1):
            s, p = rec["stored_MS"][j], rec["pw_MS"][j]
            if s is not None and (o["stored_min"][j] is None or s < o["stored_min"][j]):
                o["stored_min"][j], o["stored_at"][j] = s, f"{at} n{rec['stored_node']} {rec['stored_class']}"
            if p is not None and (o["pw_min"][j] is None or p < o["pw_min"][j]):
                o["pw_min"][j], o["pw_at"][j] = p, f"{at} (stored minimum n{rec['stored_node']} {rec['stored_class']}; delta {rec['delta_MPa']:.4f} MPa)"
    for o in out["per_part_case"].values():
        o["pw_lower_at_3dp"] = [bool(s is not None and p is not None and round(p, 3) < round(s, 3)) for s, p in zip(o["stored_min"], o["pw_min"])]
    out["all_rows_reproduce_hb_singular_check_4dp"] = all(r["reproduces_hb_singular_check_4dp"] for r in out["rows"])
    (RES / "v352" / "hb_partwide_v352.json").write_text(json.dumps(out, indent=1, default=float))
    for k, o in sorted(out["per_part_case"].items()):
        print(f"{k:12s} stored {[None if v is None else round(v, 5) for v in o['stored_min']]} pw {[None if v is None else round(v, 5) for v in o['pw_min']]} "
              f"lower@3dp {o['pw_lower_at_3dp']} dmax {o['delta_max_MPa']:.4f}")
    print("reproduces hb_singular_check (4 dp):", out["all_rows_reproduce_hb_singular_check_4dp"], len(out["rows"]))


if __name__ == "__main__":
    main()

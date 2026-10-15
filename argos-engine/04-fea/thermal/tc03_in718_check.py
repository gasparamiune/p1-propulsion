"""TC-03 seat insert in Inconel 718: M14x1 thread fit and flange seal at temperature (04-fea/thermal, v1, 2026-10-13, Mechanical).

Lead relay 2026-10-13 item 3: TC-03 is now Inconel 718; re-run the thermal (k ~11 W/mK) and check the M14x1 fit and the
flange seal at temperature.  Reads the 2-D axisymmetric runs (run_thermal.py, --mat ENG-TC-03=IN718) and, for comparison,
the same duty cycle with the 17-4PH H1150 insert.  Thermal-mesh frame: injector face zf 112.02, flange zf..zf+2 (r <= 10),
M14x1 thread zf+2..124.02 (insert r <= 7), head counterbore floor z zf+2 (AS568-016 FKM groove r 7.8-9.8, 1.3 deep).

Per frd time:  T_ins = mean of TC-03 nodes r 6.0-7.0 in the thread length; T_head = mean of TC-02 nodes r 7.0-7.6 same z;
  diametral fit change at the pitch diameter d2 13.35 mm:  dc = d2 (alpha_ins(T_ins) dT_ins - alpha_head(T_head) dT_head)
  (> 0 = the insert grows more = clearance closes; secant CTE from 20 C, engmat v1.1);  M14x1-6g/6H minimum clearance 26 um
  (es 6g = -(15 + 11 P) um, ISO 965-1), maximum 288 um (Td2 6g 112 + TD2 6H 150 um at d 14, P 1);
  axial: the insert (tension, flange -> thread) and the head (compression, counterbore floor -> thread) share the clamp length
  L 6 mm (mid-thread engagement, ASSUMED); d_ax = L (alpha_head dT_head - alpha_ins dT_ins) > 0 adds preload (head grows more).
  Seal: max of TC-02 nodes r 7.8-9.8, z zf+2 .. zf+3.3 (groove) vs FKM limits 200 C continuous / ~250 C short (ASSUMED class
  values, compound data sheet to confirm), PTFE thread tape 260 C.
usage: tc03_in718_check.py <label> [<label> ...]  -> tc03_in718_check_v1.json
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[0] / "src"))
import ax_thermal as at
import engmat

RUNS = Path("/home/claude/work/mechanical/runs/thermal")
OUT = HERE / "tc03_in718_check_v1.json"
ZF = 112.02
D2, C_MIN_UM, C_MAX_UM, L_CLAMP = 13.35, 26.0, 288.0, 6.0
ZONES = {"insert_thread": ("ENG-TC-03", 6.0, 7.0, ZF + 2.0, 124.02),
         "head_thread": ("ENG-TC-02", 7.0, 7.6, ZF + 2.0, 124.02),
         "seal_groove": ("ENG-TC-02", 7.8, 9.8, ZF + 1.95, ZF + 3.35),
         "insert_flange": ("ENG-TC-03", 7.0, 10.0, ZF, ZF + 2.0)}


def alpha(mat, T_K):
    return engmat.prop(mat, "alpha", T_K - 273.15)


def main(labels):
    res = json.loads(OUT.read_text()) if OUT.exists() else {"runs": {}}
    res.update({"script": "04-fea/thermal/tc03_in718_check.py v1", "date": "2026-10-13", "method": __doc__.split("\n\n")[1]})
    for lab in labels:
        run = RUNS / lab
        meta = json.loads((run / f"{lab}_meta.json").read_text())
        mat_ins = (meta.get("material_overrides") or {}).get("ENG-TC-03", "SS17-4PH-H1150")
        d = np.load(run / "envelope_nodes.npz", allow_pickle=True)
        X, E, pn = d["X"], d["E"], d["pn"]
        ids = {}
        for k, (p, r0, r1, z0, z1) in ZONES.items():
            nn = np.unique(E[pn == p])
            ids[k] = [int(q) for q in nn if r0 <= X[q][0] <= r1 and z0 <= X[q][1] <= z1]
        t_last = meta["t_last_shutdown_s"]
        rows = []
        for t, vals in at.read_frd_nt(run / f"{lab}.frd"):
            z = {k: [vals[q + 1] for q in v] for k, v in ids.items()}
            Ti, Th = float(np.mean(z["insert_thread"])), float(np.mean(z["head_thread"]))
            dTi, dTh = Ti - 293.15, Th - 293.15
            dc = D2 * (alpha(mat_ins, Ti) * dTi - alpha("AL6061-T6", Th) * dTh) * 1e3       # um
            dax = L_CLAMP * (alpha("AL6061-T6", Th) * dTh - alpha(mat_ins, Ti) * dTi) * 1e3  # um
            rows.append((t, Ti, Th, dc, dax, float(np.max(z["seal_groove"])), float(np.max(z["insert_flange"]))))
        A = np.array(rows)
        fl = A[:, 0] <= t_last + 1e-6

        out = {"insert_material": mat_ins, "dc": meta.get("case", {}).get("dc") if isinstance(meta.get("case"), dict) else None,
               "t_last_shutdown_s": t_last, "n_nodes": {k: len(v) for k, v in ids.items()}}
        for name, mask in (("flight", fl), ("all_incl_soak", np.ones(len(A), bool))):
            sub = A[mask]
            kdc = int(np.argmax(sub[:, 3])); kdcm = int(np.argmin(sub[:, 3])); kax = int(np.argmax(sub[:, 4]))
            ks = int(np.argmax(sub[:, 5]))
            out[name] = {"T_insert_thread_max_C": round(float(sub[:, 1].max()) - 273.15, 1),
                         "T_head_thread_max_C": round(float(sub[:, 2].max()) - 273.15, 1),
                         "fit_change_max_um": round(float(sub[kdc, 3]), 1), "at_t_s": round(float(sub[kdc, 0]), 2),
                         "fit_change_min_um": round(float(sub[kdcm, 3]), 1), "at_t_min_s": round(float(sub[kdcm, 0]), 2),
                         "clearance_left_at_max_um": round(C_MIN_UM - float(sub[kdc, 3]), 1),
                         "axial_preload_gain_max_um": round(float(sub[kax, 4]), 2), "at_t_ax_s": round(float(sub[kax, 0]), 2),
                         "T_seal_groove_max_C": round(float(sub[ks, 5]) - 273.15, 1), "at_t_seal_s": round(float(sub[ks, 0]), 2),
                         "T_flange_max_C": round(float(sub[:, 6].max()) - 273.15, 1),
                         "seal_s_above_200C": round(float(np.sum(np.diff(sub[:, 0])[(sub[1:, 5] > 473.15) & (sub[:-1, 5] > 473.15)])), 2),
                         "seal_s_above_175C": round(float(np.sum(np.diff(sub[:, 0])[(sub[1:, 5] > 448.15) & (sub[:-1, 5] > 448.15)])), 2)}
        res["runs"][lab] = out
        print(lab, json.dumps(out))
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])

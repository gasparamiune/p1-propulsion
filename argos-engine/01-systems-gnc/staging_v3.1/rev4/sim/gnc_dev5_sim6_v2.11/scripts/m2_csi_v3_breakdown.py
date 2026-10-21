"""Breakdown of the m2_csi_v3 base corners (LPF only) by thrust level, actuator corner, K and damping; and a candidate
notch evaluated with the rigid-loop phase margin per corner. Env GNC_OUT, GNC_CSI_TAG; GNC_CSI_NOTCH='Q,depth,mis1,mis2,..'.
Output OUT/csi_v3_breakdown_<TAG>.json"""
import json
import os
import sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m2_csi_v3 as V  # noqa: E402

OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/csi_v3")
TAG = os.environ.get("GNC_CSI_TAG", "fea")


def group(rows, key):
    g = {}
    for r in rows:
        k = key(r)
        e = g.setdefault(k, dict(n=0, unstable=0, below6=0, gm_min=None))
        e["n"] += 1
        e["unstable"] += 0 if r["stable"] else 1
        e["below6"] += 0 if r["ok6"] else 1
        if r["stable"] and r["gm_up_dB"] is not None:
            e["gm_min"] = r["gm_up_dB"] if e["gm_min"] is None else min(e["gm_min"], r["gm_up_dB"])
    return g


def main():
    relay = json.load(open(V.RELAY))
    n = relay["n_linkage"]["v"]
    conds, meta, srcs = V.build_conditions(relay)
    Kc = relay["K_series_centre_Nm_per_rad"]["v"]; K7 = relay["K_series_alpha_p7deg_Nm_per_rad"]["v"]
    Kax = {ax: sorted(set(Kc[ax] + K7[ax])) for ax in ("alpha", "beta")}
    Jc = relay["J_int_servo_output_kgm2"]["v"]
    out = {}
    spec = os.environ.get("GNC_CSI_NOTCH")
    for ax in ("alpha", "beta"):
        for J in (0.0, Jc["central"]):
            for lab, rule in [("lpf", None)] + ([] if not spec else [
                    (f"notch_{spec}_mis{m}", (lambda c, m=float(m), q=float(spec.split(',')[0]), d=float(spec.split(',')[1]):
                                              (m * c["w_rock"] / (2 * np.pi), q, d))) for m in spec.split(",")[2:]]):
                s, rows = V.run_set(conds, Kax[ax], (0.02, 0.05), J, n, rule, keep=True)
                key = f"{ax}|J{J * 1e3:g}|{lab}"
                out[key] = dict(summary=s,
                                by_thrust=group(rows, lambda r: "|".join(r["corner"].split("|")[:2])),
                                by_act=group(rows, lambda r: r["corner"].split("|")[2]),
                                by_K=group(rows, lambda r: f"K{r['K']:.0f}"),
                                by_zeta=group(rows, lambda r: f"z{r['zeta_rock']:.2f}"),
                                pm_min_deg_stable=min((r["pm_min_deg"] for r in rows if r["stable"] and r["pm_min_deg"] is not None), default=None))
                print(key, json.dumps({k: out[key][k] for k in ("by_thrust", "by_zeta")}), flush=True)
    with open(os.path.join(OUT, f"csi_v3_breakdown_{TAG}.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)


if __name__ == "__main__":
    main()

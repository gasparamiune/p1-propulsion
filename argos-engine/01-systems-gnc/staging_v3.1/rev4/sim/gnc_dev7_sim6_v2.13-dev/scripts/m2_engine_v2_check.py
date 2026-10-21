"""Engine model change for gnc.json v3: combustion.json v2 throttle map (published 2026-10-12) against the relay model
flown in gnc.json v2 (combustion.json v1 map x relay factors k_ox(F), k_f(F), S230 grain).

Compares mdot_ox, mdot_f, total mass flow and Isp at the map thrust points and the thrust ceiling vs tank pressure.
Inputs: GNC_IFACE_V1 (interface set with combustion.json v1, default the local snapshot) and GNC_IFACE (interface set
with combustion.json v2 and its map CSV). Output: GNC_RES/engine_v2map_vs_relay.json and .csv.
Run: python scripts/m2_engine_v2_check.py
"""
import csv
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import engine_v2 as E  # noqa: E402

RES = os.environ.get("GNC_RES", "/home/claude/work/space/out/results_v2")
V1 = os.environ.get("GNC_IFACE_V1", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "iface_snapshot"))
V2 = os.environ.get("GNC_IFACE", "/home/claude/work/space/iface_v3")


def tables(iface, relay):
    c = json.load(open(os.path.join(iface, "combustion.json")))
    old = E.IFACE
    E.IFACE = iface
    try:
        t = E.combustion_tables(c)
    finally:
        E.IFACE = old
    if relay:
        corr = E.load_relay_correction(c)
        if corr is None:
            raise RuntimeError("relay correction does not apply to " + str(c.get("version")))
        t = E.apply_relay(t, corr)
    return c, t


def at(t, F, key, D=0.025):
    j = int(np.argmin(np.abs(t["Dg"] - D)))
    return float(np.interp(F, t["Fg"], t[key][:, j]))


def main():
    c1, t1 = tables(V1, relay=True)
    c2, t2 = tables(V2, relay=False)
    rows = []
    for F in (62.5, 75.0, 100.0, 125.0, 150.0, 200.0, 250.0, 300.0, 375.0, 450.0, 500.0):
        r = dict(F_N=F)
        for lab, t in (("relay", t1), ("v2map", t2)):
            mo, mf = at(t, F, "mox"), at(t, F, "mf")
            r[f"{lab}_mdot_ox"] = mo
            r[f"{lab}_mdot_f"] = mf
            r[f"{lab}_mdot"] = mo + mf
            r[f"{lab}_Isp"] = F / ((mo + mf) * 9.80665)
            r[f"{lab}_OF"] = mo / mf
        r["dmdot_rel"] = r["v2map_mdot"] / r["relay_mdot"] - 1.0
        r["dIsp_s"] = r["v2map_Isp"] - r["relay_Isp"]
        rows.append(r)
        print(f"F {F:6.1f} N: mdot relay {r['relay_mdot']:.4f} v2 {r['v2map_mdot']:.4f} ({100 * r['dmdot_rel']:+.1f} %), "
              f"Isp {r['relay_Isp']:.1f} -> {r['v2map_Isp']:.1f} s, O/F {r['relay_OF']:.2f} -> {r['v2map_OF']:.2f}")
    ceil = []
    for P in (3.0e6, 3.5e6, 4.0e6, 4.5e6, 5.0e6, 5.5e6):
        j1 = int(np.argmin(np.abs(t1["Dg"] - 0.025))); j2 = int(np.argmin(np.abs(t2["Dg"] - 0.025)))
        ceil.append(dict(P_tank_Pa=P, relay_ceiling_N=float(np.interp(P, t1["Pg"], t1["ceil"][:, j1])),
                         v2map_ceiling_N=float(np.interp(P, t2["Pg"], t2["ceil"][:, j2]))))
        print(f"P_tank {P / 1e5:.0f} bar: ceiling relay {ceil[-1]['relay_ceiling_N']:.0f} N, v2 map {ceil[-1]['v2map_ceiling_N']:.0f} N")
    out = dict(tool="m2_engine_v2_check v1", relay=dict(combustion_json=c1.get("version"), meta=t1["meta"].get("relay_correction", {}).get("version")),
               v2map=dict(combustion_json=c2.get("version"), map_meta={k: v for k, v in t2["meta"].items() if k not in ("F_pts", "Isp_pts", "OF_pts", "Pc_pts")}),
               points=rows, ceiling=ceil)
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "engine_v2map_vs_relay.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    with open(os.path.join(RES, "engine_v2map_vs_relay.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("written", os.path.join(RES, "engine_v2map_vs_relay.json"))


if __name__ == "__main__":
    main()

"""rg08_isp v1 (independent GNC review, 2026-10-13): coverage of the +25 % usable-liquid rule against a delivered-thrust
(C_F c*) shortfall, on the reviewer's independent 1-DOF model (rg03_vertical v1.1, k_thr).

Why: the 6-DOF sensitivity rg05 (thrust_scale x 0.90 on every run, paired with the published draws) gives A1 P 0.950
(-24/+3, exact McNemar p 4.9e-5, 21 runs exhaust the liquid) and B1 62 m P 0.986 (2 exhausted). The rule is evaluated by the
author on the nominal flight at the nominal map. This script finds the delivered-thrust factor at which the nominal flight
stops meeting the rule, with an IDEAL effectiveness estimate in the guidance (k_hat = k_thr), i.e. the propellant cost of the
shortfall alone (an upper bound of the factor the rule tolerates; the FSW estimator is not ideal).
Checks: k_thr = 1.0 reproduces rg03_vertical.json (v1) exactly.
Output: rg08_isp.json
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import rg03_vertical as V  # noqa: E402
A_DRY = 16.0746 - 2.0
B_DRY = 15.4246 - 2.0
CASES = {
    "A1_plan0.81_liq_med": lambda k: V.fly("A", 300.0, A_DRY, False, d_ign=0.3152, t_est=0.81, k_thr=k),
    "B1_62m": lambda k: V.fly("B", 62.0, B_DRY, True, k_thr=k),
    "B1_85m": lambda k: V.fly("B", 85.0, B_DRY, True, k_thr=k),
}
KEYS = ("n2o_burned", "fuel_burned", "liquid_left", "usable", "reserve", "thrust_on_s", "impulse_Ns", "td_vz", "h_apo", "closes")


def slim(r):
    return {k: r.get(k) for k in KEYS} | {"exhausted": bool(r.get("exhausted", False))}


def main():
    ref = json.load(open(os.path.join(HERE, "rg03_vertical.json")))["results"]
    out = dict(script="rg08_isp v1", model="rg03_vertical v1.1", check_k1={}, sweep={}, break_even={})
    for nm, f in CASES.items():
        t0 = time.time()
        r = f(1.0)
        same = all(r[k] == ref[nm][k] for k in ("n2o_burned", "fuel_burned", "liquid_left", "impulse_Ns", "thrust_on_s"))
        out["check_k1"][nm] = dict(identical_to_v1=bool(same), reserve=r["reserve"])
        print(nm, "k_thr 1.0 identical to v1:", same, f"reserve {100 * r['reserve']:.2f} %", f"{time.time() - t0:.0f}s", flush=True)
        out["sweep"][nm] = {}
        for k in (0.95, 0.90):
            rr = f(k)
            out["sweep"][nm][f"{k:.2f}"] = slim(rr)
            print(f"   k_thr {k:.2f}: reserve {100 * rr['reserve']:.2f} % burned {rr['n2o_burned']:.4f} usable {rr['usable']:.4f} "
                  f"on {rr['thrust_on_s']:.2f} s td {rr.get('td_vz')} apo {rr.get('h_apo')} exhausted {rr.get('exhausted', False)}", flush=True)
        if nm in ("A1_plan0.81_liq_med", "B1_62m", "B1_85m"):
            lo, hi = 0.80, 1.0      # reserve(lo) < 0.25 assumed, reserve(hi) as computed
            if r["reserve"] < 0.25:
                out["break_even"][nm] = dict(k_thr=None, note="does not meet the rule at k_thr 1.0")
                continue
            for _ in range(9):
                mid = 0.5 * (lo + hi)
                rm = f(mid)
                ok = (rm["reserve"] >= 0.25) and not rm.get("exhausted", False)
                if ok:
                    hi = mid
                else:
                    lo = mid
            out["break_even"][nm] = dict(k_thr=hi, shortfall_pct=100 * (1 - hi), resolution=hi - lo)
            print(f"   rule met down to k_thr {hi:.4f} (shortfall {100 * (1 - hi):.1f} %, resolution {hi - lo:.4f})", flush=True)
        json.dump(out, open(os.path.join(HERE, "rg08_isp.json"), "w"), indent=1, default=float)
    json.dump(out, open(os.path.join(HERE, "rg08_isp.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()

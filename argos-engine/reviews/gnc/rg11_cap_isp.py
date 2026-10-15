"""rg11_cap_isp v1 (independent GNC review, 2026-10-13): sensitivity of the B1 62 m cap to a delivered-thrust shortfall,
on the AUTHOR's model and cap logic (m2_regband_mc.max_h: lowest closing hop by bisection lo 30 / hi 85 m, 10 iterations,
+25 % rule on the nominal flight, no wind, no noise), unchanged code from the byte-identical scratch copy (rg02).

The shortfall is the run6 dispersion thrust_scale (delivered thrust per Pc-map thrust at the same propellant flow, the
quantity the Monte Carlo draws N(1, 0.05)), applied to every flight of the cap search through run6.fly(disp=...).
Cases: governing corner (a 0.6, n 0.68, throat growth 0.11, J_ref of the flight, 'flight' mode) and the no-band B1.
thrust_scale 1.00 must reproduce the author's governing cap (62.9 m rounded down to 62 m; regband_nominal.json).
Output: rg11_cap_isp.json. One process.
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import rg05_sens as S  # noqa: E402

_ORIG_FLY = S.R.fly
DISP_NOW = {}


def _fly(cfg, disp=None, nrec=6000):
    d = dict(DISP_NOW)
    if disp:
        d.update(disp)
    return _ORIG_FLY(cfg, disp=d or None, nrec=nrec)


S.R.fly = _fly


def main():
    out = dict(script="rg11_cap_isp v1", cases={})
    bases = {"corner a0.6|n0.68|g0.11 (governing)": dict(S.RBM.B1, reg_a=0.6, reg_n=0.68, throat_g=0.11, throat_loop=1),
             "no band, no growth": dict(S.RBM.B1)}
    for ts in (1.00, 0.97, 0.95, 0.90):
        DISP_NOW.clear()
        if ts != 1.0:
            DISP_NOW["thrust_scale"] = ts
        for nm, base in bases.items():
            t0 = time.time()
            h, ob = S.RBM.max_h(dict(base))
            o62 = dict(base, h_target=62.0)
            if o62.get("throat_g", 0.0) > 0.0:
                o62["throat_jref"] = S.TG.j_ref({k: v for k, v in o62.items() if k not in ("throat_g", "throat_jref")})[0]
            r62 = S.PC.nominal(o62, S.PC.M_TANK)
            row = dict(thrust_scale=ts, h_cap_m=h, reserve_at_cap=(S.PC.nominal(ob, S.PC.M_TANK)["reserve_frac"] if ob else None),
                       at_62m=dict(reserve=r62["reserve_frac"], closes=r62["closes"], landed=r62["landed_ok"],
                                   exhausted=r62["exhausted"], n2o_burned=r62["n2o_burned"], burn_time_s=r62["burn_time_s"],
                                   h_max=r62["h_max"]))
            out["cases"].setdefault(nm, []).append(row)
            print(nm, json.dumps(row), f"{time.time() - t0:.0f}s", flush=True)
            json.dump(out, open(os.path.join(HERE, "rg11_cap_isp.json"), "w"), indent=1, default=float)
    json.dump(out, open(os.path.join(HERE, "rg11_cap_isp.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()

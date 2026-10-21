"""m2_dc_burn_check v1 (2026-10-13): burn-time definition check of the dispersed duty cycles v3 (Combustion query relayed by
the lead 2026-10-13: DC-B1_hop_85m_disp_max_kest2_v3.csv thrust ends at 23.59 s, the index gives 24.09 s).

Finding being checked: the index burn_time_s was the sim6 result 'burn_time', an engine-ON counter: it accumulates while the
FSW burn state is on, so it (a) excludes the shutdown tail-off (thrust still > 1 N for a few hundredths of a second after
the cut) and (b) on a propellant-limited run keeps counting after the liquid is gone (thrust and flow already zero) until
the touchdown cut. The thermal quantity is the THRUST-ON time of the time history (F > 1 N; sum of both burns for A1).
This script re-flies all 500 runs of each Monte Carlo case behind the dispersed duty cycles (same configuration, draws seed
101, sim6/run6 v2.7-dev) with the recorder on, computes the thrust-on time of every run, and repeats the duty-cycle selection
('p99' = smallest value >= the 99th percentile; 'max' = largest) on the thrust-on time, to show whether the selected runs
change. Every re-flown run is checked against its Monte Carlo CSV row ('burn_time' and 'ok').
Env: GNC_IFACE, GNC_ACT_RATE, GNC_BC_OUT (default out/duty_cycles_v3). Output: <out>/dc_burn_check.json"""
import csv
import json
import os
import sys
from multiprocessing import Pool
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("GNC_PC_RATCHET", "1")
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_duty_cycles_disp as DD  # noqa: E402

S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_BC_OUT", f"{S}/duty_cycles_v3")
I = {n: i for i, n in enumerate(s6.REC_NAMES)}
N, SEED = 500, 101
CASES = ["tg_B1_none_k2", "tg_B1_pc_k2", "tg_A1_none_k2", "tg_A1_pc_k2"]
_W = {}


def _init(case):
    cases, _ = DD.case_over()
    over = dict(cases[case][0])
    m = over.pop("m_fixed")
    cfg = R.cfg_of(**dict(over, m_n2o=float(m)))
    _W["cfg"] = cfg
    _W["D"] = R.draw(np.random.default_rng(SEED), N, cfg)


def _one(i):
    c, disp = R.run_cfg(_W["cfg"], _W["D"][i])
    res, rec, info = R.fly(dict(c, rec_dt=0.01), disp, nrec=8000)
    t, F = rec[:, I["t"]], rec[:, I["F"]]
    dt = np.diff(t, prepend=0.0)
    on = F > 1.0
    last = float(t[on][-1]) if on.any() else float("nan")
    return i, float(np.sum(dt[on])), last, float(res["burn_time"]), bool(res["exhausted"] > 0.5), R.success(res)


def pick(x, rule):
    if rule == "max":
        return int(np.argmax(x)), float(np.percentile(x, 99))
    p = float(np.percentile(x, 99))
    cand = [j for j in range(len(x)) if x[j] >= p]
    return min(cand, key=lambda j: x[j]), p


def main():
    os.makedirs(OUT, exist_ok=True)
    cases, _ = DD.case_over()
    out = dict(version="m2_dc_burn_check v1", date="2026-10-13", sim=s6.SIM6_VERSION, iface=R.IFACE,
               definition=("thrust_on_s = sum of record steps (0.01 s) with delivered thrust F > 1 N (all burns); "
                           "engine_on_counter_s = sim6 result burn_time (FSW burn state on; excludes the shutdown tail-off, "
                           "includes zero-thrust time after propellant exhaustion until the cut)"), cases={})
    for case in CASES:
        rows = list(csv.DictReader(open(cases[case][1])))
        with Pool(2, initializer=_init, initargs=(case,)) as p:
            res = sorted(p.map(_one, range(N), chunksize=25))
        ton = np.array([r[1] for r in res]); cnt = np.array([r[3] for r in res])
        rep = all(float(rows[i]["burn_time"]) == cnt[i] and (int(rows[i]["ok"]) == 1) == res[i][5] for i in range(N))
        cnt_csv = np.array([float(r["burn_time"]) for r in rows])
        sel = {}
        for rule in ("p99", "max"):
            i_c, p_c = pick(cnt_csv, rule)
            i_t, p_t = pick(ton, rule)
            sel[rule] = dict(by_counter=dict(run=i_c, value_s=float(cnt_csv[i_c]), p99_s=p_c, thrust_on_of_that_run_s=float(ton[i_c])),
                             by_thrust_on=dict(run=i_t, value_s=float(ton[i_t]), p99_s=p_t),
                             same_run=bool(i_c == i_t))
        exh = [dict(run=r[0], thrust_on_s=r[1], counter_s=r[3], last_thrust_t_s=r[2]) for r in res if r[4]]
        d = ton - cnt
        ne = np.array([not r[4] for r in res])
        out["cases"][case] = dict(reproduces_mc_csv=rep, selection=sel, exhausted_runs=exh,
                                  thrust_on_minus_counter_s_non_exhausted=dict(min=float(d[ne].min()), median=float(np.median(d[ne])),
                                                                                max=float(d[ne].max())),
                                  thrust_on_p50_p99_max_s=[float(np.percentile(ton, 50)), float(np.percentile(ton, 99)), float(ton.max())],
                                  counter_p50_p99_max_s=[float(np.percentile(cnt, 50)), float(np.percentile(cnt, 99)), float(cnt.max())])
        print(case, "reproduces", rep, "| p99 counter run", sel["p99"]["by_counter"]["run"], "thrust-on run", sel["p99"]["by_thrust_on"]["run"],
              "| max counter run", sel["max"]["by_counter"]["run"], f"({sel['max']['by_counter']['value_s']:.3f} s, thrust-on "
              f"{sel['max']['by_counter']['thrust_on_of_that_run_s']:.3f} s)", "thrust-on run", sel["max"]["by_thrust_on"]["run"],
              f"({sel['max']['by_thrust_on']['value_s']:.3f} s) | exhausted {len(exh)} | non-exhausted thrust-on - counter "
              f"{d[ne].min():.3f}..{d[ne].max():.3f} s", flush=True)
    with open(os.path.join(OUT, "dc_burn_check.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", os.path.join(OUT, "dc_burn_check.json"))


if __name__ == "__main__":
    main()

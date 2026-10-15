"""m2_rev3_hold_trace v1.0 (GNC rev3, 2026-10-13): P4 - command-hold trace for R2 v2 (LEAD CHANGELOG line 186 (2): ECU
command held at the start level while the drogue is attached and Pc is invalid; line 194 (2): flame-out side on F_cold(lift,
P_tank), lit side PENDING the Combustion v2.4b grain_q1d start-level CSV).

Flies, with records, on sim6 v2.12-dev (amendment V2 hold; V3 off), base A1_none, state pw, purge G73, 4 runs each (seed-101
draws of m2_bitcheck_v211.fly_case):
  fo_cb_hold     undetected flame-out, cold-flow thrust = DERIVED design bound F_cold(lift, P_tank) (pv2_cold 1), command
                 held at 62.5 N, no release (pcf_Facc 1e9), R2 window to 0.8 s  [the P4s fo_cb statistics arm]
  fo_cb_nohold   the same without the hold (guidance command)                    [the P4s fo_cb_nohold arm]
  lit_k100_hold  lit at 62.5 N x pcf_k 1.0 - the lit model WITHDRAWN by line 194 (2); recorded only to show the command
                 and the R2 estimate during the hold, not as the lit thrust history (PENDING v2.4b)
Per run: the records from t_relight - 0.05 s to t_relight + 1.6 s (t, Fcmd, F truth, Fcl cold-flow thrust, valve lift,
pfa = R2 estimate of the deciding mode, Ptank) and a summary: the command values during the hold, its start / end, the
largest cold-flow thrust, lift and R2 estimate. SIM only; no hardware data; the cold-flow bound is DERIVED (Combustion), the
start-lift point is TO-VERIFY (CF-3).
Env: m2r3_env.sh (strict, pins_rev3). Output: <out>/hold_trace.json."""
import hashlib
import json
import os
import sys
from collections import OrderedDict
import numpy as np

TREE = os.environ.get("GNC_TREE", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, TREE)
sys.path.insert(0, os.path.join(TREE, "scripts"))
import m2_bitcheck_v211 as B11  # noqa: E402
from gncsim import run6 as R, sim6 as s6  # noqa: E402

VERSION = "m2_rev3_hold_trace v1.0"
OUT = os.environ.get("GNC_REV3_OUT", "/home/claude/work/space/out/rev3/fly")
PC2 = dict(pcf_on=1, pcf_dt=0.0, pcf_rule=2, pv2_on=1, pv2_hold=1, pv2_Fh=62.5, pv2_bl=0, pcf_Facc=1e9, pcf_tmax=0.8)
CASES = OrderedDict([
    ("fo_cb_hold", dict(PC2, pcf_fo=1, pv2_cold=1)),
    ("fo_cb_nohold", dict(PC2, pcf_fo=1, pv2_cold=1, pv2_hold=0)),
    ("lit_k100_hold", dict(PC2)),
])
COLS = ("t", "Fcmd", "F", "Fcl", "lift", "pfa", "Ptank")


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def main():
    ri = {k: i for i, k in enumerate(s6.RES_NAMES)}
    ci = {k: i for i, k in enumerate(s6.REC_NAMES)}
    out = OrderedDict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, sim6_sha16=sha16(s6.__file__),
                      run6_sha16=sha16(R.__file__), method=__doc__.split("\n\n")[1].strip(), cases=OrderedDict())
    for name, ex in CASES.items():
        r, recs = B11.fly_case("A1_none", "pw", "G73", "", ex, 4, 4)
        runs = []
        for j, rc in enumerate(recs):
            t = rc[:, ci["t"]]
            tr = float(r[j, ri["t_relight"]])
            w = (t >= tr - 0.05) & (t <= tr + 1.6)
            hold = np.where(np.abs(rc[:, ci["Fcmd"]] - 62.5) < 1e-9)[0]
            e = OrderedDict(t_relight=round(tr, 3), hold_s=round(float(r[j, ri["pv2_hold_s"]]), 3),
                            aborted=float(r[j, ri["pcf_abt"]]) if "pcf_abt" in ri else None,
                            hold_records=int(len(hold)),
                            hold_t=[round(float(t[hold[0]]), 3), round(float(t[hold[-1]]), 3)] if len(hold) else None,
                            Fcmd_values_in_window=sorted(set(round(float(x), 1) for x in rc[w, ci["Fcmd"]])),
                            F_truth_max_in_window=round(float(rc[w, ci["F"]].max()), 1),
                            Fcl_max=round(float(rc[w, ci["Fcl"]].max()), 2), lift_max_mm=round(float(rc[w, ci["lift"]].max()), 4),
                            pfa_max=round(float(rc[w, ci["pfa"]].max()), 2),
                            trace=OrderedDict((c, [round(float(x), 4) for x in rc[w, ci[c]]]) for c in COLS))
            runs.append(e)
            print(f"{name} run {j}: t_relight {e['t_relight']} hold {e['hold_s']} s, {e['hold_records']} records at 62.5 N "
                  f"{e['hold_t']}, Fcmd values {e['Fcmd_values_in_window'][:8]}, F max {e['F_truth_max_in_window']}, "
                  f"Fcl max {e['Fcl_max']}, lift max {e['lift_max_mm']} mm, R2 max {e['pfa_max']}", flush=True)
        out["cases"][name] = OrderedDict(extra=ex, runs=runs)
    p = os.path.join(OUT, "hold_trace.json")
    json.dump(out, open(p, "w"))
    print("wrote", p, sha16(p), flush=True)


if __name__ == "__main__":
    main()

"""m2_dc_a1_v28_record v1 (GNC, 2026-10-13): A1 dispersed p99 duty cycle on the v2.8 relight design, published as a RECORD.

Lead decision 2026-10-13 (early_light_sizing): B1 governs thermal and erosion; no A1 thermal re-run for early lights; GNC
publishes the early-light A1 p99 cycle as a record once the fix is chosen. The fix chosen is the v2.8 relight design (Finding A
= option (b)); the earliest lights of that design are the liquid-line lights (Combustion RC-03 E0->E2 0.126-0.499 s), flown at
the planning value 0.81 s (GNC rule, adopted by the lead 2026-10-13; relight_planning_v28). This script re-flies the p99 run (smallest engine-on counter >= the 99th
percentile, the m2_duty_cycles_disp selection rule) of the m2_relight_v28 cases
  v28_liq_p{PLAN}_A1_none_k2  -> DC-A1_full_flight_disp_p99_kest2_v28liq_v3      (record)
  v28_liq_p{PLAN}_A1_pc_k2    -> DC-A1_full_flight_disp_p99_kest2_v28liq_tg711_v3 (record, throat growth)
with the recorder, checks every result field against that run's Monte Carlo row, and writes the cycle in the duty-cycle v3 format
(m2_duty_cycles_disp rows_of: same 23 columns and units) plus the metadata into the index under 'records' (not 'cycles': a
record is not a sizing case). Index revision 2026-10-13d.
Env: GNC_IFACE, GNC_ACT_RATE, GNC_DC_OUT (out/duty_cycles_v3), GNC_V28_OUT (out/relight_v28), GNC_V28_PLAN (0.81)."""
import csv
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("GNC_PC_RATCHET", "1")
os.environ.setdefault("GNC_OUT", "/home/claude/work/space/out/prop_closure_m2")
os.environ.setdefault("GNC_SUFFIX", "pc2")
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_duty_cycles_disp as DD  # noqa: E402
import m2_duty_cycles_v3 as DC3  # noqa: E402
import m2_relight_v28 as V  # noqa: E402

VERSION = "m2_dc_a1_v28_record v1"
I = {n: i for i, n in enumerate(s6.REC_NAMES)}
OUT = DC3.OUT
V28 = os.environ.get("GNC_V28_OUT", "/home/claude/work/space/out/relight_v28")
PLAN = float(os.environ.get("GNC_V28_PLAN", "0.81"))
TARGETS = [("DC-A1_full_flight_disp_p99_kest2_v28liq_v3", "A1_none"),
           ("DC-A1_full_flight_disp_p99_kest2_v28liq_tg711_v3", "A1_pc")]


def main():
    tabs = V.e0e2_tables()
    idx_p = os.path.join(OUT, "duty_cycles_index_v3.json")
    idx = json.load(open(idx_p))
    rev = idx.get("index_revision") or {}
    recs = [r for r in idx.get("records", []) if r["name"] not in [t[0] for t in TARGETS]]
    a1sz = max((c.get("engine_on_counter_s") or 0.0) for c in idx["cycles"] if c["name"].startswith("DC-A1_full_flight_disp_p99"))
    for name, base in TARGETS:
        case = V.cname(base, "liq", PLAN)
        csvp = os.path.join(V28, f"mc6_runs_{case}_v28.csv")
        mc_rows = list(csv.DictReader(open(csvp)))
        i, p99, bt = DD.pick(mc_rows, "p99")
        over = V.case_over(base, "liq", PLAN, tabs)
        cfg = R.cfg_of(**dict({k: v for k, v in over.items() if k != "m_fixed"}, m_n2o=float(over["m_fixed"])))
        D = R.draw(np.random.default_rng(DD.SEED), DD.N, cfg)
        c, disp = R.run_cfg(cfg, D[i])
        res, rec, info = R.fly(dict(c, rec_dt=0.01), disp, nrec=8000)
        mrow = mc_rows[i]
        mism = [k for k in mrow if k in s6.RES_NAMES and k != "nrec" and not (float(mrow[k]) == float(res[k]) or
                                                             (np.isnan(float(mrow[k])) and np.isnan(float(res[k]))))]
        rows = DD.rows_of(rec, info)
        t, F = rec[:, I["t"]], rec[:, I["F"]]
        mox, mf = rec[:, I["mox"]], rec[:, I["mf"]]
        n2o = float(np.sum(0.5 * (mox[1:] + mox[:-1]) * np.diff(t)))
        fuel = float(np.sum(0.5 * (mf[1:] + mf[:-1]) * np.diff(t)))
        meta = dict(name=name, kind="record_v2.8_relight", generator=VERSION,
                    source=f"SIM {s6.SIM6_VERSION} 6-DOF, dt 1 ms, recorded 10 ms; Monte Carlo run {i} of case {case} re-flown",
                    purpose=("RECORD (lead 2026-10-13): A1 p99 cycle with the earliest lights of the chosen relight fix (v2.8, "
                             f"liquid line, planning value {PLAN:g} s adopted by the lead 2026-10-13); NOT a sizing case: B1 governs "
                             "thermal and erosion"),
                    selection=dict(rule="smallest engine-on counter >= the 99th percentile of the 500 runs",
                                   burn_time_p50_p99_max_of_case_s=[float(np.percentile(bt, 50)), p99, float(bt.max())]),
                    mc_case=case, mc_csv=os.path.basename(csvp), mc_seed=DD.SEED, run_index=i, run_seed=int(D[i]["_seed"]),
                    start_delay_s=float(D[i]["_t_ign_q"]), reproduces_mc_row=not mism, mismatched_fields=mism[:10],
                    success=R.success(res), burn_time_s=DC3.burn_of(t, F)[0], engine_on_counter_s=float(res["burn_time"]),
                    burns_s=DC3.burn_of(t, F)[1], starts=int(res["starts"]), total_impulse_Ns=float(np.trapezoid(F, t)),
                    n2o_burned_kg=n2o, fuel_burned_kg=fuel,
                    vs_a1_sizing_cycle=dict(sizing_engine_on_counter_s=a1sz, this_counter_s=float(res["burn_time"]),
                                            inside=bool(float(res["burn_time"]) <= a1sz)))
        meta = DC3.write(name, rows, meta)    # same writer, columns and number format as every v3 cycle
        meta.update(DC3.axial_stats(rows, rec[:, I["legF"]]))
        recs.append(meta)
        print(f"{name}: run {i}, counter {res['burn_time']:.2f} s (case p99 {p99:.2f} s; A1 sizing {a1sz:.2f} s), thrust-on "
              f"{meta['burn_time_s']:.2f} s, reproduces MC row: {not mism}, success {meta['success']}", flush=True)
    idx["records"] = recs
    hist = list(rev.get("history", []))
    hist.append(f"2026-10-13d: 'records' added (A1 p99 cycles on the v2.8 relight design, liquid line, planning value {PLAN:g} s "
                "adopted by the lead; records, not sizing cases; lead 2026-10-13); cycles unchanged")
    idx["index_revision"] = dict(revision="2026-10-13d", history=hist)
    tmp = idx_p + ".tmp"
    with open(tmp, "w") as f:
        json.dump(idx, f, indent=1, default=float)
    os.replace(tmp, idx_p)
    print("index", idx_p, "revision 2026-10-13d")


if __name__ == "__main__":
    main()

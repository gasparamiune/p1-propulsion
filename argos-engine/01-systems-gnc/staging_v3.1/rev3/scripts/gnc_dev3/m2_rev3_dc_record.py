"""m2_rev3_dc_record v1.0 (GNC rev3, 2026-10-13): the 285 m duty-cycle record (rev3 plan P3, lead CHANGELOG line 181 (6)).

A1 dispersed p99 cycle at the 285 m apogee trim on the rev3 decided configuration, as a RECORD in the sense of the lead
decision of 2026-10-13 (early_light_sizing: B1 governs thermal and erosion; A1 p99 cycles are published as records, not sizing
cases). Method of m2_dc_a1_v28_record v1 and m2_duty_cycles_disp v1.2, unchanged: the p99 run (smallest sim6 engine-on
counter >= the 99th percentile of the 500 runs) of a rev3 Monte Carlo table is re-flown with the recorder on the same code
(gnc_dev3, sim6 v2.9-dev), every result field is compared with that run's table row, and the cycle is written in the
duty-cycle v3 format (m2_duty_cycles_disp rows_of: same 23 columns, units and number format).
  liq|G73|h285 on A1_none -> DC-A1_full_flight_285m_disp_p99_kest2_liqG73_A1none_rev3
  liq|G73|h285 on A1J_pc  -> DC-A1_full_flight_285m_disp_p99_kest2_liqG73_A1Jpc_rev3
The liquid-line state is taken because its p99 counter is the longest of the decided line states on every base (liq
8.37 / 8.19 s, pw 8.27 / 8.08 s on A1_none / A1J_pc; rf tables of m2_rev3_fly v1.1). The flight replicates m2_rev3_fly v1.1
fly() (m2_rg01_refly base_cfg, FSW-R2, mass estimator tot_cal_comp, decided release rule, purge G73, no plateau, h_target
285 m). Flown with the 60 g unusable residual (3 % of the load, ASSUMED); the R3-17 dip onset (62-80 g, DERIVED by the
reviewer) is compared with the liquid left of the run, not re-flown. SIM only; one Monte Carlo run, not a nominal flight; no
hardware data; not a physical approval. Output (work area only): <out>/<name>.csv and <out>/dc_record_285m.json; the files
are staged in staging_v3.1/rev3/duty_cycles/ (the published 01-systems-gnc/duty_cycles/ index is not touched).
Env: m2r3_env.sh with GNC_IFACE_PIN = pins_rev3; GNC_DC_REC_OUT (default out/rev3/dc_record_285)."""
import csv
import gzip
import hashlib
import json
import os
import sys
from collections import OrderedDict
import numpy as np

SP = "/home/claude/work/space"
OUTD = os.environ.get("GNC_DC_REC_OUT", f"{SP}/out/rev3/dc_record_285")
os.environ["GNC_DC_OUT"] = OUTD          # m2_duty_cycles_v3 / _disp read their OUT at import; nothing is written there
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m2_rev3_fly as RF  # noqa: E402
from m2_rev3_fly import F  # noqa: E402   (m2_rg01_refly, imported by m2_rev3_fly)
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_duty_cycles_disp as DD  # noqa: E402
import m2_duty_cycles_v3 as DC3  # noqa: E402

VERSION = "m2_rev3_dc_record v1.0"
I = {n: i for i, n in enumerate(s6.REC_NAMES)}
ARM = "liq|G73|h285"
TARGETS = [("DC-A1_full_flight_285m_disp_p99_kest2_liqG73_A1none_rev3", "A1_none"),
           ("DC-A1_full_flight_285m_disp_p99_kest2_liqG73_A1Jpc_rev3", "A1J_pc")]
HUB = "/home/claude/work/shared-fallback/engine"
IDX = f"{HUB}/01-systems-gnc/duty_cycles/duty_cycles_index_v3.json"
ONSETS_G = OrderedDict([("125N_62g", 62.0), ("250N_69g", 69.0), ("500N_80g", 80.0)])   # REV-COMB-3 R3-17 (DERIVED)


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def fly_one(base, i, p07z):
    """run i of m2_rev3_fly v1.1 fly(base, ARM) with the recorder (same cfg, draw, estimator and decided settings)."""
    spec = RF.ARMS[ARM]
    cfg, m = F.base_cfg(base, spec["state"], RF.cfg_extra(spec, p07z))
    jr = json.load(open(F.TG))["j_ref"]
    F.MV.TG_JREF_DEFAULT = float(jr["A1J" if base.startswith("A1J") else "A1"])
    D = R.draw(np.random.default_rng(101), F.N, cfg)
    ms = F.MV.case_specs()["tot_cal_comp"]
    c, disp = F.MV.run_cfg_case(cfg, D[i], ms, i, "base")
    c.update(F.DEC)
    c.update(F.PURGE[spec["purge"]])
    c.update(F.PLAT[spec["plat"]])
    res, rec, info = R.fly(dict(c, rec_dt=0.01), disp, nrec=8000)
    return res, rec, info, D[i], c, m


def main():
    os.makedirs(OUTD, exist_ok=True)
    idx = json.load(open(IDX))
    ref = OrderedDict()
    for c in idx["cycles"] + idx.get("records", []):
        if c["name"].startswith("DC-A1"):
            ref[c["name"]] = dict(kind=c.get("kind"), engine_on_counter_s=c.get("engine_on_counter_s"),
                                  burn_time_s=c.get("burn_time_s"), h_max_m=(c.get("summary") or {}).get("h_max"),
                                  total_impulse_Ns=c.get("total_impulse_Ns"), sha256_16=(c.get("sha256") or "")[:16])
    a1sz = max(v["engine_on_counter_s"] or 0.0 for k, v in ref.items() if k.startswith("DC-A1_full_flight_disp_p99")
               and "v28" not in k)
    p07z = F.engine_bay_mid()[0]
    out = OrderedDict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, sim6_sha16=sha16(s6.__file__),
                      run6_sha16=sha16(R.__file__), script_sha16=sha16(os.path.abspath(__file__)),
                      method=__doc__.split("\n\n")[1].strip(), iface=os.path.realpath(os.environ.get("GNC_IFACE", "")),
                      pin=os.environ.get("GNC_IFACE_PIN"),
                      pin_sha16=sha16(os.environ["GNC_IFACE_PIN"]) if os.environ.get("GNC_IFACE_PIN") else None,
                      published_index=dict(path=IDX, sha256_16=sha16(IDX), revision=(idx.get("index_revision") or {}).get("revision")),
                      a1_sizing_counter_s=a1sz, published_a1_cycles=ref, records=[])
    for name, base in TARGETS:
        tp = os.path.join(RF.OUT, RF.fname(base, ARM) + ".gz")
        rows_mc = list(csv.DictReader(gzip.open(tp, "rt")))
        i, p99, bt = DD.pick(rows_mc, "p99")
        res, rec, info, dr, c, m = fly_one(base, i, p07z)
        mrow = rows_mc[i]
        mism = [k for k in mrow if k in s6.RES_NAMES and k != "nrec" and not (float(mrow[k]) == float(res[k]) or
                                                             (np.isnan(float(mrow[k])) and np.isnan(float(res[k]))))]
        rows = DD.rows_of(rec, info)
        t, Fv = rec[:, I["t"]], rec[:, I["F"]]
        mox, mf = rec[:, I["mox"]], rec[:, I["mf"]]
        on = (Fv > 1.0) & (mf > 0)
        n2o = float(np.sum(0.5 * (mox[1:] + mox[:-1]) * np.diff(t)))
        fuel = float(np.sum(0.5 * (mf[1:] + mf[:-1]) * np.diff(t)))
        of = mox[on] / mf[on]
        liq_g = 1e3 * float(res["liq_left"])
        bts = [float(np.percentile(bt, 50)), p99, float(bt.max())]
        meta = OrderedDict(
            name=name, kind="record_rev3_285m", generator=VERSION,
            source=f"SIM {s6.SIM6_VERSION} 6-DOF, dt 1 ms, recorded 10 ms; Monte Carlo run {i} of rev3 arm {ARM} on {base} re-flown",
            purpose=("RECORD (rev3 plan P3; lead decision 2026-10-13 early_light_sizing): A1 p99 cycle at the 285 m apogee trim on "
                     "the rev3 decided configuration (FSW-R2 incl. k_est_asc 2, purge G73, decided release rule, liquid line); NOT "
                     "a sizing case: B1 governs thermal and erosion"),
            selection=dict(rule="smallest engine-on counter >= the 99th percentile of the 500 runs (m2_duty_cycles_disp pick)",
                           burn_time_p50_p99_max_of_case_s=bts, n_runs=len(bt)),
            mc_table=dict(path=tp, sha256_16=sha16(tp)), mc_seed=101, run_index=i, run_seed=int(dr["_seed"]),
            start_delay_s=float(dr["_t_ign_q"]) if "_t_ign_q" in dr else None,
            k_est_asc_flown=float(c["k_est_asc"]) if "k_est_asc" in c else None, h_target_flown_m=float(c.get("h_target", np.nan)),
            m_n2o_kg=float(m), reproduces_mc_row=not mism, mismatched_fields=mism[:10],
            summary={k: float(res[k]) for k in ("landed", "td_vz", "td_vh", "td_tilt", "td_rate", "prop_used", "liq_left",
                                                 "h_max", "h_ign", "v_ign", "burn_time", "starts", "max_gim", "max_hinge",
                                                 "max_axial_g") if k in res},
            success=R.success(res), burn_time_s=DC3.burn_of(t, Fv)[0], engine_on_counter_s=float(res["burn_time"]),
            burns_s=DC3.burn_of(t, Fv)[1], thrust_end_s=DC3.burn_of(t, Fv)[2], starts=int(res["starts"]),
            total_impulse_Ns=float(np.trapezoid(Fv, t)), n2o_burned_kg=n2o, fuel_burned_kg=fuel,
            OF_overall=n2o / fuel if fuel > 0 else None, OF_range_burning=[float(of.min()), float(of.max())] if of.size else None,
            Pc_max_Pa=float(np.max(rows[:, 6])), throttle_max=float(np.max(rows[:, 3])),
            vs_a1_sizing_cycle=dict(sizing_engine_on_counter_s=a1sz, this_counter_s=float(res["burn_time"]),
                                    inside=bool(float(res["burn_time"]) <= a1sz)),
            residual=OrderedDict(flown_g=round(1e3 * 0.03 * float(m), 1), basis="3 % of the load, ASSUMED (60 g for 2.00 kg)",
                                 liquid_left_g=round(liq_g, 1),
                                 margin_to_dip_onset_g=OrderedDict((k, round(liq_g - v, 1)) for k, v in ONSETS_G.items()),
                                 note="R3-17 onsets DERIVED by the reviewer (outlet geometry MISSING, Mechanical OI-32); "
                                      "compared with the liquid left of this run, not re-flown"))
        meta = DC3.write(name, rows, meta)
        meta["file"] = f"01-systems-gnc/staging_v3.1/rev3/duty_cycles/{name}.csv"
        meta["sha256_16"] = meta["sha256"][:16]
        meta.update(DC3.axial_stats(rows, rec[:, I["legF"]]))
        out["records"].append(meta)
        print(f"{name}: {base} run {i} seed {meta['run_seed']}, counter {res['burn_time']:.3f} s (case p50/p99/max "
              f"{bts[0]:.2f}/{p99:.3f}/{bts[2]:.2f} s; A1 sizing {a1sz:.3f} s, inside {meta['vs_a1_sizing_cycle']['inside']}), "
              f"thrust-on {meta['burn_time_s']:.2f} s, burns {[[round(a, 2), round(b, 2)] for a, b in meta['burns_s']]}, "
              f"I {meta['total_impulse_Ns']:.0f} N s, N2O {n2o:.3f} kg, apex {res['h_max']:.1f} m, liq left {liq_g:.1f} g, "
              f"success {meta['success']}, reproduces MC row {not mism} {mism[:5]}", flush=True)
    p = os.path.join(OUTD, "dc_record_285m.json")
    with open(p, "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", p, sha16(p), flush=True)


if __name__ == "__main__":
    main()

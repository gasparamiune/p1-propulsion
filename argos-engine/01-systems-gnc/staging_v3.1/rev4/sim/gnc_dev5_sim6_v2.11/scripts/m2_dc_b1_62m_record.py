"""m2_dc_b1_62m_record v1 (GNC, 2026-10-13): B1 dispersed p99 and max duty cycles at the lead's provisional 62 m cap, as RECORDS
in the duty-cycle v3 format (lead request 2026-10-13: Combustion confirms the web corner at 62 m; the 85 m dispersed cycles stay
the sizing cases, lead decision 2026-10-13 b1_hop_cap_62m).

Cases (500 runs each, seed 101, FSW v2.7 provisional k_est_asc 2 + ratchet, N2O 2.00 kg, pc2 configuration; iface_v3c;
sim6/run6 v2.7.1-dev):
  tgl_B1_lead62_none_k2  B1 62 m, no throat growth: NEW 500-run Monte Carlo (m2_mc6.run_case, as m2_regband_mc v1.1 runs its
                         cases); the analogue of tg_B1_none_k2, the basis of the 85 m sizing cycle DC-B1_hop_85m_disp_p99_kest2_v3
  tgl_B1_lead62_pc_k2    B1 62 m, throat growth U(0.07, 0.11) + ECU Pc loop, J_ref of the no-band 62 m flight: the m2_regband_mc
                         v1.1 case (its CSV, configuration rebuilt by m2_regband_mc.cases and checked against rb_case_*.json)
Selection (m2_duty_cycles_disp v1.2 rule): p99 = the run with the smallest engine-on counter >= the 99th percentile; max = the
longest counter. Every one of the 500 runs of each case is re-flown with the 10 ms recorder, checked field by field against its
Monte Carlo row, and its thrust-on time computed, so the selection is cross-checked on the thrust-on time as well
(m2_dc_burn_check convention).
Files: DC-B1_hop_62m_disp_{p99,max}_kest2_v3.csv (no growth) and DC-B1_hop_62m_disp_{p99,max}_kest2_tg711_v3.csv (growth): the
same 23 columns, units and number format as every v3 cycle (m2_duty_cycles_v3 writer, m2_duty_cycles_disp rows_of), and
duty_cycles_records_b1_62m_v3.1.json (records only). The hub index duty_cycles_index_v3.json rev d is frozen with gnc.json v3
under independent review: these records are a v3.1 STAGING addition (hub 01-systems-gnc/staging_v3.1/duty_cycles/).
Env: GNC_IFACE, GNC_ACT_RATE, GNC_DC_OUT (default out/duty_cycles_v3_1), GNC_B62_PARTS (mc,records)."""
import csv
import json
import os
import sys
import time
import numpy as np

S = "/home/claude/work/space/out"
os.environ.setdefault("GNC_DC_OUT", f"{S}/duty_cycles_v3_1")
os.environ.setdefault("GNC_PC_RATCHET", "1")
os.environ.setdefault("GNC_OUT", "/home/claude/work/space/out/prop_closure_m2")
os.environ.setdefault("GNC_SUFFIX", "pc2")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_duty_cycles_v3 as DC3  # noqa: E402
import m2_duty_cycles_disp as DD  # noqa: E402
import m2_mc6 as M  # noqa: E402
import m2_prop_closure as PC  # noqa: E402
import m2_regband_mc as RBM  # noqa: E402

VERSION = "m2_dc_b1_62m_record v1"
OUT = DC3.OUT
MCD = os.path.join(OUT, "mc")
PARTS = os.environ.get("GNC_B62_PARTS", "mc,records").split(",")
HUB = "01-systems-gnc/staging_v3.1/duty_cycles/"
MC_HUB = {"tgl_B1_lead62_none_k2": "01-systems-gnc/staging_v3.1/results/b1_62m_mc/mc6_runs_tgl_B1_lead62_none_k2.csv.gz",
          "tgl_B1_lead62_pc_k2": "01-systems-gnc/results/regband/mc6_runs_tgl_B1_lead62_pc_k2_rb.csv.gz"}
H = 62.0                 # REQ lead decision 2026-10-13 (b1_hop_cap_62m, provisional)
V3_INDEX = f"{S}/duty_cycles_v3/duty_cycles_index_v3.json"
TARGETS = [("DC-B1_hop_62m_disp_p99_kest2_v3", "tgl_B1_lead62_none_k2", "p99"),
           ("DC-B1_hop_62m_disp_max_kest2_v3", "tgl_B1_lead62_none_k2", "max"),
           ("DC-B1_hop_62m_disp_p99_kest2_tg711_v3", "tgl_B1_lead62_pc_k2", "p99"),
           ("DC-B1_hop_62m_disp_max_kest2_tg711_v3", "tgl_B1_lead62_pc_k2", "max")]
SIZING_85 = {"tgl_B1_lead62_none_k2": ("DC-B1_hop_85m_disp_p99_kest2_v3", "DC-B1_hop_85m_disp_max_kest2_v3"),
             "tgl_B1_lead62_pc_k2": ("DC-B1_hop_85m_disp_p99_kest2_tg711_v3", "DC-B1_hop_85m_disp_max_kest2_tg711_v3")}


def case_defs():
    cs = RBM.cases(None)
    pc_over, _, pc_note = cs["tgl_B1_lead62_pc_k2"]
    cj = json.load(open(os.path.join(RBM.OUT, "rb_case_tgl_B1_lead62_pc_k2.json")))
    if abs(float(cj["config"]["throat_jref"]) - float(pc_over["throat_jref"])) > 1e-9 or float(cj["config"]["h_target"]) != H:
        raise SystemExit(f"tgl_B1_lead62_pc_k2 configuration does not match its Monte Carlo record: {cj['config']}")
    none_over = dict(RBM.B1, h_target=H, m_fixed=PC.M_TANK)
    return {"tgl_B1_lead62_none_k2": (none_over, os.path.join(MCD, "mc6_runs_tgl_B1_lead62_none_k2.csv"),
                                      f"B1 at the lead's provisional cap {H:.1f} m, k_est_asc 2, no throat growth (GNC "
                                      "2026-10-13, for the 62 m records)"),
            "tgl_B1_lead62_pc_k2": (pc_over, os.path.join(RBM.OUT, "mc6_runs_tgl_B1_lead62_pc_k2_rb.csv"), pc_note)}


def part_mc(cs):
    os.makedirs(MCD, exist_ok=True)
    over, p, note = cs["tgl_B1_lead62_none_k2"]
    if os.path.exists(p) and os.path.getsize(p) > 100:
        print("exists", p, flush=True)
        return
    o, rows = M.run_case("tgl_B1_lead62_none_k2", over, note)
    if not rows:
        raise SystemExit("tgl_B1_lead62_none_k2: no Monte Carlo (nominal sizing gate)")
    M.write_csv(p, rows)
    keep = {k: o.get(k) for k in ("case", "note", "m_n2o_mc_kg", "m_liftoff_kg", "cpu_s", "sim")}
    keep["fail_modes"] = o["summary"]["fail_modes"]
    keep["config"] = {k: over.get(k) for k in ("h_target", "throat_g_band", "throat_jref", "throat_loop", "k_est_asc", "reg_band")}
    with open(os.path.join(MCD, "case_tgl_B1_lead62_none_k2.json"), "w") as f:
        json.dump(keep, f, indent=1, default=float)
    print(f"tgl_B1_lead62_none_k2: P {np.mean([r['ok'] for r in rows]):.3f} fails {o['summary']['fail_modes']} "
          f"({o['cpu_s']:.0f} s)", flush=True)


def refly_all(over, mc_rows, keep_runs):
    """re-fly all runs (10 ms recorder): thrust-on time, reproduction of the MC row; keep the records of keep_runs."""
    over = dict(over)
    m = over.pop("m_fixed")
    cfg = R.cfg_of(**dict(over, m_n2o=float(m)))
    D = R.draw(np.random.default_rng(DD.SEED), DD.N, cfg)
    th_on, mism, kept = [], [], {}
    for i, dr in enumerate(D):
        c, disp = R.run_cfg(cfg, dr)
        res, rec, info = R.fly(dict(c, rec_dt=0.01), disp, nrec=8000)
        mrow = mc_rows[i]
        mm = [k for k in mrow if k in s6.RES_NAMES and k != "nrec" and not (float(mrow[k]) == float(res[k]) or
                                                           (np.isnan(float(mrow[k])) and np.isnan(float(res[k]))))]
        if mm:
            mism.append(dict(run=i, fields=mm[:8]))
        th_on.append(DC3.burn_of(rec[:, DD.I["t"]], rec[:, DD.I["F"]])[0])
        if i in keep_runs:
            kept[i] = (res, rec, info, dr, mm)
    return np.array(th_on), mism, kept, cfg


def selection_check(bt, th):
    out = {}
    for rule in ("p99", "max"):
        if rule == "max":
            ic, it_ = int(np.argmax(bt)), int(np.argmax(th))
        else:
            p_c, p_t = np.percentile(bt, 99), np.percentile(th, 99)
            ic = min([j for j in range(len(bt)) if bt[j] >= p_c], key=lambda j: bt[j])
            it_ = min([j for j in range(len(th)) if th[j] >= p_t], key=lambda j: th[j])
        out[rule] = dict(same_run=ic == it_, by_counter=dict(run=ic, value_s=float(bt[ic]), thrust_on_of_that_run_s=float(th[ic])),
                         by_thrust_on=dict(run=it_, value_s=float(th[it_]), p99_s=float(np.percentile(th, 99))))
    return out


def part_records(cs):
    os.makedirs(OUT, exist_ok=True)
    v3 = json.load(open(V3_INDEX))
    v3c = {c["name"]: c for c in v3["cycles"]}
    recs, checks = [], {}
    t0 = time.time()
    for case in ("tgl_B1_lead62_none_k2", "tgl_B1_lead62_pc_k2"):
        over, csvp, note = cs[case]
        mc_rows = list(csv.DictReader(open(csvp)))
        sel = {rule: DD.pick(mc_rows, rule) for rule in ("p99", "max")}
        bt = sel["p99"][2]
        th, mism, kept, cfg = refly_all(over, mc_rows, {sel["p99"][0], sel["max"][0]})
        sc = selection_check(bt, th)
        checks[case] = dict(n_runs=len(mc_rows), runs_reproducing_mc_row=len(mc_rows) - len(mism), mismatches=mism[:10],
                            counter_p50_p99_max_s=[float(np.percentile(bt, 50)), float(np.percentile(bt, 99)), float(bt.max())],
                            thrust_on_p50_p99_max_s=[float(np.percentile(th, 50)), float(np.percentile(th, 99)), float(th.max())],
                            success_rate=float(np.mean([float(r["ok"]) for r in mc_rows])), selection=sc,
                            mc_csv=os.path.relpath(csvp, S), mc_csv_hub=MC_HUB[case], note=note)
        print(f"{case}: re-flown {len(mc_rows)} runs ({time.time() - t0:.0f} s), reproduce {len(mc_rows) - len(mism)}; counter "
              f"p50/p99/max {checks[case]['counter_p50_p99_max_s']}; thrust-on {checks[case]['thrust_on_p50_p99_max_s']}; "
              f"selection {[(k, v['same_run']) for k, v in sc.items()]}", flush=True)
        for name, cse, rule in TARGETS:
            if cse != case:
                continue
            i, p99, _ = sel[rule]
            res, rec, info, dr, mm = kept[i]
            rows = DD.rows_of(rec, info)
            t = rec[:, DD.I["t"]]
            F = rec[:, DD.I["F"]]
            mox, mf = rec[:, DD.I["mox"]], rec[:, DD.I["mf"]]
            on = (F > 1.0) & (mf > 0)
            n2o = float(np.sum(0.5 * (mox[1:] + mox[:-1]) * np.diff(t)))
            fuel = float(np.sum(0.5 * (mf[1:] + mf[:-1]) * np.diff(t)))
            of = mox[on] / mf[on]
            sz = v3c[SIZING_85[case][0 if rule == "p99" else 1]]
            meta = dict(name=name, kind="record_b1_62m_lead_cap", generator=VERSION,
                        source=f"SIM {s6.SIM6_VERSION} 6-DOF, engine: {info['tags']['engine_model'][1]}, dt 1 ms, recorded 10 ms; "
                               f"Monte Carlo run {i} of case {case} re-flown",
                        purpose=("RECORD (lead 2026-10-13): B1 at the provisional 62 m cap for Combustion's web-corner check; NOT a "
                                 "sizing case: the 85 m dispersed cycles stay the sizing cases (lead decision 2026-10-13)"),
                        selection=dict(rule=("smallest engine-on counter >= the 99th percentile of the 500 runs" if rule == "p99"
                                             else "longest engine-on counter of the 500 runs"),
                                       rule_variable="Monte Carlo engine-on counter (sim6 burn_time)",
                                       thrust_on_cross_check=sc[rule],
                                       burn_time_p50_p99_max_of_case_s=[float(np.percentile(bt, 50)), p99, float(bt.max())],
                                       n_runs=len(bt)),
                        mc_case=case, mc_csv=os.path.relpath(csvp, S), mc_csv_hub=MC_HUB[case], mc_seed=DD.SEED, run_index=i,
                        run_seed=int(dr["_seed"]),
                        reproduces_mc_row=not mm, mismatched_fields=mm[:10],
                        dispersions={k: (float(dr[k]) if dr.get(k) is not None else None) for k in
                                     ("thrust_scale", "isp_scale", "dry_scale", "m_est_err", "_wind", "_wind_dir", "_gust_scale",
                                      "_T0", "_rho0", "_t_ign", "_k_retro", "_ca_tf", "throat_g")},
                        config={k: (v if not isinstance(v, (np.floating, np.integer)) else float(v)) for k, v in over.items()},
                        m_n2o_kg=float(over["m_fixed"]), tank_V_m3=info["tank_V"], m_liftoff_kg=info["m_liftoff"],
                        summary={k: float(res[k]) for k in ["landed", "td_vz", "td_vh", "td_tilt", "td_rate", "prop_used",
                                                            "liq_left", "h_max", "burn_time", "starts", "max_gim", "max_hinge",
                                                            "max_axial_g", "throat_g_end", "throat_J"] if k in res},
                        success=R.success(res), burn_time_s=DC3.burn_of(t, F)[0], engine_on_counter_s=float(res["burn_time"]),
                        burns_s=DC3.burn_of(t, F)[1], thrust_end_s=DC3.burn_of(t, F)[2], starts=int(res["starts"]),
                        total_impulse_Ns=float(np.trapezoid(F, t)), n2o_burned_kg=n2o, fuel_burned_kg=fuel,
                        OF_overall=n2o / fuel if fuel > 0 else None,
                        OF_range_burning=[float(of.min()), float(of.max())] if of.size else None,
                        Pc_max_Pa=float(np.max(rows[:, 6])), throttle_max=float(np.max(rows[:, 3])),
                        max_axial_specific_mps2=float(np.nanmax(rows[:, 9])), max_gimbal_deg=float(res["max_gim"]),
                        max_gimbal_rate_dps=float(res["max_gim_rate"]), max_hinge_est_Nm=float(res["max_hinge"]),
                        wind_mps_at_10m=float(dr["_wind"]),
                        vs_85m_sizing_cycle=dict(name=sz["name"], sizing_burn_time_s=sz["burn_time_s"],
                                                 sizing_engine_on_counter_s=sz["engine_on_counter_s"],
                                                 sizing_impulse_Ns=sz.get("total_impulse_Ns"),
                                                 sizing_n2o_burned_kg=sz.get("n2o_burned_kg"),
                                                 inside_on_burn_time=bool(DC3.burn_of(t, F)[0] <= sz["burn_time_s"]),
                                                 inside_on_n2o=bool(n2o <= (sz.get("n2o_burned_kg") or 1e9))),
                        note=("record at the lead's provisional 62 m cap; FSW v2.7 with k_est_asc 2 (provisional baseline); one "
                              "Monte Carlo run, not a nominal flight"))
            if not meta["success"]:
                sm = meta["summary"]
                meta["note"] += (f"; this run FAILS its landing (touchdown vz {sm.get('td_vz', float('nan')):.2f} m/s, vh "
                                 f"{sm.get('td_vh', float('nan')):.2f} m/s, tilt {sm.get('td_tilt', float('nan')):.1f} deg); the "
                                 "engine history is valid as a thermal input")
            meta.update(DC3.axial_stats(rows, rec[:, DD.I["legF"]]))
            meta = DC3.write(name, rows, meta)
            meta["file"] = HUB + name + ".csv"
            recs.append(meta)
            print(f"{name:40s} run {i:3d} counter {res['burn_time']:.2f} s (case p99 {p99:.2f}, max {bt.max():.2f}) thrust-on "
                  f"{meta['burn_time_s']:.2f} s I {meta['total_impulse_Ns']:.0f} N s N2O {n2o:.3f} kg ok {meta['success']} "
                  f"reproduces {meta['reproduces_mc_row']} | 85 m sizing {sz['burn_time_s']:.2f} s inside "
                  f"{meta['vs_85m_sizing_cycle']['inside_on_burn_time']}", flush=True)
    idx = dict(version="duty_cycles v3 records (B1 62 m)", status="v3.1 STAGING (gnc.json v3 and its duty_cycles_index_v3.json rev "
               "d are frozen under the independent GNC review; merge into the index at v3.1 publication)", date="2026-10-13",
               owner="Space/GNC", generator=VERSION, sim=s6.SIM6_VERSION, interface_set=R.IFACE,
               base_index=dict(file="01-systems-gnc/duty_cycles/duty_cycles_index_v3.json",
                               revision=(v3.get("index_revision") or {}).get("revision"), sha256=DC3.sha(V3_INDEX)),
               lead_decision="B1 cap 62 m provisional (REQ lead decision 2026-10-13, b1_hop_cap_62m); the 85 m dispersed cycles stay "
                             "the sizing cases",
               request="lead 2026-10-13: the B1 62 m p99 and max duty-cycle CSVs, same format, for Combustion's web-corner "
                       "check at 62 m",
               units=v3["units"], phase_codes=v3["phase_codes"], columns=DC3.COLS, burn_time_definition=DC3.BURN_DEF,
               max_axial_definition=DC3.AX_DEF, records=recs, selection_checks=checks,
               note=("records, not sizing cases. Throat growth variant (tg711): growth U(0.07, 0.11) with the ECU Pc loop, J_ref of "
                     "the no-band 62 m flight (m2_regband_mc v1.1 convention). No regression band in these flights (Combustion "
                     "applies its band corners to the thrust and oxidiser-flow histories, as for DC-B1 v3 p99 at 85 m)."))
    p = os.path.join(OUT, "duty_cycles_records_b1_62m_v3.1.json")
    with open(p, "w") as f:
        json.dump(idx, f, indent=1, default=float)
    print("wrote", p, flush=True)


def main():
    cs = case_defs()
    if "mc" in PARTS:
        part_mc(cs)
    if "records" in PARTS:
        part_records(cs)


if __name__ == "__main__":
    main()

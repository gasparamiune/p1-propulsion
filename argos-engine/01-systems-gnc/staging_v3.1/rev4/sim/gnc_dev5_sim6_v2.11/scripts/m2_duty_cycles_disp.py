"""m2_duty_cycles_disp v1.2 (2026-10-13; v1.2: axial-load fields of m2_duty_cycles_v3 v1.3 (airborne and leg-contact
maxima, location of the overall maximum); the failed max runs say that their overall maximum is the touchdown crash impact;
files unchanged. v1.1: burn_time_s = thrust-on time of the file and engine_on_counter_s = sim6
burn_time, as m2_duty_cycles_v3 v1.2 (Combustion query relayed by the lead: the B1 max run's thrust ends at liquid
depletion, 23.58-23.59 s, while the engine-on counter ran to the touchdown cut, 24.09 s); the selection rule stays on the
Monte Carlo counter (files unchanged) and the index records the thrust-on cross-check of m2_dc_burn_check v1; FSW note
reworded per the lead: the A1 paired check found no significant difference at 500 runs, it did not show 'no degradation'.
v1: DISPERSED-ENVELOPE duty cycles v3 for the thermal chain (lead decisions 2026-10-13:
the dispersed B1 85 m flights burn past the 19.0 s DC-B1 v2 envelope; k_est_asc 2 adopted provisionally as the FSW baseline;
the dispersed files gate the Combustion head-end BC files and the Mechanical thermal re-runs).

Each file is ONE Monte Carlo run re-flown with the recorder on: same configuration, same draw (seed 101, run index i), same
sim6/run6 v2.7-dev code as the 500-run case it comes from, checked value by value against that run's CSV row. Selection by
burn time (sum of both burns for A1): 'p99' = the run with the smallest burn time >= the 99th percentile of the 500 runs;
'max' = the longest-burning run. Failed runs are eligible (the engine burns either way).
  DC-B1_hop_85m_disp_{p99,max}_kest2_v3          B1 85 m hop, FSW v2.7 with k_est_asc 2, no throat growth   (tg_B1_none_k2)
  DC-B1_hop_85m_disp_{p99,max}_kest2_tg711_v3    same with in-flight throat growth U(0.07, 0.11), Pc loop    (tg_B1_pc_k2)
  DC-A1_full_flight_disp_p99_kest2_v3            A1 300 m, relight placeholder 1.1 / 1.7 s, k_est_asc 2      (tg_A1_none_k2)
  DC-A1_full_flight_disp_p99_kest2_tg711_v3      same with throat growth                                     (tg_A1_pc_k2)
Basis: iface_v3c (combustion.json v2.3 map, mechanical.json v2, electronics.json v1), N2O 2.00 kg, pc2 configuration of the
closure Monte Carlo (ideal-rate actuator model act_model 0: the thrust history, not the gimbal, is the thermal input).
Format: identical to DC-B1 v2 / v3 (same 23 columns, same units). Pc_Pa is the published map Pc at the Pc-equivalent thrust
F / thrust_scale (what the Pc loop holds; = F for an undispersed engine); O/F = mdot_ox_kgps / mdot_fuel_kgps (both columns
present); throttle_frac = F / 500 N (delivered thrust). The index gains every dispersed cycle in 'cycles' (kind
'dispersed_envelope') with the run index, the per-run seed and the drawn dispersions.
Env: GNC_IFACE, GNC_ACT_RATE, GNC_DC_OUT (default out/duty_cycles_v3). Output: CSVs + duty_cycles_index_v3.json updated."""
import csv
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("GNC_PC_RATCHET", "1")
from gncsim import run6 as R, sim6 as s6  # noqa: E402
from gncsim.propulsion import _bilin  # noqa: E402
import m2_duty_cycles_v3 as DC3  # noqa: E402
import m2_throat_mc as TG  # noqa: E402

S = "/home/claude/work/space/out"
OUT = DC3.OUT
_BC = os.path.join(OUT, "dc_burn_check.json")
BCHK = json.load(open(_BC))["cases"] if os.path.exists(_BC) else {}
VERSION = "m2_duty_cycles_disp v1.2"
I = {n: i for i, n in enumerate(s6.REC_NAMES)}
N = 500
SEED = 101


def case_over():
    """The MC case configurations exactly as m2_throat_mc v1.1 builds them (J_ref recomputed: deterministic)."""
    PC, MV = TG.PC, TG.MV
    ncs = PC.MM.NCS["slots"]
    est0 = R.DEF["t_ign_est"] + ncs
    A1 = dict(PC.DC["A1"], t_ign_add=ncs + TG.DT_RL, t_ign_est=est0 + TG.DT_RL)
    B1 = dict(PC.DC["B1"], h_target=85.0)
    jA, _ = TG.j_ref(A1)
    jB, _ = TG.j_ref(B1)
    GA = dict(throat_g_band=TG.BAND)
    return {"tg_B1_none_k2": (dict(B1, m_fixed=PC.M_TANK, k_est_asc=2), f"{S}/throat_growth/mc6_runs_tg_B1_none_k2_tg.csv"),
            "tg_B1_pc_k2": (dict(B1, m_fixed=PC.M_TANK, throat_jref=jB, throat_loop=1, k_est_asc=2, **GA),
                            f"{S}/throat_growth/mc6_runs_tg_B1_pc_k2_tg.csv"),
            "tg_A1_none_k2": (dict(A1, m_fixed=PC.M_TANK, k_est_asc=2), f"{S}/throat_growth_a1k2/mc6_runs_tg_A1_none_k2_tg.csv"),
            "tg_A1_pc_k2": (dict(A1, m_fixed=PC.M_TANK, throat_jref=jA, throat_loop=1, k_est_asc=2, **GA),
                            f"{S}/throat_growth/mc6_runs_tg_A1_pc_k2_tg.csv")}, dict(A1=jA, B1=jB)


TARGETS = [("DC-B1_hop_85m_disp_p99_kest2_v3", "tg_B1_none_k2", "p99"),
           ("DC-B1_hop_85m_disp_max_kest2_v3", "tg_B1_none_k2", "max"),
           ("DC-B1_hop_85m_disp_p99_kest2_tg711_v3", "tg_B1_pc_k2", "p99"),
           ("DC-B1_hop_85m_disp_max_kest2_tg711_v3", "tg_B1_pc_k2", "max"),
           ("DC-A1_full_flight_disp_p99_kest2_v3", "tg_A1_none_k2", "p99"),
           ("DC-A1_full_flight_disp_p99_kest2_tg711_v3", "tg_A1_pc_k2", "p99")]


def _sel_text(bc):
    """plain-text summary of the thrust-on cross-check of the selection (from m2_dc_burn_check)."""
    out = []
    for case, v in bc.items():
        for rule in ("p99", "max"):
            x = v["selection"][rule]
            c, t_ = x["by_counter"], x["by_thrust_on"]
            if x["same_run"]:
                out.append(f"{case} {rule}: same run {c['run']} ({c.get('thrust_on_of_that_run_s', c['value_s']):.2f} s thrust-on)")
            else:
                ok_ = c["thrust_on_of_that_run_s"] >= t_["p99_s"]
                out.append(f"{case} {rule}: published run {c['run']} ({c['thrust_on_of_that_run_s']:.2f} s thrust-on) vs run "
                           f"{t_['run']} ({t_['value_s']:.2f} s) by thrust-on; published file "
                           + ("at or above the thrust-on 99th percentile "
                              f"{t_['p99_s']:.2f} s (conservative, kept)" if ok_ else
                              f"BELOW the thrust-on 99th percentile {t_['p99_s']:.2f} s"))
    return "; ".join(out)


def pick(rows, rule):
    bt = np.array([float(r["burn_time"]) for r in rows])
    if rule == "max":
        i = int(np.argmax(bt))
        return i, float(np.percentile(bt, 99)), bt
    p99 = float(np.percentile(bt, 99))
    cand = [j for j in range(len(bt)) if bt[j] >= p99]
    i = min(cand, key=lambda j: bt[j])
    return i, p99, bt


def refly(over, i):
    over = dict(over)
    m = over.pop("m_fixed")
    cfg = R.cfg_of(**dict(over, m_n2o=float(m)))
    D = R.draw(np.random.default_rng(SEED), N, cfg)
    c, disp = R.run_cfg(cfg, D[i])
    res, rec, info = R.fly(dict(c, rec_dt=0.01), disp, nrec=8000)
    return res, rec, info, D[i], cfg


def rows_of(rec, info):
    tab = DC3.src["tab"]
    F = rec[:, I["F"]]
    Fpc = rec[:, I["Fpc"]]
    pc = np.array([_bilin(tab["Fg"], tab["Dg"], tab["pc"], f, tab["Dg"][0]) if f > 1 else 1.0e5 for f in Fpc])
    return np.column_stack([rec[:, I["t"]], F, rec[:, I["Fcmd"]], F / 500.0, rec[:, I["mox"]], rec[:, I["mf"]], pc,
                            rec[:, I["Ptank"]], rec[:, I["Ttank"]], rec[:, I["fax"]], rec[:, I["z"]] - info["zcg0"],
                            rec[:, I["vz"]], rec[:, I["m"]], rec[:, I["zcg"]], rec[:, I["It"]], rec[:, I["Ir"]],
                            rec[:, I["dcx"]], rec[:, I["dcy"]], rec[:, I["dgx"]], rec[:, I["dgy"]], rec[:, I["hinge"]],
                            rec[:, I["tilt"]], rec[:, I["phase"]]])


def main():
    os.makedirs(OUT, exist_ok=True)
    cases, jr = case_over()
    print(f"J_ref A1 {jr['A1']:.6f} B1 {jr['B1']:.6f}", flush=True)
    idx_p = os.path.join(OUT, "duty_cycles_index_v3.json")
    idx = json.load(open(idx_p))
    if idx.get("generator", "").find("m2_duty_cycles_v3") < 0:
        raise SystemExit("run m2_duty_cycles_v3 first (nominal cycles + index)")
    for c in idx["cycles"]:
        c.setdefault("kind", "nominal_seeded")
    sel = os.environ.get("GNC_DCD_TARGETS")
    targets = [t for t in TARGETS if not sel or t[0] in sel.split(",")]
    names = [t[0] for t in targets]
    idx["cycles"] = [c for c in idx["cycles"] if c["name"] not in names]
    disp_meta = []
    for name, case, rule in targets:
        over, csvp = cases[case]
        mc_rows = list(csv.DictReader(open(csvp)))
        i, p99, bt = pick(mc_rows, rule)
        res, rec, info, dr, cfg = refly(over, i)
        mrow = mc_rows[i]
        mism = [k for k in mrow if k in s6.RES_NAMES and k != "nrec" and not (float(mrow[k]) == float(res[k]) or
                                                             (np.isnan(float(mrow[k])) and np.isnan(float(res[k]))))]
        rows = rows_of(rec, info)
        t = rec[:, I["t"]]
        F = rec[:, I["F"]]
        mox, mf = rec[:, I["mox"]], rec[:, I["mf"]]
        on = (F > 1.0) & (mf > 0)
        n2o = float(np.sum(0.5 * (mox[1:] + mox[:-1]) * np.diff(t)))
        fuel = float(np.sum(0.5 * (mf[1:] + mf[:-1]) * np.diff(t)))
        of = mox[on] / mf[on]
        tags = info["tags"]
        meta = dict(name=name, kind="dispersed_envelope",
                    source=f"SIM {s6.SIM6_VERSION} 6-DOF, engine: {tags['engine_model'][1]}, dt 1 ms, recorded 10 ms; Monte Carlo "
                           f"run {i} of case {case} re-flown",
                    selection=dict(rule=("smallest burn time >= the 99th percentile of the 500 runs" if rule == "p99"
                                         else "longest burn time of the 500 runs"),
                                   rule_variable="Monte Carlo engine-on counter (sim6 burn_time; see burn_time_definition)",
                                   thrust_on_cross_check=BCHK.get(case, {}).get("selection", {}).get(rule),
                                   burn_time_p50_p99_max_of_case_s=[float(np.percentile(bt, 50)), p99, float(bt.max())],
                                   n_runs=len(bt), runs_over_19s=int(np.sum(bt > 19.0))),
                    mc_case=case, mc_csv=os.path.relpath(csvp, S), mc_seed=SEED, run_index=i, run_seed=int(dr["_seed"]),
                    reproduces_mc_row=not mism, mismatched_fields=mism[:10],
                    dispersions={k: (float(dr[k]) if dr.get(k) is not None else None) for k in
                                 ("thrust_scale", "isp_scale", "dry_scale", "m_est_err", "_wind", "_wind_dir", "_gust_scale",
                                  "_T0", "_rho0", "_t_ign", "_k_retro", "_ca_tf", "throat_g")},
                    config={k: (v if not isinstance(v, (np.floating, np.integer)) else float(v)) for k, v in over.items()},
                    throat_jref=(jr["B1"] if "B1" in case else jr["A1"]) if "pc" in case.split("_")[2] else None,
                    m_n2o_kg=float(over["m_fixed"]), tank_V_m3=info["tank_V"], m_liftoff_kg=info["m_liftoff"],
                    summary={k: float(res[k]) for k in ["landed", "td_vz", "td_vh", "td_tilt", "td_rate", "prop_used", "liq_left",
                                                        "h_max", "h_ign", "v_ign", "burn_time", "starts", "max_gim", "max_hinge",
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
                    note=("dispersed-envelope thermal input (lead 2026-10-13); FSW v2.7 with k_est_asc 2 (provisional baseline, "
                          "pending the independent GNC review); one Monte Carlo run, not a nominal flight"))
        if not meta["success"]:
            sm = meta["summary"]
            meta["note"] += (f"; this run FAILS its landing (touchdown {sm.get('td_vz', float('nan')):.1f} m/s, liquid left "
                             f"{sm.get('liq_left', float('nan')):.3f} kg vs {DC3.TRAP * meta['m_n2o_kg']:.3f} kg trapped: "
                             "propellant-limited); thrust ends at liquid depletion (no vapour-phase burn modelled)"
                             + (f" at t = {meta['thrust_end_s']:.2f} s (last record with F > 1 N); the engine-on counter runs on "
                                f"at zero thrust to the touchdown cut ({meta['engine_on_counter_s']:.2f} s)"
                                if sm.get("liq_left", 1.0) <= DC3.TRAP * meta["m_n2o_kg"] else ""))
        meta.update(DC3.axial_stats(rows, rec[:, I["legF"]]))
        if not meta["success"] and meta["max_axial_leg_force_N"] > 0.0:
            meta["note"] += (f"; max_axial_specific_mps2 ({meta['max_axial_specific_mps2']:.0f} m/s2 at t = {meta['max_axial_at_s']:.2f} s, "
                             f"thrust {meta['max_axial_thrust_N']:.0f} N, leg force {meta['max_axial_leg_force_N']:.0f} N) is the "
                             "touchdown crash impact of this failed landing in the leg spring-damper model, NOT a design load; "
                             f"airborne maximum {meta['max_axial_specific_airborne_mps2']:.1f} m/s2")
        meta = DC3.write(name, rows, meta)
        disp_meta.append(meta)
        print(f"{name:42s} run {i:3d} seed {meta['run_seed']:10d} burn {meta['burn_time_s']:6.2f} s (case p99 {p99:.2f}, max "
              f"{bt.max():.2f}) I {meta['total_impulse_Ns']:6.0f} N s N2O {n2o:.3f} kg O/F {meta['OF_overall']:.2f} Pc max "
              f"{meta['Pc_max_Pa'] / 1e5:.1f} bar ok {meta['success']} reproduces {meta['reproduces_mc_row']} "
              f"tsc {dr['thrust_scale']:.3f} dry {dr['dry_scale']:.3f} g {dr.get('throat_g')}", flush=True)
    idx["cycles"] += disp_meta
    order = {t[0]: k for k, t in enumerate(TARGETS)}
    idx["cycles"].sort(key=lambda c: (c.get("kind") == "dispersed_envelope", order.get(c["name"], -1)))
    idx["generator"] = f"{DC3.VERSION} + {VERSION}"
    idx["date"] = "2026-10-13"
    disp_meta = [c for c in idx["cycles"] if c.get("kind") == "dispersed_envelope"]
    bts = [m["burn_time_s"] for m in disp_meta]
    idx["dispersed_envelope"] = dict(
        files=[m["name"] for m in disp_meta], longest_burn_s=max(bts),
        B1_burn_p99_max_s={m["name"]: m["burn_time_s"] for m in disp_meta if m["name"].startswith("DC-B1")},
        engine_on_counter_s={m["name"]: m["engine_on_counter_s"] for m in disp_meta},
        selection_check=dict(source="m2_dc_burn_check v1 (all 500 runs of each case re-flown, thrust-on time per run)",
                             result=_sel_text(BCHK) if BCHK else "not run",
                             per_case={k: v.get("selection") for k, v in BCHK.items()},
                             thrust_on_p50_p99_max_s={k: v.get("thrust_on_p50_p99_max_s") for k, v in BCHK.items()}),
        status="thermal input for the Combustion head-end BC and the Mechanical thermal re-runs (lead 2026-10-13); DC-B1 v2 "
               "(19.0 s, nominal 100 m) is NOT conservative for dispersed B1 85 m flights and stays as history",
        evidence="gnc.json v3 throat_growth / b1_dispersed_burn (500-run Monte Carlo, seed 101)")
    idx["sizing_cases_lead_2026-10-13"] = dict(
        B1_thermal_and_erosion_sizing="DC-B1_hop_85m_disp_p99_kest2_v3",
        B1_no_failure_check="DC-B1_hop_85m_disp_max_kest2_v3",
        A1_sizing="DC-A1_full_flight_disp_p99_kest2_v3",
        throat_growth_variants=["DC-B1_hop_85m_disp_p99_kest2_tg711_v3", "DC-B1_hop_85m_disp_max_kest2_tg711_v3",
                                "DC-A1_full_flight_disp_p99_kest2_tg711_v3"],
        nominal_data_points=["DC-A1_full_flight_drogue_fins_300m_v3", "DC-B1_hop_85m_floor20_v3"],
        fsw=("v2.7 with k_est_asc 2 on both profiles (lead 2026-10-13: provisional baseline, one FSW, pending the independent "
             "GNC review). A1 paired check at 500 runs, k_est_asc 2 vs 0, no throat growth: no significant difference (pc2 "
             "basis 3 lost / 1 gained, P 0.984 vs 0.988, exact McNemar p 0.62; ENG-07d basis 2 lost / 1 gained, P 0.984 vs "
             "0.986, p 1.0); this does not show that A1 is not degraded"),
        tag="REQ lead decision 2026-10-13 (interfaces/CHANGELOG.md) on SIM m2_throat_mc v1.1")
    q = idx.get("qualification_check", {})
    if q.get("DC_D_burn_s"):
        q["ratio_to_dispersed_longest"] = q["DC_D_burn_s"] / max(bts)
        idx["qualification_check"] = q
    with open(os.path.join(OUT, "duty_cycles_index_v3.json"), "w") as f:
        json.dump(idx, f, indent=1, default=float)
    print("index", os.path.join(OUT, "duty_cycles_index_v3.json"), "cycles", [c["name"] for c in idx["cycles"]])


if __name__ == "__main__":
    main()

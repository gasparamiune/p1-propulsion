"""TVC actuator study (lead requests 2026-10-12): linkage ratio n 4.8 vs 6 with the servo pair on its torque-speed lines
through the exact Cardan kinematics (sim6 v2.5 act_model 1), fixed plug voltage or Electronics' resistive supply chain
(plug voltage sags with the servo currents).

For every actuator case in mc6_summary_v2.json (name AD_prov_act_*): success with Wilson 95 % interval, failure modes,
paired exact McNemar tests on the same draws (seed 101) against
  * AD_fins_f20  - the 0.984 baseline the lead names (RCS fitted, sized load; reference servo model, n 6, 7.4 V),
  * AD_prov_2kg  - the same vehicle (N2O 2.00 kg, no RCS) with the reference servo model (n 6, 7.4 V),
  * the n 6 case with the same supply (same actuator model; isolates the linkage ratio),
torque-saturation statistics (how often, how long, how deep), the plug-voltage minimum and servo current maximum
(sag cases), the engine-side holding moment at neutral (weakest direction) and the association of lost landings with
saturation. A case "loses" when its P is below the comparator's and the exact McNemar p < 0.05 (the rule used for the
ENG-07 slew study).
Output: GNC_RES/actuator_study_v2.json and .csv. Run after m2_mc6.py: python scripts/m2_actuator_study.py
"""
import csv
import json
import math
import os
import sys
import numpy as np
from scipy.stats import binomtest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R, sim6 as s6  # noqa: E402

OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/m2")
RES = os.environ.get("GNC_RES", "/home/claude/work/space/out/results_v2")
SUFFIX = os.environ.get("GNC_SUFFIX", "v2")
BASE = "AD_fins_f20"
LEADBASE = "AD_prov_2kg"
ALPHA = 0.05


def load_rows(case):
    p = os.path.join(OUT, f"mc6_runs_{case}_{SUFFIX}.csv")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return list(csv.DictReader(f))


def mcnemar(ra, rb):
    """Paired exact McNemar (two-sided binomial on the discordant pairs): a = comparator, b = case."""
    oa = np.array([int(r["ok"]) for r in ra]) > 0
    ob = np.array([int(r["ok"]) for r in rb]) > 0
    lost = int(np.sum(oa & ~ob))
    gained = int(np.sum(~oa & ob))
    p = binomtest(lost, lost + gained, 0.5).pvalue if lost + gained > 0 else 1.0
    return dict(P_comparator=float(oa.mean()), P_case=float(ob.mean()), lost=lost, gained=gained, mcnemar_exact_p=float(p),
                loses=bool(ob.mean() < oa.mean() and p < ALPHA))


def pct(x, q):
    return float(np.percentile(x, q)) if len(x) else float("nan")


def holding_moment(par):
    """Weakest engine-side stall moment at neutral over 360 directions at the stall-torque line of the plug voltage
    (fixed: act_Ts; sag: Ts at the HOLD plug voltage), from the same act_scale as the kernel."""
    Ts = par[s6.P_act_Ts]
    wnl = par[s6.P_act_wnl]
    m = 1e9
    for k in range(360):
        th = 2 * math.pi * k / 360
        u = (math.cos(th), math.sin(th))
        kk, _, _, _ = s6.act_scale(0.0, 0.0, 0.0, 0.0, 100.0 * u[0], 100.0 * u[1], par[s6.P_act_az1], par[s6.P_act_az2],
                                par[s6.P_act_re], par[s6.P_act_zb], par[s6.P_act_rh], Ts, wnl, Ts, wnl)
        m = min(m, 100.0 * kk)
    return m


def main():
    S = json.load(open(os.path.join(OUT, f"mc6_summary_{SUFFIX}.json")))["cases"]
    names = [c for c in S if c.startswith("AD_prov_act_")]
    base_rows = {c: load_rows(c) for c in (BASE, LEADBASE)}
    out = dict(tool="m2_actuator_study v1", sim=s6.SIM6_VERSION, alpha=ALPHA,
               rule="loses = P below the comparator and exact McNemar p < 0.05 on the same draws (seed 101)",
               comparators={BASE: "0.984 baseline (RCS fitted, sized load, reference servo model n 6 at 7.4 V)",
                            LEADBASE: "same vehicle (N2O 2.00 kg, no RCS), reference servo model n 6 at 7.4 V",
                            "n6_same_supply": "same actuator model and supply, n 6.0"},
               cases={})
    rows_csv = []
    for c in sorted(names):
        rows = load_rows(c)
        if rows is None:
            continue
        cs = S[c]
        cfg = cs["config"]
        n = float(cfg["act_n"]) if cfg.get("act_n") is not None else 6.0
        V = float(cfg["servo_V"])
        J = float(cfg.get("act_Jint") or 0.0)
        chain = cfg.get("supply_chain")
        Vrest = cfg.get("supply_Vrest")
        cfg_b = R.cfg_of(**{k: (tuple(v) if isinstance(v, list) else v) for k, v in cfg.items()})
        par = R.build(cfg_b)[0]
        if chain is not None and Vrest is not None:
            ch = R.supply_chain(chain)
            V_hold = R.hold_plug_voltage(ch, float(Vrest))
        else:
            V_hold = V
        # holding moment at the HOLD plug voltage
        par_h = par.copy()
        Ts_h, wnl_h = R.servo_line(R.sources()["el"]["actuators"]["tvc_A"], V_hold)
        par_h[s6.P_act_Ts] = Ts_h
        par_h[s6.P_act_wnl] = math.radians(wnl_h)
        hold = holding_moment(par_h)
        st = np.array([float(r["act_sat_time"]) for r in rows])
        stl = np.array([float(r["act_sat_time_land"]) for r in rows])
        ev = np.array([float(r["act_sat_events"]) for r in rows])
        md = np.array([float(r["act_sat_max_dur"]) for r in rows])
        km = np.array([float(r["act_sat_kmin"]) for r in rows])
        std = np.array([float(r["act_sat_time_td"]) for r in rows])
        hd = np.array([float(r["max_hinge_dem"]) for r in rows])
        sts = np.array([float(r.get("act_sat_time_stall", "nan")) for r in rows])
        mds = np.array([float(r.get("act_sat_max_dur_stall", "nan")) for r in rows])
        mh = np.array([float(r["max_hinge"]) for r in rows])
        bt = np.array([float(r["burn_time"]) for r in rows])
        ok = np.array([int(r["ok"]) for r in rows]) > 0
        sat = st > 0
        satd = dict(
            runs_saturated_in_flight=int(sat.sum()), frac_runs_saturated=float(sat.mean()),
            frac_runs_saturated_in_landing_burn=float((stl > 0).mean()),
            sat_time_s_all_runs=dict(p50=pct(st, 50), p90=pct(st, 90), p99=pct(st, 99), max=float(st.max())),
            sat_time_s_saturated_runs=dict(p50=pct(st[sat], 50), p90=pct(st[sat], 90), max=float(st[sat].max()) if sat.any() else 0.0),
            sat_time_landing_burn_s=dict(p99=pct(stl, 99), max=float(stl.max())),
            sat_fraction_of_burn_time=dict(p99=pct(st / np.maximum(bt, 1e-9), 99), max=float(np.max(st / np.maximum(bt, 1e-9)))),
            episodes_per_run=dict(mean=float(ev.mean()), p99=pct(ev, 99), max=float(ev.max())),
            longest_episode_s=dict(p50_saturated=pct(md[sat], 50), p99=pct(md, 99), max=float(md.max())),
            depth_kmin=dict(min=float(km.min()), p1=pct(km, 1), note="delivered / demanded moment at the deepest point (1 = unsaturated)"),
            after_touchdown=dict(frac_runs=float((std > 0).mean()), max_s=float(std.max())),
            demanded_hinge_moment_Nm=dict(p50=pct(hd, 50), p99=pct(hd, 99), max=float(hd.max()),
                                          frac_runs_above_holding=float((hd > hold).mean())),
            failed_runs_saturated=int(np.sum(~ok & sat)), failed_runs=int(np.sum(~ok)),
            delivered_hinge_moment_Nm=dict(p50=pct(mh, 50), p99=pct(mh, 99), max=float(mh.max()),
                                           note="largest per-axis linkage moment on the engine (after saturation and friction)"))
        if not np.all(np.isnan(sts)):
            satd["torque_limited"] = dict(
                note="part of the saturated time in which a servo's demand exceeds its stall torque (the rest is speed-limited "
                     "on the torque-speed line)",
                frac_runs=float((sts > 0).mean()), time_s=dict(p50=pct(sts, 50), p99=pct(sts, 99), max=float(np.max(sts))),
                longest_episode_s=dict(p99=pct(mds, 99), max=float(np.max(mds))))
        if chain is not None:
            vm = np.array([float(r["act_Vmin"]) for r in rows])
            im = np.array([float(r["act_Imax"]) for r in rows])
            satd["plug_voltage_min_V"] = dict(min=float(vm.min()), p1=pct(vm, 1), p50=pct(vm, 50))
            satd["servo_current_max_A"] = dict(max=float(im.max()), p99=pct(im, 99))
        comp = {}
        for b in (BASE, LEADBASE):
            if base_rows[b] is not None:
                comp[b] = mcnemar(base_rows[b], rows)
                oa = np.array([int(r["ok"]) for r in base_rows[b]]) > 0
                lost_idx = np.where(oa & ~ok)[0]
                comp[b]["lost_runs_saturated"] = int(np.sum(sat[lost_idx]))
                comp[b]["lost_runs_sat_time_s"] = [round(float(st[i]), 4) for i in lost_idx]
                comp[b]["lost_run_ids"] = [int(i) for i in lost_idx]
        # same-supply n 6 counterpart
        twin = None
        if abs(n - 6.0) > 1e-9:
            for c2 in names:
                cf2 = S[c2]["config"]
                if (cf2.get("act_n") is None and abs(float(cf2["servo_V"]) - V) < 1e-9 and float(cf2.get("act_Jint") or 0) == J
                        and cf2.get("supply_chain") == chain and cf2.get("supply_Vrest") == Vrest):
                    twin = c2
            if twin is not None and load_rows(twin) is not None:
                comp["n6_same_supply"] = dict(mcnemar(load_rows(twin), rows), case=twin)
        fm = cs["summary"]["fail_modes"]
        rec = dict(case=c, note=cs["note"], n=n, servo_V=V, V_hold_plug=V_hold, supply_chain=chain, supply_Vrest=Vrest,
                   J_int_servo_kgm2=J, holding_moment_neutral_weakest_Nm=hold,
                   engine_noload_rate_neutral_dps=wnl_h / n,
                   P=float(ok.mean()), ci95=list(R.wilson(int(ok.sum()), len(ok))), fail_modes=fm,
                   td_vh_p99=cs["summary"]["td_vh_p99"], td_tilt_p99=cs["summary"]["td_tilt_p99"],
                   td_rate_p99=cs["summary"]["td_rate_p99"], saturation=satd, paired=comp, sim=cs["sim"])
        out["cases"][c] = rec
        row = dict(case=c, n=n, V=V, V_hold=round(V_hold, 3), chain=chain or "fixed", J=J, hold_Nm=round(hold, 2),
                   P=round(rec["P"], 3), ci_lo=round(rec["ci95"][0], 3), ci_hi=round(rec["ci95"][1], 3),
                   sat_frac=round(satd["frac_runs_saturated"], 3), sat_p99_s=round(satd["sat_time_s_all_runs"]["p99"], 4),
                   sat_max_s=round(satd["sat_time_s_all_runs"]["max"], 4), longest_max_s=round(satd["longest_episode_s"]["max"], 4),
                   kmin=round(satd["depth_kmin"]["min"], 3), hinge_dem_p99=round(satd["demanded_hinge_moment_Nm"]["p99"], 2),
                   hinge_dem_max=round(satd["demanded_hinge_moment_Nm"]["max"], 2),
                   hinge_del_p99=round(satd["delivered_hinge_moment_Nm"]["p99"], 2), hinge_del_max=round(satd["delivered_hinge_moment_Nm"]["max"], 2),
                   stall_frac=(round(satd["torque_limited"]["frac_runs"], 3) if "torque_limited" in satd else None),
                   stall_p99_s=(round(satd["torque_limited"]["time_s"]["p99"], 4) if "torque_limited" in satd else None),
                   stall_max_s=(round(satd["torque_limited"]["time_s"]["max"], 4) if "torque_limited" in satd else None))
        for b, lab in ((BASE, "base"), (LEADBASE, "prov"), ("n6_same_supply", "n6")):
            if b in comp:
                row[f"{lab}_lost"] = comp[b]["lost"]
                row[f"{lab}_gained"] = comp[b]["gained"]
                row[f"{lab}_p"] = round(comp[b]["mcnemar_exact_p"], 4)
                row[f"{lab}_loses"] = comp[b]["loses"]
        rows_csv.append(row)
        print(f"{c:34s} hold {hold:5.2f} P {rec['P']:.3f} [{rec['ci95'][0]:.3f},{rec['ci95'][1]:.3f}] sat {satd['frac_runs_saturated']:.3f} "
              f"t99 {satd['sat_time_s_all_runs']['p99']:.3f} tmax {satd['sat_time_s_all_runs']['max']:.3f} "
              + " ".join(f"{b[:6]}: -{comp[b]['lost']}/+{comp[b]['gained']} p {comp[b]['mcnemar_exact_p']:.3g}{' LOSES' if comp[b]['loses'] else ''}"
                         for b in comp), flush=True)
    keys = []
    for r in rows_csv:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(os.path.join(RES, "actuator_study_v2.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows_csv)
    with open(os.path.join(RES, "actuator_study_v2.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("written", os.path.join(RES, "actuator_study_v2.json"))


if __name__ == "__main__":
    main()

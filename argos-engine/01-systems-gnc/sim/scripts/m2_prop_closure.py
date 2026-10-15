"""m2_prop_closure v1.1 (2026-10-12; v1.1: GNC_PC_RATCHET=1 adds the reference-governor ratchet att_ref_mode 1 to
the flight software of every cycle): N2O closure of the flight duty cycles on the published engine (lead request
2026-10-12, high priority: Combustion OI-1 says the gnc.json v2 cycles A2 / B1 need 2.54 / 2.44 kg against the 2.00 kg
tank; delivered Isp ~188-193 s).

Flights: sim6/run6 v2.6 6-DOF on the interface set in GNC_IFACE (combustion.json v2.x published map; mechanical.json v1
+ the S230 growth until mechanical.json v2 is published), flight software v2.6 (gimbal tracker + reference governor,
lift-ramp shutdown, 72 % pre-MECO throttle-down, relight start rule) and the NC-valve-closed relight timeline (sequence
time from combustion.json added to the start delay and to the relight planning value; relight 90 % thrust 0.29 s after
the torch per combustion.json igniter.model_transients = run6 nominal). RCS not fitted (lead: provision only).
  DC-A1  A-D 300 m, nose drogue + aft fins (lead baseline mission)
  DC-A2  A-F 300 m free fall, finless, TVC flip (descent-envelope flight)
  DC-B1  B continuous-burn hop 100 m, 20 % floor;  DC-B2 the 50 m hop (reference)
Closure rule (lead '+25 % reserve'): on the nominal flight (no wind, no sensor noise) the USABLE liquid N2O left at
touchdown must be >= 25 % of the N2O burned; usable = liquid left - trapped liquid (3 % of the load, ASSUMED as in
gnc.json v2). Equivalently load >= 1.25 x burned + vapour left in the tank + trapped liquid. N2O burned = integral of
the injector N2O flow; vapour left = load - burned - liquid left (self-pressurised tank, no RCS draw).
'Needed' = smallest load meeting the rule (tank volume sized with the load at 85 % liquid fill at 25 C, tank mass
scaled with it by the RV-1c ledger). The gnc.json v2 rule (usable >= 20 % of propellant used, sized load x 1.15) is
reported next to it for continuity with Combustion's OI-1 numbers.
Parts (env GNC_PC_PART, default all): nominal = closure table at 2.00 kg + needed loads + trade sweeps (B1 hop height,
A2 apogee, A1 apogee, floors, larger tank); mc = 500-run Monte Carlo (seed 101, same draws as every case) at 2.00 kg and
at the closing loads / mission changes. Env: GNC_OUT (default out/prop_closure), GNC_SUFFIX (default pc),
GNC_RESERVE (0.25), GNC_PC_CASES (mc case list).
Output: <out>/prop_closure_<suf>.json (+ mc6_summary_<suf>.json, mc6_runs_<case>_<suf>.csv)"""
import json
import os
import sys
import time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("GNC_OUT", "/home/claude/work/space/out/prop_closure")
os.environ.setdefault("GNC_SUFFIX", "pc")
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_mc6 as M  # noqa: E402
import m2_meco_mc as MM  # noqa: E402  (NC-closed relight sequence time from combustion.json)

OUT = os.environ["GNC_OUT"]
SUF = os.environ["GNC_SUFFIX"]
PART = os.environ.get("GNC_PC_PART", "all")
RESERVE = float(os.environ.get("GNC_RESERVE", "0.25"))
TRAP = 0.03                 # ASSUMED trapped liquid fraction of the load (gnc.json v2 residual_liquid_frac)
M_TANK = 2.00               # REQ lead decision 2026-10-12: N2O load 2.00 kg in 3.17 L
G0 = 9.80665
RAT = dict(att_ref_mode=1) if os.environ.get("GNC_PC_RATCHET", "0") == "1" else {}   # v1.1
FSW = dict(gim_cmd_acc=2000.0, att_ref_rate=40.0, toff_model=1, meco_td=0.72, relight_start=0.20, **RAT)
NC = dict(t_ign_add=MM.NCS["slots"], t_ign_est=R.DEF["t_ign_est"] + MM.NCS["slots"])
DC = {
    "A1": dict(profile="A-D", fins=True, rcs=False, floor=0.20, **FSW, **NC),
    "A2": dict(profile="A-F", fins=False, rcs=False, floor=0.20, **FSW, **NC),
    "B1": dict(profile="B", fins=False, rcs=False, floor=0.20, gim_cmd_acc=2000.0, att_ref_rate=40.0, toff_model=1, **RAT),
    "B2": dict(profile="B", fins=False, rcs=False, floor=0.20, h_target=50.0, gim_cmd_acc=2000.0, att_ref_rate=40.0,
               toff_model=1, **RAT),
}
I = {n: i for i, n in enumerate(s6.REC_NAMES)}


def nominal(over, m):
    """Nominal flight (no wind, no noise) at load m: closure quantities."""
    cfg = R.cfg_of(**dict(over, m_n2o=m))
    res, rec, info = R.fly(dict(cfg, noise=False, wind=0.0, gust=False, rec_dt=0.01), nrec=20000)
    t = rec[:, I["t"]]
    burned = float(np.sum(0.5 * (rec[1:, I["mox"]] + rec[:-1, I["mox"]]) * np.diff(t)))
    F = rec[:, I["F"]]
    imp = float(np.sum(0.5 * (F[1:] + F[:-1]) * np.diff(t)))
    liq = float(res["liq_left"])
    usable = liq - TRAP * m
    land = rec[-1, I["m"]]
    return dict(m_n2o=m, tank_V_L=info["tank_V"] * 1e3, m_liftoff=info["m_liftoff"], TW_liftoff=500.0 / (info["m_liftoff"] * G0),
                m_end=float(land), floor_over_W_end=float(over.get("floor", 0.2) * 500.0 / (land * G0)),
                landed_ok=R.success(res), exhausted=bool(res["exhausted"] > 0.5), n2o_burned=burned,
                fuel_burned=float(res["prop_used"]) - burned, liquid_left=liq, vapour_left=m - burned - liq,
                trapped=TRAP * m, usable_left=usable, reserve_frac=usable / burned if burned > 0 else float("nan"),
                closes=bool(R.success(res) and usable >= RESERVE * burned), impulse_Ns=imp, burn_time_s=float(res["burn_time"]),
                isp_delivered_s=imp / (float(res["prop_used"]) * G0) if res["prop_used"] > 0 else float("nan"),
                h_max=float(res["h_max"]), h_ign=float(res["h_ign"]), v_ign=float(res["v_ign"]), td_vz=float(res["td_vz"]),
                td_vh=float(res["td_vh"]), starts=int(res["starts"]))


def needed(over, lo=1.0, hi=4.0, iters=18):
    """Smallest load meeting the reserve rule on the nominal flight (bisection; None if hi does not close)."""
    if not nominal(over, hi)["closes"]:
        return None, None
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if nominal(over, mid)["closes"]:
            hi = mid
        else:
            lo = mid
    return hi, nominal(over, hi)


def v2_rule(over):
    """gnc.json v2 sizing (usable >= 20 % of ox + fuel used, then x 1.15), for continuity with OI-1."""
    ms, _ = R.size_load(R.cfg_of(**over))
    return None if ms is None else ms * 1.15


def max_param_closing(over, key, lo, hi, iters=12, m=M_TANK):
    """Largest value of cfg[key] in [lo, hi] for which the load m closes (bisection; assumes closure falls with key)."""
    if not nominal(dict(over, **{key: lo}), m)["closes"]:
        return None
    if nominal(dict(over, **{key: hi}), m)["closes"]:
        return hi
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if nominal(dict(over, **{key: mid}), m)["closes"]:
            lo = mid
        else:
            hi = mid
    return lo


def rnd(x, n=4):
    if isinstance(x, dict):
        return {k: rnd(v, n) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [rnd(v, n) for v in x]
    if isinstance(x, (float, np.floating)):
        return float(round(float(x), n)) if np.isfinite(x) else None
    return x


def part_nominal(out):
    t0 = time.time()
    tab = {}
    for k, over in DC.items():
        at2 = nominal(over, M_TANK)
        mn, nm = needed(over)
        tab[k] = dict(config=over, at_2kg=at2, needed_kg=mn, at_needed=nm, v2_rule_kg=v2_rule(over),
                      closes_at_2kg=at2["closes"])
        print(f"{k}: at 2.00 kg burned {at2['n2o_burned']:.3f} liq {at2['liquid_left']:.3f} vap {at2['vapour_left']:.3f} "
              f"usable {at2['usable_left']:.3f} reserve {100 * at2['reserve_frac']:.1f} % closes {at2['closes']} landed "
              f"{at2['landed_ok']} | Isp {at2['isp_delivered_s']:.1f} s I {at2['impulse_Ns']:.0f} N s burn {at2['burn_time_s']:.2f} s"
              f" | needed (+{100 * RESERVE:.0f} %) {mn if mn is None else round(mn, 3)} kg "
              f"(V {nm['tank_V_L'] if nm else float('nan'):.2f} L) | v2 rule {tab[k]['v2_rule_kg']:.3f} kg ({time.time() - t0:.0f}s)",
              flush=True)
    out["closure"] = tab
    # ---------------------------------------------------------------- trades
    tr = {}
    # (a) mission: B hop height, A2 apogee, A1 apogee that close at 2.00 kg; sweeps for the curves
    sw = {}
    for k, key, vals in (("B1", "h_target", (100.0, 90.0, 80.0, 75.0, 70.0, 60.0, 50.0)),
                         ("A2", "h_target", (300.0, 275.0, 250.0, 225.0, 200.0, 175.0, 150.0)),
                         ("A1", "h_target", (300.0, 275.0, 250.0, 225.0, 200.0))):
        rows = []
        for v in vals:
            ov = dict(DC[k], **{key: v})
            a = nominal(ov, M_TANK)
            mn, _ = needed(ov)
            rows.append(dict(value=v, reserve_frac_at_2kg=a["reserve_frac"], closes_at_2kg=a["closes"], landed=a["landed_ok"],
                             n2o_burned=a["n2o_burned"], needed_kg=mn, h_max=a["h_max"], burn_time_s=a["burn_time_s"]))
        sw[f"{k}_{key}"] = rows
        hmax = max_param_closing(DC[k], key, min(vals), max(vals))
        tr[f"{k}_max_{key}_closing_at_2kg_m"] = hmax
        print(f"sweep {k} {key}: " + " ".join(f"{r['value']:.0f}:{100 * r['reserve_frac_at_2kg']:.0f}%/{r['needed_kg'] or float('nan'):.2f}kg"
                                              for r in rows) + f" | max closing {hmax} ({time.time() - t0:.0f}s)", flush=True)
    tr["sweeps"] = sw
    # (c) floor variants for the hop and the full flights (12.5 % stretch floor, 25 % requirement floor)
    fl = {}
    for k in ("A1", "A2", "B1"):
        for f in (0.125, 0.25):
            ov = dict(DC[k], floor=f)
            a = nominal(ov, M_TANK)
            mn, _ = needed(ov)
            fl[f"{k}_floor{f:g}"] = dict(reserve_frac_at_2kg=a["reserve_frac"], closes_at_2kg=a["closes"], landed=a["landed_ok"],
                                         n2o_burned=a["n2o_burned"], needed_kg=mn)
            print(f"floor {k} {f:g}: reserve {100 * a['reserve_frac']:.1f} % burned {a['n2o_burned']:.3f} needed {mn}", flush=True)
    tr["floors"] = fl
    # (b) larger tank: the closing load of each cycle and the consequences at that load (nominal)
    big = {}
    for k in ("A1", "A2", "B1"):
        mn = tab[k]["needed_kg"]
        if mn is None:
            continue
        mcl = max(mn, M_TANK)
        big[k] = dict(closing_load_kg=mcl, at_load=nominal(DC[k], mcl),
                      other_cycles_at_this_load={kk: nominal(DC[kk], mcl)["reserve_frac"] for kk in ("A1", "A2", "B1")})
    tr["larger_tank"] = big
    out["trades"] = tr
    out["cpu_s_nominal"] = time.time() - t0


def mc_cases(out):
    """Monte Carlo cases: each cycle at 2.00 kg, at the load that closes the worst cycle, and the mission changes."""
    cl = out.get("closure", {})
    tr = out.get("trades", {})
    worst = max((cl[k]["needed_kg"] or 0.0) for k in ("A1", "A2", "B1")) if cl else None
    cases = {}
    for k in ("A1", "A2", "B1"):
        cases[f"pc_{k}_2kg"] = (dict(DC[k], m_fixed=M_TANK), f"DC-{k} configuration, lead tank 2.00 kg")
        if worst and worst > M_TANK:
            cases[f"pc_{k}_m{worst:.2f}"] = (dict(DC[k], m_fixed=round(worst, 3)), f"DC-{k} configuration, tank closing the worst "
                                                                                 f"cycle ({worst:.3f} kg)")
    hb = tr.get("B1_max_h_target_closing_at_2kg_m")
    if hb and hb < 100.0:
        hb_ = float(np.floor(hb / 5.0) * 5.0)          # round mission numbers: hop height in 5 m steps
        cases[f"pc_B1_h{hb_:.0f}_2kg"] = (dict(DC["B1"], h_target=hb_, m_fixed=M_TANK), f"B hop {hb_:.0f} m (closes at 2.00 kg)")
    ha = tr.get("A2_max_h_target_closing_at_2kg_m")
    if ha and ha < 300.0:
        ha_ = float(np.floor(ha / 10.0) * 10.0)        # apogee in 10 m steps
        cases[f"pc_A2_h{ha_:.0f}_2kg"] = (dict(DC["A2"], h_target=ha_, m_fixed=M_TANK), f"A-F from {ha_:.0f} m (closes at 2.00 kg)")
    fl = tr.get("floors", {}).get("B1_floor0.125")
    if fl and fl.get("closes_at_2kg"):
        cases["pc_B1_f125_2kg"] = (dict(DC["B1"], floor=0.125, m_fixed=M_TANK), "B hop 100 m on the 12.5 % floor (closes at 2.00 kg)")
    return cases


def part_mc(out):
    cases = mc_cases(out)
    sel = os.environ.get("GNC_PC_CASES")
    names = [c for c in (sel.split(",") if sel else cases) if c in cases]
    p_sum = os.path.join(OUT, f"mc6_summary_{SUF}.json")
    allsum = json.load(open(p_sum))["cases"] if os.path.exists(p_sum) else {}
    for name in names:
        over, note = cases[name]
        o, rows = M.run_case(name, over, note)
        allsum[name] = o
        M.write_csv(os.path.join(OUT, f"mc6_runs_{name}_{SUF}.csv"), rows)
        s = o["summary"]
        liq = np.array([r["liq_left"] for r in rows])
        o["liq_left_p01_min"] = [float(np.percentile(liq, 1)), float(liq.min())]
        print(f"{name:20s} P {s['success']:.3f} [{s['ci95'][0]:.3f},{s['ci95'][1]:.3f}] fails {s['fail_modes']} liq p01 "
              f"{o['liq_left_p01_min'][0]:.3f} min {o['liq_left_p01_min'][1]:.3f} m_liftoff {o['m_liftoff_kg']:.2f} ({o['cpu_s']:.0f}s)",
              flush=True)
        with open(p_sum, "w") as f:
            json.dump(dict(version=f"m2_prop_closure v1.1 {SUF}", sim=s6.SIM6_VERSION, n=M.N, cases=allsum), f, indent=1, default=float)
    out["mc_cases"] = {c: dict(note=allsum[c]["note"], P=allsum[c]["summary"]["success"], ci95=allsum[c]["summary"]["ci95"],
                               fail_modes=allsum[c]["summary"]["fail_modes"], m_n2o_kg=allsum[c]["m_n2o_mc_kg"],
                               m_liftoff_kg=allsum[c]["m_liftoff_kg"], tank_V_L=allsum[c]["tank_V_L"],
                               liq_left_p01_min_kg=allsum[c].get("liq_left_p01_min"))
                       for c in allsum}


def main():
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f"prop_closure_{SUF}.json")
    out = json.load(open(path)) if os.path.exists(path) and PART == "mc" else {}
    src = R.sources()
    out.update(version=f"m2_prop_closure v1.1 {SUF}", date=time.strftime("%Y-%m-%d"), sim=s6.SIM6_VERSION,
               interfaces={k: src[k].get("version") if src.get(k) else None for k in ("comb", "mech", "el")},
               iface=R.IFACE, rule=dict(reserve_frac_of_n2o_burned=RESERVE, trapped_liquid_frac_of_load=TRAP,
                                        text="usable liquid at touchdown (nominal flight) >= reserve x N2O burned; "
                                             "load = burned + liquid left + vapour left"),
               lead_tank=dict(m_n2o_kg=M_TANK, tank_V_L=R.build(R.cfg_of(**dict(DC["A1"], m_n2o=M_TANK)))[5]["tank_V"] * 1e3),
               nc_relight=dict(sequence_s=MM.NCS["slots"], planning_value_s=NC["t_ign_est"], source=MM.NCS["source"]),
               flight_software=FSW)
    if PART in ("all", "nominal"):
        part_nominal(out)
        with open(path, "w") as f:
            json.dump(rnd(out), f, indent=1, default=float)
    if PART in ("all", "mc"):
        part_mc(out)
    with open(path, "w") as f:
        json.dump(rnd(out), f, indent=1, default=float)
    print("wrote", path)


if __name__ == "__main__":
    main()

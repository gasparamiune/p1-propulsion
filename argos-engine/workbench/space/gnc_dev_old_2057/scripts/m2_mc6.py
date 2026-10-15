"""M2 6-DOF Monte Carlo cases (sim6 v2.5, run6 v2.5; with act_model 0 bit-identical to sim6 v2.4; vehicle RV-1c ledger v3c, combustion v2 relay engine model,
unless a case says otherwise).

For each case: size the N2O load on the deterministic nominal 6-DOF flight (20 % reserve), fly
N dispersed runs (brief C.7 dispersions + mechanical.json ranges, run6.draw) at the sized load x LOAD_MARGIN,
record every run, summarise (success vs vz <= 2, vh <= 0.5, tilt <= 5 deg, rate <= 10 deg/s, no exhaustion,
no tip-over, Wilson 95 % interval), success by wind bin, and rank sensitivities (Spearman).

Baseline (gnc.json v2): A-D, aft fins, 20 % floor, ADIS16470, standalone GNSS, LiDAR 40 m, PD lateral + reference/PI
vertical, lateral disturbance feed-forward, 8 m terminal gate, 4.5 deg terminal tilt, 2nd-order 50 rad/s command
filter, 100 deg/s command slew limit, flexible engine mount (mechanical.json stiffness range), roll RCS on,
engine = combustion.json v1 map x combustion v2 relay factors (S230 straight port), residual roll torque
U(-0.02, 0.02) N m ASSUMED.

Env: GNC_MC_N (default 500), GNC_CASES (comma list, default all), GNC_SUFFIX (default v2),
GNC_OUT (default /home/claude/work/space/out/m2). Run: nice -n 10 python scripts/m2_mc6.py
"""
import csv
import json
import os
import sys
import time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R, sim6 as s6  # noqa: E402

OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/m2")
os.makedirs(OUT, exist_ok=True)
N = int(os.environ.get("GNC_MC_N", "500"))
SUFFIX = os.environ.get("GNC_SUFFIX", "v2")
LOAD_MARGIN = float(os.environ.get("GNC_LOAD_MARGIN", "1.15"))
UPWIND_K = 1.5          # DESIGN ascent bias velocity = -k x measured pad wind (m/s per m/s)
WIND_MEAS = (1.0, np.radians(15.0))   # ASSUMED pad anemometer error 1 sigma: speed [m/s], direction [rad]


def upwind_bias(c, dr):
    """Upwind ascent bias from a pad wind measurement with error (seeded from the run seed)."""
    rng = np.random.default_rng(int(dr["_seed"]) + 17)
    W = max(dr["_wind"] + rng.normal(0.0, WIND_MEAS[0]), 0.0)
    d = dr["_wind_dir"] + rng.normal(0.0, WIND_MEAS[1])
    return (-UPWIND_K * W * np.cos(d), -UPWIND_K * W * np.sin(d))


def hover_ballast(floor, margin_kg=0.3):
    """Ballast so that the floor thrust is <= 0.9 x landing weight (hover rule), from the nominal flight."""
    cfg = R.cfg_of(profile="A-D", fins=True, floor=0.20)
    m, res = R.size_load(cfg)
    m_land = res["m_land"]
    need = floor * 500.0 / (0.9 * R.G0) - m_land
    return max(0.0, need + margin_kg), m_land


BASE = dict(profile="A-D", fins=True, floor=0.20)
# case name -> (config overrides, note)
CASES = {
    "AD_fins_f20": (dict(BASE), "BASELINE: RV-1c A-D + aft fins, 20 % floor, ADIS16470, PD lateral, roll RCS"),
    "AD_nofins_f20": (dict(BASE, fins=False), "A-D finless (coast attitude)"),
    "AD_fins_f125": (dict(BASE, floor=0.125), "stretch floor 12.5 %"),
    "AD_fins_f25": (dict(BASE, floor=0.25), "requirement floor 25 % (auto hover/hoverslam)"),
    "AD_fins_f40": (dict(BASE, floor=0.40), "40 % floor (auto -> hoverslam)"),
    "AD_fins_f20_hslam": (dict(BASE, hslam=True), "forced Falcon-9-style hoverslam at 20 %"),
    "AD_fins_f40_ballast": (dict(BASE, floor=0.40, hslam=False, ballast="auto"), "40 % floor, hover with ballast"),
    "AD_fins_f25_ballast": (dict(BASE, floor=0.25, hslam=False, ballast="auto"), "25 % floor, hover with ballast"),
    "AD_fins_f20_BMI088": (dict(BASE, imu="BMI088"), "cheaper IMU class (BMI088)"),
    "AD_fins_f20_ICM42688": (dict(BASE, imu="ICM42688"), "cheaper IMU class (ICM-42688-P)"),
    "AD_fins_f20_rtk": (dict(BASE, gnss="rtk"), "RTK GNSS"),
    "AD_fins_f20_lidar12": (dict(BASE, lidar_range=12.0), "short-range LiDAR (12 m)"),
    "AD_fins_f20_zemzev": (dict(BASE, lat_mode=1, vert_mode=1), "ZEM/ZEV vertical (sim6 v2.3 tgo law) + lateral"),
    "AD_fins_f20_zemzev_lat": (dict(BASE, lat_mode=1), "reference+PI vertical, ZEM/ZEV lateral"),
    "AD_fins_f20_cvx": (dict(BASE, lat_mode=2), "reference+PI vertical, convex-lite lateral"),
    "AD_fins_f20_norcs": (dict(BASE, rcs=False), "no roll control, straight-port residual roll torque U(-0.02, 0.02) N m ASSUMED"),
    "AD_fins_f20_norcs_r0": (dict(BASE, rcs=False, roll_amp=0.0), "no roll control, zero engine roll torque (gimbal x CG-offset roll only)"),
    "AD_fins_f20_norcs_r005": (dict(BASE, rcs=False, roll_amp=0.005), "no roll control, roll torque U(-0.005, 0.005) N m"),
    "AD_fins_f20_norcs_r01": (dict(BASE, rcs=False, roll_amp=0.01), "no roll control, roll torque U(-0.01, 0.01) N m"),
    "AD_fins_f20_norcs_r05": (dict(BASE, rcs=False, roll_amp=0.05), "no roll control, roll torque U(-0.05, 0.05) N m"),
    "AD_fins_f20_norcs_r10": (dict(BASE, rcs=False, roll_amp=0.10), "no roll control, v1 helical-port envelope U(-0.1, 0.1) N m"),
    "AD_fins_f20_r10": (dict(BASE, roll_amp=0.10), "roll RCS on, v1 helical-port envelope U(-0.1, 0.1) N m"),
    "AD_fins_f20_v1engine": (dict(BASE, engine="v1"), "combustion.json v1 map without the relay correction, v1 grain, no engine growth"),
    "AD_fins_f20_norcs_r03": (dict(BASE, rcs=False, roll_amp=0.03), "no roll control, roll torque U(-0.03, 0.03) N m"),
    "AD_fins_f20_norcs_r04": (dict(BASE, rcs=False, roll_amp=0.04), "no roll control, roll torque U(-0.04, 0.04) N m"),
    "AD_fins_f20_rate80": (dict(BASE, gim_cmd_rate=80.0), "command slew limit 80 deg/s (rate requirement comparator)"),
    "AD_fins_f20_bw8": (dict(BASE, gim_wn_hz=8.0), "actuator natural frequency fixed at 8 Hz (ENG-07 bandwidth)"),
    "AD_fins_f20_bw6": (dict(BASE, gim_wn_hz=6.0), "actuator natural frequency fixed at 6 Hz (below ENG-07)"),
    "AD_fins_f20_slowPc": (dict(BASE, tau=0.20 / 2.197), "thrust response t10-90 0.20 s nominal (MC 0.14-0.30 s)"),
    "AD_fins_f20_q2": (dict(BASE, quant=0.02), "throttle command resolution 2 % (ENG-03 limit)"),
    # lead decisions 2026-10-12: N2O 2.00 kg / 3.17 L baseline; roll RCS provision only (hardware not fitted)
    "AD_prov_2kg": (dict(BASE, rcs=False, m_fixed=2.00),
                    "LEAD BASELINE 2026-10-12: roll RCS provision only (not fitted), N2O load fixed 2.00 kg (3.17 L), "
                    "residual roll torque U(-0.02, 0.02) N m ASSUMED"),
    "AD_fins_f20_openloop": (dict(BASE, fuel_phi=0.1, tau_fuel=0.5), "open-loop pintle (fuel lag per combustion.json plant)"),
    "AD_fins_f20_nolpf": (dict(BASE, gim_lpf_w=0.0, gim_cmd_rate=0.0), "no structural filter / slew limit (CSI comparator)"),
    "AD_fins_f20_rate60": (dict(BASE, gim_cmd_rate=60.0), "command slew limit 60 deg/s (rate requirement comparator)"),
    "AD_fins_f20_gim6": (dict(BASE, gim_max_deg=6.0), "gimbal vector limit 6 deg (7 deg decision)"),
    "AD_fins_f20_gim5": (dict(BASE, gim_max_deg=5.0), "gimbal vector limit 5 deg (7 deg decision)"),
    "AD_fins_f20_upwind": (dict(BASE, ascent_bias_auto=upwind_bias),
                           f"upwind ascent bias {UPWIND_K} x pad wind (meas. error 1 m/s, 15 deg)"),
    "AD_fins_f20_RV1b": (dict(BASE, vehicle="RV-1b"), "pre-mechanical vehicle RV-1b (126 mm, ledger engine), same GNC"),
    "AF_nofins_f20": (dict(profile="A-F", fins=False, floor=0.20), "A-F free fall, TVC flip, relight ~140 m"),
    "B_f20": (dict(profile="B", fins=False, floor=0.20), "continuous-burn hop 100 m"),
    "B_f25": (dict(profile="B", fins=False, floor=0.25), "continuous-burn hop 100 m, 25 % floor"),
    "B_f125": (dict(profile="B", fins=False, floor=0.125), "continuous-burn hop 100 m, 12.5 % floor"),
}
# lead requests 2026-10-12 (n 4.8 decision, provisional; 6.6 V governing): torque/speed-limited servo pair on the
# SB-2292SG torque-speed line mapped through the exact Cardan kinematics (sim6 v2.5 act_model 1), on the lead baseline
# (N2O 2.00 kg, RCS provision only). Supply: fixed plug voltage V for the whole flight, or a resistive chain from
# Electronics calc/tvc_supply_budget_v1 (sag: the plug voltage falls with the servo currents; V is then the plug voltage
# with both servos at stall, HOLD, unless a rest voltage is given).
# Names: AD_prov_act_n<10 n>_<V with 'V' for the point>[_J<J_int in 1e-3 kg m2>][_sag<chain>|_rest<V>_sag<chain>].
ACT_NOTE = ("LEAD BASELINE (N2O 2.00 kg, no RCS) + torque/speed-limited servo pair through the Cardan kinematics "
            "(sim6 v2.5 act_model 1)")
ACT_CHAINS = {"D": "v2.2_as_drawn/typ/15", "D+": "v2.2_as_drawn/max/15", "3": "v2.3_proposal/typ/15", "B": "basis_SIL_v2.2/typ/None"}


def _vtag(V):
    t = f"{V:.2f}".rstrip("0").rstrip(".")
    return t.replace(".", "V") if "." in t else t + "V0"


def _act_case(n, V, J=0.0, chain=None, Vrest=None):
    tag = f"AD_prov_act_n{int(round(n * 10)):02d}_{_vtag(V) if Vrest is None else 'rest' + _vtag(Vrest)}"
    tag += (f"_J{J * 1e3:g}" if J else "") + (f"_sag{chain.replace('+', 'max')}" if chain else "")
    over = dict(BASE, rcs=False, m_fixed=2.00, act_model=1, servo_V=V, act_n=(None if n == 6.0 else n), act_Jint=J,
                supply_chain=(ACT_CHAINS[chain] if chain else None), supply_Vrest=Vrest)
    if chain is None:
        sup = f"fixed plug voltage {V:.2f} V"
    elif Vrest is None:
        sup = f"supply chain {ACT_CHAINS[chain]} with {V:.2f} V at the plug when both servos stall (sag model)"
    else:
        sup = f"supply chain {ACT_CHAINS[chain]} from a rest voltage of {Vrest:.2f} V (sag model)"
    note = f"{ACT_NOTE}: n {n:.1f}, {sup}" + (f", reflected servo inertia J_int {J:g} kg m2 (Electronics SIL ASSUMED)"
                                               if J else ", J_int not modelled")
    return tag, (over, note)


for _a in ((6.0, 7.4), (6.0, 7.6), (4.8, 7.6), (4.8, 6.6), (6.0, 6.6),
           (4.8, 6.6, 0.0, "D"), (6.0, 6.6, 0.0, "D"), (4.8, 6.6, 0.0, "D", 8.1),
           (4.8, 6.6, 2e-3), (6.0, 6.6, 2e-3), (4.8, 6.6, 2e-3, "D"), (6.0, 6.6, 2e-3, "D"),
           (4.8, 7.6, 2e-3), (6.0, 7.6, 2e-3),
           (4.8, 7.25), (6.0, 7.25), (4.8, 7.25, 0.0, "3"), (6.0, 7.25, 0.0, "3"),
           (4.8, 6.86), (4.8, 7.0), (4.8, 7.4), (4.8, 6.0), (4.8, 6.0, 0.0, "D"),
           (4.8, 6.6, 1e-3, "D"), (4.8, 6.6, 4e-3, "D"), (6.0, 6.6, 1e-3, "D"), (6.0, 6.6, 4e-3, "D"),
           (5.0, 7.25), (5.2, 7.25), (5.4, 7.25), (5.6, 7.25),
           (5.0, 6.6), (5.2, 6.6), (5.4, 6.6), (5.6, 6.6),
           (5.0, 6.6, 0.0, "D"), (5.2, 6.6, 0.0, "D"), (5.4, 6.6, 0.0, "D"), (5.6, 6.6, 0.0, "D")):
    _k, _v = _act_case(*_a)
    CASES[_k] = _v


def write_csv(path, rows):
    keys = []
    for x in rows:
        for k in x:
            if k not in keys:
                keys.append(k)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for x in rows:
            w.writerow(x)


def wind_bins(rows, edges=(0.0, 2.0, 4.0, 6.0, 7.0, 8.0)):
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        sel = [r for r in rows if a <= r["wind"] < b]
        k = sum(r["ok"] for r in sel)
        out.append(dict(wind_lo=a, wind_hi=b, n=len(sel), success=(k / len(sel)) if sel else None,
                        ci95=R.wilson(k, len(sel)) if sel else None))
    return out


def run_case(name, over, note, seed=101):
    t0 = time.time()
    over = dict(over)
    ballast_info = None
    if over.get("ballast") == "auto":
        b, m_land = hover_ballast(over["floor"])
        over["ballast"] = b
        ballast_info = dict(ballast_kg=b, m_land_nominal_without_ballast=m_land,
                            rule="floor x 500 N <= 0.9 x landing weight, + 0.3 kg margin")
    m_fixed = over.pop("m_fixed", None)
    cfg = R.cfg_of(**over)
    m_sized, res_nom = R.size_load(cfg)
    if m_sized is None:
        return dict(case=name, note=note, closes=False, nominal=dict((k, float(v)) for k, v in res_nom.items())), []
    m_mc = m_sized * LOAD_MARGIN if m_fixed is None else float(m_fixed)
    cfg = R.cfg_of(**dict(over, m_n2o=m_mc))
    rng = np.random.default_rng(seed)
    D = R.draw(rng, N, cfg)
    rows = []
    for i, dr in enumerate(D):
        res = R.run_one(cfg, dr)
        rows.append(R.flat_row(i, dr, res, R.success(res), cfg))
    s = R.summarize(rows)
    s["by_wind"] = wind_bins(rows)
    s["max_gim_raw_p99"] = float(np.percentile([r["max_gim_raw"] for r in rows], 99))
    s["max_tilt_land_max"] = float(np.max([r["max_tilt_land"] for r in rows]))
    s["max_rate_coast_max"] = float(np.max([r["max_rate_coast"] for r in rows]))
    s["max_hinge_max"] = float(np.max([r["max_hinge"] for r in rows]))
    s["max_gim_max"] = float(np.max([r["max_gim"] for r in rows]))
    s["td_miss_p99"] = float(np.percentile([r["td_miss"] for r in rows if r["landed"] > 0.5], 99))
    sens = R.sensitivity(rows)
    par, apar, comp, mp, tab, info = R.build(cfg)
    out = dict(case=name, note=note, closes=True, sim=s6.SIM6_VERSION, engine_model=info["tags"]["engine_model"][1],
               config={k: (v if not callable(v) else f"callable:{getattr(v, '__name__', 'f')}") for k, v in cfg.items()},
               m_n2o_sized_kg=m_sized, m_n2o_mc_kg=m_mc, load_rule=("fixed (lead decision)" if m_fixed is not None
                                                                   else f"sized x {LOAD_MARGIN}"), tank_V_L=info["tank_V"] * 1e3, vehicle=info["vehicle"],
               d_body_m=info["d"], m_liftoff_kg=info["m_liftoff"], zcg0_m=info["zcg0"], z_pivot_m=info["z_pivot"],
               ballast=ballast_info, nominal=dict((k, float(v)) for k, v in res_nom.items()), summary=s, sensitivity=sens,
               cpu_s=time.time() - t0)
    return out, rows


def main():
    names = os.environ.get("GNC_CASES")
    names = names.split(",") if names else list(CASES)
    allsum = {}
    p_old = os.path.join(OUT, f"mc6_summary_{SUFFIX}.json")
    if os.environ.get("GNC_APPEND") and os.path.exists(p_old):
        allsum = json.load(open(p_old))["cases"]
    for name in names:
        over, note = CASES[name]
        out, rows = run_case(name, over, note)
        allsum[name] = out
        if rows:
            write_csv(os.path.join(OUT, f"mc6_runs_{name}_{SUFFIX}.csv"), rows)
            s = out["summary"]
            print(f"{name:24s} m_sized {out['m_n2o_sized_kg']:.3f} P {s['success']:.3f} "
                  f"[{s['ci95'][0]:.3f},{s['ci95'][1]:.3f}] fails {s['fail_modes']} "
                  f"vz99 {s['td_vz_p99']:.2f} vh99 {s['td_vh_p99']:.2f} tilt99 {s['td_tilt_p99']:.2f} "
                  f"rate99 {s['td_rate_p99']:.2f} miss50 {s['td_miss_p50']:.1f} ({out['cpu_s']:.0f}s)", flush=True)
        else:
            print(f"{name:24s} NO CLOSURE", flush=True)
        with open(os.path.join(OUT, f"mc6_summary_{SUFFIX}.json"), "w") as f:
            json.dump(dict(version=f"m2_mc6 {SUFFIX}", sim=s6.SIM6_VERSION,
                           sims_in_cases=sorted(set(str(c.get("sim")) for c in allsum.values())), n=N, load_margin=LOAD_MARGIN,
                           criteria=R.CRIT, cases=allsum), f, indent=1, default=float)


if __name__ == "__main__":
    main()

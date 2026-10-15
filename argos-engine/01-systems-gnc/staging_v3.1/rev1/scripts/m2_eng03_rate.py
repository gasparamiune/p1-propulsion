"""m2_eng03_rate v1.1 (GNC, 2026-10-13): ENG-03 with the HV69 pintle drive - the state-dependent thrust-rate limit flown in the 6-DOF,
paired against the 5 F_max/s (2500 N/s) baseline on the same draws.

Request (lead, CHANGELOG 2026-10-13 ENG-03 provisional): Electronics finds the HV69 CLOSES at >= 2500 N/s in every state but OPENS
slower above ~50 % thrust at low tank pressure (dynamic 2500 N/s ramps to 100 %: 1484 / 1812 / 2024 / 2153 / 2220 N/s at 3.5 /
4.0 / 4.5 / 5.0 / 5.5 MPa, corner spring +10 %, 7.335 V). Fly it as a state-dependent rate limit (opening vs closing, by tank
pressure and thrust) plus the servo lag; A1, A1J and B1 62 m paired against 5 F_max/s; rate-aware feed-forward allowed. Decision
rule (lead): loss within the Monte Carlo resolution (about 1 %) -> ENG-03 becomes the state-dependent map and the HV69 stays;
otherwise an actuator change is sized. Report the P change, the exact McNemar p-value and the phases where the opening rate binds.

Map (GNC_ENG03_MAP): Electronics 06-electronics/results/pintle_rate_map_v1.json (hub; sha256 411b0573d604364e...): 5 tank pressures
3.5-5.5 MPa x 19 thrust levels 62.5-500 N (F = frac x 500 N on the Combustion map), rate_map.<case>.R_open_N_per_s /
R_close_N_per_s = envelope (minimum over the needle-force laws L0/L1/L2); corner = spring +10 % opening / -10 % closing, plug
7.335 V (design / dispersion bound); nominal = spring nominal, 7.49 V. Reduced drive model B (Electronics, FIT to their nonlinear
drive simulation, ASSUMED servo): v_cmd = clip((F_cmd(t - 4 ms) - F) / 8.5 ms, -R_close, +R_open), 8.0 ms dv/dt = v_cmd - v,
dF/dt = v. sim6 v2.8-dev looks the map up at the truth tank pressure and the delivered thrust / thrust_scale, bilinear, holding the
edge values outside the grid (time below 3.5 MPa while binding is recorded = Electronics' 'flag').

Structure. sim6's thrust response is the CLOSED-LOOP (ECU Pc loop) response of ENG-03: first order, tau = 0.100 / 2.197 s x U(0.7,
1.5), saturated at 5 F_max/s. Electronics' drive model excludes the Pc loop and the chamber / fuel lag, so the closed-loop response
is kept and the drive enters as (i) the rate saturation (the drive limits the closed loop in large signal) and (ii) a bound with
the drive dynamics added in series.
Arms (all on the stored baseline's draws, seed 101, and its N2O load):
  base  stored v3 / v3.1 baseline runs (sim6 v2.7.1-dev; v2.8-dev with the options off reproduces them, m2_bitcheck_v28)
  R1    corner opening map (capped at 2500 N/s), closing 2500 N/s, closed-loop tau as baseline: the AMENDED-REQUIREMENT envelope
        (opening >= corner map, closing >= 2500 N/s, t10-90 <= 100 ms): the DECISION arm
  R2    R1 + Electronics' drive model B (4 ms latency, tau_p 8.5 ms, tau_v 8.0 ms, corner opening capped, closing 2500 N/s) in
        series ahead of the closed-loop response: a lag BOUND (the drive lag is also inside the closed-loop tau)
  R3    the HV69 corner in both directions, not capped (opening up to 2757 N/s at low thrust; closing R_close >= 2635 N/s,
        spring assist not credited)
  R1n   R1 with the NOMINAL map (spring nominal, 7.49 V): sensitivity
  R4    R1 + rate-aware feed-forward (thr_ff_rise added to the landing-burn trigger planning lag), only with GNC_ENG03_FF > 0
  v1.1: GNC_ENG03_FF may list several values [s]; arms R4f<ms> (R1 + FF) and R2Ff<ms> (R2 + FF: does the feed-forward recover the
        lag bound?) are formed for each value when 'R4' / 'R2F' is in GNC_ENG03_ARMS; GNC_ENG03_BASES selects the bases (default all)
Bases: A1_none, A1_pc, A1J_none, A1J_pc (gnc.json v3 A1 baseline: liquid line, relight plan 0.81 s), B1 62 m rbl (regression band
+ growth, lead's provisional cap) and tgl (growth only).
Parts (GNC_ENG03_PARTS, default run,eval; v1.1 adds export: the compact paired table for the hub); GNC_ENG03_SPLIT k/n; GNC_ENG03_ARMS (default R1,R2,R3,R1n).
Env: GNC_IFACE, GNC_ACT_RATE (iface_v3c set), GNC_ENG03_OUT (default out/eng03_rate)."""
import csv
import hashlib
import json
import os
import sys
import time
import numpy as np

os.environ.setdefault("GNC_PC_RATCHET", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_mc6 as M  # noqa: E402
import m2_relight_v28 as V  # noqa: E402
import m2_regband_mc as RBM  # noqa: E402
import m2_throat_mc as TG  # noqa: E402

VERSION = "m2_eng03_rate v1.1"
S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_ENG03_OUT", f"{S}/eng03_rate")
PARTS = os.environ.get("GNC_ENG03_PARTS", "run,eval").split(",")
SPLIT = os.environ.get("GNC_ENG03_SPLIT", "0/1")
MAP_SRC = os.environ.get("GNC_ENG03_MAP", "/home/claude/work/shared-fallback/engine/06-electronics/results/pintle_rate_map_v1.json")
ARMS_SEL = os.environ.get("GNC_ENG03_ARMS", "R1,R2,R3,R1n").split(",")
FFS = [float(x) for x in os.environ.get("GNC_ENG03_FF", "0").split(",") if x.strip() and float(x) > 0.0]
BASES_SEL = os.environ.get("GNC_ENG03_BASES", "")
FMAX = 500.0
A1_BASES = ("A1_none", "A1_pc", "A1J_none", "A1J_pc")
B1_BASES = ("rbl_B1_lead62_pc_k2", "tgl_B1_lead62_pc_k2")
PLAN_V3 = 0.81
_RB_CASES = {}
_MAPS = {}


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def rows_csv(p):
    return list(csv.DictReader(open(p))) if os.path.exists(p) else None


def load_map(case="corner", path=MAP_SRC):
    """Electronics pintle_rate_map_v1: grid [P_tank][frac], envelope tables of the case; closing also assist-credited (minimum
    over the laws of by_law.<L>.R_close_assist_credited)."""
    key = (case, path)
    if key in _MAPS:
        return _MAPS[key]
    d = json.load(open(path))
    g = d["grid"]
    rm = d["rate_map"][case]
    P = [float(p) * 1e6 for p in g["P_tank_MPa"]]
    F = [float(f) * FMAX for f in g["frac"]]
    Fn = np.asarray(rm["F_N"], float)
    dev = float(np.max(np.abs(Fn - np.asarray(F)[None, :])))
    bl = rm.get("by_law", {})
    ca = None
    if bl and all("R_close_assist_credited" in v for v in bl.values()):
        ca = np.min(np.array([v["R_close_assist_credited"] for v in bl.values()], float), axis=0).tolist()
    m = dict(P_tank_Pa=P, F_N=F, open_N_per_s=rm["R_open_N_per_s"], close_N_per_s=rm["R_close_N_per_s"], close_assist_N_per_s=ca,
             case=case, label=rm.get("label"), source=f"{path} (sha256/16 {sha16(path)}) rate_map.{case}",
             tag=f"SIM/DERIVED Electronics {d.get('id')} {d.get('version')} ({d.get('status', '')[:160]})",
             F_grid_max_dev_from_frac_x_500_N=dev, model_B=d["reduced_model_for_gnc"]["B_two_state"]["parameters"],
             version=d.get("version"), date=d.get("date"))
    _MAPS[key] = m
    return m


def interp_map(m, P, F, which="open_N_per_s"):
    """numpy twin of sim6._rmap (bilinear, edge values held)."""
    Ps, Fs, Z = np.asarray(m["P_tank_Pa"]), np.asarray(m["F_N"]), np.asarray(m[which])
    P = min(max(P, Ps[0]), Ps[-1])
    F = min(max(F, Fs[0]), Fs[-1])
    i = min(max(int(np.searchsorted(Ps, P) - 1), 0), len(Ps) - 2)
    j = min(max(int(np.searchsorted(Fs, F) - 1), 0), len(Fs) - 2)
    u = (P - Ps[i]) / (Ps[i + 1] - Ps[i])
    w = (F - Fs[j]) / (Fs[j + 1] - Fs[j])
    return float((1 - u) * ((1 - w) * Z[i, j] + w * Z[i, j + 1]) + u * ((1 - w) * Z[i + 1, j] + w * Z[i + 1, j + 1]))


def base_ref(base):
    """(over, csv, case json) of the stored baseline of a base."""
    if base in A1_BASES:
        c = f"v28_liq_p{PLAN_V3:.2f}_{base}_k2"
        return (V.case_over(base, "liq", PLAN_V3, V.e0e2_tables()), os.path.join(V.OUT, f"mc6_runs_{c}_v28.csv"),
                os.path.join(V.OUT, f"v28_case_{c}.json"))
    if not _RB_CASES:
        _RB_CASES.update(RBM.cases(None))
    return dict(_RB_CASES[base][0]), os.path.join(RBM.OUT, f"mc6_runs_{base}_rb.csv"), os.path.join(RBM.OUT, f"rb_case_{base}.json")


def arms():
    mc, mn = load_map("corner"), load_map("nominal")
    pB = mc["model_B"]
    drv = dict(thr_drive=1, thr_lat=float(pB["latency_s"]), thr_tau_p=float(pB["tau_p_s"]), thr_tau_v=float(pB["tau_v_s"]))
    a = {"R1": dict(rate_map=mc, rmap_close=0, rmap_cap=1),
         "R2": dict(rate_map=mc, rmap_close=0, rmap_cap=1, **drv),
         "R3": dict(rate_map=mc, rmap_close=1, rmap_cap=0),
         "R1n": dict(rate_map=mn, rmap_close=0, rmap_cap=1)}
    sel = {k: v for k, v in a.items() if k in ARMS_SEL}
    for ff in FFS:
        tag = f"f{int(round(ff * 1000))}"
        if "R4" in ARMS_SEL:
            sel["R4" + tag] = dict(rate_map=mc, rmap_close=0, rmap_cap=1, thr_ff_rise=ff)
        if "R2F" in ARMS_SEL:
            sel["R2F" + tag] = dict(rate_map=mc, rmap_close=0, rmap_cap=1, thr_ff_rise=ff, **drv)
    return sel


def bases():
    b = A1_BASES + B1_BASES
    return tuple(x for x in b if x in BASES_SEL.split(",")) if BASES_SEL else b


def run_fixed(over, m_load, seed=101):
    cfg = R.cfg_of(**dict({k: v for k, v in over.items() if k != "m_fixed"}, m_n2o=float(m_load)))
    D = R.draw(np.random.default_rng(seed), M.N, cfg)
    return [R.flat_row(i, dr, res, R.success(res), cfg) for i, dr in enumerate(D) for res in (R.run_one(cfg, dr),)]


def part_run():
    os.makedirs(OUT, exist_ok=True)
    k, n = (int(x) for x in SPLIT.split("/"))
    A = arms()
    jobs = [(b, a) for a in A for b in bases()][k::n]
    for base, arm in jobs:
        p = os.path.join(OUT, f"mc6_runs_{base}_{arm}.csv")
        if os.path.exists(p) and os.path.getsize(p) > 100 and os.environ.get("GNC_ENG03_FORCE") != "1":
            print("exists", base, arm, flush=True)
            continue
        t0 = time.time()
        over, bcsv, bjson = base_ref(base)
        m_load = json.load(open(bjson))["m_n2o_mc_kg"]
        ov = dict(over)
        ov.update(A[arm])
        rows = run_fixed(ov, m_load)
        M.write_csv(p, rows)
        ok = np.array([r["ok"] for r in rows]) > 0.5
        ob = np.array([float(r["ok"]) for r in rows_csv(bcsv)]) > 0.5
        print(f"{base:22s} {arm:3s}: P {ok.mean():.3f} (base {ob.mean():.3f}; -{int(np.sum(ob & ~ok))}/+{int(np.sum(~ob & ok))}) "
              f"bind land p50 {np.median([r['rmap_bind_land'] for r in rows]):.3f} s ({time.time() - t0:.0f} s)", flush=True)
        with open(os.path.join(OUT, f"case_{base}_{arm}.json"), "w") as f:
            json.dump(dict(base=base, arm=arm, m_n2o_mc_kg=m_load, baseline_csv=bcsv, sim=s6.SIM6_VERSION,
                           arm_config={kk: (vv if kk != "rate_map" else vv["source"]) for kk, vv in A[arm].items()},
                           cpu_s=time.time() - t0), f, indent=1)


def mcnemar(a, b):
    from scipy.stats import binomtest
    lost, gained = int(np.sum(a & ~b)), int(np.sum(~a & b))
    return dict(P_base=float(a.mean()), P_arm=float(b.mean()), dP=float(b.mean() - a.mean()), lost=lost, gained=gained,
                p_exact=float(binomtest(lost, lost + gained, 0.5).pvalue) if lost + gained else 1.0, n=int(len(a)))


def pct(x, qs=(50, 99)):
    x = np.asarray(x, float)
    return [float(np.percentile(x, q)) for q in qs] + [float(x.max())]


def part_eval():
    A = arms()
    mc = load_map("corner")
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, iface=R.IFACE, request=__doc__.split("\n\n")[1],
               maps={c: {k: load_map(c)[k] for k in ("source", "label", "tag", "F_grid_max_dev_from_frac_x_500_N")} for c in ("corner", "nominal")},
               map_corner_min_open_N_per_s=float(np.min(mc["open_N_per_s"])), model_B=mc["model_B"],
               arms={k: {kk: (vv if kk != "rate_map" else vv["case"]) for kk, vv in v.items()} for k, v in A.items()},
               by_base={}, pooled={}, decision_rule=("lead 2026-10-13: loss within the Monte Carlo resolution (about 1 %) -> ENG-03 becomes "
                                                     "the state-dependent map and the HV69 stays; otherwise an actuator change is sized"))
    pools = {}
    for base in bases():
        over, bcsv, bjson = base_ref(base)
        b = rows_csv(bcsv)
        if not b:
            continue
        ob = np.array([float(r["ok"]) for r in b]) > 0.5
        bb = dict(baseline=dict(csv=bcsv, P=float(ob.mean()), ci95=TG.wilson(int(ob.sum()), len(ob))))
        for arm in A:
            rr = rows_csv(os.path.join(OUT, f"mc6_runs_{base}_{arm}.csv"))
            if not rr:
                continue
            ok = np.array([float(r["ok"]) for r in rr]) > 0.5
            g = lambda k: np.array([float(r[k]) for r in rr])  # noqa: E731
            same = ([r["wind"] for r in rr] == [r["wind"] for r in b] and
                    [r.get("t_ign_u") for r in rr] == [r.get("t_ign_u") for r in b] and
                    [r.get("thrust_scale") for r in rr] == [r.get("thrust_scale") for r in b])
            x = dict(P=float(ok.mean()), ci95=TG.wilson(int(ok.sum()), len(ok)), paired=mcnemar(ob, ok), same_draws=bool(same),
                     bind_total_s_p50_p99_max=pct(g("rmap_bind_t")), bind_ascent_s_p50_p99_max=pct(g("rmap_bind_asc")),
                     bind_phase2to4_s_p50_p99_max=pct(g("rmap_bind_mid")), bind_landing_s_p50_p99_max=pct(g("rmap_bind_land")),
                     shortfall_max_N_p50_p99_max=pct(g("rmap_short_max")),
                     runs_binding=dict(ascent=int(np.sum(g("rmap_bind_asc") > 0)), phase2to4=int(np.sum(g("rmap_bind_mid") > 0)),
                                       landing=int(np.sum(g("rmap_bind_land") > 0))),
                     tank_P_min_MPa_p01_p50=[float(np.percentile(g("rmap_pt_min"), 1)) / 1e6, float(np.median(g("rmap_pt_min"))) / 1e6],
                     tank_P_at_landing_trigger_MPa_p01_p50_p99=[float(np.percentile(g("pt_trigger"), q)) / 1e6 for q in (1, 50, 99)],
                     runs_below_map_P=int(np.sum(g("rmap_pt_min") < 3.5e6)), bind_below_map_P_s_max=float(g("rmap_pt_ext_t").max()))
            lost = [i for i in range(len(ok)) if ob[i] and not ok[i]]
            gained = [i for i in range(len(ok)) if ok[i] and not ob[i]]
            x["lost_runs"] = [dict(run=i, bind_land_s=float(rr[i]["rmap_bind_land"]), bind_asc_s=float(rr[i]["rmap_bind_asc"]),
                                   shortfall_N=float(rr[i]["rmap_short_max"]), td_vz=float(rr[i]["td_vz"]), td_vh=float(rr[i]["td_vh"]),
                                   td_tilt=float(rr[i]["td_tilt"]), td_rate=float(rr[i]["td_rate"]), landed=float(rr[i]["landed"]),
                                   base_td_vz=float(b[i]["td_vz"]), base_td_vh=float(b[i]["td_vh"])) for i in lost]
            x["gained_runs"] = [int(i) for i in gained]
            # v1.1: paired result by mean-wind bin (draw U(0, 8) m/s) - where the losses sit
            wv = np.array([float(r["wind"]) for r in rr])
            x["by_wind_m_s"] = {f"{lo:g}-{hi:g}": dict(n=int(np.sum((wv >= lo) & (wv < hi))), **{k_: v_ for k_, v_ in mcnemar(
                ob[(wv >= lo) & (wv < hi)], ok[(wv >= lo) & (wv < hi)]).items() if k_ != "n"}) for lo, hi in ((0.0, 4.0), (4.0, 6.0), (6.0, 8.01))}
            x["lost_runs_wind_m_s"] = [round(float(wv[i]), 2) for i in lost]
            x["lost_vs_binding"] = dict(
                lost_runs_binding_landing=int(sum(1 for i in lost if float(rr[i]["rmap_bind_land"]) > 0)),
                all_runs_binding_landing=int(np.sum(g("rmap_bind_land") > 0)),
                bind_land_s_lost_median=float(np.median([float(rr[i]["rmap_bind_land"]) for i in lost])) if lost else None,
                bind_land_s_all_median=float(np.median(g("rmap_bind_land"))))
            bb[arm] = x
            grp = "A1" if base in A1_BASES else "B1"
            pools.setdefault((grp, arm), []).append((ob, ok))
            pools.setdefault(("all", arm), []).append((ob, ok))
            pools.setdefault((grp + "_wind>=6", arm), []).append((ob[wv >= 6.0], ok[wv >= 6.0]))
            print(f"{base:22s} {arm:3s}: P {x['P']:.3f} vs {ob.mean():.3f} -{x['paired']['lost']}/+{x['paired']['gained']} p "
                  f"{x['paired']['p_exact']:.3g} | bind asc {np.round(x['bind_ascent_s_p50_p99_max'], 3).tolist()} mid "
                  f"{np.round(x['bind_phase2to4_s_p50_p99_max'], 3).tolist()} land {np.round(x['bind_landing_s_p50_p99_max'], 3).tolist()}"
                  f" | short {np.round(x['shortfall_max_N_p50_p99_max'], 1).tolist()} N | P_trig "
                  f"{np.round(x['tank_P_at_landing_trigger_MPa_p01_p50_p99'], 2).tolist()} Pmin {np.round(x['tank_P_min_MPa_p01_p50'], 2).tolist()}"
                  f" below3.5 {x['runs_below_map_P']} | same draws {same}", flush=True)
        out["by_base"][base] = bb
    for (grp, arm), lst in sorted(pools.items()):
        a = np.concatenate([x for x, _ in lst])
        b = np.concatenate([y for _, y in lst])
        d = mcnemar(a, b)
        d.update(ci95_arm=TG.wilson(int(b.sum()), len(b)), ci95_base=TG.wilson(int(a.sum()), len(a)), n_bases=len(lst),
                 within_1pct=bool(abs(d["dP"]) <= 0.01))
        out["pooled"][f"{grp}|{arm}"] = d
        print(f"pooled {grp:3s} {arm:3s}: P {d['P_arm']:.4f} vs {d['P_base']:.4f} dP {d['dP']:+.4f} -{d['lost']}/+{d['gained']} p "
              f"{d['p_exact']:.3g} (n {d['n']})", flush=True)
    out["not_modelled"] = [
        "the ECU Pc loop around the drive is represented by sim6's closed-loop first-order response (ENG-03 t10-90, MC-drawn tau); the "
        "drive enters as its rate saturation (R1, R3, R1n) and, as a bound, with its two-state dynamics in series (R2)",
        "tank pressure below the map's 3.5 MPa: the 3.5 MPa rates are held (runs_below_map_P, bind_below_map_P_s_max)",
        "the corner drive (spring +10 %, rail minimum) on every run (no per-run draw of the drive state): conservative for the decision",
        "B-PNT-1 has not measured the HV69 torque-speed line under load (Electronics: retailer copies of MKS data, ASSUMED servo loop)",
        "start (kStartRamp 2500 N/s COMB start cap) and shutdown transients: the sim6 start / lift-ramp shutdown models are unchanged"]
    with open(os.path.join(OUT, "eng03_rate.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", os.path.join(OUT, "eng03_rate.json"), flush=True)


def part_export():
    """v1.1: compact paired table (one row per base, arm and run) for the hub: the base and arm outcomes on the same draws, the
    draws that matter here and the rate-map records. gzip CSV: eng03_paired_runs_v1.1.csv.gz."""
    import gzip
    A = arms()
    cols = ["base", "arm", "run", "ok_base", "ok_arm", "wind", "gust_scale", "tau_f", "thrust_scale", "t_ign", "rmap_bind_t",
            "rmap_bind_asc", "rmap_bind_mid", "rmap_bind_land", "rmap_pt_min", "pt_trigger", "td_vz", "td_vh", "td_tilt", "td_rate",
            "base_td_vz", "base_td_vh"]
    p = os.path.join(OUT, "eng03_paired_runs_v1.1.csv.gz")
    n = 0
    with gzip.open(p, "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for base in bases():
            _, bcsv, _ = base_ref(base)
            b = rows_csv(bcsv)
            for arm in A:
                rr = rows_csv(os.path.join(OUT, f"mc6_runs_{base}_{arm}.csv"))
                if not rr or not b:
                    continue
                for i, r in enumerate(rr):
                    w.writerow([base, arm, i, int(float(b[i]["ok"]) > 0.5), int(float(r["ok"]) > 0.5)] +
                               [r.get(k, "") for k in cols[5:20]] + [b[i]["td_vz"], b[i]["td_vh"]])
                    n += 1
    print("wrote", p, n, "rows", flush=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    if "run" in PARTS:
        part_run()
    if "eval" in PARTS:
        part_eval()
    if "export" in PARTS:
        part_export()


if __name__ == "__main__":
    main()

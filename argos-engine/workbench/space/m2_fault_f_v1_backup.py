"""m2_fault_f v1 (GNC, 2026-10-13): review REV-GNC-1 RG-18, stuck-pintle over-thrust faults flown in the 6-DOF loop with every
detector (sim6 v2.8-dev amendment F), the consequence of a miss and the geofence proposal (research).

Bases (flown mass estimator with every calibrated error source and the lever-arm / direction compensation; m2_mass_est v2
specs, draws and combustion prior; seed 101 dispersions):
  A1  A1_none (liquid relight plan 0.81 s; relight NOT CLOSED, RG-01). Pc valid: tot_cal_comp. Pc lost: pclhi_re_comp
      (flow and thrust per command x 1.143) / pcllo_re_comp (x 0.875).
  B1  B1 62 m. Pc valid: tgl_B1_lead62_pc_k2 tot_cal_comp. Pc lost: B1_62_none pclhi_re_comp / pcllo_re_comp.
Onsets (own generator RNG_F + onset index; the same onset times and FC_THRUST frame phases in every branch and level of an onset):
  A1asc   flt_ph 1, flight time U(0.3, 2.5) s (boost)          A1land  flt_ph 5, U(0.2, 2.0) s after the landing-burn start
  B1asc   flt_ph 1, U(0.3, 0.8) s (boost)                      B1floor flt_ph 2, flight time U(1.2, 10.0) s (floor phases)
  B1land  flt_ph 5, U(0.2, 2.0) s after the landing-burn start
  FC_THRUST frame phase U(0, 1 / fct_hz) per run.
Levels: L670 670 N at 2.5 kN/s (threshold + 20 N, REQ review); L876 876 N at 3.6 kN/s (Combustion full-open MEOP case).
Branches (every flight detector armed, geofence off):
  Venc       Pc valid, the pintle encoder sees the jam (over-pressure, PINTLE_FAULT, FC_THRUST)
  Vblind     Pc valid, linkage failure the encoder does not see (over-pressure, FC_THRUST)
  Lhi_blind  Pc lost (flow x 1.143), linkage failure (FC_THRUST only)
  Llo_blind  Pc lost (x 0.875), linkage failure (FC_THRUST only)
  Llo_enc    Pc lost (x 0.875), encoder sees the jam (PINTLE_FAULT, FC_THRUST)
MISS arms (Lhi_blind with every detector off): the consequence of a miss. GEO arms: MISS + the geofence proposal
(h_est > h_target + geo_dh with the engine lit -> ABORT).
Runs: N_F per arm (default 200; MISS / GEO N_M, default 100), the first runs of the seed-101 draws.
Metrics per arm: detection (a decision after the onset) with Wilson bounds (0 / 200 -> 1.9 %; per-profile, independent error
sets: m2_mass_est v2 err_draws per run); time from the onset to the decision and to the MV seat; decision source; impulse from
the onset to the end of the tail-off; highest true height and largest vertical speed after the onset; touchdown vertical
speed and distance from the pad; false decisions (before the onset); FC_THRUST held maxima before (margin to 650 N) and after
the onset; the flight outcome flag of the landing criteria (an aborted flight is a lost vehicle; the flag is reported only).
Not modelled (stated): axial structural modes, IMU group delay, flight-computer and ECU scheduling beyond the Electronics
abt_lat term, Pc filter lag, combustion low-frequency content (RG-19); the segment inventory after the MV seat (~20-36 g).
Env: GNC_FF_PARTS (mc,eval), GNC_FF_SPLIT (k/n), GNC_FF_N (200), GNC_FF_NM (100), GNC_FF_OUT.
Output: <out>/fault_<arm>.csv, <out>/fault_f.json"""
import csv
import json
import os
import sys
import time
import numpy as np

S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_FF_OUT", f"{S}/fault_f")
os.environ.setdefault("GNC_PC_RATCHET", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_mass_est_v2 as MV  # noqa: E402
import m2_mc6 as M  # noqa: E402

VERSION = "m2_fault_f v1"
PARTS = os.environ.get("GNC_FF_PARTS", "mc,eval").split(",")
SPLIT = os.environ.get("GNC_FF_SPLIT", "0/1")
N_F = int(os.environ.get("GNC_FF_N", "200"))
N_M = int(os.environ.get("GNC_FF_NM", "100"))
RNG_F = 20261029
THR = 650.0
ONS = {"A1asc": ("A1", 1, (0.3, 2.5)), "A1land": ("A1", 5, (0.2, 2.0)), "B1asc": ("B1", 1, (0.3, 0.8)),
       "B1floor": ("B1", 2, (1.2, 10.0)), "B1land": ("B1", 5, (0.2, 2.0))}
LEV = {"L670": (670.0, 2500.0), "L876": (876.0, 3600.0)}
BR = {"Venc": ("V", 0, 1), "Vblind": ("V", 0, 0), "Lhi_blind": ("Lhi", 1, 0), "Llo_blind": ("Llo", 1, 0),
      "Llo_enc": ("Llo", 1, 1)}
BASE = {("A1", "V"): "A1_none", ("A1", "L"): "A1_none", ("B1", "V"): "tgl_B1_lead62_pc_k2", ("B1", "L"): "B1_62_none"}
SRC = {1.0: "FC_THRUST", 2.0: "over-pressure", 3.0: "PINTLE_FAULT", 4.0: "geofence"}
KEEP = ("ok", "landed", "crash", "td_vz", "td_vh", "td_tilt", "td_x", "td_y", "td_t", "h_max", "t_end", "exhausted", "prop_used",
        "starts", "t_meco", "t_relight", "mest_e_maxabs_fc", "mest_e_end") + tuple(k for k in s6.RES_NAMES if k.startswith(("flt_", "fct_")))


def arms():
    a = {}
    for on in ONS:
        for lv in LEV:
            for br in BR:
                a[f"{on}|{lv}|{br}"] = dict(on=on, lv=lv, br=br, kind="det", n=N_F)
            a[f"{on}|{lv}|MISS"] = dict(on=on, lv=lv, br="Lhi_blind", kind="miss", n=N_M)
            a[f"{on}|{lv}|GEO"] = dict(on=on, lv=lv, br="Lhi_blind", kind="geo", n=N_M)
    return a


def onset_draws(on, n):
    k = list(ONS).index(on)
    rg = np.random.default_rng(RNG_F + k)
    lo, hi = ONS[on][2]
    return rg.uniform(lo, hi, n), rg.uniform(0.0, 0.01, n)


_CFG = {}


def cfg_for(prof, kind):
    key = (prof, kind)
    if key not in _CFG:
        cfg = MV.base_cfg(BASE[key])
        _CFG[key] = (cfg, R.draw(np.random.default_rng(101), 500, cfg))
    return _CFG[key]


def spec_of(sk):
    cs, ps = MV.case_specs(), MV.pcl_specs()
    return {"V": cs["tot_cal_comp"], "Lhi": ps["pclhi_re_comp"], "Llo": ps["pcllo_re_comp"]}[sk]


def fly_arm(name, a):
    prof, ph, _ = ONS[a["on"]]
    F_, rate_ = LEV[a["lv"]]
    sk, pcl, enc = BR[a["br"]]
    cfg, D = cfg_for(prof, "V" if sk == "V" else "L")
    spec = spec_of(sk)
    tt, fph = onset_draws(a["on"], a["n"])
    rows = []
    for i in range(a["n"]):
        c, disp = MV.run_cfg_case(cfg, D[i], spec, i, "comb")
        c = dict(c, flt_on=1, flt_ph=ph, flt_t=float(tt[i]), flt_F=F_, flt_rate=rate_, flt_enc=enc, flt_pcl=pcl,
                 fct_ph=float(fph[i]), fct_comp=1)
        if a["kind"] in ("miss", "geo"):
            c.update(det_fct=0, det_op=0, det_pf=0)
        if a["kind"] == "geo":
            c["det_geo"] = 1
        res = R.fly(c, disp, nrec=10)[0]
        row = dict(run=i, onset_draw_s=float(tt[i]), frame_phase_s=float(fph[i]), ok=int(R.success(res)))
        row.update({k: float(res[k]) for k in KEEP if k != "ok"})
        rows.append(row)
    return rows


def fname(name):
    return os.path.join(OUT, "fault_" + name.replace("|", "_") + ".csv")


def part_mc():
    global MV
    os.makedirs(OUT, exist_ok=True)
    MV.COMB = MV.comb_draws(500)
    jr = json.load(open(f"{S}/throat_growth/throat_growth.json"))["j_ref"]
    k, n = (int(x) for x in SPLIT.split("/"))
    A = arms()
    for name in list(A)[k::n]:
        p = fname(name)
        if os.path.exists(p) and os.path.getsize(p) > 100 and os.environ.get("GNC_FF_FORCE") != "1":
            print("exists", name, flush=True)
            continue
        a = A[name]
        MV.TG_JREF_DEFAULT = float(jr["A1" if ONS[a["on"]][0] == "A1" else "B1"])
        t0 = time.time()
        rows = fly_arm(name, a)
        M.write_csv(p, rows)
        det = np.array([r["flt_tdec"] >= r["flt_t0"] >= 0.0 for r in rows])
        print(f"{name:28s}: n {len(rows)} detected {det.sum()} ({time.time() - t0:.0f} s)", flush=True)


def rows_csv(p):
    return list(csv.DictReader(open(p))) if os.path.exists(p) else None


def col(rows, k):
    return np.array([float(r[k]) for r in rows])


def pct(x, qs=(50, 99)):
    x = np.asarray(x, float)
    if x.size == 0:
        return None
    return dict({f"p{q:02d}": float(np.percentile(x, q)) for q in qs}, min=float(x.min()), max=float(x.max()), n=int(x.size))


def wilson(k, n):
    lo, hi = R.wilson(k, n)
    return [float(lo), float(hi)]


def arm_stats(rows):
    t0, dec, seat = col(rows, "flt_t0"), col(rows, "flt_tdec"), col(rows, "flt_tseat")
    on = t0 >= 0.0
    det = on & (dec >= t0)
    fal = col(rows, "flt_false") > 0.5
    n = len(rows)
    src = col(rows, "flt_src")
    dist = np.hypot(col(rows, "td_x"), col(rows, "td_y"))
    e = dict(n=n, onset_reached=int(on.sum()), detected=int(det.sum()), missed=int((on & ~det).sum()),
             miss_wilson=wilson(int((on & ~det).sum()), int(on.sum())) if on.sum() else None,
             false_decisions=int(fal.sum()), false_wilson=wilson(int(fal.sum()), n),
             source_counts={SRC.get(s_, str(s_)): int(np.sum((src == s_) & det)) for s_ in np.unique(src[det])},
             onset_to_decision_ms=pct(1e3 * (dec - t0)[det], (50, 99)),
             onset_to_seat_ms=pct(1e3 * (seat - t0)[det & (seat >= 0)], (50, 99)),
             impulse_after_onset_Ns=pct(col(rows, "flt_imp")[on], (50, 99)),
             max_true_height_after_onset_m=pct(col(rows, "flt_hmax")[on], (50, 99)),
             max_vz_after_onset_mps=pct(col(rows, "flt_vzmax")[on], (50, 99)),
             touchdown_vz_mps=pct(col(rows, "td_vz")[on], (1, 50)),
             touchdown_distance_m=pct(dist[on], (50, 99)),
             apex_m=pct(col(rows, "h_max"), (50, 99)),
             landing_criteria_met=int(np.sum(col(rows, "ok") > 0.5)),
             fct_held_pre_N=pct(col(rows, "fct_held_pre"), (50, 99)),
             fct_held_post_N=pct(col(rows, "fct_held_post")[on], (1, 50)),
             fct_trip_ms_after_onset=pct(1e3 * (col(rows, "flt_tr_fct") - t0)[on & (col(rows, "flt_tr_fct") >= t0)], (50, 99)),
             op_trip_ms_after_onset=pct(1e3 * (col(rows, "flt_tr_op") - t0)[on & (col(rows, "flt_tr_op") >= t0)], (50, 99)),
             pf_trip_ms_after_onset=pct(1e3 * (col(rows, "flt_tr_pf") - t0)[on & (col(rows, "flt_tr_pf") >= t0)], (50, 99)),
             geo_trip_ms_after_onset=pct(1e3 * (col(rows, "flt_tr_geo") - t0)[on & (col(rows, "flt_tr_geo") >= t0)], (50, 99)),
             end_states={str(int(v)): int(np.sum(col(rows, "flt_end") == v)) for v in np.unique(col(rows, "flt_end"))},
             activations={str(int(v)): int(np.sum(col(rows, "flt_n_on") == v)) for v in np.unique(col(rows, "flt_n_on"))})
    return e


def part_eval():
    A = arms()
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, method=__doc__.split("\n\n")[0], rng_onset=RNG_F,
               n_det=N_F, n_miss=N_M, threshold_N=THR, arms={}, pooled={})
    for name, a in A.items():
        rows = rows_csv(fname(name))
        if rows:
            out["arms"][name] = dict(a, **arm_stats(rows))
    # pooled detection per profile and branch (all onsets and levels): misses / onsets reached
    for prof in ("A1", "B1"):
        for br in BR:
            k_ = [nm for nm, a in A.items() if a["kind"] == "det" and a["br"] == br and ONS[a["on"]][0] == prof and nm in out["arms"]]
            if not k_:
                continue
            on_ = sum(out["arms"][x]["onset_reached"] for x in k_)
            mi_ = sum(out["arms"][x]["missed"] for x in k_)
            fa_ = sum(out["arms"][x]["false_decisions"] for x in k_)
            nn_ = sum(out["arms"][x]["n"] for x in k_)
            out["pooled"][f"{prof}|{br}"] = dict(arms=len(k_), onsets=on_, missed=mi_, miss_wilson=wilson(mi_, on_),
                                                 false_decisions=fa_, flights=nn_,
                                                 note="arms of one profile share the seed-101 dispersions and error sets "
                                                      "(m2_mass_est v2 err_draws): the pooled bound is not tighter than "
                                                      "the per-arm bound in effect (RG-17)")
    out["valid_window"] = VALID_WINDOW
    out["tether_rule_flight_C"] = TETHER_RULE
    with open(os.path.join(OUT, "fault_f.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    for name, e in out["arms"].items():
        d = e["onset_to_decision_ms"] or {}
        s_ = e["onset_to_seat_ms"] or {}
        h_ = e["max_true_height_after_onset_m"] or {}
        tv = e["touchdown_vz_mps"] or {}
        print(f"{name:28s} det {e['detected']:3d}/{e['onset_reached']:3d} false {e['false_decisions']} src {e['source_counts']} | "
              f"dec p50/p99/max {d.get('p50', float('nan')):.0f}/{d.get('p99', float('nan')):.0f}/{d.get('max', float('nan')):.0f} ms "
              f"seat p99 {s_.get('p99', float('nan')):.0f} | imp p99 {e['impulse_after_onset_Ns']['p99']:.0f} N s | hmax p99/max "
              f"{h_.get('p99', float('nan')):.0f}/{h_.get('max', float('nan')):.0f} m | td_vz p01 {tv.get('p01', float('nan')):.1f} | "
              f"held pre p99 {e['fct_held_pre_N']['p99']:.0f} post p01 {(e['fct_held_post_N'] or {}).get('p01', float('nan')):.0f}",
              flush=True)
    for k_, v in out["pooled"].items():
        print("pooled", k_, v["missed"], "/", v["onsets"], v["miss_wilson"], "false", v["false_decisions"], flush=True)


VALID_WINDOW = dict(
    definition=("FC_THRUST frames count toward the over-thrust abort only while ALL of: (1) airborne latch set (h_est > 1 m once "
                "after liftoff; the latch never clears); (2) h_est > 1 m; (3) ECU in RUN (engine lit, the over-thrust check has "
                "no meaning with the MV closed); (4) no drogue load: before the drogue deploys, or after the release confirmed by "
                "the release command plus the load-cell or drop-out indication; (5) no tether load (flight C rule below); "
                "(6) before touchdown (leg switch or the touchdown logic). A frame outside the window resets the consecutive "
                "count. Stale accelerometer data (> 50 ms) flag only, never abort (lead rule)."),
    sim6=("amendment F: fc_air (h_est > 1 m latch) and h_est > 1 m and lit and not drogue and not td_done; the drogue state "
          "is the sim's attachment state (A1: deployed at apogee, released when the relight thrust exceeds half the floor)"),
    covers=("the A1 ascent cases from 500 N (no drogue load before deployment), the A1 landing burn after the release, every "
            "B1 phase; the A1 relight transient while the drogue still loads the vehicle is outside the window: there the "
            "Pc-valid detectors and PINTLE_FAULT act alone"),
    tags="REQ wording proposed by GNC for the lead (review RG-18); sim6 amendment F implements it")
TETHER_RULE = dict(
    proposal=("flight C (tethered): the tether load enters the force balance (F_acc = m_hat f_z + D_model + T_meas along the "
              "body axis) when a tether load cell feeds the flight computer, and its uncertainty enters the RG-16 budget; "
              "without a load cell, FC_THRUST is outside its valid window whenever the tether can be taut, and flight C needs a "
              "valid Pc (over-pressure abort) and the PINTLE_FAULT path as GO conditions"),
    why="a taut tether pulling down by T makes F_acc under-read the thrust by T: a stuck pintle can be masked by the tether",
    tags="PROPOSAL GNC; tether hardware, load-cell range and data path TO-DEFINE (Mechanical, Electronics)")


def main():
    if "mc" in PARTS:
        part_mc()
    if "eval" in PARTS:
        part_eval()


if __name__ == "__main__":
    main()

"""m2_purge_bleed v1 (GNC, 2026-10-13): RG-01 re-fly model prepared on the coordinator's relay (2026-10-13): the A1 relight
forced purge (MV open, pintle seated, head-end bleed open 2-3 s ending at the lift; CF-4 decides whether it is fitted) and the
stuck-open bleed fault (6.3-19.4 g/s during a burn, 3-8 % of the engine flow at 0.6 mm, up to 14 % at 0.8 mm), flown with sim6
v2.8-dev amendment P. The relight plan value (0.81 s liquid plan) and the light (W 0.65 s) are NOT changed here: Combustion
states whether the purge shifts them; this run gives the GNC side (purge timing, swing during the purge, propellant, mass
estimate, landing).

Bases (flown mass estimator with every calibrated error source and the lever-arm / direction compensation, m2_mass_est v2
tot_cal_comp with the base draws: prior 'base'; seed 101, 500 runs, paired exact McNemar against the arm 'ref' of the profile):
  A1  A1_none (liquid plan 0.81 s; relight NOT CLOSED, RG-01)
  B1  B1 62 m regression band + growth, FSW burn limit action 1 and the Pc-based apex predictor (m2_web_limit W1p)
Arms:
  A1 ref         no purge
  A1 P25         purge 2.5 s + 0.5 s anticipation, 0.8 mm (20.0 g/s liquid, DERIVED Combustion purge_sizing_v2p4), jet
                 105.8 m/s radial (2.1 N; vent direction TO-DEFINE), lift priority, booked by the FSW
  A1 P30         as P25 with 3.0 s                      A1 P20_06   2.0 s, 0.6 mm (11.25 g/s)
  A1 P25_nojet   balanced / axial vent                  A1 P25_nobook  the FSW does not book the purge
  A1 P25_wait    the lift waits for the full purge (prg_prio 0, comparator)
  A1 P25_lead0   no anticipation margin (prg_lead 0)
  A1 S194_0 / S1285_0 / S063_0   P25 + stuck-open bleed from the lift (fails to close), additive bracket, 19.4 / 12.85 / 6.3 g/s
  A1 S194_1      P25 + stuck bleed, subtractive bracket (share of the injector flow capped at 14 %)
  A1 S194_0_nojet  as S194_0 with a balanced / axial vent
  B1 ref; B1 B194_0 / B1285_0 / B063_0 stuck-open bleed from ignition (additive); B1 B194_1 (subtractive); B1 B194_0_nojet
Output: <out>/pb_<arm>.csv, <out>/purge_bleed.json"""
import csv
import json
import os
import sys
import time
import numpy as np

S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_PB_OUT", f"{S}/purge_bleed")
os.environ.setdefault("GNC_PC_RATCHET", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_mass_est_v2 as MV  # noqa: E402
import m2_web_limit as WL  # noqa: E402
import m2_mc6 as M  # noqa: E402

VERSION = "m2_purge_bleed v1"
PARTS = os.environ.get("GNC_PB_PARTS", "mc,eval").split(",")
SPLIT = os.environ.get("GNC_PB_SPLIT", "0/1")
N = int(os.environ.get("GNC_PB_N", "500"))
P25 = dict(prg_on=1, prg_T=2.5, prg_lead=0.5, prg_mdot=0.0200, prg_jet=1, prg_prio=1, prg_book=1)
ARMS = {
    "A1|ref": {},
    "A1|P25": dict(P25),
    "A1|P30": dict(P25, prg_T=3.0),
    "A1|P20_06": dict(P25, prg_T=2.0, prg_mdot=0.01125),
    "A1|P25_nojet": dict(P25, prg_jet=0),
    "A1|P25_nobook": dict(P25, prg_book=0),
    "A1|P25_wait": dict(P25, prg_prio=0),
    "A1|P25_lead0": dict(P25, prg_lead=0.0),
    "A1|S194_0": dict(P25, blf_on=1, blf_ph=4, blf_mode=0, blf_mdot=0.0194),
    "A1|S1285_0": dict(P25, blf_on=1, blf_ph=4, blf_mode=0, blf_mdot=0.01285),
    "A1|S063_0": dict(P25, blf_on=1, blf_ph=4, blf_mode=0, blf_mdot=0.0063),
    "A1|S194_1": dict(P25, blf_on=1, blf_ph=4, blf_mode=1, blf_mdot=0.0194),
    "A1|S194_0_nojet": dict(P25, blf_on=1, blf_ph=4, blf_mode=0, blf_mdot=0.0194, bl_vj=0.0),
    "B1|ref": {},
    "B1|B194_0": dict(blf_on=1, blf_ph=0, blf_mode=0, blf_mdot=0.0194),
    "B1|B1285_0": dict(blf_on=1, blf_ph=0, blf_mode=0, blf_mdot=0.01285),
    "B1|B063_0": dict(blf_on=1, blf_ph=0, blf_mode=0, blf_mdot=0.0063),
    "B1|B194_1": dict(blf_on=1, blf_ph=0, blf_mode=1, blf_mdot=0.0194),
    "B1|B194_0_nojet": dict(blf_on=1, blf_ph=0, blf_mode=0, blf_mdot=0.0194, bl_vj=0.0),
}
KEEP = ("ok", "landed", "crash", "td_vz", "td_vh", "td_tilt", "td_rate", "td_x", "td_y", "h_max", "exhausted", "liq_left",
        "prop_used", "t_relight", "h_ign", "v_ign", "t90_relight", "burn_time", "mest_e_end", "mest_e_b1end", "max_tilt_desc",
        "max_rate_desc", "relight_ok") + tuple(k for k in s6.RES_NAMES if k.startswith(("prg_", "blf_")))
_B = {}


def base(prof):
    if prof not in _B:
        if prof == "A1":
            cfg = MV.base_cfg("A1_none")
            _B[prof] = (cfg, R.draw(np.random.default_rng(101), 500, cfg), None)
        else:
            cfg = WL.base_cfg()[0]
            _B[prof] = (cfg, R.draw(np.random.default_rng(101), 500, cfg), WL.meas_draws(500))
    return _B[prof]


def fly_arm(name):
    prof = name.split("|")[0]
    cfg, D, Z = base(prof)
    spec = MV.case_specs()["tot_cal_comp"]
    rows = []
    for i in range(N):
        c, disp = MV.run_cfg_case(cfg, D[i], spec, i, "base")
        if prof == "B1":
            c.update(WL.web_over(D[i], Z[i], WL.CASES["W1p"], float(cfg.get("throat_jref") or 0.0))[0])
        c.update(ARMS[name])
        res = R.fly(c, disp, nrec=10)[0]
        row = dict(run=i, ok=int(R.success(res)))
        row.update({k: float(res[k]) for k in KEEP if k != "ok"})
        rows.append(row)
    return rows


def fname(name):
    return os.path.join(OUT, "pb_" + name.replace("|", "_") + ".csv")


def part_mc():
    os.makedirs(OUT, exist_ok=True)
    jr = json.load(open(f"{S}/throat_growth/throat_growth.json"))["j_ref"]
    k, n = (int(x) for x in SPLIT.split("/"))
    for name in list(ARMS)[k::n]:
        p = fname(name)
        if os.path.exists(p) and os.path.getsize(p) > 100 and os.environ.get("GNC_PB_FORCE") != "1":
            print("exists", name, flush=True)
            continue
        MV.TG_JREF_DEFAULT = float(jr[name.split("|")[0]])
        t0 = time.time()
        rows = fly_arm(name)
        M.write_csv(p, rows)
        ok = np.mean([r["ok"] for r in rows])
        print(f"{name:18s}: P {ok:.3f} exhausted {sum(r['exhausted'] > 0.5 for r in rows)} ({time.time() - t0:.0f} s)", flush=True)


def rows_csv(p):
    return list(csv.DictReader(open(p))) if os.path.exists(p) else None


def col(rows, k):
    return np.array([float(r[k]) for r in rows])


def pct(x, qs=(1, 50, 99)):
    x = np.asarray(x, float)
    if x.size == 0:
        return None
    return dict({f"p{q:02d}": float(np.percentile(x, q)) for q in qs}, min=float(x.min()), max=float(x.max()), n=int(x.size))


def mcnemar(a, b):
    from scipy.stats import binomtest
    lost, gained = int(np.sum(a & ~b)), int(np.sum(~a & b))
    return dict(P_ref=float(a.mean()), P_case=float(b.mean()), lost=lost, gained=gained,
                p_exact=float(binomtest(lost, lost + gained, 0.5).pvalue) if lost + gained else 1.0, n=int(len(a)))


def part_eval():
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, method=__doc__.split("\n\n")[0], n=N, arms={})
    C = {k: rows_csv(fname(k)) for k in ARMS}
    for name, rows in C.items():
        if not rows:
            continue
        prof = name.split("|")[0]
        ref = C.get(f"{prof}|ref")
        ok = col(rows, "ok") > 0.5
        e = dict(spec=ARMS[name], P=float(ok.mean()), P_wilson=[float(x) for x in R.wilson(int(ok.sum()), len(rows))],
                 exhausted=int(np.sum(col(rows, "exhausted") > 0.5)), crash=int(np.sum(col(rows, "crash") > 0.5)),
                 liquid_left_kg=pct(col(rows, "liq_left")), td_vz=pct(col(rows, "td_vz")),
                 mest_e_end_pct=pct(100 * col(rows, "mest_e_end")), h_max=pct(col(rows, "h_max"), (50, 99)))
        if ref and name != f"{prof}|ref":
            e["vs_ref"] = mcnemar(col(ref, "ok") > 0.5, ok)
            e["liquid_left_shift_kg"] = pct(col(rows, "liq_left") - col(ref, "liq_left"))
            if prof == "A1":
                e["t_relight_shift_s"] = pct(col(rows, "t_relight") - col(ref, "t_relight"))
                e["h_ign_shift_m"] = pct(col(rows, "h_ign") - col(ref, "h_ign"))
        if ARMS[name].get("prg_on"):
            dur = col(rows, "prg_dur")
            T_ = ARMS[name]["prg_T"]
            e["purge"] = dict(T=T_, duration_s=pct(dur), truncated_runs=int(np.sum((dur >= 0) & (dur < T_ - 1e-6))),
                              no_purge_runs=int(np.sum(dur < 0)),
                              wait_runs=int(np.sum(col(rows, "prg_wait") > 1e-9)), wait_s=pct(col(rows, "prg_wait")[col(rows, "prg_wait") > 1e-9]),
                              mass_g=pct(1e3 * col(rows, "prg_mass")), start_height_m=pct(col(rows, "prg_h0")),
                              tilt_max_during_deg=pct(col(rows, "prg_tilt_max")), tilt_at_lift_deg=pct(col(rows, "prg_tilt_lift")),
                              body_rate_max_during_dps=pct(col(rows, "prg_rate_max")))
        if ARMS[name].get("blf_on"):
            e["bleed"] = dict(bled_g=pct(1e3 * col(rows, "blf_mass")), time_s=pct(col(rows, "blf_time")),
                              thrust_factor_min=pct(col(rows, "blf_kF_min")))
        out["arms"][name] = e
    out["inputs"] = dict(purge_sizing=dict(path="/home/claude/work/combustion/data/v2/v2p4/purge_sizing_v2p4.json",
                                           note="Combustion workdir (hub publication pending): 0.6 mm 11.25 g/s liquid, 1.19 N; "
                                                "0.8 mm 20.0 g/s, 2.12 N; T_p for P_abort 0: 1.0-2.0 s; traps A 13.533 / B 19.0 cm3"),
                         relay="coordinator 2026-10-13: purge 2-3 s ending at the lift; stuck bleed 6.3-19.4 g/s, 3-8 % / up to "
                               "14 % of the engine flow; trap zero-abort limit 18.86 cm3 at W 0.65 s, 13.53 cm3 -> P_abort 0")
    with open(os.path.join(OUT, "purge_bleed.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    for name, e in out["arms"].items():
        v = e.get("vs_ref", {})
        pg = e.get("purge", {})
        bl = e.get("bleed", {})
        print(f"{name:18s} P {e['P']:.3f} ({v.get('lost', '-')}/{v.get('gained', '-')} p {v.get('p_exact', float('nan')):.3g}) exh "
              f"{e['exhausted']} liq p01 {1e3 * e['liquid_left_kg']['p01']:.0f} g min {1e3 * e['liquid_left_kg']['min']:.0f} | mest_end "
              f"p01/p99 {e['mest_e_end_pct']['p01']:+.2f}/{e['mest_e_end_pct']['p99']:+.2f} %"
              + (f" | purge dur min {pg['duration_s']['min']:.2f} p01 {pg['duration_s']['p01']:.2f} trunc {pg['truncated_runs']} wait "
                 f"{pg['wait_runs']} tilt p99/max {pg['tilt_max_during_deg']['p99']:.2f}/{pg['tilt_max_during_deg']['max']:.2f} lift "
                 f"p99 {pg['tilt_at_lift_deg']['p99']:.2f} rate p99 {pg['body_rate_max_during_dps']['p99']:.1f} h0 p01 "
                 f"{pg['start_height_m']['p01']:.0f}" if pg else "")
              + (f" | bled p50/max {bl['bled_g']['p50']:.0f}/{bl['bled_g']['max']:.0f} g kF min {bl['thrust_factor_min']['min']:.3f}"
                 if bl else ""), flush=True)


def main():
    if "mc" in PARTS:
        part_mc()
    if "eval" in PARTS:
        part_eval()


if __name__ == "__main__":
    main()

"""m2_b1_m60 v1.2 (GNC rev2, 2026-10-13; v1.1: eval adds the default B1 grain gate of lead line 172 (3); v1.2: eval adds the end-of-record web and the runs where the burn limit acted; flights of v1.0): B1 62 m (decided web-limit FSW W1p + flown mass estimator tot_cal_comp, FSW-R2)
against (i) +0.60 kg on the fixed engine module (bleed-valve mass risk, LEAD line 164 (7); point mass at ledger item P07
'fixed TVC module' z, DESIGN placement) and (ii) the stuck-open head-end bleed of the decided purge path at its all-liquid
flow 31.24 g/s from the first ignition (Combustion purge_vented_mass_v2p4 flows_g_s.all_liquid; additive, no jet thrust,
no FSW model; fault state for the FMEA and the RG-16 over-read term). 500 runs, seed 101 draws and WL measurement draws,
identical in every arm (paired).
Method: as m2_purge_bleed v1.x B1 arms (WL.base_cfg, MV.run_cfg_case 'base', WL.web_over W1p, MV.TG_JREF_DEFAULT = B1).
Output: OUT/b1_<arm>.csv, OUT/b1_m60.json. Env: m2r2_env.sh; GNC_B1_OUT (out/rev2/b1_m60), GNC_B1_PARTS (mc,eval),
GNC_B1_SPLIT (0/1)."""
import json
import os
import sys
import time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_mass_est_v2 as MV  # noqa: E402
import m2_web_limit as WL  # noqa: E402
import m2_mc6 as M  # noqa: E402
import m2_rg01_refly as F  # noqa: E402

VERSION = "m2_b1_m60 v1.2"
S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_B1_OUT", f"{S}/rev2/b1_m60")
PARTS = os.environ.get("GNC_B1_PARTS", "mc,eval").split(",")
SPLIT = os.environ.get("GNC_B1_SPLIT", "0/1")
N = 500
ARMS = {"ref": {}, "m60": dict(_m60=True),
        "blf31": dict(blf_on=1, blf_ph=0, blf_mode=0, blf_mdot=0.03124, bl_vj=0.0)}


def fly(name, bay_z):
    cfg = WL.base_cfg()[0]
    D = R.draw(np.random.default_rng(WL.SEED), N, cfg)
    Z = WL.meas_draws(N)
    jr = json.load(open(F.TG))["j_ref"]
    MV.TG_JREF_DEFAULT = float(jr["B1"])
    spec = MV.case_specs()["tot_cal_comp"]
    m = float(cfg["m_n2o"])
    rows = []
    for i in range(N):
        c, disp = MV.run_cfg_case(cfg, D[i], spec, i, "base")
        c.update(WL.web_over(D[i], Z[i], WL.CASES["W1p"], float(cfg.get("throat_jref") or 0.0))[0])
        c.update(fct_comp=1)
        a = ARMS[name]
        if a.get("_m60"):
            c.update(ballast=F.M60, ballast_z=bay_z)
        c.update({k: v for k, v in a.items() if not k.startswith("_")})
        res = R.fly(c, disp, nrec=10)[0]
        row = R.flat_row(i, D[i], res, R.success(res), cfg)
        row["m_n2o"] = m
        rows.append(row)
    return rows


def part_mc():
    os.makedirs(OUT, exist_ok=True)
    k, n = (int(x) for x in SPLIT.split("/"))
    bay_z = F.engine_bay_mid()[0]
    for name in list(ARMS)[k::n]:
        p = os.path.join(OUT, f"b1_{name}.csv")
        if os.path.exists(p) and os.environ.get("GNC_B1_FORCE") != "1":
            print("exists", name, flush=True)
            continue
        t0 = time.time()
        rows = fly(name, bay_z)
        M.write_csv(p, rows)
        ok = np.array([r["ok"] for r in rows]) > 0.5
        print(f"B1 {name:6s}: P {ok.mean():.3f} exhausted {int(sum(r['exhausted'] > 0.5 for r in rows))} ({time.time() - t0:.0f} s)",
              flush=True)


def part_eval():
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, method=__doc__.split("\n")[0], mass_risk_kg=F.M60,
               mass_risk_z_m=F.engine_bay_mid()[0], cases={}, paired={})
    ref = F.rows_csv(os.path.join(OUT, "b1_ref.csv"))
    # v1.1 (lead line 172 (3)): B1 on the DEFAULT pre-flight grain gate "lead rule OR a_meas >= 1.25 -> change the grain":
    # flown engines are those with a_meas < 1.25 (the lead rule needs a_meas >= 1.25 as well); same measurement draws as the flights
    cfg = WL.base_cfg()[0]
    D = R.draw(np.random.default_rng(WL.SEED), N, cfg)
    Z = WL.meas_draws(N)
    jref = float(cfg.get("throat_jref") or 0.0)
    am = np.array([WL.web_over(D[i], Z[i], WL.CASES["W1p"], jref)[1] for i in range(N)])
    nm = np.array([WL.web_over(D[i], Z[i], WL.CASES["W1p"], jref)[2] for i in range(N)])
    kept = ~(((am >= WL.GATE_A) & (nm <= WL.GATE_N)) | (am >= 1.25))
    out["default_gate"] = dict(rule="lead rule (a_meas >= 1.25 and n_meas <= 0.40) OR a_meas >= 1.25 -> grain change (LEAD line 172 (3))",
                               kept_runs=int(kept.sum()), kept_fraction=float(kept.mean()), cases={}, paired={})
    for name in ARMS:
        r = F.rows_csv(os.path.join(OUT, f"b1_{name}.csv"))
        if not r:
            continue
        ok = F.col(r, "ok") > 0.5
        fm = {}
        for x, o in zip(r, ok):
            if not o:
                fm[F.fail_mode(x)] = fm.get(F.fail_mode(x), 0) + 1
        us = F.usable_g(r)
        e = dict(P=float(ok.mean()), P_wilson=[float(v) for v in R.wilson(int(ok.sum()), len(ok))], fail_modes=fm,
                 exhausted=int(np.sum(F.col(r, "exhausted") > 0.5)), usable_reserve_g=F.pct(us, (1, 5, 50)),
                 hop_apex_m=F.pct(F.col(r, "h_max"), (1, 50, 99)), td_vz=F.pct(F.col(r, "td_vz"), (1, 50, 99)),
                 m_land_kg=F.pct(F.col(r, "m_land"), (1, 50, 99)))
        if name == "blf31":
            e["bled_mass_g"] = F.pct(1e3 * F.col(r, "blf_mass"), (50, 99))
            e["bleed_time_s"] = F.pct(F.col(r, "blf_time"), (50, 99))
        # v1.2: fuel web at the end of the record (sim6 amendment W, limit action ON in W1p) and runs where the limit acted
        wt, wl = F.col(r, "web_t_end"), F.col(r, "web_tL") >= 0.0
        e["web_end_mm"] = F.pct(1e3 * wt, (1, 50))
        e["web_end_below_1mm"] = int(np.sum(wt < 1e-3))
        e["web_limit_acted"] = int(np.sum(wl))
        out["cases"][name] = e
        okk = ok[kept]
        out["default_gate"]["cases"][name] = dict(P=float(okk.mean()), n=int(kept.sum()),
                                                  P_wilson=[float(v) for v in R.wilson(int(okk.sum()), int(kept.sum()))],
                                                  exhausted=int(np.sum(F.col(r, "exhausted")[kept] > 0.5)),
                                                  usable_reserve_g=F.pct(us[kept], (1, 5, 50)),
                                                  web_end_below_1mm=int(np.sum(wt[kept] < 1e-3)), web_limit_acted=int(np.sum(wl[kept])),
                                                  web_end_mm=F.pct(1e3 * wt[kept], (1, 50)))
        if ref and name != "ref":
            out["default_gate"]["paired"][name] = dict(F.mcnemar((F.col(ref, "ok") > 0.5)[kept], okk),
                                                       reserve_shift_g=F.pct((us - F.usable_g(ref))[kept], (1, 50, 99)))
        if ref and name != "ref":
            out["paired"][name] = dict(F.mcnemar(F.col(ref, "ok") > 0.5, ok),
                                       reserve_shift_g=F.pct(us - F.usable_g(ref), (1, 50, 99)),
                                       apex_shift_m=F.pct(F.col(r, "h_max") - F.col(ref, "h_max"), (1, 50, 99)))
        print(f"B1 {name:6s} P {e['P']:.3f} ex {e['exhausted']} res p01/p50 {e['usable_reserve_g']['p01']:.0f}/"
              f"{e['usable_reserve_g']['p50']:.0f} g apex p50 {e['hop_apex_m']['p50']:.1f} fm {fm} "
              f"{out['paired'].get(name, '')}", flush=True)
    print("default gate:", out["default_gate"]["kept_runs"], {k: (round(v["P"], 4), v["exhausted"]) for k, v in out["default_gate"]["cases"].items()},
          {k: (v["lost"], v["gained"], round(v["p_exact"], 3)) for k, v in out["default_gate"]["paired"].items()}, flush=True)
    with open(os.path.join(OUT, "b1_m60.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", os.path.join(OUT, "b1_m60.json"), flush=True)


if __name__ == "__main__":
    if "mc" in PARTS:
        part_mc()
    if "eval" in PARTS:
        part_eval()

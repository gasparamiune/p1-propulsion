"""rg05_sens v1 (independent GNC review, 2026-10-13): paired 6-DOF sensitivity runs on the author's simulator (unchanged
code, executed from the byte-identical scratch copy checked by rg02), for items the published Monte Carlo does not disperse
or holds at ASSUMED values.

Method
  - Same draws as the published cases: numpy default_rng(101), N = 500 (+ the author's add-on generators). Each sensitivity
    applies ONE change to every run of the base case and is compared run by run with the re-flown base (exact McNemar on
    the discordant pairs, Wilson 95 % interval).
  - Changes are applied in this harness only (the hub code is not modified):
      ca_legs x f, ca_nf x f : multiplicative factors added to the per-run aero uncertainty dict (truth only; the FSW
                               nominal drag models drag_cda_nom / kest_cda_* are built from the nominal set and do not change).
                               gnc.json v3 tags CA 'ASSUMED (+/-30 %)' but the MC disperses CA_tf only.
      a_bias x k             : the drawn accelerometer bias vector scaled by k (same normal deviates; 1 mg ASSUMED 1-sigma).
      thrust x f             : the drawn thrust_scale of every run multiplied by f (low-thrust engine; tests k_est_asc 2).
      m_est_err x k          : the drawn constant mass-estimate error scaled by k.
      gust x k               : the drawn gust scale multiplied by k.
      slew s                 : cfg slew = s F_max/s (author ASSUMED 5; ENG-03 asks >= 1000 N/s = 2 F_max/s).
      k_est_asc 0            : the v2.7 ascent / floor estimator off (B1).
  - Also: the author's nominal flights (no wind, no noise) with records, for the rg03 comparison, and a fine h_target scan of
    the governing regression corner (a 0.6, n 0.68, g 0.11) recording MECO time / apex / burn time.
Output: rg05_sens.json.  Run on one core: NUMBA_NUM_THREADS=1 nice -n 10 /opt/engine-venv/bin/python -I rg05_sens.py
"""
import hashlib
import json
import math
import os
import sys
import time
from fractions import Fraction
from math import comb

sys.dont_write_bytecode = True
SCR = os.environ.get("RG_SCRATCH", "/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad")
COPY = os.environ.get("RG_SIMCOPY", f"{SCR}/simcopy")
HUB = "/home/claude/work/shared-fallback/engine"
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("GNC_IFACE", f"{SCR}/iface_v3c")
os.environ.setdefault("GNC_ACT_RATE", f"{SCR}/iface_v3c/actuator_rate_check_v2.json")
os.environ.setdefault("NUMBA_CACHE_DIR", f"{SCR}/numba_cache")
os.environ.setdefault("NUMBA_NUM_THREADS", "1")
for k in ("GNC_OUT", "GNC_V28_OUT", "GNC_RB_OUT", "GNC_TG_OUT"):
    os.environ[k] = f"{SCR}/out/{k.lower()}"
sys.path.insert(0, COPY)
sys.path.insert(0, f"{COPY}/scripts")
import numpy as np  # noqa: E402
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_relight_v28 as RV  # noqa: E402
import m2_regband_mc as RBM  # noqa: E402
import m2_prop_closure as PC  # noqa: E402
import m2_throat_mc as TG  # noqa: E402

PARTS = os.environ.get("RG05_PARTS", "nominal,scan,mc").split(",")
OUTP = os.path.join(HERE, "rg05_sens.json")


def wilson(k, n, z=1.959963984540054):
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    hw = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [max(0.0, c - hw), min(1.0, c + hw)]


def mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = 2 * Fraction(sum(comb(n, i) for i in range(k + 1)), 2 ** n)
    return float(min(p, 1))


_ORIG_RUN_CFG = R.run_cfg
AERO_EXTRA = {}


def _run_cfg(cfg, dr):
    c, disp = _ORIG_RUN_CFG(cfg, dr)
    if AERO_EXTRA:
        au = dict(c.get("aero_unc") or {})
        au.update(AERO_EXTRA)
        c["aero_unc"] = au
    return c, disp


R.run_cfg = _run_cfg


def mod_draw(dr, mod):
    d = dict(dr)
    if "a_bias" in mod:
        d["a_b"] = tuple(mod["a_bias"] * x for x in dr["a_b"])
    if "thrust" in mod:
        d["thrust_scale"] = dr["thrust_scale"] * mod["thrust"]
    if "m_est" in mod:
        d["m_est_err"] = dr["m_est_err"] * mod["m_est"]
    if "gust" in mod:
        d["_gust_scale"] = dr["_gust_scale"] * mod["gust"]
    return d


def fly_case(over, mod, n=500):
    over = dict(over)
    m = float(over.pop("m_fixed"))
    cfg_over = dict(over, m_n2o=m)
    for k in ("slew", "k_est_asc"):
        if k in mod:
            cfg_over[k] = mod[k]
    cfg_over.update(mod.get("cfg", {}))
    cfg = R.cfg_of(**cfg_over)
    D = R.draw(np.random.default_rng(101), n, cfg)
    AERO_EXTRA.clear()
    for k in ("ca_legs", "ca_nf"):
        if k in mod:
            AERO_EXTRA[k] = mod[k]
    out = []
    for i in range(n):
        res = R.run_one(cfg, mod_draw(D[i], mod))
        out.append(dict(ok=bool(R.success(res)), exhausted=bool(res["exhausted"] > 0.5), liq_left=float(res["liq_left"]),
                        burn_time=float(res["burn_time"]), prop_used=float(res["prop_used"]), td_vz=float(res["td_vz"]),
                        td_vh=float(res["td_vh"]), td_rate=float(res["td_rate"]), td_tilt=float(res["td_tilt"]),
                        tipover=bool(res["tipover"] > 0.5), crash=bool(res["crash"] > 0.5), landed=bool(res["landed"] > 0.5),
                        h_max=float(res["h_max"])))
    AERO_EXTRA.clear()
    return out


def summ(rows, m_load=2.0):
    ok = np.array([r["ok"] for r in rows])
    k = int(ok.sum())
    n = len(rows)
    usable = np.array([r["liq_left"] - 0.03 * m_load for r in rows])
    bt = np.array([r["burn_time"] for r in rows])
    fm = {}
    for r in rows:
        if not r["ok"]:
            why = ("exhausted" if r["exhausted"] else "crash/no_td" if (r["crash"] or not r["landed"]) else "tipover" if r["tipover"]
                   else "vz" if abs(r["td_vz"]) > 2.0 else "vh" if r["td_vh"] > 0.5 else "tilt" if r["td_tilt"] > 5.0 else "rate")
            fm[why] = fm.get(why, 0) + 1
    return dict(n=n, P=k / n, ci95=wilson(k, n), n_exhausted=int(sum(r["exhausted"] for r in rows)),
                usable_p01=float(np.percentile(usable, 1)), usable_min=float(usable.min()),
                burn_p50_p99_max=[float(np.percentile(bt, 50)), float(np.percentile(bt, 99)), float(bt.max())], fail_modes=fm)


def paired(base, case):
    b = sum(1 for x, y in zip(base, case) if x["ok"] and not y["ok"])
    c = sum(1 for x, y in zip(base, case) if (not x["ok"]) and y["ok"])
    return dict(lost=b, gained=c, p_exact=mcnemar(b, c))


def part_mc(out):
    tabs = RV.e0e2_tables()
    bases = {
        "B1_62m_band_growth (rbl_B1_lead62_pc_k2)": (RBM.cases(None)["rbl_B1_lead62_pc_k2"][0],
                                                     f"{HUB}/01-systems-gnc/results/regband/mc6_runs_rbl_B1_lead62_pc_k2_rb.csv.gz"),
        "A1_liq_plan0.81 (v28_liq_p0.81_A1_none_k2)": (RV.case_over("A1_none", "liq", 0.81, tabs),
                                                       f"{HUB}/01-systems-gnc/results/relight_v28/mc6_runs_v28_liq_p0.81_A1_none_k2_v28.csv.gz"),
    }
    mods_B = [("ca_legs x1.3", dict(ca_legs=1.3)), ("ca_legs x0.7", dict(ca_legs=0.7)), ("ca_nf x1.3", dict(ca_nf=1.3)),
              ("ca_nf x0.7", dict(ca_nf=0.7)), ("a_bias x3 (3 mg)", dict(a_bias=3.0)), ("a_bias x10 (10 mg)", dict(a_bias=10.0)),
              ("thrust x0.90", dict(thrust=0.90)), ("m_est_err x2", dict(m_est=2.0)), ("gust x2", dict(gust=2.0)),
              ("slew 2 Fmax/s (ENG-03 1000 N/s)", dict(slew=2.0)), ("k_est_asc 0", dict(k_est_asc=0)),
              ("ca_legs x1.3 + thrust x0.90", dict(ca_legs=1.3, thrust=0.90))]
    mods_A = [("ca_legs x1.3", dict(ca_legs=1.3)), ("ca_legs x0.7", dict(ca_legs=0.7)), ("a_bias x3 (3 mg)", dict(a_bias=3.0)),
              ("a_bias x10 (10 mg)", dict(a_bias=10.0)), ("thrust x0.90", dict(thrust=0.90)), ("m_est_err x2", dict(m_est=2.0)),
              ("gust x2", dict(gust=2.0)), ("slew 2 Fmax/s (ENG-03 1000 N/s)", dict(slew=2.0))]
    import csv
    import gzip
    for bname, (over, pub) in bases.items():
        t0 = time.time()
        base = fly_case(over, {})
        with gzip.open(pub, "rt") as f:
            pub_ok = [int(float(r["ok"])) for r in csv.DictReader(f)]
        rep = sum(1 for a, b in zip(pub_ok, base) if a == int(b["ok"]))
        out["mc"][bname] = dict(base=summ(base), base_reproduces_published_ok=f"{rep}/{len(base)}", cases={})
        print(bname, "base", out["mc"][bname]["base"], "reproduces", rep, f"{time.time() - t0:.0f}s", flush=True)
        for mname, mod in (mods_B if bname.startswith("B1") else mods_A):
            t1 = time.time()
            rows = fly_case(over, mod)
            s = summ(rows)
            s.update(paired(base, rows))
            out["mc"][bname]["cases"][mname] = s
            print(f"   {mname:34s} P {s['P']:.3f} [{s['ci95'][0]:.3f}, {s['ci95'][1]:.3f}] -{s['lost']}/+{s['gained']} p {s['p_exact']:.3g} "
                  f"exh {s['n_exhausted']} usable p01 {s['usable_p01']:.3f} burn {np.round(s['burn_p50_p99_max'], 2).tolist()} "
                  f"{s['fail_modes']} {time.time() - t1:.0f}s", flush=True)
            json.dump(out, open(OUTP, "w"), indent=1)


def part_mc2(out):
    """ENG-07d actuator basis for B1 (act_model 1, 6.6 V, supply chain D, J_int 1.6e-3, tracked notch with mistune; the
    configuration of the author's A1J / m2_J1.6_n15 basis), and A1J sensitivities."""
    import csv
    import gzip
    import m2_mechv2_mc as MV
    eng07d = dict(MV.ACT, act_Jint=MV.J_C, **MV.N15)
    tabs = RV.e0e2_tables()
    bases = {
        "B1_62m_band_growth (rbl_B1_lead62_pc_k2) [mc2]": (RBM.cases(None)["rbl_B1_lead62_pc_k2"][0],
                                                           f"{HUB}/01-systems-gnc/results/regband/mc6_runs_rbl_B1_lead62_pc_k2_rb.csv.gz"),
        "A1J_liq_plan0.81 (v28_liq_p0.81_A1J_none_k2)": (RV.case_over("A1J_none", "liq", 0.81, tabs),
                                                         f"{HUB}/01-systems-gnc/results/relight_v28/mc6_runs_v28_liq_p0.81_A1J_none_k2_v28.csv.gz"),
    }
    mods = {
        "B1": [("ENG-07d actuator basis", dict(cfg=eng07d)), ("ENG-07d + slew 2 Fmax/s", dict(cfg=eng07d, slew=2.0)),
               ("ENG-07d + gust x2", dict(cfg=eng07d, gust=2.0)), ("ENG-07d + thrust x0.90", dict(cfg=eng07d, thrust=0.90))],
        "A1": [("gust x2", dict(gust=2.0)), ("slew 2 Fmax/s (ENG-03 1000 N/s)", dict(slew=2.0)), ("thrust x0.90", dict(thrust=0.90)),
               ("m_est_err x2", dict(m_est=2.0)), ("ca_legs x1.3", dict(ca_legs=1.3))],
    }
    out.setdefault("mc2", {})
    out["mc2"]["eng07d_cfg"] = {k: (v if isinstance(v, (int, float, str)) or v is None else str(v)) for k, v in eng07d.items()}
    for bname, (over, pub) in bases.items():
        t0 = time.time()
        base = fly_case(over, {})
        with gzip.open(pub, "rt") as f:
            pub_ok = [int(float(r["ok"])) for r in csv.DictReader(f)]
        rep = sum(1 for a, b in zip(pub_ok, base) if a == int(b["ok"]))
        out["mc2"][bname] = dict(base=summ(base), base_reproduces_published_ok=f"{rep}/{len(base)}", cases={})
        print(bname, "base", out["mc2"][bname]["base"], "reproduces", rep, f"{time.time() - t0:.0f}s", flush=True)
        for mname, mod in mods["B1" if bname.startswith("B1") else "A1"]:
            t1 = time.time()
            rows = fly_case(over, mod)
            s_ = summ(rows)
            s_.update(paired(base, rows))
            out["mc2"][bname]["cases"][mname] = s_
            print(f"   {mname:34s} P {s_['P']:.3f} [{s_['ci95'][0]:.3f}, {s_['ci95'][1]:.3f}] -{s_['lost']}/+{s_['gained']} p {s_['p_exact']:.3g} "
                  f"exh {s_['n_exhausted']} usable p01 {s_['usable_p01']:.3f} burn {np.round(s_['burn_p50_p99_max'], 2).tolist()} "
                  f"{s_['fail_modes']} {time.time() - t1:.0f}s", flush=True)
            json.dump(out, open(OUTP, "w"), indent=1)


def part_nominal(out):
    I = {n: i for i, n in enumerate(s6.REC_NAMES)}
    tabs = RV.e0e2_tables()
    cases = {
        "A1_plan0.81_liq_med": dict(PC.DC["A1"], k_est_asc=2, t_ign=float(tabs["liq"]["check"]["median_given"]) if "check" in tabs["liq"] else 0.3152,
                                    t_ign_est=0.81),
        "B1_85m": dict(PC.DC["B1"], h_target=85.0, k_est_asc=2),
        "B1_62m": dict(PC.DC["B1"], h_target=62.0, k_est_asc=2),
    }
    for nm, over in cases.items():
        r = PC.nominal(over, PC.M_TANK)
        cfg = R.cfg_of(**dict(over, m_n2o=PC.M_TANK))
        res, rec, info = R.fly(dict(cfg, noise=False, wind=0.0, gust=False, rec_dt=0.1), nrec=20000)
        cols = [c for c in ("t", "z", "vz", "F", "Fcmd", "mox", "mf", "Ptank", "mliq", "m", "Ttank", "keff", "phase", "Fceil", "qdyn") if c in I]
        hist = rec[:, [I[c] for c in cols]].round(5).tolist()
        out["nominal"][nm] = dict(closure={k: (float(v) if isinstance(v, (int, float, np.floating)) else v) for k, v in r.items()},
                                  t_meco=float(res["t_meco"]), h_meco=float(res["h_meco"]), v_meco=float(res["v_meco"]),
                                  h_ign=float(res["h_ign"]), v_ign=float(res["v_ign"]), t_relight=float(res["t_relight"]),
                                  hist_cols=cols, hist=hist)
        print(nm, {k: r[k] for k in ("n2o_burned", "reserve_frac", "burn_time_s", "impulse_Ns", "h_max", "liquid_left", "fuel_burned")},
              "t_meco", res["t_meco"], "h_meco", res["h_meco"], "v_meco", res["v_meco"], flush=True)
    print("REC cols available:", s6.REC_NAMES, flush=True)
    json.dump(out, open(OUTP, "w"), indent=1)


def part_scan(out):
    rows = []
    for h in np.arange(61.0, 63.51, 0.25):
        o = dict(RBM.B1, h_target=float(h), reg_a=0.6, reg_n=0.68, throat_g=0.11, throat_loop=1)
        o["throat_jref"] = TG.j_ref({k: v for k, v in o.items() if k not in ("throat_g", "throat_jref")})[0]
        r = PC.nominal(o, PC.M_TANK)
        cfg = R.cfg_of(**dict(o, m_n2o=PC.M_TANK))
        res, rec, info = R.fly(dict(cfg, noise=False, wind=0.0, gust=False, rec_dt=0.01), nrec=20000)
        row = dict(h_target=float(h), reserve=float(r["reserve_frac"]), n2o_burned=float(r["n2o_burned"]), burn_time=float(r["burn_time_s"]),
                   h_max=float(r["h_max"]), t_meco=float(res["t_meco"]), h_meco=float(res["h_meco"]), v_meco=float(res["v_meco"]),
                   t_td=float(res["td_t"]), v_ign=float(res["v_ign"]), h_ign=float(res["h_ign"]), t_relight=float(res["t_relight"]))
        rows.append(row)
        print(row, flush=True)
    out["scan_a0.6_n0.68_g0.11"] = rows
    json.dump(out, open(OUTP, "w"), indent=1)


def main():
    out = dict(script="rg05_sens v1", copy=COPY, nominal={}, mc={})
    try:
        out.update({k: v for k, v in json.load(open(OUTP)).items() if k in ("nominal", "mc", "mc2", "scan_a0.6_n0.68_g0.11")})
    except (OSError, ValueError):
        pass
    if "nominal" in PARTS:
        part_nominal(out)
    if "scan" in PARTS:
        part_scan(out)
    if "mc" in PARTS:
        part_mc(out)
    if "mc2" in PARTS:
        part_mc2(out)
    json.dump(out, open(OUTP, "w"), indent=1)


if __name__ == "__main__":
    main()

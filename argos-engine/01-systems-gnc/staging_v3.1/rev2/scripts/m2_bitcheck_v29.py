"""m2_bitcheck_v29 v1.1 (GNC rev2, 2026-10-13; v1.1: run 1 (out/rev2/bitcheck_v29/bitcheck_v29_run1_FAIL.*) failed two TEST
expectations, kept as evidence: G1 compared the purge mass with the record LIQUID drop (81.6 g vs 73.0 g: the liquid also boils
off into the ullage) -> now the vehicle-mass drop; N4 expected the KeyError on dynamics_for_GNC, the build stops earlier on
'stiffness' -> any KeyError, the key recorded. G6 now flies the exact rev1 P30 arm. The simulator was not changed): checks of sim6/run6 v2.9-dev (amendments G, K, V; strict inputs N4).
A0  options off vs stored v2.8 tables: rel_A1_none_rel1 / rel_A1J_pc_rel1 (out/release_rule, sim6 v2.8-dev, decided rule
    rel_mode 1 rel_to 0.10, combustion.json v2.3 via iface_v3c): first K runs + every failed run, every stored result
    field compared exactly, flown now on combustion.json v2.4 (iface_v3d) in strict mode with the pin list.
A1  differential against the rev1 simulator copy (staging_v3.1/rev1/sim/gncsim_v2.8-dev_MWFPRS, sha256 checked against
    MANIFEST_rev1, run from a scratch copy in a subprocess): identical (cfg, disp) inputs, every result field common to
    both versions compared exactly; cases exercise the v2.8 amendments M (flown mass estimator, Pc lost), W (web limit,
    B apex predictor), F (stuck pintle, detectors, abort), P (forced purge, stuck-open bleed), R/S (release rule,
    plateau) with the v2.9-dev options off.
G   amendment G (decided purge sequence + trigger gate), nominal A1 on the 1 ms record + 500-run P30 reproduction.
K   amendment K (freeze k_hat / B apex predictor thrust on Pc invalid).
V   amendment V (Pc invalid inside [E2, release], release alternatives).
N   strict inputs (REV-GNC-2 N4/N5): unreadable GNC_IFACE, pin mismatch, version assertion, electronics v2, combustion
    v2.3 -> v2.4 identity on the decided purge path.
RF  the final simulator reproduces the stored RG-01 re-fly tables (first GNC_BIT_KR runs + every failed run of three arms).
Env: m2r2_env.sh; GNC_RES (default out/rev2/bitcheck_v29), GNC_BIT_K (40), GNC_BIT_KR (20), GNC_BIT_PARTS (A0,A1,G,K,V,N,RF).
Output: GNC_RES/bitcheck_v29.json"""
import csv
import hashlib
import json
import os
import pickle
import shutil
import subprocess
import sys
import numpy as np

os.environ.setdefault("GNC_PC_RATCHET", "1")
DEV = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, DEV)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6, engine_v2 as EV  # noqa: E402
import m2_eng03_rate as E  # noqa: E402
import m2_mass_est_v2 as MV  # noqa: E402
import m2_web_limit as WL  # noqa: E402

VERSION = "m2_bitcheck_v29 v1.1 (+code hashes)"
S = "/home/claude/work/space/out"
RES = os.environ.get("GNC_RES", f"{S}/rev2/bitcheck_v29")
K = int(os.environ.get("GNC_BIT_K", "40"))
PARTS = os.environ.get("GNC_BIT_PARTS", "A0,A1,G,K,V,N,RF").split(",")
N = 500
I = {n: i for i, n in enumerate(s6.REC_NAMES)}
PN = {n: i for i, n in enumerate(s6.PAR_NAMES)}
NEW = [n for n in s6.RES_NAMES if n.startswith(("pgg_", "pcf_"))]
DEC = dict(rel_mode=1, rel_to=0.10, fct_comp=1)
G73 = dict(prg_on=1, pgg_on=1, prg_book=1, prg_jet=0, prg_mdot=0.0292, prg_mdot_hat=0.0292)
PS10 = dict(prg_on=1, prg_T=2.5, prg_lead=0.5, prg_book=1, prg_jet=0, prg_prio=1, prg_mdot=0.0313, prg_mdot_hat=0.0313)
BLEED = dict(blf_on=1, blf_ph=4, blf_mdot=0.03124, blf_mode=0, bl_vj=0.0)
REV1 = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/rev1"
REV1_SIM = "sim/gncsim_v2.8-dev_MWFPRS"
SCR = os.environ.get("GNC_BIT_SCRATCH", "/home/claude/work/space/scratch_bit29")
RUNNER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "m2_bit29_runner.py")
JR = json.load(open(f"{S}/throat_growth/throat_growth.json"))["j_ref"]


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def cfg_of_base(base):
    over, bcsv, bjson = E.base_ref(base)
    m = json.load(open(bjson))["m_n2o_mc_kg"]
    return R.cfg_of(**dict({k: v for k, v in over.items() if k != "m_fixed"}, m_n2o=float(m))), bcsv


def r2_case(cfg, dr, i, base, extra=None):
    """(c, disp) of run i on the declared flight FSW (FSW-R2): stored v2.8 base + flown mass estimator tot_cal_comp +
    decided release rule + fct_comp; extra = arm overrides."""
    MV.TG_JREF_DEFAULT = float(JR["A1J" if base.startswith("A1J") else ("B1" if "B1" in base else "A1")])
    c, disp = MV.run_cfg_case(cfg, dr, MV.case_specs()["tot_cal_comp"], i, "base")
    c.update(DEC)
    if extra:
        c.update(extra)
    return c, disp


def diff(a, b, names):
    m = []
    for k in names:
        x, y = float(a[k]), float(b[k])
        if not (x == y or (np.isnan(x) and np.isnan(y))):
            m.append(dict(field=k, ref=x, new=y))
    return m


def nominal(cfg, **kw):
    return R.fly(dict(cfg, noise=False, wind=0.0, gust=False, rec_dt=0.001, **kw), nrec=200000)


def runner(args, env=None, timeout=1800):
    e = dict(os.environ)
    if env:
        for k, v in env.items():
            if v is None:
                e.pop(k, None)
            else:
                e[k] = v
    p = subprocess.run([sys.executable, RUNNER] + args, env=e, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout[-3000:], p.stderr[-3000:]


# ------------------------------------------------------------------------------------------------------------------ A0
def part_a0():
    out, ok = {}, True
    for base in ("A1_none", "A1J_pc"):
        cfgb, _ = cfg_of_base(base)
        p = os.path.join(S, "release_rule", f"rel_{base}_rel1.csv")
        rows = list(csv.DictReader(open(p)))
        D = R.draw(np.random.default_rng(101), N, cfgb)
        idx = list(range(K)) + [i for i, r in enumerate(rows) if int(float(r["ok"])) == 0 and i >= K]
        mism, nf = [], 0
        for i in idx:
            c, disp = R.run_cfg(cfgb, D[i])
            res = R.fly(dict(c, rel_mode=1, rel_to=0.10), disp, nrec=10)[0]
            for k in rows[i]:
                if k in s6.RES_NAMES:
                    nf += 1
                    a, b = float(rows[i][k]), float(res[k])
                    if not (a == b or (np.isnan(a) and np.isnan(b))):
                        mism.append(dict(run=i, field=k, ref=a, new=b))
        out[base] = dict(reference=f"{p} (sha256/16 {sha16(p)})", runs=len(idx), failed_runs_included=len(idx) - K,
                         values_compared=nf, mismatches=len(mism), first=mism[:10], passed=bool(nf > 0 and not mism))
        ok &= out[base]["passed"]
        print(f"A0 {base}: runs {len(idx)} values {nf} mismatches {len(mism)}", flush=True)
    return out, ok


# ------------------------------------------------------------------------------------------------------------------ A1
def rev1_copy():
    src = os.path.join(REV1, REV1_SIM)
    man = {}
    for ln in open(os.path.join(REV1, "MANIFEST_rev1.sha256")):
        h, n = ln.split(None, 1)
        man[n.strip().lstrip("*")] = h
    dst = os.path.join(SCR, "rev1sim")
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(os.path.join(dst, "gncsim"))
    files = sorted(f for f in os.listdir(src) if f.endswith(".py"))
    bad = []
    for f in files:
        h = hashlib.sha256(open(os.path.join(src, f), "rb").read()).hexdigest()
        if man.get(f"{REV1_SIM}/{f}") != h:
            bad.append(f)
        shutil.copy2(os.path.join(src, f), os.path.join(dst, "gncsim", f))
    os.symlink(os.path.join(DEV, "data"), os.path.join(dst, "data"))
    return dst, dict(files=len(files), manifest_mismatch=bad, sim6_sha16=sha16(os.path.join(src, "sim6.py")))


def a1_jobs():
    jobs = []
    for base, tag, extra in (("A1_none", "R2", {}), ("A1J_pc", "R2", {}), ("A1_none", "P", PS10),
                             ("A1J_pc", "Pbf", dict(PS10, **BLEED)), ("A1_none", "S", dict(st_on=1, st_Pc=2.4e5, st_T=0.4)),
                             ("A1_none", "F", dict(flt_on=1)), ("A1_none", "Mpcl", dict(mest_pcl_t=30.0))):
        cfg, _ = cfg_of_base(base)
        D = R.draw(np.random.default_rng(101), 4, cfg)
        for i in range(4):
            c, disp = r2_case(cfg, D[i], i, base, extra)
            jobs.append((f"{base}|{tag}|{i}", c, disp))
    cfg, _, _, _ = WL.base_cfg()
    D = R.draw(np.random.default_rng(WL.SEED), 4, cfg)
    Z = WL.meas_draws(4)
    jref = float(cfg.get("throat_jref") or 0.0)
    for i in range(4):
        for tag, extra in (("W1p", {}), ("W1p_pcl", dict(mest_pcl_t=2.0))):
            c, disp = r2_case(cfg, D[i], i, "B1_62m_W1p")
            c.update(WL.web_over(D[i], Z[i], WL.CASES["W1p"], jref)[0])
            c.update(extra)
            jobs.append((f"B1_62m|{tag}|{i}", c, disp))
    return jobs


def part_a1():
    dst, man = rev1_copy()
    jobs = a1_jobs()
    os.makedirs(SCR, exist_ok=True)
    jp, op = os.path.join(SCR, "a1_jobs.pkl"), os.path.join(SCR, "a1_rev1.pkl")
    pickle.dump(jobs, open(jp, "wb"))
    rc, so, se = runner(["--sim", dst, "--jobs", jp, "--out", op], env=dict(GNC_STRICT="0"))
    if rc != 0:
        print("A1 rev1 runner failed", se[-800:], flush=True)
        return dict(error=se[-800:], copy=man), False
    old = pickle.load(open(op, "rb"))
    cases, ok, nf = {}, not man["manifest_mismatch"], 0
    for name, c, disp in jobs:
        new = R.fly(c, disp, nrec=10)[0]
        common = [k for k in old["res"][name] if k in s6.RES_NAMES]
        m = diff(old["res"][name], new, common)
        nf += len(common)
        cases[name] = dict(fields=len(common), mismatches=len(m), first=m[:5])
        ok &= not m
    print(f"A1 differential vs {old['sim']}: jobs {len(jobs)} values {nf} mismatching jobs "
          f"{sum(1 for v in cases.values() if v['mismatches'])}", flush=True)
    return dict(rev1_sim=old["sim"], rev1_copy=man, jobs=len(jobs), values_compared=nf,
                mismatching_jobs=[k for k, v in cases.items() if v["mismatches"]], cases=cases, passed=bool(ok)), ok


# ------------------------------------------------------------------------------------------------------------------- G
def light_time(rec, n):
    ph = rec[:n, I["phase"]]
    return float(rec[int(np.argmax(ph == 5)), I["t"]]) if np.any(ph == 5) else None


def part_g():
    out, ok = {}, True
    cfg, _ = cfg_of_base("A1_none")
    par = R.build(dict(cfg, **DEC, **G73))[0]
    dt = float(par[PN["dt"]])
    out["dt_s"] = dt
    # G1 decided sequence on the nominal flight
    res, rec, _ = nominal(cfg, **DEC, **G73)
    n = int(res["nrec"])
    t, ml, ph, mt = rec[:n, I["t"]], rec[:n, I["mliq"]], rec[:n, I["phase"]], rec[:n, I["m"]]
    t0, tE0, tfl0, fl = float(res["pgg_t0"]), float(res["pgg_tE0"]), float(res["pgg_tfl0"]), float(res["pgg_fl"])
    a_, b_ = int(np.searchsorted(t, tfl0 - 2 * dt)), int(np.searchsorted(t, tfl0 + fl + 2 * dt))
    dml = float(ml[a_] - ml[b_])
    dmt = float(mt[a_] - mt[b_])     # v1.1: total vehicle mass (the liquid also boils off into the ullage, run 1 evidence)
    t4 = float(t[int(np.argmax(ph >= 4))]) if np.any(ph >= 4) else None
    g1 = dict(src=float(res["pgg_src"]), t_commit=t0, h_commit=float(res["pgg_h0"]), tE0=tE0, hE0=float(res["pgg_hE0"]),
              tE0_minus_commit=tE0 - t0, tfl0_minus_commit=tfl0 - t0, flow_s=fl, purge_mass_g=1e3 * float(res["prg_mass"]),
              record_liquid_drop_g=1e3 * dml, record_vehicle_mass_drop_g=1e3 * dmt, liquid_at_flow_start_g=1e3 * float(ml[a_]), liquid_at_flow_end_g=1e3 * float(ml[b_]),
              tilt_max_in_purge_deg=float(res["prg_tilt_max"]), rate_max_in_purge_dps=float(res["prg_rate_max"]),
              phase4_record_t=t4, gate_open_t=float(res["pgg_topen"]),
              gate_open_h=float(res["pgg_hopen"]), spurious=float(res["pgg_spur"]), plain_fired=float(res["pgg_tgo"]),
              landed_ok=bool(R.success(res)))
    g1["passed"] = bool(g1["src"] == 1.0 and abs(g1["tE0_minus_commit"] - 2.90) <= dt + 1e-9
                        and abs(g1["tfl0_minus_commit"] - 0.35) < 1e-9 and abs(fl - 2.5) <= dt + 1e-9
                        and abs(g1["purge_mass_g"] - 29.2 * fl) < 1e-6 and abs(g1["purge_mass_g"] - 73.0) <= 29.2 * dt + 1e-9
                        and abs(g1["record_vehicle_mass_drop_g"] - g1["purge_mass_g"]) < 0.5
                        and t4 is not None and abs(t4 - tE0) <= 2 * dt + 1e-9 and g1["spurious"] == 0.0
                        and g1["gate_open_t"] <= t0 and tE0 - (tfl0 + fl) >= 0.05 - dt - 1e-9)
    out["G1_sequence_nominal"] = g1
    ok &= g1["passed"]
    print("G1:", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in g1.items()}, flush=True)
    # G2 late commit (no predictor horizon -> commit on the plain trigger, src 3): T_fire = t_go + 0.35 + 1.9 + 0.05 s
    res2 = nominal(cfg, **DEC, **G73, pgg_ant=0.0)[0]
    g2 = dict(src=float(res2["pgg_src"]), tgo=float(res2["pgg_tgo"]), t_commit=float(res2["pgg_t0"]), tE0=float(res2["pgg_tE0"]),
              delay_s=float(res2["pgg_dly"]), flow_s=float(res2["pgg_fl"]), purge_mass_g=1e3 * float(res2["prg_mass"]),
              hE0=float(res2["pgg_hE0"]), hgo=float(res2["pgg_hgo"]), height_cost_m=float(res2["pgg_hgo"] - res2["pgg_hE0"]),
              landed_ok=bool(R.success(res2)))
    g2["passed"] = bool(g2["src"] == 3.0 and abs(g2["t_commit"] - g2["tgo"]) < 1e-9 and abs(g2["delay_s"] - 2.30) <= dt + 1e-9
                        and abs(g2["flow_s"] - 1.9) <= dt + 1e-9)
    out["G2_late_commit_flow_floor"] = g2
    ok &= g2["passed"]
    print("G2:", g2, flush=True)
    # G3 override: planned T_fire far (pgg_Tc 5.0 s); the plain trigger brings it forward, never before 1.9 s of flow
    res3 = nominal(cfg, **DEC, **G73, pgg_Tc=5.0)[0]
    t0_, tgo_, tE0_ = float(res3["pgg_t0"]), float(res3["pgg_tgo"]), float(res3["pgg_tE0"])
    exp_ = max(tgo_ + 0.077 + 0.05, t0_ + 0.35 + 1.9 + 0.05)
    g3 = dict(src=float(res3["pgg_src"]), t_commit=t0_, tgo=tgo_, tE0=tE0_, expected_tE0=exp_, flow_s=float(res3["pgg_fl"]),
              expected_flow_s=min(2.5, exp_ - 0.05 - (t0_ + 0.35)))
    g3["passed"] = bool(g3["src"] == 1.0 and tgo_ > 0 and abs(tE0_ - exp_) <= dt + 1e-9 and tE0_ < t0_ + 5.0
                        and abs(g3["flow_s"] - g3["expected_flow_s"]) <= 2 * dt + 1e-9 and g3["flow_s"] >= 1.9 - dt - 1e-9)
    out["G3_override_never_before_floor"] = g3
    ok &= g3["passed"]
    print("G3:", g3, flush=True)
    # G4 ECU duration cap: scheduled 3.0 s -> 2.5 s of flow
    res4 = nominal(cfg, **DEC, **G73, pgg_Tp=3.0)[0]
    g4 = dict(flow_s=float(res4["pgg_fl"]), purge_mass_g=1e3 * float(res4["prg_mass"]))
    g4["passed"] = bool(abs(g4["flow_s"] - 2.5) <= dt + 1e-9)
    out["G4_ecu_cap"] = g4
    ok &= g4["passed"]
    print("G4:", g4, flush=True)
    # G5 height floor commit (src 2) without horizon
    res5 = nominal(cfg, **DEC, **G73, pgg_ant=0.0, pgg_hfl=150.0)[0]
    g5 = dict(src=float(res5["pgg_src"]), h_commit=float(res5["pgg_h0"]), tE0_minus_commit=float(res5["pgg_tE0"] - res5["pgg_t0"]))
    g5["passed"] = bool(g5["src"] == 2.0 and g5["h_commit"] <= 150.0 and g5["h_commit"] > 149.0
                        and (abs(g5["tE0_minus_commit"] - 2.90) <= dt + 1e-9 or res5["pgg_tgo"] >= 0))
    out["G5_height_floor"] = g5
    ok &= g5["passed"]
    print("G5:", g5, flush=True)
    # G6 P30 reproduction (500 runs, FSW-R2, A1_none): old amendment P (PS10) start heights; G with the gate off and
    # constant-acceleration extrapolation; G as decided (gate on, constant velocity)
    D = R.draw(np.random.default_rng(101), N, cfg)
    # v1.1: P30 = m2_purge_bleed v1.1 arm A1|P30 exactly (old amendment P, prg_T 3.0 s, lead 0.5 s, 20 g/s, jet on); the
    # G mechanism reproduction uses the same horizon (pgg_ant 3.5 s) with the gate off and constant-acceleration extrapolation
    P30 = dict(prg_on=1, prg_T=3.0, prg_lead=0.5, prg_mdot=0.0200, prg_jet=1, prg_prio=1, prg_book=1)
    arms = {"oldP_P30": P30, "oldP_PS10": PS10, "G_gate0_CA_h3.5": dict(G73, pgg_gate=0, pgg_cv=0, pgg_ant=3.5),
            "G_decided": G73}
    g6 = {}
    for nm, ex in arms.items():
        h0, spur, aq, topen, tcom = [], [], [], [], []
        for i in range(N):
            c, disp = r2_case(cfg, D[i], i, "A1_none", ex)
            r_ = R.fly(c, disp, nrec=10)[0]
            if nm.startswith("oldP"):
                h0.append(float(r_["prg_h0"]))
            else:
                h0.append(float(r_["pgg_h0"]))
                spur.append(float(r_["pgg_spur"]))
                aq.append(float(r_["pgg_aqmax"]))
                topen.append(float(r_["pgg_topen"]))
                tcom.append(float(r_["pgg_t0"]))
        h0 = np.array(h0)
        e = dict(start_h_p01=float(np.percentile(h0, 1)), start_h_p50=float(np.percentile(h0, 50)),
                 start_h_p99=float(np.percentile(h0, 99)), start_h_max=float(h0.max()),
                 starts_above_200m=int(np.sum(h0 > 200.0)), starts_above_160m=int(np.sum(h0 > 160.0)))
        if spur:
            e.update(spurious=int(np.sum(np.array(spur) > 0.5)), aq_max_p99=float(np.percentile(aq, 99)),
                     commit_before_gate=int(np.sum(np.array(tcom) < np.array(topen) - 1e-9)))
        g6[nm] = e
        print("G6", nm, e, flush=True)
    g6["passed"] = bool(g6["G_decided"]["spurious"] == 0 and g6["G_decided"]["commit_before_gate"] == 0
                        and g6["G_decided"]["starts_above_200m"] == 0)
    g6["P30_reproduced"] = bool(g6["oldP_P30"]["starts_above_200m"] > 0)
    g6["note"] = ("P30 (predecessor) = starts of the old amendment-P purge during the drogue-deployment transient; the "
                  "decided G sequence must show none (gate + constant-velocity extrapolation)")
    out["G6_P30_reproduction"] = g6
    ok &= g6["passed"]
    return out, ok


# ------------------------------------------------------------------------------------------------------------------- K
def part_k():
    out, ok = {}, True
    cfg, _ = cfg_of_base("A1_none")
    D = R.draw(np.random.default_rng(101), 6, cfg)
    # K1 Pc valid: kfz_on 1 identical to kfz_on 0 (A1 FSW-R2 + G73, B1 62 m W1p)
    mm, nf = [], 0
    for i in range(6):
        c, disp = r2_case(cfg, D[i], i, "A1_none", G73)
        a = R.fly(c, disp, nrec=10)[0]
        b = R.fly(dict(c, kfz_on=1), disp, nrec=10)[0]
        m = diff(a, b, s6.RES_NAMES)
        nf += len(s6.RES_NAMES)
        mm += [dict(x, run=i) for x in m]
    cfgB, _, _, _ = WL.base_cfg()
    DB = R.draw(np.random.default_rng(WL.SEED), 4, cfgB)
    Z = WL.meas_draws(4)
    jref = float(cfgB.get("throat_jref") or 0.0)
    for i in range(4):
        c, disp = r2_case(cfgB, DB[i], i, "B1_62m_W1p")
        c.update(WL.web_over(DB[i], Z[i], WL.CASES["W1p"], jref)[0])
        a = R.fly(c, disp, nrec=10)[0]
        b = R.fly(dict(c, kfz_on=1), disp, nrec=10)[0]
        m = diff(a, b, s6.RES_NAMES)
        nf += len(s6.RES_NAMES)
        mm += [dict(x, run=f"B1_{i}") for x in m]
    out["K1_pc_valid_identity"] = dict(values_compared=nf, mismatches=len(mm), first=mm[:5], passed=bool(not mm))
    ok &= not mm
    print("K1:", out["K1_pc_valid_identity"], flush=True)
    # K2 Pc invalid from t = 0: k_hat never leaves its initial value
    res, rec, _ = nominal(cfg, **DEC, **G73, mest_pcl_t=0.0, kfz_on=1)
    n = int(res["nrec"])
    kf = rec[:n, I["keff"]]
    res0, rec0, _ = nominal(cfg, **DEC, **G73, mest_pcl_t=0.0, kfz_on=0)
    k0 = rec0[: int(res0["nrec"]), I["keff"]]
    out["K2_pc_lost_t0"] = dict(k_hat_min=float(kf.min()), k_hat_max=float(kf.max()), without_freeze_min=float(k0.min()),
                                without_freeze_max=float(k0.max()), landed_ok=bool(R.success(res)),
                                passed=bool(kf.min() == 1.0 and kf.max() == 1.0))
    ok &= out["K2_pc_lost_t0"]["passed"]
    print("K2:", out["K2_pc_lost_t0"], flush=True)
    # K3 Pc lost 0.30 s after the A-relight light: k_hat frozen from then on; record identical before the loss
    resv, recv, _ = nominal(cfg, **DEC, **G73)
    nv = int(resv["nrec"])
    t5 = light_time(recv, nv)
    tL = t5 + 0.30
    res3, rec3, _ = nominal(cfg, **DEC, **G73, mest_pcl_t=tL, kfz_on=1)
    n3 = int(res3["nrec"])
    t3, k3 = rec3[:n3, I["t"]], rec3[:n3, I["keff"]]
    after = t3 >= tL + 0.002
    before = recv[:nv, I["t"]] < tL - 0.002
    nb = int(np.sum(before))
    same_before = bool(np.array_equal(rec3[:nb], recv[:nb]))
    out["K3_pc_lost_after_light"] = dict(t_light=t5, t_loss=tL, k_hat_at_loss=float(k3[int(np.searchsorted(t3, tL))]),
                                         k_hat_after_min=float(k3[after].min()), k_hat_after_max=float(k3[after].max()),
                                         k_hat_valid_end=float(recv[nv - 1, I["keff"]]), record_identical_before_loss=same_before,
                                         landed_ok=bool(R.success(res3)),
                                         passed=bool(same_before and k3[after].min() == k3[after].max()))
    ok &= out["K3_pc_lost_after_light"]["passed"]
    print("K3:", out["K3_pc_lost_after_light"], flush=True)
    return out, ok


# ------------------------------------------------------------------------------------------------------------------- V
def part_v():
    out, ok = {}, True
    cfg, _ = cfg_of_base("A1_none")
    par = R.build(dict(cfg, **DEC, **G73))[0]
    dt = float(par[PN["dt"]])
    relF = float(par[PN["rel_F"]])
    # V1 onset never reached: identical to off (6 dispersed FSW-R2 runs), pcf_* results excluded
    D = R.draw(np.random.default_rng(101), 6, cfg)
    mm, nf = [], 0
    names = [k for k in s6.RES_NAMES if not k.startswith("pcf_")]
    for i in range(6):
        c, disp = r2_case(cfg, D[i], i, "A1_none", G73)
        a = R.fly(c, disp, nrec=10)[0]
        b = R.fly(dict(c, pcf_on=1, pcf_dt=1.0e3, pcf_rule=1), disp, nrec=10)[0]
        m = diff(a, b, names)
        nf += len(names)
        mm += [dict(x, run=i) for x in m]
    out["V1_onset_never_identity"] = dict(values_compared=nf, mismatches=len(mm), first=mm[:5], passed=bool(not mm))
    ok &= not mm
    print("V1:", out["V1_onset_never_identity"], flush=True)

    def nv(**kw):
        r_, rec_, _ = nominal(cfg, **DEC, **G73, pcf_on=1, pcf_dt=0.0, **kw)
        return r_, rec_, int(r_["nrec"])
    # V2 decided predicate only: no release while Pc is invalid
    r2, _, _ = nv(pcf_rule=0)
    v2 = dict(rel_t=float(r2["rel_t"]), pcf_t0=float(r2["pcf_t0"]), pcf_rel=float(r2["pcf_rel"]), pcf_abt=float(r2["pcf_abt"]),
              landed_ok=bool(R.success(r2)))
    v2["passed"] = bool(v2["rel_t"] < 0.0 and v2["pcf_t0"] > 0.0 and v2["pcf_rel"] == 0.0 and v2["pcf_abt"] == 0.0)
    out["V2_rule0_no_release"] = v2
    ok &= v2["passed"]
    print("V2:", v2, flush=True)
    # V3 interim rule: release at E2 + rel_to (0.10 s) while lit
    r3, _, _ = nv(pcf_rule=1)
    v3 = dict(rel_t=float(r3["rel_t"]), rel_br=float(r3["rel_br"]), pcf_rel=float(r3["pcf_rel"]), pcf_relt=float(r3["pcf_relt"]),
              landed_ok=bool(R.success(r3)), td_vz=float(r3["td_vz"]))
    v3["passed"] = bool(0.10 - 1e-9 <= v3["rel_t"] <= 0.10 + dt + 1e-9 and v3["rel_br"] == 3.0 and v3["pcf_rel"] == 1.0
                        and v3["pcf_relt"] == v3["rel_t"])
    out["V3_rule1_interim"] = v3
    ok &= v3["passed"]
    print("V3:", v3, flush=True)
    # V4 hold the drogue and abort
    r4, rec4, n4 = nv(pcf_rule=3)
    t4_ = rec4[:n4, I["t"]]
    t5 = light_time(rec4, n4)
    Fl = rec4[:n4, I["F"]][t4_ >= t5 + 1.0]
    v4 = dict(rel_t=float(r4["rel_t"]), pcf_abt=float(r4["pcf_abt"]), F_max_after_1s=float(Fl.max()) if Fl.size else None,
              landed_ok=bool(R.success(r4)))
    v4["passed"] = bool(v4["rel_t"] < 0.0 and v4["pcf_abt"] == 1.0 and v4["F_max_after_1s"] is not None
                        and v4["F_max_after_1s"] < 1.0)
    out["V4_rule3_hold_abort"] = v4
    ok &= v4["passed"]
    print("V4:", v4, flush=True)
    # V5 accelerometer-gated release (threshold = rel_F, the map thrust at 3.0 bar abs)
    r5, _, _ = nv(pcf_rule=2)
    v5 = dict(rel_t=float(r5["rel_t"]), rel_br=float(r5["rel_br"]), pcf_rel=float(r5["pcf_rel"]), pcf_abt=float(r5["pcf_abt"]),
              Facc_max_N=float(r5["pcf_Facc_max"]), threshold_N=relF, fz0=float(r5["pcf_fz0"]), landed_ok=bool(R.success(r5)))
    v5["passed"] = bool((v5["rel_br"] == 4.0 and v5["pcf_rel"] == 2.0 and v5["Facc_max_N"] >= relF and v5["rel_t"] >= 0.03 - 1e-9)
                        or (v5["pcf_abt"] == 1.0 and v5["Facc_max_N"] < relF and v5["rel_t"] < 0.0))
    out["V5_rule2_accelerometer"] = v5
    ok &= v5["passed"]
    print("V5:", v5, flush=True)
    # V6 open-loop scale: tsc x pcf_k at the onset
    r6, rec6, n6 = nv(pcf_rule=1, pcf_k=1.25)
    ts = rec6[:n6, I["tsc"]]
    t6 = rec6[:n6, I["t"]]
    k_on = int(np.searchsorted(t6, float(r6["pcf_t0"])))
    ratio = float(ts[k_on + 1] / ts[k_on - 2])
    v6 = dict(onset_t=float(r6["pcf_t0"]), tsc_before=float(ts[k_on - 2]), tsc_after=float(ts[k_on + 1]), ratio=ratio)
    v6["passed"] = bool(abs(ratio - 1.25) < 2e-3)
    out["V6_open_loop_scale"] = v6
    ok &= v6["passed"]
    print("V6:", v6, flush=True)
    # V7 flame-out at the onset (undetected, ECU in RUN): the accelerometer rule must not release (abort at E2 + pcf_tmax);
    # the interim rule releases at E2 + rel_to on a dead engine (evidence for the rule choice)
    r7, rec7, n7 = nv(pcf_rule=2, pcf_fo=1)
    r8, _, _ = nv(pcf_rule=1, pcf_fo=1)
    t7 = rec7[:n7, I["t"]]
    F7 = rec7[:n7, I["F"]][t7 >= float(r7["pcf_t0"]) + 0.3]
    v7 = dict(accel_rel_t=float(r7["rel_t"]), accel_abt=float(r7["pcf_abt"]), accel_Facc_max_N=float(r7["pcf_Facc_max"]),
              F_max_0p3s_after_onset_N=float(F7.max()) if F7.size else None, accel_landed_ok=bool(R.success(r7)),
              interim_rel_t=float(r8["rel_t"]), interim_rel_br=float(r8["rel_br"]), interim_landed_ok=bool(R.success(r8)),
              interim_td_vz=float(r8["td_vz"]))
    v7["passed"] = bool(v7["accel_rel_t"] < 0.0 and v7["accel_abt"] == 1.0 and v7["accel_Facc_max_N"] < relF
                        and 0.10 - 1e-9 <= v7["interim_rel_t"] <= 0.10 + dt + 1e-9 and v7["interim_rel_br"] == 3.0
                        and F7.size and v7["F_max_0p3s_after_onset_N"] < 0.05 * float(rec7[:n7, I["F"]].max()))
    out["V7_flameout"] = v7
    ok &= bool(v7["passed"])
    print("V7:", v7, flush=True)
    return out, ok


# ------------------------------------------------------------------------------------------------------------------- N
def part_n():
    out, ok = {}, True
    sim = ["--sim", DEV, "--sources", "A1_none"]
    os.makedirs(SCR, exist_ok=True)
    # N1 unreadable GNC_IFACE
    rc, so, se = runner(sim, env=dict(GNC_IFACE="/nonexistent_iface"))
    out["N1_unreadable_iface"] = dict(rc=rc, msg=se.strip().splitlines()[-1] if se.strip() else so[-200:],
                                      passed=bool(rc != 0 and "unreadable" in se))
    # N2 pin mismatch (combustion.json hash altered in a copy of the pin list)
    pin = os.environ.get("GNC_IFACE_PIN")
    bad = os.path.join(SCR, "pins_bad.sha256")
    with open(bad, "w") as f:
        for ln in open(pin):
            h, n = ln.split(None, 1)
            f.write(("0" * 64 if n.strip() == "combustion.json" else h) + "  " + n.strip() + "\n")
    rc, so, se = runner(sim, env=dict(GNC_IFACE_PIN=bad))
    out["N2_pin_mismatch"] = dict(rc=rc, msg=se.strip().splitlines()[-1] if se.strip() else "", passed=bool(rc != 0 and "pinned" in se))
    # N3 version assertion
    rc, so, se = runner(sim, env=dict(GNC_COMB_VERSION="v2.3"))
    out["N3_version_assert"] = dict(rc=rc, msg=se.strip().splitlines()[-1] if se.strip() else "", passed=bool(rc != 0 and "version" in se))
    # N4 hub electronics.json v2: refused in strict mode; without strict mode the build fails on dynamics_for_GNC (N5)
    d4 = os.path.join(SCR, "iface_el2")
    if os.path.exists(d4):
        shutil.rmtree(d4)
    shutil.copytree(os.environ["GNC_IFACE"], d4)
    shutil.copy2("/home/claude/work/shared-fallback/engine/interfaces/electronics.json", os.path.join(d4, "electronics.json"))
    pin4 = os.path.join(SCR, "pins_el2.sha256")
    with open(pin4, "w") as f:
        for ln in open(pin):
            h, n = ln.split(None, 1)
            if n.strip() == "electronics.json":
                h = hashlib.sha256(open(os.path.join(d4, "electronics.json"), "rb").read()).hexdigest()
            f.write(h + "  " + n.strip() + "\n")
    rc, so, se = runner(sim, env=dict(GNC_IFACE=d4, GNC_IFACE_PIN=pin4, GNC_ACT_RATE=os.path.join(d4, "actuator_rate_check_v2.json")))
    rc2, so2, se2 = runner(sim, env=dict(GNC_IFACE=d4, GNC_IFACE_PIN=pin4, GNC_STRICT="0",
                                         GNC_ACT_RATE=os.path.join(d4, "actuator_rate_check_v2.json")))
    out["N4_electronics_v2"] = dict(strict_rc=rc, strict_msg=se.strip().splitlines()[-1] if se.strip() else "",
                                    nonstrict_rc=rc2, nonstrict_msg=se2.strip().splitlines()[-1] if se2.strip() else "",
                                    electronics_hub_sha16=sha16(os.path.join(d4, "electronics.json")),
                                    v2_has_dynamics_for_GNC=("dynamics_for_GNC" in open(os.path.join(d4, "electronics.json")).read()),
                                    passed=bool(rc != 0 and "electronics.json version" in se and rc2 != 0 and "KeyError" in se2))
    # N0 positive control: the declared set loads and builds
    rc, so, se = runner(sim)
    out["N0_declared_set_builds"] = dict(rc=rc, out=so.strip().splitlines()[-2:], passed=bool(rc == 0 and "BUILD_OK" in so))
    # N5 combustion.json v2.3 (iface_v3c) vs v2.4 (iface_v3d): identical results on the decided purge path
    cfg, _ = cfg_of_base("A1_none")
    D = R.draw(np.random.default_rng(101), 4, cfg)
    jobs = []
    for i in range(4):
        c, disp = r2_case(cfg, D[i], i, "A1_none", G73)
        jobs.append((f"A1_none|G73|{i}", c, disp))
    jp, op = os.path.join(SCR, "n5_jobs.pkl"), os.path.join(SCR, "n5_v23.pkl")
    pickle.dump(jobs, open(jp, "wb"))
    pin_old = os.path.join(DEV, "data", "pins", "pins_rev2_pre_comb24.sha256")
    rc, so, se = runner(["--sim", DEV, "--jobs", jp, "--out", op],
                        env=dict(GNC_IFACE="/home/claude/work/space/iface_v3c", GNC_IFACE_PIN=pin_old, GNC_COMB_VERSION="v2.3",
                                 GNC_ACT_RATE="/home/claude/work/space/iface_v3c/actuator_rate_check_v2.json"))
    if rc == 0:
        old = pickle.load(open(op, "rb"))["res"]
        mm, nf = [], 0
        for name, c, disp in jobs:
            new = R.fly(c, disp, nrec=10)[0]
            m = diff(old[name], new, s6.RES_NAMES)
            nf += len(s6.RES_NAMES)
            mm += [dict(x, job=name) for x in m]
        out["N5_comb_v23_vs_v24"] = dict(values_compared=nf, mismatches=len(mm), first=mm[:5], passed=bool(not mm))
    else:
        out["N5_comb_v23_vs_v24"] = dict(error=se[-600:], passed=False)
    for k, v in out.items():
        ok &= v["passed"]
        print(k, {a: b for a, b in v.items() if a not in ("first",)}, flush=True)
    return out, ok


def part_rf():
    """RF: the final v2.9-dev sim reproduces the stored RG-01 re-fly tables (first KR runs + every failed run of two arms)."""
    import m2_rg01_refly as F
    out, ok = {}, True
    KR = int(os.environ.get("GNC_BIT_KR", "20"))
    bay_z = F.engine_bay_mid()[0]
    for base, name in (("A1_none", "pw|G73"), ("A1J_pc", "liq|G73"), ("A1_none", "bf|G73")):
        p = os.path.join(F.OUT, f"rf_{base}_{name.replace('|', '_')}.csv")
        if not os.path.exists(p):
            continue
        rows = list(csv.DictReader(open(p)))
        spec = F.ARMS[name]
        st = spec["state"]
        cfg, m = F.base_cfg(base, "pw" if st == "bf" else st, F.arm_extra(spec, bay_z))
        MV.TG_JREF_DEFAULT = float(JR["A1J" if base.startswith("A1J") else "A1"])
        D = R.draw(np.random.default_rng(101), N, cfg)
        idx = list(range(KR)) + [i for i, r in enumerate(rows) if int(float(r["ok"])) == 0 and i >= KR]
        mism, nf = [], 0
        for i in idx:
            c, disp = MV.run_cfg_case(cfg, D[i], MV.case_specs()["tot_cal_comp"], i, "base")
            c.update(F.DEC); c.update(F.PURGE[spec["purge"]]); c.update(F.PLAT[spec["plat"]])
            if st == "bf":
                c.update(F.BLEED)
            res = R.fly(c, disp, nrec=10)[0]
            for k in rows[i]:
                if k in s6.RES_NAMES:
                    nf += 1
                    x, y = float(rows[i][k]), float(res[k])
                    if not (x == y or (np.isnan(x) and np.isnan(y))):
                        mism.append(dict(run=i, field=k, ref=x, new=y))
        out[f"{base}|{name}"] = dict(reference=f"{p} (sha256/16 {sha16(p)})", runs=len(idx), values_compared=nf,
                                     mismatches=len(mism), first=mism[:5], passed=bool(nf > 0 and not mism))
        ok &= out[f"{base}|{name}"]["passed"]
        print(f"RF {base} {name}: runs {len(idx)} values {nf} mismatches {len(mism)}", flush=True)
    return out, ok


def main():
    os.makedirs(RES, exist_ok=True)
    out = dict(tool=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, run6=R.__doc__.split("\n")[0][:100],
               iface=os.environ.get("GNC_IFACE"), pins=os.environ.get("GNC_IFACE_PIN"), strict=EV.STRICT, K=K, parts={},
               parts_run=PARTS, code_sha256_16={os.path.basename(f_): hashlib.sha256(open(f_, "rb").read()).hexdigest()[:16]
                                                 for f_ in (s6.__file__, R.__file__, os.path.abspath(__file__))})
    ok_all = True
    for p, fn in (("A0", part_a0), ("A1", part_a1), ("G", part_g), ("K", part_k), ("V", part_v), ("N", part_n), ("RF", part_rf)):
        if p in PARTS:
            r_, ok_ = fn()
            out["parts"][p] = dict(r_, passed=bool(ok_))
            ok_all &= ok_
            print(f"== part {p}: {'PASS' if ok_ else 'FAIL'}", flush=True)
    out["all_passed"] = bool(ok_all)
    with open(os.path.join(RES, "bitcheck_v29.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("ALL", "PASS" if ok_all else "FAIL", "->", os.path.join(RES, "bitcheck_v29.json"), flush=True)


if __name__ == "__main__":
    main()

"""m2_eng07_6v6 v1.2 (GNC, 2026-10-13): ENG-07 at the 6.6 V degraded servo plug on the v3.4 hose coil, A1 and B1 62 m in the
6-DOF, paired against the stored baselines on the same draws (lead CHANGELOG 2026-10-13 decision (2): "GNC states which 6.6 V
slew gave P 0.982 and flies the v3.4 coil values (95.9 / 85.5 deg/s at EI 0.05 / 0.25); the hose EI limit is set from that").
v1.1: the re-routed coil (CAD v3.4.1 feed, the baseline since the vapour fix; Mechanical hose_end_reactions_v341_v1.json,
ENG07_worst_vector_dps) is flown with the same arm methods: K_max = 93.476 x EI N m/rad (largest eigenvalue of the coupled
K matrix [[64.459, 32.728], [32.728, 56.563]] x EI; smallest 27.546 x EI) and the worst-vector slew at 6.6 / 7.4 V for EI
0.05 / 0.184 (Mechanical's 7.4 V break-even, K 17.2) / 0.25 / 0.5 N m2. RR = rule arms, RRv = bracket, PR = act_model 1. The
v1 arms (v3.4 coil) are kept unchanged; the EI limit of each coil is reported as the bracket between the largest EI flown
that does not lose and the smallest EI flown that loses (no interpolation between flown points).
v1.2: two arms on the re-routed coil at EI 0.5 with a 7.4 V servo supply, RR74_EI05 (rule, 73.36 deg/s) and PR74_EI05
(act_model 1): does a 7.4 V supply recover the first EI that loses at 6.6 V? Eval otherwise unchanged (JSON keys fixed).

Provenance of P 0.982 (answered from the stored results, not re-flown): actuator_study v1 (sim6 v2.5, results_v2) case
AD_prov_act_n48_6V6 = the lead baseline of 2026-10-12 (N2O 2.00 kg, no RCS) with act_model 1 (servo pair on the SB-2292SG
torque-speed lines at a FIXED 6.60 V plug through the Cardan kinematics, n 4.8, J_int not modelled), FSW command limit 100 deg/s
per axis, hose_K drawn U(0.20, 1.97) N m/rad (mechanical.json v1, since corrected by erratum to U(1.73, 17.48)). No slew value
was imposed: the 6-DOF used the servo lines and the simulated loads. P 0.982 = AD_prov_2kg (reference servo n 6, 7.4 V) with
0 lost / 0 gained; the 6.0 V plug, n 6.0 and the sag-chain D variants gave the same 0.982. The 95.3 deg/s next to it in
REQUIREMENTS ENG-07 is Mechanical's quasi-static worst-vector rate of the same servo lines at 6.6 V under 3.19 N m (mechanical.json
v2 rate_engine_dps_under_3.19Nm); it was never a simulation input.

Arms (hose_K fixed per arm at the v3.4 coil K_max_singular(EI) of Mechanical coil_o3b_v34_v1.json per_EI: 0 / 2.962 / 14.809 /
29.618 N m/rad at EI 0 / 0.05 / 0.25 / 0.5 N m2 (ASSUMED EI there; B-FD-1); all other draws identical to the stored baseline):
  R<V>_EI<x>   ENG-07 rule method (as the 2026-10-12 slew study that set 100 deg/s: AD_fins_f20_rate80/60): reference servo
               (act_model 0) at servo_V (torque-speed line rescaled by the DATASHEET voltage points) and the command slew limit
               per axis = Mechanical's worst-vector slew at 7 deg for that EI and voltage, capped at the FSW 100 deg/s.
  Rv66_EI<x>   bracket: per-axis limit = slew / sqrt 2, so the commanded VECTOR rate never exceeds the worst-vector slew in any
               direction (the per-axis tracker of R allows up to sqrt 2 x the limit on a diagonal).
  P<V>_<x>     physical cross-check: act_model 1 (servo pair on the SB-2292SG lines at a fixed plug voltage through the Cardan
               kinematics, n 4.8 as mechanical.json v2), FSW limit 100 deg/s, hose_K per EI ('base' = the base's hose dispersion
               U(1.73, 17.48)): the direction dependence is modelled, the per-axis convention of R is not needed.
Decision rule used for the ENG-07 slew study (actuator study): an arm LOSES when its P is below the comparator's and the exact
McNemar p < 0.05 on the same draws; the lead's ENG-03 rule (loss within the Monte Carlo resolution, about 1 %) is reported too.
More degrees of freedom (act_model 1) is not proof of accuracy: both models rest on DATASHEET servo lines (B-TVC-1 measures).
Parts (GNC_E7_PARTS, default check,run,eval); GNC_E7_SPLIT k/n; GNC_E7_ARMS (default all); env GNC_IFACE, GNC_ACT_RATE (iface_v3c).
Output: GNC_E7_OUT (default out/eng07_6v6): mc6_runs_<base>_<arm>.csv, eng07_6v6.json."""
import csv
import hashlib
import json
import math
import os
import sys
import time
import numpy as np

os.environ.setdefault("GNC_PC_RATCHET", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_mc6 as M  # noqa: E402
import m2_eng03_rate as E  # noqa: E402
import m2_throat_mc as TG  # noqa: E402

VERSION = "m2_eng07_6v6 v1.2"
S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_E7_OUT", f"{S}/eng07_6v6")
PARTS = os.environ.get("GNC_E7_PARTS", "check,run,eval").split(",")
SPLIT = os.environ.get("GNC_E7_SPLIT", "0/1")
ARMS_SEL = os.environ.get("GNC_E7_ARMS", "")
BASES = ("A1_none", "rbl_B1_lead62_pc_k2")
COIL = os.environ.get("GNC_E7_COIL", "/home/claude/work/mechanical/engine/03-cad/src/calcs/coil_o3b_v34_v1.json")
COIL_RR = os.environ.get("GNC_E7_COIL_RR", "/home/claude/work/shared-fallback/engine/03-cad/calcs/hose_end_reactions_v341_v1.json")
STUDY = f"{S}/results_v2/actuator_study_v2.json"
FSW_LIMIT = 100.0
EIS = ("0.0", "0.05", "0.25", "0.5")
EIS_RR = ("0.05", "0.184", "0.25", "0.5")


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def coil():
    """Mechanical v3.4 coil: hose K_max_singular per EI and the ENG07 worst-vector slew per EI and voltage."""
    d = json.load(open(COIL))
    K = {"0.0": 0.0}
    for e in EIS[1:]:
        K[e] = float(d["per_EI"][f"EI={e}"]["K_max_singular_Nm_rad"])
    sl = {}
    for e in EIS:
        for V in ("6.6", "7.4"):
            sl[(e, V)] = float(d["ENG07"]["cases"][f"EI={e}|{V}V"]["worst_any_dps"])
    return dict(K=K, slew=sl, src=f"{COIL} (sha256/16 {sha16(COIL)}) {d.get('id')} {d.get('version')} {d.get('date')}",
                load_basis=d["ENG07"]["load_basis"], EI_tag=d["EI_tag"])


def coil_rr():
    """Mechanical re-routed coil (CAD v3.4.1 feed): K_max per EI and the ENG07 worst-vector slew per EI and voltage."""
    d = json.load(open(COIL_RR))
    w = d["ENG07_worst_vector_dps"]
    K = {e: float(w[e]["K_max_Nm_rad"]) for e in EIS_RR}
    sl = {(e, V): float(w[e][f"{V}V"]["dps"]) for e in EIS_RR for V in ("6.6", "7.4")}
    pose = {f"EI={e}|{V}V": dict(pose_phi_deg=w[e][f"{V}V"]["pose_phi_deg"], motion_chi_deg=w[e][f"{V}V"]["motion_chi_deg"])
            for e in EIS_RR for V in ("6.6", "7.4")}
    rc = d["route_check"]
    Km = np.array(rc["K_per_EI_Nm_rad"], float)
    return dict(K=K, slew=sl, pose=pose, K_per_EI=Km.tolist(), K_eig_per_EI=sorted(np.linalg.eigvalsh(Km).tolist()),
                K_max_per_EI=float(rc["K_max_per_EI"]), EI_breakeven=float(rc["EI_breakeven_Nm2"]), gates=rc.get("gates"),
                src=f"{COIL_RR} (sha256/16 {sha16(COIL_RR)}) {d.get('id')} {d.get('version')} {d.get('date')}", tag=d.get("tag"))


def tag_ei(e):
    return {"0.0": "0", "0.05": "005", "0.184": "0184", "0.25": "025", "0.5": "05"}[e]


def arms():
    c = coil()
    A = {}
    for e in EIS:
        r = min(FSW_LIMIT, c["slew"][(e, "6.6")])
        A[f"R66_EI{tag_ei(e)}"] = dict(over=dict(servo_V=6.6, gim_cmd_rate=r), hose_K=c["K"][e],
                                       note=f"rule: act_model 0 at 6.6 V, per-axis command limit {r:.2f} deg/s (worst-vector slew at "
                                            f"EI {e}), hose_K {c['K'][e]:.3f} N m/rad")
    for e in ("0.25", "0.5"):
        r = min(FSW_LIMIT, c["slew"][(e, "7.4")])
        A[f"R74_EI{tag_ei(e)}"] = dict(over=dict(servo_V=7.4, gim_cmd_rate=r), hose_K=c["K"][e],
                                       note=f"rule: act_model 0 at 7.4 V, per-axis command limit {r:.2f} deg/s (capable "
                                            f"{c['slew'][(e, '7.4')]:.2f}), hose_K {c['K'][e]:.3f} N m/rad")
    for e in ("0.05", "0.25"):
        r = c["slew"][(e, "6.6")] / math.sqrt(2.0)
        A[f"Rv66_EI{tag_ei(e)}"] = dict(over=dict(servo_V=6.6, gim_cmd_rate=r), hose_K=c["K"][e],
                                        note=f"bracket: per-axis limit {r:.2f} deg/s = slew / sqrt 2 (vector rate <= "
                                             f"{c['slew'][(e, '6.6')]:.2f} in every direction), hose_K {c['K'][e]:.3f}")
    A["P74_base"] = dict(over=dict(act_model=1, servo_V=7.4), hose_K=None,
                         note="physical: act_model 1 at a fixed 7.4 V plug, hose_K as the base dispersion U(1.73, 17.48)")
    A["P66_base"] = dict(over=dict(act_model=1, servo_V=6.6), hose_K=None,
                         note="physical: act_model 1 at a fixed 6.6 V plug, hose_K as the base dispersion U(1.73, 17.48)")
    for e in ("0.05", "0.25", "0.5"):
        A[f"P66_EI{tag_ei(e)}"] = dict(over=dict(act_model=1, servo_V=6.6), hose_K=c["K"][e],
                                       note=f"physical: act_model 1 at a fixed 6.6 V plug, hose_K {c['K'][e]:.3f} N m/rad (EI {e})")
    A["P74_EI05"] = dict(over=dict(act_model=1, servo_V=7.4), hose_K=c["K"]["0.5"],
                         note=f"physical: act_model 1 at a fixed 7.4 V plug, hose_K {c['K']['0.5']:.3f} N m/rad (EI 0.5)")
    # v1.1: re-routed coil (CAD v3.4.1 feed)
    q = coil_rr()
    for e in EIS_RR:
        r = min(FSW_LIMIT, q["slew"][(e, "6.6")])
        A[f"RR66_EI{tag_ei(e)}"] = dict(over=dict(servo_V=6.6, gim_cmd_rate=r), hose_K=q["K"][e], coil="v3.4.1 re-route",
                                        note=f"re-routed coil rule: act_model 0 at 6.6 V, per-axis command limit {r:.2f} deg/s "
                                             f"(worst-vector slew at EI {e}), hose_K {q['K'][e]:.3f} N m/rad")
    for e in ("0.184", "0.25", "0.5"):
        r = min(FSW_LIMIT, q["slew"][(e, "7.4")])
        A[f"RR74_EI{tag_ei(e)}"] = dict(over=dict(servo_V=7.4, gim_cmd_rate=r), hose_K=q["K"][e], coil="v3.4.1 re-route",
                                        note=f"re-routed coil rule: act_model 0 at 7.4 V, per-axis command limit {r:.2f} deg/s "
                                             f"(capable {q['slew'][(e, '7.4')]:.2f}), hose_K {q['K'][e]:.3f} N m/rad")
    r = q["slew"][("0.184", "6.6")] / math.sqrt(2.0)
    A["RRv66_EI0184"] = dict(over=dict(servo_V=6.6, gim_cmd_rate=r), hose_K=q["K"]["0.184"], coil="v3.4.1 re-route",
                             note=f"re-routed coil bracket: per-axis limit {r:.2f} deg/s = slew / sqrt 2, hose_K {q['K']['0.184']:.3f}")
    for e in ("0.184", "0.25", "0.5"):
        A[f"PR66_EI{tag_ei(e)}"] = dict(over=dict(act_model=1, servo_V=6.6), hose_K=q["K"][e], coil="v3.4.1 re-route",
                                        note=f"re-routed coil physical: act_model 1 at a fixed 6.6 V plug, hose_K {q['K'][e]:.3f} "
                                             f"N m/rad (EI {e})")
    # v1.2: does a 7.4 V servo supply recover the re-routed coil at EI 0.5 (the first EI that loses at 6.6 V)?
    A["PR74_EI05"] = dict(over=dict(act_model=1, servo_V=7.4), hose_K=q["K"]["0.5"], coil="v3.4.1 re-route",
                          note=f"re-routed coil physical: act_model 1 at a fixed 7.4 V plug, hose_K {q['K']['0.5']:.3f} N m/rad "
                               f"(EI 0.5)")
    if ARMS_SEL:
        A = {k: v for k, v in A.items() if k in ARMS_SEL.split(",")}
    return A


def rows_csv(p):
    return list(csv.DictReader(open(p))) if os.path.exists(p) else None


def run_arm(base, arm, n=None, seed=101):
    over, bcsv, bjson = E.base_ref(base)
    m_load = json.load(open(bjson))["m_n2o_mc_kg"]
    ov = dict({k: v for k, v in over.items() if k != "m_fixed"}, m_n2o=float(m_load))
    a = arms()[arm] if arm != "ctl" else dict(over={}, hose_K=None)
    ov.update(a["over"])
    cfg = R.cfg_of(**ov)
    D = R.draw(np.random.default_rng(seed), M.N, cfg)
    if a["hose_K"] is not None:
        for dr in D:
            dr["hose_K"] = float(a["hose_K"])
    D = D if n is None else D[:n]
    return [R.flat_row(i, dr, res, R.success(res), cfg) for i, dr in enumerate(D) for res in (R.run_one(cfg, dr),)]


def part_check():
    """identity: the no-change arm reproduces the stored baseline rows (first 20 runs, every RES column)."""
    out = {}
    for base in BASES:
        _, bcsv, _ = E.base_ref(base)
        b = rows_csv(bcsv)
        rr = run_arm(base, "ctl", n=20)
        mism = []
        for i, r in enumerate(rr):
            for k in s6.RES_NAMES:
                if k in b[i] and b[i][k] not in ("", "nan"):
                    x, y = float(r[k]), float(b[i][k])
                    if not (abs(x - y) <= 1e-9 * max(1.0, abs(y)) or (math.isnan(x) and math.isnan(y))):
                        mism.append((i, k, x, y))
        out[base] = dict(runs=len(rr), mismatches=len(mism), first=mism[:5])
        print(f"check {base}: {len(rr)} runs, {len(mism)} mismatches {mism[:3]}", flush=True)
    return out


def part_run():
    os.makedirs(OUT, exist_ok=True)
    k, n = (int(x) for x in SPLIT.split("/"))
    A = arms()
    jobs = [(b, a) for a in A for b in BASES][k::n]
    for base, arm in jobs:
        p = os.path.join(OUT, f"mc6_runs_{base}_{arm}.csv")
        if os.path.exists(p) and os.path.getsize(p) > 100 and os.environ.get("GNC_E7_FORCE") != "1":
            print("exists", base, arm, flush=True)
            continue
        t0 = time.time()
        rows = run_arm(base, arm)
        M.write_csv(p, rows)
        _, bcsv, _ = E.base_ref(base)
        ok = np.array([r["ok"] for r in rows]) > 0.5
        ob = np.array([float(r["ok"]) for r in rows_csv(bcsv)]) > 0.5
        print(f"{base:22s} {arm:10s}: P {ok.mean():.3f} (base {ob.mean():.3f}; -{int(np.sum(ob & ~ok))}/+{int(np.sum(~ob & ok))}) "
              f"max_gim_rate p99 {np.percentile([r['max_gim_rate'] for r in rows], 99):.1f} ({time.time() - t0:.0f} s)", flush=True)


def mcnemar(a, b):
    from scipy.stats import binomtest
    lost, gained = int(np.sum(a & ~b)), int(np.sum(~a & b))
    p = float(binomtest(lost, lost + gained, 0.5).pvalue) if lost + gained else 1.0
    return dict(P_ref=float(a.mean()), P_arm=float(b.mean()), dP=float(b.mean() - a.mean()), lost=lost, gained=gained, p_exact=p,
                n=int(len(a)), loses=bool(b.mean() < a.mean() and p < 0.05), within_1pct=bool(b.mean() - a.mean() >= -0.01))


def pct(x, qs=(50, 99)):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return [float(np.percentile(x, q)) for q in qs] + [float(x.max())] if len(x) else None


def fail_modes(rows):
    fm = {}
    for r in rows:
        if float(r["ok"]) > 0.5:
            continue
        if float(r["landed"]) < 0.5 or float(r.get("crash", 0)) > 0.5:
            k = "no_touchdown_or_crash"
        elif float(r["exhausted"]) > 0.5:
            k = "exhausted"
        elif float(r["tipover"]) > 0.5:
            k = "tipover"
        elif abs(float(r["td_vz"])) > R.CRIT["vz"]:
            k = "vz"
        elif float(r["td_vh"]) > R.CRIT["vh"]:
            k = "vh"
        elif float(r["td_tilt"]) > R.CRIT["tilt"]:
            k = "tilt"
        else:
            k = "rate"
        fm[k] = fm.get(k, 0) + 1
    return fm


def part_eval(check=None):
    A = arms()
    c = coil()
    st = json.load(open(STUDY))
    prov = {k: dict(P=st["cases"][k]["P"], note=st["cases"][k]["note"], sim=st["cases"][k]["sim"],
                    holding_moment_neutral_weakest_Nm=st["cases"][k]["holding_moment_neutral_weakest_Nm"],
                    engine_noload_rate_neutral_dps=st["cases"][k]["engine_noload_rate_neutral_dps"],
                    paired_vs_AD_prov_2kg=st["cases"][k]["paired"]["AD_prov_2kg"],
                    paired_vs_AD_fins_f20=st["cases"][k]["paired"]["AD_fins_f20"])
            for k in ("AD_prov_act_n48_6V6", "AD_prov_act_n48_6V6_sagD", "AD_prov_act_n60_6V6", "AD_prov_act_n48_6V0")}
    hk = []
    p26 = os.path.join(S, "m2", "mc6_runs_AD_prov_act_n48_6V6_v2.csv")
    if os.path.exists(p26):
        hk = [float(r["hose_K"]) for r in rows_csv(p26)]
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, iface=R.IFACE, request=__doc__.split("\n\n")[0],
               provenance_P0982=dict(
                   answer=("No fixed slew produced P 0.982. It is the 6-DOF result of actuator_study v1 case AD_prov_act_n48_6V6 "
                           "(sim6 v2.5): the servo pair on the SB-2292SG torque-speed lines at a fixed 6.60 V plug through the "
                           "Cardan kinematics, n 4.8, FSW limit 100 deg/s per axis, hose_K U(0.20, 1.97) N m/rad (mechanical.json "
                           "v1, before the erratum). 95.3 deg/s (REQUIREMENTS) is Mechanical's quasi-static worst-vector value "
                           "of the same lines at 6.6 V under 3.19 N m, quoted beside the result but never flown."),
                   hose_K_range_flown_Nm_rad=[min(hk), max(hk)] if hk else None,
                   v34_coil_EI_equivalent_of_K_1p97=float(1.97 / (c["K"]["0.05"] / 0.05)),
                   cases=prov),
               coil=dict(src=c["src"], load_basis=c["load_basis"], EI_tag=c["EI_tag"], K_max_singular_Nm_rad=c["K"],
                         worst_vector_slew_dps={f"EI={e}|{V}V": c["slew"][(e, V)] for e in EIS for V in ("6.6", "7.4")}),
               coil_reroute_v341=(lambda d: dict(d, slew={f"EI={e}|{V}V": v for (e, V), v in d["slew"].items()}))(coil_rr()),
               arms={k: dict(over=v["over"], hose_K=v["hose_K"], coil=v.get("coil", "v3.4"), note=v["note"]) for k, v in A.items()},
               rule=("loses = P below the stored baseline and exact McNemar p < 0.05 on the same draws (seed 101, 500 runs); "
                     "within_1pct = the lead's ENG-03 resolution rule"),
               identity_check=check, by_base={}, pooled={}, cross={})
    pools = {}
    okd = {}
    for base in BASES:
        _, bcsv, _ = E.base_ref(base)
        b = rows_csv(bcsv)
        ob = np.array([float(r["ok"]) for r in b]) > 0.5
        bb = dict(baseline=dict(csv=bcsv, sha16=sha16(bcsv), P=float(ob.mean()), ci95=TG.wilson(int(ob.sum()), len(ob)),
                                fail_modes=fail_modes(b)))
        okd[(base, "base")] = ob
        for arm in A:
            rr = rows_csv(os.path.join(OUT, f"mc6_runs_{base}_{arm}.csv"))
            if not rr:
                continue
            ok = np.array([float(r["ok"]) for r in rr]) > 0.5
            okd[(base, arm)] = ok
            g = lambda k: np.array([float(r[k]) for r in rr])  # noqa: E731
            same = ([r["wind"] for r in rr] == [r["wind"] for r in b] and
                    [r.get("thrust_scale") for r in rr] == [r.get("thrust_scale") for r in b] and
                    [r.get("gust_scale") for r in rr] == [r.get("gust_scale") for r in b])
            wv = g("wind")
            x = dict(P=float(ok.mean()), ci95=TG.wilson(int(ok.sum()), len(ok)), paired_vs_baseline=mcnemar(ob, ok),
                     same_draws_except_hose=bool(same), hose_K_flown=pct(g("hose_K"), (0, 50)), fail_modes=fail_modes(rr),
                     td_vh_p50_p99_max=pct(g("td_vh")), td_tilt_p50_p99_max=pct(g("td_tilt")), td_rate_p50_p99_max=pct(g("td_rate")),
                     max_gim_rate_dps_p50_p99_max=pct(g("max_gim_rate")),
                     max_hinge_Nm_p50_p99_max=pct(g("max_hinge")), max_gim_deg_p50_p99_max=pct(g("max_gim")),
                     by_wind_m_s={f"{lo:g}-{hi:g}": {k_: v_ for k_, v_ in mcnemar(ob[(wv >= lo) & (wv < hi)], ok[(wv >= lo) & (wv < hi)]).items()}
                                  for lo, hi in ((0.0, 4.0), (4.0, 6.0), (6.0, 8.01))},
                     lost_runs=[dict(run=i, wind=round(float(wv[i]), 2), td_vz=float(rr[i]["td_vz"]), td_vh=float(rr[i]["td_vh"]),
                                     td_tilt=float(rr[i]["td_tilt"]), td_rate=float(rr[i]["td_rate"]), landed=float(rr[i]["landed"]),
                                     base_td_vh=float(b[i]["td_vh"]), base_td_tilt=float(b[i]["td_tilt"]))
                                for i in range(len(ok)) if ob[i] and not ok[i]],
                     gained_runs=[int(i) for i in range(len(ok)) if ok[i] and not ob[i]])
            if A[arm]["over"].get("act_model", 0) == 1:
                x["act_model1"] = dict(sat_time_land_s_p50_p99_max=pct(g("act_sat_time_land")),
                                       ENG07b_longest_episode_s_p50_p99_max=pct(g("act_sat_max_dur")),
                                       ENG07b_pass_p99_le_0p1s=bool(np.percentile(g("act_sat_max_dur"), 99) <= 0.1),
                                       runs_saturated=int(np.sum(g("act_sat_time") > 0)),
                                       stall_time_s_p99_max=pct(g("act_sat_time_stall"), (99,)),
                                       hinge_demand_Nm_p50_p99_max=pct(g("max_hinge_dem")))
            bb[arm] = x
            grp = "A1" if base.startswith("A1") else "B1"
            pools.setdefault(arm, []).append((ob, ok))
            pr = x["paired_vs_baseline"]
            print(f"{base:22s} {arm:10s}: P {x['P']:.3f} vs {ob.mean():.3f} -{pr['lost']}/+{pr['gained']} p {pr['p_exact']:.3g} "
                  f"{'LOSES' if pr['loses'] else ''} | vh p99 {x['td_vh_p50_p99_max'][1]:.3f} tilt p99 {x['td_tilt_p50_p99_max'][1]:.2f} "
                  f"| gim rate p99 {x['max_gim_rate_dps_p50_p99_max'][1]:.1f} | fm {x['fail_modes']} | same {same}"
                  + (f" | ENG-07b p99 {1e3 * x['act_model1']['ENG07b_longest_episode_s_p50_p99_max'][1]:.0f} ms" if "act_model1" in x else ""),
                  flush=True)
            _ = grp
        out["by_base"][base] = bb
    for arm, lst in pools.items():
        a = np.concatenate([x for x, _ in lst])
        b = np.concatenate([y for _, y in lst])
        d = mcnemar(a, b)
        d.update(n_bases=len(lst))
        out["pooled"][arm] = d
        print(f"pooled A1+B1 {arm:10s}: P {d['P_arm']:.4f} vs {d['P_ref']:.4f} dP {d['dP']:+.4f} -{d['lost']}/+{d['gained']} p {d['p_exact']:.3g}",
              flush=True)
    # arm vs arm on the same draws: the EI effect at 6.6 V and the voltage effect at a given EI
    pairs = [("R66_EI005", "R66_EI025"), ("R66_EI025", "R66_EI05"), ("R66_EI0", "R66_EI005"), ("R74_EI025", "R66_EI025"),
             ("R74_EI05", "R66_EI05"), ("P66_EI005", "P66_EI025"), ("P66_EI025", "P66_EI05"), ("P74_base", "P66_base"),
             ("P66_base", "P66_EI025"), ("R66_EI025", "Rv66_EI025"), ("R66_EI005", "Rv66_EI005"), ("P74_EI05", "P66_EI05"),
             ("RR66_EI005", "RR66_EI0184"), ("RR66_EI0184", "RR66_EI025"), ("RR66_EI025", "RR66_EI05"),
             ("RR74_EI0184", "RR66_EI0184"), ("RR74_EI025", "RR66_EI025"), ("RR66_EI0184", "RRv66_EI0184"),
             ("PR66_EI0184", "PR66_EI025"), ("PR66_EI025", "PR66_EI05"), ("R66_EI025", "RR66_EI0184"), ("R66_EI05", "RR66_EI025"),
             ("P66_EI025", "PR66_EI0184"), ("RR74_EI05", "RR66_EI05"), ("PR74_EI05", "PR66_EI05"), ("RR74_EI025", "RR74_EI05")]
    for base in BASES:
        for a1, a2 in pairs:
            if (base, a1) in okd and (base, a2) in okd:
                out["cross"][f"{base}|{a1}->{a2}"] = mcnemar(okd[(base, a1)], okd[(base, a2)])
    # EI limit per coil and method: bracket between the largest flown EI that does not lose (pooled A1 + B1, decision rule) and
    # the smallest flown EI that loses; within_1pct (lead ENG-03 resolution rule) reported beside it. No interpolation.
    lim = {}
    for coil_name, prefix, eis in (("v3.4", "R66_EI", EIS), ("v3.4", "P66_EI", EIS[1:]), ("v3.4.1 re-route", "RR66_EI", EIS_RR),
                                   ("v3.4.1 re-route", "PR66_EI", EIS_RR[1:])):
        pts = []
        for e in eis:
            k = prefix + tag_ei(e)
            if k in out["pooled"]:
                d_ = out["pooled"][k]
                pts.append(dict(EI=float(e), arm=k, P=d_["P_arm"], P_ref=d_["P_ref"], lost=d_["lost"], gained=d_["gained"],
                                p_exact=d_["p_exact"], loses=d_["loses"], within_1pct=d_["within_1pct"],
                                hose_K=A[k]["hose_K"], cmd_rate=A[k]["over"].get("gim_cmd_rate", FSW_LIMIT)))
        if not pts:
            continue
        ok_e = [x["EI"] for x in pts if not x["loses"]]
        bad_e = [x["EI"] for x in pts if x["loses"]]
        lo = max([e for e in ok_e if not bad_e or e < min(bad_e)], default=None)
        lim[f"{coil_name}|{prefix.rstrip('_EI')}"] = dict(
            points=pts, EI_largest_not_losing=lo, EI_smallest_losing=min(bad_e) if bad_e else None,
            K_at_largest_not_losing=next((x["hose_K"] for x in pts if x["EI"] == lo), None),
            note="bracket between flown points; the limit lies in (largest not losing, smallest losing]; no interpolation")
    out["EI_limit"] = lim
    for k, v in lim.items():
        print(f"EI limit {k:28s}: not losing up to EI {v['EI_largest_not_losing']} (K {v['K_at_largest_not_losing']}), "
              f"smallest losing {v['EI_smallest_losing']}", flush=True)
    out["not_modelled"] = [
        "hose stiffness as a scalar per axis at the coil's largest singular value (the coil K matrix is coupled, K_sym_eig "
        "0.97-2.96 at EI 0.05): conservative for the hinge load, direction-independent",
        "pressurised-hose EI unknown (Mechanical ASSUMED 0.05-0.5 N m2; B-FD-1 measures); thermal stiffening of the PTFE liner "
        "with the hot case not included",
        "servo lines are DATASHEET points (SB-2292SG) with eta 0.9 ASSUMED; B-TVC-1 measures the loaded slew",
        "rule arms (R): the command slew limit stands for the loaded actuator capability in every direction and at every "
        "deflection (worst-vector value at 7 deg applied everywhere): conservative except on diagonals, where the per-axis "
        "tracker allows sqrt 2 x the limit (bracketed by Rv66)",
        "the 6.6 V plug for the whole flight (no sag); act_model 1 sag-chain cases were insensitive at 6.6 V in the actuator study",
        "re-routed coil (v1.1): the coupled K matrix has eigenvalues 93.476 and 27.546 x EI N m/rad; the scalar per axis at the "
        "largest eigenvalue over-states the stiffness in the soft direction by 3.4x (conservative for the hinge load and the "
        "servo slew); the worst-vector slew is at pose phi 316-319 deg (EI <= 0.25) or 133.5-134.5 deg (EI 0.5), motion chi near "
        "0 deg (Mechanical), applied here to every direction and deflection"]
    with open(os.path.join(OUT, "eng07_6v6.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", os.path.join(OUT, "eng07_6v6.json"), flush=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    chk = None
    if "check" in PARTS:
        chk = part_check()
        with open(os.path.join(OUT, "identity_check.json"), "w") as f:
            json.dump(chk, f, indent=1, default=float)
    if "run" in PARTS:
        part_run()
    if "eval" in PARTS:
        if chk is None and os.path.exists(os.path.join(OUT, "identity_check.json")):
            chk = json.load(open(os.path.join(OUT, "identity_check.json")))
        part_eval(chk)


if __name__ == "__main__":
    main()

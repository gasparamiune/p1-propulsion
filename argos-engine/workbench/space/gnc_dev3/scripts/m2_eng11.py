"""m2_eng11 v1.1 (GNC rev4, 2026-10-13; v1.1: phase margin as the smallest |PM| over all gain crossings and the modulus
margin sm reported beside m2_csi's min(PM), which python-control wraps into [-180, 180) so a flex crossing 151 deg from
the critical point reads -151; rigid-loop upper GM; mass variants from the v3.5.1 file; v1.0 kept in superseded_rev4/,
its 'ends' output superseded): ENG-11 / ENG-07d robustness of the TVC loop over Mechanical's V5c gimbal
stiffness (lead CHANGELOG 188 (7) RM1-08 and 204 (6); coordinator rev4 item 1). Linear CSI margins, DERIVED.

Question: is the TVC loop robust over the V5c structure stiffness 3133-7406 N m/rad (structure + rod chain, servo rigid;
spread -39.5 / +38.3 % about the 5353 mean, against the ENG-11 +/-20 % rule)? If yes, the lead amends the spread rule;
if not, GNC states the minimum K.

Model (unchanged from m2_csi v2.5 / m2_csi_v3 v1.3, imported, not copied): pitch-plane loop with rigid body, tail-wags-dog,
first slosh mode, ASSUMED first bending mode, electronics.json servo 2nd order + transport delay, sim6 attitude law, the
50 rad/s command low-pass and the engine rocking mode in the actuator path (m2_csi.loop_flex); ECU Notch2 as
m2_csi_v3.notch_tf; flight conditions from m2_csi_v3.build_conditions on the interface set named by GNC_IFACE (rev4:
iface_v35a with the v35t cfg ballast, the 285 m bracket flown in rev3; the ballast is injected through run6.cfg_of so the
condition code itself is unchanged, and the no-ballast conditions are checked equal to m2_csi_v3's).
Per pose p (9 V5c poses) and axis a, from 04-fea/stiffness/gimbal_k_summary_V5c_v1.json (read-only):
  S(p, a)  structure + rod chain with the servo rigid: mech_T (primary), mech_T_chainlow / mech_C_chainhigh (variants)
  g(p, a)  servo kinematic factor = [1 / (1/smin_T - 1/mech_T)] / 58, i.e. the FE's own series split (checked against
           the smax_T / 174 split, and equal to n^2 at the centre pose)
  K_tot    = 1 / (1/S + 1/(K_s g)), K_s the servo output stiffness (ASSUMED 58-174 N m/rad, electronics.json v1 via
           mechanical.json v2.1; B-TVC-1 measures it)
  J_refl   = J g(p, a) (primary: the rotor and the servo spring reflect through the same pose-dependent ratio) or J n^2
           with n = mechanical.json gear_ratio_n (run6 convention, sensitivity 'n48')
  f        = sqrt(K_tot / (I_piv + J_refl)) / 2 pi with I_piv of each flight condition (full / landing).
The loop depends on K, I and J only through (f, zeta) (m2_csi_v3 ftarget note), so each corner is evaluated with
K = (2 pi f)^2 I_piv and J 0 (identical dynamics), which also lets equal corners share one evaluation (cache).
Notch per axis (ENG-07d: separate alpha / beta centres set from B-TVC-1), fixed for the flight:
  f_n = c x e x f(centre pose, a) in the landing state, same K_s / chain / J / kinematics as the build;
  e in {0.95, 1, 1.05}: B-TVC-1 measurement error +/-5 % (the ENG-07d design basis); c: placement factor (1 = at the
  measured centre-pose mode); ECU default Q 1 / -12 dB, plus Q 0.7, Q 0.5 and -20 dB variants; 'lpf' = no notch.
  RESEARCH PROPOSAL, not baselined: pose-scheduled notch 'sched' (f_n = e x f(p, a), the ECU looks the mode up from the
  AS5048A gimbal angles in a table measured at B-TVC-1 over the poses). Hypothesis: it removes the pose mistune;
  comparator: the fixed notch; evidence: this linear scan only; refutation: B-TVC-1 shows mode-vs-pose not repeatable
  within +/-5 % or the table lookup adds a lag that costs > 1 dB.
Metric (ENG-07d as written): closed loop stable and upper gain margin >= 6 dB over all phase crossings at every corner of
the floor20 set (landing 100 N / hover / 500 N and full-tank 500 N with max-q aero, servo nom / worst / fast); the 62.5 N
stretch floor is reported apart ('f62'), as in m2_csi_v3. Rigid-loop phase margin with each notch placed at its lowest
centre frequency is reported (the notch must not eat the rigid margin; rigid baseline PM min from the same conditions).
Evaluation: m2_csi.margins_all + closed-loop poles exactly as m2_csi_v3.evaluate (the frequency-response extras of
evaluate are skipped for speed; a self-check compares both on sample corners).
Parts (env GNC_E11_PART, comma list): ends (lo / nominal / hi ends asked by the lead), pose (main per-pose scan),
place (fixed-notch placement and Q / depth variants), sens (J 2.7e-3 / 0.76e-3, kinematics n48, chain low / high),
kstruct (structure-only sweep at the centre kinematics), mink (minimum structure scale per axis and K_s), ksmin (minimum
K_s for the V5c structure as is). Each part writes out/rev4/eng11/eng11_<part>.json.
Hypotheses and limits: linear, one axis at a time (cross terms K_xy up to 16 % of the diagonal at the cone poses are
neglected; the extreme poses betam7 / betap7 have |K_xy| < 0.1 %); rotor inertia lumped on the engine side; mount damping
zeta 0.02 / 0.05 / 0.10 (ASSUMED, run6 MC range U(0.02, 0.10)); servo dynamics electronics.json dynamics_for_GNC (ASSUMED
2nd order 94.2 rad/s, zeta 0.7, unchanged in electronics.json v3: checked); K_s and J ASSUMED until B-TVC-1.
DERIVED analysis only: no hardware data, not physical approval."""
import hashlib
import json
import os
import sys
import time
import numpy as np
import control as ct

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m2_csi as C  # noqa: E402
import m2_csi_v3 as V3  # noqa: E402
from gncsim import run6 as R, sim6 as s6  # noqa: E402

VERSION = "m2_eng11 v1.1"
SP = "/home/claude/work/space"
HUB = "/home/claude/work/shared-fallback/engine"
V5C = f"{HUB}/04-fea/stiffness/gimbal_k_summary_V5c_v1.json"
MECH_HUB = f"{HUB}/interfaces/mechanical.json"
EL_HUB = f"{HUB}/interfaces/electronics.json"
MASS_V35 = f"{SP}/out/rev3/mass_v35/mass_v35_vs_v3d.json"
MASS_V351 = f"{SP}/out/rev4/mass_v351/mass_v351_vs_v3d.json"
RELAY = f"{SP}/gnc_dev3/data/relay/lead_relay_mech_fea_k_20261012.json"
OUT = os.environ.get("GNC_E11_OUT", f"{SP}/out/rev4/eng11")
PARTS = [p for p in os.environ.get("GNC_E11_PART", "ends").split(",") if p]
MASS_VARIANT = os.environ.get("GNC_E11_MASS", "v35t")
AXES = ("alpha", "beta")
ZETAS = (0.02, 0.05, 0.10)
ERRS = (0.95, 1.0, 1.05)
KS_FULL = (58.0, 87.0, 116.0, 145.0, 174.0)
KS3 = (58.0, 116.0, 174.0)
J_C, J_HI, J_LO = 1.6e-3, 2.7e-3, 0.76e-3      # ENG-07c estimate 1.6e-3 (0.76-2.7e-3), ASSUMED
NOTCH_ECU = (1.0, -12.0)                      # ECU firmware default (Notch2 Q, depth dB)


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


# ----------------------------------------------------------------------------------------------------------- inputs
def v5c_table():
    d = json.load(open(V5C))
    n_m = float(json.load(open(MECH_HUB))["tvc_actuation"]["gear_ratio_n"]["v"])
    T = {}
    chk = []
    for p, q in d["poses"].items():
        for a in AXES:
            k = f"K_{a}"
            st = q["mech_T"][k]
            g58 = 1.0 / (1.0 / q["smin_T"][k] - 1.0 / st) / 58.0
            g174 = 1.0 / (1.0 / q["smax_T"][k] - 1.0 / st) / 174.0
            chk.append(abs(g174 / g58 - 1.0))
            T[(p, a)] = dict(S=dict(T=st, low=q["mech_T_chainlow"][k], high=q["mech_C_chainhigh"][k]), g=g58, g174=g174,
                             smin_T=q["smin_T"][k], smax_T=q["smax_T"][k], alpha_deg=q["alpha_deg"], beta_deg=q["beta_deg"],
                             K_xy=q["mech_T"]["K_xy"])
    return d, T, n_m, max(chk)


def conditions():
    """m2_csi_v3.build_conditions on the current GNC_IFACE, with the mass variant's cfg ballast injected via cfg_of."""
    relay = json.load(open(RELAY))
    extra = {}
    if MASS_VARIANT != "none":
        vv = json.load(open(MASS_V35))["simulator"]["variants"]
        if MASS_VARIANT not in vv:
            vv = json.load(open(MASS_V351))["simulator"]["variants"]
        s = vv[MASS_VARIANT]
        if os.path.realpath(s["iface"]) != os.path.realpath(os.environ.get("GNC_IFACE", "")):
            raise RuntimeError(f"mass variant {MASS_VARIANT} needs GNC_IFACE {s['iface']}")
        if float(s["ballast_kg"]) > 0.0:
            extra = dict(ballast=float(s["ballast_kg"]), ballast_z=float(s["ballast_z_m"]))
    base, meta0, src0 = V3.build_conditions(relay)
    if not extra:
        return base, meta0, src0, extra, None
    orig = R.cfg_of
    try:
        R.cfg_of = lambda **kw: orig(**dict(kw, **extra))
        conds, meta, src = V3.build_conditions(relay)
    finally:
        R.cfg_of = orig
    # self-check: the injection changes the vehicle mass terms only; the condition code path is the same
    same_keys = all(set(conds[k]) == set(base[k]) for k in base) and list(conds) == list(base)
    return conds, meta, src, extra, dict(same_keys=same_keys, no_ballast_I_piv=meta0["landing"]["I_piv"],
                                         ballast_I_piv=meta["landing"]["I_piv"])


def el_check(src):
    """electronics.json v3 (hub) keeps dynamics_for_GNC = the pinned v1 values used by the conditions."""
    hub = json.load(open(EL_HUB))["actuators"]["tvc_A"]["dynamics_for_GNC"]["v"]
    pin = src["servo_dynamics"]
    keys = ("omega_n_rad_s", "omega_n_range_rad_s", "zeta", "transport_delay_s")
    return dict(equal=all(hub[k] == pin[k] for k in keys), hub_version=json.load(open(EL_HUB)).get("version"),
                hub_sha16=sha16(EL_HUB), keys=list(keys))


# ------------------------------------------------------------------------------------------------------- evaluation
_CACHE = {}
_NEVAL = [0, 0]


def margins(L):
    """m2_csi.margins_all's post-processing of one ct.stability_margins(returnall=True) call, plus the smallest |PM| over
    all gain crossings (python-control wraps PM into [-180, 180): a flex crossing reads e.g. -151 deg, i.e. 151 deg from
    the critical point, so min(PM) is not the closest crossing; min |PM| is) and the minimum distance to -1 (sm)."""
    gm_all, pm_all, sm, wpc_all, wgc_all, wms = ct.stability_margins(L, returnall=True)
    gm_all = np.atleast_1d(gm_all); pm_all = np.atleast_1d(pm_all)
    up = [20 * np.log10(g) for g in gm_all if np.isfinite(g) and g > 1.0]
    lo = [20 * np.log10(g) for g in gm_all if np.isfinite(g) and 0.0 < g < 1.0]
    pm = [p for p in pm_all if np.isfinite(p)]
    return (float(min(up)) if up else None, float(max(lo)) if lo else None, float(min(pm)) if pm else None,
            float(np.min(np.atleast_1d(sm))), float(min(abs(p) for p in pm)) if pm else None)


def ev(cond_name, cond, f_r, zr, notch):
    """(stable, gm_up_dB, pm_min_deg, ok6, pm_abs_min_deg, sm) of one corner: m2_csi_v3.evaluate's margin and stability
    calls, without its frequency-response extras. notch = (f0 Hz, Q, depth dB) or None. pm_min_deg is m2_csi's min(PM)
    (wrapped, kept for continuity); pm_abs_min_deg the smallest angular distance of any gain crossing from -180 deg; sm the
    minimum distance of L(jw) to -1 (modulus margin)."""
    key = (cond_name, round(f_r, 6), zr, None if notch is None else tuple(round(x, 6) for x in notch))
    _NEVAL[1] += 1
    if key in _CACHE:
        return _CACHE[key]
    _NEVAL[0] += 1
    c = V3.flex_case(cond, (2.0 * np.pi * f_r) ** 2 * cond["I_piv"], zr, 0.0, 1.0)
    L = ct.series(C.cmd_filter(c), C.loop_flex(c))
    if notch is not None:
        L = ct.series(V3.notch_tf(*notch), L)
    gm_up, gm_lo, pm_min, sm, pm_abs = margins(L)
    stable = bool(np.all(np.real(ct.poles(ct.feedback(L, 1))) < 0))
    r = (stable, gm_up, pm_min, bool(stable and (gm_up is None or gm_up >= 6.0)), pm_abs, sm)
    _CACHE[key] = r
    return r


_RCACHE = {}


def ev_rigid(conds, notch):
    """Rigid loop (no rocking mode) with a notch: min phase margin (python-control PM and min |PM|), min upper GM, min
    modulus margin and unstable count over the conditions."""
    key = None if notch is None else tuple(round(x, 6) for x in notch)
    if key in _RCACHE:
        return _RCACHE[key]
    pms, pabs, gms, sms, nu = [], [], [], [], 0
    for cn, cond in conds.items():
        c = dict(cond, w_rock=1.0)
        L = ct.series(C.cmd_filter(c), C.loop(c))
        if notch is not None:
            L = ct.series(V3.notch_tf(*notch), L)
        gm_up, gm_lo, pm_min, sm, pm_abs = margins(L)
        st = bool(np.all(np.real(ct.poles(ct.feedback(L, 1))) < 0))
        nu += 0 if st else 1
        if st and pm_min is not None:
            pms.append(pm_min); pabs.append(pm_abs)
        if st and gm_up is not None:
            gms.append(gm_up)
        if st:
            sms.append(sm)
    r = dict(n_unstable=nu, pm_min_deg=min(pms) if pms else None, pm_abs_min_deg=min(pabs) if pabs else None,
             gm_up_min_dB=min(gms) if gms else None, sm_min=min(sms) if sms else None)
    _RCACHE[key] = r
    return r


def self_check(conds):
    """ev() against m2_csi_v3.evaluate on sample corners (same stability flag, GM and PM)."""
    rng = np.random.default_rng(11)
    names = list(conds)
    out = []
    for _ in range(24):
        cn = names[int(rng.integers(len(names)))]
        f_r = float(rng.uniform(13.0, 32.0)); zr = float(rng.choice(ZETAS))
        nt = None if rng.random() < 0.25 else (f_r * float(rng.uniform(0.8, 1.2)), 1.0, -12.0)
        a = ev(cn, conds[cn], f_r, zr, nt)
        c = V3.flex_case(conds[cn], (2.0 * np.pi * f_r) ** 2 * conds[cn]["I_piv"], zr, 0.0, 1.0)
        Lc = ct.series(C.cmd_filter(c), C.loop_flex(c))
        if nt is not None:
            Lc = ct.series(V3.notch_tf(*nt), Lc)
        ma = C.margins_all(Lc)
        mb = margins(Lc)
        same_ma = all((x is None and y is None) or (x is not None and y is not None and x == y) for x, y in zip(ma, mb[:4]))
        b = V3.evaluate(c, True, nt)
        # same corner with the physical K and J split (J 1.6e-3 at n 4.8): identical dynamics expected
        Kp = (2.0 * np.pi * f_r) ** 2 * (conds[cn]["I_piv"] + J_C * 4.8 ** 2)
        b2 = V3.evaluate(V3.flex_case(conds[cn], Kp, zr, J_C, 4.8), True, nt)
        out.append(dict(cond=cn, f_r=f_r, zeta=zr, notch=nt, same_as_margins_all=bool(same_ma), pm_abs=a[4], sm=a[5],
                        fast=[a[0], a[1], a[2]], ref=[b["stable"], b["gm_up_dB"],
                                                                                          b["pm_min_deg"]],
                        ref_KJ=[b2["stable"], b2["gm_up_dB"], b2["pm_min_deg"]]))

    def d(x, y):
        return 0.0 if (x is None and y is None) else (abs(x - y) if (x is not None and y is not None) else 99.0)
    worst = max(max(d(o["fast"][1], o["ref"][1]), d(o["fast"][1], o["ref_KJ"][1])) for o in out)
    worst_pm = max(d(o["fast"][2], o["ref"][2]) for o in out)
    same_st = all(o["fast"][0] == o["ref"][0] == o["ref_KJ"][0] for o in out)
    same_m = all(o["same_as_margins_all"] for o in out)
    return dict(n=len(out), same_stability=same_st, max_gm_diff_dB=worst, max_pm_diff_deg=worst_pm,
                margins_equal_m2_csi_margins_all=same_m,
                passed=bool(same_st and same_m and worst < 0.01 and worst_pm < 0.01), rows=out)


# ------------------------------------------------------------------------------------------------------ mode model
class Model:
    def __init__(self, T, n_m, conds):
        self.T, self.n2, self.conds = T, n_m * n_m, conds
        self.Ip_land = conds["landing|hover|act_nom|noaero"]["I_piv"]
        self.poses = sorted({p for p, _ in T}, key=lambda p: list(dict.fromkeys(p for p, _ in T)).index(p))

    def ktot(self, p, a, Ks, chain="T", s=1.0):
        t = self.T[(p, a)]
        return 1.0 / (1.0 / (s * t["S"][chain]) + 1.0 / (Ks * t["g"]))

    def jrefl(self, p, a, J, kin):
        return J * (self.T[(p, a)]["g"] if kin == "cons" else self.n2)

    def f(self, p, a, Ks, J, kin="cons", chain="T", Ip=None, s=1.0):
        Ip = self.Ip_land if Ip is None else Ip
        return float(np.sqrt(self.ktot(p, a, Ks, chain, s) / (Ip + self.jrefl(p, a, J, kin))) / (2.0 * np.pi))


def is62(cn):
    return "floor62N" in cn


def scan(M, Ks_list, J, kin, chain, notch, axes=AXES, poses=None, s=1.0, keep_rows=False, early=False,
         zetas=ZETAS, errs=ERRS):
    """Corners over poses x axes x K_s x zeta x e x conditions for one notch rule.
    notch: ('lpf',) | ('fixed', c, Q, depth) | ('sched', Q, depth). Returns per (axis, K_s) summaries (floor20 / f62),
    per-pose worst GM, and the notch / rigid-loop figures. early=True stops at the first floor20 failure (pass/fail use)."""
    poses = poses or M.poses
    res = {}
    for a in axes:
        for Ks in Ks_list:
            agg = dict(floor20=[0, 0, 0, None, None, None, None, None], f62=[0, 0, 0, None, None, None, None, None])
            per_pose = {}
            fn_all = []
            for p in poses:
                pw = None
                for e in (errs if notch[0] != "lpf" else (1.0,)):
                    for zr in zetas:
                        for cn, cond in M.conds.items():
                            f_r = M.f(p, a, Ks, J, kin, chain, Ip=cond["I_piv"], s=s)
                            if notch[0] == "lpf":
                                nt = None
                            elif notch[0] == "fixed":
                                nt = (notch[1] * e * M.f("centre", a, Ks, J, kin, chain, s=s), notch[2], notch[3])
                            else:
                                nt = (e * M.f(p, a, Ks, J, kin, chain, s=s), notch[1], notch[2])
                            if nt is not None:
                                fn_all.append(nt[0])
                            st, gm, pm, ok, pma, sm = ev(cn, cond, f_r, zr, nt)
                            g = agg["f62" if is62(cn) else "floor20"]
                            g[0] += 1; g[1] += 0 if st else 1; g[2] += 0 if ok else 1
                            if st and pma is not None and (g[6] is None or pma < g[6]):
                                g[6] = pma
                            if st and (g[7] is None or sm < g[7]):
                                g[7] = sm
                            if st and gm is not None and (g[3] is None or gm < g[3]):
                                g[3] = gm
                                g[5] = f"{p}|{a}|Ks{Ks:g}|e{e:g}|z{zr:g}|{cn}|f{f_r:.2f}|fn{(nt[0] if nt else 0):.2f}"
                            if not st and (g[5] is None or not g[5].startswith("UNSTABLE")):
                                g[5] = f"UNSTABLE {p}|{a}|Ks{Ks:g}|e{e:g}|z{zr:g}|{cn}|f{f_r:.2f}"
                            if st and pm is not None and (g[4] is None or pm < g[4]):
                                g[4] = pm
                            if not is62(cn):
                                gv = gm if st else -99.0
                                if gv is not None and (pw is None or gv < pw):
                                    pw = gv
                            if early and not is62(cn) and not ok:
                                return dict(pass_floor20=False, first_fail=f"{p}|{a}|Ks{Ks:g}|e{e:g}|z{zr:g}|{cn}")
                per_pose[p] = dict(gm_min_floor20=pw, f_land_Hz=M.f(p, a, Ks, J, kin, chain, s=s),
                                   K_tot=M.ktot(p, a, Ks, chain, s),
                                   mis_vs_centre=(M.f("centre", a, Ks, J, kin, chain, s=s) / M.f(p, a, Ks, J, kin, chain, s=s)))
            out = {k: dict(n=v[0], n_unstable=v[1], n_below_6dB=v[2], gm_up_min_dB=v[3], pm_min_deg=v[4], worst=v[5],
                           pm_abs_min_deg=v[6], sm_min=v[7], pass_6dB=v[2] == 0) for k, v in agg.items()}
            out["per_pose"] = per_pose
            if fn_all:
                fmin = min(fn_all)
                out["notch_f_range_Hz"] = [fmin, max(fn_all)]
                out["rigid_with_lowest_notch"] = ev_rigid(M.conds, (fmin, notch[-2], notch[-1]))
            res[f"{a}|Ks{Ks:g}"] = out
    if early:
        return dict(pass_floor20=True)
    return res


def compact(res):
    return {k: dict(floor20=dict((kk, v["floor20"][kk]) for kk in ("n", "n_unstable", "n_below_6dB", "gm_up_min_dB",
                                                                   "pm_min_deg", "pm_abs_min_deg", "sm_min", "worst",
                                                                   "pass_6dB")),
                    f62=dict((kk, v["f62"][kk]) for kk in ("n", "n_unstable", "n_below_6dB", "gm_up_min_dB",
                                                           "pm_abs_min_deg", "sm_min", "pass_6dB")),
                    per_pose_gm_min=dict((p, None if q["gm_min_floor20"] is None else round(q["gm_min_floor20"], 2))
                                         for p, q in v["per_pose"].items()),
                    per_pose_f_Hz=dict((p, round(q["f_land_Hz"], 2)) for p, q in v["per_pose"].items()),
                    per_pose_mis=dict((p, round(q["mis_vs_centre"], 4)) for p, q in v["per_pose"].items()),
                    notch_f_range_Hz=v.get("notch_f_range_Hz"), rigid_with_lowest_notch=v.get("rigid_with_lowest_notch"))
            for k, v in res.items()}


# ------------------------------------------------------------------------------------------------------------ parts
def part_ends(M, T):
    """The lead's three points: structure 3133 (low end: betam7 beta, chain-low), 5353 (V5c mean, centre kinematics,
    notch on its own mode) and 7406 (high end: betam7 alpha). Each with its axis notch at the centre-pose mode."""
    d = json.load(open(V5C))
    pts = {
        "lo_3133": dict(pose="betam7", axis="beta", chain="low", S=T[("betam7", "beta")]["S"]["low"]),
        "nom_5353": dict(pose=None, axis=None, chain=None, S=float(d["variant"]["mean"])),
        "hi_7406": dict(pose="betam7", axis="alpha", chain="T", S=T[("betam7", "alpha")]["S"]["T"]),
    }
    out = {}
    for nm, pt in pts.items():
        rows = {}
        for Ks in KS3:
            for kin in ("cons", "n48"):
                for rule in (("lpf",), ("fixed", 1.0) + NOTCH_ECU, ("sched",) + NOTCH_ECU):
                    agg = dict(floor20=[0, 0, 0, None, None, None, None], f62=[0, 0, 0, None, None, None, None])
                    fz = {}
                    for zr in ZETAS:
                        for e in (ERRS if rule[0] != "lpf" else (1.0,)):
                            for cn, cond in M.conds.items():
                                if pt["pose"] is None:
                                    g = M.n2          # nominal: centre kinematics, S = mean
                                    Kt = 1.0 / (1.0 / pt["S"] + 1.0 / (Ks * g))
                                    Jr = J_C * M.n2
                                    f_r = float(np.sqrt(Kt / (cond["I_piv"] + Jr)) / (2 * np.pi))
                                    f_ref = float(np.sqrt(Kt / (M.Ip_land + Jr)) / (2 * np.pi))
                                    f_own = f_ref
                                else:
                                    f_r = M.f(pt["pose"], pt["axis"], Ks, J_C, kin, pt["chain"], Ip=cond["I_piv"])
                                    f_ref = M.f("centre", pt["axis"], Ks, J_C, kin, pt["chain"])
                                    f_own = M.f(pt["pose"], pt["axis"], Ks, J_C, kin, pt["chain"])
                                nt = None if rule[0] == "lpf" else (
                                    ((f_ref if rule[0] == "fixed" else f_own) * e, rule[-2], rule[-1]))
                                st, gm, pm, ok, pma, sm = ev(cn, cond, f_r, zr, nt)
                                g_ = agg["f62" if is62(cn) else "floor20"]
                                g_[0] += 1; g_[1] += 0 if st else 1; g_[2] += 0 if ok else 1
                                if st and pma is not None and (g_[5] is None or pma < g_[5]):
                                    g_[5] = pma
                                if st and (g_[6] is None or sm < g_[6]):
                                    g_[6] = sm
                                if st and gm is not None and (g_[3] is None or gm < g_[3]):
                                    g_[3] = gm
                                if st and pm is not None and (g_[4] is None or pm < g_[4]):
                                    g_[4] = pm
                                if not is62(cn):
                                    fz.setdefault(f"z{zr:g}", []).append(gm if st else -99.0)
                                if cn == "landing|hover|act_nom|noaero" and zr == 0.05 and e == 1.0:
                                    f_hover = f_r
                    key = f"Ks{Ks:g}|{kin}|{rule[0]}"
                    rows[key] = dict(f_landing_Hz=f_hover, notch_ref_Hz=(None if rule[0] == "lpf" else
                                                                         (f_ref if rule[0] == "fixed" else f_own)),
                                     floor20=dict(n=agg["floor20"][0], n_unstable=agg["floor20"][1],
                                                  n_below_6dB=agg["floor20"][2], gm_up_min_dB=agg["floor20"][3],
                                                  pm_min_deg=agg["floor20"][4], pm_abs_min_deg=agg["floor20"][5],
                                                  sm_min=agg["floor20"][6]),
                                     f62=dict(n=agg["f62"][0], n_unstable=agg["f62"][1], n_below_6dB=agg["f62"][2],
                                              gm_up_min_dB=agg["f62"][3], pm_abs_min_deg=agg["f62"][5],
                                              sm_min=agg["f62"][6]),
                                     gm_min_by_zeta=dict((k, min(v)) for k, v in fz.items()))
                    if kin == "n48" and pt["pose"] is None:
                        break
        out[nm] = dict(point=pt, rows=rows)
        r0 = rows[f"Ks58|cons|fixed"]; r1 = rows[f"Ks174|cons|fixed"]
        print(f"ends {nm:9s} S {pt['S']:7.1f}: fixed notch Ks58 f {r0['f_landing_Hz']:.1f} Hz GMmin {r0['floor20']['gm_up_min_dB']}"
              f" (<6dB {r0['floor20']['n_below_6dB']}/{r0['floor20']['n']}) | Ks174 f {r1['f_landing_Hz']:.1f} Hz GMmin "
              f"{r1['floor20']['gm_up_min_dB']} (<6dB {r1['floor20']['n_below_6dB']})", flush=True)
    return out


def part_pose(M):
    out = {}
    for nm, (Ksl, rule) in {"lpf": (KS3, ("lpf",)), "fixed_c1_Q1_-12": (KS_FULL, ("fixed", 1.0) + NOTCH_ECU),
                            "sched_Q1_-12": (KS_FULL, ("sched",) + NOTCH_ECU)}.items():
        t0 = time.time()
        r = scan(M, Ksl, J_C, "cons", "T", rule)
        out[nm] = compact(r)
        for k, v in out[nm].items():
            print(f"pose {nm:18s} {k:12s}: floor20 GMmin {v['floor20']['gm_up_min_dB'] if v['floor20']['gm_up_min_dB'] is None else round(v['floor20']['gm_up_min_dB'], 2)}"
                  f" unstable {v['floor20']['n_unstable']} <6dB {v['floor20']['n_below_6dB']}/{v['floor20']['n']} | worst "
                  f"{v['floor20']['worst']}", flush=True)
        print(f"   ({time.time() - t0:.0f} s, evals {_NEVAL})", flush=True)
    return out


def part_place(M):
    out = {}
    rules = {}
    for c_ in (0.85, 0.90, 0.95, 1.05, 1.10):
        rules[f"fixed_c{c_:g}_Q1_-12"] = ("fixed", c_) + NOTCH_ECU
    rules["fixed_c1_Q0.7_-12"] = ("fixed", 1.0, 0.7, -12.0)
    rules["fixed_c1_Q0.5_-12"] = ("fixed", 1.0, 0.5, -12.0)
    rules["fixed_c1_Q1_-20"] = ("fixed", 1.0, 1.0, -20.0)
    rules["fixed_c0.9_Q0.7_-12"] = ("fixed", 0.9, 0.7, -12.0)
    for nm, rule in rules.items():
        t0 = time.time()
        out[nm] = compact(scan(M, KS3, J_C, "cons", "T", rule))
        print(f"place {nm:22s}: " + "; ".join(f"{k} {'+' if v['floor20']['pass_6dB'] else '-'}{v['floor20']['gm_up_min_dB'] if v['floor20']['gm_up_min_dB'] is None else round(v['floor20']['gm_up_min_dB'], 1)}"
                                             for k, v in out[nm].items()) + f" ({time.time() - t0:.0f} s)", flush=True)
    return out


def part_sens(M):
    out = {}
    for nm, (J, kin, chain) in {"J2.7": (J_HI, "cons", "T"), "J0.76": (J_LO, "cons", "T"), "n48": (J_C, "n48", "T"),
                                "chain_low": (J_C, "cons", "low"), "chain_high": (J_C, "cons", "high")}.items():
        for rn, rule in (("fixed_c1_Q1_-12", ("fixed", 1.0) + NOTCH_ECU), ("sched_Q1_-12", ("sched",) + NOTCH_ECU)):
            t0 = time.time()
            out[f"{nm}|{rn}"] = compact(scan(M, KS3, J, kin, chain, rule))
            print(f"sens {nm:10s} {rn:16s}: " + "; ".join(f"{k} {'+' if v['floor20']['pass_6dB'] else '-'}{v['floor20']['gm_up_min_dB'] if v['floor20']['gm_up_min_dB'] is None else round(v['floor20']['gm_up_min_dB'], 1)}"
                                                         for k, v in out[f"{nm}|{rn}"].items()) + f" ({time.time() - t0:.0f} s)", flush=True)
    return out


def part_kstruct(M):
    """Structure-only sweep at the centre kinematics (n^2), notch on the build's own mode x e: the margin as a function
    of the structure stiffness alone (no pose mistune)."""
    out = {}
    for S in (2000.0, 3133.2, 4325.1, 5353.1, 6539.3, 7406.0, 10000.0, 1.0e9):
        for Ks in KS3:
            Kt = 1.0 / (1.0 / S + 1.0 / (Ks * M.n2))
            for rn, rule in (("lpf", None), ("own_Q1_-12", NOTCH_ECU)):
                agg = [0, 0, 0, None]
                for zr in ZETAS:
                    for e in (ERRS if rule else (1.0,)):
                        for cn, cond in M.conds.items():
                            if is62(cn):
                                continue
                            f_r = float(np.sqrt(Kt / (cond["I_piv"] + J_C * M.n2)) / (2 * np.pi))
                            fo = float(np.sqrt(Kt / (M.Ip_land + J_C * M.n2)) / (2 * np.pi))
                            st, gm, pm, ok = ev(cn, cond, f_r, zr, None if rule is None else (fo * e,) + rule)[:4]
                            agg[0] += 1; agg[1] += 0 if st else 1; agg[2] += 0 if ok else 1
                            if st and gm is not None and (agg[3] is None or gm < agg[3]):
                                agg[3] = gm
                out[f"S{S:g}|Ks{Ks:g}|{rn}"] = dict(S=S, K_s=Ks, K_tot=Kt, f_landing_Hz=fo, n=agg[0], n_unstable=agg[1],
                                                    n_below_6dB=agg[2], gm_up_min_dB=agg[3], pass_6dB=agg[2] == 0)
        print(f"kstruct S {S:9.0f}: " + "; ".join(f"Ks{Ks:g} {rn} f {out[f'S{S:g}|Ks{Ks:g}|{rn}']['f_landing_Hz']:.1f} GM "
                                                  f"{out[f'S{S:g}|Ks{Ks:g}|{rn}']['gm_up_min_dB'] if out[f'S{S:g}|Ks{Ks:g}|{rn}']['gm_up_min_dB'] is None else round(out[f'S{S:g}|Ks{Ks:g}|{rn}']['gm_up_min_dB'], 1)}"
                                                  for Ks in KS3 for rn in ("lpf", "own_Q1_-12")), flush=True)
    return out


def bisect_pass(fun, lo, hi, it=9):
    """Smallest x in [lo, hi] with fun(x) True, assuming fun monotone (False below, True above); None if fun(hi) False."""
    if not fun(hi):
        return None
    if fun(lo):
        return lo
    for _ in range(it):
        mid = np.sqrt(lo * hi)
        if fun(mid):
            hi = mid
        else:
            lo = mid
    return hi


def part_mink(M):
    """Minimum uniform scale s on the V5c structure stiffness of one axis (all 9 poses scaled, servo term unchanged) for
    ENG-07d at every floor20 corner; K_min at the worst and the centre pose. 'None' = no structure stiffness suffices
    (the servo term caps the mode)."""
    out = {}
    for a in AXES:
        Sw = min(M.T[(p, a)]["S"]["T"] for p in M.poses)
        Sc = M.T[("centre", a)]["S"]["T"]
        for rn, rule, kin in (("fixed_c1_Q1_-12", ("fixed", 1.0) + NOTCH_ECU, "cons"), ("sched_Q1_-12", ("sched",) + NOTCH_ECU, "cons"),
                              ("fixed_c1_Q1_-12|n48", ("fixed", 1.0) + NOTCH_ECU, "n48")):
            for Ks in KS3:
                t0 = time.time()

                def ok(s):
                    return scan(M, (Ks,), J_C, kin, "T", rule, axes=(a,), s=s, early=True)["pass_floor20"]
                s_min = bisect_pass(ok, 0.5, 1.0e4)
                if s_min is not None:
                    chk = [ok(s_min * 1.25), ok(s_min * 2.0)]
                else:
                    chk = None
                out[f"{a}|{rn}|Ks{Ks:g}"] = dict(s_min=s_min, K_struct_min_worst_pose=(None if s_min is None else s_min * Sw),
                                                 K_struct_min_centre=(None if s_min is None else s_min * Sc),
                                                 worst_pose_S_V5c=Sw, centre_S_V5c=Sc,
                                                 f_worst_pose_at_s_min_Hz=(None if s_min is None else min(
                                                     M.f(p, a, Ks, J_C, kin, "T", s=s_min) for p in M.poses)),
                                                 monotone_check_above=chk)
                print(f"mink {a:5s} {rn:22s} Ks {Ks:5.0f}: s_min {s_min if s_min is None else round(s_min, 3)} -> K_struct worst "
                      f"pose {out[f'{a}|{rn}|Ks{Ks:g}']['K_struct_min_worst_pose']} (V5c {Sw:.0f}) check {chk} "
                      f"({time.time() - t0:.0f} s)", flush=True)
    return out


def part_ksmin(M):
    """Minimum servo output stiffness K_s for which the V5c structure as is meets ENG-07d on every floor20 corner."""
    out = {}
    for a in AXES:
        for rn, rule in (("fixed_c1_Q1_-12", ("fixed", 1.0) + NOTCH_ECU), ("sched_Q1_-12", ("sched",) + NOTCH_ECU),
                         ("lpf", ("lpf",))):
            t0 = time.time()

            def ok(Ks):
                return scan(M, (Ks,), J_C, "cons", "T", rule, axes=(a,), early=True)["pass_floor20"]
            k_min = bisect_pass(ok, 58.0, 2000.0)
            out[f"{a}|{rn}"] = dict(K_s_min=k_min, f_min_pose_Hz=(None if k_min is None else min(
                M.f(p, a, k_min, J_C, "cons", "T") for p in M.poses)),
                monotone_check_above=(None if k_min is None else [ok(k_min * 1.2), ok(k_min * 1.6)]))
            print(f"ksmin {a:5s} {rn:16s}: K_s min {k_min if k_min is None else round(k_min, 1)} N m/rad "
                  f"({time.time() - t0:.0f} s)", flush=True)
    return out


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    d5, T, n_m, gchk = v5c_table()
    conds, meta, src, extra, cchk = conditions()
    M = Model(T, n_m, conds)
    head = dict(version=VERSION, date=time.strftime("%Y-%m-%d"), sim=s6.SIM6_VERSION, iface=os.environ.get("GNC_IFACE"),
                iface_pin=os.environ.get("GNC_IFACE_PIN"), mass_variant=MASS_VARIANT, cfg_ballast=extra,
                conditions_check=cchk, mass_properties=meta, sources=src, electronics_hub_check=el_check(src),
                inputs_sha256_16={V5C: sha16(V5C), MECH_HUB: sha16(MECH_HUB), EL_HUB: sha16(EL_HUB), MASS_V35: sha16(MASS_V35),
                                  MASS_V351: sha16(MASS_V351),
                                  RELAY: sha16(RELAY), os.path.abspath(__file__): sha16(os.path.abspath(__file__)),
                                  os.path.abspath(C.__file__): sha16(C.__file__), os.path.abspath(V3.__file__): sha16(V3.__file__)},
                n_mech=n_m, servo_split_check_max_rel=gchk, I_piv_landing=M.Ip_land,
                pose_table={f"{p}|{a}": dict(S_T=v["S"]["T"], S_low=v["S"]["low"], S_high=v["S"]["high"], g=v["g"],
                                             n_eff=float(np.sqrt(v["g"])), K_tot_Ks58=M.ktot(p, a, 58.0),
                                             K_tot_Ks174=M.ktot(p, a, 174.0),
                                             f_cons_Ks58_Hz=M.f(p, a, 58.0, J_C), f_cons_Ks174_Hz=M.f(p, a, 174.0, J_C),
                                             f_n48_Ks58_Hz=M.f(p, a, 58.0, J_C, "n48"), f_n48_Ks174_Hz=M.f(p, a, 174.0, J_C, "n48"),
                                             K_xy_mech_T=v["K_xy"]) for (p, a), v in T.items()},
                tags=dict(stiffness="DERIVED from FEA (Mechanical V5c) + ASSUMED servo K_s 58-174 N m/rad",
                          J_int="ASSUMED (Electronics estimate 1.6e-3, 0.76-2.7e-3 kg m2)",
                          mount_damping="ASSUMED zeta 0.02-0.10", margins="DERIVED (linear model)",
                          notch_schedule="RESEARCH PROPOSAL (not baselined)"),
                metric="ENG-07d: closed loop stable and upper gain margin >= 6 dB over all phase crossings (floor20 set)")
    print(f"{VERSION}: iface {head['iface']} mass {MASS_VARIANT} {extra}; I_piv landing {M.Ip_land:.5f}; servo split "
          f"check {gchk:.2e}; electronics hub check {head['electronics_hub_check']['equal']}", flush=True)
    for nm in PARTS:
        tp = time.time()
        if nm == "selfcheck":
            res = self_check(conds)
            print("self-check", res["passed"], res["max_gm_diff_dB"], res["max_pm_diff_deg"], flush=True)
        elif nm == "ends":
            res = part_ends(M, T)
        elif nm == "pose":
            res = part_pose(M)
        elif nm == "place":
            res = part_place(M)
        elif nm == "sens":
            res = part_sens(M)
        elif nm == "kstruct":
            res = part_kstruct(M)
        elif nm == "mink":
            res = part_mink(M)
        elif nm == "ksmin":
            res = part_ksmin(M)
        else:
            raise KeyError(nm)
        o = dict(head, part=nm, result=res, wall_s=round(time.time() - tp, 1), evals=list(_NEVAL))
        p = os.path.join(OUT, f"eng11_{nm}.json")
        with open(p, "w") as f:
            json.dump(o, f, indent=1, default=float)
        print(f"wrote {p} ({time.time() - tp:.0f} s; total {time.time() - t0:.0f} s)", flush=True)


if __name__ == "__main__":
    main()

"""m2_csi_v3 v1.3 (2026-10-12): ENG-07d control-structure interaction re-check on Mechanical's FEA axis stiffness
(lead request 2026-10-12, high priority).

Model: the m2_csi v2.5 pitch-plane loop (rigid body + tail-wags-dog + first slosh mode + ASSUMED first bending mode
+ electronics.json servo 2nd order + transport delay + sim6 attitude law), with the engine rocking mode in the actuator
path (loop_flex): servo output -> axis stiffness K -> engine inertia I_piv + J_int n^2 (servo rotor lumped on the
engine side = the conservative simplification accepted by the lead; B-TVC-1 separates the two masses).
New in v3 (inputs from data/relay/lead_relay_mech_fea_k_20261012.json, no number typed here):
  * K per axis from the FEA (structure in series with the servo), at the gimbal centre and at alpha +7 deg;
  * engine inertia scaled to the CAD v3.3 wet value I_pivot 0.052 kg m2 (mechanical.json v1 mass properties
    otherwise; the scale is applied to the engine's own inertia, so J_twd moves with it);
  * J_int 0, 1.6e-3 (Electronics central) and 2.7e-3 kg m2 (upper end) at n 4.8;
  * the ECU ENG-07d notch (firmware filters.h Notch2: RBJ peaking EQ with finite depth; continuous equivalent
    H(s) = (s^2 + A w0/Q s + w0^2) / (s^2 + w0/(A Q) s + w0^2), A = 10^(depth/40)) after the 50 rad/s low-pass;
  * a structural-stiffness sweep (K_struct in series with K_servo n^2) for the Mechanical target.
Flex margin metric (ENG-07d): closed loop stable AND the upper gain margin over all phase crossings >= 6 dB.
Also reported: loop gain at the rocking frequency (gain stabilisation when <= -6 dB) and the rigid-loop phase margin
with the notch in place (the notch must not eat the rigid margins).
v1.1: part ftarget: the margins depend on K, I_piv and J_int only through the rocking frequency f_r (and the damping), so
the ENG-07d boundary is stated as the lowest f_r above which every corner has >= 6 dB, per damping and per filter variant
(low-pass 50 / 35 rad/s, notch Q1 -12 dB at +/-15 % or +/-5 % mistune), with the rigid-loop phase margin of each filter
and the stiffness that reaches it for each J_int and each end of the servo-stiffness range. Results of earlier parts are
kept when a later part rewrites the file (v1 dropped notch_gain_clamp_62N / notch_rigid_cost when the sweep part ran as
its own process). Parts base, notch and sweep are identical in v1 and v1.1.
v1.2: ftarget also reports, per grid frequency, the rigid-loop phase margin with the notch placed at that mode (worst over
the mistune set), so the notch cost is read at the frequency that sets f_min; extra filter variants from env
GNC_CSI_F_EXTRA ('name=lpf_w,Q,depth,mistune_halfwidth[,landing_wn_scale];...', Q 0 = no notch; the optional
scale multiplies the landing attitude-loop natural frequency, integral gain 0.1 wn^3 as in sim6); GNC_CSI_F_MERGE=1 adds the variants run to
an existing ftarget section instead of replacing it (stiffness conversion recomputed for every case).
v1.3: on mechanical.json >= v2 (interface set v3c) the 6-DOF engine model already reproduces the CAD mass properties
(m2_mech_v2_check C1: I_pivot within 0.05 % at five states), so the engine inertia is NOT rescaled (scale 1); the relay
scale to 0.052 kg m2 applies to mechanical.json v1 only. Parts base / notch / sweep still take K from the relay file
(mechanical.json v1 FEA); on v3c only the ftarget part is meaningful (it sweeps the mode frequency, K follows).
Env: GNC_OUT (default out/csi_v3), GNC_CSI_TAG (default fea), GNC_CSI_PART (all | base | notch | sweep | ftarget),
GNC_CSI_SWEEP_NOTCH ('Q,depth'), GNC_CSI_F_GRID (Hz list), GNC_CSI_F_ZETA, GNC_CSI_F_VARIANTS (comma list),
GNC_CSI_F_EXTRA, GNC_CSI_F_MERGE.
"""
import json
import os
import sys
import time
import numpy as np
import control as ct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import m2_csi as C  # noqa: E402
from gncsim import run6 as R, sim6 as s6, aero  # noqa: E402

OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/csi_v3")
TAG = os.environ.get("GNC_CSI_TAG", "fea")
PART = os.environ.get("GNC_CSI_PART", "all")
RELAY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "relay",
                     "lead_relay_mech_fea_k_20261012.json")
W = np.logspace(-1, 3.5, 3000)


def notch_tf(f0, q, depth_db):
    if f0 <= 0.0 or depth_db >= 0.0:
        return ct.tf([1.0], [1.0])
    w0 = 2.0 * np.pi * f0
    A = 10.0 ** (depth_db / 40.0)
    return ct.tf([1.0, A * w0 / q, w0 * w0], [1.0, w0 / (A * q), w0 * w0])


def evaluate(case, flex=True, notch=None):
    """Margins of one corner; notch = (f0 Hz, Q, depth dB) or None."""
    L = ct.series(C.cmd_filter(case), C.loop_flex(case) if flex else C.loop(case))
    if case.get("kscale", 1.0) != 1.0:
        L = ct.series(ct.tf([case["kscale"]], [1.0]), L)
    if notch is not None:
        L = ct.series(notch_tf(*notch), L)
    gm_up, gm_lo, pm_min, smarg = C.margins_all(L)
    poles = ct.poles(ct.feedback(L, 1))
    stable = bool(np.all(np.real(poles) < 0))
    r = ct.frequency_response(L, W)
    mag = np.abs(r.frdata[0, 0, :])
    wr = case.get("w_rock_eff", case["w_rock"])
    g_r = float(20 * np.log10(abs(ct.frequency_response(L, [wr]).frdata[0, 0, 0]) + 1e-300))
    # peak loop gain in the rocking band (0.6-1.6 x w_rock) and the rigid-body crossover / phase margin
    band = (W > 0.6 * wr) & (W < 1.6 * wr)
    g_band = float(20 * np.log10(mag[band].max())) if band.any() else None
    gm, pm, wcg, wcp = ct.margin(L)
    return dict(stable=stable, gm_up_dB=gm_up, gm_lo_dB=gm_lo, pm_min_deg=pm_min, pm_deg=float(pm) if np.isfinite(pm) else None,
                w_c_radps=float(wcp) if np.isfinite(wcp) else None, gain_at_rock_dB=g_r, gain_band_max_dB=g_band,
                max_real_cl_pole=float(np.max(np.real(poles))),
                ok6=bool(stable and gm_up is not None and gm_up >= 6.0) or bool(stable and gm_up is None))


def build_conditions(relay):
    """Rigid-loop conditions (as m2_csi v2.5) with the engine inertia scaled to the CAD v3.3 wet value."""
    src = R.sources()
    el = src["el"]
    dyn = el["actuators"]["tvc_A"]["dynamics_for_GNC"]["v"]
    lat = el["loop_rates_and_latency"]["latency_s"]["v"]
    tau_nom = dyn["transport_delay_s"] + lat["fc_cmd_to_ecu_tick_max"] + 0.001
    v2m = src["mech"] is not None and str(src["mech"].get("version")) != "v1"     # v1.3
    I_target = None if v2m else relay["I_pivot_wet_kgm2"]["v"]
    m_full = 2.00
    conds = {}
    meta = {}
    sI = None
    for label, m_liq in [("full", m_full), ("landing", 0.30)]:
        cfg = R.cfg_of(profile="A-D", fins=True, m_n2o=m_full)
        par, apar, comp, mp, tab, info = R.build(cfg)
        o = np.zeros(8)
        rho_l = par[s6.P_rho_l_nom]
        s6.massprops(mp, m_liq, 0.0, rho_l, par[s6.P_m_fuel0] * (1.0 if label == "full" else 0.75), o)
        m, zcg, It, Ir, me, ze, Ie, Dp = o
        zp = mp[15]
        lp = zcg - zp
        le = zp - ze
        if sI is None:
            sI = 1.0 if v2m else (I_target - me * le * le) / Ie   # wet (full) engine own inertia -> CAD v3.3 I_pivot (v1)
        Ie = Ie * sI
        Jt = Ie + me * le * (le + lp)
        Ipiv = Ie + me * le * le
        tankA = mp[9]
        tR = np.sqrt(tankA / np.pi)
        h = m_liq / (rho_l * tankA)
        xi = 1.841
        msl = min(0.5 * m_liq, m_liq * (2 * tR / (xi * (xi * xi - 1) * h)) * np.tanh(xi * h / tR))
        zs_ = mp[8] + h - 0.54 * tR
        L_b = 2.03
        d_o = info["geo"]["d"]
        d_i = d_o - 2 * info["geo"].get("wall", 0.0025)
        EI = 2.0e9 * np.pi / 64 * (d_o ** 4 - d_i ** 4)
        wb, xb, phi, dphi, Mg = C.beam_mode(L_b, EI, m / L_b)
        phig = float(np.interp(zp + 0.03, xb, phi))
        sig = float(np.interp(1.15 + 0.03, xb, dphi))
        V_mq = 68.5
        Ma_ = {}
        for fins_ in (False, True):
            g2 = dict(info["geo"]); g2["n_fins"] = 4 if fins_ else 0
            ap, cp = aero.build_aero_params(dict(g2, drogue_CdA=0.0))
            Fq = np.zeros(3); Mq = np.zeros(3); da = np.radians(1.0)
            aero.aero_forces(np.array([V_mq * np.sin(da), 0.0, V_mq * np.cos(da)]), np.zeros(3), 1.225, zcg, False, ap, cp, Fq, Mq)
            Ma_[fins_] = float(-Mq[1] / da)
        meta[label] = dict(m=m, zcg=zcg, It=It, l_p=lp, l_e=le, m_e=me, I_e_scaled=Ie, I_piv=Ipiv, J_twd=Jt,
                           I_scale=sI, f_bend_Hz=wb / (2 * np.pi), M_alpha_maxq=dict(finless=Ma_[False], fins=Ma_[True]))
        for thrust_label, F in [("floor62N", 62.5), ("floor100N", 100.0), ("hover", m * R.G0), ("max500N", 500.0)]:
            if label == "full" and thrust_label != "max500N":
                continue
            fax = F / m
            ws = np.sqrt((xi * fax / tR) * np.tanh(xi * h / tR))
            for act_label, wa, tau in [("nom", dyn["omega_n_rad_s"], tau_nom),
                                       ("worst", dyn["omega_n_range_rad_s"][0], tau_nom + 0.0032),
                                       ("fast", dyn["omega_n_range_rad_s"][1], tau_nom)]:
                for aero_label, Ma in [("noaero", 0.0)] + ([("maxq_finless", Ma_[False]), ("maxq_fins", Ma_[True])]
                                                         if label == "full" else []):
                    wn = R.DEF["att_wn_asc"] if label == "full" else R.DEF["att_wn"]
                    conds[f"{label}|{thrust_label}|act_{act_label}|{aero_label}"] = dict(
                        It=It, F=F, lp=lp, Jtwd=Jt, m_s=msl, m_r=m - msl, w_s=ws, z_s=0.005, r_s=zs_ - zcg, M_alpha=Ma,
                        w_b=wb, z_b=0.02, phi_g=phig, sigma_imu=sig, M_b=Mg, w_a=wa, z_a=dyn["zeta"], tau=tau, wn=wn,
                        zeta=0.7, Ki=0.1 * wn ** 3, I_piv=Ipiv, m=m, zcg=zcg, lpf_w=R.DEF["gim_lpf_w"],
                        lpf_z=R.DEF["gim_lpf_z"], w_rock=1.0)
    return conds, meta, dict(electronics=el.get("version"), mechanical=(src["mech"] or {}).get("version"),
                             combustion=src["comb"].get("version"), servo_dynamics=dyn, tau_nom=tau_nom)


def flex_case(cond, K, zr, J, n):
    I_add = J * n * n
    c = dict(cond, K_axis=K, zeta_rock=zr, I_add=I_add)
    c["w_rock"] = float(np.sqrt(K / (cond["I_piv"] + I_add)))
    return c


def run_set(conds, Ks, zrs, J, n, notch_rule=None, keep=False):
    """All corners for one K list; notch_rule(case) -> (f0, Q, depth) or None. Returns summary (+ rows if keep)."""
    rows = []
    for cn, cond in conds.items():
        for K in Ks:
            for zr in zrs:
                c = flex_case(cond, K, zr, J, n)
                nt = notch_rule(c) if notch_rule else None
                r = evaluate(c, True, nt)
                r.update(corner=f"{cn}|K{K:.0f}|z{zr:.2f}", K=K, zeta_rock=zr, f_rock_Hz=c["w_rock"] / (2 * np.pi),
                         notch=nt)
                rows.append(r)
    s = summarize(rows)
    s["floor20_set"] = summarize([r for r in rows if "floor62N" not in r["corner"]])
    s["floor62N_only"] = summarize([r for r in rows if "floor62N" in r["corner"]])
    return (s, rows) if keep else (s, None)


def summarize(rows):
    """Counts and worst corners; floor20_set = corners at or above the 20 % baseline floor (100 N), floor62N_only = the
    12.5 % stretch floor."""
    if not rows:
        return {}
    st = [r for r in rows if r["stable"]]
    gms = [r["gm_up_dB"] for r in st if r["gm_up_dB"] is not None]
    worst = sorted(rows, key=lambda r: (r["stable"], r["gm_up_dB"] if r["gm_up_dB"] is not None else 99.0))[:5]
    return dict(n=len(rows), n_unstable=sum(1 for r in rows if not r["stable"]), n_below_6dB=sum(1 for r in rows if not r["ok6"]),
                gm_up_min_dB=(min(gms) if gms else None), gain_at_rock_max_dB=max(r["gain_at_rock_dB"] for r in rows),
                f_rock_Hz=[min(r["f_rock_Hz"] for r in rows), max(r["f_rock_Hz"] for r in rows)],
                worst=[dict((k, w[k]) for k in ("corner", "stable", "gm_up_dB", "pm_min_deg", "gain_at_rock_dB", "f_rock_Hz", "notch"))
                       for w in worst],
                pass_6dB=bool(all(r["ok6"] for r in rows)))


def rigid_set(conds, notch=None):
    """Rigid loop (no rocking) with an optional fixed notch: rigid margins must stay (phase margin, crossover)."""
    out = []
    for cn, cond in conds.items():
        c = dict(cond, w_rock=1.0)
        r = evaluate(c, False, notch)
        out.append(dict(corner=cn, stable=r["stable"], pm_deg=r["pm_deg"], pm_min_deg=r["pm_min_deg"], gm_up_dB=r["gm_up_dB"],
                        w_c_radps=r["w_c_radps"]))
    pms = [o["pm_deg"] for o in out if o["stable"] and o["pm_deg"] is not None]
    return dict(n_unstable=sum(1 for o in out if not o["stable"]), pm_min_deg=min(pms) if pms else None,
                gm_up_min_dB=min((o["gm_up_dB"] for o in out if o["stable"] and o["gm_up_dB"] is not None), default=None),
                rows=out)


def main():
    t0 = time.time()
    os.makedirs(OUT, exist_ok=True)
    relay = json.load(open(RELAY))
    n = relay["n_linkage"]["v"]
    conds, meta, srcs = build_conditions(relay)
    Kc = relay["K_series_centre_Nm_per_rad"]["v"]; K7 = relay["K_series_alpha_p7deg_Nm_per_rad"]["v"]
    Kax = {ax: sorted(set(Kc[ax] + K7[ax])) for ax in ("alpha", "beta")}
    Jc = relay["J_int_servo_output_kgm2"]["v"]
    Js = [0.0, Jc["central"], Jc["range"][1]]
    zrs = (0.02, 0.05)
    out = dict(version=f"m2_csi_v3 v1.3 {TAG}", date=time.strftime("%Y-%m-%d"), sim=s6.SIM6_VERSION, relay=RELAY, sources=srcs,
               relay_values=relay, mass_properties=meta, K_corners=Kax, J_int=Js, zeta_rock=list(zrs),
               metric="ENG-07d: closed loop stable and upper gain margin >= 6 dB over all phase crossings")
    path = os.path.join(OUT, f"csi_v3_{TAG}.json")
    if os.path.exists(path):
        old = json.load(open(path))
        # v1.1: keep every result section written by an earlier part (v1 dropped the gain-clamp and rigid-cost sections)
        for k in ("base", "notch", "sweep", "rigid", "notch_gain_clamp_62N", "notch_rigid_cost", "ftarget"):
            if k in old:
                out[k] = old[k]
    if PART in ("all", "base"):
        base = {}
        for ax in ("alpha", "beta"):
            for J in Js:
                for flt, cfun in (("lpf", None),):
                    s, rows = run_set(conds, Kax[ax], zrs, J, n, cfun, keep=False)
                    key = f"{ax}|J{J * 1e3:g}|{flt}"
                    base[key] = s
                    print(f"{key:22s} floor20 set: unstable {s['floor20_set']['n_unstable']}/{s['floor20_set']['n']} <6dB "
                          f"{s['floor20_set']['n_below_6dB']} GMmin {s['floor20_set']['gm_up_min_dB']} | all: "
                          f"unstable {s['n_unstable']:3d}/{s['n']}  below6dB {s['n_below_6dB']:3d}  GMmin "
                          f"{s['gm_up_min_dB'] if s['gm_up_min_dB'] is None else round(s['gm_up_min_dB'], 2)}  "
                          f"gain@rock max {s['gain_at_rock_max_dB']:.1f} dB  f_rock {s['f_rock_Hz'][0]:.1f}-{s['f_rock_Hz'][1]:.1f} Hz "
                          f"({time.time() - t0:.0f}s)", flush=True)
        # nofilt reference for the worst axis without J (shows what the low-pass already buys)
        s, _ = run_set({k: dict(v, lpf_w=0.0) for k, v in conds.items()}, Kax["beta"], zrs, 0.0, n)
        base["beta|J0|nofilt"] = s
        print(f"beta|J0|nofilt          unstable {s['n_unstable']}/{s['n']} below6dB {s['n_below_6dB']} GMmin {s['gm_up_min_dB']}", flush=True)
        out["base"] = base
        out["rigid"] = dict(lpf=rigid_set(conds), lpf_nofilt=rigid_set({k: dict(v, lpf_w=0.0) for k, v in conds.items()}))
        print("rigid lpf: unstable", out["rigid"]["lpf"]["n_unstable"], "PM min", out["rigid"]["lpf"]["pm_min_deg"], flush=True)
        with open(path, "w") as f:
            json.dump(out, f, indent=1, default=float)
    NOTCHES = [(1.0, -12.0), (1.5, -15.0), (2.0, -12.0), (2.0, -20.0), (3.0, -20.0)]
    MIS = (0.85, 1.0, 1.15)
    if PART in ("all", "notch"):
        # notch centred on the measured mode of the build (B-TVC-1), mistuned by m (in-flight mode shift: pose,
        # supply voltage on the servo stiffness, thrust preload, measurement error), Q and depth from a grid
        notch = {}
        for ax in ("alpha", "beta"):
            for J in Js:
                for (q, dep) in NOTCHES:
                    for mis in MIS:
                        rule = (lambda c, mis=mis, q=q, dep=dep: (mis * c["w_rock"] / (2 * np.pi), q, dep))
                        s, _ = run_set(conds, Kax[ax], zrs, J, n, rule)
                        notch[f"{ax}|J{J * 1e3:g}|Q{q:g}|{dep:g}dB|mis{mis:g}"] = s
                    ws = [notch[f"{ax}|J{J * 1e3:g}|Q{q:g}|{dep:g}dB|mis{m:g}"] for m in MIS]
                    print(f"{ax:5s} J{J * 1e3:g} notch Q{q:g} {dep:g} dB over mistune {MIS}: all-corners unstable "
                          f"{max(w['n_unstable'] for w in ws)} <6dB {max(w['n_below_6dB'] for w in ws)} | floor20 set unstable "
                          f"{max(w['floor20_set']['n_unstable'] for w in ws)} <6dB {max(w['floor20_set']['n_below_6dB'] for w in ws)}"
                          f"/{ws[0]['floor20_set']['n']} GMmin {min((w['floor20_set']['gm_up_min_dB'] or 99) for w in ws):.2f} | "
                          f"62.5 N <6dB {max(w['floor62N_only']['n_below_6dB'] for w in ws)}/{ws[0]['floor62N_only']['n']} "
                          f"({time.time() - t0:.0f}s)", flush=True)
        out["notch"] = notch
        # 12.5 % stretch floor with the attitude-gain normalisation clamped at the 20 % thrust (loop gain x 62.5/100)
        clamp = {}
        c62 = {k: dict(v, kscale=62.5 / 100.0) for k, v in conds.items() if "floor62N" in k}
        for ax in ("alpha", "beta"):
            for J in Js:
                for (q, dep) in [(None, None)] + NOTCHES:
                    for mis in ((1.0,) if q is None else MIS):
                        rule = None if q is None else (lambda c, mis=mis, q=q, dep=dep: (mis * c["w_rock"] / (2 * np.pi), q, dep))
                        s, _ = run_set(c62, Kax[ax], zrs, J, n, rule)
                        clamp[f"{ax}|J{J * 1e3:g}|{'lpf' if q is None else f'Q{q:g}|{dep:g}dB'}|mis{mis:g}"] = s
                print(f"{ax:5s} J{J * 1e3:g} 62.5 N gain clamp: lpf <6dB {clamp[f'{ax}|J{J * 1e3:g}|lpf|mis1']['n_below_6dB']}; "
                      + "; ".join(f"Q{q:g} {dep:g}: <6dB {max(clamp[f'{ax}|J{J * 1e3:g}|Q{q:g}|{dep:g}dB|mis{m:g}']['n_below_6dB'] for m in MIS)}"
                                  for q, dep in NOTCHES), flush=True)
        out["notch_gain_clamp_62N"] = clamp
        # rigid-loop cost of each notch at the lowest and highest centre frequency considered
        rc = {}
        for f0 in (11.0, 14.0, 19.0, 27.0):
            for (q, dep) in NOTCHES:
                r = rigid_set(conds, (f0, q, dep))
                rc[f"f{f0:g}|Q{q:g}|{dep:g}dB"] = dict(n_unstable=r["n_unstable"], pm_min_deg=r["pm_min_deg"],
                                                       gm_up_min_dB=r["gm_up_min_dB"])
        out["notch_rigid_cost"] = rc
        print("notch rigid cost:", json.dumps({k: (v["n_unstable"], round(v["pm_min_deg"], 1)) for k, v in rc.items()}), flush=True)
        with open(path, "w") as f:
            json.dump(out, f, indent=1, default=float)
    if PART in ("all", "sweep"):
        # structural stiffness target: K = 1 / (1/K_struct + 1/(K_s n^2)), K_s at both ends of Mechanical's range
        Ks_out = relay["K_servo_output_Nm_per_rad"]["v"]
        qn, dn = [float(x) for x in os.environ.get("GNC_CSI_SWEEP_NOTCH", "1,-12").split(",")]
        sweep = {}
        for J in Js:
            for flt, rule in [("lpf", None)] + [(f"lpf+notch_Q{qn:g}_{dn:g}dB_mis{m:g}",
                                                 (lambda c, m=m: (m * c["w_rock"] / (2 * np.pi), qn, dn))) for m in MIS]:
                res = []
                for Kst in (1604.0, 2434.0, 4000.0, 8000.0, 16000.0, 1.0e9):
                    Ks_series = [1.0 / (1.0 / Kst + 1.0 / (ks * n * n)) for ks in Ks_out]
                    s, _ = run_set(conds, Ks_series, zrs, J, n, rule)
                    res.append(dict(K_struct=Kst, K_series=Ks_series, n_unstable=s["n_unstable"], n_below_6dB=s["n_below_6dB"],
                                    gm_up_min_dB=s["gm_up_min_dB"], f_rock_Hz=s["f_rock_Hz"], pass_6dB=s["pass_6dB"],
                                    floor20_set=dict((k, s["floor20_set"][k]) for k in ("n", "n_unstable", "n_below_6dB", "gm_up_min_dB", "pass_6dB")),
                                    floor62N_only=dict((k, s["floor62N_only"][k]) for k in ("n", "n_unstable", "n_below_6dB", "gm_up_min_dB", "pass_6dB"))))
                    print(f"sweep J{J * 1e3:g} {flt:30s} K_struct {Kst:9.0f}: all <6dB {s['n_below_6dB']}/{s['n']} | floor20 "
                          f"unstable {s['floor20_set']['n_unstable']} <6dB {s['floor20_set']['n_below_6dB']}/{s['floor20_set']['n']} "
                          f"GMmin {s['floor20_set']['gm_up_min_dB']} | f {s['f_rock_Hz'][0]:.1f}-{s['f_rock_Hz'][1]:.1f} Hz "
                          f"({time.time() - t0:.0f}s)", flush=True)
                sweep[f"J{J * 1e3:g}|{flt}"] = res
        out["sweep"] = sweep
        with open(path, "w") as f:
            json.dump(out, f, indent=1, default=float)
    if PART in ("all", "ftarget"):
        # v1.1: ENG-07d boundary in terms of the rocking mode itself. In loop_flex the engine dynamics depend on K and the
        # inertia only through w_r = sqrt(K / (I_piv + J n^2)) and zeta_r (c = 2 zeta_r sqrt(K Ip)), and the reaction on the
        # vehicle is J_twd x engine acceleration, so the margins are a function of (f_r, zeta_r) per flight condition. This
        # part finds, per damping and filter, the lowest rocking frequency above which every corner has >= 6 dB; Mechanical's
        # stiffness follows from K_total = (2 pi f_r)^2 (I_piv + J n^2) and 1/K_struct = 1/K_total - 1/(K_s n^2).
        FG = [float(x) for x in os.environ.get("GNC_CSI_F_GRID", "14,16,18,20,22,25,28,32,37,43,50").split(",")]
        ZR = [float(x) for x in os.environ.get("GNC_CSI_F_ZETA", "0.02,0.05,0.10").split(",")]
        variants = {
            "lpf50": dict(lpf=50.0, notch=None, mis=(1.0,)),
            "lpf50+notchQ1-12_mis15": dict(lpf=50.0, notch=(1.0, -12.0), mis=(0.85, 1.0, 1.15)),
            "lpf50+notchQ1-12_mis5": dict(lpf=50.0, notch=(1.0, -12.0), mis=(0.95, 1.0, 1.05)),
            "lpf35": dict(lpf=35.0, notch=None, mis=(1.0,)),
            "lpf35+notchQ1-12_mis15": dict(lpf=35.0, notch=(1.0, -12.0), mis=(0.85, 1.0, 1.15)),
        }
        for spec in [x for x in os.environ.get("GNC_CSI_F_EXTRA", "").split(";") if x.strip()]:   # v1.2
            nm, vals = spec.split("=")
            vv = [float(x) for x in vals.split(",")]
            lw, q_, d_, w_ = vv[:4]
            variants[nm.strip()] = dict(lpf=lw, notch=(None if q_ <= 0 else (q_, d_)),
                                        mis=((1.0,) if q_ <= 0 or w_ <= 0 else (1.0 - w_, 1.0, 1.0 + w_)),
                                        wn_scale=(vv[4] if len(vv) > 4 else 1.0))   # optional: landing attitude-loop wn scale
        sel_v = os.environ.get("GNC_CSI_F_VARIANTS")
        if sel_v:
            variants = {k: v for k, v in variants.items() if k in sel_v.split(",")}
        new_v = {k: dict(lpf_w=v["lpf"], notch=v["notch"], mistune=list(v["mis"]), landing_wn_scale=v.get("wn_scale", 1.0))
                 for k, v in variants.items()}
        if os.environ.get("GNC_CSI_F_MERGE") and out.get("ftarget") and out["ftarget"].get("f_grid_Hz") == FG:
            ft = out["ftarget"]                        # v1.2: add to the earlier variants (same grid)
            ft["variants"].update(new_v)
            ft.setdefault("zeta", ZR)
        else:
            ft = dict(f_grid_Hz=FG, zeta=ZR, variants=new_v, cases={}, rigid={})
        for vk, v in variants.items():
            ws_ = v.get("wn_scale", 1.0)          # v1.2: landing attitude-loop bandwidth scale (controller option)
            cv = {k: dict(c, lpf_w=v["lpf"], **({"wn": c["wn"] * ws_, "Ki": 0.1 * (c["wn"] * ws_) ** 3}
                                                if ws_ != 1.0 and k.startswith("landing") else {})) for k, c in conds.items()}
            ft["rigid"][vk] = {kk: vv for kk, vv in rigid_set(cv).items() if kk != "rows"}
            rig_cache = {}
            for zr in ZR:
                rows = []
                for f_r in FG:
                    worst = None
                    agg = dict(all=[0, 0, 0, None, None], floor20=[0, 0, 0, None, None], f62=[0, 0, 0, None, None])
                    for mis in v["mis"]:
                        for cn, cond in cv.items():
                            Kf = (2 * np.pi * f_r) ** 2 * cond["I_piv"]          # J = 0 with the same f_r: same dynamics
                            c = flex_case(cond, Kf, zr, 0.0, n)
                            nt = None if v["notch"] is None else (mis * f_r, v["notch"][0], v["notch"][1])
                            r = evaluate(c, True, nt)
                            for key in ("all", "floor20", "f62"):
                                if key == "floor20" and "floor62N" in cn:
                                    continue
                                if key == "f62" and "floor62N" not in cn:
                                    continue
                                a = agg[key]
                                a[0] += 1; a[1] += 0 if r["stable"] else 1; a[2] += 0 if r["ok6"] else 1
                                if r["stable"] and r["gm_up_dB"] is not None:
                                    a[3] = r["gm_up_dB"] if a[3] is None else min(a[3], r["gm_up_dB"])
                                if r["stable"] and r["pm_min_deg"] is not None:
                                    a[4] = r["pm_min_deg"] if a[4] is None else min(a[4], r["pm_min_deg"])
                            if worst is None or (r["stable"], r["gm_up_dB"] or 99.0) < (worst[1], worst[2] or 99.0):
                                worst = (f"{cn}|mis{mis:g}", r["stable"], r["gm_up_dB"])
                    rows.append(dict(f_r_Hz=f_r, worst=worst, **{k: dict(n=a[0], n_unstable=a[1], n_below_6dB=a[2], gm_up_min_dB=a[3],
                                                                         pm_min_deg=a[4], pass_6dB=a[2] == 0) for k, a in agg.items()}))
                    if v["notch"] is not None:                 # v1.2: rigid loop with the notch at this mode
                        if f_r not in rig_cache:
                            rr = [rigid_set(cv, (mis * f_r, v["notch"][0], v["notch"][1])) for mis in v["mis"]]
                            rig_cache[f_r] = dict(pm_min_deg=min((x["pm_min_deg"] for x in rr if x["pm_min_deg"] is not None), default=None),
                                                  n_unstable=max(x["n_unstable"] for x in rr))
                        rows[-1]["rigid_with_notch"] = rig_cache[f_r]

                def fmin(key):
                    ok = [r[key]["pass_6dB"] for r in rows]
                    return next((FG[i] for i in range(len(FG)) if all(ok[i:])), None)
                res = dict(rows=rows, f_min_Hz={k: fmin(k) for k in ("all", "floor20", "f62")})
                ft["cases"][f"{vk}|z{zr:g}"] = res
                fm_ = res["f_min_Hz"]["floor20"]
                rn_ = next((r.get("rigid_with_notch") for r in rows if r["f_r_Hz"] == fm_), None)
                print(f"ftarget {vk:24s} zeta {zr:4.2f}: f_min floor20 {res['f_min_Hz']['floor20']} all {res['f_min_Hz']['all']} | "
                      f"floor20 {''.join('+' if r['floor20']['pass_6dB'] else '-' for r in rows)} all "
                      f"{''.join('+' if r['all']['pass_6dB'] else '-' for r in rows)} | rigid PM min "
                      f"{ft['rigid'][vk]['pm_min_deg']:.1f}" + (f", with the notch at f_min {rn_['pm_min_deg']:.1f}" if rn_ else "")
                      + f" ({time.time() - t0:.0f}s)", flush=True)
        # stiffness that reaches f_min for each J_int and each end of the servo-stiffness range (lumped rotor)
        Ks_out = relay["K_servo_output_Nm_per_rad"]["v"]
        Ip_l = meta["landing"]["I_piv"]
        conv = {}
        for key, res in ft["cases"].items():
            fm = res["f_min_Hz"]["floor20"]
            if fm is None:
                conv[key] = None
                continue
            conv[key] = {}
            for J in Js:
                Kt = (2 * np.pi * fm) ** 2 * (Ip_l + J * n * n)
                conv[key][f"J{J * 1e3:g}"] = dict(K_total_min=Kt, **{f"K_struct_min_at_K_s_{ks:g}": (None if Kt >= ks * n * n else
                                                                                                  1.0 / (1.0 / Kt - 1.0 / (ks * n * n)))
                                                                    for ks in Ks_out})
        ft["stiffness_for_floor20_f_min"] = conv
        ft["I_piv_landing_kgm2"] = Ip_l
        out["ftarget"] = ft
        with open(path, "w") as f:
            json.dump(out, f, indent=1, default=float)
    out["cpu_s"] = time.time() - t0
    with open(path, "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", path, f"{time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()

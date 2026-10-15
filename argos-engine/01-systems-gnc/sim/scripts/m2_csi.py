"""M2 control-structure interaction (CSI) check for the TVC attitude loop (python-control).

Linear pitch-plane model about a near-vertical thrusting state (DERIVED from the sim6 equations):
  It th''   = -F l_p d - J_twd d'' + r_s F_s + M_a th                 (rigid body + tail-wags-dog + slosh + aero)
  eta''     = -ws^2 eta - 2 zs ws eta' - (F d + F_s)/m_r - r_s th''    (first lateral slosh mode, spring-mass)
  F_s       = m_s (ws^2 eta + 2 zs ws eta')
  q_b''     = -2 zb wb q_b' - wb^2 q_b + phi_g F d / M_b                 (first free-free bending mode, ASSUMED beam)
  gyro      = th' + sigma_imu q_b'                                      (rate gyro at the IMU station)
  d''       = wa^2 (d_c(t - tau) - d) - 2 za wa d'                      (electronics.json actuator, Pade delay)
  d_c       = -(It/(F l_p)) [wn^2 (0 - th_est) - 2 z wn gyro + Ki int(-th_est)]    (sim6 attitude law)
The loop is broken at the actuator command; gain and phase margins, crossover, and the loop gain at the
slosh, bending and engine-rocking frequencies are reported for the landing (floor and max thrust) and
ascent max-q (finless and finned) conditions, with actuator bandwidth and delay at nominal and worst case.
v2.1 (2026-10-12): vehicle RV-1c (mechanical.json v1 engine module, 146 mm body), engine-axis stiffness and
rocking mode from mechanical.json (electronics.json servo stiffness x n^2), floors 12.5 % and 20 %, and the
tail-wags-dog zero w_z = sqrt(F l_p / J_twd) reported per case.
v2.5 variant options (lead n 4.8 study, 2026-10-12): GNC_CSI_N = linkage ratio n (axis stiffness rescaled by
(n / n_mechanical)^2, i.e. servo stiffness x n^2), GNC_CSI_JINT = servo output-referred inertia J [kg m2] added to the
engine DOF as J n^2 (rocking mode sqrt(K / (I_piv + J n^2)); its reaction on the vehicle is J / N_gear and is neglected);
GNC_CSI_TAG names the outputs (default SUFFIX). Inputs (MC summary) still use SUFFIX.
Outputs OUT/csi_<TAG>.json and a Bode plot PNG.
"""
import json
import os
import sys
import numpy as np
import control as ct

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R, sim6 as s6, aero  # noqa: E402
from gncsim import vehicle as _veh  # noqa: E402
R.veh = _veh

OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/m2")
os.makedirs(OUT, exist_ok=True)
SUFFIX = os.environ.get("GNC_SUFFIX", "v2")
TAG = os.environ.get("GNC_CSI_TAG", SUFFIX)
CSI_N = os.environ.get("GNC_CSI_N")
CSI_JINT = float(os.environ.get("GNC_CSI_JINT", "0"))


def beam_mode(L, EI, m_per_L):
    """Uniform free-free beam, first mode: frequency, mode shape (unit generalized mass per total mass)."""
    bl = 4.7300407
    sg = (np.cosh(bl) - np.cos(bl)) / (np.sinh(bl) - np.sin(bl))
    x = np.linspace(0.0, L, 2001)
    b = bl / L
    phi = np.cosh(b * x) + np.cos(b * x) - sg * (np.sinh(b * x) + np.sin(b * x))
    dphi = b * (np.sinh(b * x) - np.sin(b * x) - sg * (np.cosh(b * x) + np.cos(b * x)))
    Mg = m_per_L * np.trapezoid(phi ** 2, x)
    w = bl ** 2 * np.sqrt(EI / (m_per_L * L ** 4))
    return w, x, phi, dphi, Mg


def loop(case):
    It, F, lp, Jt, ms, mr, ws, zs, rs, Ma = (case[k] for k in ["It", "F", "lp", "Jtwd", "m_s", "m_r", "w_s", "z_s",
                                                                "r_s", "M_alpha"])
    wb, zb, phig, sig, Mb = (case[k] for k in ["w_b", "z_b", "phi_g", "sigma_imu", "M_b"])
    wa, za, tau = case["w_a"], case["z_a"], case["tau"]
    wn, z, Ki = case["wn"], case["zeta"], case["Ki"]
    # actuator: d'' = wa^2 (u - d) - 2 za wa d' with u = delayed command
    # states x = [th, th', eta, eta', qb, qb', d, d', int_e]
    # first solve the coupled accelerations (th'' and eta'' depend on each other and on d'')
    # It th'' + rs ms eta'' * 0 ... use the explicit forms:
    #   F_s = ms (ws^2 eta + 2 zs ws eta')
    #   th'' = (-F lp d - Jt d'' + rs F_s + Ma th) / It
    #   eta'' = -ws^2 eta - 2 zs ws eta' - (F d + F_s)/mr - rs th''
    n = 9
    A = np.zeros((n, n))
    B = np.zeros((n, 1))
    # d'' row (index 7): wa^2 (u - d) - 2 za wa d'
    dd_d = -wa ** 2
    dd_dd = -2 * za * wa
    dd_u = wa ** 2
    # th'' = a_th . x + b_th u
    a_th = np.zeros(n)
    a_th[0] += Ma / It
    a_th[2] += rs * ms * ws ** 2 / It
    a_th[3] += rs * ms * 2 * zs * ws / It
    a_th[6] += -F * lp / It - Jt * dd_d / It
    a_th[7] += -Jt * dd_dd / It
    b_th = -Jt * dd_u / It
    # eta''
    a_eta = np.zeros(n)
    a_eta[2] = -ws ** 2 - ms * ws ** 2 / mr
    a_eta[3] = -2 * zs * ws - ms * 2 * zs * ws / mr
    a_eta[6] = -F / mr
    a_eta -= rs * a_th
    b_eta = -rs * b_th
    # bending: qb'' = -2 zb wb qb' - wb^2 qb + phig F d / Mb
    A[0, 1] = 1.0
    A[1, :] = a_th
    B[1, 0] = b_th
    A[2, 3] = 1.0
    A[3, :] = a_eta
    B[3, 0] = b_eta
    A[4, 5] = 1.0
    A[5, 4] = -wb ** 2
    A[5, 5] = -2 * zb * wb
    A[5, 6] = phig * F / Mb
    A[6, 7] = 1.0
    A[7, 6] = dd_d
    A[7, 7] = dd_dd
    B[7, 0] = dd_u
    # integrator of the attitude error (e = -th, th_est = th: estimator ignored at these frequencies)
    A[8, 0] = -1.0
    # controller output (command before the delay): d_c = -(It/(F lp)) [wn^2 (-th) - 2 z wn gyro + Ki int]
    k0 = -It / (F * lp)
    C = np.zeros((1, n))
    C[0, 0] = k0 * (-wn ** 2)
    C[0, 1] = k0 * (-2 * z * wn)
    C[0, 5] = k0 * (-2 * z * wn) * sig
    C[0, 8] = k0 * Ki
    P = ct.ss(A, B, C, np.zeros((1, 1)))
    num, den = ct.pade(tau, 3)
    Dl = ct.tf(num, den)
    Lp = -ct.series(Dl, P)      # loop transfer with negative feedback convention: u = -L e
    return Lp


def loop_flex(case):
    """As loop(), with the engine rocking mode in the actuator path: servo output d_s (2nd order, delayed command)
    drives the engine angle d_e through the axis stiffness K and a damper (zeta_r); thrust, tail-wags-dog,
    slosh and bending use d_e:  I_piv d_e'' = K (d_s - d_e) + c (d_s' - d_e')   (vehicle angular acceleration
    coupling -I_piv th'' neglected: I_piv / It ~ 1 %).  States [th, th', eta, eta', qb, qb', d_s, d_s', int, d_e, d_e']."""
    It, F, lp, Jt, ms, mr, ws, zs, rs, Ma = (case[k] for k in ["It", "F", "lp", "Jtwd", "m_s", "m_r", "w_s", "z_s",
                                                                "r_s", "M_alpha"])
    wb, zb, phig, sig, Mb = (case[k] for k in ["w_b", "z_b", "phi_g", "sigma_imu", "M_b"])
    wa, za, tau = case["w_a"], case["z_a"], case["tau"]
    wn, z, Ki = case["wn"], case["zeta"], case["Ki"]
    K, zr, Ip = case["K_axis"], case["zeta_rock"], case["I_piv"] + case.get("I_add", 0.0)
    c = 2.0 * zr * np.sqrt(K * Ip)
    n = 11
    A = np.zeros((n, n))
    B = np.zeros((n, 1))
    # engine angular acceleration (relative), linear in the states
    a_de = np.zeros(n)
    a_de[6] = K / Ip; a_de[9] = -K / Ip; a_de[7] = c / Ip; a_de[10] = -c / Ip
    a_th = np.zeros(n)
    a_th[0] += Ma / It
    a_th[2] += rs * ms * ws ** 2 / It
    a_th[3] += rs * ms * 2 * zs * ws / It
    a_th[9] += -F * lp / It
    a_th -= Jt * a_de / It
    a_eta = np.zeros(n)
    a_eta[2] = -ws ** 2 - ms * ws ** 2 / mr
    a_eta[3] = -2 * zs * ws - ms * 2 * zs * ws / mr
    a_eta[9] = -F / mr
    a_eta -= rs * a_th
    A[0, 1] = 1.0
    A[1, :] = a_th
    A[2, 3] = 1.0
    A[3, :] = a_eta
    A[4, 5] = 1.0
    A[5, 4] = -wb ** 2
    A[5, 5] = -2 * zb * wb
    A[5, 9] = phig * F / Mb
    A[6, 7] = 1.0
    A[7, 6] = -wa ** 2
    A[7, 7] = -2 * za * wa
    B[7, 0] = wa ** 2
    A[8, 0] = -1.0
    A[9, 10] = 1.0
    A[10, :] = a_de
    k0 = -It / (F * lp)
    C = np.zeros((1, n))
    C[0, 0] = k0 * (-wn ** 2)
    C[0, 1] = k0 * (-2 * z * wn)
    C[0, 5] = k0 * (-2 * z * wn) * sig
    C[0, 8] = k0 * Ki
    P = ct.ss(A, B, C, np.zeros((1, 1)))
    num, den = ct.pade(tau, 3)
    return -ct.series(ct.tf(num, den), P)


def margins_all(L):
    """Upper and lower gain margins (dB) and the phase margin from all crossings."""
    gm_all, pm_all, sm, wpc_all, wgc_all, wms = ct.stability_margins(L, returnall=True)
    gm_all = np.atleast_1d(gm_all); wpc_all = np.atleast_1d(wpc_all)
    pm_all = np.atleast_1d(pm_all); wgc_all = np.atleast_1d(wgc_all)
    up = [20 * np.log10(g) for g in gm_all if np.isfinite(g) and g > 1.0]
    lo = [20 * np.log10(g) for g in gm_all if np.isfinite(g) and 0.0 < g < 1.0]
    pm = [p for p in pm_all if np.isfinite(p)]
    return (float(min(up)) if up else None, float(max(lo)) if lo else None,
            float(min(pm)) if pm else None, float(np.min(np.atleast_1d(sm))))


def cmd_filter(case):
    """Structural low-pass on the gimbal command (sim6 gim_lpf_w, gim_lpf_z); identity when off."""
    wf, zf = case.get("lpf_w", 0.0), case.get("lpf_z", 0.5)
    if wf <= 0.0:
        return ct.tf([1.0], [1.0])
    return ct.tf([wf * wf], [1.0, 2.0 * zf * wf, wf * wf])


def analyse(name, case, w=np.logspace(-1, 3.5, 3000), flex=False):
    L = ct.series(cmd_filter(case), loop_flex(case) if flex else loop(case))
    gm, pm, wcg, wcp = ct.margin(L)
    gm_up, gm_lo, pm_min, smarg = margins_all(L)
    om = w
    resp = ct.frequency_response(L, w)
    mag = np.abs(resp.frdata[0, 0, :])
    cl = ct.feedback(L, 1)
    poles = ct.poles(cl)
    stable = bool(np.all(np.real(poles) < 0))

    def gain_at(wq):
        r = ct.frequency_response(L, [wq])
        return float(20 * np.log10(abs(r.frdata[0, 0, 0]) + 1e-300))
    return dict(case=name, stable=stable, gain_margin_upper_dB=gm_up, gain_margin_lower_dB=gm_lo, phase_margin_min_deg=pm_min,
                stability_margin_min_distance=smarg,
                gain_margin_dB=float(20 * np.log10(gm)) if np.isfinite(gm) and gm > 0 else None,
                phase_margin_deg=float(pm) if np.isfinite(pm) else None, w_gain_cross_radps=float(wcp),
                w_phase_cross_radps=float(wcg), loop_gain_at_slosh_dB=gain_at(case["w_s"]),
                loop_gain_at_bending_dB=gain_at(case["w_b"]), loop_gain_at_rocking_dB=gain_at(case["w_rock"]),
                max_real_cl_pole=float(np.max(np.real(poles))),
                inputs={k: float(v) for k, v in case.items()}), (w, mag)


def main():
    src = R.sources()
    el = src["el"]
    dyn = el["actuators"]["tvc_A"]["dynamics_for_GNC"]["v"]
    mech = src["mech"]
    I_add = 0.0
    if mech is not None:
        stiff = mech["tvc_actuation"]["axis_stiffness_Nm_per_rad"]["v"]
        stiff_src = f"mechanical.json {mech.get('version')} axis_stiffness_Nm_per_rad (servo stiffness x n^2, rigid structure)"
        n_m = mech["tvc_actuation"]["gear_ratio_n"]["v"]
        n_v = float(CSI_N) if CSI_N else n_m
        if CSI_N:
            stiff = [k * (n_v / n_m) ** 2 for k in stiff]
            stiff_src += f" x (n {n_v} / {n_m})^2 (GNC_CSI_N)"
        I_add = CSI_JINT * n_v ** 2
    else:
        stiff = el["actuators"]["tvc_A"]["stiffness"]["v"]["at_engine_Nm_per_rad"]
        stiff_src = "electronics.json v1 stiffness at engine (ASSUMED there)"
    lat = el["loop_rates_and_latency"]["latency_s"]["v"]
    tau_nom = dyn["transport_delay_s"] + lat["fc_cmd_to_ecu_tick_max"] + 0.001
    out = dict(version=f"m2_csi {TAG}", sources=dict(electronics=el.get("version"), combustion=src["comb"].get("version"),
                                                     mechanical=(mech or {}).get("version")),
               variant=dict(n=(float(CSI_N) if CSI_N else None), J_int_servo_kgm2=CSI_JINT, I_add_engine_kgm2=I_add))
    cases = {}
    plots = {}
    # N2O load and MECO speed of the baseline MC case (m2_mc6 output) when available, else the v1 values
    m_full, V_meco = 1.45, 68.5
    p_mc = os.path.join(OUT, f"mc6_summary_{SUFFIX}.json")
    if os.path.exists(p_mc):
        try:
            cb = json.load(open(p_mc))["cases"]["AD_fins_f20"]
            m_full, V_meco = float(cb["m_n2o_mc_kg"]), float(cb["nominal"]["v_meco"])
        except (KeyError, ValueError):
            pass
    out["load_and_meco_speed"] = dict(m_n2o_full_kg=m_full, V_meco_mps=V_meco)
    for prof_m in [("full", m_full), ("landing", 0.30)]:
        label, m_liq = prof_m
        cfg = R.cfg_of(profile="A-D", fins=True, m_n2o=m_full)
        par, apar, comp, mp, tab, info = R.build(cfg)
        # mass properties at this liquid level (vapour neglected)
        o = np.zeros(8)
        rho_l = par[s6.P_rho_l_nom]
        s6.massprops(mp, m_liq, 0.0, rho_l, par[s6.P_m_fuel0] * (1.0 if label == "full" else 0.75), o)
        m, zcg, It, Ir, me, ze, Ie, Dp = o
        zp = mp[15]
        lp = zcg - zp
        le = zp - ze
        Jt = Ie + me * le * (le + lp)
        Ipiv = Ie + me * le * le
        tankA = mp[9]
        tR = np.sqrt(tankA / np.pi)
        h = m_liq / (rho_l * tankA)
        xi = 1.841
        msl = min(0.5 * m_liq, m_liq * (2 * tR / (xi * (xi * xi - 1) * h)) * np.tanh(xi * h / tR))
        zs_ = mp[8] + h - 0.54 * tR
        # bending: uniform PETG tube (ASSUMED E = 2.0 GPa) of 2.03 m with the vehicle mass spread uniformly
        L_b = 2.03
        d_o = info["geo"]["d"]
        d_i = d_o - 2 * info["geo"].get("wall", 0.0025)
        EI = 2.0e9 * np.pi / 64 * (d_o ** 4 - d_i ** 4)
        wb, xb, phi, dphi, Mg = beam_mode(L_b, EI, m / L_b)
        xg = zp + 0.03
        ximu = 1.15 + 0.03
        phig = float(np.interp(xg, xb, phi))
        sig = float(np.interp(ximu, xb, dphi))
        # aerodynamic pitch stiffness at max q (MECO speed from the nominal flight, sea-level density)
        V_mq = V_meco
        Ma_ = {}
        for fins_ in (False, True):
            g2 = dict(info["geo"])
            g2["n_fins"] = 4 if fins_ else 0
            ap, cp = aero.build_aero_params(dict(g2, drogue_CdA=0.0))
            Fq = np.zeros(3); Mq = np.zeros(3)
            da = np.radians(1.0)
            aero.aero_forces(np.array([V_mq * np.sin(da), 0.0, V_mq * np.cos(da)]), np.zeros(3), 1.225, zcg, False, ap, cp, Fq, Mq)
            # body x-velocity +V sin(a) means the nose points toward -x of the airflow: pitch angle th = -a about y
            Ma_[fins_] = float(-Mq[1] / da)
        Ma_nf, Ma_f = Ma_[False], Ma_[True]
        out[f"M_alpha_maxq_{label}"] = dict(V=V_mq, finless=Ma_nf, fins=Ma_f,
                                           note="dM_y/dth [N m/rad] at max q from aero.py; > 0 destabilising")
        for thrust_label, F in [("floor62N", 62.5), ("floor100N", 100.0), ("hover", m * R.G0), ("max500N", 500.0)]:
            if label == "full" and thrust_label != "max500N":
                continue
            fax = F / m
            ws = np.sqrt((xi * fax / tR) * np.tanh(xi * h / tR))
            for act_label, wa, tau in [("nom", dyn["omega_n_rad_s"], tau_nom),
                                       ("worst", dyn["omega_n_range_rad_s"][0], tau_nom + 0.0032),
                                       ("fast", dyn["omega_n_range_rad_s"][1], tau_nom)]:
                for aero_label, Ma in [("noaero", 0.0)] + ([("maxq_finless", Ma_nf), ("maxq_fins", Ma_f)]
                                                         if label == "full" else []):
                  for flt_label, lpf_w in [("nofilt", 0.0), ("lpf", R.DEF["gim_lpf_w"])]:
                    wn = R.DEF["att_wn_asc"] if label == "full" else R.DEF["att_wn"]
                    case = dict(It=It, F=F, lp=lp, Jtwd=Jt, m_s=msl, m_r=m - msl, w_s=ws, z_s=0.005, r_s=zs_ - zcg,
                                M_alpha=Ma, w_b=wb, z_b=0.02, phi_g=phig, sigma_imu=sig, M_b=Mg, w_a=wa, z_a=dyn["zeta"],
                                tau=tau, wn=wn, zeta=0.7, Ki=0.1 * wn ** 3, w_rock=np.sqrt(stiff[0] / Ipiv),
                                I_piv=Ipiv, m=m, zcg=zcg, w_twd_zero=np.sqrt(F * lp / Jt), lpf_w=lpf_w,
                                lpf_z=R.DEF["gim_lpf_z"])
                    name = f"{label}|{thrust_label}|act_{act_label}|{aero_label}|{flt_label}"
                    r, pl = analyse(name, case)
                    cases[name] = r
                    plots[name] = pl
                    # flexible engine mount (rocking mode in the loop), stiffness range x damping
                    for K_ in stiff:
                        for zr_ in (0.02, 0.05):
                            c2 = dict(case, K_axis=K_, zeta_rock=zr_, I_add=I_add)
                            nm2 = f"{name}|rock_K{K_:.0f}_z{zr_:.2f}"
                            r2, pl2 = analyse(nm2, c2, flex=True)
                            cases[nm2] = r2
                            plots[nm2] = pl2
        out[f"bending_{label}"] = dict(f_b_Hz=wb / (2 * np.pi), EI_Nm2=EI, phi_gimbal=phig, slope_imu_per_m=sig,
                                       M_gen_kg=Mg, note="ASSUMED uniform PETG tube E 2.0 GPa, uniform mass; "
                                       "Lauty's airframe FEA replaces this")
        out[f"rocking_{label}"] = dict(I_piv=Ipiv, I_add_servo_reflected=I_add,
                                       f_rock_Hz=[float(np.sqrt(k / (Ipiv + I_add)) / (2 * np.pi)) for k in stiff],
                                       stiffness_Nm_per_rad=stiff, source=stiff_src)
        out[f"twd_{label}"] = dict(l_p_m=lp, l_e_m=le, J_twd_kgm2=Jt, I_e_own_kgm2=Ie, m_e_kg=me,
                                   w_zero_radps={f"{F_:.1f}N": float(np.sqrt(F_ * lp / Jt)) for F_ in (62.5, 100.0, 125.0, 500.0)},
                                   note="tail-wags-dog zero of th/d: sqrt(F l_p / J_twd), J_twd = I_e + m_e l_e (l_e + l_p)")
    out["cases"] = cases
    summ = {}
    for flt in ("nofilt", "lpf"):
        sel = {k: v for k, v in cases.items() if f"|{flt}" in k}
        rig = {k: v for k, v in sel.items() if "|rock_" not in k}
        flx = {k: v for k, v in sel.items() if "|rock_" in k}
        summ[flt] = dict(n_cases=len(sel), n_unstable=sum(1 for v in sel.values() if not v["stable"]),
                         rigid_unstable=[k for k, v in rig.items() if not v["stable"]],
                         flex_unstable=[k for k, v in flx.items() if not v["stable"]],
                         rigid_pm_min_deg=min((v["phase_margin_min_deg"] for v in rig.values()
                                               if v["stable"] and v["phase_margin_min_deg"] is not None), default=None),
                         rigid_gm_up_min_dB=min((v["gain_margin_upper_dB"] for v in rig.values()
                                                 if v["stable"] and v["gain_margin_upper_dB"] is not None), default=None),
                         flex_gm_up_min_dB=min((v["gain_margin_upper_dB"] for v in flx.values()
                                                if v["stable"] and v["gain_margin_upper_dB"] is not None), default=None))
    out["summary"] = summ
    out["filter"] = dict(kind="2nd-order low-pass on the gimbal command", w_rad_s=R.DEF["gim_lpf_w"], zeta=R.DEF["gim_lpf_z"],
                         attitude_wn_ascent=R.DEF["att_wn_asc"], attitude_wn_landing=R.DEF["att_wn"])
    with open(os.path.join(OUT, f"csi_{TAG}.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for name in ["landing|floor62N|act_fast|noaero|nofilt", "landing|floor62N|act_fast|noaero|lpf",
                 "landing|hover|act_nom|noaero|nofilt|rock_K2088_z0.02", "landing|hover|act_nom|noaero|lpf|rock_K2088_z0.02",
                 "full|max500N|act_worst|maxq_fins|lpf", "full|max500N|act_nom|maxq_finless|lpf"]:
        if name in plots:
            w, mag = plots[name]
            ax.semilogx(w / (2 * np.pi), 20 * np.log10(mag), label=name)
    ax.axhline(0, color="k", lw=0.5)
    ax.set_xlabel("frequency [Hz]")
    ax.set_ylabel("|L(jw)| [dB]")
    ax.set_title("TVC attitude loop gain, RV-1c (sim6 law, actuator, slosh, bending, delay)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, f"csi_loop_gain_{TAG}.png"), dpi=130)
    for k, r in cases.items():
        f_ = lambda v: "None" if v is None else f"{v:.1f}"
        print(f"{k:62s} stable={r['stable']} GMup={f_(r['gain_margin_upper_dB'])} GMlo={f_(r['gain_margin_lower_dB'])} "
              f"PM={f_(r['phase_margin_min_deg'])} wc={r['w_gain_cross_radps']:.1f} "
              f"slosh={r['loop_gain_at_slosh_dB']:.1f}dB bend={r['loop_gain_at_bending_dB']:.1f}dB rock={r['loop_gain_at_rocking_dB']:.1f}dB")
    print({k: out[k] for k in out if k.startswith("bending") or k.startswith("rocking") or k.startswith("twd")})
    print(json.dumps(summ, indent=1, default=float))


if __name__ == "__main__":
    main()

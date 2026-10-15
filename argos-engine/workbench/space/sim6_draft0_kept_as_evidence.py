"""6-DOF flight simulator (numba) for the 500 N throttleable N2O/ABS hybrid VTVL vehicle.

Frames: world W = ENU, flat earth, origin at the pad, z up. Body B: z_b along the vehicle axis toward
the nose; stations z [m] from the airframe aft datum (see vehicle.py). Quaternion q (scalar first)
rotates body -> world.

Truth model
 * rigid body with variable mass, CG and inertia (vehicle.massprops: N2O liquid settled aft, grain
   regression), Euler rotational equations, jet damping, lateral CG offset;
 * thrust along the gimballed nozzle axis through the pivot (on axis), thrust misalignment angles;
   tail-wags-dog reaction torque  -J_twd * delta_ddot,  J_twd = I_e + m_e l_e (l_e + l_p);
   engine roll torque (helical-port swirl, ASSUMED magnitude) proportional to thrust;
 * engine: command -> floor/ceiling clamp -> deadband -> quantisation -> slew -> first-order
   (closed-loop Pc response); ignition delay, tail-off; mass flow from the throttle map
   (O/F shift, Isp vs throttle; combustion.json v1 or the GNC placeholder), Isp dispersion;
   equilibrium self-pressurised N2O tank every 10 ms; thrust ceiling vs tank pressure;
 * gimbal actuators (2 axes): command transport delay (ring buffer), 2nd-order servo (wn, zeta),
   rate limit from a linear torque-speed line loaded by the hinge moment, deadband, backlash
   (dead zone between servo output and engine), mechanical angle limit;
 * aerodynamics: all-attitude component build-up (aero.py) at the local air velocity incl. omega x r,
   steady wind with power-law shear + Dryden turbulence (first-order forms, MIL-F-8785C low-altitude
   scales), ISA density; nose drogue (quasi-steady tension at the nose tip), legs, optional fins;
 * propellant slosh: first lateral mode as a spring-mass (Abramson, NASA SP-106 tall-tank formulas),
   active only while the liquid is settled (axial specific force > 0.5 m/s2);
 * landing legs: 4 spring-damper feet with stroke limit (hard stop) and regularised Coulomb friction.

Flight-software model
 * sensors: IMU (gyro/accel bias, scale factor, noise density, vibration noise while burning), GNSS
   (pos/vel at gnss_rate), LiDAR altimeter (< lidar_range), barometer (bias); pad alignment error;
 * estimator: gyro-propagated attitude (no in-flight aiding) + three decoupled 3-state Kalman
   filters [position, velocity, accel bias] per world axis at 100 Hz;
 * guidance: ascent lateral-velocity hold (+ optional upwind bias) and MECO on predicted apogee;
   coast; drogue at apogee; relight on the predicted stopping distance planned on the latest
   ignition; landing burn: vertical velocity-tracking reference with PI, accelerometer
   thrust-effectiveness estimator and hoverslam mode (as sim1d v1.2); lateral divert
   lat_mode 0 = PD to the pad, 1 = ZEM/ZEV polynomial, 2 = tracking of a caller-supplied reference
   (LP 'convex-lite' profile); terminal: lateral-velocity nulling and attitude to vertical;
 * control: attitude PD(+I) on the thrust-direction error, gain-scheduled on estimated thrust and
   moment arm -> gimbal angles, circular gimbal limit, anti-windup; throttle = vertical channel /
   cos(tilt) with floor/ceiling saturation; optional roll RCS (bang-bang with deadband).
All parameters are passed in par[] (names in PAR_NAMES) by run6.py, which reads the interface
JSON and tags every value.
"""
import numpy as np
from numba import njit
from .propulsion import tank_solve, tank_init, _bilin
from .aero import (aero_forces, A_LEGS_DEPLOYED, A_DROGUE_DEPLOYED, A_SREF, A_CA0_NF, A_CA0_TF,
                   A_CA_LEGS, A_K_RETRO)
from .vehicle import massprops

G0 = 9.80665

PAR_NAMES = """
profile h_target Fmax floor tau slew deadb quant t_ign t_ign_est t_rise t_off thrust_scale isp_scale
tank_V m_n2o T0 c_wall resid rho_l_nom m_fuel0
z_tip z_foot r_foot z_imu legs_mode legs_k legs_c legs_stroke legs_mu
kd ht vt kv hslam hcut hover_k hs_margin k_est k_est_tau
gim_max gim_wn gim_zeta gim_rate_nl gim_stall_engine gim_delay gim_deadband gim_backlash hose_K gim_fric
att_wn att_zeta att_ki att_wn_asc tilt_max_land tilt_max_asc lat_mode lat_wn lat_zeta target_x target_y
mis_x mis_y cg_x cg_y roll_torque rcs_on rcs_torque rcs_deadband
wind_u wind_dir wind_alpha gust_on gust_scale rho0
drogue_CdA descent_mode fins_on ascent_bias_x ascent_bias_y
slosh_on slosh_zeta
g_bx g_by g_bz a_bx a_by a_bz g_sf a_sf g_arw a_vrw vib_sigma align_x align_y
gnss_sp_h gnss_sp_v gnss_sv gnss_rate lidar_on lidar_sigma lidar_frac lidar_range baro_sigma baro_bias
mest dt tmax seed rec_dt hold_tw coast_floor t_post h_bias_nav
""".split()
for _i, _n in enumerate(PAR_NAMES):
    globals()["P_" + _n] = _i
NP = len(PAR_NAMES)

RES_NAMES = """
landed td_vz td_vh td_tilt td_rate td_miss td_t prop_used liq_left exhausted h_max apo_x apo_y
v_ign h_ign max_gim max_gim_rate max_hinge max_rate_coast max_rate_desc max_rate_land max_tilt_land
max_aoa_asc tumble_coast starts burn_time tipover peak_leg_force td_roll_rate max_axial_g max_lat_g_eng
hslam_used cut m_land nrec t_end max_tilt_desc relight_ok att_err_td nav_h_err_td nav_v_err_td
lat_err_td max_q coast_aoa_max fuel_left gim_sat_frac td_x td_y max_roll_rate
""".split()
for _i, _n in enumerate(RES_NAMES):
    globals()["R_" + _n] = _i
NR = len(RES_NAMES)

REC_NAMES = """
t x y z vx vy vz q0 q1 q2 q3 wx wy wz F Fcmd dgx dgy dcx dcy m zcg phase tilt aoa xe ye ze vxe vye vze
Ptank mliq hinge keff windx windy
""".split()
NREC = len(REC_NAMES)


@njit(cache=True)
def _rho(h, rho0):
    hh = h if h > 0.0 else 0.0
    return rho0 * (1.0 - 2.2558e-5 * hh) ** 4.2559


@njit(cache=True)
def qmul(a, b, out):
    out[0] = a[0] * b[0] - a[1] * b[1] - a[2] * b[2] - a[3] * b[3]
    out[1] = a[0] * b[1] + a[1] * b[0] + a[2] * b[3] - a[3] * b[2]
    out[2] = a[0] * b[2] - a[1] * b[3] + a[2] * b[0] + a[3] * b[1]
    out[3] = a[0] * b[3] + a[1] * b[2] - a[2] * b[1] + a[3] * b[0]


@njit(cache=True)
def qrot(q, v, out):
    """out = R(q) v  (body -> world)."""
    w, x, y, z = q[0], q[1], q[2], q[3]
    a, b, c = v[0], v[1], v[2]
    out[0] = (1 - 2 * (y * y + z * z)) * a + 2 * (x * y - w * z) * b + 2 * (x * z + w * y) * c
    out[1] = 2 * (x * y + w * z) * a + (1 - 2 * (x * x + z * z)) * b + 2 * (y * z - w * x) * c
    out[2] = 2 * (x * z - w * y) * a + 2 * (y * z + w * x) * b + (1 - 2 * (x * x + y * y)) * c


@njit(cache=True)
def qrotT(q, v, out):
    """out = R(q)^T v  (world -> body)."""
    w, x, y, z = q[0], q[1], q[2], q[3]
    a, b, c = v[0], v[1], v[2]
    out[0] = (1 - 2 * (y * y + z * z)) * a + 2 * (x * y + w * z) * b + 2 * (x * z - w * y) * c
    out[1] = 2 * (x * y - w * z) * a + (1 - 2 * (x * x + z * z)) * b + 2 * (y * z + w * x) * c
    out[2] = 2 * (x * z + w * y) * a + 2 * (y * z - w * x) * b + (1 - 2 * (x * x + y * y)) * c


@njit(cache=True)
def qnorm(q):
    n = np.sqrt(q[0] ** 2 + q[1] ** 2 + q[2] ** 2 + q[3] ** 2)
    for i in range(4):
        q[i] /= n


@njit(cache=True)
def qint(q, w, dt):
    """q <- q (x) exp(0.5 w dt), w in body axes."""
    wn = np.sqrt(w[0] ** 2 + w[1] ** 2 + w[2] ** 2)
    a = wn * dt
    if a < 1e-14:
        return
    s = np.sin(0.5 * a) / wn
    dq = np.empty(4)
    dq[0] = np.cos(0.5 * a); dq[1] = w[0] * s; dq[2] = w[1] * s; dq[3] = w[2] * s
    tmp = np.empty(4)
    qmul(q, dq, tmp)
    for i in range(4):
        q[i] = tmp[i]
    qnorm(q)


@njit(cache=True)
def kf3_predict(x, P, a, dt, qa, qb):
    """Per-axis KF, state [pos, vel, accel bias]; accel input a (bias subtracted)."""
    acc = a - x[2]
    x[0] += x[1] * dt + 0.5 * acc * dt * dt
    x[1] += acc * dt
    F = np.array([[1.0, dt, -0.5 * dt * dt], [0.0, 1.0, -dt], [0.0, 0.0, 1.0]])
    Pn = F @ P @ F.T
    Pn[0, 0] += 0.25 * dt ** 4 * qa / dt
    Pn[0, 1] += 0.5 * dt ** 3 * qa / dt
    Pn[1, 0] += 0.5 * dt ** 3 * qa / dt
    Pn[1, 1] += dt * qa
    Pn[2, 2] += qb * dt
    for i in range(3):
        for j in range(3):
            P[i, j] = Pn[i, j]


@njit(cache=True)
def kf3_update(x, P, idx, z, R):
    y = z - x[idx]
    S_ = P[idx, idx] + R
    K = np.empty(3)
    for i in range(3):
        K[i] = P[i, idx] / S_
    for i in range(3):
        x[i] += K[i] * y
    Pn = np.empty((3, 3))
    for i in range(3):
        for j in range(3):
            Pn[i, j] = P[i, j] - K[i] * P[idx, j]
    for i in range(3):
        for j in range(3):
            P[i, j] = 0.5 * (Pn[i, j] + Pn[j, i])


@njit(cache=True)
def run6(par, apar, comp, mp, Fg, Dg, tmox, tmf, Pg, ceil, ref, out_rec):
    """Integrate one 6-DOF flight; ref (N, 7) = [t_rel, x, y, z, vx, vy, vz] for lat_mode 2.
    Returns res[NR]; fills out_rec[k, :NREC] every rec_dt."""
    np.random.seed(int(par[P_seed]))
    dt = par[P_dt]
    g = G0
    prof = int(par[P_profile])
    Fmax = par[P_Fmax]
    floorF = par[P_floor] * Fmax
    tsc = par[P_thrust_scale]
    isc = par[P_isp_scale]
    S = apar[A_SREF]
    res = np.zeros(NR)
    # ---------------- tank, fuel, mass properties
    V = par[P_tank_V]
    Cw = par[P_c_wall]
    mt = par[P_m_n2o]
    E = tank_init(mt, par[P_T0], V, Cw)
    T, Pt, ml, mv, hl = tank_solve(mt, E, V, Cw)
    resid = par[P_resid] * mt
    mfuel = par[P_m_fuel0]
    mo = np.zeros(8)
    rho_l = par[P_rho_l_nom]
    massprops(mp, ml, mv, rho_l, mfuel, mo)
    m_tot, zcg, It, Ir, m_e, z_e, I_e, Dp = mo[0], mo[1], mo[2], mo[3], mo[4], mo[5], mo[6], mo[7]
    z_p = mp[15]
    tank_zb = mp[8]
    tank_A = mp[9]
    tank_R = np.sqrt(tank_A / np.pi)
    # ---------------- states
    r = np.zeros(3); v = np.zeros(3); w = np.zeros(3)
    q = np.array([1.0, 0.0, 0.0, 0.0])
    on_legs = par[P_legs_mode] > 0.5            # 1: legs fixed/deployed at t0 (B, hops)
    legs_dep = on_legs
    apar[A_LEGS_DEPLOYED] = 1.0 if legs_dep else 0.0
    apar[A_DROGUE_DEPLOYED] = 0.0
    # initial CG height: feet on the ground (legs) or on a launch stand at the same height
    r[2] = zcg - par[P_z_foot] + (0.0 if on_legs else 0.0)
    if on_legs:
        r[2] -= 9.0 * m_tot / (4.0 * par[P_legs_k]) * 0.0
    held = True                                 # hold-down until T/W > hold_tw
    # slosh
    xs = np.zeros(2); vs = np.zeros(2)
    # gimbal actuators: servo angle/rate, engine angle (after backlash), command delay buffer
    dsv = np.zeros(2); dsr = np.zeros(2); deng = np.zeros(2); deng_prev = np.zeros(2); dd_prev = np.zeros(2)
    nbuf = 64
    cbuf = np.zeros((nbuf, 2))
    kdel = int(par[P_gim_delay] / dt + 0.5)
    if kdel > nbuf - 1:
        kdel = nbuf - 1
    ibuf = 0
    dcmd = np.zeros(2)
    gmax = np.radians(par[P_gim_max])
    # wind (steady + Dryden)
    wdir = par[P_wind_dir]
    gu = np.zeros(3)
    # IMU errors
    bg = np.array([par[P_g_bx], par[P_g_by], par[P_g_bz]])
    ba = np.array([par[P_a_bx], par[P_a_by], par[P_a_bz]])
    # estimator
    qe = np.array([1.0, 0.5 * par[P_align_x], 0.5 * par[P_align_y], 0.0])
    qnorm(qe)
    kx = np.zeros((3, 3)); Px = np.zeros((3, 3, 3))
    for a in range(3):
        kx[a, 0] = r[a] + (np.random.normal() * 0.5 if a < 2 else 0.0)
        Px[a, 0, 0] = 1.0; Px[a, 1, 1] = 0.01; Px[a, 2, 2] = 0.04
    kx[2, 0] = r[2]
    kf_timer = 0.0; gnss_timer = 0.0; lidar_timer = 0.0; baro_timer = 0.0
    acc_meas_sum = np.zeros(3); n_acc = 0
    # engine / sequencing
    F = 0.0; Fcmd = 0.0; Fc_prev = 0.0
    lit = False; burning = False
    phase = 0
    t = 0.0
    t_ign_cmd = -1.0
    hmax = 0.0; prop_used = 0.0
    landed = False
    starts = 0
    burn_time = 0.0
    hs_mode = int(par[P_hslam]); hslam = hs_mode == 1; mode_locked = False; cut = False
    k_hat = 1.0
    ei = 0.0; sat_lo = False; sat_hi = False
    eix = 0.0; eiy = 0.0
    acc_prev = 0.0
    exhausted = False
    td_done = False
    t_td = -1.0
    drogue = False
    nrec = 0; next_rec = 0.0
    tank_timer = 0.0
    Fceil = Fmax
    # metrics
    max_gim = 0.0; max_gim_rate = 0.0; max_hinge = 0.0; max_rate_coast = 0.0; max_rate_desc = 0.0
    max_rate_land = 0.0; max_tilt_land = 0.0; max_aoa_asc = 0.0; max_axial = 0.0; max_lat_eng = 0.0
    max_tilt_desc = 0.0; max_q = 0.0; coast_aoa = 0.0; peak_leg = 0.0; sat_steps = 0; burn_steps = 0
    max_roll = 0.0
    v_ign = 0.0; h_ign = 0.0
    apo_x = 0.0; apo_y = 0.0
    relight_ok = 0.0
    tip = False
    hinge_now = 0.0
    keff = 1.0
    # working arrays
    tb = np.zeros(3); Fb = np.zeros(3); Mb = np.zeros(3); Fw = np.zeros(3); tmp3 = np.zeros(3)
    vrel_w = np.zeros(3); vrel_b = np.zeros(3); Fa = np.zeros(3); Ma = np.zeros(3)
    zb_w = np.zeros(3); fb = np.zeros(3); fimu = np.zeros(3); wm = np.zeros(3); fm = np.zeros(3)
    fw_est = np.zeros(3); n_d = np.zeros(3); n_b = np.zeros(3); zbe = np.zeros(3)
    a_lat = np.zeros(2)
    alpha_prev = np.zeros(3)
    w_prev = np.zeros(3)
    tilt = 0.0
    aoa = 0.0
    tgo = 5.0
    h_est = r[2] - (zcg - par[P_z_foot])
    while t < par[P_tmax]:
        # ================================================================ mass properties (10 ms)
        massprops(mp, ml, mv, rho_l, mfuel, mo)
        m_tot, zcg, It, Ir, m_e, z_e, I_e, Dp = mo[0], mo[1], mo[2], mo[3], mo[4], mo[5], mo[6], mo[7]
        l_p = zcg - z_p
        l_e = z_p - z_e
        J_twd = I_e + m_e * l_e * (l_e + l_p)
        I_piv = I_e + m_e * l_e * l_e
        # engine ceiling
        Fceil = tsc * _bilin(Pg, Dg, ceil, Pt, Dp)
        if Fceil > Fmax * tsc:
            Fceil = Fmax * tsc
        if ml <= resid:
            Fceil = 0.0
            if burning:
                exhausted = True
        Fc_avail = Fceil / tsc
        # ================================================================ environment
        qrot(q, np.array([0.0, 0.0, 1.0]), zb_w)
        tilt = np.arccos(min(1.0, max(-1.0, zb_w[2])))
        h_cg = r[2]
        h_ft = max(h_cg, 1.0) / 0.3048
        rho = _rho(h_cg, par[P_rho0])
        Uh = par[P_wind_u] * (max(h_cg, 0.5) / 10.0) ** par[P_wind_alpha]
        wx = Uh * np.cos(wdir); wy = Uh * np.sin(wdir)
        if par[P_gust_on] > 0.5:
            W20 = par[P_wind_u] * (6.1 / 10.0) ** par[P_wind_alpha]
            sw = 0.1 * W20 * par[P_gust_scale]
            den = (0.177 + 0.000823 * h_ft)
            su = sw / den ** 0.4
            Lw = max(h_ft, 10.0) * 0.3048
            Lu = (max(h_ft, 10.0) / den ** 1.2) * 0.3048
            Vt = np.sqrt((v[0] - wx) ** 2 + (v[1] - wy) ** 2 + v[2] ** 2)
            if Vt < par[P_wind_u]:
                Vt = par[P_wind_u]
            if Vt < 1.0:
                Vt = 1.0
            au = Vt * dt / Lu; aw = Vt * dt / Lw
            if au > 1.0:
                au = 1.0
            if aw > 1.0:
                aw = 1.0
            gu[0] = gu[0] * (1.0 - au) + su * np.sqrt(2.0 * au) * np.random.normal()
            gu[1] = gu[1] * (1.0 - au) + su * np.sqrt(2.0 * au) * np.random.normal()
            gu[2] = gu[2] * (1.0 - aw) + sw * np.sqrt(2.0 * aw) * np.random.normal()
        # gust components: u along the mean wind, v across, w vertical
        cwd = np.cos(wdir); swd = np.sin(wdir)
        wwx = wx + gu[0] * cwd - gu[1] * swd
        wwy = wy + gu[0] * swd + gu[1] * cwd
        wwz = gu[2] if h_cg > 1.0 else gu[2] * max(h_cg, 0.0)
        vrel_w[0] = v[0] - wwx; vrel_w[1] = v[1] - wwy; vrel_w[2] = v[2] - wwz
        qrotT(q, vrel_w, vrel_b)
        Vair = np.sqrt(vrel_b[0] ** 2 + vrel_b[1] ** 2 + vrel_b[2] ** 2)
        aoa = np.arccos(min(1.0, max(-1.0, vrel_b[2] / Vair))) if Vair > 0.5 else 0.0
        qdyn = 0.5 * rho * Vair * Vair
        if qdyn > max_q:
            max_q = qdyn
        # ================================================================ sensors (truth specific force from last step)
        # gyro
        for i in range(3):
            wm[i] = w[i] * (1.0 + par[P_g_sf]) + bg[i] + par[P_g_arw] / np.sqrt(dt) * np.random.normal()
        qint(qe, wm, dt)
        # accelerometer at the IMU station (specific force from the previous step's forces)
        vib = par[P_vib_sigma] * (F / Fmax) if F > 1.0 else 0.0
        rz_imu = par[P_z_imu] - zcg
        fimu[0] = fb[0] + alpha_prev[1] * rz_imu + w[0] * w[2] * rz_imu
        fimu[1] = fb[1] - alpha_prev[0] * rz_imu + w[1] * w[2] * rz_imu
        fimu[2] = fb[2] - (w[0] * w[0] + w[1] * w[1]) * rz_imu
        for i in range(3):
            fm[i] = fimu[i] * (1.0 + par[P_a_sf]) + ba[i] + (par[P_a_vrw] / np.sqrt(dt) + vib) * np.random.normal()
            acc_meas_sum[i] += fm[i]
        n_acc += 1
        # KF at 100 Hz with the averaged accelerometer
        kf_timer += dt
        gnss_timer += dt; lidar_timer += dt; baro_timer += dt
        if kf_timer >= 0.01 - 1e-12:
            for i in range(3):
                tmp3[i] = acc_meas_sum[i] / n_acc
                acc_meas_sum[i] = 0.0
            n_acc = 0
            qrot(qe, tmp3, fw_est)
            fw_est[2] -= g
            for a in range(3):
                kf3_predict(kx[a], Px[a], fw_est[a], kf_timer, (par[P_a_vrw] ** 2 + 0.05 ** 2) * 4.0, 1e-4)
            kf_timer = 0.0
            if gnss_timer >= 1.0 / par[P_gnss_rate] - 1e-12:
                gnss_timer = 0.0
                for a in range(3):
                    sp = par[P_gnss_sp_h] if a < 2 else par[P_gnss_sp_v]
                    kf3_update(kx[a], Px[a], 0, r[a] + sp * np.random.normal(), sp * sp)
                    kf3_update(kx[a], Px[a], 1, v[a] + par[P_gnss_sv] * np.random.normal(),
                               par[P_gnss_sv] ** 2)
            if par[P_lidar_on] > 0.5 and lidar_timer >= 0.02 - 1e-12:
                lidar_timer = 0.0
                hfoot = r[2] - (zcg - par[P_z_foot]) * np.cos(tilt)
                if hfoot < par[P_lidar_range] and tilt < 0.5:
                    sl = par[P_lidar_sigma] + par[P_lidar_frac] * max(hfoot, 0.0)
                    kf3_update(kx[2], Px[2], 0, r[2] + sl * np.random.normal(), sl * sl)
            if baro_timer >= 0.04 - 1e-12:
                baro_timer = 0.0
                kf3_update(kx[2], Px[2], 0, r[2] + par[P_baro_bias] + par[P_baro_sigma] * np.random.normal(),
                           par[P_baro_sigma] ** 2 + par[P_baro_bias] ** 2)
        # ================================================================ guidance & control (estimated state)
        m_est = m_tot * (1.0 + par[P_mest])
        qrot(qe, np.array([0.0, 0.0, 1.0]), zbe)
        tilt_e = np.arccos(min(1.0, max(-1.0, zbe[2])))
        h_est = kx[2, 0] - (zcg - par[P_z_foot]) * np.cos(tilt_e) + par[P_h_bias_nav]
        vz_e = kx[2, 1]
        # default: thrust direction vertical, no lateral acceleration
        a_lat[0] = 0.0; a_lat[1] = 0.0
        tilt_lim = np.radians(par[P_tilt_max_land])
        att_active = True
        if phase == 0:
            Fcmd = Fmax
            lit = True; burning = True
            if starts == 0:
                starts = 1
            phase = 1
        elif phase == 1:
            Fcmd = Fmax
            # lateral velocity hold (+ optional upwind bias velocity)
            kvl = 0.6
            a_lat[0] = kvl * (par[P_ascent_bias_x] - kx[0, 1])
            a_lat[1] = kvl * (par[P_ascent_bias_y] - kx[1, 1])
            tilt_lim = np.radians(par[P_tilt_max_asc])
            if vz_e > 0.5:
                if prof == 0:
                    k = 0.5 * rho * S * apar[A_CA0_NF] / m_est
                    hap = h_est + np.log(1.0 + k * vz_e * vz_e / g) / (2.0 * k) + vz_e * par[P_t_off]
                    if hap >= par[P_h_target]:
                        phase = 2
                        lit = False
                else:
                    Fsw = floorF + par[P_slew] * Fmax * par[P_tau]
                    if Fsw > F:
                        Fsw = F
                    t_ramp = (F - Fsw) / (par[P_slew] * Fmax)
                    dv1 = (0.5 * (F + Fsw) / m_est - g) * t_ramp
                    dv2 = ((Fsw - floorF) / m_est) * par[P_tau] + (floorF / m_est - g) * par[P_tau]
                    lagd = t_ramp + par[P_tau]
                    vq = vz_e + dv1 + dv2
                    hq = h_est + 0.5 * (vz_e + vq) * lagd
                    mdf = floorF / (140.0 * G0)
                    mm = m_est
                    geff = g - floorF / mm
                    for _it in range(3):
                        geff = g - floorF / mm
                        if geff < 0.2:
                            geff = 0.2
                        tco = vq / geff
                        mm = m_est - 0.5 * mdf * tco
                    k = 0.5 * rho * S * apar[A_CA0_NF] / mm
                    hap = hq + np.log(1.0 + k * vq * vq / geff) / (2.0 * k)
                    if hap >= par[P_h_target]:
                        phase = 2
        if phase == 2 or phase == 3:
            if prof == 1:
                Fcmd = floorF
                if phase == 2 and vz_e > 0.0:
                    geff = g - floorF / m_est
                    if geff < 0.2:
                        geff = 0.2
                    hap_now = h_est + vz_e * vz_e / (2.0 * geff)
                    if hap_now < par[P_h_target] - 0.5:
                        Fcmd = floorF + m_est * 0.08 * (par[P_h_target] - hap_now)
                # lateral: null horizontal velocity and drift back toward the pad slowly
                a_lat[0] = 0.3 * (par[P_target_x] - kx[0, 0]) * 0.2 - 0.6 * kx[0, 1]
                a_lat[1] = 0.3 * (par[P_target_y] - kx[1, 0]) * 0.2 - 0.6 * kx[1, 1]
            else:
                Fcmd = 0.0
                att_active = False
            if vz_e < 0.0 and phase == 2:
                phase = 3
                apo_x = r[0]; apo_y = r[1]
                if par[P_descent_mode] > 0.5 and prof == 0:
                    drogue = True
                    apar[A_DROGUE_DEPLOYED] = 1.0
            if phase == 3:
                if hs_mode < 0 and not mode_locked:
                    hslam = floorF > par[P_hover_k] * m_est * g
                ad = par[P_kd] * (Fc_avail / m_est - g)
                if hslam:
                    amin = floorF / m_est - g
                    ad = amin + 0.5 * ((Fc_avail / m_est - g) - amin)
                    if ad < amin + 0.5:
                        ad = amin + 0.5
                lag = par[P_t_ign_est] + par[P_t_rise] if prof == 0 else par[P_tau] * 2.0
                amin_ = floorF / m_est - g
                a_term_ = (amin_ + par[P_hs_margin] if amin_ + par[P_hs_margin] > 1.0 else 1.0) if hslam else 1.5
                vt = np.sqrt(par[P_vt] ** 2 + 2.0 * a_term_ * par[P_ht])
                vi = vz_e + acc_prev * lag
                hi = h_est + vz_e * lag + 0.5 * acc_prev * lag * lag
                htrig = (vi * vi - vt * vt) / (2.0 * ad) + par[P_ht]
                if hi <= htrig and vi < 0.0:
                    mode_locked = True
                    if prof == 0:
                        phase = 4
                        t_ign_cmd = t
                        v_ign = v[2]
                        h_ign = h_est
                        legs_dep = True
                        apar[A_LEGS_DEPLOYED] = 1.0
                    else:
                        phase = 5
        if phase == 4:
            Fcmd = floorF
            att_active = False
            if t - t_ign_cmd >= par[P_t_ign]:
                lit = True; burning = True
                starts += 1
                F = 0.05 * Fmax * tsc
                phase = 5
        if phase == 5 or phase == 6:
            # drogue release on confirmed thrust
            if drogue and F > 0.5 * floorF * tsc:
                drogue = False
                apar[A_DROGUE_DEPLOYED] = 0.0
                relight_ok = 1.0
            keff = k_hat if par[P_k_est] > 0.5 else 1.0
            amin = keff * floorF / m_est - g
            amax = keff * Fc_avail / m_est - g
            vtd = par[P_vt]; hg = par[P_ht]
            if hslam:
                a_term = amin + par[P_hs_margin]
                if a_term < 1.0:
                    a_term = 1.0
                ad = amin + 0.5 * (amax - amin)
            else:
                a_term = 1.5
                ad = par[P_kd] * amax
            if ad < a_term + 0.5:
                ad = a_term + 0.5
            vg = np.sqrt(vtd * vtd + 2.0 * a_term * hg)
            hh = h_est if h_est > 0.0 else 0.0
            if h_est > hg:
                vref = -np.sqrt(vg * vg + 2.0 * ad * (h_est - hg))
                aref = ad * vz_e / vref
                tgo = (-vref - vg) / ad + 2.0 * hg / (vg + vtd)
            else:
                if phase == 5:
                    ei = 0.0
                phase = 6
                vref = -np.sqrt(vtd * vtd + 2.0 * a_term * hh)
                aref = a_term * vz_e / vref
                tgo = 2.0 * hh / (-vref + vtd)
            if aref < 0.0:
                aref = 0.0
            if hslam and vz_e > -par[P_hcut] and not td_done:
                cut = True; lit = False; phase = 7
            ev = vref - vz_e
            if not ((sat_hi and ev > 0.0) or (sat_lo and ev < 0.0)):
                ei += ev * dt
            ki = 0.6 * par[P_kv]
            if ki * ei > 3.0:
                ei = 3.0 / ki
            if ki * ei < -3.0:
                ei = -3.0 / ki
            az = aref + par[P_kv] * ev + ki * ei
            # lateral guidance
            if phase == 5:
                if par[P_lat_mode] < 0.5:
                    wl = par[P_lat_wn]; zl = par[P_lat_zeta]
                    a_lat[0] = wl * wl * (par[P_target_x] - kx[0, 0]) - 2.0 * zl * wl * kx[0, 1]
                    a_lat[1] = wl * wl * (par[P_target_y] - kx[1, 0]) - 2.0 * zl * wl * kx[1, 1]
                elif par[P_lat_mode] < 1.5:
                    tg = tgo if tgo > 1.0 else 1.0
                    for a in range(2):
                        tgt = par[P_target_x] if a == 0 else par[P_target_y]
                        zem = tgt - (kx[a, 0] + kx[a, 1] * tg)
                        zev = 0.0 - kx[a, 1]
                        a_lat[a] = 6.0 * zem / (tg * tg) - 2.0 * zev / tg
                else:
                    # track the caller's reference (t_rel since landing-burn start)
                    nref = ref.shape[0]
                    if nref > 1:
                        trel = t - (t_ign_cmd + par[P_t_ign] if prof == 0 else 0.0)
                        k0 = 0
                        while k0 < nref - 2 and ref[k0 + 1, 0] < trel:
                            k0 += 1
                        f_ = (trel - ref[k0, 0]) / max(ref[k0 + 1, 0] - ref[k0, 0], 1e-6)
                        if f_ < 0.0:
                            f_ = 0.0
                        if f_ > 1.0:
                            f_ = 1.0
                        wl = par[P_lat_wn]; zl = par[P_lat_zeta]
                        for a in range(2):
                            pr = ref[k0, 1 + a] + f_ * (ref[k0 + 1, 1 + a] - ref[k0, 1 + a])
                            vr = ref[k0, 4 + a] + f_ * (ref[k0 + 1, 4 + a] - ref[k0, 4 + a])
                            ar = (ref[k0 + 1, 4 + a] - ref[k0, 4 + a]) / max(ref[k0 + 1, 0] - ref[k0, 0], 1e-6)
                            a_lat[a] = ar + wl * wl * (pr - kx[a, 0]) + 2.0 * zl * wl * (vr - kx[a, 1])
            else:
                # terminal: null horizontal velocity, stay near vertical
                a_lat[0] = -1.5 * kx[0, 1]
                a_lat[1] = -1.5 * kx[1, 1]
                tilt_lim = np.radians(3.0)
            # thrust vector (world): T = m (a_d + g)
            Tz = m_est * (g + az)
            Tz -= 0.5 * rho * S * apar[A_CA0_TF] * (0.5 + 0.5 * apar[A_K_RETRO]) * vz_e * vz_e
            if Tz < 0.0:
                Tz = 0.0
            Tx = m_est * a_lat[0]; Ty = m_est * a_lat[1]
            Th = np.sqrt(Tx * Tx + Ty * Ty)
            if Tz > 1.0 and Th > Tz * np.tan(tilt_lim):
                sc = Tz * np.tan(tilt_lim) / Th
                Tx *= sc; Ty *= sc
            Fcmd = np.sqrt(Tx * Tx + Ty * Ty + Tz * Tz) / keff
            if phase == 7:
                Fcmd = 0.0
        if phase == 7 or td_done:
            Fcmd = 0.0
            lit = False
        # ---------------- attitude command: desired thrust direction n_d (world)
        if phase == 5 or phase == 6:
            nn = np.sqrt(Tx * Tx + Ty * Ty + Tz * Tz)
            if nn > 1e-6:
                n_d[0] = Tx / nn; n_d[1] = Ty / nn; n_d[2] = Tz / nn
            else:
                n_d[0] = 0.0; n_d[1] = 0.0; n_d[2] = 1.0
        else:
            ax_ = a_lat[0]; ay_ = a_lat[1]
            th_ = np.sqrt(ax_ * ax_ + ay_ * ay_) / g
            if th_ > np.tan(tilt_lim):
                ax_ *= np.tan(tilt_lim) / th_; ay_ *= np.tan(tilt_lim) / th_
            nn = np.sqrt(ax_ * ax_ + ay_ * ay_ + g * g)
            n_d[0] = ax_ / nn; n_d[1] = ay_ / nn; n_d[2] = g / nn
        qrotT(qe, n_d, n_b)
        # attitude error (rotation that takes body z to n_d), body axes x/y
        ex = -n_b[1]
        ey = n_b[0]
        # gyro-measured rates (bias included) for damping
        F_est = (F / tsc if F > 1.0 else 0.0) * keff
        lp_est = l_p
        wn_a = par[P_att_wn_asc] if phase == 1 else par[P_att_wn]
        za = par[P_att_zeta]
        if att_active and F_est > 0.2 * floorF and lit:
            eix += ex * dt
            eiy += ey * dt
            Mx = It * (wn_a * wn_a * ex - 2.0 * za * wn_a * wm[0] + par[P_att_ki] * eix)
            My = It * (wn_a * wn_a * ey - 2.0 * za * wn_a * wm[1] + par[P_att_ki] * eiy)
            den_ = F_est * lp_est
            dcx = -Mx / den_
            dcy = -My / den_
            dm = np.sqrt(dcx * dcx + dcy * dcy)
            if dm > gmax:
                dcx *= gmax / dm; dcy *= gmax / dm
                eix -= ex * dt; eiy -= ey * dt          # anti-windup
                sat_steps += 1
            burn_steps += 1
            dcmd[0] = dcx; dcmd[1] = dcy
        else:
            # hold centre (no authority)
            dcmd[0] = 0.0; dcmd[1] = 0.0
            eix = 0.0; eiy = 0.0
        # roll RCS
        Mrcs = 0.0
        if par[P_rcs_on] > 0.5:
            if wm[2] > par[P_rcs_deadband]:
                Mrcs = -par[P_rcs_torque]
            elif wm[2] < -par[P_rcs_deadband]:
                Mrcs = par[P_rcs_torque]
        # ================================================================ engine
        if lit and burning:
            sat_lo = Fcmd <= floorF
            sat_hi = Fcmd >= Fc_avail
            if Fcmd < floorF:
                Fcmd = floorF
            if Fcmd > Fc_avail:
                Fcmd = Fc_avail
            if abs(Fcmd - Fc_prev) < par[P_deadb] * Fmax:
                Fcmd = Fc_prev
            qq = par[P_quant] * Fmax
            if qq > 0:
                Fcmd = np.floor(Fcmd / qq + 0.5) * qq
            Fc_prev = Fcmd
            Ftgt = Fcmd * tsc
            if Ftgt > Fceil:
                Ftgt = Fceil
            dF = (Ftgt - F) / par[P_tau] * dt
            lim = par[P_slew] * Fmax * dt
            if dF > lim:
                dF = lim
            if dF < -lim:
                dF = -lim
            F += dF
            burn_time += dt
        else:
            F += (0.0 - F) / par[P_t_off] * dt
            if F < 0.5:
                F = 0.0
            if not lit:
                burning = False if F == 0.0 else burning
        if F < 0.0:
            F = 0.0
        mox = 0.0; mf_ = 0.0
        if F > 0.0 and ml > resid:
            mox = _bilin(Fg, Dg, tmox, F / tsc, Dp) / isc
            mf_ = _bilin(Fg, Dg, tmf, F / tsc, Dp) / isc
        elif F > 0.0:
            F = 0.0
        # ================================================================ gimbal actuators
        cbuf[ibuf, 0] = dcmd[0]; cbuf[ibuf, 1] = dcmd[1]
        jb = ibuf - kdel
        if jb < 0:
            jb += nbuf
        ibuf = (ibuf + 1) % nbuf
        wn_g = par[P_gim_wn]; zg_ = par[P_gim_zeta]
        hinge_now = 0.0
        for a in range(2):
            u = cbuf[jb, a]
            if abs(u - dsv[a]) < np.radians(par[P_gim_deadband]):
                u = dsv[a]
            acc_s = wn_g * wn_g * (u - dsv[a]) - 2.0 * zg_ * wn_g * dsr[a]
            dsr[a] += acc_s * dt
            # load-dependent rate limit (linear torque-speed line), hinge load estimate
            hl_a = abs(I_piv * acc_s) + par[P_hose_K] * abs(deng[a]) + par[P_gim_fric] * (F / Fmax)
            rl = np.radians(par[P_gim_rate_nl]) * (1.0 - hl_a / par[P_gim_stall_engine])
            if rl < np.radians(5.0):
                rl = np.radians(5.0)
            if dsr[a] > rl:
                dsr[a] = rl
            if dsr[a] < -rl:
                dsr[a] = -rl
            dsv[a] += dsr[a] * dt
            if dsv[a] > gmax * 1.05:
                dsv[a] = gmax * 1.05; dsr[a] = 0.0
            if dsv[a] < -gmax * 1.05:
                dsv[a] = -gmax * 1.05; dsr[a] = 0.0
            # backlash: engine follows the servo only outside a dead zone of +/- b/2
            hb = 0.5 * np.radians(par[P_gim_backlash])
            if dsv[a] - deng[a] > hb:
                deng[a] = dsv[a] - hb
            elif deng[a] - dsv[a] > hb:
                deng[a] = dsv[a] + hb
            if hl_a > hinge_now:
                hinge_now = hl_a
        dd = np.zeros(2)
        for a in range(2):
            dd_now = (deng[a] - deng_prev[a]) / dt
            dd[a] = (dd_now - dd_prev[a]) / dt          # engine angular acceleration
            dd_prev[a] = dd_now
            deng_prev[a] = deng[a]
            if abs(dd_now) > max_gim_rate and lit:
                max_gim_rate = abs(dd_now)
        gm = np.sqrt(deng[0] ** 2 + deng[1] ** 2)
        if gm > max_gim and lit:
            max_gim = gm
        if hinge_now > max_hinge and lit:
            max_hinge = hinge_now
        # ================================================================ forces and moments (body)
        dx = deng[0] + par[P_mis_x]
        dy = deng[1] + par[P_mis_y]
        tb[0] = np.sin(dy) * np.cos(dx)
        tb[1] = -np.sin(dx)
        tb[2] = np.cos(dx) * np.cos(dy)
        for i in range(3):
            Fb[i] = F * tb[i]
        # thrust acts at the pivot: r_p = (-cg_x, -cg_y, z_p - zcg)
        rpx = -par[P_cg_x]; rpy = -par[P_cg_y]; rpz = z_p - zcg
        Mb[0] = rpy * Fb[2] - rpz * Fb[1]
        Mb[1] = rpz * Fb[0] - rpx * Fb[2]
        Mb[2] = rpx * Fb[1] - rpy * Fb[0] + par[P_roll_torque] * (F / Fmax) + Mrcs
        # tail-wags-dog: engine angular acceleration reaction
        Mb[0] += -J_twd * dd[0]
        Mb[1] += -J_twd * dd[1]
        # jet damping
        mdot = mox + mf_
        le2 = (zcg - (-0.03)) ** 2
        Mb[0] += -mdot * le2 * w[0]
        Mb[1] += -mdot * le2 * w[1]
        # aerodynamics (aero.py: v_rel, omega body; forces/moments about the CG)
        aero_forces(vrel_b, w, rho, zcg, F > 1.0, apar, comp, Fa, Ma)
        for i in range(3):
            Fb[i] += Fa[i]; Mb[i] += Ma[i]
        # slosh (first lateral mode)
        hliq = ml / (rho_l * tank_A) if ml > 0 else 0.0
        ms = 0.0
        if par[P_slosh_on] > 0.5 and hliq > 0.02:
            xi = 1.841
            ms = ml * (2.0 * tank_R / (xi * (xi * xi - 1.0) * hliq)) * np.tanh(xi * hliq / tank_R)
            if ms > 0.5 * ml:
                ms = 0.5 * ml
        f_ax = Fb[2] / m_tot
        if ms > 0.0 and f_ax > 0.5:
            ws2 = (1.841 * f_ax / tank_R) * np.tanh(1.841 * hliq / tank_R)
            wss = np.sqrt(ws2)
            zs = tank_zb + hliq - 0.54 * tank_R
            rzs = zs - zcg
            # lateral specific force at the slosh station (rigid body, previous alpha)
            fsx = Fb[0] / m_tot + alpha_prev[1] * rzs
            fsy = Fb[1] / m_tot - alpha_prev[0] * rzs
            for a in range(2):
                fl = fsx if a == 0 else fsy
                acc_s2 = -ws2 * xs[a] - 2.0 * par[P_slosh_zeta] * wss * vs[a] - fl
                vs[a] += acc_s2 * dt
                xs[a] += vs[a] * dt
            fx_s = ms * (ws2 * xs[0] + 2.0 * par[P_slosh_zeta] * wss * vs[0])
            fy_s = ms * (ws2 * xs[1] + 2.0 * par[P_slosh_zeta] * wss * vs[1])
            Fb[0] += fx_s; Fb[1] += fy_s
            Mb[0] += -rzs * fy_s
            Mb[1] += rzs * fx_s
        else:
            xs[0] *= 0.99; xs[1] *= 0.99; vs[0] *= 0.99; vs[1] *= 0.99
        # legs / ground contact (world forces)
        Fw[0] = 0.0; Fw[1] = 0.0; Fw[2] = 0.0
        leg_f_tot = 0.0
        contact = False
        nfeet = 4
        rf = par[P_r_foot] if legs_dep else 0.06
        zf = par[P_z_foot] if legs_dep else -0.03
        for kf in range(nfeet):
            ang = 0.25 * np.pi + 0.5 * np.pi * kf
            bx = rf * np.cos(ang); by = rf * np.sin(ang); bz = zf - zcg
            qrot(q, np.array([bx, by, bz]), tmp3)
            pz = r[2] + tmp3[2]
            if pz < 0.0:
                contact = True
                # foot velocity: v + R (w x b)
                wxb = np.array([w[1] * bz - w[2] * by, w[2] * bx - w[0] * bz, w[0] * by - w[1] * bx])
                vf = np.zeros(3)
                qrot(q, wxb, vf)
                for i in range(3):
                    vf[i] += v[i]
                pen = -pz
                if legs_dep:
                    fn = par[P_legs_k] * pen - par[P_legs_c] * vf[2]
                    if pen > par[P_legs_stroke]:
                        fn += 2.0e5 * (pen - par[P_legs_stroke])
                else:
                    fn = 2.0e5 * pen - 2.0e3 * vf[2]
                if fn < 0.0:
                    fn = 0.0
                vt_ = np.sqrt(vf[0] ** 2 + vf[1] ** 2)
                mu = par[P_legs_mu]
                ftx = -mu * fn * vf[0] / max(vt_, 0.05)
                fty = -mu * fn * vf[1] / max(vt_, 0.05)
                fwx = ftx; fwy = fty; fwz = fn
                Fw[0] += fwx; Fw[1] += fwy; Fw[2] += fwz
                leg_f_tot += np.sqrt(fwx * fwx + fwy * fwy + fwz * fwz)
                # moment: (R b) x F_w -> body
                mwx = tmp3[1] * fwz - tmp3[2] * fwy
                mwy = tmp3[2] * fwx - tmp3[0] * fwz
                mwz = tmp3[0] * fwy - tmp3[1] * fwx
                mb_ = np.zeros(3)
                qrotT(q, np.array([mwx, mwy, mwz]), mb_)
                for i in range(3):
                    Mb[i] += mb_[i]
        if leg_f_tot > peak_leg:
            peak_leg = leg_f_tot
        # ================================================================ hold-down / touchdown logic
        if held:
            if F >= par[P_hold_tw] * m_tot * g or (on_legs and F > m_tot * g):
                held = False
        if (not held) and contact and t > 1.0 and not td_done and phase >= 3 and (prof == 1 or phase >= 4):
            td_done = True
            t_td = t
            res[R_td_vz] = v[2]
            res[R_td_vh] = np.sqrt(v[0] ** 2 + v[1] ** 2)
            res[R_td_tilt] = np.degrees(tilt)
            res[R_td_rate] = np.degrees(np.sqrt(w[0] ** 2 + w[1] ** 2))
            res[R_td_miss] = np.sqrt((r[0] - par[P_target_x]) ** 2 + (r[1] - par[P_target_y]) ** 2)
            res[R_td_x] = r[0]; res[R_td_y] = r[1]
            res[R_td_t] = t
            res[R_td_roll_rate] = np.degrees(abs(w[2]))
            res[R_att_err_td] = np.degrees(np.arccos(min(1.0, max(-1.0, zbe[0] * zb_w[0] + zbe[1] * zb_w[1] + zbe[2] * zb_w[2]))))
            res[R_nav_h_err_td] = kx[2, 0] - r[2]
            res[R_nav_v_err_td] = kx[2, 1] - v[2]
            res[R_lat_err_td] = np.sqrt((kx[0, 0] - r[0]) ** 2 + (kx[1, 0] - r[1]) ** 2)
            res[R_m_land] = m_tot
            lit = False
        # ================================================================ integrate translational
        Fws = np.zeros(3)
        qrot(q, Fb, Fws)
        m_r = m_tot - ms
        if held:
            acc = np.zeros(3)
            fb[0] = Fb[0] / m_tot; fb[1] = Fb[1] / m_tot; fb[2] = (Fb[2] + m_tot * g) / m_tot
        else:
            acc = np.zeros(3)
            for i in range(3):
                acc[i] = (Fws[i] + Fw[i]) / m_r
            acc[2] -= g
            # specific force in body (for the IMU): (F_aero+thrust+contact)/m
            Fcb = np.zeros(3)
            qrotT(q, Fw, Fcb)
            for i in range(3):
                fb[i] = (Fb[i] + Fcb[i]) / m_r
        for i in range(3):
            v[i] += acc[i] * dt
            r[i] += v[i] * dt
        acc_prev = acc[2] if not held else 0.0
        # axial and lateral load at the engine (pivot station)
        ax_g = abs(fb[2]) / g
        if ax_g > max_axial:
            max_axial = ax_g
        # ================================================================ integrate rotational
        if held:
            for i in range(3):
                w[i] = 0.0
                alpha_prev[i] = 0.0
        else:
            al = np.zeros(3)
            al[0] = (Mb[0] - w[1] * w[2] * (Ir - It)) / It
            al[1] = (Mb[1] - w[2] * w[0] * (It - Ir)) / It
            al[2] = Mb[2] / Ir
            for i in range(3):
                w[i] += al[i] * dt
                alpha_prev[i] = al[i]
            qint(q, w, dt)
            lat_eng = np.sqrt((fb[0] + al[1] * rpz) ** 2 + (fb[1] - al[0] * rpz) ** 2) / g
            if lat_eng > max_lat_eng:
                max_lat_eng = lat_eng
        # ================================================================ propellant / tank
        dm_ox = mox * dt
        dm_f = mf_ * dt
        if dm_f > mfuel:
            dm_f = mfuel
        mfuel -= dm_f
        prop_used += dm_ox + dm_f
        E -= dm_ox * hl
        mt -= dm_ox
        tank_timer += dt
        if tank_timer >= 0.01 - 1e-12:
            T, Pt, ml, mv, hl = tank_solve(mt, E, V, Cw)
            tank_timer = 0.0
        # thrust-effectiveness estimator (accelerometer, landing burn)
        if par[P_k_est] > 0.5 and (phase == 5 or phase == 6) and F > 0.15 * Fmax * tsc and not td_done:
            F_mod = F / tsc
            k_raw = (fm[2] * m_est - Fa[2]) / F_mod
            k_hat += (k_raw - k_hat) * dt / par[P_k_est_tau]
        # ================================================================ metrics
        wt = np.sqrt(w[0] ** 2 + w[1] ** 2)
        if abs(w[2]) > max_roll:
            max_roll = abs(w[2])
        if phase == 1 and Vair > 5.0:
            if aoa > max_aoa_asc:
                max_aoa_asc = aoa
        if phase == 2 and prof == 0:
            if wt > max_rate_coast:
                max_rate_coast = wt
            if Vair > 5.0 and aoa > coast_aoa:
                coast_aoa = aoa
        if (phase == 3 or phase == 4):
            if wt > max_rate_desc:
                max_rate_desc = wt
            if np.pi - tilt > max_tilt_desc and prof == 0:
                pass
        if phase == 4 or (phase == 3 and prof == 0):
            # attitude during the unpowered descent: angle of the body axis from vertical
            if tilt > max_tilt_desc:
                max_tilt_desc = tilt
        if (phase == 5 or phase == 6) and not td_done:
            if wt > max_rate_land:
                max_rate_land = wt
            if tilt > max_tilt_land:
                max_tilt_land = tilt
        if r[2] > hmax:
            hmax = r[2]
        t += dt
        # ================================================================ record
        if t >= next_rec and nrec < out_rec.shape[0]:
            o = out_rec[nrec]
            o[0] = t; o[1] = r[0]; o[2] = r[1]; o[3] = r[2]; o[4] = v[0]; o[5] = v[1]; o[6] = v[2]
            o[7] = q[0]; o[8] = q[1]; o[9] = q[2]; o[10] = q[3]; o[11] = w[0]; o[12] = w[1]; o[13] = w[2]
            o[14] = F; o[15] = Fcmd if lit else 0.0; o[16] = np.degrees(deng[0]); o[17] = np.degrees(deng[1])
            o[18] = np.degrees(dcmd[0]); o[19] = np.degrees(dcmd[1]); o[20] = m_tot; o[21] = zcg; o[22] = phase
            o[23] = np.degrees(tilt); o[24] = np.degrees(aoa); o[25] = kx[0, 0]; o[26] = kx[1, 0]; o[27] = kx[2, 0]
            o[28] = kx[0, 1]; o[29] = kx[1, 1]; o[30] = kx[2, 1]; o[31] = Pt; o[32] = ml; o[33] = hinge_now
            o[34] = k_hat; o[35] = wwx; o[36] = wwy
            nrec += 1
            next_rec += par[P_rec_dt]
        # ================================================================ termination
        if td_done and t > t_td + par[P_t_post]:
            landed = True
            break
        if (not held) and t > 2.0 and r[2] < -1.0:
            break
        if td_done and tilt > np.radians(60.0):
            tip = True
    if td_done and tilt > np.radians(45.0):
        tip = True
    res[R_landed] = 1.0 if td_done else 0.0
    res[R_prop_used] = prop_used
    res[R_liq_left] = ml
    res[R_exhausted] = 1.0 if exhausted else 0.0
    res[R_h_max] = hmax
    res[R_apo_x] = apo_x; res[R_apo_y] = apo_y
    res[R_v_ign] = v_ign; res[R_h_ign] = h_ign
    res[R_max_gim] = np.degrees(max_gim); res[R_max_gim_rate] = np.degrees(max_gim_rate)
    res[R_max_hinge] = max_hinge
    res[R_max_rate_coast] = np.degrees(max_rate_coast); res[R_max_rate_desc] = np.degrees(max_rate_desc)
    res[R_max_rate_land] = np.degrees(max_rate_land); res[R_max_tilt_land] = np.degrees(max_tilt_land)
    res[R_max_aoa_asc] = np.degrees(max_aoa_asc)
    res[R_tumble_coast] = 1.0 if max_rate_coast > np.radians(90.0) else 0.0
    res[R_starts] = starts; res[R_burn_time] = burn_time
    res[R_tipover] = 1.0 if tip else 0.0
    res[R_peak_leg_force] = peak_leg
    res[R_max_axial_g] = max_axial; res[R_max_lat_g_eng] = max_lat_eng
    res[R_hslam_used] = 1.0 if hslam else 0.0
    res[R_cut] = 1.0 if cut else 0.0
    res[R_nrec] = nrec; res[R_t_end] = t
    res[R_max_tilt_desc] = np.degrees(max_tilt_desc)
    res[R_relight_ok] = relight_ok
    res[R_max_q] = max_q
    res[R_coast_aoa_max] = np.degrees(coast_aoa)
    res[R_fuel_left] = mfuel
    res[R_gim_sat_frac] = sat_steps / burn_steps if burn_steps > 0 else 0.0
    res[R_max_roll_rate] = np.degrees(max_roll)
    if res[R_m_land] == 0.0:
        res[R_m_land] = m_tot
    return res

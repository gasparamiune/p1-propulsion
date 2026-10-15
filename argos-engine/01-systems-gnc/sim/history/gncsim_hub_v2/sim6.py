"""6-DOF flight simulator (numba) for the 500 N throttleable N2O/ABS hybrid VTVL vehicle.  sim6 v2.7.1-dev

Frames: world W = ENU, flat earth, origin at the pad, z up. Body B: z_b along the vehicle axis toward
the nose; stations z [m] from the airframe aft datum (vehicle.py). Quaternion q (scalar first)
rotates body -> world.

Truth model
 * rigid body with variable mass, CG and inertia (vehicle.massprops: N2O liquid settled aft, grain
   regression), Euler rotational equations, jet damping, lateral CG offset;
 * thrust along the gimballed nozzle axis through the pivot (on axis), thrust misalignment angles;
   tail-wags-dog reaction torque  -J_twd * delta_ddot,  J_twd = I_e + m_e l_e (l_e + l_p);
   engine roll torque (helical-port swirl, ASSUMED magnitude) proportional to thrust;
 * engine: command -> floor/ceiling clamp -> deadband -> quantisation -> slew -> first-order
   (closed-loop Pc response); ignition delay, tail-off; mass flow from the throttle map
   (O/F shift, Isp vs throttle), Isp dispersion; equilibrium self-pressurised N2O tank every 10 ms;
   thrust ceiling vs tank pressure (blowdown);
 * gimbal actuators (2 axes): command transport delay (ring buffer), 2nd-order servo (wn, zeta),
   rate limit from a linear torque-speed line loaded by the hinge-moment estimate, deadband,
   backlash (dead zone between servo output and engine), mechanical angle limit (v2.1: optional
   crank-linkage nonlinearity, engine rate x cos(psi) and torque / cos(psi), psi = asin(n |delta|),
   and a conical stop on the gimbal vector, both from mechanical.json; optional flexible engine mount:
   engine angle on the axis stiffness rock_K with damping rock_zeta behind the backlash);
 * aerodynamics: all-attitude component build-up (aero.py) at the local air velocity incl. omega x r,
   steady wind with power-law shear + Dryden turbulence (first-order forms, MIL-F-8785C low-altitude
   scales), ISA density; nose drogue (quasi-steady tension at the nose tip), legs, optional fins;
 * propellant slosh: first lateral mode as a spring-mass (Abramson, NASA SP-106), active while the
   liquid is settled (axial specific force > 0.5 m/s2); the slosh mass moves with the tank axially;
 * landing legs: 4 spring-damper feet with stroke limit (hard stop) and regularised Coulomb friction.
Flight-software model
 * sensors: IMU (gyro/accel residual bias, scale factor, noise density, thrust-proportional vibration
   noise), GNSS (constant per-run bias + white noise, uncompensated latency), LiDAR altimeter
   (< lidar_range, tilt < 30 deg), barometer (bias); pad alignment error (3 axes);
 * estimator: gyro-propagated attitude (no in-flight aiding) + three decoupled 3-state Kalman filters
   [position, velocity, accel bias] per world axis at 100 Hz;
 * guidance: ascent lateral-velocity hold (+ optional upwind bias) and MECO on predicted apogee;
   coast; drogue at apogee; relight on the predicted stopping distance planned on the latest
   ignition; landing burn vertical: vert_mode 0 = velocity-tracking reference + PI (sim1d v1.2),
   1 = ZEM/ZEV to the terminal gate (ht); accelerometer thrust-effectiveness estimator; hoverslam mode;
   lateral: lat_mode 0 = PD, 1 = ZEM/ZEV, both to a reachable target (divert radius clip),
   2 = 'convex-lite': box-constrained minimum-energy divert (QP, KKT clipped-linear solution,
   semismooth Newton, target scaled into the reachable set) re-solved at 10 Hz;
   terminal (below the gate ht): lateral-velocity nulling (gain kt_lat), tilt limit tilt_term_hi at the gate
   tapering to tilt_term below 1 m;
   v2.1: optional lateral disturbance feed-forward (dff): d = R(q_est) f_meas - F_est R(q_est) t_b(encoder) / m_est,
   low-pass dff_tau, subtracted from the lateral acceleration command in the landing burn; drag
   feed-forward and the thrust-effectiveness estimator use a NOMINAL drag model (drag_cda_nom,
   rho 1.2), not the dispersed truth;
 * control: attitude PD+I on the thrust-direction error, gain-scheduled on estimated thrust and
   moment arm -> gimbal angles, circular gimbal limit, anti-windup; throttle = |T_cmd| / k_eff
   with floor/ceiling saturation and integrator freeze; optional roll RCS (bang-bang, deadband);
   v2.1: optional command slew-rate limit (gim_cmd_rate) and 2nd-order structural low-pass on the gimbal
   command (gim_lpf_w, gim_lpf_z).
 * v2.2: inactive attitude loop returns the gimbal command to neutral through the slew limit and low-pass
   (no step); base excitation of the flexible engine mount (body angular acceleration, pivot lateral and axial
   specific force on m_e l_e) so the actuator load at touchdown is computed; load maxima split into flight
   (before touchdown) and touchdown (after first contact) metrics.
 * v2.3: vert_mode 1 (ZEM/ZEV vertical) re-estimates the time-to-go every step from the planned deceleration,
   tgo = (|vz| - vg)/ad, and hands over to the terminal law when tgo < t_hand (v2.2: fixed final time from burn
   start with a 0.3 s floor, which has an equilibrium hover above the gate); load metrics in g are normalised by
   standard gravity G0 (test mode 1 runs with g = 0). vert_mode 0 (baseline) is unchanged.
 * v2.4: rotational integration split (rot_int 1, default): torque kick w += (M / I) dt, then the EXACT torque-free
   motion of the axisymmetric body over dt, q <- q (x) exp(H_b / It dt) (x) exp(b e_z dt), b = w_z (It - Ir) / It, and the
   body transverse rates rotated by -b dt about z. v2.3 integrated w with explicit Euler including the gyroscopic
   term: the transverse rate amplitude of a spinning body grew as exp(T b^2 dt / 2) (torque-free test: |H| drift
   8.9 % over 20 s at 3 rad/s spin, dt 1 ms). rot_int 0 reproduces v2.3.
 * v2.5: optional torque- and speed-limited TVC actuator pair (act_model 1). The moment that the flexible mount asks of
   the linkage, K (d_link - d_engine) + c (..), plus bearing friction opposing the engine motion, is mapped through the
   exact Cardan + vertical-pushrod + horn kinematics (mechanical.json geometry, as Electronics tvc_slew_check_v1) to the
   two servo torques; each servo is held to its linear torque-speed line (driving) or its stall torque (braking), and the
   moment vector is scaled by the most limiting servo. The engine then receives the scaled moment. The servo reference
   keeps its 2nd-order dynamics without the v2.4 inertia/load limits (the torque saturation replaces them). Optional
   reflected servo inertia act_Jint on the engine DOF. Supply: fixed plug voltage (act_sag 0: act_Ts, act_wnl) or a
   resistive supply chain (act_sag 1: rest voltage, shared source, TVC common path and per-servo branch resistances,
   servo current I_run + (I_stall(V) - I_run) |T| / Ts), each servo on the torque-speed line of its own plug voltage
   (DATASHEET points, torque and time per 60 deg linear in V). Saturation time (flight, landing burn, after touchdown),
   episodes, longest episode, depth (minimum scale factor), the part of it in which a servo's demand exceeds its stall torque
   (torque-limited; the rest is speed-limited on the line), minimum plug voltage and maximum servo current are recorded.
   act_model 0 (default) reproduces v2.4.
 * v2.6 (flight software v2.6, lead decisions 2026-10-12; every option off by default, bit-identical to v2.5 when off,
   m2_bitcheck_v26): rate- and acceleration-limited gimbal command tracker (gim_cmd_rate, gim_cmd_acc); attitude reference
   governor (att_ref_rate, att_ref_win, att_ref_rate2; att_ref_mode 1 = ratchet); lift-ramp shutdown model (toff_model 1,
   gncsim.tailoff); pre-MECO throttle-down (meco_td, meco_td_max, meco_td_hold); relight start rule (relight_start_frac:
   start at max(floor, frac), hold to 90 %); ENG-07d notch on the gimbal command (gim_notch_*: fixed or tracking the
   run's own rocking mode); integrator anti-windup reset option (gim_aw_thr, gim_aw_tau).
 * v2.7 (flight software v2.7 PROVISIONAL, lead 2026-10-13; off by default, bit-identical to v2.6 when off,
   m2_bitcheck_v27): in-flight throat-area growth with the ECU Pc-loop model (throat_g, throat_jref, throat_loop: area
   growth with the burn as J = int (Pc/Pc_max)^0.68 dt, reaching throat_g at the nominal flight's J; CF change of the
   eroded expansion ratio, k_cf tabulated); thrust-effectiveness estimator in the
   B-profile ascent / apex / floor descent (k_est_asc 1 rejected, kept; k_est_asc 2: signed nominal axial-force model,
   airborne gate h_est > 1 m, floor and top-up commands divided by k_hat in [0.8, 1.25]).
 * v2.7.1-dev (2026-10-13; off by default, bit-identical when off, m2_bitcheck_v271): regression-law band (reg_on,
   reg_x*, reg_o*, reg_u*: oxidiser and fuel flow per delivered thrust multiplied by piecewise-linear phi(X), X = oxidiser
   burned at map flow; knots from gncsim.regband); run6 adds the start-delay quantile option t_ign_q (no sim6 change).
All parameters are passed in par[] (names in PAR_NAMES) by run6.py, which reads the interface
JSON and tags every value.
"""
import numpy as np
from numba import njit
from .propulsion import tank_solve, tank_init, _bilin
from .aero import (aero_forces, A_LEGS_DEPLOYED, A_DROGUE_DEPLOYED, A_SREF, A_CA0_NF, A_CA0_TF,
                   A_K_RETRO)
from .vehicle import massprops

G0 = 9.80665
SIM6_VERSION = "sim6 v2.7.1-dev (2026-10-13)"

PAR_NAMES = """
profile h_target Fmax floor tau slew deadb quant t_ign t_ign_est t_rise t_off thrust_scale isp_scale
tank_V m_n2o T0 c_wall resid rho_l_nom m_fuel0
z_tip z_foot r_foot z_imu legs_mode legs_k legs_c legs_stroke legs_mu
kd ht vt kv hslam hcut hover_k hs_margin k_est k_est_tau
gim_max gim_wn gim_zeta gim_rate_nl gim_stall_engine gim_delay gim_deadband gim_backlash hose_K gim_fric
att_wn att_zeta att_ki att_wn_asc tilt_max_land tilt_max_asc tilt_term tilt_term_hi lat_mode lat_wn lat_zeta
target_x target_y vert_mode div_margin t_hmin
mis_x mis_y cg_x cg_y zcg_err roll_torque rcs_on rcs_torque rcs_deadband
wind_u wind_dir wind_alpha gust_on gust_scale rho0
drogue_CdA descent_mode fins_on ascent_bias_x ascent_bias_y
slosh_on slosh_zeta
g_bx g_by g_bz a_bx a_by a_bz g_sf a_sf g_arw a_vrw vib_sigma align_x align_y align_z
gnss_sp_h gnss_sp_v gnss_sv gnss_rate gnss_lat gnss_bx gnss_by gnss_bz gnss_bsh gnss_bsv
lidar_on lidar_sigma lidar_frac lidar_range baro_sigma baro_bias baro_bsig
mest dt tmax seed rec_dt hold_tw t_post h_bias_nav
fuel_phi tau_fuel test_mode w0x w0y w0z v0z h0 gim_n gim_stop dff dff_tau drag_cda_nom
rock_K rock_zeta gim_lpf_w gim_lpf_z gim_cmd_rate roll_comp_tau kt_lat t_hand rot_int
act_model act_Ts act_wnl act_re act_rh act_zb act_az1 act_az2 act_Jint
act_sag act_Vrest act_Rs act_Rc act_Rb act_Io act_Irun act_Ia act_Ik act_V0 act_V1 act_V2 act_T0 act_T1 act_T2
act_s0 act_s1 act_s2
gim_cmd_acc gim_aw_thr gim_aw_tau gim_enc_q att_ref_rate att_ref_win att_ref_rate2
toff_model toff_vs toff_lag_a toff_lag_c toff_l1 toff_l2 toff_l3 toff_l4 toff_l5 toff_f1 toff_f2 toff_f3 toff_f4 toff_f5
meco_td meco_td_hold relight_start_frac toff_l0 meco_td_max
gim_notch_f gim_notch_q gim_notch_db
att_ref_mode
throat_g throat_jref throat_k0 throat_k1 throat_k2 throat_k3
k_est_asc throat_loop
kest_cda_nf kest_cda_legs floor_comp_min
reg_on reg_nk
""".split() + [f"reg_x{_k}" for _k in range(40)] + [f"reg_o{_k}" for _k in range(40)] + [f"reg_u{_k}" for _k in range(40)]
# v2.7.1-dev: regression-law band (gncsim.regband): reg_nk knots X [kg oxidiser at the map flows] in reg_x*, phi_ox in reg_o*,
# phi_f in reg_u* (40 slots; off unless reg_on)
for _i, _n in enumerate(PAR_NAMES):
    globals()["P_" + _n] = _i
NP = len(PAR_NAMES)

RES_NAMES = """
landed td_vz td_vh td_tilt td_rate td_miss td_t prop_used liq_left exhausted h_max apo_x apo_y
v_ign h_ign max_gim max_gim_rate max_hinge max_rate_coast max_rate_desc max_rate_land max_tilt_land
max_aoa_asc tumble_coast starts burn_time tipover peak_leg_force td_roll_rate max_axial_g max_lat_g_eng
hslam_used cut m_land nrec t_end max_tilt_desc relight_ok att_err_td nav_h_err_td nav_v_err_td
lat_err_td max_q coast_aoa_max fuel_left gim_sat_frac td_x td_y max_roll_rate rcs_time rcs_ang_imp
max_gim_acc t_meco h_meco v_meco max_tilt_asc crash min_h_cut max_pen td_wind max_rate_post max_gim_raw
max_axial_g_flt max_lat_g_eng_flt max_alpha_flt max_axial_g_td max_lat_g_eng_td max_alpha_td max_hinge_td
act_sat_time act_sat_events act_sat_max_dur act_sat_kmin act_sat_time_td max_hinge_dem act_sat_time_land
act_Vmin act_Imax act_sat_time_stall act_sat_max_dur_stall aw_resets aw_time act_sat_max_t1 t_relight
t90_relight F_meco_cmd tailoff_imp t_td_start F_start_cmd
throat_g_end throat_J
reg_X_end
""".split()
for _i, _n in enumerate(RES_NAMES):
    globals()["R_" + _n] = _i
NR = len(RES_NAMES)

REC_NAMES = """
t x y z vx vy vz q0 q1 q2 q3 wx wy wz F Fcmd dgx dgy dcx dcy m zcg phase tilt aoa xe ye ze vxe vye vze
Ptank mliq hinge keff windx windy Fceil vref qdyn legF mox mf It Ir mfuel fax Ttank
dhx dhy alx aly tlim hest dsx dsy ksat mdem vplug attex attey araw
Fpc thg
""".split()
NREC = len(REC_NAMES)


@njit(cache=True)
def _rho(h, rho0):
    hh = h if h > 0.0 else 0.0
    return rho0 * (1.0 - 2.2558e-5 * hh) ** 4.2559


@njit(cache=True)
def _act_dz(a, b, az, re, zb):
    """Vertical displacement of the lever ball at azimuth az (radius re, height zb) for Cardan angles a (about x), b
    (about y): R = Rx(a) Ry(b) (Electronics tvc_slew_check_v1 geometry)."""
    x0 = re * np.cos(az)
    y0 = re * np.sin(az)
    z1 = -x0 * np.sin(b) + zb * np.cos(b)
    return y0 * np.sin(a) + z1 * np.cos(a) - zb


@njit(cache=True)
def servo_TV(V, V0, V1, V2, T0, T1, T2, s0, s1, s2):
    """Servo stall torque [N m] and no-load speed [rad/s] at plug voltage V: torque linear in V and time per 60 deg
    linear in V between the DATASHEET points (V0 < V1 < V2), end segments extrapolated (run6.servo_line rule)."""
    if V <= V1:
        f = (V - V0) / (V1 - V0)
        Ts = T0 + (T1 - T0) * f
        s60 = s0 + (s1 - s0) * f
    else:
        f = (V - V1) / (V2 - V1)
        Ts = T1 + (T2 - T1) * f
        s60 = s1 + (s2 - s1) * f
    if Ts < 0.0:
        Ts = 0.0
    if s60 < 1e-3:
        s60 = 1e-3
    return Ts, (np.pi / 3.0) / s60


@njit(cache=True)
def act_scale(a, b, wa, wb, Ma, Mb, az1, az2, re, zb, rh, Ts1, wnl1, Ts2, wnl2):
    """Scale factor k <= 1 on the demanded engine moment (Ma, Mb) so that both servos stay on their torque-speed
    lines; returns (k, T_1, T_2, stall) with the demanded servo torques T_i before scaling and stall = 1 when a servo's
    demand exceeds its stall torque (torque-limited, as opposed to speed-limited on the line). Rod forces f = J^-T M
    (J = d dz / d(a, b)); servo torque T_i = f_i r_h cos psi_i, servo speed w_i = (J_i . w_engine) / (r_h cos psi_i),
    psi_i = asin(dz_i / r_h). Driving (T_i w_i > 0): |T_i| <= Ts_i (1 - |w_i| / wnl_i); braking: |T_i| <= Ts_i."""
    h = 1e-6
    j00 = (_act_dz(a + h, b, az1, re, zb) - _act_dz(a - h, b, az1, re, zb)) / (2.0 * h)
    j01 = (_act_dz(a, b + h, az1, re, zb) - _act_dz(a, b - h, az1, re, zb)) / (2.0 * h)
    j10 = (_act_dz(a + h, b, az2, re, zb) - _act_dz(a - h, b, az2, re, zb)) / (2.0 * h)
    j11 = (_act_dz(a, b + h, az2, re, zb) - _act_dz(a, b - h, az2, re, zb)) / (2.0 * h)
    det = j00 * j11 - j01 * j10
    if abs(det) < 1e-12:
        return 1.0, 0.0, 0.0, 0
    f0 = (j11 * Ma - j10 * Mb) / det
    f1 = (-j01 * Ma + j00 * Mb) / det
    k = 1.0
    T_1 = 0.0
    T_2 = 0.0
    stall = 0
    for i in range(2):
        if i == 0:
            s_ = _act_dz(a, b, az1, re, zb) / rh
            fi = f0
            wi_ = j00 * wa + j01 * wb
            Ts = Ts1
            wnl = wnl1
        else:
            s_ = _act_dz(a, b, az2, re, zb) / rh
            fi = f1
            wi_ = j10 * wa + j11 * wb
            Ts = Ts2
            wnl = wnl2
        if s_ > 0.99:
            s_ = 0.99
        if s_ < -0.99:
            s_ = -0.99
        c_ = rh * np.sqrt(1.0 - s_ * s_)
        Ti = fi * c_
        if i == 0:
            T_1 = Ti
        else:
            T_2 = Ti
        wi = wi_ / c_
        if Ti * wi > 0.0:
            L = Ts * (1.0 - abs(wi) / wnl)
            if L < 0.0:
                L = 0.0
        else:
            L = Ts
        aT = abs(Ti)
        if aT > Ts:
            stall = 1
        if aT > L and aT > 1e-12:
            kk = L / aT
            if kk < k:
                k = kk
    return k, T_1, T_2, stall


@njit(cache=True)
def _interp6(x, xs, ys):
    """Piecewise-linear y(x) on 6 increasing points (clamped at the ends)."""
    if x <= xs[0]:
        return ys[0]
    for i in range(1, 6):
        if x <= xs[i]:
            return ys[i - 1] + (ys[i] - ys[i - 1]) * (x - xs[i - 1]) / max(xs[i] - xs[i - 1], 1e-12)
    return ys[5]


@njit(cache=True)
def _reg_phi(par, X, off_y):
    """v2.7.1-dev regression band: phi(X) piecewise-linear on the reg_nk knots in par (ends held), as regband.phi."""
    nk = int(par[P_reg_nk])
    if X <= par[P_reg_x0]:
        return par[off_y]
    for i in range(1, nk):
        xi = par[P_reg_x0 + i]
        if X <= xi:
            xa = par[P_reg_x0 + i - 1]
            w = (X - xa) / max(xi - xa, 1e-12)
            return par[off_y + i - 1] * (1.0 - w) + par[off_y + i] * w
    return par[off_y + nk - 1]


@njit(cache=True)
def _tail_imp(F0, tl, tf, vs, lag):
    """Tail-off impulse [N s] of a shutdown from thrust F0 with the pintle closing at lift speed vs [mm/s] on the
    lift-thrust table (tl [mm], tf [N]) plus the actuator/chamber lags: (1/vs) int_0^{l0} F(l) dl + F0 lag."""
    l0 = _interp6(F0, tf, tl)
    acc = 0.0
    for i in range(1, 6):
        a = tl[i - 1]; b = tl[i]
        if a >= l0:
            break
        bb = b if b < l0 else l0
        fa = tf[i - 1]; fb = _interp6(bb, tl, tf)
        acc += 0.5 * (fa + fb) * (bb - a)
    return acc / max(vs, 1e-9) + F0 * lag


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
def qint(q, w, dt):
    """q <- q (x) exp(0.5 w dt), w in body axes (exact for constant w over dt), renormalised."""
    wn = np.sqrt(w[0] ** 2 + w[1] ** 2 + w[2] ** 2)
    a = wn * dt
    if a < 1e-14:
        return
    s = np.sin(0.5 * a) / wn
    d0 = np.cos(0.5 * a); d1 = w[0] * s; d2 = w[1] * s; d3 = w[2] * s
    a0, a1, a2, a3 = q[0], q[1], q[2], q[3]
    q[0] = a0 * d0 - a1 * d1 - a2 * d2 - a3 * d3
    q[1] = a0 * d1 + a1 * d0 + a2 * d3 - a3 * d2
    q[2] = a0 * d2 - a1 * d3 + a2 * d0 + a3 * d1
    q[3] = a0 * d3 + a1 * d2 - a2 * d1 + a3 * d0
    n = np.sqrt(q[0] ** 2 + q[1] ** 2 + q[2] ** 2 + q[3] ** 2)
    for i in range(4):
        q[i] /= n


@njit(cache=True)
def kf3_predict(x, P, a, dt, qa, qb):
    """Per-axis KF, state [pos, vel, accel bias]; input a = measured acceleration (bias in state)."""
    acc = a - x[2]
    x[0] += x[1] * dt + 0.5 * acc * dt * dt
    x[1] += acc * dt
    # P <- F P F^T + Q,  F = [[1, dt, -dt^2/2], [0, 1, -dt], [0, 0, 1]]
    f01 = dt; f02 = -0.5 * dt * dt; f12 = -dt
    # A = F P
    a00 = P[0, 0] + f01 * P[1, 0] + f02 * P[2, 0]
    a01 = P[0, 1] + f01 * P[1, 1] + f02 * P[2, 1]
    a02 = P[0, 2] + f01 * P[1, 2] + f02 * P[2, 2]
    a10 = P[1, 0] + f12 * P[2, 0]
    a11 = P[1, 1] + f12 * P[2, 1]
    a12 = P[1, 2] + f12 * P[2, 2]
    a20 = P[2, 0]; a21 = P[2, 1]; a22 = P[2, 2]
    # P = A F^T
    P[0, 0] = a00 + a01 * f01 + a02 * f02
    P[0, 1] = a01 + a02 * f12
    P[0, 2] = a02
    P[1, 0] = a10 + a11 * f01 + a12 * f02
    P[1, 1] = a11 + a12 * f12
    P[1, 2] = a12
    P[2, 0] = a20 + a21 * f01 + a22 * f02
    P[2, 1] = a21 + a22 * f12
    P[2, 2] = a22
    # white-acceleration process noise (PSD qa) and bias random walk (PSD qb)
    P[0, 0] += qa * dt ** 3 / 3.0
    P[0, 1] += qa * dt ** 2 / 2.0
    P[1, 0] += qa * dt ** 2 / 2.0
    P[1, 1] += qa * dt
    P[2, 2] += qb * dt


@njit(cache=True)
def kf3_update(x, P, idx, z, R):
    y = z - x[idx]
    S_ = P[idx, idx] + R
    k0 = P[0, idx] / S_; k1 = P[1, idx] / S_; k2 = P[2, idx] / S_
    x[0] += k0 * y; x[1] += k1 * y; x[2] += k2 * y
    p0 = P[idx, 0]; p1 = P[idx, 1]; p2 = P[idx, 2]
    P[0, 0] -= k0 * p0; P[0, 1] -= k0 * p1; P[0, 2] -= k0 * p2
    P[1, 0] -= k1 * p0; P[1, 1] -= k1 * p1; P[1, 2] -= k1 * p2
    P[2, 0] -= k2 * p0; P[2, 1] -= k2 * p1; P[2, 2] -= k2 * p2
    for i in range(3):
        for j in range(i + 1, 3):
            m = 0.5 * (P[i, j] + P[j, i])
            P[i, j] = m; P[j, i] = m


@njit(cache=True)
def _cl_newton(dp, dv, T, amax, lam):
    """Box-constrained minimum-energy double-integrator divert on [0, T]:
        min 1/2 int a^2 dt  s.t.  int a dt = dv,  int (T - t) a dt = dp,  |a| <= amax.
    KKT: a(t) = clip(l1 (T - t) + l2, -amax, amax). Semismooth Newton on (l1, l2), trapezoid N = 40.
    Returns 1 if converged (feasible), 0 otherwise; lam updated in place."""
    N = 40
    h = T / N
    l1 = lam[0]; l2 = lam[1]
    for it in range(50):
        I0 = 0.0; I1 = 0.0; Ja = 0.0; Jb = 0.0; Jc = 0.0
        for k in range(N + 1):
            tau = T - k * h
            wk = h * (0.5 if (k == 0 or k == N) else 1.0)
            u = l1 * tau + l2
            if u > amax:
                aa = amax
            elif u < -amax:
                aa = -amax
            else:
                aa = u
                Ja += wk * tau; Jb += wk; Jc += wk * tau * tau
            I0 += wk * aa; I1 += wk * tau * aa
        r0 = I0 - dv; r1 = I1 - dp
        if abs(r0) < 1e-4 * (0.1 + abs(dv)) and abs(r1) < 1e-4 * (0.1 + abs(dp)):
            lam[0] = l1; lam[1] = l2
            return 1
        det = Ja * Ja - Jb * Jc
        if abs(det) < 1e-12:
            # fully saturated: pull the multipliers back toward the unsaturated region
            l1 *= 0.5; l2 *= 0.5
            continue
        dl1 = (r0 * Ja - Jb * r1) / det
        dl2 = (Ja * r1 - Jc * r0) / det
        l1 -= dl1; l2 -= dl2
    lam[0] = l1; lam[1] = l2
    return 0


@njit(cache=True)
def convex_lite_a0(p, v, ptgt, T, amax, lam):
    """First acceleration of the box-constrained min-energy divert from (p, v) to (ptgt, 0) in time T.
    If (ptgt, 0) is not reachable, the position target is scaled toward the free-drift point by
    bisection until reachable (target-reachability = convex projection along the segment)."""
    if T < 0.3:
        T = 0.3
    dv = -v
    if abs(dv) > 0.98 * amax * T:
        return -amax if v > 0 else amax
    dp_full = ptgt - p - v * T
    # unconstrained (ZEM/ZEV) initial guess
    lam[0] = 12.0 * (dp_full - dv * T / 2.0) / T ** 3
    lam[1] = (dv - lam[0] * T * T / 2.0) / T
    if _cl_newton(dp_full, dv, T, amax, lam) == 1:
        a0 = lam[0] * T + lam[1]
        return min(max(a0, -amax), amax)
    # unreachable: target slides from the constant-deceleration stop point (s = 0) toward the pad
    dp_stop = -0.5 * v * T
    lo = 0.0; hi = 1.0
    lam[0] = 0.0
    lam[1] = dv / T
    best0 = lam[0]; best1 = lam[1]
    for _ in range(14):
        s = 0.5 * (lo + hi)
        lam[0] = best0; lam[1] = best1
        if _cl_newton(dp_stop + s * (dp_full - dp_stop), dv, T, amax, lam) == 1:
            lo = s
            best0 = lam[0]; best1 = lam[1]
        else:
            hi = s
    a0 = best0 * T + best1
    lam[0] = best0; lam[1] = best1
    return min(max(a0, -amax), amax)


@njit(cache=True)
def run6(par, apar, comp, mp, Fg, Dg, tmox, tmf, Pg, ceil, out_rec):
    """Integrate one 6-DOF flight. Returns res[NR]; fills out_rec[k, :NREC] every rec_dt."""
    np.random.seed(int(par[P_seed]))
    dt = par[P_dt]
    g = G0
    prof = int(par[P_profile])
    Fmax = par[P_Fmax]
    floorF = par[P_floor] * Fmax
    tsc = par[P_thrust_scale]
    isc = par[P_isp_scale]
    # v2.7 (ENG-06, review RC-06): in-flight throat-area growth under the ECU Pc loop. At = At0 (1 + g); g grows with
    # the burn as J = int (Pc/Pc_max)^0.68 dt (literature scaling of the erosion rate, Pc ~ command-equivalent thrust)
    # and reaches throat_g at J = throat_jref (the nominal flight's J). The Pc loop holds Pc at the map value of the
    # command, so the delivered thrust per command is x (1 + g)(1 + k_cf g) and the propellant flow x (1 + g) (c* and O/F
    # unchanged, ASSUMED); the flow-limited ceiling changes by (1 + k_cf g) only. k_cf (relative change of the sea-level
    # thrust coefficient per unit g at the eroded expansion ratio) is tabulated at 12.5 / 20 / 60 / 100 % thrust.
    # The flight software does not know g: every F / tsc below is its Pc-based estimate. Off when throat_g <= 0.
    # throat_loop 1 (default) = the ECU holds Pc on the nominal map; 0 = the ECU compensates the throat (thrust per
    # command unchanged, flow / thrust x 1 / (1 + k_cf g)): the bound of what a compensating loop can achieve.
    tsc0 = tsc
    thr_on = par[P_throat_g] > 0.0
    thr_g = 0.0; thr_J = 0.0; thr_kc = 0.0; thr_ff = 1.0
    # v2.7.1-dev (review RC-07): fuel-regression-law band. The oxidiser and fuel flows per thrust of the map are multiplied by
    # phi_ox / phi_f of the run's (a, n), tabulated against X = oxidiser burned at the map flows (gncsim.regband, calibrated
    # on Combustion's band runs of DC-B1 85 m; B-profile scope). Pc per thrust unchanged (< 0.3 % in those runs). Off unless
    # reg_on; liquid depletion still cuts the thrust (no vapour phase: conservative).
    reg_on = par[P_reg_on] > 0.5
    reg_X = 0.0
    S = apar[A_SREF]
    res = np.zeros(NR)
    res[R_min_h_cut] = 99.0
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
    m_tot = mo[0]; zcg = mo[1]; It = mo[2]; Ir = mo[3]; m_e = mo[4]; z_e = mo[5]; I_e = mo[6]; Dp = mo[7]
    z_p = mp[15]
    tank_zb = mp[8]
    tank_A = mp[9]
    tank_R = np.sqrt(tank_A / np.pi)
    # ---------------- states
    r = np.zeros(3); v = np.zeros(3); w = np.zeros(3)
    q = np.array([1.0, 0.0, 0.0, 0.0])
    on_legs = par[P_legs_mode] > 0.5            # 1: legs deployed at t0 (hop from the legs)
    legs_dep = on_legs
    apar[A_LEGS_DEPLOYED] = 1.0 if legs_dep else 0.0
    apar[A_DROGUE_DEPLOYED] = 0.0
    r[2] = zcg - par[P_z_foot]                  # feet (or stand) at ground level
    held = True
    tmode = int(par[P_test_mode])
    if tmode == 1:
        # verification: torque-free rigid body, no gravity, no aero, no thrust
        g = 0.0
        held = False
        r[2] = 1000.0
        w[0] = par[P_w0x]; w[1] = par[P_w0y]; w[2] = par[P_w0z]
    elif tmode == 2:
        # verification: vacuum ballistic flight from (h0, v0z), engine off, no aero
        held = False
        r[2] = par[P_h0]; v[2] = par[P_v0z]
    # slosh
    xs = np.zeros(2); vs = np.zeros(2)
    # gimbal actuators: servo angle/rate, engine angle (after backlash), delay ring buffer
    dsv = np.zeros(2); dsr = np.zeros(2); deng = np.zeros(2); deng_prev = np.zeros(2); dd_prev = np.zeros(2)
    dd = np.zeros(2)
    nbuf = 64
    cbuf = np.zeros((nbuf, 2))
    kdel = int(par[P_gim_delay] / dt + 0.5)
    if kdel > nbuf - 1:
        kdel = nbuf - 1
    ibuf = 0
    dcmd = np.zeros(2)
    gmax = np.radians(par[P_gim_max])
    # truth history for GNSS latency
    nhist = 512
    hist = np.zeros((nhist, 6))
    ihist = 0
    klat = int(par[P_gnss_lat] / dt + 0.5)
    if klat > nhist - 1:
        klat = nhist - 1
    # wind
    wdir = par[P_wind_dir]
    gu = np.zeros(3)
    # IMU errors
    bg = np.array([par[P_g_bx], par[P_g_by], par[P_g_bz]])
    ba = np.array([par[P_a_bx], par[P_a_by], par[P_a_bz]])
    # estimator: initial attitude = truth (vertical) + alignment error
    qe = np.array([1.0, 0.5 * par[P_align_x], 0.5 * par[P_align_y], 0.5 * par[P_align_z]])
    nq = np.sqrt(qe[0] ** 2 + qe[1] ** 2 + qe[2] ** 2 + qe[3] ** 2)
    for i in range(4):
        qe[i] /= nq
    kx = np.zeros((3, 3)); Px = np.zeros((3, 3, 3))
    for a in range(3):
        kx[a, 0] = r[a]
        Px[a, 0, 0] = 0.01; Px[a, 1, 1] = 1e-4; Px[a, 2, 2] = 0.04
    kf_timer = 0.0; gnss_timer = 0.0; lidar_timer = 0.0; baro_timer = 0.0
    acc_meas_sum = np.zeros(3); n_acc = 0
    az_est = 0.0
    # engine / sequencing
    F = 0.0; Fcmd = 0.0; Fc_prev = 0.0
    lit = False; burning = False
    phase = 0 if tmode == 0 else 99
    t = 0.0
    Fa_ = 0.0; Fs_ = 0.0
    phi_f = par[P_fuel_phi]
    t_ign_cmd = -1.0; t5 = -1.0
    hmax = 0.0; prop_used = 0.0
    starts = 0
    burn_time = 0.0
    hs_mode = int(par[P_hslam]); hslam = hs_mode == 1; mode_locked = False; cut = False; hs_armed = False
    k_hat = 1.0
    fl_b = floorF   # v2.7 k_est_asc 2: compensated B-profile floor command (= floorF otherwise)
    ei = 0.0; sat_lo = False; sat_hi = False
    eix = 0.0; eiy = 0.0
    exhausted = False
    td_done = False
    crash = False
    t_td = -1.0
    drogue = False
    nrec = 0; next_rec = 0.0
    tank_timer = 0.0
    Fceil = Fmax
    Fc_avail = Fmax
    vref = 0.0
    # metrics
    max_gim = 0.0; max_gim_rate = 0.0; max_gim_acc = 0.0; max_hinge = 0.0; max_rate_coast = 0.0
    max_rate_desc = 0.0; max_rate_land = 0.0; max_tilt_land = 0.0; max_aoa_asc = 0.0; max_axial = 0.0
    max_lat_eng = 0.0; max_tilt_desc = 0.0; max_q = 0.0; coast_aoa = 0.0; peak_leg = 0.0
    max_gim_raw = 0.0
    max_axial_flt = 0.0; max_lat_flt = 0.0; max_alpha_flt = 0.0
    max_axial_td = 0.0; max_lat_td = 0.0; max_alpha_td = 0.0; max_hinge_td = 0.0
    act_sat_time = 0.0; act_sat_events = 0.0; act_sat_dur = 0.0; act_sat_max_dur = 0.0; act_sat_kmin = 1.0
    act_sat_time_td = 0.0; max_hinge_dem = 0.0; act_prev_sat = False; act_sat_time_land = 0.0
    act_I1 = par[P_act_Irun]; act_I2 = par[P_act_Irun]; act_Vmin = 99.0; act_Imax = 0.0
    rec_ksat = 1.0; rec_mdm = 0.0; rec_vp = 0.0; rec_raw = 0.0; ex = 0.0; ey = 0.0
    act_sat_time_stall = 0.0; act_sat_max_dur_stall = 0.0; act_sat_dur_stall = 0.0
    apiv = np.zeros(2); fz_prev = 0.0
    d_hat = np.zeros(2); tw_e = np.zeros(3); tbm = np.zeros(3)
    dlk = np.zeros(2); der = np.zeros(2); lf = np.zeros(2); lfr = np.zeros(2)
    rlc = np.zeros(2); rlv = np.zeros(2)
    emr = np.zeros(2); em_prev = np.zeros(2); aw_resets = 0.0; aw_time = 0.0
    sat_steps = 0; burn_steps = 0; max_roll = 0.0; max_tilt_asc = 0.0; max_pen = 0.0; max_rate_post = 0.0
    rcs_time = 0.0; rcs_imp = 0.0
    v_ign = 0.0; h_ign = 0.0; act_sat_max_t1 = 0.0; t_relight = 0.0
    apo_x = 0.0; apo_y = 0.0
    relight_ok = 0.0
    tip = False
    hinge_now = 0.0
    keff = 1.0
    # working arrays and scalars (allocation-free loop)
    tb = np.zeros(3); Fb = np.zeros(3); Mb = np.zeros(3); Fw = np.zeros(3); tmp3 = np.zeros(3)
    vrel_w = np.zeros(3); vrel_b = np.zeros(3); Fa = np.zeros(3); Ma = np.zeros(3)
    zb_w = np.zeros(3); fb = np.zeros(3); fimu = np.zeros(3); wm = np.zeros(3); fm = np.zeros(3)
    fw_est = np.zeros(3); n_d = np.zeros(3); n_b = np.zeros(3); zbe = np.zeros(3)
    n_ref = np.zeros(3); n_ref[2] = 1.0; zb_ = np.zeros(3); ez_ = np.zeros(3); ez_[2] = 1.0
    gov_on = False; t_gov = 0.0
    # v2.6 ENG-07d notch on the engine-angle command (ECU firmware Notch2: RBJ peaking EQ of finite depth, biquad at the
    # step rate = ECU tvc_shaping 1 kHz), after the low-pass; off when gim_notch_f <= 0
    nt_on = par[P_gim_notch_f] > 0.0 and par[P_gim_notch_db] < 0.0
    nb0 = 1.0; nb1 = 0.0; nb2 = 0.0; na1 = 0.0; na2 = 0.0
    if nt_on:
        w0_ = 2.0 * np.pi * par[P_gim_notch_f] * dt
        A_ = 10.0 ** (par[P_gim_notch_db] / 40.0)
        al_ = np.sin(w0_) / (2.0 * par[P_gim_notch_q]); c_ = np.cos(w0_)
        a0_ = 1.0 + al_ / A_
        nb0 = (1.0 + al_ * A_) / a0_; nb1 = -2.0 * c_ / a0_; nb2 = (1.0 - al_ * A_) / a0_
        na1 = nb1; na2 = (1.0 - al_ / A_) / a0_
    nz1 = np.zeros(2); nz2 = np.zeros(2)
    tl6 = np.array([par[P_toff_l0], par[P_toff_l1], par[P_toff_l2], par[P_toff_l3], par[P_toff_l4], par[P_toff_l5]])
    tf6 = np.array([0.0, par[P_toff_f1], par[P_toff_f2], par[P_toff_f3], par[P_toff_f4], par[P_toff_f5]])
    toff_on = False; l_r = 0.0; l_a = 0.0; tail_imp = 0.0; td_on = False; t_tdn = 0.0; t90_rl = 0.0
    F_start = 0.0; tail_meas = False
    bvec = np.zeros(3); wxb = np.zeros(3); vf = np.zeros(3); mwv = np.zeros(3); mb_ = np.zeros(3)
    Fws = np.zeros(3); acc = np.zeros(3); Fcb = np.zeros(3); al = np.zeros(3); Ftot = np.zeros(3)
    a_lat = np.zeros(2); lat_hold = np.zeros(2); lam = np.zeros(2)
    alpha_prev = np.zeros(3)
    wa_ = np.zeros(3); wb_ = np.zeros(3)
    cl_timer = 1.0
    Tx = 0.0; Ty = 0.0; Tz = 0.0
    tilt = 0.0; aoa = 0.0; tgo = 5.0; Vair = 0.0; qdyn = 0.0; wwx = 0.0; wwy = 0.0
    leg_f_tot = 0.0
    ms = 0.0
    mox = 0.0; mf_ = 0.0
    h_est = 0.0
    It_est = It
    while t < par[P_tmax]:
        # ================================================================ mass properties
        massprops(mp, ml, mv, rho_l, mfuel, mo)
        m_tot = mo[0]; zcg = mo[1]; It = mo[2]; Ir = mo[3]; m_e = mo[4]; z_e = mo[5]; I_e = mo[6]; Dp = mo[7]
        l_p = zcg - z_p
        l_e = z_p - z_e
        J_twd = I_e + m_e * l_e * (l_e + l_p)
        I_piv = I_e + m_e * l_e * l_e
        It_est = It * (1.0 + par[P_mest])
        # engine ceiling (tank pressure, port) and propellant depletion
        if thr_on:
            fr_ = (Fa_ / tsc) / Fmax if Fa_ > 1.0 else par[P_floor]
            if fr_ <= 0.125:
                thr_kc = par[P_throat_k0]
            elif fr_ <= 0.2:
                thr_kc = par[P_throat_k0] + (par[P_throat_k1] - par[P_throat_k0]) * (fr_ - 0.125) / 0.075
            elif fr_ <= 0.6:
                thr_kc = par[P_throat_k1] + (par[P_throat_k2] - par[P_throat_k1]) * (fr_ - 0.2) / 0.4
            elif fr_ <= 1.0:
                thr_kc = par[P_throat_k2] + (par[P_throat_k3] - par[P_throat_k2]) * (fr_ - 0.6) / 0.4
            else:
                thr_kc = par[P_throat_k3]
            thr_g = par[P_throat_g] * min(1.0, thr_J / par[P_throat_jref])
            if par[P_throat_loop] > 0.5:
                # ECU holds Pc on the nominal map (no throat compensation): more thrust and more flow per command
                tsc = tsc0 * (1.0 + thr_g) * (1.0 + thr_kc * thr_g)
                thr_ff = 1.0 + thr_g
            else:
                # ECU compensates the throat (thrust per command kept): flow per thrust follows the CF change only
                tsc = tsc0
                thr_ff = 1.0 / (1.0 + thr_kc * thr_g)
        Fceil = tsc0 * (1.0 + thr_kc * thr_g) * _bilin(Pg, Dg, ceil, Pt, Dp)
        if Fceil > Fmax * tsc:
            Fceil = Fmax * tsc
        if ml <= resid:
            Fceil = 0.0
            if burning:
                exhausted = True
        Fc_avail = Fceil / tsc
        # ================================================================ environment (truth)
        zb_w[0] = 2.0 * (q[1] * q[3] + q[0] * q[2])
        zb_w[1] = 2.0 * (q[2] * q[3] - q[0] * q[1])
        zb_w[2] = 1.0 - 2.0 * (q[1] * q[1] + q[2] * q[2])
        tilt = np.arccos(min(1.0, max(-1.0, zb_w[2])))
        h_cg = r[2]
        h_ft = max(h_cg, 1.0) / 0.3048
        rho = _rho(h_cg, par[P_rho0])
        Uh = par[P_wind_u] * (max(h_cg, 0.5) / 10.0) ** par[P_wind_alpha]
        cwd = np.cos(wdir); swd = np.sin(wdir)
        wx_ = Uh * cwd; wy_ = Uh * swd
        if par[P_gust_on] > 0.5:
            W20 = par[P_wind_u] * (6.1 / 10.0) ** par[P_wind_alpha]
            sw = 0.1 * W20 * par[P_gust_scale]
            den = (0.177 + 0.000823 * h_ft)
            su = sw / den ** 0.4
            Lw = max(h_ft, 10.0) * 0.3048
            Lu = (max(h_ft, 10.0) / den ** 1.2) * 0.3048
            Vt = np.sqrt((v[0] - wx_) ** 2 + (v[1] - wy_) ** 2 + v[2] ** 2)
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
        wwx = wx_ + gu[0] * cwd - gu[1] * swd
        wwy = wy_ + gu[0] * swd + gu[1] * cwd
        wwz = gu[2] if h_cg > 1.0 else gu[2] * max(h_cg, 0.0)
        vrel_w[0] = v[0] - wwx; vrel_w[1] = v[1] - wwy; vrel_w[2] = v[2] - wwz
        qrotT(q, vrel_w, vrel_b)
        Vair = np.sqrt(vrel_b[0] ** 2 + vrel_b[1] ** 2 + vrel_b[2] ** 2)
        aoa = np.arccos(min(1.0, max(-1.0, vrel_b[2] / Vair))) if Vair > 0.5 else 0.0
        qdyn = 0.5 * rho * Vair * Vair
        if qdyn > max_q:
            max_q = qdyn
        # ================================================================ sensors
        for i in range(3):
            wm[i] = w[i] * (1.0 + par[P_g_sf]) + bg[i] + par[P_g_arw] / np.sqrt(dt) * np.random.normal()
        if held:
            # on the pad the attitude estimate is held (pre-launch alignment); gyro noise ignored
            pass
        else:
            qint(qe, wm, dt)
        vib = par[P_vib_sigma] * (F / Fmax) if F > 1.0 else 0.0
        rz_imu = par[P_z_imu] - zcg
        fimu[0] = fb[0] + alpha_prev[1] * rz_imu + w[0] * w[2] * rz_imu
        fimu[1] = fb[1] - alpha_prev[0] * rz_imu + w[1] * w[2] * rz_imu
        fimu[2] = fb[2] - (w[0] * w[0] + w[1] * w[1]) * rz_imu
        for i in range(3):
            fm[i] = fimu[i] * (1.0 + par[P_a_sf]) + ba[i] + (par[P_a_vrw] / np.sqrt(dt) + vib) * np.random.normal()
            acc_meas_sum[i] += fm[i]
        n_acc += 1
        # truth history for delayed GNSS
        hist[ihist, 0] = r[0]; hist[ihist, 1] = r[1]; hist[ihist, 2] = r[2]
        hist[ihist, 3] = v[0]; hist[ihist, 4] = v[1]; hist[ihist, 5] = v[2]
        jh = ihist - klat
        if jh < 0:
            jh += nhist
        ihist = (ihist + 1) % nhist
        kf_timer += dt
        gnss_timer += dt; lidar_timer += dt; baro_timer += dt
        if kf_timer >= 0.01 - 1e-12:
            for i in range(3):
                tmp3[i] = acc_meas_sum[i] / n_acc
                acc_meas_sum[i] = 0.0
            n_acc = 0
            qrot(qe, tmp3, fw_est)
            fw_est[2] -= g
            az_est = fw_est[2] - kx[2, 2]
            # lateral disturbance (aero side force) estimate: measured specific force minus the modelled
            # thrust specific force (Pc-model thrust x k_hat along the encoder-measured nozzle axis)
            if (phase == 5 or phase == 6) and F > 0.15 * Fmax * tsc and not td_done:
                tbm[0] = np.sin(deng[1]) * np.cos(deng[0]); tbm[1] = -np.sin(deng[0])
                tbm[2] = np.cos(deng[0]) * np.cos(deng[1])
                qrot(qe, tbm, tw_e)
                fth_ = (F / tsc) * k_hat / (m_tot * (1.0 + par[P_mest]))
                for a in range(2):
                    d_hat[a] += (fw_est[a] - fth_ * tw_e[a] - d_hat[a]) * 0.01 / par[P_dff_tau]
            else:
                d_hat[0] = 0.0; d_hat[1] = 0.0
            qa = (par[P_a_vrw] ** 2 + (par[P_vib_sigma] * F / Fmax) ** 2 * dt + 0.03 ** 2) * 4.0
            for a in range(3):
                kf3_predict(kx[a], Px[a], fw_est[a], kf_timer, qa, 1e-4)
            kf_timer = 0.0
            if gnss_timer >= 1.0 / par[P_gnss_rate] - 1e-12:
                gnss_timer = 0.0
                for a in range(3):
                    sp = par[P_gnss_sp_h] if a < 2 else par[P_gnss_sp_v]
                    bsg = par[P_gnss_bsh] if a < 2 else par[P_gnss_bsv]
                    gb = par[P_gnss_bx] if a == 0 else (par[P_gnss_by] if a == 1 else par[P_gnss_bz])
                    kf3_update(kx[a], Px[a], 0, hist[jh, a] + gb + sp * np.random.normal(), sp * sp + bsg * bsg)
                    kf3_update(kx[a], Px[a], 1, hist[jh, 3 + a] + par[P_gnss_sv] * np.random.normal(),
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
                           par[P_baro_sigma] ** 2 + par[P_baro_bsig] ** 2)
        # ================================================================ guidance (estimated state)
        m_est = m_tot * (1.0 + par[P_mest])
        zbe[0] = 2.0 * (qe[1] * qe[3] + qe[0] * qe[2])
        zbe[1] = 2.0 * (qe[2] * qe[3] - qe[0] * qe[1])
        zbe[2] = 1.0 - 2.0 * (qe[1] * qe[1] + qe[2] * qe[2])
        tilt_e = np.arccos(min(1.0, max(-1.0, zbe[2])))
        h_est = kx[2, 0] - (zcg - par[P_z_foot]) * np.cos(tilt_e) + par[P_h_bias_nav]
        vz_e = kx[2, 1]
        a_lat[0] = 0.0; a_lat[1] = 0.0
        tilt_lim = np.radians(par[P_tilt_max_land])
        att_active = True
        use_T = False
        if phase == 0:
            Fcmd = Fmax
            lit = True; burning = True
            starts = 1
            phase = 1
        elif phase == 1:
            Fcmd = Fmax
            a_lat[0] = 0.6 * (par[P_ascent_bias_x] - kx[0, 1])
            a_lat[1] = 0.6 * (par[P_ascent_bias_y] - kx[1, 1])
            tilt_lim = np.radians(par[P_tilt_max_asc])
            if vz_e > 0.5 and not held:
                if prof == 0 and par[P_meco_td] > 0.0 and par[P_toff_model] > 0.5:
                    # v2.6 (lead decision 2026-10-12, ENG-05 with the MKS HV69 pintle drive): throttle down to
                    # meco_td x F_max, hold meco_td_hold, then MECO; the apogee predictor carries the tail-off impulse
                    # of the lift-ramp model (same table as the truth model) and the hold segment
                    k = 0.5 * rho * S * apar[A_CA0_NF] / m_est
                    lag_ = par[P_toff_lag_a] + par[P_toff_lag_c]
                    Ftd_ = par[P_meco_td] * Fmax
                    th_ = par[P_meco_td_hold]
                    if not td_on:
                        a1_ = Ftd_ / m_est - g
                        h1_ = h_est + vz_e * th_ + 0.5 * a1_ * th_ * th_
                        v1_ = vz_e + a1_ * th_ + _tail_imp(Ftd_, tl6, tf6, par[P_toff_vs], lag_) / m_est
                        hap = h1_ + np.log(1.0 + k * v1_ * v1_ / g) / (2.0 * k)
                        if hap >= par[P_h_target]:
                            td_on = True
                            t_tdn = t
                            res[R_t_td_start] = t
                    if td_on:
                        Fcmd = Ftd_
                        Fe_ = F / tsc if F > 1.0 else Ftd_
                        v1_ = vz_e + _tail_imp(Fe_, tl6, tf6, par[P_toff_vs], lag_) / m_est
                        hap = h_est + np.log(1.0 + k * v1_ * v1_ / g) / (2.0 * k)
                        # MECO once the predicted apogee reaches the target AND the measured thrust (Pc) is at or below
                        # meco_td_max x F_max (ENG-05 rule); the thrust gate is waived 2 x hold after the throttle-down
                        # command (apogee accuracy first; the run then records F_meco_cmd above the gate)
                        settled_ = F <= par[P_meco_td_max] * Fmax * tsc or t - t_tdn >= 2.0 * th_
                        if settled_ and hap >= par[P_h_target]:
                            phase = 2
                            lit = False
                            res[R_t_meco] = t; res[R_h_meco] = r[2]; res[R_v_meco] = v[2]
                            res[R_F_meco_cmd] = F
                elif prof == 0:
                    k = 0.5 * rho * S * apar[A_CA0_NF] / m_est
                    if par[P_toff_model] > 0.5:
                        v1_ = vz_e + _tail_imp(F / tsc if F > 1.0 else Fmax, tl6, tf6, par[P_toff_vs],
                                               par[P_toff_lag_a] + par[P_toff_lag_c]) / m_est
                        hap = h_est + np.log(1.0 + k * v1_ * v1_ / g) / (2.0 * k)
                    else:
                        hap = h_est + np.log(1.0 + k * vz_e * vz_e / g) / (2.0 * k) + vz_e * par[P_t_off]
                    if hap >= par[P_h_target]:
                        phase = 2
                        lit = False
                        res[R_t_meco] = t; res[R_h_meco] = r[2]; res[R_v_meco] = v[2]
                        res[R_F_meco_cmd] = F
                else:
                    # option 1: the predictor uses the learnt effectiveness on the (uncompensated) floor; option 2
                    # compensates the floor command, so the delivered floor is nominal (kfl_ = 1)
                    kfl_ = k_hat if (par[P_k_est] > 0.5 and par[P_k_est_asc] > 0.5 and par[P_k_est_asc] < 1.5) else 1.0
                    Fsw = floorF + par[P_slew] * Fmax * par[P_tau]
                    if Fsw > F:
                        Fsw = F
                    t_ramp = (F - Fsw) / (par[P_slew] * Fmax)
                    dv1 = (0.5 * (F + Fsw) / m_est - g) * t_ramp
                    dv2 = ((Fsw - floorF) / m_est) * par[P_tau] + (kfl_ * floorF / m_est - g) * par[P_tau]
                    lagd = t_ramp + par[P_tau]
                    vq = vz_e + dv1 + dv2
                    hq = h_est + 0.5 * (vz_e + vq) * lagd
                    mdf = floorF / (140.0 * G0)
                    mm = m_est
                    geff = g - floorF / mm
                    for _it in range(3):
                        geff = g - kfl_ * floorF / mm
                        if geff < 0.2:
                            geff = 0.2
                        tco = vq / geff
                        mm = m_est - 0.5 * mdf * tco
                    k = 0.5 * rho * S * apar[A_CA0_NF] / mm
                    hap = hq + np.log(1.0 + k * vq * vq / geff) / (2.0 * k)
                    if hap >= par[P_h_target]:
                        phase = 2
                        res[R_t_meco] = t; res[R_h_meco] = r[2]; res[R_v_meco] = v[2]
        if phase == 2 or phase == 3:
            if prof == 1:
                kc_ = 1.0
                if par[P_k_est] > 0.5 and par[P_k_est_asc] > 1.5:
                    # v2.7 k_est_asc 2: the open-loop floor and top-up commands are divided by the learnt thrust
                    # effectiveness (bounded to [0.8, 1.25]); the compensated floor is not allowed below floor_comp_min
                    kc_ = min(1.25, max(0.8, k_hat))
                fl_b = floorF / kc_
                if par[P_k_est_asc] > 1.5 and fl_b < par[P_floor_comp_min] * Fmax:
                    fl_b = par[P_floor_comp_min] * Fmax
                Fcmd = fl_b
                if phase == 2 and vz_e > 0.0:
                    kfl2_ = k_hat if (par[P_k_est] > 0.5 and par[P_k_est_asc] > 0.5 and par[P_k_est_asc] < 1.5) else 1.0
                    geff = g - kfl2_ * floorF / m_est
                    if geff < 0.2:
                        geff = 0.2
                    hap_now = h_est + vz_e * vz_e / (2.0 * geff)
                    if hap_now < par[P_h_target] - 0.5:
                        Fcmd = (floorF + m_est * 0.08 * (par[P_h_target] - hap_now)) / kc_
                a_lat[0] = 0.06 * (par[P_target_x] - kx[0, 0]) - 0.6 * kx[0, 1]
                a_lat[1] = 0.06 * (par[P_target_y] - kx[1, 0]) - 0.6 * kx[1, 1]
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
                if ad < a_term_ + 0.5:
                    ad = a_term_ + 0.5
                vt = np.sqrt(par[P_vt] ** 2 + 2.0 * a_term_ * par[P_ht])
                vi = vz_e + az_est * lag
                hi = h_est + vz_e * lag + 0.5 * az_est * lag * lag
                htrig = (vi * vi - vt * vt) / (2.0 * ad) + par[P_ht]
                if hi <= htrig and vi < 0.0:
                    mode_locked = True
                    if prof == 0:
                        phase = 4
                        t_ign_cmd = t
                        v_ign = v[2]
                        h_ign = h_est
                        t_relight = t
                        legs_dep = True
                        apar[A_LEGS_DEPLOYED] = 1.0
                    else:
                        phase = 5
                        t5 = t
                        v_ign = v[2]
                        h_ign = h_est
                        t_relight = t
        if phase == 4:
            Fcmd = floorF
            if par[P_relight_start_frac] * Fmax > Fcmd:
                Fcmd = par[P_relight_start_frac] * Fmax
            F_start = Fcmd
            att_active = False
            if t - t_ign_cmd >= par[P_t_ign]:
                lit = True; burning = True
                starts += 1
                F = 0.05 * Fmax * tsc
                Fa_ = F; Fs_ = F
                phase = 5
                t5 = t
        if phase == 5 or phase == 6:
            use_T = True
            if t90_rl == 0.0 and F >= 0.9 * F_start * tsc and F_start > 0.0:
                t90_rl = t - t_ign_cmd
                res[R_t90_relight] = t90_rl
                res[R_F_start_cmd] = F_start
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
            go5 = h_est > hg and phase == 5
            tz = 0.0
            if go5 and par[P_vert_mode] > 0.5:
                # ZEM/ZEV to the gate (h = hg, v = -vg) (sim6 v2.3): time-to-go re-estimated every step from the
                # planned deceleration, tgo = (|vz| - vg) / ad; the terminal law takes over when tgo < t_hand.
                # (v2.2 used a fixed final time from burn start with a 0.3 s floor: with the floor active the law
                # has an equilibrium hover at dh = vg tz / 3 above the gate and burned the load; kept as evidence.)
                tz = (-vz_e - vg) / ad
                if tz < par[P_t_hand]:
                    go5 = False
            if go5:
                vref = -np.sqrt(vg * vg + 2.0 * ad * (h_est - hg))
                aref = ad * vz_e / vref
                tgo = (-vref - vg) / ad
                if par[P_vert_mode] > 0.5:
                    zem = hg - (h_est + vz_e * tz)
                    zev = -vg - vz_e
                    aref = 6.0 * zem / (tz * tz) - 2.0 * zev / tz
                    vref = vz_e
                    tgo = tz
            else:
                if phase == 5:
                    ei = 0.0
                phase = 6
                vref = -np.sqrt(vtd * vtd + 2.0 * a_term * hh)
                aref = a_term * vz_e / vref
                tgo = 2.0 * hh / (-vref + vtd)
            if aref < 0.0 and par[P_vert_mode] < 0.5:
                aref = 0.0
            if vz_e < -1.0:
                hs_armed = True
            if hslam and hs_armed and vz_e > -par[P_hcut] and not td_done:
                cut = True; lit = False; phase = 7
                res[R_min_h_cut] = r[2] - (zcg - par[P_z_foot])
            ev = vref - vz_e
            if not ((sat_hi and ev > 0.0) or (sat_lo and ev < 0.0)):
                ei += ev * dt
            ki = 0.6 * par[P_kv]
            if ki * ei > 3.0:
                ei = 3.0 / ki
            if ki * ei < -3.0:
                ei = -3.0 / ki
            az = aref + par[P_kv] * ev + ki * ei
            # ---- lateral guidance
            if phase == 5:
                tg = tgo if tgo > 0.5 else 0.5
                az_th = g + az
                if az_th < g:
                    az_th = g
                almax = az_th * np.tan(tilt_lim) * 0.8
                # reachable target (all laws): constant-deceleration stopping point p + v tg / 2, moved toward
                # the pad by at most the bang-bang divert distance of the remaining lateral authority
                vh_ = np.sqrt(kx[0, 1] ** 2 + kx[1, 1] ** 2)
                arem = almax - vh_ / tg
                if arem < 0.0:
                    arem = 0.0
                rdiv = 0.25 * arem * tg * tg * par[P_div_margin]
                px_ = kx[0, 0] + 0.5 * kx[0, 1] * tg; py_ = kx[1, 0] + 0.5 * kx[1, 1] * tg
                ddx = par[P_target_x] - px_; ddy = par[P_target_y] - py_
                dn = np.sqrt(ddx * ddx + ddy * ddy)
                tx_ = par[P_target_x]; ty_ = par[P_target_y]
                if dn > rdiv and dn > 1e-9:
                    tx_ = px_ + ddx * rdiv / dn; ty_ = py_ + ddy * rdiv / dn
                if par[P_lat_mode] < 0.5:
                    # PD with bounded outer-loop bandwidth (time-scale separation from the attitude loop)
                    wl = par[P_lat_wn]
                    zl = par[P_lat_zeta]
                    a_lat[0] = wl * wl * (tx_ - kx[0, 0]) - 2.0 * zl * wl * kx[0, 1]
                    a_lat[1] = wl * wl * (ty_ - kx[1, 0]) - 2.0 * zl * wl * kx[1, 1]
                elif par[P_lat_mode] < 1.5:
                    # ZEM/ZEV (unconstrained minimum-energy), horizon floor bounds the gains
                    tgz = tg if tg > par[P_t_hmin] else par[P_t_hmin]
                    a_lat[0] = 6.0 * (tx_ - (kx[0, 0] + kx[0, 1] * tgz)) / (tgz * tgz) + 2.0 * kx[0, 1] / tgz
                    a_lat[1] = 6.0 * (ty_ - (kx[1, 0] + kx[1, 1] * tgz)) / (tgz * tgz) + 2.0 * kx[1, 1] / tgz
                else:
                    # convex-lite: box-constrained minimum-energy divert to the same reachable target,
                    # re-solved at 10 Hz (receding horizon with floor t_hmin)
                    cl_timer += dt
                    if cl_timer >= 0.1 - 1e-12:
                        cl_timer = 0.0
                        th_ = tg if tg > par[P_t_hmin] else par[P_t_hmin]
                        # per-axis boxes aligned with the unconstrained (ZEM/ZEV) demand, |w| = 1, floor 0.2,
                        # so the box corner lies on the circular tilt limit (v2.1; v2.0 used amax/sqrt 2)
                        a0x = 6.0 * (tx_ - kx[0, 0] - kx[0, 1] * th_) / (th_ * th_) + 2.0 * kx[0, 1] / th_
                        a0y = 6.0 * (ty_ - kx[1, 0] - kx[1, 1] * th_) / (th_ * th_) + 2.0 * kx[1, 1] / th_
                        a0n = np.sqrt(a0x * a0x + a0y * a0y)
                        wx_ = 0.70710678; wy_ = 0.70710678
                        if a0n > 1e-6:
                            wx_ = max(abs(a0x) / a0n, 0.2); wy_ = max(abs(a0y) / a0n, 0.2)
                            wn_ = np.sqrt(wx_ * wx_ + wy_ * wy_)
                            wx_ /= wn_; wy_ /= wn_
                        lat_hold[0] = convex_lite_a0(kx[0, 0], kx[0, 1], tx_, th_, almax * wx_, lam)
                        lat_hold[1] = convex_lite_a0(kx[1, 0], kx[1, 1], ty_, th_, almax * wy_, lam)
                    a_lat[0] = lat_hold[0]; a_lat[1] = lat_hold[1]
            else:
                a_lat[0] = -par[P_kt_lat] * kx[0, 1]
                a_lat[1] = -par[P_kt_lat] * kx[1, 1]
                # terminal tilt limit: tilt_term_hi at the gate tapering to tilt_term below 1 m (touchdown <= 5 deg)
                fr_ = (h_est - 1.0) / max(hg - 1.0, 0.1)
                if fr_ < 0.0:
                    fr_ = 0.0
                if fr_ > 1.0:
                    fr_ = 1.0
                tilt_lim = np.radians(par[P_tilt_term] + (par[P_tilt_term_hi] - par[P_tilt_term]) * fr_)
            if par[P_dff] > 0.5:
                a_lat[0] -= d_hat[0]
                a_lat[1] -= d_hat[1]
            # thrust vector (world): T = m (a_d + g) minus drag feed-forward (nominal drag model)
            Tz = m_est * (g + az)
            Tz -= 0.5 * 1.2 * par[P_drag_cda_nom] * vz_e * vz_e
            if Tz < 0.0:
                Tz = 0.0
            Tx = m_est * a_lat[0]; Ty = m_est * a_lat[1]
            Th = np.sqrt(Tx * Tx + Ty * Ty)
            if Tz > 1.0 and Th > Tz * np.tan(tilt_lim):
                sc = Tz * np.tan(tilt_lim) / Th
                Tx *= sc; Ty *= sc
            Fcmd = np.sqrt(Tx * Tx + Ty * Ty + Tz * Tz) / keff
            if par[P_relight_start_frac] > 0.0 and t90_rl == 0.0 and F_start > 0.0 and Fcmd < F_start:
                # v2.6 relight rule: hold the start level until the start is established (90 % of it), then throttle
                Fcmd = F_start
            if phase == 7:
                Fcmd = 0.0
        if phase == 7 or td_done:
            Fcmd = 0.0
            lit = False
        # ---------------- attitude command: desired thrust direction n_d (world)
        if use_T:
            nn = np.sqrt(Tx * Tx + Ty * Ty + Tz * Tz)
            if nn > 1e-6:
                n_d[0] = Tx / nn; n_d[1] = Ty / nn; n_d[2] = Tz / nn
            else:
                n_d[0] = 0.0; n_d[1] = 0.0; n_d[2] = 1.0
        else:
            # vertical reference G0 (= g in flight; test mode 1 runs with g = 0 and must not divide by it)
            ax_ = a_lat[0]; ay_ = a_lat[1]
            th_ = np.sqrt(ax_ * ax_ + ay_ * ay_) / G0
            if th_ > np.tan(tilt_lim):
                ax_ *= np.tan(tilt_lim) / th_; ay_ *= np.tan(tilt_lim) / th_
            nn = np.sqrt(ax_ * ax_ + ay_ * ay_ + G0 * G0)
            n_d[0] = ax_ / nn; n_d[1] = ay_ / nn; n_d[2] = G0 / nn
        if par[P_att_ref_rate] > 0.0:
            # v2.6 reference governor on the attitude command: while the attitude loop runs, the commanded thrust
            # direction moves toward the guidance demand n_d at no more than att_ref_rate; otherwise it follows the
            # estimated body axis, so the loop starts from the current attitude (no step at relight / activation)
            fe_ = (F / tsc if F > 1.0 else 0.0) * keff
            if att_active and lit and (not held) and fe_ > 0.2 * floorF:
                if not gov_on:
                    gov_on = True
                    t_gov = t
                rg_ = par[P_att_ref_rate]
                if par[P_att_ref_win] > 0.0 and t - t_gov > par[P_att_ref_win]:
                    rg_ = par[P_att_ref_rate2]
                if par[P_att_ref_mode] > 0.5:
                    # v2.6 ratchet (att_ref_mode 1): the reference is never farther from the guidance demand than the
                    # estimated body axis. If the body is closer (a vehicle still rotating from the free-fall tumble swings
                    # through the demand after relight), the reference restarts from the body axis, so the loop is not
                    # commanded back toward the attitude it had when the governor started.
                    qrot(qe, ez_, zb_)
                    cb_ = zb_[0] * n_d[0] + zb_[1] * n_d[1] + zb_[2] * n_d[2]
                    cr_ = n_ref[0] * n_d[0] + n_ref[1] * n_d[1] + n_ref[2] * n_d[2]
                    if cb_ > cr_:
                        for i_ in range(3):
                            n_ref[i_] = zb_[i_]
                cph_ = n_ref[0] * n_d[0] + n_ref[1] * n_d[1] + n_ref[2] * n_d[2]
                if cph_ > 1.0:
                    cph_ = 1.0
                if cph_ < -1.0:
                    cph_ = -1.0
                ph_ = np.arccos(cph_)
                st_ = np.radians(rg_) * dt
                if ph_ > st_ and ph_ > 1e-9:
                    sp_ = np.sin(ph_)
                    a_ = np.sin(ph_ - st_) / sp_; b_ = np.sin(st_) / sp_
                    for i_ in range(3):
                        n_ref[i_] = a_ * n_ref[i_] + b_ * n_d[i_]
                else:
                    for i_ in range(3):
                        n_ref[i_] = n_d[i_]
                nr_ = np.sqrt(n_ref[0] * n_ref[0] + n_ref[1] * n_ref[1] + n_ref[2] * n_ref[2])
                for i_ in range(3):
                    n_ref[i_] /= nr_
            else:
                gov_on = False
                qrot(qe, ez_, zb_)
                for i_ in range(3):
                    n_ref[i_] = zb_[i_]
            qrotT(qe, n_ref, n_b)
        else:
            qrotT(qe, n_d, n_b)
        ex = -n_b[1]
        ey = n_b[0]
        F_est = (F / tsc if F > 1.0 else 0.0) * keff
        lp_est = l_p - par[P_zcg_err]
        wn_a = par[P_att_wn_asc] if phase == 1 else par[P_att_wn]
        za = par[P_att_zeta]
        if att_active and lit and (not held) and F_est > 0.2 * floorF:
            eix += ex * dt
            eiy += ey * dt
            Mx = It_est * (wn_a * wn_a * ex - 2.0 * za * wn_a * wm[0] + par[P_att_ki] * eix)
            My = It_est * (wn_a * wn_a * ey - 2.0 * za * wn_a * wm[1] + par[P_att_ki] * eiy)
            den_ = F_est * lp_est
            dcx = -Mx / den_
            dcy = -My / den_
            dm = np.sqrt(dcx * dcx + dcy * dcy)
            rec_raw = dm
            if dm > max_gim_raw:
                max_gim_raw = dm
            if par[P_gim_lpf_w] > 0.0 or par[P_gim_cmd_rate] > 0.0:
                # pre-limit the raw command at 2 x gim_max so the shaping states stay bounded
                if dm > 2.0 * gmax:
                    dcx *= 2.0 * gmax / dm; dcy *= 2.0 * gmax / dm
            if par[P_gim_cmd_rate] > 0.0 and par[P_gim_cmd_acc] > 0.0:
                # v2.6: rate- AND acceleration-limited command tracker ahead of the low-pass (time-optimal braking
                # law per axis): the commanded engine acceleration never exceeds gim_cmd_acc, so the servo pair is
                # not asked for more moment than the worst-case inertia (engine + reflected rotor) allows
                vmax_ = np.radians(par[P_gim_cmd_rate]); amax_ = np.radians(par[P_gim_cmd_acc])
                for a in range(2):
                    e_ = (dcx if a == 0 else dcy) - rlc[a]
                    vd_ = np.sqrt(2.0 * amax_ * abs(e_))
                    if vd_ > abs(e_) / dt:
                        vd_ = abs(e_) / dt
                    if vd_ > vmax_:
                        vd_ = vmax_
                    if e_ < 0.0:
                        vd_ = -vd_
                    dv_ = vd_ - rlv[a]
                    if dv_ > amax_ * dt:
                        dv_ = amax_ * dt
                    if dv_ < -amax_ * dt:
                        dv_ = -amax_ * dt
                    rlv[a] += dv_
                    rlc[a] += rlv[a] * dt
                dcx = rlc[0]; dcy = rlc[1]
                dm = np.sqrt(dcx * dcx + dcy * dcy)
            elif par[P_gim_cmd_rate] > 0.0:
                # command slew-rate limit ahead of the low-pass (bounds the gimbal acceleration and hinge moment)
                rmax_ = np.radians(par[P_gim_cmd_rate]) * dt
                ddx_ = dcx - rlc[0]; ddy_ = dcy - rlc[1]
                if ddx_ > rmax_:
                    ddx_ = rmax_
                if ddx_ < -rmax_:
                    ddx_ = -rmax_
                if ddy_ > rmax_:
                    ddy_ = rmax_
                if ddy_ < -rmax_:
                    ddy_ = -rmax_
                rlc[0] += ddx_; rlc[1] += ddy_
                dcx = rlc[0]; dcy = rlc[1]
                dm = np.sqrt(dcx * dcx + dcy * dcy)
            if par[P_gim_lpf_w] > 0.0:
                # structural low-pass on the gimbal command (CSI: engine rocking mode / tail-wags-dog)
                wf_ = par[P_gim_lpf_w]; zf_ = par[P_gim_lpf_z]
                lfr[0] += (wf_ * wf_ * (dcx - lf[0]) - 2.0 * zf_ * wf_ * lfr[0]) * dt
                lfr[1] += (wf_ * wf_ * (dcy - lf[1]) - 2.0 * zf_ * wf_ * lfr[1]) * dt
                lf[0] += lfr[0] * dt; lf[1] += lfr[1] * dt
                dcx = lf[0]; dcy = lf[1]
                dm = np.sqrt(dcx * dcx + dcy * dcy)
            if nt_on:
                yx_ = nb0 * dcx + nz1[0]
                nz1[0] = nb1 * dcx - na1 * yx_ + nz2[0]; nz2[0] = nb2 * dcx - na2 * yx_
                yy_ = nb0 * dcy + nz1[1]
                nz1[1] = nb1 * dcy - na1 * yy_ + nz2[1]; nz2[1] = nb2 * dcy - na2 * yy_
                dcx = yx_; dcy = yy_
                dm = np.sqrt(dcx * dcx + dcy * dcy)
            if par[P_gim_aw_thr] > 0.0:
                # v2.6: encoder-referenced re-initialisation of the shaping chain (ECU, AS5048A on each pivot axis):
                # when the shaped command leads the measured engine angle by more than gim_aw_thr, the tracker and
                # low-pass states restart from the measured engine angle and rate, so the servo is never asked to
                # chase a reference it cannot reach (anti-windup of the actuator command); integrator frozen
                aw_ = False
                for a in range(2):
                    thm_ = deng[a] if par[P_gim_enc_q] <= 0.0 else np.round(deng[a] / par[P_gim_enc_q]) * par[P_gim_enc_q]
                    if abs((dcx if a == 0 else dcy) - thm_) > np.radians(par[P_gim_aw_thr]):
                        rlc[a] = thm_; rlv[a] = emr[a]; lf[a] = thm_; lfr[a] = emr[a]
                        aw_ = True
                if aw_:
                    aw_resets += 1.0
                    aw_time += dt
                    eix -= ex * dt; eiy -= ey * dt
                    if par[P_gim_lpf_w] > 0.0:
                        dcx = lf[0]; dcy = lf[1]
                    else:
                        dcx = rlc[0]; dcy = rlc[1]
                    dm = np.sqrt(dcx * dcx + dcy * dcy)
            if dm > gmax:
                dcx *= gmax / dm; dcy *= gmax / dm
                eix -= ex * dt; eiy -= ey * dt          # anti-windup (freeze integrator)
                sat_steps += 1
            burn_steps += 1
            if par[P_roll_comp_tau] != 0.0:
                # roll-rate compensation: the body turns by w_z tau_c between command and effect
                # (delay + structural filter + servo lag); rotate the command by -w_z tau_c
                ph_ = -wm[2] * par[P_roll_comp_tau]
                c_ = np.cos(ph_); s_ = np.sin(ph_)
                t_ = c_ * dcx - s_ * dcy
                dcy = s_ * dcx + c_ * dcy
                dcx = t_
            dcmd[0] = dcx; dcmd[1] = dcy
        else:
            eix = 0.0; eiy = 0.0
            # v2.2: loop inactive (pad, coast, ignition transient, after touchdown): the command returns to
            # neutral THROUGH the shaping chain (slew limit + low-pass) instead of stepping to zero
            # (v2.1 reset the states: the step produced hinge-moment spikes at MECO and touchdown)
            dcx = 0.0; dcy = 0.0
            if par[P_gim_cmd_rate] > 0.0 and par[P_gim_cmd_acc] > 0.0:
                vmax_ = np.radians(par[P_gim_cmd_rate]); amax_ = np.radians(par[P_gim_cmd_acc])
                for a in range(2):
                    e_ = -rlc[a]
                    vd_ = np.sqrt(2.0 * amax_ * abs(e_))
                    if vd_ > abs(e_) / dt:
                        vd_ = abs(e_) / dt
                    if vd_ > vmax_:
                        vd_ = vmax_
                    if e_ < 0.0:
                        vd_ = -vd_
                    dv_ = vd_ - rlv[a]
                    if dv_ > amax_ * dt:
                        dv_ = amax_ * dt
                    if dv_ < -amax_ * dt:
                        dv_ = -amax_ * dt
                    rlv[a] += dv_
                    rlc[a] += rlv[a] * dt
                dcx = rlc[0]; dcy = rlc[1]
            elif par[P_gim_cmd_rate] > 0.0:
                rmax_ = np.radians(par[P_gim_cmd_rate]) * dt
                for a in range(2):
                    dd_ = -rlc[a]
                    if dd_ > rmax_:
                        dd_ = rmax_
                    if dd_ < -rmax_:
                        dd_ = -rmax_
                    rlc[a] += dd_
                dcx = rlc[0]; dcy = rlc[1]
            if par[P_gim_lpf_w] > 0.0:
                wf_ = par[P_gim_lpf_w]; zf_ = par[P_gim_lpf_z]
                lfr[0] += (wf_ * wf_ * (dcx - lf[0]) - 2.0 * zf_ * wf_ * lfr[0]) * dt
                lfr[1] += (wf_ * wf_ * (dcy - lf[1]) - 2.0 * zf_ * wf_ * lfr[1]) * dt
                lf[0] += lfr[0] * dt; lf[1] += lfr[1] * dt
                dcx = lf[0]; dcy = lf[1]
            if nt_on:
                yx_ = nb0 * dcx + nz1[0]
                nz1[0] = nb1 * dcx - na1 * yx_ + nz2[0]; nz2[0] = nb2 * dcx - na2 * yx_
                yy_ = nb0 * dcy + nz1[1]
                nz1[1] = nb1 * dcy - na1 * yy_ + nz2[1]; nz2[1] = nb2 * dcy - na2 * yy_
                dcx = yx_; dcy = yy_
            dcmd[0] = dcx; dcmd[1] = dcy
        # roll RCS (bang-bang on measured roll rate)
        Mrcs = 0.0
        if par[P_rcs_on] > 0.5 and not held and not td_done:
            if wm[2] > par[P_rcs_deadband]:
                Mrcs = -par[P_rcs_torque]
            elif wm[2] < -par[P_rcs_deadband]:
                Mrcs = par[P_rcs_torque]
            if Mrcs != 0.0:
                rcs_time += dt
                rcs_imp += abs(Mrcs) * dt
        # ================================================================ engine
        if lit and burning:
            fl_ = floorF
            if par[P_k_est_asc] > 1.5 and prof == 1 and (phase == 2 or phase == 3):
                fl_ = fl_b
            sat_lo = Fcmd <= fl_
            sat_hi = Fcmd >= Fc_avail
            if Fcmd < fl_:
                Fcmd = fl_
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
            dF = (Ftgt - Fa_) / par[P_tau] * dt
            lim = par[P_slew] * Fmax * dt
            if dF > lim:
                dF = lim
            if dF < -lim:
                dF = -lim
            Fa_ += dF
            if phi_f > 0.0:
                # open-loop pintle: fraction phi of the static gain follows the fuel (solid-phase) lag
                Fs_ += (Fa_ - Fs_) / par[P_tau_fuel] * dt
                F = (1.0 - phi_f) * Fa_ + phi_f * Fs_
            else:
                Fs_ = Fa_
                F = Fa_
            burn_time += dt
        elif par[P_toff_model] > 0.5:
            # v2.6 shutdown on the pintle lift ramp (Combustion actuator_rate_check_v2, MKS HV69 ~0.25 s full stroke):
            # lift command closes at toff_vs, actuator lag toff_lag_a, quasi-static thrust on the lift-thrust table,
            # chamber lag toff_lag_c
            if not toff_on and Fa_ > 0.5:
                toff_on = True
                l_r = _interp6(Fa_ / tsc, tf6, tl6); l_a = l_r
                tail_imp = 0.0; tail_meas = True
            if toff_on:
                l_r -= par[P_toff_vs] * dt
                if l_r < 0.0:
                    l_r = 0.0
                l_a += (l_r - l_a) * dt / max(par[P_toff_lag_a], dt)
                Fq_ = tsc * _interp6(l_a, tl6, tf6)
                Fa_ += (Fq_ - Fa_) * dt / max(par[P_toff_lag_c], dt)
                Fs_ += (Fq_ - Fs_) * dt / max(par[P_toff_lag_c], dt)
            F = (1.0 - phi_f) * Fa_ + phi_f * Fs_
            if tail_meas:
                tail_imp += F * dt
            if F < 0.5:
                F = 0.0; Fa_ = 0.0; Fs_ = 0.0
                if toff_on:
                    toff_on = False
                    if tail_meas and phase >= 2 and res[R_tailoff_imp] == 0.0:
                        res[R_tailoff_imp] = tail_imp
                    tail_meas = False
            if not lit and F == 0.0:
                burning = False
        else:
            Fa_ += (0.0 - Fa_) / par[P_t_off] * dt
            Fs_ += (0.0 - Fs_) / par[P_t_off] * dt
            F = (1.0 - phi_f) * Fa_ + phi_f * Fs_
            if F < 0.5:
                F = 0.0; Fa_ = 0.0; Fs_ = 0.0
            if not lit and F == 0.0:
                burning = False
        if F < 0.0:
            F = 0.0
        mox = 0.0; mf_ = 0.0
        if F > 0.0 and ml > resid:
            mox = _bilin(Fg, Dg, tmox, F / tsc, Dp) / isc * thr_ff
            mf_ = _bilin(Fg, Dg, tmf, F / tsc, Dp) / isc * thr_ff
            if reg_on:
                ph_o = _reg_phi(par, reg_X, P_reg_o0)
                ph_u = _reg_phi(par, reg_X, P_reg_u0)
                reg_X += mox * dt
                mox = mox * ph_o
                mf_ = mf_ * ph_u
            if thr_on:
                thr_J += (F / tsc / Fmax) ** 0.68 * dt
        elif F > 0.0:
            F = 0.0; Fa_ = 0.0; Fs_ = 0.0
        # ================================================================ gimbal actuators
        cbuf[ibuf, 0] = dcmd[0]; cbuf[ibuf, 1] = dcmd[1]
        jb = ibuf - kdel
        if jb < 0:
            jb += nbuf
        ibuf = (ibuf + 1) % nbuf
        wn_g = par[P_gim_wn]; zg_ = par[P_gim_zeta]
        hinge_now = 0.0
        hb = 0.5 * np.radians(par[P_gim_backlash])
        dbd = np.radians(par[P_gim_deadband])
        # crank-linkage nonlinearity (mechanical.json v1 kinematics): servo angle psi = asin(n |delta|) on the
        # worst-loaded servo; engine-side rate scales with cos(psi), engine-side torque with 1/cos(psi)
        cpsi = 1.0
        if par[P_gim_n] > 0.0:
            sp_ = par[P_gim_n] * np.sqrt(dsv[0] * dsv[0] + dsv[1] * dsv[1])
            if sp_ > 0.95:
                sp_ = 0.95
            cpsi = np.sqrt(1.0 - sp_ * sp_)
        stall_e = par[P_gim_stall_engine] / cpsi
        for a in range(2):
            u = cbuf[jb, a]
            if abs(u - dsv[a]) < dbd:
                u = dsv[a]
            acc_s = wn_g * wn_g * (u - dsv[a]) - 2.0 * zg_ * wn_g * dsr[a]
            # linear torque-speed motor (engine side): T_motor <= T_stall (1 - |w|/w_nl) when driving,
            # <= T_stall when braking; T_motor = I_piv acc + T_ext (hose + friction)
            t_static = par[P_hose_K] * abs(deng[a]) + par[P_gim_fric] * (F / Fmax)
            w_nl = np.radians(par[P_gim_rate_nl]) * cpsi
            if acc_s * dsr[a] > 0.0:
                t_av = stall_e * (1.0 - abs(dsr[a]) / w_nl)
            else:
                t_av = stall_e
            if par[P_act_model] < 0.5:
                acc_lim = (t_av - t_static) / max(I_piv, 1e-4)
                if acc_lim < 0.0:
                    acc_lim = 0.0
                if acc_s > acc_lim:
                    acc_s = acc_lim
                elif acc_s < -acc_lim:
                    acc_s = -acc_lim
            dsr[a] += acc_s * dt
            hl_a = abs(I_piv * (acc_s + alpha_prev[a])) + t_static
            if par[P_act_model] < 0.5:
                # speed limit under the external load (no-load speed on the torque-speed line)
                rl = w_nl * (1.0 - t_static / stall_e)
                if rl < np.radians(5.0):
                    rl = np.radians(5.0)
                if dsr[a] > rl:
                    dsr[a] = rl
                if dsr[a] < -rl:
                    dsr[a] = -rl
            dsv[a] += dsr[a] * dt
            if par[P_gim_stop] <= 0.0:
                if dsv[a] > gmax * 1.05:
                    dsv[a] = gmax * 1.05; dsr[a] = 0.0
                if dsv[a] < -gmax * 1.05:
                    dsv[a] = -gmax * 1.05; dsr[a] = 0.0
            if hl_a > hinge_now:
                hinge_now = hl_a
        if par[P_gim_stop] > 0.0:
            # conical mechanical stop on the engine vector (mechanical.json: 8 deg polyurethane bumper)
            gs_ = np.radians(par[P_gim_stop])
            vm_ = np.sqrt(dsv[0] * dsv[0] + dsv[1] * dsv[1])
            if vm_ > gs_:
                for a in range(2):
                    dsv[a] *= gs_ / vm_
                    dsr[a] = 0.0
        for a in range(2):
            # backlash: dead zone between the servo output and the linkage
            if dsv[a] - dlk[a] > hb:
                dlk[a] = dsv[a] - hb
            elif dlk[a] - dsv[a] > hb:
                dlk[a] = dsv[a] + hb
        if par[P_rock_K] > 0.0:
            # flexible engine mount (v2.1): engine angle driven by the linkage through the axis stiffness and a
            # damper (rocking mode sqrt(K / I_piv)); hose spring on the engine; conical stop on the engine vector
            Kr = par[P_rock_K]
            cr = 2.0 * par[P_rock_zeta] * np.sqrt(Kr * max(I_piv, 1e-4))
            hinge_now = 0.0
            tq0_ = 0.0; tq1_ = 0.0
            for a in range(2):
                lr = dsr[a] if abs(dsv[a] - dlk[a]) >= hb - 1e-12 else 0.0
                if a == 0:
                    tq0_ = Kr * (dlk[a] - deng[a]) + cr * (lr - der[a])
                else:
                    tq1_ = Kr * (dlk[a] - deng[a]) + cr * (lr - der[a])
            Ie_ = max(I_piv, 1e-4)
            if par[P_act_model] > 0.5:
                # v2.5: servo pair on its torque-speed lines through the Cardan kinematics; friction opposes the motion
                ffr = par[P_gim_fric] * (F / Fmax)
                fr0 = 0.0; fr1 = 0.0
                if der[0] > 1e-4:
                    fr0 = ffr
                elif der[0] < -1e-4:
                    fr0 = -ffr
                if der[1] > 1e-4:
                    fr1 = ffr
                elif der[1] < -1e-4:
                    fr1 = -ffr
                md0 = tq0_ + fr0; md1 = tq1_ + fr1
                if par[P_act_sag] > 0.5:
                    # servo plug voltages from the previous step's supply currents (Electronics tvc_supply_budget_v1
                    # chain: shared source R_s carries both servos + other loads, TVC common path R_c both servos,
                    # branch R_b one servo); one-step lag closes the algebraic loop (contraction, slope ~ -R dI/dV)
                    vsh_ = par[P_act_Vrest] - (act_I1 + act_I2 + par[P_act_Io]) * par[P_act_Rs] - (act_I1 + act_I2) * par[P_act_Rc]
                    Vp1 = vsh_ - act_I1 * par[P_act_Rb]
                    Vp2 = vsh_ - act_I2 * par[P_act_Rb]
                    Ts1_, wn1_ = servo_TV(Vp1, par[P_act_V0], par[P_act_V1], par[P_act_V2], par[P_act_T0], par[P_act_T1],
                                          par[P_act_T2], par[P_act_s0], par[P_act_s1], par[P_act_s2])
                    Ts2_, wn2_ = servo_TV(Vp2, par[P_act_V0], par[P_act_V1], par[P_act_V2], par[P_act_T0], par[P_act_T1],
                                          par[P_act_T2], par[P_act_s0], par[P_act_s1], par[P_act_s2])
                else:
                    Vp1 = 0.0; Vp2 = 0.0
                    Ts1_ = par[P_act_Ts]; Ts2_ = par[P_act_Ts]; wn1_ = par[P_act_wnl]; wn2_ = par[P_act_wnl]
                ksat, Tsv1, Tsv2, kstall = act_scale(deng[0], deng[1], der[0], der[1], md0, md1, par[P_act_az1],
                                                     par[P_act_az2], par[P_act_re], par[P_act_zb], par[P_act_rh], Ts1_,
                                                     wn1_, Ts2_, wn2_)
                if lit and not td_done and ksat < 0.999 and kstall == 1:
                    act_sat_time_stall += dt
                    act_sat_dur_stall += dt
                    if act_sat_dur_stall > act_sat_max_dur_stall:
                        act_sat_max_dur_stall = act_sat_dur_stall
                else:
                    act_sat_dur_stall = 0.0
                if par[P_act_sag] > 0.5:
                    # supply current of each servo from its delivered torque: I = I_run + (I_stall(V) - I_run) |T| / Ts
                    for i_ in range(2):
                        Ti_ = abs(ksat * (Tsv1 if i_ == 0 else Tsv2))
                        Tsi_ = Ts1_ if i_ == 0 else Ts2_
                        Vi_ = Vp1 if i_ == 0 else Vp2
                        fq_ = Ti_ / Tsi_ if Tsi_ > 1e-9 else 1.0
                        if fq_ > 1.0:
                            fq_ = 1.0
                        Ii_ = par[P_act_Irun] + (par[P_act_Ia] + par[P_act_Ik] * Vi_ - par[P_act_Irun]) * fq_
                        if i_ == 0:
                            act_I1 = Ii_
                        else:
                            act_I2 = Ii_
                    if lit and not td_done:
                        if Vp1 < act_Vmin:
                            act_Vmin = Vp1
                        if Vp2 < act_Vmin:
                            act_Vmin = Vp2
                        if act_I1 > act_Imax:
                            act_Imax = act_I1
                        if act_I2 > act_Imax:
                            act_Imax = act_I2
                mdm = np.sqrt(md0 * md0 + md1 * md1)
                rec_ksat = ksat; rec_mdm = mdm; rec_vp = Vp1 if Vp1 < Vp2 else Vp2
                if lit and not td_done and mdm > max_hinge_dem:
                    max_hinge_dem = mdm
                if ksat < 0.999:
                    if td_done:
                        act_sat_time_td += dt
                    elif lit:
                        act_sat_time += dt
                        if phase >= 4:
                            act_sat_time_land += dt
                        if not act_prev_sat:
                            act_sat_events += 1.0
                            act_sat_dur = 0.0
                        act_sat_dur += dt
                        if act_sat_dur > act_sat_max_dur:
                            act_sat_max_dur = act_sat_dur
                            act_sat_max_t1 = t
                        if ksat < act_sat_kmin:
                            act_sat_kmin = ksat
                    act_prev_sat = lit and not td_done
                else:
                    act_prev_sat = False
                tq0_ = ksat * md0 - fr0
                tq1_ = ksat * md1 - fr1
                Ie_ = Ie_ + par[P_act_Jint]
            for a in range(2):
                tq_l = tq0_ if a == 0 else tq1_
                # v2.2 base excitation (engine about the moving pivot): I_P (alpha_body + dd) = tq - K_h d
                #   - m_e l_e (f_z sin d + f_lat), f = specific force at the pivot (previous step), body axes;
                #   axis 0 (about x): f_lat = +f_y; axis 1 (about y): f_lat = -f_x
                # v2.5: with a reflected servo inertia J (act_model 1): (I_P + J) dd + I_P alpha_body = tq - K_h d + ext
                fl_ = apiv[1] if a == 0 else -apiv[0]
                ext_ = -m_e * l_e * (fz_prev * np.sin(deng[a]) + fl_)
                if Ie_ == max(I_piv, 1e-4):
                    der[a] += ((tq_l - par[P_hose_K] * deng[a] + ext_) / Ie_ - alpha_prev[a]) * dt
                else:
                    der[a] += ((tq_l - par[P_hose_K] * deng[a] + ext_ - max(I_piv, 1e-4) * alpha_prev[a]) / Ie_) * dt
                deng[a] += der[a] * dt
                if abs(tq_l) > hinge_now:
                    hinge_now = abs(tq_l)
            if par[P_gim_stop] > 0.0:
                gs_ = np.radians(par[P_gim_stop])
                vm_ = np.sqrt(deng[0] * deng[0] + deng[1] * deng[1])
                if vm_ > gs_:
                    for a in range(2):
                        deng[a] *= gs_ / vm_
                        der[a] = 0.0
        else:
            for a in range(2):
                deng[a] = dlk[a]
        if par[P_gim_aw_thr] > 0.0:
            # ECU engine-rate estimate: quantised encoder angle, finite difference, first-order filter gim_aw_tau
            for a in range(2):
                thq_ = deng[a] if par[P_gim_enc_q] <= 0.0 else np.round(deng[a] / par[P_gim_enc_q]) * par[P_gim_enc_q]
                emr[a] += ((thq_ - em_prev[a]) / dt - emr[a]) * dt / max(par[P_gim_aw_tau], dt)
                em_prev[a] = thq_
        for a in range(2):
            dd_now = (deng[a] - deng_prev[a]) / dt
            dd[a] = (dd_now - dd_prev[a]) / dt
            dd_prev[a] = dd_now
            deng_prev[a] = deng[a]
            if lit:
                if abs(dd_now) > max_gim_rate:
                    max_gim_rate = abs(dd_now)
                if abs(dd[a]) > max_gim_acc:
                    max_gim_acc = abs(dd[a])
        gm = np.sqrt(deng[0] ** 2 + deng[1] ** 2)
        if gm > max_gim and lit:
            max_gim = gm
        if hinge_now > max_hinge and lit:
            max_hinge = hinge_now
        if td_done and hinge_now > max_hinge_td:
            max_hinge_td = hinge_now
        # ================================================================ forces and moments (body, about CG)
        dx = deng[0] + par[P_mis_x]
        dy = deng[1] + par[P_mis_y]
        tb[0] = np.sin(dy) * np.cos(dx)
        tb[1] = -np.sin(dx)
        tb[2] = np.cos(dx) * np.cos(dy)
        for i in range(3):
            Fb[i] = F * tb[i]
        rpx = -par[P_cg_x]; rpy = -par[P_cg_y]; rpz = z_p - zcg
        Mb[0] = rpy * Fb[2] - rpz * Fb[1]
        Mb[1] = rpz * Fb[0] - rpx * Fb[2]
        Mb[2] = rpx * Fb[1] - rpy * Fb[0] + par[P_roll_torque] * (F / Fmax) + Mrcs
        Mb[0] += -J_twd * dd[0]
        Mb[1] += -J_twd * dd[1]
        mdot = mox + mf_
        le2 = (zcg - (-0.03)) ** 2
        Mb[0] += -mdot * le2 * w[0]
        Mb[1] += -mdot * le2 * w[1]
        if tmode == 0:
            aero_forces(vrel_b, w, rho, zcg, F > 1.0, apar, comp, Fa, Ma)
        else:
            Fa[0] = 0.0; Fa[1] = 0.0; Fa[2] = 0.0; Ma[0] = 0.0; Ma[1] = 0.0; Ma[2] = 0.0
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
            ms = 0.0
            xs[0] *= 0.99; xs[1] *= 0.99; vs[0] *= 0.99; vs[1] *= 0.99
        # legs / ground contact (world forces)
        Fw[0] = 0.0; Fw[1] = 0.0; Fw[2] = 0.0
        leg_f_tot = 0.0
        contact = False
        rf = par[P_r_foot] if legs_dep else 0.06
        zf = par[P_z_foot] if legs_dep else -0.03
        for kf in range(4):
            ang = 0.25 * np.pi + 0.5 * np.pi * kf
            bvec[0] = rf * np.cos(ang); bvec[1] = rf * np.sin(ang); bvec[2] = zf - zcg
            qrot(q, bvec, tmp3)
            pz = r[2] + tmp3[2]
            if pz < 0.0:
                contact = True
                wxb[0] = w[1] * bvec[2] - w[2] * bvec[1]
                wxb[1] = w[2] * bvec[0] - w[0] * bvec[2]
                wxb[2] = w[0] * bvec[1] - w[1] * bvec[0]
                qrot(q, wxb, vf)
                for i in range(3):
                    vf[i] += v[i]
                pen = -pz
                if pen > max_pen:
                    max_pen = pen
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
                fwx = -mu * fn * vf[0] / max(vt_, 0.05)
                fwy = -mu * fn * vf[1] / max(vt_, 0.05)
                fwz = fn
                Fw[0] += fwx; Fw[1] += fwy; Fw[2] += fwz
                leg_f_tot += np.sqrt(fwx * fwx + fwy * fwy + fwz * fwz)
                mwv[0] = tmp3[1] * fwz - tmp3[2] * fwy
                mwv[1] = tmp3[2] * fwx - tmp3[0] * fwz
                mwv[2] = tmp3[0] * fwy - tmp3[1] * fwx
                qrotT(q, mwv, mb_)
                for i in range(3):
                    Mb[i] += mb_[i]
        if leg_f_tot > peak_leg and not held:
            peak_leg = leg_f_tot
        # ================================================================ hold-down / touchdown logic
        if held:
            if F >= par[P_hold_tw] * m_tot * g or (on_legs and F > m_tot * g):
                held = False
        if (not held) and contact and t > 1.0 and not td_done and tmode == 0 and (phase >= 2 or prof == 0):
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
            res[R_td_wind] = np.sqrt(wwx * wwx + wwy * wwy)
            lit = False
        # ================================================================ integrate translational
        if held:
            for i in range(3):
                acc[i] = 0.0
            fb[0] = 0.0; fb[1] = 0.0; fb[2] = g
        else:
            qrotT(q, Fw, Fcb)
            m_r = m_tot - ms
            for i in range(3):
                Ftot[i] = Fb[i] + Fcb[i]
            # slosh mass moves with the tank axially, not laterally
            fb[0] = Ftot[0] / m_r; fb[1] = Ftot[1] / m_r; fb[2] = Ftot[2] / m_tot
            qrot(q, fb, acc)
            acc[2] -= g
        for i in range(3):
            v[i] += acc[i] * dt
            r[i] += v[i] * dt
        ax_g = abs(fb[2]) / G0          # g-units of standard gravity (g may be 0 in test mode 1)
        if ax_g > max_axial and not held:
            max_axial = ax_g
        if not held:
            if td_done:
                if ax_g > max_axial_td:
                    max_axial_td = ax_g
            elif ax_g > max_axial_flt:
                max_axial_flt = ax_g
        fz_prev = fb[2]
        # ================================================================ integrate rotational
        if held:
            for i in range(3):
                w[i] = 0.0
                alpha_prev[i] = 0.0
        else:
            al[0] = (Mb[0] - w[1] * w[2] * (Ir - It)) / It
            al[1] = (Mb[1] - w[2] * w[0] * (It - Ir)) / It
            al[2] = Mb[2] / Ir
            for i in range(3):
                alpha_prev[i] = al[i]
            if par[P_rot_int] > 0.5:
                # v2.4: torque kick, then the exact free motion of the axisymmetric body over dt
                w0_ = w[0] + Mb[0] / It * dt
                w1_ = w[1] + Mb[1] / It * dt
                w2_ = w[2] + Mb[2] / Ir * dt
                bz_ = w2_ * (It - Ir) / It
                wa_[0] = w0_; wa_[1] = w1_; wa_[2] = w2_ * Ir / It
                qint(q, wa_, dt)
                wb_[0] = 0.0; wb_[1] = 0.0; wb_[2] = bz_
                qint(q, wb_, dt)
                c_ = np.cos(bz_ * dt); s_ = np.sin(bz_ * dt)
                w[0] = w0_ * c_ + w1_ * s_
                w[1] = -w0_ * s_ + w1_ * c_
                w[2] = w2_
            else:
                for i in range(3):
                    w[i] += al[i] * dt
                qint(q, w, dt)
            apiv[0] = fb[0] + al[1] * rpz
            apiv[1] = fb[1] - al[0] * rpz
            lat_eng = np.sqrt(apiv[0] ** 2 + apiv[1] ** 2) / G0
            if lat_eng > max_lat_eng:
                max_lat_eng = lat_eng
            alm_ = np.sqrt(al[0] * al[0] + al[1] * al[1])
            if td_done:
                if lat_eng > max_lat_td:
                    max_lat_td = lat_eng
                if alm_ > max_alpha_td:
                    max_alpha_td = alm_
            else:
                if lat_eng > max_lat_flt:
                    max_lat_flt = lat_eng
                if alm_ > max_alpha_flt:
                    max_alpha_flt = alm_
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
        # thrust-effectiveness estimator (axial accelerometer, landing burn)
        if par[P_k_est] > 0.5 and (phase == 5 or phase == 6 or (par[P_k_est_asc] > 0.5 and prof != 0 and phase >= 1
                                                                and phase <= 3 and t > 1.0
                                                                and (par[P_k_est_asc] < 1.5 or h_est > 1.0))) \
                and F > 0.15 * Fmax * tsc and not td_done:
            # v2.7 option 2 airborne gate (h_est > 1 m) in the ascent / floor phases: on the pad the accelerometer reads the
            # ground reaction (specific force = g whatever the thrust), which would bias the estimate on a slow start
            # v2.7 k_est_asc: also through the B-profile hop ascent, apex and floor descent (one continuous burn), so
            # the apex predictors and the descent start use the learnt thrust effectiveness (throat growth, scale error)
            F_mod = F / tsc
            if par[P_k_est_asc] > 1.5:
                # v2.7 option 2: signed nominal axial force (option 1 and v2.6 subtract the tail-first drag in every
                # direction, a -2 D / F bias in the ascent): nose-first S (CA0_nf + CA_engine-on) going up, tail-first
                # S CA0_tf (0.5 + 0.5 k_retro) going down, + S CA_legs with the legs out (FSW nominal model, rho 1.2)
                cda_ = par[P_kest_cda_nf] if vz_e > 0.0 else par[P_drag_cda_nom]
                if legs_dep:
                    cda_ += par[P_kest_cda_legs]
                d_ = 0.5 * 1.2 * cda_ * vz_e * vz_e
                k_raw = (fm[2] * m_est + (d_ if vz_e > 0.0 else -d_)) / F_mod
            else:
                k_raw = (fm[2] * m_est - 0.5 * 1.2 * par[P_drag_cda_nom] * vz_e * vz_e) / F_mod
            k_hat += (k_raw - k_hat) * dt / par[P_k_est_tau]
        # ================================================================ metrics
        wt = np.sqrt(w[0] ** 2 + w[1] ** 2)
        if abs(w[2]) > max_roll and not td_done:
            max_roll = abs(w[2])
        if phase == 1 and Vair > 5.0:
            if aoa > max_aoa_asc:
                max_aoa_asc = aoa
            if tilt > max_tilt_asc:
                max_tilt_asc = tilt
        if phase == 2 and prof == 0:
            if wt > max_rate_coast:
                max_rate_coast = wt
            if Vair > 5.0 and aoa > coast_aoa:
                coast_aoa = aoa
        if phase == 3 or phase == 4:
            if wt > max_rate_desc:
                max_rate_desc = wt
        if (phase == 4 or phase == 3) and prof == 0:
            if tilt > max_tilt_desc:
                max_tilt_desc = tilt
        if (phase == 5 or phase == 6) and not td_done:
            if wt > max_rate_land:
                max_rate_land = wt
            if tilt > max_tilt_land and t - t5 > 0.5:
                max_tilt_land = tilt
        if td_done and wt > max_rate_post:
            max_rate_post = wt
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
            o[34] = k_hat; o[35] = wwx; o[36] = wwy; o[37] = Fc_avail; o[38] = vref; o[39] = qdyn
            o[40] = leg_f_tot; o[41] = mox; o[42] = mf_; o[43] = It; o[44] = Ir; o[45] = mfuel; o[46] = fb[2]
            o[47] = T
            o[48] = d_hat[0]; o[49] = d_hat[1]; o[50] = a_lat[0]; o[51] = a_lat[1]; o[52] = np.degrees(tilt_lim)
            o[53] = h_est
            o[54] = np.degrees(dsv[0]); o[55] = np.degrees(dsv[1]); o[56] = rec_ksat; o[57] = rec_mdm; o[58] = rec_vp
            o[59] = np.degrees(ex); o[60] = np.degrees(ey); o[61] = np.degrees(rec_raw)
            # v2.7: Pc-equivalent thrust F / tsc (what the Pc map implies; = F when tsc = 1) and the throat-area growth g
            o[62] = F / tsc if F > 0.0 else 0.0; o[63] = thr_g
            nrec += 1
            next_rec += par[P_rec_dt]
        # ================================================================ termination
        if td_done:
            if tilt > np.radians(60.0):
                tip = True
            if t > t_td + par[P_t_post]:
                break
        if (not held) and t > 2.0 and r[2] < (zcg - par[P_z_foot]) - 1.5:
            crash = True
            break
    if td_done and tilt > np.radians(45.0):
        tip = True
    res[R_landed] = 1.0 if td_done else 0.0
    res[R_crash] = 1.0 if crash else 0.0
    res[R_prop_used] = prop_used
    res[R_liq_left] = ml
    res[R_exhausted] = 1.0 if exhausted else 0.0
    res[R_h_max] = hmax
    res[R_apo_x] = apo_x; res[R_apo_y] = apo_y
    res[R_v_ign] = v_ign; res[R_h_ign] = h_ign
    res[R_max_gim] = np.degrees(max_gim); res[R_max_gim_rate] = np.degrees(max_gim_rate)
    res[R_max_gim_acc] = max_gim_acc
    res[R_max_hinge] = max_hinge
    res[R_max_rate_coast] = np.degrees(max_rate_coast); res[R_max_rate_desc] = np.degrees(max_rate_desc)
    res[R_max_rate_land] = np.degrees(max_rate_land); res[R_max_tilt_land] = np.degrees(max_tilt_land)
    res[R_max_aoa_asc] = np.degrees(max_aoa_asc); res[R_max_tilt_asc] = np.degrees(max_tilt_asc)
    res[R_tumble_coast] = 1.0 if max_rate_coast > np.radians(90.0) else 0.0
    res[R_starts] = starts; res[R_burn_time] = burn_time
    res[R_tipover] = 1.0 if tip else 0.0
    res[R_peak_leg_force] = peak_leg
    res[R_max_axial_g] = max_axial; res[R_max_lat_g_eng] = max_lat_eng
    res[R_hslam_used] = 1.0 if hslam else 0.0
    res[R_cut] = 1.0 if cut else 0.0
    res[R_nrec] = nrec; res[R_t_end] = t
    res[R_throat_g_end] = thr_g; res[R_throat_J] = thr_J
    res[R_reg_X_end] = reg_X
    res[R_aw_resets] = aw_resets; res[R_aw_time] = aw_time
    res[R_act_sat_max_t1] = act_sat_max_t1; res[R_t_relight] = t_relight
    res[R_max_tilt_desc] = np.degrees(max_tilt_desc)
    res[R_relight_ok] = relight_ok
    res[R_max_q] = max_q
    res[R_coast_aoa_max] = np.degrees(coast_aoa)
    res[R_fuel_left] = mfuel
    res[R_gim_sat_frac] = sat_steps / burn_steps if burn_steps > 0 else 0.0
    res[R_max_gim_raw] = np.degrees(max_gim_raw)
    res[R_max_roll_rate] = np.degrees(max_roll)
    res[R_rcs_time] = rcs_time; res[R_rcs_ang_imp] = rcs_imp
    res[R_max_pen] = max_pen
    res[R_max_rate_post] = np.degrees(max_rate_post)
    res[R_max_axial_g_flt] = max_axial_flt; res[R_max_lat_g_eng_flt] = max_lat_flt; res[R_max_alpha_flt] = max_alpha_flt
    res[R_max_axial_g_td] = max_axial_td; res[R_max_lat_g_eng_td] = max_lat_td; res[R_max_alpha_td] = max_alpha_td
    res[R_max_hinge_td] = max_hinge_td
    res[R_act_sat_time] = act_sat_time; res[R_act_sat_events] = act_sat_events; res[R_act_sat_max_dur] = act_sat_max_dur
    res[R_act_sat_kmin] = act_sat_kmin; res[R_act_sat_time_td] = act_sat_time_td; res[R_max_hinge_dem] = max_hinge_dem
    res[R_act_sat_time_land] = act_sat_time_land
    res[R_act_Vmin] = act_Vmin; res[R_act_Imax] = act_Imax
    res[R_act_sat_time_stall] = act_sat_time_stall; res[R_act_sat_max_dur_stall] = act_sat_max_dur_stall
    if res[R_m_land] == 0.0:
        res[R_m_land] = m_tot
    return res

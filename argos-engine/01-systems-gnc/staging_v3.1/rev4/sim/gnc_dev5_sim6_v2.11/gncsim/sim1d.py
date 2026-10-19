"""1-D vertical flight simulator (first-pass profiles, duty cycles, landing-closure MC).

State: h (foot-plane altitude above ground) [m], v [m/s], tank (m, E), fuel mass, thrust F.
Dynamics:  m dv/dt = F_eff - m g - D(v),  D = 0.5 rho v|v| S C_A(direction, engine, legs)
Engine:    command -> clamp [floor, ceiling(P_tank, D_port)] -> deadband/quantisation ->
           rate limit -> first-order lag (tau) -> F;  ignition delay, rise and tail-off.
           mdot from the steady map table (O/F shift and Isp vs throttle), Isp dispersion scale.
Tank:      equilibrium self-pressurised N2O, updated every 10 ms.
Profiles:  0 = A ballistic: full-thrust ascent, MECO on predicted apogee, unpowered descent
               (free-fall tail-first, or under drogue), relight, landing burn;
           1 = B continuous-burn hop: ascent, throttle to floor on predicted apogee, floor
               through apex and descent, landing burn (no shutdown until touchdown);
Landing guidance: velocity-tracking 'throttle-margin hoverslam' (v_ref(h) parabola at the
           design deceleration a_d = k_d (F_ceil/m - g) to a terminal gate (h_t, v_t), then
           constant-rate descent) for hover-capable floors; Falcon-9-style hoverslam (v_ref to 0
           at h = 0, cutoff at h_cut) when the floor exceeds ~0.9 W.
"""
import numpy as np
from numba import njit
from .propulsion import tank_solve, tank_init, _bilin, _interp1

G0 = 9.80665

# parameter vector indices
(I_PROFILE, I_H_TARGET, I_FMAX, I_FLOOR, I_TAU, I_SLEW, I_DEADB, I_QUANT, I_TIGN, I_TRISE,
 I_TOFF, I_THRUST_SCALE, I_ISP_SCALE, I_TANK_V, I_M_N2O, I_T0, I_CWALL, I_RESID, I_M_DRY,
 I_M_FUEL0, I_RHOF, I_GL, I_GDO, I_S_REF, I_CA_NF, I_CA_TF, I_CA_LEGS, I_DROGUE_CDA,
 I_KD, I_HT, I_VT, I_KV, I_HSLAM, I_HCUT, I_RHO0, I_DT, I_TIGN_EST, I_LEGS_AT_IGN, I_KRETRO,
 I_TMAX, I_ASCENT_THR, I_FLOOR_HOP, I_HOVER_K, I_WIND_V, I_MECO_BIAS, I_BALLAST, I_VREL_IGN,
 I_NOISE_V, I_SEED, I_HBIAS, I_VBIAS, I_MEST, I_ABIAS, I_KEST, I_KEST_TAU, I_HS_MARGIN) = range(56)
N_PAR = 56


@njit(cache=True)
def _rho(h, rho0):
    # ISA troposphere density ratio about the site (rho0 at site); adequate below ~1 km
    return rho0 * (1.0 - 2.2558e-5 * h) ** 4.2559


@njit(cache=True)
def run(par, Fg, Dg, tmox, tmf, Pg, ceil, rec_dt, out_rec):
    """Integrate one flight. Returns summary array; fills out_rec[k, :] every rec_dt.
    out_rec columns: t, h, v, a_body(specific force), F, F_cmd, mdot, mox, mf, P_tank, T_tank,
                     m, m_liq, m_fuel, phase, F_ceil, Pc_proxy(F/Fmax)."""
    dt = par[I_DT]
    g = G0
    prof = int(par[I_PROFILE])
    Fmax = par[I_FMAX]
    floorF = par[I_FLOOR] * Fmax
    tsc = par[I_THRUST_SCALE]
    isc = par[I_ISP_SCALE]
    S = par[I_S_REF]
    V = par[I_TANK_V]
    Cw = par[I_CWALL]
    mt = par[I_M_N2O]
    E = tank_init(mt, par[I_T0], V, Cw)
    T, Pt, ml, mv, hl = tank_solve(mt, E, V, Cw)
    resid = par[I_RESID] * par[I_M_N2O]
    mfuel = par[I_M_FUEL0]
    m_dry = par[I_M_DRY] + par[I_BALLAST]
    h = 0.0; v = 0.0; t = 0.0
    F = 0.0; Fcmd = 0.0; Fc_prev = 0.0
    lit = False; burning = False
    phase = 0      # 0 pad,1 ascent,2 coast/floor-coast,3 descent unpowered,4 ignition wait,5 landing burn,6 terminal,7 shutdown,8 landed
    t_ign_cmd = -1.0
    hmax = 0.0
    prop_used = 0.0
    landed = False
    td_v = 0.0
    t_lift = -1.0
    burn_time = 0.0
    starts = 0
    hs_mode = int(par[I_HSLAM])       # -1 auto (flight-software decision), 0 hover-capable, 1 hoverslam
    hslam = hs_mode == 1
    mode_locked = False
    cut = False
    nrec = 0
    next_rec = 0.0
    Fceil = Fmax
    Dp = 0.03
    max_acc = 0.0
    min_acc = 0.0
    a_body = 0.0
    tank_timer = 0.0
    F_land_max = 0.0
    landing_started = False
    vrel_ign = 0.0
    h_ign = 0.0
    t_land_start = -1.0
    exhausted = False
    acc_prev = 0.0
    ei = 0.0                 # velocity-error integral (PI loop, anti-windup)
    sat_lo = False
    k_hat = 1.0              # in-flight thrust-effectiveness estimate (accelerometer-based), 1 = map nominal
    D_last = 0.0
    sat_hi = False
    while t < par[I_TMAX]:
        m = m_dry + mfuel + mt
        # port diameter from fuel mass
        Ap = mfuel / (par[I_RHOF] * par[I_GL])
        dp2 = par[I_GDO] ** 2 - 4.0 * Ap / np.pi
        Dp = np.sqrt(dp2) if dp2 > 1e-6 else 1e-3
        Fceil = tsc * _bilin(Pg, Dg, ceil, Pt, Dp)
        if Fceil > Fmax * tsc:
            Fceil = Fmax * tsc
        if ml <= resid:
            Fceil = 0.0
            if burning:
                exhausted = True
        Fc_avail = Fceil / tsc          # what guidance believes is available (nominal map)
        rho = _rho(h, par[I_RHO0])
        # navigation errors (constant biases per run) and guidance mass knowledge error
        h_true = h
        v_true = v
        m_true = m
        h = h_true + par[I_HBIAS]
        v = v_true + par[I_VBIAS]
        m = m_true * (1.0 + par[I_MEST])
        # --------------------------------------------------------- guidance / sequencing
        if phase == 0:
            Fcmd = Fmax
            lit = True
            burning = True
            if starts == 0:
                starts = 1
            phase = 1
        elif phase == 1:
            Fcmd = Fmax * par[I_ASCENT_THR]
            if v > 0.5:
                # predicted apogee
                if prof == 0:
                    k = 0.5 * rho * S * par[I_CA_NF] / m
                    hap = h + np.log(1.0 + k * v * v / g) / (2.0 * k) + v * par[I_TOFF]
                    if hap >= par[I_H_TARGET] + par[I_MECO_BIAS]:
                        phase = 2
                        lit = False
                else:
                    # apex under floor thrust: mean mass over the coast and throttle-down lag
                    # throttle-down = slew-limited ramp to F_sw, then first-order tail (tau)
                    Fsw = floorF + par[I_SLEW] * Fmax * par[I_TAU]
                    if Fsw > F:
                        Fsw = F
                    t_ramp = (F - Fsw) / (par[I_SLEW] * Fmax)
                    dv1 = (0.5 * (F + Fsw) / m - g) * t_ramp
                    dv2 = ((Fsw - floorF) / m) * par[I_TAU] + (floorF / m - g) * par[I_TAU]
                    lagd = t_ramp + par[I_TAU]
                    vq = v + dv1 + dv2
                    hq = h + 0.5 * (v + vq) * lagd
                    mdf = floorF / (140.0 * G0)
                    mm = m
                    for _it in range(3):
                        geff = g - floorF / mm
                        if geff < 0.2:
                            geff = 0.2
                        tco = vq / geff
                        mm = m - 0.5 * mdf * tco
                    k = 0.5 * rho * S * par[I_CA_NF] / mm
                    hap = hq + np.log(1.0 + k * vq * vq / geff) / (2.0 * k)
                    if hap >= par[I_H_TARGET]:
                        phase = 2
        if phase == 2 or phase == 3:
            if prof == 1:
                Fcmd = floorF
                if phase == 2 and v > 0.0:
                    geff = g - floorF / m
                    if geff < 0.2:
                        geff = 0.2
                    hap_now = h + v * v / (2.0 * geff)
                    if hap_now < par[I_H_TARGET] - 0.5:
                        Fcmd = floorF + m * 0.08 * (par[I_H_TARGET] - hap_now)
            else:
                Fcmd = 0.0
            if v < 0.0 and phase == 2:
                phase = 3
            if phase == 3:
                if hs_mode < 0 and not mode_locked:
                    hslam = floorF > par[I_HOVER_K] * m * g     # m is the guidance estimate here
                # landing-burn trigger: stopping distance at design deceleration + lag allowance
                ad = par[I_KD] * (Fc_avail / m - g)
                if hslam:
                    amin = floorF / m - g
                    ad = amin + 0.5 * ((Fc_avail / m - g) - amin)
                    if ad < amin + 0.5:
                        ad = amin + 0.5
                lag = par[I_TIGN_EST] + par[I_TRISE] if prof == 0 else par[I_TAU] * 2.0
                amin_ = floorF / m - g
                a_term_ = (amin_ + par[I_HS_MARGIN] if amin_ + par[I_HS_MARGIN] > 1.0 else 1.0) if hslam else 1.5
                ht = par[I_HT]
                vt = np.sqrt(par[I_VT] ** 2 + 2.0 * a_term_ * ht)
                # predicted state when thrust arrives: current acceleration held over the lag
                a_now = acc_prev
                vi = v + a_now * lag
                hi = h + v * lag + 0.5 * a_now * lag * lag
                htrig = (vi * vi - vt * vt) / (2.0 * ad) + ht
                if hi <= htrig and vi < 0.0:
                    mode_locked = True
                    if prof == 0:
                        phase = 4
                        t_ign_cmd = t
                        vrel_ign = v
                        h_ign = h
                    else:
                        phase = 5
                    if t_land_start < 0:
                        t_land_start = t
        if phase == 4:
            Fcmd = floorF
            if t - t_ign_cmd >= par[I_TIGN]:
                lit = True
                burning = True
                starts += 1
                F = 0.05 * Fmax * tsc
                phase = 5
        if phase == 5 or phase == 6:
            landing_started = True
            keff = k_hat if par[I_KEST] > 0.5 else 1.0
            amin = keff * floorF / m - g
            amax = keff * Fc_avail / m - g
            vtd = par[I_VT]
            hg = par[I_HT]
            if hslam:
                a_term = amin + par[I_HS_MARGIN]
                if a_term < 1.0:
                    a_term = 1.0
                ad = amin + 0.5 * (amax - amin)
            else:
                a_term = 1.5
                ad = par[I_KD] * amax
            if ad < a_term + 0.5:
                ad = a_term + 0.5
            vg = np.sqrt(vtd * vtd + 2.0 * a_term * hg)
            if h > hg:
                vref = -np.sqrt(vg * vg + 2.0 * ad * (h - hg))
                aref = ad * v / vref
            else:
                if phase == 5:
                    ei = 0.0          # reset the integrator at the terminal gate
                phase = 6
                vref = -np.sqrt(vtd * vtd + 2.0 * a_term * max(h, 0.0))
                aref = a_term * v / vref
            if aref < 0.0:
                aref = 0.0
            if hslam and v > -par[I_HCUT]:
                # Falcon-9 logic: the vehicle is stopping (floor > W) before contact was sensed: cut now.
                # (v1.0 also required h_nav > 0.03 m; with a negative altimeter bias the vehicle then
                #  stopped above the ground, climbed at floor thrust and fell from higher: removed in v1.1)
                cut = True
                lit = False
                phase = 7
            ev = vref - v
            # anti-windup: integrate only when not saturated in the direction of the error
            if not ((sat_hi and ev > 0.0) or (sat_lo and ev < 0.0)):
                ei += ev * dt
            ki = 0.6 * par[I_KV]
            if ki * ei > 3.0:
                ei = 3.0 / ki
            if ki * ei < -3.0:
                ei = -3.0 / ki
            Fcmd = m * (g + aref + par[I_KV] * ev + ki * ei)
            # drag feed-forward (tail-first descent, engine on)
            Fcmd -= 0.5 * rho * S * par[I_CA_TF] * (0.5 + 0.5 * par[I_KRETRO]) * v * v
            Fcmd = Fcmd / keff
            if phase == 7:
                Fcmd = 0.0
        if phase == 7:
            Fcmd = 0.0
            lit = False
        # restore truth for the physics
        h = h_true
        v = v_true
        m = m_true
        # --------------------------------------------------------- engine
        if lit and burning:
            # command clamps, deadband and quantisation (closed-loop Pc assumed to track command)
            sat_lo = Fcmd <= floorF
            sat_hi = Fcmd >= Fc_avail
            if Fcmd < floorF:
                Fcmd = floorF
            if Fcmd > Fc_avail:
                Fcmd = Fc_avail
            if abs(Fcmd - Fc_prev) < par[I_DEADB] * Fmax:
                Fcmd = Fc_prev
            q = par[I_QUANT] * Fmax
            if q > 0:
                Fcmd = np.floor(Fcmd / q + 0.5) * q
            Fc_prev = Fcmd
            Ftgt = Fcmd * tsc
            if Ftgt > Fceil:
                Ftgt = Fceil
            dF = (Ftgt - F) / par[I_TAU] * dt
            lim = par[I_SLEW] * Fmax * dt
            if dF > lim:
                dF = lim
            if dF < -lim:
                dF = -lim
            F += dF
            burn_time += dt
        else:
            F += (0.0 - F) / par[I_TOFF] * dt
            if F < 0.5:
                F = 0.0
            if not lit:
                burning = False if F == 0.0 else burning
        if F < 0.0:
            F = 0.0
        # mass flow from steady map (Isp dispersion scales mdot)
        mox = 0.0
        mf_ = 0.0
        if F > 0.0 and ml > resid:
            mox = _bilin(Fg, Dg, tmox, F / tsc, Dp) / isc
            mf_ = _bilin(Fg, Dg, tmf, F / tsc, Dp) / isc
        elif F > 0.0:
            F = 0.0
        # --------------------------------------------------------- dynamics
        # drag coefficient by direction and configuration
        if v >= 0.0:
            CA = par[I_CA_NF] + (-0.07 if F > 1.0 else 0.0)
        else:
            CA = par[I_CA_TF] * ((0.5 + 0.5 * par[I_KRETRO]) if F > 1.0 else 1.0)
            if (phase >= 4 and par[I_LEGS_AT_IGN] > 0.5) or par[I_LEGS_AT_IGN] > 1.5:
                CA += par[I_CA_LEGS]
        D = -0.5 * rho * S * CA * v * abs(v)
        Dd = 0.0
        if prof == 0 and par[I_DROGUE_CDA] > 0.0 and (phase == 3 or phase == 4):
            Dd = 0.5 * rho * par[I_DROGUE_CDA] * v * v     # drogue (upward while falling)
        if h <= 0.0 and not landing_started and F + D < m * g and t_lift < 0:
            acc = 0.0
            v = 0.0
        else:
            if t_lift < 0:
                t_lift = t
            acc = (F + D + Dd) / m - g
        a_body = (F + D + Dd) / m       # specific force along the body axis (vertical flight)
        # thrust-effectiveness estimator: accelerometer specific force (with bias) x estimated mass,
        # minus modelled drag, over the flight-software engine-model thrust (nominal map units)
        if par[I_KEST] > 0.5 and (phase == 5 or phase == 6) and F > 0.15 * Fmax * tsc:
            F_mod = F / tsc
            k_raw = ((a_body + par[I_ABIAS]) * m * (1.0 + par[I_MEST]) - D - Dd) / F_mod
            k_hat += (k_raw - k_hat) * dt / par[I_KEST_TAU]
        if a_body > max_acc:
            max_acc = a_body
        if a_body < min_acc:
            min_acc = a_body
        acc_prev = acc
        v += acc * dt
        h += v * dt
        if h > hmax:
            hmax = h
        dm_ox = mox * dt
        dm_f = mf_ * dt
        if dm_f > mfuel:
            dm_f = mfuel
        mfuel -= dm_f
        prop_used += dm_ox + dm_f
        # tank (every 10 ms)
        E -= dm_ox * hl
        mt -= dm_ox
        tank_timer += dt
        if tank_timer >= 0.01 - 1e-12:
            T, Pt, ml, mv, hl = tank_solve(mt, E, V, Cw)
            tank_timer = 0.0
        if F > F_land_max and landing_started:
            F_land_max = F
        t += dt
        # record
        if t >= next_rec and nrec < out_rec.shape[0]:
            out_rec[nrec, 0] = t; out_rec[nrec, 1] = h; out_rec[nrec, 2] = v; out_rec[nrec, 3] = a_body
            out_rec[nrec, 4] = F; out_rec[nrec, 5] = Fcmd if (lit or phase == 4) else 0.0
            out_rec[nrec, 6] = mox + mf_; out_rec[nrec, 7] = mox; out_rec[nrec, 8] = mf_
            out_rec[nrec, 9] = Pt; out_rec[nrec, 10] = T; out_rec[nrec, 11] = m
            out_rec[nrec, 12] = ml; out_rec[nrec, 13] = mfuel; out_rec[nrec, 14] = phase
            out_rec[nrec, 15] = Fceil; out_rec[nrec, 16] = F / Fmax
            nrec += 1
            next_rec += rec_dt
        if t_lift >= 0 and h <= 0.0 and t > t_lift + 0.5:
            landed = True
            td_v = v
            break
    res = np.zeros(22)
    res[0] = 1.0 if landed else 0.0
    res[1] = td_v
    res[2] = hmax
    res[3] = prop_used
    res[4] = mt                       # N2O remaining (liquid + vapour)
    res[5] = ml
    res[6] = mfuel
    res[7] = t
    res[8] = burn_time
    res[9] = starts
    res[10] = max_acc
    res[11] = min_acc
    res[12] = m_dry + mfuel + mt      # landing mass
    res[13] = nrec
    res[14] = F_land_max
    res[15] = vrel_ign
    res[16] = h_ign
    res[17] = 1.0 if exhausted else 0.0
    res[18] = Pt
    res[19] = T
    res[20] = 1.0 if hslam else 0.0     # landing mode actually flown (1 = hoverslam)
    res[21] = 1.0 if cut else 0.0       # engine cut before contact (hoverslam stop-aloft logic)
    return res

"""Apply sim6 amendment P (A-relight forced purge and stuck-open head-end bleed fault) to a sim6.py file (path argument).
Requires amendments M, W and F already applied. v1.1 (GNC, 2026-10-13): lift priority option prg_prio, subtractive-bracket cap
blf_fmax with the bled mass and jet taken as the capped share of the injector flow."""
import sys

p = sys.argv[1]
s = open(p).read()


def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, (old[:80], n)
    s = s.replace(old, new)


# ---------------------------------------------------------------- docstring and version
rep("""   the onset, false-abort flag (a decision before the onset), the FC_THRUST held maxima before and after the onset.
""", """   the onset, false-abort flag (a decision before the onset), the FC_THRUST held maxima before and after the onset.
 * v2.8-dev amendment P (2026-10-13, coordinator relay of the RG-01 forced-purge design and of the stuck-open bleed fault; off
   by default, bit-identical when off, m2_bitcheck_v28 part P): PURGE (prg_on 1, A profile): the relight trigger of the phase-3
   planner is evaluated a second time with the planning lag extended by prg_T + prg_lead; when that earlier trigger fires the
   purge starts (MV open, pintle seated, head-end bleed open). prg_prio 1 (GNC proposal): the lift (= the relight command, phase
   4) keeps the plain trigger and the purge is truncated if it started late; prg_prio 0: the lift waits until the purge has run
   prg_T (lift delay recorded). The purge ends at the lift. Truth: the tank loses prg_mdot [kg/s] of liquid during the purge (ASSUMED liquid at the
   bleed for the whole purge: upper bound of mass and jet force); the bleed jet (prg_jet 1) is a radial body-frame force
   prg_mdot x bl_vj at azimuth bl_az applied at the engine pivot height (ASSUMED vent location and direction, TO-DEFINE). FSW:
   prg_book 1 books prg_mdot_hat x dt into m_hat while the purge is commanded. STUCK-OPEN BLEED (blf_on 1): from the onset
   (blf_ph 0: first ignition; 4: the relight lift, the bleed fails to close) the bleed passes blf_mdot whenever the main valve is
   open (lit, or between the lift and the light), until the liquid is exhausted or the MV is seated by an abort. blf_mode 0
   (additive bracket): the engine flow and thrust are unchanged, the tank loses blf_mdot more; blf_mode 1 (subtractive bracket):
   the bleed takes a share f = min(blf_mdot / mox, blf_fmax) of the injector oxidiser flow at the same lift (bled mass and jet =
   f mox), chamber oxidiser x (1 - f), fuel x (1 - f)^blf_n, thrust x the chamber-flow ratio (constant c* Cf, ASSUMED), tank
   outflow unchanged (the fuel-web state uses the line flow: conservative); with no injector flow (lift to light) the bleed passes
   blf_mdot from the tank. Jet force blf_mdot x bl_vj radial at bl_az (bl_vj 0: balanced or axial vent). No detector of the
   stuck bleed is modelled (TO-DEFINE). Results: purge start, duration, lift wait beyond the plain trigger, purge mass, height at
   the purge start, largest tilt and body rate (pitch/yaw) during the purge, tilt at the lift; bleed onset, bled mass and time,
   smallest thrust factor (mode 1).
""")
rep('SIM6_VERSION = "sim6 v2.8-dev (2026-10-13, amendments M, W, F)"',
    'SIM6_VERSION = "sim6 v2.8-dev (2026-10-13, amendments M, W, F, P)"')

# ---------------------------------------------------------------- names
rep('''              "fct_hz fct_ph fct_comp det_op_F det_op_t det_pf_t det_pf_dF geo_dh abt_lat abt_seat abt_sdto abt_sdenc abt_imp").split()
''', '''              "fct_hz fct_ph fct_comp det_op_F det_op_t det_pf_t det_pf_dF geo_dh abt_lat abt_seat abt_sdto abt_sdenc abt_imp").split()
# v2.8-dev amendment P: A-relight forced purge (bleed open with the pintle seated before the lift) and stuck-open bleed fault
PAR_NAMES += ("prg_on prg_T prg_lead prg_mdot prg_mdot_hat prg_book prg_jet prg_prio blf_on blf_ph blf_mdot blf_mode blf_n "
              "blf_fmax bl_vj bl_az").split()
''')
rep('''flt_tr_fct flt_tr_op flt_tr_pf flt_tr_geo fct_held_pre fct_held_post
""".split()''', '''flt_tr_fct flt_tr_op flt_tr_pf flt_tr_geo fct_held_pre fct_held_post
prg_t0 prg_dur prg_wait prg_mass prg_h0 prg_tilt_max prg_tilt_lift prg_rate_max blf_t0 blf_mass blf_time blf_kF_min
""".split()''')

# ---------------------------------------------------------------- state
rep('''    tr_fct = -1.0; tr_op = -1.0; tr_pf = -1.0; tr_geo = -1.0
''', '''    tr_fct = -1.0; tr_op = -1.0; tr_pf = -1.0; tr_geo = -1.0
    # v2.8-dev amendment P: purge (pg_*) and stuck-open bleed (bl_*) state
    prg_on = par[P_prg_on] > 0.5
    blf_on = par[P_blf_on] > 0.5
    pg_t0 = -1.0; pg_t1 = -1.0; pg_tw = -1.0; pg_h0 = 0.0; pg_m = 0.0; pg_tilt = 0.0; pg_rate = 0.0; pg_tlift = 0.0
    bl_t0 = -1.0; bl_m = 0.0; bl_time = 0.0; bl_kmin = 1.0
    blx_ = 0.0; pg_act_ = False; blf_fl_ = False; bjm_ = 0.0
''')

# ---------------------------------------------------------------- planner: purge start and lift gate
rep('''                if hi <= htrig and vi < 0.0:
                    mode_locked = True''', '''                go_ = hi <= htrig and vi < 0.0
                if prg_on and prof == 0:
                    # amendment P: the purge starts on the same trigger evaluated prg_T + prg_lead earlier; prg_prio 0: the
                    # lift waits until the purge has run prg_T; prg_prio 1: the lift keeps the plain trigger (purge truncated)
                    if pg_t0 < 0.0:
                        lgp_ = lag + par[P_prg_T] + par[P_prg_lead]
                        vip_ = vz_e + az_est * lgp_
                        hip_ = h_est + vz_e * lgp_ + 0.5 * az_est * lgp_ * lgp_
                        if (vip_ < 0.0 and hip_ <= (vip_ * vip_ - vt * vt) / (2.0 * ad) + par[P_ht]) or go_:
                            pg_t0 = t; pg_h0 = h_est
                    if go_:
                        if pg_tw < 0.0:
                            pg_tw = t
                        if par[P_prg_prio] < 0.5 and t - pg_t0 < par[P_prg_T] - 1.0e-9:
                            go_ = False
                if go_:
                    mode_locked = True''')
rep('''                        t_relight = t
                        legs_dep = True''', '''                        t_relight = t
                        if prg_on:
                            pg_t1 = t; pg_tlift = tilt
                        legs_dep = True''')

# ---------------------------------------------------------------- truth flows
rep('''            mox = 0.0; mf_ = 0.0              # amendment F: MV seated, tank isolated (segment inventory not deducted)
''', '''            mox = 0.0; mf_ = 0.0              # amendment F: MV seated, tank isolated (segment inventory not deducted)
        # v2.8-dev amendment P: forced purge and stuck-open bleed (truth)
        blx_ = 0.0; pg_act_ = False; blf_fl_ = False; bjm_ = 0.0
        if prg_on or blf_on:
            if prg_on and pg_t0 >= 0.0 and pg_t1 < 0.0 and ml > resid:
                pg_act_ = True
                blx_ += par[P_prg_mdot]
                pg_m += par[P_prg_mdot] * dt
                if par[P_prg_jet] > 0.5:
                    bjm_ += par[P_prg_mdot]
                if tilt > pg_tilt:
                    pg_tilt = tilt
                wq_ = np.sqrt(w[0] * w[0] + w[1] * w[1])
                if wq_ > pg_rate:
                    pg_rate = wq_
            if blf_on:
                if bl_t0 < 0.0:
                    if (par[P_blf_ph] < 0.5 and lit) or (par[P_blf_ph] > 3.5 and prof == 0 and t_ign_cmd >= 0.0):
                        bl_t0 = t
                mvo_ = lit or (prof == 0 and phase == 4)
                if bl_t0 >= 0.0 and mvo_ and ml > resid and not (flt_on and fa_st == 3) and not pg_act_:
                    blf_fl_ = True
                    bl_time += dt
                    if par[P_blf_mode] > 0.5 and F > 0.0 and mox > 0.0:
                        fb_ = par[P_blf_mdot] / mox
                        if fb_ > par[P_blf_fmax]:
                            fb_ = par[P_blf_fmax]
                        mfn_ = mf_ * (1.0 - fb_) ** par[P_blf_n]
                        kF_ = (mox * (1.0 - fb_) + mfn_) / (mox + mf_)
                        F = F * kF_
                        mf_ = mfn_
                        bl_m += fb_ * mox * dt
                        bjm_ += fb_ * mox
                        if kF_ < bl_kmin:
                            bl_kmin = kF_
                    else:
                        blx_ += par[P_blf_mdot]
                        bl_m += par[P_blf_mdot] * dt
                        bjm_ += par[P_blf_mdot]
''')

# ---------------------------------------------------------------- jet force (body frame, about the CG)
rep('''        Mb[1] += -J_twd * dd[1]
''', '''        Mb[1] += -J_twd * dd[1]
        if bjm_ > 0.0 and par[P_bl_vj] > 0.0:
            # amendment P: bleed jet, radial in the body frame at azimuth bl_az, applied at the pivot height (ASSUMED)
            fj_ = bjm_ * par[P_bl_vj]
            fjx_ = fj_ * np.cos(par[P_bl_az]); fjy_ = fj_ * np.sin(par[P_bl_az])
            Fb[0] += fjx_; Fb[1] += fjy_
            Mb[0] += -rpz * fjy_
            Mb[1] += rpz * fjx_
            Mb[2] += rpx * fjy_ - rpy * fjx_
''')

# ---------------------------------------------------------------- tank
rep('''        dm_ox = mox * dt
''', '''        dm_ox = (mox + blx_) * dt
''')

# ---------------------------------------------------------------- FSW booking of the commanded purge
rep('''            m_hat -= qh_ * dt
''', '''            m_hat -= qh_ * dt
            if pg_act_ and par[P_prg_book] > 0.5:
                m_hat -= par[P_prg_mdot_hat] * dt     # amendment P: commanded purge booked at its nominal flow
''')

# ---------------------------------------------------------------- results
rep('''    res[R_aw_resets] = aw_resets; res[R_aw_time] = aw_time
''', '''    if prg_on or blf_on:
        res[R_prg_t0] = pg_t0
        res[R_prg_dur] = (pg_t1 - pg_t0) if (pg_t1 >= 0.0 and pg_t0 >= 0.0) else -1.0
        res[R_prg_wait] = (pg_t1 - pg_tw) if (pg_t1 >= 0.0 and pg_tw >= 0.0) else -1.0
        res[R_prg_mass] = pg_m; res[R_prg_h0] = pg_h0
        res[R_prg_tilt_max] = np.degrees(pg_tilt); res[R_prg_tilt_lift] = np.degrees(pg_tlift)
        res[R_prg_rate_max] = np.degrees(pg_rate)
        res[R_blf_t0] = bl_t0; res[R_blf_mass] = bl_m; res[R_blf_time] = bl_time; res[R_blf_kF_min] = bl_kmin
    res[R_aw_resets] = aw_resets; res[R_aw_time] = aw_time
''')
open(p, "w").write(s)
print("amendment P applied to", p)

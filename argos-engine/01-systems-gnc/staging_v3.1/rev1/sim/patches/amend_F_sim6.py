"""Apply sim6 amendment F (stuck-pintle over-thrust fault, in-loop detectors, abort) to a sim6.py file (path argument)."""
import sys

p = sys.argv[1]
s = open(p).read()


def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, (old[:80], n)
    s = s.replace(old, new)


# ---------------------------------------------------------------- docstring
rep("""   web at the end, t_L, phase, true height and truth web at t_L, action flag.
""", """   web at the end, t_L, phase, true height and truth web at t_L, action flag.
 * v2.8-dev amendment F (2026-10-13, review REV-GNC-1 RG-18; off by default, bit-identical when off, m2_bitcheck_v28 part F):
   stuck-pintle over-thrust fault flown in the loop with the detectors and the abort (flt_on 1). TRUTH: at the onset (flt_ph 1:
   flight time t >= flt_t with the engine lit in the ascent; flt_ph 5: flt_t after the landing-burn start) the delivered thrust
   leaves the command and ramps at flt_rate [N/s] from its value to flt_F [N] (held; the commands no longer reach the pintle;
   ASSUMED step-free ramp), the propellant flows follow the map at F / tsc, extrapolated at the map's top specific impulse above
   its last thrust point (ASSUMED), until the main valve (MV) is seated; then a tail-off F_seat exp(-t / tau), tau = abt_imp /
   F_seat (Combustion tail-off impulse), with the tank isolated (the segment inventory, ~20-36 g, is not deducted: ASSUMED).
   Liquid exhaustion cuts the thrust as in the base model. flt_enc 1: the pintle encoder sees the jam; 0: linkage failure the
   encoder does not see (the servo follows the commands). flt_pcl 1: Pc invalid (the ECU over-pressure check is blind).
   DETECTORS (ECU firmware v2.8.3 config.h semantics): det_fct FC_THRUST over-thrust: F_acc = m_hat f_z + D_model (the k_est_asc
   2 axial-force model on the estimated vertical velocity, fct_comp 1 = lever-arm / encoder-direction compensation), first order
   fct_tau, frames at fct_hz from phase fct_ph, valid flag = airborne (h_est > 1 m after the first exceedance) AND engine lit (ECU
   RUN) AND drogue not attached (before deployment or after release) AND before touchdown; fct_n consecutive valid frames above
   fct_thr in RUN -> ABORT; det_op over-pressure: Pc-equivalent thrust F / tsc above det_op_F (the map thrust at the 30 bar abs
   abort, DERIVED in run6) for det_op_t, any powered state, Pc valid only; det_pf PINTLE_FAULT time path (flt_enc 1 only): the
   commanded-minus-actual Pc-equivalent thrust beyond det_pf_dF (the 0.15 mm tracking band on the lift table, DERIVED) with no
   progress for det_pf_t (the healthy no-progress logic is not modelled: the detector runs only while the fault is active);
   det_geo (GNC PROPOSAL, research): h_est above h_target + geo_dh with the engine lit -> ABORT. ABORT: lit off, relight lockout,
   MV commanded abt_lat after the decision (CAN + ECU), seated abt_seat later (latch release + MV-P close). A NORMAL shutdown by
   the flight software with the pintle stuck: encoder-visible jam -> the seat timeout abt_sdto opens the MV path (PINTLE_FAULT
   usually acts first); linkage failure -> the servo seats at abt_sdenc, the ECU confirms the seat and closes the MV, no fault, no
   lockout; flt_persist 1 re-activates the fault at the next start (the linkage is still broken). Records fca (FC_THRUST filter
   output) and flts (fault state). Results: onset time and thrust, first decision time and source, MV seated time, each
   detector's own first trip time, impulse from the onset to the end of the tail-off, highest true height and vertical speed after
   the onset, false-abort flag (a decision before the onset), the FC_THRUST held maxima before and after the onset.
""")
rep('SIM6_VERSION = "sim6 v2.8-dev (2026-10-13, amendments M, W)"', 'SIM6_VERSION = "sim6 v2.8-dev (2026-10-13, amendments M, W, F)"')
# ---------------------------------------------------------------- names
rep("""PAR_NAMES += "web_on web_D0 web_Do web_lim web_kt web_nt web_kf web_nf1 web_nf2 web_kcal web_ghat web_jref web_act bpred_pc".split()
""", """PAR_NAMES += "web_on web_D0 web_Do web_lim web_kt web_nt web_kf web_nf1 web_nf2 web_kcal web_ghat web_jref web_act bpred_pc".split()
# v2.8-dev amendment F: stuck-pintle over-thrust fault, in-loop detectors (FC_THRUST, ECU over-pressure, PINTLE_FAULT, geofence
# proposal) and the abort (MV close, tail-off, relight lockout)
PAR_NAMES += ("flt_on flt_ph flt_t flt_F flt_rate flt_enc flt_pcl flt_persist det_fct det_op det_pf det_geo fct_thr fct_n fct_tau "
              "fct_hz fct_ph fct_comp det_op_F det_op_t det_pf_t det_pf_dF geo_dh abt_lat abt_seat abt_sdto abt_sdenc abt_imp").split()
""")
rep("""web_t_end web_t_t1 web_t_t0 web_f_end web_tL web_tL_phase web_tL_h web_t_at_tL web_acted
""".split("\n")[0] + "\n" + '""".split()\n', """web_t_end web_t_t1 web_t_t0 web_f_end web_tL web_tL_phase web_tL_h web_t_at_tL web_acted
flt_t0 flt_F0 flt_tdec flt_src flt_tmv flt_tseat flt_Fseat flt_imp flt_hmax flt_vzmax flt_false flt_n_on flt_end
flt_tr_fct flt_tr_op flt_tr_pf flt_tr_geo fct_held_pre fct_held_post
\"\"\".split()
""")
rep("""mhe mex
wt wf
\"\"\".split()""", """mhe mex
wt wf
fca flts
\"\"\".split()""")
# ---------------------------------------------------------------- state init
rep("""    wb_hit = False; wb_acted = 0.0
    while t < par[P_tmax]:""", """    wb_hit = False; wb_acted = 0.0
    # v2.8-dev amendment F: fault state (0 not yet, 1 stuck with the MV open, 2 MV commanded, 3 MV seated / tail-off,
    # 4 dormant after a normal close (flt_persist), 5 done), detectors, abort
    flt_on = par[P_flt_on] > 0.5
    fa_st = 0; fa_t0 = -1.0; fa_F0 = 0.0; fa_Fs = 0.0; fa_dec = -1.0; fa_src = 0.0; fa_mvt = -1.0; fa_seat = -1.0
    fa_Fst = 0.0; fa_tau = 0.05; fa_imp = 0.0; fa_hmax = 0.0; fa_vzmax = -1.0e9; fa_false = 0.0; fa_lock = False
    fa_n = 0.0; fa_sd = -1.0; fa_lit_prev = False; fa_end = 0.0
    fc_y = 0.0; fc_next = par[P_fct_ph]; fc_cnt = 0; fc_nv = 0; fc_fr = np.zeros(8); fc_air = False
    fc_hpre = 0.0; fc_hpost = 0.0; op_t = 0.0; pf_on = -1.0
    tr_fct = -1.0; tr_op = -1.0; tr_pf = -1.0; tr_geo = -1.0
    while t < par[P_tmax]:""")
# ---------------------------------------------------------------- relight lockout after an abort
rep("""            if t - t_ign_cmd >= par[P_t_ign]:
                lit = True; burning = True""", """            if t - t_ign_cmd >= par[P_t_ign] and not fa_lock:
                lit = True; burning = True""")
# ---------------------------------------------------------------- truth override after the engine block
rep("""        if F < 0.0:
            F = 0.0
        mox = 0.0; mf_ = 0.0
        if F > 0.0 and ml > resid:""", """        if F < 0.0:
            F = 0.0
        # v2.8-dev amendment F: stuck-pintle fault (truth). The state machine is documented in the module docstring.
        if flt_on:
            if fa_st == 0 and fa_dec < 0.0:
                trig_ = False
                if par[P_flt_ph] < 2.5:
                    trig_ = lit and burning and phase >= 1 and t >= par[P_flt_t]
                else:
                    trig_ = lit and burning and (phase == 5 or phase == 6) and t5 >= 0.0 and t - t5 >= par[P_flt_t]
                if trig_:
                    fa_st = 1; fa_n += 1.0; fa_Fs = F; fa_t0 = t; fa_F0 = F
            elif fa_st == 4 and lit and burning:
                # next start with the linkage still failed (flt_persist)
                fa_st = 1; fa_n += 1.0; fa_Fs = F; fa_sd = -1.0; fa_mvt = -1.0; pf_on = -1.0
            if fa_st == 1 and fa_lit_prev and (not lit) and fa_mvt < 0.0:
                # normal shutdown commanded by the flight software with the pintle stuck
                fa_sd = t
                if par[P_flt_enc] < 0.5:
                    fa_mvt = t + par[P_abt_sdenc]      # linkage failure: servo seated, seat confirmed, MV closes, no fault
                    fa_src = 5.0 if fa_dec < 0.0 else fa_src
                else:
                    fa_mvt = t + par[P_abt_sdto]       # jam seen: the seat timeout unlatches the MV (fault PINTLE)
                    fa_lock = True
                fa_st = 2
            if fa_st == 1 or fa_st == 2:
                if fa_mvt >= 0.0 and t >= fa_mvt + par[P_abt_seat]:
                    fa_st = 3
                    fa_seat = t
                    fa_Fst = fa_Fs if fa_Fs > 1.0 else 1.0
                    fa_tau = par[P_abt_imp] / fa_Fst
                else:
                    fa_Fs += par[P_flt_rate] * dt
                    if fa_Fs > par[P_flt_F]:
                        fa_Fs = par[P_flt_F]
                    F = fa_Fs; Fa_ = F; Fs_ = F; burning = True
            if fa_st == 3:
                F = fa_Fst * np.exp(-(t - fa_seat) / fa_tau)
                if F < 0.5:
                    F = 0.0
                    fa_st = 4 if (par[P_flt_persist] > 0.5 and not fa_lock) else 5
                    if not lit:
                        burning = False
                Fa_ = F; Fs_ = F
            if fa_st >= 1 and fa_st <= 3:
                fa_imp += F * dt
            if fa_t0 >= 0.0:
                hh_ = r[2] - (zcg - par[P_z_foot])
                if hh_ > fa_hmax:
                    fa_hmax = hh_
                if v[2] > fa_vzmax:
                    fa_vzmax = v[2]
            fa_lit_prev = lit
        mox = 0.0; mf_ = 0.0
        if F > 0.0 and ml > resid:""")
rep("""            mox = _bilin(Fg, Dg, tmox, F / tsc, Dp) / isc * thr_ff
            mf_ = _bilin(Fg, Dg, tmf, F / tsc, Dp) / isc * thr_ff
            if reg_on:""", """            mox = _bilin(Fg, Dg, tmox, F / tsc, Dp) / isc * thr_ff
            mf_ = _bilin(Fg, Dg, tmf, F / tsc, Dp) / isc * thr_ff
            if flt_on and F / tsc > Fg[Fg.shape[0] - 1]:
                # amendment F: above the map's last thrust point at its top specific impulse and O/F (ASSUMED)
                xr_ = (F / tsc) / Fg[Fg.shape[0] - 1]
                mox *= xr_; mf_ *= xr_
            if reg_on:""")
rep("""        elif F > 0.0:
            F = 0.0; Fa_ = 0.0; Fs_ = 0.0
        # v2.8-dev amendment W: fuel-web states""", """        elif F > 0.0:
            F = 0.0; Fa_ = 0.0; Fs_ = 0.0
            if flt_on and fa_st >= 1 and fa_st <= 2:
                fa_st = 5; fa_end = 7.0       # amendment F: liquid exhausted with the MV still open
        if flt_on and fa_st == 3:
            mox = 0.0; mf_ = 0.0              # amendment F: MV seated, tank isolated (segment inventory not deducted)
        # v2.8-dev amendment W: fuel-web states""")
# ---------------------------------------------------------------- detectors (after the flown mass estimator)
rep("""            mh_lit_prev = F > 0.0
            mh_fc_prev = fcw_
""", """            mh_lit_prev = F > 0.0
            mh_fc_prev = fcw_
        # v2.8-dev amendment F: in-loop detectors and the abort
        if flt_on:
            if (not fc_air) and (not held) and h_est > 1.0:
                fc_air = True
            fvw_ = fc_air and h_est > 1.0 and lit and (not drogue) and (not td_done)
            mfc_ = m_hat if mest_on else m_est
            fzc_ = fm[2]
            cdc_ = 1.0
            if par[P_fct_comp] > 0.5:
                fzc_ = fm[2] + (wm[0] * wm[0] + wm[1] * wm[1]) * (par[P_z_imu] - zcg)
                cdc_ = np.cos(deng[0]) * np.cos(deng[1])
            cdac_ = par[P_kest_cda_nf] if vz_e > 0.0 else par[P_drag_cda_nom]
            if legs_dep:
                cdac_ += par[P_kest_cda_legs]
            dmc_ = 0.5 * 1.2 * cdac_ * vz_e * vz_e
            fraw_ = (fzc_ * mfc_ + (dmc_ if vz_e > 0.0 else -dmc_)) / cdc_
            fc_y += (fraw_ - fc_y) * dt / par[P_fct_tau]
            dec_ = 0.0
            if t >= fc_next - 1e-9:
                fc_next += 1.0 / par[P_fct_hz]
                if fvw_:
                    for k_ in range(7, 0, -1):
                        fc_fr[k_] = fc_fr[k_ - 1]
                    fc_fr[0] = fc_y
                    fc_nv += 1
                    nn_ = int(par[P_fct_n])
                    if fc_nv >= nn_:
                        hm_ = fc_fr[0]
                        for k_ in range(1, nn_):
                            if fc_fr[k_] < hm_:
                                hm_ = fc_fr[k_]
                        if fa_t0 < 0.0:
                            if hm_ > fc_hpre:
                                fc_hpre = hm_
                        elif hm_ > fc_hpost:
                            fc_hpost = hm_
                    if fc_y > par[P_fct_thr]:
                        fc_cnt += 1
                    else:
                        fc_cnt = 0
                    if fc_cnt >= int(par[P_fct_n]):
                        if tr_fct < 0.0:
                            tr_fct = t
                        if par[P_det_fct] > 0.5:
                            dec_ = 1.0
                else:
                    fc_nv = 0; fc_cnt = 0
            # ECU over-pressure (Pc valid): Pc-equivalent thrust above the 30 bar abs map thrust for det_op_t, any powered state
            if par[P_flt_pcl] < 0.5 and burning and F / tsc > par[P_det_op_F]:
                op_t += dt
            else:
                op_t = 0.0
            if op_t >= par[P_det_op_t] - 1e-9:
                if tr_op < 0.0:
                    tr_op = t
                if par[P_det_op] > 0.5 and dec_ == 0.0:
                    dec_ = 2.0
            # PINTLE_FAULT time path (encoder sees the jam), while the fault is active
            if par[P_flt_enc] > 0.5 and (fa_st == 1 or fa_st == 2):
                cmd_ = Fcmd if lit else 0.0
                if abs(F / tsc - cmd_) > par[P_det_pf_dF]:
                    if pf_on < 0.0:
                        pf_on = t
                    if t - pf_on >= par[P_det_pf_t] - 1e-9:
                        if tr_pf < 0.0:
                            tr_pf = t
                        if par[P_det_pf] > 0.5 and dec_ == 0.0:
                            dec_ = 3.0
                else:
                    pf_on = -1.0
            # geofence (GNC proposal): estimated height above the target + geo_dh with the engine lit
            if lit and h_est > par[P_h_target] + par[P_geo_dh]:
                if tr_geo < 0.0:
                    tr_geo = t
                if par[P_det_geo] > 0.5 and dec_ == 0.0:
                    dec_ = 4.0
            if dec_ > 0.0 and fa_dec < 0.0:
                fa_dec = t; fa_src = dec_
                if fa_st == 0:
                    fa_false = 1.0
                    fa_st = 5
                fa_lock = True
                lit = False
                if phase == 1:
                    phase = 2
                mvn_ = t + par[P_abt_lat]
                if fa_mvt < 0.0 or mvn_ < fa_mvt:
                    fa_mvt = mvn_
                if fa_st == 1:
                    fa_st = 2
                fa_lit_prev = False
""")
# ---------------------------------------------------------------- records
rep("""            o[70] = 0.5 * (par[P_web_Do] - (wb_D1 if wb_D1 > wb_D2 else wb_D2)) if web_on else 0.0
            nrec += 1""", """            o[70] = 0.5 * (par[P_web_Do] - (wb_D1 if wb_D1 > wb_D2 else wb_D2)) if web_on else 0.0
            o[71] = fc_y if flt_on else 0.0
            o[72] = float(fa_st) if flt_on else 0.0
            nrec += 1""")
# ---------------------------------------------------------------- results
rep("""        res[R_web_acted] = wb_acted
""", """        res[R_web_acted] = wb_acted
    if flt_on:
        res[R_flt_t0] = fa_t0; res[R_flt_F0] = fa_F0; res[R_flt_tdec] = fa_dec; res[R_flt_src] = fa_src
        res[R_flt_tmv] = fa_mvt; res[R_flt_tseat] = fa_seat; res[R_flt_Fseat] = fa_Fst; res[R_flt_imp] = fa_imp
        res[R_flt_hmax] = fa_hmax; res[R_flt_vzmax] = fa_vzmax if fa_t0 >= 0.0 else 0.0; res[R_flt_false] = fa_false
        res[R_flt_n_on] = fa_n; res[R_flt_end] = fa_end if fa_end > 0.0 else float(fa_st)
        res[R_flt_tr_fct] = tr_fct; res[R_flt_tr_op] = tr_op; res[R_flt_tr_pf] = tr_pf; res[R_flt_tr_geo] = tr_geo
        res[R_fct_held_pre] = fc_hpre; res[R_fct_held_post] = fc_hpost
""")
open(p, "w").write(s)
print("patched", p)

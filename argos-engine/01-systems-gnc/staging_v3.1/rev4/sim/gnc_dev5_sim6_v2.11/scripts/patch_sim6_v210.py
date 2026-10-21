"""patch_sim6_v210 v1.0 (GNC rev3, 2026-10-13): applies sim6 v2.10-dev amendment V2 (R2 v2: command hold, E2 re-reference and
drogue-drag compensation, cold-flow apparent thrust after an undetected flame-out, release hold) to a copy of sim6 v2.9-dev
(f90e0ba8e993ad60). Every anchor must occur exactly once; the source hash is checked first. Run once on gnc_dev4."""
import hashlib
import sys

P = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/work/space/gnc_dev4/gncsim/sim6.py"
SRC16 = "f90e0ba8e993ad60"
s = open(P).read()
h = hashlib.sha256(s.encode()).hexdigest()[:16]
if h != SRC16:
    raise SystemExit(f"{P}: sha256/16 {h} != v2.9-dev {SRC16} (already patched?)")


def rep(old, new, count=1):
    global s
    n = s.count(old)
    if n != count:
        raise SystemExit(f"anchor found {n} times (expected {count}): {old[:90]!r}")
    s = s.replace(old, new)


# ---------------------------------------------------------------------------------------------------------- docstring
rep("""   thrust estimate, baseline specific force.
All parameters are passed in par[]""", """   thrust estimate, baseline specific force.
 * v2.10-dev amendment V2 (2026-10-13, R2 v2; LEAD CHANGELOG lines 181 (4) and 186 (1)-(2); off by default (pv2_on 0),
   bit-identical when off, m2_bitcheck_v210): (i) COMMAND HOLD (pv2_hold, adopted in design, line 186 (2)): while the drogue
   is attached with Pc invalid (after the amendment-V onset) the ECU open-loop command is held at the start level pv2_Fh
   (62.5 N, Combustion F_lift) until the release; the hold bypasses the closed-loop floor and the command quantisation, and
   the vertical-guidance integrator is frozen while it holds. (ii) R2 BASELINE MODES (pv2_bl): 0 the amendment-V form
   (baseline low-passed with pcf_tbl and frozen at E0, filtered signal initialised at E0); 1 re-reference at E2 (the
   continuously filtered axial specific force, fct_tau, sampled at the 6-DOF light); 2 = 0 plus drogue-drag compensation
   m_est fz0 (1 - (vz / vz0)^2), vz the navigation vertical velocity and vz0 its value at the baseline; 3 = 1 plus the same
   compensation referenced at E2. All four estimates are computed on every 100 Hz frame of the confirmation window and their
   pcf_n-frame running minima are recorded (maxima over E2 + 0.5 s and E2 + 0.8 s) whichever mode decides; with pcf_Facc
   very large nothing is released and the statistics cover the whole window (threshold derivation). (iii) COLD FLOW
   (pv2_cold 1 = DERIVED adiabatic bound, 2 = HEM nominal Cd 0.70; pv2_ck scales the thrust, e.g. 1.3 for chamber heat
   pick-up): after the undetected flame-out (pcf_fo) and while the ECU stays in RUN the truth thrust is the amendment-V decay
   PLUS F_cold(lift, P_tank) and the tank loses the cold-flow mass flow (Combustion cold_flow_thrust_v2p4a.csv, bilinear in
   lift and tank pressure, clamped in lift, linear in pressure); the lift is the open-loop map lift of the ECU command at
   the truth tank pressure (Combustion per-command table, cold_flow_thrust_v2p4a.json) behind a first-order lag pv2_llag
   and the drive rate pv2_lrate (HV69, 16.7 mm/s). (iv) RELEASE HOLD (pv2_rh > 0; the lead's alternative for an unpurged
   relight, line 186 (1)): no release branch may release before E2 + pv2_rh. Not modelled: lights during the vapour gap and
   the A3 abort itself (the outcome classes stay Combustion's), canopy dynamics (quasi-steady massless drogue), N2O
   decomposition or re-ignition on the hot grain, vapour in the feed line. Results: window statistics per mode, hold time,
   peak cold-flow thrust and lift, tank pressure at the onset, cold-flow mass, R2 estimate and cold-flow thrust at the
   release, release-hold flag. Records: Fcl (cold-flow thrust), lift [mm], pfa (R2 estimate of the deciding mode).
All parameters are passed in par[]""")
rep('SIM6_VERSION = "sim6 v2.9-dev (2026-10-13, amendments M, W, F, P, R, S, G, K, V)"',
    'SIM6_VERSION = "sim6 v2.10-dev (2026-10-13, amendments M, W, F, P, R, S, G, K, V, V2)"')
# ---------------------------------------------------------------------------------------------------------- parameters
rep('''PAR_NAMES += "pcf_on pcf_dt pcf_k pcf_rule pcf_Facc pcf_n pcf_tmax pcf_tbl pcf_fo".split()
''', '''PAR_NAMES += "pcf_on pcf_dt pcf_k pcf_rule pcf_Facc pcf_n pcf_tmax pcf_tbl pcf_fo".split()
# v2.10-dev amendment V2 (R2 v2): command hold, baseline modes, cold-flow thrust after an undetected flame-out, release hold;
# cold-flow tables: pv2_np tank pressures (pv2_P*), pv2_nl lifts [mm] (pv2_l*), F / mdot bound and nominal row-major
# [i_P x pv2_nl + j_l]; open-loop map lift per command: pv2_nc commands [N] (pv2_c*), lifts [mm] row-major [i_P x pv2_nc + j_c]
PAR_NAMES += "pv2_on pv2_hold pv2_Fh pv2_bl pv2_cold pv2_ck pv2_lrate pv2_llag pv2_rh pv2_np pv2_nl pv2_nc".split()
PAR_NAMES += [f"pv2_P{_k}" for _k in range(4)] + [f"pv2_l{_k}" for _k in range(24)] + [f"pv2_c{_k}" for _k in range(12)]
PAR_NAMES += [f"pv2_Fb{_k}" for _k in range(96)] + [f"pv2_Fn{_k}" for _k in range(96)]
PAR_NAMES += [f"pv2_mb{_k}" for _k in range(96)] + [f"pv2_mn{_k}" for _k in range(96)] + [f"pv2_cl{_k}" for _k in range(48)]
''')
rep('''pcf_t0 pcf_rel pcf_relt pcf_abt pcf_Facc_max pcf_fz0
''', '''pcf_t0 pcf_rel pcf_relt pcf_abt pcf_Facc_max pcf_fz0
pv2_s5_0 pv2_s5_1 pv2_s5_2 pv2_s5_3 pv2_s8_0 pv2_s8_1 pv2_s8_2 pv2_s8_3 pv2_hold_s pv2_Fcl_max pv2_l_max pv2_Pt0 pv2_mcold
pv2_fa_rel pv2_rhb pv2_Fcl_rel
''')
rep('''fca flts
""".split()''', '''fca flts
Fcl lift pfa
""".split()''')
# ---------------------------------------------------------------------------------------------------------- helpers
rep('''@njit(cache=True)
def qrot(q, v, out):''', '''@njit(cache=True)
def _pv2_lift(par, Fc, P):
    """v2.10-dev amendment V2: open-loop map lift [mm] of the ECU command Fc [N] at the tank pressure P [Pa] (Combustion
    per-command table): linear in Fc (clamped at the table ends), linear in P (extrapolated, weight held in [-1, 2])."""
    n_p = int(par[P_pv2_np]); n_c = int(par[P_pv2_nc])
    i = 0
    while i < n_p - 2 and P > par[P_pv2_P0 + i + 1]:
        i += 1
    u = (P - par[P_pv2_P0 + i]) / (par[P_pv2_P0 + i + 1] - par[P_pv2_P0 + i])
    if u < -1.0:
        u = -1.0
    if u > 2.0:
        u = 2.0
    j = 0; w = 0.0
    if Fc >= par[P_pv2_c0 + n_c - 1]:
        j = n_c - 2; w = 1.0
    elif Fc > par[P_pv2_c0]:
        while j < n_c - 2 and Fc > par[P_pv2_c0 + j + 1]:
            j += 1
        w = (Fc - par[P_pv2_c0 + j]) / (par[P_pv2_c0 + j + 1] - par[P_pv2_c0 + j])
    a0 = (1.0 - w) * par[P_pv2_cl0 + i * n_c + j] + w * par[P_pv2_cl0 + i * n_c + j + 1]
    a1 = (1.0 - w) * par[P_pv2_cl0 + (i + 1) * n_c + j] + w * par[P_pv2_cl0 + (i + 1) * n_c + j + 1]
    return (1.0 - u) * a0 + u * a1


@njit(cache=True)
def _pv2_tab(par, off, lift, P):
    """v2.10-dev amendment V2: cold-flow table value (thrust or mass flow) at lift [mm] and tank pressure P [Pa], from the
    row-major table at par slot off: linear in lift (clamped at the table ends), linear in P (weight held in [-1, 2])."""
    n_p = int(par[P_pv2_np]); n_l = int(par[P_pv2_nl])
    i = 0
    while i < n_p - 2 and P > par[P_pv2_P0 + i + 1]:
        i += 1
    u = (P - par[P_pv2_P0 + i]) / (par[P_pv2_P0 + i + 1] - par[P_pv2_P0 + i])
    if u < -1.0:
        u = -1.0
    if u > 2.0:
        u = 2.0
    j = 0; w = 0.0
    if lift >= par[P_pv2_l0 + n_l - 1]:
        j = n_l - 2; w = 1.0
    elif lift > par[P_pv2_l0]:
        while j < n_l - 2 and lift > par[P_pv2_l0 + j + 1]:
            j += 1
        w = (lift - par[P_pv2_l0 + j]) / (par[P_pv2_l0 + j + 1] - par[P_pv2_l0 + j])
    a0 = (1.0 - w) * par[off + i * n_l + j] + w * par[off + i * n_l + j + 1]
    a1 = (1.0 - w) * par[off + (i + 1) * n_l + j] + w * par[off + (i + 1) * n_l + j + 1]
    return (1.0 - u) * a0 + u * a1


@njit(cache=True)
def qrot(q, v, out):''')
# ---------------------------------------------------------------------------------------------------------- state init
rep('''    pf_fzf = 0.0; pf_cnt = 0; pf_next = 0.0
''', '''    pf_fzf = 0.0; pf_cnt = 0; pf_next = 0.0
    # v2.10-dev amendment V2 (pv_*): command hold, baseline modes, cold flow, release hold
    pv2_on = par[P_pv2_on] > 0.5
    pv_fzf = 0.0; pv_fzf_ok = False; pv_fz2 = 0.0; pv_vz0 = 0.0; pv_vz2 = 0.0
    pv_fa = np.zeros(4); pv_hist = np.zeros((4, 8)); pv_nf = 0
    pv_s5 = np.zeros(4); pv_s8 = np.zeros(4)
    for k_ in range(4):
        pv_s5[k_] = -999.0; pv_s8[k_] = -999.0
    pv_hold_ = False; pv_hold_t = 0.0
    pv_l = 0.0; pv_lc = 0.0; pv_lmax = 0.0; pv_Fcl = 0.0; pv_Fclmax = 0.0; pv_mcold = 0.0
    pv_Pt0 = 0.0; pv_farel = -999.0; pv_rhb = 0.0; pv_Fclrel = -1.0; pv_fal = 0.0
''')
# ---------------------------------------------------------------------------------------------------------- IMU filter
rep('''        n_acc += 1
''', '''        n_acc += 1
        if pv2_on and pcf_on and prof == 0 and phase >= 3:
            # amendment V2: continuously filtered axial specific force (fct_tau) for the E2 re-reference
            if not pv_fzf_ok:
                pv_fzf = fm[2]; pv_fzf_ok = True
            else:
                pv_fzf += (fm[2] - pv_fzf) * dt / par[P_fct_tau]
''')
rep('''        pcinv_ = False
''', '''        pcinv_ = False
        pv_hold_ = False
''')
# ---------------------------------------------------------------------------------------------------------- onset
rep('''                isc = isc / par[P_pcf_k]
''', '''                isc = isc / par[P_pcf_k]
                if pv2_on:
                    pv_Pt0 = Pt
                    if par[P_pv2_cold] > 0.5:
                        pv_l = _pv2_lift(par, par[P_pv2_Fh], Pt)
                        pv_lc = pv_l
''')
# ---------------------------------------------------------------------------------------------------------- E0 / light
rep('''                            pf_fz0 = pf_fzb; pf_fzf = pf_fzb
''', '''                            pf_fz0 = pf_fzb; pf_fzf = pf_fzb
                            if pv2_on:
                                pv_vz0 = vz_e
''')
rep('''                Ssv = F; drvF = F; drvV = 0.0
                phase = 5
                t5 = t
''', '''                Ssv = F; drvF = F; drvV = 0.0
                phase = 5
                t5 = t
                if pv2_on and pcf_on:
                    pv_fz2 = pv_fzf; pv_vz2 = vz_e
''')
# ---------------------------------------------------------------------------------------------------------- R2 frame
rep('''                            fa_ = m_est * (pf_fzf - pf_fz0)
                            if fa_ > pf_Fmx:
''', '''                            fa_ = m_est * (pf_fzf - pf_fz0)
                            if pv2_on:
                                # amendment V2: the four baseline modes on this frame, running minima and window maxima
                                vr0_ = vz_e / pv_vz0 if pv_vz0 < -0.5 else 1.0
                                vr2_ = vz_e / pv_vz2 if pv_vz2 < -0.5 else 1.0
                                pv_fa[0] = fa_
                                pv_fa[1] = m_est * (pv_fzf - pv_fz2)
                                pv_fa[2] = fa_ + m_est * pf_fz0 * (1.0 - vr0_ * vr0_)
                                pv_fa[3] = pv_fa[1] + m_est * pv_fz2 * (1.0 - vr2_ * vr2_)
                                nn_ = int(par[P_pcf_n])
                                if nn_ < 1:
                                    nn_ = 1
                                if nn_ > 8:
                                    nn_ = 8
                                tw_ = t - t5 - par[P_rel_dt]
                                for k_ in range(4):
                                    for j_ in range(7, 0, -1):
                                        pv_hist[k_, j_] = pv_hist[k_, j_ - 1]
                                    pv_hist[k_, 0] = pv_fa[k_]
                                pv_nf += 1
                                if pv_nf >= nn_:
                                    for k_ in range(4):
                                        mn_ = pv_hist[k_, 0]
                                        for j_ in range(1, nn_):
                                            if pv_hist[k_, j_] < mn_:
                                                mn_ = pv_hist[k_, j_]
                                        if tw_ <= 0.5 + 1e-9 and mn_ > pv_s5[k_]:
                                            pv_s5[k_] = mn_
                                        if tw_ <= 0.8 + 1e-9 and mn_ > pv_s8[k_]:
                                            pv_s8[k_] = mn_
                                bl_ = int(par[P_pv2_bl] + 0.5)
                                if bl_ >= 0 and bl_ <= 3:
                                    fa_ = pv_fa[bl_]
                                pv_fal = fa_
                            if fa_ > pf_Fmx:
''')
rep('''                                rls_ = True; rl_br = 4.0; pf_rel = 2.0
''', '''                                rls_ = True; rl_br = 4.0; pf_rel = 2.0
                                if pv2_on:
                                    pv_farel = fa_; pv_Fclrel = pv_Fcl
''')
rep('''                if rls_ and pcf_on and pcb_ and drogue:
''', '''                if pv2_on and par[P_pv2_rh] > 0.0 and rls_ and drogue and t - t5 < par[P_rel_dt] + par[P_pv2_rh] - 1e-9:
                    # amendment V2 (iv): release held to >= E2 + pv2_rh (unpurged-relight alternative, LEAD line 186 (1))
                    rls_ = False; pv_rhb = 1.0
                if rls_ and pcf_on and pcb_ and drogue:
''')
# ---------------------------------------------------------------------------------------------------------- integrator
rep('''            ev = vref - vz_e
            if not ((sat_hi and ev > 0.0) or (sat_lo and ev < 0.0)):
                ei += ev * dt
''', '''            ev = vref - vz_e
            if not ((sat_hi and ev > 0.0) or (sat_lo and ev < 0.0)) and not (
                    pv2_on and par[P_pv2_hold] > 0.5 and pcf_on and drogue and pf_t0 >= 0.0 and pf_abt == 0.0):
                ei += ev * dt
''')
# ---------------------------------------------------------------------------------------------------------- hold
rep('''                Fcmd = F_start
            if phase == 7:
                Fcmd = 0.0
''', '''                Fcmd = F_start
            if pv2_on and par[P_pv2_hold] > 0.5 and pcf_on and drogue and pf_t0 >= 0.0 and pf_abt == 0.0:
                # amendment V2 (i): ECU open-loop command held at the start level while the drogue is attached, Pc invalid
                Fcmd = par[P_pv2_Fh]
                pv_hold_ = True
                pv_hold_t += dt
            if phase == 7:
                Fcmd = 0.0
''')
rep('''            if Fcmd < fl_:
                Fcmd = fl_
''', '''            if Fcmd < fl_ and not pv_hold_:
                Fcmd = fl_
''')
rep('''            qq = par[P_quant] * Fmax
            if qq > 0:
''', '''            qq = par[P_quant] * Fmax
            if qq > 0 and not pv_hold_:
''')
# ---------------------------------------------------------------------------------------------------------- cold flow
rep('''        # v2.8-dev amendment W: fuel-web states (Combustion law_for_gnc), burn limit t_L and the shutdown comparison (web_act 2)
''', '''        if pv2_on and pf_fo and lit and par[P_pv2_cold] > 0.5 and ml > resid:
            # amendment V2 (iii): cold-flow apparent thrust after the undetected flame-out (ECU in RUN, pintle at the open-loop
            # map lift of the command behind the drive lag and rate), ADDED to the amendment-V decay; liquid leaves the tank
            fc_ = Fcmd
            if not pv_hold_:
                if fc_ < floorF:
                    fc_ = floorF
                if fc_ > Fc_avail:
                    fc_ = Fc_avail
            lq_ = _pv2_lift(par, fc_, Pt)
            pv_lc += (lq_ - pv_lc) * dt / max(par[P_pv2_llag], dt)
            dl_ = pv_lc - pv_l
            lr_ = par[P_pv2_lrate] * dt
            if dl_ > lr_:
                dl_ = lr_
            if dl_ < -lr_:
                dl_ = -lr_
            pv_l += dl_
            if pv_l > pv_lmax:
                pv_lmax = pv_l
            if par[P_pv2_cold] < 1.5:
                pv_Fcl = par[P_pv2_ck] * _pv2_tab(par, P_pv2_Fb0, pv_l, Pt)
                mdc_ = _pv2_tab(par, P_pv2_mb0, pv_l, Pt)
            else:
                pv_Fcl = par[P_pv2_ck] * _pv2_tab(par, P_pv2_Fn0, pv_l, Pt)
                mdc_ = _pv2_tab(par, P_pv2_mn0, pv_l, Pt)
            if pv_Fcl < 0.0:
                pv_Fcl = 0.0
            if mdc_ < 0.0:
                mdc_ = 0.0
            F += pv_Fcl
            blx_ += mdc_
            pv_mcold += mdc_ * dt
            if pv_Fcl > pv_Fclmax:
                pv_Fclmax = pv_Fcl
        elif pv2_on:
            pv_Fcl = 0.0
        # v2.8-dev amendment W: fuel-web states (Combustion law_for_gnc), burn limit t_L and the shutdown comparison (web_act 2)
''')
# ---------------------------------------------------------------------------------------------------------- records / results
rep('''            o[72] = float(fa_st) if flt_on else 0.0
''', '''            o[72] = float(fa_st) if flt_on else 0.0
            o[73] = pv_Fcl; o[74] = pv_l; o[75] = pv_fal
''')
rep('''        res[R_pcf_Facc_max] = pf_Fmx; res[R_pcf_fz0] = pf_fz0
''', '''        res[R_pcf_Facc_max] = pf_Fmx; res[R_pcf_fz0] = pf_fz0
    if pv2_on:
        res[R_pv2_s5_0] = pv_s5[0]; res[R_pv2_s5_1] = pv_s5[1]; res[R_pv2_s5_2] = pv_s5[2]; res[R_pv2_s5_3] = pv_s5[3]
        res[R_pv2_s8_0] = pv_s8[0]; res[R_pv2_s8_1] = pv_s8[1]; res[R_pv2_s8_2] = pv_s8[2]; res[R_pv2_s8_3] = pv_s8[3]
        res[R_pv2_hold_s] = pv_hold_t; res[R_pv2_Fcl_max] = pv_Fclmax; res[R_pv2_l_max] = pv_lmax; res[R_pv2_Pt0] = pv_Pt0
        res[R_pv2_mcold] = pv_mcold; res[R_pv2_fa_rel] = pv_farel; res[R_pv2_rhb] = pv_rhb; res[R_pv2_Fcl_rel] = pv_Fclrel
''')
open(P, "w").write(s)
print("patched", P, hashlib.sha256(s.encode()).hexdigest()[:16])

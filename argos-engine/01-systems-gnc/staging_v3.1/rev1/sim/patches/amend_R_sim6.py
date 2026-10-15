"""Apply sim6 amendment R (drogue release rule of the light-detection fix, lead / coordinator 2026-10-13) to a sim6.py file (path
argument). Requires amendments M, W, F and P already applied. v1 (GNC, 2026-10-13)."""
import sys

p = sys.argv[1]
s = open(p).read()


def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, (old[:80], n)
    s = s.replace(old, new)


rep("""   smallest thrust factor (mode 1).
""", """   smallest thrust factor (mode 1).
 * v2.8-dev amendment R (2026-10-13, coordinator relay of the light-detection fix; off by default, bit-identical when off,
   m2_bitcheck_v28 part R): DROGUE RELEASE RULE. rel_mode 0 (v2.8 model): the drogue releases when the delivered thrust exceeds
   half the floor thrust (truth F > 0.5 floor x tsc). rel_mode 1 (adopted FSW rule): release on E2 (relative light
   confirmation: Pc rise >= 0.8 bar above the pre-lift baseline held 10 ms; declared rel_dt after the 6-DOF light) AND measured
   Pc >= 3.0 bar abs, evaluated as the Pc-equivalent thrust F / tsc >= rel_F (run6 DERIVED from the map Pc(F)); Pc sensor error
   not modelled (B-PC-1 residual target <= 0.3 bar). The 6-DOF light remains the drawn start delay (RC-03 E0 -> E2 on the old
   3.0 bar absolute rule); the earlier E2 of the relative rule is represented by a start-delay shift in the run (t_ign).
   Results: release time after the light, Pc-equivalent thrust at the release.
""")
rep('SIM6_VERSION = "sim6 v2.8-dev (2026-10-13, amendments M, W, F, P)"',
    'SIM6_VERSION = "sim6 v2.8-dev (2026-10-13, amendments M, W, F, P, R)"')
rep('''PAR_NAMES += ("prg_on prg_T prg_lead prg_mdot prg_mdot_hat prg_book prg_jet prg_prio blf_on blf_ph blf_mdot blf_mode blf_n "
              "blf_fmax bl_vj bl_az").split()
''', '''PAR_NAMES += ("prg_on prg_T prg_lead prg_mdot prg_mdot_hat prg_book prg_jet prg_prio blf_on blf_ph blf_mdot blf_mode blf_n "
              "blf_fmax bl_vj bl_az").split()
# v2.8-dev amendment R: drogue release rule (E2 relative light confirmation AND measured Pc >= 3.0 bar abs)
PAR_NAMES += "rel_mode rel_F rel_dt".split()
''')
rep('''prg_t0 prg_dur prg_wait prg_mass prg_h0 prg_tilt_max prg_tilt_lift prg_rate_max blf_t0 blf_mass blf_time blf_kF_min
''', '''prg_t0 prg_dur prg_wait prg_mass prg_h0 prg_tilt_max prg_tilt_lift prg_rate_max blf_t0 blf_mass blf_time blf_kF_min
rel_t rel_Fpc
''')
rep('''    bl_t0 = -1.0; bl_m = 0.0; bl_time = 0.0; bl_kmin = 1.0
''', '''    bl_t0 = -1.0; bl_m = 0.0; bl_time = 0.0; bl_kmin = 1.0
    rl_t = -1.0; rl_F = 0.0      # amendment R: drogue release time after the light, Pc-equivalent thrust at the release
''')
rep('''            if drogue and F > 0.5 * floorF * tsc:
                drogue = False
''', '''            if par[P_rel_mode] > 0.5:
                # amendment R: release on E2 (rel_dt after the 6-DOF light) AND measured Pc >= 3.0 bar abs (F / tsc >= rel_F)
                rls_ = t - t5 >= par[P_rel_dt] - 1e-9 and F / tsc >= par[P_rel_F]
            else:
                rls_ = F > 0.5 * floorF * tsc
            if drogue and rls_:
                drogue = False
                rl_t = t - t5; rl_F = F / tsc
''')
rep('''    res[R_aw_resets] = aw_resets; res[R_aw_time] = aw_time
    res[R_act_sat_max_t1] = act_sat_max_t1; res[R_t_relight] = t_relight
''', '''    res[R_rel_t] = rl_t; res[R_rel_Fpc] = rl_F
    res[R_aw_resets] = aw_resets; res[R_aw_time] = aw_time
    res[R_act_sat_max_t1] = act_sat_max_t1; res[R_t_relight] = t_relight
''')
open(p, "w").write(s)
print("amendment R applied to", p)

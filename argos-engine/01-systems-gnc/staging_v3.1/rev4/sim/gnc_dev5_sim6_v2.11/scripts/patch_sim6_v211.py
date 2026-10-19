"""patch_sim6_v211 v1.0 (GNC rev3, 2026-10-13): sim6 v2.11-dev amendment L - the RG-16 detection-latency allowance flown as a
forced abort decision (LEAD CHANGELOG line 181 (3)). Source sim6 v2.10-dev 1f92061d41db894a; every anchor must occur exactly
once. Off by default (flt_dla < 0): bit-identical when off (m2_bitcheck_v211)."""
import hashlib
import sys

P = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/work/space/gnc_dev5/gncsim/sim6.py"
SRC16 = "1f92061d41db894a"
s = open(P).read()
h = hashlib.sha256(s.encode()).hexdigest()[:16]
if h != SRC16:
    raise SystemExit(f"{P}: sha256/16 {h} != v2.10-dev {SRC16} (already patched?)")


def rep(old, new, count=1):
    global s
    n = s.count(old)
    if n != count:
        raise SystemExit(f"anchor found {n} times (expected {count}): {old[:90]!r}")
    s = s.replace(old, new)


HT = "r[2] - (zcg - par[P_z_foot])"
# ---------------------------------------------------------------------------------------------------------- docstring
rep("""pfa (R2 estimate of the deciding mode).
All parameters are passed in par[]""", """pfa (R2 estimate of the deciding mode).
 * v2.11-dev amendment L (2026-10-13, RG-16 detection-latency allowance; LEAD CHANGELOG line 181 (3); off by default
   (flt_dla < 0), bit-identical when off, m2_bitcheck_v211): with the stuck-pintle fault flown (flt_on 1), a FORCED abort
   decision (source 5) flt_dla seconds after the onset of the plateau of the current activation (the first instant the truth
   stuck thrust reaches flt_F; a re-activation at a later start restarts the plateau clock), taken only while the flight
   software holds the engine lit (the FC_THRUST validity condition of the ECU RUN state). The abort then follows amendment F
   (relight lockout, MV commanded abt_lat later, seated abt_seat after, tail-off). The detectors stay as configured; the
   allowance arms switch them off so that the decision falls exactly at the allowance. Results (first activation): plateau
   onset time, vertical velocity and true height at the fault onset, at the plateau onset, at the decision and at the end of
   the first tail-off, the time of that end and the vehicle mass at the decision.
All parameters are passed in par[]""")
rep('SIM6_VERSION = "sim6 v2.10-dev (2026-10-13, amendments M, W, F, P, R, S, G, K, V, V2)"',
    'SIM6_VERSION = "sim6 v2.11-dev (2026-10-13, amendments M, W, F, P, R, S, G, K, V, V2, L)"')
# ---------------------------------------------------------------------------------------------------------- parameters / results
rep('''PAR_NAMES += [f"pv2_mb{_k}" for _k in range(96)] + [f"pv2_mn{_k}" for _k in range(96)] + [f"pv2_cl{_k}" for _k in range(48)]
''', '''PAR_NAMES += [f"pv2_mb{_k}" for _k in range(96)] + [f"pv2_mn{_k}" for _k in range(96)] + [f"pv2_cl{_k}" for _k in range(48)]
# v2.11-dev amendment L: forced abort decision flt_dla [s] after the plateau onset of the stuck-pintle fault (< 0 = off)
PAR_NAMES += ["flt_dla"]
''')
rep('''pv2_fa_rel pv2_rhb pv2_Fcl_rel
""".split()''', '''pv2_fa_rel pv2_rhb pv2_Fcl_rel
flt_tpl flt_vz0 flt_h0 flt_vzpl flt_hpl flt_vzdec flt_hdec flt_mdec flt_ttoe flt_vztoe flt_htoe
""".split()''')
# ---------------------------------------------------------------------------------------------------------- state
rep('''    fa_n = 0.0; fa_sd = -1.0; fa_lit_prev = False; fa_end = 0.0
''', '''    fa_n = 0.0; fa_sd = -1.0; fa_lit_prev = False; fa_end = 0.0
    # v2.11-dev amendment L: plateau onset of the current activation (fl_tpa), first-activation records
    fl_tpa = -1.0; fl_tpl = -1.0; fl_vz0 = 0.0; fl_h0 = 0.0; fl_vzpl = 0.0; fl_hpl = 0.0; fl_vzd = 0.0; fl_hd = 0.0
    fl_md = 0.0; fl_te = -1.0; fl_vze = 0.0; fl_he = 0.0
''')
# ---------------------------------------------------------------------------------------------------------- truth
rep('''                    fa_st = 1; fa_n += 1.0; fa_Fs = F; fa_t0 = t; fa_F0 = F
''', '''                    fa_st = 1; fa_n += 1.0; fa_Fs = F; fa_t0 = t; fa_F0 = F
                    fl_vz0 = v[2]; fl_h0 = ''' + HT + '''
''')
rep('''                fa_st = 1; fa_n += 1.0; fa_Fs = F; fa_mvt = -1.0; pf_on = -1.0
''', '''                fa_st = 1; fa_n += 1.0; fa_Fs = F; fa_mvt = -1.0; pf_on = -1.0
                fl_tpa = -1.0                  # amendment L: the plateau clock restarts with the re-activation
''')
rep('''                    fa_Fs += par[P_flt_rate] * dt
                    if fa_Fs > par[P_flt_F]:
                        fa_Fs = par[P_flt_F]
''', '''                    fa_Fs += par[P_flt_rate] * dt
                    if fa_Fs > par[P_flt_F]:
                        fa_Fs = par[P_flt_F]
                    if fl_tpa < 0.0 and fa_Fs >= par[P_flt_F] - 1e-9:
                        fl_tpa = t             # amendment L: plateau onset of this activation
                        if fl_tpl < 0.0:
                            fl_tpl = t; fl_vzpl = v[2]; fl_hpl = ''' + HT + '''
''')
rep('''                if F < 0.5:
                    F = 0.0
                    fa_st = 4 if (par[P_flt_persist] > 0.5 and not fa_lock) else 5
''', '''                if F < 0.5:
                    F = 0.0
                    fa_st = 4 if (par[P_flt_persist] > 0.5 and not fa_lock) else 5
                    if fl_te < 0.0:
                        fl_te = t; fl_vze = v[2]; fl_he = ''' + HT + '''
''')
# ---------------------------------------------------------------------------------------------------------- decision
rep('''            if dec_ > 0.0 and fa_dec < 0.0:
                fa_dec = t; fa_src = dec_
''', '''            # v2.11-dev amendment L: forced decision at the latency allowance after the plateau onset (engine lit)
            if par[P_flt_dla] >= 0.0 and fl_tpa >= 0.0 and lit and dec_ == 0.0 and t >= fl_tpa + par[P_flt_dla] - 1e-9:
                dec_ = 5.0
            if dec_ > 0.0 and fa_dec < 0.0:
                fa_dec = t; fa_src = dec_
                fl_vzd = v[2]; fl_hd = ''' + HT + '''; fl_md = m_tot
''')
rep('''        res[R_fct_held_pre] = fc_hpre; res[R_fct_held_post] = fc_hpost
''', '''        res[R_fct_held_pre] = fc_hpre; res[R_fct_held_post] = fc_hpost
        res[R_flt_tpl] = fl_tpl; res[R_flt_vz0] = fl_vz0; res[R_flt_h0] = fl_h0; res[R_flt_vzpl] = fl_vzpl
        res[R_flt_hpl] = fl_hpl; res[R_flt_vzdec] = fl_vzd; res[R_flt_hdec] = fl_hd; res[R_flt_mdec] = fl_md
        res[R_flt_ttoe] = fl_te; res[R_flt_vztoe] = fl_vze; res[R_flt_htoe] = fl_he
''')
open(P, "w").write(s)
print("patched", P, hashlib.sha256(s.encode()).hexdigest()[:16])

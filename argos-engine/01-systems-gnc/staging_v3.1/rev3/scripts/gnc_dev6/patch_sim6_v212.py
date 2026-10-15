"""patch_sim6_v212 v1.0 (GNC rev3, 2026-10-13): sim6 v2.12-dev amendment V3 - the ECU command profile flown while the drogue
release is held for the unpurged-relight comparator (LEAD CHANGELOG line 194 (3), REV-COMB-3 R3-01: the admissible hold
depends on the post-E2 command profile: H >= 0.30 s on the 2500 N/s ramp to 200 N, H >= 0.19 s on the ramp to 500 N, no hold
within W with the flow held at the start lift). Source sim6 v2.11-dev 8ae4ecdc5ac910dc; every anchor must occur exactly once.
Off by default (pv2_rhF 0): bit-identical when off (m2_bitcheck_v212)."""
import hashlib
import sys

P = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/work/space/gnc_dev6/gncsim/sim6.py"
SRC16 = "8ae4ecdc5ac910dc"
s = open(P).read()
h = hashlib.sha256(s.encode()).hexdigest()[:16]
if h != SRC16:
    raise SystemExit(f"{P}: sha256/16 {h} != v2.11-dev {SRC16} (already patched?)")


def rep(old, new, count=1):
    global s
    n = s.count(old)
    if n != count:
        raise SystemExit(f"anchor found {n} times (expected {count}): {old[:90]!r}")
    s = s.replace(old, new)


ACT = ("pv2_on and par[P_pv2_rhF] > 0.0 and par[P_pv2_rh] > 0.0 and drogue and t5 >= 0.0 and "
       "t - t5 < par[P_rel_dt] + par[P_pv2_rh] - 1e-9")
# ---------------------------------------------------------------------------------------------------------- docstring
rep("""   the first tail-off, the time of that end and the vehicle mass at the decision.
All parameters are passed in par[]""", """   the first tail-off, the time of that end and the vehicle mass at the decision.
 * v2.12-dev amendment V3 (2026-10-13, LEAD CHANGELOG line 194 (3), REV-COMB-3 R3-01; off by default (pv2_rhF 0),
   bit-identical when off, m2_bitcheck_v212): with the amendment-V2 release hold active (pv2_rh > 0), the ECU command from
   E2 until the release (drogue attached, t - E2 < rel_dt + pv2_rh) is pv2_rhF [N] (e.g. 200 or 500 N: Combustion's 'ramp
   to 200 N / 500 N' profiles; the rise to it follows the engine and command-rate model of the flight, not an imposed 2500
   N/s), with the start-level-hold semantics of V2 (i): closed-loop floor and command quantisation bypassed, the vertical
   guidance integrator frozen. The V2 (i) Pc-invalid start-level hold, when active, takes precedence (lead 186 (2): the
   alternative is not admissible with Pc invalid). Not modelled: the post-light vapour gap and the A3 trip (the outcome
   classes stay Combustion's per-record table). Results: time under the profile, largest truth thrust under it.
All parameters are passed in par[]""")
rep('SIM6_VERSION = "sim6 v2.11-dev (2026-10-13, amendments M, W, F, P, R, S, G, K, V, V2, L)"',
    'SIM6_VERSION = "sim6 v2.12-dev (2026-10-13, amendments M, W, F, P, R, S, G, K, V, V2, L, V3)"')
# ---------------------------------------------------------------------------------------------------------- parameters / results
rep('''PAR_NAMES += ["flt_dla"]
''', '''PAR_NAMES += ["flt_dla"]
# v2.12-dev amendment V3: ECU command [N] flown during the release hold of V2 (iv) (0 = off: the guidance command)
PAR_NAMES += ["pv2_rhF"]
''')
rep('''flt_tpl flt_vz0 flt_h0 flt_vzpl flt_hpl flt_vzdec flt_hdec flt_mdec flt_ttoe flt_vztoe flt_htoe
""".split()''', '''flt_tpl flt_vz0 flt_h0 flt_vzpl flt_hpl flt_vzdec flt_hdec flt_mdec flt_ttoe flt_vztoe flt_htoe
pv3_rhp_s pv3_Frhp_max
""".split()''')
# ---------------------------------------------------------------------------------------------------------- state
rep('''    pv_Pt0 = 0.0; pv_farel = -999.0; pv_rhb = 0.0; pv_Fclrel = -1.0; pv_fal = 0.0
''', '''    pv_Pt0 = 0.0; pv_farel = -999.0; pv_rhb = 0.0; pv_Fclrel = -1.0; pv_fal = 0.0
    pv_rhp_t = 0.0; pv_rhp_Fmx = 0.0      # v2.12-dev amendment V3
''')
# ---------------------------------------------------------------------------------------------------------- guidance integrator
rep('''            if not ((sat_hi and ev > 0.0) or (sat_lo and ev < 0.0)) and not (
                    pv2_on and par[P_pv2_hold] > 0.5 and pcf_on and drogue and pf_t0 >= 0.0 and pf_abt == 0.0):
''', '''            if not ((sat_hi and ev > 0.0) or (sat_lo and ev < 0.0)) and not (
                    pv2_on and par[P_pv2_hold] > 0.5 and pcf_on and drogue and pf_t0 >= 0.0 and pf_abt == 0.0) and not (
                    ''' + ACT + '''):
''')
# ---------------------------------------------------------------------------------------------------------- command
rep('''            if pv2_on and par[P_pv2_hold] > 0.5 and pcf_on and drogue and pf_t0 >= 0.0 and pf_abt == 0.0:
                # amendment V2 (i): ECU open-loop command held at the start level while the drogue is attached, Pc invalid
''', '''            if ''' + ACT + ''':
                # v2.12-dev amendment V3: command profile during the release hold (LEAD line 194 (3)); V2 (i) below wins
                Fcmd = par[P_pv2_rhF]
                pv_hold_ = True
                pv_rhp_t += dt
                if F > pv_rhp_Fmx:
                    pv_rhp_Fmx = F
            if pv2_on and par[P_pv2_hold] > 0.5 and pcf_on and drogue and pf_t0 >= 0.0 and pf_abt == 0.0:
                # amendment V2 (i): ECU open-loop command held at the start level while the drogue is attached, Pc invalid
''')
# ---------------------------------------------------------------------------------------------------------- results
rep('''        res[R_pv2_mcold] = pv_mcold; res[R_pv2_fa_rel] = pv_farel; res[R_pv2_rhb] = pv_rhb; res[R_pv2_Fcl_rel] = pv_Fclrel
''', '''        res[R_pv2_mcold] = pv_mcold; res[R_pv2_fa_rel] = pv_farel; res[R_pv2_rhb] = pv_rhb; res[R_pv2_Fcl_rel] = pv_Fclrel
        res[R_pv3_rhp_s] = pv_rhp_t; res[R_pv3_Frhp_max] = pv_rhp_Fmx
''')
open(P, "w").write(s)
print("patched", P, hashlib.sha256(s.encode()).hexdigest()[:16])

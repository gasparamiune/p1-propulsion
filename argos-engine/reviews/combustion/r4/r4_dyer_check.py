"""REV-COMB-4 reviewer script: independent Dyer / SPI / HEM liquid mass flux of saturated N2O at the three relight tank states, against
the author's G_L 56843 kg/m2s at 289.5 K (retained_vapour_v341_v2p4 constant) and the tank-state rate ratios used in the purge basis
(purge_basis_line216_v2p4b uncertainty.tank_state: two-tap liquid rate 29.40 / 31.2416 / 33.20 g/s at 283.15 / 289.5 / 297.15 K).

G_SPI = sqrt(2 rho_l (P1 - P2)); G_HEM = max over P2' in [P2, P1] of rho(P2', s1) sqrt(2 (h1 - h(P2', s1))) (isentropic homogeneous
equilibrium from saturated liquid, choked maximum); Dyer kappa = sqrt((P1 - P2) / (Pv - P2)) = 1 for saturated liquid, so
G_Dyer = (kappa G_SPI + G_HEM) / (1 + kappa) = (G_SPI + G_HEM) / 2.  P2 = 1.01325 bar (vent to ambient, ASSUMED: the bleed taps vent
overboard).  CoolProp HEOS NitrousOxide.
Tags: DERIVED (CoolProp properties; Dyer model ASSUMED, as the author's).  Not physical evidence.
usage: python -I r4_dyer_check.py OUT_JSON
"""
import hashlib, json, sys
import numpy as np
import CoolProp.CoolProp as CP

out_f = sys.argv[1]
F = 'NitrousOxide'; P2 = 101325.0
res = dict(script='r4_dyer_check.py', script_sha16=hashlib.sha256(open(sys.argv[0], 'rb').read()).hexdigest()[:16],
           CoolProp=CP.get_global_param_string('version'), P2_Pa=P2, states={})
AUTH_RL = {283.15: 29.40, 289.5: 31.2416, 297.15: 33.20}
for T in (283.15, 289.5, 297.15):
    P1 = CP.PropsSI('P', 'T', T, 'Q', 0, F); rl = CP.PropsSI('D', 'T', T, 'Q', 0, F)
    h1 = CP.PropsSI('H', 'T', T, 'Q', 0, F); s1 = CP.PropsSI('S', 'T', T, 'Q', 0, F)
    g_spi = float(np.sqrt(2 * rl * (P1 - P2)))
    best = 0.0; pbest = None
    for p in np.linspace(P2, P1 * 0.999, 4000):
        try:
            h2 = CP.PropsSI('H', 'P', p, 'S', s1, F); r2 = CP.PropsSI('D', 'P', p, 'S', s1, F)
        except ValueError:
            continue
        g = r2 * np.sqrt(max(2 * (h1 - h2), 0.0))
        if g > best:
            best, pbest = float(g), float(p)
    g_dyer = 0.5 * (g_spi + best)
    res['states'][f'{T}'] = dict(P_sat_bar=round(P1 / 1e5, 4), rho_l=round(rl, 3), G_SPI=round(g_spi, 1), G_HEM_choked=round(best, 1),
                                 P_choke_bar=round(pbest / 1e5, 3), G_Dyer=round(g_dyer, 1))
ref = res['states']['289.5']['G_Dyer']
for T in (283.15, 289.5, 297.15):
    s = res['states'][f'{T}']
    s['ratio_to_289p5'] = round(s['G_Dyer'] / ref, 5)
    s['author_liquid_rate_ratio'] = round(AUTH_RL[T] / AUTH_RL[289.5], 5)
res['author_G_L_289p5'] = 56843.0
res['reviewer_minus_author_G_L_289p5_pct'] = round(100 * (ref / 56843.0 - 1), 3)
json.dump(res, open(out_f, 'w'), indent=1)
print(json.dumps(res, indent=1))

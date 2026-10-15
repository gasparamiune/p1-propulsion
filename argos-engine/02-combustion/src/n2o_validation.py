"""N2O property validation (Combustion v2, brief task 2.1).

Compares CoolProp 'NitrousOxide' (Lemmon & Span 2006 short EOS) saturation properties with an independent
representation of measured data: the ESDU 91022 saturation correlations for N2O, as transcribed in
R. Newlands, 'Modelling the nitrous run tank emptying', Aspire Space technical paper (coefficients and forms
reproduced below; the ESDU original was NOT accessible -> tag LITERATURE-UNVERIFIED (secondary transcription)).
Also: critical constants, near-critical behaviour (the EOS remains continuous to Tc; the correlations are fits to
data with their own Tc = 309.57 K / pc = 7.251 MPa), and transport-property availability (CoolProp 8 has NO
viscosity/conductivity model for N2O -> CO2 corresponding-states surrogate used in the tank heat-transfer closure).
Outputs: data/v2/n2o_validation_v2.csv, n2o_validation_v2.json, figs/v2/n2o_validation_v2.png
"""
from __future__ import annotations
import csv, json, os, sys
import numpy as np
import CoolProp.CoolProp as CP

F = 'NitrousOxide'
# ESDU 91022 (via Newlands/Aspire Space)  -- LITERATURE-UNVERIFIED secondary transcription
E_TC, E_PC, E_RHOC = 309.57, 7.251e6, 452.0
B_P = [-6.71893, 1.35966, -1.3779, -4.051]; X_P = [1.0, 1.5, 2.5, 5.0]
B_RL = [1.72328, -0.83950, 0.51060, -0.10412]
B_RV = [-1.00900, -6.28792, 7.50332, -7.90463, 0.629427]
B_HL = [-200.0, 116.043, -917.225, 794.779, -589.587]
B_HV = [-200.0, 440.055, -459.701, 434.081, -485.338]


def esdu(T):
    Tr = T / E_TC; a = 1 - Tr
    p = E_PC * np.exp(sum(b * a ** x for b, x in zip(B_P, X_P)) / Tr)
    rl = E_RHOC * np.exp(sum(b * a ** ((i + 1) / 3) for i, b in enumerate(B_RL)))
    rv = E_RHOC * np.exp(sum(b * (1 / Tr - 1) ** ((i + 1) / 3) for i, b in enumerate(B_RV)))
    hl = B_HL[0] + sum(B_HL[i] * a ** (i / 3) for i in range(1, 5))
    hv = B_HV[0] + sum(B_HV[i] * a ** (i / 3) for i in range(1, 5))
    return dict(P=p, rho_l=rl, rho_v=rv, h_fg=(hv - hl) * 1e3)


def coolprop(T):
    d = {}
    d['P'] = CP.PropsSI('P', 'T', T, 'Q', 0, F)
    d['rho_l'] = CP.PropsSI('D', 'T', T, 'Q', 0, F); d['rho_v'] = CP.PropsSI('D', 'T', T, 'Q', 1, F)
    d['h_fg'] = CP.PropsSI('H', 'T', T, 'Q', 1, F) - CP.PropsSI('H', 'T', T, 'Q', 0, F)
    d['sigma'] = CP.PropsSI('I', 'T', T, 'Q', 0, F)
    d['cp_l'] = CP.PropsSI('C', 'T', T, 'Q', 0, F)
    return d


def main(out_data, out_fig):
    Ts = np.concatenate([np.arange(230.0, 300.0, 5.0), np.arange(300.0, 309.0, 1.0), [309.0, 309.2, 309.4, 309.5]])
    rows = []
    for T in Ts:
        c = coolprop(T); e = esdu(T)
        r = dict(T_K=T, T_C=T - 273.15)
        for k in ('P', 'rho_l', 'rho_v', 'h_fg'):
            r[f'{k}_CoolProp'] = c[k]; r[f'{k}_ESDU'] = e[k]; r[f'{k}_dev_pct'] = 100 * (c[k] / e[k] - 1)
        r['sigma_CoolProp_N_m'] = c['sigma']; r['cp_l_CoolProp'] = c['cp_l']
        rows.append(r)
    fn = os.path.join(out_data, 'n2o_validation_v2.csv')
    with open(fn, 'w', newline='') as f:
        f.write('# N2O saturation: CoolProp 8.0 (Lemmon & Span 2006 EOS) vs ESDU 91022 correlations (secondary transcription, '
                'Newlands/Aspire Space; LITERATURE-UNVERIFIED). dev_pct = 100 (CoolProp/ESDU - 1). SI units.\n')
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    def band(lo, hi, k):
        v = [abs(r[f'{k}_dev_pct']) for r in rows if lo <= r['T_K'] <= hi]
        return max(v) if v else None
    summ = dict(
        coolprop_version=__import__('CoolProp').__version__,
        critical_CoolProp=dict(T_K=CP.PropsSI('Tcrit', F), p_Pa=CP.PropsSI('pcrit', F), rho=CP.PropsSI('rhocrit', F)),
        critical_ESDU=dict(T_K=E_TC, p_Pa=E_PC, rho=E_RHOC),
        max_abs_dev_pct={rng: {k: band(*lims, k) for k in ('P', 'rho_l', 'rho_v', 'h_fg')}
                         for rng, lims in {'230-290K': (230, 290), '290-300K': (290, 300), '300-305K': (300, 305),
                                           '305-309.5K': (305, 309.5)}.items()},
        operating_window_K=[288.15, 298.15],
        transport='CoolProp 8 provides no viscosity/thermal-conductivity model for NitrousOxide; tank heat-transfer closure uses '
                  'CO2 (CoolProp) at the same reduced temperature as a corresponding-states surrogate (ASSUMED).',
        verdict='',
    )
    m = summ['max_abs_dev_pct']
    summ['verdict'] = (f"In the operating window 15-25 C (and up to 300 K) the two representations agree within "
                       f"{max(m['290-300K'].values()):.2f} % (P, rho_l, rho_v, h_fg); below 290 K within {max(m['230-290K'].values()):.2f} %; "
                       f"300-305 K within {max(m['300-305K'].values()):.1f} %. Within 4 K of Tc the deviations grow to "
                       f"{max(m['305-309.5K'].values()):.0f} % (h_fg) because the two critical points differ (Tc 309.52 vs 309.57 K) and "
                       "saturated properties vary steeply there. Use: CoolProp with ~1 % property uncertainty up to 300 K (27 C), ~2 % to 305 K; "
                       "30-36 C (never a planned condition: ENG-12 20+/-3 C) is a hazard regime, not a design point.")
    json.dump(summ, open(os.path.join(out_data, 'n2o_validation_v2.json'), 'w'), indent=1, default=float)
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    T = np.array([r['T_K'] for r in rows])
    for k, lab in (('P', 'p_sat'), ('rho_l', 'rho_l'), ('rho_v', 'rho_v'), ('h_fg', 'h_fg')):
        ax[1].plot(T - 273.15, [r[f'{k}_dev_pct'] for r in rows], 'o-', ms=3, label=lab)
    ax[1].axvspan(15, 25, color='0.9'); ax[1].set_ylim(-6, 6); ax[1].grid(alpha=.3)
    ax[1].set_xlabel('T [C]'); ax[1].set_ylabel('CoolProp / ESDU 91022 - 1 [%]'); ax[1].legend(fontsize=8)
    ax[1].set_title('deviation (grey: conditioning window 15-25 C)', fontsize=9)
    ax0 = ax[0]; ax0b = ax0.twinx()
    ax0.plot(T - 273.15, [r['P_CoolProp'] / 1e6 for r in rows], 'k-', label='p_sat CoolProp')
    ax0.plot(T - 273.15, [r['P_ESDU'] / 1e6 for r in rows], 'k--', label='p_sat ESDU')
    ax0b.plot(T - 273.15, [r['rho_l_CoolProp'] for r in rows], 'b-'); ax0b.plot(T - 273.15, [r['rho_l_ESDU'] for r in rows], 'b--')
    ax0b.plot(T - 273.15, [r['rho_v_CoolProp'] for r in rows], 'r-'); ax0b.plot(T - 273.15, [r['rho_v_ESDU'] for r in rows], 'r--')
    ax0.set_xlabel('T [C]'); ax0.set_ylabel('p_sat [MPa]'); ax0b.set_ylabel('rho_l (blue), rho_v (red) [kg/m3]')
    ax0.set_title('N2O saturation: solid CoolProp, dashed ESDU 91022', fontsize=9); ax0.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(os.path.join(out_fig, 'n2o_validation_v2.png'), dpi=140)
    print(json.dumps(summ, indent=1, default=float))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

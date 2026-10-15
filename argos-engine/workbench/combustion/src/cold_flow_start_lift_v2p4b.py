"""Start-lift conditions of the cold-flow bound and the CF-3 start-lift acceptance (Combustion v2.4b, 2026-10-13).

REV-COMB-3 R3-05/R3-14 and LEAD CHANGELOG line 194 (4): the 186 (2) command hold keeps the dead-engine apparent thrust at the start
level within the 16.31 N W10 < 6 m/s margin only CONDITIONALLY on Cd x A x G at the start lift, which no test accepts (CF-1/CF-3 accept
Cd <= 0.80 at full stroke only).  Using the v2.4a bound functions unchanged (cold_flow_thrust_v2p4a.py imported, b4cbf147753ecc7c), for
the three tank states (283.15 / 286.7 / 289.5 K) this script gives
  (1) the start-level map lift and bound, and the factor on Cd x A x G that uses up the 16.31 N margin;
  (2) the lift offset at the start lift that uses it up (bound at Cd 0.80);
  (3) the flux sensitivity: single-phase incompressible against Dyer at the saturated inlet (k = 1);
  (4) the CF-3 start-lift acceptance: mdot <= 16.31 N / v(dh) and F <= 16.31 N - heat allowance, for a heat allowance dh added at tank
      pressure before the throttling (injector-body / feed soak-back, TO-VERIFY): heat allowance in N = mdot_lim x (v(dh) - v(0));
  (5) the heat at tank pressure that takes the start-level bound to 16.31 N (kJ/kg and kW).
Tags: DERIVED (CoolProp HEOS, Dyer/HEM fluxes, isentropic equilibrium expansion to 1 atm) on ASSUMED Cd <= 0.80 and the map lift; not
physical evidence.
usage: python -I cold_flow_start_lift_v2p4b.py THROTTLE_MAP_S230 OUT_JSON
"""
from __future__ import annotations
import hashlib, json, os, sys
sys.dont_write_bytecode = True
import numpy as np
from scipy.optimize import brentq
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import cold_flow_thrust_v2p4a as CF

EXPECT_SRC = {'cold_flow_thrust_v2p4a.py': 'b4cbf147753ecc7c', 'injector.py': '4ee8e0a1b4825a09'}
F_W10 = 16.31            # N, GNC W10 < 6 m/s margin (REVIEW-GNC-R2 / REPORT §7.3)
F_ALL = 4.16             # N, all-winds margin
DH_KJ = (0.0, 10.0, 20.0, 30.0, 50.0, 75.0, 100.0)


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def main(map_fn, out_f):
    for f, h in EXPECT_SRC.items():
        assert sha16(os.path.join(HERE, f)) == h, (f, sha16(os.path.join(HERE, f)))
    assert sha16(map_fn) == CF.EXPECT_MAP, sha16(map_fn)
    M = CF.load_map(map_fn)
    res = {}
    for lab, T in CF.T_STATES.items():
        st = CF.sat_liq(T)
        h0 = CF.map_lift(M, CF.F_START, st['P'])
        v0 = CF.v_iso(st['h'], st['s'], CF.PA)[0]
        mb, G = CF.mdot_bound(h0, T)
        Fb = mb * v0
        f_h = lambda h: CF.mdot_bound(h, T)[0] * v0 - F_W10
        h16 = brentq(f_h, h0, 1.0e-3, xtol=1e-12)
        h4 = brentq(lambda h: CF.mdot_bound(h, T)[0] * v0 - F_ALL, 1e-6, h0, xtol=1e-12) if CF.mdot_bound(1e-6, T)[0] * v0 < F_ALL < Fb else None
        r = dict(T_K=T, P_tank_bar=st['P'] / 1e5, start_lift_mm=1e3 * h0, v_iso_eq_m_s=v0, mdot_bound_g_s=1e3 * mb, F_bound_N=Fb,
                 G_dyer_kg_m2s=G['G_dyer'], G_spi_kg_m2s=G['G_spi'], G_hem_kg_m2s=G['G_hem'], G_spi_over_dyer=G['G_spi'] / G['G_dyer'],
                 F_bound_with_SPI_flux_N=Fb * G['G_spi'] / G['G_dyer'],
                 factor_on_CdAG_to_16p31N=F_W10 / Fb, lift_for_16p31N_mm=1e3 * h16, lift_offset_to_16p31N_mm=1e3 * (h16 - h0),
                 lift_for_4p16N_mm=(1e3 * h4) if h4 else None)
        acc = []
        for dh in DH_KJ:
            v = CF.v_heated(T, dh * 1e3, CF.PA) if dh > 0 else v0
            m_lim = F_W10 / v
            acc.append(dict(dh_kJ_kg=dh, v_m_s=v, mdot_limit_g_s=1e3 * m_lim, heat_allowance_N=m_lim * (v - v0),
                            F_limit_cold_N=F_W10 - m_lim * (v - v0), heat_kW_at_mdot_limit=m_lim * dh,
                            F_bound_start_lift_N=mb * v))
        r['cf3_acceptance_by_heat_allowance'] = acc
        dh16 = brentq(lambda x: mb * CF.v_heated(T, x, CF.PA) - F_W10, 1.0, 400e3, xtol=1e-3)
        r['heat_to_16p31N_at_start_lift_kJ_kg'] = dh16 / 1e3
        r['heat_to_16p31N_at_start_lift_kW'] = mb * dh16 / 1e3
        res[lab] = r
    rng = lambda k: [min(r[k] for r in res.values()), max(r[k] for r in res.values())]
    summ = dict(start_lift_mm=rng('start_lift_mm'), F_bound_N=rng('F_bound_N'), factor_on_CdAG=rng('factor_on_CdAG_to_16p31N'),
                lift_offset_mm=rng('lift_offset_to_16p31N_mm'), G_spi_over_dyer=rng('G_spi_over_dyer'),
                F_bound_SPI_N=rng('F_bound_with_SPI_flux_N'), mdot_limit_no_heat_g_s=[min(r['cf3_acceptance_by_heat_allowance'][0]['mdot_limit_g_s'] for r in res.values()),
                                                                                    max(r['cf3_acceptance_by_heat_allowance'][0]['mdot_limit_g_s'] for r in res.values())],
                heat_to_16p31N_kJ_kg=rng('heat_to_16p31N_at_start_lift_kJ_kg'), heat_to_16p31N_kW=rng('heat_to_16p31N_at_start_lift_kW'))
    out = dict(version='v2.4b', date='2026-10-13', script='02-combustion/src/cold_flow_start_lift_v2p4b.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               request='REV-COMB-3 R3-05/R3-14; LEAD CHANGELOG line 194 (4): CF-3 start-lift acceptance; the bound is CONDITIONAL on Cd x A x G at the start lift',
               inputs=dict(code=EXPECT_SRC, throttle_map=sha16(map_fn)),
               margins_N=dict(W10_lt_6=F_W10, all_winds=F_ALL),
               acceptance_rule=('CF-3 start-lift point: at the start-level command (62.5 N open-loop map lift) record the encoder lift, mdot and the '
                                'load-cell F (cold chamber, ambient back pressure). Accept if F <= 16.31 N - heat allowance, or mdot <= 16.31 N / v(dh) '
                                '(52.6-56.3 g/s with no heat allowance). dh is the heat added at tank pressure before the throttling (injector-body / '
                                'feed soak-back at the relight, TO-VERIFY); the heat allowance in N is mdot_limit x (v(dh) - v(0)). A failure returns '
                                'the hold level and the W10 rule to the lead (LEAD line 194 (4)).'),
               states=res, summary=summ,
               tags=dict(bound='DERIVED (adiabatic isentropic-equilibrium bound; Cd 0.80 ASSUMED limit; map lift DERIVED)',
                         heat='DERIVED sensitivity; the soak-back heat at the relight is TO-VERIFY (injector-body temperature)',
                         status='not physical evidence; CF-3 at the start lift measures it'))
    json.dump(out, open(out_f, 'w'), indent=1, default=float)
    print(json.dumps(summ, indent=1))
    for lab, r in res.items():
        print(lab, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items() if k != 'cf3_acceptance_by_heat_allowance'})
        for a in r['cf3_acceptance_by_heat_allowance']:
            print('   ', {k: round(v, 3) for k, v in a.items()})
    print('wrote', out_f, sha16(out_f))


if __name__ == '__main__':
    main(*sys.argv[1:3])

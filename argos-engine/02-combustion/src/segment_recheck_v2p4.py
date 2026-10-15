"""Valve-to-seat segment re-check for the MV-P module at the zone top (Combustion v2.4; lead relays 2026-10-13: segment about
44 cm3 / 36 g at 15 C with the module at the zone top and a fixed 3/8 line to the coil; 32.6 cm3 = Mechanical's earlier value;
21.42 cm3 = v2.3 basis). Mechanical measures the final volume on the v3.4 solids; every result here scales with it.

Per volume (21.42 / 32.6 / 44.0 cm3), all DERIVED with CoolProp (HEOS, NitrousOxide):
  A. liquid mass at 15/20/25 C and the A1 relight tank state (286.7 K); vapour mass if the whole segment is saturated vapour;
     purge time of a vapour-filled segment through the 12.5 % lift (0.31 s per 21.42 cm3, SIM C7, scaled with volume);
  B. coast heating with the MV closed and the back-relief check working (segment held at P_tank + crack): heat to boil off
     the whole segment and the time at 18 / 58 W (Mechanical manifold estimate at relight) and 200 W (bound);
  C. S1 flag (MV closed, P_feed - P_tank > 2.0 bar for 1 s; back-relief check stuck shut): liquid-full isochore from
     saturated liquid at T0: temperature rise and heating time to +2 bar (flag), to the 8.42 MPa MAWP and to 9.03 MPa
     (lower burst limit of the proposed 9.5 MPa +/- 5 % secondary disc); the heat capacity is m c_v of the trapped liquid;
  D. trapped-liquid relief: liquid expansion flow at constant pressure (beta V dT/dt) and the vapour displacement flow when
     the hot end boils, at the same heat inputs; required Cv of the back-relief check at its cracking pressure.
usage: python -I segment_recheck_v2p4.py OUTDIR
"""
from __future__ import annotations
import json, math, os, sys
sys.dont_write_bytecode = True
import CoolProp.CoolProp as CP

FL = 'NitrousOxide'
AS = CP.AbstractState('HEOS', FL)


def sat(T, q):
    AS.update(CP.QT_INPUTS, q, T)
    return AS.p(), AS.rhomass(), AS.hmass(), AS.umass()


def iso_T_for_P(rho, P_target, T0):
    """Temperature at which the liquid-full isochore (density rho) reaches P_target (bisection)."""
    lo, hi = T0, T0 + 80.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        AS.update(CP.DmassT_INPUTS, rho, mid)
        if AS.p() > P_target:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


def main(outdir):
    vols = {'v2.3_basis_21.42cm3': 21.42e-6, 'Mechanical_32.6cm3': 32.6e-6, 'zone_top_44cm3': 44.0e-6}
    states = {'15C': 288.15, '20C': 293.15, '25C': 298.15, 'A1_relight_286.7K': 286.7}
    res = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/segment_recheck_v2p4.py',
               request='LEAD 2026-10-13: MV-P/FS-01 at the zone top, segment ~44 cm3 (~36 g at 15 C); re-check vapour mass, purge, '
                       'R1-R4 inventories, trapped-liquid relief and the S1 isochore',
               tags=dict(volumes='LEAD relay of Mechanical (44 cm3 ESTIMATE until the v3.4 solids)', purge='SIM C7 0.31 s per 21.42 cm3, scaled (DERIVED)',
                         heat='Mechanical manifold 305-345 K at relight, hA 1 W/K -> 18-58 W (ESTIMATE); 200 W bound (ASSUMED)',
                         crack='back-relief check cracking 0.07 MPa (Mechanical FS-01: MAWP 8.35 + 0.07)', props='CoolProp HEOS (DERIVED)'))
    A, B, C, D = {}, {}, {}, {}
    for vl, V in vols.items():
        a = {}
        for sl, T in states.items():
            P, rl, hl, ul = sat(T, 0.0); _, rv, hv, uv = sat(T, 1.0)
            a[sl] = dict(P_sat_Pa=P, liquid_g=V * rl * 1e3, vapour_if_full_g=V * rv * 1e3)
        a['purge_full_vapour_s'] = 0.31 * V / 21.42e-6
        A[vl] = a
        # B. coast boil-off with the check working (A1 state, held at P_tank + 0.07 MPa)
        T0 = 286.7; P0, rl, hl, ul = sat(T0, 0.0)
        AS.update(CP.PQ_INPUTS, P0 + 0.07e6, 0.0); Tb = AS.T(); hlb = AS.hmass(); AS.update(CP.PQ_INPUTS, P0 + 0.07e6, 1.0); hvb = AS.hmass()
        m = V * rl
        AS.update(CP.QT_INPUTS, 0.0, T0); cpl = AS.cpmass()
        E_sens = m * cpl * (Tb - T0); E_boil = m * (hvb - hlb)
        B[vl] = dict(liquid_g=m * 1e3, subcooling_K=Tb - T0, E_sensible_J=E_sens, E_boil_off_J=E_boil,
                     t_boil_off_s={f'{q:.0f}W': (E_sens + E_boil) / q for q in (18.0, 58.0, 200.0)},
                     vapour_after_A1_coast_g={f'{q:.0f}W|{tc}s': min(max(q * tc - E_sens, 0.0) / (hvb - hlb), m) * 1e3
                                              for q in (18.0, 58.0) for tc in (19.1, 22.2)})
        # C. S1 isochore (check stuck shut): from saturated liquid at T0
        c = {}
        for sl, T in states.items():
            P0, rl, hl, ul = sat(T, 0.0)
            AS.update(CP.DmassT_INPUTS, rl, T + 0.25); dPdT = (AS.p() - P0) / 0.25
            cv = AS.cvmass()
            m = V * rl
            row = dict(P0_Pa=P0, dPdT_Pa_K=dPdT, cv_J_kgK=cv)
            for lab, Pt in (('S1_flag_+2bar', P0 + 2e5), ('MAWP_8.42MPa', 8.42e6), ('disc_low_9.03MPa', 9.03e6), ('proof_10.5MPa', 10.5e6)):
                Tt = iso_T_for_P(rl, Pt, T)
                E = m * cv * (Tt - T)
                row[lab] = dict(dT_K=Tt - T, E_J=E, t_s={f'{q:.0f}W': E / q for q in (18.0, 58.0, 200.0)})
            c[sl] = row
        C[vl] = c
        # D. relief flows (A1 state, held at P_tank + crack): liquid expansion and boiling displacement
        T0 = 286.7; P0, rl, hl, ul = sat(T0, 0.0)
        AS.update(CP.PT_INPUTS, P0 + 0.07e6, T0 - 0.05); r1 = AS.rhomass(); cp = AS.cpmass()
        AS.update(CP.PT_INPUTS, P0 + 0.07e6, T0 - 0.15); r0 = AS.rhomass()
        beta = -(r1 - r0) / (0.10 * 0.5 * (r1 + r0))
        AS.update(CP.PQ_INPUTS, P0 + 0.07e6, 1.0); rvb = AS.rhomass(); hvb = AS.hmass(); AS.update(CP.PQ_INPUTS, P0 + 0.07e6, 0.0); hlb = AS.hmass(); rlb = AS.rhomass()
        d = {}
        for q in (18.0, 58.0, 200.0):
            dTdt = q / (V * rl * cp)
            Qexp = beta * V * dTdt                                  # m3/s liquid expelled while warming (no boiling)
            mv = q / (hvb - hlb); Qdisp = mv / rvb                  # m3/s liquid displaced by vapour when the hot end boils
            m_disp = Qdisp * rlb
            Kv = Qdisp * 3600 / math.sqrt(0.07e6 / 1e5 / (rlb / 1000.0))
            d[f'{q:.0f}W'] = dict(dTdt_K_s=dTdt, expansion_flow_cm3_s=Qexp * 1e6, boil_displacement_cm3_s=Qdisp * 1e6,
                                  displaced_liquid_g_s=m_disp * 1e3, Cv_required_liquid_at_crack=Kv / 0.865)
        D[vl] = dict(beta_1_K=beta, flows=d)
    res['A_masses_purge'] = A; res['B_coast_boil_off'] = B; res['C_S1_isochore'] = C; res['D_relief_flows'] = D
    fn = os.path.join(outdir, 'segment_recheck_v2p4.json')
    json.dump(res, open(fn, 'w'), indent=1)
    for vl in vols:
        print(vl, 'A1 liquid %.1f g, vapour-full %.2f g, purge %.3f s' % (A[vl]['A1_relight_286.7K']['liquid_g'], A[vl]['A1_relight_286.7K']['vapour_if_full_g'], A[vl]['purge_full_vapour_s']),
              '| 15C liquid %.1f g' % A[vl]['15C']['liquid_g'])
        print('   boil-off', {k: round(v, 1) for k, v in B[vl]['t_boil_off_s'].items()}, 'vapour after coast', {k: round(v, 2) for k, v in B[vl]['vapour_after_A1_coast_g'].items()})
        for sl in ('A1_relight_286.7K', '25C'):
            r = C[vl][sl]
            print('   S1', sl, 'dPdT %.2f MPa/K' % (r['dPdT_Pa_K'] / 1e6), {k: (round(v['dT_K'], 2), {kk: round(vv, 1) for kk, vv in v['t_s'].items()}) for k, v in r.items() if isinstance(v, dict)})
        print('   relief', {k: (round(v['boil_displacement_cm3_s'], 2), round(v['displaced_liquid_g_s'], 2), round(v['Cv_required_liquid_at_crack'], 4)) for k, v in D[vl]['flows'].items()})
    print('wrote', fn)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')

"""Trapped volumes, relief basis and sizing, segment heating in coasts and after landing, stored energy (Combustion v2.4;
closes REVIEW-COMBUSTION RC-04, RC-05, RC-12; 2026-10-13).

Sections (all SI; every input tagged in the output):
  A. trapped volumes and liquid masses (valve->seat segment from low_inlet_check_v2p3; torch line ASSUMED; tank hydraulic
     full temperature for 2.00 kg in 3.17 L);
  B. heating of the stagnant valve->seat segment with the NC valve closed: O3b hose coil beside the case (radiation +
     conduction across the air gap) and the manifold in the injector head (hA 1 W/K, headend_thermal_v2 coast model);
     liquid-full isochoric pressure rise against warming (CoolProp); with differential relief to the tank side, vapour
     generated over the A1 coast and the vapour fraction at relight; post-landing boil-off time;
  C. relief: segment check valve (differential, to the tank side) capacity; tank relief for fire (API 521 heat input,
     two-phase / supercritical relieving fluid, W = Q (dv/dh)_P / v), heater runaway (heater power ASSUMED) and
     blocked-in liquid-full expansion; required flow area with an HEM isentropic mass flux and Kd 0.85 (ASSUMED);
     the 15 L ground tank (ASSUMED geometry) for the fire case;
  D. stored energy: N2O decomposition energy (gas and liquid basis) and the isentropic expansion (burst) energy of each
     vessel's contents to 1 atm, TNT equivalent at 4.184 MJ/kg and an order-of-magnitude 6.9 kPa distance
     (scaled distance 17.9 m kg^-1/3, LITERATURE as recalled, TO-VERIFY). Fragments not computed.
usage: python -I safing_relief_v2p4.py DATA_V2P4_DIR
"""
from __future__ import annotations
import json, math, os, sys
sys.dont_write_bytecode = True
import numpy as np
import CoolProp.CoolProp as CP
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)

FL = 'NitrousOxide'
PA = 101325.0
SIG = 5.670374419e-8
TC_, PC_ = CP.PropsSI('Tcrit', FL), CP.PropsSI('pcrit', FL)
M_N2O = 44.013e-3


def rho_l(T): return CP.PropsSI('D', 'T', T, 'Q', 0, FL)
def rho_v(T): return CP.PropsSI('D', 'T', T, 'Q', 1, FL)
def psat(T): return CP.PropsSI('P', 'T', T, 'Q', 0, FL)
def tsat(P): return CP.PropsSI('T', 'P', P, 'Q', 0, FL)


def hem_flux(P0, h0, n=120):
    """HEM isentropic mass flux, maximised over the throat pressure (choking), from (P0, h0) to ambient."""
    s0 = CP.PropsSI('S', 'P', P0, 'H', h0, FL)
    best = 0.0
    for p in np.linspace(PA * 1.01, P0 * 0.999, n):
        try:
            rho = CP.PropsSI('D', 'P', p, 'S', s0, FL); h = CP.PropsSI('H', 'P', p, 'S', s0, FL)
        except ValueError:
            continue
        best = max(best, rho * math.sqrt(max(2 * (h0 - h), 0.0)))
    return best


def relief_required(Q, P_rel, T_lo, T_hi, Kd=0.85, n=60):
    """Scan the relieving state along the isobar P_rel from T_lo to T_hi (the contents heat at constant pressure while
    the relief flows): W = Q (dv/dh)_P / v; area = W / (Kd G_HEM). Returns the worst (largest) area and its state."""
    worst = None
    for T in np.linspace(T_lo, T_hi, n):
        try:
            h = CP.PropsSI('H', 'P', P_rel, 'T', T, FL); v = 1 / CP.PropsSI('D', 'P', P_rel, 'T', T, FL)
            dT = 0.05
            h2 = CP.PropsSI('H', 'P', P_rel, 'T', T + dT, FL); v2 = 1 / CP.PropsSI('D', 'P', P_rel, 'T', T + dT, FL)
        except ValueError:
            continue
        dvdh = (v2 - v) / (h2 - h)
        W = Q * dvdh / v
        G = hem_flux(P_rel, h)
        A = W / (Kd * G) if G > 0 else float('inf')
        row = dict(T_K=T, rho=1 / v, W_kg_s=W, G_kg_m2s=G, A_m2=A)
        if worst is None or A > worst['A_m2']:
            worst = row
    worst['d_eq_mm'] = 1e3 * math.sqrt(4 * worst['A_m2'] / math.pi)
    return worst


def expansion_energy(m, T, x_vol_liquid=None, V=None):
    """Isentropic expansion work of saturated N2O contents (liquid + vapour at T) to 1 atm: m (u1 - u2s), each phase
    expanded separately (CCPS-style superheated-liquid + vapour method)."""
    if V is not None and T < TC_:
        rl, rv = rho_l(T), rho_v(T)
        # mass split from m and V
        Vl = (m - rv * V) / (rl - rv)
        ml = max(min(Vl * rl, m), 0.0); mv = m - ml
    else:
        ml, mv = m, 0.0
    E = 0.0
    if T >= TC_ and V is not None:      # supercritical single phase: expand (rho, T) isentropically to 1 atm
        u1 = CP.PropsSI('U', 'D', m / V, 'T', T, FL); s1 = CP.PropsSI('S', 'D', m / V, 'T', T, FL)
        return m * (u1 - CP.PropsSI('U', 'P', PA, 'S', s1, FL)), m, 0.0
    for mm, q in ((ml, 0), (mv, 1)):
        if mm <= 0:
            continue
        u1 = CP.PropsSI('U', 'T', T, 'Q', q, FL); s1 = CP.PropsSI('S', 'T', T, 'Q', q, FL)
        u2 = CP.PropsSI('U', 'P', PA, 'S', s1, FL)
        E += mm * (u1 - u2)
    return E, ml, mv


def main(d):
    lo = json.load(open('/home/claude/work/combustion/data/v2/low_inlet_check_v2p3.json'))
    vts = lo['3_volumes']['valve_to_seat_cm3']
    res = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/safing_relief_v2p4.py',
               closes='REVIEW-COMBUSTION RC-04, RC-05, RC-12', critical_point=dict(T_K=TC_, P_Pa=PC_, tag='CoolProp'))
    # ---------------- A. trapped volumes
    A = {}
    for lab, V in (('valve_to_seat_valve_at_coil_fixed_end_ADOPTED', vts['valve_at_coil_fixed_end']), ('valve_to_seat_valve_at_zone_top', vts['valve_at_zone_top'])):
        A[lab] = dict(V_cm3=V, items_cm3=vts.get('items_cm3'), liquid_g={f'{t-273.15:.0f}C': V * 1e-6 * rho_l(t) * 1e3 for t in (288.15, 293.15, 298.15)},
                      tag='SIM low_inlet_check_v2p3 3_volumes (CAD v3.3 stations; Mechanical re-measures on CAD v3.4 with E1)')
    V_torch = math.pi / 4 * 0.0016 ** 2 * 0.6
    A['torch_N2O_line_tap_to_SOL1'] = dict(V_cm3=V_torch * 1e6, liquid_g_20C=V_torch * rho_l(293.15) * 1e3,
                                           trapped='no while the tank-side tap is open (line follows the tank); trapped only if a tap isolation valve is closed on liquid',
                                           tag='ASSUMED 1/8 in PTFE line, 1.6 mm bore, 0.6 m (Mechanical routing TBD)')
    m_t, V_t = 2.0, 3.17e-3
    rho_avg = m_t / V_t
    Ts = np.linspace(283.15, TC_ - 0.05, 2000)
    T_full = None
    for T in Ts:
        if rho_l(T) <= rho_avg:
            T_full = float(T); break
    fill = {f'{t-273.15:.0f}C': (rho_avg - rho_v(t)) / (rho_l(t) - rho_v(t)) for t in (288.15, 293.15, 298.15, 303.15)}
    A['flight_tank'] = dict(m_kg=m_t, V_m3=V_t, mean_density=rho_avg, liquid_volume_fraction=fill, hydraulic_full_T_K=T_full,
                            P_at_hydraulic_full_Pa=psat(T_full) if T_full else None,
                            note='above the hydraulic-full temperature the tank is liquid-full: P rises ~0.4-0.5 MPa/K and the tank relief '
                                 'must flow liquid/supercritical fluid; the 15-25 C arm window is below it',
                            tag='DERIVED CoolProp; m, V LEAD 2026-10-12')
    res['A_trapped_volumes'] = A
    # ---------------- B. segment heating
    B = {}
    # liquid-full isochoric pressure rise from saturated liquid at T0
    iso = {}
    for T0 in (286.70, 288.15, 293.15, 298.15):
        r0 = rho_l(T0); P0 = psat(T0)
        pts = {}
        for dT in (0.5, 1, 2, 3, 4, 5, 6, 8, 10, 15, 20, 30):
            try:
                pts[f'{dT:g}'] = CP.PropsSI('P', 'D', r0, 'T', T0 + dT, FL)
            except ValueError:
                pts[f'{dT:g}'] = None
        dPdT = (CP.PropsSI('P', 'D', r0, 'T', T0 + 0.5, FL) - P0) / 0.5
        iso[f'{T0:.2f}K'] = dict(P0_Pa=P0, dPdT_Pa_K=dPdT, P_after_dT_Pa=pts,
                                 dT_to_7p0MPa_K=next((float(k) for k, v in pts.items() if v and v >= 7.0e6), None),
                                 dT_to_7p5MPa_K=next((float(k) for k, v in pts.items() if v and v >= 7.5e6), None))
    B['liquid_full_isochore'] = dict(v=iso, tag='DERIVED CoolProp (constant density from saturated liquid at T0)')
    # coil heat input: hose OD 14 mm (ASSUMED -6 PTFE/braid), L 0.25 m (O3b), half the circumference facing the case
    D_o, L_c = 0.014, 0.25
    A_face = 0.5 * math.pi * D_o * L_c
    coil = {}
    for Tcase_C in (86.0, 136.0, 178.0, 250.0):
        for gap in (0.003, 0.015):
            Tc = Tcase_C + 273.15; Th = 293.15
            eps_eff = 1 / (1 / 0.8 + 1 / 0.35 - 1)     # case 0.8 (ASSUMED oxidised/painted), braid 0.35 (ASSUMED)
            q_rad = SIG * eps_eff * (Tc ** 4 - Th ** 4)
            k_air = 0.026 + 7e-5 * (0.5 * (Tc + Th) - 293.15)
            q_cond = k_air * (Tc - Th) / gap
            coil[f'case{Tcase_C:.0f}C|gap{gap*1e3:.0f}mm'] = dict(q_rad_W_m2=q_rad, q_cond_W_m2=q_cond, Q_W=(q_rad + q_cond) * A_face)
    B['coil_heat_input'] = dict(v=coil, A_facing_m2=A_face, tag='ESTIMATE: radiation (eps case 0.8 / braid 0.35, ASSUMED) + conduction across '
                                'the still-air gap (no convection credit, conservative), hose wall resistance neglected (conservative); '
                                'case 86-250 C = head-end model case_fwd range at the A1 relight (headend_thermal_v2, all variants); '
                                '136-178 C = lead hose-routing condition')
    # manifold: hA 1 W/K (headend_thermal_v2 coast model) x (T_head - T_N2O)
    man = {}
    for Th in (312.2, 355.1, 400.0, 477.7):
        man[f'head{Th:.0f}K'] = dict(Q_W=1.0 * (Th - 286.7))
    B['manifold_heat_input'] = dict(v=man, tag='ESTIMATE: hA 1 W/K ASSUMED (headend_thermal_v2 coast model) x (T_head - 286.7 K); T_head at '
                                    'the A1 relight 312-478 K over the head-model variants (gnc v2 cycle)')
    # A1 coast with differential relief to the tank: vapour generated and vapour fraction at relight
    T_seg = 286.70; P_seg = psat(T_seg); hfg = CP.PropsSI('H', 'P', P_seg, 'Q', 1, FL) - CP.PropsSI('H', 'P', P_seg, 'Q', 0, FL)
    m_seg = 21.42e-6 * rho_l(T_seg)
    cr = {}
    for Qw in (10.0, 30.0, 70.0, 200.0):
        for t_c in (19.1, 22.2):
            # sensible heat to reach saturation at P_tank + 0.05 MPa crack first
            dT_s = tsat(P_seg + 0.05e6) - T_seg
            cpl = CP.PropsSI('C', 'T', T_seg, 'Q', 0, FL)
            E = Qw * t_c; E_s = m_seg * cpl * dT_s
            m_v = max(E - E_s, 0.0) / hfg
            m_v = min(m_v, m_seg)
            vfrac = (m_v / rho_l(T_seg)) / 21.42e-6       # volume of liquid boiled off = volume taken by vapour (rest vents to the tank)
            cr[f'Q{Qw:.0f}W|coast{t_c}s'] = dict(vapour_generated_g=1e3 * m_v, vapour_volume_fraction=min(vfrac, 1.0),
                                                 t_to_boil_off_segment_s=(m_seg * hfg + E_s) / Qw)
    B['A1_coast_differential_relief'] = dict(v=cr, segment_liquid_g=1e3 * m_seg, T_seg_K=T_seg, P_tank_Pa=P_seg, h_fg_J_kg=hfg, crack_Pa=0.05e6,
                                             tag='ESTIMATE: valve closed at MECO, segment liquid at the A1 relight tank state (286.7 K, 4.35 MPa), '
                                                 'heat input Q (coil + manifold, B above), vapour vented to the tank through the differential check '
                                                 'valve, liquid boiled off is replaced by vapour; the hot manifold boils first, so the vapour sits at '
                                                 'the injector end')
    # post-landing boil-off
    pl = {}
    for Qw in (30.0, 100.0, 350.0):
        pl[f'Q{Qw:.0f}W'] = dict(t_boil_off_s=m_seg * hfg / Qw)
    B['post_landing_boil_off'] = dict(v=pl, tag='ESTIMATE: head soak peak 347-644 K (A1 gnc v2, headend_thermal_v2) -> hA 1 W/K x dT up to ~350 W')
    res['B_segment_heating'] = B
    # ---------------- C. relief
    C = {}
    Qmax = 350.0 + 30.0
    T_ref = 298.15
    rv_ref = rho_v(T_ref); hfg_ref = CP.PropsSI('H', 'T', T_ref, 'Q', 1, FL) - CP.PropsSI('H', 'T', T_ref, 'Q', 0, FL)
    Qvol = Qmax / hfg_ref / rv_ref
    dp_crack = 0.05e6
    # required Cv (gas-like, liquid formula as an order of magnitude with the vapour density): Q[m3/s] = Kv/3600 sqrt(dp/1e5 / SG)
    SG = rv_ref / 1000.0
    Kv = Qvol * 3600 / math.sqrt(dp_crack / 1e5 / SG)
    C['segment_differential_check_valve'] = dict(heat_input_bound_W=Qmax, vapour_volume_flow_m3_s=Qvol, Kv_required_m3_h=Kv, Cv_required=Kv / 0.865,
                                                 crack_Pa=dp_crack, tag='DERIVED (order of magnitude): any 1/8-1/4 in soft-seat check valve (Cv >= 0.1) '
                                                 'passes the boil-off at the cracking pressure; cracking 0.3-0.7 bar class ASSUMED')
    # tank relief
    D_t, L_t = 0.1016, 0.4449
    A_wet_flight = math.pi * D_t * L_t + 2 * math.pi * D_t ** 2 / 4
    set_P = 6.9e6
    for lab, Aw, m_c, V_c in (('flight_tank', A_wet_flight, 2.0, 3.17e-3), ('ground_tank_15L', math.pi * 0.14 * 0.974 + 2 * math.pi * 0.14 ** 2 / 4, 10.4, 15e-3)):
        rows = {}
        for drain, C1 in (('adequate_drainage', 43200.0), ('no_drainage', 70900.0)):
            Qf = C1 * 1.0 * Aw ** 0.82
            P_rel = set_P * 1.21
            w = relief_required(Qf, P_rel, 300.0, 400.0)
            rows[f'fire|{drain}'] = dict(Q_W=Qf, P_relieving_Pa=P_rel, **w)
        Qh = 100.0
        P_rel = set_P * 1.10
        w = relief_required(Qh, P_rel, 300.0, 380.0)
        rows['heater_runaway_100W'] = dict(Q_W=Qh, P_relieving_Pa=P_rel, **w)
        C[f'tank_relief|{lab}'] = dict(wetted_area_m2=Aw, m_kg=m_c, V_m3=V_c, set_Pa=set_P, rows=rows)
    C['tank_relief_tags'] = dict(fire='API 521 (as recalled, TO-VERIFY) Q = C1 F A^0.82, C1 43.2 kW (adequate drainage and fire-fighting) / '
                                 '70.9 kW (none), F 1 (bare vessel), A = whole outer surface (small vessel fully engulfed); relieving '
                                 'pressure set x 1.21 (fire accumulation)', heater='heater power 100 W ASSUMED (the ENG-12 blanket is not '
                                 'specified), accumulation 10 %', method='W = Q (dv/dh)_P / v scanned over 300-400 K at the relieving pressure '
                                 '(supercritical above 7.245 MPa); G = HEM isentropic flux to 1 atm (CoolProp); Kd 0.85 ASSUMED',
                                 ground_tank='15 L cylinder ASSUMED 140 mm x 0.974 m (REPORT v2.3 DC-C/D assumption), 10.4 kg (85 % fill at 20 C, '
                                 'review RC-05); a commercial cylinder carries its own relief device under its standard (TO-VERIFY on the '
                                 'purchased cylinder)', set='tank relief set 6.9 MPa so that the segment (tank + check cracking <= 0.07 MPa) '
                                 'stays <= the 7.0 MPa N2O-side MEOP; reseat above the 25 C arm pressure 5.66 MPa (TO-VERIFY with the part)')
    res['C_relief'] = C
    # ---------------- D. stored energy
    import cantera as ct
    g = ct.Solution('gri30.yaml')
    g.TPX = 298.15, PA, 'N2O:1'; h_n2o = g.enthalpy_mass
    g.TPX = 298.15, PA, 'N2:1, O2:0.5'; h_p = g.enthalpy_mass * (28.014 + 16.0) / 44.013   # per kg of N2O
    dH_gas = (h_n2o - h_p)
    T20 = 293.15
    h_ig = CP.PropsSI('H', 'T', T20, 'P', 1000.0, FL); h_lq = CP.PropsSI('H', 'T', T20, 'Q', 0, FL)
    dH_liq = dH_gas - (h_ig - h_lq)
    Dt = {}
    TNT = 4.184e6
    Z = 17.9
    vessels = [('flight_tank_20C', 2.0, T20, 3.17e-3), ('flight_tank_35C', 2.0, 308.15, 3.17e-3), ('A1_residual_0p61kg_20C', 0.61, T20, 3.17e-3),
               ('A1_residual_0p61kg_50C', 0.61, 323.15, 3.17e-3), ('ground_tank_15L_20C', 10.4, T20, 15e-3), ('segment_21p4cm3_20C', 21.42e-6 * rho_l(T20), T20, None),
               ('hard_start_inventory_15g', 0.0152, T20, None)]
    # A1 residual from this model's dispersed p99 history (last row: liquid + vapour in the tank)
    import pandas as pd
    hA1 = pd.read_csv('/home/claude/work/combustion/data/v2/dc_gncv3/DC-A1dispp99-S230_neqE1e+03_reg1.csv').iloc[-1]
    Tr = float(hA1.T_tank); mlr = float(hA1.m_liq)
    mvr = (3.1671e-3 - mlr / rho_l(Tr)) * rho_v(Tr)
    vessels.insert(4, ('A1_residual_this_model_disp_p99_end', mlr + mvr, Tr, 3.1671e-3))
    for lab, m, T, V in vessels:
        if V is not None:
            E_x, ml, mv = expansion_energy(m, T, V=V)
        else:
            E_x, ml, mv = expansion_energy(m, T)
        E_dec = ml * dH_liq + mv * dH_gas      # liquid basis for the liquid, gas basis for the vapour (and supercritical: liquid basis)
        tnt_dec = E_dec / TNT; tnt_x = E_x / TNT if np.isfinite(E_x) else float('nan')
        Dt[lab] = dict(m_kg=m, T_K=T, V_m3=V, liquid_kg=ml, vapour_kg=mv, P_Pa=psat(T) if T < TC_ else None,
                       decomposition_J=E_dec, decomposition_TNT_kg=tnt_dec, expansion_J=E_x, expansion_TNT_kg=tnt_x,
                       R_6p9kPa_m_decomposition=Z * tnt_dec ** (1 / 3), R_6p9kPa_m_expansion=Z * tnt_x ** (1 / 3) if np.isfinite(tnt_x) else None)
    # chamber gas at MEOP (Brode)
    Vc = 284.6e-6
    E_b = (45e5 - PA) * Vc / (1.25 - 1)
    Dt['chamber_gas_at_MEOP_Brode'] = dict(V_m3=Vc, P_Pa=45e5, gamma=1.25, expansion_J=E_b, expansion_TNT_kg=E_b / TNT,
                                           R_6p9kPa_m_expansion=Z * (E_b / TNT) ** (1 / 3))
    res['D_stored_energy'] = dict(v=Dt, dH_decomposition_gas_J_kg=dH_gas, dH_decomposition_liquid_J_kg=dH_liq, TNT_J_kg=TNT, scaled_distance_m_kg13=Z,
                                  tag='DERIVED Cantera GRI-3.0 (dH N2O -> N2 + 1/2 O2 at 298 K) and CoolProp (liquid basis at 20 C; isentropic '
                                      'expansion of each phase to 1 atm); TNT 4.184 MJ/kg; scaled distance 17.9 m kg^-1/3 for 6.9 kPa side-on '
                                      '(Kinney-Graham class, LITERATURE as recalled, TO-VERIFY); decomposition is not a detonation: TNT '
                                      'equivalence over-states the blast of a deflagrating decomposition but is the conventional bound; '
                                      'FRAGMENTS NOT COMPUTED (they usually govern; founders apply their chosen standard)')
    fn = os.path.join(d, 'safing_relief_v2p4.json')
    json.dump(res, open(fn, 'w'), indent=1, default=float)
    print(json.dumps(res['A_trapped_volumes'], default=float)[:1500])
    for k, v in iso.items():
        print('iso', k, round(v['dPdT_Pa_K'] / 1e6, 3), 'MPa/K', 'dT->7.0', v['dT_to_7p0MPa_K'], 'dT->7.5', v['dT_to_7p5MPa_K'])
    for k, v in coil.items():
        print('coil', k, {kk: round(vv, 1) for kk, vv in v.items()})
    for k, v in cr.items():
        print('coast', k, {kk: round(vv, 3) for kk, vv in v.items()})
    print('postlanding', pl)
    print('check valve', C['segment_differential_check_valve'])
    for k, v in C.items():
        if k.startswith('tank_relief|'):
            for kk, vv in v['rows'].items():
                print(k, kk, 'Q', round(vv['Q_W']), 'W', round(vv['W_kg_s'], 4), 'kg/s at T', round(vv['T_K'], 1), 'G', round(vv['G_kg_m2s']), 'A mm2', round(vv['A_m2'] * 1e6, 3), 'd', round(vv['d_eq_mm'], 2))
    print('dH dec gas/liq MJ/kg', round(dH_gas / 1e6, 3), round(dH_liq / 1e6, 3))
    for k, v in Dt.items():
        print('energy', k, {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()})
    print('wrote', fn)


if __name__ == '__main__':
    main(sys.argv[1])

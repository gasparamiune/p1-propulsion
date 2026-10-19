"""A1 apogee target about 210 m (LEAD CHANGELOG line 213): what in Combustion v2.4b depends on the A1 profile (Combustion v2.4b, 2026-10-13).

LEAD line 213 (founder decision) lowered the A1 apogee target from the 300 m lead default (285 m trim since line 175) to about 210 m; the
exact band is the line-208 band of the GNC rev4 N = 1000 re-fly (gnc.json v3.2, not yet in the hub).  No 210 m A1 duty-cycle record
exists yet, so no 210 m value is computed here.  This script
  (1) reads the 300 m A1 records of gnc.json v3.1 (DC-A1 v2/v3 CSVs; SIM, GNC) and gives per record the launch, MECO and relight tank
      states, the ascent burn, the coast and the ascent cooling, and checks whether the GNC tank changes temperature over the coast;
  (2) evaluates saturated tank states 283.15-298.15 K (297.15 K = the 24 C ARM limit) with the v2.4a functions unchanged
      (cold_flow_thrust_v2p4a imported): Dyer flux, the two-tap all-liquid purge rate, the start-level map lift, the cold-flow bound at
      the map lift and at THE start-level lift h_s(T) of the ECU table; it first reproduces the stored states of
      cold_flow_start_lift_v2p4b.json;
  (3) scales the purge vented mass at 2.5 s and 2.60 s of flow from the 289.5 K basis to warmer relight states (liquid-phase time x the
      liquid-rate change; vapour-phase rate scaled with P_sat, ASSUMED) -- DERIVED; the purge records are NOT re-run;
  (4) reads the dip-onset rows and the dense single-phase sound-speed minima at the warmer saturation pressures (stored data);
  (5) lists each A1-profile statement of v2.4b with its basis (300 m / 285 m), the direction at 210 m and its status.
Tags per value; nothing here is physical evidence or approval.
usage: python -I a1_profile_line213_v2p4b.py HUB DATA_V2_DIR THROTTLE_MAP_S230 OUT_JSON
"""
from __future__ import annotations
import csv, hashlib, json, math, os, sys
sys.dont_write_bytecode = True
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import cold_flow_thrust_v2p4a as CF

EXPECT_SRC = {'cold_flow_thrust_v2p4a.py': 'b4cbf147753ecc7c', 'injector.py': '4ee8e0a1b4825a09',
              'cold_flow_start_lift_v2p4b.py': None, 'lead_items_203_205_v2p4b.py': None}
EXPECT_HUB = {'interfaces/gnc.json': '4f3209323b0e0ed4'}
EXPECT_DATA = {'v2p4b/lead_items_203_205_v2p4b.json': 'e20a8b8c33af9162', 'v2p4b/cold_flow_start_lift_v2p4b.json': '28ce48092f33da1b',
               'v2p4b/tank_outlet_dip_v2p4b.json': '6c11d3c19afe983c', 'v2p4a/vented_mass_brackets_v2p4a.json': '8e8ca9329c74a01f'}
DC_DIR = '01-systems-gnc/duty_cycles'
RECORDS = ['DC-A1_full_flight_drogue_fins_300m_v2.csv', 'DC-A1_full_flight_drogue_fins_300m_v3.csv',
           'DC-A1_full_flight_disp_p99_kest2_v3.csv', 'DC-A1_full_flight_disp_p99_kest2_tg711_v3.csv',
           'DC-A1_full_flight_disp_p99_kest2_v28liq_v3.csv', 'DC-A1_full_flight_disp_p99_kest2_v28liq_tg711_v3.csv']
T_EVAL = (283.15, 286.70, 289.50, 291.15, 293.15, 295.15, 297.15, 298.15)
T_ARM = 297.15            # K, the 24 C ARM interlock (LEAD)
T_BASIS = 289.50          # K, the warm-end coast state of the purge flux bound (rg01 line states v2.4: 46.45 bar, 289.5 K)
A2 = 2 * math.pi / 4 * (0.707e-3) ** 2   # two bleed taps at 0.707 mm (decided)
CD_TAP = 0.70             # ASSUMED, as the purge records
F_W10 = 16.31             # N, GNC W10 < 6 m/s margin
LINE213_KEY = 'A1 APOGEE TARGET LOWERED'


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def r(x, n=3):
    return None if x is None else round(float(x), n)


def gnc_index_entry(G, name):
    """Return the gnc.json v3.1 duty-cycle index entry whose file ends with name (current or retained), or None."""
    out = None
    def walk(o):
        nonlocal out
        if isinstance(o, dict):
            f = o.get('file')
            if isinstance(f, str) and f.endswith('/' + name) and out is None:
                out = o
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(G['duty_cycles'])
    return out


def record_states(path):
    rows = list(csv.DictReader(open(path)))
    t = np.array([float(x['t_s']) for x in rows]); F = np.array([float(x['F_N']) for x in rows])
    T = np.array([float(x['T_tank_K']) for x in rows]); P = np.array([float(x['P_tank_Pa']) for x in rows])
    h = np.array([float(x['h_m']) for x in rows])
    on = np.flatnonzero(F > 1.0)
    segs = []; s = on[0]; p = on[0]
    for i in on[1:]:
        if i != p + 1:
            segs.append((s, p)); s = i
        p = i
    segs.append((s, p))
    assert len(segs) == 2, (path, len(segs))
    (a1, b1), (a2, b2) = segs
    coast = slice(b1, a2 + 1)
    return dict(T0_K=r(T[0], 2), P0_bar=r(P[0] / 1e5, 2), ascent_burn_s=[r(t[a1], 2), r(t[b1], 2)], T_MECO_K=r(T[b1], 2),
                coast_s=r(t[a2] - t[b1], 2), T_relight_K=r(T[a2], 2), P_relight_bar=r(P[a2] / 1e5, 2),
                coast_T_change_K=r(float(T[coast].max() - T[coast].min()), 4), ascent_cooling_K=r(T[0] - T[b1], 2),
                landing_burn_s=[r(t[a2], 2), r(t[b2], 2)], T_end_landing_K=r(T[b2], 2), max_h_m_csv=r(h.max(), 1))


def main(hub, d2, map_fn, out_f):
    for f, h in EXPECT_SRC.items():
        if h:
            assert sha16(os.path.join(HERE, f)) == h, (f, sha16(os.path.join(HERE, f)))
    for f, h in EXPECT_HUB.items():
        assert sha16(os.path.join(hub, f)) == h, (f, sha16(os.path.join(hub, f)))
    for f, h in EXPECT_DATA.items():
        assert sha16(os.path.join(d2, f)) == h, (f, sha16(os.path.join(d2, f)))
    assert sha16(map_fn) == CF.EXPECT_MAP, sha16(map_fn)
    G = json.load(open(os.path.join(hub, 'interfaces/gnc.json')))
    LI = json.load(open(os.path.join(d2, 'v2p4b/lead_items_203_205_v2p4b.json')))
    CFS = json.load(open(os.path.join(d2, 'v2p4b/cold_flow_start_lift_v2p4b.json')))
    DIP = json.load(open(os.path.join(d2, 'v2p4b/tank_outlet_dip_v2p4b.json')))
    VM = json.load(open(os.path.join(d2, 'v2p4a/vented_mass_brackets_v2p4a.json')))
    # the lead line (CHANGELOG grows; the line text is hashed, not the file)
    cl = open(os.path.join(hub, 'interfaces/CHANGELOG.md'), encoding='utf-8').read().split('\n')
    i213 = [i for i, x in enumerate(cl) if LINE213_KEY in x]
    assert i213 == [212], i213
    line213 = cl[212]
    assert '210 m' in line213 and '200-220 m' in line213 and 'B1 still governs thermal and erosion sizing' in line213

    # (1) 300 m A1 records -------------------------------------------------------------------------------------------
    recs = {}
    for name in RECORDS:
        p = os.path.join(hub, DC_DIR, name)
        e = gnc_index_entry(G, name)
        full = hashlib.sha256(open(p, 'rb').read()).hexdigest()
        if e and e.get('sha256'):
            assert e['sha256'] == full, (name, 'hash differs from gnc.json index')
        st = record_states(p)
        st.update(sha256_16=full[:16], gnc_index=('gnc.json v3.1 duty_cycles index (sha256 matches)' if e and e.get('sha256') else
                                                  'not hashed in the gnc.json v3.1 index (read from the hub folder)'))
        if e:
            for k in ('kind', 'apex_m', 'engine_on_counter_s', 'burn_thrust_on_s', 'mc_case'):
                if k in e:
                    st[k] = e[k]
        recs[name] = st
    cool = [v['ascent_cooling_K'] for v in recs.values()]
    asc = [v['ascent_burn_s'][1] - v['ascent_burn_s'][0] for v in recs.values()]
    coast = [v['coast_s'] for v in recs.values()]
    trel = [v['T_relight_K'] for v in recs.values()]
    tend = [v['T_end_landing_K'] for v in recs.values()]
    dTc = max(v['coast_T_change_K'] for v in recs.values())

    # (2) tank states ------------------------------------------------------------------------------------------------
    M = CF.load_map(map_fn)
    ecu = LI['item2_start_level_lift']['ecu_table']
    Pmap = (min(M), max(M))
    states = {}
    for T in T_EVAL:
        st = CF.sat_liq(T)
        hm = CF.map_lift(M, CF.F_START, st['P'])
        v0 = CF.v_iso(st['h'], st['s'], CF.PA)[0]
        mb, Gf = CF.mdot_bound(hm, T)
        hs = float(np.interp(T, ecu['T_K'], ecu['lift_mm'])) * 1e-3
        mbs, _ = CF.mdot_bound(hs, T)
        states['%.2fK' % T] = dict(T_K=T, P_sat_bar=st['P'] / 1e5, rho_l=st['rho'], v_iso_eq_m_s=v0, G_dyer_kg_m2s=Gf['G_dyer'],
                                   purge_all_liquid_two_taps_g_s=1e3 * CD_TAP * A2 * Gf['G_dyer'],
                                   map_lift_mm=1e3 * hm, map_lift_clamped=bool(st['P'] > Pmap[1] or st['P'] < Pmap[0]),
                                   F_bound_map_lift_N=mb * v0, factor_to_16p31N_map_lift=F_W10 / (mb * v0),
                                   h_s_ECU_mm=1e3 * hs, F_bound_h_s_N=mbs * v0, mdot_bound_h_s_g_s=1e3 * mbs)
    # reproduce the stored states of cold_flow_start_lift_v2p4b.json
    for lab, s in CFS['states'].items():
        mine = states['%.2fK' % s['T_K']]
        for a, b in (('G_dyer_kg_m2s', 'G_dyer_kg_m2s'), ('F_bound_map_lift_N', 'F_bound_N'), ('map_lift_mm', 'start_lift_mm'),
                     ('v_iso_eq_m_s', 'v_iso_eq_m_s')):
            assert abs(mine[a] / s[b] - 1) < 1e-9, (lab, a, mine[a], s[b])
    for lab, s in LI['item1_purge_basis']['liquid_rate_by_state_two_taps'].items():
        assert abs(states['%.2fK' % s['T_K']]['purge_all_liquid_two_taps_g_s'] - s['all_liquid_two_taps_g_s']) < 0.006, lab

    # (3) purge vented mass scaled from the 289.5 K basis ----------------------------------------------------------------
    LIQ, VAP = VM['rate_lines_g_s']['all_liquid'], VM['rate_lines_g_s']['all_vapour']
    vm = LI['item1_purge_basis']['vented_mass_g']
    m25 = vm['2.50 s flow (nominal schedule)']['combustion_bound_open_g']
    m26 = [v for k, v in vm.items() if k.startswith('2.60 s flow')][0]['combustion_bound_open_g']
    t_vap = (LIQ * 2.5 - m25) / (LIQ - VAP)
    ref = states['%.2fK' % T_BASIS]
    purge = {}
    for k, s in states.items():
        if s['T_K'] < T_BASIS:
            continue
        kl = s['purge_all_liquid_two_taps_g_s'] / ref['purge_all_liquid_two_taps_g_s']; kv = s['P_sat_bar'] / ref['P_sat_bar']
        d25 = (2.5 - t_vap) * LIQ * (kl - 1) + t_vap * VAP * (kv - 1)
        d26 = (2.6 - t_vap) * LIQ * (kl - 1) + t_vap * VAP * (kv - 1)
        purge[k] = dict(T_K=s['T_K'], liquid_rate_g_s=r(LIQ * kl, 2), M_2p5s_g=r(m25 + d25, 2), M_2p60s_g=r(m26 + d26, 2))
    Ts = np.array([v['T_K'] for v in purge.values()]); m25s = np.array([v['M_2p5s_g'] for v in purge.values()])
    m26s = np.array([v['M_2p60s_g'] for v in purge.values()])
    def cross(y, lim):
        if y[0] >= lim:
            return 'at or below %.2f K' % Ts[0]
        if y[-1] < lim:
            return 'not reached up to %.2f K' % Ts[-1]
        return r(float(np.interp(lim, y, Ts)), 2)
    fK = lambda x: x if isinstance(x, str) else '%.2f K' % x
    slope_liq = (purge['%.2fK' % 293.15]['liquid_rate_g_s'] - purge['%.2fK' % T_BASIS]['liquid_rate_g_s']) / (293.15 - T_BASIS)
    slope_m25 = (purge['%.2fK' % 293.15]['M_2p5s_g'] - m25) / (293.15 - T_BASIS)

    # (4) stored data: dip onset rows and dense c minima ---------------------------------------------------------------
    dip = {}
    for row in DIP['rows']:
        if abs(row['F_N'] - 500.0) < 1e-6:
            dip.setdefault(row['T_K'], []).append(row['liquid_at_onset_g'])
    dip500 = {('%.2fK' % T): [r(min(v), 1), r(max(v), 1)] for T, v in sorted(dip.items())}
    dense = LI['item8_pc_port_gas']['N2O_single_phase_minimum_dense']['values']
    dP = sorted((float(k.replace('bar', '')), v['c_min_m_s']) for k, v in dense.items())
    c_at = {k: r(float(np.interp(s['P_sat_bar'], [x[0] for x in dP], [x[1] for x in dP])), 1) for k, s in states.items() if s['T_K'] >= T_BASIS}
    isd = LI['item8_pc_port_gas']['N2O_isentropic_from_saturation_minimum']
    cmin = LI['item8_pc_port_gas']['c_design_min_m_s']
    wall = LI['item8_pc_port_gas']['wall_temperature_at_relight_K']

    sA = states['%.2fK' % T_ARM]; s93 = states['%.2fK' % 293.15]
    pA = purge['%.2fK' % T_ARM]
    f_rng = (min(s['F_bound_map_lift_N'] for s in states.values() if s['T_K'] <= T_BASIS),
             max(s['F_bound_map_lift_N'] for s in states.values() if s['T_K'] <= T_BASIS))
    stmts = [
        dict(id='A1-1', topic='A1 duty cycle, erosion, residual web and insert life',
             where='REPORT Tables 4.4, 4.6, 5.4; §5.4 life statement; §15.13; JSON a1_duration_note_v2p4b',
             basis='300 m: gnc.json v3.1 A1 records (A1 sizing DC-A1 disp p99: engine-on %.3f s, apex %.1f m; nominal v3 apex %.1f m) and the '
                   'v1/v2 300 m cycles; 285 m: GNC rev3 F11 (A1_none p99 engine-on 8.375 s; records, not sizing, LEAD 204 (4))'
                   % (recs['DC-A1_full_flight_disp_p99_kest2_v3.csv']['engine_on_counter_s'], recs['DC-A1_full_flight_disp_p99_kest2_v3.csv']['apex_m'],
                      recs['DC-A1_full_flight_drogue_fins_300m_v3.csv']['apex_m']),
             direction_at_210m='shorter A1 duty cycle (LEAD line 213), so less erosion and heat per A1 flight; B1 still governs thermal and '
                               'erosion sizing (LEAD); no new sizing case',
             status='COMPARATOR: the 300 m and 285 m tables stay; 210 m values MISSING until the 210 m record (gnc.json v3.2). One insert per '
                    'flight stays (it rests on the missing T1/T4 bore data, not on the cycle)'),
        dict(id='A1-2', topic='A1 relight tank state',
             where='REPORT Tables 7.3a, 7.3b, 2.4b; §7.3; §15.3; §15.9; CF-4 v2.1 §4; FA-1 cases (286.70 K, 43.53 bar)',
             basis='283.15 / 286.7 / 289.5 K (40.0 / 43.5 / 46.5 bar): cold, A1 v2 relight state, warm-end coast state (300 m era)',
             direction_at_210m='WARMER at the same launch temperature (DERIVED direction): on every 300 m record the GNC tank keeps its MECO '
                               'temperature over the coast (largest change %.4f K), so the relight state is the launch temperature minus the '
                               'ascent cooling (%.2f-%.2f K over %.2f-%.2f s of ascent burn; relight %.2f-%.2f K); a 210 m ascent ends earlier '
                               '(MECO on a lower predicted apogee) and cools the tank less. Upper bound: the %.2f K ARM limit (LEAD), as the '
                               'modelled tank does not warm over the coast' % (dTc, min(cool), max(cool), min(asc), max(asc), min(trel),
                                                                                max(trel), T_ARM),
             status='MAGNITUDE MISSING until the 210 m record gives T_tank at MECO; the 300 m states stay as comparators'),
        dict(id='A1-3', topic='Purge vented mass against the 76 g limit (P5; OI-42)',
             where='REPORT §15.9; JSON purge_basis_v2p4b; CF-4 P5',
             basis='M(2.5 s) <= %.2f g and %.2f g at 2.60 s of flow (the 2.55 s both-open cap), at the %.1f K warm-end coast state '
                   '(upper-bound flux)' % (m25, m26, T_BASIS),
             direction_at_210m='RISES with the relight state (DERIVED scaling, records not re-run): liquid rate +%.2f g/s per K and M(2.5 s) '
                               '+%.2f g per K above %.1f K; the 2.5 s schedule stays <= 76 g up to %s; the 2.55 s cap is at the limit at '
                               '%.1f K (%.2f g) and above it at any warmer state; at the %.2f K ARM limit M(2.5 s) = %.2f g and M(2.60 s) = '
                               '%.2f g' % (slope_liq, slope_m25, T_BASIS, fK(cross(m25s, 76.0)), T_BASIS, m26, T_ARM, pA['M_2p5s_g'],
                                           pA['M_2p60s_g']),
             status='TO-VERIFY at the 210 m warm-end relight state (GNC record) and in CF-4 (P5 read at that state); the 289.5 K "upper-bound '
                    'flux" is an upper bound only for relight states <= 289.5 K'),
        dict(id='A1-4', topic='Cold-flow apparent thrust at the start level (dead engine under the drogue)',
             where='REPORT Table 7.3a; §7.3 CONDITIONAL margin; JSON cold_flow_start_lift_v2p4b',
             basis='%.2f-%.2f N at the start-level map lift over 283.15-289.5 K; 12.86 N at THE start-level lift (A1 state)' % f_rng,
             direction_at_210m='RISES with the relight state (DERIVED, functions unchanged): %.2f N at 293.15 K and %.2f N at the %.2f K ARM '
                               'limit at the map lift (map clamped at its 5.0 MPa row above 50 bar), %.2f N at h_s(T) at %.2f K; all below '
                               'the 16.31 N inside-W10 < 6 m/s margin; the factor on Cd x A x G to 16.31 N falls to %.2f'
                               % (s93['F_bound_map_lift_N'], sA['F_bound_map_lift_N'], T_ARM, sA['F_bound_h_s_N'], T_ARM,
                                  sA['factor_to_16p31N_map_lift']),
             status='still CONDITIONAL on Cd x A x G at the start lift (CF-3), as before'),
        dict(id='A1-5', topic='THE start-level lift h_s(T) and the lit thrust at the start level',
             where='REPORT §15.3, §15.4, Table 7.3b; JSON start_level_lift_v2p4b, start_level_lit_thrust_v2p4b',
             basis='h_s = the ECU ignition-lift row at the measured tank temperature (table 273.15-308.15 K); quoted at 286.70 K (0.21776 mm); '
                   'lit histories at 0.21776 mm (A1 state, port 32.2 mm, 1.16 kg) and 0.2039 mm',
             direction_at_210m='the rule holds at any 210 m state (temperature lookup); h_s is lower at warmer states (%.5f mm at 293.15 K, '
                               '%.5f mm at %.2f K); the relight port after a shorter ascent is smaller and the propellant mass larger, so the '
                               'lit-thrust direction is not established (it depends on n in the band)' % (s93['h_s_ECU_mm'], sA['h_s_ECU_mm'], T_ARM),
             status='rule unchanged; quoted A1 values and Table 7.3b are COMPARATORS; Table 7.3b at the 210 m relight state MISSING'),
        dict(id='A1-6', topic='CF-4 tank state and the IS-2 heated hold',
             where='CF-4 v2.1 §4 (tank 43.5-46.5 bar, 286.7-289.5 K) and the IS-2 row (A1 coast duration)',
             basis='300 m A1 relight states; 300 m coast %.2f-%.2f s (records)' % (min(coast), max(coast)),
             direction_at_210m='warmer relight state (A1-2); shorter coast, so less segment heat in the hold: the 300 m coast duration is the '
                               'conservative side for the vapour cap (DERIVED direction)',
             status='CF-4 keeps the 300 m bracket and hold as comparators and adds the 210 m warm-end relight state as a tank-state point when '
                    'GNC publishes it'),
        dict(id='A1-7', topic='Gas in the Pc port passage (line 205)',
             where='REPORT §15.8; JSON pc_port_gas_v2p4b',
             basis='c >= %.0f m/s: single-phase N2O scanned over 250-600 K and 22-88 bar; isentropic-from-saturation %.1f m/s at entry %.2f bar '
                   '(the warm-end coast saturation); wall %.1f-%.1f K at RELIGHT (Mechanical, A1 p99 300 m case)'
                   % (cmin, isd['c_m_s'], isd['entry_bar'], wall['A1_SIM'][0], wall['A1_SIM'][1]),
             direction_at_210m='the %.0f m/s floor does not depend on the profile; a warmer relight state raises the entry pressure and lowers the '
                               'isentropic value toward the floor (dense single-phase minimum %.1f m/s at P_sat(293.15 K), %.1f m/s at P_sat(%.2f K)); '
                               'the wall temperatures at an earlier relight are not established' % (cmin, c_at['%.2fK' % 293.15], c_at['%.2fK' % T_ARM], T_ARM),
             status='bound unchanged; at-relight values COMPARATORS; 210 m wall temperatures MISSING (Mechanical)'),
        dict(id='A1-8', topic='Tank outlet dip onset (GNC landing reserve)',
             where='REPORT Table 2.4b; §15.11; JSON tank_outlet_dip_v2p4b',
             basis='500 N: %s g (by tank temperature, two vehicle masses); line 208 (1) fixes the GNC onset at 80 g' %
                   '; '.join('%s K: %s-%s' % (k.replace('K', ''), v[0], v[1]) for k, v in dip500.items()),
             direction_at_210m='the onset mass falls as the tank warms; the 300 m records end the landing burn at %.2f-%.2f K, partly below '
                               'the 283-289.5 K column (the 270 K row covers them); the 210 m landing-end state is not established'
                               % (min(tend), max(tend)),
             status='COMPARATOR; GNC applies its 80 g rule (208 (1)) until OI-32 sets the outlet geometry'),
        dict(id='A1-9', topic='Release-hold records, per-record classes and line states (unpurged alternative)',
             where='REPORT Table 2.18, §15.6; rg01 line states v2.4',
             basis='A1 coast heat cases of the 300 m era (ARM_bay45C_liq24C governing)',
             direction_at_210m='shorter coast, warmer tank: not re-run',
             status='COMPARATOR data only; the alternative is NOT ADOPTED (204 (2), strengthened by 208 (3))'),
        dict(id='A1-10', topic='FA-1 envelope and spectra',
             where='REPORT §7.6, §15.7; JSON fa1_spectra_v2p4b',
             basis='FA-1 cases at the A1 relight state 286.70 K, 43.53 bar (fa1_envelope_v2p4a state)',
             direction_at_210m='the start-level flow is held at 37.4 g/s by the temperature-indexed lift table, so the start inflow does not rise '
                               'with the tank temperature to first order (DERIVED); the envelope at the 210 m relight state is not re-run',
             status='TO-VERIFY at the 210 m relight state; the period-domain load rule and its contradiction OI-41 are unchanged'),
    ]
    res = dict(
        version='v2.4b', date='2026-10-13', script='02-combustion/src/a1_profile_line213_v2p4b.py', script_sha256_16=sha16(os.path.abspath(__file__)),
        request='LEAD CHANGELOG line 213 (relayed by the coordinator): where v2.4b quotes the A1 profile, state the about-210 m target and keep '
                'the 285 m and 300 m tables as comparators',
        inputs={**{f: sha16(os.path.join(hub, f)) for f in EXPECT_HUB}, **{f: sha16(os.path.join(d2, f)) for f in EXPECT_DATA},
                os.path.basename(map_fn): sha16(map_fn), 'cold_flow_thrust_v2p4a.py': sha16(os.path.join(HERE, 'cold_flow_thrust_v2p4a.py')),
                'CHANGELOG line 213 text': hashlib.sha256(line213.encode('utf-8')).hexdigest()[:16]},
        target=dict(apogee_m_approx=210, tag='LEAD (founder decision, CHANGELOG line 213, 2026-10-13 18:31:08Z)',
                    band='the line-208 band of the GNC rev4 N = 1000 re-fly on massprops v3.5.1 (488b47f9d55ff91b), expected within about 5 m '
                         'of 210 m; a band outside 200-220 m returns to the founder',
                    carried_by='gnc.json v3.2 (not in the hub at this build; gnc.json v3.1 read)',
                    previous='300 m lead default; 285 m trim since line 175 (lines 168 (4), 175 (1), 181 (6))',
                    lead_consequences='the A1 duty cycle shortens; B1 still governs thermal and erosion sizing, no new sizing case; tank stays '
                                      '2.00 kg'),
        comparators_300m_records=recs,
        comparators_300m_summary=dict(ascent_cooling_K=[min(cool), max(cool)], ascent_burn_s=[r(min(asc), 2), r(max(asc), 2)],
                                      coast_s=[min(coast), max(coast)], T_relight_K=[min(trel), max(trel)],
                                      T_end_landing_K=[min(tend), max(tend)], coast_T_change_max_K=dTc,
                                      note='gnc.json v3.1 lists DC-A1_full_flight_disp_p99_kest2_tg711_v3 as a run above 24 C '
                                           '(t_tank_arm_range); its T0 is above the ARM limit'),
        comparator_285m=dict(source='GNC rev3 F11 (LEAD 204 (4)): 285 m duty records are records, not sizing', A1_none_p99_engine_on_s=8.375),
        states={k: {kk: (r(vv, 5) if isinstance(vv, float) else vv) for kk, vv in v.items()} for k, v in states.items()},
        purge_scaling=dict(basis_T_K=T_BASIS, M_rec_2p5s_g=m25, M_bound_2p60s_g=m26, rate_lines_g_s=dict(all_liquid=LIQ, all_vapour=VAP),
                           t_vapour_phase_s=r(t_vap, 4), rows=purge, liquid_rate_slope_g_s_per_K=r(slope_liq, 3),
                           M_2p5s_slope_g_per_K=r(slope_m25, 3), T_at_76g_2p5s_K=cross(m25s, 76.0), T_at_76g_2p60s_K=cross(m26s, 76.0),
                           T_at_80g_2p5s_K=cross(m25s, 80.0), T_at_80g_2p60s_K=cross(m26s, 80.0),
                           method='M(T) = M(289.5 K) + t_liquid x 31.24 g/s x (G_dyer(T)/G_dyer(289.5 K) - 1) + t_vapour x 8.49 g/s x '
                                  '(P_sat(T)/P_sat(289.5 K) - 1); t_vapour = (31.24 x 2.5 - M_rec(2.5 s)) / (31.24 - 8.49); records NOT re-run'),
        dip_onset_500N_g=dip500,
        c_dense_min_at_Psat_m_s=c_at,
        statements=stmts,
        line208_cross_references=dict(
            dip_onset='208 (1) fixes the GNC onset at 80 g ("upper end of the R3-17 bracket"); v2.4b Table 2.4b gives 78.3-80.6 g at 500 N over '
                      '283-289.5 K and %s-%s g at 270 K' % (dip500['270.00K'][0], dip500['270.00K'][1]),
            purge_80g='208 (1) sensitivity arm "~80 g purge": on the 289.5 K basis 80 g is reached at %.3f s of flow; at 2.60 s of flow (the '
                      '2.55 s cap) 80 g is reached at a relight state of %s; on the 2.5 s schedule 80 g is %s'
                      % (LI['item1_purge_basis']['gnc_80g_sensitivity']['t_flow_s'], fK(cross(m26s, 80.0)), fK(cross(m25s, 80.0))),
            not_adopted='208 (3) strengthens 204 (2) NOT ADOPTED; no Combustion change'),
        missing=['the 210 m A1 duty-cycle record (gnc.json v3.2): engine-on time, burns, T_tank at MECO/relight, coast duration, ARM-hot case',
                 'Mechanical: wall temperatures at RELIGHT on the 210 m record',
                 'Combustion re-runs on the 210 m record when published: A1 grain run (relight state, port), Table 7.3b, the purge records at '
                 'the warm-end state, FA-1 at the relight state (no new sizing case; LEAD)'],
        tags=dict(records='SIM (GNC duty cycles, read only)', states='DERIVED (CoolProp HEOS; Dyer; isentropic equilibrium expansion; '
                  'Cd 0.70 taps ASSUMED; Cd 0.80 bound ASSUMED)', purge='DERIVED scaling of SIM records; records not re-run',
                  directions='DERIVED (qualitative unless a number is given)', target='LEAD',
                  status='simulation and derivation only; not physical evidence or approval'))
    json.dump(res, open(out_f, 'w'), indent=1)
    for k, v in recs.items():
        print(k, v['T0_K'], v['T_MECO_K'], v['T_relight_K'], v['coast_s'], v['ascent_cooling_K'], v.get('apex_m'), v.get('engine_on_counter_s'))
    for k, v in states.items():
        print(k, 'P %.2f' % v['P_sat_bar'], 'rate %.2f' % v['purge_all_liquid_two_taps_g_s'], 'Fmap %.2f' % v['F_bound_map_lift_N'],
              'Fhs %.2f' % v['F_bound_h_s_N'], 'hs %.5f' % v['h_s_ECU_mm'], 'clamp', v['map_lift_clamped'])
    for k, v in purge.items():
        print('purge', k, v)
    print('slopes', slope_liq, slope_m25, 'T76', cross(m25s, 76.0), cross(m26s, 76.0), 'T80', cross(m25s, 80.0), cross(m26s, 80.0))
    print('dip500', dip500, 'c_at', c_at)
    print('wrote', out_f, sha16(out_f))


if __name__ == '__main__':
    main(*sys.argv[1:5])

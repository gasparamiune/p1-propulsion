"""ONE purge flow basis for the measured-time ECU cap (Combustion v2.4b final, 2026-10-19; LEAD CHANGELOG line 216 (5); lead message
2026-10-13 ~19:05Z; REV-ELEC-2 R2-05).

Line 216 (5): the ECU purge cap takes the measured-time form after CF-4 / B-BLEED-1,
    both-open overlap <= 76 g / mdot - (t_close - t_open),
and until then every team carries ONE flow basis stated by Combustion v2.4b, with GNC's G80 arm as the high-basis sensitivity.
The cap form is a constant-rate model: vented mass = mdot x flow time, flow time = overlap + (t_close - t_open) (firmware flow
model, hbFlowEnd: both-open + 0.050 s with the ASSUMED 30 / 80 ms valve times).  The Combustion vented-mass bound is not a
constant rate: the line starts with vapour (all-vapour line 8.49 g/s for t_v = 0.2274 s equivalent), then flows liquid (31.24 g/s
at 289.5 K) (v2.4a records, extended at the all-liquid rate; v2.4b §15.9).  The single basis that makes the constant-rate cap
form exact at the 76 g limit on that bound is
    mdot_basis = 76 g / t76,   t76 = t_v + (76 g - r_vap t_v) / r_liq   (the flow time at which the bound reaches 76 g).
State: the 289.5 K warm-end relight state (upper end of the 283.15-289.5 K relight bracket of the 300 m era; the 210 m relight
state is MISSING, warmer direction, OI-49).  This script evaluates the basis, its equivalences, the reconciliation of the candidate
values (Combustion 29.2 / 29.8, SIL 31.44 / 32.0, bleed_driver_v1.json) and the uncertainty by source (tank state, Cd, flashing
model, line vapour at the purge start, valve times), and maps GNC's G80 arm onto them.
Tags: records SIM (purge_duration_v2p4 trade records; Cd 0.70 and slip brackets ASSUMED); law and basis DERIVED; HEM / SPI / Dyer
fluxes DERIVED (CoolProp HEOS, as published in cold_flow_start_lift_v2p4b.json); Cd bracket 0.60-0.80 ASSUMED; valve times ASSUMED.
Not physical evidence; B-BLEED-1 / CF-4 measure mdot and the valve times.
usage: python -I purge_basis_line216_v2p4b.py LEAD_ITEMS_JSON A1_PROFILE_JSON COLD_FLOW_START_LIFT_JSON BLEED_DRIVER_JSON
       CHANGELOG_MD OUT_JSON
"""
from __future__ import annotations
import hashlib, json, os, sys

EXPECT = {'lead_items': 'e20a8b8c33af9162', 'a1_profile': '46b6a1c6efec0351', 'cold_flow_start_lift': '28ce48092f33da1b',
          'bleed_driver_v1': '298b405b0621acd5'}
LIMIT_G = 76.0
DT_VALVES_S = 0.05            # (t_close - t_open): Electronics ASSUMED 80 ms close - 30 ms open (bleed_driver_v1.json firmware inputs)
OVERLAP_SCHED_S = 2.45        # scheduled both-open overlap (V2 open cmd 0.32 s, V1 close cmd 2.77 s after PURGE; REV-ELEC-2 R2-05)
CAP_PROV_S = 2.55             # provisional software cap on the both-open command (line 203 (3), 216 (5))
HW_FLOW_S = 3.293             # hardware-only bound on the flow (REV-ELEC-2 R2-05; bleed_driver_v1 hardware window + valve times)
CD_NOM, CD_LO, CD_HI = 0.70, 0.60, 0.80


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def r(x, n=3):
    return round(float(x), n)


def main(li_f, a1_f, cf_f, bd_f, chl_f, out_f):
    for lab, f in (('lead_items', li_f), ('a1_profile', a1_f), ('cold_flow_start_lift', cf_f), ('bleed_driver_v1', bd_f)):
        assert sha16(f) == EXPECT[lab], (lab, sha16(f))
    LI = json.load(open(li_f))['item1_purge_basis']; A1 = json.load(open(a1_f)); CF = json.load(open(cf_f)); BD = json.load(open(bd_f))
    lines = open(chl_f).read().split('\n')
    l216 = [x for x in lines if x.startswith('2026-10-13 | lead | (decision) | On REV-ELEC-2 (line 215)')]
    assert len(l216) == 1 and '(5) R2-05, 203 (3) RESTATED' in l216[0]
    ps = A1['purge_scaling']
    r_liq0, r_vap0 = ps['rate_lines_g_s']['all_liquid'], ps['rate_lines_g_s']['all_vapour']
    t_v = ps['t_vapour_phase_s']; T0 = ps['basis_T_K']
    assert abs(r_liq0 * 2.5 - (r_liq0 - r_vap0) * t_v - ps['M_rec_2p5s_g']) < 0.01
    st = A1['states']; P0 = st['289.50K']['P_sat_bar']; G0 = st['289.50K']['G_dyer_kg_m2s']

    def law(T_key, k_liq=1.0, k_vap=1.0, tv=t_v):
        s = st[T_key]
        rl = r_liq0 * s['G_dyer_kg_m2s'] / G0 * k_liq; rv = r_vap0 * s['P_sat_bar'] / P0 * k_vap
        return rl, rv, tv

    def M(t, rl, rv, tv):
        return rl * t if tv <= 0 else (rv * t if t <= tv else rv * tv + rl * (t - tv))

    def t_for(mass, rl, rv, tv):
        if tv <= 0:
            return mass / rl
        return mass / rv if mass <= rv * tv else tv + (mass - rv * tv) / rl

    rl, rv, tv = law('289.50K')
    t76 = t_for(LIMIT_G, rl, rv, tv); basis = LIMIT_G / t76
    assert abs(M(2.5, rl, rv, tv) - ps['M_rec_2p5s_g']) < 0.01 and abs(t76 - LI['cap_for_76g']['t_flow_s']) < 1e-3
    cap_overlap = LIMIT_G / basis - DT_VALVES_S

    def rows_for(mdot):
        out = {}
        for lab, fl in (('scheduled 2.45 s overlap (2.50 s flow)', OVERLAP_SCHED_S + DT_VALVES_S),
                        ('provisional 2.55 s cap (2.60 s flow)', CAP_PROV_S + DT_VALVES_S),
                        ('Electronics firmware-cap row 2.61 s (2.66 s flow)', 2.66),
                        ('hardware-only bound (3.293 s flow)', HW_FLOW_S)):
            out[lab] = dict(flow_s=r(fl, 3), basis_g=r(mdot * fl, 2), bound_g=r(M(fl, rl, rv, tv), 2))
        return out
    equivalences = rows_for(basis)
    # (a) tank state
    by_state = {}
    for k in st:
        rl_, rv_, tv_ = law(k)
        t_ = t_for(LIMIT_G, rl_, rv_, tv_)
        by_state[k] = dict(T_K=st[k]['T_K'], r_liq_g_s=r(rl_, 2), r_vap_g_s=r(rv_, 2), M_2p5s_g=r(M(2.5, rl_, rv_, tv_), 2),
                           t76_flow_s=r(t_, 4), mdot_eq_g_s=r(LIMIT_G / t_, 2), cap_overlap_s=r(t_ - DT_VALVES_S, 3))
    # (b) Cd (both phases scale with Cd)
    by_cd = {}
    for cd in (CD_LO, 0.65, CD_NOM, 0.75, CD_HI):
        k = cd / CD_NOM; t_ = t_for(LIMIT_G, rl * k, rv * k, tv)
        by_cd['Cd %.2f' % cd] = dict(factor=r(k, 4), mdot_eq_g_s=r(LIMIT_G / t_, 2), M_2p5s_g=r(M(2.5, rl * k, rv * k, tv), 2),
                                     cap_overlap_s=r(t_ - DT_VALVES_S, 3))
    # (c) flashing model on the liquid phase (Dyer at saturation = mean of SPI and HEM; ratios at the cold-flow states)
    cfs = CF['states']['coast_289.5K']
    k_hem = cfs['G_hem_kg_m2s'] / cfs['G_dyer_kg_m2s']; k_spi = cfs['G_spi_kg_m2s'] / cfs['G_dyer_kg_m2s']
    assert abs(cfs['G_dyer_kg_m2s'] - G0) / G0 < 1e-3
    by_model = {}
    for lab, k in (('HEM (equilibrium, lower flux)', k_hem), ('Dyer (basis)', 1.0), ('SPI (frozen, upper flux)', k_spi)):
        t_ = t_for(LIMIT_G, rl * k, rv, tv)
        by_model[lab] = dict(liquid_flux_factor=r(k, 4), r_liq_g_s=r(rl * k, 2), mdot_eq_g_s=r(LIMIT_G / t_, 2),
                             M_2p5s_g=r(M(2.5, rl * k, rv, tv), 2), cap_overlap_s=r(t_ - DT_VALVES_S, 3))
    # (d) line vapour at the purge start
    by_line = {}
    for lab, tv_ in (('all-liquid start (no vapour; the SIL S12 form)', 0.0), ('record maximum, open element (basis)', tv)):
        t_ = t_for(LIMIT_G, rl, rv, tv_)
        by_line[lab] = dict(t_vapour_s=r(tv_, 4), mdot_eq_g_s=r(LIMIT_G / t_, 2), M_2p5s_g=r(M(2.5, rl, rv, tv_), 2),
                            cap_overlap_s=r(t_ - DT_VALVES_S, 3))
    m_bar = LI['vented_mass_g']['2.50 s flow (nominal schedule)']['combustion_barrier_g']
    by_line['record, barrier element'] = dict(M_2p5s_g=m_bar, mdot_eq_g_s=r(LIMIT_G / (2.5 + (LIMIT_G - m_bar) / rl), 2),
                                              note='barrier bracket ends 0.87 g below the open element at 2.5 s; marginal rate as the open element')
    # bounding combination (not statistical)
    k_lo, k_hi = CD_LO / CD_NOM, CD_HI / CD_NOM
    rl_c, rv_c, tv_c = law('283.15K')
    combo = dict(
        state_and_Cd=dict(low=r(LIMIT_G / t_for(LIMIT_G, rl_c * k_lo, rv_c * k_lo, tv), 2), high=r(LIMIT_G / t_for(LIMIT_G, rl * k_hi, rv * k_hi, tv), 2),
                          range='283.15-289.5 K x Cd 0.60-0.80, Dyer, record line state'),
        state_Cd_model=dict(low=r(LIMIT_G / t_for(LIMIT_G, rl_c * k_lo * k_hem, rv_c * k_lo, tv), 2),
                            high=r(LIMIT_G / t_for(LIMIT_G, rl * k_hi * k_spi, rv * k_hi, 0.0), 2),
                            range='283.15-289.5 K x Cd 0.60-0.80 x HEM-SPI liquid flux x line state (high end: all-liquid start)'),
        note='bounds of the stated assumptions, not a statistical interval; nothing here is measured')
    # G80 mapping
    g80 = dict(mass_g=80.0, mean_rate_on_2p50s_flow_g_s=r(80.0 / 2.5, 2), over_basis_pct=r(100 * (80.0 / 2.5 / basis - 1), 1),
               bound_flow_s_at_80g=r(t_for(80.0, rl, rv, tv), 3),
               covers=['tank state up to the 297.15 K ARM limit on the 2.5 s schedule (M(2.5 s) %.2f g)' % by_state['297.15K']['M_2p5s_g'],
                       'an all-liquid start at 289.5 K (%.2f g at 2.5 s)' % by_line['all-liquid start (no vapour; the SIL S12 form)']['M_2p5s_g'],
                       'Cd up to %.3f at 289.5 K (record line state)' % (CD_NOM * 80.0 / M(2.5, rl, rv, tv))],
               does_not_cover=['the SPI end of the flashing-flow envelope', 'Cd 0.80 combined with a warm (> 289.5 K) relight state',
                               'the 2.55 s cap at the ARM limit (M(2.60 s) %.2f g at 297.15 K)' % M(2.6, *law('297.15K'))])
    cand = [
        dict(value_g_s=29.2, source='CHANGELOG 166 (3); bleed_driver_v1.json mdot_comb_g_s', is_='73.0 g / 2.5 s: the Combustion record maximum '
             'averaged over the 2.5 s scheduled flow (289.5 K)', vs_basis_pct=r(100 * (29.2 / basis - 1), 2),
             verdict='same records and state; exact at 2.5 s only (cap form gives 2.553 s and 76.15 g on the bound)'),
        dict(value_g_s=29.8, source='Electronics line-203 (3) item (REV-ELEC-2 R2-05)', is_='77.7 g / 2.61 s: 29.2 g/s x 2.66 s of flow divided by '
             'the 2.61 s both-open time (flow time and both-open time mixed)', vs_basis_pct=r(100 * (29.8 / basis - 1), 2),
             verdict='definition mismatch; not a flow rate'),
        dict(value_g_s=BD['inputs']['mdot_sil_g_s'], source='bleed_driver_v1.json mdot_sil_g_s (SIL S12 nominal)', is_='the SIL liquid rate '
             'applied from t = 0 (no vapour at the purge start); SIL flux 57187 kg/m2s at Cd 0.70 on the 1.0 mm area',
             vs_basis_pct=r(100 * (BD['inputs']['mdot_sil_g_s'] / basis - 1), 2),
             verdict='0.6 % above the Combustion all-liquid rate (31.24 g/s); as a mean rate it assumes no line vapour (+7.8 % on M(2.5 s))'),
        dict(value_g_s=32.0, source='Electronics line-203 (3) item (REV-ELEC-2 R2-05)', is_='83.6 g / 2.61 s: 31.44 g/s x 2.66 s divided by the '
             '2.61 s both-open time', vs_basis_pct=r(100 * (32.0 / basis - 1), 2), verdict='definition mismatch on the SIL value'),
        dict(value_g_s=r(rl, 2), source='Combustion all-liquid two-tap rate (v2.4a/v2.4b H16 stuck-open, catch-volume sizing)',
             is_='marginal (liquid-phase) rate at 289.5 K', vs_basis_pct=r(100 * (rl / basis - 1), 2),
             verdict='kept for stuck-open outflow and for the mass beyond the cap (marginal rate); not the mean-rate basis')]
    out = dict(
        version='v2.4b', date='2026-10-19', script='02-combustion/src/purge_basis_line216_v2p4b.py', script_sha256_16=sha16(os.path.abspath(__file__)),
        request='LEAD CHANGELOG line 216 (5) and lead message 2026-10-13 ~19:05Z: ONE purge flow basis (g/s) with its derivation and uncertainty',
        inputs=dict(lead_items_203_205_v2p4b=sha16(li_f), a1_profile_line213_v2p4b=sha16(a1_f), cold_flow_start_lift_v2p4b=sha16(cf_f),
                    bleed_driver_v1='06-electronics/results/bleed_driver_v1.json %s (read only)' % sha16(bd_f),
                    changelog_line_216='%d chars, text sha16 %s' % (len(l216[0]), hashlib.sha256(l216[0].encode()).hexdigest()[:16])),
        basis=dict(
            mdot_g_s=r(basis, 2), value_tag='DERIVED (from SIM records on ASSUMED Cd 0.70 and slip brackets; Dyer flux CoolProp HEOS)',
            definition=('mean vented rate over the flow that vents 76 g, on the Combustion bound at the 289.5 K warm-end relight state: '
                        'mdot = 76 g / t76; use with flow time = both-open overlap + (t_close - t_open)'),
            state='289.5 K, P_sat %.2f bar (warm end of the 283.15-289.5 K relight bracket; the 210 m relight state is MISSING, OI-49)' % P0,
            law=dict(r_liq_g_s=r(rl, 4), r_vap_g_s=r(rv, 4), t_vapour_s=r(tv, 4),
                     form='M(t) = r_vap t (t <= t_v); r_vap t_v + r_liq (t - t_v) (t > t_v); DERIVED upper bound of the v2.4a records'),
            t76_flow_s=r(t76, 4), cap_overlap_s=r(cap_overlap, 4),
            cap_rule='until CF-4 / B-BLEED-1: both-open overlap <= 76 g / %.2f g/s - 0.05 s = %.3f s (valve times ASSUMED 30 / 80 ms)' % (basis, cap_overlap),
            beyond_cap_rule='for flows longer than t76 the incremental rate is the all-liquid rate %.2f g/s (the stuck-open rate); the basis '
                            'times flow time understates the bound beyond t76 (hardware-window row)' % rl,
            equivalences=equivalences),
        candidates=cand,
        uncertainty=dict(tank_state=by_state, Cd=by_cd, flashing_model=by_model, line_vapour=by_line, combined_bounds=combo,
                         valve_times='(t_close - t_open) = 0.05 s ASSUMED (30 / 80 ms); it enters the cap, not mdot; measured in B-BLEED-1',
                         direction_at_210m=('warmer relight state (A1-2): mdot_eq rises %.2f g/s per K above 289.5 K; shorter coast, less line heat: '
                                            'less vapour at the purge start, mdot_eq moves toward the all-liquid %.2f g/s; magnitudes MISSING '
                                            '(records not re-run; GNC 210 m duty-cycle record not flown)'
                                            % ((by_state['291.15K']['mdot_eq_g_s'] - basis) / (291.15 - 289.5), rl))),
        g80_high_basis_sensitivity=g80,
        consequences=[
            'All teams carry %.2f g/s with flow time = overlap + 0.05 s until CF-4 / B-BLEED-1 (line 216 (5)); GNC G73 stays the nominal arm '
            '(73.1 g at the 2.5 s schedule on the basis; 72.93 g on the bound) and G80 the high-basis sensitivity' % basis,
            'ECU measured-time cap: overlap <= 76 g / mdot_measured - (t_close - t_open)_measured, with mdot_measured on the same definition '
            '(vented mass of a scheduled-length purge / its flow time); on the basis the cap is %.3f s, 0.098 s above the 2.45 s schedule' % cap_overlap,
            'the 2.55 s provisional cap is %.3f s above the basis cap: 76.05 g on the bound and on the basis (at the limit)' % (CAP_PROV_S - cap_overlap),
            'SIL S12: replace 31.44 g/s x t (no line vapour) by the basis (or by the two-segment law) for vented-mass statements; keep the '
            'liquid rate for stuck-open',
            'if B-BLEED-1 measures more than 30.4 g/s on this definition, the 2.5 s schedule itself exceeds 76 g; the needed flow is 1.9 s '
            'unlined / 2.2 s lined (REPORT §2.8), so the schedule can shorten without losing the purge class'],
        tags=dict(records='SIM (purge_duration_v2p4 trade records; Cd 0.70, slip brackets ASSUMED)', law_basis='DERIVED',
                  fluxes='DERIVED (CoolProp HEOS; Dyer / HEM / SPI as published in cold_flow_start_lift_v2p4b.json)',
                  Cd_bracket='ASSUMED 0.60-0.80', valve_times='ASSUMED (Electronics)', electronics_values='as published by Electronics',
                  status='not physical evidence; nothing here is physical approval'))
    json.dump(out, open(out_f, 'w'), indent=1)
    print('basis %.3f g/s t76 %.4f s cap overlap %.4f s' % (basis, t76, cap_overlap))
    print('state', {k: v['mdot_eq_g_s'] for k, v in by_state.items()})
    print('Cd', {k: v['mdot_eq_g_s'] for k, v in by_cd.items()})
    print('model', {k: v['mdot_eq_g_s'] for k, v in by_model.items()})
    print('line', {k: v.get('mdot_eq_g_s') for k, v in by_line.items()})
    print('combo', combo)
    print('g80', g80)
    print('equiv', equivalences)
    print('wrote', out_f, sha16(out_f))


if __name__ == '__main__':
    main(*sys.argv[1:7])

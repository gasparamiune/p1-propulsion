"""Final fold of Combustion v2.4b (2026-10-19): LEAD CHANGELOG lines 214-228 and the lead requests of 2026-10-19 (items 1-5) into the
staged v2.4b files (REPORT 768d7d41b5937eda, combustion.json 593dc296b155cd8e, CF-4 v2.1 86cd01e34c28aa82; T1-T4 v3 unchanged).

Order: CF-4 (P5 basis, A1 210 m decided) -> combustion.json (new keys; replaced values under *_superseded; the new CF-4 hash) ->
REPORT (targeted replacements, each asserted unique, plus §16; the new interface and CF-4 hashes).  Every number in the new text
is read from the v2.4b data files at build time (hashes asserted); CHANGELOG lines are quoted by hash.  Nothing is physical approval.
usage: python -I build_final_fold_v2p4b.py STAGED_DIR DATA_V2P4B_DIR CHANGELOG DATASHEET_MD OUT_DIR
"""
import hashlib, json, math, os, re, shutil, sys
sys.dont_write_bytecode = True
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
shs = lambda s: hashlib.sha256(s.encode('utf-8')).hexdigest()[:16]
EXPECT_STAGED = {'REPORT.md': '768d7d41b5937eda', 'combustion.json': '593dc296b155cd8e', 'CF-4-SPEC.md': '86cd01e34c28aa82',
                 'T1-T4-REGRESSION-SPEC.md': 'b0c42b09ba47cb9c'}
EXPECT_DATA = {'purge_basis_line216_v2p4b.json': 'ca2ee1f0ea0f0194', 'p4c_lit_side_v2p4b.json': '12f7699ddbeeecda',
               'tank_2p20kg_option_v2p4b.json': '59995244124f7c9a', 'fa1_spectra_damped_v2p4b.json': '3a84a905052d5364',
               'fa1_per_mode_peq_v2p4b.json': '7ade3ee7ef544f7a', 'fa1_modal_th_bound_v2p4b.json': '639f5fbf3db77ee8'}
NEW_DATA = ['purge_basis_line216_v2p4b.json', 'p4c_lit_side_v2p4b.json', 'tank_2p20kg_option_v2p4b.json', 'fa1_spectra_damped_v2p4b.json',
            'fa1_pressure_spectra_published_v2p4b.csv', 'fa1_pressure_spectra_modal_periods_v2p4b.csv', 'fa1_per_mode_peq_v2p4b.json',
            'fa1_modal_th_bound_v2p4b.json', 'fa1_relative_spectrum_E_v2p4b.csv']
NEW_SRC = ['purge_basis_line216_v2p4b.py', 'p4c_lit_side_v2p4b.py', 'tank_2p20kg_option_v2p4b.py', 'fa1_spectra_damped_v2p4b.py',
           'fa1_per_mode_peq_v2p4b.py', 'fa1_modal_th_bound_v2p4b.py', 'build_datasheet_inputs_v2p4b.py', 'build_final_fold_v2p4b.py']
BASE, ALLG = 'vapour_once|rounded_Cd1.0|grid_OF4-12|all', 'all|all|incl_OF3-3.5|all'
SCALES = (1.00, 0.90, 0.85)
ZETAS = (0.0, 0.02, 0.05)
P_AMB = 1.01325
HERE = os.path.dirname(os.path.abspath(__file__))


def rep(txt, old, new, count=1, label=''):
    n = txt.count(old)
    assert n == count, ('replacement anchor', label or old[:80], n, count)
    return txt.replace(old, new)


def line_with(txt, prefix):
    L = txt.split('\n')
    hits = [i for i, x in enumerate(L) if x.startswith(prefix)]
    assert len(hits) == 1, (prefix, hits)
    return hits[0]


def append_to_line(txt, prefix, add):
    L = txt.split('\n'); i = line_with(txt, prefix)
    L[i] = L[i] + add
    return '\n'.join(L)


def insert_after_line(txt, prefix, new_lines):
    L = txt.split('\n'); i = line_with(txt, prefix)
    return '\n'.join(L[:i + 1] + new_lines + L[i + 1:])


def f1(x):
    return '%.1f' % x


def f2(x):
    return '%.2f' % x


def iv(a, nd=1):
    return ('%.*f-%.*f' % (nd, a[0], nd, a[1])) if abs(a[1] - a[0]) >= 0.5 * 10 ** (-nd) else ('%.*f' % (nd, a[0]))


def main(staged, dd, chlog_f, ds_f, out):
    for f, h in EXPECT_STAGED.items():
        assert sha(os.path.join(staged, f)) == h, (f, sha(os.path.join(staged, f)))
    got = {}
    for f, h in EXPECT_DATA.items():
        got[f] = sha(os.path.join(dd, f)); assert h is None or got[f] == h, (f, got[f])
    os.makedirs(out, exist_ok=True)
    J = lambda f: json.load(open(os.path.join(dd, f)))
    H = lambda f: sha(os.path.join(dd, f))
    PB, P4, TK = J('purge_basis_line216_v2p4b.json'), J('p4c_lit_side_v2p4b.json'), J('tank_2p20kg_option_v2p4b.json')
    DS, PM, TH = J('fa1_spectra_damped_v2p4b.json'), J('fa1_per_mode_peq_v2p4b.json'), J('fa1_modal_th_bound_v2p4b.json')
    for x in (DS, TH):
        assert not x.get('smoke_test_subset'), 'smoke-test output'
    assert PM['inputs']['damped_json'].endswith(H('fa1_spectra_damped_v2p4b.json'))
    for f in NEW_SRC:
        if f != 'build_final_fold_v2p4b.py':
            assert os.path.exists(os.path.join(HERE, f)), f
    for X, f in ((PB, 'purge_basis_line216_v2p4b.py'), (P4, 'p4c_lit_side_v2p4b.py'), (TK, 'tank_2p20kg_option_v2p4b.py'),
                 (DS, 'fa1_spectra_damped_v2p4b.py'), (PM, 'fa1_per_mode_peq_v2p4b.py'), (TH, 'fa1_modal_th_bound_v2p4b.py')):
        assert X['script_sha256_16'] == sha(os.path.join(HERE, f)), ('script hash recorded in data differs from src', f)
    CL = open(chlog_f, encoding='utf-8').read().split('\n')
    assert open(chlog_f, 'rb').read().count(b'\n') >= 228
    lh = {str(n): shs(CL[n - 1]) for n in range(214, 229)}
    l227 = CL[226]; l228 = CL[227]; l223 = CL[222]
    assert 'RV6-05' in l227 and 'sum(share_i x S(T_i))' in l228 and '116.2-117.7' in l223
    ds_sha = sha(ds_f)

    # ------------------------------------------------------------------ numbers used in the text
    bm = DS['band_maxima']
    def band(b, node, grp, z):
        x = bm[b]['%s|%s|zeta%g' % (node, grp, z)]; return x['value_bar'], x['period_ms'], x['case']
    BANDS = (('T_le_0p1ms', 'T <= 0.1 ms'), ('T_0p1_to_1ms', '0.1 < T <= 1 ms'), ('T_1_to_20ms', '1 < T <= 20 ms'), ('T_20_to_50ms', '20 < T <= 50 ms'))
    resk = {s: [k for k in bm if k.startswith('T_le_') and k.endswith('_residual_s%.2f' % s)][0] for s in SCALES}
    hA = {b: {z: band(b, 'head', 'all', z) for z in ZETAS} for b, _ in BANDS}
    hB = {b: {z: band(b, 'head', 'baseline', z) for z in ZETAS} for b, _ in BANDS}
    aA = {b: {z: band(b, 'aft', 'all', z) for z in ZETAS} for b, _ in BANDS}
    aB = {b: {z: band(b, 'aft', 'baseline', z) for z in ZETAS} for b, _ in BANDS}
    chk = DS['envelopes'][ALLG].get('P_head|zeta0_exact_minus_sampled_bar', {})
    cm = DS['checks']['zeta0_modal_exact_minus_sampled_bar']
    prop = {'T_le_0p1ms': math.ceil(hA['T_le_0p1ms'][0][0]), 'T_0p1_to_1ms': math.ceil(hA['T_0p1_to_1ms'][0][0]),
            'T_0p1_to_1ms_z002': math.ceil(hA['T_0p1_to_1ms'][0.02][0]), 'T_1_to_20ms': math.ceil(hA['T_1_to_20ms'][0][0]),
            'T_20_to_50ms': math.ceil(hA['T_20_to_50ms'][0][0])}
    # TC-01 per mode
    jt = TH['results'][ALLG]['nodes']['TC-01_JFWD']; lt = TH['results'][ALLG]['nodes']['TC-01_LC1']
    jtb = TH['results'][BASE]['nodes']['TC-01_JFWD']
    Pby, Pbu = TH['jfwd_breakeven']['yield_bar_abs'], TH['jfwd_breakeven']['ult_bar_abs']
    assert abs(Pby - PM['jfwd_breakeven']['yield_bar_abs']) < 1e-6 and abs(Pbu - PM['jfwd_breakeven']['ult_bar_abs']) < 1e-6
    def thw(d, z, key):
        return max((d['zeta%g|s%.2f' % (z, s)][key], s) for s in SCALES)
    pmn = PM['nodes']
    def pmr(node, z, s, comb, spec='head|all', fn='principal'):
        return pmn[node]['functionals'][fn]['results']['%s|zeta%g|s%.2f' % (spec, z, s)][comb]
    def pm_worst(node, z, comb, spec='head|all', fn='principal'):
        return [min(pmr(node, z, s, comb, spec, fn)[0] for s in SCALES), max(pmr(node, z, s, comb, spec, fn)[1] for s in SCALES)]
    jf = pmn['TC-01_JFWD']['functionals']['principal']
    n_known_j = len(jf['known_modes'])
    n_unpub_j = sum(b['n_unpublished'] for b in jf['bins'].values())
    r_j = jf['residual_share']
    ms = lambda P, Pb: Pb / P - 1.0
    th0, th2, th5 = (thw(jt, z, 'TH_upper_bar_abs') for z in ZETAS)
    er0, er2, er5 = (thw(jt, z, 'E_rule_upper_bar_abs') for z in ZETAS)
    kc0 = thw(jt, 0, 'known_coherent_bar_abs')
    lth0, lth2 = thw(lt, 0, 'TH_upper_bar_abs'), thw(lt, 0.02, 'TH_upper_bar_abs')
    ler0 = thw(lt, 0, 'E_rule_upper_bar_abs')
    sg0, ab0, sr0 = (pm_worst('TC-01_JFWD', 0, c) for c in ('signed', 'ABS', 'SRSS'))
    sg2, ab2, sr2 = (pm_worst('TC-01_JFWD', 0.02, c) for c in ('signed', 'ABS', 'SRSS'))
    lsg0, lab0, lsr0 = (pm_worst('TC-01_LC1', 0, c) for c in ('signed', 'ABS', 'SRSS'))
    pg_all = TH['results'][ALLG]['P_gauge_peak_bar']; pg_base = TH['results'][BASE]['P_gauge_peak_bar']
    # J-FWD consequence of the two options of §16.3 (J-FWD is a 0.1-1 ms path, line 223): its largest published shares are modes 22 / 23
    mpT = {}
    for ln in open(os.path.join(dd, 'fa1_pressure_spectra_modal_periods_v2p4b.csv')).read().split('\n')[1:]:
        if ln:
            x = ln.split(','); mpT.setdefault(int(x[0]), []).append(float(x[3]))
    T2223 = [min(mpT[22] + mpT[23]), max(mpT[22] + mpT[23])]
    assert 0.1 < T2223[0] and T2223[1] <= 1.0, T2223
    kmj = jf['known_modes']; top2 = sorted(kmj, key=lambda k: -abs(kmj[k]))[:2]
    assert sorted(top2) == ['22', '23'], top2
    c22, c23 = kmj['22'], kmj['23']
    CONS = {k: dict(P_bar_abs=v[0], s=v[1], MS_yield=round(ms(v[0], Pby), 6), MS_ult=round(ms(v[0], Pbu), 6)) for k, v in
            (('band_a', (prop['T_0p1_to_1ms'], None)), ('band_a_if_zeta0p02_measured', (prop['T_0p1_to_1ms_z002'], None)),
             ('rule_b_time_domain_bound', th0), ('rule_b_E_rule', er0))}
    rlim = abs(r_j) + (Pby - th0[0]) / jt['zeta0|s%.2f' % th0[1]]['E_res_bar']
    def verdict(lo, hi, Pb):
        return 'below' if hi < Pb else ('above' if lo > Pb else 'straddles')
    # other nodes (spectral sums, zeta 0, worst factor)
    other = []
    for key in ('TC-02_FA1', 'TC-02_LC1', 'TC-09_FA1', 'TC-09_LC1_B1_2', 'TC-09_LC1_B1_21', 'NZ-01_FA1', 'NZ-01_LC1_FA1S', 'NZ-01_LC1'):
        if key not in pmn:
            continue
        nd = pmn[key]
        other.append((key, nd['role'], pm_worst(key, 0, 'signed'), pm_worst(key, 0, 'ABS'), pm_worst(key, 0, 'SRSS'),
                      nd.get('breakeven_bar_abs_from_tags'), nd['functionals']['principal']['residual_share']))
    cq = PM['cqc_rho_modes_22_23']
    # purge, lift, P4c, tank
    pb = PB['basis']; un = PB['uncertainty']
    ts = un['tank_state']; cdv = un['Cd']
    sl = P4['start_level_lift']; lit = P4['lit_side']['lift_0p21776mm']; lit2 = P4['lit_side']['lift_0p2039mm_sensitivity']
    w5, w8 = lit['torch0.0']['window_0.5s'], lit['torch0.0']['window_0.8s']
    w8b = lit2['torch0.0']['window_0.8s']
    fo = P4['flame_out_side']['by_state']
    c210 = TK['cases_2p00kg_210m']['cases']; k210 = sorted(c210, key=lambda k: -c210[k]['burn_s'])
    ca, cb = c210[k210[0]], c210[k210[1]]
    t871, t892, t924 = TK['cases']['p99_8.71s'], TK['cases']['p99_8.92s'], TK['cases']['max_9.24s']
    m227 = re.search(r"burn p99 ([0-9.]+) / ([0-9.]+) s at 210 m against ([0-9.]+) / ([0-9.]+) s at 285 m", l227)
    b210 = m227.groups()

    # ------------------------------------------------------------------ CF-4
    cf = open(os.path.join(staged, 'CF-4-SPEC.md'), encoding='utf-8').read()
    cf = rep(cf, 'Version 2.1 (Combustion v2.4b), 2026-10-13.', 'Version 2.1 (Combustion v2.4b), 2026-10-19 (staged 2026-10-13; final fold of LEAD lines '
             '214-228, last change bullet below).')
    cf = rep(cf, '- LEAD line 213 (founder decision): the A1 apogee target is about 210 m (it was the 300 m lead default and the 285 m trim).',
             '- LEAD line 213 (founder decision), DECIDED by lines 214 and 227 (1): the A1 apogee target is 210 m (it was the 300 m lead default and the 285 m trim).')
    cf = insert_after_line(cf, '- LEAD line 213 (founder decision), DECIDED', [
        '- Final fold (2026-10-19; LEAD lines 214-228, 216 (5) and 216 (9)): P5 names ONE purge flow basis, %.2f g/s (DERIVED: 76 g over %.3f s of flow '
        'at the 289.5 K warm-end relight state on the Combustion record bound; REPORT §16.5), and the measured-time form of the cap that CF-4 / B-BLEED-1 '
        'set: both-open overlap <= 76 g / mdot_measured - (t_close - t_open). The start-level lift at the A1 relight state is confirmed as %.5f mm '
        '(216 (9); REPORT §16.6). The A1 duty cycle does not shorten at 210 m (227 (9), RV6-05); the 210 m relight state is still MISSING (OI-49).'
        % (pb['mdot_g_s'], pb['t76_flow_s'], sl['value_mm'])])
    cf = rep(cf, 'A1 profile (LEAD line 213; new in v2.1). The A1 apogee target is about 210 m; GNC sets the exact band (gnc.json v3.2).',
             'A1 profile (LEAD lines 213, 214 and 227 (1); new in v2.1). The A1 apogee target is 210 m, DECIDED (line 214; accepted in 227 (1)); gnc.json v3.2 '
             'carries the record (not in the hub at this build).')
    cf = rep(cf, 'a mass below 80 % of that flags a restricted path | LEAD plan <= 76 g per purge.',
             'a mass below 80 %% of that flags a restricted path. Flow basis (LEAD 216 (5)): ONE basis, %.2f g/s = 76 g / %.3f s of flow at 289.5 K '
             '(flow time = both-open overlap + (t_close - t_open), valve times ASSUMED 30 / 80 ms): strict 76 g needs overlap <= %.3f s. After the IS-2 '
             'runs at the A1 relight state the cap is set from the measurement: overlap <= 76 g / mdot_measured - (t_close - t_open), with mdot_measured '
             '= M(t_flow) / t_flow from the load cell and t_open, t_close from the valve position channels | LEAD plan <= 76 g per purge; basis LEAD 216 (5) '
             '(`purge_basis_line216_v2p4b.json` `%s`).' % (pb['mdot_g_s'], pb['t76_flow_s'], pb['cap_overlap_s'], H('purge_basis_line216_v2p4b.json')))
    cf_out = os.path.join(out, 'CF-4-SPEC.md')
    open(cf_out, 'w', encoding='utf-8').write(cf)
    cf_sha = sha(cf_out)
    shutil.copyfile(os.path.join(staged, 'T1-T4-REGRESSION-SPEC.md'), os.path.join(out, 'T1-T4-REGRESSION-SPEC.md'))
    assert sha(os.path.join(out, 'T1-T4-REGRESSION-SPEC.md')) == EXPECT_STAGED['T1-T4-REGRESSION-SPEC.md']

    # ------------------------------------------------------------------ interface
    CJ = json.load(open(os.path.join(staged, 'combustion.json')))
    n_keys0 = len(CJ)
    CJ['date_superseded'] = CJ['date']; CJ['date'] = '2026-10-19'
    CJ['revision_note_superseded'] = CJ['revision_note']
    CJ['revision_note'] = CJ['revision_note'] + (
        ' Final fold (2026-10-19): LEAD CHANGELOG lines 214-228 and the lead requests of 2026-10-19: FA-1 spectra as data with damping '
        '(fa1_spectra_damped_v2p4b), the per-mode TC-01 equivalent pressure (fa1_per_mode_peq_v2p4b), ONE purge flow basis 29.25 g/s '
        '(purge_basis_line216_v2p4b), the start-level lift at the A1 relight state (start_level_lift_v2p4b.v.line216_9), the GNC P4c lit side '
        '(p4c_lit_side_v2p4b), the 2.20 kg tank option (tank_2p20kg_option_v2p4b), the datasheet inputs (datasheet_inputs_v2p4b); A1 210 m decided '
        '(214, 227 (1)) and the A1 duty-cycle statement corrected (227 (9)); open items OI-50 to OI-52 (final_fold_v2p4b).')
    CJ['status_superseded'] = CJ['status']
    CJ['status'] = ('v2.4b REVISION (digital only, Por revisar), final fold 2026-10-19. Design point unchanged. No number is MEASURED. The relight claim is '
                    'gated by CF-4; FA-1 is accepted for design continuation only. Decided by the lead and folded: L* = 1.3 s with no unpurged relight below '
                    'it (186 (1)); the R2 command hold at the start level (186 (2), margin CONDITIONAL 194 (4)); the FA-1 period domain (194 (1)), which the '
                    'published all-case spectrum exceeds below 1 ms (OI-41; restatement and per-mode rule proposed, final_fold_v2p4b); the unpurged '
                    'alternative NOT ADOPTED (204 (2)); A1 apogee target 210 m DECIDED (214, 227 (1)): the A1 values are 300 m / 285 m comparators until the '
                    '210 m record, the A1 duty cycle does not shorten (227 (9)), B1 governs sizing; tank 2.00 kg (219), 2.20 kg an option with B1 / thermal / '
                    'erosion TO-VERIFY (OI-50). Nothing here is physical approval.')
    tags_std = 'not physical evidence; nothing here is physical approval'
    CJ['purge_basis_line216_v2p4b'] = dict(v=dict(
        answer='ONE basis: %.2f g/s, the mean vented rate of the flow that vents 76 g on the Combustion record bound at the 289.5 K warm-end relight '
               'state (76 g / %.4f s of flow); use with flow time = both-open overlap + (t_close - t_open)' % (pb['mdot_g_s'], pb['t76_flow_s']),
        mdot_g_s=pb['mdot_g_s'], t76_flow_s=pb['t76_flow_s'], cap_overlap_s=pb['cap_overlap_s'], law=pb['law'], cap_rule=pb['cap_rule'],
        beyond_cap_rule=pb['beyond_cap_rule'], measured_time_form='after CF-4 / B-BLEED-1: both-open overlap <= 76 g / mdot_measured - (t_close - t_open)',
        uncertainty_g_s=dict(tank_state_283p15_to_297p15K=[ts['283.15K']['mdot_eq_g_s'], ts['297.15K']['mdot_eq_g_s']],
                             Cd_0p60_to_0p80=[min(x['mdot_eq_g_s'] for x in cdv.values()), max(x['mdot_eq_g_s'] for x in cdv.values())],
                             detail='data/v2p4b/purge_basis_line216_v2p4b.json uncertainty, g80_high_basis_sensitivity'),
        equivalences=pb['equivalences'], file='02-combustion/data/v2p4b/purge_basis_line216_v2p4b.json', sha256_16=H('purge_basis_line216_v2p4b.json')),
        tag='DERIVED (from SIM records on ASSUMED Cd 0.70 and slip brackets; valve times ASSUMED); LEAD 216 (5) request', src='REPORT v2.4b §16.5')
    pbv = CJ['purge_basis_v2p4b']['v']
    pbv['answer_superseded'] = pbv['answer']
    pbv['answer'] = ('ONE basis (LEAD 216 (5)): %.2f g/s over the flow time (both-open overlap + (t_close - t_open)); it equals the record bound at the '
                     '76 g point (%.4f s of flow) and is conservative before it; beyond it the incremental rate is the all-liquid 31.24 g/s; the 29.8 and '
                     '32.0 g/s readings of 203 (3) are superseded (purge_basis_line216_v2p4b)' % (pb['mdot_g_s'], pb['t76_flow_s']))
    slv = CJ['start_level_lift_v2p4b']['v'] if 'v' in CJ['start_level_lift_v2p4b'] else CJ['start_level_lift_v2p4b']
    slv['line216_9'] = dict(lift_mm=sl['value_mm'], state=sl['state'], tag=sl['tag'], rule=sl['rule'], at_20C_mm=0.2039,
                            file='02-combustion/data/v2p4b/p4c_lit_side_v2p4b.json', sha256_16=H('p4c_lit_side_v2p4b.json'))
    CJ['p4c_lit_side_v2p4b'] = dict(v=dict(
        lift_mm=sl['value_mm'], windows_s=[0.5, 0.8], time_origin=P4['lit_side']['time_origin'], statistic=P4['lit_side']['statistic'],
        F_min_N=dict(lift_0p21776mm=w8['F_min_over_corners_N'], lift_0p2039mm=w8b['F_min_over_corners_N']),
        corners_never_37p16N_0p8s=dict(lift_0p21776mm=w8['thresholds']['37.16 N']['n_corners_never'], lift_0p2039mm=w8b['thresholds']['37.16 N']['n_corners_never']),
        latest_crossing_37p16N_s=dict(lift_0p21776mm=[w8['thresholds']['37.16 N']['latest_first_crossing_after_E2_s'], w8['thresholds']['37.16 N']['latest_plus_3_frames_s']]),
        F_at_1s_range_N=lit['F_at_1s_range_N'], flame_out_bound_N=dict((k, v['F_cold_bound_at_h_s_N']) for k, v in fo.items()),
        implications=P4['implications'], missing=P4['missing'], file='02-combustion/data/v2p4b/p4c_lit_side_v2p4b.json', sha256_16=H('p4c_lit_side_v2p4b.json')),
        tag='SIM lit (grain_q1d v2, ASSUMED bands); DESIGN lift (ECU table); DERIVED flame-out bound, CONDITIONAL', src='REPORT v2.4b §16.7')
    CJ['fa1_spectra_damped_v2p4b'] = dict(v=dict(
        files={'02-combustion/data/v2p4b/fa1_spectra_damped_v2p4b.json': H('fa1_spectra_damped_v2p4b.json'),
               '02-combustion/data/v2p4b/fa1_pressure_spectra_published_v2p4b.csv': H('fa1_pressure_spectra_published_v2p4b.csv'),
               '02-combustion/data/v2p4b/fa1_pressure_spectra_modal_periods_v2p4b.csv': H('fa1_pressure_spectra_modal_periods_v2p4b.csv'),
               '02-combustion/data/v2p4b/fa1_thrust_spectra_dense_v2p4b.csv': H('fa1_thrust_spectra_dense_v2p4b.csv')},
        columns='period_ms, then head / aft x baseline / all x zeta 0 / 0.02 / 0.05 (bar abs)', periods_ms=[min(DS['periods_ms']['dense']), max(DS['periods_ms']['dense'])],
        n_periods_dense=len(DS['periods_ms']['dense']),
        head_all_band_maxima_bar_abs={b: {('zeta%g' % z): hA[b][z][0] for z in ZETAS} for b, _ in BANDS},
        head_baseline_band_maxima_bar_abs={b: {('zeta%g' % z): hB[b][z][0] for z in ZETAS} for b, _ in BANDS},
        aft_all_band_maxima_bar_abs={b: {('zeta%g' % z): aA[b][z][0] for z in ZETAS} for b, _ in BANDS},
        residual_band_head_all_bar_abs={('s%.2f' % s): {('zeta%g' % z): bm[resk[s]]['head|all|zeta%g' % z]['value_bar'] for z in ZETAS} for s in SCALES},
        line194_1_values_bar_abs={'T_le_0p1ms': 90, 'T_0p1_to_1ms': {'FA1D_yield': 93, 'FA1U_ult': 102}, 'T_gt_1ms': 'spectrum or FA1S 151.04'},
        contradiction='all-case head maxima exceed the 194 (1) values below 1 ms (OI-41)',
        proposal=dict(band_values_bar_abs=dict(T_le_0p1ms=prop['T_le_0p1ms'], T_0p1_to_1ms=prop['T_0p1_to_1ms'], T_0p1_to_1ms_if_zeta0p02_measured=prop['T_0p1_to_1ms_z002'],
                                               T_1_to_20ms=prop['T_1_to_20ms'], T_20_to_50ms=prop['T_20_to_50ms'], bound_all_periods='FA1S 151.04'),
                      per_mode_rule='Peq = p_amb + max_t[g + sum_i c_i e_i + r e_res] with the full share vector; until it is published, the E rule '
                                    'p_amb + max g + sum |c_i| E_i + |r| E_res (rigorous, exact in the static limit); REPORT §16.3',
                      consequence_TC01_JFWD=dict(CONS, breakeven_bar_abs={'yield': Pby, 'ultimate': Pbu},modes_22_23_T_ms=[round(T2223[0], 4), round(T2223[1], 4)],
                                                 note='J-FWD is a 0.1-1 ms path (line 223); zeta 0, worst FE factor s; MS = break-even / P - 1; the residual '
                                                      'caveat of REPORT §16.4 applies to the time-domain bound; DERIVED on SIM inputs')),
        checks=dict(zeta0_modal_exact_minus_sampled_bar=cm, zeta0_dense_exact_minus_sampled_bar_head_all=chk),
        thrust_spectrum='fa1_thrust_spectra_dense_v2p4b.csv to 200 ms (unchanged; published with the staged v2.4b)'),
        tag='SIM histories (v2.4a construct, ASSUMED inputs); DERIVED spectra; damping ASSUMED (0.02, 0.05; 0 = bound); proposal for the LEAD',
        src='REPORT v2.4b §16.2-16.3')
    def thd(d):
        return {k: dict(TH_upper_bar_abs=v['TH_upper_bar_abs'], E_rule_upper_bar_abs=v['E_rule_upper_bar_abs'], known_coherent_bar_abs=v['known_coherent_bar_abs'],
                        unpublished_bound_bar=v['unpublished_bound_bar'], residual_term_bar=v['residual_term_bar']) for k, v in d.items()}
    CJ['fa1_per_mode_peq_v2p4b'] = dict(v=dict(
        request='LEAD 228 (c) (i)-(ii); lead request 2026-10-19 item 2',
        jfwd_breakeven_bar_abs=dict(yield_=Pby, ult=Pbu),
        jfwd_spectral_sums_bar_abs={'zeta0': dict(signed=sg0, ABS=ab0, SRSS=sr0), 'zeta0.02': dict(signed=sg2, ABS=ab2, SRSS=sr2),
                                    'note': 'intervals over the unpublished shares and the worst of the factors x0.85 / 0.90 / 1.00; head all-case spectrum'},
        lc1_spectral_sums_bar_abs={'zeta0': dict(signed=lsg0, ABS=lab0, SRSS=lsr0)},
        time_domain_bound_all_case=dict(TC01_JFWD=thd(jt), TC01_LC1=thd(lt)),
        jfwd_margins_all_case=TH['jfwd_margins_all_case'], cqc_rho_modes_22_23=cq['rho'],
        shares_published_jfwd=dict(n_known=n_known_j, n_unpublished=n_unpub_j, residual=r_j),
        jfwd_bound_residual_caveat=dict(residual_signed_share=r_j, zeta=0, s=th0[1], E_res_bar=jt['zeta0|s%.2f' % th0[1]]['E_res_bar'],
                                        residual_abs_share_limit_for_yield=round(rlim, 6),
                                        note='the time-domain bound takes the residual at its published signed share; it stays below the yield '
                                             'break-even while the residual absolute share is <= the limit (REPORT §16.4)'),
        consequence_of_line194_options='fa1_spectra_damped_v2p4b.v.proposal.consequence_TC01_JFWD',
        missing=PM['missing'], files={'02-combustion/data/v2p4b/fa1_per_mode_peq_v2p4b.json': H('fa1_per_mode_peq_v2p4b.json'),
                                      '02-combustion/data/v2p4b/fa1_modal_th_bound_v2p4b.json': H('fa1_modal_th_bound_v2p4b.json'),
                                      '02-combustion/data/v2p4b/fa1_relative_spectrum_E_v2p4b.csv': H('fa1_relative_spectrum_E_v2p4b.csv')}),
        tag='DERIVED (SDOF / modal superposition bounds) on SIM shares (FEA3D modal_v351ca2b_c71, read only) and SIM histories; damping ASSUMED; '
            'break-even SIM (FEA3D); not a margin approval', src='REPORT v2.4b §16.4')
    CJ['tank_2p20kg_option_v2p4b'] = dict(v=dict(
        decision='tank stays 2.00 kg (LEAD 219, founder); 2.20 kg is an option; B1 / thermal / erosion TO-VERIFY (227 (9))',
        cases=TK['cases'], cases_2p00kg_210m=TK['cases_2p00kg_210m'], findings=TK['findings'], open_item=TK['open_item'],
        file='02-combustion/data/v2p4b/tank_2p20kg_option_v2p4b.json', sha256_16=H('tank_2p20kg_option_v2p4b.json')),
        tag=TK['tags']['scaling'] + '; ' + TK['tags']['records'], src='REPORT v2.4b §16.8')
    CJ['datasheet_inputs_v2p4b'] = dict(v=dict(file='02-combustion/DATASHEET-INPUTS-COMBUSTION.md', sha256_16=ds_sha,
                                               builder='02-combustion/src/build_datasheet_inputs_v2p4b.py', request='lead request 2026-10-19 item 5'),
                                        tag='index (each row carries its own tag)', src='REPORT v2.4b §16.9')
    a1 = CJ['a1_apogee_target_v2p4b']['v']
    tg = a1['target']
    tg['status'] = 'DECIDED: LEAD 214 (A1 = 210 m on the GNC rev4 line-208 band) and 227 (1) (accepted with the RV6-03 condition of 227 (8))'
    tg['lead_consequences_superseded'] = tg['lead_consequences']
    tg['lead_consequences'] = ('B1 governs thermal and erosion sizing; no new sizing case; tank stays 2.00 kg (219). The A1 duty cycle does NOT shorten '
                               '(227 (9), RV6-05: burn p99 %s / %s s at 210 m against %s / %s s at 285 m)' % b210)
    st = [s for s in a1['statements'] if s['id'] == 'A1-1'][0]
    st['direction_at_210m_superseded'] = st['direction_at_210m']
    st['direction_at_210m'] = ('NOT shorter (227 (9), RV6-05; corrects 213): burn p99 %s / %s s at 210 m against the 8.258 s A1 sizing counter (+%.1f %% at most); '
                               'first order (time ratio), nominal A1 throat-area growth %.2f %% per flight at n 0.5 (%.2f %% at n 0.68), web >= %.2f mm '
                               '(a x1.0 n 0.5) / %.2f mm (band corner); B1 still governs (LEAD); no new sizing case' % (
                                   b210[0], b210[1], (ca['time_ratio'] - 1) * 100, ca['erosion_nominal_dAt_pct'], ca['erosion_nominal_n068_dAt_pct'],
                                   ca['web_end_a1p0_n0p5_mm'], ca['web_end_min_band_a1p5_n0p35_mm']))
    st['status_superseded'] = st['status']
    st['status'] = ('COMPARATOR tables stay (300 m / 285 m); first-order 210 m values in tank_2p20kg_option_v2p4b.cases_2p00kg_210m; the 210 m grain run '
                    'waits for the record (OI-49). One insert per flight stays')
    dn = CJ['a1_duration_note_v2p4b']
    dn['line213_note_superseded'] = dn['line213_note']
    dn['line213_note'] = ('LEAD lines 213, 214, 227 (1): A1 apogee target 210 m, DECIDED. The A1-profile values here are from the 300 m / 285 m records and stay '
                          'as comparators. A1-1: the A1 duty cycle does NOT shorten (227 (9), RV6-05: burn p99 %s / %s s at 210 m); first-order values in '
                          'tank_2p20kg_option_v2p4b.cases_2p00kg_210m; B1 still governs thermal and erosion sizing (LEAD); no new sizing case. One insert per '
                          'flight stays (a1_apogee_target_v2p4b)' % (b210[0], b210[1]))
    thr = CJ['fa1_spectra_v2p4b']['v']['thrust']
    thr['rule_superseded'] = thr['rule']
    thr['rule'] = ('LEAD 194 (2): rectangle only for T <= 20 ms; for T > 20 ms the FA-1 long-period thrust spectrum (engine data for the mounting; '
                   'ICD-AIRFRAME v2.1 was removed from the finish scope by line 222)')
    LD = CJ['lead_decisions_folded_v2p4b']['v']
    LD.update({
        '214': 'A1 apogee target 210 m DECIDED: a1_apogee_target_v2p4b.v.target.status; CF-4 v2.1 §4; REPORT §16.1, §16.8',
        '215': 'REV-ELEC-2 result: read (Electronics v2.11); no Combustion change',
        '216 (5)': 'ONE purge flow basis 29.25 g/s: purge_basis_line216_v2p4b; purge_basis_v2p4b.v.answer; CF-4 P5; REPORT §16.5; OI-42',
        '216 (9)': 'start-level lift 0.21776 mm at the A1 relight state: start_level_lift_v2p4b.v.line216_9; REPORT §16.6',
        '216 (other)': 'Electronics items (v2.11): read; THE start-level lift stays the hold lift (OI-43)',
        '217, 220, 224, 226': 'FEA3D results: read for status; shares and break-even used from 221 / 225 (fa1_per_mode_peq_v2p4b)',
        '218': 'GNC rev4 staged: read (v32_proposals_rev4 item [15] T/W for the 2.20 kg option; burn p99 at 210 m via 227 (9))',
        '219': 'tank stays 2.00 kg (founder); 2.20 kg option: tank_2p20kg_option_v2p4b; OI-50',
        '221, 225': 'FEA3D modal shares (published subset) and FA-1 columns: fa1_per_mode_peq_v2p4b; OI-51',
        '222': 'ICD-AIRFRAME removed from scope: the two v2.4b references (REPORT §7.6 thrust note; fa1_spectra_v2p4b.v.thrust.rule) restated; no other change',
        '223': 'TC-01 J-FWD a 0.1-1 ms path, PROVISIONAL: the Combustion side of condition (a) in fa1_per_mode_peq_v2p4b (shares are FEA3D)',
        '227 (1), (5), (8)': '210 m accepted; R2 starve window 0.8 s (P4c window: p4c_lit_side_v2p4b); RV6-03 gate-delay arm is a GNC item',
        '227 (9)': 'A1 duty cycle does not shorten (RV6-05): a1_apogee_target_v2p4b.v.statements A1-1; 2.20 kg TO-VERIFY: tank_2p20kg_option_v2p4b',
        '228': 'third condition on TC-01: fa1_spectra_damped_v2p4b (published head spectrum, damping stated), fa1_per_mode_peq_v2p4b (per-mode Peq); '
               'band values restatement proposed (OI-41)'})
    OI = CJ['open_items_v2p4b']['v']
    ids = [x.get('id') for x in OI]
    def upd(i, item, action, owner=None):
        x = OI[ids.index(i)]
        x['item_superseded'] = x['item']; x['item'] = item
        x['action_superseded'] = x['action']; x['action'] = action
        if owner:
            x['owner_superseded'] = x['owner']; x['owner'] = owner
    upd('OI-41', 'FA-1 band values of 194 (1) below the published all-case head spectrum: T <= 0.1 ms %.1f > 90; 0.1-1 ms %.1f undamped (%.1f at zeta 0.02) > 93 / 102 '
                 'bar abs (fa1_spectra_damped_v2p4b)' % (hA['T_le_0p1ms'][0][0], hA['T_0p1_to_1ms'][0][0], hA['T_0p1_to_1ms'][0.02][0]),
        'lead: restate the band values (proposal %d / %d / %d / %d bar abs) or adopt the per-mode rule for paths with published shares (E rule until the '
        'full vector, OI-51); Mechanical re-checks TC-02; the flight Pc proof follows' % (prop['T_le_0p1ms'], prop['T_0p1_to_1ms'], prop['T_1_to_20ms'], prop['T_20_to_50ms']),
        'Lead; Mechanical')
    upd('OI-42', 'purge cap on the ONE basis %.2f g/s (216 (5)): strict 76 g needs both-open overlap <= %.3f s; the 2.55 s cap gives 76.05 g; Cd ASSUMED' % (
        pb['mdot_g_s'], pb['cap_overlap_s']),
        'lead: set 2.548 s (or accept 76.05 g as 76 g) until CF-4 / B-BLEED-1, then the measured-time form overlap <= 76 g / mdot_measured - (t_close - t_open)',
        'Lead; Electronics; founders')
    upd('OI-49', 'A1 apogee target 210 m DECIDED (214, 227 (1)): no 210 m A1 record in the hub (gnc.json v3.2); A1 values are 300 m / 285 m comparators; the duty '
                 'cycle does not shorten (227 (9): burn p99 %s / %s s); the warm-end relight state rises (purge +0.66 g per K above 289.5 K)' % (b210[0], b210[1]),
        'GNC publishes the 210 m record (gnc.json v3.2); Combustion re-runs the A1 grain run (first-order values in tank_2p20kg_option_v2p4b), Table 7.3b, '
        'the purge records at the warm-end state and FA-1 at the relight state; Mechanical the relight wall temperatures; no new sizing case (LEAD)')
    new_oi = [
        dict(id='OI-50', item=TK['open_item']['text'], action='GNC flies B1 and A1 with the 2.20 kg tank; Combustion re-runs S230 grain, erosion and thermal; '
             'Mechanical checks the tank and structure; the datasheet quotes 2.20 kg as an option with B1 / thermal / erosion TO-VERIFY', owner='; '.join(TK['open_item']['owners'])),
        dict(id='OI-51', item='FEA3D share vector: the full signed modal shares c_i (60 modes) of the principal (and tensor) stress functional at every assessed '
             'node, and the tensor 0.1-1 ms absolute sum; %d of 60 are published at TC-01 J-FWD, so the per-mode Peq is an interval' % n_known_j,
             action='FEA3D publishes the vector from modal_v351ca2b_c71 (fa1_band_sensitivity.py already forms it); Combustion re-runs fa1_per_mode_peq / '
                    'fa1_modal_th_bound (minutes) and the interval collapses to a number', owner='FEA3D (Mechanical); Combustion'),
        dict(id='OI-52', item='structural damping of the engine assembly: zeta 0.02 is an ASSUMED design value (bolted joints), 0.05 a sensitivity; no modal test; '
             'the 0.1-1 ms values fall from %.1f (zeta 0) to %.1f (0.02) and %.1f (0.05) bar abs' % (hA['T_0p1_to_1ms'][0][0], hA['T_0p1_to_1ms'][0.02][0],
                                                                                                     hA['T_0p1_to_1ms'][0.05][0]),
             action='founders: impact (tap) test of the assembled engine on its mount, damping of the modes in 1-5 kHz; Mechanical states the damping basis; '
                    'until then zeta 0 is the bound', owner='founders (test); Mechanical; Combustion (re-run)')]
    iu = ids.index('updates')
    OI[iu:iu] = new_oi
    OI[-1]['items']['OI-41 (final fold)'] = 'restatement / per-mode rule proposed (final_fold_v2p4b)'
    for k, f in (('02-combustion/CF-4-SPEC.md', CJ['specs_v2p4b']['v']), ('02-combustion/CF-4-SPEC.md', CJ['files']['v2p4b']['v']['specs'])):
        f[k]['sha256_16_superseded'] = f[k]['sha256_16']; f[k]['sha256_16'] = cf_sha
    CJ['cf4_gate']['spec_version_staged_superseded'] = CJ['cf4_gate']['spec_version']
    CJ['cf4_gate']['spec_version'] = 'CF-4-SPEC v2.1 (v2.4b final fold, %s)' % cf_sha
    CJ['files']['v2p4b']['v']['datasheet_inputs'] = '02-combustion/DATASHEET-INPUTS-COMBUSTION.md (%s)' % ds_sha
    CJ['files']['v2p4b']['v']['final_fold_builder'] = '02-combustion/src/build_final_fold_v2p4b.py'
    SUP = CJ['superseded_v2p4b']['v']
    SUP.update({
        'purge flow basis "neither 29.8 nor 32.0 g/s x t" (203 (3))': 'ONE basis 29.25 g/s (216 (5)); purge_basis_line216_v2p4b',
        'A1 apogee target about 210 m (213)': '210 m DECIDED (214, 227 (1))',
        '"the A1 duty cycle shortens" (213)': 'not supported (227 (9), RV6-05); a1_apogee_target_v2p4b A1-1',
        'FA-1 band values 90 / 93 / 102 bar abs (194 (1)) as Combustion\'s reading': 'below the published all-case spectrum (OI-41); restatement or '
                                                                                    'per-mode rule proposed (fa1_spectra_damped_v2p4b.v.proposal)',
        'CF-4 v2.1 %s (staged)' % EXPECT_STAGED['CF-4-SPEC.md']: 'CF-4 v2.1 %s (final fold: P5 basis, A1 210 m decided)' % cf_sha})
    CJ['final_fold_v2p4b'] = dict(v=dict(
        date='2026-10-19', changelog_lines_sha256_16=lh, changelog_at_build=dict(lines=open(chlog_f, 'rb').read().count(b'\n'), sha256_16=sha(chlog_f)),
        requests_2026_10_19={'1 FA-1 spectra as data': 'fa1_spectra_damped_v2p4b; REPORT §16.2-16.3',
                             '2 TC-01 per-mode Peq': 'fa1_per_mode_peq_v2p4b; REPORT §16.4', '3 GNC P4c lit side, pcf_tmax': 'p4c_lit_side_v2p4b; REPORT §16.7',
                             '4 2.20 kg tank': 'tank_2p20kg_option_v2p4b; OI-50; REPORT §16.8', '5 datasheet inputs': 'datasheet_inputs_v2p4b; REPORT §16.9'},
        relays_line216={'(5)': 'purge_basis_line216_v2p4b', '(9)': 'start_level_lift_v2p4b.v.line216_9'},
        new_open_items=['OI-50', 'OI-51', 'OI-52'], data_files={f: H(f) for f in NEW_DATA}),
        tag='index; ' + tags_std, src='REPORT v2.4b §16')
    cj_out = os.path.join(out, 'combustion.json')
    json.dump(CJ, open(cj_out, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    # every staged key is kept; values replaced only where a *_superseded key keeps the old one
    CJ0 = json.load(open(os.path.join(staged, 'combustion.json')))
    def leaves(o, p=''):
        if isinstance(o, dict):
            for k, v in o.items():
                yield from leaves(v, p + '/' + k)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                yield from leaves(v, p + '[%d]' % i)
        else:
            yield p
    L0, L1 = set(leaves(CJ0)), set(leaves(json.load(open(cj_out))))
    lost = [p for p in L0 if p not in L1]
    lost = [p for p in lost if not re.search(r'/open_items_v2p4b/v\[9\]', p)]          # the 'updates' entry moved from index 9 to 12
    assert not lost, lost[:5]
    cj_sha = sha(cj_out)

    # ------------------------------------------------------------------ REPORT
    R = open(os.path.join(staged, 'REPORT.md'), encoding='utf-8').read()
    R = rep(R, 'Version 2.4b, 2026-10-13. Owner', 'Version 2.4b, 2026-10-19 (staged 2026-10-13; final fold of LEAD lines 214-228 and the lead requests of '
            '2026-10-19 in §16). Owner')
    R = rep(R, '`interfaces/combustion.json` v2.4b (sha256/16 `593dc296b155cd8e`)', '`interfaces/combustion.json` v2.4b (sha256/16 `%s`)' % cj_sha)
    R = rep(R, '| `interfaces/combustion.json` v2.4b (`593dc296b155cd8e`) |', '| `interfaces/combustion.json` v2.4b (`593dc296b155cd8e` as built; `%s` after '
            '`build_final_fold_v2p4b.py`, §16.11) |' % cj_sha)
    R = rep(R, '`CF-4-SPEC.md` v2.1 (`86cd01e34c28aa82`) | §10 |', '`CF-4-SPEC.md` v2.1 (`86cd01e34c28aa82` as built; `%s` after `build_final_fold_v2p4b.py`, '
            '§16.11) | §10 |' % cf_sha)
    R = rep(R, '`02-combustion/CF-4-SPEC.md` v2.1 (`86cd01e34c28aa82`)', '`02-combustion/CF-4-SPEC.md` v2.1 (`%s`)' % cf_sha)
    R = rep(R, '- **CF-4 v2.1 (`86cd01e34c28aa82`):**', '- **CF-4 v2.1 (`%s`):**' % cf_sha)
    assert R.count('86cd01e34c28aa82') == 1
    R = rep(R, 'and the founder decision of line 213 (A1 apogee target about 210 m). v2.4a',
            'the founder decision of line 213 and the lead lines 214-228 (A1 apogee target 210 m, DECIDED by lines 214 and 227 (1)). v2.4a')
    R = rep(R, '14. **A1 apogee target about 210 m (LEAD line 213, founder decision; §15.15).**',
            '14. **A1 apogee target 210 m (LEAD line 213, founder decision; DECIDED by lines 214 and 227 (1); §15.15, §16.8).**')
    R = rep(R, 'the A1 duty cycle is shorter;', 'the A1 duty cycle does not shorten (corrected by line 227 (9), RV6-05: GNC rev4 burn p99 %s / %s s at 210 m against '
            '%s / %s s at 285 m; §16.8);' % b210)
    j1, j2 = hA['T_le_0p1ms'][0], hA['T_0p1_to_1ms'][0]
    item15 = [
        '15. **v2.4b final fold (LEAD lines 214-228; lead requests of 2026-10-19; §16).**',
        '    - **FA-1 spectra as data (§16.2).** Head and aft S(T), T %.2f-%.0f ms, zeta 0 / 0.02 / 0.05, baseline and all cases, in '
        '`fa1_pressure_spectra_published_v2p4b.csv`; thrust spectra to 200 ms as before. Plainly: the line-194 (1) band values are below the published all-case '
        'head spectrum: %.1f bar abs at T <= 0.1 ms against 90, %.1f at 0.1-1 ms (zeta 0; %.1f at zeta 0.02) against 93 / 102 (OI-41).' % (
            min(DS['periods_ms']['dense']), max(DS['periods_ms']['dense']), j1[0], j2[0], hA['T_0p1_to_1ms'][0.02][0]),
        '    - **Proposal for line 194 (1) (§16.3).** Restated band values %d / %d / %d / %d bar abs (T <= 0.1 / 0.1-1 / 1-20 / 20-50 ms; undamped all-case maxima '
        'rounded up; FA1S 151.04 bounds all), or a per-mode rule for paths with published shares: the time-domain modal bound, with the E rule as its '
        'conservative form until FEA3D publishes the share vector (OI-51). At TC-01 J-FWD (a 0.1-1 ms path) the restated %d bar abs gives MS %+.3f yield / '
        '%+.3f ultimate; the time-domain bound gives %+.3f / %+.3f (§16.3).' % (
            prop['T_le_0p1ms'], prop['T_0p1_to_1ms'], prop['T_1_to_20ms'], prop['T_20_to_50ms'], prop['T_0p1_to_1ms'], CONS['band_a']['MS_yield'],
            CONS['band_a']['MS_ult'], CONS['rule_b_time_domain_bound']['MS_yield'], CONS['rule_b_time_domain_bound']['MS_ult']),
        '    - **TC-01 per-mode equivalent pressure (line 228 (c); §16.4).** J-FWD, all-case head spectrum, worst factor of x0.85 / 0.90 / 1.00: signed sum '
        '%s, absolute sum %s, SRSS %s bar abs (zeta 0; intervals: %d of 60 shares published); time-domain bound %.1f (zeta 0), %.1f (zeta 0.02 ASSUMED); E rule %.1f; '
        'break-even %.1f yield / %.1f ultimate. The signed sum and the time-domain bound are %s the yield break-even (the bound by %.1f bar, with the residual '
        'at its published signed share); the absolute sum and the E rule are not; SRSS does not apply to this coherent load.' % (
            iv(sg0), iv(ab0), iv(sr0), n_known_j, th0[0], th2[0], er0[0], Pby, Pbu,
            'below' if (sg0[1] < Pby and th0[0] < Pby) else 'NOT both below', Pby - th0[0]),
        '    - **Purge basis and start-level lift (line 216 (5), (9); §16.5-16.6).** ONE basis %.2f g/s (76 g / %.3f s of flow at 289.5 K; %.2f-%.2f g/s over the '
        'relight states); start-level lift %.5f mm at the A1 relight state (DESIGN, ECU table; model %+.3f %%).' % (
            pb['mdot_g_s'], pb['t76_flow_s'], ts['283.15K']['mdot_eq_g_s'], ts['297.15K']['mdot_eq_g_s'], sl['value_mm'], -0.056),
        '    - **GNC P4c (§16.7).** Lit thrust at %.5f mm: minimum %.2f N in both windows; %d of 72 corners never reach 37.16 N, the others by E2 + %.3f s '
        '(+ 3 frames %.3f s); pcf_tmax 0.8 s is not limited by the lit side.' % (sl['value_mm'], w8['F_min_over_corners_N'], w8['thresholds']['37.16 N']['n_corners_never'],
                                                                                 w8['thresholds']['37.16 N']['latest_first_crossing_after_E2_s'], w8['thresholds']['37.16 N']['latest_plus_3_frames_s']),
        '    - **A1 at 210 m and the 2.20 kg option (lines 214, 219, 227; §16.8).** The A1 duty cycle does not shorten (RV6-05): first order, nominal A1 '
        'throat-area growth %.2f %% per flight with 2.00 kg; with 2.20 kg %.2f-%.2f %% (above the NZ-01 2 %% criterion at the p99 and max burns), web >= %.2f mm; '
        'B1 / thermal / erosion with 2.20 kg TO-VERIFY (OI-50).' % (ca['erosion_nominal_dAt_pct'], t871['erosion_nominal_dAt_pct'][0], t924['erosion_nominal_dAt_pct'][1],
                                                                     t924['web_end_min_band_a1p5_n0p35_mm']),
        '    - **Datasheet inputs (§16.9)** in `DATASHEET-INPUTS-COMBUSTION.md` (`%s`). New open items OI-50 to OI-52 (§16.10).' % ds_sha]
    L = R.split('\n'); i14 = line_with(R, '14. **A1 apogee target 210 m')
    assert L[i14 + 1] == '', 'item 14 is one line'
    R = '\n'.join(L[:i14 + 1] + item15 + L[i14 + 1:])
    R = rep(R, '**Configuration.** v2.4b: lead decisions to CHANGELOG line 213 (lines 186', '**Configuration.** v2.4b: lead decisions to CHANGELOG line 228 (lines '
            '214-228 folded in §16; lines 186')
    R = rep(R, 'A1 apogee target: about 210 m (line 213, founder decision; GNC sets the exact band in gnc.json v3.2).',
            'A1 apogee target: 210 m (line 213, founder decision; DECIDED by lines 214 and 227 (1); gnc.json v3.2 carries the band and the record). Final fold '
            '(2026-10-19): CHANGELOG read to line 228 (`%s` at %d lines); FEA3D `modal_modal_v351ca2b_c71.json` (`9af80c657eed11ac`) and `fa1_band_sensitivity.json` '
            '(`794155b97167a784`); GNC rev4 staged `v32_proposals_rev4.json` (`6fd6d66e08aef5d8`; SIM, not gnc.json); the interfaces read are those listed next, unchanged since the staged build (§16.1).' % (
                sha(chlog_f), open(chlog_f, 'rb').read().count(b'\n')))
    R = rep(R, '(see OI-40: erosion alone can exceed 2 % per A1 flight).', '(see OI-40: erosion alone can exceed 2 %% per A1 flight; first order, the nominal model '
            'gives %.2f %% per flight at 210 m with 2.00 kg and %.2f-%.2f %% with the 2.20 kg option, §16.8).' % (
                ca['erosion_nominal_dAt_pct'], t871['erosion_nominal_dAt_pct'][0], t924['erosion_nominal_dAt_pct'][1]))
    R = append_to_line(R, '**Files.** Hub', ' The final fold adds `DATASHEET-INPUTS-COMBUSTION.md` and nine data files in `data/v2p4b/` (§16.11).')
    R = append_to_line(R, '**Tests (digital).**', ' Final fold: the damped spectra reproduce the undamped exact maxima at the modal periods (exact minus sampled %.3f to %.3f bar); '
                       'the time-domain modal bound returns the static value of a 50 ms ramp to 80 bar within %.2f %% (the ramp-corner overshoot of the modes) and its exact '
                       '|q - g| maxima exceed a 64-point sampling by %.5f to %.5f bar; '
                       'every number of §16 is read from the data files by `build_final_fold_v2p4b.py`.' % (
                           cm['min'], cm['max'], 100 * TH['checks']['static_limit_rel_error'], TH['checks']['e_bound_vs_sampled_64']['min_exact_minus_sampled64_bar'],
                           TH['checks']['e_bound_vs_sampled_64']['max_exact_minus_sampled64_bar']))
    R = append_to_line(R, '**Unknowns** (§11).', ' v2.4b final fold: the structural damping of the engine assembly (no modal test; OI-52); FEA3D\'s full modal share '
                       'vector (OI-51); the B1 duty cycle with the 2.20 kg tank (OI-50).')
    R = rep(R, 'Lead: OI-41 (which FA-1 case group governs each period domain; the flight Pc proof follows), OI-42 (accept 76.05 g at the 2.55 s cap or set 2.54 s).',
            'Lead: OI-41 (restate the line-194 (1) band values or adopt the per-mode rule, §16.3; the flight Pc proof follows), OI-42 (the cap on the ONE basis '
            '%.2f g/s: %.3f s strict, then the measured-time form after CF-4, §16.5). FEA3D (Mechanical): the full modal share vector at the assessed nodes (OI-51). '
            'Founders: an impact (tap) test for the assembly damping (OI-52).' % (pb['mdot_g_s'], pb['cap_overlap_s']))
    R = rep(R, '; the 210 m A1 record (gnc.json v3.2; OI-49), after which Combustion re-runs its A1 items (§15.15).',
            '; the 210 m A1 record (gnc.json v3.2; OI-49), after which Combustion re-runs its A1 items (§15.15); B1 and A1 records with the 2.20 kg tank if the '
            'option is pursued (OI-50).')
    R = insert_after_line(R, '- §15 v2.4b: lead lines 186, 194, 203-205 and 213', [
        '- §16 v2.4b final fold: lead lines 214-228 and the requests of 2026-10-19 (16.1 lines folded; 16.2 FA-1 spectra as data; 16.3 proposal for line 194 (1); '
        '16.4 TC-01 per-mode equivalent pressure; 16.5 purge flow basis; 16.6 start-level lift; 16.7 GNC P4c; 16.8 A1 at 210 m and the 2.20 kg option; '
        '16.9 datasheet inputs; 16.10 open items; 16.11 files, reproduction and failures)'])
    R = rep(R, '[v2.4b: LEAD line 213 lowered the A1 target to about 210 m; the 285 m and 300 m values stay as comparators (§15.15).]',
            '[v2.4b: LEAD line 213 lowered the A1 target to 210 m, DECIDED by lines 214 and 227 (1); the 285 m and 300 m values stay as comparators (§15.15, §16.8).]')
    R = rep(R, 'comparators; the about-210 m A1 duty cycle is shorter (LEAD) and its values are MISSING (§15.15).]',
            'comparators. The 210 m A1 duty cycle is not shorter (line 227 (9), RV6-05): burn p99 %s s, %+.1f %% against the 8.258 s counter; first order, the nominal '
            'A1 rows rise by up to %.1f %% (%.2f %% per flight at n 0.5) (§16.8).]' % (b210[0], (ca['time_ratio'] - 1) * 100, (ca['time_ratio'] - 1) * 100,
                                                                                     ca['erosion_nominal_dAt_pct']))
    R = rep(R, 'the about-210 m A1 duty cycle is shorter (LEAD) and its values are MISSING until the 210 m record; one insert per flight stays (§15.15).]',
            'the 210 m A1 duty cycle is not shorter (line 227 (9), RV6-05: burn p99 up to %.1f %% longer, so on the first-order time ratio the A1 flight counts '
            'fall by up to about %.0f %%); one insert per flight stays (§15.15, §16.8).]' % ((ca['time_ratio'] - 1) * 100, math.ceil((1 - 1 / ca['time_ratio']) * 100)))
    # §12 rows
    oi41 = line_with(R, '| OI-41 |'); oi42 = line_with(R, '| OI-42 |'); oi49 = line_with(R, '| OI-49 |')
    L = R.split('\n')
    L[oi41] = ('| OI-41 | FA-1 period-domain values (v2.4b; final fold) | The published all-case head spectrum is above the line-194 (1) values below 1 ms: %.1f > 90 bar abs '
               '(T <= 0.1 ms); 0.1-1 ms %.1f (zeta 0), %.1f (zeta 0.02), %.1f (zeta 0.05) against 93 / 102; baseline %.1f / %.1f (zeta 0). Proposed (§16.3): restated band '
               'values %d / %d / %d / %d bar abs, or the per-mode rule for paths with published shares (E rule until OI-51) | Lead; Mechanical |' % (
                   hA['T_le_0p1ms'][0][0], hA['T_0p1_to_1ms'][0][0], hA['T_0p1_to_1ms'][0.02][0], hA['T_0p1_to_1ms'][0.05][0], hB['T_le_0p1ms'][0][0],
                   hB['T_0p1_to_1ms'][0][0], prop['T_le_0p1ms'], prop['T_0p1_to_1ms'], prop['T_1_to_20ms'], prop['T_20_to_50ms']))
    L[oi42] = ('| OI-42 | Purge cap and the 76 g allowance (v2.4b; final fold) | ONE flow basis %.2f g/s (line 216 (5); §16.5): strict 76 g needs both-open overlap '
               '<= %.3f s; the 2.55 s cap gives 76.05 g; Cd ASSUMED. Set 2.548 s (or accept 76.05 g as 76 g) until CF-4 / B-BLEED-1, then overlap <= 76 g / '
               'mdot_measured - (t_close - t_open). A warmer 210 m relight state adds about 0.66 g per K above 289.5 K (OI-49) | Lead; Electronics; founders |' % (
                   pb['mdot_g_s'], pb['cap_overlap_s']))
    L[oi49] = ('| OI-49 | A1 apogee target 210 m (lines 213, 214, 227; v2.4b) | DECIDED (214, 227 (1)). No 210 m A1 record in the hub (gnc.json v3.2); the A1 values '
               'are 300 m / 285 m comparators; the duty cycle does not shorten (227 (9): burn p99 %s / %s s; first-order values §16.8). The warm-end relight state rises: '
               'purge +0.66 g per K above 289.5 K, cold-flow bound +0.13 N per K. GNC publishes the 210 m record; Combustion re-runs the A1 grain run, Table 7.3b, '
               'the purge records at the warm-end state and FA-1 at the relight state; Mechanical the relight wall temperatures; no new sizing case (LEAD) | GNC; '
               'Combustion; Mechanical |' % (b210[0], b210[1]))
    L[oi49 + 1:oi49 + 1] = [
        '| OI-50 | 2.20 kg tank option (lines 219, 227 (9); final fold) | First-order A1 only (§16.8): nominal throat-area growth %.2f-%.2f %% per flight, web >= %.2f mm. '
        'Not covered: B1 with 2.20 kg, the 210 m relight state, the wall-temperature rise of a longer burn, the tank structure. GNC flies B1 and A1 with 2.20 kg; '
        'Combustion re-runs grain, erosion and thermal; the datasheet quotes the option with "B1 / thermal / erosion TO-VERIFY" | GNC; Combustion; Mechanical |' % (
            t871['erosion_nominal_dAt_pct'][0], t924['erosion_nominal_dAt_pct'][1], t924['web_end_min_band_a1p5_n0p35_mm']),
        '| OI-51 | FEA3D modal share vector (line 228 (c); final fold) | %d of 60 signed shares are published at TC-01 J-FWD (the rest as bin sums), so the per-mode '
        'Peq is an interval (§16.4). FEA3D publishes the 60-mode signed vector of the principal and tensor functionals at every assessed node (and the tensor '
        '0.1-1 ms absolute sum); Combustion re-runs the two scripts (minutes) | FEA3D (Mechanical); Combustion |' % n_known_j,
        '| OI-52 | Assembly damping (final fold) | zeta 0.02 is ASSUMED (bolted joints), 0.05 a sensitivity; no modal test. Impact (tap) test of the engine on its mount '
        'for the modes in 1-5 kHz; until then zeta 0 is the bound | Founders (test); Mechanical; Combustion |']
    R = '\n'.join(L)
    # §13 and §15 rows
    R = insert_after_line(R, '| A1 apogee target 285 m (trim) / 300 m (lead default) as the A1 basis |', [
        '| "The A1 duty cycle shortens" (LEAD line 213; §0 item 14, §15.13, §15.15 A1-1, Tables 5.3 note, life statement; staged v2.4b) | LEAD line 227 (9) (RV6-05): '
        'not supported (burn p99 %s / %s s at 210 m) | corrected in place; first-order values §16.8 |' % (b210[0], b210[1]),
        '| Purge flow basis "neither 29.8 nor 32.0 g/s x t" (§15.9; staged v2.4b) | ONE basis %.2f g/s (LEAD 216 (5)) | §16.5; the §15.9 text stays as the derivation |' % pb['mdot_g_s'],
        '| FA-1 band values 90 / 93 / 102 bar abs (LEAD 194 (1)) read as covering the all-case spectrum | below the published all-case head spectrum (OI-41) | '
        'restatement or per-mode rule proposed (§16.3) |'])
    R = insert_after_line(R, '| 213 (founder) | A1 apogee target about 210 m;', ['| 214-228 | A1 210 m decided; purge basis; start-level lift; FA-1 per mode; 2.20 kg option; '
                                                                               'RV6-05 correction | §16.1 |'])
    R = rep(R, 'LEAD line 213 (v2.4b): the A1 target is about 210 m. 8.258 s (the 300 m A1 sizing record, apex 302.4 m) and 8.375 s (the 285 m F11 record) are '
            'comparators. The 210 m duty cycle is shorter (LEAD), so (a) and (c) hold on it;',
            'LEAD lines 213, 214 and 227 (1) (v2.4b): the A1 target is 210 m. 8.258 s (the 300 m A1 sizing record, apex 302.4 m) and 8.375 s (the 285 m F11 record) '
            'are comparators. The 210 m duty cycle is not shorter (line 227 (9), RV6-05: burn p99 %s / %s s); on the first-order time ratio (§16.8) (a) and (c) still '
            'hold (web >= %.2f mm at the band corner; B1 governs the thermal sizing);' % (b210[0], b210[1], ca['web_end_min_band_a1p5_n0p35_mm']))
    R = insert_after_line(R, '- Consequences: ECU: hold lift = h_s(T_tank at E0)', [
        '- LEAD line 216 (9) (final fold): confirmed as a LIFT value at the A1 relight state: %.5f mm at 286.70 K, 43.53 bar (the ECU kIgnLiftTab_m row, DESIGN; '
        'Combustion injector model 0.21788 mm, -0.056 %%, DERIVED); 0.2039 mm at 20 C; TO-VERIFY at CF-3 (encoder lift, mdot, load cell) (§16.6).' % sl['value_mm']])
    R = rep(R, '### 15.9 Purge flow basis and the ECU cap (line 203 (3); relay item 1)\n\nNeither constant rate is right.',
            '### 15.9 Purge flow basis and the ECU cap (line 203 (3); relay item 1)\n\n[Final fold, LEAD 216 (5): ONE basis, %.2f g/s, is stated in §16.5; the text '
            'below is the 203 (3) derivation it rests on.] Neither constant rate is right.' % pb['mdot_g_s'])
    R = rep(R, 'the lead carries it into ICD-AIRFRAME v2.1.', 'the lead had planned to carry it into ICD-AIRFRAME v2.1, which line 222 removed from the finish '
            'scope; the spectrum stays published here (Table 7.6d, `fa1_thrust_spectra_dense_v2p4b.csv`) as engine data for the mounting (FEA3D line 226).')
    R = rep(R, '### 15.15 A1 apogee target about 210 m (line 213)', '### 15.15 A1 apogee target 210 m (line 213; DECIDED by lines 214 and 227 (1))')
    R = rep(R, 'The lead states that the A1 duty cycle shortens, that B1 still governs thermal and erosion sizing, and that no new sizing case is needed. No 210 m A1 '
            'record exists yet, so this section computes no 210 m value.',
            'The lead stated that the A1 duty cycle shortens, that B1 still governs thermal and erosion sizing, and that no new sizing case is needed; line 227 (9) '
            'corrects the first (RV6-05: burn p99 %s / %s s at 210 m against %s / %s s at 285 m); line 214 decides the 210 m target and 227 (1) accepts it. No 210 m '
            'A1 record is in the hub yet (gnc.json v3.2), so this section computes no 210 m value beyond the first-order duty-cycle scaling of §16.8.' % b210)
    R = rep(R, '| ID | Topic | Basis (300 m / 285 m) | Direction at about 210 m | Status |', '| ID | Topic | Basis (300 m / 285 m) | Direction at 210 m | Status |')
    R = rep(R, '| shorter A1 duty cycle (LEAD line 213), so less erosion and heat per A1 flight; B1 still governs thermal and erosion sizing (LEAD); no new sizing case |',
            '| NOT shorter (line 227 (9), RV6-05; corrects line 213): burn p99 %s / %s s at 210 m against %s / %s s at 285 m and the 8.258 s counter (%+.1f %% at most); '
            'first order, nominal A1 throat-area growth %.2f %% per flight at n 0.5 (%.2f %% at n 0.68), web >= %.2f / %.2f mm (§16.8); B1 still governs thermal and '
            'erosion sizing (LEAD); no new sizing case |' % (b210 + ((ca['time_ratio'] - 1) * 100, ca['erosion_nominal_dAt_pct'], ca['erosion_nominal_n068_dAt_pct'],
                                                         ca['web_end_a1p0_n0p5_mm'], ca['web_end_min_band_a1p5_n0p35_mm'])))
    R = rep(R, 'The all-case values exceed the line-194 (1) numbers below 1 ms (OI-41, for the lead); FA1S (about 151 bar abs) bounds every period.',
            'The all-case values exceed the line-194 (1) numbers below 1 ms (OI-41); the damped spectra, a per-mode rule and restated band values are proposed in '
            '§16.2-16.4; FA1S (151.04 bar abs) bounds every period.')
    R = rep(R, 'and 76.05 g at 2.60 s of flow (the 2.55 s both-open cap), at the 76 g limit (OI-42). The firmware',
            'and 76.05 g at 2.60 s of flow (the 2.55 s both-open cap), at the 76 g limit (OI-42); line 216 (5): ONE basis %.2f g/s (§16.5). The firmware' % pb['mdot_g_s'])
    R = R.rstrip('\n') + '\n\n' + section16(locals()) + '\n'
    rep_out = os.path.join(out, 'REPORT.md')
    open(rep_out, 'w', encoding='utf-8').write(R)
    assert 'Version 2.4b, 2026-10-19' in R.split('\n')[2]
    assert 'the lead carries it into ICD-AIRFRAME' not in R and 'ICD-AIRFRAME' not in cf      # line 222: stale references restated
    print('wrote', cf_out, cf_sha, '|', cj_out, cj_sha, 'keys %d -> %d' % (n_keys0, len(CJ)), '|', rep_out, sha(rep_out), 'lines', R.count('\n'))


def section16(V):
    g = V.get
    hA, hB, aA, aB, BANDS, prop, DS = g('hA'), g('hB'), g('aA'), g('aB'), g('BANDS'), g('prop'), g('DS')
    jt, lt, jtb, TH, PM = g('jt'), g('lt'), g('jtb'), g('TH'), g('PM')
    Pby, Pbu, n_known_j, n_unpub_j, r_j = g('Pby'), g('Pbu'), g('n_known_j'), g('n_unpub_j'), g('r_j')
    pb, ts, cdv, PB, sl, w5, w8, w8b, lit, lit2, fo, P4 = (g(k) for k in ('pb', 'ts', 'cdv', 'PB', 'sl', 'w5', 'w8', 'w8b', 'lit', 'lit2', 'fo', 'P4'))
    TK, ca, cb, t871, t892, t924, b210 = (g(k) for k in ('TK', 'ca', 'cb', 't871', 't892', 't924', 'b210'))
    H, lh, ds_sha, cf_sha, cj_sha, other, cq, resk = (g(k) for k in ('H', 'lh', 'ds_sha', 'cf_sha', 'cj_sha', 'other', 'cq', 'resk'))
    bm, pg_all, pg_base, cm, chk = g('bm'), g('pg_all'), g('pg_base'), g('cm'), g('chk')
    sg0, ab0, sr0, sg2, ab2, sr2, lsg0, lab0, lsr0 = (g(k) for k in ('sg0', 'ab0', 'sr0', 'sg2', 'ab2', 'sr2', 'lsg0', 'lab0', 'lsr0'))
    th0, th2, th5, er0, er2, er5, kc0, lth0, lth2, ler0 = (g(k) for k in ('th0', 'th2', 'th5', 'er0', 'er2', 'er5', 'kc0', 'lth0', 'lth2', 'ler0'))
    verdict, ms = g('verdict'), g('ms')
    CONS, T2223, c22, c23 = g('CONS'), g('T2223'), g('c22'), g('c23')
    VP = {'below': 'is below', 'above': 'is above', 'straddles': 'straddles'}
    def cmp2(x, a, b):
        return 'above both' if x > max(a, b) else ('below both' if x < min(a, b) else 'between them')
    o = []
    A = o.append
    A('## 16. v2.4b final fold: lead lines 214-228 and the requests of 2026-10-19')
    A('')
    A('This section folds the lead lines 214-228 and answers the lead requests of 2026-10-19 (items 1-5) and the line-216 relays (5) and (9). The '
      'interface keys are listed in each subsection; every number is read from the v2.4b data files at build time by `src/build_final_fold_v2p4b.py`. '
      'Tags: SIM, DERIVED, ASSUMED, DESIGN, LEAD, TO-VERIFY, MISSING. Digital only; nothing here is physical approval.')
    A('')
    A('### 16.1 Lines folded and configuration')
    A('')
    A('| Line | Content (read) | Fold | Where |')
    A('|---|---|---|---|')
    rows = [
        ('214', 'A1 apogee target = 210 m (lead decision on the GNC rev4 line-208 band)', 'A1 values stay 300 m / 285 m comparators until the 210 m record', '§15.15, §16.8; `a1_apogee_target_v2p4b`; CF-4 §4'),
        ('215', 'REV-ELEC-2 result (Electronics v2.10)', 'read; no Combustion change', '-'),
        ('216 (5)', 'one purge flow basis in g/s with derivation and uncertainty', '%.2f g/s' % pb['mdot_g_s'], '§16.5; `purge_basis_line216_v2p4b`; CF-4 P5'),
        ('216 (9)', 'the start-level lift as a LIFT value at the A1 relight state', '%.5f mm' % sl['value_mm'], '§15.3, §16.6; `start_level_lift_v2p4b.v.line216_9`'),
        ('216 (other)', 'Electronics v2.11 deltas', 'read; THE start-level lift stays the hold lift (OI-43)', '-'),
        ('217, 220, 224, 226', 'FEA3D F1-F4 results and the final republish', 'read for status', '-'),
        ('218', 'GNC rev4 staged (v32_proposals_rev4 `6fd6d66e08aef5d8`)', 'item [15] T/W used for the 2.20 kg thrust factor', '§16.8'),
        ('219', 'tank stays 2.00 kg (founder); 2.20 kg characterised as an option', 'first-order A1 estimate; OI-50', '§16.8; `tank_2p20kg_option_v2p4b`'),
        ('221, 225', 'FEA3D modal periods, band shares and FA-1 columns', 'shares used as published (%d of 60 at J-FWD)' % n_known_j, '§16.4; OI-51'),
        ('222', 'ICD-AIRFRAME removed from the finish scope', 'the two v2.4b references restated (thrust spectrum = engine data for the mounting)', '§7.6; `fa1_spectra_v2p4b.v.thrust.rule`'),
        ('223', 'TC-01 J-FWD a 0.1-1 ms path, PROVISIONAL, conditions (a), (b)', 'Combustion side of (a): spectra at the scaled FE periods', '§16.2, §16.4'),
        ('227 (1), (5), (8)', '210 m accepted; R2 starve window 0.8 s; RV6-03 gate-delay arm', 'P4c windows 0.5 / 0.8 s; gate delay is a GNC item', '§16.7'),
        ('227 (9)', '"A1 duty cycle shortens" corrected (RV6-05); 2.20 kg B1 / thermal / erosion TO-VERIFY', 'corrected in place; first-order values', '§0 item 14, §5.3, §15.13, §15.15, §16.8'),
        ('228', 'third condition on TC-01: per-mode Peq from the published head spectrum', 'spectra published; Peq computed as intervals and bounds', '§16.2-16.4')]
    for r in rows:
        A('| %s |' % ' | '.join(r))
    A('')
    A('CHANGELOG line hashes (sha256/16 of the line text): ' + '; '.join('%s `%s`' % (k, v) for k, v in lh.items()) + '.')
    A('')
    # ---- 16.2
    A('### 16.2 FA-1 spectra as data (request item 1; line 228)')
    A('')
    A('S(T) is the equivalent static pressure, bar abs: p_amb + the maximum over time of the SDOF response (static gain 1, from rest) to the gauge history; '
      'published envelope = max(b clipped, c unclipped), as in §7.6. Undamped values are exact continuous maxima; damped values (zeta 0.02, 0.05) use the '
      'closed-form response sampled at up to 64 points per 0.05 ms step, with the free decay after the record added analytically. Files (`data/v2p4b/`):')
    A('')
    A('- `fa1_pressure_spectra_published_v2p4b.csv` (`%s`): %d periods, T %.2f-%.0f ms (dense below 1 ms); columns `period_ms`, then head / aft x baseline / all x '
      'zeta 0 / 0.02 / 0.05.' % (H('fa1_pressure_spectra_published_v2p4b.csv'), len(DS['periods_ms']['dense']), min(DS['periods_ms']['dense']), max(DS['periods_ms']['dense'])))
    A('- `fa1_pressure_spectra_modal_periods_v2p4b.csv` (`%s`): S at the 60 FE mode periods x the factors 1.00 / 0.90 / 0.85 (T = 1 / (s f_FE)).' % H('fa1_pressure_spectra_modal_periods_v2p4b.csv'))
    A('- `fa1_spectra_damped_v2p4b.json` (`%s`): envelopes with the governing case per period, band maxima, checks.' % H('fa1_spectra_damped_v2p4b.json'))
    A('- Thrust spectra to 200 ms: `fa1_thrust_spectra_dense_v2p4b.csv` (`%s`, unchanged; Table 7.6d).' % H('fa1_thrust_spectra_dense_v2p4b.csv'))
    A('')
    A('Table 16.2a. Band maxima of S(T), bar abs (period of the maximum, ms). Groups: baseline (168 cases), all cases (896).')
    A('')
    A('| Band | Node / group | zeta 0 | zeta 0.02 | zeta 0.05 |')
    A('|---|---|---|---|---|')
    for b, lab in BANDS:
        for nm, D in (('head / all', hA), ('head / baseline', hB), ('aft / all', aA), ('aft / baseline', aB)):
            A('| %s | %s | %s |' % (lab, nm, ' | '.join('%.1f (%.3g)' % (D[b][z][0], D[b][z][1]) for z in (0.0, 0.02, 0.05))))
    A('')
    A('Residual band for the TC-01 rule (T <= T_min / s, T_min = 0.1949 ms), head, all cases: ' + '; '.join(
        's %.2f (T <= %.4f ms): %s' % (s, 0.194914 / s, ' / '.join('%.1f' % bm[resk[s]]['head|all|zeta%g' % z]['value_bar'] for z in (0.0, 0.02, 0.05)))
        for s in (1.00, 0.90, 0.85)) + ' bar abs (zeta 0 / 0.02 / 0.05). Peak head pressure: %.1f bar abs (all cases), %.1f (baseline).' % (pg_all + 1.01325, pg_base + 1.01325))
    A('')
    A('Checks: at the 180 modal periods the exact undamped maxima exceed the sampled ones by %.3f to %.3f bar (sampling shortfall, so the sampled damped '
      'values are low by about that much at most); on the dense grid %s.' % (cm['min'], cm['max'], ('%.3f to %.3f bar' % (chk['min'], chk['max'])) if chk else 'see the JSON'))
    A('')
    A('**The contradiction with line 194 (1), plainly.** Line 194 (1) sets 90 bar abs for T <= 0.1 ms and, for 0.1 < T <= 1 ms, 93 bar abs (FA1D, yield) and '
      '102 bar abs (FA1U, ultimate). The published all-case head spectrum is above both: %.1f bar abs at T <= 0.1 ms (T = %.3g ms), and %.1f bar abs at 0.1-1 ms '
      '(T = %.3g ms) undamped, %.1f at zeta 0.02 and %.1f at zeta 0.05. The baseline group alone (zeta 0) reads %.1f at T <= 0.1 ms, within 90, and %.1f at '
      '0.1-1 ms, %.1f bar above 93 and %.1f bar above 102. So the band values bound neither the all-case spectrum below 1 ms nor the baseline group in 0.1-1 ms '
      '(the ultimate column only marginally). A part whose modes sit near %.2f ms sees up to %.1f bar abs. '
      'Which case group governs is the lead\'s decision (OI-41); above 1 ms FA1S (151.04 bar abs) bounds the spectrum (%.1f at 1-20 ms, %.1f at 20-50 ms).' % (
          hA['T_le_0p1ms'][0][0], hA['T_le_0p1ms'][0][1], hA['T_0p1_to_1ms'][0][0], hA['T_0p1_to_1ms'][0][1], hA['T_0p1_to_1ms'][0.02][0], hA['T_0p1_to_1ms'][0.05][0],
          hB['T_le_0p1ms'][0][0], hB['T_0p1_to_1ms'][0][0], hB['T_0p1_to_1ms'][0][0] - 93, hB['T_0p1_to_1ms'][0][0] - 102,
          hA['T_0p1_to_1ms'][0][1], hA['T_0p1_to_1ms'][0][0], hA['T_1_to_20ms'][0][0], hA['T_20_to_50ms'][0][0]))
    assert hB['T_le_0p1ms'][0][0] <= 90 and 0 < hB['T_0p1_to_1ms'][0][0] - 102 < 1 and min(hA['T_le_0p1ms'][0][0] - 90, hA['T_0p1_to_1ms'][0][0] - 102) > 0
    A('')
    # ---- 16.3
    A('### 16.3 Proposal for line 194 (1): restated band values or a per-mode rule')
    A('')
    A('Two options for the lead (either closes OI-41; neither is a Combustion decision):')
    A('')
    A('(a) **Restated band values** (all-case head maxima, undamped, rounded up to the next bar; zeta 0 because no damping is measured, OI-52):')
    A('')
    A('| Band | Line 194 (1) | Proposed [bar abs] | Basis |')
    A('|---|---|---|---|')
    A('| T <= 0.1 ms | 90 | %d | %.1f, all cases, zeta 0 |' % (prop['T_le_0p1ms'], hA['T_le_0p1ms'][0][0]))
    A('| 0.1 < T <= 1 ms | 93 (FA1D yield) / 102 (FA1U ultimate) | %d (both columns) | %.1f, all cases, zeta 0; %d if zeta 0.02 is measured (%.1f) |' % (
        prop['T_0p1_to_1ms'], hA['T_0p1_to_1ms'][0][0], prop['T_0p1_to_1ms_z002'], hA['T_0p1_to_1ms'][0.02][0]))
    A('| 1 < T <= 20 ms | spectrum or FA1S | %d, or FA1S 151.04 | %.1f, all cases, zeta 0 |' % (prop['T_1_to_20ms'], hA['T_1_to_20ms'][0][0]))
    A('| 20 < T <= 50 ms | spectrum or FA1S | %d, or FA1S 151.04 | %.1f, all cases, zeta 0 |' % (prop['T_20_to_50ms'], hA['T_20_to_50ms'][0][0]))
    A('')
    A('(b) **Per-mode rule** for a load path whose modal shares are published (sum c_i + r = 1 on the static unit-pressure stress): Peq = p_amb + max over time of '
      '[g + sum_i c_i e_i + r e_res], e_i = q_i - g the dynamic increment of mode i (time-domain modal superposition, coherent). It is exact for a linear '
      'structure, gives p_amb + max g in the static limit, and needs the full signed share vector. Until FEA3D publishes it (OI-51) the published form is the '
      '**E rule**: Peq <= p_amb + max g + sum_i |c_i| E_i + |r| E_res, with E(T) = max |q - g| the relative spectrum (`fa1_relative_spectrum_E_v2p4b.csv`, '
      '`%s`); it is a rigorous upper bound and exact in the static limit. The spectral sums the lead named are not: the signed sum sum c_i S(T_i) puts every modal '
      'peak at the same instant with its sign (neither a bound nor an estimate of a coherent load); the absolute sum counts the static part sum |c_i| + |r| times '
      '(1.345 at J-FWD); SRSS returns about 0.55 of a static load and treats the closely spaced modes 22 / 23 as uncorrelated (CQC rho %.2f at zeta 0.02). They '
      'are reported in §16.4 as asked.' % (H('fa1_relative_spectrum_E_v2p4b.csv'), cq['rho']['zeta0.02']))
    A('')
    ca_, cz_, ct_, ce_ = (CONS[k] for k in ('band_a', 'band_a_if_zeta0p02_measured', 'rule_b_time_domain_bound', 'rule_b_E_rule'))
    A('**Consequence at TC-01 J-FWD** (a 0.1-1 ms path, line 223: its largest published shares, modes 22 and 23 (c = %.3f, %.3f), sit at T = %.2f-%.2f ms over '
      'the three factors; break-even %.2f yield / %.2f ultimate bar abs; MS = break-even / P - 1). Line 228 lists TC-01 at +0.25 / +0.23 on the line-194 (1) '
      'band reading (93 / 102 bar abs; %+.3f / %+.3f with these break-evens). Under (a) the band value %d bar abs gives MS %+.3f yield / '
      '%+.3f ultimate (%d bar abs if zeta 0.02 is measured: %+.3f / %+.3f). Under (b) the time-domain bound (zeta 0, worst factor s %.2f) %.1f bar abs gives '
      '%+.3f / %+.3f; its conservative E-rule form %.1f gives %+.3f / %+.3f. So with the restated band values J-FWD does not show the yield margin unless a '
      'damping of at least 0.02 is measured (and then only %+.3f); the per-mode bound shows it by %.1f bar, subject to the residual caveat of §16.4. DERIVED on '
      'SIM inputs; the choice is the lead\'s (OI-41); FEA3D\'s condition (a) and REV-MECH-2\'s check (b) of line 223 (3) stand.' % (
          c22, c23, T2223[0], T2223[1], Pby, Pbu, ms(93, Pby), ms(102, Pbu), ca_['P_bar_abs'], ca_['MS_yield'], ca_['MS_ult'], cz_['P_bar_abs'], cz_['MS_yield'], cz_['MS_ult'],
          ct_['s'], ct_['P_bar_abs'], ct_['MS_yield'], ct_['MS_ult'], ce_['P_bar_abs'], ce_['MS_yield'], ce_['MS_ult'], cz_['MS_yield'], Pby - ct_['P_bar_abs']))
    assert ca_['MS_yield'] < 0 < cz_['MS_yield'] and ct_['MS_yield'] > 0 and ce_['MS_yield'] < 0
    assert round(ms(93, Pby), 2) == 0.25 and round(ms(102, Pbu), 2) == 0.23
    A('')
    # ---- 16.4
    A('### 16.4 TC-01 per-mode equivalent pressure (request item 2; line 228 (c))')
    A('')
    A('Inputs: the all-case head spectrum (§16.2) at zeta 0 (the bound), 0.02 (Q = 25; ASSUMED design value at the low end of the range usually quoted for '
      'bolted metallic assemblies, recalled, TO-VERIFY; no modal test, OI-52) and 0.05 (Q = 10, sensitivity); FE periods scaled by 1 / s for s = 1.00, 0.90, '
      '0.85 (true f = s f_FE); the residual at the spectrum maximum for T <= 0.1949 / s ms; FEA3D shares (modal_v351ca2b_c71, `9af80c657eed11ac`; '
      'fa1_band_sensitivity.json, `794155b97167a784`; read only). At J-FWD FEA3D publishes %d signed shares (top 6, modes 11-13) and bin sums; the other %d are '
      'MISSING, so each sum is an interval over every distribution of the unpublished shares consistent with the bin sums (LP bounds, |c_j| capped at the '
      'smallest published |c|); residual share %.3f. Break-even (FEA3D columns, stress proportional to pressure, line 223 (2)): %.2f bar abs yield, %.2f bar abs '
      'ultimate.' % (n_known_j, n_unpub_j, r_j, Pby, Pbu))
    A('')
    A('Table 16.4a. TC-01 J-FWD, bar abs (all cases). Spectral sums as intervals [over the unpublished shares]; time-domain bound and E rule are upper bounds.')
    A('')
    A('| zeta | s | signed sum | absolute sum | SRSS | time-domain bound | E rule | MS yield / ult at the bound |')
    A('|---|---|---|---|---|---|---|---|')
    for z in (0.0, 0.02, 0.05):
        for s in (1.00, 0.90, 0.85):
            key = 'head|all|zeta%g|s%.2f' % (z, s)
            x = PM['nodes']['TC-01_JFWD']['functionals']['principal']['results'][key]
            t = jt['zeta%g|s%.2f' % (z, s)]
            A('| %g | %.2f | %s | %s | %s | %.1f | %.1f | %+.3f / %+.3f |' % (z, s, iv(x['signed']), iv(x['ABS']), iv(x['SRSS']), t['TH_upper_bar_abs'],
                                                                              t['E_rule_upper_bar_abs'], ms(t['TH_upper_bar_abs'], Pby), ms(t['TH_upper_bar_abs'], Pbu)))
    A('')
    A('Table 16.4b. TC-01 LC1 node, bar abs (all cases, worst of s).')
    A('')
    A('| zeta | signed sum | absolute sum | SRSS | time-domain bound | E rule |')
    A('|---|---|---|---|---|---|')
    for z in (0.0, 0.02, 0.05):
        sg = [min(PM['nodes']['TC-01_LC1']['functionals']['principal']['results']['head|all|zeta%g|s%.2f' % (z, s)]['signed'][0] for s in (1.0, 0.9, 0.85)),
              max(PM['nodes']['TC-01_LC1']['functionals']['principal']['results']['head|all|zeta%g|s%.2f' % (z, s)]['signed'][1] for s in (1.0, 0.9, 0.85))]
        ab = [min(PM['nodes']['TC-01_LC1']['functionals']['principal']['results']['head|all|zeta%g|s%.2f' % (z, s)]['ABS'][0] for s in (1.0, 0.9, 0.85)),
              max(PM['nodes']['TC-01_LC1']['functionals']['principal']['results']['head|all|zeta%g|s%.2f' % (z, s)]['ABS'][1] for s in (1.0, 0.9, 0.85))]
        sr = [min(PM['nodes']['TC-01_LC1']['functionals']['principal']['results']['head|all|zeta%g|s%.2f' % (z, s)]['SRSS'][0] for s in (1.0, 0.9, 0.85)),
              max(PM['nodes']['TC-01_LC1']['functionals']['principal']['results']['head|all|zeta%g|s%.2f' % (z, s)]['SRSS'][1] for s in (1.0, 0.9, 0.85))]
        A('| %g | %s | %s | %s | %.1f | %.1f |' % (z, iv(sg), iv(ab), iv(sr), max(lt['zeta%g|s%.2f' % (z, s)]['TH_upper_bar_abs'] for s in (1.0, 0.9, 0.85)),
                                                  max(lt['zeta%g|s%.2f' % (z, s)]['E_rule_upper_bar_abs'] for s in (1.0, 0.9, 0.85))))
    A('')
    A('Reading against line 228 (c) (ii) (stay below %.1f yield / %.1f ultimate), worst factor, zeta 0: the time-domain bound %.1f bar abs is %s the yield break-even '
      '(MS %+.3f) and %s the ultimate (MS %+.3f); the E rule %.1f is %s (MS %+.3f / %+.3f); the signed spectral sum (%s) %s the yield break-even; the absolute sum (%s) %s it. At zeta '
      '0.02 (ASSUMED) the bound is %.1f. On the baseline group the bound is %.1f. These are DERIVED on SIM inputs and the published share subset; they do not '
      'replace FEA3D\'s condition (a) or REV-MECH-2\'s check (b) of line 223 (3).' % (
          Pby, Pbu, th0[0], 'below' if th0[0] < Pby else 'above', ms(th0[0], Pby), 'below' if th0[0] < Pbu else 'above', ms(th0[0], Pbu),
          er0[0], cmp2(er0[0], Pby, Pbu), ms(er0[0], Pby), ms(er0[0], Pbu), iv(sg0), VP[verdict(sg0[0], sg0[1], Pby)],
          iv(ab0), VP[verdict(ab0[0], ab0[1], Pby)], th2[0], max(jtb['zeta0|s%.2f' % s]['TH_upper_bar_abs'] for s in (1.0, 0.9, 0.85))))
    A('')
    sw = th0[1]; xw = jt['zeta0|s%.2f' % sw]
    A('Caveats of the bound: (1) it treats the residual (modes above the 60th, T < 0.1949 / s ms) as one term r e_res with r = %.3f, the signed value FEA3D publishes; '
      'if the residual\'s absolute content is larger, the term grows by E_res = %.2f bar per unit of share (zeta 0, s %.2f), so the bound stays below the yield '
      'break-even while the residual\'s absolute share is <= %.3f; (2) the known modes are combined at 16 points per 0.05 ms step (>= 64 per period; shortfall '
      '<= about 0.05 bar); (3) the unpublished modes carry their bin\'s remaining absolute share with |c_j| <= the smallest published |c| (FEA3D top lists); '
      '(4) linear structure, FEA3D unit-pressure shares, head-node pressure history. The known-mode coherent part alone is %.1f bar abs and the unpublished '
      'modes add up to %.1f bar.' % (r_j, xw['E_res_bar'], sw, g('rlim'),xw['known_coherent_bar_abs'], xw['unpublished_bound_bar'][1]))
    A('')
    if other:
        A('Table 16.4c. Other governing nodes (spectral sums only, zeta 0, all-case head spectrum, worst of s; intervals over the unpublished shares; FEA3D '
          'publishes 5 shares per node here). Break-even from the FEA3D MS tags (read as yield MS; verified at J-FWD only).')
        A('')
        A('| Node | Role | signed | absolute | SRSS | residual share | break-even (tags) |')
        A('|---|---|---|---|---|---|---|')
        for key, role, sg, ab, sr, be, rr in other:
            A('| %s | %s | %s | %s | %s | %.3f | %s |' % (key, role, iv(sg), iv(ab), iv(sr), rr, ', '.join('%s %.1f' % (k, v) for k, v in be.items()) if be else '-'))
        A('')
    A('Missing (exactly): %s Owner: %s (OI-51).' % (PM['missing']['item'][0].upper() + PM['missing']['item'][1:] + '.', PM['missing']['owner']))
    A('')
    # ---- 16.5
    A('### 16.5 Purge flow basis (line 216 (5))')
    A('')
    A('ONE basis: **%.2f g/s** (DERIVED), the mean vented rate of the flow that vents 76 g on the Combustion record bound at the 289.5 K warm-end relight state '
      '(P_sat 46.47 bar): 76 g / %.4f s of flow. Use it with flow time = both-open overlap + (t_close - t_open) (valve times ASSUMED 30 / 80 ms). Derivation: the '
      'record bound M(t) = r_vap t for t <= t_v, then r_vap t_v + r_liq (t - t_v), with r_vap %.4f g/s, r_liq %.4f g/s (two taps at 0.707 mm, Cd 0.70 ASSUMED, '
      'Dyer flux), t_v %.4f s; M reaches 76 g at %.4f s. Below that point the basis is above the record (conservative); beyond it the incremental rate is the '
      'all-liquid %.2f g/s. Strict 76 g: overlap <= %.3f s (OI-42).' % (pb['mdot_g_s'], pb['t76_flow_s'], pb['law']['r_vap_g_s'], pb['law']['r_liq_g_s'],
                                                                       pb['law']['t_vapour_s'], pb['t76_flow_s'], pb['law']['r_liq_g_s'], pb['cap_overlap_s']))
    A('')
    A('Uncertainty (DERIVED; records not re-run): tank state 283.15-297.15 K: %.2f-%.2f g/s (cap %.3f-%.3f s); Cd 0.60-0.80: %.2f-%.2f g/s. The flux model '
      'spread (HEM / SPI against Dyer) is larger and is given in the file with its sources. After CF-4 / B-BLEED-1 the cap takes the measured-time form: '
      'overlap <= 76 g / mdot_measured - (t_close - t_open) (CF-4 P5). File: `purge_basis_line216_v2p4b.json` (`%s`).' % (
          ts['283.15K']['mdot_eq_g_s'], ts['297.15K']['mdot_eq_g_s'], ts['297.15K']['cap_overlap_s'], ts['283.15K']['cap_overlap_s'],
          min(x['mdot_eq_g_s'] for x in cdv.values()), max(x['mdot_eq_g_s'] for x in cdv.values()), H('purge_basis_line216_v2p4b.json')))
    A('')
    # ---- 16.6
    A('### 16.6 Start-level lift at the A1 relight state (line 216 (9))')
    A('')
    A('**%.5f mm** at the A1 relight state of record (286.70 K, P_sat 43.53 bar, port 32.2 mm, 1.16 kg): the ECU ignition-lift row (Electronics config.h '
      'kIgnLiftTab_m, DESIGN, read only); Combustion\'s injector model gives 0.21788 mm (-0.056 %%, DERIVED). Rule: the R2 hold commands h_s(T_tank at E0), the '
      'same row the ECU commands at E1 and holds to E2. At 20 C the row is 0.2039 mm. TO-VERIFY at CF-3 (encoder lift, mdot, load cell). The 210 m relight '
      'state is MISSING (OI-49); the lookup rule holds at any state.' % sl['value_mm'])
    A('')
    # ---- 16.7
    A('### 16.7 GNC P4c: lit side and pcf_tmax (request item 3)')
    A('')
    A('Raw engine thrust from grain_q1d (72 corners of the ASSUMED bands; SIM), time origin E2 per corner; GNC applies its R2 estimator, filter, frame noise and '
      'drogue terms. File: `p4c_lit_side_v2p4b.json` (`%s`); histories `start_level_lit_thrust_0p21776mm_v2p4b.csv` and `start_level_lit_thrust_v2p4b.csv`.' % H('p4c_lit_side_v2p4b.json'))
    A('')
    A('| Lift | Window | F min [N] | p05 / p50 of corner means [N] | corners never >= 37.16 N | latest first crossing (+3 frames) [s] |')
    A('|---|---|---|---|---|---|')
    for lab, Lx in (('%.5f mm (A1 state)' % sl['value_mm'], lit), ('0.2039 mm (20 C row)', lit2)):
        for wk in ('window_0.5s', 'window_0.8s'):
            w = Lx['torch0.0'][wk]; th = w['thresholds']['37.16 N']
            A('| %s | %s | %.2f | %.2f / %.2f | %d of 72 | %.3f (%.3f) |' % (lab, wk.split('_')[1].replace('s', ' s'),w['F_min_over_corners_N'], w['F_mean_min_p05_p50_N'][1],
                                                                          w['F_mean_min_p05_p50_N'][2], th['n_corners_never'], th['latest_first_crossing_after_E2_s'],
                                                                          th['latest_plus_3_frames_s']))
    A('')
    A('pcf_tmax: at %.5f mm every corner that reaches 37.16 N does so by E2 + %.3f s (+3 frames %.3f s), inside both windows; the %d corners that never reach it '
      'are not rescued by a longer window (F at 1 s >= %.2f N), so the 0.8 s window of line 227 (5) is not limited by the lit side. Flame-out side: the dead-engine '
      'cold-flow bound at the hold lift is <= %.2f N at the A1 state and %.2f N at the 297.15 K ARM limit (CONDITIONAL on CF-3). The threshold and window are GNC / '
      'lead decisions; raising the lift to lift the low corners conflicts with the 37.1 / 37.4 g/s start-flow caps (hard start).' % (
          sl['value_mm'], w8['thresholds']['37.16 N']['latest_first_crossing_after_E2_s'], w8['thresholds']['37.16 N']['latest_plus_3_frames_s'],
          w8['thresholds']['37.16 N']['n_corners_never'], lit['F_at_1s_range_N'][0], fo['286.70K']['F_cold_bound_at_h_s_N'], fo['297.15K']['F_cold_bound_at_h_s_N']))
    A('')
    # ---- 16.8
    A('### 16.8 A1 at 210 m (lines 214, 227 (1), (9)) and the 2.20 kg tank option (lines 219, 227 (9))')
    A('')
    A('A1 = 210 m is DECIDED. RV6-05 corrects "the A1 duty cycle shortens": GNC rev4 gives burn p99 %s / %s s at 210 m against %s / %s s at 285 m (SIM, staged). '
      'Against the 8.258 s A1 sizing counter that is %+.1f %% / %+.1f %%. First order (time ratio; same tank and vehicle), nominal A1 throat-area growth %.2f %% '
      'per flight at n 0.5 (%.2f %% at n 0.68; conservative %.2f %%, literature %.1f-%.1f %%); residual web >= %.2f mm (a x1.0, n 0.5) and >= %.2f mm at the band '
      'corner a x1.5, n 0.35; ENG-06 holds; B1 governs the thermal sizing. The A1 tables stay on the 300 m records as comparators until the 210 m record (OI-49).' % (
          b210 + ((ca['time_ratio'] - 1) * 100, (cb['time_ratio'] - 1) * 100, ca['erosion_nominal_dAt_pct'], ca['erosion_nominal_n068_dAt_pct'],
                  ca['erosion_conservative_dAt_pct'], ca['erosion_literature_dAt_pct'][0], ca['erosion_literature_dAt_pct'][1], ca['web_end_a1p0_n0p5_mm'],
                  ca['web_end_min_band_a1p5_n0p35_mm'])))
    A('')
    A('2.20 kg option (first order, DERIVED; no run): A1 burn p99 8.92 / 8.71 s, max 9.24 s (227 (9)) against the 8.258 s counter; the thrust factor (m_2.20 / '
      'm_2.00)^0.8 = %.4f bounds the heat-transfer rise (mass ratio from the GNC rev4 item [15] T/W).' % TK['basis']['thrust_factor_upper'])
    A('')
    A('| Case | Burn [s] | Nominal dAt/At [%] (n 0.5) | n 0.68 | Conservative | Literature | Web a x1.0 n 0.5 [mm] | Web band corner [mm] |')
    A('|---|---|---|---|---|---|---|---|')
    for lab, c in (('2.00 kg, 210 m p99 (first value of 227 (9))', ca), ('2.00 kg, 210 m p99 (second value)', cb)):
        A('| %s | %.3f | %.2f | %.2f | %.2f | %.1f-%.1f | %.2f | %.2f |' % (lab, c['burn_s'], c['erosion_nominal_dAt_pct'], c['erosion_nominal_n068_dAt_pct'],
                                                                          c['erosion_conservative_dAt_pct'], c['erosion_literature_dAt_pct'][0], c['erosion_literature_dAt_pct'][1],
                                                                          c['web_end_a1p0_n0p5_mm'], c['web_end_min_band_a1p5_n0p35_mm']))
    for lab, c in (('2.20 kg p99', t871), ('2.20 kg p99', t892), ('2.20 kg max', t924)):
        A('| %s | %.2f | %.2f-%.2f | %.2f-%.2f | %.2f-%.2f | %.1f-%.1f | %.2f-%.2f | %.2f |' % (
            lab, c['burn_s'], c['erosion_nominal_dAt_pct'][0], c['erosion_nominal_dAt_pct'][1], c['erosion_nominal_n068_dAt_pct'][0], c['erosion_nominal_n068_dAt_pct'][1],
            c['erosion_conservative_dAt_pct'][0], c['erosion_conservative_dAt_pct'][1], c['erosion_literature_dAt_pct'][0], c['erosion_literature_dAt_pct'][1],
            c['web_end_a1p0_n0p5_mm'][0], c['web_end_a1p0_n0p5_mm'][1], c['web_end_min_band_a1p5_n0p35_mm']))
    A('')
    A('Findings: ' + ' '.join(TK['findings']) + ' File: `tank_2p20kg_option_v2p4b.json` (`%s`). Open item OI-50 (GNC, Combustion, Mechanical).' % H('tank_2p20kg_option_v2p4b.json'))
    A('')
    # ---- 16.9
    A('### 16.9 Datasheet inputs (request item 5)')
    A('')
    A('`02-combustion/DATASHEET-INPUTS-COMBUSTION.md` (`%s`): one table of the headline engine numbers with tags and sources (rated and worst-case thrust and '
      'Pc, O/F, Isp, throttle range, burn time and impulse with the 2.0 kg tank, the 2.20 kg option, the start level, the purge basis, the FA-1 basis and TC-01). '
      'Built by `src/build_datasheet_inputs_v2p4b.py` from the interface keys and data files; interface key `datasheet_inputs_v2p4b`.' % ds_sha)
    A('')
    # ---- 16.10
    A('### 16.10 Open items (final fold)')
    A('')
    A('Updated: OI-41 (proposal §16.3), OI-42 (ONE basis; measured-time form), OI-49 (210 m decided; record missing). New: OI-50 2.20 kg option (GNC; Combustion; '
      'Mechanical); OI-51 FEA3D share vector (FEA3D / Mechanical; Combustion); OI-52 assembly damping (founders; Mechanical; Combustion). Rows in §12.')
    A('')
    # ---- 16.11
    A('### 16.11 Files, reproduction and failures kept')
    A('')
    A('| Script (src/) | Data (data/v2p4b/) | Use |')
    A('|---|---|---|')
    src = HERE
    def S(f):
        return '`%s` (`%s`)' % (f, sha(os.path.join(src, f)))
    A('| %s | purge_basis_line216_v2p4b.json (`%s`) | §16.5 |' % (S('purge_basis_line216_v2p4b.py'), H('purge_basis_line216_v2p4b.json')))
    A('| %s | p4c_lit_side_v2p4b.json (`%s`) | §16.6, §16.7 |' % (S('p4c_lit_side_v2p4b.py'), H('p4c_lit_side_v2p4b.json')))
    A('| %s | tank_2p20kg_option_v2p4b.json (`%s`) | §16.8 |' % (S('tank_2p20kg_option_v2p4b.py'), H('tank_2p20kg_option_v2p4b.json')))
    A('| %s | fa1_spectra_damped_v2p4b.json (`%s`), fa1_pressure_spectra_published_v2p4b.csv (`%s`), fa1_pressure_spectra_modal_periods_v2p4b.csv (`%s`) | §16.2 |' % (
        S('fa1_spectra_damped_v2p4b.py'), H('fa1_spectra_damped_v2p4b.json'), H('fa1_pressure_spectra_published_v2p4b.csv'), H('fa1_pressure_spectra_modal_periods_v2p4b.csv')))
    A('| %s | fa1_per_mode_peq_v2p4b.json (`%s`) | §16.4 spectral sums |' % (S('fa1_per_mode_peq_v2p4b.py'), H('fa1_per_mode_peq_v2p4b.json')))
    A('| %s | fa1_modal_th_bound_v2p4b.json (`%s`), fa1_relative_spectrum_E_v2p4b.csv (`%s`) | §16.3, §16.4 bounds |' % (
        S('fa1_modal_th_bound_v2p4b.py'), H('fa1_modal_th_bound_v2p4b.json'), H('fa1_relative_spectrum_E_v2p4b.csv')))
    A('| %s | `DATASHEET-INPUTS-COMBUSTION.md` (`%s`) | §16.9 |' % (S('build_datasheet_inputs_v2p4b.py'), ds_sha))
    A('| `build_final_fold_v2p4b.py` | this report, `interfaces/combustion.json` (`%s`), `CF-4-SPEC.md` v2.1 (`%s`) | §16 |' % (cj_sha, cf_sha))
    A('')
    A('Reproduction: `/opt/engine-venv/bin/python -I` from `src/`, usage in each docstring, input hashes asserted. The damped-spectrum run took about 64 min and the '
      'time-domain bound about 24 min on the shared CPU (nice 15, one thread); the rest take seconds to minutes.')
    A('')
    A('Failures kept as evidence: (1) the first damped-spectrum run stopped on its own time-grid assert (the stored float32 time vectors drift from k x 0.05 ms by '
      'up to 1.85e-5 s); the assert was widened to 2.5e-5 s and the exact undamped check moved to the stored grid, then re-run; no output of the first run was '
      'used. (2) The first relative-spectrum bound |2 zeta s / omega| + R overestimated max |q - g| (ratio up to 2.78 against a 64-point sampling); it was replaced '
      'by the exact per-step maximum (step ends and stationary points) before any value was used. (3) The 2.20 kg script failed once on a literal percent sign in '
      'a formatted string. (4) The FEA3D share vector is not published, so the per-mode result is an interval (OI-51), not a number. (5) A check in the fold '
      'builder found two references to ICD-AIRFRAME v2.1 that line 222 made stale (the §7.6 thrust note and the interface thrust rule; the session notes had '
      'recorded none); both are restated, the old interface value kept under `rule_superseded`.')
    return '\n'.join(o)


if __name__ == '__main__':
    main(*sys.argv[1:6])

"""DATASHEET-INPUTS-COMBUSTION.md: one table of the headline engine numbers with their evidence tags (Combustion v2.4b, 2026-10-19;
lead request 2026-10-19 item 5).  Every value is read from a published or staged Combustion file at build time (interface keys by
name, data files by hash); nothing is typed in by hand except the wording.  The datasheet owner quotes from this table; the tags
travel with the numbers.  Nothing here is physical approval.
usage: python -I build_datasheet_inputs_v2p4b.py COMBUSTION_JSON_V24B DATA_V2P4B_DIR DC_GNCV3_SUMMARY CHANGELOG OUT_MD
"""
import hashlib, json, math, os, re, sys
sys.dont_write_bytecode = True
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
BASE, ALLG = 'vapour_once|rounded_Cd1.0|grid_OF4-12|all', 'all|all|incl_OF3-3.5|all'
SCALES = (1.00, 0.90, 0.85)
EXPECT = {'dc_summary': '7f4f181b80d55331'}


def main(cj_f, dd, dc_f, chlog_f, out_f):
    assert sha(dc_f) == EXPECT['dc_summary'], sha(dc_f)
    CJ = json.load(open(cj_f)); assert CJ['version'] == 'v2.4b'
    J = lambda f: json.load(open(os.path.join(dd, f)))
    H = lambda f: sha(os.path.join(dd, f))
    DC = json.load(open(dc_f))
    PB, P4, TK = J('purge_basis_line216_v2p4b.json'), J('p4c_lit_side_v2p4b.json'), J('tank_2p20kg_option_v2p4b.json')
    DS, PM, TH = J('fa1_spectra_damped_v2p4b.json'), J('fa1_per_mode_peq_v2p4b.json'), J('fa1_modal_th_bound_v2p4b.json')
    for x in (DS, TH):
        assert not x.get('smoke_test_subset'), 'smoke-test output'
    L = open(chlog_f).read().splitlines()
    op = CJ['operating_points']; mt = op['max_thrust']; tp = op['throttle_points_20C_initial_port']; pl = op['pressure_limits']
    hold = op['max_thrust_hold_baseline_tank']; mb = CJ['meop_basis_v2p4']['v']; nz = CJ['gas_path']['nozzle']; gr = CJ['gas_path']['grain']
    v = lambda o: o['v'] if isinstance(o, dict) and 'v' in o else o
    fs = [r for r in v(pl['full_stroke_failure_S230']) if r['T_tank_C'] <= 25.0]
    fs30 = [r for r in v(pl['full_stroke_failure_S230']) if r['T_tank_C'] == 30.0]
    rec = {k.split('-S230')[0]: x for k, x in DC.items()}
    a1, a1h = rec['DC-A1dispp99'], rec['DC-A1dispp99_tg711']
    b1, b1m, b1h = rec['DC-B1v3p99'], rec['DC-B1v3max'], rec['DC-B1v3p99_tg711']
    m227 = re.search(r"burn p99 ([0-9.]+) / ([0-9.]+) s at 210 m", L[226]); assert m227
    # FA-1: band maxima (head, all cases / baseline), the per-mode results at TC-01 J-FWD
    bm = DS['band_maxima']
    def band(b, key):
        x = bm[b][key]; return x['value_bar'], x['period_ms']
    jt = TH['results'][ALLG]['nodes']['TC-01_JFWD']; lt = TH['results'][ALLG]['nodes']['TC-01_LC1']
    def worst(d, z, k):
        return max((d['zeta%g|s%.2f' % (z, s)][k], s) for s in SCALES)
    th0, th2 = worst(jt, 0, 'TH_upper_bar_abs'), worst(jt, 0.02, 'TH_upper_bar_abs')
    er0, er2 = worst(jt, 0, 'E_rule_upper_bar_abs'), worst(jt, 0.02, 'E_rule_upper_bar_abs')
    lth0, ler0 = worst(lt, 0, 'TH_upper_bar_abs'), worst(lt, 0, 'E_rule_upper_bar_abs')
    Pby, Pbu = TH['jfwd_breakeven']['yield_bar_abs'], TH['jfwd_breakeven']['ult_bar_abs']
    pr = PM['nodes']['TC-01_JFWD']['functionals']['principal']['results']
    def pm_rng(z, comb):
        lo = min(pr['head|all|zeta%g|s%.2f' % (z, s)][comb][0] for s in SCALES)
        hi = max(pr['head|all|zeta%g|s%.2f' % (z, s)][comb][1] for s in SCALES)
        return lo, hi
    sg0, ab0, sr0 = pm_rng(0, 'signed'), pm_rng(0, 'ABS'), pm_rng(0, 'SRSS')
    pg = TH['results'][ALLG]['P_gauge_peak_bar']
    rj = PM['nodes']['TC-01_JFWD']['functionals']['principal']['residual_share']
    rows = []
    R = lambda *c: rows.append(c)
    R('Rated thrust (maximum commanded)', '%.0f N; Pc %.2f bar abs; O/F %.2f; Isp (sea level) %.1f s; c* %.0f m/s delivered; propellant flow %.1f g/s '
      '(N2O %.1f, ABS %.1f)' % (v(mt['F_N']), v(mt['Pc_Pa']) / 1e5, v(mt['OF']), v(mt['Isp_SL_s']), v(mt['cstar_delivered_m_s']),
                                v(mt['mdot_total_kg_s']) * 1e3, v(mt['mdot_ox_kg_s']) * 1e3, v(mt['mdot_fuel_kg_s']) * 1e3),
      '20 C saturated tank, initial port 25 mm, nominal regression law, eta_c* 0.92, eta_cf 0.975, pintle Cd 0.70', 'SIM (grain_q1d v2 on ASSUMED law, Cd and efficiencies; CEA)',
      '`combustion.json` operating_points.max_thrust')
    R('Chamber pressure limits', 'software cap %.0f bar; ECU abort %.0f bar; MEOP %.0f bar; proof %.1f bar; MEOP basis %.2f bar (margin %.2f bar to MEOP)' % (
        v(pl['normal_cap_Pa']) / 1e5, v(pl['abort_Pa']) / 1e5, v(pl['chamber_MEOP_Pa']) / 1e5, v(pl['proof_Pa']) / 1e5, mb['basis_bar'], mb['margin_to_MEOP_bar']),
      'MEOP basis: late light at the 24 C interlock with the designed line loss and the conservative bands', 'LEAD (limits); SIM (basis)',
      '`combustion.json` operating_points.pressure_limits, meop_basis_v2p4')
    R('Thrust ceiling (available, not commanded)', v(op['ceiling_vs_Cd_20C_and_models']), 'ceiling = F at min(full stroke 4 mm, injector dP/Pc >= 0.25)',
      'SIM (injector models; Cd ASSUMED 0.5-0.8)', '`combustion.json` operating_points.ceiling_vs_Cd_20C_and_models')
    R('Worst-case steady thrust and Pc (pintle full-stroke failure)', '%.0f-%.0f N, Pc %.1f-%.1f bar abs at 15-25 C (Cd 0.6-0.8); %.0f N, %.2f bar abs at the 30 C bound' % (
        min(r['F_N'] for r in fs), max(r['F_N'] for r in fs), min(r['Pc_bar'] for r in fs), max(r['Pc_bar'] for r in fs),
        max(r['F_N'] for r in fs30), max(r['Pc_bar'] for r in fs30)),
      'initial port, steady; the ECU abort (30 bar) acts on it; the hard-start transient is the FA-1 row', 'SIM (grain_q1d v2 steady)',
      '`combustion.json` operating_points.pressure_limits.full_stroke_failure_S230')
    lo, hi = tp[-1], tp[0]
    R('Throttle range', '%.1f-%.0f N (%.1f-%.0f %%): Pc %.2f-%.2f bar abs; O/F %.2f-%.2f; Isp (sea level) %.1f-%.1f s' % (
        lo['F_N'], hi['F_N'], lo['fraction'] * 100, hi['fraction'] * 100, lo['Pc_Pa'] / 1e5, hi['Pc_Pa'] / 1e5, lo['OF'], hi['OF'], lo['Isp_SL_s'], hi['Isp_SL_s']),
      '25 %% floor (125 N): %s; 20 %% target (100 N): %s; 12.5 %% stretch: model meets it, low-flux combustion UNVERIFIED (static fire T3)' % (
          op['floor_requirement_25pct']['status'], op['floor_target_20pct']['status']),
      'SIM (floors REQ)', '`combustion.json` operating_points.throttle_points_20C_initial_port, floor_*')
    R('Burn time and total impulse at a 500 N hold (2.0 kg tank)', '500 N held %.2f-%.2f s; liquid end %.2f-%.2f s; impulse to liquid end %.0f-%.0f N s; N2O %.3f-%.3f kg' % (
        tuple(v(hold['t_500N_held_s'])) + tuple(v(hold['t_liquid_depletion_s'])) + tuple(v(hold['impulse_to_liquid_end_Ns'])) + tuple(v(hold['ox_to_liquid_end_kg']))),
      '15-25 C tank (the 25 C end is a bound: ARM 15-24 C), equilibrium and non-equilibrium tank', 'SIM',
      '`combustion.json` operating_points.max_thrust_hold_baseline_tank')
    R('Mission burns (2.0 kg tank, 3.167 L)', 'A1 dispersed p99: %.2f s, %.1f N s, O/F %.2f, Isp %.1f s (T0 %.2f K); A1 p99 throat-growth record (tg711, T0 %.2f K): %.2f s, %.1f N s; '
      'B1 85 m p99: %.2f s, %.1f N s, O/F %.2f, Isp %.1f s; B1 max: %.2f s, %.1f N s, Isp %.1f s; B1 p99 throat-growth record (tg711, T0 %.2f K): %.2f s, %.1f N s, Isp %.1f s' % (
          a1['burn_s'], a1['impulse_Ns'], a1['OF_mean'], a1['Isp_mean_s'], a1['T0_K'], a1h['T0_K'], a1h['burn_s'], a1h['impulse_Ns'],
          b1['burn_s'], b1['impulse_Ns'], b1['OF_mean'], b1['Isp_mean_s'], b1m['burn_s'], b1m['impulse_Ns'], b1m['Isp_mean_s'],
          b1h['T0_K'], b1h['burn_s'], b1h['impulse_Ns'], b1h['Isp_mean_s']),
      'gnc.json v3 records flown on the S230 grain (non-equilibrium tank); the A1 rows are the 300 m record (comparator). A1 is decided at 210 m '
      '(lines 214, 227 (1)): GNC rev4 burn p99 %s / %s s (RV6-05: not shorter); its impulse is MISSING until gnc.json v3.2; B1 governs sizing' % m227.groups(),
      'SIM', '`02-combustion/data/v2/dc_gncv3/summary_v2p4.json` (`%s`); CHANGELOG 227 (9)' % sha(dc_f))
    c9 = TK['cases']['max_9.24s']; c8 = TK['cases']['p99_8.71s']
    R('N2O tank', '2.00 kg (founder, line 219). Option 2.20 kg: A1 burn p99 %.2f / %.2f s (max %.2f s) over the %.3f s A1 sizing counter; first-order A1 '
      'throat-area growth %.2f-%.2f %% per flight (nominal, n 0.5), residual web >= %.2f mm' % (
          TK['basis']['burn_p99_s'][0], TK['basis']['burn_p99_s'][1], TK['basis']['burn_max_s'], TK['basis']['sizing_counter_s'],
          c8['erosion_nominal_dAt_pct'][0], c9['erosion_nominal_dAt_pct'][1], c9['web_end_min_band_a1p5_n0p35_mm']),
      '2.20 kg: B1, thermal and erosion TO-VERIFY (line 227 (9)); no B1 record with 2.20 kg (OI-50)', 'LEAD (2.00 kg); DERIVED (first-order scaling)',
      '`data/v2p4b/tank_2p20kg_option_v2p4b.json` (`%s`)' % H('tank_2p20kg_option_v2p4b.json'))
    R('Nozzle and grain', 'throat %.2f mm, exit %.2f mm, expansion ratio %.1f (graphite insert, one per flight); ABS grain %.1f mm OD x %.0f mm, one straight port %.0f mm initial' % (
        v(nz['throat_diameter_m']) * 1e3, v(nz['exit_diameter_m']) * 1e3, v(nz['expansion_ratio']), v(gr['outer_diameter_m']) * 1e3, v(gr['length_m']) * 1e3,
        v(gr['port']['initial_diameter_m']) * 1e3),
      'graphite grade TO-QUOTE (Sønderborg DK-6400)', 'DESIGN', '`combustion.json` gas_path')
    sl = P4['start_level_lift']; w8 = P4['lit_side']['lift_0p21776mm']['torch0.0']['window_0.8s']
    R('Start level (relight)', 'start-level lift %.5f mm at the A1 relight state (286.70 K), 0.2039 mm at 20 C (the ECU ignition-lift row at the tank '
      'temperature); lit thrust from E2 to E2 + 0.8 s >= %.2f N (%d of 72 corners never reach 37.16 N); dead-engine cold flow <= 12.86 N (CONDITIONAL on CF-3)' % (
          sl['value_mm'], w8['F_min_over_corners_N'], w8['thresholds']['37.16 N']['n_corners_never']),
      'lit thrust: grain_q1d over 72 corners of the ASSUMED bands; lift: ECU table (Electronics)', 'DESIGN (lift); SIM (lit); DERIVED bound (cold flow)',
      '`data/v2p4b/p4c_lit_side_v2p4b.json` (`%s`)' % H('p4c_lit_side_v2p4b.json'))
    b = PB['basis']
    R('Relight purge flow basis', '%.2f g/s = 76 g / %.4f s of flow at %.1f K (flow time = both-open overlap + 0.05 s); strict 76 g needs overlap <= %.3f s' % (
        b['mdot_g_s'], b['t76_flow_s'], 289.5, b['cap_overlap_s']),
      'uncertainty: %.2f-%.2f g/s over the relight tank state 283.15-297.15 K; Cd 0.60-0.80 ASSUMED' % (
          PB['uncertainty']['tank_state']['283.15K']['mdot_eq_g_s'], PB['uncertainty']['tank_state']['297.15K']['mdot_eq_g_s']),
      'DERIVED (from SIM records on ASSUMED Cd)', '`data/v2p4b/purge_basis_line216_v2p4b.json` (`%s`)' % H('purge_basis_line216_v2p4b.json'))
    k = lambda z: 'head|all|zeta%g' % z
    t1, t2, t3, t4 = (band(bb, k(0)) for bb in ('T_le_0p1ms', 'T_0p1_to_1ms', 'T_1_to_20ms', 'T_20_to_50ms'))
    d2 = band('T_0p1_to_1ms', k(0.02)); d5 = band('T_0p1_to_1ms', k(0.05))
    R('FA-1 hard start: structural load', 'head equivalent static pressure, all 896 cases, undamped: %.1f bar abs (T <= 0.1 ms), %.1f (0.1-1 ms; %.1f at zeta 0.02, %.1f at '
      'zeta 0.05), %.1f (1-20 ms), %.1f (20-50 ms, at T = %.1f ms near its lower edge); peak head pressure %.1f bar abs; FA1S 151.04 bar abs bounds every period' % (
          t1[0], t2[0], d2[0], d5[0], t3[0], t4[0], t4[1], pg + 1.01325),
      'the line-194 (1) band values (90 bar abs at T <= 0.1 ms; 93 yield / 102 ultimate at 0.1-1 ms) are below the all-case values under 1 ms (OI-41; '
      'restated values %d / %d / %d / %d bar abs or a per-mode rule proposed in REPORT §16.3); ' % tuple(math.ceil(x[0]) for x in (t1, t2, t3, t4)) +
      'damping ASSUMED (no modal test)', 'SIM histories (ASSUMED inputs); DERIVED spectra; LEAD to decide',
      '`data/v2p4b/fa1_spectra_damped_v2p4b.json` (`%s`)' % H('fa1_spectra_damped_v2p4b.json'))
    R('FA-1 at TC-01 J-FWD (per-mode)', 'time-domain modal bound %.1f bar abs undamped (%.1f at zeta 0.02), E rule %.1f (%.1f); spectral sums at zeta 0: signed %.1f-%.1f, '
      'absolute %.1f-%.1f, SRSS %.1f-%.1f bar abs; break-even %.1f yield / %.1f ultimate; MS at the bound %+.3f / %+.3f; on the restated 0.1-1 ms band value '
      '%d bar abs %+.3f / %+.3f (line 228 lists +0.25 / +0.23 on the 93 / 102 band reading)' % (
          th0[0], th2[0], er0[0], er2[0], sg0[0], sg0[1], ab0[0], ab0[1], sr0[0], sr0[1], Pby, Pbu, Pby / th0[0] - 1, Pbu / th0[0] - 1,
          math.ceil(band('T_0p1_to_1ms', 'head|all|zeta0')[0]), Pby / math.ceil(band('T_0p1_to_1ms', 'head|all|zeta0')[0]) - 1,
          Pbu / math.ceil(band('T_0p1_to_1ms', 'head|all|zeta0')[0]) - 1),
      'worst of the FE frequency factors x0.85 / 0.90 / 1.00; intervals because FEA3D publishes %d of 60 modal shares (OI-51); the bound takes the residual at its '
      'published signed share %.3f and stays below the yield break-even while the residual absolute share is <= %.3f; TC-01 LC1 node: %.1f (bound), %.1f (E rule)' % (
          len(PM['nodes']['TC-01_JFWD']['functionals']['principal']['known_modes']), rj, abs(rj) + (Pby - th0[0]) / jt['zeta0|s%.2f' % th0[1]]['E_res_bar'],
          lth0[0], ler0[0]),
      'DERIVED on SIM shares (FEA3D) and SIM histories; damping ASSUMED', '`data/v2p4b/fa1_modal_th_bound_v2p4b.json` (`%s`), `fa1_per_mode_peq_v2p4b.json` (`%s`)' % (
          H('fa1_modal_th_bound_v2p4b.json'), H('fa1_per_mode_peq_v2p4b.json')))
    head = ['Item', 'Value', 'Condition / basis', 'Tag', 'Source']
    tab = ['| ' + ' | '.join(head) + ' |', '|' + '---|' * len(head)] + ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows]
    doc = '\n'.join([
        '# Datasheet inputs: Combustion and Propulsion (ARGOS H1 engine)', '',
        'Version v2.4b, 2026-10-19. Owner: Combustion and Propulsion. Built by `02-combustion/src/build_datasheet_inputs_v2p4b.py` from '
        '`interfaces/combustion.json` v2.4b (values by key; the published file carries the same values) and the v2.4b data files named in each row. '
        'Lead request 2026-10-19 item 5. Units SI with bar for pressures (abs unless stated). No number here is MEASURED: the engine has not been '
        'fired. Tags: SIM (model run), DERIVED (computed from other values), ASSUMED, DESIGN, LEAD, REQ, TO-VERIFY, MISSING. '
        'Nothing here is physical approval.', '',
        '\n'.join(tab), '',
        'Notes:',
        '- A1 apogee target 210 m is decided (lines 214, 227 (1)); the A1 records above are the 300 m comparators until gnc.json v3.2 (OI-49).',
        '- Prices: none quoted here; any quote is TO-QUOTE, delivered to Sønderborg DK-6400.',
        '- The FA-1 rows are proposals for the lead (OI-41) and depend on the FEA3D share vector (OI-51) and on damping (OI-52).', ''])
    open(out_f, 'w', encoding='utf-8').write(doc)
    print('wrote', out_f, sha(out_f), 'rows', len(rows))


if __name__ == '__main__':
    main(*sys.argv[1:6])

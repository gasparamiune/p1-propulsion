# ---------------------------------------------------------------------------------------------
# section 7 (v0.3.0): combustion, sequences, purge, abort set, FA-1 rulings, tests
# ---------------------------------------------------------------------------------------------
def sec_combustion(ctx, doc, a, D):
    cl = D['cl']
    o = [doc.h(1, '7 Combustion, sequences and the abort set')]
    if ctx.ovr and any(e['status'] == 'ACTIVE' for e in ctx.ovr.entries):
        o.append(note_box(f'<b>Reading this section.</b> combustion.json {esc(ctx.src("CMB").version or "")} is the source of every value here unless a row names '
                          'another source. Where a quoted text still carries wording that a newer lead decision replaced, the old words are '
                          '<del class="stale">struck through</del> and the decision is <ins class="dec">inserted</ins> with its override id (§13.1).', 'info'))
    o.append(doc.h(2, '7.1 Design point'))
    rows = [
        ['Fuel', tvtxt(ctx.v('CMB', '/decisions/fuel'))],
        ['Oxidiser load and tank volume', cat(ctx.v('CMB', '/decisions/N2O_load_and_tank/v/m_N2O_kg', 'kg', tag_ptr='/decisions/N2O_load_and_tank').h('.2f'), ' in ',
                                              ctx.v('CMB', '/decisions/N2O_load_and_tank/v/V_tank_m3', 'L', conv=(1000, 0, 'm³ to L'), tag_ptr='/decisions/N2O_load_and_tank').h('.2f'), Cell('', ctx.recent[-2:]))],
        ['Tank conditioning', tvtxt(ctx.v('CMB', '/decisions/tank_pressurisation'), 400)],
        ['Ignition interlock guard band', tvtxt(ctx.v('CMB', '/interlock_guard_band/v/thresholds', tag_ptr='/interlock_guard_band'), 300)],
        ['Model basis', tvtxt(ctx.v('CMB', '/operating_points/basis', tag='SIM'), 300)],
        ['Combustion and nozzle efficiencies η<sub>c*</sub> / η<sub>cf</sub>', cat(rx(ctx, 'CMB', '/operating_points/basis', r'eta_c\* ([\d.]+)', tag='ASSUMED').h('.3f'), ' / ',
                                                                                   rx(ctx, 'CMB', '/operating_points/basis', r'eta_cf ([\d.]+)', tag='ASSUMED').h('.3f'), Cell('', ctx.recent[-2:]))],
        ['Oxidiser flux at the head, rated, initial port', num_cell(ctx.v('CMB', '/operating_points/max_thrust/G_ox_initial_kg_m2s', 'kg/(m²·s)'), '.0f')],
        ['Regression law (form)', tvtxt(ctx.v('CMB', '/gas_path/grain/regression_law/form', tag='ASSUMED'))],
        ['Regression coefficient a / exponent n', cat(ctx.v('CMB', '/gas_path/grain/regression_law/a', 'm/s·(kg/m²s)^-n').h('.3e'), ' / ', ctx.v('CMB', '/gas_path/grain/regression_law/n').h('.2f'), Cell('', ctx.recent[-2:]))],
        ['Regression law note', tvtxt(ctx.v('CMB', '/gas_path/grain/regression_law/note', tag='ASSUMED'), 300)],
        ['MEOP basis (SIM)', tvtxt(ctx.v('CMB', '/meop_basis_v2p4'), 300)],
        ['Stored energy (flight tank)', tvtxt(ctx.v('CMB', '/stored_energy/v/flight_tank_20C', tag_ptr='/stored_energy'), 200)],
    ]
    o.append(dtable(['Item', 'Value'], rows, widths=['32%', '68%']))

    o.append(doc.h(2, '7.2 Fuel grain'))
    G = '/gas_path/grain'
    segs = [D['bom_by_pn'].get('ENG-GR-01'), D['bom_by_pn'].get('ENG-GR-02')]
    seg_len = []
    for pn in ('ENG-GR-01', 'ENG-GR-02'):
        lo, hi, n = manifest_extent(ctx, pn_prefix=pn + '#')
        seg_len.append(man_tv(ctx, (hi[2] - lo[2]) if n else None, f'z extent of {pn}', pn_prefix=pn + '#'))
    rows = [
        ['Segments (BOM)', cat(*[Cell(f'{esc(r.l.get("name", ""))} {r.row_tv.ref()}<br>', [r.row_tv]) for r in segs if r])],
        ['Segment length from the CAD manifest (GR-01 / GR-02)', cat(seg_len[0].h('.1f'), ' / ', seg_len[1].h('.1f'))],
        ['Grain outer diameter / total length', cat(ctx.v('CMB', f'{G}/outer_diameter_m', 'mm', conv=(1000, 0, 'm to mm')).h('.1f'), ' / ',
                                                   ctx.v('CMB', f'{G}/length_m', 'mm', conv=(1000, 0, 'm to mm')).h('.1f'), Cell('', ctx.recent[-2:]))],
        ['Port', cat(ctx.v('CMB', f'{G}/port/type').h(), ', initial Ø ', ctx.v('CMB', f'{G}/port/initial_diameter_m', 'mm', conv=(1000, 0, 'm to mm')).h('.1f'), Cell('', ctx.recent[-2:]))],
        ['Initial web', num_cell(ctx.v('CMB', f'{G}/port/initial_web_m', 'mm', conv=(1000, 0, 'm to mm')), '.2f')],
        ['Port entrance (decided)', tvtxt(cl.item(160, 4), 400)],
        ['Density (printed ABS)', num_cell(ctx.v('CMB', f'{G}/density_kg_m3', 'kg/m³'), '.0f')],
        ['Grain mass: Combustion / CAD', cat(ctx.v('CMB', f'{G}/mass_kg', 'kg').h('.3f'), ' / ', ctx.v('MP', '/grain_mass_wet_kg', 'kg', tag='DERIVED').h('.4f'), Cell('', ctx.recent[-2:]))],
        ['Residual web rule', tvtxt(ctx.v('CMB', f'{G}/residual_web_rule'))],
        ['Retention', tvtxt(ctx.v('CMB', f'{G}/retention', tag='DESIGN'), 300)],
    ]
    o.append(dtable(['Item', 'Value'], rows, widths=['32%', '68%']))

    o.append(doc.h(2, '7.3 Injector, feed and igniter'))
    V = '/valves_and_actuators'
    I = '/igniter'
    ts = f'{I}/torch_sizing'
    el = f'{I}/electrical'
    igm = ctx.v('CMB', f'{I}/mass_kg', 'kg')
    ig_bom = D['bom_by_pn'].get('ENG-IG-01')
    rows = [
        ['Feed architecture', tvtxt(ctx.v('CMB', f'{V}/architecture', tag='DESIGN'), 400)],
        ['Injector flow model', tvtxt(ctx.v('CMB', '/gas_path/injector/flow_model', tag='LITERATURE'))],
        ['Filter', tvtxt(ctx.v('CMB', '/gas_path/injector/filter'))],
        ['Isolation valve: minimum Cv / MEOP / closing time', cat(ctx.v('CMB', f'{V}/isolation_valve/Cv_min').h('.1f'), ' / ',
                                                                  Cell(pres(ctx, ctx.v('CMB', f'{V}/isolation_valve/MEOP_Pa', 'Pa')), [ctx.recent[-1]]), ' / ',
                                                                  ctx.v('CMB', f'{V}/isolation_valve/close_time_max_s', 's').h('.2f'), Cell('', [ctx.recent[-1], ctx.recent[-3]]))],
        ['Relief: trapped liquid, back-relief and tank', tvtxt(ctx.v('CMB', f'{V}/isolation_valve/trapped_liquid_relief'))],
        ['Tank relief (v2.4a)', tvtxt(ctx.v('CMB', '/relief_v2p4a'), 400)],
        ['Hose across the gimbal', tvtxt(ctx.v('CMB', f'{V}/hose', tag='DERIVED'), 300)],
        ['Pc tap and sense line', cat(tvtxt(ctx.v('CMB', '/gas_path/pc_tap/location', tag='DESIGN')), '<br>', tvtxt(ctx.v('CMB', '/gas_path/pc_tap/sense_line')))],
        ['Igniter type', tvtxt(ctx.v('CMB', f'{I}/type', tag='DESIGN'))],
        ['Torch chamber pressure / O/F / throat diameter', cat(ctx.v('CMB', f'{ts}/v/Pc_torch_bar', 'bar', tag='DERIVED', tag_ptr=ts).h('.1f'), ' / ',
                                                               ctx.v('CMB', f'{ts}/v/OF', tag='DERIVED', tag_ptr=ts).h('.1f'), ' / ',
                                                               ctx.v('CMB', f'{ts}/v/throat_d_m', 'mm', conv=(1000, 0, 'm to mm'), tag='DERIVED', tag_ptr=ts).h('.1f'), Cell('', ctx.recent[-3:]))],
        ['Torch flows N2O / propane', cat(ctx.v('CMB', f'{ts}/v/mdot_n2o_kg_s', 'g/s', conv=(1000, 0, 'kg/s to g/s'), tag='DERIVED', tag_ptr=ts).h('.3f'), ' / ',
                                          ctx.v('CMB', f'{ts}/v/mdot_propane_kg_s', 'g/s', conv=(1000, 0, 'kg/s to g/s'), tag='DERIVED', tag_ptr=ts).h('.3f'), Cell('', ctx.recent[-2:]))],
        ['Spark: supply / energy / rate', cat(ctx.v('CMB', f'{el}/v/spark_supply_V', 'V', tag_ptr=el).h('.0f'), ' / ', ctx.v('CMB', f'{el}/v/spark_energy_J', 'J', tag_ptr=el).h('.2f'), ' / ',
                                              ctx.v('CMB', f'{el}/v/rate_Hz', 'Hz', tag_ptr=el).h('.0f'), Cell('', ctx.recent[-3:]))],
        ['Igniter system mass: Combustion / BOM ENG-IG-01', cat(igm.h('.2f'), ' / ', ig_bom.mass_tv.h('.3f') if ig_bom else 'MISSING', Cell('', [igm] + ([ig_bom.mass_tv] if ig_bom else [])))],
        ['Starts per flight', tvtxt(ctx.v('CMB', f'{I}/starts_per_flight'))],
        ['Light windows W from the lift command', cat(ctx.v('CMB', '/light_windows/v/flight_first_start', 's', tag_ptr='/light_windows').h('.2f'), ' first start · ',
                                                      ctx.v('CMB', '/light_windows/v/flight_relight', 's', tag_ptr='/light_windows').h('.2f'), ' relight · ',
                                                      ctx.v('CMB', '/light_windows/v/stand', 's', tag_ptr='/light_windows').h('.2f'), ' stand')],
    ]
    o.append(dtable(['Item', 'Value'], rows, widths=['32%', '68%']))

    o.append(doc.h(2, '7.4 Start and relight sequence'))
    SQ = f'{I}/sequence/v'
    seq = ctx.raw('CMB', SQ + '/start', default=[]) or []
    rows = []
    for k, e in enumerate(seq):
        ep = ctx.v('CMB', f'{SQ}/start/{k}/epoch', tag='LEAD', tag_ptr=f'{I}/sequence')
        tt = ctx.v('CMB', f'{SQ}/start/{k}/t_s', 's', tag='LEAD', tag_ptr=f'{I}/sequence')
        ac = ctx.v('CMB', f'{SQ}/start/{k}/action', tag='LEAD', tag_ptr=f'{I}/sequence')
        rows.append([Cell(f'<b>{esc(ep.value)}</b>', [ep]), num_cell(tt, '.3f') if tt.value is not None else Cell('—', [tt]), tvtxt(ac, 1600)])
    o.append(dtable(['Epoch', 't [s]', 'Action'], rows, label_cols=0, widths=['12%', '8%', '80%'], cls='tight',
                    caption=f'Start and relight sequence (combustion.json {esc(ctx.src("CMB").version or "")} /igniter/sequence; times relative to E0 where the source states one).'))
    F = '/igniter_sequence_fields_v2p4c/v/fields'
    fl = ctx.raw('CMB', F, default=[]) or []
    rows = []
    for k, f in enumerate(fl):
        tv = ctx.v('CMB', f'{F}/{k}', f.get('unit', ''))
        val = tv.value
        vs = (', '.join(f'{x:g}' for x in val) if isinstance(val, list) and all(isinstance(x, (int, float)) for x in val) else
              (f'{val:g}' if isinstance(val, (int, float)) and not isinstance(val, bool) else str(val)))
        rows.append([Cell(f'<span class="mono small">{esc(f.get("id", ""))}</span>', []),
                     Cell(f'<span class="v">{esc(vs)}</span><span class="u">&#8239;{esc(f.get("unit", ""))}</span> {tv.pill()}{tv.ref()}', [tv]),
                     tvtxt(ctx.v('CMB', f'{F}/{k}/src', tag='DESIGN'), 160)])
    o.append(dtable(['Field', 'Value', 'Source (as written)'], rows, widths=['30%', '26%', '44%'], cls='tight',
                    caption='One field per value (combustion.json /igniter_sequence_fields_v2p4c, the generated-table input for Electronics); the pill is each field\'s own tag.'))
    rows = []
    for lab, key in (('ARM preconditions', 'arm_preconditions'), ('Relight', 'relight'), ('Shutdown', 'shutdown'), ('Abort if no ignition', 'abort_if_no_ignition')):
        items = ctx.raw('CMB', f'{SQ}/{key}', default=[]) or []
        for j, _ in enumerate(items):
            tv = ctx.v('CMB', f'{SQ}/{key}/{j}', tag='LEAD', tag_ptr=f'{I}/sequence')
            cell = tvtxt(tv, 700)
            if key == 'arm_preconditions' and isinstance(tv.value, str) and 'P_torch 0-70 bar class' in tv.value:
                # the P_torch clause vs lead 264 (4) (lead 2026-10-21 13:47Z, REV-DS-1 D1-04: pointer at T1427, C-14)
                p4 = D['cl'].clip(264, 4, 'P_torch (J901', 'same part as P_mid (ENG-BL-08) and C1.')
                cell = cat(tvtxt(tv), gnote(f'P_torch: lead 264 (4){p4.ref()} selects the C1-family Kulite XTL-190SM-2000A; the "0-70 bar class" '
                                            'and "or isolation" wording is superseded (isolation is rejected); the threshold re-base is OPEN: '
                                            'contradiction register C-14', [p4]))
                D.setdefault('c14_sides', []).append((f'combustion.json /igniter/sequence ARM precondition {j + 1} (P_torch clause)', tv))
            rows.append([lab if j == 0 else '', cell])
    o.append(dtable(['Phase', 'Rule'], rows, widths=['18%', '82%'], cls='tight'))
    o.append(note_box('<b>Stand safing after a no-light.</b> ' + tvtxt(ctx.v('CMB', '/stand_safing_v2p4a', tag_ptr='/stand_safing_v2p4a'), 500).html, 'info'))

    o.append(doc.h(2, '7.5 Relight purge (decided schedule and conditions)'))
    P = '/purge_decision_v2p4c/v'
    rows = [['Commit rule', tvtxt(ctx.v('CMB', '/purge_commit_rule_v2p4b/v/rule', tag_ptr='/purge_commit_rule_v2p4b'), 400)],
            ['Decision', tvtxt(ctx.v('CMB', f'{P}/decision', tag_ptr='/purge_decision_v2p4c'), 400)],
            ['Scheduled flow / both-open overlap / both-open cap / flow at the cap',
             cat(ctx.v('CMB', f'{P}/flow_s', 's', tag_ptr='/purge_decision_v2p4c').h(), ' / ', ctx.v('CMB', f'{P}/both_open_overlap_s', 's', tag_ptr='/purge_decision_v2p4c').h(), ' / ',
                 ctx.v('CMB', f'{P}/cap_both_open_s', 's', tag_ptr='/purge_decision_v2p4c').h(), ' / ', ctx.v('CMB', f'{P}/flow_at_cap_s', 's', tag_ptr='/purge_decision_v2p4c').h())],
            ['Needed flow, unlined line (283.15 / 289.5 / 297.15 K)', tvtxt(ctx.v('CMB', f'{P}/needed_flow_unlined_s', 's', tag='DERIVED'))],
            ['Margins at 2.43 s, unlined', tvtxt(ctx.v('CMB', f'{P}/margins_at_2p43s_unlined_s', 's', tag='DERIVED'))],
            ['Vented N2O bound (law) at 2.43 s', tvtxt(ctx.v('CMB', f'{P}/vented_N2O_bound_law_g', 'g', tag='DERIVED'))],
            ['Vented N2O at Cd 0.80, fixed schedule', cat(tvtxt(ctx.v('CMB', f'{P}/vented_N2O_Cd0p80_fixed_schedule_g', 'g', tag='ESTIMATE')), '<br>',
                                                         tvtxt(ctx.v('CMB', f'{P}/vented_N2O_Cd0p80_tag', tag='ESTIMATE'), 300))],
            ['A1 reserve test (REV-GNC-7)', tvtxt(ctx.v('CMB', f'{P}/a1_reserve_test_REV_GNC_7', tag='DERIVED'), 500)],
            ['Condition (a), LEAD 256 (2)', tvtxt(ctx.v('CMB', f'{P}/conditions_LEAD_256_2/a', tag='LEAD'))],
            ['Condition (b), LEAD 256 (2)', tvtxt(ctx.v('CMB', f'{P}/conditions_LEAD_256_2/b', tag='LEAD'))],
            ['Condition (c), LEAD 256 (2)', tvtxt(ctx.v('CMB', f'{P}/conditions_LEAD_256_2/c', tag='LEAD'))],
            ['Condition (d), LEAD 257 (2)', tvtxt(ctx.v('CMB', f'{P}/condition_d_LEAD_257_2', tag='LEAD'), 1400)],
            ['Condition (d1), LEAD 258 (2)', tvtxt(ctx.v('CMB', f'{P}/conditions_LEAD_258_2/d1', tag='LEAD'), 600)],
            ['Condition (d2), LEAD 258 (2)', tvtxt(ctx.v('CMB', f'{P}/conditions_LEAD_258_2/d2', tag='LEAD'), 600)],
            ['PURGE command time (open)', tvtxt(ctx.v('CMB', f'{P}/PURGE_command_time', tag='DERIVED'), 400)],
            ['CF-4', tvtxt(ctx.v('CMB', f'{P}/CF4', tag='LEAD'), 500)],
            ['Electronics constants', cat(tvtxt(ctx.v('CMB', f'{P}/electronics', tag='DESIGN'), 500),
                                          *([gnote(f'implemented in electronics.json v4.1 as the purge FINAL calibration constants: ACCEPTED (REV-ELEC-4, line '
                                                   f'{D["ele"]["line"]}){D["ele"]["acc_tv"].ref()}; §10.6', [D['ele']['acc_tv']])] if D['ele']['promo'] else []))],
            ['Vented-mass reserve', tvtxt(ctx.v('CMB', f'{P}/reserve', tag='LEAD'), 500)]]
    o.append(dtable(['Item', 'Value'], rows, widths=['28%', '72%'], cls='tight',
                    caption='combustion.json /purge_decision_v2p4c (decided by LEAD 253 (7)(ii), final in 256 (2); conditions 256 (2), 257 (2), 258 (2)). '
                            'The v2.4b records were run with 2.5 s of flow (the analysed basis, more flow than decided).'))

    o.append(doc.h(2, '7.6 Abort set (Combustion matrix; firmware causes in §10.5)'))
    cm = '/abort_matrix_v2p4/v'
    rows = []
    for k in (ctx.raw('CMB', cm, default={}) or {}):
        if k.endswith('_superseded'):
            continue
        rows.append([Cell(f'<b>{esc(k)}</b>', []), tvtxt(ctx.v('CMB', ptr_join('abort_matrix_v2p4', 'v', k), tag_ptr='/abort_matrix_v2p4'), 700)])
    o.append(dtable(['ID', 'Combustion abort matrix (as published)'], rows, widths=['14%', '86%'], cls='tight',
                    caption=f'combustion.json /abort_matrix_v2p4 ({esc(str(ctx.raw("CMB", "/abort_matrix_v2p4/tag", default="")))}). '
                            + (f'The F4 PC_SENSOR HIGH abort (TB-state) and the flight J-FWD indication (JFWD_LS; Q_JFWD on the stand at B-DPC-1), routed to '
                               f'Electronics v2.12 by LEAD 258 (4), are implemented in electronics.json v4.1: <span class="ev ev-status">ACCEPTED (REV-ELEC-4, line '
                               f'{D["ele"]["line"]})</span>{D["ele"]["acc_tv"].ref()}; §10.' if D['ele']['promo'] else
                               'The F4 PC_SENSOR HIGH abort and the Q_JFWD logging are routed to Electronics v2.12 (LEAD 258 (4)): PENDING.')))
    o.append(note_box(f'<b>Abort action (firmware {fw_ver(D)}, SIL only).</b> {tvtxt(ctx.v("ELE", "/abort_matrix/actions", tag="LEAD"), 600).html}', 'info'))

    o.append(doc.h(2, '7.7 FA-1 hard start: rulings of record'))
    Z = '/z3_jfwd_rulings_v2p4d/v'
    rows = [subrow('Z3 v2 (FA-1 class; LEAD 258 (3))', 2)]
    rows += [[esc(k.replace('_', ' ')), tvtxt(ctx.v('CMB', f'{Z}/Z3_v2/{k}', tag_ptr='/z3_jfwd_rulings_v2p4d'), 800)] for k in ('decision', 'grid', 'flight', 'not_adopted')]
    rows.append(subrow('J-FWD replace rule on Q_JFWD (LEAD 258 (3))', 2))
    rows += [[esc(k.replace('_', ' ')), tvtxt(ctx.v('CMB', f'{Z}/jfwd_replace_rule/{k}', tag_ptr='/z3_jfwd_rulings_v2p4d'), 800)]
             for k in ('decision', 'grid', 'why', 'normal_lights', 'measured_traces', 'basis', 'band', 'replaces', 'electronics')]
    rows.append(subrow('Open before flight acceptance (LEAD 258 (3))', 2))
    ob = ctx.raw('CMB', f'{Z}/open_before_flight_acceptance', default=[]) or []
    rows += [[f'open item {j + 1}', tvtxt(ctx.v('CMB', f'{Z}/open_before_flight_acceptance/{j}', tag='TO-VERIFY'), 400)] for j in range(len(ob))]
    rows.append(subrow('Torch passage pressure and the J-FWD rows', 2))
    rows.append(['P_torch design case (FA1S)', tvtxt(ctx.v('CMB', '/fa1_p_torch_v2p4c/v/design_case', tag='LEAD'), 600)])
    rows.append(['Mechanical row (tap wall v3)', tvtxt(ctx.v('CMB', '/fa1_p_torch_v2p4c/v/mechanical_row', tag='CALC'), 600)])
    rows.append(['Grid statistics status', tvtxt(ctx.v('CMB', '/fa1_grid_statistics_v2p4c/v/status', tag='LEAD'), 400)])
    rows.append(['Combustion side', tvtxt(ctx.v('CMB', f'{Z}/combustion_side', tag_ptr='/z3_jfwd_rulings_v2p4d'), 500)])
    o.append(dtable(['Item', 'Value (quoted)'], rows, widths=['22%', '78%'], cls='tight',
                    caption='combustion.json /z3_jfwd_rulings_v2p4d and /fa1_p_torch_v2p4c. Grid counts are on an ASSUMED construct, not probabilities. '
                            'The FA-1 pressure spectrum is in §2.4; the J-FWD criterion rows in §9.5.'))

    o.append(doc.h(2, '7.8 Stability'))
    st = '/stability/points_initial_port'
    pts = ctx.raw('CMB', st + '/v', default={}) or {}
    rows = []
    for fr in pts:
        base = f'{st}/v/{fr}'
        cells = [Cell(f'{float(fr) * 100:.1f} %', [])]
        for key, unit, f in (('dP_over_Pc', '', '.2f'), ('GM_tau5ms', '', '.1f'), ('GM_tau10ms', '', '.1f'), ('f_1L_Hz', 'Hz', '.0f'),
                             ('f_Helmholtz_Hz', 'Hz', '.0f'), ('f_thermal_lag_Hz', 'Hz', '.2f')):
            cells.append(num_cell(ctx.v('CMB', f'{base}/{key}', unit, tag_ptr=st), f))
        rows.append(cells)
    o.append(dtable(['Throttle', 'dP/Pc', 'Chug gain margin, 5 ms', 'Chug gain margin, 10 ms', '1L acoustic', 'Helmholtz', 'Thermal lag'], rows,
                    caption='Stability indicators at the initial port (SIM).'))
    o.append(note_box(tvtxt(ctx.v('CMB', '/stability/criteria', tag='DERIVED')).html + '<br>' + tvtxt(ctx.v('CMB', '/stability/hybrid_LF_note', tag='TO-VERIFY')).html, 'info'))

    o.append(doc.h(2, '7.9 Test specifications: CF-4 and T1-T4'))
    rows = [['CF-4 claim', tvtxt(ctx.v('CMB', '/cf4_gate/v/claim', tag='LEAD', tag_ptr='/cf4_gate'))],
            ['CF-4 specification', tvtxt(ctx.v('CMB', '/cf4_gate/spec_version', tag='DESIGN'))]]
    pcs = ctx.raw('CMB', '/cf4_gate/v/pass_criteria', default=[]) or []
    for k, _ in enumerate(pcs):
        rows.append([f'CF-4 pass criterion {k + 1}', tvtxt(ctx.v('CMB', f'/cf4_gate/v/pass_criteria/{k}', tag='LEAD', tag_ptr='/cf4_gate'), 600)])
    rows.append(['T1-T4 law rule', tvtxt(ctx.v('CMB', '/t1t4_law_v2/v/rule', tag_ptr='/t1t4_law_v2'), 400)])
    rows.append(['T1-T4 specification', tvtxt(md_heading(ctx, 'T14', 'T1-T4', 'DESIGN', tag_raw='document heading'), 200)])
    rows.append(['T4 duration (N-07) and re-size', tvtxt(ctx.v('CMB', '/t4_duration_note_v2p4c/v/status', tag='LEAD'), 900)])
    rows.append(['T4 decision (CHANGELOG 261 (2))', cat(tvtxt(cl.item(261, 2), 900), gnote('the relight length of 261 (2) is superseded by 264 (5), next row; '
                                                                                          'contradiction register C-15'))])
    # the 264 (5) statement (REV-DS-1 D1-10; lead 2026-10-21 13:47Z): what T4 demonstrates
    i5 = cl.item(264, 5)
    t4d = cl.clip(264, 5, 'T4 then demonstrates', 'say so.')
    rows.append(['T4 relight (CHANGELOG 264 (5), N-07, OI-T4-RESIZE)',
                 cat(tvtxt(i5), Cell(f'<div class="dec"><b>What T4 demonstrates (264 (5)):</b> {tvtxt(t4d).html}</div>', [t4d]),
                     gnote('the length is OPEN: Combustion sets it in the T4 re-run with Mechanical\'s soak-back'
                           + (f'; T4 is a stand relight and waits for v2.13 ({D["ele"]["line"]} (6)){D["ele"]["cons_tv"].ref()}' if D['ele']['promo'] else '')
                           + '; contradiction register C-15', [D['ele']['cons_tv']] if D['ele']['promo'] else []))])
    rows.append(['Test budgets', tvtxt(ctx.v('CMB', '/test_budgets_v2p4b', tag_ptr='/test_budgets_v2p4b'), 500)])
    o.append(dtable(['Item', 'Value (quoted)'], rows, widths=['24%', '76%'], cls='tight',
                    caption='Physical tests are run by the founders; none has been run. The T4 rows of T1-T4 v3.2 stay the DC-D computation [SIM] until Combustion re-runs them (OPEN).'))
    return '\n'.join(o)

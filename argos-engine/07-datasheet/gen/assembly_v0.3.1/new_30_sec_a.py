# ---------------------------------------------------------------------------------------------
# sections 1-3 (v0.3.0): identification, key performance, throttle and TVC
# ---------------------------------------------------------------------------------------------
EV_DOC = [('SIM', 'model run (CFD, FE, Monte Carlo, quasi-1D, CEA, SIL)'), ('CALC', 'hand calculation on model loads or standard geometry'),
          ('DERIVED', 'computed from other traced values (by a specialist, a reviewer or this generator)'),
          ('ASSUMED', 'an input adopted without a measurement or a source'), ('DATASHEET', 'maker data'), ('LITERATURE', 'published data, cited'),
          ('AS RECALLED', 'a value quoted from memory by its author; to be sourced'), ('TO-VERIFY', 'needed from, or to be confirmed by, the named owner'),
          ('MISSING', 'not available; never estimated by the generator'), ('ESTIMATE', 'an estimate named as such by its source'),
          ('DECIDED', 'a design value, decided limit or requirement: chosen, not measured or computed; where the source gives a basis, that basis '
                      'and its tag are shown beside it (source class: design value, lead decision line N, or requirement)'),
          ('REF', 'a reference or provenance text (a source, a review id, a "no number changed" statement): it carries no value and no pill')]
EV_STATUS_DOC = [('PENDING', 'an input that has not landed (never assumed)'), ('SUPERSEDED', 'withdrawn by a newer decision, shown only as history'),
                 ('TO-DEFINE', 'not yet defined by its owner (the value is MISSING)')]


def src_tv(ctx, sid):
    s = ctx.src(sid)
    return TV(ctx, f'{s.version or "–"} · sha256/16 {s.sha16 or "MISSING"}', '', 'DERIVED', f'generator: version and sha256/16 of source {sid} at this build',
              sid, '(file)', note=os.path.basename(s.path))


def plot_pressure_ladder(a, items):
    """items: [(label, bar value or (lo, hi), colour, note[, unit])] horizontal ladder on a log scale; each label carries the unit of its
    source ('bar abs' where the source states it, else 'bar'; REV-DS-1 D1-08)."""
    plt = mpl_setup()
    n = len(items)
    fig, ax = plt.subplots(figsize=(6.9, 0.2 * n + 0.75))
    for i, it in enumerate(items):
        lab, v, c, note = it[:4]
        un = it[4] if len(it) > 4 else 'bar'
        y = n - 1 - i
        if v is None:
            ax.text(1.05, y, f'{lab}: MISSING', va='center', fontsize=6, color=C_BAD)
            continue
        if isinstance(v, (tuple, list)):
            ax.barh(y, v[1] - v[0], left=v[0], height=0.6, color=c, alpha=0.85)
            ax.text(v[1] * 1.03, y, f'{v[0]:g}–{v[1]:g} {un}  {note}', va='center', fontsize=5.8)
        else:
            ax.barh(y, v, height=0.6, color=c, alpha=0.85)
            ax.text(v * 1.03, y, f'{v:g} {un}  {note}', va='center', fontsize=5.8)
    ax.set_yticks(range(n))
    ax.set_yticklabels([it[0] for it in items][::-1], fontsize=6.2)
    ax.set_xscale('log')
    ax.set_xlim(1, 1200)
    ax.set_xlabel('pressure [bar] (log scale; bar abs where the source states it)')
    ax.grid(axis='y', visible=False)
    fig.tight_layout()
    return save_plot(fig, a, 'plot_pressure_ladder')


def plot_fa1_spectrum(a, T, series, fa1s, bands):
    plt = mpl_setup()
    fig, ax = plt.subplots(figsize=(6.9, 2.9))
    for lab, ys, c, ls in series:
        ax.plot(T, ys, color=c, lw=1.0, ls=ls, label=lab)
    if fa1s is not None:
        ax.axhline(fa1s, color=C_BAD, lw=0.9, ls='--', label=f'FA1S {fa1s:g} bar abs (design case)')
    for (t0, t1, v) in bands:
        if v is not None:
            ax.plot([t0, t1], [v, v], color=C_OK, lw=1.6, solid_capstyle='butt')
    ax.plot([], [], color=C_OK, lw=1.6, label='decided band values (LEAD 230 (2))')
    ax.set_xscale('log')
    ax.set_xlabel('SDOF period T [ms]')
    ax.set_ylabel('equivalent static pressure [bar abs]')
    ax.set_xlim(0.02, 50)
    ax.legend(fontsize=6, loc='lower center', ncol=2)
    fig.tight_layout()
    return save_plot(fig, a, 'plot_fa1_spectrum')


def plot_throttle(a, pts):
    """pts: list of dicts fraction, F, Pc_bar, Isp, OF."""
    plt = mpl_setup()
    fig, axs = plt.subplots(1, 3, figsize=(6.9, 2.2))
    fr = [p['fraction'] * 100 for p in pts]
    axs[0].plot(fr, [p['F'] for p in pts], 'o-', color=C_ACC, ms=3, lw=1)
    axs[0].set_xlabel('throttle [%]')
    axs[0].set_ylabel('thrust [N] (SL)')
    axs[1].plot([p['F'] for p in pts], [p['Pc_bar'] for p in pts], 'o-', color=C_ACC2, ms=3, lw=1)
    axs[1].set_xlabel('thrust [N]')
    axs[1].set_ylabel('Pc [bar abs]')
    axs[2].plot([p['F'] for p in pts], [p['Isp'] for p in pts], 'o-', color=C_WARN, ms=3, lw=1)
    axs[2].set_xlabel('thrust [N]')
    axs[2].set_ylabel('Isp SL [s]')
    for ax in axs:
        ax.tick_params(labelsize=6)
    fig.tight_layout()
    return save_plot(fig, a, 'plot_throttle')


def sec_identification(ctx, doc, a, D):
    o = [doc.h(1, '1 Identification')]
    cl = D['cl']
    o.append(note_box(f'<b class="stmt">{esc(PAGE_STATEMENT)}.</b> This datasheet is generated from the engine programme hub by '
                      f'gen/{GEN_NAME} {GEN_VERSION}. Every value in a data column is a traced value (T###, Appendix A) with its evidence class. '
                      'No value is MEASURED: the engine has not been built or fired. Missing data are shown as MISSING, TO-DEFINE or PENDING and never '
                      'estimated here.', 'warn'))
    o.append(doc.h(2, '1.1 Document and configuration'))
    cfg = [('CAD set (FINAL v3.5.2)', 'SET'), ('CAD manifest', 'CADMAN'), ('Assembly GLB (renders)', 'GLB'), ('Bill of materials', 'BOM'),
           ('Mass properties', 'MP'), ('Combustion interface', 'CMB'), ('Combustion datasheet inputs', 'DSIC'), ('Mechanical interface', 'MEC'),
           ('Mechanical 04-fea/v352 manifest', 'MMAN'), ('GNC interface', 'GNC'), ('GNC datasheet inputs', 'DSIG'), ('Electronics interface', 'ELE'),
           ('FEA3D v3.5.2 report', 'F3D'), ('Margin matrix of record (rows v8)', 'MMX'), ('Decision log', 'CL'), ('Review register', 'SUP'),
           ('Requirements', 'REQ'),
           ('Airframe ICD (out of the finish scope, CHANGELOG 222; no value is taken from it)', 'ICD')]
    rows = [[lab, Cell(f'<span class="mono small">{esc(src_tv(ctx, sid).value)}</span>{src_tv(ctx, sid).ref()}', [src_tv(ctx, sid)])] for lab, sid in cfg]
    rows.insert(1, ['CAD set status', tvtxt(ctx.v('SET', '/status', tag='DESIGN'), 520)])
    o.append(dtable(['Item', 'Version · sha256/16 (this build)'], rows, widths=['32%', '68%'],
                    caption=f'{esc(DOC_ID)} {esc(a.rev)}, CAD {esc(a.cad_version)}. Full source list with paths in §15.2.'))
    o.append(doc.h(2, '1.2 What changed since rev0'))
    r0 = 'REV0S'
    rows = []
    for lab, sid in (('CAD', None), ('Combustion interface', 'CMB'), ('Mechanical interface', 'MEC'), ('GNC interface', 'GNC'),
                     ('Electronics interface', 'ELE'), ('Decision log', 'CL')):
        if sid is None:
            old = ctx.v(r0, '/cad_version', tag='DERIVED', note='rev0 sources.json')
            new = TV(ctx, a.cad_version, '', 'DESIGN', 'CAD version of this build (render manifest and CAD folder)', 'RMAN', '/cad_version')
        else:
            old = ctx.v(r0, f'/sources/{sid}/version', tag='DERIVED', note='rev0 sources.json')
            new = TV(ctx, ctx.src(sid).version, '', 'DERIVED', f'version of source {sid} at this build', sid, '(file version)')
        rows.append([lab, num_cell(old), num_cell(new)])
    rows.append(['Parts changed vs v3.5.1', Cell('–', []), tvtxt(ctx.v('SET', '/changed_parts_vs_v3.5.1', tag='DESIGN'))])
    rows.append(['Mass change and the GNC trigger', Cell('–', []), tvtxt(ctx.v('MEC', '/gimballed_mass_properties_v352/delta_vs_v3.5.1/gnc_trigger/verdict', tag='DERIVED'), 500)])
    e11 = cl.item(258, 1)
    w0 = rx_text(ctx, e11, r'rev0 datasheet row 8 window (\d+)-(\d+) is withdrawn', 'N m/rad', tag='DERIVED', group=2,
                 note='upper end of the rev0 window (DERIVED on CAD v3.5.1, withdrawn by line 258 (1))')
    rows.append(['GNC row 8: servo output stiffness K_s (filed under ENG-11): upper end of the design-to window',
                 Cell(f'{w0.h(".0f")} <span class="ev ev-status">SUPERSEDED</span>', [w0]), eng11_cell(ctx, D)])
    rows.append(['Case-TC limits', Cell('–', []), tvtxt(cl.part(257, '423.15'), 500)])
    rows.append(['3D FEA of the assembled engine', Cell('–', []), tvtxt(md_find(ctx, 'F3D', 'REPORT FEA3D v3.5.2', {0: 'Status'}, 1, ev='DERIVED',
                                                                                 tag_raw='FEA3D-2 report header'), 300)])
    o.append(dtable(['Item', 'rev0 (2026-10-13)', 'rev1 (this build)'], rows, widths=['24%', '24%', '52%'], cls='tight',
                    caption='Rev0 values from the rev0 sources.json (07-datasheet/out/sources.json, kept); rev1 values from this build.'))
    o.append(doc.h(2, '1.3 Evidence classes'))
    o.append(table(['Class', 'Meaning'], [[(ev_pill(k) if k != 'REF' else '<b>REF</b>'), esc(v)] for k, v in EV_DOC]
                   + [[f'<span class="ev ev-status">{esc(k)}</span>', esc(v)] for k, v in EV_STATUS_DOC], cls='dt tight', widths=['16%', '84%']))
    o.append('<p class="small">Every number carries one of the ten evidence tags (SIM, CALC, DERIVED, ASSUMED, DATASHEET, LITERATURE, AS RECALLED, '
             'TO-VERIFY, MISSING, ESTIMATE) or the source-class pill DECIDED. The tag comes from the source tag or the quoted text; where neither '
             'gives one, the trace names the class set at the call site. This generator sets no default class: a value without a class is counted '
             'as UNTAGGED in qa_report. A lead line that quotes a SIM, DERIVED or CALC number keeps that number\'s tag; DECIDED applies only to the '
             'chosen value itself. PENDING, SUPERSEDED and TO-DEFINE are statuses shown beside the tag. A review verdict, a matching number or a '
             'passing check is not physical approval.</p>')
    o.append(doc.h(2, '1.4 At a glance: found negatives, open rulings and pending inputs'))
    nb = D.get('neg_by_class', {})
    o.append(note_box(f'<b>Found negatives.</b> {D["neg_total"].h()} margin-matrix cells are negative ('
                      + ', '.join(f'{esc(k)} {v.h(pill=False)}' for k, v in sorted(nb.items())) + '); every one is listed with its class and closure in §9.3. '
                      'Named: TC-04 (BT), the TC-01 J-FWD seat-line P+Q (DC; the R2-B select fit closes it only in the CALC band model), the J-FWD screw LCF '
                      '(C6 OPEN: single-use screws), the screw head fillet from zero (§9.4). The mesh convergence of the seat-line P+Q is not shown (§9.1.1).', 'neg'))
    rows = []
    promo = D.get('ele', {}).get('promo')
    for lab, tv in D['pending']:
        rows.append([esc(lab), tvtxt(tv) if promo else tvtxt(tv, 600)])
    o.append(dtable(['Pending input', 'Status (quoted)'], rows, widths=['34%', '66%'], cls='tight',
                    caption=('Inputs still pending at this build, each quoted in full (REV-DS-1 D1-06). Where a value waits for one of them it is marked '
                             f'at the value: SUSPENDED UNTIL v2.13 ({D["ele"]["line"]} (6)) for the option (b) values; OPEN for the T4 relight length (§7.9).'
                             if promo else 'Inputs still pending at this build; their values are shown as PENDING (REVIEW) where used.')))
    o.append(doc.h(2, '1.5 Recent lead decisions'))
    decs = cl.decisions('lead', last=a.decisions)
    rows = [[f'L{d["n"]}', esc(d.get('date') or ''), tvtxt(cl.whole(d['n'], maxlen=900))] for d in decs]
    o.append(dtable(['Line', 'Date', 'Decision text (first 900 characters; full line in the CHANGELOG)'], rows, label_cols=2,
                    widths=['6%', '10%', '84%'], cls='tight', caption=f'The last {len(decs)} lead decision lines of the CHANGELOG ({esc(src_label(ctx, "CL"))}).'))
    return '\n'.join(o)


def sec_performance(ctx, doc, a, D):
    o = [doc.h(1, '2 Key performance')]
    o.append(doc.h(2, '2.1 Combustion datasheet inputs'))
    allr = md_rows_all(ctx.src('DSIC').text or '', None)
    rows = []
    for ln, r in allr[1:]:
        if len(r) < 5:
            continue
        item = re.sub(r'\*\*', '', r[0]).strip()
        tag = r[3].strip()
        ev = normalise_tag(tag.split(';')[0].split('(')[0])
        c2t = md_cell_ln(ctx, 'DSIC', ln, r, 2, ev, tag_raw=tag)
        c2 = tvtxt(c2t, 700)
        if item == 'Pc transducer proof' and isinstance(c2t.value, str) and 'P_torch 070BG' in c2t.value:
            # combustion-side P_torch text vs lead 264 (4) (lead 2026-10-21 13:47Z, REV-DS-1 D1-04, C-14)
            p4 = D['cl'].clip(264, 4, 'P_torch (J901', 'same part as P_mid (ENG-BL-08) and C1.')
            c2 = cat(c2, gnote(f'P_torch: lead 264 (4){p4.ref()} selects the C1-family Kulite XTL-190SM-2000A; this 070BG text is superseded; the threshold '
                               're-base is OPEN: contradiction register C-14', [p4]))
            D.setdefault('c14_sides', []).insert(0, ('combustion datasheet inputs, row "Pc transducer proof" (condition / basis)', c2t))
        rows.append([Cell(f'<b>{esc(item)}</b>', []), tvtxt(md_cell_ln(ctx, 'DSIC', ln, r, 1, ev, tag_raw=tag)),
                     c2, tvtxt(md_cell_ln(ctx, 'DSIC', ln, r, 4, 'REF', tag_raw='source column'), 300)])
    o.append(dtable(['Item', 'Value', 'Condition / basis', 'Source'], rows, cls='tight', widths=['13%', '37%', '34%', '16%'],
                    caption=f'Every row of 02-combustion/DATASHEET-INPUTS-COMBUSTION.md ({esc(src_label(ctx, "DSIC"))}), quoted; the pill is the row\'s tag.'))
    notes = [ln for ln in (ctx.src('DSIC').text or '').splitlines() if ln.startswith('- ')]
    L = (ctx.src('DSIC').text or '').splitlines()
    nrows = [[tvtxt(ctx.t('DSIC', f'notes line {L.index(n) + 1}', n[2:].strip(), 'DESIGN', tag_raw='datasheet inputs note'), 900)] for n in notes]
    o.append(dtable(['Notes of the combustion datasheet inputs (quoted)'], nrows, label_cols=0, widths=['100%'], cls='tight'))
    o.append(doc.h(2, '2.2 Throttle points (20 C tank, initial port)'))
    pts = ctx.raw('CMB', '/operating_points/throttle_points_20C_initial_port', default=[]) or []
    rows, plot_pts, refs = [], [], []
    for i, p in enumerate(pts):
        b = f'/operating_points/throttle_points_20C_initial_port/{i}'

        def g(k, unit='', conv=None):
            return ctx.v('CMB', f'{b}/{k}', unit, conv=conv, tag='SIM', tag_ptr='/operating_points/basis')
        F, Pc, OF, Isp = g('F_N', 'N'), g('Pc_Pa', 'bar', (1e-5, 0, 'Pa to bar')), g('OF'), g('Isp_SL_s', 's')
        mo, mf, lift, dpp = g('mdot_ox_kg_s', 'g/s', (1000, 0, 'kg/s to g/s')), g('mdot_fuel_kg_s', 'g/s', (1000, 0, 'kg/s to g/s')), \
            g('pintle_lift_m', 'mm', (1000, 0, 'm to mm')), g('dP_inj_over_Pc')
        fr = g('fraction')
        rows.append([num_cell(fr, '.3f'), num_cell(F, '.1f'), num_cell(Pc, '.2f'), num_cell(OF, '.2f'), num_cell(Isp, '.1f'),
                     num_cell(mo, '.1f'), num_cell(mf, '.2f'), num_cell(lift, '.3f'), num_cell(dpp, '.2f')])
        refs += [F.tid, Pc.tid, Isp.tid]
        if None not in (F.value, Pc.value, Isp.value, fr.value):
            plot_pts.append({'fraction': fr.value, 'F': F.value, 'Pc_bar': Pc.value, 'Isp': Isp.value})
    o.append(dtable(['Fraction', 'Thrust', 'Pc', 'O/F', 'Isp SL', 'N2O flow', 'ABS flow', 'Pintle lift', 'dP_inj / Pc'], rows, label_cols=0, cls='tight',
                    caption=f'combustion.json /operating_points/throttle_points_20C_initial_port; basis: {esc(clipw(str(ctx.raw("CMB", "/operating_points/basis", default="")), 300))}'))
    if plot_pts:
        o.append(fig_html(plot_throttle(a, plot_pts), 'Throttle points: thrust vs throttle fraction, chamber pressure and sea-level Isp vs thrust (SIM).', refs, 'wide'))
    o.append(doc.h(2, '2.3 Pressure ladder'))
    lim = '/operating_points/pressure_limits'
    cap = ctx.v('CMB', lim + '/normal_cap_Pa/v', 'bar', conv=(1e-5, 0, 'Pa to bar'), tag_ptr=lim + '/normal_cap_Pa')
    ab = ctx.v('CMB', lim + '/abort_Pa/v', 'bar', conv=(1e-5, 0, 'Pa to bar'), tag_ptr=lim + '/abort_Pa')
    meop = ctx.v('CMB', lim + '/chamber_MEOP_Pa/v', 'bar', conv=(1e-5, 0, 'Pa to bar'), tag_ptr=lim + '/chamber_MEOP_Pa')
    proof = ctx.v('CMB', lim + '/proof_Pa/v', 'bar', conv=(1e-5, 0, 'Pa to bar'), tag_ptr=lim + '/proof_Pa')
    mb = ctx.v('CMB', '/meop_basis_v2p4/v/basis_bar', 'bar', tag_ptr='/meop_basis_v2p4')
    bm = '/fa1_spectra_damped_v2p4b/v/head_all_band_maxima_bar_abs'
    bands = [(ctx.v('CMB', f'{bm}/{k}/zeta0', 'bar', tag='SIM', tag_ptr='/fa1_spectra_damped_v2p4b', note='undamped (zeta 0) band maximum, head, all cases'))
             for k in ('T_le_0p1ms', 'T_0p1_to_1ms', 'T_1_to_20ms', 'T_20_to_50ms')]
    for b_ in bands:
        b_.unit = 'bar abs'  # the source key is head_all_band_maxima_bar_abs (REV-DS-1 D1-08)
    fa1s = rx_text(ctx, ctx.v('CMB', '/fa1_p_torch_v2p4c/v/design_case', tag_ptr='/fa1_p_torch_v2p4c'), r'FA1S ([\d.]+) bar abs', 'bar abs')
    # 166.14 bar abs is DERIVED (1.1 x FA1S); the LEAD class of DSIC row 21 belongs to the rule, not to the number (lead 2026-10-21 13:24Z)
    dsic21 = md_find(ctx, 'DSIC', None, {0: 'Pc transducer proof'}, 1, ev='LEAD', tag_raw='LEAD (249 (4), 230 (2))')
    fproof = rx_text(ctx, dsic21, r'>= ([\d.]+) bar abs', 'bar abs', tag='DERIVED',
                     note='1.1 x FA1S; the rule is the lead\'s (249 (4)), the number is DERIVED')
    fk = rx_text(ctx, dsic21, r'\(([\d.]+) x FA1S [\d.]+\)', '', tag='LEAD', note='factor of the rule (249 (4))')
    req256 = D['cl'].clip(256, 5, 'R4-12 (070BG proof rating', 'state saturation and recovery)')
    req264 = D['cl'].clip(264, 4, 'P_torch (J901', 'same part as P_mid (ENG-BL-08) and C1.')
    c1 = rx_text(ctx, md_find(ctx, 'DSIC', None, {0: 'Pc transducer proof'}, 1, ev='DATASHEET', tag_raw='DATASHEET (C1 rating)'), r'XTL-190SM-2000A pick, ([\d.]+) bar abs', 'bar abs', tag='DATASHEET')
    items = [('Software Pc cap (normal)', cap.value, C_ACC, cap.ev), ('ECU over-pressure abort', ab.value, C_WARN, ab.ev),
             ('MEOP basis (late light, 24 C interlock)', mb.value, C_GREY, mb.ev), ('Chamber MEOP', meop.value, C_BAD, meop.ev),
             ('Proof pressure', proof.value, C_BAD, proof.ev),
             ('FA-1 band, T <= 0.1 ms', bands[0].value, C_ACC2, bands[0].ev), ('FA-1 band, 0.1-1 ms', bands[1].value, C_ACC2, bands[1].ev),
             ('FA-1 band, 1-20 ms', bands[2].value, C_ACC2, bands[2].ev), ('FA1S design case (gas-filled passages)', fa1s.value, C_BAD, fa1s.ev),
             ('Transducer proof (minimum)', fproof.value, C_OK, fproof.ev), ('C1 Kulite rating (proof, maker 1.5x rule)', c1.value, C_OK, c1.ev)]
    NS = 'not stated in the source (bar)'
    bas = {id(cap): f'{NS}; combustion.json pressure_limits in Pa', id(ab): f'{NS}; combustion.json pressure_limits in Pa',
           id(mb): f'{NS}; combustion.json meop_basis_v2p4 basis_bar', id(meop): f'{NS}; combustion.json pressure_limits in Pa',
           id(proof): f'{NS}; combustion.json pressure_limits in Pa'}
    for b_ in bands:
        bas[id(b_)] = 'bar abs: combustion.json key head_all_band_maxima_bar_abs'
    bas[id(fa1s)] = 'bar abs: combustion.json fa1_p_torch_v2p4c ("FA1S ... bar abs")'
    bas[id(fproof)] = 'bar abs: DATASHEET-INPUTS-COMBUSTION.md row "Pc transducer proof" (">= ... bar abs")'
    bas[id(c1)] = 'bar abs: DATASHEET-INPUTS-COMBUSTION.md row "Pc transducer proof" (C1 rating "... bar abs")'
    tvl = [cap, ab, mb, meop, proof, bands[0], bands[1], bands[2], fa1s, fproof, c1]
    rows = [[lab, num_cell(tv), Cell(f'<span class="small">{esc(bas[id(tv)])}</span>', [tv])] for lab, tv in zip([i[0] for i in items], tvl)]
    items = [it + (tv.unit or 'bar',) for it, tv in zip(items, tvl)]
    # the transducer-proof row carries its derivation and the decisions that require it (lead 2026-10-21 13:24Z)
    k_fp = [i[0] for i in items].index('Transducer proof (minimum)')
    rows[k_fp][1] = Cell(f'{fproof.h()} = {fk.h("g", unit=False)} × FA1S {fa1s.h()}'
                         f'<div class="small">Required of the flight Pc transducer and of P_torch: CHANGELOG 256 (5), R4-12 {req256.pill()}{req256.ref()}, '
                         f'and 264 (4) {req264.pill()}{req264.ref()}</div>', [fproof, fk, fa1s, req256, req264])
    o.append(dtable(['Pressure level', 'Value', 'Basis of the unit (bar or bar abs)'], rows, widths=['40%', '34%', '26%'], cls='tight',
                    caption='Each value at the precision of its source, with the unit its source states: bar abs where the source says so; '
                            'otherwise bar, with "not stated in the source" (REV-DS-1 D1-08).'))
    o.append(fig_html(plot_pressure_ladder(a, [(i[0], i[1], i[2], i[3], i[4]) for i in items]),
                      'Pressure ladder (bar, log scale; bar abs where the source states it, see the table), each level with its class: limits (DECIDED, lead decisions), the MEOP basis (SIM), FA-1 '
                      'equivalent-static band maxima (SIM on ASSUMED inputs; the decided band values of line 230 (2) are rounded up from these), the FA1S '
                      'design case (DERIVED) and the transducer ratings.',
                      [t.tid for t in (cap, ab, mb, meop, proof, fa1s, fproof, c1)] + [b.tid for b in bands], 'wide'))
    o.append(doc.h(2, '2.4 FA-1 hard start: equivalent static pressure spectrum'))
    sp = ctx.src('FA1SP')
    T, cols = [], {}
    if sp.text:
        lines = [l for l in sp.text.splitlines() if l.strip()]
        hdr = lines[0].split(',')
        want = ['head|all|zeta0', 'head|all|zeta0.02', 'head|all|zeta0.05', 'head|baseline|zeta0']
        idxs = {w: hdr.index(w) for w in want if w in hdr}
        for l in lines[1:]:
            c = l.split(',')
            T.append(float(c[0]))
            for w, j in idxs.items():
                cols.setdefault(w, []).append(float(c[j]))
    sptv = TV(ctx, f'{len(T)} periods, columns head|all|zeta0, zeta0.02, zeta0.05, head|baseline|zeta0', '', 'SIM', 'SIM histories (ASSUMED inputs); DERIVED spectra',
              'FA1SP', '(csv columns period_ms, head|all|zeta*, head|baseline|zeta0)', note='plotted as published')
    series = [('head, all cases, ζ 0', cols.get('head|all|zeta0', []), C_ACC, '-'), ('head, all cases, ζ 0.02', cols.get('head|all|zeta0.02', []), C_ACC2, '-'),
              ('head, all cases, ζ 0.05', cols.get('head|all|zeta0.05', []), C_GREY, '-'), ('head, baseline cases, ζ 0', cols.get('head|baseline|zeta0', []), C_WARN, ':')]
    series = [s for s in series if s[1]]
    bandseg = [(0.02, 0.1, 94), (0.1, 1, 121), (1, 20, 147), (20, 50, 94)]
    dec = rx_text(ctx, md_find(ctx, 'DSIC', None, {0: 'FA-1 hard start: structural load'}, 2, ev='LEAD', tag_raw='LEAD (230 (2))'),
                  r'band values ([\d]+) / ([\d]+) / ([\d]+) / ([\d]+) bar abs DECIDED', 'bar', tag='LEAD', group=1)
    dvals = []
    m = re.search(r'band values ([\d]+) / ([\d]+) / ([\d]+) / ([\d]+) bar abs DECIDED', str(md_find(ctx, 'DSIC', None, {0: 'FA-1 hard start: structural load'}, 2,
                                                                                                    ev='LEAD', tag_raw='LEAD (230 (2))').value))
    if m:
        dvals = [float(x) for x in m.groups()]
        bandseg = [(s[0], s[1], dvals[i]) for i, s in enumerate(bandseg)]
    else:
        bandseg = [(s[0], s[1], None) for s in bandseg]
    if T:
        o.append(fig_html(plot_fa1_spectrum(a, T, series, fa1s.value, bandseg),
                          f'FA-1 equivalent static pressure at the head vs SDOF period ({len(T)} periods, {min(T):g}-{max(T):g} ms, counted from the file), '
                          f'undamped and damped (damping ASSUMED); red: the FA1S design case, {esc(fa1s.num())} bar abs; green: the decided band '
                          'values for structural SDOF paths (line 230 (2)). SIM histories on ASSUMED inputs, DERIVED spectra (Combustion v2.4b data, '
                          'unchanged by the text-only v2.4c and v2.4d folds: table below).', [sptv.tid, fa1s.tid, dec.tid], 'wide'))
        o.append(dtable(['Currency check of the FA-1 spectrum data', 'Record'], fa1_currency_rows(ctx), widths=['30%', '70%'], cls='tight'))
    else:
        o.append(f'<p class="miss">FA-1 spectra file missing {sptv.ref()}</p>')
    return '\n'.join(o)


def sec_throttle_tvc(ctx, doc, a, D):
    o = [doc.h(1, '3 Throttle and thrust vector control')]
    cl = D['cl']
    o.append(doc.h(2, '3.1 Throttle'))
    rows = []
    for k in ('floor_requirement_25pct', 'floor_target_20pct', 'floor_stretch_12p5pct', 'thrust_ceiling_rule', 'chamber_fill_time_constant_s'):
        rows.append([esc(k.replace('_', ' ')), tvtxt(ctx.v('CMB', f'/operating_points/{k}', tag='SIM'), 500)])
    rows.append(['throttle architecture', tvtxt(ctx.v('CMB', '/decisions/throttle_architecture', tag='LEAD'), 500)])
    o.append(dtable(['Item', 'Value (combustion.json)'], rows, widths=['24%', '76%'], cls='tight'))
    o.append(doc.h(2, '3.2 Gimbal and TVC requirements (GNC v3.2 datasheet inputs)'))
    rows = []
    for key in ('6', '7', '8'):
        ln_r = [x for x in md_rows_all(ctx.src('DSIG').text or '', None) if x[1] and x[1][0].strip() == key]
        if not ln_r:
            rows.append([key, ctx.missing(f'DSIG row {key}')])
            continue
        ln, r = ln_r[0]
        tag = r[3].strip() if len(r) > 3 else None
        ev = normalise_tag(tag)
        val = eng11_cell(ctx, D) if key == '8' else tvtxt(md_cell_ln(ctx, 'DSIG', ln, r, 2, ev, tag_raw=tag, label=r[1].strip()))
        evb, trb = ev, tag
        if tag and re.search(r'\bfrom SIM\b', tag) and ev == 'REQ':
            # the basis cell states the MC results the requirement is set from: SIM (lead 2026-10-21 14:05Z, REV-DS-1 D1-07, T912)
            evb, trb = 'SIM', f'{tag} (class set at the call site: SIM: the basis cell states the GNC MC results; REV-DS-1 D1-07)'
        lab = r[1].strip()
        if key == '8':
            lab = 'GNC row 8: servo output stiffness K_s (filed under ENG-11; ENG-11 (REQ) is the gimbal axis stiffness, §3.3 and §12.5)'
        rows.append([Cell(f'<b>{esc(lab)}</b>', []), val,
                     tvtxt(md_cell_ln(ctx, 'DSIG', ln, r, 4, evb, tag_raw=trb, label=r[1].strip()), 600)])
    o.append(dtable(['Item', 'Value for the datasheet', 'Basis'], rows, widths=['14%', '50%', '36%'], cls='tight',
                    caption=f'01-systems-gnc/DATASHEET-INPUTS-GNC.md rows 6-8 ({esc(src_label(ctx, "DSIG"))}).'))
    o.append(note_box('<b>GNC row 8 (servo output stiffness K_s, filed under ENG-11) changed since rev0.</b> ' + inl(cl.item(258, 1))
                      + ' The rev0 window is SUPERSEDED and not used. ENG-11 (REQ), the gimbal axis stiffness of REQUIREMENTS.md line 62, is in §3.3 and §12.5.', 'warn'))
    o.append(doc.h(2, '3.3 Axis stiffness band and rocking modes (FEA3D, R3 poses)'))
    rr = '/range_over_posted_R3_poses'
    rows = []
    for key, lab in (('FE_coupled_alpha', 'FE, α'), ('FE_coupled_beta', 'FE, β'), ('k_s58_coupled_alpha', 'with servo k_s 58, α'),
                     ('k_s58_coupled_beta', 'with servo k_s 58, β'), ('k_s174_coupled_alpha', 'with servo k_s 174, α'), ('k_s174_coupled_beta', 'with servo k_s 174, β')):
        lo = ctx.v('KTAB', f'{rr}/{key}/min', 'N m/rad', tag='SIM' if key.startswith('FE') else 'DERIVED')
        hi = ctx.v('KTAB', f'{rr}/{key}/max', 'N m/rad', tag='SIM' if key.startswith('FE') else 'DERIVED')
        lp = ctx.v('KTAB', f'{rr}/{key}/min_pose', tag='DERIVED')
        hp = ctx.v('KTAB', f'{rr}/{key}/max_pose', tag='DERIVED')
        if key.startswith('FE_coupled_'):
            D.setdefault('ktab', {})[key.rsplit('_', 1)[1]] = (lo, hi)  # ENG-11 per axis (D1-13)
        rows.append([lab, cat(lo.h('.0f'), ' (', lp.h(pill=False), ') – ', hi.h('.0f'), ' (', hp.h(pill=False), ')')])
    o.append(dtable(['Axis stiffness K over the 17 R3 poses', 'min (pose) – max (pose)'], rows, widths=['40%', '60%'], cls='tight',
                    caption='Per-pose values in §9.7. Servo k_s ASSUMED (TO-VERIFY at B-TVC-1). The FE rows are ENG-11 (REQ), the gimbal axis stiffness, per axis.'))
    sp = eng11_spread(ctx, D)
    kt = D.get('ktab') or {}
    if 'beta' in kt and 'alpha' in kt:
        i7 = cl.item(188, 7)
        o.append(f'<p class="small"><b>ENG-11 (REQ) status on these FE values (REQUIREMENTS.md line 62):</b> the hard minimum ≥ {sp["hmin"].h()} holds '
                 f'(beta minimum {kt["beta"][0].h()}); the spread element (alpha / beta spread across poses ≤ ±{sp["lim"].h()}) is not met on beta: '
                 f'±{sp["beta"].h(".1f")} half-range over mid-range (alpha ±{sp["alpha"].h(".1f")}); OPEN under 188 (7){i7.ref()}: GNC robustness assessment, '
                 'then the lead amends the requirement or Mechanical stiffens (§12.5; open item 11b, §11.2).</p>')
    o.append(doc.h(2, '3.4 TVC actuation record (mechanical.json v2.1, not re-derived for v3.5.2)'))
    rows = []
    CLS34 = {'ENG-07_rate_status': ('CALC', 'CALC / DERIVED, with SIM for the P value it quotes'),
             'ENG-11_status': ('SIM', 'SIM / DERIVED')}  # lead 2026-10-21 14:05Z, REV-DS-1 D1-07 (T942, T944)
    for k in ('concept', 'gear_ratio_n', 'servo_angle_range_deg', 'rate_engine_dps_under_3.19Nm', 'ENG-07_rate_status', 'hinge_moment_design_Nm', 'ENG-11_status'):
        if k in CLS34:
            ev, why = CLS34[k]
            t = ctx.v('MEC', f'/tvc_actuation/{k}', tag=ev, note='v2.1 record; not_re_derived_v352')
            base = re.sub(r'\s*\(class set at the call site: [^)]*\)', '', t.tag_raw or '').strip()  # one call-site note, the D1-07 one
            t.tag_raw = f'{base} (class set at the call site: {why}; REV-DS-1 D1-07)'.strip()
            rows.append([esc(k.replace('_', ' ')), cat(tvtxt(t), gnote(f'class: {why}'))])
        else:
            rows.append([esc(k.replace('_', ' ')), tvtxt(ctx.v('MEC', f'/tvc_actuation/{k}', tag='DESIGN', note='v2.1 record; not_re_derived_v352'), 400)])
    for k in ('architecture', 'range_deg', 'mechanical_stop_deg', 'bearings'):
        rows.append([esc('gimbal ' + k.replace('_', ' ')), tvtxt(ctx.v('MEC', f'/gimbal/{k}', tag='DESIGN', note='v2.1 record; not_re_derived_v352'), 400)])
    o.append(dtable(['Item', 'Value (v2.1 record)'], rows, widths=['26%', '74%'], cls='tight',
                    caption='These v2.1 sections were not re-derived for v3.5.2 (mechanical.json not_re_derived_v352); where they conflict with a _v352 section, the _v352 section governs.'))
    return '\n'.join(o)


def eng11_cell(ctx, D):
    """ENG-11 as the lead requires it written (12:13Z item 7; line 258 (1)): design-to 100-110 N m/rad at the ASSUMED servo
    J 1.6e-3 kg m2, not robust across J. The numbers are traced to DSIG row 8; the J is ASSUMED."""
    if 'eng11' in D:
        return D['eng11']
    hit = [x for x in md_rows_all(ctx.src('DSIG').text or '', None) if x[1] and x[1][0].strip() == '8']
    if not hit:
        m = ctx.missing('DSIG row 8 (ENG-11)')
        D['eng11'] = Cell(m.h(), [m])
        return D['eng11']
    ln, r = hit[0]
    tag = r[3].strip() if len(r) > 3 else None
    row = md_cell_ln(ctx, 'DSIG', ln, r, 2, normalise_tag(tag), tag_raw=tag, label='ENG-11 servo output stiffness K_s')
    lo = rx_text(ctx, row, r'Design-to (\d+)-(\d+) N m/rad', 'N m/rad', group=1)
    hi = rx_text(ctx, row, r'Design-to (\d+)-(\d+) N m/rad', 'N m/rad', group=2)
    J = rx_text(ctx, row, r'servo J ([\d.]+e-\d+) kg m2', 'kg m²', tag='ASSUMED',
                note='the "nominal servo J" of DSIG row 8 is the ASSUMED value (lead 12:13Z item 7; CHANGELOG 258 (1), 262 (4))')
    rob = md_find_sentence(ctx, row, 'not robust')
    D['eng11'] = cat('design-to ', lo.h('.0f', unit=False), '–', hi.h('.0f'), ' at the ASSUMED servo J ', J.h('.1e'),
                     ', not robust across J: ', tvtxt(rob, 600))
    return D['eng11']


def md_find_sentence(ctx, tv, contains):
    """The sentence of an already traced text that contains a phrase (same source and key, sentence selector added)."""
    s = tv.value if isinstance(tv.value, str) else ''
    k = s.find(contains)
    if k < 0:
        ctx.issue('WARN', f'no sentence containing {contains!r} in {tv.sid}:{tv.ptr}')
        return ctx.missing(f'{tv.sid} sentence containing {contains}')
    starts = [0] + [m.end() for m in re.finditer(r'(?<=[.;:])\s+(?=[A-Z(*`])', s[:k])]
    m = re.compile(r'(?<=[A-Za-z0-9)\]`*"\'])[.;](?=\s+[A-Z(*`]|\s*$)').search(s, k + len(contains))
    txt = s[starts[-1]:(m.end() if m else len(s))].strip()
    return TV(ctx, txt, '', tv.ev if tv.ev != 'DECIDED' else tv.basis_kind, tv.tag_raw, tv.sid, f'{tv.ptr} [sentence containing "{contains}"]')


def fa1_currency_rows(ctx):
    """FA-1 spectrum data of record: the file named by combustion.json (same sha) and the text-only v2.4c / v2.4d folds
    (lead 12:13Z item 11)."""
    sp = ctx.src('FA1SP')
    rel = '02-combustion/data/v2p4b/fa1_pressure_spectra_published_v2p4b.csv'
    named = ctx.v('CMB', '/fa1_spectra_damped_v2p4b/v/files/' + rel.replace('~', '~0').replace('/', '~1'), tag='REF')
    chk = ctx.d(('same file: ' if named.value == sp.sha16 else 'DIFFERENT file: ') + f'combustion.json {ctx.src("CMB").version} names {rel} with '
                f'sha256/16 {named.value}; the file read here has {sp.sha16}', '', 'generator check: sha named by combustion.json vs the file read', [named])
    s17 = md_sentence(ctx, 'RCMB', '17. v2.4c', 'Text only', 'REF', tag_raw='combustion REPORT.md §17 (v2.4c) header paragraph')
    s18 = md_sentence(ctx, 'RCMB', '18. v2.4d', 'Text only', 'REF', tag_raw='combustion REPORT.md §18 (v2.4d) header paragraph')
    s183 = md_sentence(ctx, 'RCMB', '18.3 Not changed', 'FA-1 grid histories', 'REF', tag_raw='combustion REPORT.md §18.3')
    return [['File named by combustion.json', tvtxt(chk, 400)], ['v2.4c fold (REPORT §17)', tvtxt(s17, 300)],
            ['v2.4d fold (REPORT §18)', tvtxt(s18, 300)], ['FA-1 data after v2.4d (REPORT §18.3)', tvtxt(s183, 300)]]


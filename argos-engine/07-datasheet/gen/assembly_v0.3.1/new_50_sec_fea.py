# ---------------------------------------------------------------------------------------------
# section 9: structural analysis, 3D FEA of the assembled engine on CAD v3.5.2 (FEA3D-2) and the
# rows-v8 margin matrix; J-FWD joint rows; mounting data; stiffness and modes; F4 joints
# ---------------------------------------------------------------------------------------------
MX_GROUPS = [('Static, pressure and FA-1 cases', ['LC1', 'LC2', 'LC2F', 'FA1Q', 'FA1D', 'FA1U', 'FA1S', 'FA1T']),
             ('Landing, gimbal-stop and thermal cases', ['LC3 cold', 'LC3 hot bound', 'GS', 'TD', 'LC6 F2', 'F2 hot bound', 'LC6 soak']),
             ('Thermal-abort states, joints and the part minimum', ['TB70', 'TBS', 'J-FWD', 'J-FD01', 'J-FD09', 'min'])]
MX_TAG = 'margin matrix v3.5.2 on rows v8 (lead re-run; 234 (4) all-node rule; MS = allowable / (SF x stress) - 1)'
NUMRE = re.compile(r'[+\-−]?\d+\.\d+')


def mx_display(txt, fn, label):
    """Matrix cell text -> compact html: the 'y / u' pair and flags; a long parenthetical goes to a footnote."""
    t = txt.strip()
    if t in ('-', ''):
        return '–'
    main, note = t, None
    k = t.find('(')
    if k > 0:
        main, note = t[:k].rstrip(), t[k:]
    main = re.sub(r'(?<![\w.])-(?=\d)', '−', main)
    h = esc(main)
    if note and len(note) <= 18:
        h += f' <span class="small">{esc(note)}</span>'
    elif note:
        fn.append(f'{label}: {txt}')
        h += f'<sup>{len(fn)}</sup>'
    return h


def mx_numbers(txt):
    v = [float(x.replace('−', '-')) for x in NUMRE.findall(txt or '')[:2]]
    return v


def plot_min_margin(a, rows):
    """rows: [(part, value, col, cls)] lowest margin per part (bar chart, negatives red)."""
    plt = mpl_setup()
    n = len(rows)
    fig, ax = plt.subplots(figsize=(6.9, 0.165 * n + 0.75))
    cap = 2.0
    for i, (p, v, col, cls) in enumerate(rows):
        y = n - 1 - i
        if v is None:
            ax.text(0.01, y, 'MISSING', va='center', fontsize=5.8, color=C_BAD)
            continue
        vv = min(v, cap)
        c = C_BAD if v < 0 else (C_WARN if v < 0.05 else C_ACC)
        ax.barh(y, vv, height=0.66, color=c)
        lab = f'{v:+.3f}  {col}' + (f'  [{cls}]' if cls else '')
        if v > cap:
            ax.text(cap + 0.03, y, f"> {lab}", va='center', fontsize=5.6, color='#333')
        elif v < 0:
            ax.text(0.03, y, lab, va='center', fontsize=5.6, color='#8c1d24')
        else:
            ax.text(vv + 0.03, y, lab, va='center', fontsize=5.6, color='#333')
    ax.set_yticks(range(n))
    ax.set_yticklabels([r[0] for r in rows][::-1], fontsize=6.0)
    ax.axvline(0, color='#333', lw=0.7)
    ax.axvline(0.05, color=C_WARN, lw=0.6, ls=':')
    ax.set_xlim(-0.7, cap + 1.15)
    ax.set_xlabel('lowest margin of safety over every case (MS_y or MS_u, the lower); bars clipped at +2.0')
    ax.grid(axis='y', visible=False)
    fig.tight_layout()
    return save_plot(fig, a, 'plot_min_margin')


def mx_part_rows(ctx):
    rows = md_rows_where(ctx, 'MMXMD', 'FEA3D margin matrix v3.5.2')
    hdr = md_rows_all(ctx.src('MMXMD').text or '', 'FEA3D margin matrix v3.5.2')[0][1]
    return hdr, rows


def mx_json_row(ctx, part):
    for i, r in enumerate(ctx.raw('MMX', '/rows', default=[]) or []):
        if r.get('part') == part.split(' (')[0] or r.get('part') == part:
            return i, r
    return None, None


def mx_jfwd_tag(ctx, part, extra=''):
    """Tag text of a J-FWD matrix cell: the class of each governing entry as margin_matrix_v352.json gives it (REV-DS-1 D1-07:
    TC-01 governing[0] SOAK MS_y 'CALC / DERIVED', governing[1] FA1S MS_u 'CALC'); the pill is CALC."""
    _, jr = mx_json_row(ctx, part)
    g = (((jr or {}).get('cells') or {}).get('J-FWD') or {}).get('governing') or []
    gs = []
    for k, e in enumerate(g):
        ms = '; '.join(f'{m} {e.get(m):+.3f}' for m in ('MS_y', 'MS_u') if isinstance(e.get(m), (int, float)))
        gs.append(f'governing[{k}] {e.get("state")} ({ms}): {e.get("tag")}')
    return MX_TAG + ('; J-FWD cell classes (margin_matrix_v352.json): ' + ' | '.join(gs) if gs else '') + extra


def sec_fea_matrix(ctx, doc, a, D, o):
    hdr, rows = mx_part_rows(ctx)
    colidx = {c: j for j, c in enumerate(hdr)}
    o.append(doc.h(2, '9.2 Margin matrix: every part × every load case'))
    o.append(f'<p>{inl(md_line_starting(ctx, "MMXMD", "Cell = MS_y", "DERIVED", tag_raw=MX_TAG))}</p>')
    o.append(note_box('Read the matrix as found: a negative cell is a FOUND NEGATIVE of the model and is never shown as passing. '
                      'Cells are MS_y / MS_u (yield / ultimate; one value for brittle parts). Red cells are negative; amber cells are below +0.05. '
                      '"–" means the case is not evaluated for that part (§9.2.4). Classes and closures of every negative cell are in §9.3.', 'neg'))
    nmis = 0
    for gi, (gname, cols) in enumerate(MX_GROUPS):
        fn = []
        body = []
        for ln, r in rows:
            part = re.sub(r'\*\*', '', r[0]).strip()
            cells = [Cell(f'<b>{esc(part)}</b>', [])]
            ji, jr = mx_json_row(ctx, part)
            for c in cols:
                j = colidx.get(c)
                if j is None or j >= len(r):
                    cells.append(ctx.missing(f'matrix column {c}'))
                    continue
                txt = re.sub(r'\*\*', '', r[j]).strip()
                ev = 'DERIVED' if c == 'min' else ('CALC' if c == 'J-FWD' else 'SIM')
                tv = md_cell_ln(ctx, 'MMXMD', ln, r, j, ev, tag_raw=(mx_jfwd_tag(ctx, part) if c == 'J-FWD' else MX_TAG), label=part)
                html_ = mx_display(txt, fn, f'{part} {c}')
                if html_ == '–':
                    cells.append(Cell('–', [tv]))
                else:
                    cells.append(Cell(f'{html_}{tv.ref()}', [tv], cls=val_class(txt)))
                # generator cross-check of the md cell against the matrix JSON (same publication)
                if jr is not None and c != 'min' and txt not in ('-', '') and not txt.startswith('>'):
                    jv = ((jr.get('cells') or {}).get(c) or {}).get('value')
                    mv = mx_numbers(txt)
                    if isinstance(jv, list) and mv:
                        jn_ = [x for x in jv if isinstance(x, (int, float))]
                        if jn_ and abs(jn_[0] - mv[0]) > 0.0015:
                            nmis += 1
                            ctx.issue('WARN', f'matrix md vs json differ: {part} {c}: md {txt!r} json {jv}')
            body.append(cells)
        heads = ['Part'] + [esc(c) for c in cols]
        w0 = '13%'
        wc = f'{87 / len(cols):.1f}%'
        o.append(dtable(heads, body, cls='mx', widths=[w0] + [wc] * len(cols),
                        caption=f'Table 9.{gi + 1}: {esc(gname)} (MS_y / MS_u; flags r, a, c, p, s, w as defined in the matrix text above; MF / BT classes; '
                                f'source MMXMD {esc(src_label(ctx, "MMXMD"))}).'))
        if fn:
            o.append('<div class="fn">' + ''.join(f'<p><sup>{i + 1}</sup> {esc(t)}</p>' for i, t in enumerate(fn)) + '</div>')
    D['mx_mismatch'] = nmis
    # lowest margin per part (JSON min) chart
    prow, refs = [], []
    neg_parts = []
    for i, jr in enumerate(ctx.raw('MMX', '/rows', default=[]) or []):
        tv = ctx.v('MMX', f'/rows/{i}/min/0', tag='DERIVED', note='lowest cell of the part (matrix json min)')
        col = ctx.v('MMX', f'/rows/{i}/min/1', tag='DERIVED')
        refs += [tv.tid, col.tid]
        cls_ = ''
        cell = ((jr.get('cells') or {}).get(col.value) or {})
        if isinstance(cell, dict) and cell.get('class'):
            cls_ = cell.get('class')
        prow.append((jr.get('part'), tv.value, f'{col.value} {ctx.raw("MMX", f"/rows/{i}/min/2", default="")}', cls_))
        if tv.value is not None and tv.value < 0:
            neg_parts.append(jr.get('part'))
    src = plot_min_margin(a, prow)
    o.append(fig_html(src, 'Lowest margin of safety per part over every load case (the matrix "min" field; red = negative, amber = below +0.05; '
                           'class of the governing cell in brackets where the matrix gives one). Bars are clipped at +2.0. DERIVED from SIM / CALC cells.',
                      refs, 'wide'))
    D['neg_parts'] = neg_parts
    # columns not evaluated
    o.append(doc.h(3, '9.2.4 Cells shown "–" and why'))
    items = []
    for ln, r in []:
        pass
    L = (ctx.src('MMXMD').text or '').splitlines()
    on = False
    for i, ln in enumerate(L, 1):
        if ln.startswith('## '):
            on = ln.startswith("## Cells shown '-' and why")
            continue
        if on and ln.startswith('- '):
            items.append(ctx.t('MMXMD', f'§Cells shown "-" and why line {i}', ln[2:].strip(), 'DERIVED', tag_raw=MX_TAG))
    o.append(dtable(['Column', 'Why'], [[Cell(esc(re.sub(r'\*\*', '', it.value).split(':')[0]), []), tvtxt(it)] for it in items],
                    widths=['14%', '86%']))


def mx_negatives(ctx, D):
    """Negative-cell table of the matrix (computed once in prepare; section 1 and section 9 both use it)."""
    if 'neg_body' in D:
        return D['neg_body']
    rows = md_rows_where(ctx, 'MMXMD', 'Negative cells and their classes')
    body, by_cls = [], {}
    for ln, r in rows:
        part = re.sub(r'\*\*', '', r[0]).strip()
        jf = len(r) > 1 and re.sub(r'\*\*', '', r[1]).strip() == 'J-FWD'  # a J-FWD cell is CALC (REV-DS-1 D1-07)
        tg = mx_jfwd_tag(ctx, part, '; negative-cell table') if jf else MX_TAG + '; negative-cell table'
        tvs = [md_cell_ln(ctx, 'MMXMD', ln, r, j, ev, tag_raw=tg, label=part)
               for j, ev in ((1, 'SIM'), (2, 'CALC' if jf else 'SIM'), (3, 'CALC' if jf else 'SIM'), (4, 'DERIVED'), (5, 'DERIVED'), (6, 'REF'))]
        by_cls.setdefault(tvs[3].value, []).append(tvs[3])
        refc = tvtxt(tvs[5])
        if isinstance(tvs[5].value, str) and re.search(r'select-fit band APPLIES \(IN718 \[[\d.]+, [\d.]+\] mm', tvs[5].value):
            refc = cat(refc, r2b_sup_note(ctx, D))  # the line-240 band and its one re-size, superseded by R2-B (lead 2026-10-21 13:47Z, REV-DS-1 D1-01)
            D['neg_band_tv'] = tvs[5]  # a side of contradiction C-11
        body.append([Cell(f'<b>{esc(part)}</b>', []), tvtxt(tvs[0]), Cell(f'<b>{esc(tvs[1].value.replace("-", "−"))}</b>{tvs[1].ref()}', [tvs[1]], cls='neg'),
                     tvtxt(tvs[2], 120), Cell(f'<span class="neg-tag">{esc(tvs[3].value)}</span>{tvs[3].ref()}', [tvs[3]]), tvtxt(tvs[4], 260), refc])
    D['neg_total'] = ctx.d(len(body), '', 'count of rows of the matrix table "Negative cells and their classes"',
                           [c for row in body for c in row if isinstance(c, TV)])
    D['neg_by_class'] = {k: ctx.d(len(by_cls[k]), '', f'count of negative cells with class {k}', by_cls[k]) for k in sorted(by_cls)}
    D['neg_body'] = body
    return body


def sec_fea_negatives(ctx, doc, a, D, o):
    o.append(doc.h(2, '9.3 Found negatives: every negative cell, its class and its closure'))
    body = mx_negatives(ctx, D)
    ntot = D['neg_total']
    cnt = [cat(f'<b>{esc(k)}</b> ', t.h(pill=False)) for k, t in D['neg_by_class'].items()]
    cls_doc = {'BT': 'bad-tet node (mesh defect; lead 21:15:29Z (4))', 'MF': 'model fidelity (a named sub-model governs; lead 21:15:29Z (3))',
               'BR': 'brittle part (graphite), thermal', 'DC': 'design change route (J-FWD seat line)', 'TS-183': 'thermal stress, 183 (1) (c) LCF / (d) time at temperature',
               'TS-212': 'thermal stress, 212 (1) (d) time at temperature', 'CH': 'char layer against an ASSUMED strength'}
    o.append(f'<p>{ntot.h(pill=True)} cells of the matrix are negative. By class (REV-MECH-2 section 10 classes; class rules of CHANGELOG 234 (4)): '
             + ' · '.join(c.html for c in cnt) + '.</p>')
    o.append(dtable(['Part', 'Column', 'Cell y / u', 'Governing record', 'Class', 'Closure (what closes it)', 'Ref'], body, label_cols=1, cls='tight',
                    widths=['8%', '9%', '10%', '22%', '6%', '33%', '12%'],
                    caption='Every negative matrix cell (MMXMD, section "Negative cells and their classes"). The class decides the closure route; '
                            'no class turns a negative into a pass. Owners: see §9.10.'))
    o.append('<p class="small">Class key (matrix class rules): ' + '; '.join(f'<b>{esc(k)}</b> {esc(v)}' for k, v in cls_doc.items()) + '. '
             'The key is a reading aid written for this datasheet; the class of each cell is the traced value in the table.</p>')
    sec_fea_info_negatives(ctx, doc, a, D, o)


def sec_fea_info_negatives(ctx, doc, a, D, o):
    """Negative cells of the information columns (margin_matrix_v352.json /info_columns): shown as information, not governing
    (lead 2026-10-21 12:13Z item 13); a cell without a class is flagged."""
    info = ctx.raw('MMX', '/info_columns', default=[]) or []
    body, unc = [], []
    for i, r in enumerate(ctx.raw('MMX', '/rows', default=[]) or []):
        for c in info:
            cell = (r.get('cells') or {}).get(c)
            if not isinstance(cell, dict):
                continue
            v = cell.get('value')
            vals = [x for x in (v if isinstance(v, list) else [v]) if isinstance(x, (int, float)) and not isinstance(x, bool)]
            if not vals or min(vals) >= 0:
                continue
            b = ptr_join('rows', i, 'cells', c)
            ty = ctx.v('MMX', b + '/value/0', tag='SIM', note=f'{r.get("part")} {c}: y')
            u = v[1] if isinstance(v, list) and len(v) > 1 else None
            tu = ctx.v('MMX', b + '/value/1', tag='SIM', note=f'{r.get("part")} {c}: u') if u is not None else None
            cls = ctx.v('MMX', b + '/class', tag='DERIVED')
            clo = ctx.v('MMX', b + '/closure', tag='DERIVED')
            flag = cls.value in (None, 'UNCLASSIFIED')
            if flag:
                unc.append((r.get('part'), c, ty, cls, clo))
            yu = f'<b>{esc(fmt_num(ty.value, "+.3f").replace("-", "−"))}</b> / ' + (esc(fmt_num(tu.value, '+.3f').replace('-', '−')) if tu is not None else 'n/a')
            body.append([Cell(f'<b>{esc(r.get("part"))}</b>', []), Cell(esc(c), [ty]), Cell(f'{yu} {ty.pill()}{ty.ref()}' + (tu.ref() if tu is not None else ''), [ty] + ([tu] if tu else []), cls='neg'),
                         Cell((f'<span class="neg-tag">{esc(cls.value)}</span>' if flag else f'<b>{esc(cls.value)}</b>') + f' {cls.pill()}{cls.ref()}', [cls]), tvtxt(clo, 220)])
    D['info_neg_total'] = ctx.d(len(body), '', 'count of negative cells in the information columns of margin_matrix_v352.json', [c for row in body for c in row if isinstance(c, TV)])
    o.append(doc.h(3, '9.3.1 Negative cells in the information columns (information, not governing)'))
    o.append(f'<p>{D["info_neg_total"].h()} more cells are negative in the information columns ({esc(", ".join(info))}). They are shown as information: '
             'they do not govern and are not in the count above.'
             + (' <b>Flagged:</b> ' + '; '.join(f'{esc(p)} {esc(c)} {t.h(".3f")} has no class ({esc(cl_.value)}; closure: {esc(str(co.value))})'
                                                for p, c, t, cl_, co in unc) + '.' if unc else '') + '</p>')
    o.append(dtable(['Part', 'Column', 'Cell y / u', 'Class', 'Closure (quoted)'], body, label_cols=1, cls='tight', widths=['9%', '17%', '16%', '14%', '44%'],
                    caption='margin_matrix_v352.json (rows v8), information columns /info_columns; cell values and classes as published.'))


def sec_fea_named(ctx, doc, a, D, o):
    o.append(doc.h(2, '9.4 Named findings stated plainly'))
    hdr, rows = mx_part_rows(ctx)
    colidx = {c: j for j, c in enumerate(hdr)}

    def cell(part, col):
        for ln, r in rows:
            if re.sub(r'\*\*', '', r[0]).strip() == part:
                jf = col == 'J-FWD'  # a J-FWD cell is CALC, with the classes the matrix JSON gives (REV-DS-1 D1-07, T2265)
                return md_cell_ln(ctx, 'MMXMD', ln, r, colidx[col], 'CALC' if jf else 'SIM', tag_raw=(mx_jfwd_tag(ctx, part) if jf else MX_TAG), label=part)
        return ctx.missing(f'matrix {part} {col}')
    t1 = cell('TC-01', 'J-FWD')
    neg = [r for ln, r in md_rows_where(ctx, 'MMXMD', 'Negative cells and their classes') if r[0].strip() == 'TC-04']
    f3d10 = md_find(ctx, 'F3D', '13. Open items and owners', {0: '10'}, 2, ev='DERIVED', tag_raw='FEA3D-2 report §13 item 10')
    f3d10o = md_find(ctx, 'F3D', '13. Open items and owners', {0: '10'}, 3, ev='LEAD', tag_raw='FEA3D-2 report §13 item 10 owner')
    c96 = ctx.v('TXT5', '/item_C/C9_founder_texts_remap_v352/(6)_TC-02_select_fit_band_R2', tag='CALC')
    c6 = ctx.v('TXT5', '/item_C/C6_founder_action_list_related', tag='CALC')
    fil = ctx.v('FIL', '/verdict', tag='CALC', tag_ptr='/status')
    lcf_st = ctx.v('LCF', '/status_183_1c', tag='LEAD')
    k30 = ctx.v('LCF', '/governing/i_firing|Kf3.0|worst_of_histories|3750/MS_cycles_vs_50', tag='CALC')
    k30n = ctx.v('LCF', '/governing/i_firing|Kf3.0|worst_of_histories|3750/N_allow', tag='CALC')
    k30z = ctx.v('LCF', '/governing/ii_assembly_from_zero|Kf3.0|worst_of_histories|3750/MS_cycles_vs_50', tag='CALC')
    k30zn = ctx.v('LCF', '/governing/ii_assembly_from_zero|Kf3.0|worst_of_histories|3750/N_allow', tag='CALC')
    hw = cell('HW-101 (J-FWD)', 'J-FWD')
    rows_ = [
        ['TC-04 hot-bound cells (class BT)', cat(f3d10, Cell('', [])), tvtxt(f3d10o)],
        ['TC-01 J-FWD seat-line P+Q (class DC)',
         cat(Cell('Matrix cell (drawn fit): ', []), Cell(f'<b class="miss">{esc(t1.value)}</b>{t1.ref()}', [t1]),
             '<br>R2-B select fit and the band (Mechanical, CALC on SIM): ', tvtxt(c96, 1700),
             gnote('a build procedure: printed in full in §12.3 (R2-B select fit)', []) if len(_plain_text(c96.value or '')) > 1700 else Cell('', [])),
         Cell('Founder / shop: select-fit process with U TO-DEFINE (R2-B, CHANGELOG 254 (1)); Mechanical / FEA3D: convergence (not shown)', [c96])],
        ['J-FWD screw LCF at the thread root (C6 OPEN, single-use screws)',
         cat(lcf_st, '<br>Kf 3.0, per firing: N_allow ', k30n, ', MS ', k30, '; assembly from zero: N_allow ', k30zn, ', MS ', k30z,
             '<br>', tvtxt(c6, 2300),
             gnote('a founder action: printed in full in §12.3 (founder rule C6, mechanical.json /jfwd_v352/founder_rules/C6, the same text)', []) if len(_plain_text(c6.value or '')) > 2300 else Cell('', [])),
         Cell('Mechanical (closure path 2) / founder (path 3, qualification test TO-DEFINE); until then every J-FWD screw is single-use', [c6])],
        ['J-FWD screw head-to-shank fillet from zero', tvtxt(fil, 1400), Cell('Mechanical: Kt page and T-head Kt TO-SOURCE', [fil])],
        ['HW-101 IN718 screw, J-FWD cell (positive; rows v8)', cat(hw), Cell('Mechanical (rows v8, R6 basis)', [hw])],
    ]
    o.append(dtable(['Finding', 'What the sources say (quoted)', 'Owner / route'], rows_, widths=['17%', '63%', '20%'], cls='tight',
                    caption='Named findings of the brief, each quoted from its source. The TC-01 seat-line P+Q is a FOUND NEGATIVE at the drawn fit; '
                            'the R2-B select fit closes it only in the CALC-on-SIM band model and only if the select-fit process is carried out.'))
    if neg:
        o.append('<p class="small">TC-04 negative cells as listed in §9.3: ' + ', '.join(esc(f'{r[1]} {r[2]}') for r in neg) + '.</p>')


def jfwd_rows_table(ctx, pi, part, sel, title, cls='tight'):
    base = f'/rows/{pi}/cells/J-FWD/rows'
    rs = ctx.raw('MMX', base, default=[]) or []
    body = []
    for k, r in enumerate(rs):
        if not sel(r):
            continue
        p = f'{base}/{k}'
        st = ctx.v('MMX', p + '/state', tag='DERIVED')
        desc = ctx.v('MMX', p + '/row', tag_ptr=p + '/tag')
        y = ctx.v('MMX', p + '/MS_y', tag_ptr=p + '/tag') if 'MS_y' in r else None
        u = ctx.v('MMX', p + '/MS_u', tag_ptr=p + '/tag') if 'MS_u' in r else None
        pre = ctx.v('MMX', p + '/preload_N', 'N', tag_ptr=p + '/tag') if r.get('preload_N') is not None else None
        crit = ctx.v('MMX', p + '/criterion', tag='LEAD') if r.get('criterion') else None
        note = ctx.v('MMX', p + '/note', tag_ptr=p + '/tag') if r.get('note') else None

        def ms(tv):
            if tv is None:
                return Cell('–', [])
            if tv.value is None:
                return Cell('–', [tv])
            c = 'neg' if tv.value < 0 else ('thin' if tv.value < 0.05 else '')
            return Cell(f'{esc(fmt_num(tv.value, "+.3f"))}{tv.ref()}', [tv], cls=c)
        extra = []
        if crit is not None:
            extra.append(crit)
        if note is not None:
            extra.append(note)
        body.append([Cell(f'{esc(st.value)}{st.ref()}', [st]), tvtxt(desc, 150), ms(y), ms(u),
                     Cell(esc(str(pre.value)) + pre.ref(), [pre]) if pre is not None else Cell('–', []),
                     Cell(f'{esc(str(r.get("tag") or ""))} {desc.pill()}', [desc]),
                     cat(*[Cell(f'<div class="small">{esc(clipw(e.value, 140))}{e.ref()}</div>', [e]) for e in extra]) if extra else Cell('–', [])])
    return body


def sec_fea_jfwd(ctx, doc, a, D, o):
    o.append(doc.h(2, '9.5 J-FWD joint rows (TC-01 / TC-02 / HW-101 screw)'))
    o.append(f'<p>{inl(md_heading(ctx, "MMXMD", "J-FWD column rows", "DERIVED", tag_raw=MX_TAG))}. '
             'The criterion rows set the matrix cell; the hand-form LC2N / LC2M rows are shown beside them as information (lead 03:30:46Z, CHANGELOG 250 (2)); '
             'every other information row follows in a third table. Values are from the matrix JSON (MMX), row by row.</p>')
    heads = ['State', 'Row', 'MS_y', 'MS_u', 'Preload', 'Tag', 'Criterion / note']
    widths = ['7%', '41%', '7%', '7%', '7%', '10%', '21%']
    for part in ('TC-01', 'TC-02', 'HW-101 (J-FWD)'):
        pi, jr = mx_json_row(ctx, part)
        if pi is None:
            o.append(f'<p class="miss">{esc(part)}: no J-FWD rows found</p>')
            continue
        cv = ctx.v('MMX', f'/rows/{pi}/cells/J-FWD/value', tag='CALC', note='J-FWD cell = minimum over the criterion rows')
        o.append(doc.h(3, f'9.5.{("TC-01", "TC-02", "HW-101 (J-FWD)").index(part) + 1} {part}: J-FWD cell {fmt_num(cv.value[0], "+.3f")} / {fmt_num(cv.value[1], "+.3f")}'
                       if isinstance(cv.value, list) and len(cv.value) == 2 and None not in cv.value else f'9.5 {part}'))
        crit = jfwd_rows_table(ctx, pi, part, lambda r: not r.get('info'), 'criterion')
        lc2 = jfwd_rows_table(ctx, pi, part, lambda r: r.get('info') and r.get('state') in ('LC2N', 'LC2M'), 'LC2 info')
        oth = jfwd_rows_table(ctx, pi, part, lambda r: r.get('info') and r.get('state') not in ('LC2N', 'LC2M'), 'other info')
        o.append(dtable(heads, crit, label_cols=0, cls='tight', widths=widths,
                        caption=f'{esc(part)}: criterion rows ({len(crit)}); cell {cv.h(pill=False)}.'))
        if lc2:
            o.append(dtable(heads, lc2, label_cols=0, cls='tight', widths=widths,
                            caption=f'{esc(part)}: hand-form LC2N / LC2M rows, INFORMATION beside the criterion (rule (A), lead 03:30:46Z) ({len(lc2)}).'))
        if oth:
            o.append(dtable(heads, oth, label_cols=0, cls='tight', widths=widths,
                            caption=f'{esc(part)}: other information rows ({len(oth)}); they do not set the cell.'))


def sec_fea_mount(ctx, doc, a, D, o):
    o.append(doc.h(2, '9.6 Mounting data: loads at the 16 airframe holes'))
    rule = ctx.v('MOUNT', '/datasheet_v352_governing/rule', tag='DERIVED')
    o.append(f'<p>{inl(md_line_starting(ctx, "MOUNTMD", "Generated", "SIM", tag_raw="FEA3D mounting data (SIM unless tagged)"))}</p>')
    o.append(f'<p>Governing rule: {inl(rule)} The CHANGELOG ruling: {inl(D["cl"].item(249, 6))}</p>')
    sec = 'v3.5.2 model: DATASHEET per-hole values, governing'
    allr = md_rows_all(ctx.src('MOUNTMD').text or '', sec)
    if not allr:
        o.append('<p class="miss">mounting table not found</p>')
        return
    hdr = allr[0][1]
    rows = allr[1:]
    o.append(f'<p class="small">{inl(md_line_starting(ctx, "MOUNTMD", "Cell = max shear", "DERIVED", tag_raw="FEA3D mounting data legend"))}</p>')
    for gi, (lo, hi) in enumerate(((1, 8), (8, len(hdr)))):
        body = []
        for ln, r in rows:
            lab = re.sub(r'\*\*', '', r[0]).strip()
            cells = [Cell(f'<span class="mono">{esc(lab)}</span>', [])]
            for j in range(lo, hi):
                tv = md_cell_ln(ctx, 'MOUNTMD', ln, r, j, 'DERIVED', tag_raw='FEA3D mounting rows: SIM as found, moment-free estimate DERIVED (! = estimate governs)', label=lab)
                cells.append(Cell(f'{esc(tv.value)}{tv.ref()}', [tv]))
            body.append(cells)
        o.append(dtable(['Hole (x, y, z mm)'] + [esc(h) for h in hdr[lo:hi]], body, cls='mount',
                        widths=['17%'] + [f'{83 / (hi - lo):.1f}%'] * (hi - lo),
                        caption=f'Per-hole governing loads, part {gi + 1} of 2: max shear / max |axial| / max pull-out [N] per case; '
                                f'"!" = the moment-free estimate governs that value by 0.5 N or more; "*" = a compliant-airframe value exceeds the rigid one '
                                f'(MOUNTMD {esc(src_label(ctx, "MOUNTMD"))}).'))
    # totals on the airframe (rigid)
    body = []
    for case in (ctx.raw('MOUNT', '/datasheet_v352_governing/groups', default={}) or {}):
        base = f'/datasheet_v352_governing/groups/{case}/total_on_airframe_rigid'
        F = ctx.v('MOUNT', base + '/max_abs_F_N', 'N', tag='DERIVED', tag_ptr=f'/datasheet_v352_governing/groups/{case}/tag')
        M = ctx.v('MOUNT', base + '/max_abs_M_Nmm', 'N mm', tag='DERIVED', tag_ptr=f'/datasheet_v352_governing/groups/{case}/tag')
        body.append([esc(case), Cell(esc(', '.join(fmt_num(x, '.1f') for x in (F.value or []))) + F.ref(), [F]),
                     Cell(esc(', '.join(fmt_num(x, '.0f') for x in (M.value or []))) + M.ref(), [M])])
    o.append(dtable(['Case', 'Total force on the airframe, max |Fx|, |Fy|, |Fz| [N]', 'Total moment, max |Mx|, |My|, |Mz| [N mm]'], body,
                    widths=['16%', '42%', '42%'], cls='tight', caption='Resultant of the 16 hole loads on the airframe, rigid airframe, per case (DERIVED).'))
    ms = [('Included FE model mass, v3.5.2 (L1)', '/mass/v352/model_kg'), ('Engine group in the model', '/mass/v352/engine'),
          ('Excluded airframe-wall equipment (loads go to the wall directly)', '/mass/v352/excluded_kg')]
    o.append(dtable(['Mounting data header', 'Value'], [[l, num_cell(ctx.v('MOUNT', p, 'kg', tag='DERIVED'), '.3f')] for l, p in ms], widths=['60%', '40%']))


def sec_fea_stiff(ctx, doc, a, D, o):
    o.append(doc.h(2, '9.7 Gimbal axis stiffness (R3 poses) and rocking modes'))
    o.append(f'<p>{inl(ctx.v("KTAB", "/evidence", tag="SIM"))}</p>')
    body = []
    for i, r in enumerate(ctx.raw('KTAB', '/rows', default=[]) or []):
        b = f'/rows/{i}/values'
        cells = [Cell(f'<b>{esc(r.get("pose"))}</b> <span class="small">{esc(str(r.get("kind") or ""))}</span>', [])]
        for key in ('FE_coupled_alpha', 'FE_coupled_beta', 'k_s58_coupled_alpha', 'k_s58_coupled_beta', 'k_s174_coupled_alpha', 'k_s174_coupled_beta'):
            tv = ctx.v('KTAB', f'{b}/{key}/R3', 'N m/rad', tag='DERIVED' if key.startswith('k_s') else 'SIM')
            cells.append(num_cell(tv, '.0f', unit=False))
        fr = ctx.v('KTAB', f'/rows/{i}/fraction_max', tag='DERIVED')
        cells.append(num_cell(fr, '.3f'))
        body.append(cells)
    o.append(dtable(['Pose', 'FE α', 'FE β', 'k_s 58: α', 'k_s 58: β', 'k_s 174: α', 'k_s 174: β', 'Fraction max'], body, cls='tight',
                    widths=['22%', '10%', '10%', '11%', '11%', '11%', '11%', '14%'],
                    caption='Axis stiffness K at the 17 R3 poses [N m/rad], coupled values: FE alone (SIM) and with the servo in series at k_s 58 and 174 N m/rad '
                            '(ASSUMED, TO-VERIFY at B-TVC-1). Fraction = the pose change over the stop045 change (KTAB).'))
    body = []
    for ks in ('58', '174'):
        for J in ('J_free', 'J_low', 'J_nom', 'J_high'):
            tv = ctx.v('ROCK', f'/pose_range_Hz/{ks}/{J}', 'Hz', tag_ptr='/tag')
            body.append([f'k_s {ks} N m/rad, {J.replace("_", " ")}', Cell(esc(' – '.join(fmt_num(x, '.1f') for x in (tv.value or []))) + ' Hz ' + tv.pill() + tv.ref(), [tv])])
    Jv = ctx.v('ROCK', '/J_kgm2', 'kg m2', tag_ptr='/tag')
    o.append(dtable(['Servo stiffness and inertia case', 'Rocking-mode range over the 17 poses'], body, widths=['45%', '55%'], cls='tight',
                    caption=f'Lumped 2-DOF rocking frequencies (ROCK; rigid airframe). Servo J values: {esc(readable(Jv.value))} {Jv.ref()}.'))


def sec_fea_f4(ctx, doc, a, D, o):
    o.append(doc.h(2, '9.8 Secondary joints J-FD01 / J-FD09 (F4)'))
    body = []
    for jn_ in ('J-FD01', 'J-FD09'):
        b = f'/joints/{jn_}'
        hwv = ctx.v('F4J', b + '/hardware', tag='DESIGN')
        tq = ctx.v('F4J', b + '/preload/T_Nm', 'N m', tag='DESIGN')
        fnom = ctx.v('F4J', b + '/preload/F_nom_N', 'N', tag='DERIVED')
        for var in (ctx.raw('F4J', b + '/worst', default={}) or {}):
            w = f'{b}/worst/{var}'
            wb = ctx.v('F4J', w + '/bounding/MS', tag='SIM')
            wc = ctx.v('F4J', w + '/bounding/case', tag='SIM')
            wa = ctx.v('F4J', w + '/bounding/area', tag='SIM')
            wp = ctx.v('F4J', w + '/phi02/MS', tag='SIM')
            body.append([f'<b>{jn_}</b>', tvtxt(hwv, 200), cat(tq.h('.1f'), ' / ', fnom.h('.0f')),
                         cat(f'<span class="small">{esc(var)}:</span> ', wa.h(pill=False)),
                         cat(wb.h('+.3f'), '<br><span class="small">', wc.h(pill=False), '</span>'), num_cell(wp, '+.3f')])
    o.append(dtable(['Joint', 'Hardware', 'Torque / nominal preload', 'Variant / area', 'Worst bolt MS_y (bounding)', 'MS_y with Φ 0.2'], body, cls='tight',
                    widths=['8%', '34%', '14%', '14%', '18%', '12%'],
                    caption='F4 secondary joints on the v3.5.2 hardware (F4J; preload scatter ±25 % and K 0.20 ASSUMED). The matrix cells J-FD01 / J-FD09 are in Table 9.3.'))


def sec_fea_followups(ctx, doc, a, D, o):
    o.append(doc.h(2, '9.9 Mechanical follow-ups after FEA3D-2: tap wall v3, LC-TB70 v2, C1 seat'))
    st = ctx.v('TAPW', '/status', tag='CALC')
    vd = ctx.v('TAPW', '/verdict', tag='CALC', tag_ptr='/status')
    g = '/rows/3750/governing'
    rows = [['Governing (TC-02 thread, SOAK52)', cat(ctx.v('TAPW', g + '/TC02_thread_T/MS_y', tag='CALC').h('+.3f'), ' / ',
                                                    ctx.v('TAPW', g + '/TC02_thread_T/MS_u', tag='CALC').h('+.3f'))],
            ['Screw-temperature sensitivity (SOAK70)', cat(ctx.v('TAPW', g + '/worst_with_screw_T_sensitivity/MS_y', tag='CALC').h('+.3f'), ' / ',
                                                           ctx.v('TAPW', g + '/worst_with_screw_T_sensitivity/MS_u', tag='CALC').h('+.3f'))],
            ['Verdict', tvtxt(vd, 900)], ['Status', tvtxt(st, 400)]]
    o.append(dtable(['TC-02 torch-tap wall at FA1S (R4-01)', 'Value'], rows, widths=['30%', '70%'], cls='tight',
                    caption=f'Tap wall v3 (TAPW {esc(src_label(ctx, "TAPW"))}); R4-01 CLOSED in CHANGELOG 259 (1).'))
    rows = [['Z3 v2 (ruled)', tvtxt(ctx.v('TB70', '/Z3_v2_text', tag='LEAD'), 1500)],
            ['J-FWD replace rule on Q_JFWD', tvtxt(ctx.v('TB70', '/jfwd_rule_v2_text', tag='LEAD'), 1500)],
            ['F4 TB-state abort set', tvtxt(ctx.v('TB70', '/F4_abort_set/verdict', tag='CALC'), 700)],
            ['Status', tvtxt(ctx.v('TB70', '/status', tag='CALC'), 500)]]
    o.append(dtable(['LC-TB70 envelope v2', 'Text (quoted)'], rows, widths=['22%', '78%'], cls='tight',
                    caption=f'LC-TB70 envelope v2 (TB70 {esc(src_label(ctx, "TB70"))}); ruled in CHANGELOG 258 (3).'))


def sec_fea(ctx, doc, a, D):
    o = [doc.h(1, '9 Structural analysis: 3D FEA of the assembled engine (CAD v3.5.2)')]
    o.append(note_box(f'<b>{esc(PAGE_STATEMENT)}.</b> Every margin below is a model result (SIM), a hand calculation on model loads (CALC) or a value derived '
                      'from them (DERIVED). Negatives are shown as found. ' + inl(md_line_starting(ctx, 'F3D', 'Delivered by', 'DERIVED',
                                                                                                  tag_raw='FEA3D-2 report §0 checkpoint')), 'warn'))
    o.append(doc.h(2, '9.1 Model, loads and status'))
    rows = []
    for k in ('Status', 'Author', 'Configuration', 'Tool', 'Units', 'Tags'):
        tv = md_find(ctx, 'F3D', 'REPORT FEA3D v3.5.2', {0: k}, 1, ev='DERIVED', tag_raw='FEA3D-2 report header table')
        c = tvtxt(tv, 900)
        if k == 'Configuration':
            # the CAD manifest of record (REV-DS-1 N-04): the issues quoted in this row are earlier issues of the same file
            cm = src_tv(ctx, 'CADMAN')
            ctext = ctx.src('CADMAN').text or ''
            nrow = ctx.d(len([x for x in ctext.splitlines() if x.strip()]), '', 'count of the non-empty rows of 03-cad/v3.5.2/MANIFEST_v3.5.2.sha256', [cm])
            c = cat(c, gnote(f'manifest of record: 03-cad/v3.5.2/MANIFEST_v3.5.2.sha256 {esc(ctx.src("CADMAN").sha16 or "MISSING")}{cm.ref()}, '
                             f'{nrow.value} rows{nrow.ref()}; the issues quoted in this row are its earlier issues', [cm, nrow]))
        rows.append([k, c])
    rows.append(['Independent review', tvtxt(D['cl'].item(262, 3))])
    rows.append(['Margin matrix of record', cat(md_line_starting(ctx, 'MMXMD', 'Cell = MS_y', 'DERIVED', tag_raw=MX_TAG), Cell('', []))])
    rows.append(['Matrix delta vs the FEA3D-2 table', cat(tvtxt(ctx.v('MMXD', '/why', tag='DERIVED', tag_ptr='/tag'), 600))])
    o.append(dtable(['Item', 'Value'], rows, widths=['18%', '82%'], cls='tight',
                    caption=f'FEA3D v3.5.2 report header (F3D {esc(src_label(ctx, "F3D"))}) and the rows-v8 matrix of record.'))
    o.append(doc.h(3, '9.1.1 Mesh convergence status'))
    rows = [['Seat-line P+Q (J-FWD)', tvtxt(md_line_starting(ctx, 'F3D', 'MF note', 'SIM', tag_raw='FEA3D-2 report §5.3 MF note', after_heading='5. Mesh convergence'))],
            ['Check cD (finer mesh, FINAL TC-01)', tvtxt(D['cl'].item(252, 1))],
            ['Ruling on cD', tvtxt(D['cl'].item(250, 10), 900)]]
    o.append(dtable(['Point', 'Status (quoted)'], rows, widths=['22%', '78%'], cls='tight',
                    caption='The seat-line P+Q is NOT shown mesh-converged; s6 + C1 stand in every state (CHANGELOG 250 (10), 252 (1)).'))
    sec_fea_matrix(ctx, doc, a, D, o)
    sec_fea_negatives(ctx, doc, a, D, o)
    sec_fea_named(ctx, doc, a, D, o)
    sec_fea_jfwd(ctx, doc, a, D, o)
    sec_fea_mount(ctx, doc, a, D, o)
    sec_fea_stiff(ctx, doc, a, D, o)
    sec_fea_f4(ctx, doc, a, D, o)
    sec_fea_followups(ctx, doc, a, D, o)
    o.append(doc.h(2, '9.10 FEA3D-2 open items and owners'))
    rows = []
    for ln, r in md_rows_where(ctx, 'F3D', '13. Open items and owners'):
        lab = re.sub(r'\*\*', '', r[0]).strip()
        tvs13 = [md_cell_ln(ctx, 'F3D', ln, r, j, ev, tag_raw='FEA3D-2 report §13 open items') for j, ev in ((1, 'DERIVED'), (2, 'SIM'), (3, 'LEAD'), (4, 'DERIVED'))]
        if lab == '1':
            D['f3d_item1'] = tvs13  # sides of contradiction C-11 (status / numbers, closure)
        cells = [tvtxt(t, 420) for t in tvs13]
        if lab == '1' and '0.0761' in _plain_text(tvs13[3].value or ''):
            cells[3] = cat(cells[3], r2b_sup_note(ctx, D))  # the line-240 band quoted in the closure is superseded by R2-B (D1-01), at the quote
        rows.append([Cell(f'<b>{esc(lab)}</b>', [])] + cells)
    # header notes on items 1 and 2 (v0.3.1; item 1: lead 2026-10-21 13:47Z, REV-DS-1 D1-01); the item-2 numbers are traced to the matrix delta
    r2 = r2b_ruling(D)
    old = ctx.v('MMXD', '/cell_value_changes/0/old_MS_y_MS_u/1', tag_ptr='/tag')
    new = ctx.v('MMXD', '/cell_value_changes/0/new_MS_y_MS_u/1', tag_ptr='/tag')
    hn = cat('<b>Item 1</b> quotes the select-fit band of line 240 (10) and its one re-size by Mechanical ', r2b_sup_note(ctx, D),
             ' Closure: R2-B select fit (254 (1)', r2.ref(), '); stays a found negative at the drawn fit (contradiction register C-11, §13.3). ',
             '<b>Item 2</b> quotes ', old.h('+.3f'), ' for the HW-101 J-FWD u cell: the rows-v8 matrix of record gives ', new.h('+.3f'),
             ' (§9.5.3; contradiction register C-01, §13.3).')
    o.append(dtable(['#', 'Item', 'Status / numbers', 'Owner', 'Closure'], rows, cls='tight', widths=['4%', '20%', '40%', '14%', '22%'],
                    caption='FEA3D-2 §13 as published (05:45Z). ' + hn.html))
    o.append(doc.h(2, '9.11 Not run, superseded, and runs that wait for the lead'))
    L = (ctx.src('F3D').text or '').splitlines()
    on, items = False, []
    for i, ln in enumerate(L, 1):
        if ln.startswith('## '):
            on = ln.startswith('## 11. Not run')
            continue
        if on and ln.startswith('- '):
            items.append(ctx.t('F3D', f'§11 line {i}', ln[2:].strip(), 'DERIVED', tag_raw='FEA3D-2 report §11'))
    o.append(dtable(['Item (quoted)'], [[tvtxt(t, 700)] for t in items], label_cols=0, cls='tight', widths=['100%'],
                    caption='FEA3D-2 §11: nothing in this list is a margin.'))
    return '\n'.join(o)

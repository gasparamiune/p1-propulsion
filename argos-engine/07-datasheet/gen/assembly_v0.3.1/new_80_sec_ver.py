# ---------------------------------------------------------------------------------------------
# section 12 (v0.3.0): verification status, founder actions, open items; contradictions register
# ---------------------------------------------------------------------------------------------
def r2b_ruling(D):
    """LEAD RULING R2-B as quoted verbatim in Mechanical's line 254 (1), its operative text up to 'to the measured bore.': a lead
    decision (DECIDED), its basis text names where it is quoted. v0.3.1: a clip, because the v0.3.0 sentence split stopped the
    quote at the 'i.e.' of the band."""
    if 'r2b' not in D:
        t = D['cl'].clip(254, 1, 'LEAD RULING R2-B', 'to the measured bore.', ev='LEAD', why='the text quotes LEAD RULING R2-B verbatim')
        if t.value is not None:
            t.basis = 'Lead ruling R2-B (2026-10-21T07:37:34Z), quoted verbatim in Mechanical line 254 (1)'
        D['r2b'] = t
    return D['r2b']


def r2b_band(ctx, D):
    """R2-B band edges (radial gap; lead ruling R2-B, line 254 (1)) and the band file of record, for the supersede notes on the
    line-240 band (lead 2026-10-21 13:47Z, REV-DS-1 D1-01)."""
    if 'r2b_band' not in D:
        r = r2b_ruling(D)
        lo = rx_text(ctx, r, r'radial gap g in \[([\d.]+), [\d.]+\] mm', 'mm')
        hi = rx_text(ctx, r, r'radial gap g in \[[\d.]+, ([\d.]+)\] mm', 'mm')
        for t in (lo, hi):
            if t.value is not None:
                t.basis = r.basis
        bd = src_tv(ctx, 'BAND')
        m = re.search(r'jfwd_pq_band_v352_v1\.json ([0-9a-f]{16})', D['cl'].items(254).get(1, ''))
        if not m or m.group(1) != ctx.src('BAND').sha16:
            ctx.issue('WARN', 'the band file named in line 254 (1) is not the band file in the hub (sha256/16 differs or not named)')
        D['r2b_band'] = (lo, hi, bd, r)
    return D['r2b_band']


def r2b_sup_note(ctx, D):
    """'[superseded: R2-B [lo, hi] mm, 254 (1); band re-size done, band v1 <sha>]' (lead 2026-10-21 13:47Z, REV-DS-1 D1-01)."""
    lo, hi, bd, r = r2b_band(ctx, D)
    return gnote(f'superseded: R2-B [{lo.h(".3f", unit=False, pill=False)}, {hi.h(".4f")}], 254 (1){r.ref()}; band re-size done, band {bd.h()}',
                 [lo, hi, bd, r])


def sup_index(ctx, rid):
    return next((k for k, r in enumerate(ctx.raw('SUP', '/reviews', default=[]) or []) if r.get('id') == rid), None)


def part_tv(ctx, tv, txt, label):
    """A verbatim part of a traced text (one step of a procedure), keeping its class and basis (Annex C4; rev1 phase 2)."""
    # v0.3.1 final: the locator is the pointer of the whole text (the part is a verbatim substring of it, so any re-trace finds it there);
    # the part is named in the note
    nt = f'{label} of the text at this pointer, quoted verbatim' + (f'; {tv.note}' if tv.note else '')
    t = TV(ctx, txt, '', tv.ev, tv.tag_raw, tv.sid, tv.ptr, note=nt, status=tv.status)
    t.ev, t.basis, t.basis_detail, t.basis_kind = tv.ev, getattr(tv, 'basis', None), getattr(tv, 'basis_detail', None), getattr(tv, 'basis_kind', None)
    return t


def proc_steps(text, first=0, last=9):
    """Start offsets of the numbered steps 'k. ' of a procedure text, k = first..last in order, each after ': ', '. ', '; ' or ') '."""
    pos, out = 0, []
    for k in range(first, last + 1):
        mm = re.search(r'(?<=[:.;)] )%d\. ' % k, text[pos:])
        if mm is None:
            break
        out.append((k, pos + mm.start()))
        pos = pos + mm.start() + 2
    return out


def tf1_status_tv(ctx, D):
    """T-F1 criteria status (texts v5): a result, CALC on SIM, accepted by the lead in 249 (3) (lead 2026-10-21 14:05Z, REV-DS-1 D1-07)."""
    if 'tf1_st' not in D:
        t = ctx.v('TXT5', '/T-F1_exposure_basis_R9/criteria_status', tag='CALC')
        t.tag_raw = '(class set at the call site: CALC on SIM; the criteria results were accepted by the lead in 249 (3); REV-DS-1 D1-07)'
        D['tf1_st'] = t
    return D['tf1_st']


def tf1_status_cell(ctx, D):
    t = tf1_status_tv(ctx, D)
    i3 = D['cl'].item(249, 3)
    return cat(tvtxt(t), gnote(f'CALC on SIM; accepted, 249 (3){i3.ref()}', [i3]))


def gse_row(D, pn):
    return next((r for r in D.get('gse', []) if r.pn == pn), None)


def gse_cell(D, pn):
    """A BOM GSE tool line as the make/buy record of a founder action: name, drawing state and price as written in the BOM (row trace)."""
    r = gse_row(D, pn)
    if r is None:
        return Cell(f'<span class="miss">BOM GSE line {esc(pn)} not found</span>', [])
    l = r.l
    sec = D.get('sec_gse', '§5')
    return Cell(f'<div class="dec"><b>BOM GSE line ({esc(sec)}):</b> <span class="qt">{esc(r.pn)}: {esc(l.get("name", ""))}; drawing {esc(l.get("drawing") or "")}; '
                f'price {esc(l.get("unit_price") or "")}; {esc(l.get("groups") or "")}</span> {r.row_tv.pill()}{r.row_tv.ref()}</div>', [r.row_tv])


def dec_cells(tvs):
    """Founder-action texts in full (lead 2026-10-21 14:05Z: a founder action, gate or build procedure is never cut)."""
    out = []
    for t in tvs:
        if isinstance(t, Cell):
            out.append(t)
        else:
            out.append(Cell(f'<div class="dec">{tvtxt(t).html}</div>', [t]))
    return cat(*out)


def sec_verification(ctx, doc, a, D):
    o = [doc.h(1, '12 Verification status')]
    cl = D['cl']
    note = ctx.v('SUP', '/note', tag='DESIGN')
    o.append(note_box(f'<b class="stmt">{esc(PAGE_STATEMENT)}.</b> {tvtxt(note).html} No value here is a measurement. '
                      'Review verdicts, matching file hashes, clean CAD checks, passing unit tests and this document\'s own trace check '
                      'are digital evidence only.', 'warn'))
    o.append(doc.h(2, '12.1 Review status of the deliverables used here'))
    rows = []
    for rid, what, line in (('REV-COMB-4', 'Combustion v2.4b (delta re-review); folded in v2.4c / v2.4d', 256),
                            ('REV-ELEC-3', 'Electronics v2.11 (firmware v2.11, electronics.json v4)', 253),
                            ('REV-GNC-7', 'GNC rev4b / gnc.json v3.2', 258),
                            ('REV-MECH-2', 'Mechanical FEA and CAD (v3.5 era)', None)):
        i = sup_index(ctx, rid)
        if i is None:
            m = ctx.missing(f'{rid} in the review register')
            rows.append([Cell(f'<b>{esc(rid)}</b>', []), esc(what), Cell(m.h(), [m]), ''])
            continue
        vd = ctx.v('SUP', f'/reviews/{i}/verdict', tag='DERIVED')
        disp = cl.part(line, rid) if line else ctx.v('SUP', f'/reviews/{i}/lead_disposition', tag='LEAD') if ctx.raw('SUP', f'/reviews/{i}/lead_disposition', default=None) else ctx.missing(f'{rid} lead disposition', 'TO-VERIFY')
        rows.append([Cell(f'<b>{esc(rid)}</b>', []), esc(what), Cell(f'<b>{esc(vd.value)}</b> {vd.pill()}{vd.ref()}', [vd]), tvtxt(disp, 500)])
    if not D['ele']['promo']:
        pe = cl.clip(264, 8, 'v4.1 is promoted only after its verdict', 'its verdict.')
        rows.append([Cell('<b>REV-ELEC-4</b>', []), 'Electronics v2.12 (firmware v2.12, electronics.json v4.1 candidate)',
                     Cell(f'<b>PENDING</b> (started; CHANGELOG 264 (8)) {pe.pill()}{pe.ref()}', [pe]),
                     tvtxt(cl.clip(264, 1, 'interfaces/electronics.json stays v4', 'as PENDING REVIEW.'), 400)])
    else:
        rows.append(ele41_review_row(ctx, D))
    fr = cl.item(262, 3)
    rows.append([Cell('<b>FEA3D-2</b>', []), '3D FEA of the v3.5.2 assembly (REPORT-FEA3D-v352.md) and the rows-v8 matrix',
                 Cell('<b>no independent review held in this finish run</b>', [fr]), tvtxt(fr, 300)])
    rows.append(revds1_row(ctx, a, D))
    o.append(dtable(['Review', 'Deliverable', 'Verdict', 'Lead disposition / plan (quoted)'], rows, label_cols=2, widths=['12%', '24%', '20%', '44%'], cls='tight',
                    caption='Verdicts from reviews/SUPERVISION.json and, for REV-ELEC-4 and REV-DS-1 (not in the register yet), from their review files; dispositions '
                            'from the CHANGELOG. A verdict covers the hashed files only (§12.2). A verdict is not physical approval.'))
    o.append(doc.h(2, '12.2 Review register'))
    sup = ctx.raw('SUP', '/reviews', default=[]) or []
    rows = []
    for k, r in enumerate(sup):
        b = f'/reviews/{k}'
        rid = ctx.v('SUP', b + '/id', tag='DERIVED')
        dt = ctx.v('SUP', b + '/date', tag='DERIVED')
        vd = ctx.v('SUP', b + '/verdict', tag='DERIVED')
        dl = ctx.v('SUP', b + '/deliverable', tag='DERIVED')
        same, changed, missing = hash_status(ctx, a, r.get('hashes_sha256_16'))
        hs = ctx.d(f'{len(same)} of {len(same) + len(changed) + len(missing)} reviewed files unchanged'
                   + (f'; changed since review: {", ".join(changed)}' if changed else '')
                   + (f'; not in the hub: {", ".join(missing)}' if missing else ''), '', 'sha256/16 of each reviewed hub file vs the register entry', [], ev='DERIVED')
        rows.append([Cell(f'<b>{esc(rid.value)}</b>{rid.ref()}<div class="small">{esc(dt.value)}</div>', [rid, dt]), tvtxt(dl, 200),
                     cat(f'<b>{esc(vd.value)}</b> ', vd.pill(), vd.ref(), Cell('', [vd])),
                     cat('<span class="small">', hs.h(pill=False), '</span>', Cell('', [hs]))])
    o.append(dtable(['Review', 'Deliverable', 'Verdict', 'Reviewed files now (generator check)'], rows, label_cols=0, widths=['12%', '36%', '22%', '30%'], cls='tight',
                    caption=f'reviews/SUPERVISION.json ({esc(ctx.src("SUP").sha16)}), {len(sup)} entries in register order. Not physical approval.'))

    o.append(doc.h(2, '12.3 Founder actions (traced to their decision)'))
    o.append('<p class="hnote">Every founder action, gate and build procedure prints in full, with its acceptance limit and its source lines, so that it '
             'can be carried out from the printed page (lead 2026-10-21 14:05Z). The J-FWD build procedure C4 is printed step by step in '
             '<a href="#annex-c4">Annex C4</a>, after this table.</p>')
    MR = '/jfwd_v352/founder_rules'
    p = purge_parts(ctx, D)
    c4 = ctx.v('MEC', f'{MR}/C4_procedure', tag='LEAD')
    D['c4_tv'] = c4
    fa = [
        ('IN718 M5 J-FWD screw: quote, and the M6 fallback', [cl.part(240, ['RULED: the J-FWD screw is IN718 M5', 'FALLBACK only if IN718'])]),
        ('HW-170 disc spring: quote with relaxation data at about 160 C', [cl.part(243, 'Spring A (Schnorr 001 500 A in 1.4568)'), ctx.v('MEC', f'{MR}/HW-170_single_use', tag='LEAD')]),
        ('J-F1: torque cap 3750 N per flight lot and the Prescale footprint check (TO-VERIFY)', [cl.part(245, ['J-F1 MAXIMUM PRELOAD IS CAPPED AT 3750 N', 'Prescale'])]),
        ('J-F1b: 175 C peak with the dwell (method TO-DEFINE)', [ctx.v('MEC', f'{MR}/J-F1b', tag='LEAD'), cl.part(254, 'J-F1b method TO-DEFINE')]),
        ('LOCTITE 243 service range (TO-VERIFY)', [cl.part(248, 'LOCTITE 243 tap zone'), cl.part(254, 'LOCTITE 243 range TO-VERIFY')]),
        ('Single-use J-FWD screws and springs; removed-screw inspection', [ctx.v('MEC', f'{MR}/single_use', tag='LEAD'), cl.part(243, 'Founder rule until C6 closes')]),
        ('Post-abort joint replacement rule', [ctx.v('MEC', f'{MR}/post_abort_joint_replacement', tag='LEAD'), cl.part(248, 'FOUNDER RULE: after any case-TC')]),
        ('HW-170 orientation', [ctx.v('MEC', f'{MR}/HW-170_orientation', tag='DERIVED')]),
        ('Stand T0 <= 24 C rule and its checklist row', [cl.item(249, 2), ctx.v('MEC', f'{MR}/stand_T0_cross_reference', tag='LEAD')]),
        ('RA-03, J-FWD hole edges (TC-01 rev 5, C1): edge breaks, deburring and the 10x inspection before assembly (240 (5); 241 (8) C1)',
         [ctx.v('TXT5', '/item_C/C1_TC01_drawing_callout_rev5', tag='DESIGN'), cl.item(240, 5),
          cl.clip(241, 8, 'C1, TC-01 rev 5 at the 10 x d5.5 J-FWD holes', '(g) and (h) as item 6 (c) and (d).')]),
        ('B-TC-1 case-TC channel: acceptance on the DESIGN install (tau and the static terms, else the tolerance is re-derived; 249 (1)); CJTO trim and mean-shift EMI pass (253 (11))',
         [cl.part(249, 'B-TC-1 (founder'), cl.clip(249, 1, 'low-reading tolerance tol_lo', 'else the tolerance is re-derived.'), cl.item(253, 11)]),
        ('T-F1, short-time exposure allowables of TC-01 / TC-02: a GATE before the first static fire; routes (i) and (ii) and the PASS criteria in full (241 (8), 249 (3), 254 (2))',
         [ctx.v('TXT5', '/T-F1', tag='CALC'), tf1_status_cell(ctx, D),
          cl.clip(241, 8, 'T-F1 (founder action, a GATE before the first static fire)', 'no recalled or estimated value replaces either route.'),
          cl.item(249, 3), cl.clip(254, 2, 'T-F1 restated per R9', '(d) OPEN)', ev='REF', why='a source line of the founder action (the specialist\'s record line, quoted as its reference)'), cl.part(249, 'T-F1 founder text on the A 175 rows')]),
        ('Shoulder-screw registration (F2) and the index pin (F5)', [cl.part(245, ['F2 ADOPTED into C4', 'F5: clocking'])]),
        ('RA-06, make or buy: ENG-TC-12 J-FWD hole-plug set (GSE; TO-DRAW / TO-QUOTE, delivered to Sønderborg DK-6400; 241 (8) C3)',
         [gse_cell(D, 'ENG-TC-12'), ctx.v('TXT5', '/item_C/C3_fitting_aid_GSE', tag='DESIGN'),
          cl.clip(241, 8, 'C3: ENG-TC-12 J-FWD hole-plug set', 'TO-DRAW / TO-QUOTE).')]),
        ('RA-06, make or buy: ENG-TC-13 J-FWD registration shoulder-screw pair (GSE; TO-DRAW / TO-QUOTE, delivered to Sønderborg DK-6400; 245 (4) F2, 246 (2) C3b)',
         [gse_cell(D, 'ENG-TC-13'), ctx.v('TXT5', '/item_C/C3b_registration_shoulder_screws_GSE', tag='DESIGN'),
          cl.clip(245, 4, 'F2 ADOPTED into C4', 'shoulder screws out last'), cl.clip(246, 2, 'new C3b (ENG-TC-13 GSE)', 'new C3b (ENG-TC-13 GSE)', ev='REF', why='a source line of the founder action (the specialist\'s record line, quoted as its reference)')]),
        ('RA-06, make: the match-drill fixture with the index pin and the guide bushings (shop tooling, TO-DRAW; not a BOM line; 245 (4) F5)',
         [ctx.v('TXT5', '/item_C/C8_jfwd_drawing_texts_rev5/open_items/2', tag='DESIGN'),
          ctx.v('TXT5', '/item_C/C8_jfwd_drawing_texts_rev5/ENG-TC-02_rev5/jfwd_fits_items/0', tag='DESIGN'),
          cl.clip(245, 4, 'F5: clocking +/-0.25 deg at match-drilling', 'tap-wall row.')]),
        ('Preload-retention audit', [cl.part(240, 'PRELOAD-RETENTION AUDIT ADOPTED')]),
        ('TC-02 spigot select fit (R2-B; U TO-DEFINE)', [r2b_ruling(D), ctx.v('TXT5', '/item_C/C9_founder_texts_remap_v352/(6)_TC-02_select_fit_band_R2', tag='CALC')]),
        ('S01 / S02 and the screws replaced after any FA-1-class event', [cl.item(240, 6), ctx.v('MEC', f'{MR}/C6', tag='LEAD')]),
        ('RA-15, C6 closure path 3: the screw qualification test (TO-DEFINE, founder; 243 (5), 254 (6))',
         [cl.clip(243, 5, 'Closure paths:', '(3) a qualification test (TO-DEFINE, founder).'), cl.clip(245, 4, 'C6 closure path 1 is negative', 'C6 OPEN'),
          cl.clip(254, 6, 'screw thread-root LCF paths 2 / 3', '(Mechanical / founder test TO-DEFINE)', ev='REF', why='a source line of the founder action (the specialist\'s record line, quoted as its reference)')]),
        ('J-FWD build procedure C4 (every assembly and re-assembly)',
         [Cell(f'<div class="dec"><b>Printed in full, step by step, in <a href="#annex-c4">Annex C4</a></b> (after this table) {c4.pill()}{c4.ref()}</div>', [c4])]),
        ('Kulite F-10, B-PC-1 zero coefficient per serial, F-13 soak and thermometer (253 (11))', [cl.item(253, 11)]),
        ('B-PC-1: the Pc-zero coefficient per serial and T_cal, with the bench plan v5 acceptance (264 (2))',
         [cl.clip(264, 2, 'with the per-serial coefficient and T_cal from B-PC-1', 'at k = 3)'), cl.item(264, 2, contains='Residuals stay OPEN')]
         + ([e4_02_cell(ctx, D)] if D['ele']['promo'] else [])),
        ('F-10: the thermal-zero maximum from Kulite (264 (2))', [cl.item(264, 2, contains='Residuals stay OPEN')]),
        ('RA-32, stand fallback (coefficient 0): allowed on the stand only within the 264 (2) limits, by F-10; never a flight configuration',
         [cl.clip(264, 2, 'The fallback (coefficient 0', 'at ARM [DERIVED].')] + ([D['ele']['carve_tv'], D['ele']['cons_tv']] if D['ele']['promo'] else [])),
        ('Confirm the A1 flight T0 design range against the launch-site climate (264 (6))', [cl.item(264, 6)]),
        ('Decide OI-JFWD-FLIGHT at flight acceptance, with T-F1 (264 (7))', [cl.item(264, 7)]),
        ('Buy the P_torch unit, a C1-family Kulite (264 (4)); TO-QUOTE delivered to Sønderborg DK-6400', [cl.clip(264, 4, 'the BOM gains one C1-family unit', 'DK-6400.')]),
        ('RA-26, CF-4 / B-BLEED-1: purge acceptance (measured Cd x A) and the re-set rule of the purge flow and the both-open cap (256 (2), 257 (2), 258 (2))',
         [cl.clip(256, 2, 'with three conditions:', 'needs 2.5 s).'), cl.clip(257, 2, 'DECIDED: after CF-4 / B-BLEED-1', 'at the measured vent.'),
          cl.clip(258, 2, 'DECIDED: the two REV-GNC-7 additions', 'condition (b) governs.'),
          Cell('<div class="small">The same conditions as published in combustion.json /purge_decision_v2p4c: §7.5. The test list (§12.6) points here.</div>', [])]),
        ('Q_JFWD > 60.0 bar abs: inspection and TC-02 tap gauging before the next run', [ctx.v('CMB', '/z3_jfwd_rulings_v2p4d/v/jfwd_replace_rule/decision', tag='LEAD'),
                                                                                       cl.part(258, 'Q_JFWD')]),
        ('Stand no-event B-DPC-1 record for a noise-floor rule (TO-VERIFY)', [ctx.v('CMB', '/z3_jfwd_rulings_v2p4d/v/jfwd_replace_rule/measured_traces', tag='TO-VERIFY')]),
    ]
    if D['ele']['promo']:
        n = D['ele']['line']
        fa.append((f'Electronics v2.13 delta (the E4-01 fix) and its review: QUEUED, NOT STARTED; the founder says when ({n} (8)); until it is reviewed, '
                   f'option (b) is not used for any start with ignition ({n} (6))', [D['ele']['q8_tv'], D['ele']['carve_tv']]))
    rows = []
    for what, tvs in fa:
        rows.append([Cell(f'<b>{esc(what)}</b>', []), dec_cells(tvs)])
    rows.append(ele_founder_block_row(ctx, D))
    o.append(dtable(['Founder action', 'Decision and text (quoted in full)'], rows, widths=['26%', '74%'], cls='tight',
                    caption='The founders run every physical step; none has been run. Purchases: TO-QUOTE delivered to Sønderborg DK-6400. '
                            + ('Bench plan v4 is REVISE (text) and does not go to the founders before v5 (CHANGELOG 253 (5)).' if not D['ele']['promo'] else
                               f'Bench plan v5 does not go to the founders before the corrections of CHANGELOG {D["ele"]["line"]} (7).')))
    o.append(annex_c4(ctx, doc, D, c4))

    o.append(doc.h(2, '12.4 Open items with owners'))
    Z = '/z3_jfwd_rulings_v2p4d/v/open_before_flight_acceptance'
    ob = ctx.raw('CMB', Z, default=[]) or []
    eo = D.get('ele_oi') or {}
    items = [('Before flight acceptance (LEAD 258 (3))', [ctx.v('CMB', f'{Z}/{j}', tag='TO-VERIFY') for j in range(len(ob))], 'LEAD / Mechanical'),
             ('Noise-floor rule for the J-FWD trigger on measured traces', [ctx.v('CMB', '/z3_jfwd_rulings_v2p4d/v/jfwd_replace_rule/measured_traces', tag='TO-VERIFY')], 'founders (B-DPC-1) / review'),
             ('OI-T4-RESIZE: the T4 re-run with the shorter relight', [cl.item(261, 2), cl.clip(264, 5, 'Combustion sets the length', 'soak-back.'),
                                                                    cl.clip(264, 5, 'T4 then demonstrates', 'say so.')], 'Combustion / Mechanical'),
             ('OI-C1-SEAT-DRIFT residuals (B-PC-1; F-10; the seat-TC mount; the P_mid temperature, MISSING)', [cl.item(264, 2, contains='Residuals stay OPEN')],
              'founders / Mechanical'),
             ('A1 pad no-go rule (NEW RULE, not implemented yet)', [cl.item(264, 2, contains='NEW RULE')],
              'Electronics, after REV-ELEC-4' if not D['ele']['promo'] else 'Electronics v2.13 (E4-N02, 266 (8))'),
             ('OI-PTORCH-PROOF: re-base of the torch thresholds on the C1 zero', [cl.clip(264, 4, 'OPEN for the next Electronics round', 'DK-6400.')],
              'Electronics; Combustion / Mechanical (torch heat)'),
             ('Purge: the measured-time form of the flow and the cap after CF-4 / B-BLEED-1', [p['i257']], 'founders (CF-4 / B-BLEED-1); Combustion / Electronics (re-set)'),
             ('Electronics v2.12 work NOT DONE: the v2.12 SIL MANIFEST; the S1-S11 / S14-S17 re-runs', [cl.clip(264, 8, 'The author did NOT produce', 'can affect.')],
              'Electronics; REV-ELEC-4 judges' if not D['ele']['promo'] else 'Electronics: v2.13 (a SIL MANIFEST_v2, 266 (8))'),
             (('Items routed to Electronics v2.12 (in the v2.12 candidate, PENDING REVIEW)' if not D['ele']['promo'] else
               'Items routed to Electronics v2.12 (in v4.1, promoted, line 266)'), [cl.item(258, 4)], 'Electronics'),
             ('ENG-11 spread element (alpha / beta spread across poses): OPEN under 188 (7)', [cl.item(188, 7), eng11_spread_cell(ctx, D)],
              'GNC (robustness assessment); lead (amendment); Mechanical (stiffening)'),
             ('Found negatives of the margin matrix', [D['neg_total']], 'per class, §9.3; owners §9.10'),
             ('FEA3D open items', [md_heading(ctx, 'F3D', '13. Open items and owners', 'DERIVED', tag_raw='FEA3D-2 report heading')], 'per item, §9.10'),
             ('GNC open items 11a-11q', [md_find(ctx, 'DSIG', None, {0: '11a'}, 1, ev='TO-VERIFY', tag_raw='GNC datasheet inputs row 11a')], 'per item, §11.2'),
             ('Electronics open issues (electronics.json), open', [eo['open'] if eo.get('open') is not None else ctx.d(len(ctx.raw('ELE', '/open_issues', default=[]) or []), '', 'count of electronics.json /open_issues', [], ev='DERIVED')], 'per item, §10.9'),
             ('Airframe items kept for when the airframe is tackled (ICD-AIRFRAME out of the finish scope)', [cl.part(222, 'The items that were queued for it')],
              'airframe work, deferred by the founder (222)')]
    if D['ele']['promo']:
        e = D['ele']
        items[0:0] = [('A1 flight: NO-GO until v2.13 is reviewed; stand first starts on the fallback only within 264 (2); no stand relight (266 (6))',
                       [e['carve_tv'], e['cons_tv']], 'lead; founders; Electronics (v2.13)'),
                      ('Electronics v2.13 delta (E4-01 fix: light-window hold, TC4 step / rate checks, E4-03, UT-1 to UT-4, S13T TC-fault set, FMEA row, '
                       'B-TC-1 TC4 row) and its review', [e['q8_tv']], 'QUEUED, NOT STARTED; the founder says when (266 (8))'),
                      ('Routed with line 266 (8): E4-N08 (the both-open backstop up to 2.741 s against the 2.39 s never-above value); the FC rule for '
                       'SEAT_STEP and the compensated-Pc release predicate', [e['routed_tv']],
                       'Combustion and the lead at B-BLEED-1 (E4-N08); GNC and the lead with v2.13')]
    if eo.get('closed') is not None and eo['closed'].value:
        items.insert(-1, ('Electronics open issues closed by a lead line (shown for the record in §10.9; only a residual a lead line names stays open)', [eo['closed']], '§10.9'))
    rows = []
    for what, tvs, own in items:
        rows.append([Cell(f'<b>{esc(what)}</b>', []), cat(*[(t if isinstance(t, Cell) else Cell(f'<div class="dec">{tvtxt(t).html if isinstance(t.value, str) or t.value is None else t.h()}</div>', [t])) for t in tvs]), esc(own)])  # in full (D1-06)
    o.append(dtable(['Item', 'Status (quoted)', 'Owner'], rows, widths=['24%', '60%', '16%'], cls='tight', free_cols=(2,)))

    o.append(doc.h(2, '12.5 Requirement verification methods'))
    rows = []
    am = [ln.strip()[2:] for ln in md_section_lines(ctx.src('REQ').text or '', 'Amendments after rev 2') if ln.strip().startswith('- ')]
    for r in md_table_rows(ctx.src('REQ').text or '', '2. Top-level'):
        if not r or not r[0].startswith('ENG-'):
            continue
        rq = md_row(ctx, 'REQ', '2. Top-level', r[0], 1, tag_col=2)
        vm = md_row(ctx, 'REQ', '2. Top-level', r[0], 3, ev='REQ')
        acell = []
        for b in am:
            if re.search(r'\b' + re.escape(r[0]) + r'\b', b):
                x = sentence_with(b, r[0]) or b
                tva = ctx.t('REQ', f'§Amendments after rev 2 bullet "{b[:48]}" [sentence containing "{r[0]}"]', x, 'REQ', tag_raw='REQ amendment bullet')
                ac = Cell(f'<div class="dec">{tvtxt(tva, 260).html}</div>', [tva])
                if r[0] == 'ENG-11' and '3133-7406' in x:
                    ac = cat(ac, v5c_note(ctx, D))
                acell.append(ac)
        idc = f'<b>{esc(r[0])}</b>'
        rqc = tvtxt(rq, 230)
        if r[0] == 'ENG-11':
            idc = '<b>ENG-11 (REQ): gimbal axis stiffness</b>'
            rqc = cat(tvtxt(rq), eng11_spread_cell(ctx, D))
            D['eng11_req'] = rq
        rows.append([idc, rqc, cat(*acell) if acell else Cell('<span class="small">none</span>', []), tvtxt(vm, 120)])
    o.append(dtable(['ID', 'Requirement (rev 2 text, start)', 'Amendments after rev 2 (sentences naming the ID)', 'Verification method'], rows,
                    widths=['7%', '42%', '33%', '18%'], free_cols=(2,), cls='tight',
                    caption=f'00-requirements/REQUIREMENTS.md §2 and its amendments ({esc(src_label(ctx, "REQ"))}). No requirement has been verified physically. '
                            'ENG-11 (REQ) is the gimbal axis stiffness; the GNC servo output stiffness K_s that the GNC inputs file under ENG-11 is in §3.2.'))
    o.append(doc.h(2, '12.6 Founder test list'))
    rows = []
    for r in md_table_rows(ctx.src('BENCH').text or '', '1. Order and gates'):
        if not r or not (r[0].isdigit() or r[0] == 'F'):
            continue
        cells = [md_row(ctx, 'BENCH', '1. Order and gates', r[0], j, ev='DESIGN') for j in (1, 2, 3)]
        out = []
        for t in cells:
            if isinstance(t.value, str) and 'executable now' in t.value:
                if not D['ele']['promo']:
                    b5x = cl.clip(253, 5, 'bench plan v4 is REVISE', 'before v5.')
                    why = f'not for execution: bench plan v4 is REVISE and does not go to the founders before v5, 253 (5){b5x.ref()}'
                else:
                    b5x = cl.clip(D['ele']['line'], 7, 'Bench plan v5 does not go to the founders before these corrections.',
                                  'Bench plan v5 does not go to the founders before these corrections.')
                    why = f'not for execution: bench plan v5 does not go to the founders before the corrections of {D["ele"]["line"]} (7){b5x.ref()}'
                out.append(Cell(f'<span class="qt"><s>{esc(t.value)}</s></span> {t.pill()}{t.ref()}<span class="gnote">[{why}]</span>', [t, b5x]))
            else:
                out.append(tvtxt(t))
        if D['ele']['promo']:
            extra = bench_row_notes(ctx, D, str(cells[0].value) if cells else '')  # the test column names the bench tests of the step
            if extra:
                out[-1] = cat(out[-1], *extra)
        rows.append([f'Bench step {esc(r[0])}'] + out)
    for r in md_table_rows(ctx.src('REQ').text or '', '4. Gating early bench tests'):
        if not r or r[0] in ('Test',):
            continue
        rows.append(['Early purchase (REQ §4)', Cell(f'<b>{esc(r[0])}</b>', [md_row(ctx, 'REQ', '4. Gating early bench tests', r[0], 0, ev='REQ')]),
                     tvtxt(md_row(ctx, 'REQ', '4. Gating early bench tests', r[0], 2, ev='REQ')), tvtxt(md_row(ctx, 'REQ', '4. Gating early bench tests', r[0], 1, ev='REQ'))])
    b5 = cl.clip(253, 5, 'bench plan v4 is REVISE', 'before v5.')
    if not D['ele']['promo']:
        o.append(note_box('<b>Bench plan v4, for information, not for execution (253 (5)); v5 PENDING REVIEW.</b> ' + inl(b5) + ' Bench plan v5 is staged with the '
                          'electronics.json v4.1 candidate and is PENDING REVIEW (REV-ELEC-4). The bench rows below are bench plan v4, the plan of electronics.json v4, '
                          'shown for information only. The CF-4 / B-BLEED-1 purge acceptance and re-set rule: founder row in §12.3 (and §7.5).', 'warn'))
        cap = (f'Bench plan v4 section 1 ({esc(src_label(ctx, "BENCH"))}): for information, not for execution (CHANGELOG 253 (5)); v5 PENDING REVIEW. REQ §4: early purchases. '
               'CF-4 and T1-T4 criteria: §7.9; the CF-4 / B-BLEED-1 purge acceptance and re-set rule: §12.3. None has been run. Cost: TO-QUOTE, delivered to Sønderborg, DK-6400.')
    else:
        o.append(bench_promo_note(ctx, D))
        cap = bench_promo_caption(ctx, D)
    o.append(dtable(['Kind', 'Test', 'Gate or measurement', 'Needs / source'], rows, label_cols=1, widths=['13%', '17%', '46%', '24%'], cls='tight', caption=cap))
    return '\n'.join(o)


def ele_founder_block_row(ctx, D):
    """Electronics founder block: F-1 to F-14 of bench plan v4 section 0 (electronics.json v4) with the 253 (5) status, in full; in the
    promoted build, F-1 to F-14 of bench plan v5 section 0 (the plan of v4.1) with the 266 (7) status, each row in full."""
    cl = D['cl']
    if D['ele']['promo']:
        n = D['ele']['line']
        rows = md_rows_where(ctx, 'BENCH', '0. Founder block', r'F-\d+')
        fbc = []
        for ln, r in rows:
            fid = re.sub(r'\*\*', '', r[0]).strip()
            parts = [md_cell_ln(ctx, 'BENCH', ln, r, j, 'DESIGN', tag_raw='bench plan v5 section 0 (founder block)', label=fid) for j in range(1, min(len(r), 5))]
            fbc.append(Cell(f'<div class="small"><b>{esc(fid)}</b> ' + ' | '.join(tvtxt(t).html for t in parts) + '</div>', parts))
        b7 = cl.clip(n, 7, 'Bench plan v5 does not go to the founders before these corrections.', 'Bench plan v5 does not go to the founders before these corrections.')
        return [Cell('<b>Electronics founder block F-1 to F-14 (bench plan v5 section 0; electronics.json v4.1): action | content | closes or feeds | done when</b>', []),
                cat(Cell(f'<div class="dec"><b>Status:</b> {tvtxt(b7).html} REV-ELEC-4 found F-13 and F-14 executable as written (§12.6); the plan as a '
                         'whole waits for the corrections.</div>', [b7]), *fbc)]
    fb = ctx.raw('ELE', '/bench_plan/founder_block', default=[]) or []
    fbc = []
    for j, x in enumerate(fb):
        t = ctx.v('ELE', f'/bench_plan/founder_block/{j}/action', tag='DESIGN')
        fbc.append(Cell(f'<div class="small"><b>{esc(x.get("id"))}</b> ' + tvtxt(t).html + '</div>', [t]))
    b5 = cl.clip(253, 5, 'bench plan v4 is REVISE', 'before v5.')
    return [Cell('<b>Electronics founder block F-1 to F-14 (bench plan v4 section 0; electronics.json v4)</b>', []),
            cat(Cell(f'<div class="dec"><b>Status:</b> {tvtxt(b5).html} v5 is staged with electronics.json v4.1 and is PENDING REVIEW (§1.4).</div>', [b5]), *fbc)]


def annex_c4(ctx, doc, D, c4):
    """Annex C4: the J-FWD build procedure C4 of mechanical.json v2.4 (= texts v5 C4) step by step, verbatim, with its source lines
    241 (8) C4 and 246 (2) C4 (lead 2026-10-21 14:05Z and 14:30Z; REV-DS-1 D1-06 (c), RA-07)."""
    cl = D['cl']
    o = [f'<h3 id="annex-c4">Annex C4. J-FWD build procedure C4 (every assembly and re-assembly), in full</h3>']
    s = c4.value if isinstance(c4.value, str) else ''
    st = proc_steps(s, 0, 9)
    rows = []
    if not st:
        ctx.issue('WARN', 'C4 procedure: steps 0-9 not found; printed as one text')
        rows.append(['C4', tvtxt(c4)])
    else:
        pre = s[:st[0][1]].strip()
        if pre:
            rows.append(['Scope', tvtxt(part_tv(ctx, c4, pre, 'scope'))])
        for n, (k, i0) in enumerate(st):
            i1 = st[n + 1][1] if n + 1 < len(st) else len(s)
            rows.append([f'Step {k}', tvtxt(part_tv(ctx, c4, s[i0:i1].strip(), f'step {k}'))])
    t5 = ctx.v('TXT5', '/item_C/C4_assembly_step_founder_procedure', tag='LEAD')
    same = ctx.d('identical' if (isinstance(c4.value, str) and t5.value == c4.value) else 'DIFFERENT', '',
                 'string comparison of mechanical.json /jfwd_v352/founder_rules/C4_procedure with texts v5 /item_C/C4_assembly_step_founder_procedure', [c4, t5])
    rows.append(['Check-T5', Cell(f'texts v5 C4 {t5.pill()}{t5.ref()} and the text above: {same.h()}', [same, t5])])
    s241 = cl.clip(241, 8, 'C4: assembly order', 'proof / leak test).')
    s246 = cl.clip(246, 2, 'C4 rewritten:', 'never re-torqued;')
    s254 = cl.clip(254, 2, 'C4 step 1 checks the select-fit pairing record', 'select-fit pairing record', ev='REF', why='a source line of the founder action (the specialist\'s record line, quoted as its reference)')
    rows.append(['Source, 241 (8) C4', cat(tvtxt(s241), gnote('246 (2) rewrote C4: the torque of 241 (8) is replaced by the J-F1 lot torque by method M-T1J (step 7)'))])
    rows.append(['Source, 246 (2) C4', tvtxt(s246)])
    rows.append(['Source, 254 (2)', tvtxt(s254)])
    o.append(dtable(['Step', 'Text (quoted in full)'], rows, widths=['12%', '88%'], cls='tight',
                    caption='mechanical.json /jfwd_v352/founder_rules/C4_procedure (the same text as item_c_tf1_texts_v352_v5.json /item_C/C4: the generator '
                            'checks that they are identical, row "Check-T5"), split at its step numbers; nothing is left out. TO-SELECT, TO-CONFIRM and '
                            'TO-VERIFY items stay as tagged in the text.'))
    if isinstance(c4.value, str) and ctx.raw('TXT5', '/item_C/C4_assembly_step_founder_procedure', default=None) != c4.value:
        ctx.issue('WARN', 'C4: mechanical.json and texts v5 differ')
    return '\n'.join(o)


# ---------------------------------------------------------------------------------------------
# rev1 phase 2 (lead 2026-10-21 14:30:54Z, REV-DS-1 D1-13 and the review-status rows) and the promoted-v4.1 build
# (lead GO 2026-10-21 14:48:44Z, CHANGELOG 266)
# ---------------------------------------------------------------------------------------------
def dq(tv, label=''):
    """A quoted text in full in its own block (founder actions, lead lines)."""
    if isinstance(tv, Cell):
        return tv
    lab = f'<b>{esc(label)}</b> ' if label else ''
    return Cell(f'<div class="dec">{lab}{tvtxt(tv).html}</div>', [tv])


def rx_num(ctx, tv, pattern, unit='', tag=None):
    """A quantity written with a thousands comma (for example '3,100 N·m/rad per axis'): quoted as the source words, with a
    [sentence containing ...] locator, so that the number keeps the digits and the unit of the source and every re-trace reads the
    same words (a [regex] locator would hand '3,100' to a float parser). The class is the class of the quoted text."""
    s = tv.value if isinstance(tv.value, str) else None
    m = re.search(pattern, s) if s else None
    if not m:
        return rx_text(ctx, tv, pattern, unit, tag=tag)
    words = m.group(0)
    words = words[2:] if words.startswith('≥ ') else words
    ev = tag or ((getattr(tv, 'basis_kind', None) or 'LEAD') if tv.ev == 'DECIDED' else tv.ev)
    return TV(ctx, words, '', ev, tv.tag_raw, tv.sid, f'{tv.ptr} [sentence containing "{words}"]')


def eng11_req(ctx, D):
    """ENG-11 (REQ): gimbal axis stiffness, REQUIREMENTS.md §2 row ENG-11 (line 62), created once (§3.3, §12.5)."""
    if 'eng11_req' not in D:
        D['eng11_req'] = md_row(ctx, 'REQ', '2. Top-level', 'ENG-11', 1, tag_col=2)
    return D['eng11_req']


def eng11_spread(ctx, D):
    """ENG-11 spread element on the v3.5.2 R3 FE values of §3.3 (lead 2026-10-21 14:30:54Z, REV-DS-1 D1-13): the half-range over
    mid-range per axis [DERIVED from the SIM values], the +-20 % and the 3,100 N.m/rad hard minimum of the requirement."""
    if 'eng11_spread' in D:
        return D['eng11_spread']
    rq = eng11_req(ctx, D)
    out = {'req': rq, 'lim': rx_text(ctx, rq, r'spread across poses ≤ ±(\d+) %', '%'),
           'hmin': rx_num(ctx, rq, r'≥ ([\d,]+) N·m/rad per axis', 'N·m/rad')}
    kt = D.get('ktab') or {}
    for ax in ('alpha', 'beta'):
        lo, hi = kt.get(ax, (None, None))
        if lo is None or not all(isinstance(t.value, (int, float)) for t in (lo, hi)):
            out[ax] = ctx.missing(f'ENG-11 {ax} spread: the §3.3 FE values are missing')
            continue
        out[ax] = ctx.d(100.0 * (hi.value - lo.value) / (hi.value + lo.value), '%',
                        f'half-range over mid-range of the FE-coupled {ax} axis stiffness over the 17 R3 poses: 100 x (max - min) / (max + min) (§3.3)',
                        [lo, hi], ev='DERIVED')
    D['eng11_spread'] = out
    return out


def eng11_spread_cell(ctx, D):
    """§12.4 / §12.5: the status of the ENG-11 spread element in the lead's words (lead 2026-10-21 14:30:54Z, REV-DS-1 D1-13)."""
    if 'eng11_spread_cell' in D:
        return D['eng11_spread_cell']
    s = eng11_spread(ctx, D)
    i7 = D['cl'].item(188, 7)
    bmin = (D.get('ktab') or {}).get('beta', (None, None))[0]
    tvs = [s['beta'], s['lim'], s['hmin'], i7]
    if bmin is not None:
        tvs.append(bmin)
        bm = bmin.h()
    else:
        mm = ctx.missing('beta minimum (§3.3)')
        tvs.append(mm)
        bm = mm.h()
    html_ = (f'<div class="dec"><b>Spread element:</b> not met on the v3.5.2 R3 FE beta values (±{s["beta"].h(".1f")} half-range over mid-range, '
             f'DERIVED from §3.3; the requirement is ±{s["lim"].h()}); OPEN under 188 (7){i7.ref()}: GNC robustness assessment, then the lead amends the '
             f'requirement or Mechanical stiffens; see §3.3 and open item 11b (§11.2). Owners (188 (7)): GNC (assessment), lead (amendment), '
             f'Mechanical (stiffening). The hard minimum ≥ {s["hmin"].h()} holds on the FE values (beta minimum {bm}).</div>')
    D['eng11_spread_cell'] = Cell(html_, tvs)
    return D['eng11_spread_cell']


def v5c_note(ctx, D):
    """Label of the 188 (7) spread range: the V5c plant, CAD v3.3 (188 (7), 227), with a pointer to the v3.5.2 values of §3.3 (lead 14:30:54Z)."""
    cl = D['cl']
    i7 = cl.item(188, 7)
    p227 = cl.part(227, 'V5c plant (CAD v3.3)')
    kt = D.get('ktab') or {}
    per, tvs = [], [i7, p227]
    for ax in ('alpha', 'beta'):
        lo, hi = kt.get(ax, (None, None))
        if lo is not None:
            per.append(f'{ax} {lo.h(".0f", unit=False, pill=False)}–{hi.h(".0f")}')
            tvs += [lo, hi]
    return gnote(f'the spread range in this sentence is the V5c plant, CAD v3.3 (188 (7){i7.ref()}, 227{p227.ref()}; published in mechanical.json v2.2 per 188 (7)), '
                 'not the v3.5.2 model; the v3.5.2 R3 FE values per axis (§3.3): ' + '; '.join(per), tvs)


def revds1_row(ctx, a, D):
    """REV-DS-1 in the review-status table (lead 2026-10-21 14:30:54Z): the verdict and counts quoted from the review file, the lead's
    status text for this build and, in the promoted build, the line that records the verdict (266 (3))."""
    vd = md_line_starting(ctx, 'RDS1', '1. VERDICT: ACCEPT WITH CORRECTIONS', 'DERIVED', tag_raw='REV-DS-1 review text, section 1')
    nb = md_line_starting(ctx, 'RDS1', 'No finding is BLOCKING.', 'DERIVED', tag_raw='REV-DS-1 review text, section 1')
    nm = md_line_starting(ctx, 'RDS1', 'There are 5 MAJOR findings', 'DERIVED', tag_raw='REV-DS-1 review text, section 1')
    st = ctx.t('generator', 'REV-DS-1 status in this build (text set by the lead 2026-10-21 14:30:54Z)',
               'REV-DS-1 (independent review of the rev1-draft): ACCEPT WITH CORRECTIONS, 0 BLOCKING, 5 MAJOR, 8 MINOR; corrections applied in this build; '
               'the check of this final build is recorded in the CHANGELOG after it.', 'DERIVED',
               tag_raw='status text set by the lead for this build; the counts are those of the review file (section 1)')
    disp = [dq(st)]
    if D['ele']['promo']:
        disp.append(dq(D['cl'].clip(D['ele']['line'], 3, 'REV-DS-1 (independent review of the rev1-draft',
                                    'Every finding ACCEPTED and sent to the author (13:47:38Z, 14:05:35Z, 14:30:54Z).'), f'CHANGELOG {D["ele"]["line"]} (3):'))
    return [Cell('<b>REV-DS-1</b>', []), 'This datasheet: the rev1-draft (PDF 8e7d007d128dfb58, not published)',
            cat(Cell(f'<b>ACCEPT WITH CORRECTIONS</b> {vd.pill()}{vd.ref()}', [vd]), Cell(f'<div class="small">{tvtxt(nb).html} {tvtxt(nm).html}</div>', [nb, nm])),
            cat(*disp)]


def ele41_review_row(ctx, D):
    """REV-ELEC-4 in the review-status table of the promoted-v4.1 build (lead GO 2026-10-21 14:48:44Z; CHANGELOG 266 (4), (6), (7))."""
    e = D['ele']
    n = e['line']
    vd = md_line_starting(ctx, 'RELE4', 'Overall: ACCEPT WITH COMMENTS', 'DERIVED', tag_raw='REV-ELEC-4 review text, section 1')
    return [Cell('<b>REV-ELEC-4</b>', []), 'Electronics v2.12 (firmware v2.12 and SIL; electronics.json v4.1; bench plan v5; BOM v2.4)',
            Cell(f'{tvtxt(vd).html}<div class="small">Review file: reviews/REVIEW-ELECTRONICS-R4.md, sha256/16 '
                 f'{esc(ctx.src("RELE4").sha16 or "MISSING")}{(lambda st: st.ref())(src_tv(ctx, "RELE4"))}; line {n}</div>', [vd]),
            cat(dq(e['verdict_tv'], f'CHANGELOG {n} (4):'), dq(e['carve_tv'], f'Carve-out, {n} (6), verbatim:'), dq(e['promo_tv'], f'{n} (7):'))]


def e4_02_cell(ctx, D):
    """The E4-02 correction that line 266 (7) applies to the 'within 5 % at k = 3' acceptance (bench plan v5, v4.1, the 264 (2) wording)."""
    if 'e4_02' not in D:
        n = D['ele']['line']
        t = D['cl'].clip(n, 7, 'E4-02 (the coefficient-within-5-percent-at-k-3 acceptance', 'with no relight objective claimed)')
        D['e4_02'] = Cell(f'<div class="dec"><b>Corrected by {n} (7), E4-02:</b> {tvtxt(t).html}</div>', [t])
    return D['e4_02']


def bench_promo_note(ctx, D):
    """§12.6 status of bench plan v5 in the promoted build (lead GO 2026-10-21 14:48:44Z: v5 does not go to the founders before the
    266 (7) corrections; REV-DS-1 D1-09: the plan is for information, not for execution)."""
    e = D['ele']
    n = e['line']
    cl = D['cl']
    b6 = cl.clip(n, 7, 'E4-06 (bench plan v5:', 'the C7 stand-DAQ TC added as a stand-only row)')
    b7 = cl.clip(n, 7, 'Bench plan v5 does not go to the founders before these corrections.', 'Bench plan v5 does not go to the founders before these corrections.')
    rv = md_find(ctx, 'RELE4', '1. VERDICT', {0: 'Bench plan v5'}, 1, ev='DERIVED', tag_raw='REV-ELEC-4 verdict table')
    rw = md_find(ctx, 'RELE4', '1. VERDICT', {0: 'Bench plan v5'}, 2, ev='DERIVED', tag_raw='REV-ELEC-4 verdict table')
    return note_box(f'<b>Bench plan v5 (the plan of electronics.json v4.1), for information, not for execution.</b> {inl(b7)} '
                    f'<b>REV-ELEC-4:</b> {inl(rv)} {inl(rw)} <b>The corrections ({n} (7)):</b> {inl(b6)} {inl(e4_02_cell(ctx, D))} '
                    'Under the carve-out the A1 pad is NO-GO and the stand relight (T4 among it) waits for v2.13 (§10.0). The CF-4 / B-BLEED-1 purge acceptance '
                    'and re-set rule: founder row in §12.3 (and §7.5).', 'warn')


def bench_promo_caption(ctx, D):
    n = D['ele']['line']
    return (f'Bench plan v5 section 1 ({esc(src_label(ctx, "BENCH"))}): for information, not for execution: it does not go to the founders before the '
            f'corrections of CHANGELOG {n} (7). REQ §4: early purchases. CF-4 and T1-T4 criteria: §7.9; the CF-4 / B-BLEED-1 purge acceptance and re-set rule: '
            '§12.3. None has been run. Cost: TO-QUOTE, delivered to Sønderborg, DK-6400.')


def bench_row_notes(ctx, D, test_txt):
    """Row notes of the promoted build on bench plan v5 rows that line 266 (7) corrects (E4-02, E4-06)."""
    n = D['ele']['line']
    cl = D['cl']
    out = []
    if 'B-PC-1' in test_txt or 'B-TC-1' in test_txt:
        out.append(e4_02_cell(ctx, D))
        t = cl.clip(n, 6, 'Suspended until v2.13, and marked so wherever shown:', 'the B-PC-1 / B-TC-1 TC4 rows.')
        out.append(Cell(f'<span class="ev ev-status">SUSPENDED UNTIL v2.13 ({n} (6))</span> the TC4 rows of B-PC-1 / B-TC-1{t.ref()}', [t]))
    if 'T1-T4' in test_txt:
        t = cl.clip(n, 7, 'T4 restated as a relight-latency demonstration', 'waiting for v2.13')
        out.append(gnote(f'{n} (7), E4-06 (2): T4 restated as a relight-latency demonstration from a soaked state, its length from Combustion\'s T4 re-run, '
                         f'waiting for v2.13{t.ref()}', [t]))
    return out


# ---------------------------------------------------------------------------------------------
# section 13.3: the contradiction register (rev1 phase 2: lead 2026-10-21 13:24Z, 13:47:38Z (D1-04) and the promoted build)
# ---------------------------------------------------------------------------------------------
def ele4_v(ctx, D, ptr, unit=''):
    """A v2.11 value of electronics.json v4 for a register side: from the §10 object in the default build; from the kept v4 file
    (staging_v2.11/results/electronics_v4.json, source ELE4) in the promoted build. A v2.11 BASE constant is a design value (D1-03)."""
    if not D['ele']['promo']:
        t = (D.get('ele_tv') or {}).get(ptr)
        if t is not None:
            return t
        t = ctx.v('ELE', ptr, unit)
    else:
        t = ctx.v('ELE4', ptr, unit)
    if any(k in ptr for k in ('kIgnBaseCheck_Pa', 'coast_rezero/max', 'limits_v2p11/14/')):
        as_design(t, BASE_BASIS, BASE_WHY)
    return t


def register_contradictions(ctx, a, D):
    cl = D['cl']
    promo = D['ele']['promo']
    n = D['ele']['line']
    # C-01: FEA3D-2 text vs the rows-v8 matrix of record (HW-101 J-FWD u cell)
    f2 = md_find(ctx, 'F3D', '13. Open items and owners', {0: '2'}, 2, ev='DERIVED', tag_raw='FEA3D-2 report §13 item 2')
    ch = ctx.v('MMXD', '/cell_value_changes/0', tag='DERIVED')
    if isinstance(f2.value, str) and '+0.301' in f2.value and isinstance(ch.value, dict) and ch.value.get('new_MS_y_MS_u', [None, None])[1] == 0.278:
        ctx.contra('C-01', 'HW-101 J-FWD u cell: FEA3D-2 report text vs the rows-v8 matrix of record',
                   [('FEA3D-2 report §13 item 2', f2), ('rows-v8 matrix delta', ch), ('rows-v8 why', ctx.v('MMXD', '/why', tag='DERIVED'))],
                   'the rows-v8 matrix value (Eq. 22 governing, rows v8; §9.5.3)', 'the report text predates the re-map; Mechanical / FEA3D to align the report wording.',
                   governs=[('rows-v8 matrix of record', src_tv(ctx, 'MMX')), ('CHANGELOG 255 (3)', cl.clip(255, 3, 'It supersedes only', 'stands as published.'))],
                   status='The matrix of record governs; the FEA3D-2 report text is stale. The matrix value is shown (§9.5.3). OPEN: Mechanical / FEA3D align the report wording.')
    # C-02: electronics.json status text vs the promotion (v4: line 253; v4.1: line 266 (7))
    st = ctx.v('ELE', '/status', tag='DESIGN')
    if isinstance(st.value, str) and 'STAGED for the lead' in st.value:
        if not promo:
            ctx.contra('C-02', 'electronics.json v4 status: "STAGED" vs promoted',
                       [('electronics.json /status', st), ('CHANGELOG 253 (5)', cl.clip(253, 5, 'PROMOTED 07:05:56Z', 'electronics_v3.json).'))],
                       'promoted v4 is the published interface (OVR-10)', 'Electronics v2.12 (electronics.json v4.1) to restate the status text.',
                       governs=[('CHANGELOG 253 (5)', cl.clip(253, 5, 'PROMOTED 07:05:56Z', 'electronics_v3.json).')),
                                ('CHANGELOG 264 (1)', cl.clip(264, 1, 'interfaces/electronics.json stays v4', 'as PENDING REVIEW.'))],
                       status='electronics.json v4 is the source of record (line 253); its internal STAGED status string is stale and is annotated (OVR-10). '
                              'OPEN: Electronics restates it (v4.1 is PENDING REVIEW).')
        else:
            g7 = cl.clip(n, 7, 'Until v4.2 this line governs v4.1 where they differ: its STAGED status text is superseded;',
                         'Until v4.2 this line governs v4.1 where they differ: its STAGED status text is superseded;')
            ctx.contra('C-02', 'electronics.json v4.1 status: "STAGED" vs promoted (line 266)',
                       [('electronics.json v4.1 /status', st), (f'CHANGELOG {n} (7)', D['ele']['promo_tv'])],
                       f'promoted v4.1 is the published interface ({n} (7); OVR-10)', 'Electronics restates the status text at v4.2.',
                       governs=[(f'CHANGELOG {n} (7)', D['ele']['promo_tv']), (f'CHANGELOG {n} (7), the governing clause', g7)],
                       status=f'Line {n} (7) governs: electronics.json v4.1 is the source of record and its internal STAGED status string is stale; it is '
                              'annotated (OVR-10). OPEN: Electronics restates it at v4.2.')
    # C-03: combustion datasheet note "until gnc.json v3.2" vs v3.2 published without a 210 m A1 record
    nt = md_line_starting(ctx, 'DSIC', 'A1 apogee target 210 m is decided', 'DESIGN', tag_raw='combustion datasheet inputs note')
    g11h = md_find(ctx, 'DSIG', None, {0: '11h'}, 2, ev='TO-VERIFY', tag_raw='GNC datasheet inputs row 11h')
    if isinstance(nt.value, str) and 'until gnc.json v3.2' in nt.value:
        ctx.contra('C-03', 'A1 mission-burn records: "300 m comparators until gnc.json v3.2" vs v3.2 published without a 210 m record',
                   [('combustion datasheet inputs note', nt), ('GNC datasheet inputs 11h', g11h), ('CHANGELOG 260 (1)', cl.part(260, 'GNC.JSON v3.2 PUBLISHED'))],
                   'the 300 m A1 records stay the comparators; the 210 m A1 duty-cycle record is OPEN (GNC)', 'GNC to fly the 210 m record; Combustion to restate the note.',
                   governs=[('GNC datasheet inputs 11h', g11h), ('CHANGELOG 213', cl.part(213, 'B1 still governs thermal and erosion sizing'))],
                   status='OPEN (GNC): the 210 m A1 mission-burn and duty-cycle record is not flown (row 11h). The 300 m records stay, labelled as 300 m '
                          'comparators; B1 governs the thermal and erosion sizing. No 210 m value is invented here.')
    # C-04: BOM / hardware strings superseded by drawing-note rulings
    tc2 = D['bom_by_pn'].get('ENG-TC-02')
    hw1 = D['bom_by_pn'].get('ENG-HW-101')
    if tc2 is not None and '57.20 f7' in (tc2.l.get('notes') or ''):
        cl2 = next(x.strip() for x in tc2.l['notes'].split(';') if '57.20 f7' in x)
        n2 = ctx.t('BOM', ptr_join('lines', tc2.idx, 'notes'), cl2, 'DESIGN', tag_raw='BOM line notes (clause quoted)',
                   note='the clause containing "57.20 f7" of the notes string at this pointer, quoted verbatim')
        ctx.contra('C-04', 'TC-02 plug fit: BOM notes "57.20 f7" vs the R2-B select fit',
                   [('BOM ENG-TC-02 notes', n2), ('CHANGELOG 254 (1)', r2b_ruling(D)),
                    ('matrix TC-01 J-FWD cell (drawn fit)', md_find(ctx, 'MMXMD', 'Negative cells and their classes', {0: 'TC-01', 1: 'J-FWD'}, 2, ev='CALC',
                                                                    tag_raw=MX_TAG + '; negative-cell table'))],
                   'R2-B select fit; the drawn 57.20 f7 fit is FOUND NEGATIVE', 'Mechanical: drawing texts carry R2-B (texts v5 C9 (6)); the BOM note is generated from the part script (no geometry change).',
                   governs=[('CHANGELOG 254 (1), R2-B', r2b_ruling(D))],
                   status='The R2-B select fit governs (line 254); the BOM fit note is superseded and the drawn fit is FOUND NEGATIVE. '
                          'OPEN: Mechanical restates the BOM note (generated from the part script; no geometry change). See also C-11.')
    if hw1 is not None and '60 bar abs' in (hw1.l.get('notes') or ''):
        cl1 = next(x.strip() for x in hw1.l['notes'].split(';') if '60 bar abs' in x)
        n1 = ctx.t('BOM', ptr_join('hardware', 'lines', hw1.idx, 'notes'), cl1, 'DESIGN', tag_raw='BOM hardware notes (clause quoted)',
                   note='the clause containing "60 bar abs" of the notes string at this pointer, quoted verbatim')
        ctx.contra('C-05', 'HW-101 action: "after any Pc above 60 bar abs" vs the Q_JFWD replace rule',
                   [('BOM ENG-HW-101 notes', n1), ('combustion.json z3_jfwd_rulings_v2p4d', ctx.v('CMB', '/z3_jfwd_rulings_v2p4d/v/jfwd_replace_rule/replaces', tag='LEAD'))],
                   'the Q_JFWD rule (LEAD 258 (3)); the BOM string is superseded (no hardware-data, BOM or geometry edit)', 'Mechanical to restate the hardware string at the next hardware-data revision.',
                   governs=[('combustion.json z3_jfwd_rulings_v2p4d (LEAD 258 (3))', ctx.v('CMB', '/z3_jfwd_rulings_v2p4d/v/jfwd_replace_rule/replaces', tag='LEAD')),
                            ('CHANGELOG 259 (6)', cl.clip(259, 6, 'no CAD, hardware-data or BOM edit', 'superseded by the drawing texts v2.', ev='REF',
                                                         why='Mechanical record that the string is superseded; it states no value'))],
                   status='The Q_JFWD replace rule (258 (3)) governs; line 259 (6) states that the HW-101 string is superseded by the drawing texts v2. '
                          'OPEN: Mechanical restates the hardware string at the next hardware-data revision.')
    # C-06: T4 rows vs the re-size
    t4 = md_line_starting(ctx, 'T14', '| T4, DC-D duty cycle', 'SIM', tag_raw='T1-T4 spec §3 T4 row')
    ctx.contra('C-06', 'T4: the T1-T4 rows (DC-D, 7.02 kg) vs the re-sized shortest firing (about 2.0 kg)',
               [('T1-T4 spec T4 row', t4), ('combustion.json t4_duration_note_v2p4c', ctx.v('CMB', '/t4_duration_note_v2p4c/v/status', tag='LEAD')),
                ('CHANGELOG 261 (2)', cl.item(261, 2))],
               'T4 re-sized (LEAD 261 (2)); the rows stay the DC-D computation [SIM] until re-run', 'Combustion re-runs the T4 rows (OPEN; not in the finish run).',
               governs=[('CHANGELOG 261 (2)', cl.item(261, 2)), ('CHANGELOG 264 (5)', cl.item(264, 5))],
               status='The re-size governs (261 (2), 264 (5)); the published T4 rows (DC-D) are superseded. OPEN (OI-T4-RESIZE): the T4 re-run sets the length. '
                      'See also C-15.')
    # C-07: bench plan path named in electronics.json vs the hub tree
    bp = ctx.v('ELE', '/bench_plan/file', tag='DESIGN')
    mb = re.match(r'(06-electronics/docs/bench_plan_v\d+\.md)', bp.value) if isinstance(bp.value, str) else None
    if mb and not os.path.isfile(os.path.join(a.hub, mb.group(1))):
        loc = TV(ctx, ctx.src('BENCH').path.replace(a.hub + '/', ''), '', 'DERIVED', 'generator: file found at this path (sha256/16 ' + (ctx.src('BENCH').sha16 or '') + ')', 'BENCH', '(file)')
        ctx.contra('C-07', f'Bench plan {ctx.src("BENCH").version or ""} location: electronics.json path vs the hub tree',
                   [('electronics.json /bench_plan/file', bp), ('file in the hub', loc)], 'the staging copy (same sha as named)', 'Electronics to state the hub path.',
                   governs=[('file in the hub', loc)],
                   status='The hub tree governs; the path is printed as it is in the hub (§15.2). OPEN: Electronics states the hub path.')
    # C-08: CF-4 baseline text
    cb = ctx.v('CMB', '/cf4_gate/v/baseline_v2p4b', tag='DESIGN')
    if isinstance(cb.value, str) and 'not yet published' in cb.value:
        ctx.contra('C-08', 'CF-4 baseline: "mechanical.json v2.2 not yet published" vs mechanical.json v2.4 published',
                   [('combustion.json /cf4_gate/baseline_v2p4b', cb), ('mechanical.json version', ctx.v('MEC', '/version', tag='DESIGN'))],
                   'mechanical.json v2.4 is published; the CF-4 bleed-path basis stays the frozen v3.5.1 path as written', 'Combustion to restate at the next text revision.',
                   governs=[('mechanical.json version', ctx.v('MEC', '/version', tag='DESIGN'))],
                   status='mechanical.json v2.4 is current; the CF-4 text predates it (the bleed-path basis stays the frozen v3.5.1 path as written). '
                          'OPEN: Combustion restates it at the next text revision.')
    # C-09: BOM mass sum vs the generator sum. Retired when they agree: the ID is kept so that the IDs of the draft stay stable (D1-04)
    bs, gs = D['bom_mass_sum'], D['bom_sum_tv']
    if isinstance(bs.value, (int, float)) and isinstance(gs.value, (int, float)) and abs(bs.value - gs.value) > 5e-4:
        ctx.contra('C-09', 'BOM mass_sum_kg vs the sum of its lines', [('BOM /mass_sum_kg', bs), ('generator sum', gs)], 'both shown (§4.4)', 'Mechanical to check the BOM header sum.',
                   status='Both are shown (§4.4). OPEN: Mechanical checks the BOM header sum.')
    else:
        ctx.contra('C-09', 'BOM mass_sum_kg vs the sum of its lines', [('BOM /mass_sum_kg', bs), ('generator sum of the BOM lines', gs)],
                   'no disagreement at this build', 'none',
                   status='RETIRED: the two agree at this build (difference below 0.0005 kg; §4.4), so there is no contradiction. The ID is kept, and not '
                          'reused, so that the IDs of the rev1-draft stay valid (REV-DS-1 D1-04).')
        ctx.contradictions[-1]['retired'] = True
    # C-10: P_torch transducer: electronics.json selection vs lead 264 (4)
    sel = ctx.v('ELE', '/sensors/pressure_transducers/selection')
    p264 = cl.clip(264, 4, 'P_torch (J901', 'same part as P_mid (ENG-BL-08) and C1.')
    if isinstance(sel.value, dict) and '070BG' in str(sel.value.get('P_TORCH')):
        gov = [('CHANGELOG 264 (4)', p264)]
        if promo:
            f7 = cl.clip(n, 7, 'the 264 (1)-(8) folds such as P_TORCH XTL-190SM-2000A', 'the 264 (1)-(8) folds such as P_TORCH XTL-190SM-2000A')
            gov.append((f'CHANGELOG {n} (7), E4-05 (7)', f7))
        ver = 'v4.1' if promo else 'v4'
        ctx.contra('C-10', f'P_torch transducer: electronics.json {ver} (TE M3234-000005-070BG) vs lead 264 (4) (C1-family Kulite XTL-190SM-2000A)',
                   [(f'electronics.json {ver} /sensors/pressure_transducers/selection', sel), ('CHANGELOG 264 (4)', p264)],
                   'lead 264 (4): the C1-family Kulite; its proof [DATASHEET] and the required proof [DERIVED] are quoted with their tags in §10.2',
                   'Electronics: thresholds re-based and the selection restated (OPEN).', governs=gov,
                   status='Line 264 (4) governs: the C1-family Kulite XTL-190SM-2000A, its proof [DATASHEET] against the required proof [DERIVED] (§2.3). '
                          f'The electronics.json {ver} P_torch entry is superseded for the design'
                          + (f' (line {n} (7) applies the 264 fold, E4-05 (7); the file keeps the old entry until v4.2)' if promo else '')
                          + '. OPEN (OI-PTORCH-PROOF): the threshold re-base' + (' (E4-N04, queued with v2.13, 266 (8))' if promo else '') + '. See also C-14.')
    # C-11: the line-240 select-fit band vs R2-B (lead 13:47:38Z, D1-04)
    lo, hi, bd, r = r2b_band(ctx, D)
    sides = []
    if D.get('neg_band_tv') is not None:
        sides.append(('margin matrix negative-cell table, TC-01 J-FWD closure (the line-240 band)', D['neg_band_tv']))
    if D.get('f3d_item1'):
        sides.append(('FEA3D-2 report §13 item 1, closure (the line-240 band)', D['f3d_item1'][3]))
    sides.append(('CHANGELOG 254 (1), LEAD RULING R2-B', r))
    ctx.contra('C-11', 'TC-01 J-FWD select-fit band: the line-240 band [0.040, 0.0761] mm quoted in the matrix and the FEA3D-2 report vs R2-B',
               sides, 'R2-B (254 (1))', 'none: the band re-size is done; the texts quote the older band',
               governs=[('CHANGELOG 254 (1), R2-B', r), ('band file of record', bd)],
               status=f'R2-B governs (254 (1)): the select-fit band is the R2-B band. Band re-size done (band v1 {ctx.src("BAND").sha16}); the seat-line P+Q '
                      'stays a found negative at the drawn fit (§9.3, §9.10 item 1). See also C-04.')
    # C-12: the 2.55 s both-open cap of v2.11 vs the 256 (2) FINAL purge (lead 13:47:38Z, D1-02 / D1-04)
    p = purge_parts(ctx, D)
    capv = ele4_v(ctx, D, '/limits_v2p11/4/value', 's')
    w, wt = impl_txt(D, 'purge_status', 'implemented in v4.1, PENDING REVIEW; the measured-time form is open after CF-4 / B-BLEED-1',
                     'implemented in v4.1, promoted, line {n}; the measured-time form is open after CF-4 / B-BLEED-1')
    ctx.contra('C-12', 'Purge both-open cap: 2.55 s (v2.11, electronics.json v4) vs the 256 (2) FINAL 2.43 s flow / 2.39 s cap',
               [('electronics.json v4 /limits_v2p11/4 (v2.11 cap)' + (' [kept v4 file]' if promo else ''), capv), ('CHANGELOG 203 (3)', p['i203']),
                ('CHANGELOG 256 (2)', p['i256'])],
               '256 (2) FINAL', 'Electronics implements the FINAL values (v2.12 / v4.1).',
               governs=[('CHANGELOG 256 (2)', p['i256']), ('CHANGELOG 257 (2)', p['i257']), ('CHANGELOG 258 (2)', p['i258'])] + [('implementation record', t) for t in wt],
               status=f'256 (2) governs (2.43 s flow, 2.39 s cap, conditions (a)-(d), (d1), (d2) of 256 (2) / 257 (2) / 258 (2)); {w}.')
    # C-13: the v2.11 BASE constants vs 264 (2) (lead 13:47:38Z, D1-03 / D1-04)
    r3 = r301_vals(ctx, D)
    bcv = ele4_v(ctx, D, '/light_rule/kIgnBaseCheck_Pa', 'Pa')
    rzv = ele4_v(ctx, D, '/sensors/pressure_transducers/coast_rezero/max', 'Pa')
    w13, wt13 = impl_txt(D, 'c13_status', 'v4.1 implementation PENDING REVIEW (REV-ELEC-4)', 'v4.1 implementation promoted, line {n}')
    ctx.contra('C-13', 'C1 re-zero and BASE constants: v2.11 kIgnBaseCheck_Pa 70000 Pa / kPcRezeroMax_Pa 30000 Pa (not accepted, 253 (5)) vs 264 (2)',
               [('electronics.json v4 /light_rule/kIgnBaseCheck_Pa (v2.11)' + (' [kept v4 file]' if promo else ''), bcv),
                ('electronics.json v4 coast re-zero max, kPcRezeroMax_Pa (v2.11)' + (' [kept v4 file]' if promo else ''), rzv),
                ('CHANGELOG 264 (2)', r3['lim'])],
               '264 (2)', 'Electronics implements 264 (2) (v2.12 / v4.1).',
               governs=[('CHANGELOG 253 (5)', r3['na']), ('CHANGELOG 264 (2)', r3['lim'])] + [('implementation record', t) for t in wt13],
               status=f'253 (5) did not accept the v2.11 values; 264 (2) governs (kPcRezeroMax_Pa 0.30 bar on the compensated residual, kIgnBaseCheck_Pa '
                      f'0.76 / 0.46 bar default / B-PC-1-shown build); {w13}.')
    # C-14: the combustion-side P_torch texts vs 264 (4) (D1-04)
    c14 = list(D.get('c14_sides') or [])
    c14.append(('CHANGELOG 264 (4)', p264))
    ctx.contra('C-14', 'P_torch on the combustion side: the 070BG / "reselected" transducer texts vs lead 264 (4)',
               c14, '264 (4)', 'Electronics re-bases the torch thresholds; Combustion restates its texts.',
               governs=[('CHANGELOG 264 (4)', p264)],
               status='264 (4) governs: P_torch is the C1-family Kulite XTL-190SM-2000A. The re-base of the torch thresholds is OPEN (OI-PTORCH-PROOF; §12.4)'
                      + (f'; it needs compensation or a photodiode-guarded gate and the torch local heat first (E4-N04, {n} (8))' if promo else '') + '. See also C-10.')
    # C-15: the relight length of 261 (2) vs 264 (5) (D1-04)
    i5 = cl.item(264, 5)
    t4d = cl.clip(264, 5, 'T4 then demonstrates', 'say so.')
    gov15 = [('CHANGELOG 264 (5)', i5)]
    if promo:
        gov15.append((f'CHANGELOG {n} (7), E4-06 (2)', cl.clip(n, 7, 'T4 restated as a relight-latency demonstration', 'waiting for v2.13')))
    ctx.contra('C-15', 'T4 relight: about 4.6 s after the B1 burn (261 (2)) vs the shorter relight of 264 (5)',
               [('CHANGELOG 261 (2)', cl.item(261, 2)), ('CHANGELOG 264 (5)', i5), ('CHANGELOG 264 (5), what T4 demonstrates', t4d)],
               '264 (5)', 'Combustion sets the length in the T4 re-run.', governs=gov15,
               status='264 (5) governs: the shorter relight is adopted and T4 demonstrates relight latency from a soaked state. The length is OPEN: Combustion '
                      'sets it in the T4 re-run with Mechanical\'s soak-back (OI-T4-RESIZE)' + (f'; T4 is a stand relight and waits for v2.13 ({n} (6))' if promo else '')
                      + '. See also C-06.')
    # C-16: OI-A1-BASE-AMB (electronics.json open issue) vs 264 (3) (D1-04)
    oi = (D.get('ele_oi_tv') or {}).get('OI-A1-BASE-AMB')
    i3 = cl.item(264, 3)
    nr = cl.item(264, 2, contains='NEW RULE')
    if oi is not None:
        gov16 = [('CHANGELOG 264 (3)', i3)]
        if promo:
            gov16.append((f'CHANGELOG {n} (6)', D['ele']['susp_tv']))
        ctx.contra('C-16', 'OI-A1-BASE-AMB: listed open in electronics.json vs closed by 264 (3)',
                   [('electronics.json /open_issues OI-A1-BASE-AMB, issue', oi['issue']), ('electronics.json OI-A1-BASE-AMB, closure', oi['closure']),
                    ('CHANGELOG 264 (3)', i3)],
                   '264 (3)', 'Electronics closes the item in the interface file.', governs=gov16,
                   status='Closed: 264 (3) adopts the A1 BASE_AMB outcome as built; the item is listed under the closed group in §10.9. Only the residual that a '
                          'lead line names stays open: the A1 pad no-go rule of 264 (2) (NEW RULE, §12.4)'
                          + (f'. The evidence (not the decision) of 264 (3) is SUSPENDED UNTIL v2.13 and is re-shown on v2.13 ({n} (6))' if promo else '') + '.')
        D['c16_nr'] = nr


def sec_contradictions(ctx, doc, a, D):
    """Section 13 (v0.3.1): every contradiction with its sides, its governing source and its status (lead 2026-10-21 13:24Z); retired IDs
    are kept with the reason (REV-DS-1 D1-04)."""
    o = [doc.h(1, '13 Decision overrides and the contradiction register')]
    o.append(sec_overrides(ctx, doc, a, D))
    o.append(doc.h(2, '13.3 Contradiction register'))
    nret = sum(1 for c in ctx.contradictions if c.get('retired'))
    o.append('<p>Each entry quotes every side, then the source that governs and the status of the disagreement. An entry is generated when the '
             'current sources disagree; a governing source already quoted under the sides is referenced, not repeated. An ID is never reused: an '
             f'entry whose sides agree at this build is kept as RETIRED, with the reason ({nret} at this build). "See also" links related entries.</p>')
    rows = []
    for c in sorted(ctx.contradictions, key=lambda c: int(re.sub(r'\D', '', c['id']) or 0)):
        sides = cat(*[Cell(f'<div class="dec"><b>{esc(sd[0])}:</b> {(sd[1].h() if not isinstance(sd[1].value, (str, dict, list)) and sd[1].value is not None else tvtxt(sd[1], sd[2] if len(sd) > 2 else 600).html)}</div>', [sd[1]])
                      for sd in c['sides']])
        side_ids = {sd[1].tid for sd in c['sides']}
        gl = []
        for lab, tv in c.get('governs') or []:
            if tv.tid in side_ids:
                gl.append(Cell(f'<div class="dec"><b>{esc(lab)}</b> (quoted under the sides) {tv.pill()}{tv.ref()}</div>', [tv]))
            else:
                body = tv.h() if (tv.value is not None and not isinstance(tv.value, (str, dict, list))) else tvtxt(tv, 600).html
                gl.append(Cell(f'<div class="dec"><b>{esc(lab)}:</b> {body}</div>', [tv]))
        gov = cat(*gl) if gl else Cell('–', [])
        txt = c.get('status') or f'{c["newest"]}. {c["resolution"]}'
        res = ctx.t('generator', f'contradiction {c["id"]} status', txt, 'DERIVED', tag_raw='generator summary of the cited sides and the governing source')
        idc = f'<b>{esc(c["id"])}</b>' + (' <span class="ev ev-status">RETIRED</span>' if c.get('retired') else '')
        rows.append([Cell(f'{idc}<div class="small">{esc(c["title"])}</div>', []), sides, gov, Cell(f'{esc(res.value)} {res.pill()}{res.ref()}', [res])])
    if rows:
        o.append(dtable(['ID', 'Sides (quoted)', 'Governing source', 'Status'], rows, widths=['14%', '42%', '24%', '20%']))
    else:
        o.append('<p>No contradiction detected in the current sources.</p>')
    return '\n'.join(o)

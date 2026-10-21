# ---------------------------------------------------------------------------------------------
# promoted-v4.1 build (v0.3.1; lead GO 2026-10-21 14:48:44Z; CHANGELOG 266): electronics.json v4.1 is the source of record (266 (7));
# option (b) is carved out of every start with ignition until a reviewed v2.13 delta (266 (6)). Per-parameter labels replace PENDING
# REVIEW: SUSPENDED UNTIL v2.13 (266 (6)) and ACCEPTED (REV-ELEC-4, line 266); every other value keeps its own evidence tag. Where line
# 266 (7) corrects a v4.1 item, the corrected text (REV-ELEC-4 section 2, as written in the review) is printed at the item with 266 (7).
# ---------------------------------------------------------------------------------------------
ACC_CONST = {'kIgnBaseCheck_Pa': 'kIgnBaseCheck_Pa 0.76 / 0.46 bar', 'kHbleedCap_s': 'purge FINAL 2.43 / 2.39 s with rule (d), (d1), (d2)',
             'kPurgeFlow_s': 'purge FINAL 2.43 / 2.39 s with rule (d), (d1), (d2)', 'kPtorchRezeroMax_Pa': 're-base OPEN, 264 (4)', 'kJfwdLsRawAbs_Pa': 'JFWD_LS'}
RV4_TAG = 'REV-ELEC-4 review text (section 2), the correction that CHANGELOG line 266 (7) applies to v4.1 as written in the review'


def lab_susp(D, what=''):
    e = D['ele']
    return Cell(f'<span class="ev ev-status">SUSPENDED UNTIL v2.13 ({e["line"]} (6))</span>{e["susp_tv"].ref()}'
                + (f' <span class="small">{esc(what)}</span>' if what else ''), [e['susp_tv']])


def lab_acc(D, what=''):
    e = D['ele']
    return Cell(f'<span class="ev ev-status">ACCEPTED (REV-ELEC-4, line {e["line"]})</span>{e["acc_tv"].ref()}'
                + (f' <span class="small">{esc(what)}</span>' if what else ''), [e['acc_tv']])


def rv4(ctx, starts, after='E4-05'):
    """A line of the REV-ELEC-4 review text (RELE4), after its finding heading, quoted in full."""
    return md_line_starting(ctx, 'RELE4', starts, 'DERIVED', tag_raw=RV4_TAG, after_heading=after)


def corr(ctx, D, tv, label):
    """'Corrected by 266 (7), <label>:' + the quoted correction."""
    return Cell(f'<div class="dec"><b>Corrected by {D["ele"]["line"]} (7), {esc(label)}:</b> {tvtxt(tv).html}</div>', [tv])


def ele41_head_note(ctx, doc, D):
    """§10.0: the status of electronics.json v4.1 under line 266, every text quoted from that line."""
    e = D['ele']
    n = e['line']
    o = [note_box(f'<b>electronics.json v4.1 (firmware v2.12, SIL only) is the published interface and the source of record of this section (CHANGELOG {n} (7)).</b> '
                  f'Line {n} governs v4.1 where they differ. The labels at the values: <span class="ev ev-status">SUSPENDED UNTIL v2.13 ({n} (6))</span> and '
                  f'<span class="ev ev-status">ACCEPTED (REV-ELEC-4, line {n})</span>, as listed in {n} (6); every other value keeps its own evidence tag. Where '
                  f'line {n} (7) corrects a v4.1 item, the corrected text is printed at the item, quoted from the REV-ELEC-4 review as {n} (7) applies it. '
                  'SIL and CALC evidence only: no hardware exists.', 'warn')]
    o.append(doc.h(2, f'10.0 Status of electronics.json v4.1 under line {n}'))
    rows = [[f'Promotion ({n} (7))', dq(e['promo_tv'])],
            [f'REV-ELEC-4 verdict ({n} (4))', dq(e['verdict_tv'])],
            [f'Carve-out ({n} (6), verbatim)', cat(dq(e['carve_tv']))],
            [f'Consequences ({n} (6))', dq(e['cons_tv'])],
            [f'SUSPENDED UNTIL v2.13 ({n} (6))', dq(e['susp_tv'])],
            [f'ACCEPTED (REV-ELEC-4, line {n})', dq(e['acc_tv'])],
            [f'Corrections that line {n} (7) applies to v4.1', dq(e['gov_tv'])],
            [f'E4-01, the MAJOR finding ({n} (5))', dq(e['e401_tv'])],
            [f'Queued and routed ({n} (8))', cat(dq(e['q8_tv']), dq(e['routed_tv']))]]
    o.append(dtable(['Item', f'Text of CHANGELOG line {n} (quoted in full)'], rows, widths=['22%', '78%'], cls='tight',
                    caption=f'CHANGELOG line {n} (lead). Each item is a lead decision; the numbers it quotes keep their own tags. Not physical approval.'))
    return '\n'.join(o)


def ele41_const_notes(ctx, D, cname, t):
    """Labels of a v4.1 firmware constant (266 (6)) and the basis of the two 264 (2) constants."""
    n = D['ele']['line']
    out = []
    if cname == 'kIgnBaseCheck_Pa' and t.ev == 'DECIDED':
        t.basis = 'Lead decision, line 264 (2) (kIgnBaseCheck_Pa 0.76 / 0.46 bar, default / B-PC-1-shown build)'
    if cname == 'kPcRezeroMax_Pa' and t.ev == 'DECIDED':
        t.basis = f'Lead decision, line 264 (2) (kPcRezeroMax_Pa stays 0.30 bar on the compensated residual); v4.1 is the source of record ({n} (7))'
    if cname in ACC_CONST:
        out.append(lab_acc(D, ACC_CONST[cname]))
    if cname == 'kIgnBaseCheck_Pa':
        out.append(lab_susp(D, 'the kIgnBaseDrift 0.06 bar basis for any relight'))
    return out


def ele41_limit_notes(ctx, D, k):
    """Corrections of line 266 (7) on the basis texts of the limit rows of v4.1 /limits_v2p11 (REV-ELEC-4 E4-05 (1), (2), (4)); the
    labels of 266 (6) are on the value cells."""
    if k == 4:
        return [corr(ctx, D, rv4(ctx, '1. limits_v2p11[4]: the basis text is stale'), 'E4-05 (1)')]
    if k == 14:
        return [corr(ctx, D, rv4(ctx, '2. limits_v2p11[14]: the basis'), 'E4-05 (2)')]
    if k == 7:
        return [corr(ctx, D, rv4(ctx, '4. limits_v2p11[7] still says'), 'E4-05 (4)')]
    return []


def ele41_missing_limits(ctx, D):
    """The limit rows that v4.1 lacks (REV-ELEC-4 E4-05 (3), applied by 266 (7)), each with its label."""
    n = D['ele']['line']
    head = rv4(ctx, '3. Missing limit rows, each with its value, tag and source:')
    rows = []
    for starts, lab in (('the seat constants (kPcSeatCoefMax_PaPerK', [lab_susp(D, 'option (b) firmware rows')]),
                        ('kIgnBaseDrift 0.06 bar;', [lab_susp(D, 'the basis for any relight'), lab_acc(D, 'as a part of kIgnBaseCheck_Pa 0.76 / 0.46 bar')]),
                        ('kPtorchRezeroMax_Pa 0.60 bar;', [lab_acc(D, 're-base OPEN, 264 (4)')]),
                        ('kJfwdLsRawAbs 47.5 bar abs.', [lab_acc(D, 'JFWD_LS'),
                                                         gnote(f'E4-N03: 47.5 against 47.75 bar abs, TO-VERIFY ({n} (8))',
                                                               [D['cl'].clip(n, 8, 'E4-N03 (47.5 against 47.75 bar abs, TO-VERIFY)',
                                                                             'E4-N03 (47.5 against 47.75 bar abs, TO-VERIFY)')])])):
        t = rv4(ctx, starts)
        rows.append([tvtxt(t), cat(*lab)])
    return dtable([f'Limit row that v4.1 lacks (REV-ELEC-4 E4-05 (3), applied by {n} (7))', 'Label'], rows, widths=['70%', '30%'], cls='tight',
                  caption=f'{tvtxt(head).html} The values are firmware v2.12 config.h constants as the review lists them; v4.2 adds the rows.')


def ele41_fw_rows(ctx, D, E):
    """§10.1 additions: firmware v2.12 tests and the REV-ELEC-4 reproduction (266 (4))."""
    n = D['ele']['line']
    rep = D['cl'].clip(n, 4, 'Reproduction [CALC / SIM, a repeat]', 'as predicted.')
    return [['Firmware v2.12 unit tests (SIL)', cat(tvtxt(ctx.v(E, '/firmware/v2p12/tests/test_core', tag='SIM')), ' / no hooks: ',
                                                    tvtxt(ctx.v(E, '/firmware/v2p12/tests/test_core_nohooks', tag='SIM')))],
            [f'REV-ELEC-4 reproduction ({n} (4))', tvtxt(rep)]]


def ele41_changes_table(ctx, doc, D, E):
    """§10.1.1: the firmware v2.12 changes of v4.1 with their labels under line 266 (6), and the corrections of 266 (7)."""
    n = D['ele']['line']
    cl = D['cl']
    chg = ctx.raw(E, '/firmware/v2p12/changes', default=[]) or []
    rows = []
    for j, x in enumerate(chg):
        t = ctx.v(E, f'/firmware/v2p12/changes/{j}', tag='DESIGN')
        s = str(x)
        lab = []
        if s.startswith('seat compensation'):
            lab = [lab_susp(D, 'option (b) firmware row')]
        elif s.startswith('ARM sanity static term'):
            lab = [lab_susp(D, 'option (b) firmware row'),
                   corr(ctx, D, cl.clip(n, 7, 'E4-03 (canArm subtracts the static term twice after an earlier ARM', 'fixed in v2.13)'), 'E4-03')]
        elif s.startswith('TB-state'):
            lab = [lab_acc(D, 'TB-state')]
        elif 'J-FWD indication' in s:
            lab = [lab_acc(D, 'JFWD_LS'), gnote(f'E4-N03, TO-VERIFY ({n} (8))', [cl.clip(n, 8, 'E4-N03 (47.5 against 47.75 bar abs, TO-VERIFY)',
                                                                                    'E4-N03 (47.5 against 47.75 bar abs, TO-VERIFY)')])]
        elif s.startswith('torch re-zero limit'):
            lab = [lab_acc(D, 're-base OPEN, 264 (4)'),
                   gnote(f'E4-N04 ({n} (8))', [cl.clip(n, 8, 'E4-N04 (the P_torch re-base needs compensation or a photodiode-guarded gate; torch local heat MISSING)',
                                                       'E4-N04 (the P_torch re-base needs compensation or a photodiode-guarded gate; torch local heat MISSING)')])]
        elif s.startswith('kIgnBaseCheck_Pa'):
            lab = [lab_acc(D, 'kIgnBaseCheck_Pa 0.76 / 0.46 bar'), lab_susp(D, 'the kIgnBaseDrift 0.06 bar basis for any relight')]
        elif s.startswith('purge FINAL'):
            lab = [lab_acc(D, 'purge FINAL')]
        elif s.startswith('log v13'):
            lab = [lab_acc(D, 'log v13')]
        rows.append([tvtxt(t), cat(*lab) if lab else Cell('<span class="small">own tag (266 (6) names it in neither list)</span>', [])])
    o = [doc.h(3, f'10.1.1 Firmware v2.12 changes and their status under line {n}')]
    o.append(dtable(['Change (electronics.json v4.1 /firmware/v2p12/changes, quoted)', f'Label ({n} (6)) and correction ({n} (7))'], rows,
                    widths=['58%', '42%'], cls='tight', caption='SIL only (firmware v2.12 has no Teensy HAL); no hardware exists.'))
    return '\n'.join(o)


def ele41_relight_rows(ctx, D, E):
    """§10.4 additions: the stand relight after B1 (SUSPENDED; E4-02) and the U330 band rows (ACCEPTED; E4-04)."""
    n = D['ele']['line']
    cl = D['cl']
    rows = []
    sr = ctx.v(E, '/r3_01_c1_drift/stand_relight_after_B1')
    rows.append(['Stand relight after B1 (v4.1 r3_01_c1_drift)', cat(tvtxt(sr), lab_susp(D, 'the stand relight after B1'), e4_02_cell(ctx, D))])
    u = ctx.raw(E, '/r3_01_c1_drift/A8_U330', default=None)
    if u is not None:
        ut = ctx.v(E, '/r3_01_c1_drift/A8_U330', tag_default='DERIVED')
        rows.append(['U330 band rows (v4.1 r3_01_c1_drift A8)', cat(tvtxt(ut, 900), lab_acc(D, 'the U330 band rows'),
                                                                   corr(ctx, D, cl.clip(n, 7, 'E4-04 (the U330 ordering gains the stand relight light', '[DERIVED])'), 'E4-04'))])
    return rows


def ele41_purge_rows(ctx, D, E):
    """§10.6 additions: purge FINAL of v2.12 (v4.1 /purge_final_v2p12), ACCEPTED (REV-ELEC-4, line 266), with E4-N08 routed (266 (8))."""
    n = D['ele']['line']
    rows = []
    for kk in ('kPurgeFlow_s', 'kHbleedCap_s'):
        c, _t = ele_const(ctx, D, E, f'/purge_final_v2p12/{kk}', label=kk)
        rows.append([esc(f'purge FINAL: {kk}'), c])
    for kk in ('calibration', 'rule_d', 'purge_command_time', 'vented_mass_DERIVED'):
        if ctx.raw(E, f'/purge_final_v2p12/{kk}', default=None) is not None:
            t = ctx.v(E, f'/purge_final_v2p12/{kk}', tag_default='DESIGN')
            rows.append([esc(f'purge FINAL: {kk.replace("_", " ")}'), tvtxt(t, 900)])
    rows.append(['purge mass basis (266 (7), E4-05 (9))', corr(ctx, D, rv4(ctx, '9. The stale'), 'E4-05 (9)')])
    return rows


def ele41_oi_note(ctx, D, oid):
    """Notes of line 266 on the electronics.json v4.1 open issues (§10.9)."""
    n = D['ele']['line']
    cl = D['cl']
    if oid == 'OI-PURGE-CAP':
        p = purge_parts(ctx, D)
        return cat(gnote(f'lead decision made, 256 (2){p["i256"].ref()}; implemented in v4.1; open: measured-time form after CF-4 / B-BLEED-1{p["i257"].ref()}; '
                         f'E4-N08 routed ({n} (8)){D["ele"]["routed_tv"].ref()}; contradiction register C-12', [p['i256'], p['i257'], D['ele']['routed_tv']]),
                   lab_acc(D, 'purge FINAL'))
    if oid == 'OI-C1-SEAT-DRIFT':
        rs = cl.item(264, 2, contains='Residuals stay OPEN')
        return cat(gnote(f'264 (2) ruled option (b); {n} (6){D["ele"]["carve_tv"].ref()}: option (b) is not used for any start with ignition until a '
                         f'reviewed v2.13 delta (carve-out, §10.0); residuals OPEN (264 (2)){rs.ref()}', [D['ele']['carve_tv'], rs]),
                   lab_susp(D, 'option (b) rows and residuals'))
    if oid == 'OI-STAND-RELIGHT-COEF':
        return cat(e4_02_cell(ctx, D), lab_susp(D, 'the stand relight after B1'))
    if oid == 'OI-PTORCH-PROOF':
        t = cl.clip(n, 8, 'E4-N04 (the P_torch re-base needs compensation or a photodiode-guarded gate; torch local heat MISSING)',
                    'E4-N04 (the P_torch re-base needs compensation or a photodiode-guarded gate; torch local heat MISSING)')
        return gnote(f'264 (4): the C1-family Kulite; threshold re-base OPEN; {n} (8){t.ref()}: E4-N04 with v2.13; contradiction register C-10, C-14', [t])
    if oid == 'OI-T4-RESIZE':
        return gnote(f'264 (5): the shorter relight; T4 is a stand relight and waits for v2.13 ({n} (6)){D["ele"]["cons_tv"].ref()}; contradiction register C-15',
                     [D['ele']['cons_tv']])
    if oid == 'OI-JFWD-FLIGHT':
        t = cl.clip(n, 8, 'E4-N02 (the 264 (2) pad rule and the 264 (7) inhibit implemented)', 'E4-N02 (the 264 (2) pad rule and the 264 (7) inhibit implemented)')
        return gnote(f'264 (7) provisional inhibit; not implemented yet: {n} (8){t.ref()}, with v2.13', [t])
    return Cell('', [])


def ele41_rulings_266_rows(ctx, D):
    """§10.8 rows for line 266 (4), (5), (8); (6) and (7) are in §10.0."""
    e = D['ele']
    n = e['line']
    return [[f'REV-ELEC-4 verdict ({n} (4))', dq(e['verdict_tv'])],
            [f'E4-01, the MAJOR finding ({n} (5))', dq(e['e401_tv'])],
            [f'Carve-out and promotion ({n} (6), (7))', Cell('<span class="small">quoted in full in §10.0</span>', [e['carve_tv'], e['promo_tv']])],
            [f'Queued and routed ({n} (8))', cat(dq(e['q8_tv']), dq(e['routed_tv']))]]


def fw_ver(D):
    """Firmware version of the electronics interface of record (v4.1: v2.12 SIL; v4: v2.11 SIL); a text label, read from the state of line 266."""
    return 'v2.12' if D.get('ele', {}).get('promo') else 'v2.11'

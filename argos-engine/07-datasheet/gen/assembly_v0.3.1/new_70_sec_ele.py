# ---------------------------------------------------------------------------------------------
# sections 10-11 (v0.3.1): electronics (electronics.json v4, firmware v2.11 SIL), mission (GNC v3.2)
# rev1 phase 2 (lead 2026-10-21 13:47Z and 14:05Z, REV-DS-1 batches 1 and 2): every firmware constant with its unit at source
# precision (D1-08); the v2.11 BASE constants as design values with the not-accepted note (D1-03); the purge-cap note (D1-02);
# the proof-requirement note (D1-05); kBayArmMax_K TO-VERIFY / TO-DEFINE and the SIL result of the A7 blank as SIM (D1-07);
# OI-A1-BASE-AMB closed by 264 (3) (D1-04, C-16); carve-out notes of the promoted-v4.1 build at their anchors
# ---------------------------------------------------------------------------------------------
BASE_KEYS = ('kPcRezeroMax_Pa', 'kIgnBaseCheck_Pa')  # 253 (5): the C1 re-zero and BASE constants of v2.11, not accepted (R3-01)
BASE_BASIS = 'Design value, Electronics v2.11 (electronics.json v4)'
BASE_WHY = 'not accepted by the lead: 253 (5), R3-01 (lead 2026-10-21 13:47Z, REV-DS-1 D1-03)'
CLOSED_BY_LEAD = {'OI-A1-BASE-AMB': (264, 3)}  # open issues of electronics.json closed by a lead line (lead 2026-10-21 13:47Z, C-16)


def node_unit(node):
    u = node.get('unit') if isinstance(node, dict) else None
    return '' if u in (None, '', '-') else str(u)


def const_name(node, ptr):
    m = re.search(r'config\.h (k\w+)', str(node.get('src') or '')) if isinstance(node, dict) else None
    return m.group(1) if m else str(ptr).rstrip('/').rsplit('/', 1)[-1].replace('~1', '/').replace('~0', '~')


def r301_vals(ctx, D):
    """Line 264 (2) values (R3-01) and the 253 (5) not-accepted clause, created once: the BASE notes, §10.8 and C-13 cite the same traces."""
    if 'r301' not in D:
        cl = D['cl']
        i2 = cl.item(264, 2)
        D['r301'] = {'i2': i2,
                     'rz': rx_text(ctx, i2, r'kPcRezeroMax_Pa stays ([\d.]+) bar', 'bar'),
                     'bc': rx_text(ctx, i2, r'kIgnBaseCheck_Pa ([\d.]+) / [\d.]+ bar', 'bar'),
                     'bc2': rx_text(ctx, i2, r'kIgnBaseCheck_Pa [\d.]+ / ([\d.]+) bar', 'bar'),
                     'lim': cl.clip(264, 2, 'kPcRezeroMax_Pa stays', '(default / B-PC-1-shown build)'),
                     'na': cl.clip(253, 5, 'EXCEPT the C1 re-zero and BASE constants', 'open MAJOR)')}
    return D['r301']


def base_note(ctx, D):
    """'[not accepted, 253 (5) (R3-01); 264 (2): ...; v4.1 implementation PENDING REVIEW (REV-ELEC-4)]' (lead 2026-10-21 13:47Z, D1-03)."""
    r = r301_vals(ctx, D)
    w, wt = impl_txt(D, 'base', 'v4.1 implementation PENDING REVIEW (REV-ELEC-4)', 'v4.1 implementation promoted, line {n}')
    return gnote(f'not accepted, 253 (5) (R3-01){r["na"].ref()}; 264 (2): kPcRezeroMax_Pa {r["rz"].h()} on the compensated residual, '
                 f'kIgnBaseCheck_Pa {r["bc"].h(unit=False, pill=False)} / {r["bc2"].h()} (default / B-PC-1-shown build); {esc(w)}'
                 + ''.join(t.ref() for t in wt) + '; contradiction register C-13', [r['na'], r['rz'], r['bc'], r['bc2']] + wt)


def purge_parts(ctx, D):
    """Line 256 (2) FINAL purge values and the condition lines 257 (2) / 258 (2), created once (§10.3, §10.6, §10.9, §12.3, C-12)."""
    if 'purge' not in D:
        cl = D['cl']
        i256 = cl.item(256, 2)
        D['purge'] = {'i256': i256,
                      'flow': rx_text(ctx, i256, r'the ([\d.]+) s scheduled flow', 's'),
                      'cap': rx_text(ctx, i256, r'with the ([\d.]+) s cap', 's'),
                      'i257': cl.item(257, 2), 'i258': cl.item(258, 2), 'i203': cl.item(203, 3),
                      'i263': cl.clip(263, 3, 'Purge FINAL 2.43 / 2.39 s', '(d) (d1) (d2)', ev='REF',
                                      why=("the Electronics author's record of the v2.12 implementation (v4.1, promoted, line "
                                           f"{D['ele']['line']} (7)); no value is taken from it" if D['ele']['promo'] else
                                           "the Electronics author's record of the v2.12 implementation, PENDING REVIEW; no value is taken from it"))}
    return D['purge']


def purge_note(ctx, D):
    """'[v2.11 value; superseded by 256 (2) FINAL: ...; implemented in v2.12 (v4.1), PENDING REVIEW]' (lead 2026-10-21 13:47Z, D1-02)."""
    p = purge_parts(ctx, D)
    w, wt = impl_txt(D, 'purge', 'implemented in v2.12 (v4.1), PENDING REVIEW', 'implemented in v2.12 (v4.1), promoted, line {n}')
    return gnote(f'v2.11 value; superseded by 256 (2) FINAL{p["i256"].ref()}: {p["flow"].h(pill=False)} flow, {p["cap"].h()} cap, conditions (a)-(d), (d1), (d2) '
                 f'of 256 (2) / 257 (2){p["i257"].ref()} / 258 (2){p["i258"].ref()}; {esc(w)}{p["i263"].ref()}' + ''.join(t.ref() for t in wt)
                 + '; contradiction register C-12', [p['i256'], p['flow'], p['cap'], p['i257'], p['i258'], p['i263']] + wt)


def cap_text_note(ctx, D):
    """Pointer on a v2.11 text that quotes the 2.55 s both-open cap (rev1 phase 2, with C-12)."""
    p = purge_parts(ctx, D)
    w, wt = impl_txt(D, 'purge', 'implemented in v2.12 (v4.1), PENDING REVIEW', 'implemented in v2.12 (v4.1), promoted, line {n}')
    return gnote(('v2.11 text, still carried in v4.1' if D['ele']['promo'] else 'v2.11 text')
                 + f'; the both-open cap is superseded by 256 (2){p["i256"].ref()} ({p["flow"].h(pill=False)} flow, {p["cap"].h(pill=False)} cap), '
                 f'{esc(w)}' + ''.join(t.ref() for t in wt) + ': contradiction register C-12', [p['i256'], p['flow'], p['cap']] + wt)


def proof_req_note(ctx, D):
    """'[requirement 166.14 bar abs DERIVED, 256 (R4-12), 264 (4)]' on the v4 proof basis (lead 2026-10-21 13:47Z, D1-05)."""
    cl = D['cl']
    i4 = cl.clip(264, 4, 'P_torch (J901', 'same part as P_mid (ENG-BL-08) and C1.')
    rq = rx_text(ctx, i4, r'against the ([\d.]+) bar abs requirement', 'bar abs', tag='DERIVED')
    r412 = cl.clip(256, 5, 'R4-12 (070BG proof rating', 'state saturation and recovery)')
    return gnote(f'requirement {rq.h()}, 256 (R4-12){r412.ref()}, 264 (4){i4.ref()}', [rq, r412, i4])


def carve(ctx, D, anchor):
    """Carve-out notes of the lead at one anchor of §10 (promoted-v4.1 build; the text is the lead's, supplied at the verdict)."""
    out = [gnote(f'<b>{esc(e["id"])}</b>: {tvtxt(e["tv"]).html}', [e['tv']]) for e in D['ele'].get('carve', []) if anchor in e['anchors']]
    return cat(*out) if out else Cell('', [])


def ele_const(ctx, D, E, ptr, label=None, name=True, notes=True):
    """One firmware constant ({v, unit, tag, src}) as a traced cell 'name = value unit' and its TV. The unit is printed and the value
    keeps its source precision (D1-08); a source tag that names no class is a design value; a tag that says TO-DEFINE is TO-VERIFY with
    the status TO-DEFINE (D1-07); a v2.11 BASE constant is a design value with the not-accepted note (D1-03); the v2.11 both-open cap
    carries the 256 (2) note (D1-02)."""
    node = ctx.raw(E, ptr, default=None)
    raw = node.get('tag') if isinstance(node, dict) else None
    tag = 'DESIGN' if (raw is not None and normalise_tag(raw) is None) else None
    tdef = bool(raw) and 'TO-DEFINE' in str(raw).upper()
    if tdef:
        tag = 'TO-VERIFY'
    t = ctx.v(E, ptr, node_unit(node), tag=tag, tag_default='DESIGN')
    cname = const_name(node, ptr)
    extra = []
    if t.value is not None and tdef:
        t.status = 'TO-DEFINE'
        if 'class set at the call site: TO-VERIFY, status TO-DEFINE' not in str(t.tag_raw):
            t.tag_raw = f'{raw} (class set at the call site: TO-VERIFY, status TO-DEFINE: the source tag says the value is still to be defined; REV-DS-1 D1-07)'
    if t.value is not None and not D['ele']['promo'] and cname in BASE_KEYS and getattr(t, 'basis_kind', None) != 'DESIGN':
        as_design(t, BASE_BASIS, BASE_WHY)  # the class is set wherever the constant is read (D1-03); the note only where notes=True
    D.setdefault('ele_tv', {}).setdefault(ptr, t)  # the first object of each constant: the C-12 / C-13 register sides reuse it
    if t.value is not None and notes and D['ele']['promo']:
        extra += ele41_const_notes(ctx, D, cname, t)
    if t.value is not None and notes and not D['ele']['promo']:
        if cname in BASE_KEYS:
            extra.append(base_note(ctx, D))
        if cname == 'kHbleedCap_s':
            p = purge_parts(ctx, D)
            if isinstance(t.value, (int, float)) and p['cap'].value is not None and abs(t.value - p['cap'].value) > 1e-9:
                extra.append(purge_note(ctx, D))
    disp = label or cname
    if label and cname.startswith('k') and cname != label:
        disp = f'{label} ({cname})'
    head = f'<b>{esc(disp)}</b> = ' if name else ''
    return cat(Cell(head + t.h(), [t]), *extra), t


def thr_cells(ctx, D, sid, base, th):
    out = []
    for kk in (th or {}):
        ptr = ptr_join(*[x for x in base.strip('/').split('/') if x], kk)
        c, _t = ele_const(ctx, D, sid, ptr, label=kk)
        out.append(Cell(f'<div class="small">{c.html}</div>', c.tvs))
    return out


def a7_blank_cell(ctx, E):
    """start_monitors.A7_flight_blank in its parts: the lead decision quote, the blind window (design) and the four conditions. A
    condition whose status reports a passing SIL test is SIM (firmware in SIL only; REV-DS-1 D1-07, T4182 'SIM (SIL)'); an OPEN condition
    is TO-VERIFY; a condition the author reports DONE in the file is a design record (design value)."""
    B = '/start_monitors/A7_flight_blank'
    ver = ctx.src(E).version or ''
    fw = 'v2.12' if ver == 'v4.1' else 'v2.11'
    node = ctx.raw(E, B, default=None)
    if not isinstance(node, dict):
        return tvtxt(ctx.v(E, B, tag_default='DESIGN'), 500)
    parts = []
    dec = None
    if 'decision' in node:
        dec = ctx.v(E, B + '/decision', tag='LEAD')
        m = re.search(r'CHANGELOG line (\d+)', str(dec.value)) if isinstance(dec.value, str) else None
        k = re.search(r'\((\d+)\) RE-12', str(dec.value)) if isinstance(dec.value, str) else None
        if m and dec.value is not None:
            dec.basis = f'Lead decision, line {m.group(1)}' + (f' ({k.group(1)})' if k else '') + f', as quoted in electronics.json {ver}'
        parts.append(Cell(f'<div class="small"><b>decision:</b> {tvtxt(dec, 500).html}</div>', [dec]))
    if 'blind_window' in node:
        bw = ctx.v(E, B + '/blind_window', tag_default='DESIGN')
        parts.append(Cell(f'<div class="small"><b>blind window:</b> {tvtxt(bw, 500).html}</div>', [bw]))
    for i, c in enumerate(node.get('conditions') or []):
        p = f'{B}/conditions/{i}'
        st = str((c or {}).get('status') or '')
        if st.upper().startswith('DONE: PASS'):
            t = ctx.v(E, p, tag='SIM')
            mv = re.search(r'PASS (v\d+\.\d+)', st)  # the firmware the status names, else the firmware of this interface version
            t.tag_raw = (f'(class set at the call site: SIM: the status reports a passing SIL unit test of firmware {mv.group(1) if mv else fw}, '
                         f'as recorded in electronics.json {ver}; REV-DS-1 D1-07)')
        elif st.upper().startswith('OPEN'):
            t = ctx.v(E, p, tag='TO-VERIFY')
            t.tag_raw = (f'(class set at the call site: TO-VERIFY: an open condition of the 216 (8) acceptance, status as stated in electronics.json {ver}; '
                         'REV-DS-1 D1-07)')
        else:
            t = ctx.v(E, p, tag='DESIGN')
            t.tag_raw = (f'(class set at the call site: DESIGN: a condition of the 216 (8) acceptance that the Electronics author reports DONE in '
                         f'electronics.json {ver}; REV-DS-1 D1-07)')
        parts.append(Cell(f'<div class="small"><b>condition {esc((c or {}).get("n", i + 1))}:</b> {tvtxt(t, 500).html}</div>', [t]))
    return cat(*parts)


def sec_electronics(ctx, doc, a, D):
    o = [doc.h(1, '10 Electronics and control')]
    cl = D['cl']
    E = 'ELE'
    promo = D['ele']['promo']
    pend = {lab: tv for lab, tv in D['pending']}
    if not promo:
        o.append(note_box('<b>electronics.json v4 (firmware v2.11, SIL only) is the published interface and the source of record of this section.</b> '
                          + inl(cl.item(253, 5)) + ' <b>PENDING:</b> ' + ' '.join(inl(tv) for tv in pend.values())
                          + ' <b>Lead rulings on the v2.12 handback (CHANGELOG 264, §10.8):</b> they decide the C1 thermal zero (R3-01, option (b)), the A1 BASE_AMB '
                          'outcome, the P_torch transducer, the T4 relight and the A1 flight T0 range; §10.8 quotes them with the values the lead decided (DECIDED, '
                          'line 264). The v2.12 firmware and the electronics.json v4.1 file that implement them are PENDING REVIEW (REV-ELEC-4); no value in this '
                          'section is taken from the v4.1 file. Where a later lead line supersedes a v2.11 value shown below, a bracketed note at the value says so.',
                          'warn'))
    else:
        o.append(ele41_head_note(ctx, doc, D))
    o.append(doc.h(2, '10.1 Engine control unit and firmware'))
    rows = [
        ['Interface status', tvtxt(ctx.v(E, '/status', tag='DESIGN'), 900)],
        ['Architecture', tvtxt(ctx.v(E, '/ecu/architecture'))],
        ['Microcontroller', tvtxt(ctx.v(E, '/ecu/mcu', tag='DESIGN'), 300)],
        ['PCB outline / enclosure reservation', cat(ctx.v(E, '/ecu/pcb_outline_mm', 'mm', tag_default='DESIGN').h(), ' / ', ctx.v(E, '/ecu/enclosure_envelope_mm', 'mm', tag_default='DESIGN').h())],
        ['ECU mass', (lambda t: Cell(t.h(), [t]) if is_number(t.value) else tvtxt(t, 300))(ctx.v(E, '/ecu/mass_kg', 'kg', tag_default='ASSUMED'))],
        ['Schematic', tvtxt(ctx.v(E, '/ecu/schematic', tag='DESIGN'), 500)],
        ['Firmware version', tvtxt(ctx.v(E, '/firmware/version', tag='DESIGN'))],
        ['Firmware target', tvtxt(ctx.v(E, '/firmware/target', tag='TO-VERIFY'), 400)],
        ['Firmware unit tests' + (' (the v2.11 record, as carried in v4.1; v2.12 below)' if promo else ''), tvtxt(ctx.v(E, '/firmware/unit_tests', tag='SIM'), 400)],
        ['SIL record v2.11', tvtxt(ctx.v(E, '/firmware/sil_record_v2p11', tag='SIM'), 400)],
        ['CAN link', tvtxt(ctx.v(E, '/can_interface/physical'), 240)],
        ['Change summary v3 to v4', tvtxt(ctx.v(E, '/change_summary_v3_to_v4/0', tag='DESIGN'), 300)],
    ]
    if promo:
        g7 = cl.clip(D['ele']['line'], 7, 'Until v4.2 this line governs v4.1 where they differ: its STAGED status text is superseded;',
                     'Until v4.2 this line governs v4.1 where they differ: its STAGED status text is superseded;')
        rows[0][1] = cat(rows[0][1], gnote(f'{D["ele"]["line"]} (7){g7.ref()}: the STAGED status text is superseded; v4.1 is the source of record; '
                                           'contradiction register C-02', [g7]))
        rows += ele41_fw_rows(ctx, D, E)
    o.append(dtable(['Item', 'Value'], rows, widths=['26%', '74%'], cls='tight'))
    if promo:
        o.append(ele41_changes_table(ctx, doc, D, E))
    o.append(doc.h(2, '10.2 Sensors'))
    PT = '/sensors/pressure_transducers'
    TC = '/sensors/thermocouples'
    CR = f'{PT}/coast_rezero'
    crn = ctx.raw(E, CR, default=None)
    if isinstance(crn, dict) and 'v' not in crn:
        crc = []
        for kk, x in crn.items():
            p = ptr_join(*[s for s in CR.strip('/').split('/') if s], kk)
            if isinstance(x, dict) and 'v' in x:
                c, _t = ele_const(ctx, D, E, p, label=kk)
            else:
                c = cat(f'<b>{esc(kk)}:</b> ', tvtxt(ctx.v(E, p, tag_default='DESIGN'), 400))
            crc.append(Cell(f'<div class="small">{c.html}</div>', c.tvs))
        crcell = cat(*crc, carve(ctx, D, 'opt_b_comp'))
    else:
        crcell = cat(tvtxt(ctx.v(E, CR, tag_default='DESIGN'), 400), carve(ctx, D, 'opt_b_comp'))
    rows = [
        ['Pressure transducers (selection, electronics.json ' + ('v4.1)' if promo else 'v4)'), sel_cell(ctx, D, E, PT)],
        ['P_torch transducer: lead 264 (4) supersedes the v4 selection', ptorch_cell(ctx, D)],
        ['Hardware over-pressure comparator', tvtxt(ctx.v(E, f'{PT}/hw_ovp'), 300)],
        ['Coast re-zero', crcell],
        ['Thermocouple channels', tc_channels_cell(ctx, D, E, TC)],
        ['Case abort / relight refusal', cat(Cell(temp_k(ctx.v(E, f'{TC}/case_abort', 'K'), 2), [ctx.recent[-1]]), ' / ',
                                             Cell(temp_k(ctx.v(E, f'{TC}/relight_refusal', 'K'), 2), [ctx.recent[-1]]))],
        ['Case abort rule', tvtxt(ctx.v(E, f'{TC}/case_abort_rule', tag_default='LEAD'), 500)],
        ['Persistence', (lambda t: Cell(t.h(), [t]))(ctx.v(E, f'{TC}/persistence', 's', tag_default='DESIGN'))],
        ['Start and ARM limit / stand ARM maximum', (lambda t1, t2: Cell(f'{temp_k(t1, 2)} / {temp_k(t2, 2)}', [t1, t2]))(
            ctx.v(E, f'{TC}/start_and_arm_limit', 'K', tag_default='LEAD'), ctx.v(E, f'{TC}/stand_arm_max', 'K', tag_default='LEAD'))],
        ['Nozzle-holder limit', (lambda t: Cell(temp_k(t, 2), [t]))(ctx.v(E, f'{TC}/nozzle_holder_limit', 'K', tag_default='ASSUMED'))],
        ['Photodiode', tvtxt(ctx.v(E, '/sensors/photodiode', tag='DESIGN'))],
        ['Encoders', tvtxt(ctx.v(E, '/sensors/encoders', tag='DESIGN'))],
        ['Stand dynamic Pc channel', tvtxt(ctx.v(E, '/sensors/stand_dynamic_pc', tag='DESIGN'))],
    ]
    o.append(dtable(['Item', 'Value'], rows, widths=['26%', '74%'], cls='tight'))
    fw = 'v2.12' if promo else 'v2.11'
    o.append(doc.h(2, f'10.3 Limits of firmware {fw}'))
    lims = ctx.raw(E, '/limits_v2p11', default=[]) or []
    rows = []
    for k, l in enumerate(lims):
        b = f'/limits_v2p11/{k}'
        vn = l.get('value')
        if isinstance(vn, dict) and 'v' in vn and not isinstance(vn.get('v'), str):
            vc, _vt = ele_const(ctx, D, E, b + '/value')
        elif isinstance(vn, dict) and 'v' not in vn:
            vcs = [ele_const(ctx, D, E, ptr_join('limits_v2p11', k, 'value', kk))[0] for kk in vn]
            vc = cat(*[Cell(f'<div class="small">{c.html}</div>', c.tvs) for c in vcs])
        else:
            vc = tvtxt(ctx.v(E, b + '/value', tag_default='DESIGN'), 200)
        bt = ctx.v(E, b + '/basis', tag='DERIVED')
        bc = tvtxt(bt, 500)
        if 'proof' in str(l.get('limit', '')).lower() and isinstance(bt.value, str) and '166.1 bar abs' in bt.value:
            bc = cat(bc, proof_req_note(ctx, D))
        if promo:
            ex = ele41_limit_notes(ctx, D, k)
            if ex:
                bc = cat(bc, *ex)
        rows.append([Cell(f'<b>{esc(l.get("limit", ""))}</b>', []), vc, bc])
    o.append(dtable(['Limit', 'Value', 'Basis (quoted)'], rows, widths=['24%', '30%', '46%'], cls='tight',
                    caption=f'electronics.json /limits_v2p11. Values are firmware constants (config.h), SIL only; each with its unit, at the precision of the source.'))
    if promo:
        o.append(ele41_missing_limits(ctx, D))
    o.append(doc.h(2, '10.4 Light rule and start monitors'))
    LR = '/light_rule'
    rows = [['Light rule', cat(tvtxt(ctx.v(E, f'{LR}/rule'), 900), carve(ctx, D, 'relight'))]]
    for kk in ('kIgnRise_Pa', 'kIgnConfirmRelN', 'kIgnPreN', 'kIgnResidual_Pa', 'kIgnBaseCheck_Pa', 'kIgnFloorAbs_Pa'):
        c, _t = ele_const(ctx, D, E, f'{LR}/{kk}', label=kk, name=False)
        rows.append([esc(kk), c])
    for kk in ('A3', 'A7', 'E3', 'A7_flight_blank', 'light_spike_record'):
        cell = a7_blank_cell(ctx, E) if kk == 'A7_flight_blank' else tvtxt(ctx.v(E, f'/start_monitors/{kk}', tag_default='DESIGN'), 500)
        rows.append([f'Start monitor {esc(kk)}', cell])
    if promo:
        rows += ele41_relight_rows(ctx, D, E)
    o.append(dtable(['Item', 'Value'], rows, widths=['24%', '76%'], cls='tight'))
    o.append(doc.h(2, f'10.5 Abort and refusal causes (firmware {fw})'))
    cs = ctx.raw(E, '/abort_matrix/causes', default=[]) or []
    rows = []
    for k, c in enumerate(cs):
        b = f'/abort_matrix/causes/{k}'
        code = ctx.v(E, b + '/code', tag='DESIGN')
        cause = ctx.v(E, b + '/cause', tag='DESIGN')
        trig = ctx.v(E, b + '/trigger', tag='DESIGN')
        trc = tvtxt(trig)  # abort triggers in full (REV-DS-1 D1-06: gates are never cut)
        if c.get('cause') == 'PC_SENSOR' and isinstance(trig.value, str) and 'by more than 0.7 bar' in trig.value:
            r = r301_vals(ctx, D)
            if not promo:
                trc = cat(trc, gnote(f'0.7 bar here is the v2.11 kIgnBaseCheck_Pa (not accepted, 253 (5){r["na"].ref()}); 264 (2) sets '
                                     f'{r["bc"].h(unit=False, pill=False)} / {r["bc2"].h()}: contradiction register C-13', [r['na'], r['bc'], r['bc2']]))
            else:
                trc = cat(trc, gnote(f'0.7 bar in this trigger text is the v2.11 kIgnBaseCheck_Pa; v4.1 holds kIgnBaseCheck_Pa at the 264 (2) values '
                                     f'{r["bc"].h(unit=False, pill=False)} / {r["bc2"].h()} (§10.4; ACCEPTED, REV-ELEC-4, line {D["ele"]["line"]}): '
                                     'contradiction register C-13', [r['bc'], r['bc2'], D['ele']['acc_tv']]))
        th = thr_cells(ctx, D, E, b + '/thresholds', c.get('thresholds'))
        rows.append([Cell(f'{esc(code.num())}{code.ref()}', [code]), Cell(f'<b>{esc(cause.value)}</b>{cause.ref()}', [cause]), trc,
                     cat(*th) if th else Cell('<span class="small">no threshold</span>', [trig])])
    o.append(dtable(['Code', 'Cause', 'Trigger', 'Thresholds'], rows, label_cols=0, cls='abort tight',
                    widths=['6%', '16%', '42%', '36%'], caption=f'{len(cs)} causes in electronics.json /abort_matrix/causes (SIL only; no hardware); '
                                                                f'thresholds with their units, at the precision of the source.'))
    o.append(doc.h(2, '10.6 Power, head-end bleed provision and fail-safe states'))
    PB = '/power_budget'
    rows = [['Battery', tvtxt(ctx.v(E, f'{PB}/battery', tag='DESIGN'))],
            ['Logic power, typical / peak', (lambda t1, t2: cat(t1.h(unit=False, pill=False), ' / ', t2.h()))(
                ctx.v(E, f'{PB}/logic_W/v/typ', 'W', tag_ptr=f'{PB}/logic_W'), ctx.v(E, f'{PB}/logic_W/v/peak', 'W', tag_ptr=f'{PB}/logic_W'))],
            ['Energy per flight day', num_cell(ctx.v(E, f'{PB}/flight_day_Wh', 'Wh'))],
            ['Energy per static-fire session', num_cell(ctx.v(E, f'{PB}/static_fire_session_Wh', 'Wh'))],
            ['Peak current', num_cell(ctx.v(E, f'{PB}/peak_current_A', 'A'))],
            ['Minimum voltage at the ECU', num_cell(ctx.v(E, f'{PB}/min_voltage_at_ECU_V', 'V'))],
            ['Fusing', tvtxt(ctx.v(E, f'{PB}/fusing', tag='DESIGN'), 300)]]
    HB = '/head_end_bleed_provision'
    for kk in ('architecture', 'schedule', 'closure_rule', 'cap_decision_230_3', 'hardware_both_open_timer', 'pad_bit'):
        t = ctx.v(E, f'{HB}/{kk}', tag_default='DESIGN')
        c = tvtxt(t, 500)
        if '2.55 s' in _plain_text(t.value):
            c = cat(c, cap_text_note(ctx, D))
        if promo and kk == 'schedule':
            c = cat(c, lab_acc(D, 'purge FINAL 2.43 / 2.39 s with rule (d), (d1), (d2)'))
        if promo and kk == 'hardware_both_open_timer':
            c = cat(c, gnote(f'routed ({D["ele"]["line"]} (8)){D["ele"]["routed_tv"].ref()}: E4-N08, the backstop allows up to 2.741 s against '
                             'the 2.39 s never-above value; Combustion and the lead at B-BLEED-1', [D['ele']['routed_tv']]))
        if promo and '73.0 g' in _plain_text(t.value):
            c = cat(c, corr(ctx, D, rv4(ctx, '9. The stale'), 'E4-05 (9)'))
        rows.append([esc('bleed: ' + kk.replace('_', ' ')), c])
    if promo:
        rows += ele41_purge_rows(ctx, D, E)
    fs = ctx.raw(E, '/fail_safe_states', default={}) or {}
    for kk in fs:
        if kk.startswith('superseded'):
            continue
        rows.append([f'Fail-safe: {esc(kk)}', tvtxt(ctx.v(E, ptr_join('fail_safe_states', kk), tag='DESIGN'), 300)])
    o.append(dtable(['Item', 'Value'], rows, widths=['26%', '74%'], cls='tight'))
    o.append(doc.h(2, '10.7 Lead rulings on v2.11 and items routed to Electronics v2.12'))
    rows = []
    for kk in (ctx.raw(E, '/lead_rulings_v2p11', default={}) or {}):
        if kk in ('record',):
            continue
        rows.append([esc(kk.replace('_', ' ')), tvtxt(ctx.v(E, ptr_join('lead_rulings_v2p11', kk), tag='LEAD'))])  # in full (D1-06)
    rows.append(['Routed to v2.12 (LEAD 258 (4))', tvtxt(cl.item(258, 4))])
    rows.append(['Electronics v2.12 (LEAD 261 (3))', tvtxt(cl.item(261, 3))])
    o.append(dtable(['Item', 'Value (quoted)'], rows, widths=['24%', '76%'], cls='tight',
                    caption='electronics.json /lead_rulings_v2p11 and the CHANGELOG items that route work to Electronics v2.12'
                            + (' (PENDING; its interface is electronics.json v4.1, not yet reviewed).' if not promo else '.')))
    o.append(doc.h(2, '10.8 Lead rulings on the Electronics v2.12 handback (CHANGELOG 264)' + ('; v4.1 PENDING REVIEW' if not promo else
                                                                                              f' and on its review (CHANGELOG {D["ele"]["line"]})')))
    o.append(rulings_264(ctx, D))
    o.append(doc.h(2, '10.9 Electronics open issues'))
    oi = ctx.raw(E, '/open_issues', default=[]) or []
    ropen, rclosed, topen, tclosed = [], [], [], []
    for k, x in enumerate(oi):
        b = f'/open_issues/{k}'
        idt = ctx.v(E, b + '/id', tag='DESIGN')
        clo = ctx.v(E, b + '/closure', tag='DESIGN')
        cc = tvtxt(clo)
        if promo and x.get('id') in ('OI-PURGE-CAP', 'OI-C1-SEAT-DRIFT', 'OI-STAND-RELIGHT-COEF', 'OI-PTORCH-PROOF', 'OI-T4-RESIZE', 'OI-JFWD-FLIGHT'):
            cc = cat(cc, ele41_oi_note(ctx, D, x.get('id')))
        if not promo and x.get('id') == 'OI-PURGE-CAP':
            p = purge_parts(ctx, D)
            cc = cat(cc, gnote(f'lead decision made, 256 (2){p["i256"].ref()}; open: measured-time form after CF-4 / B-BLEED-1{p["i257"].ref()}; '
                               'contradiction register C-12', [p['i256'], p['i257']]))
        itv = ctx.v(E, b + '/issue', tag='TO-VERIFY')
        D.setdefault('ele_oi_tv', {})[x.get('id')] = {'id': idt, 'issue': itv, 'closure': clo}  # sides of C-12 / C-16
        row = [Cell(f'<b>{esc(x.get("id"))}</b>', [idt]), tvtxt(ctx.v(E, b + '/severity', tag='DESIGN')),
               tvtxt(itv), tvtxt(ctx.v(E, b + '/owner', tag='DESIGN')), cc]
        if x.get('id') in CLOSED_BY_LEAD:
            row[4] = cat(cc, oi_closed_note(ctx, D, x.get('id')))
            rclosed.append(row)
            tclosed.append(idt)
        elif str(x.get('severity') or '').upper().startswith('CLOSED'):
            rclosed.append(row)  # closed in the interface file itself (severity CLOSED ...)
            tclosed.append(idt)
        else:
            ropen.append(row)
            topen.append(idt)
    no = ctx.d(len(ropen), '', 'count of electronics.json /open_issues not closed (by a lead line or in the file)', topen)
    nc = ctx.d(len(rclosed), '', 'count of electronics.json /open_issues closed by a lead line or marked CLOSED in the file (shown for the record)', tclosed)
    D['ele_oi'] = {'open': no, 'closed': nc}
    rows = [f'<tr class="grp"><td colspan="5">Open: {no.h(pill=False)}</td></tr>'] + ropen
    if rclosed:
        rows += [f'<tr class="grp"><td colspan="5">Closed by a lead line or marked CLOSED in the file (kept for the record): {nc.h(pill=False)}</td></tr>'] + rclosed
    o.append(dtable(['ID', 'Severity', 'Issue', 'Owner', 'Closure'], rows, label_cols=0, widths=['13%', '9%', '46%', '12%', '20%'], cls='tight',
                    caption=f'electronics.json /open_issues ({len(oi)} items as published). An item a later lead line closes is listed under the closed group, '
                            'with the line that closes it; only a residual that a lead line names stays open.'))
    return '\n'.join(o)


def oi_closed_note(ctx, D, oid):
    cl = D['cl']
    if oid == 'OI-A1-BASE-AMB':
        i3 = cl.item(264, 3)
        nr = cl.item(264, 2, contains='NEW RULE')
        s5 = cl.clip(253, 5, "the '0 of 500' evidence of OI-A1-BASE-AMB", 'not an occurrence rate')
        if D['ele']['promo']:
            n = D['ele']['line']
            return cat(gnote(f'closed by 264 (3){i3.ref()} (BASE_AMB at the A1 relight ADOPTED as built); the evidence (not the decision) of 264 (3) is '
                             f'suspended until v2.13 and is re-shown on v2.13 ({n} (6)); open only for the residual a lead line names: the A1 pad no-go rule '
                             f'of 264 (2){nr.ref()} (NEW RULE; NO-GO until v2.13, {n} (6); §12.4). 253 (5){s5.ref()}: the "0 of 500" evidence is structural, '
                             'not an occurrence rate. Contradiction register C-16', [i3, nr, s5]), lab_susp(D, 'the evidence of 264 (3)'))
        return gnote(f'closed by 264 (3){i3.ref()} (BASE_AMB at the A1 relight ADOPTED as built); open only for the residual a lead line names: the A1 pad '
                     f'no-go rule of 264 (2){nr.ref()} (NEW RULE, not implemented yet; §12.4). 253 (5){s5.ref()}: the "0 of 500" evidence is structural, '
                     'not an occurrence rate. Contradiction register C-16', [i3, nr, s5])
    n, k = CLOSED_BY_LEAD[oid]
    t = cl.item(n, k)
    return gnote(f'closed by {n} ({k}){t.ref()}', [t])


def dsig_rows(ctx, keys):
    allr = md_rows_all(ctx.src('DSIG').text or '', None)
    out = []
    for key in keys:
        hit = [x for x in allr if x[1] and x[1][0].strip() == key]
        if not hit:
            out.append((key, None, None))
            continue
        out.append((key,) + hit[0])
    return out


def sec_mission(ctx, doc, a, D):
    o = [doc.h(1, '11 Mission and landing (GNC v3.2)')]
    o.append(note_box('<b>Basis.</b> ' + inl(md_line_starting(ctx, 'DSIG', 'The basis is the published gnc.json v3.2', 'DESIGN', tag_raw='GNC datasheet inputs header')), 'info'))
    o.append(doc.h(2, '11.1 Mission headline numbers'))
    rows = []
    for key, ln, r in dsig_rows(ctx, ['1', '2', '3', '4', '5', '9', '10']):
        if r is None:
            m = ctx.missing(f'DSIG row {key}')
            rows.append([key, Cell(m.h(), [m]), '', ''])
            continue
        tag = r[3].strip() if len(r) > 3 else None
        ev = normalise_tag(tag)
        rows.append([Cell(f'<b>{esc(r[1].strip())}</b>', []), tvtxt(md_cell_ln(ctx, 'DSIG', ln, r, 2, ev, tag_raw=tag, label=r[1].strip()), 900),
                     tvtxt(md_cell_ln(ctx, 'DSIG', ln, r, 4, ev, tag_raw=tag, label=r[1].strip()), 500),
                     tvtxt(md_cell_ln(ctx, 'DSIG', ln, r, 5, 'REF', tag_raw='source column (reference)', label=r[1].strip()), 200)])
    o.append(dtable(['Item', 'Value for the datasheet', 'Basis', 'Source'], rows, widths=['14%', '44%', '28%', '14%'], cls='tight',
                    caption=f'01-systems-gnc/DATASHEET-INPUTS-GNC.md ({esc(src_label(ctx, "DSIG"))}); rows 6-8 (gimbal, slew, servo stiffness) are in §3.2. '
                            '<b>Vehicle basis of rows 1-5 and 9: massprops v3.5.1</b> (the basis column names it); the CAD v3.5.2 mass change is in the table below.'))
    gm = gnc_mass_cells(ctx, D)
    rows = [['GNC vehicle basis (row 4): liftoff mass / liftoff T/W (massprops v3.5.1)', cat(gm['lift'].h(), ' / ', gm['tw'].h())],
            ['Landing-mass change v3.5.2 vs v3.5.1: as built / without the conditional TC-09 thinning', cat(gm['dl'].h('+.4f'), ' / ', gm['dl0'].h('+.4f'))],
            ["GNC's re-fly trigger (landing-mass growth)", num_cell(gm['trig'])],
            ['Verdict and evidence (03-cad/v3.5.2/massdelta_v3.5.2_vs_v3.5.1.json /gnc_trigger)', cat(tvtxt(gm['verdict'], 300), '<br>', tvtxt(gm['evid'], 300))]]
    o.append(dtable(['Item', 'Value'], rows, widths=['40%', '60%'], cls='tight',
                    caption='The GNC figures above (rows 1-5 and 9: the A1 apogee, the landing P, the liftoff mass and T/W) are on massprops v3.5.1. The CAD v3.5.2 '
                            'landing-mass change is below GNC\'s re-fly trigger with and without the conditional TC-09 thinning: no re-fly by mass. The change is CALC, not weighed. '
                            'gnc.json /reference_vehicle/liftoff_mass_kg is the ledger-v3d reference vehicle and is not quoted as current (lead 262 (5)).'))
    o.append(doc.h(2, '11.2 GNC open items'))
    keys = [f'11{c}' for c in 'abcdefghijklmnopq']
    rows = []
    for key, ln, r in dsig_rows(ctx, keys):
        if r is None:
            continue
        tag = r[3].strip() if len(r) > 3 else None
        ev = normalise_tag(tag)
        traw = tag
        if ev is None and (tag or '').strip().lower() == 'not flown':
            ev, traw = 'MISSING', f'{tag} (class set at the call site: MISSING: the source tag says no flight or simulation exists for the item)'
        rows.append([Cell(f'<b>{esc(key)}</b> {esc(r[1].strip())}', []), tvtxt(md_cell_ln(ctx, 'DSIG', ln, r, 2, ev, tag_raw=traw, label=key), 700),
                     tvtxt(md_cell_ln(ctx, 'DSIG', ln, r, 5, 'REF', tag_raw='owner / source column (reference)', label=key), 200)])
    o.append(dtable(['Open item', 'What is needed (quoted)', 'Owner / source'], rows, widths=['20%', '60%', '20%'], cls='tight'))
    return '\n'.join(o)


def ptorch_cell(ctx, D):
    """P_torch transducer after lead 264 (4) (OI-PTORCH-PROOF): the v4 selection names the TE 070BG; the lead moves P_torch to a
    C1-family Kulite. Quoted with its tagged numbers; the threshold re-base is OPEN (§12.4)."""
    cl = D['cl']
    i4 = cl.clip(264, 4, 'P_torch (J901', 'same part as P_mid (ENG-BL-08) and C1.')
    pr = rx_text(ctx, i4, r'proof ([\d.]+) bar abs \[DATASHEET\]', 'bar abs', tag='DATASHEET')
    rq = rx_text(ctx, i4, r'against the ([\d.]+) bar abs requirement', 'bar abs', tag='DERIVED')
    out = cat(tvtxt(i4, 700), '<br>New unit: proof ', pr.h(), ' against the required ', rq.h(),
              '. Its thresholds are re-based in a later Electronics round (OPEN, §12.4; contradiction register C-10, C-14).')
    if D['ele']['promo']:
        n = D['ele']['line']
        t = cl.clip(n, 8, 'E4-N04 (the P_torch re-base needs compensation or a photodiode-guarded gate; torch local heat MISSING)',
                    'E4-N04 (the P_torch re-base needs compensation or a photodiode-guarded gate; torch local heat MISSING)')
        out = cat(out, gnote(f'{n} (8){t.ref()}: E4-N04, queued with v2.13', [t]))
    return out


def rulings_264(ctx, D):
    """Lead rulings on the Electronics v2.12 handback (CHANGELOG 264 (1)-(8)); each item DECIDED (lead decision, line 264 (k)),
    the numbers it quotes keep their own tags (lead 2026-10-21 12:52Z). v0.3.1: the 264 (2) limits keep DECIDED (lead) with
    'PENDING REVIEW (v4.1 implementation)' beside them (lead 13:47Z, D1-03); pointers to the contradiction register."""
    cl = D['cl']
    r = r301_vals(ctx, D)
    w, wt = impl_txt(D, 'r264', 'PENDING REVIEW (v4.1 implementation)', 'v4.1 implementation promoted, line {n}')
    rows = []
    rows.append(['Electronics v2.12 staged (Electronics, line 263)',
                 tvtxt(cl.part(263, 'candidate results/electronics_v4.1.json', ev='REF', why='provenance record of the staged candidate'), 500)])
    promo = D['ele']['promo']
    n = D['ele']['line']
    rows.append(['Source of record and the v4.1 candidate (264 (1))', cat(tvtxt(D['ele']['pend_tv'], 500),
                 gnote(f'superseded by the promotion, {n} (7){D["ele"]["promo_tv"].ref()}', [D['ele']['promo_tv']]) if promo else Cell('', []))])
    rows.append(['R3-01 Pc zero, OI-C1-SEAT-DRIFT (264 (2))', cat(tvtxt(r['i2'], 2400), carve(ctx, D, 'opt_b_comp'),
                                                                  e4_02_cell(ctx, D) if promo else Cell('', []),
                                                                  tc4_corr(ctx, D) if promo else Cell('', []))])
    if not promo:
        rows.append(['Pc re-zero limit on the compensated residual; BASE check, default / B-PC-1-shown build (264 (2))',
                     cat(r['rz'].h(), '; ', r['bc'].h(unit=False, pill=False), ' / ', r['bc2'].h(), f' <span class="ev ev-status">{esc(w)}</span>',
                         Cell(''.join(t.ref() for t in wt), wt), gnote('the v2.11 values these replace are shown in §10.2-§10.5 with the not-accepted note: '
                                                                       'contradiction register C-13'), carve(ctx, D, 'lim_264_2'))])
    else:
        rows.append(['Pc re-zero limit on the compensated residual; BASE check, default / B-PC-1-shown build (264 (2))',
                     cat(r['rz'].h(), '; ', r['bc'].h(unit=False, pill=False), ' / ', r['bc2'].h(), ' ', lab_acc(D, 'kIgnBaseCheck_Pa 0.76 / 0.46 bar'),
                         gnote('the v2.11 values these replace (electronics.json v4): contradiction register C-13'), carve(ctx, D, 'lim_264_2'))])
    rows.append(['A1 BASE_AMB outcome (264 (3))', cat(tvtxt(cl.item(264, 3), 800), gnote('closes OI-A1-BASE-AMB (§10.9): contradiction register C-16'),
                                                      lab_susp(D, 'the evidence (not the decision) of 264 (3); re-shown on v2.13') if promo else Cell('', []),
                                                      carve(ctx, D, 'relight'))])
    rows.append(['P_torch transducer, OI-PTORCH-PROOF (264 (4))', cat(tvtxt(cl.item(264, 4), 1600), gnote('contradiction register C-10 and C-14'))])
    rows.append(['T4 relight, OI-T4-RESIZE (264 (5))', cat(tvtxt(cl.item(264, 5), 900), gnote('§7.9; contradiction register C-15'),
                                                           (gnote(f'T4 is a stand relight: it waits for v2.13 ({n} (6)){D["ele"]["cons_tv"].ref()}', [D['ele']['cons_tv']])
                                                            if promo else Cell('', [])), carve(ctx, D, 'relight'))])
    i6 = cl.item(264, 6)
    t0a = rx_text(ctx, i6, r'T0 (\d+)-\d+ C', '°C')
    t0b = rx_text(ctx, i6, r'T0 \d+-(\d+) C', '°C')
    for t in (t0a, t0b):
        if t.value is not None and t.basis:
            t.basis += '; an ASSUMED design range (264 (6))'
    rows.append(['A1 flight T0 range (264 (6))', cat(tvtxt(i6, 500), '<br>Range ', t0a.h(), ' to ', t0b.h())])
    rows.append(['OI-JFWD-FLIGHT, PROVISIONAL (264 (7))', cat(tvtxt(cl.item(264, 7), 800), ele41_oi_note(ctx, D, 'OI-JFWD-FLIGHT') if promo else Cell('', []))])
    rows.append(['REV-ELEC-4 and work not done (264 (8))', tvtxt(cl.clip(264, 8, 'v4.1 is promoted only after its verdict', 'can affect.'), 500)])
    if promo:
        rows += ele41_rulings_266_rows(ctx, D)
    cap = ('CHANGELOG line 264 (lead). Each item is a lead decision (DECIDED, Lead decision, line 264 (k)); numbers quoted in an item keep their own tags. '
           + ('The firmware v2.12 and electronics.json v4.1 that implement them are PENDING REVIEW (REV-ELEC-4); interfaces/electronics.json v4 stays the source of record.'
              if not D['ele']['promo'] else f'electronics.json v4.1 implements them; it is the source of record under line {D["ele"]["line"]} (§10.0), with '
                                              f'option (b) carved out of every start with ignition until a reviewed v2.13 delta ({D["ele"]["line"]} (6)).'))
    return dtable(['Ruling', 'Text (quoted) and values'], rows, widths=['24%', '76%'], cls='tight', caption=cap)


def ele41_head_note(ctx, D):
    """Top note of §10 in the promoted-v4.1 build (filled in when that build is implemented)."""
    m = ctx.missing('promoted-v4.1 head note (not implemented in this generator yet)', 'MISSING')
    return note_box(m.h(), 'warn')


def tc_channels_cell(ctx, D, E, TC):
    """Thermocouple channels; in the promoted build the TC4 label correction of line 266 (7) (C1 seat, not bore top)."""
    t = ctx.v(E, f'{TC}/channels', tag='DESIGN')
    c = tvtxt(t, 500)
    if D['ele']['promo'] and 'bore top' in _plain_text(t.value):
        c = cat(c, tc4_corr(ctx, D))
    return c


def tc4_corr(ctx, D):
    """The TC4 label correction of line 266 (7), quoted from that line (C1 seat TC, not bore top)."""
    n = D['ele']['line']
    return corr(ctx, D, D['cl'].clip(n, 7, 'TC4 is the C1 seat TC (MAX31856 U904, J904, BOM row 205), not bore top',
                                     'the file keeps the old label until v4.2)'), 'TC4 label')


def sel_cell(ctx, D, E, PT):
    """Pressure-transducer selection; in the promoted build the 264 (4) fold that line 266 (7) applies (P_TORCH is the XTL-190SM-2000A)."""
    t = ctx.v(E, f'{PT}/selection')
    c = tvtxt(t, 500)
    if D['ele']['promo'] and '070BG' in _plain_text(t.value):
        n = D['ele']['line']
        f7 = D['cl'].clip(n, 7, 'the 264 (1)-(8) folds such as P_TORCH XTL-190SM-2000A', 'the 264 (1)-(8) folds such as P_TORCH XTL-190SM-2000A')
        c = cat(c, gnote(f'{n} (7), E4-05 (7){f7.ref()}: the 264 (4) fold applies: P_TORCH is the XTL-190SM-2000A; the file keeps the 070BG entry until v4.2; '
                         'contradiction register C-10', [f7]))
    return c

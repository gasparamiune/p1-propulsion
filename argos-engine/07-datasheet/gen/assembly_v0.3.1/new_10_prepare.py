# ---------------------------------------------------------------------------------------------
# preparation (v0.3.0): renders, BOM, mass, envelope, pending inputs
# ---------------------------------------------------------------------------------------------
def hw_mass_class(ms):
    u = (ms or '').strip().upper()
    if not u:
        return None
    if u.startswith('CALC'):
        return 'CALC'
    if u.startswith('TO-FETCH'):
        return 'MISSING'
    if u.startswith('NEGLIGIBLE'):
        return 'ASSUMED'
    return bom_mass_class(ms)


class HwRow(BomRow):
    """BOM /hardware/lines row (standard parts, not modelled): CALC masses."""

    def __init__(self, ctx, idx, line):
        self.kind, self.idx, self.l = 'hardware', idx, line
        self.pn = line['pn']
        self.fam = family_of(self.pn)
        self.qty = fnum(line.get('qty'))
        self.unit = fnum(line.get('unit_mass_kg'))
        self.mclass = hw_mass_class(line.get('mass_source'))
        self.pstate = price_state(line.get('unit_price'))
        ptr = ptr_join('hardware', 'lines', idx)
        self.row_tv = TV(ctx, f"{self.pn}: {line.get('name', '')}", '', 'DESIGN', 'BOM hardware row (standard part, not modelled)', 'BOM', ptr,
                         note='row trace: name, qty, host, size, grade, torque, tightening method, unit_mass_kg, mass_source, unit_price')
        if self.unit is not None:
            self.mass_tv = TV(ctx, self.unit, 'kg', self.mclass or 'CALC', line.get('mass_source'), 'BOM', ptr + '/unit_mass_kg')
        else:
            st = 'MISSING' if self.mclass in (None, 'MISSING') else self.mclass
            self.mass_tv = TV(ctx, None, 'kg', st, line.get('mass_source'), 'BOM', ptr + '/unit_mass_kg', status=st if st != 'ASSUMED' else 'negligible')
        self.line_mass = (self.unit * self.qty) if (self.unit is not None and self.qty is not None) else None
        if self.pstate == 'INVALID':
            ctx.issue('ERROR', f'BOM hardware {self.pn}: price field violates the price rule: {line.get("unit_price")!r}')


def ele_state(ctx, a, cl):
    """Record state of the electronics interface (lead 2026-10-21 13:45Z): electronics.json v4 with the v4.1 candidate PENDING
    REVIEW (the default build), or the promoted-v4.1 build (--ele41-line N, N the CHANGELOG line that records the promotion)."""
    st = {'promo': False, 'line': None, 'promo_tv': None, 'carve': [], 'wording': {},
          'pend_tv': cl.clip(264, 1, 'interfaces/electronics.json stays v4', 'as PENDING REVIEW.')}
    n = getattr(a, 'ele41_line', None)
    if n:
        # promoted-v4.1 build (lead GO 2026-10-21 14:48:44Z): line n records the promotion (266 (7)), the carve-out (266 (6)) and the
        # REV-ELEC-4 verdict (266 (4)); every text below is a clip of that line, so the datasheet quotes the lead, never paraphrases it
        st.update(promo=True, line=n)
        st['promo_tv'] = cl.clip(n, 7, 'PROMOTED 14:45:39Z', 'under the carve-out of (6).')
        st['carve_tv'] = cl.clip(n, 6, 'Option (b) (seat coefficient loaded', 'bench work without ignition.')
        st['cons_tv'] = cl.clip(n, 6, 'Consequences under the rulings in force:', 'keeps the A1 relight at k = 3 [SIM S13T].')
        st['susp_tv'] = cl.clip(n, 6, 'Suspended until v2.13, and marked so wherever shown:', 'the B-PC-1 / B-TC-1 TC4 rows.')
        st['acc_tv'] = cl.clip(n, 6, 'Accepted now:', 'the T1-T4 planning rule.')
        st['gov_tv'] = cl.clip(n, 7, 'Until v4.2 this line governs v4.1 where they differ:', 'Bench plan v5 does not go to the founders before these corrections.')
        st['verdict_tv'] = cl.clip(n, 4, 'REV-ELEC-4 (independent delta review of Electronics v2.12', '11 NOTES')
        st['q8_tv'] = cl.clip(n, 8, 'QUEUED, NOT STARTED (the founder says when)', 'a SIL MANIFEST_v2).')
        st['routed_tv'] = cl.clip(n, 8, 'Routed: E4-N08', 'are GNC and lead items with v2.13.')
        st['e401_tv'] = cl.item(n, 5)
        st['carve'] = [{'id': f'Carve-out, {n} (6)', 'anchors': ['opt_b_comp', 'relight', 'lim_264_2'], 'tv': st['carve_tv']}]
        s = ctx.src('ELE')
        m = re.search(r'electronics_v4\.1\.json ([0-9a-f]{16}), byte for byte', st['promo_tv'].value or '')
        if not m or m.group(1) != s.sha16:
            ctx.issue('ERROR', f'promoted build: interfaces/electronics.json sha256/16 {s.sha16} is not the file line {n} (7) promotes')
        if str((s.data or {}).get('version')) != 'v4.1':
            ctx.issue('ERROR', f'promoted build: interfaces/electronics.json is {(s.data or {}).get("version")}, not v4.1')
        st['wording'] = {'base': 'kIgnBaseCheck_Pa 0.76 / 0.46 bar implemented in v4.1: ACCEPTED (REV-ELEC-4, line {n})',
                         'purge': 'implemented in v2.12 (v4.1): ACCEPTED (REV-ELEC-4, line {n})',
                         'purge_status': 'implemented in v4.1: ACCEPTED (REV-ELEC-4, line {n}); the measured-time form is open after CF-4 / B-BLEED-1',
                         'c13_status': 'v4.1 implementation: kIgnBaseCheck_Pa 0.76 / 0.46 bar ACCEPTED (REV-ELEC-4, line {n}); the option (b) rows and '
                                       'residuals SUSPENDED UNTIL v2.13 ({n} (6))'}
    return st


def impl_txt(D, key, pending, promoted):
    """(text, tvs) of the state of the electronics implementation of a lead decision: the pending wording with the 264 (1) record,
    or, in the promoted-v4.1 build, the promotion wording with the promotion line ('{n}' is its number; the lead's wording for the
    key, when the carve-out file gives one, replaces the default) (lead 2026-10-21 13:47Z)."""
    e = D['ele']
    if e['promo']:
        w = (e['wording'].get(key) or promoted).format(n=e['line'])
        # each label cites the item of line n that sets it: the promotion (7), ACCEPTED and SUSPENDED UNTIL v2.13 (6)
        return w, [e['promo_tv']] + ([e['acc_tv']] if 'ACCEPTED' in w else []) + ([e['susp_tv']] if 'SUSPENDED' in w else [])
    return pending, [e['pend_tv']]


def prepare(ctx, a):
    D = {'generated': now_utc()}
    D['cl'] = cl = Changelog(ctx, 'CL')
    D['ele'] = ele_state(ctx, a, cl)
    idx = pts_index(ctx)
    D['tpi'] = idx
    D['rated'] = {'F': tp(ctx, idx, 1.0, 'F_N', 'N'), 'Isp': tp(ctx, idx, 1.0, 'Isp_SL_s', 's'), 'OF': tp(ctx, idx, 1.0, 'OF')}
    pc = tp(ctx, idx, 1.0, 'Pc_Pa', 'Pa')
    D['pc_rated'] = pc
    D['pc_rated_cell'] = Cell(pres(ctx, pc), [pc])
    D['floor_F'] = tp(ctx, idx, 0.2, 'F_N', 'N')  # floor target 20 % (rev0 basis); 25 % requirement and 12.5 % stretch in section 2
    D['mass_wet_all'] = ctx.v('MP', '/states/wet/all/m_kg', 'kg', tag='DERIVED', note='CAD model total, wet (full grain); hardware CALC carried')
    D['mass_mid_eng'] = ctx.v('MEC', '/gimballed_mass_properties_v352/states/mid/engine/m_kg', 'kg', tag='DERIVED')
    # envelope from the assembly manifest
    lo, hi, n = manifest_extent(ctx)
    elo, ehi, en = manifest_extent(ctx, group='engine')
    flo, fhi, fn = manifest_extent(ctx, group='fixed')
    dims = {'lo': lo, 'hi': hi,
            'H': man_tv(ctx, hi[2] - lo[2], 'overall z extent'), 'top': man_tv(ctx, hi[2], 'z of the forward end (pivot at z 0)'),
            'aft': man_tv(ctx, -lo[2], 'distance pivot to aft end'), 'Wx': man_tv(ctx, hi[0] - lo[0], 'x extent'), 'Wy': man_tv(ctx, hi[1] - lo[1], 'y extent')}
    if en:
        dims.update(eng_lo=elo[2], eng_hi=ehi[2], eng_len=man_tv(ctx, ehi[2] - elo[2], 'z extent', group='engine'),
                    eng_rng=man_tv(ctx, [elo[2], ehi[2]], 'z range', group='engine'))
    if fn:
        dims.update(fix_lo=flo[2], fix_hi=fhi[2], fix_len=man_tv(ctx, fhi[2] - flo[2], 'z extent', group='fixed'),
                    fix_rng=man_tv(ctx, [flo[2], fhi[2]], 'z range', group='fixed'))
    D['geo'] = {'dims': dims, 'n_inst': n}
    Wx, Wy, H = dims['Wx'], dims['Wy'], dims['H']
    D['env_cell'] = Cell(f'<span class="v">{fmt_num(Wx.value, ".1f")} × {fmt_num(Wy.value, ".1f")} × {fmt_num(H.value, ".1f")}</span>'
                         f'<span class="u">&#8239;mm</span> {H.pill()}{Wx.ref()}{Wy.ref()}{H.ref()}', [Wx, Wy, H])
    # renders
    check_renders(ctx, a)
    R = {}
    R['iso_alpha'] = prep_render(ctx, a, 'iso', keep_alpha=True)
    R['iso'] = prep_render(ctx, a, 'iso')
    for v in ('front', 'side', 'section', 'layout'):
        R[v] = prep_render(ctx, a, v)
    # BOM
    bom = load_bom(ctx)
    D['bom'] = bom
    b = ctx.src('BOM').data or {}
    D['gse'] = [BomRow(ctx, 'gse_tool_lines', i, l) for i, l in enumerate(b.get('gse_tool_lines', []))]
    D['hw'] = [HwRow(ctx, i, l) for i, l in enumerate((b.get('hardware') or {}).get('lines', []))]
    by = {}
    for r in bom + D['gse'] + D['hw']:
        if r.pn not in by:
            by[r.pn] = r
    D['bom_by_pn'] = by
    order, fams = [], {}
    for r in bom:
        if r.kind != 'lines' or r.l.get('groups') == 'lock':
            continue
        if r.fam not in order:
            order.append(r.fam)
    D['family_order'] = order
    for f in order:
        rs = [r for r in bom if r.kind == 'lines' and r.fam == f and r.l.get('groups') != 'lock']
        miss = [r.pn for r in rs if r.line_mass is None]
        m = sum(r.line_mass for r in rs if r.line_mass is not None)
        fams[f] = {'n_tv': ctx.d(len(rs), '', f'count of BOM lines with part-number family {f}', [r.row_tv for r in rs]),
                   'mass_tv': ctx.d(m, 'kg', f'Σ qty × unit mass over the {f} lines', [r.mass_tv for r in rs], ev='TO-VERIFY' if miss else 'DERIVED',
                                    note=(f'lines without a mass: {", ".join(miss)}' if miss else ''))}
        R['family_' + f] = prep_render(ctx, a, 'family_' + f)
    D['families'] = fams
    D['R'] = R
    lines = [r for r in bom if r.kind == 'lines' and r.l.get('groups') != 'lock']
    tot = sum(r.line_mass for r in lines if r.line_mass is not None)
    D['bom_sum_tv'] = ctx.d(tot, 'kg', 'Σ qty × unit mass over all BOM lines (transport lock excluded)', [f['mass_tv'] for f in fams.values()])
    lock = [r for r in bom if r.kind == 'lines' and r.l.get('groups') == 'lock']
    D['bom_lock_tv'] = ctx.d(sum(r.line_mass for r in lock if r.line_mass is not None), 'kg',
                             'Σ qty × unit mass over the transport-lock lines (group lock)', [r.mass_tv for r in lock])
    hws = sum(r.line_mass for r in D['hw'] if r.line_mass is not None)
    D['hw_sum_tv'] = ctx.d(hws, 'kg', 'Σ qty × unit mass over the BOM hardware lines (CALC)', [r.mass_tv for r in D['hw']], ev='CALC',
                           note='lines without a mass: ' + ', '.join(r.pn for r in D['hw'] if r.line_mass is None))
    D['bom_mass_sum'] = ctx.v('BOM', '/mass_sum_kg', 'kg', tag='DERIVED', tag_ptr='/mass_sum_note')
    bs = D['bom_mass_sum'].value
    if bs is not None and abs(bs - tot) > 1e-3:
        ctx.issue('INFO', f'BOM mass_sum_kg {bs} vs the generator sum {tot:.4f} (lock lines {D["bom_lock_tv"].value:.4f} kg)')
    D['cost_tv'] = TV(ctx, None, 'EUR', 'MISSING', 'BOM unit_price: every line TO-QUOTE (delivery Sonderborg, Denmark, DK-6400)', 'BOM', '/lines/*/unit_price',
                      note='total not summed: no line carries a DK-6400 quotation', status='TO-QUOTE (not summed)')
    ctx.unknowns.append({'what': 'Total cost (every BOM line TO-QUOTE, delivery Sønderborg DK-6400)', 'status': 'MISSING', 'tid': D['cost_tv'].tid})
    # material usage (BOM lines; hardware listed separately)
    mu = {}
    for r in lines:
        k = r.l.get('material_name') or r.l.get('material') or 'unspecified'
        mu.setdefault(k, []).append(r)
    D['mat_usage'] = {k: {'n_tv': ctx.d(len(v), '', f'count of BOM lines with material_name "{k}"', [r.row_tv for r in v]),
                          'mass_tv': ctx.d(sum(r.line_mass or 0 for r in v), 'kg', f'Σ qty × unit mass, material "{k}"', [r.mass_tv for r in v]),
                          'o2_tv': ctx.d(sum(1 for r in v if str(r.l.get('oxygen_clean')) == 'True'), '', f'count of oxygen-clean lines, material "{k}"', [r.row_tv for r in v])}
                      for k, v in mu.items()}
    D['cause_idx'] = {c.get('cause'): i for i, c in enumerate(ctx.raw('ELE', '/abort_matrix/causes', default=[]) or [])}
    # items outside the CAD mass (not zero: carried at their source value or UNKNOWN); v2.1 records labelled
    v21 = 'mechanical.json v2.1 record (not re-derived for v3.5.2: not_re_derived_v352)'
    ex, ep, er = [], [], []
    tank = ctx.v('MEC', '/fixed_module/tank/tube_mass_kg', 'kg', tag='DERIVED', note=v21)
    ex.append(['N2O tank: tube only (bulkheads, valves, fittings not designed)', num_cell(tank, '.3f'),
               cat(tvtxt(ctx.v('MEC', '/fixed_module/tank/concept', tag='DERIVED', note=v21), 160), f'<div class="small">{esc(v21)}</div>')])
    ep.append(('N2O tank, tube only', tank.value))
    er.append(tank.tid)
    prng = ctx.v('BOM', '/provision_mass_estimate_kg/estimate_range_kg', 'kg', tag='ASSUMED')
    ex.append(['Head-end bleed provision, excluding valves (BOM provision lines)', num_cell(prng, '.3f'),
               tvtxt(ctx.v('BOM', '/provision_mass_estimate_kg/note', tag='ASSUMED'), 200)])
    ep.append(('Bleed provision excl. valves', tuple(prng.value) if isinstance(prng.value, list) else prng.value))
    er.append(prng.tid)
    nm = ctx.v('MEC', '/fixed_module/not_modelled', tag='MISSING', note=v21)
    nmm = ctx.missing('mass of the items listed as not modelled in mechanical.json (v2.1 record)', 'MISSING')
    ex.append(['Other items not modelled (mechanical.json list)', Cell(nmm.h(), [nmm]), tvtxt(nm, 300)])
    ep.append(('Other items not modelled', None))
    er.append(nmm.tid)
    ecu = ctx.v('ELE', '/ecu/mass_kg', 'kg')
    ecur = ctx.v('ELE', '/ecu/mass_kg/range', 'kg', tag='ASSUMED')
    ex.append(['Engine ECU (on the fixed structure, not in CAD)', cat(ecu.h('.2f'), ' (', ecur.h('.2f', pill=False), ')'),
               tvtxt(ctx.v('ELE', '/ecu/architecture'), 160)])
    ep.append(('Engine ECU', tuple(ecur.value) if isinstance(ecur.value, list) else ecu.value))
    er.append(ecu.tid)
    n2o = ctx.v('CMB', '/decisions/N2O_load_and_tank/v/m_N2O_kg', 'kg', tag_ptr='/decisions/N2O_load_and_tank')
    ex.append(['N2O load (propellant)', num_cell(n2o, '.2f'), tvtxt(ctx.v('CMB', '/decisions/N2O_load_and_tank/tag', tag='LEAD'), 160)])
    er.append(n2o.tid)
    D['exclusions'], D['excl_plot'], D['excl_refs'] = ex, ep, er
    # inputs still pending at this build (from the decision log, never assumed; lead update 2026-10-21 12:52Z)
    pend = []
    if not D['ele']['promo']:
        pend.append(('Electronics v2.12: firmware v2.12 and the electronics.json v4.1 candidate are PENDING REVIEW (REV-ELEC-4); interfaces/electronics.json v4 '
                     'stays the source of record', cl.clip(264, 1, 'interfaces/electronics.json stays v4', 'as PENDING REVIEW.')))
        pend.append(('REV-ELEC-4 verdict (PENDING; never assumed)', cl.clip(264, 8, 'v4.1 is promoted only after its verdict', 'its verdict.')))
    else:
        n = D['ele']['line']
        pend.append((f'Electronics v2.13 delta (the E4-01 fix) and its review: QUEUED, NOT STARTED; the founder says when ({n} (8)). Until it is reviewed, '
                     f'option (b) is not used for any start with ignition ({n} (6))', D['ele']['q8_tv']))
    pend.append(('T4 re-run: the length of the shorter T4 relight (OPEN, 261 (2) and 264 (5))', cl.clip(264, 5, 'Combustion sets the length', "soak-back.")))
    D['pending'] = pend
    mx_negatives(ctx, D)
    D['pending_inputs'] = [p[0] for p in pend]
    D['pending_n'] = ctx.d(len(pend), '', 'count of inputs pending at this build (§1.4)', [p[1] for p in pend], ev='PENDING')
    return D

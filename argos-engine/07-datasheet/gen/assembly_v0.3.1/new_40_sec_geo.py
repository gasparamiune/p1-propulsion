# ---------------------------------------------------------------------------------------------
# cover and sections 4-6 (v0.3.0): geometry and mass, parts list, materials
# ---------------------------------------------------------------------------------------------
def sec_cover(ctx, doc, a, D):
    rated = D['rated']
    cfg = [('CMB', 'Combustion'), ('MEC', 'Mechanical'), ('ELE', 'Electronics'), ('GNC', 'Space/GNC'), ('F3D', '3D FEA report'),
           ('MMX', 'Margin matrix (rows v8)'), ('REQ', 'Requirements'), ('CL', 'Decision log'), ('SUP', 'Review register')] + \
          ([('OVR', 'Decision overrides')] if 'OVR' in ctx.sources else [])
    gabs = glb_absent(ctx, D)
    cfg_rows = ''.join(f'<tr><td>{n}</td><td>{esc(ctx.src(s).version or "–")}</td><td class="mono">{esc(ctx.src(s).sha16 or "MISSING")}</td></tr>'
                       for s, n in cfg)
    nt = D['neg_total']
    tiles = [
        ('Rated thrust (SL), Pc at the software cap', rated['F']), ('Chamber pressure, rated', D['pc_rated_cell']),
        ('Throttle floor target (20 %)', D['floor_F']), ('Isp, rated (SL)', rated['Isp']),
        ('CAD mass, wet, all groups (hardware CALC)', D['mass_wet_all']), ('Envelope (CAD bounding box)', D['env_cell']),
        ('Found negatives in the margin matrix (§9.3)', nt), ('Inputs still PENDING (§1.4)', D['pending_n']),
    ]
    th = ''.join(f'<div class="tile"><div class="tl">{esc(l)}</div><div class="tv">{(v.h() if isinstance(v, TV) else v.html)}</div></div>' for l, v in tiles)
    CELL_STATS['data_cells'] += len(tiles)
    CELL_STATS['traced'] += len(tiles)
    hero = D['R'].get('iso_alpha')
    hero_html = f'<img class="hero" src="{hero["file"]}" alt="CAD render, isometric">' if hero else '<div class="miss">render missing</div>'
    return f'''
<section class="cover">
 <div class="cv-band">
  <div class="cv-prog">ARGOS H1 · engine programme · {esc(DOC_ID)}</div>
  <div class="cv-title">Engine technical datasheet</div>
  <div class="cv-sub">N<sub>2</sub>O / printed-ABS hybrid rocket engine · servo-pintle throttle · two-axis gimbal · for a self-landing rocket</div>
 </div>
 <div class="cv-main">
  <div class="cv-hero">{hero_html}<div class="cv-cap">FINAL CAD {esc(a.cad_version)} assembly, neutral pose. Visualisation of tessellated display geometry (GLB {esc(ctx.src("GLB").sha16 or "MISSING")}), not a drawing. {gabs.h()}</div></div>
  <div class="cv-side">
   <div class="cv-draft">{esc(a.status)} · {esc(a.rev)}</div>
   <div class="cv-warn"><b>{esc(PAGE_STATEMENT)}.</b> Nothing in this datasheet is physical approval or acceptance. No value is MEASURED. Every number carries one of the ten evidence tags (SIM, CALC, DERIVED, ASSUMED, DATASHEET, LITERATURE, AS RECALLED, TO-VERIFY, MISSING, ESTIMATE) or the source-class pill DECIDED (a design value, decided limit or requirement: chosen, not measured or computed), and a trace reference (T###, Appendix A). Missing data are shown as MISSING, TO-DEFINE or PENDING, never estimated by the generator.</div>
   <div class="tiles">{th}</div>
   <table class="cv-cfg"><thead><tr><th>Configuration</th><th>Version</th><th>sha256/16</th></tr></thead><tbody>
   <tr><td>CAD (FINAL)</td><td>{esc(a.cad_version)}</td><td class="mono">manifest {esc(ctx.src("CADMAN").sha16 or "MISSING")}</td></tr>
   {cfg_rows}</tbody></table>
   <div class="cv-gen">Generated {esc(D["generated"])} by gen/{GEN_NAME} {GEN_VERSION}. Quotations: delivery Sønderborg, Denmark, DK-6400 (every price TO-QUOTE). Units SI; pressures in bar abs unless marked.</div>
  </div>
 </div>
</section>'''


def sec_geometry_mass(ctx, doc, a, D):
    o = [doc.h(1, '4 Geometry and mass')]
    o.append(note_box('<b>Renders are visualisation only.</b> They are produced by gen/render_views.sh from the tessellated GLB display mesh '
                      f'of the FINAL CAD {esc(a.cad_version)} (GLB sha256/16 {esc(ctx.src("GLB").sha16)}; render manifest {esc(ctx.src("RMAN").sha16)}). '
                      'They are not drawings and carry no tolerances. Dimensions printed on them are bounding-box extents from the assembly manifest; '
                      'the STEP solids are the CAD of record.', 'warn'))
    g = D['geo']
    o.append(doc.h(2, '4.1 Envelope and principal dimensions'))
    R = D['R']
    figs = []
    for key, axis, title in (('front', 0, 'Front view (looking along +Y)'), ('side', 1, 'Side view (looking along −X)')):
        if R.get(key):
            dims = dict(g['dims'])
            dims['Wh'] = g['dims']['W' + 'xy'[axis]]
            figs.append(f'<div class="ortho">{svg_ortho_dims(ctx, R[key], axis, dims, title)}</div>')
    o.append('<div class="ortho-pair">' + ''.join(figs) + '</div>')
    d = g['dims']
    rows = [
        ['Overall length along the engine axis (z)', num_cell(d['H'], '.1f')],
        ['Overall width X / Y (axis-aligned bounding box)', cat(d['Wx'].h('.2f'), ' / ', d['Wy'].h('.2f'))],
        ['Pivot to forward end / pivot to aft end', cat(d['top'].h('.1f'), ' / ', d['aft'].h('.1f'))],
        ['Gimballed engine group: z range / length', cat(d['eng_rng'].h('.1f'), ' / ', d['eng_len'].h('.1f'))],
        ['Fixed module (thrust frame, valve module, servos): z range / length', cat(d['fix_rng'].h('.1f'), ' / ', d['fix_len'].h('.1f'))],
        ['GLB read-back: meshes / bounds error / result', cat(ctx.v('GLBR', '/readback_meshes', tag='DERIVED').h('d'), ' / ',
                                                           ctx.v('GLBR', '/bounds_err_m', 'mm', conv=(1000, 0, 'm to mm'), tag='DERIVED').h('.3f'), ' / ',
                                                           ctx.v('GLBR', '/passed', tag='DERIVED').h())],
        ['Clearance at 18 poses: not-whitelisted interferences / smallest moving clearance',
         cat(ctx.v('CLR', '/summary/n_not_whitelisted', tag='DERIVED').h('d'), ' / ', ctx.v('CLR', '/summary/min_moving_clearance_mm', 'mm', tag='DERIVED').h('.3f'))],
    ]
    bay = bay_cells(ctx, D)
    rows += [
        ['Engine-bay inner diameter (requirement)', tvtxt(bay['req'])],
        ['Thrust rings GM-09 / GM-10: outer diameter (CAD bounds) / radial gap to the bay bore', cat(bay['ring_od'].h('.2f'), ' / ', bay['gap'].h('.3f'))],
        ['Instances reaching beyond the ring radius (CAD bounds)', tvtxt(bay['beyond'], 400)],
    ]
    o.append(dtable(['Dimension', 'Value'], rows, widths=['42%', '58%'],
                    caption=f'Envelope from the union of the {g["n_inst"]} instance bounding boxes in the assembly manifest (engine frame, mm, origin at the gimbal pivot, +z forward). '
                            'An axis-aligned box does not bound the radial extent; the pose clearance check is listed in §4.6. The bay requirement is '
                            'REQUIREMENTS.md §1 (the airframe ICD draft 0.2 is not used, see §4.5).'))
    o.append(doc.h(2, '4.2 Assembly views'))
    gabs = glb_absent(ctx, D)
    o.append(note_box('<b>What the renders do not show.</b> ' + gabs.h(), 'info'))
    if R.get('iso'):
        o.append(f'<figure class="render iso"><img src="{R["iso"]["file"]}"><figcaption>Isometric view, FINAL CAD {esc(a.cad_version)}, neutral pose '
                 f'(render {esc(R["iso"]["png_sha16"])}). Visualisation only; parts not in the GLB are listed above the figure.</figcaption></figure>')
    if R.get('layout'):
        o.append(f'<figure class="render layout">{svg_layout(ctx, R["layout"])}<figcaption>Thrust chamber and pintle stack laid out side by side '
                 'along the axis order (pintle drive at left, nozzle joint at right), true scale. Axial positions are not preserved; the CAD z range '
                 'of each group is printed under it. Visualisation only.</figcaption></figure>')
    if R.get('section'):
        svg, shown, missing = svg_section(ctx, R['section'], D['bom_by_pn'], SECTION_CALLOUTS)
        D['section_shown'] = shown
        refs = [D['bom_by_pn'][p].row_tv.tid for p in shown if p in D['bom_by_pn']]
        o.append(f'<figure class="render section">{svg}<figcaption>Half section in the plane y = 0 (the y &lt; 0 half removed; cut faces darkened). '
                 'Labels: BOM name, part number and material, placed at the area-weighted centroid of each part\'s cut face. '
                 'Visualisation of display geometry, not a drawing. The section shows no screw, spring or other standard hardware (not in the GLB; see the note in §4.2).'
                 + (f' Parts without a cut face in this plane: {esc(", ".join(missing))}.' if missing else '')
                 + ' <span class="figref">BOM rows: ' + ', '.join(f'<a class="tr" href="#{r}">{r}</a>' for r in refs) + '</span></figcaption></figure>')
    o.append(doc.h(2, '4.3 Part families'))
    cards = []
    for fam, info in D['families'].items():
        Rf = R.get('family_' + fam)
        img = f'<img src="{Rf["file"]}">' if Rf else '<div class="miss">render missing</div>'
        cards.append(f'<div class="fam"><div class="fimg">{img}</div><div class="fcap"><b>{esc(fam)} · {esc(FAMILY_NAMES.get(fam, fam))}</b><br>'
                     f'{info["n_tv"].h()} lines · {info["mass_tv"].h(".3f")}</div></div>')
        CELL_STATS['data_cells'] += 2
        CELL_STATS['traced'] += 2
    o.append('<div class="famgrid">' + ''.join(cards) + '</div>')
    hwfam = (R.get('family_HW') or {}).get('meta', {}).get('pns') or []
    o.append('<p class="small">Each family is rendered at its assembly position (not exploded). Line counts and masses are sums over the BOM lines '
             'of the family (qty × unit mass, DERIVED by this generator; the transport lock and the standard hardware lines are excluded). '
             + (f'The HW family render shows the modelled BOM lines {esc(", ".join(hwfam))} (render metadata) and no fastener or spring: ' if hwfam else '')
             + 'the standard hardware of BOM /hardware and the transport lock are not in the GLB (§4.2).</p>')

    o.append(doc.h(2, '4.4 Mass'))
    states = ['wet', 'mid', 'burnout', 'nograin']
    groups = ['engine', 'ring', 'horn', 'pushrod', 'fixed', 'all']
    rows = []
    for gname in groups:
        cells = [f'{GROUP_NAMES.get(gname, gname)}']
        for s_ in states:
            t = ctx.v('MP', f'/states/{s_}/{gname}/m_kg', 'kg', tag='DERIVED', note='CAD volume × density, COTS masses and the hardware CALC (massprops hardware_rule)')
            cells.append(num_cell(t, '.4f'))
        rows.append(cells)
    o.append(dtable(['Group', 'Wet (full grain)', 'Mid-burn', 'Burn-out', 'No grain'], rows, widths=['32%', '17%', '17%', '17%', '17%'],
                    caption=f'Mass by subassembly and state, massprops {esc(src_label(ctx, "MP"))}. The states include the standard hardware carried as '
                            'max(0.20 kg allowance, CALC sum) at the host parts (lead 188 (11)). Group "all" is the CAD model total. Not weighed.'))
    G = '/gimballed_mass_properties_v352/states'
    rows = []
    for s_ in states:
        m = ctx.v('MEC', f'{G}/{s_}/engine/m_kg', 'kg', tag='DERIVED', note='mechanical.json _v352 (FINAL set massprops)')
        cg = ctx.v('MEC', f'{G}/{s_}/engine/cg_mm', 'mm', tag='DERIVED')
        ip = ctx.v('MEC', f'{G}/{s_}/engine/I_pivot_kgm2', 'kg·m²', tag='DERIVED')
        diag = ctx.d([ip.value[i][i] for i in range(3)] if isinstance(ip.value, list) else None, 'kg·m²', 'diagonal of I_pivot (Ixx, Iyy, Izz)', [ip])
        rows.append([esc(s_), num_cell(m, '.5f'), Cell(f'<span class="v">{esc(", ".join(f"{x:.3f}" for x in cg.value)) if isinstance(cg.value, list) else "MISSING"}</span>'
                                                       f'<span class="u">&#8239;mm</span> {cg.pill()}{cg.ref()}', [cg]),
                     Cell(f'<span class="v">{esc(", ".join(f"{x:.5f}" for x in diag.value)) if isinstance(diag.value, list) else "MISSING"}</span>'
                          f'<span class="u">&#8239;kg·m²</span> {diag.pill()}{diag.ref()}', [diag])])
    o.append(dtable(['State', 'Gimballed engine mass', 'CG (x, y, z) from the pivot', 'I about the pivot: Ixx, Iyy, Izz'], rows,
                    widths=['14%', '22%', '30%', '34%'],
                    caption='Gimballed body (group "engine": thrust chamber, grain, collar and levers, inner pins, pintle stack, engine shares of hose and lines, '
                            'J-FWD hardware), mechanical.json /gimballed_mass_properties_v352 (GNC input). Full inertia tensors in the source.'))
    hc = '/hardware_carried'
    gm = gnc_mass_cells(ctx, D)
    rows = [['Hardware carried: allowance / CALC sum / carried', cat(ctx.v('MP', f'{hc}/allowance_kg', 'kg', tag='LEAD', tag_ptr='/hardware_rule').h('.2f'), ' / ',
                                                                    ctx.v('MP', f'{hc}/calc_sum_kg', 'kg', tag='CALC').h('.5f'), ' / ',
                                                                    ctx.v('MP', f'{hc}/carried_kg', 'kg', tag='CALC').h('.5f'))],
            ['Hardware lines without a mass', tvtxt(ctx.v('MP', f'{hc}/lines_without_mass', tag='MISSING'))],
            ['Landing-mass change vs v3.5.1: as built / without the conditional TC-09 thinning / the thinning',
             cat(gm['dl'].h('+.4f'), ' / ', gm['dl0'].h('+.4f'), ' / ', gm['thin'].h('+.4f'))],
            ['GNC re-fly trigger and verdict', cat(gm['trig'].h('.2f'), '<br>', tvtxt(gm['verdict'], 300), '<br>', tvtxt(gm['evid'], 300))],
            ['CAD set mass statement', tvtxt(ctx.v('SET', '/mass', tag='CALC'), 500)],
            ['Electronics mass statement vs the trigger', tvtxt(ctx.v('ELE', '/mass_statement/against_trigger', tag_ptr='/mass_statement/against_trigger'), 500)]]
    o.append(dtable(['Item', 'Value'], rows, widths=['30%', '70%']))
    fam_rows = []
    for fam, info in D['families'].items():
        fam_rows.append([f'{fam} · {FAMILY_NAMES.get(fam, fam)}', Cell(info['n_tv'].h(), [info['n_tv']]), num_cell(info['mass_tv'], '.4f')])
    fam_rows.append(['Sum of BOM part lines (transport lock and standard hardware excluded)', '', num_cell(D['bom_sum_tv'], '.4f')])
    fam_rows.append(['BOM mass_sum_kg as published (BOM header)', '', num_cell(D['bom_mass_sum'], '.4f')])
    fam_rows.append(['Standard hardware lines (BOM /hardware, CALC)', '', num_cell(D['hw_sum_tv'], '.5f')])
    o.append(dtable(['BOM family', 'Lines', 'Mass'], fam_rows, widths=['56%', '14%', '30%'], free_cols=(),
                    caption='Mass by BOM part family (DERIVED: Σ qty × unit mass over the BOM lines).'))
    ex = D['exclusions']
    o.append(dtable(['Not in the CAD mass', 'Mass', 'Status / source'], [[e[0], e[1], e[2]] for e in ex], widths=['34%', '24%', '42%'],
                    caption='Items excluded from the CAD mass. They are not zero: each is carried at its source value or as UNKNOWN. '
                            'Rows from mechanical.json v2.1 sections are labelled: they were not re-derived for v3.5.2.'))
    src = plot_mass(a, [(f'{f} {FAMILY_NAMES.get(f, f)}', info['mass_tv'].value) for f, info in D['families'].items()], D['excl_plot'])
    o.append(fig_html(src, 'CAD mass by BOM family (solid) and items outside the CAD mass (hatched; ranges where the source gives one).',
                      [i['mass_tv'].tid for i in D['families'].values()] + D['excl_refs'], 'wide'))
    o.append(doc.h(2, '4.5 Airframe interface and engine mounting (current sources)'))
    cl = D['cl']
    rows = [subrow('Bay, attachment and gimbal', 2)]
    rows.append(['Engine-bay inner diameter (REQUIREMENTS.md §1)', tvtxt(bay['req'])])
    rows.append(['Thrust ring outer diameter / radial gap to the bay bore (CAD bounds)', cat(bay['ring_od'].h('.2f'), ' / ', bay['gap'].h('.3f'))])
    for pn in ('ENG-GM-09', 'ENG-GM-10'):
        r = D['bom_by_pn'].get(pn)
        if r is not None:
            rows.append([f'Airframe attachment: {pn} (BOM)', bom_name_cell(r)])
    scr = [D['bom_by_pn'][pn] for pn in ('ENG-HW-125', 'ENG-HW-126') if pn in D['bom_by_pn']]
    for r in scr:
        rows.append([f'Airframe screws: {r.pn} (BOM /hardware)', Cell(f'<span class="v">{esc(r.l.get("qty"))} × {esc(r.l.get("size") or "")}</span> '
                                                               f'<span class="small">{esc(clipw(r.l.get("name"), 110))}</span> {r.row_tv.pill()}{r.row_tv.ref()}', [r.row_tv])])
    if scr:
        nsc = ctx.d(sum(int(r.qty or 0) for r in scr), '', 'Σ qty of the airframe screw lines ' + ' + '.join(r.pn for r in scr), [r.row_tv for r in scr])
        rows.append(['Airframe screws in total', Cell(f'{nsc.h("d")} <span class="small">(the mounting holes of §9.6)</span>', [nsc])])
    rows.append(['Gimbal range / mechanical stop (REQ ENG-07)', cat(bay['rng'].h('.0f'), ' / ', bay['stop'].h('.0f'))])
    bl6 = D['bom_by_pn'].get('ENG-BL-06')
    if bl6 is not None:
        rows.append(['Head-end bleed vent through the bay wall (BOM)', bom_name_cell(bl6)])
    rows.append(['Feed across the gimbal (mechanical.json v2.1 record, not re-derived for v3.5.2)',
                 tvtxt(ctx.v('MEC', '/feed_across_gimbal/hose', note='mechanical.json /not_re_derived_v352 lists feed_across_gimbal'), 300)])
    rows.append(subrow('Loads into the airframe', 2))
    rows.append(['Max thrust (requirement ENG-01)', num_cell(bay['fmax'], '.0f')])
    rows.append(['Rated thrust (sea level), throttle point at the software Pc cap', num_cell(D['rated']['F'], '.1f')])
    ci = D['cause_idx'].get('OVER_THRUST')
    if ci is not None:
        rows.append([f'Over-thrust abort threshold (firmware {fw_ver(D)} config)', num_cell(ctx.v('ELE', f'/abort_matrix/causes/{ci}/thresholds/kOverThrust_N', 'N'), '.0f')])
    meop = ctx.v('CMB', '/operating_points/pressure_limits/chamber_MEOP_Pa', 'Pa')
    proof = ctx.v('CMB', '/operating_points/pressure_limits/proof_Pa', 'Pa')
    rows.append(['Chamber MEOP / proof pressure', cat(Cell(pres(ctx, meop), [meop]), ' / ', Cell(pres(ctx, proof), [proof]))])
    rows.append(['Lateral thrust at the gimbal range (max thrust × sin range)', num_cell(bay['flat'], '.1f')])
    DL = '/design_limit_loads'
    for k, lab in (('axial_accel_flight_g', 'Axial acceleration in flight, max of the dispersed set'),
                   ('axial_accel_touchdown_g', 'Axial acceleration after first contact (touchdown), max'),
                   ('lateral_accel_at_pivot_touchdown_g', 'Lateral acceleration at the pivot, touchdown, max'),
                   ('axial_accel_landing_shock_envelope_g', 'Landing shock envelope')):
        tv = ctx.v('GNC', f'{DL}/{k}', 'g')
        nt = ctx.raw('GNC', f'{DL}/{k}/note', default=None)
        p99 = rx(ctx, 'GNC', f'{DL}/{k}/note', r'p99 ([\d.]+) g', 'g', tag='SIM',
                 note='p99 of the same dispersed set, from the record note') if (isinstance(nt, str) and re.search(r'p99 [\d.]+ g', nt)) else None
        rows.append([f'{lab} (gnc.json {esc(ctx.src("GNC").version or "")})',
                     cat(num_cell(tv, '.2f'), *(['; p99 ', p99.h('.2f')] if p99 is not None else []))])
    rows.append(subrow('Mass', 2))
    rows.append(['CAD mass, wet, all groups (hardware CALC carried; not weighed)', num_cell(D['mass_wet_all'], '.4f')])
    rows.append(['GNC vehicle basis (massprops v3.5.1): liftoff mass / liftoff T/W (DATASHEET-INPUTS-GNC row 4)', cat(gm['lift'].h('.2f'), ' / ', gm['tw'].h('.2f'))])
    rows.append(['Landing-mass change v3.5.2 vs v3.5.1 / without the conditional TC-09 thinning; GNC re-fly trigger',
                 cat(gm['dl'].h('+.4f'), ' / ', gm['dl0'].h('+.4f'), '; trigger ', gm['trig'].h('.2f'))])
    rows.append(['Verdict (massdelta v3.5.2)', tvtxt(gm['verdict'], 300)])
    o.append(dtable(['Item', 'Value'], rows, widths=['40%', '60%'],
                    caption='Airframe-facing engine data from the current sources: REQUIREMENTS.md rev 2, the CAD v3.5.2 BOM and assembly manifest, '
                            f'combustion.json {esc(ctx.src("CMB").version or "")}, electronics.json {esc(ctx.src("ELE").version or "")}, '
                            f'gnc.json {esc(ctx.src("GNC").version or "")} and massdelta v3.5.2. Engine mounting hole loads and ring resultants of the v3.5.2 FEA: §9.6 '
                            '(they govern for the airframe).'))
    c222 = cl.clip(222, None, 'ICD-AIRFRAME v2.1 is REMOVED', '(superseded in places, not updated).')
    k222 = cl.clip(222, None, 'The items that were queued for it', 'the 2.20 kg tank option (line 219).')
    o.append(note_box('<b>ICD-AIRFRAME.</b> ' + inl(c222) + ' No value in this datasheet is taken from ICD-AIRFRAME draft 0.2 (2026-10-13): '
                      'every row above has a current source. ' + inl(k222) + ' In this datasheet: bay bore and envelope §4.1 and above; mounting loads §9.6; '
                      'engine-mount modes and axis stiffness §9.7; the BL-06 vent above; tank station and the 210 m apogee §11.1; the airframe first bending mode '
                      'and the 2.20 kg tank option §11.2 (rows 11d, 11g).', 'info'))
    o.append(doc.h(2, '4.6 CAD build, fit and interference checks'))
    rows = [['Build record', tvtxt(ctx.v('SET', '/build_evidence', tag='DERIVED'), 400)],
            ['STEP round trips (parts)', cat(ctx.v('CHK', '/roundtrip_parts/n_passed', tag='DERIVED').h('d'), ' of ', ctx.v('CHK', '/roundtrip_parts/n', tag='DERIVED').h('d'))],
            ['Final set vs the interim set', tvtxt(ctx.v('SET', '/final_vs_interim', tag='DERIVED'), 600)],
            ['Parts changed vs v3.5.1 (STL sha256)', tvtxt(ctx.v('SET', '/how_changed_was_found', tag='DERIVED'), 400)],
            ['Interference checks of record', tvtxt(ctx.v('SET', '/interference', tag='DERIVED'), 900)],
            ['Rebuild proof', tvtxt(ctx.v('SET', '/rebuild_proof/claim', tag='DERIVED'), 400)]]
    o.append(dtable(['Check', 'Record (quoted)'], rows, widths=['26%', '74%']))
    poses = ctx.raw('CLR', '/poses', default=[]) or []
    rows = []
    for k, p in enumerate(poses):
        base = f'/poses/{k}'
        pn = ctx.v('CLR', base + '/pose', tag='DESIGN')
        itf = ctx.v('CLR', base + '/interference', tag='DERIVED')
        nw = ctx.v('CLR', base + '/not_whitelisted', tag='DERIVED')
        cl3 = ctx.v('CLR', base + '/close_lt_3mm', tag='DERIVED')
        n_itf = ctx.d(len(itf.value or []), '', 'count of interference records at the pose (whitelisted thread overlaps included)', [itf])
        n_nw = ctx.d(len(nw.value or []), '', 'count of not-whitelisted interferences at the pose', [nw])
        n_cl = ctx.d(len(cl3.value or []), '', 'count of pairs closer than 3 mm at the pose', [cl3])
        dmin = ctx.d(min((c.get('dist_mm') for c in (cl3.value or []) if isinstance(c.get('dist_mm'), (int, float))), default=None), 'mm',
                     'smallest pair distance among the pairs closer than 3 mm', [cl3])
        rows.append([Cell(f'{esc(pn.value)}{pn.ref()}', [pn]), num_cell(n_itf, 'd'), num_cell(n_nw, 'd'), num_cell(n_cl, 'd'), num_cell(dmin, '.3f')])
    o.append(dtable(['Pose', 'Interference records (whitelisted)', 'Not whitelisted', 'Pairs closer than 3 mm', 'Smallest of those'], rows,
                    widths=['20%', '20%', '16%', '22%', '22%'],
                    caption=f'Software geometric check at 18 poses ({esc(src_label(ctx, "CLR"))}; run on the interim set, whose geometry the final set keeps except the '
                            'ENG-TC-01 material removal, see the CAD set record above). Pairs closer than 3 mm include expected contacts; a clean software check is not a physical fit check.'))
    return '\n'.join(o)


def sec_bom(ctx, doc, a, D):
    o = [doc.h(1, '5 Parts list')]
    deliv = ctx.v('BOM', '/delivery', tag='REQ')
    curr = ctx.v('BOM', '/currency', tag='DESIGN')
    nl = ctx.v('BOM', '/n_lines', tag='DERIVED')
    ni = ctx.v('BOM', '/n_instances', tag='DERIVED')
    rows = [['Delivery address for quotations', tvtxt(deliv)], ['Price status', tvtxt(curr)],
            ['BOM part lines / placed instances', cat(nl.h('d'), ' / ', ni.h('d'))],
            ['Standard hardware: lines / items', cat(ctx.v('BOM', '/hardware/n_lines', tag='DERIVED').h('d'), ' / ', ctx.v('BOM', '/hardware/n_items', tag='DERIVED').h('d'))],
            ['Hardware mass rule', tvtxt(ctx.v('BOM', '/hardware/mass_rule', tag='CALC'), 300)],
            ['Total cost', Cell(D['cost_tv'].h(), [D['cost_tv']])]]
    o.append(dtable(['Item', 'Value'], rows, widths=['30%', '70%'],
                    caption=f'BOM {esc(src_label(ctx, "BOM"))}. Price rule: every line TO-QUOTE delivered to Sønderborg DK-6400 unless dated; no zero and no "from" prices.'))
    o.append('<p class="small">Columns: part number (with its BOM-row trace), name and supplier as written in the BOM, quantity, material, process, unit mass with its evidence class, '
             'and price status. COTS = commercial part. Wetted oxygen-clean parts are marked O<sub>2</sub>.</p>')
    k = 0
    for fam in D['family_order']:
        rs = [r for r in D['bom'] if r.kind == 'lines' and r.fam == fam]
        if not rs:
            continue
        k += 1
        info = D['families'].get(fam)
        o.append(doc.h(2, f'5.{k} {fam} — {FAMILY_NAMES.get(fam, fam)}'))
        rows = []
        for r in rs:
            l = r.l
            nm = esc(clipw(l.get('name', ''), 110))
            sup = esc(clipw(l.get('supplier'), 80))
            o2 = ' <span class="o2">O<sub>2</sub></span>' if str(l.get('oxygen_clean')) == 'True' else ''
            lock = ' <span class="q">transport lock, not placed, excluded from mass</span>' if l.get('groups') == 'lock' else ''
            rows.append([
                Cell(f'<span class="pn">{esc(r.pn)}</span>{r.row_tv.ref()}', [r.row_tv]),
                Cell(f'{nm}{o2}{lock}<div class="sup">{sup}</div>', [r.row_tv]),
                Cell(esc(l.get('qty', '')), [r.row_tv]),
                Cell(esc(short_mat(l.get('material_name'), l.get('material'))) + ('<div class="sup">COTS</div>' if str(l.get('cots')) == 'True' else ''), [r.row_tv]),
                Cell('<span class="small">' + esc(clipw(l.get('process'), 70)) + '</span>', [r.row_tv]),
                Cell(r.mass_tv.h('.4f', unit=False), [r.mass_tv]),
                price_cell(r)])
        o.append(dtable(['PN', 'Part and supplier', 'Qty', 'Material', 'Process', 'Unit mass [kg]', 'Price'], rows, label_cols=0, cls='bom',
                        widths=['9%', '33%', '4%', '13%', '15%', '11%', '15%'],
                        caption=(f'{fam} family: {info["n_tv"].value} lines, {info["mass_tv"].value:.4f} kg (Σ qty × unit mass).' if info else None)))
    k += 1
    o.append(doc.h(2, f'5.{k} Standard hardware (fasteners, springs, bearings; BOM /hardware, CALC masses)'))
    rows = []
    for r in D['hw']:
        l = r.l
        nm = esc(clipw(l.get('name', ''), 120))
        notes = l.get('notes') or ''
        m = re.search(r'torque ([^;(]+)', notes)
        tq = esc(clipw(m.group(1).strip(), 40)) if m else ''
        rows.append([Cell(f'<span class="pn">{esc(r.pn)}</span>{r.row_tv.ref()}', [r.row_tv]),
                     Cell(f'{nm}<div class="sup">{esc(clipw(l.get("supplier_pn") or l.get("supplier"), 90))}</div>', [r.row_tv]),
                     Cell(esc(l.get('qty', '')), [r.row_tv]), Cell(esc(l.get('groups', '')), [r.row_tv]),
                     Cell(esc(short_mat(l.get('material_name'), l.get('material'))), [r.row_tv]),
                     Cell(f'<span class="small">{tq}</span>', [r.row_tv]),
                     Cell(r.mass_tv.h('.5f', unit=False), [r.mass_tv]), price_cell(r)])
    o.append(dtable(['PN', 'Item and standard', 'Qty', 'Group', 'Material', 'Torque (notes)', 'Unit mass [kg]', 'Price'], rows, label_cols=0, cls='bom',
                    widths=['9%', '34%', '4%', '7%', '13%', '10%', '9%', '14%'],
                    caption='Torque as written in the line notes (DESIGN; J-FWD: set per flight lot by J-F1, see M-T1J). Unit masses are CALC on standard nominal geometry, not datasheet.'))
    tm = ctx.raw('BOM', '/tightening_methods', default={}) or {}
    rows = [[Cell(f'<b>{esc(kk)}</b>', []), tvtxt(ctx.v('BOM', ptr_join('tightening_methods', kk), tag='DESIGN'), 900)] for kk in tm]
    rows.append([Cell('<b>Preload scatter rule</b>', []), tvtxt(ctx.v('BOM', '/preload_scatter_rule', tag='ASSUMED'), 600)])
    o.append(dtable(['Method', 'Tightening method (BOM)'], rows, widths=['16%', '84%'], cls='tight'))
    k += 1
    D['sec_gse'] = f'§5.{k}'
    o.append(doc.h(2, f'5.{k} Ground support tools, provisions and contingency (not flight mass)'))
    rows = []
    for r in D['gse'] + [x for x in D['bom'] if x.kind != 'lines']:
        l = r.l
        rows.append([Cell(f'<span class="pn">{esc(r.pn)}</span>{r.row_tv.ref()}', [r.row_tv]),
                     Cell(esc(clipw(l.get('name', ''), 140)) + f'<div class="sup">{esc(clipw(l.get("supplier"), 80))}</div>', [r.row_tv]),
                     Cell(esc(l.get('qty', '')), [r.row_tv]), Cell(esc(l.get('groups', '')), [r.row_tv]),
                     Cell(r.mass_tv.h('.4f', unit=False), [r.mass_tv]), price_cell(r)])
    pm = ctx.v('BOM', '/provision_mass_estimate_kg/estimate_range_kg', 'kg', tag='ASSUMED', tag_ptr='/provision_mass_estimate_kg/note')
    o.append(dtable(['PN', 'Item', 'Qty', 'Status', 'Unit mass [kg]', 'Price'], rows, label_cols=0, cls='bom', widths=['10%', '44%', '5%', '15%', '11%', '15%']))
    o.append(note_box(f'Bleed provision mass estimate (excluding the valves): {pm.h(".3f")}. Valve mass: {tvtxt(ctx.v("BOM", "/provision_mass_estimate_kg/valves", tag="TO-VERIFY")).html}', 'info'))
    return '\n'.join(o)


def sec_materials(ctx, doc, a, D):
    o = [doc.h(1, '6 Materials and thermal protection')]
    o.append(doc.h(2, '6.1 Materials'))
    rows = []
    for mname, info in sorted(D['mat_usage'].items(), key=lambda kv: -kv[1]['mass_tv'].value):
        rows.append([esc(mname), Cell(info['n_tv'].h(), [info['n_tv']]), num_cell(info['mass_tv'], '.4f'), Cell(info['o2_tv'].h(), [info['o2_tv']])])
    o.append(dtable(['Material (BOM material_name)', 'Lines', 'Mass', 'Oxygen-clean lines'], rows, widths=['52%', '12%', '20%', '16%'],
                    caption='Material usage over the BOM part lines (DERIVED by this generator; transport lock and standard hardware excluded).'))
    o.append(doc.h(2, '6.2 Short-time exposure of the 6061-T6 case and head (T-F1)'))
    tf = ctx.v('TXT5', '/T-F1', tag='CALC')
    av = ctx.v('TXT5', '/T-F1_exposure_basis_R9/abort_value', tag='LEAD')
    al = ctx.raw('TXT5', '/T-F1_engmat_10000h_values_used_by_the_cells', default={}) or {}
    rows = [['T-F1 founder action (text v5)', cat(tvtxt(tf, 1400), gnote('continues; printed in full in §12.3 with routes (i) and (ii), the coupon test and its pass rules', []))],
            ['Criteria status', tf1_status_cell(ctx, D)], ['Abort value', tvtxt(av)]]
    for T in al:
        rows.append([f'6061-T6 allowables at {esc(T)} C (10 000 h basis): Fty / Ftu',
                     cat(ctx.v('TXT5', ptr_join('T-F1_engmat_10000h_values_used_by_the_cells', T, 'Fty_MPa'), 'MPa', tag='LITERATURE').h('.1f'), ' / ',
                         ctx.v('TXT5', ptr_join('T-F1_engmat_10000h_values_used_by_the_cells', T, 'Ftu_MPa'), 'MPa', tag='LITERATURE').h('.1f'))])
    o.append(dtable(['Item', 'Value'], rows, widths=['36%', '64%'], cls='tight',
                    caption='04-fea/v352/texts/item_c_tf1_texts_v352_v5.json. The 10 000 h values are conservative for a short exposure; (d) stays OPEN until a sourced short-time allowable exists.'))
    o.append(doc.h(2, '6.3 Thermal protection and thermal loads'))
    T = '/thermal_and_loads'
    pf = ctx.v('CMB', f'{T}/peak_convective_heat_flux_W_m2', 'MW/m²', conv=(1e-6, 0, 'W/m² to MW/m²'))
    hg = ctx.v('CMB', f'{T}/peak_h_g_W_m2K', 'W/(m²·K)')
    taw = ctx.v('CMB', f'{T}/T_aw_throat_K', 'K')
    pfi = ctx.v('CMB', f'{T}/peak_incident_flux_cold_wall_transient_W_m2', 'MW/m²', conv=(1e-6, 0, 'W/m² to MW/m²'))
    ci = D['cause_idx'].get('OVER_TEMP', 0)
    cot = ctx.v('ELE', f'/abort_matrix/causes/{ci}/thresholds/kCaseOverTemp_K', 'K')
    crl = ctx.v('ELE', f'/abort_matrix/causes/{ci}/thresholds/kCaseRelightMax_K', 'K')
    nht = ctx.v('ELE', f'/abort_matrix/causes/{ci}/thresholds/kNozzleHolderOverTemp_K', 'K')
    rows = [
        ['Grain-zone liner thickness', num_cell(ctx.v('CMB', '/gas_path/liner_grain_zone/thickness_m', 'mm', conv=(1000, 0, 'm to mm')), '.1f')],
        ['Post-chamber insulator', tvtxt(ctx.v('CMB', '/gas_path/post_chamber_insulator'), 300)],
        ['Peak convective heat flux at the throat (Bartz, 600 K wall)', num_cell(pf, '.2f')],
        ['Peak gas-side heat-transfer coefficient', num_cell(hg, '.0f')],
        ['Adiabatic wall temperature at the throat', Cell(temp_k(taw, 0), [taw])],
        ['Incident flux on a cold wall at start (nominal–conservative)', num_cell(pfi, '.2f')],
        ['Throat insert replacement rule', tvtxt(ctx.v('CMB', f'{T}/throat_replacement_rule'))],
        ['Throat insert acceptance (NZ-01 criterion)', tvtxt(ctx.v('CMB', '/nz01_criterion_v2p4b/v/criterion', tag_ptr='/nz01_criterion_v2p4b'), 500)],
        ['Nozzle gasket NZ-03 finding / joint J1', cat(tvtxt(ctx.v('CMB', '/nozzle_joint/v/NZ03_gasket', tag_ptr='/nozzle_joint')), '<br>',
                                                     tvtxt(ctx.v('CMB', '/nozzle_joint/v/proposal_J1', tag_ptr='/nozzle_joint')))],
        [f'Case-TC abort A / start and relight limit / nozzle-holder limit (firmware {fw_ver(D)})', cat(temp_k(cot, 2), ' / ', temp_k(crl, 2), ' / ', temp_k(nht, 2), Cell('', [cot, crl, nht]))],
        ['Case-TC decisions (CHANGELOG 257)', tvtxt(D['cl'].part(257, ['423.15', '403.15']), 600)],
    ]
    o.append(dtable(['Item', 'Value'], rows, widths=['36%', '64%']))
    o.append('<p class="small">Thermal margins of the parts: 3D FEA thermal and thermo-mechanical cases, §9 (margin matrix columns LC3, TD, LC6, TB70, TBS).</p>')
    return '\n'.join(o)


def glb_absent(ctx, D):
    """Statement of the BOM parts that are not in the GLB display mesh, so in no render (lead 2026-10-21 12:13Z item 12):
    render metadata /pns of the isometric view against BOM /lines and BOM /hardware/lines (computed, not typed)."""
    if 'gabs' in D:
        return D['gabs']
    R = D['R'].get('iso')
    if not R:
        D['gabs'] = ctx.missing('render metadata of the isometric view (part list)')
        return D['gabs']
    pns_tv = ctx.v(R['sid'], '/pns', tag='DERIVED', note='part numbers of the GLB objects in the render (render script, from the GLB)')
    pns = set(pns_tv.value or [])
    ml = [r for r in D['bom'] if r.kind == 'lines' and r.pn not in pns]
    mh = [r for r in D['hw'] if r.pn not in pns]
    hwd = ctx.raw('HWD', '/lines', default=[]) or []
    parts = []
    if mh:
        named = [r.pn for r in mh if r.pn in ('ENG-HW-101', 'ENG-HW-170')]
        parts.append(f'all {len(mh)} of the {len(D["hw"])} standard-hardware lines of BOM /hardware ({mh[0].pn} to {mh[-1].pn}; hardware_v352 lists '
                     f'{len(hwd)} lines), so no screw, spring, pin or insert' + (f', among them {" and ".join(named)} (the J-FWD radial screw and the disc spring under its head)' if named else ''))
    for r in ml:
        parts.append(f'{r.pn} ({r.l.get("name") or ""})')
    txt = ('Not in the GLB display mesh, so shown in no render: ' + '; '.join(parts) + '.') if parts else 'Every BOM line is in the GLB display mesh.'
    D['gabs'] = ctx.d(txt, '', 'BOM /lines and BOM /hardware/lines whose part number is not among the render metadata /pns (isometric view)',
                      [pns_tv] + [r.row_tv for r in ml] + [r.row_tv for r in mh])
    return D['gabs']


def bay_cells(ctx, D):
    """Bay bore (REQUIREMENTS.md §1), thrust-ring size from the CAD bounds, the gimbal range and stop (ENG-07), the
    max thrust (ENG-01) and the lateral thrust at the range: current sources for the airframe-facing rows (lead 12:13Z item 3)."""
    if 'bay' in D:
        return D['bay']
    import math
    B = {}
    B['req'] = md_row(ctx, 'REQ', '1. Mission', 'Engine-bay inner diameter', 1, tag_col=2)
    bore = rx_text(ctx, B['req'], r'≥\s*([\d.]+)\s*mm', 'mm')
    ods = []
    for pfx in ('ENG-GM-09', 'ENG-GM-10'):
        lo, hi, n = manifest_extent(ctx, pn_prefix=pfx)
        if n:
            ods.append(max(hi[0] - lo[0], hi[1] - lo[1]))
    od = max(ods) if ods else None
    B['ring_od'] = man_tv(ctx, od, 'largest x or y extent of the thrust rings', pn_prefix='ENG-GM-09 / ENG-GM-10')
    B['gap'] = ctx.d((bore.value - od) / 2 if (bore.value is not None and od is not None) else None, 'mm',
                     '(bay inner diameter − thrust-ring outer diameter) / 2', [bore, B['ring_od']])
    out, refs = [], [B['ring_od']]
    if od is not None:
        for it in ctx.raw('MAN', '/instances', default=[]) or []:
            b = it['bounds_mm']
            rr = max(abs(b[0]), abs(b[1]), abs(b[3]), abs(b[4]))
            pn = it['inst'].split('#')[0]
            if rr > od / 2 + 1e-6 and pn not in ('ENG-GM-09', 'ENG-GM-10'):
                br = D['bom_by_pn'].get(pn)
                if br is not None:
                    refs.append(br.row_tv)
                nm = (br.l.get('name') if br else '') or ''
                if len(nm) > 200:  # never cut a name silently (rev1 phase 2: the 110-character cut dropped 'ICD-14)')
                    nm = nm[:nm.rfind(' ', 0, 199)] + ' …'
                out.append(f'{it["inst"]}: {rr:.2f} mm from the axis ({nm})')
    B['beyond'] = ctx.d('; '.join(out) if out else 'none', '', 'instances whose bounding box reaches beyond the thrust-ring radius (largest |x| or |y| of the bounds)', refs)
    e07 = md_row(ctx, 'REQ', '2. Top-level', 'ENG-07', 1, tag_col=2)
    B['rng'] = rx_text(ctx, e07, r'Range ±(\d+)°', '°', tag='REQ')
    B['stop'] = rx_text(ctx, e07, r'(\d+)° conical mechanical stop', '°', tag='REQ')
    e01 = md_row(ctx, 'REQ', '2. Top-level', 'ENG-01', 1, tag_col=2)
    B['fmax'] = rx_text(ctx, e01, r'Max thrust (\d+) N', 'N', tag='REQ')
    f, r_ = B['fmax'].value, B['rng'].value
    B['flat'] = ctx.d(f * math.sin(math.radians(r_)) if (f is not None and r_ is not None) else None, 'N', 'max thrust × sin(gimbal range)', [B['fmax'], B['rng']])
    D['bay'] = B
    return B


def gnc_mass_cells(ctx, D):
    """GNC vehicle basis (massprops v3.5.1, DATASHEET-INPUTS-GNC row 4) and the CAD v3.5.2 landing-mass change against GNC's re-fly
    trigger (03-cad/v3.5.2/massdelta /gnc_trigger; lead 12:13Z item 6). gnc.json /reference_vehicle/liftoff_mass_kg is not used."""
    if 'gncm' in D:
        return D['gncm']
    G = {}
    G['row4'] = md_find(ctx, 'DSIG', None, {0: '4'}, 4, tag_col=3)
    G['lift'] = rx_text(ctx, G['row4'], r'liftoff mass ([\d.]+) kg', 'kg', note='GNC basis: massprops v3.5.1 (row 4 basis text)')
    G['tw'] = rx_text(ctx, md_find(ctx, 'DSIG', None, {0: '4'}, 2, tag_col=3), r'([\d.]+)', '')
    T = '/gnc_trigger'
    G['dl'] = ctx.v('MDEL', f'{T}/dm_landing_kg', 'kg', tag_ptr=f'{T}/evidence')
    G['dl0'] = ctx.v('MDEL', f'{T}/dm_landing_without_TC09_thinning_kg', 'kg', tag_ptr=f'{T}/evidence')
    G['thin'] = ctx.v('MDEL', f'{T}/TC09_thinning_kg', 'kg', tag_ptr=f'{T}/evidence')
    G['trig'] = rx(ctx, 'MDEL', f'{T}/rule', r'>= ([\d.]+) kg', 'kg', tag='LEAD', note="GNC's re-fly trigger as written in the rule (lead / GNC trigger)")
    G['verdict'] = ctx.v('MDEL', f'{T}/verdict', tag_ptr=f'{T}/evidence')
    G['evid'] = ctx.v('MDEL', f'{T}/evidence', tag_ptr=f'{T}/evidence')
    D['gncm'] = G
    return G


def bom_name_cell(r, maxlen=200):
    """BOM line name in full (row trace of the line)."""
    nm = (r.l.get('name') or '')
    nm = nm if len(nm) <= maxlen else nm[:maxlen].rsplit(' ', 1)[0] + ' …'
    return Cell(f'<span class="qt">{esc(r.pn)}: {esc(nm)}</span> {r.row_tv.pill()}{r.row_tv.ref()}', [r.row_tv])

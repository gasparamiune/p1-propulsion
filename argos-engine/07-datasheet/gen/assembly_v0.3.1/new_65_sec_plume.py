# ---------------------------------------------------------------------------------------------
# section 8 (v0.3.0): plume CFD. Every table and figure names its operating point (the v1 point,
# O/F 7.76) and how it relates to the current max-thrust point (lead 12:13Z item 5); currency of
# RPL v2.2b and PVAL v2.1a checked against the 05-plume-cfd folder (item 11)
# ---------------------------------------------------------------------------------------------
def plume_points(ctx, a, D):
    """Operating points of the plume package and the current max-thrust point (computed once)."""
    if 'plume_pts' in D:
        return D['plume_pts']
    b1 = md_bullet(ctx, 'RPL', '0. Checkpoint', 'v1 (combustion.json v1)', 'SIM')
    b2 = md_bullet(ctx, 'RPL', '0. Checkpoint', 'v2 (combustion.json v2.1 S230 point)', 'SIM')
    of1 = rx_text(ctx, b1, r'O/F ([\d.]+)')
    pc1 = rx_text(ctx, b1, r'Pc ([\d.]+) bar', 'bar')
    of2 = ctx.v('PVAL', '/v2op/gas/OF', tag='SIM', note='validation_v2.json carries no tags: the v2-point inputs of the CFD run')
    p02 = ctx.v('PVAL', '/v2op/gas/p0', 'bar', conv=(1e-5, 0, 'Pa to bar'), tag='SIM')
    B = '/operating_points'
    F = ctx.v('CMB', f'{B}/max_thrust/F_N', 'N')
    pc = ctx.v('CMB', f'{B}/max_thrust/Pc_Pa', 'bar', conv=(1e-5, 0, 'Pa to bar'))
    of = ctx.v('CMB', f'{B}/throttle_points_20C_initial_port/0/OF', tag_ptr=f'{B}/basis')
    t0 = ctx.v('CMB', f'{B}/throttle_points_20C_initial_port/0/T0_delivered_K', 'K', tag_ptr=f'{B}/basis')
    V = '/v2op_vs_v1'
    dF = ctx.v('PVAL', f'{V}/thrust_exit_N/diff_pct', '%', tag='SIM')
    dx = ctx.v('PVAL', f'{V}/x_mach_disk_De/diff_pct', '%', tag='SIM')
    dm = ctx.v('PVAL', f'{V}/mdot_throat_kg_s/diff_pct', '%', tag='SIM')
    dT = ctx.v('PVAL', f'{V}/T_axis_10De_K/diff_pct', '%', tag='SIM')
    same = None
    if None not in (of.value, of2.value, pc.value, p02.value):
        same = abs(of.value - of2.value) < 1e-6 and abs(pc.value - p02.value) < 1e-6
    ver = ctx.src('CMB').version or ''
    if same is None:
        rel = ctx.missing('relation of the plume points to the current max-thrust point (an input is MISSING)')
    else:
        txt = (f'The current max-thrust point (combustion.json {ver}: {F.num(".0f")} N, Pc {pc.num(".2f")} bar, O/F {of.num(".3f")}) '
               + ('is the plume v2 point (same Pc and O/F; coarse grid only). ' if same else
                  f'is not a plume point (the plume v2 point is Pc {p02.num(".2f")} bar, O/F {of2.num(".3f")}). ')
               + f'The fine-grid results and the field figures of §8.1-8.2 are at the v1 point (O/F {of1.num(".2f")}, Pc {pc1.num(".2f")} bar). '
               f'On the coarse grid the v2 point differs from the v1 point by {dF.num("+.3f")} % in thrust, {dx.num("+.2f")} % in the Mach disk '
               f'position, {dm.num("+.2f")} % in mass flow and {dT.num("+.1f")} % in the axis temperature at 10 De (validation_v2.json /v2op_vs_v1).')
        rel = ctx.d(txt, '', 'statement built from the traced operating points and the v2-vs-v1 coarse-grid differences',
                    [b1, of1, pc1, of2, p02, F, pc, of, dF, dx, dm, dT])
    tag_ = f'v1 point, O/F {of1.num(".2f")} (current max-thrust point O/F {of.num(".3f")}: Table 8.0)'
    D['plume_pts'] = {'b1': b1, 'b2': b2, 'of1': of1, 'pc1': pc1, 'of2': of2, 'p02': p02, 'F': F, 'pc': pc, 'of': of, 't0': t0,
                      'rel': rel, 'same': same, 'tag': tag_}
    return D['plume_pts']


def plume_currency(ctx, a):
    """Generator check: RPL and PVAL against the newest files of 05-plume-cfd (no newer report or result)."""
    root = os.path.join(a.hub, '05-plume-cfd')
    newest, newest_f = None, None
    for dp, dn, fn in os.walk(root):
        for f in fn:
            p = os.path.join(dp, f)
            try:
                t = os.path.getmtime(p)
            except OSError:
                continue
            if newest is None or t > newest:
                newest, newest_f = t, p
    rpl, pval = ctx.src('RPL'), ctx.src('PVAL')
    alt = os.path.join(root, 'REPORT_v2p2b.txt')
    same_txt = os.path.exists(alt) and sha16_file(alt) == rpl.sha16
    stamp = datetime.datetime.fromtimestamp(newest, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%MZ') if newest else 'MISSING'
    txt = (f'RPL (05-plume-cfd/REPORT.md, text revision {rpl.version}, {rpl.sha16}) and PVAL (validation_v2.json {pval.version}, {pval.sha16}) '
           f'are the current plume files: the newest file in 05-plume-cfd/ is {os.path.relpath(newest_f, a.hub) if newest_f else "MISSING"} '
           f'({stamp}); REPORT.md {"equals" if same_txt else "differs from"} REPORT_v2p2b.txt.')
    return ctx.d(txt, '', 'generator check on this build: newest modification time under 05-plume-cfd/ and the REPORT.md / REPORT_v2p2b.txt sha', [])


def sec_plume(ctx, doc, a, D):
    o = [doc.h(1, '8 Plume CFD')]
    P = 'PVAL'
    De = ctx.v('CMB', '/gas_path/nozzle/exit_diameter_m', 'm')
    stl = md_line(ctx, 'RPL', 'Version ', 'SIM')
    o.append(note_box('<b>Simulation, not measurement.</b> ' + tvtxt(stl, 700).html, 'info'))
    pp = plume_points(ctx, a, D)
    o.append(doc.h(2, '8.0 Operating points'))
    rows = [['Plume v1 point: every grid level, sensitivity and OpenFOAM run', tvtxt(pp['b1'], 300)],
            ['Plume v2 point: coarse grid only', tvtxt(pp['b2'], 300)],
            ['Current max-thrust point (combustion.json): thrust / Pc / O/F / delivered T0',
             cat(pp['F'].h('.0f'), ' / ', pp['pc'].h('.2f'), ' / ', pp['of'].h('.3f'), ' / ', pp['t0'].h('.0f'))],
            ['Relation of the plume points to the current max-thrust point', tvtxt(pp['rel'], 900)],
            ['Currency of the plume report and results', tvtxt(plume_currency(ctx, a), 600)]]
    o.append(dtable(['Item', 'Value'], rows, widths=['34%', '66%'],
                    caption='Table 8.0: operating points of the plume CFD (RPL §0) and the current max-thrust point (combustion.json /operating_points). '
                            'Every table and figure of this section names its point.'))

    def mm(tv):
        return ctx.d(tv.value * De.value * 1000 if (tv.value is not None and De.value) else None, 'mm',
                     'x/De × De (exit diameter from combustion.json, tagged v1 geometry)', [tv, De])

    S = lambda ptr, unit='', tag='SIM': ctx.v(P, ptr, unit, tag=tag, note='validation_v2.json carries no tags: CFD outputs SIM, 1-D and correlation values DERIVED')
    o.append(doc.h(2, f'8.1 Key results at the v1 point (O/F {pp["of1"].num(".2f")})'))
    xmd, xlc = S('/correlations/own_f_2s_rans/x_md_cfd', 'De'), S('/correlations/own_f_2s_rans/x_md_lewis_carlson', 'De', 'DERIVED')
    sp1, sp3, ppt = S('/correlations/own_f_2s_rans/spacing_first_mach', 'De'), S('/correlations/own_f_2s_rans/spacing_mean3_mach', 'De'), \
        S('/correlations/own_f_2s_rans/spacing_pp_tam', 'De', 'DERIVED')
    core = S('/gci/core_length_Z095_De/fine', 'De')
    t10, t20 = S('/gci/T_axis_10De_K/fine', 'K'), S('/gci/T_axis_20De_K/fine', 'K')
    fcfd, f1d, fdev = S('/thrust_vs_1d/own_f_2s_rans/F_cfd', 'N'), S('/one_d/F_ideal_lambda_N', 'N', 'DERIVED'), S('/thrust_vs_1d/own_f_2s_rans/dev_vs_ideal_lambda_pct', '%')
    mcfd, m1d, mdev = S('/thrust_vs_1d/own_f_2s_rans/mdot_cfd', 'kg/s'), S('/one_d/mdot', 'kg/s', 'DERIVED'), S('/thrust_vs_1d/own_f_2s_rans/mdot_dev_pct', '%')
    rows = [
        ['Exit Mach number / pe/pa / fully expanded Mach number (1-D)', cat(S('/one_d/Me', '', 'DERIVED').h('.3f'), ' / ', S('/one_d/pe_over_pa', '', 'DERIVED').h('.3f'), ' / ',
                                                                              S('/one_d/Mj', '', 'DERIVED').h('.3f'))],
        ['Mach disk position, fine grid (in mm) and Lewis–Carlson correlation', cat(xmd.h('.3f'), ' (', mm(xmd).h('.1f'), ') — correlation ', xlc.h('.3f'))],
        ['Mach disk resolvability', tvtxt(S('/gci_resolvability/x_mach_disk_De/verdict'), 240)],
        ['Shock-cell spacing, first / mean of three (in mm)', cat(sp1.h('.2f'), ' (', mm(sp1).h('.1f'), ') / ', sp3.h('.2f'), ' (', mm(sp3).h('.1f'), ')')],
        ['Shock-cell spacing, Prandtl–Pack–Tam correlation', num_cell(ppt, '.2f')],
        ['Shock-cell spacing grid sensitivity', cat(S('/gci/spacing_mean_3_De/gci_fine_pct', '%').h('.2f'), ' — ', tvtxt(S('/gci/spacing_mean_3_De/note')))],
        ['Peak Mach number before the disk', num_cell(S('/gci/M_max_before_disk/fine'), '.2f')],
        ['Potential core length, axis Z ≥ 0.95 (in mm)', cat(core.h('.1f'), ' (', mm(core).h('.0f'), ')')],
        ['Axis temperature at 10 De / 20 De (frozen, no afterburning)', cat(Cell(temp_k(t10, 0), [t10]), ' / ', Cell(temp_k(t20, 0), [t20]))],
        ['Thrust, exit integral (fine) vs 1-D with divergence factor; deviation', cat(fcfd.h('.1f'), ' vs ', f1d.h('.1f'), '; ', fdev.h('.2f'))],
        ['Thrust grid sensitivity', cat(S('/gci/thrust_exit_N/gci_fine_pct', '%').h('.2f'), ' — ', tvtxt(S('/gci/thrust_exit_N/note')))],
        ['Mass flow, CFD vs 1-D; deviation', cat(mcfd.h('.4f'), ' vs ', m1d.h('.4f'), '; ', mdev.h('.2f'))],
        ['Starting-jet front at the end of the run', num_cell(S('/jet_front_x_De/own_f_2s_rans', 'De'), '.1f')],
        ['v2 point (= the current max-thrust point when Table 8.0 says so), coarse grid: Mach disk CFD / correlation; thrust deviation',
         cat(S('/v2op/x_md_cfd', 'De').h('.3f'), ' / ', S('/v2op/x_md_lewis_carlson', 'De', 'DERIVED').h('.3f'), '; ', S('/v2op/thrust_dev_vs_ideal_lambda_pct', '%').h('.2f'))],
        ['v2 point remark', tvtxt(S('/v2op/note'), 320)],
    ]
    o.append(dtable(['Quantity', 'Value'], rows, widths=['38%', '62%'],
                    caption=f'Plume CFD results ({esc(src_label(ctx, "PVAL"))}), fine grid at the {esc(pp["tag"])} unless a row says otherwise; '
                            'lengths in exit diameters De.'))
    o.append(doc.h(2, '8.2 Fields'))
    pt = f'{esc(pp["tag"])}'
    o.append(img_fig(ctx, a, 'PF-MACH', f'<b>Mach number, near field</b> (SIM, fine grid, {pt}).', 'wide'))
    o.append(img_fig(ctx, a, 'PF-SCHL', f'<b>Numerical schlieren</b> |∇ρ| (SIM, fine grid, {pt}): Mach disk, reflected shocks and the shock-cell train.', 'wide'))
    o.append(img_fig(ctx, a, 'PF-TEMP', f'<b>Static temperature, full domain</b> (SIM, fine grid, {pt}; frozen chemistry, no afterburning). The far field is not statistically stationary.', 'wide'))
    o.append(img_fig(ctx, a, 'PF-AXIS', f'<b>Centreline profiles</b> (SIM, fine grid, {pt}).', 'half'))
    o.append(img_fig(ctx, a, 'PF-V2MACH', f'<b>Mach number at the v2 point</b> (SIM, coarse grid; O/F {esc(pp["of2"].num(".3f"))}, '
                                          + ('the current max-thrust point' if pp['same'] else 'not the current max-thrust point') +
                     ', Table 8.0). v2-v1 differences carry the grid error of the coarse level.', 'wide'))
    o.append(doc.h(2, '8.3 Afterburning and model limits'))
    rows = [[f'Afterburning at the v1 point (O/F {esc(pp["of1"].num(".2f"))})', tvtxt(md_bullet(ctx, 'RPL', '0. Checkpoint', 'adds 172', 'SIM'), 400)],
            [f'Afterburning at the v2 point (O/F {esc(pp["of2"].num(".3f"))}; the current max-thrust point when Table 8.0 says so)',
             tvtxt(md_bullet(ctx, 'RPL', '0. Checkpoint', 'adds nothing', 'SIM'), 400)],
            ['Afterburning at the stretch floor (12.5 %)', tvtxt(md_bullet(ctx, 'RPL', '0. Checkpoint', 'adds up to', 'SIM'), 300)]]
    for k in ('**Soot and radiation', '**Finite-rate chemistry', '**Exhaust gas model', '**Geometry and setting', '**Duration', '**No acoustics'):
        rows.append(['Limit: ' + k.strip('*'), tvtxt(md_bullet(ctx, 'RPL', '10. What the model cannot show', k, 'SIM'), 360)])
    o.append(dtable(['Item', 'Report statement'], rows, widths=['24%', '76%'],
                    caption='Afterburning by operating point (RPL §0) and the model limits (RPL §10); operating points in Table 8.0.'))
    o.append(doc.h(2, '8.4 Illustration'))
    o.append(img_fig(ctx, a, 'PF-ART', '<b>Illustration, not simulation.</b> Blender render of revolved CFD fields with exposure, colour and emitter chosen '
                     'for appearance (ARTISTIC); it is not a radiation prediction, carries no data and is not tied to an operating point for any value.', 'wide art'))
    o.append(doc.h(2, '8.5 Review status'))
    sup_ = ctx.raw('SUP', '/reviews', default=[]) or []
    ids = [k for k, r in enumerate(sup_) if str(r.get('id', '')).startswith('REV-PLUME')]
    if ids:
        rows = []
        for i in ids:
            hs = ctx.raw('SUP', f'/reviews/{i}/hashes_sha256_16', default={}) or {}
            same, changed, missing = hash_status(ctx, a, hs)
            hst = ctx.d(f'{len(same)} unchanged, {len(changed)} changed since review ({", ".join(changed) or "none"}), {len(missing)} not found', '',
                        'sha256/16 of each reviewed hub file vs the register', [], ev='DERIVED')
            rid = ctx.v('SUP', f'/reviews/{i}/id', tag='REF')
            key = 'comments' if sup_[i].get('comments') else 'criteria'
            rows.append([Cell(f'<b>{esc(rid.value)}</b> {rid.ref()}', [rid]), num_cell(ctx.v('SUP', f'/reviews/{i}/verdict', tag='DERIVED')),
                         tvtxt(ctx.v('SUP', f'/reviews/{i}/{key}', tag='DERIVED'), 300), Cell(hst.h(), [hst])])
        o.append(dtable(['Review', 'Verdict', 'Comments (or criteria)', 'Reviewed file hashes vs current files'], rows, label_cols=0,
                        widths=['13%', '17%', '42%', '28%'],
                        caption='Independent reviews of the plume CFD in register order, newest last (reviews/SUPERVISION.json). A review verdict is not physical approval.'))
        o.append(dtable(['Item', 'Value'], [['Report text revision answering the comments', tvtxt(stl, 400)]], widths=['30%', '70%']))
    else:
        o.append(Cell(ctx.missing('REV-PLUME entry in the review register').h()).html)
    return '\n'.join(o)

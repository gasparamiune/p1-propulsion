# ---------------------------------------------------------------------------------------------
# section 15 and appendix A (v0.3.0): sources with hub-relative paths only (lead 12:13Z items 2, 9);
# the value trace shows the class, and for a DECIDED value its source class and basis (lead 12:17Z)
# ---------------------------------------------------------------------------------------------
def sec_revision_sources(ctx, doc, a, D):
    o = [doc.h(1, '15 Revision history and sources')]
    o.append(doc.h(2, '15.1 Revision history'))
    hist = D.get('history', [])
    o.append(table(['Revision', 'Generated (UTC)', 'CAD', 'Generator', 'Note'],
                   [[esc(h['rev']), esc(h['generated']), esc(h['cad_version']), esc(h['generator']), esc(h.get('note', ''))] for h in hist],
                   cls='dt', widths=['14%', '20%', '10%', '16%', '40%']))
    o.append(doc.h(2, '15.2 Sources'))
    rows = []
    for sid, s in ctx.sources.items():
        rel = hub_rel(a, s.path)
        if rel is None:
            ctx.issue('ERROR', f'source {sid} is outside the hub; it may not be printed or used')
            rel = '(outside the hub: not used)'
        rows.append([f'<b>{esc(sid)}</b>', esc(s.role), f'<span class="mono">{esc(rel)}</span>', esc(s.version or '—'),
                     f'<span class="mono">{esc(s.sha16 or "MISSING")}</span>', esc(s.mtime or '—'), str(s.reads)])
    o.append(table(['ID', 'Role', 'Path (hub-relative)', 'Version', 'sha256/16', 'Modified (UTC)', 'Reads'], rows, cls='dt src',
                   widths=['7%', '24%', '30%', '9%', '13%', '13%', '4%']))
    o.append('<p class="small">Paths are relative to the engine programme hub (argos-engine). The same list is written to out/rev1/sources.json. '
             '"Reads" counts JSON key reads; text sources are read by line, row or sentence (Appendix A).</p>')
    return '\n'.join(o)


def fmt_full(v, computed=False):
    """Appendix A number: a value read from a source at the precision the source gives (shortest round-trip form), a value the
    generator computes (formula) to 6 significant digits. The body may show the same value rounded (rev1 phase 2)."""
    if isinstance(v, bool):
        return 'yes' if v else 'no'
    if isinstance(v, int):
        s = str(v)
    elif computed:
        s = f'{v:.6g}'
    else:
        s = repr(float(v))
        if s.endswith('.0'):
            s = s[:-2]
    return s.replace('-', '−', 1) if s.startswith('-') else s


def trace_val_full(tv):
    v = tv.value
    if v is None:
        return tv.status or 'MISSING'
    comp = bool(tv.formula)
    if isinstance(v, (int, float)):
        s = fmt_full(v, comp)
    elif isinstance(v, (list, tuple)) and all(isinstance(x, (int, float)) for x in v):
        s = ('–' if len(v) == 2 else ', ').join(fmt_full(x, comp) for x in v)
    else:
        return str(v)
    return s + (f' {tv.unit}' if tv.unit else '')


def sec_trace(ctx, doc, a, D):
    o = [doc.h(1, 'Appendix A Value trace')]
    o.append('<p class="small">Every traced value used in this document: trace id, value (a value read from a source at the precision of '
             'that source; a value the generator computes, to 6 significant digits; the body may show it rounded), class, source and version, '
             'key (JSON pointer, markdown row, CHANGELOG line and item, or generator formula) and the source tag text. A DECIDED value also shows '
             'its source class (design value, lead decision or requirement). Identical source keys share one id. '
             'Display rules of the body and of this appendix (trace.json keeps the source strings): the review status written in Spanish in the FEA3D-2 report prints as '
             '"to be reviewed" (REV-DS-1 D1-12); a bare "§n" in a combustion.json text prints as "combustion REPORT §n" (D1-11); a number read from a '
             'source prints at the precision of that source, and a number read from a text keeps the digits of the text (D1-08).</p>')
    rows = []
    for tv in ctx.traces:
        s = ctx.sources.get(tv.sid)
        src = f'{tv.sid} {s.version or ""}'.strip() if s else (tv.sid or '—')
        if isinstance(tv.value, str):
            val = clipw(display_text(tv, tv.value), 90)  # display rules and a word-boundary cut with a visible ' …'; trace.json keeps the full string
        elif isinstance(tv.value, dict) or (isinstance(tv.value, list) and not all(isinstance(x, (int, float)) for x in tv.value)):
            val = clipw(display_text(tv, readable(tv.value)), 90)
        else:
            val = trace_val_full(tv)
        if ctx.ovr:
            val = ctx.ovr.annot_plain(val)
        key = tv.ptr or (f'formula: {tv.formula}' if tv.formula else '')
        extra = tv.tag_raw or ''
        if getattr(tv, 'basis_detail', None) and tv.ev == 'DECIDED' and tv.basis_detail not in extra:
            extra = tv.basis_detail
        if tv.inputs:
            extra += ' ← ' + ', '.join(tv.inputs[:8]) + (' …' if len(tv.inputs) > 8 else '')
        if tv.note and tv.note not in extra:
            extra += f' [{tv.note}]'
        pill = ev_pill(tv.ev, None, getattr(tv, 'basis', None), tv.status if tv.value is not None else None)
        rows.append(f'<tr id="{tv.tid}"><td class="mono">{tv.tid}</td><td>{esc(val)}</td><td>{pill}</td><td>{esc(src)}</td>'
                    f'<td class="mono">{esc(clipw(key, 160))}</td><td>{esc(clipw(extra, 200))}</td></tr>')  # word-boundary cuts with a visible ' …'
    o.append('<table class="dt trace"><colgroup><col style="width:6%"><col style="width:20%"><col style="width:11%"><col style="width:10%">'
             '<col style="width:25%"><col style="width:28%"></colgroup><thead><tr><th>ID</th><th>Value</th><th>Class</th><th>Source</th><th>Key</th>'
             '<th>Source tag / formula</th></tr></thead><tbody>' + '\n'.join(rows) + '</tbody></table>')
    return '\n'.join(o)

# ---------------------------------------------------------------------------------------------
# main (v0.3.0)
# ---------------------------------------------------------------------------------------------
def trace_key(t):
    return f'{t.get("source")}|{t.get("key")}|{t.get("formula") or ""}'


def diff_traces(prev_path, cur):
    """Values that changed between a previous trace.json and this build, matched by source and key."""
    old = json.load(open(prev_path))
    om = {}
    for t in old.get('traces', []):
        om.setdefault(trace_key(t), []).append(t)
    cm = {}
    for t in cur:
        cm.setdefault(trace_key(t), []).append(t)
    changed, added, removed = [], [], []
    for k, ts in cm.items():
        if k not in om:
            added.append({'key': k, 'id': ts[0]['id'], 'value': ts[0]['value'], 'class': ts[0]['class']})
            continue
        ov = [json.dumps(x['value'], sort_keys=True, default=str) + '|' + str(x['class']) for x in om[k]]
        nv = [json.dumps(x['value'], sort_keys=True, default=str) + '|' + str(x['class']) for x in ts]
        if sorted(ov) != sorted(nv):
            changed.append({'key': k, 'id': ts[0]['id'], 'old': [x['value'] for x in om[k]], 'old_class': [x['class'] for x in om[k]],
                            'new': [x['value'] for x in ts], 'new_class': [x['class'] for x in ts]})
    for k, ts in om.items():
        if k not in cm:
            removed.append({'key': k, 'id': ts[0]['id'], 'value': ts[0]['value'], 'class': ts[0]['class']})
    return {'against': prev_path, 'against_revision': old.get('revision'), 'n_changed': len(changed), 'n_added': len(added),
            'n_removed': len(removed), 'changed': changed, 'added': added, 'removed': removed}


def evidence_counters(ctx):
    """qa_report counters of the v0.3.0 evidence model (lead 2026-10-21 12:17Z): decided_values (numbers with the DECIDED pill, by
    source class and source file), decided texts, identifiers, and untagged (a number without one of the ten tags or DECIDED,
    or a text that states a quantity without a class). untagged must be 0."""
    dv, dt, ids, unt, txt_free, by_kind, by_src, by_basis = [], [], [], [], [], {}, {}, {}
    for t in ctx.traces:
        num = is_number(t.value)
        if getattr(t, 'ident', False):
            ids.append(t.tid)
            continue
        if t.ev == 'DECIDED':
            (dv if num else dt).append(t.tid)
            if num:
                k = getattr(t, 'basis_kind', None) or '?'
                by_kind[k] = by_kind.get(k, 0) + 1
                src = SRC_FILE.get(t.sid) or t.sid or 'generator'
                by_src[src] = by_src.get(src, 0) + 1
                b = re.sub(r';.*$', '', getattr(t, 'basis', None) or '?')
                b = re.sub(r', line (\d+).*$', r', line \1', b)
                by_basis[b] = by_basis.get(b, 0) + 1
            continue
        if num:
            if not (ev_ok(t.ev)):
                unt.append(t.tid)
        elif isinstance(t.value, str) or isinstance(t.value, (dict, list)):
            if t.ev is None or (t.ev not in ('REF',) and not ev_ok(t.ev)):
                (unt if has_quantity(_plain_text(t.value)) else txt_free).append(t.tid)
    return {'decided_values': {'n': len(dv), 'by_source_class': by_kind, 'by_source_file': by_src, 'by_basis_text': dict(sorted(by_basis.items(), key=lambda kv: -kv[1])),
                               'ids': dv},
            'decided_texts': {'n': len(dt)}, 'identifiers': {'n': len(ids), 'ids': ids},
            'untagged': {'n': len(unt), 'ids': unt,
                         'rule': 'a number whose class is not one of the ten tags or DECIDED, or a text without a class that states a quantity'},
            'texts_without_class': {'n': len(txt_free), 'ids': txt_free, 'note': 'texts that state no quantity and carry no class (information only)'}}


def main(argv=None):
    ap = argparse.ArgumentParser(description='ARGOS H1 engine datasheet generator')
    ap.add_argument('--cad-version', default='v3.5.2')
    ap.add_argument('--cad-dir', default=DEFAULT_CAD_DIR)
    ap.add_argument('--hub', default=DEFAULT_HUB)
    ap.add_argument('--rev', default='rev1-draft')
    ap.add_argument('--status', default='DRAFT', help='status word printed on the cover and in the page header (v0.3.1)')
    ap.add_argument('--note', default='rev1 draft for the FINAL CAD v3.5.2; inputs as they stand (PENDING where an input is pending)')
    ap.add_argument('--out', default=os.path.join(DS_ROOT, 'out', 'rev1'))
    ap.add_argument('--renders', default=None, help='render folder (default build/renders/<cad-version>)')
    ap.add_argument('--decisions', type=int, default=10, help='number of recent lead decision lines listed in §1')
    ap.add_argument('--no-pdf', action='store_true')
    ap.add_argument('--nice', type=int, default=15)
    ap.add_argument('--node', default='/opt/node22/bin/node')
    ap.add_argument('--pw-browsers', default='/opt/pw-browsers')
    ap.add_argument('--overrides', default=os.path.join(HERE, 'decision_overrides.json'),
                    help='decision override table (JSON); "none" shows every interface value as published')
    ap.add_argument('--diff-against', default=None, help='previous trace.json: write diff_vs_<rev>.json (values that changed)')
    ap.add_argument('--prev-sources', default=None, help='sources.json of the previous revision (revision history)')
    ap.add_argument('--ele41-line', type=int, default=None,
                    help='promoted-v4.1 build: the CHANGELOG line that records the promotion of electronics.json v4.1 (v0.3.1; lead GO 2026-10-21 14:48:44Z)')
    a = ap.parse_args(argv)
    a.overrides = None if a.overrides == 'none' else os.path.abspath(a.overrides)
    a.hub, a.cad_dir, a.out = os.path.abspath(a.hub), os.path.abspath(a.cad_dir), os.path.abspath(a.out)
    a.renders = os.path.abspath(a.renders or os.path.join(DS_ROOT, 'build', 'renders', a.cad_version))
    a.build = os.path.join(DS_ROOT, 'build')
    os.makedirs(os.path.join(a.out, 'assets'), exist_ok=True)
    os.makedirs(a.build, exist_ok=True)
    ctx = Ctx(a)
    register_sources(ctx, a)
    if ensure_fonts(ctx, a):
        MPL_FONTS[:] = a.fonts
    errs = [q for q in ctx.qa if q['level'] == 'ERROR']
    if errs:
        for q in errs:
            print('ERROR', q['msg'], file=sys.stderr)
        sys.exit(2)
    if 'OVR' in ctx.sources and ctx.src('OVR').data is not None:
        ctx.ovr = Overrides(ctx, a.overrides)
        ctx.ovr.load({'cl': Changelog(ctx, 'CL')})
    D = prepare(ctx, a)
    if ctx.ovr:
        ents = ctx.ovr.entries
        cnt = {k: sum(1 for e in ents if e['status'] == k) for k in ('ACTIVE', 'REDUNDANT', 'ERROR')}
        nw = sum(1 for e in ctx.ovr.sups for p in e['pointers'] if p['status'] == 'WITHHELD')
        D['ovr_summary'] = ctx.d(f'{ctx.ovr.version}: {cnt["ACTIVE"]} active, {cnt["REDUNDANT"]} redundant, {cnt["ERROR"]} in error; '
                                 f'{len(ctx.ovr.sups)} superseded values withheld ({nw} interface keys); see §13.1 and §13.2', '',
                                 'count of override entries by status on this build', [e['value_tv'] for e in ents])
    else:
        D['ovr_summary'] = ctx.missing('decision override table not loaded (interface wording shown as published)', 'MISSING')
    hist = []
    for prev in [p for p in (a.prev_sources, os.path.join(DS_ROOT, 'out', 'sources.json'), os.path.join(a.out, 'sources.json')) if p]:
        if os.path.exists(prev):
            try:
                for h in json.load(open(prev)).get('revision_history', []):
                    if h.get('rev') != a.rev and not any(x.get('rev') == h.get('rev') for x in hist):
                        hist.append(h)
            except (ValueError, OSError):
                pass
    hist.append({'rev': a.rev, 'generated': D['generated'], 'cad_version': a.cad_version, 'generator': f'{GEN_NAME} {GEN_VERSION}', 'note': a.note})
    D['history'] = hist
    doc = Doc()
    parts = []
    for fn in (sec_identification, sec_performance, sec_throttle_tvc, sec_geometry_mass, sec_bom, sec_materials, sec_combustion,
               sec_plume, sec_fea, sec_electronics, sec_mission, sec_verification):
        parts.append(fn(ctx, doc, a, D))
    register_contradictions(ctx, a, D)
    parts.append(sec_contradictions(ctx, doc, a, D))
    parts.append(sec_unknowns(ctx, doc, a, D))
    parts.append(sec_revision_sources(ctx, doc, a, D))
    parts.append(sec_trace(ctx, doc, a, D))
    cover = sec_cover(ctx, doc, a, D)
    body = '\n'.join(parts)
    title = f'{DOC_ID} {a.rev}'
    html_path = os.path.join(a.out, 'datasheet.html')
    pdf_name = f'{DOC_ID}_{a.rev}.pdf'
    pdf_path = os.path.join(a.out, pdf_name)

    def write_html():
        open(html_path, 'w', encoding='utf-8').write(html_doc(title, cover + sec_toc(doc) + body))
    write_html()
    leak_scan(ctx, 'datasheet.html', open(html_path, encoding='utf-8').read())
    n_path = path_scan(ctx, 'datasheet.html', open(html_path, encoding='utf-8').read())
    for fn in sorted(glob.glob(os.path.join(a.out, 'assets', '*.svg'))):
        leak_scan(ctx, 'assets/' + os.path.basename(fn), open(fn, encoding='utf-8', errors='replace').read())
        n_path += path_scan(ctx, 'assets/' + os.path.basename(fn), open(fn, encoding='utf-8', errors='replace').read())
    toc_info = {'passes': 0, 'missing': None, 'stable': None}
    npages = None
    if not a.no_pdf:
        print_pdf(a, html_path, pdf_path, D)
        prev_pages = None
        for p in range(3):
            pages = pdf_pages_text(pdf_path)
            missing = locate_heads(doc, pages)
            cur = [h['page'] for h in doc.heads]
            toc_info['passes'] = p + 1
            toc_info['missing'] = missing
            if cur == prev_pages:
                toc_info['stable'] = True
                break
            prev_pages = cur
            write_html()
            print_pdf(a, html_path, pdf_path, D)
        else:
            pages = pdf_pages_text(pdf_path)
            locate_heads(doc, pages)
            toc_info['stable'] = [h['page'] for h in doc.heads] == prev_pages
        npages = pdf_npages(pdf_path)
        ptxt = pdf_pages_text(pdf_path)
        if ptxt and not ptxt[-1].strip() and (npages is None or len(ptxt) > npages):
            ptxt = ptxt[:-1]   # pdftotext ends the last page with a form feed
        leak_scan(ctx, 'the PDF text', '\n'.join(ptxt))
        n_path += path_scan(ctx, 'the PDF text', '\n'.join(ptxt))
        annot_scan(ctx, ptxt)
        nost = [i + 1 for i, t in enumerate(ptxt) if PAGE_STATEMENT not in re.sub(r'\s+', ' ', t)]
        if nost:
            ctx.issue('ERROR', f'page statement missing on pages {nost[:20]}')
        toc_info['pages_with_statement'] = len(ptxt) - len(nost)
        if toc_info['missing']:
            ctx.issue('WARN', f'headings not located in the PDF text: {toc_info["missing"]}')
    srcs = {sid: {'path': hub_rel(a, s.path) or ('OUTSIDE THE HUB: ' + os.path.basename(s.path)), 'role': s.role, 'kind': s.kind, 'version': s.version, 'sha256_16': s.sha16, 'size': s.size,
                  'mtime_utc': s.mtime, 'exists': s.exists, 'required': s.required, 'reads': s.reads} for sid, s in ctx.sources.items()}
    json.dump({'document': DOC_ID, 'revision': a.rev, 'generated_utc': D['generated'], 'generator': f'gen/{GEN_NAME} {GEN_VERSION}',
               'generator_sha256_16': sha16_file(os.path.abspath(__file__)), 'cad_version': a.cad_version, 'hub': 'argos-engine (paths below are hub-relative)',
               'cad_dir': hub_rel(a, a.cad_dir), 'renders': hub_rel(a, a.renders), 'sources': srcs, 'revision_history': hist,
               'note': 'Digital design data only; nothing here is physical approval; no hardware has been tested.'},
              open(os.path.join(a.out, 'sources.json'), 'w'), indent=1)
    tr = [{'id': t.tid, 'value': t.value if not isinstance(t.value, float) or math.isfinite(t.value) else str(t.value), 'unit': t.unit, 'class': t.ev,
           'tag_raw': t.tag_raw, 'source': t.sid, 'key': t.ptr, 'note': t.note, 'formula': t.formula, 'inputs': t.inputs, 'status': t.status,
           'basis': getattr(t, 'basis', None), 'basis_detail': getattr(t, 'basis_detail', None), 'basis_kind': getattr(t, 'basis_kind', None),
           'identifier': getattr(t, 'ident', False), 'masked': t.masked} for t in ctx.traces]
    json.dump({'document': DOC_ID, 'revision': a.rev, 'n': len(tr), 'traces': tr}, open(os.path.join(a.out, 'trace.json'), 'w'), indent=0, default=str)
    diff = None
    if a.diff_against:
        diff = diff_traces(a.diff_against, json.loads(json.dumps(tr, default=str)))
        diff['against'] = hub_rel(a, a.diff_against) or os.path.basename(a.diff_against)
        json.dump(diff, open(os.path.join(a.out, f'diff_vs_{diff.get("against_revision") or "previous"}.json'), 'w'), indent=1, default=str)
    cls_counts = {}
    for t in ctx.traces:
        cls_counts[t.ev or 'UNTAGGED'] = cls_counts.get(t.ev or 'UNTAGGED', 0) + 1
    ev_q = evidence_counters(ctx)
    qa = {'generated_utc': D['generated'], 'generator': f'{GEN_NAME} {GEN_VERSION}', 'generator_sha256_16': sha16_file(os.path.abspath(__file__)),
          'cells': {'data_cells': CELL_STATS['data_cells'], 'traced': CELL_STATS['traced'], 'untraced': CELL_STATS['untraced']},
          'traces': len(ctx.traces), 'classes': cls_counts, 'evidence': ev_q, 'decided_values': ev_q['decided_values']['n'],
          'untagged': ev_q['untagged']['ids'], 'private_paths_visible': n_path,
          'issues': ctx.qa, 'contradictions': [c['id'] + ' ' + c['title'] + (' (RETIRED)' if c.get('retired') else '') for c in ctx.contradictions],
          'contradictions_open': sum(1 for c in ctx.contradictions if not c.get('retired')),
          'contradictions_retired': [c['id'] for c in ctx.contradictions if c.get('retired')],
          'electronics_build': ({'promoted_v4.1_line': D['ele']['line']} if D['ele']['promo'] else 'v4 with v4.1 PENDING REVIEW'),
          'unknowns': D.get('unknown_counts'), 'pending_inputs': D.get('pending_inputs'), 'pages': npages, 'toc': toc_info,
          'diff': ({k: diff[k] for k in ('against', 'against_revision', 'n_changed', 'n_added', 'n_removed')} if diff else None),
          'overrides': [{'id': e['id'], 'status': e['status'], 'errors': e['errors'],
                         'targets': [{k: t[k] for k in ('sid', 'ptr', 'mode', 'status', 'shown')} for t in e['targets']],
                         'annotation': ({'status': e['annot']['status'], 'shown': e['annot']['shown']} if e.get('annot') else None)}
                        for e in (ctx.ovr.entries if ctx.ovr else [])],
          'withheld': [{'id': e['id'], 'pointers': e['pointers'], 'masked_fields': (ctx.ovr.mask_hits.get(e['id'], 0) if ctx.ovr else 0),
                        'corroborated': e['corroborated']} for e in (ctx.ovr.sups if ctx.ovr else [])],
          'headings': [{'text': h['text'], 'page': h['page']} for h in doc.heads]}
    json.dump(qa, open(os.path.join(a.out, 'qa_report.json'), 'w'), indent=1, default=str)
    n_err = sum(1 for q in ctx.qa if q['level'] == 'ERROR')
    print(f'datasheet: {html_path}')
    if not a.no_pdf:
        print(f'pdf: {pdf_path} ({npages} pages, contents passes {toc_info["passes"]}, stable {toc_info["stable"]})')
    print(f'traces {len(ctx.traces)}; data cells {CELL_STATS["data_cells"]}, traced {CELL_STATS["traced"]}, untraced {len(CELL_STATS["untraced"])}; '
          f'decided_values {ev_q["decided_values"]["n"]}; untagged {len(qa["untagged"])}; issues: {n_err} errors, {sum(1 for q in ctx.qa if q["level"] == "WARN")} warnings; '
          f'contradictions {sum(1 for c in ctx.contradictions if not c.get("retired"))} (+{sum(1 for c in ctx.contradictions if c.get("retired"))} retired)')
    if diff:
        print(f'diff vs {diff["against_revision"]}: changed {diff["n_changed"]}, added {diff["n_added"]}, removed {diff["n_removed"]}')
    return 1 if n_err else 0

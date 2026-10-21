"""Assemble gen/build_datasheet.py v0.3.1 (v0.3.0 was the rev1-draft generator) from gen/history/build_datasheet_v0.2.0.py and the new code
pieces ds/new_*.py (sorted by name). Each patch is asserted (exactly one match). Run with
/opt/engine-venv/bin/python -I assemble.py"""
import ast, glob, os, py_compile, sys

G = '/home/claude/work/shared-fallback/engine/07-datasheet/gen'
SRC = G + '/history/build_datasheet_v0.2.0.py'
OUT = G + '/build_datasheet.py'
DS = os.path.dirname(os.path.abspath(__file__))

REMOVE = ['fa1_envelope', 'sec_fa1', 'plot_throttle', 'plot_pressure_ladder', 'plot_landing', 'plot_slew', 'plot_sequence',
          'sec_cover', 'sec_identification', 'sec_performance', 'sec_throttle_tvc', 'sec_geometry_mass', 'sec_bom', 'sec_materials',
          'ABORT_MAP', 'sec_combustion', 'FEA_SCHEMA', 'FEA_GLOBS', 'find_fea_tables', 'sec_fea', 'fea_margin_tables',
          'sec_electronics', 'sec_mission', 'sec_verification', 'register_contradictions', 'register_sources', 'prepare',
          'print_pdf', 'main',
          # v0.3.0 evidence model (lead rulings 2026-10-21 12:13Z item 4, 12:17Z): redefined in new_00_infra.py
          'EV_CLASSES', 'normalise_tag', 'Changelog', 'rx', 'rx_text', 'md_row', 'ev_pill',
          # redefined in new_65_sec_plume.py (operating points) and new_95_appendix.py (hub-relative paths, DECIDED basis)
          'sec_plume', 'sec_revision_sources', 'sec_trace',
          # v0.3.1 (rev1 phase 2): contradictions with the governing source and status (lead 2026-10-21 13:24Z), new_80_sec_ver.py
          'sec_contradictions']

PATCHES = [
    # rev1 phase 2 (REV-DS-1 D1-08): a source number prints at its source precision ('src'); a number read from a text keeps the
    # digits of the text; derived numbers keep the generator's display rounding
    ("def fmt_num(v, fmt=None):\n    if fmt:\n        try:\n            s = format(v, fmt)\n",
     "def fmt_num(v, fmt=None):\n    if fmt == 'src':\n        s = src_digits(v)  # v0.3.1: source precision (REV-DS-1 D1-08)\n    elif fmt:\n        try:\n            s = format(v, fmt)\n"),
    ("        if isinstance(v, bool):\n            return 'yes' if v else 'no'\n        if isinstance(v, (int, float)):\n            return fmt_num(v, fmt)\n",
     "        if isinstance(v, bool):\n            return 'yes' if v else 'no'\n"
     "        if fmt is None and isinstance(v, (int, float)) and getattr(self, 'src_txt', None):\n"
     "            return self.src_txt.replace('-', '−') if self.src_txt.startswith('-') else self.src_txt  # v0.3.1: the digits of the source text\n"
     "        if fmt is None and self.formula is None and self.sid not in (None, 'generator') and not str(self.tag_raw or '').startswith('DERIVED by'):\n"
     "            fmt = 'src'  # v0.3.1: a source value prints at its source precision (REV-DS-1 D1-08)\n"
     "        if isinstance(v, (int, float)):\n            return fmt_num(v, fmt)\n"),
    # rev1 phase 2 (REV-DS-1 D1-11, D1-12): display rules for quoted text; the trace keeps the source string
    ("    s = tv.value if isinstance(tv.value, str) else readable(tv.value)\n    ov = getattr(tv.ctx, 'ovr', None)\n",
     "    s = tv.value if isinstance(tv.value, str) else readable(tv.value)\n"
     "    s = display_text(tv, s)  # v0.3.1: display rules (REV-DS-1 D1-11, D1-12); the trace keeps the source string\n"
     "    ov = getattr(tv.ctx, 'ovr', None)\n"),
    # rev1 phase 2: layout labels near the figure edge stay inside the figure (the last 'mm' was clipped on the draft's page 11)
    ("""        o.append(f'<line x1="{px:.1f}" y1="{H - 4:.1f}" x2="{px:.1f}" y2="{y - fs:.1f}" class="ld"/>')\n"""
     """        o.append(svg_text(px, y, g['group'], fs, 'middle', 600, '#1d2733'))\n"""
     """        z0, z1 = g['cad_z_range_m']\n"""
     """        o.append(svg_text(px, y + fs + 2, f'CAD z {z0 * 1000:+.0f} … {z1 * 1000:+.0f} mm', fs * 0.82, 'middle', 400, '#55626f'))\n""",
     """        z0, z1 = g['cad_z_range_m']\n"""
     """        zt = f'CAD z {z0 * 1000:+.0f} … {z1 * 1000:+.0f} mm'\n"""
     """        hw = max(len(g['group']) * fs * 0.31, len(zt) * fs * 0.82 * 0.31)  # estimated half width of the label\n"""
     """        tx = min(max(px, hw + 6), W - hw - 6)\n"""
     """        o.append(f'<line x1="{px:.1f}" y1="{H - 4:.1f}" x2="{tx:.1f}" y2="{y - fs:.1f}" class="ld"/>')\n"""
     """        o.append(svg_text(tx, y, g['group'], fs, 'middle', 600, '#1d2733'))\n"""
     """        o.append(svg_text(tx, y + fs + 2, zt, fs * 0.82, 'middle', 400, '#55626f'))\n"""),
    # rev1 phase 2: a contradiction carries its governing source(s) and its status (lead 2026-10-21 13:24Z)
    ("""    def contra(self, cid, title, sides, newest, resolution):\n"""
     """        \"\"\"sides: list of (label, TV); newest: label of the side shown as current.\"\"\"\n"""
     """        self.contradictions.append({'id': cid, 'title': title, 'sides': sides, 'newest': newest,\n"""
     """                                    'resolution': resolution})\n""",
     """    def contra(self, cid, title, sides, newest, resolution, governs=None, status=None):\n"""
     """        \"\"\"sides: list of (label, TV); newest: label of the side shown as current; governs: list of (label, TV), the governing\n"""
     """        source(s); status: the state of the disagreement (v0.3.1).\"\"\"\n"""
     """        self.contradictions.append({'id': cid, 'title': title, 'sides': sides, 'newest': newest,\n"""
     """                                    'resolution': resolution, 'governs': governs or [], 'status': status})\n"""),
    # rev1 phase 2 (ovr-6): the overrides section names the entries retired under the table's drop rule
    ("""             'the stale wording is still in it. An entry with no active target is reported REDUNDANT and can be dropped.</p>')\n    rows = []\n""",
     """             'the stale wording is still in it. An entry with no active target is reported REDUNDANT and can be dropped.</p>')\n"""
     """    ret = [r.get('id') for r in ((src.data or {}).get('retired') or []) if isinstance(r, dict)]\n"""
     """    if ret:\n"""
     """        o.append(f'<p class="small">Retired in {esc(ov.version or "")}, each REDUNDANT at the rev1 draft build (the table\\'s drop rule), '\n"""
     """                 f'kept verbatim in the file under "retired" and in gen/history/: {esc(", ".join(ret))}.</p>')\n"""
     """    rows = []\n"""),
    # rev1 phase 2: the BOM row trace value carries the full part name (the 60-character cut was silent)
    ("""        self.row_tv = TV(ctx, f"{self.pn}: {line.get('name', '')[:60]}", '', 'DESIGN',\n""",
     """        self.row_tv = TV(ctx, f"{self.pn}: {line.get('name', '')}", '', 'DESIGN',\n"""),
    # rev1 final: the unknowns register prints a structured value as 'key: value; ...' (not a Python repr), applies the display rules,
    # and cuts at a word boundary with a visible ' …' (the trace keeps the full value)
    ("""            val = tv.num() if tv.value is not None else (tv.status or tv.ev)\n            if isinstance(tv.value, str):\n                val = tv.value\n""",
     """            val = tv.num() if tv.value is not None else (tv.status or tv.ev)\n            if isinstance(tv.value, str):\n                val = tv.value\n"""
     """            elif isinstance(tv.value, (dict, list)):\n                val = readable(tv.value)  # v0.3.1: not a Python repr\n"""
     """            val = display_text(tv, val) if isinstance(val, str) else val  # v0.3.1: display rules (REV-DS-1 D1-11, D1-12)\n"""),
    ("""             esc(str(r[4])[:260] + ('…' if len(str(r[4])) > 260 else ''))] for r in rows]\n""",
     """             esc(clipw(str(r[4]), 260))] for r in rows]  # v0.3.1: word-boundary cut with a visible ' …'\n"""),
    # rev1 final: a short part name is cut at a word boundary with a visible ' …' (the row trace keeps the full name)
    ("""    return s if len(s) <= maxlen else s[:maxlen - 1].rstrip() + '…'\n""",
     """    return s if len(s) <= maxlen else clipw(s, maxlen)  # v0.3.1: word-boundary cut with a visible ' …'\n"""),
    # rev1 final: a price reference is printed whole up to 140 characters, then cut at a word with a visible ' …' (was a silent 70 / 90 cut)
    ("""esc((m.group(1) if m else p)[:70]) + ' (not a DK quote)</span>'""",
     """esc(clipw(m.group(1) if m else p, 140)) + ' (not a DK quote)</span>'"""),
    ("""        h = '<span class="small">' + esc(p[:90]) + '</span> <span class="q">DK delivery TO-QUOTE</span>'""",
     """        h = '<span class="small">' + esc(clipw(p, 140)) + '</span> <span class="q">DK delivery TO-QUOTE</span>'"""),
    ("""f'<span class="mono">{esc(r[3][:150])}</span>',""", """f'<span class="mono">{esc(clipw(r[3], 150))}</span>',"""),
    ("GEN_VERSION = '0.2.0'", "GEN_VERSION = '0.3.1'"),  # 0.3.0 = rev1-draft (gen/history/build_datasheet_v0.3.0.py); 0.3.1 = rev1 phase 2
    ("DEFAULT_CAD_DIR = '/home/claude/work/mechanical/engine/03-cad'",
     "DEFAULT_CAD_DIR = '/home/claude/work/shared-fallback/engine/03-cad/v3.5.2'"),
    # every traced value gets its final class from the v0.3.0 evidence model (resolve_class, new_00_infra.py)
    ("            ov.filter_tv(self)\n        self.tid = ctx.register(self)\n",
     "            ov.filter_tv(self)\n        resolve_class(self)  # v0.3.0: ten tags or DECIDED; no default class\n        self.tid = ctx.register(self)\n"),
    ("        return ev_pill(self.ev, self.tag_raw)\n",
     "        return ev_pill(self.ev, self.tag_raw, getattr(self, 'basis', None), self.status if self.value is not None else None)\n"),
    ("                tag_raw = f'(class set by generator: {tag})'\n",
     "                tag_raw = f'(class set at the call site: {tag})'\n"),
    ("ev, tag_raw = tag_default, f'(no source tag; class set by generator: {tag_default})'",
     "ev, tag_raw = tag_default, f'(no source tag; class set at the call site: {tag_default})'"),
    ("caption='Values the Combustion author withdrew in REPORT v2.4 §13 that are still live in combustion.json v2.4 (REV-COMB-2 R2-05). '",
     "caption='Values the Combustion author withdrew in REPORT v2.4 §13 (their list: combustion.json /superseded_v2p4), wherever combustion.json '\n"
     "                            f'{esc(ctx.src(\"CMB\").version or \"\")} still carries them. '"),
    ("SRC_FILE = {'CMB': 'combustion.json', 'REQ': 'REQUIREMENTS.md', 'ICD': 'ICD-AIRFRAME.md', 'CL': 'CHANGELOG.md',\n"
     "            'ELE': 'electronics.json', 'GNC': 'gnc.json', 'MEC': 'mechanical.json', 'FA1': 'fa1_envelope_v2p4a.json'}",
     "SRC_FILE = {'CMB': 'combustion.json', 'REQ': 'REQUIREMENTS.md', 'ICD': 'ICD-AIRFRAME.md', 'CL': 'CHANGELOG.md',\n"
     "            'ELE': 'electronics.json', 'GNC': 'gnc.json', 'MEC': 'mechanical.json', 'FA1': 'fa1_envelope_v2p4a.json',\n"
     "            'F3D': 'REPORT-FEA3D-v352.md', 'DSIC': 'DATASHEET-INPUTS-COMBUSTION.md', 'DSIG': 'DATASHEET-INPUTS-GNC.md',\n"
     "            'MMXMD': 'margin_matrix_v352.md (rows v8)', 'TXT5': 'item_c_tf1_texts_v352_v5.json', 'BOM': 'BOM_v3.5.2.json',\n"
     "            'MP': 'massprops_v3.5.2.json', 'MDEL': 'massdelta_v3.5.2_vs_v3.5.1.json', 'F4J': 'f4_v352.json', 'SET': 'set_v3.5.2.json',\n"
     "            'BENCH': 'bench_plan_v4.md', 'RCMB': 'combustion REPORT.md', 'RPL': 'plume REPORT.md', 'PVAL': 'validation_v2.json'}"),
    ("    return (f'<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>{esc(title)}</title>'\n"
     "            f'<meta name=\"generator\" content=\"{GEN_NAME} {GEN_VERSION}\"><style>{CSS}</style></head><body>{body}</body></html>')",
     "    return (f'<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>{esc(title)}</title>'\n"
     "            f'<meta name=\"generator\" content=\"{GEN_NAME} {GEN_VERSION}\"><style>{CSS}{CSS_REV1}</style></head><body>{body}</body></html>')"),
]


def main():
    src = open(SRC, encoding='utf-8').read()
    for old, new in PATCHES:
        n = src.count(old)
        assert n == 1, (n, old[:120])
        src = src.replace(old, new)
    tree = ast.parse(src)
    lines = src.splitlines(keepends=True)
    drop = []
    found = set()
    for node in tree.body:
        name = None
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            name = node.name
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
        if name in REMOVE:
            start = node.lineno - 1
            if getattr(node, 'decorator_list', None):
                start = min(d.lineno for d in node.decorator_list) - 1
            drop.append((start, node.end_lineno))
            found.add(name)
    miss = set(REMOVE) - found
    assert not miss, miss
    keep = []
    i = 0
    for s, e in sorted(drop):
        keep.extend(lines[i:s])
        i = e
    keep.extend(lines[i:])
    body = ''.join(keep)
    # collapse runs of blank lines left by removals
    while '\n\n\n\n' in body:
        body = body.replace('\n\n\n\n', '\n\n\n')
    pieces = sorted(glob.glob(os.path.join(DS, 'new_*.py')))
    new = '\n\n'.join(open(p, encoding='utf-8').read().rstrip() + '\n' for p in pieces)
    marker = '# page design (print CSS)'
    k = body.index(marker)
    k = body.rindex('\n# ====', 0, k) + 1
    body = body[:k] + '# ' + '=' * 93 + '\n# rev1 code (v0.3.1): ' + ', '.join(os.path.basename(p) for p in pieces) + '\n# ' + '=' * 93 + '\n' + \
        new + '\n\n' + body[k:]
    # main() goes last
    if '\nif __name__ == ' in body:
        a, b = body.split('\nif __name__ == ', 1)
        body = a.rstrip() + '\n\n\nif __name__ == ' + b
    out = OUT
    if '--test-out' in sys.argv:
        # test copy outside gen/ (gen/build_datasheet.py stays as published); it reads its inputs from the real gen/
        out = sys.argv[sys.argv.index('--test-out') + 1]
        assert not os.path.abspath(out).startswith(G), out
        h0 = "HERE = os.path.dirname(os.path.abspath(__file__))"
        assert body.count(h0) == 1
        body = body.replace(h0, f"HERE = {G!r}  # test copy: inputs from the real gen/")
    open(out, 'w', encoding='utf-8').write(body)
    py_compile.compile(out, cfile='/dev/shm/ds_rev1/build_datasheet.pyc', doraise=True)  # keep bytecode out of gen/
    print('wrote', out, len(body.splitlines()), 'lines; pieces', [os.path.basename(p) for p in pieces])


if __name__ == '__main__':
    main()

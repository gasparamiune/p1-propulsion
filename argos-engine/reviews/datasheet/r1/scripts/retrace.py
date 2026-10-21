#!/opt/engine-venv/bin/python -I
"""REV-DS-1 independent re-trace harness (reviewer's own code; read-only on the hub).

For each value id it follows the chain
    PDF page (T-id token)  ->  HTML display string  ->  trace.json entry (source id + key)
    ->  sources.json (path, sha at build)  ->  the source file today (sha, value at the key)
and reports, per id: the PDF body pages, the displayed text, the source pointer, the value read
from the source by this harness, and whether the three agree.

It re-implements the locator forms of the datasheet generator (JSON pointer with optional
[regex ...]; CHANGELOG L<n>(<k>) items with [sentence containing ...]; markdown locators by line,
row, section, bullet or heading) without importing the generator, and adds an independent check
for every text value: the traced text must occur verbatim in the source line(s) it names.

usage:
  retrace.py --out-dir <dir> --trace <trace.json> --sources <sources.json>
             [--html <datasheet.html>] [--pdf <file.pdf>] (--ids T001,T002 | --all | --ids-file f)
Writes <out-dir>/retrace_<label>.json and prints a table. Nothing here is physical approval:
a value match shows the datasheet quotes its source faithfully, not that the source is right.
"""
import argparse
import hashlib
import html as htmlmod
import json
import os
import re
import subprocess
import sys

TOL_REL = 1e-9
WITHHELD_RE = re.compile(r'\[withheld: [^\]]*\]')


# ------------------------------------------------------------------ basic helpers
def sha16_bytes(b):
    return hashlib.sha256(b).hexdigest()[:16]


def sha16_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()[:16]


def sha16_text(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()[:16]


def ptr_get(doc, ptr):
    if ptr in ('', '/'):
        return doc
    x = doc
    for part in ptr.split('/')[1:]:
        part = part.replace('~1', '/').replace('~0', '~')
        if isinstance(x, list):
            x = x[int(part)]
        else:
            x = x[part]
    return x


def norm_ws(s):
    return re.sub(r'\s+', ' ', str(s)).strip()


def strip_md(s):
    s = str(s).replace('**', '')
    return norm_ws(s)


def num_eq(a, b):
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return False
    return abs(a - b) <= TOL_REL * max(1.0, abs(a), abs(b))


def is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def text_contains(hay, needle):
    """Verbatim (whitespace- and bold-normalised) containment, honouring withheld masks."""
    H = strip_md(hay)
    N = strip_md(needle)
    if N.endswith(' …'):
        N = N[:-2].strip()
    if not N:
        return True
    if WITHHELD_RE.search(N):
        pos = 0
        for frag in WITHHELD_RE.split(N):
            frag = frag.strip()
            if not frag:
                continue
            i = H.find(frag, pos)
            if i < 0:
                return False
            pos = i + len(frag)
        return True
    return N in H


# ------------------------------------------------------------------ source cache
class Sources:
    def __init__(self, sources_json):
        self.meta = json.load(open(sources_json, encoding='utf-8'))
        self.src = self.meta.get('sources', {})
        self._cache = {}

    def info(self, sid):
        return self.src.get(sid)

    def load(self, sid):
        if sid in self._cache:
            return self._cache[sid]
        s = self.src.get(sid)
        out = {'sid': sid, 'path': None, 'exists': False, 'sha_now': None, 'sha_build': None,
               'data': None, 'text': None, 'lines': None, 'kind': None}
        if s is None:
            self._cache[sid] = out
            return out
        p = s.get('path')
        out.update(path=p, sha_build=s.get('sha256_16'), kind=s.get('kind'))
        if p and os.path.isfile(p):
            out['exists'] = True
            raw = open(p, 'rb').read()
            out['sha_now'] = sha16_bytes(raw)
            if s.get('kind') == 'json':
                try:
                    out['data'] = json.loads(raw.decode('utf-8'))
                except Exception as e:  # noqa
                    out['data'] = None
                    out['err'] = f'json load: {e}'
            if s.get('kind') in ('md', 'text', 'csv') or s.get('kind') is None:
                t = raw.decode('utf-8', errors='replace')
                out['text'] = t
                out['lines'] = t.splitlines()
        self._cache[sid] = out
        return out


# ------------------------------------------------------------------ conversions recorded in notes
CONV_RE = re.compile(r'display = raw x ([\-+0-9.eE]+)(?: \+ ([\-+0-9.eE]+))?')


def apply_conv(val, note):
    if not note or not is_num(val):
        return val, None
    m = CONV_RE.search(note)
    if not m:
        return val, None
    f = float(m.group(1))
    off = float(m.group(2)) if m.group(2) else 0.0
    return val * f + off, f'x{f:g}+{off:g}'


# ------------------------------------------------------------------ CHANGELOG (re-implemented)
CL_MARK = re.compile(r'^\(?(founder )?(decisions?|result|review|note|handback|direction)\b', re.I)


def cl_parse(raw):
    parts = raw.split(' | ')
    rec = {'raw': raw, 'sha16': sha16_text(raw)}
    if len(parts) >= 4 and re.match(r'^\d{4}-\d\d-\d\d$', parts[0]) and CL_MARK.match(parts[2]):
        rec.update(owner=parts[1], what=parts[2], text=' | '.join(parts[3:]))
    elif len(parts) >= 4 and re.match(r'^\d{4}-\d\d-\d\d$', parts[0]):
        rec.update(owner=parts[1], what=parts[2],
                   text=' | '.join(parts[3:-1]) if len(parts) > 4 else parts[3],
                   why=parts[-1] if len(parts) > 4 else '')
    else:
        rec.update(owner=None, what=None, text=raw)
    return rec


def cl_items(text):
    out = {}
    pos, k, starts = 0, 1, []
    while True:
        m = None
        for mm in re.finditer(r'\((%d)\)\s' % k, text[pos:]):
            i = pos + mm.start()
            before = text[:i].rstrip()
            if i == 0 or (before and before[-1] in '.:;)') or before.endswith('|'):
                m = i
                break
        if m is None:
            break
        starts.append((k, m))
        pos = m + 3
        k += 1
    for j, (kk, st) in enumerate(starts):
        end = starts[j + 1][1] if j + 1 < len(starts) else len(text)
        out[kk] = text[st:end].strip()
    return out


def sentences_with(txt, phrases):
    sents = re.split(r'(?<=[.;])\s+(?=[A-Z(])', txt)
    return [s for s in sents if any(p.lower() in s.lower() for p in phrases)]


def parse_tail(tail):
    """Optional [sentence containing "a" | "b"] and [regex pat] suffixes of a locator."""
    phrases, regex = None, None
    m = re.search(r'\[sentence containing ((?:"[^"]*"(?: \| )?)+)\]', tail)
    if m:
        phrases = re.findall(r'"([^"]*)"', m.group(1))
    m = re.search(r'\[regex (.*)\]\s*$', tail)
    if m:
        regex = m.group(1)
    return phrases, regex


def resolve_cl(S, sid, key, entry):
    src = S.load(sid)
    r = {'kind': 'CL'}
    m = re.match(r'^L(\d+)(?:\((\d+)\))?(.*)$', key or '')
    if not m or not src['lines']:
        r.update(ok=None, why='unparsed CL key or no text')
        return r
    n, k, tail = int(m.group(1)), (int(m.group(2)) if m.group(2) else None), m.group(3)
    if n > len(src['lines']):
        r.update(ok=False, why=f'line {n} beyond file ({len(src["lines"])})')
        return r
    raw = src['lines'][n - 1]
    rec = cl_parse(raw)
    r['line'] = n
    r['line_sha_now'] = rec['sha16']
    msha = re.search(r'line sha ([0-9a-f]{16})', entry.get('tag_raw') or '')
    r['line_sha_build'] = msha.group(1) if msha else None
    r['line_sha_ok'] = (r['line_sha_build'] == rec['sha16']) if msha else None
    txt = rec['text']
    if k is not None:
        its = cl_items(txt)
        if k not in its:
            r.update(ok=False, why=f'no item ({k}) in line {n}')
            return r
        txt = re.sub(r'^\(%d\)\s*' % k, '', its[k])
    phrases, regex = parse_tail(tail)
    if phrases:
        hit = sentences_with(txt, phrases)
        if hit:
            txt = ' '.join(hit)
    val = entry.get('value')
    if regex:
        mm = re.search(regex, txt)
        if not mm:
            r.update(ok=False, why=f'regex {regex!r} not matched', source_value=None)
            return r
        sv = float(mm.group(1))
        r['source_value'] = sv
        r['ok'] = num_eq(sv, val)
        r['why'] = 'regex on item text'
        return r
    r['source_value'] = txt if len(txt) < 400 else txt[:400] + ' ...'
    if isinstance(val, str):
        same = strip_md(val) == strip_md(txt) or text_contains(txt, val)
        verb = text_contains(raw, val)
        if not verb and phrases:
            # joined non-adjacent sentences: each piece must be verbatim in the raw line
            pieces = re.split(r'(?<=[.;])\s+(?=[A-Z(])', val)
            verb = all(text_contains(raw, p) for p in pieces if p.strip())
        r['ok'] = bool(same and verb)
        r['why'] = ('item text equal' if strip_md(val) == strip_md(txt) else 'value contained in item') + \
                   ('; verbatim in raw line' if verb else '; NOT verbatim in raw line')
    else:
        r['ok'] = None
        r['why'] = 'non-text value on a CL key without regex'
    return r


# ------------------------------------------------------------------ markdown locators
def md_cells(line):
    return [c.strip() for c in line.strip().strip('|').split(' | ')]


def md_section_lines(text, heading_prefix):
    out, on = [], False
    for ln in text.splitlines():
        if ln.startswith('#'):
            h = ln.lstrip('#').strip()
            if on:
                break
            on = h.startswith(heading_prefix)
            continue
        if on:
            out.append(ln)
    return out


def md_table_rows(text, section_prefix=None):
    lines = text.splitlines()
    in_sec = section_prefix is None
    rows = []
    for ln in lines:
        if ln.startswith('#'):
            if section_prefix is not None:
                in_sec = ln.lstrip('#').strip().startswith(section_prefix)
            continue
        if in_sec and ln.startswith('|') and not re.match(r'^\|\s*-', ln):
            rows.append(md_cells(ln))
    return rows


def compare_text_or_num(val, txt, regex=None):
    if regex:
        mm = re.search(regex, txt or '')
        if not mm:
            return None, False, f'regex {regex!r} not matched'
        sv = float(mm.group(1))
        return sv, num_eq(sv, val), 'regex'
    if isinstance(val, str):
        ok = strip_md(val) == strip_md(txt) or text_contains(txt, val)
        return txt, ok, 'text equal' if strip_md(val) == strip_md(txt) else ('text contained' if ok else 'text differs')
    if is_num(val):
        # numeric value from a text cell: first number of the cell
        mm = re.search(r'[+\-−]?\d+(?:\.\d+)?(?:[eE][+\-]?\d+)?', txt or '')
        if not mm:
            return txt, False, 'no number in cell'
        sv = float(mm.group(0).replace('−', '-'))
        return sv, num_eq(sv, val), 'first number of the cell'
    return txt, None, 'value type not compared'


def resolve_md(S, sid, key, entry):
    src = S.load(sid)
    r = {'kind': 'MD'}
    L = src['lines']
    if L is None:
        r.update(ok=None, why='no text loaded')
        return r
    val = entry.get('value')
    k = key or ''
    phrases, regex = parse_tail(k)
    base = re.sub(r'\s*\[(sentence containing|regex) .*$', '', k)
    txt = None
    how = None
    # 1) '... (line N)' or 'line N row "lab" col C' or '§... row c0=... col C (line N)'
    m = re.search(r'col (\d+)(?: \(line (\d+)\))?', base)
    mline = re.search(r'\(line (\d+)\)', base) or re.match(r'^line (\d+)\b', base)
    if m and mline:
        n = int(mline.group(1))
        cells = md_cells(L[n - 1])
        c = int(m.group(1))
        txt = cells[c] if c < len(cells) else None
        how = f'line {n} col {c}'
        if txt is not None:
            txt = txt.replace('**', '').strip()
    elif re.match(r'^lines (\d+)-(\d+)$', base):
        a, b = map(int, re.match(r'^lines (\d+)-(\d+)$', base).groups())
        txt = ' '.join(x.strip() for x in L[a - 1:b]).strip()
        how = f'lines {a}-{b}'
    elif re.match(r'^line (\d+)', base) or re.search(r' line (\d+)$', base) or re.match(r'^heading line (\d+)$', base):
        mm = re.match(r'^line (\d+)', base) or re.search(r' line (\d+)$', base) or re.match(r'^heading line (\d+)$', base)
        n = int(mm.group(1))
        t = L[n - 1].strip()
        t = re.sub(r'^#+\s*', '', t)
        t = re.sub(r'^[-*]\s+', '', t)
        txt = t.replace('**', '')
        how = f'line {n}'
    elif re.match(r'^§(.*) row "(.*)" col (\d+)$', base):
        sec, rk, c = re.match(r'^§(.*) row "(.*)" col (\d+)$', base).groups()
        sec = None if sec == '*' else sec
        for row in md_table_rows(src['text'], sec):
            if row and re.sub(r'\*', '', row[0]).strip() == rk:
                txt = row[int(c)].replace('**', '').strip() if int(c) < len(row) else None
                break
        how = f'§{sec} row {rk!r} col {c}'
    elif re.match(r'^§(.*) bullet "(.*)"$', base):
        sec, st = re.match(r'^§(.*) bullet "(.*)"$', base).groups()
        for ln in md_section_lines(src['text'], sec):
            t = ln.strip()
            if t.startswith('- ') and t[2:].startswith(st):
                txt = t[2:]
                break
        how = f'§{sec} bullet'
    elif base.endswith(' (whole section)'):
        sec = base[1:-len(' (whole section)')]
        ls = [re.sub(r'^\s*-\s+', '', x).strip() for x in md_section_lines(src['text'], sec) if x.strip()]
        txt = ' '.join(ls)
        how = 'whole section'
    elif base.endswith(' first paragraph'):
        sec = base[1:-len(' first paragraph')]
        for x in md_section_lines(src['text'], sec):
            if x.strip():
                txt = x.strip()
                break
        how = 'first paragraph'
    elif base.startswith('sentence containing'):
        ph = re.findall(r'"([^"]*)"', base)
        hits = sentences_with(src['text'].replace('\n', ' '), ph)
        txt = ' '.join(hits) if hits else None
        how = 'sentence containing (whole file)'
    if txt is None:
        # fall back: verbatim containment anywhere in the file
        if isinstance(val, str) and text_contains(src['text'], val):
            r.update(ok=True, why='locator not re-resolved; value verbatim in file', source_value=None, how='file containment')
            return r
        r.update(ok=False if isinstance(val, str) else None, why=f'locator not resolved: {k[:120]}', how=how)
        return r
    if phrases and isinstance(txt, str):
        hits = sentences_with(txt, phrases)
        if hits:
            txt = ' '.join(hits)
    sv, ok, why = compare_text_or_num(val, txt, regex)
    r.update(source_value=sv if not isinstance(sv, str) or len(sv) < 400 else sv[:400] + ' ...', ok=ok, why=why, how=how)
    return r


# ------------------------------------------------------------------ JSON locators
def resolve_json(S, sid, key, entry):
    src = S.load(sid)
    r = {'kind': 'JSON'}
    if src['data'] is None:
        r.update(ok=None, why='json not loaded')
        return r
    k = key or ''
    regex = None
    mm = re.match(r'^(\S*) \[regex (.*)\]$', k)
    if mm:
        k, regex = mm.group(1), mm.group(2)
    if '*' in k:
        if sid == 'MAN' and k == '/instances/*/bounds_mm':
            return recompute_man(src['data'], entry, r)
        r.update(ok=None, why='wildcard pointer (generator aggregate); see recompute', how='wildcard')
        return r
    try:
        node = ptr_get(src['data'], k)
    except Exception as e:  # noqa
        if entry.get('value') is None:
            r.update(ok=None, why=f'pointer not found and the trace records the value as {entry.get("status") or "MISSING"} '
                                  f'(consistent; an unknown, not a mismatch)', source_value=None)
        else:
            r.update(ok=False, why=f'pointer not found: {type(e).__name__}', source_value=None)
        return r
    tag = None
    if isinstance(node, dict) and 'v' in node:
        tag = node.get('tag')
        node = node['v']
    val = entry.get('value')
    r['source_tag'] = tag if tag is None or len(str(tag)) < 300 else str(tag)[:300] + ' ...'
    if regex:
        m = re.search(regex, str(node))
        if not m:
            r.update(ok=False, why=f'regex {regex!r} not matched', source_value=None)
            return r
        sv = float(m.group(1))
        sv2, conv = apply_conv(sv, entry.get('note'))
        r.update(source_value=sv2, ok=num_eq(sv2, val), why='regex' + (f' conv {conv}' if conv else ''))
        return r
    if is_num(node):
        sv2, conv = apply_conv(node, entry.get('note'))
        r.update(source_value=sv2, ok=num_eq(sv2, val), why='number' + (f' conv {conv}' if conv else ''))
        return r
    if isinstance(node, list) and isinstance(val, list):
        if all(is_num(a) for a in node) and all(is_num(b) for b in val) and len(node) == len(val):
            note = entry.get('note') or ''
            conv_vals = [apply_conv(a, note)[0] for a in node]
            r.update(source_value=conv_vals, ok=all(num_eq(a, b) for a, b in zip(conv_vals, val)), why='list of numbers')
            return r
        r.update(source_value=node, ok=(node == val), why='list equality')
        return r
    if isinstance(node, str) and isinstance(val, str):
        ok = strip_md(node) == strip_md(val) or text_contains(node, val)
        r.update(source_value=node if len(node) < 400 else node[:400] + ' ...', ok=ok,
                 why='text equal' if strip_md(node) == strip_md(val) else ('text contained' if ok else 'text differs'))
        return r
    if isinstance(node, bool) or node is None:
        r.update(source_value=node, ok=(node == val), why='scalar equality')
        return r
    if isinstance(val, str):
        js = json.dumps(node, ensure_ascii=False)
        ok = text_contains(js, val) or strip_md(js) == strip_md(val)
        if ok:
            r.update(source_value=js[:400], ok=True, why='json dump contains value')
            return r
        # a composed display string (e.g. 'PN: name'): every word of the value must occur in the node
        words = [w for w in re.findall(r'[A-Za-z0-9][A-Za-z0-9.\-+/]{2,}', WITHHELD_RE.sub(' ', val))]
        miss = [w for w in words if w not in js]
        r.update(source_value=js[:400], ok=(not miss) if words else False,
                 why=('composed string: all %d words found in the node (weak check)' % len(words)) if not miss
                 else ('composed string: words not in node: ' + ', '.join(miss[:8])))
        return r
    r.update(source_value=str(node)[:400], ok=(node == val), why='generic equality')
    return r


def recompute_man(data, entry, r):
    """Independent recompute of the generator's assembly-manifest extents (union of instance bounds)."""
    tag = entry.get('tag_raw') or ''
    note = (entry.get('note') or '').strip()
    mg = re.search(r'\(group = ([^)]+)\)', tag)
    mp = re.search(r'instance prefix ([^)\s]+)', tag)
    group = mg.group(1).strip() if mg else None
    pfx = mp.group(1).strip() if mp else None
    lo, hi, n = [1e9] * 3, [-1e9] * 3, 0
    for it in data.get('instances', []):
        if group and it.get('group') != group:
            continue
        if pfx and not str(it.get('inst', '')).startswith(pfx):
            continue
        b = it['bounds_mm']
        for kk in range(3):
            lo[kk] = min(lo[kk], b[kk])
            hi[kk] = max(hi[kk], b[kk + 3])
        n += 1
    calc = {'overall z extent': hi[2] - lo[2], 'z of the forward end (pivot at z 0)': hi[2],
            'distance pivot to aft end': -lo[2], 'x extent': hi[0] - lo[0], 'y extent': hi[1] - lo[1],
            'z extent': hi[2] - lo[2], 'z range': [lo[2], hi[2]]}
    if note not in calc or n == 0:
        r.update(ok=None, why=f'wildcard aggregate {note!r} not recomputed', how='wildcard')
        return r
    sv = calc[note]
    val = entry.get('value')
    if isinstance(sv, list):
        ok = isinstance(val, list) and len(val) == 2 and all(num_eq(a, b) for a, b in zip(sv, val))
    else:
        ok = num_eq(sv, val)
    r.update(source_value=sv, ok=ok, why=f'recomputed {note} over {n} instances' + (f' (group {group})' if group else ''),
             how='recompute')
    return r


# ------------------------------------------------------------------ dispatcher
def resolve(S, entry):
    sid = entry.get('source')
    key = entry.get('key')
    info = S.info(sid) if sid else None
    res = {'sid': sid, 'key': key}
    if sid in (None, 'generator'):
        res.update(kind='GEN', ok=None, why='generator value: formula ' + str(entry.get('formula'))[:160],
                   inputs=entry.get('inputs'))
        return res
    if info is None:
        res.update(kind='?', ok=False, why=f'source id {sid} not in sources.json')
        return res
    src = S.load(sid)
    res.update(path=src['path'], sha_build=src['sha_build'], sha_now=src['sha_now'],
               sha_same=(src['sha_build'] == src['sha_now']))
    if not src['exists']:
        res.update(kind='?', ok=False, why='source file missing now')
        return res
    kind = info.get('kind')
    if sid == 'CL':
        sub = resolve_cl(S, sid, key, entry)
    elif kind == 'json':
        sub = resolve_json(S, sid, key, entry)
    elif kind in ('md', 'text', 'csv'):
        sub = resolve_md(S, sid, key, entry)
    else:
        sub = {'kind': kind, 'ok': None, 'why': f'kind {kind} not re-resolved (sha only)'}
    res.update(sub)
    return res


# ------------------------------------------------------------------ HTML displays and PDF pages
TR_RE = re.compile(r'<a class="tr" href="#(T\d+)">T\d+</a>')
BOUND_RE = re.compile(r'(<td[^>]*>|</td>|<div class="tv">|<div[^>]*class="[^"]*\b(?:tile|tl|cell)\b[^"]*"[^>]*>|<li>|<p>|</a>)')


def html_displays(html_path, appendix_marker='id="appendix-trace"'):
    t = open(html_path, encoding='utf-8', errors='replace').read()
    cut = len(t)
    for mk in (appendix_marker, 'Appendix A', 'Value trace</h'):
        i = t.find(mk)
        if i > 0:
            cut = min(cut, i) if mk != 'Appendix A' else cut
    # appendix: the last occurrence of the 'Value trace' heading
    j = t.rfind('Value trace</h')
    if j > 0:
        cut = min(cut, j)
    body = t[:cut]
    out = {}
    for m in TR_RE.finditer(body):
        tid = m.group(1)
        start = m.start()
        # walk back to a boundary
        seg_start = max(0, start - 3000)
        seg = body[seg_start:start]
        bs = [b for b in BOUND_RE.finditer(seg)]
        if bs:
            seg = seg[bs[-1].end():]
        disp = re.sub(r'<span class="ev[^"]*"[^>]*>[^<]*</span>', '', seg)
        disp = re.sub(r'<[^>]+>', '', disp)
        disp = htmlmod.unescape(disp).replace(' ', ' ').strip()
        disp = norm_ws(disp)
        out.setdefault(tid, []).append(disp[-300:])
    return out


def pdf_pages(pdf_path):
    txt = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], capture_output=True, text=True).stdout
    pages = txt.split('\f')
    if pages and not pages[-1].strip():
        pages = pages[:-1]
    app = None
    # TOC line 'Appendix A Value trace .... NN'
    for ln in (pages[1] + pages[2] + (pages[3] if len(pages) > 3 else '')).splitlines() if len(pages) > 3 else []:
        mm = re.search(r'Appendix A\s+Value trace\s+(\d+)\s*$', ln.strip())
        if mm:
            app = int(mm.group(1))
    return pages, app


def num_tokens(s):
    return [float(x.replace('−', '-')) for x in re.findall(r'[+\-−]?\d+(?:\.\d+)?', s.replace(',', ''))]


def pdf_check(tid, disp, pages, app):
    pat = re.compile(r'(?<![A-Za-z0-9])%s(?![0-9])' % re.escape(tid))
    body = []
    for i, p in enumerate(pages, 1):
        if app and i >= app:
            break
        if pat.search(p):
            body.append(i)
    shown = None
    if body and disp:
        ptxt = ' '.join(pages[i - 1] for i in body)
        P = norm_ws(ptxt.replace('−', '-').replace(' ', ' '))
        d = norm_ws(disp.replace('−', '-'))
        toks = re.findall(r'[+\-]?\d+(?:\.\d+)?', d)
        shown = all(t in P for t in toks) if toks else (d[:40] in P)
    return body, shown


def display_matches(val, disp):
    """Does the HTML display show the traced number (at its shown precision, allowing x1e-3..x1e-6,
    x100, x1000 and K->C conversions)?"""
    if not is_num(val) or not disp:
        return None
    for t in re.findall(r'[+\-−]?\d+(?:\.\d+)?(?:[eE][+\-]?\d+)?', disp.replace(',', '')):
        s = t.replace('−', '-')
        try:
            x = float(s)
        except ValueError:
            continue
        d = len(s.split('.')[1]) if '.' in s and 'e' not in s.lower() else 0
        for f, off in ((1, 0), (1e-3, 0), (1e-5, 0), (1e-6, 0), (100, 0), (1e3, 0), (1, -273.15), (1e6, 0), (1e-2, 0)):
            y = val * f + off
            if abs(round(y, d) - x) <= 0.5 * 10 ** (-d) + 1e-12:
                return True
    return False


# ------------------------------------------------------------------ main
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--trace', required=True)
    ap.add_argument('--sources', required=True)
    ap.add_argument('--html')
    ap.add_argument('--pdf')
    ap.add_argument('--ids')
    ap.add_argument('--ids-file')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--label', default='run')
    a = ap.parse_args(argv)
    T = json.load(open(a.trace, encoding='utf-8'))
    traces = {t['id']: t for t in T['traces']}
    S = Sources(a.sources)
    if a.all:
        ids = list(traces)
    elif a.ids_file:
        ids = [x.strip().split()[0] for x in open(a.ids_file) if x.strip() and not x.startswith('#')]
    else:
        ids = [x.strip() for x in (a.ids or '').split(',') if x.strip()]
    disp = html_displays(a.html) if a.html else {}
    pages, app = (pdf_pages(a.pdf) if a.pdf else ([], None))
    rows = []
    for tid in ids:
        e = traces.get(tid)
        if e is None:
            rows.append({'id': tid, 'ok': False, 'why': 'id not in trace.json'})
            continue
        r = resolve(S, e)
        d = disp.get(tid, [])
        r['id'] = tid
        r['trace_value'] = e.get('value') if not isinstance(e.get('value'), str) or len(e['value']) < 300 else e['value'][:300] + ' ...'
        r['unit'] = e.get('unit')
        r['class'] = e.get('class')
        r['masked'] = e.get('masked')
        r['display'] = d[0] if d else None
        r['n_displays'] = len(d)
        r['display_ok'] = display_matches(e.get('value'), d[0]) if d else None
        if pages:
            bp, shown = pdf_check(tid, d[0] if d else '', pages, app)
            r['pdf_pages'] = bp
            r['pdf_shown'] = shown
        rows.append(r)
    os.makedirs(a.out_dir, exist_ok=True)
    outp = os.path.join(a.out_dir, f'retrace_{a.label}.json')
    meta = {'trace': a.trace, 'trace_sha16': sha16_file(a.trace), 'sources': a.sources,
            'sources_sha16': sha16_file(a.sources), 'html': a.html, 'html_sha16': sha16_file(a.html) if a.html else None,
            'pdf': a.pdf, 'pdf_sha16': sha16_file(a.pdf) if a.pdf else None, 'appendix_page': app,
            'harness_sha16': sha16_file(os.path.abspath(__file__)), 'n': len(rows)}
    json.dump({'meta': meta, 'rows': rows}, open(outp, 'w', encoding='utf-8'), indent=1, ensure_ascii=False, default=str)
    # table
    nok = sum(1 for r in rows if r.get('ok') is True)
    nbad = sum(1 for r in rows if r.get('ok') is False)
    print(f'# {len(rows)} ids; source match {nok}; mismatch {nbad}; not compared {len(rows) - nok - nbad}; appendix p{app}')
    for r in rows:
        sv = r.get('source_value')
        sv = (str(sv)[:60] + '...') if isinstance(sv, str) and len(str(sv)) > 60 else sv
        tv = r.get('trace_value')
        tv = (str(tv)[:60] + '...') if isinstance(tv, str) and len(str(tv)) > 60 else tv
        print(f"{r['id']}\tp{r.get('pdf_pages')}\t{r.get('sid')}\t{str(r.get('key'))[:70]}\tsrc={sv}\ttrace={tv}\t"
              f"ok={r.get('ok')}\tdisp_ok={r.get('display_ok')}\tpdf_shown={r.get('pdf_shown')}\tsha_same={r.get('sha_same')}\t{r.get('why')}")
    print('wrote', outp)


if __name__ == '__main__':
    sys.exit(main())

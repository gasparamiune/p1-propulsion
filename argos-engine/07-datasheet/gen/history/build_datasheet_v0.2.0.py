#!/usr/bin/env python3
"""ARGOS H1 engine technical datasheet generator.

Reads the programme hub (interfaces, requirements, reports, reviews) and one CAD version
(BOM, mass properties, assembly manifest, GLB renders) by explicit key paths, records the
sha256/16 and version of every input, and emits a print-designed A4 HTML document plus a PDF
printed with Chromium (Playwright). No number is typed by hand: every value in a table is a
traced value (source id + JSON pointer, markdown row key or CHANGELOG line/item) with its
evidence tag, listed in the value-trace appendix and in out/trace.json.

Run with the engine venv in isolated mode, for example:
  /opt/engine-venv/bin/python -I gen/build_datasheet.py --cad-version v3.4.1
Renders must exist first (gen/render_views.sh <cad-version>).
"""
import argparse, collections, csv, datetime, glob, hashlib, html, io, json, math, os, re, shutil, subprocess, sys

GEN_NAME = 'build_datasheet.py'
GEN_VERSION = '0.2.0'
DOC_ID = 'ARGOS-H1-ENGINE-DATASHEET'
DEFAULT_HUB = '/home/claude/work/shared-fallback/engine'
DEFAULT_CAD_DIR = '/home/claude/work/mechanical/engine/03-cad'
HERE = os.path.dirname(os.path.abspath(__file__))
DS_ROOT = os.path.dirname(HERE)
G0 = 9.80665  # standard gravity, m/s2 (defined constant, not data)

EV_CLASSES = ['SIM', 'DERIVED', 'ASSUMED', 'DATASHEET', 'TO-VERIFY', 'LITERATURE', 'DESIGN', 'REQ',
              'LEAD', 'MISSING', 'TO-DEFINE', 'PENDING', 'SUPERSEDED']


# =============================================================================================
# helpers
# =============================================================================================
def sha16_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()[:16]


def sha16_text(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()[:16]


def esc(s):
    return html.escape(str(s), quote=True)


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def ptr_get(doc, ptr):
    """RFC 6901 JSON pointer ('' = whole document)."""
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


def ptr_join(*parts):
    out = ''
    for p in parts:
        out += '/' + str(p).replace('~', '~0').replace('/', '~1')
    return out


def normalise_tag(raw):
    """Map a source tag string onto the programme evidence classes."""
    if raw is None:
        return None
    t = str(raw).strip()
    u = t.upper()
    if not u:
        return None
    if u.startswith('TO-VERIFY') or u.startswith('TO-CONFIRM') or u.startswith('DATASHEET-PENDING') \
            or u.startswith('TO-CHECK'):
        return 'TO-VERIFY'
    if u.startswith('TO-DEFINE'):
        return 'TO-DEFINE'
    if u.startswith('PENDING'):
        return 'PENDING'
    if u.startswith('UNKNOWN') or u.startswith('OPEN') or u.startswith('MISSING'):
        return 'MISSING'
    if u.startswith('SIM') or u.startswith('FEA') or u.startswith('CEA'):
        return 'SIM'
    if u.startswith('DERIVED') or u.startswith('ESTIMATE'):
        return 'DERIVED'
    if u.startswith('ASSUMED'):
        return 'ASSUMED'
    if u.startswith('DATASHEET'):
        return 'DATASHEET'
    if u.startswith('LITERATURE'):
        return 'LITERATURE'
    if u.startswith('REQ'):
        return 'REQ'
    if u.startswith('LEAD') or u.startswith('[DESIGN; COMB') or 'LEAD DECISION' in u or u.startswith('COMB V2.4 / LEAD') \
            or ('/ LEAD' in u and u.startswith(('GNC', 'COMB'))):
        return 'LEAD'
    if u.startswith('DESIGN'):
        return 'DESIGN'
    if u.startswith('COMB/GNC') or u.startswith('LEAD/COMB') or u.startswith('LEAD/GNC'):
        return 'LEAD'
    if re.match(r'^(V\d|COMBUSTION\.JSON V\d|MECHANICAL\.JSON V\d|ELECTRONICS\.JSON V\d)', u):
        return 'DESIGN'
    if u.startswith('KICAD') or u.startswith('CHECK_NETLIST'):
        return 'DERIVED'
    if u.startswith('COOLPROP') or u.startswith('DS-DERIVED'):
        return 'DERIVED'   # property-library or datasheet-derived calculation
    if re.match(r'^(MECH|MECHANICAL|GNC|COMB|COMBUSTION|ELEC|ELECTRONICS)\b.*(DECISION|\d{4}-\d\d-\d\d)', u):
        return 'DESIGN'    # a specialist's dated design decision (not a lead decision)
    if re.match(r'^[\d.]+\s*\S*\s*=\s*\S', t):
        return 'DERIVED'   # tag states the conversion it was derived by ('4.75 V = 74.4 bar g ...')
    m = re.search(r'\b(SIM|DERIVED|ASSUMED|DATASHEET|LITERATURE|DESIGN|REQ|LEAD)\b', u)
    if m:
        return m.group(1)  # first class word inside a free-text tag
    return None


# =============================================================================================
# context: sources, traced values, QA
# =============================================================================================
class Source:
    def __init__(self, sid, path, role, kind, required=True):
        self.sid, self.path, self.role, self.kind, self.required = sid, path, role, kind, required
        self.exists = os.path.exists(path)
        self.sha16 = sha16_file(path) if self.exists and os.path.isfile(path) else None
        self.size = os.path.getsize(path) if self.exists and os.path.isfile(path) else None
        self.mtime = (datetime.datetime.fromtimestamp(os.path.getmtime(path), datetime.timezone.utc)
                      .strftime('%Y-%m-%dT%H:%M:%SZ') if self.exists else None)
        self.data = None
        self.text = None
        self.version = None
        if self.exists and os.path.isfile(path):
            if kind == 'json':
                self.data = json.load(open(path, encoding='utf-8'))
                if isinstance(self.data, dict):
                    self.version = self.data.get('version') or self.data.get('cad_version')
            elif kind in ('md', 'text', 'csv'):
                self.text = open(path, encoding='utf-8', errors='replace').read()
        self.reads = 0


class TV:
    """A traced value: one number or string from one source key, with its evidence tag."""

    def __init__(self, ctx, value, unit='', ev=None, tag_raw=None, sid=None, ptr=None, note='',
                 formula=None, inputs=None, status=None):
        self.ctx, self.value, self.unit = ctx, value, unit
        self.ev, self.tag_raw, self.sid, self.ptr = ev, tag_raw, sid, ptr
        self.note, self.formula, self.inputs, self.status = note, formula, inputs or [], status
        self.masked = []
        ov = getattr(ctx, 'ovr', None)
        if ov is not None:
            ov.filter_tv(self)
        self.tid = ctx.register(self)
        ctx.recent.append(self)

    # ---- formatting -----------------------------------------------------------------------
    def num(self, fmt=None):
        v = self.value
        if v is None:
            return self.status or 'MISSING'
        if isinstance(v, bool):
            return 'yes' if v else 'no'
        if isinstance(v, (int, float)):
            return fmt_num(v, fmt)
        if isinstance(v, (list, tuple)) and all(isinstance(a, (int, float)) for a in v):
            return '–'.join(fmt_num(a, fmt) for a in v) if len(v) == 2 else ', '.join(fmt_num(a, fmt) for a in v)
        return str(v)

    def pill(self):
        return ev_pill(self.ev, self.tag_raw)

    def ref(self):
        return f'<a class="tr" href="#{self.tid}">{self.tid}</a>'

    def h(self, fmt=None, unit=True, pill=True, ref=True, text_cls=''):
        if self.value is None:
            body = f'<span class="miss">{esc(self.status or "MISSING")}</span>'
        elif isinstance(self.value, str):
            body = f'<span class="txt {text_cls}">{esc(self.value)}</span>'
        else:
            body = f'<span class="v">{esc(self.num(fmt))}</span>'
            if unit and self.unit:
                body += f'<span class="u">&#8239;{esc(self.unit)}</span>'
        out = body
        if pill:
            out += ' ' + self.pill()
        if ref:
            out += self.ref()
        return out


def fmt_num(v, fmt=None):
    if fmt:
        try:
            s = format(v, fmt)
        except (ValueError, TypeError):
            s = str(v)
    else:
        if isinstance(v, int):
            s = str(v)
        else:
            a = abs(v)
            if a == 0:
                s = '0'
            elif a >= 1000:
                s = f'{v:.0f}'
            elif a >= 100:
                s = f'{v:.1f}'.rstrip('0').rstrip('.')
            else:
                s = f'{v:.4g}'
    s = s.replace('-', '−') if s.startswith('-') else s
    return s


def ev_pill(ev, tag_raw=None):
    if not ev:
        return '<span class="ev ev-none" title="no tag">UNTAGGED</span>'
    title = f' title="{esc(tag_raw)}"' if tag_raw else ''
    return f'<span class="ev ev-{ev.lower()}"{title}>{esc(ev)}</span>'


class Ctx:
    def __init__(self, args):
        self.args = args
        self.sources = {}
        self.traces = []
        self.qa = []
        self.contradictions = []
        self.unknowns = []
        self.figrefs = []
        self._n = 0
        self._keys = {}
        self.recent = []
        self.ovr = None

    # ---- sources --------------------------------------------------------------------------
    def add(self, sid, path, role, kind='json', required=True):
        s = Source(sid, path, role, kind, required)
        self.sources[sid] = s
        if not s.exists:
            self.issue('ERROR' if required else 'WARN', f'source {sid} missing: {path}')
        return s

    def src(self, sid):
        return self.sources[sid]

    def raw(self, sid, ptr, default=KeyError):
        s = self.sources.get(sid)
        if s is None or s.data is None:
            if default is KeyError:
                raise KeyError(f'{sid} not loaded')
            return default
        try:
            s.reads += 1
            return ptr_get(s.data, ptr)
        except (KeyError, IndexError, ValueError, TypeError):
            if default is KeyError:
                raise
            return default

    def register(self, tv):
        key = None
        if tv.sid is not None and tv.ptr is not None and tv.formula is None:
            key = (tv.sid, tv.ptr, json.dumps(tv.value, sort_keys=True, default=str), tv.unit, tv.ev, tv.tag_raw, tv.note, tv.status)
            if key in self._keys:
                return self._keys[key]
        self._n += 1
        tid = f'T{self._n:03d}'
        self.traces.append(tv)
        if key is not None:
            self._keys[key] = tid
        return tid

    def issue(self, level, msg):
        self.qa.append({'level': level, 'msg': msg})

    # ---- traced value constructors --------------------------------------------------------
    def v(self, sid, ptr, unit='', conv=None, tag=None, tag_ptr=None, note='', fmt_hint=None, tag_default=None):
        """Value at a JSON pointer. A {v, tag} node yields v and its tag. Unit conversions are
        explicit and recorded (conv = (factor, offset, 'text'))."""
        try:
            node = self.raw(sid, ptr)
        except (KeyError, IndexError, ValueError, TypeError):
            self.issue('WARN', f'missing key {sid}:{ptr}')
            tv = TV(self, None, unit, 'MISSING', None, sid, ptr, note=note or 'key not found', status='MISSING')
            self.unknowns.append({'what': f'{sid}:{ptr}', 'status': 'MISSING', 'tid': tv.tid})
            return tv
        tag_raw = None
        val = node
        if isinstance(node, dict) and 'v' in node:
            val = node['v']
            tag_raw = node.get('tag')
        if tag_ptr is not None and (tag_raw is None or str(tag_raw).strip().lower().startswith('see ')):
            t = self.raw(sid, tag_ptr, default=None)
            if isinstance(t, dict):
                t = t.get('tag')
            tag_raw = t if t is not None else tag_raw
        if tag is not None:
            ev = tag
            if tag_raw is None:
                tag_raw = f'(class set by generator: {tag})'
        else:
            ev = normalise_tag(tag_raw)
            if ev is None and tag_raw is None and tag_default is not None:
                ev, tag_raw = tag_default, f'(no source tag; class set by generator: {tag_default})'
            if ev is None:
                self.issue('WARN', f'unmapped evidence tag at {sid}:{ptr}: {str(tag_raw)[:80]!r}')
        if conv is not None and isinstance(val, (int, float)) and not isinstance(val, bool):
            f, off, why = conv
            val = val * f + off
            note = (note + '; ' if note else '') + f'display = raw x {f:g}{" + " + format(off, "g") if off else ""} ({why})'
        elif conv is not None and isinstance(val, list) and all(isinstance(a, (int, float)) for a in val):
            f, off, why = conv
            val = [a * f + off for a in val]
            note = (note + '; ' if note else '') + f'display = raw x {f:g} ({why})'
        return TV(self, val, unit, ev, tag_raw, sid, ptr, note=note)

    def d(self, value, unit, formula, inputs, ev='DERIVED', note=''):
        """Value computed by this generator from traced inputs."""
        return TV(self, value, unit, ev, f'DERIVED by {GEN_NAME}: {formula}', 'generator', None,
                  note=note, formula=formula, inputs=[i.tid for i in inputs if isinstance(i, TV)])

    def t(self, sid, ptr, text, ev, tag_raw=None, note=''):
        """A text value from a non-JSON source (markdown row, CHANGELOG item) with its locator."""
        return TV(self, text, '', ev, tag_raw, sid, ptr, note=note)

    def missing(self, what, status='MISSING', note=''):
        tv = TV(self, None, '', status, None, None, None, note=note or what, status=status)
        self.unknowns.append({'what': what, 'status': status, 'tid': tv.tid, 'note': note})
        return tv

    def contra(self, cid, title, sides, newest, resolution):
        """sides: list of (label, TV); newest: label of the side shown as current."""
        self.contradictions.append({'id': cid, 'title': title, 'sides': sides, 'newest': newest,
                                    'resolution': resolution})


# =============================================================================================
# markdown and CHANGELOG readers (explicit keys: table row id, section heading, line/item)
# =============================================================================================
def md_table_rows(text, section_prefix=None):
    """Rows of the markdown tables in a section (heading line starting with section_prefix)."""
    lines = text.splitlines()
    in_sec = section_prefix is None
    rows = []
    for ln in lines:
        if ln.startswith('#'):
            if section_prefix is not None:
                in_sec = ln.lstrip('#').strip().startswith(section_prefix)
            continue
        if in_sec and ln.startswith('|') and not re.match(r'^\|\s*-', ln):
            cells = [c.strip() for c in ln.strip().strip('|').split(' | ')]
            rows.append(cells)
    return rows


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


def md_inline(s):
    """Minimal markdown inline rendering for quoted source text (bold, code)."""
    s = esc(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'`(.+?)`', r'<code>\1</code>', s)
    return s


class Changelog:
    def __init__(self, ctx, sid):
        self.ctx, self.sid = ctx, sid
        self.lines = ctx.src(sid).text.splitlines() if ctx.src(sid).text else []

    def line(self, n):
        raw = self.lines[n - 1]
        parts = raw.split(' | ')
        rec = {'n': n, 'raw': raw, 'sha16': sha16_text(raw)}
        if len(parts) >= 4 and re.match(r'^\d{4}-\d\d-\d\d$', parts[0]):
            rec.update(date=parts[0], owner=parts[1], what=parts[2], text=' | '.join(parts[3:-1]) if len(parts) > 4 else parts[3],
                       why=parts[-1] if len(parts) > 4 else '')
        else:
            rec.update(date=None, owner=None, what=None, text=raw, why='')
        return rec

    def items(self, n):
        """Split a decision text into its numbered items (1), (2), ... in sequence. A split needs the
        expected next number and a preceding sentence/clause boundary, so 'item (2) of' is not one."""
        text = self.line(n)['text']
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

    def item(self, n, k, sentence=None, contains=None):
        rec = self.line(n)
        its = self.items(n)
        ptr = f'L{n}({k})'
        if k not in its:
            self.ctx.issue('WARN', f'CHANGELOG line {n} has no item ({k})')
            return self.ctx.missing(f'CHANGELOG L{n} item ({k})')
        txt = re.sub(r'^\(%d\)\s*' % k, '', its[k])
        if contains:
            sents = re.split(r'(?<=[.;])\s+(?=[A-Z(])', txt)
            hit = [s for s in sents if contains.lower() in s.lower()]
            if hit:
                txt = ' '.join(hit)
                ptr += f'[sentence containing "{contains}"]'
        ev = 'LEAD' if rec.get('owner') == 'lead' else (normalise_tag(rec.get('owner')) or 'DERIVED')
        return self.ctx.t(self.sid, ptr, txt, ev, tag_raw=f"{rec.get('owner')} {rec.get('what')} {rec.get('date')} (line sha {rec['sha16']})")

    def whole(self, n, maxlen=None):
        rec = self.line(n)
        txt = rec['text'] if maxlen is None or len(rec['text']) <= maxlen else rec['text'][:maxlen].rsplit(' ', 1)[0] + ' …'
        ev = 'LEAD' if rec.get('owner') == 'lead' else 'DERIVED'
        if rec.get('what') == '(result)' and rec.get('owner') in ('gnc', 'combustion', 'electronics', 'mechanical'):
            ev = 'SIM'
        return self.ctx.t(self.sid, f'L{n}', txt, ev, tag_raw=f"{rec.get('owner')} {rec.get('what')} {rec.get('date')} (line sha {rec['sha16']})")

    def find(self, needle, owner='lead', what='(decision)'):
        """Line number of the newest entry by owner/what whose text contains needle (None if absent)."""
        for i in range(len(self.lines), 0, -1):
            rec = self.line(i)
            if rec.get('owner') == owner and rec.get('what') == what and needle in rec['text']:
                return i
        return None

    def part(self, n, contains=None):
        """Decision text of a line (no numbered items needed), or its sentences containing a phrase."""
        rec = self.line(n)
        txt, ptr = rec['text'], f'L{n}'
        if contains:
            phr = [contains] if isinstance(contains, str) else list(contains)
            sents = re.split(r'(?<=[.;])\s+(?=[A-Z(])', txt)
            hit = [x for x in sents if any(p.lower() in x.lower() for p in phr)]
            if not hit:
                self.ctx.issue('WARN', f'CHANGELOG line {n}: no sentence containing {contains!r}')
                return self.ctx.missing(f'CHANGELOG L{n} sentence containing {" | ".join(phr)}')
            txt = ' '.join(hit)
            ptr += '[sentence containing ' + ' | '.join(f'"{p}"' for p in phr) + ']'
        ev = 'LEAD' if rec.get('owner') == 'lead' else (normalise_tag(rec.get('owner')) or 'DERIVED')
        if rec.get('what') == '(result)' and rec.get('owner') in ('gnc', 'combustion', 'electronics', 'mechanical'):
            ev = 'SIM'   # same rule as whole(): a specialist's result line
        return self.ctx.t(self.sid, ptr, txt, ev, tag_raw=f"{rec.get('owner')} {rec.get('what')} {rec.get('date')} (line sha {rec['sha16']})")

    def decisions(self, owner='lead', last=None):
        out = []
        for i in range(1, len(self.lines) + 1):
            rec = self.line(i)
            if rec.get('owner') == owner and rec.get('what') == '(decision)':
                out.append(rec)
        return out[-last:] if last else out


# =============================================================================================
# HTML building blocks
# =============================================================================================
def table(headers, rows, cls='', widths=None, caption=None):
    h = [f'<table class="{cls}">']
    if caption:
        h.append(f'<caption>{caption}</caption>')
    if widths:
        h.append('<colgroup>' + ''.join(f'<col style="width:{w}">' for w in widths) + '</colgroup>')
    h.append('<thead><tr>' + ''.join(f'<th>{c}</th>' for c in headers) + '</tr></thead><tbody>')
    for r in rows:
        if isinstance(r, str):
            h.append(r)
            continue
        h.append('<tr>' + ''.join(f'<td>{c}</td>' for c in r) + '</tr>')
    h.append('</tbody></table>')
    return '\n'.join(h)


def kv_rows(items):
    """[(label, TV or html)] -> rows for a 2-column table."""
    rows = []
    for lab, val in items:
        rows.append([lab, val.h() if isinstance(val, TV) else val])
    return rows


def note_box(text, kind='info'):
    return f'<div class="box box-{kind}">{text}</div>'


def pres(ctx, tv_pa, digits=2):
    """'2.50 MPa (25.0 bar)' from a Pa-valued TV (both shown; bar matches the decision records)."""
    if tv_pa.value is None:
        return tv_pa.h()
    mpa = tv_pa.value / 1e6
    bar = tv_pa.value / 1e5
    return (f'<span class="v">{fmt_num(mpa, f".{digits}f")}</span><span class="u">&#8239;MPa</span> '
            f'<span class="alt">({fmt_num(bar, ".1f")} bar)</span> {tv_pa.pill()}{tv_pa.ref()}')


def pres_bar(ctx, tv_bar, digits=1):
    if tv_bar.value is None:
        return tv_bar.h()
    v = tv_bar.value
    if isinstance(v, list):
        return (f'<span class="v">{"–".join(fmt_num(a / 10, ".2f") for a in v)}</span><span class="u">&#8239;MPa</span> '
                f'<span class="alt">({"–".join(fmt_num(a, f".{digits}f") for a in v)} bar)</span> {tv_bar.pill()}{tv_bar.ref()}')
    return (f'<span class="v">{fmt_num(v / 10, ".3f")}</span><span class="u">&#8239;MPa</span> '
            f'<span class="alt">({fmt_num(v, f".{digits}f")} bar)</span> {tv_bar.pill()}{tv_bar.ref()}')


def temp_k(tv_k, digits=1):
    if tv_k.value is None:
        return tv_k.h()
    v = tv_k.value
    if isinstance(v, list):
        return (f'<span class="v">{"–".join(fmt_num(a, f".{digits}f") for a in v)}</span><span class="u">&#8239;K</span> '
                f'<span class="alt">({"–".join(fmt_num(a - 273.15, ".0f") for a in v)} °C)</span> {tv_k.pill()}{tv_k.ref()}')
    return (f'<span class="v">{fmt_num(v, f".{digits}f")}</span><span class="u">&#8239;K</span> '
            f'<span class="alt">({fmt_num(v - 273.15, ".0f")} °C)</span> {tv_k.pill()}{tv_k.ref()}')


def short_name(name, maxlen=44):
    s = name
    cut = len(s)
    for sep in [':', ' (', ', ', ' - ', ' – ']:
        i = s.find(sep)
        if 4 <= i < cut:
            cut = i
    s = s[:cut].strip()
    return s if len(s) <= maxlen else s[:maxlen - 1].rstrip() + '…'


def short_mat(material_name, code):
    if not material_name:
        return code
    s = material_name
    for sep in [',', ' (']:
        i = s.find(sep)
        if i > 3:
            s = s[:i]
    if code == 'COTS-MIXED':
        return 'COTS assembly'
    return s.strip()[:38]


FAMILY_NAMES = {  # display names for BOM part-number families (text labels only)
    'TC': 'Thrust chamber', 'GR': 'Fuel grain', 'NZ': 'Nozzle and joint', 'PD': 'Pintle drive',
    'IG': 'Igniter', 'FD': 'Oxidiser feed', 'FS': 'Main valve module (fixed)', 'GM': 'Gimbal and thrust frame',
    'HW': 'Bearings and hardware', 'EL': 'Sensors and encoders', 'BL': 'Head-end bleed (provision)',
}
GROUP_NAMES = {'engine': 'gimballed engine', 'ring': 'gimbal ring', 'horn': 'TVC horns', 'pushrod': 'TVC pushrods',
               'fixed': 'fixed module (thrust frame, MV module, servos)', 'all': 'total'}
SECTION_CALLOUTS = ['ENG-FS-10', 'ENG-FS-01A', 'ENG-PD-13', 'ENG-PD-04', 'ENG-IG-01', 'ENG-TC-04', 'ENG-TC-05',
                    'ENG-TC-02', 'ENG-FD-01', 'ENG-FD-03', 'ENG-TC-06', 'ENG-TC-01', 'ENG-GM-09', 'ENG-GM-03',
                    'ENG-FD-07', 'ENG-GR-01', 'ENG-GR-02', 'ENG-TC-07', 'ENG-GM-10', 'ENG-TC-08', 'ENG-TC-09',
                    'ENG-NZ-01', 'ENG-NZ-02', 'ENG-GM-15']


def family_of(pn):
    p = pn.split('-')
    return p[1] if len(p) > 2 else p[0]


# =============================================================================================
# traced table cells and the structural trace check
# =============================================================================================
class Cell:
    """Table cell: html plus the traced values it shows (traced = at least one TV)."""

    def __init__(self, html_, tvs=(), cls=''):
        self.html, self.tvs, self.cls = html_, [t for t in tvs if isinstance(t, TV)], cls


CELL_STATS = {'data_cells': 0, 'traced': 0, 'untraced': []}


def as_cell(c):
    if isinstance(c, Cell):
        return c
    if isinstance(c, TV):
        return Cell(c.h(), [c])
    return Cell('' if c is None else str(c), [])


def dtable(headers, rows, label_cols=1, cls='', widths=None, caption=None, tid=None, free_cols=()):
    """Data table. Columns >= label_cols must hold traced cells (TV or Cell with TVs); plain
    strings there are counted as untraced in the QA report. A str row is inserted verbatim
    (group sub-header)."""
    h = [f'<table class="dt {cls}"' + (f' id="{tid}"' if tid else '') + '>']
    if caption:
        h.append(f'<caption>{caption}</caption>')
    if widths:
        h.append('<colgroup>' + ''.join(f'<col style="width:{w}">' for w in widths) + '</colgroup>')
    h.append('<thead><tr>' + ''.join(f'<th>{c}</th>' for c in headers) + '</tr></thead><tbody>')
    for r in rows:
        if isinstance(r, str):
            h.append(r)
            continue
        tds = []
        for j, c in enumerate(r):
            cc = as_cell(c)
            vis = re.sub('<[^>]+>', '', cc.html).strip()
            if j >= label_cols and j not in free_cols and vis not in ('', '—', '–'):
                CELL_STATS['data_cells'] += 1
                if cc.tvs or 'class="tr"' in cc.html:
                    CELL_STATS['traced'] += 1
                else:
                    CELL_STATS['untraced'].append({'table': caption or (headers[0] if headers else '?'),
                                                   'col': headers[j] if j < len(headers) else j,
                                                   'text': re.sub('<[^>]+>', '', cc.html)[:60]})
            tds.append(f'<td class="{cc.cls}">{cc.html}</td>' if cc.cls else f'<td>{cc.html}</td>')
        h.append('<tr>' + ''.join(tds) + '</tr>')
    h.append('</tbody></table>')
    return '\n'.join(h)


def subrow(text, ncol):
    return f'<tr class="sub"><td colspan="{ncol}">{text}</td></tr>'


def cat(*parts):
    """Concatenate traced cells into one Cell (keeps every TV)."""
    hs, tvs = [], []
    for p in parts:
        if isinstance(p, TV):
            hs.append(p.h())
            tvs.append(p)
        elif isinstance(p, Cell):
            hs.append(p.html)
            tvs += p.tvs
        else:
            hs.append(str(p))
    return Cell(''.join(hs), tvs)


def tvtxt(tv, maxlen=None, cls='', ovr=True):
    """Long source text as a traced cell (markdown-inline rendered, optional truncation). Active
    decision overrides (gen/decision_overrides.json) are applied here: stale wording struck through,
    the decision inserted with its override id."""
    if tv.value is None:
        return Cell(tv.h(), [tv])
    s = tv.value if isinstance(tv.value, str) else readable(tv.value)
    ov = getattr(tv.ctx, 'ovr', None)
    if ov is not None and ovr:
        c = ov.render(tv, s, cls, annot_only=(ovr == 'annot'))
        if c is not None:
            return c
    if maxlen and len(s) > maxlen:
        s = s[:maxlen].rsplit(' ', 1)[0] + ' …'
    return Cell(f'<span class="qt {cls}">{md_inline(s)}</span> {tv.pill()}{tv.ref()}', [tv])


def readable(v):
    """Compact text for a structured value: 'key: value; ...' for a dict, 'a; b' for a list of strings."""
    if isinstance(v, dict):
        return '; '.join(f'{k}: {readable(x) if isinstance(x, (dict, list)) else (x if isinstance(x, str) else json.dumps(x))}' for k, x in v.items())
    if isinstance(v, list) and all(isinstance(x, str) for x in v):
        return '; '.join(v)
    return json.dumps(v, ensure_ascii=False)


def num_cell(tv, fmt=None, unit=True):
    return Cell(tv.h(fmt=fmt, unit=unit), [tv])


# =============================================================================================
# fonts: TrueType copies of the installed Inter OpenType-CFF fonts (Chromium embeds CFF as Type 3)
# =============================================================================================
FONT_FAMILY = 'Inter DS'
FONT_SRC_DIR = '/usr/share/fonts/opentype/inter'
FONT_STYLES = ['Regular', 'SemiBold', 'Bold', 'ExtraBold']


def otf_to_ttf(src, dst, family):
    """CFF outlines to quadratic TrueType outlines (fontTools cu2qu, max error 1 unit), family renamed."""
    from fontTools.ttLib import TTFont, newTable
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    f = TTFont(src)
    order = f.getGlyphOrder()
    gs = f.getGlyphSet()
    quad = {}
    for g in order:
        pen = TTGlyphPen(gs)
        gs[g].draw(Cu2QuPen(pen, 1.0, reverse_direction=True))
        quad[g] = pen.glyph()
    f['loca'] = newTable('loca')
    f['glyf'] = glyf = newTable('glyf')
    glyf.glyphOrder = order
    glyf.glyphs = quad
    del f['CFF ']
    if 'VORG' in f:
        del f['VORG']
    glyf.compile(f)
    hmtx = f['hmtx']
    for gname, g in glyf.glyphs.items():
        if hasattr(g, 'xMin'):
            hmtx[gname] = (hmtx[gname][0], g.xMin)
    f['maxp'] = maxp = newTable('maxp')
    maxp.tableVersion = 0x00010000
    for k in ('maxZones', ):
        setattr(maxp, k, 1)
    for k in ('maxTwilightPoints', 'maxStorage', 'maxFunctionDefs', 'maxInstructionDefs', 'maxStackElements', 'maxSizeOfInstructions'):
        setattr(maxp, k, 0)
    maxp.maxComponentElements = max(len(getattr(g, 'components', []) or []) for g in glyf.glyphs.values())
    maxp.compile(f)
    post = f['post']
    post.formatType, post.extraNames, post.mapping, post.glyphOrder = 2.0, [], {}, order
    try:
        post.compile(f)
    except OverflowError:
        post.formatType = 3
    f.sfntVersion = '\000\001\000\000'
    style = os.path.basename(src).rsplit('-', 1)[-1].split('.')[0]
    ribbi = style in ('Regular', 'Bold', 'Italic', 'BoldItalic')
    for rec in f['name'].names:
        if rec.nameID == 1:
            rec.string = family if ribbi else f'{family} {style}'   # legacy family (non-RIBBI weights carry the style)
        elif rec.nameID in (16, 21):
            rec.string = family                                     # typographic and WWS family
        elif rec.nameID == 4:
            rec.string = f'{family} {style}'
        elif rec.nameID == 6:
            rec.string = f'{family.replace(" ", "")}-{style}'
        elif rec.nameID == 3:
            rec.string = f'{family.replace(" ", "")}-{style};datasheet build copy'
    f.save(dst)


def ensure_fonts(ctx, a):
    """Builds (once) build/fonts/InterDS-*.ttf and build/fonts.conf; returns the family name or None."""
    fdir = os.path.join(a.build, 'fonts')
    os.makedirs(fdir, exist_ok=True)
    made = []
    try:
        for st in FONT_STYLES:
            src = os.path.join(FONT_SRC_DIR, f'Inter-{st}.otf')
            dst = os.path.join(fdir, f'InterDS-{st}.ttf')
            if not os.path.exists(src):
                raise FileNotFoundError(src)
            if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
                otf_to_ttf(src, dst, FONT_FAMILY)
            made.append(dst)
    except Exception as e:  # the system Inter (CFF, embedded as Type 3) is the fallback
        ctx.issue('WARN', f'TrueType font copies not built ({e}); the PDF uses the installed OpenType Inter')
        return None
    conf = os.path.join(a.build, 'fonts.conf')
    open(conf, 'w').write('<?xml version="1.0"?>\n<!DOCTYPE fontconfig SYSTEM "fonts.dtd">\n<fontconfig>\n'
                          f'  <cachedir>{esc(os.path.join(a.build, "fontcache"))}</cachedir>\n'
                          '  <include ignore_missing="yes">/etc/fonts/fonts.conf</include>\n'
                          f'  <dir>{esc(fdir)}</dir>\n</fontconfig>\n')
    a.fontconf = conf
    a.fonts = made
    return FONT_FAMILY


# =============================================================================================
# decision overrides (gen/decision_overrides.json): lead decisions not yet carried by combustion.json
# =============================================================================================
NUM_TOKEN = re.compile(r'(?<![A-Za-z\d.])\d+(?:\.\d+)?(?![A-Za-z\d])')
SRC_FILE = {'CMB': 'combustion.json', 'REQ': 'REQUIREMENTS.md', 'ICD': 'ICD-AIRFRAME.md', 'CL': 'CHANGELOG.md',
            'ELE': 'electronics.json', 'GNC': 'gnc.json', 'MEC': 'mechanical.json', 'FA1': 'fa1_envelope_v2p4a.json'}


def num_in(tok, text):
    return re.search(r'(?<!\d)(?<!\d\.)' + re.escape(tok) + r'(?!\d|\.\d)', text) is not None


def sentence_with(text, contains):
    sents = re.split(r'(?<=[.;])\s+(?=[A-Z(])', text)
    hit = [x for x in sents if contains.lower() in x.lower()]
    return ' '.join(hit) if hit else None


def flat_keys(x, ptr=''):
    out = []
    if isinstance(x, dict):
        for k, v in x.items():
            p = ptr + '/' + str(k).replace('~', '~0').replace('/', '~1')
            out.append(p)
            out += flat_keys(v, p)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            out += flat_keys(v, f'{ptr}/{i}')
    return out


class Overrides:
    """Decision override table. Entries are applied only while their stale wording is present in
    the target; every entry's numbers and 'verify' strings are checked against the cited sources."""

    def __init__(self, ctx, path):
        self.ctx, self.path = ctx, path
        self.entries, self.sups = [], []
        self.by_target = {}
        self.withheld = {}
        self.annots = []
        self.mask_hits = collections.Counter()
        self.version = None

    # ---- loading ---------------------------------------------------------------------------
    def load(self, D):
        ctx = self.ctx
        src = ctx.sources.get('OVR')
        if src is None or src.data is None:
            ctx.issue('WARN', 'decision override table not loaded: combustion.json wording shown as published')
            return
        d = src.data
        self.version = d.get('version')
        sup_keys = list((ctx.raw('CMB', '/superseded_v2p4/v', default={}) or {}).keys())
        for k, e in enumerate(d.get('suppress', [])):
            rec = {'id': e['id'], 'k': k, 'topic': e.get('topic', ''), 'replacement': e.get('replacement', ''),
                   'basis': e.get('basis', ''), 'patterns': [re.compile(p) for p in e.get('patterns', [])],
                   'pointers': [], 'corroborated': None}
            if e.get('corroborate_re'):
                rec['corroborated'] = any(re.search(e['corroborate_re'], key) for key in sup_keys)
                if not rec['corroborated']:
                    ctx.issue('WARN', f'{e["id"]}: not corroborated by combustion.json /superseded_v2p4')
            for p in e.get('pointers', []):
                v = ctx.raw(p['sid'], p['ptr'], default=None)
                vv = v.get('v') if isinstance(v, dict) and 'v' in v else v
                txt = vv if isinstance(vv, str) else json.dumps(vv, ensure_ascii=False)
                live = vv is not None and any(r_.search(txt) for r_ in rec['patterns'])
                rec['pointers'].append({'sid': p['sid'], 'ptr': p['ptr'], 'status': 'WITHHELD' if live else ('NOT FOUND' if vv is None else 'REDUNDANT')})
                if live:
                    self.withheld[(p['sid'], p['ptr'])] = e['id']
            self.sups.append(rec)
        for k, e in enumerate(d.get('overrides', [])):
            rec = {'id': e['id'], 'k': k, 'topic': e.get('topic', ''), 'value': e.get('value', ''), 'short': e.get('short'),
                   'basis': e.get('basis', ''), 'srcs': [], 'targets': [], 'errors': [], 'annot': None}
            texts = []
            for sp in e.get('sources', []):
                tv = self.resolve_source(sp, D)
                rec['srcs'].append(tv)
                txt = tv.value if isinstance(tv.value, str) else (json.dumps(tv.value, ensure_ascii=False) if tv.value is not None else '')
                if not txt:
                    rec['errors'].append(f'source not found: {self.loc(sp)}')
                for vs in sp.get('verify', []):
                    if txt and vs not in txt:
                        rec['errors'].append(f'{self.loc(sp)} does not contain "{vs}"')
                texts.append(txt)
            allt = '\n'.join(texts)
            for fld in ('value', 'short'):
                for tok in NUM_TOKEN.findall(rec[fld] or ''):
                    if not num_in(tok, allt):
                        rec['errors'].append(f'number {tok} in "{fld}" is not in the cited sources')
            for t in e.get('targets', []):
                cur = self.target_text(t, D)
                if cur is None:
                    st = 'NOT FOUND'
                elif t.get('stale_re'):
                    st = 'ACTIVE' if re.search(t['stale_re'], cur) else 'REDUNDANT'
                else:
                    st = 'ACTIVE' if not re.search(t['absent_re'], cur) else 'REDUNDANT'
                tt = dict(t, status=st, shown=0)
                rec['targets'].append(tt)
                if st == 'NOT FOUND':
                    ctx.issue('WARN', f'{rec["id"]}: target {t["sid"]} {t["ptr"]} not found')
                if st == 'ACTIVE' and not rec['errors']:
                    self.by_target.setdefault((t['sid'], t['ptr']), []).append((rec, tt))
            if e.get('annotate_re'):
                aw = e.get('active_while') or {}
                act = True
                if aw.get('absent_key_re'):
                    keys = flat_keys(ctx.raw(aw['sid'], '', default={}) or {})
                    act = not any(re.search(aw['absent_key_re'], key) for key in keys)
                rec['annot'] = {'re': re.compile(e['annotate_re']), 'status': 'ACTIVE' if act else 'REDUNDANT', 'shown': 0}
                if act and not rec['errors']:
                    self.annots.append(rec)
            sts = [t['status'] for t in rec['targets']] + ([rec['annot']['status']] if rec['annot'] else [])
            rec['status'] = 'ERROR' if rec['errors'] else ('ACTIVE' if 'ACTIVE' in sts else 'REDUNDANT')
            for err in rec['errors']:
                ctx.issue('ERROR', f'{rec["id"]}: {err}')
            if rec['status'] == 'REDUNDANT':
                ctx.issue('INFO', f'{rec["id"]} REDUNDANT: no target holds the stale wording any more; drop it from {os.path.basename(self.path)}')
            rec['value_tv'] = TV(ctx, rec['value'], '', 'LEAD', f'override {rec["id"]} ({self.version}); numbers and key phrases checked against the cited sources',
                                 'OVR', f'/overrides/{k}/value')
            self.entries.append(rec)
        for rec in self.sups:
            if not rec['pointers'] or all(p['status'] != 'WITHHELD' for p in rec['pointers']):
                rec['no_live_key'] = True

    @staticmethod
    def loc(sp):
        if sp.get('sid') == 'CL':
            if 'item' not in sp:
                return f'CHANGELOG decision citing "{sp.get("line_contains", "")[:40]}"' + (f' [sentence "{sp["contains"]}"]' if sp.get('contains') else '')
            return f'CHANGELOG {sp.get("line")} ({sp.get("item")})'
        if 'bullet' in sp:
            return f'{sp["sid"]} bullet "{sp["bullet"]}"'
        if 'review' in sp:
            return f'{sp["sid"]} {sp["review"]} {sp.get("field")}'
        if 'line_contains' in sp:
            return f'{sp["sid"]} line containing "{sp["line_contains"][:40]}"'
        return f'{sp.get("sid")} {sp.get("ptr")}'

    def resolve_source(self, sp, D):
        ctx = self.ctx
        sid = sp['sid']
        if sid not in ctx.sources:
            return ctx.missing(f'override source {sid} not registered')
        if sid == 'CL':
            if 'item' in sp:
                return D['cl'].item(sp['line'], sp['item'], contains=sp.get('contains'))
            n = sp.get('line') or D['cl'].find(sp.get('line_contains', '\0'))
            if n is None:
                return ctx.missing(f'CHANGELOG decision containing {sp.get("line_contains")}')
            return D['cl'].part(n, sp.get('contains'))
        if 'bullet' in sp:
            tv = md_bullet(ctx, sid, sp['section'], sp['bullet'], 'REQ' if sid == 'REQ' else 'DESIGN')
            if sp.get('contains') and isinstance(tv.value, str):
                x = sentence_with(tv.value, sp['contains'])
                if x is None:
                    return ctx.missing(f'{sid} bullet {sp["bullet"]} sentence containing {sp["contains"]}')
                return ctx.t(sid, f'{tv.ptr}[sentence containing "{sp["contains"]}"]', x, tv.ev, tag_raw=tv.tag_raw)
            return tv
        if 'review' in sp:
            sup = ctx.raw(sid, '/reviews', default=[]) or []
            i = next((j for j, r in enumerate(sup) if r.get('id') == sp['review']), None)
            if i is None:
                return ctx.missing(f'review {sp["review"]} in the register')
            lst = sup[i].get(sp['field'])
            if isinstance(lst, list):
                j = next((j for j, x in enumerate(lst) if sp.get('contains', '') in str(x)), None)
                if j is None:
                    return ctx.missing(f'{sp["review"]} {sp["field"]} entry containing {sp.get("contains")}')
                return ctx.v(sid, f'/reviews/{i}/{sp["field"]}/{j}', tag='DERIVED')
            return ctx.v(sid, f'/reviews/{i}/{sp["field"]}', tag='DERIVED')
        if 'line_contains' in sp:
            for n, ln in enumerate((ctx.src(sid).text or '').splitlines(), 1):
                if sp['line_contains'] in ln:
                    return ctx.t(sid, f'line {n}', re.sub(r'^\s*-\s+', '', ln).strip(), 'DERIVED',
                                 tag_raw=f'{sid} line {n} (independent review text)')
            return ctx.missing(f'{sid} line containing {sp["line_contains"]}')
        if 'ptr' in sp:
            p = sp['ptr']
            return ctx.v(sid, p, tag_ptr=p[:-2] if p.endswith('/v') else None)
        return ctx.missing(f'override source {sp}')

    def target_text(self, t, D):
        ctx = self.ctx
        sid, ptr = t['sid'], t['ptr']
        if sid not in ctx.sources:
            return None
        if sid == 'CL':
            m = re.match(r'^L(\d+)\((\d+)\)$', ptr)
            if not m:
                return None
            txt = D['cl'].items(int(m.group(1))).get(int(m.group(2)))
            return re.sub(r'^\(\d+\)\s*', '', txt) if txt else None
        m = re.match(r'^§(.+) row "(.+)" col (\d+)$', ptr)
        if m:
            for r in md_table_rows(ctx.src(sid).text or '', m.group(1)):
                if r and re.sub(r'\*', '', r[0]).strip() == m.group(2) and int(m.group(3)) < len(r):
                    return re.sub(r'\*\*', '', r[int(m.group(3))]).strip()
            return None
        v = ctx.raw(sid, ptr, default=None)
        if isinstance(v, dict) and 'v' in v:
            v = v['v']
        return v if isinstance(v, str) else (json.dumps(v, ensure_ascii=False) if v is not None else None)

    # ---- filtering and rendering ------------------------------------------------------------
    def mask_text(self, x):
        ids = []
        for e in self.sups:
            for r_ in e['patterns']:
                if r_.search(x):
                    x = r_.sub(f'[withheld: superseded value, {e["id"]}]', x)
                    ids.append(e['id'])
        return x, ids

    def filter_tv(self, tv):
        key = (tv.sid, tv.ptr)
        if key in self.withheld and tv.value is not None:
            sid_ = self.withheld[key]
            tv.value, tv.status, tv.ev = None, f'WITHHELD (superseded, {sid_})', 'SUPERSEDED'
            tv.masked.append(sid_)
        for attr in ('value', 'tag_raw', 'note', 'ptr'):
            v = getattr(tv, attr)
            if isinstance(v, str):
                nv, ids = self.mask_text(v)
                if ids:
                    setattr(tv, attr, nv)
                    tv.masked += ids
        if isinstance(tv.value, (list, dict)):
            nv, ids = self.mask_text(json.dumps(tv.value, ensure_ascii=False))
            if ids:
                tv.value = nv
                tv.masked += ids
        for i in tv.masked:
            self.mask_hits[i] += 1

    def _ins(self, rec, short=False):
        txt = (rec['short'] if short and rec.get('short') else rec['value'])
        return (f'<ins class="dec">{esc(txt)} <a class="ovr" href="#{esc(rec["id"])}">{esc(rec["id"])}</a></ins>')

    def render(self, tv, x, cls='', annot_only=False):
        hits = [] if annot_only else self.by_target.get((tv.sid, tv.ptr), [])
        ann = [r for r in self.annots if r['annot']['re'].search(x)]
        if not hits and not ann:
            return None
        recs = []
        rep_ = [(r, t) for r, t in hits if t['mode'] == 'replace']
        if rep_:
            r, t = rep_[0]
            t['shown'] += 1
            recs.append(r)
            body = (self._ins(r) + f'<div class="stale-src">{esc(SRC_FILE.get(tv.sid, tv.sid))} still reads: '
                    f'<del class="stale">{md_inline(x)}</del></div>')
        else:
            spans = []
            for r, t in hits:
                if t['mode'] == 'annotate':
                    m = re.search(t['stale_re'], x)
                    if m:
                        spans.append((m.start(), m.end(), r, t))
            spans.sort(key=lambda z: z[0])
            out, pos = [], 0
            for st, en, r, t in spans:
                if st < pos:
                    continue
                out.append(md_inline(x[pos:st]))
                out.append(f'<del class="stale">{md_inline(x[st:en])}</del>' + self._ins(r, short=True))
                pos = en
                t['shown'] += 1
                recs.append(r)
            out.append(md_inline(x[pos:]))
            for r, t in hits:
                if t['mode'] == 'append':
                    out.append(' ' + self._ins(r, short=True))
                    t['shown'] += 1
                    recs.append(r)
            body = ''.join(out)
        for r in ann:
            m = r['annot']['re'].search(body)
            if m:
                body = body[:m.end()] + f'<sup class="ovr-m"><a href="#{esc(r["id"])}">{esc(r["id"])}</a></sup>' + body[m.end():]
                body += f'<span class="ovr-note">{esc(r["id"])}: {esc(r.get("short") or r["value"])}</span>'
                r['annot']['shown'] += 1
                recs.append(r)
        tvs = [tv]
        for r in recs:
            tvs += [r['value_tv']] + r['srcs']
        return Cell(f'<span class="qt {cls}">{body}</span> {tv.pill()}{tv.ref()}', tvs)

    def annot_plain(self, x):
        """Plain-text form of the annotations (trace appendix, unknowns register)."""
        for r in self.annots:
            if isinstance(x, str) and r['annot']['re'].search(x):
                r['annot']['shown'] += 1
                x = f'{x} [{r["id"]}: {r.get("short") or r["value"]}]'
        return x

    def note_for(self, oid):
        """Short decided note (html, tvs) of an override for numeric cells shown outside tvtxt."""
        r = next((e for e in self.entries if e['id'] == oid), None)
        if r is None or r['status'] != 'ACTIVE':
            return None
        if r.get('annot'):
            r['annot']['shown'] += 1
        return Cell(f'<span class="ovr-note">{self._ins(r, short=True)}</span>', [r['value_tv']] + r['srcs'])


def annot_scan(ctx, pages):
    """WARN for every page where a value an override annotates appears without the override id nearby."""
    ov = getattr(ctx, 'ovr', None)
    if ov is None:
        return
    for r in ov.annots:
        for n, t in enumerate(pages, 1):
            flat = re.sub(r'\s+', ' ', t)
            for m in r['annot']['re'].finditer(flat):
                if r['id'] not in flat[max(0, m.start() - 300):m.end() + 700]:
                    ctx.issue('WARN', f'{r["id"]}: value on page {n} without the override note nearby: …{flat[max(0, m.start() - 60):m.end() + 40]!r}…')


def leak_scan(ctx, label, text):
    """ERROR for every superseded value that is visible in an output text (html, svg or pdf text)."""
    ov = getattr(ctx, 'ovr', None)
    if ov is None:
        return 0
    t = re.sub(r'<style.*?</style>', ' ', text, flags=re.S)
    n = 0
    for e in ov.sups:
        for r_ in e['patterns']:
            for m in r_.finditer(t):
                n += 1
                ctx.issue('ERROR', f'{e["id"]} superseded value visible in {label}: …{t[max(0, m.start() - 50):m.end() + 20]!r}…')
    return n


# =============================================================================================
# sources
# =============================================================================================
PLUME_FIGS = [
    ('PF-MACH', '05-plume-cfd/ownruns/f_2s_100/fig/f2s_mach_near.png', 'Mach number, near field (fine grid, v1 point)'),
    ('PF-SCHL', '05-plume-cfd/ownruns/f_2s_100/fig/f2s_schlieren_near.png', 'Numerical schlieren, near field (fine grid, v1 point)'),
    ('PF-TEMP', '05-plume-cfd/ownruns/f_2s_100/fig/f2s_T_full.png', 'Static temperature, full domain (fine grid, v1 point)'),
    ('PF-AXIS', '05-plume-cfd/ownruns/f_2s_100/fig/f2s_centreline.png', 'Centreline profiles (fine grid, v1 point)'),
    ('PF-V2MACH', '05-plume-cfd/ownruns/c_2s_100_v2op/fig/c2s_v2op_mach_near.png', 'Mach number, near field at the v2 design point (coarse grid)'),
    ('PF-ART', '05-plume-cfd/blender/final/argos_plume_artistic_side.png', 'Blender plume render (ARTISTIC)'),
]
PLUME_FIG_ALT_DIRS = ['05-plume-cfd/ownruns/f_2s_100/fig', '05-plume-cfd/ownruns/c_2s_100_v2op/fig']


def find_hub_file(hub, rel):
    p = os.path.join(hub, rel)
    if os.path.exists(p):
        return p
    base = os.path.basename(rel)
    for d in PLUME_FIG_ALT_DIRS:
        q = os.path.join(hub, d, base)
        if os.path.exists(q):
            return q
    return p


def md_version(sid, text):
    """Version string from a markdown header, by explicit per-document patterns."""
    head = '\n'.join(text.splitlines()[:12]) if text else ''
    pats = {
        'RCMB': [r'Version (\d+(?:\.\d+)+)'],
        'RPL': [r'Text revision (v[\d.]+\w*)', r'Version (v[\d.]+\w*)'],
        'REQ': [r'requirements, (rev \d+)'],
        'ICD': [r'\((draft [\d.]+)\)'],
        'CF4': [r'Version (\d+(?:\.\d+)+)'],
        'T14': [r'Combustion (v[\d.]+)'],
        'BENCH': [r'test plan (v\d+)'],
        'RELE': [r'(v\d+(?:\.\d+)+)'],
        'RGNC': [r'(v\d+(?:\.\d+)*)'],
    }
    for p in pats.get(sid, []):
        m = re.search(p, head)
        if m:
            return m.group(1)
    return None


def register_sources(ctx, a):
    H, C, V = a.hub, a.cad_dir, a.cad_version
    J = os.path.join
    ctx.add('CMB', J(H, 'interfaces/combustion.json'), 'Combustion interface (design point, grain, injector, igniter, sequences)')
    ctx.add('MEC', J(H, 'interfaces/mechanical.json'), 'Mechanical interface (gimbal, TVC, envelope, materials)')
    ctx.add('ELE', J(H, 'interfaces/electronics.json'), 'Electronics interface (ECU, sensors, firmware, abort causes)')
    ctx.add('GNC', J(H, 'interfaces/gnc.json'), 'Space/GNC interface (reference vehicle, mission, Monte Carlo)')
    ctx.add('BASE', J(H, 'interfaces/ENGINE-BASELINE-v0.json'), 'Engine baseline v0 (seed values, superseded)')
    ctx.add('CL', J(H, 'interfaces/CHANGELOG.md'), 'Decision log (line-numbered)', 'md')
    ctx.add('REQ', J(H, '00-requirements/REQUIREMENTS.md'), 'Engine requirements', 'md')
    ctx.add('ICD', J(H, '00-requirements/ICD-AIRFRAME.md'), 'Engine-airframe ICD', 'md')
    ctx.add('SUP', J(H, 'reviews/SUPERVISION.json'), 'Independent review register')
    ctx.add('RV2', J(H, 'reviews/REVIEW-COMBUSTION-R2.md'), 'Independent Combustion re-review REV-COMB-2 (text)', 'md', required=False)
    if a.overrides:
        ctx.add('OVR', a.overrides, 'Decision override table (datasheet generator input; drop entries when combustion.json v2.4a lands)')
    ctx.add('FA1', J(H, '02-combustion/data/v2p4a/fa1_envelope_v2p4a.json'),
            'Combustion v2.4a FA-1 relight-pulse load envelope (SIM on an ASSUMED construct)', required=False)
    ctx.add('RCMB', J(H, '02-combustion/REPORT.md'), 'Combustion report', 'md')
    ctx.add('CF4', J(H, '02-combustion/CF-4-SPEC.md'), 'CF-4 relight-purge cold-flow specification', 'md')
    ctx.add('T14', J(H, '02-combustion/T1-T4-REGRESSION-SPEC.md'), 'T1-T4 regression measurement specification', 'md')
    ctx.add('RPL', J(H, '05-plume-cfd/REPORT.md'), 'Plume CFD report', 'md')
    ctx.add('PVAL', J(H, '05-plume-cfd/validation/results/validation_v2.json'), 'Plume CFD validation results')
    ctx.add('FEALC', J(H, '04-fea/loadcases_v1.json'), 'FEA load cases (inputs)')
    ctx.add('SLEW', J(H, '03-cad/calcs/actuator_slew_v2.json'), 'TVC slew calculation v2 (Mechanical, hub copy)')
    ctx.add('BENCH', J(H, '06-electronics/docs/bench_plan_v2.md'), 'Electronics bench and test plan', 'md')
    ctx.add('RELE', J(H, '06-electronics/REPORT-v2.9-HANDBACK.md'), 'Electronics v2.9 handback report', 'md', required=False)
    ctx.add('RGNC', J(H, '01-systems-gnc/REPORT-v3.md'), 'Space/GNC report v3', 'md', required=False)
    ctx.add('BOM', J(C, f'BOM_{V}.json'), f'Bill of materials (CAD {V})')
    ctx.add('MP', J(C, f'massprops_{V}.json'), f'Mass properties (CAD {V})')
    ctx.add('MAN', J(C, f'assembly/assembly_manifest_{V}.json'), f'Assembly manifest, instance bounds (CAD {V})')
    ctx.add('GLB', J(C, f'assembly/ENGINE_{V}_neutral.glb'), f'Assembly GLB, visualisation geometry (CAD {V})', 'bin')
    ctx.add('PROP', J(C, 'properties.json'), 'CAD build properties and results', required=False)
    ctx.add('CHK', J(C, f'checks/checks_summary_{V}.json'), f'CAD software geometric checks (CAD {V})', required=False)
    ctx.add('RMAN', J(a.renders, 'render_manifest.json'), 'Render manifest (this generator)')
    for fid, rel, _ in PLUME_FIGS:
        ctx.add(fid, find_hub_file(H, rel), 'Plume figure', 'img', required=False)
    # versions for markdown and binary sources
    for sid, s in ctx.sources.items():
        if s.version is None and s.text is not None:
            s.version = md_version(sid, s.text)
        if sid == 'CL' and s.text is not None:
            s.version = f'{len(s.text.splitlines())} lines'
        if sid == 'SUP' and isinstance(s.data, dict) and s.version is None:
            s.version = f'{len(s.data.get("reviews") or [])} reviews'
        if sid == 'GLB':
            s.version = V
        if sid == 'PVAL' and s.version is None:
            m = re.search(r'_(v\d+)\.json$', s.path)
            s.version = m.group(1) if m else None
        if sid in ('PROP', 'CHK', 'MAN') and s.data is not None:
            s.version = s.data.get('cad_version') or s.version
        if s.kind == 'img' and s.version is None:
            s.version = 'figure'


def src_label(ctx, sid):
    s = ctx.sources.get(sid)
    if s is None:
        return sid
    return f'{sid} {s.version or ""}'.strip()


# =============================================================================================
# BOM and CAD-derived data
# =============================================================================================
def fnum(x):
    try:
        if x is None or x == '' or x == 'None':
            return None
        return float(x)
    except (TypeError, ValueError):
        return None


def bom_mass_class(ms):
    s = (ms or '').strip()
    u = s.upper()
    if not s:
        return None
    if 'TO-VERIFY' in u:
        return 'TO-VERIFY'
    if u.startswith('CAD VOLUME') or u.startswith('CALC'):
        return 'DERIVED'
    if u.startswith('COTS MASS (DATASHEET') or u.startswith('COTS MASS (INTERFACE'):
        return 'DATASHEET'
    if u.startswith('COTS MASS (DERIVED'):
        return 'DERIVED'
    if 'ESTIMATE' in u or 'ASSUMED' in u:
        return 'ASSUMED'
    if u.startswith('NOT FITTED'):
        return 'TO-DEFINE'
    return None


def price_state(p):
    s = (p or '').strip()
    if not s or s in ('0', '0.0') or re.search(r'\bfrom\b', s, re.I):
        return 'INVALID'
    if s.upper().startswith('TO-QUOTE'):
        return 'TO-QUOTE' if 'reference' not in s.lower() else 'TO-QUOTE-REF'
    if re.search(r'\d', s):
        return 'DATED-REF'
    return 'INVALID'


class BomRow:
    def __init__(self, ctx, kind, idx, line):
        self.kind, self.idx, self.l = kind, idx, line
        self.pn = line['pn']
        self.fam = family_of(self.pn)
        self.qty = fnum(line.get('qty'))
        self.unit = fnum(line.get('unit_mass_kg'))
        self.mclass = bom_mass_class(line.get('mass_source'))
        self.pstate = price_state(line.get('unit_price'))
        ptr = ptr_join(kind, idx)
        self.row_tv = TV(ctx, f"{self.pn}: {line.get('name', '')[:60]}", '', 'DESIGN',
                         f"BOM row (CAD {line.get('step', '')})", 'BOM', ptr,
                         note='row trace: name, qty, groups, material_name, process, unit_mass_kg, mass_source, unit_price, supplier')
        if self.unit is not None:
            self.mass_tv = TV(ctx, self.unit, 'kg', self.mclass, line.get('mass_source'), 'BOM', ptr + '/unit_mass_kg')
            if self.mclass is None:
                ctx.issue('WARN', f'BOM {self.pn}: unmapped mass source {line.get("mass_source")!r}')
        else:
            st = 'TO-DEFINE' if self.mclass == 'TO-DEFINE' else 'MISSING'
            self.mass_tv = TV(ctx, None, 'kg', st, line.get('mass_source'), 'BOM', ptr + '/unit_mass_kg', status=st)
        self.line_mass = (self.unit * self.qty) if (self.unit is not None and self.qty is not None) else None
        if self.pstate == 'INVALID':
            ctx.issue('ERROR', f'BOM {self.pn}: price field violates the price rule: {line.get("unit_price")!r}')

    @property
    def groups(self):
        return [g.strip() for g in str(self.l.get('groups') or '').split('/') if g.strip()]


def load_bom(ctx):
    b = ctx.src('BOM').data
    rows = []
    for kind in ('lines', 'provision_lines', 'contingency_lines'):
        for i, l in enumerate(b.get(kind, [])):
            rows.append(BomRow(ctx, kind, i, l))
    return rows


def manifest_extent(ctx, group=None, pn_prefix=None):
    """Union of instance bounds (mm) from the assembly manifest."""
    inst = ctx.raw('MAN', '/instances')
    lo, hi, n = [1e9] * 3, [-1e9] * 3, 0
    for it in inst:
        if group and it.get('group') != group:
            continue
        if pn_prefix and not it['inst'].startswith(pn_prefix):
            continue
        b = it['bounds_mm']
        for k in range(3):
            lo[k] = min(lo[k], b[k])
            hi[k] = max(hi[k], b[k + 3])
        n += 1
    return (lo, hi, n) if n else (None, None, 0)


def man_tv(ctx, value, what, group=None, pn_prefix=None, unit='mm'):
    sel = (f'group = {group}' if group else '') + (f'instance prefix {pn_prefix}' if pn_prefix else '')
    return TV(ctx, value, unit, 'DERIVED', f'DERIVED by {GEN_NAME}: {what} over assembly-manifest instance bounds'
              + (f' ({sel})' if sel else ''), 'MAN', '/instances/*/bounds_mm', note=what)


# =============================================================================================
# renders: crop/composite, projection, SVG overlays (visualisation only)
# =============================================================================================
def prep_render(ctx, a, name, keep_alpha=False, margin_frac=0.035, bg=(255, 255, 255)):
    from PIL import Image
    rdir = a.renders
    png = os.path.join(rdir, name + '.png')
    mpath = os.path.join(rdir, name + '_meta.json')
    if not (os.path.exists(png) and os.path.exists(mpath)):
        ctx.issue('ERROR', f'render missing: {png}')
        return None
    sid = 'R-' + name.upper().replace('FAMILY_', 'FAM-')
    if sid not in ctx.sources:
        ctx.add(sid, mpath, f'Render metadata: {name} (camera, anchors)', 'json')
    meta = json.load(open(mpath))
    im = Image.open(png).convert('RGBA')
    al = im.getchannel('A').point(lambda v: 255 if v > 6 else 0)
    bb = al.getbbox() or (0, 0, im.size[0], im.size[1])
    m = int(margin_frac * max(bb[2] - bb[0], bb[3] - bb[1]))
    box = (max(0, bb[0] - m), max(0, bb[1] - m), min(im.size[0], bb[2] + m), min(im.size[1], bb[3] + m))
    im = im.crop(box)
    os.makedirs(os.path.join(a.out, 'assets'), exist_ok=True)
    if keep_alpha:
        fn = f'render_{name}.png'
        im.save(os.path.join(a.out, 'assets', fn), optimize=True)
    else:
        fn = f'render_{name}.jpg'
        bgim = Image.new('RGBA', im.size, bg + (255,))
        bgim.alpha_composite(im)
        bgim.convert('RGB').save(os.path.join(a.out, 'assets', fn), quality=90, optimize=True)
    # projection self-check against Blender's own probe of the origin
    pr = meta.get('probe_points_px', {}).get('origin')
    if pr:
        q = project_raw(meta, (0.0, 0.0, 0.0))
        if abs(q[0] - pr[0]) > 1.0 or abs(q[1] - pr[1]) > 1.0:
            ctx.issue('ERROR', f'projection check failed for {name}: {q} vs {pr}')
    return {'name': name, 'file': 'assets/' + fn, 'x0': box[0], 'y0': box[1], 'w': box[2] - box[0],
            'h': box[3] - box[1], 'meta': meta, 'sid': sid, 'png_sha16': sha16_file(png)}


def project_raw(meta, P):
    cam = meta['camera']
    W, H = meta['res']
    c, r, u, mpp = cam['centre_m'], cam['right'], cam['up'], cam['m_per_px']
    d = [P[i] - c[i] for i in range(3)]
    return (W / 2 + sum(d[i] * r[i] for i in range(3)) / mpp,
            H / 2 - sum(d[i] * u[i] for i in range(3)) / mpp)


def proj(R, P):
    x, y = project_raw(R['meta'], P)
    return x - R['x0'], y - R['y0']


def svg_text(x, y, s, size, anchor='start', weight=400, fill='#1d2733', rotate=None, cls=''):
    tr = f' transform="rotate({rotate} {x:.1f} {y:.1f})"' if rotate is not None else ''
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size:.1f}" text-anchor="{anchor}" '
            f'font-weight="{weight}" fill="{fill}"{tr} class="{cls}">{esc(s)}</text>')


def svg_dim_v(x, y1, y2, label, size, side='right', ext_from=None):
    """Vertical dimension line at x between y1 and y2 with arrowheads; extension lines from ext_from."""
    o = []
    if ext_from is not None:
        for yy, xf in ((y1, ext_from[0]), (y2, ext_from[1])):
            o.append(f'<line x1="{xf:.1f}" y1="{yy:.1f}" x2="{x + (8 if side == "right" else -8):.1f}" y2="{yy:.1f}" class="ext"/>')
    o.append(f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2:.1f}" class="dim" marker-start="url(#arr)" marker-end="url(#arr)"/>')
    ym = (y1 + y2) / 2
    tx = x + (size * 0.9 if side == 'right' else -size * 0.5)
    o.append(svg_text(tx, ym, label, size, 'middle', 600, '#0b3a5c', rotate=-90))
    return '\n'.join(o)


def svg_dim_h(y, x1, x2, label, size, ext_from=None, below=True):
    o = []
    if ext_from is not None:
        for xx, yf in ((x1, ext_from[0]), (x2, ext_from[1])):
            o.append(f'<line x1="{xx:.1f}" y1="{yf:.1f}" x2="{xx:.1f}" y2="{y + (8 if below else -8):.1f}" class="ext"/>')
    o.append(f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" class="dim" marker-start="url(#arr)" marker-end="url(#arr)"/>')
    o.append(svg_text((x1 + x2) / 2, y + (size * 1.15 if below else -size * 0.45), label, size, 'middle', 600, '#0b3a5c'))
    return '\n'.join(o)


SVG_DEFS = ('<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            'orient="auto-start-reverse"><path d="M0,1.5 L9,5 L0,8.5 z" fill="#0b3a5c"/></marker></defs>'
            '<style>.dim{stroke:#0b3a5c;stroke-width:1.6;fill:none}.ext{stroke:#5d6b78;stroke-width:0.9;fill:none}'
            '.cl{stroke:#b4232a;stroke-width:1.3;stroke-dasharray:22 6 4 6;fill:none}.ld{stroke:#44515e;stroke-width:1.1;fill:none}'
            '.br{stroke:#2f6f4f;stroke-width:1.6;fill:none}</style>')


def svg_ortho_dims(ctx, R, axis_h, dims, title):
    """Orthographic view with envelope dimensions. axis_h = 0 (X) for the front view, 1 (Y) for the side
    view. dims: dict of TVs from the manifest. Returns (svg, list of TVs shown)."""
    W, H = R['w'], R['h']
    padL, padR, padT, padB = 250, 250, 70, 150
    fs = 25
    lo, hi = dims['lo'], dims['hi']
    def P(h, z):
        v = [0.0, 0.0, 0.0]
        v[axis_h] = h / 1000.0
        v[2] = z / 1000.0
        x, y = proj(R, v)
        return x + padL, y + padT
    xL, _ = P(lo[axis_h], 0)
    xR, _ = P(hi[axis_h], 0)
    _, yTop = P(0, hi[2])
    _, yBot = P(0, lo[2])
    _, y0 = P(0, 0.0)
    o = [f'<svg class="ov" viewBox="0 0 {W + padL + padR} {H + padT + padB}" xmlns="http://www.w3.org/2000/svg">', SVG_DEFS,
         f'<image href="{R["file"]}" x="{padL}" y="{padT}" width="{W}" height="{H}"/>']
    # pivot centre line
    o.append(f'<line x1="{padL - 40}" y1="{y0:.1f}" x2="{W + padL + 40}" y2="{y0:.1f}" class="cl"/>')
    o.append(svg_text(padL - 44, y0 - 8, 'pivot, z = 0', fs * 0.82, 'end', 600, '#b4232a'))
    # overall height (right), pivot->top and pivot->aft (left)
    o.append(svg_dim_v(xR + 95, yTop, yBot, f'{fmt_num(dims["H"].value, ".1f")} mm', fs, 'right', ext_from=(xR + 4, xR + 4)))
    o.append(svg_dim_v(xL - 70, yTop, y0, f'{fmt_num(dims["top"].value, ".1f")}', fs, 'left', ext_from=(xL - 4, xL - 4)))
    o.append(svg_dim_v(xL - 70, y0, yBot, f'{fmt_num(dims["aft"].value, ".1f")}', fs, 'left'))
    # gimballed engine group bracket (left, outer) and fixed module bracket (right, outer)
    if dims.get('eng_lo') is not None:
        _, ye1 = P(0, dims['eng_hi'])
        _, ye2 = P(0, dims['eng_lo'])
        xb = xL - 165
        o.append(f'<path d="M{xb + 14:.1f},{ye1:.1f} H{xb:.1f} V{ye2:.1f} H{xb + 14:.1f}" class="br"/>')
        o.append(svg_text(xb - 10, (ye1 + ye2) / 2, f'gimballed engine group {fmt_num(dims["eng_len"].value, ".1f")} mm',
                          fs * 0.78, 'middle', 600, '#2f6f4f', rotate=-90))
    if dims.get('fix_lo') is not None:
        _, yf1 = P(0, dims['fix_hi'])
        _, yf2 = P(0, dims['fix_lo'])
        xb = xR + 185
        o.append(f'<path d="M{xb - 14:.1f},{yf1:.1f} H{xb:.1f} V{yf2:.1f} H{xb - 14:.1f}" class="br"/>')
        o.append(svg_text(xb + 26, (yf1 + yf2) / 2, f'fixed module {fmt_num(dims["fix_len"].value, ".1f")} mm',
                          fs * 0.78, 'middle', 600, '#2f6f4f', rotate=-90))
    # overall width (bottom)
    o.append(svg_dim_h(yBot + 70, xL, xR, f'{fmt_num(dims["Wh"].value, ".1f")} mm', fs, ext_from=(yBot + 4, yBot + 4)))
    o.append(svg_text((W + padL + padR) / 2, H + padT + padB - 14, title, fs * 0.9, 'middle', 600, '#1d2733'))
    o.append('</svg>')
    return '\n'.join(o)


def label_layout(items, ymin, ymax, gap):
    """items: list of dicts with 'ty' (target y). Assign label y: sorted, non-overlapping, near targets."""
    items = sorted(items, key=lambda i: i['ty'])
    ys = [i['ty'] for i in items]
    for k in range(len(ys)):
        ys[k] = max(ys[k], ymin if k == 0 else ys[k - 1] + gap)
    over = (ys[-1] - ymax) if ys else 0
    if over > 0:
        ys[-1] -= over
        for k in range(len(ys) - 2, -1, -1):
            ys[k] = min(ys[k], ys[k + 1] - gap)
    for i, y in zip(items, ys):
        i['ly'] = y
    return items


def svg_section(ctx, R, bom_by_pn, callouts):
    W, H = R['w'], R['h']
    pad = 440
    padT, padB = 30, 30
    fs1, fs2 = 17.5, 14.5
    anchors = R['meta'].get('anchors', {})
    items, missing = [], []
    for pn in callouts:
        al = [x for x in anchors.get(pn, []) if x.get('kind') == 'cut-face centroid']
        if not al:
            al = anchors.get(pn, [])
        if not al or pn not in bom_by_pn:
            missing.append(pn)
            continue
        sides = {}
        for x in al:
            s = x.get('side') or ('L' if x['px'][0] < R['meta']['res'][0] / 2 else 'R')
            if s not in sides or x.get('area_m2', 0) > sides[s].get('area_m2', 0):
                sides[s] = x
        items.append({'pn': pn, 'sides': sides})
    # side assignment: forced if one side only; else balance counts in vertical order
    cnt = {'L': 0, 'R': 0}
    for it in sorted(items, key=lambda i: min(v['px'][1] for v in i['sides'].values())):
        if len(it['sides']) == 1:
            it['side'] = list(it['sides'])[0]
        else:
            it['side'] = 'L' if cnt['L'] <= cnt['R'] else 'R'
        cnt[it['side']] += 1
    for it in items:
        if len(it['sides']) > 1:
            continue
    # recount after forced ones and rebalance two-sided items if very uneven
    o = [f'<svg class="ov" viewBox="0 0 {W + 2 * pad} {H + padT + padB}" xmlns="http://www.w3.org/2000/svg">', SVG_DEFS,
         f'<image href="{R["file"]}" x="{pad}" y="{padT}" width="{W}" height="{H}"/>']
    shown = []
    for side in ('L', 'R'):
        grp = []
        for it in items:
            if it['side'] != side:
                continue
            a = it['sides'][side]
            tx, ty = a['px'][0] - R['x0'] + pad, a['px'][1] - R['y0'] + padT
            grp.append({'pn': it['pn'], 'tx': tx, 'ty': ty})
        label_layout(grp, padT + 20, H + padT - 30, fs1 + fs2 + 12)
        for g in grp:
            r = bom_by_pn[g['pn']]
            l1 = short_name(r.l.get('name', ''), 36)
            l2 = f"{g['pn'].replace('ENG-', '')} · {short_mat(r.l.get('material_name'), r.l.get('material'))}"
            if side == 'L':
                xe = pad - 26
                o.append(svg_text(xe, g['ly'] - 3, l1, fs1, 'end', 600, '#1d2733'))
                o.append(svg_text(xe, g['ly'] + fs2 + 1, l2, fs2, 'end', 400, '#55626f'))
                o.append(f'<path d="M{xe + 6:.1f},{g["ly"] - 7:.1f} H{xe + 18:.1f} L{g["tx"]:.1f},{g["ty"]:.1f}" class="ld"/>')
            else:
                xs = W + pad + 26
                o.append(svg_text(xs, g['ly'] - 3, l1, fs1, 'start', 600, '#1d2733'))
                o.append(svg_text(xs, g['ly'] + fs2 + 1, l2, fs2, 'start', 400, '#55626f'))
                o.append(f'<path d="M{xs - 6:.1f},{g["ly"] - 7:.1f} H{xs - 18:.1f} L{g["tx"]:.1f},{g["ty"]:.1f}" class="ld"/>')
            o.append(f'<circle cx="{g["tx"]:.1f}" cy="{g["ty"]:.1f}" r="4.2" fill="#e8912d" stroke="#5a3200" stroke-width="0.8"/>')
            shown.append(g['pn'])
    o.append('</svg>')
    if missing:
        ctx.issue('INFO', f'section callouts without a cut anchor (part entirely in the removed half or not in BOM): {missing}')
    return '\n'.join(o), shown, missing


def svg_layout(ctx, R):
    W, H = R['w'], R['h']
    padB = 150
    fs = 21
    o = [f'<svg class="ov" viewBox="0 0 {W} {H + padB}" xmlns="http://www.w3.org/2000/svg">', SVG_DEFS,
         f'<image href="{R["file"]}" x="0" y="0" width="{W}" height="{H}"/>']
    groups = R['meta'].get('layout_groups') or []
    cam = R['meta']['camera']
    for k, g in enumerate(groups):
        px = R['meta']['res'][0] / 2 + (g['x_centre_m'] - cam['centre_m'][0]) / cam['m_per_px'] - R['x0']
        row = k % 2
        y = H + 34 + row * 60
        o.append(f'<line x1="{px:.1f}" y1="{H - 4:.1f}" x2="{px:.1f}" y2="{y - fs:.1f}" class="ld"/>')
        o.append(svg_text(px, y, g['group'], fs, 'middle', 600, '#1d2733'))
        z0, z1 = g['cad_z_range_m']
        o.append(svg_text(px, y + fs + 2, f'CAD z {z0 * 1000:+.0f} … {z1 * 1000:+.0f} mm', fs * 0.82, 'middle', 400, '#55626f'))
    o.append('</svg>')
    return '\n'.join(o)


# =============================================================================================
# plots (matplotlib, SVG with live text)
# =============================================================================================
def mpl_setup():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    fam = 'Inter'
    for p in MPL_FONTS:
        try:
            font_manager.fontManager.addfont(p)
            fam = FONT_FAMILY
        except (OSError, RuntimeError, ValueError):
            pass
    plt.rcParams.update({
        'font.family': fam, 'font.size': 7.2, 'svg.fonttype': 'none', 'axes.linewidth': 0.6,
        'axes.edgecolor': '#3b4652', 'axes.labelcolor': '#1d2733', 'xtick.color': '#3b4652', 'ytick.color': '#3b4652',
        'xtick.major.width': 0.5, 'ytick.major.width': 0.5, 'grid.color': '#d9dee4', 'grid.linewidth': 0.5,
        'axes.grid': True, 'axes.spines.top': False, 'axes.spines.right': False, 'legend.frameon': False,
        'legend.fontsize': 6.6, 'axes.titlesize': 7.6, 'axes.titleweight': 'semibold', 'figure.dpi': 100,
    })
    return plt


MPL_FONTS = []
C_ACC, C_ACC2, C_WARN, C_BAD, C_OK, C_GREY = '#0b5c8c', '#2f8f83', '#d58a1c', '#b4232a', '#2f6f4f', '#8a96a3'


def save_plot(fig, a, name):
    p = os.path.join(a.out, 'assets', name + '.svg')
    fig.savefig(p, format='svg', bbox_inches='tight', pad_inches=0.03, metadata={'Date': None})
    import matplotlib.pyplot as plt
    plt.close(fig)
    return 'assets/' + name + '.svg'


def fa1_envelope(ctx, D):
    """FA-1 relight-pulse load: the Combustion v2.4a envelope (SIM on an ASSUMED construct) and the lead
    load decision that cites the data file (CHANGELOG). None while either is missing from the hub."""
    cl = D['cl']
    n = cl.find('fa1_envelope_v2p4a.json')
    if n is None or 'FA1' not in ctx.sources or ctx.src('FA1').data is None:
        return None
    F = {'n': n}
    dec = F['dec'] = cl.part(n, 'DECISION: FA-1 structural load')
    F['load'] = rx_text(ctx, dec, r'structural load = (\d+) bar abs', 'bar', tag='LEAD')
    F['p_des'] = rx_text(ctx, dec, r'margins also at (\d+) bar abs', 'bar', tag='LEAD')
    F['p_sens'] = rx_text(ctx, dec, r'and at (\d+) bar abs \(sensitivity', 'bar', tag='LEAD')
    F['per'] = [rx_text(ctx, dec, r'natural period of ([\d.]+)-([\d.]+) ms', 'ms', tag='LEAD', group=g) for g in (1, 2)]
    F['f_int'] = rx_text(ctx, dec, r'thrust spike ([\d.]+) kN x (\d+) ms', 'kN', tag='LEAD', group=1)
    F['t_int'] = rx_text(ctx, dec, r'thrust spike ([\d.]+) kN x (\d+) ms', 'ms', tag='LEAD', group=2)
    F['summary'] = cl.part(n, ("FA-1 envelope (", 'head peak'))
    F['bounding'] = cl.part(n, 'O/F bounding')
    F['dlf'] = cl.part(n, 'Pressure DLF')
    F['inv'] = cl.part(n, 'Missing datum')
    F['evid'] = cl.part(n, 'physical evidence')
    m = re.search(r'fa1_envelope_v2p4a\.json ([0-9a-f]{16})', cl.line(n)['text'])
    cited, have = (m.group(1) if m else None), ctx.src('FA1').sha16
    F['hash'] = ctx.t('generator', f'FA1 sha256/16 against the citation in CHANGELOG L{n}',
                      (f'{have}: matches the citation' if cited == have else f'MISMATCH: cited {cited}, file {have}') if cited else f'{have}: no hash cited',
                      'DERIVED', tag_raw='generator check on this build')
    if cited != have:
        ctx.issue('WARN', f'FA-1 envelope file sha256/16 {have} differs from the decision citation {cited} (CHANGELOG L{n})')
    E, T = '/envelope', '/tags/model'
    VO, BO = 'vapour_once|incl_OF3-3.5|all', 'both|incl_OF3-3.5|all'

    def ev(key, metric, unit, tagp=T):
        return ctx.v('FA1', f'{E}/{key}/{metric}/max', unit, tag_ptr=tagp)
    F['pk'] = [ev('vapour_once|grid_OF4-12|rounded_Cd1.0', 'peak_head_bar', 'bar'),
               ev('vapour_once|grid_OF4-12|sharp_Cd0.65', 'peak_head_bar', 'bar'),
               ev(BO, 'peak_head_bar', 'bar')]
    F['aft'] = ctx.v('FA1', f'{E}/{BO}/aft_over_head_peak', '', tag_ptr=T)
    F['above'] = []
    for k in ('above45_head_total_ms', 'above67p5_head_total_ms', 'above90_head_total_ms'):
        mm = re.match(r'above(\d+)(?:p(\d+))?_', k)
        lev = float(mm.group(1) + ('.' + mm.group(2) if mm.group(2) else ''))
        F['above'].append((lev, ev(VO, k, 'ms'), ev(BO, k, 'ms')))
    F['imp'] = (ev(VO, 'impulse_above_P0_25ms_head_bar_ms', 'bar·ms'), ev(BO, 'impulse_above_P0_25ms_head_bar_ms', 'bar·ms'))
    F['imp_def'] = ctx.v('FA1', '/metric_definitions/impulse', tag_ptr=T)
    F['fpk'] = (ev(VO, 'F_peak_QSx0.975_N', 'N', '/tags/thrust'), ev(BO, 'F_peak_QSx0.975_N', 'N', '/tags/thrust'))
    sd = ctx.v('FA1', f'{E}/{BO}/F_sdof_QSx0.975_N_max_by_period', 'N', tag_ptr='/tags/sdof')
    F['sdof'] = ctx.d(max(sd.value) if isinstance(sd.value, list) and sd.value else None, 'N',
                      'max over the SDOF periods of F_sdof_QSx0.975_N_max_by_period (upper bracket)', [sd])
    ri = ctx.v('FA1', '/interim_load_comparison/thrust_rect_sdof_N', 'N', tag_ptr='/tags/sdof')
    F['sdof_int'] = ctx.d([min(ri.value), max(ri.value)] if isinstance(ri.value, list) and ri.value else None, 'N',
                          'range over the SDOF periods of the interim rectangular thrust pulse', [ri])

    def eqs(key):
        tv = ctx.v('FA1', f'{E}/{key}/P_head_equiv_static_by_period', 'bar', tag_ptr='/tags/sdof')
        vals = [x.get('P_equiv_static_abs_bar') for x in tv.value if isinstance(x, dict)] if isinstance(tv.value, list) else []
        vals = [x for x in vals if isinstance(x, (int, float))]
        return ctx.d(max(vals) if vals else None, 'bar', f'max over the SDOF periods of P_head_equiv_static_by_period ({key})', [tv])
    F['eqs'] = (eqs('vapour_once|grid_OF4-12|rounded_Cd1.0'), eqs(BO))
    F['grid'] = ctx.v('FA1', '/grid', tag_ptr=T)
    F['ncases'] = ctx.v('FA1', '/grid/n_cases', tag_ptr=T)
    F['tag'] = ctx.v('FA1', T, tag='SIM')
    F['notmod'] = ctx.v('FA1', '/not_modelled', tag_ptr=T)
    F['inv_status'] = ctx.v('FA1', '/fuel_vapour_inventory/status', tag='TO-VERIFY')
    n_m = cl.find('FA-1', owner='mechanical', what='(result)')
    if n_m and n_m > n:
        F['n_mech'] = n_m
        F['mech'] = F['margins'] = cl.whole(n_m)
        F['mech_key'] = cl.part(n_m, ('YIELD', 'J-FWD', 'bearings exceed', 'brinelling'))
        F['mech_rev'] = ctx.missing(f'Independent review and lead decision on the Mechanical FA-1 margins (CHANGELOG {n_m}) '
                                    'and on the CAD changes they propose', 'PENDING')
    else:
        F['margins'] = ctx.missing('Mechanical structural margins at the FA-1 structural, design and sensitivity pressures', 'PENDING')
    F['inv_unk'] = ctx.missing('FA-1 fuel-vapour inventory at light (data file: first-order bound only; lead decision: remains TO-VERIFY)', 'TO-VERIFY')
    return F


def sec_fa1(ctx, doc, F):
    """Section 2.5: the FA-1 envelope and the load decision."""
    o = [doc.h(2, '2.5 FA-1 relight-pulse load')]
    o.append('<p>The fuel-assisted relight pulse (FMEA FA-1) is published as an envelope over the Combustion v2.4a case grid, computed on a vented '
             'three-node construct with ASSUMED inputs: an estimate, not acceptance evidence. The lead set the structural load on it (CHANGELOG '
             f'{F["n"]}). The single point in combustion.json v2.4 is not a load any more and is annotated wherever it is quoted (OVR-07).</p>')
    pk, vo_bo = F['pk'], ' / '
    rows = [['Case grid (as published, with the number of cases)', tvtxt(F['grid'], 400)],
            ['Head peak: baseline (vapour counted once, rounded entrance) / sharp entrance / upper bracket',
             cat(pres_bar(ctx, pk[0]), vo_bo, pres_bar(ctx, pk[1]), vo_bo, pres_bar(ctx, pk[2]), Cell('', pk))],
            ['Aft peak relative to the head peak (range over the cases)', num_cell(F['aft'], '.3f')]]
    for lev, a_, b_ in F['above']:
        rows.append([f'Time above {fmt_num(lev)} bar at the head (summed): baseline / upper bracket', cat(a_.h('.2f'), vo_bo, b_.h('.2f'))])
    rows += [['Head pressure impulse above the cold-flow pressure: baseline / upper bracket',
              cat(F['imp'][0].h('.0f'), vo_bo, F['imp'][1].h('.0f'), '<div class="small">', tvtxt(F['imp_def'], 200), '</div>')],
             ['Thrust spike, peak (quasi-steady nozzle × η<sub>cf</sub>): baseline / upper bracket', cat(F['fpk'][0].h('.0f'), vo_bo, F['fpk'][1].h('.0f'))],
             ['Thrust spike, single-degree-of-freedom equivalent (max over periods), upper bracket; interim rectangular pulse for comparison',
              cat(F['sdof'].h('.0f'), '; interim pulse ', F['sdof_int'].h('.0f'))],
             ['Head equivalent static pressure with the dynamic load factor (max over periods): baseline rounded / upper bracket',
              cat(pres_bar(ctx, F['eqs'][0]), vo_bo, pres_bar(ctx, F['eqs'][1]), Cell('', list(F['eqs'])))],
             ['Lead summary of the envelope', cat(tvtxt(F['summary'], 700), ' ', tvtxt(F['bounding'], 400), ' ', tvtxt(F['dlf'], 400))],
             ['Model tag', tvtxt(F['tag'], 300)],
             ['Not modelled', tvtxt(F['notmod'], 700)],
             ['Fuel-vapour inventory at light', cat(tvtxt(F['inv_status'], 240), ' ', tvtxt(F['inv'], 200), ' ', F['inv_unk'].h())],
             ['Data file', cat(f'<span class="mono small">02-combustion/data/v2p4a/{esc(SRC_FILE["FA1"])}</span> ', F['hash'].h())]]
    o.append(dtable(['FA-1 envelope (Combustion v2.4a)', 'Value'], rows, widths=['40%', '60%'],
                    caption='Envelope maxima over the case grid. Baseline: fuel vapour counted once; upper bracket: both initial conditions. '
                            'Absolute pressures. SIM on an ASSUMED construct.'))
    per = F['per']
    rows = [['FA-1 structural load, quasi-static at head and aft, all parts', Cell(pres_bar(ctx, F['load'], 0), [F['load']])],
            ['Parts with a natural period in the decided band (closures, bolts, J1 lip): design / sensitivity pressure',
             cat(f'<span class="v">{per[0].num("g")}–{per[1].num("g")}</span><span class="u">&#8239;ms</span> {per[0].pill()}{per[0].ref()} {per[1].ref()}: ',
                 pres_bar(ctx, F['p_des'], 0), vo_bo, pres_bar(ctx, F['p_sens'], 0), Cell('', [per[0], per[1], F['p_des'], F['p_sens']]))],
            ['Thrust spike, interim structural load (confirmed bounding)', cat(F['f_int'].h('.1f'), ' × ', F['t_int'].h('g'))],
            (['Mechanical margins at these loads (decision-log result, not independently reviewed)',
              cat(tvtxt(F['mech'], 1800), ' ', F['mech_rev'].h())] if F.get('mech') else
             ['Mechanical margins at these loads', Cell(F['margins'].h(), [F['margins']])]),
            ['Physical evidence', tvtxt(F['evid'], 300)],
            ['Decision text', tvtxt(F['dec'], 900)]]
    o.append(dtable(['FA-1 load decision', 'Value'], rows, widths=['40%', '60%'],
                    caption=('Lead decision on the envelope and the margins Mechanical reported against it (quoted as reported, negative values '
                             'included; SIM, not the assembled FEA of record; §9.2, §13.3 C-14). ' if F.get('mech') else
                             'Lead decision on the envelope. The structural margins at these loads are Mechanical\'s to report (§9, §12.2). ') +
                            'The proof pressure is in the §2.4 ladder (its absolute or gauge basis is not stated in combustion.json).'))
    return o


def plot_throttle(a, pts, fails, cap_bar, meop_bar, stiff_rule, marks, fail_label, basis=None):
    plt = mpl_setup()
    fig, ax = plt.subplots(2, 2, figsize=(6.9, 4.3))
    F = [p['F'].value for p in pts]
    def ser(k, f=1.0):
        return [p[k].value * f if p[k].value is not None else float('nan') for p in pts]
    pc = ser('Pc', 1e-5)
    ax[0, 0].plot(F, pc, 'o-', color=C_ACC, ms=3.2, lw=1.1, label='operating-point list (SIM)')
    if fails:
        import textwrap
        ax[0, 0].plot([f['F'] for f in fails], [f['Pc'] for f in fails], 's', color=C_BAD, ms=2.8, alpha=0.75,
                      label='\n'.join(textwrap.wrap(fail_label, 36)))
    ax[0, 0].axhline(cap_bar, color=C_WARN, lw=0.8, ls='--')
    ax[0, 0].text(0.02, cap_bar + 0.8, f'software cap {cap_bar:g} bar', color=C_WARN, fontsize=6.2, transform=ax[0, 0].get_yaxis_transform())
    ax[0, 0].axhline(meop_bar, color=C_BAD, lw=0.8, ls='--')
    ax[0, 0].text(0.02, meop_bar + 0.8, f'MEOP {meop_bar:g} bar', color=C_BAD, fontsize=6.2, transform=ax[0, 0].get_yaxis_transform())
    if basis is not None:
        ax[0, 0].axhline(basis[0], color=C_ACC, lw=0.8, ls='-.')
        ax[0, 0].text(0.98, basis[0] - 2.6, basis[1], color=C_ACC, fontsize=6.0, ha='right', transform=ax[0, 0].get_yaxis_transform())
    ax[0, 0].set_xlabel('thrust F [N]')
    ax[0, 0].set_ylabel('chamber pressure Pc [bar]')
    ax[0, 0].legend(loc='lower right', fontsize=5.8, frameon=True, framealpha=0.92, edgecolor='none')
    ax[0, 0].set_ylim(0, meop_bar * 1.16)
    ax[0, 1].plot(F, ser('OF'), 'o-', color=C_ACC2, ms=3.2, lw=1.1)
    ax[0, 1].set_xlabel('thrust F [N]')
    ax[0, 1].set_ylabel('O/F [–]')
    ax[1, 0].plot(F, ser('Isp'), 'o-', color=C_ACC, ms=3.2, lw=1.1)
    ax[1, 0].set_xlabel('thrust F [N]')
    ax[1, 0].set_ylabel('Isp, sea level [s]')
    ax[1, 1].semilogy(F, ser('dP'), 'o-', color=C_OK, ms=3.2, lw=1.1)
    # plain decimal tick labels: mathtext labels are split into tspans whose whitespace falls back to the SVG default (serif) font
    from matplotlib.ticker import FuncFormatter, NullFormatter
    ax[1, 1].yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:g}'))
    ax[1, 1].yaxis.set_minor_formatter(NullFormatter())
    ax[1, 1].axhline(stiff_rule, color=C_BAD, lw=0.8, ls='--')
    ax[1, 1].text(0.02, stiff_rule * 1.12, f'stiffness rule dP/Pc ≥ {stiff_rule:g}', color=C_BAD, fontsize=6.2, transform=ax[1, 1].get_yaxis_transform())
    ax[1, 1].set_xlabel('thrust F [N]')
    ax[1, 1].set_ylabel('injector dP / Pc [–]')
    fmax = max([v for v in F if v is not None] + [0])
    fall = max([fmax] + [f['F'] for f in fails if f['F'] is not None])
    for x in ax.flat:
        for f, lab in marks:
            if f is not None:
                x.axvline(f, color=C_GREY, lw=0.6, ls=':')
        x.set_xlim(0, (fall if x is ax[0, 0] else fmax) * 1.06)
    fig.tight_layout(h_pad=1.0, w_pad=1.6)
    return save_plot(fig, a, 'plot_throttle')


def plot_pressure_ladder(a, items):
    """items: (label, value_bar or (lo, hi), color, note)"""
    plt = mpl_setup()
    fig, ax = plt.subplots(figsize=(6.9, 0.28 * len(items) + 0.5))
    ys = list(range(len(items)))[::-1]
    for y, (lab, v, col, note) in zip(ys, items):
        if isinstance(v, (list, tuple)):
            ax.barh(y, v[1] - v[0], left=v[0], height=0.55, color=col, alpha=0.55)
            ax.text(v[1] + 0.8, y, f'{v[0]:.1f}–{v[1]:.1f} bar  {note}', va='center', fontsize=6.3, color='#1d2733')
        else:
            ax.barh(y, v, height=0.55, color=col)
            ax.text(v + 0.8, y, f'{v:.2f} bar  {note}', va='center', fontsize=6.3, color='#1d2733')
    ax.set_yticks(ys)
    ax.set_yticklabels([i[0] for i in items])
    ax.set_xlabel('pressure [bar] (absolute unless noted)')
    vmax = max((max(v) if isinstance(v, (list, tuple)) else v) for _, v, _, _ in items if v is not None)
    ax.set_xlim(0, vmax * 1.12)
    ax.grid(axis='y', visible=False)
    fig.tight_layout()
    return save_plot(fig, a, 'plot_pressure_ladder')


def plot_mass(a, fams, excl):
    plt = mpl_setup()
    n = len(fams) + len(excl)
    fig, ax = plt.subplots(figsize=(6.9, 0.22 * n + 0.6))
    labels, y = [], n - 1
    for lab, v in fams:
        ax.barh(y, v, height=0.62, color=C_ACC)
        ax.text(v + 0.01, y, f'{v:.3f} kg', va='center', fontsize=6.2)
        labels.append((y, lab))
        y -= 1
    for lab, v in excl:
        if isinstance(v, (list, tuple)):
            ax.barh(y, v[1] - v[0], left=v[0], height=0.62, color='white', edgecolor=C_WARN, hatch='////', lw=0.6)
            ax.text(v[1] + 0.01, y, f'{v[0]:.3f}–{v[1]:.3f} kg (not in CAD)', va='center', fontsize=6.2, color='#7a4b06')
        elif v is None:
            ax.text(0.005, y, 'MASS UNKNOWN (not designed)', va='center', fontsize=6.2, color=C_BAD)
        else:
            ax.barh(y, v, height=0.62, color='white', edgecolor=C_WARN, hatch='////', lw=0.6)
            ax.text(v + 0.01, y, f'{v:.3f} kg (not in CAD)', va='center', fontsize=6.2, color='#7a4b06')
        labels.append((y, lab))
        y -= 1
    ax.set_yticks([l[0] for l in labels])
    ax.set_yticklabels([l[1] for l in labels])
    ax.set_xlabel('mass [kg]')
    ax.grid(axis='y', visible=False)
    ax.set_xlim(0, max([v for _, v in fams] + [1.3]) * 1.25)
    fig.tight_layout()
    return save_plot(fig, a, 'plot_mass')


def plot_landing(a, rows):
    """rows: (label, P, lo, hi, color)"""
    plt = mpl_setup()
    fig, ax = plt.subplots(figsize=(6.9, 0.2 * len(rows) + 0.7))
    ys = list(range(len(rows)))[::-1]
    for y, (lab, p, lo, hi, col) in zip(ys, rows):
        ax.errorbar(p, y, xerr=[[p - lo], [hi - p]], fmt='o', color=col, ms=3.0, lw=0.9, capsize=2)
        ax.text(1.003, y, f'{p:.3f} [{lo:.3f}, {hi:.3f}]', va='center', fontsize=6.0, transform=ax.get_yaxis_transform())
    ax.set_yticks(ys)
    ax.set_yticklabels([r[0] for r in rows])
    ax.set_xlabel('P(landing success), 500 dispersed runs, Wilson 95 % interval')
    ax.set_xlim(min(0.2, min(r[2] for r in rows) - 0.02), 1.0)
    ax.grid(axis='y', visible=False)
    fig.tight_layout()
    fig.subplots_adjust(right=0.80)
    return save_plot(fig, a, 'plot_landing')


def plot_slew(a, cases, req):
    """cases: list of (load label, {V: dps}); req: required dps"""
    plt = mpl_setup()
    fig, ax = plt.subplots(figsize=(6.9, 2.1))
    volts = sorted({v for _, d in cases for v in d})
    w = 0.8 / max(1, len(volts))
    cols = {volts[0]: C_GREY, volts[-1]: C_ACC2}
    for k, v in enumerate(volts):
        xs = [i + (k - (len(volts) - 1) / 2) * w for i in range(len(cases))]
        vals = [d.get(v, float('nan')) for _, d in cases]
        ax.bar(xs, vals, width=w * 0.92, color=cols.get(v, C_ACC), label=f'{v} V plug')
        for x, val in zip(xs, vals):
            ax.text(x, val + 1.5, f'{val:.1f}', ha='center', fontsize=5.6)
    ax.axhline(req, color=C_BAD, lw=0.9, ls='--')
    ax.text(len(cases) - 0.5, req + 2, f'ENG-07 ≥ {req:g} °/s', color=C_BAD, fontsize=6.2, ha='right')
    ax.set_xticks(range(len(cases)))
    ax.set_xticklabels([c[0] for c in cases], fontsize=6.3)
    ax.set_ylabel('worst-direction slew at 7° [°/s]')
    ax.legend(ncol=len(volts), loc='upper left', fontsize=6.2)
    ax.set_ylim(0, max(max(d.values()) for _, d in cases) * 1.18)
    ax.grid(axis='x', visible=False)
    fig.tight_layout()
    return save_plot(fig, a, 'plot_slew')


def plot_sequence(a, ev, purge, windows):
    """ev: list of (t, label); purge: dict(t0, ramp, flow, end); windows: list of (label, t0, t1)"""
    plt = mpl_setup()
    fig, ax = plt.subplots(figsize=(6.9, 1.9))
    ax.barh(2, purge['ramp'], left=purge['t0'], height=0.5, color=C_GREY, label='MV opener ramp')
    ax.barh(2, purge['flow'], left=purge['end'] - purge['flow'], height=0.5, color=C_ACC2, alpha=0.8, label='purge flow (2 taps)')
    for k, (lab, t0, t1) in enumerate(windows):
        ax.barh(1 - 0.0 * k, t1 - t0, left=t0, height=0.5, color=C_WARN, alpha=0.35 + 0.2 * k)
        ax.text(t1 + 0.03, 1, lab, va='center', fontsize=6.0)
    for k, (t, lab) in enumerate(sorted(ev)):
        ax.axvline(t, color=C_ACC, lw=0.7, ls=':')
        ax.text(t + 0.012, (0.62, 0.36, 0.10)[k % 3], lab, va='bottom', ha='left', fontsize=6.0, color=C_ACC,
                bbox=dict(boxstyle='round,pad=0.12', fc='white', ec='none', alpha=0.85))
    ax.set_yticks([2, 1])
    ax.set_yticklabels(['PURGE (A1 relight)', 'light window W'])
    ax.set_xlabel('time relative to E0 (RELIGHT command) [s]')
    ax.set_ylim(0, 2.6)
    ax.set_xlim(purge['t0'] - 0.2, 1.4)
    ax.legend(loc='upper right', fontsize=6.0, ncol=2)
    ax.grid(axis='y', visible=False)
    fig.tight_layout()
    return save_plot(fig, a, 'plot_sequence')


# =============================================================================================
# document scaffolding
# =============================================================================================
class Doc:
    def __init__(self):
        self.heads = []

    def h(self, level, text, cls=''):
        hid = 'sec%02d' % (len(self.heads) + 1)
        self.heads.append({'level': level, 'id': hid, 'text': text, 'page': None})
        return f'<h{level} id="{hid}" class="{cls}">{esc(text)}</h{level}>'


def rx(ctx, sid, ptr, pattern, unit='', tag=None, conv=None, group=1, note=''):
    """Number extracted from a text value at a JSON pointer with an explicit regex (recorded)."""
    s = ctx.raw(sid, ptr, default=None)
    if isinstance(s, dict):
        tag_raw = s.get('tag')
        s = s.get('v')
    else:
        tag_raw = None
    m = re.search(pattern, str(s)) if s is not None else None
    loc = f'{ptr} [regex {pattern}]'
    if not m:
        ctx.issue('WARN', f'regex not matched {sid}:{ptr} {pattern}')
        tv = TV(ctx, None, unit, 'MISSING', tag_raw, sid, loc, status='MISSING', note='pattern not found')
        ctx.unknowns.append({'what': f'{sid}:{loc}', 'status': 'MISSING', 'tid': tv.tid})
        return tv
    val = float(m.group(group))
    if conv:
        val = val * conv[0] + conv[1]
        note = (note + '; ' if note else '') + f'display = raw x {conv[0]:g} ({conv[2]})'
    ev = tag or normalise_tag(tag_raw) or 'DERIVED'
    return TV(ctx, val, unit, ev, tag_raw or f'(class set by generator: {ev})', sid, loc, note=note)


def md_row(ctx, sid, section_prefix, key, col, ev=None, tag_col=None, maxlen=None):
    """Text cell of a markdown table row selected by its first-column key."""
    rows = md_table_rows(ctx.src(sid).text or '', section_prefix)
    for r in rows:
        if r and re.sub(r'\*', '', r[0]).strip() == key:
            if col >= len(r):
                break
            txt = re.sub(r'\*\*', '', r[col]).strip()
            tag_raw = r[tag_col].strip() if (tag_col is not None and tag_col < len(r)) else None
            e = ev or normalise_tag(tag_raw.split('/')[0] if tag_raw else None) or 'DESIGN'
            return ctx.t(sid, f'§{section_prefix or "*"} row "{key}" col {col}', txt, e, tag_raw=tag_raw)
    ctx.issue('WARN', f'markdown row not found {sid} §{section_prefix} {key!r}')
    return ctx.missing(f'{sid} §{section_prefix} row {key}')


def req_row(ctx, key, maxlen=None):
    """REQUIREMENTS.md rev 2 table row: requirement text with its basis column as tag."""
    return md_row(ctx, 'REQ', '2. Top-level', key, 1, tag_col=2)


def pts_index(ctx):
    pts = ctx.raw('CMB', '/operating_points/throttle_points_20C_initial_port', default=[]) or []
    return {round(p.get('fraction', -1), 4): i for i, p in enumerate(pts)}


def tp(ctx, idx, frac, key, unit='', conv=None):
    i = idx.get(round(frac, 4))
    if i is None:
        return ctx.missing(f'throttle point {frac} {key}')
    return ctx.v('CMB', f'/operating_points/throttle_points_20C_initial_port/{i}/{key}', unit, conv=conv, tag='SIM',
                 tag_ptr='/operating_points/basis')


def pill_box(ev, text):
    return f'<span class="ev ev-{ev.lower()}">{esc(ev)}</span> {text}'


# =============================================================================================
# section 0: cover and contents
# =============================================================================================
def sec_cover(ctx, doc, a, D):
    g = D['geo']
    rated = D['rated']
    cfg = [('CMB', 'Combustion'), ('MEC', 'Mechanical'), ('ELE', 'Electronics'), ('GNC', 'Space/GNC'),
           ('REQ', 'Requirements'), ('ICD', 'Airframe ICD'), ('CL', 'Decision log'), ('SUP', 'Review register')] + \
          ([('OVR', 'Decision overrides')] if 'OVR' in ctx.sources else [])
    cfg_rows = ''.join(f'<tr><td>{n}</td><td>{esc(ctx.src(s).version or "–")}</td><td class="mono">{esc(ctx.src(s).sha16 or "MISSING")}</td></tr>'
                       for s, n in cfg)
    low = D.get('rated_low')
    rated_cell = cat(rated['F'].h(), f'<div class="tsub">≈ {low.h()} if η<sub>cf</sub> is at the low end of its band</div>', Cell('', [low])) \
        if (low is not None and low.value is not None) else rated['F']
    tiles = [
        ('Rated thrust (SL), Pc at the software cap', rated_cell), ('Chamber pressure', D['pc_rated_cell']), ('Throttle floor 5:1', D['floor_F']),
        ('Isp, rated (SL)', rated['Isp']), ('CAD mass, wet (excl. tank)', D['mass_wet_all']),
        ('Envelope (CAD bbox)', D['env_cell']),
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
  <div class="cv-hero">{hero_html}<div class="cv-cap">CAD {esc(a.cad_version)} assembly, neutral pose. Visualisation of tessellated display geometry, not a drawing.</div></div>
  <div class="cv-side">
   <div class="cv-draft">DRAFT · {esc(a.rev)}</div>
   <div class="cv-warn"><b>Not physical approval.</b> Nothing in this datasheet is physical approval or acceptance. No value is MEASURED: every value is design, simulation, derivation, assumption, datasheet or requirement data and carries its evidence tag and a trace reference (T###, Appendix A). Missing data are shown as MISSING, TO-DEFINE or PENDING, never estimated by the generator.</div>
   <div class="tiles">{th}</div>
   <table class="cv-cfg"><thead><tr><th>Configuration</th><th>Version</th><th>sha256/16</th></tr></thead><tbody>
   <tr><td>CAD</td><td>{esc(a.cad_version)}</td><td class="mono">GLB {esc(ctx.src("GLB").sha16 or "MISSING")}</td></tr>
   {cfg_rows}</tbody></table>
   <div class="cv-gen">Generated {esc(D["generated"])} by gen/{GEN_NAME} {GEN_VERSION}. Quotations: delivery Sønderborg, Denmark, DK-6400. Units SI; pressures in MPa with bar in brackets.</div>
  </div>
 </div>
</section>'''


def sec_toc(doc):
    rows = []
    for hd in doc.heads:
        if hd['level'] > 2:
            continue
        pg = hd['page'] if hd['page'] is not None else '00'
        rows.append(f'<div class="toc-l{hd["level"]}"><a href="#{hd["id"]}"><span class="tt">{esc(hd["text"])}</span>'
                    f'<span class="dots"></span><span class="pg">{pg}</span></a></div>')
    return '<section class="toc"><h1 class="toc-h" id="contents">Contents</h1>' + '\n'.join(rows) + '</section>'


# =============================================================================================
# section 1: identification and status
# =============================================================================================
def sec_identification(ctx, doc, a, D):
    cl = D['cl']
    o = [doc.h(1, '1 Identification and status')]
    gen = lambda v, what: TV(ctx, v, '', 'DESIGN', 'generator configuration (command line / run time)', 'generator', what)
    rows = [
        ('Document', gen(DOC_ID, 'DOC_ID')),
        ('Revision and status', gen(f'{a.rev} — DRAFT, digital design data only', '--rev')),
        ('Generated', gen(D['generated'], 'run time (UTC)')),
        ('Engine (requirement ENG-01)', req_row(ctx, 'ENG-01')),
        ('Throttle architecture', ctx.v('CMB', '/decisions/throttle_architecture')),
        ('Propellants and grain (ENG-12)', req_row(ctx, 'ENG-12')),
        ('Thrust vector control (ENG-07)', req_row(ctx, 'ENG-07')),
        ('Ignition', ctx.v('CMB', '/decisions/igniter')),
        ('CAD configuration', ctx.v('PROP', '/status', tag='DESIGN')),
        ('Combustion interface status', ctx.v('CMB', '/status', tag='DESIGN')),
        ('Electronics interface status', ctx.v('ELE', '/status', tag='DESIGN')),
        ('Review register note', ctx.v('SUP', '/note', tag='DESIGN')),
        ('Decision overrides in force', D['ovr_summary']),
    ]
    o.append(dtable(['Item', 'Value'], [[l, tvtxt(v, 520)] for l, v in rows], widths=['24%', '76%'],
                    caption='Identification. Text values are quoted from their sources (trace references link to Appendix A).'))
    o.append(doc.h(2, '1.1 Separation of evidence'))
    o.append('<p>The programme keeps five kinds of evidence apart. This datasheet labels every value with one of them; none of them is a physical test.</p>')
    sep = [
        ('Conceptual geometry', 'Items defined in text or hand calculation only, not modelled as solids: N2O tank, isolation-valve module mass, head-end bleed path, relief and fill/vent hardware.',
         ctx.v('MEC', '/fixed_module/tank/concept/src', tag='DESIGN')),
        ('CAD solid model', f'CAD {a.cad_version}: STEP solids of record, assembly manifest and GLB display mesh. Software checks only.',
         ctx.v('PROP', '/results/parts_summary', tag='DERIVED')),
        ('Mass budget', 'CAD volume × density for modelled parts, datasheet or assumed masses for COTS items, explicit exclusions (§4.4).',
         ctx.v('BOM', '/mass_sum_note', tag='DERIVED')),
        ('Simulation', 'Quasi-1D combustion and CEA, plume CFD, 6-DOF Monte Carlo, firmware SIL. Predictions with stated inputs and tags.',
         ctx.v('GNC', '/status', tag='SIM')),
        ('Physical validation', 'None performed. Bench, cold-flow and static-fire tests are listed in §12 and executed by the founders.',
         ctx.v('SUP', '/note', tag='DESIGN')),
    ]
    o.append(dtable(['Evidence kind', 'Scope in this datasheet', 'Source statement'],
                    [[k, s, tvtxt(v, 300)] for k, s, v in sep], label_cols=2, widths=['17%', '40%', '43%']))
    o.append(doc.h(2, '1.2 Evidence tags'))
    leg = [('SIM', 'model prediction (CEA, quasi-1D, CFD, 6-DOF, SIL)'), ('DERIVED', 'calculated from tagged inputs (by a specialist or by this generator)'),
           ('ASSUMED', 'engineering assumption pending data'), ('DATASHEET', 'vendor or catalogue value'),
           ('TO-VERIFY', 'value or feature to confirm (vendor, CAD or test)'), ('LITERATURE', 'published reference'),
           ('DESIGN', 'design choice or specification value'), ('REQ', 'requirement (founder or lead)'),
           ('LEAD', 'lead decision recorded in the CHANGELOG'), ('MISSING', 'no value in the sources'),
           ('TO-DEFINE', 'value not yet defined by its owner'), ('PENDING', 'analysis not yet delivered'),
           ('SUPERSEDED', 'withdrawn value, not shown (§13.2)')]
    o.append('<div class="legend">' + ''.join(f'<div>{ev_pill(e)} {esc(t)}</div>' for e, t in leg) + '</div>')
    o.append('<p class="small">Each value is followed by its tag and a trace reference T###. The trace gives the source file, its version and sha256/16, and the exact key (JSON pointer, markdown row or CHANGELOG line and item). Where a source carries a longer tag text, Appendix A keeps it verbatim.</p>')
    o.append(note_box('<b>Decisions newer than combustion.json v2.4.</b> Where an interface file still carries wording that a later lead decision replaced '
                      '(REV-COMB-2 findings R2-01, R2-02 and R2-05), the stale words are <del class="stale">struck through</del> and the decision is '
                      '<ins class="dec">inserted with its override id</ins>. The override table (§13.1) cites the decision text and checks it on every build; '
                      'values the Combustion author withdrew are not shown at all (§13.2).', 'info'))
    o.append(doc.h(2, '1.3 Recent lead decisions folded in'))
    dec = cl.decisions('lead', last=a.decisions)
    o.append(dtable(['Line', 'Date', 'Decision (start of text)'],
                    [[str(d['n']), d['date'] or '', tvtxt(cl.whole(d['n'], 420), None)] for d in dec], label_cols=2,
                    widths=['6%', '11%', '83%'],
                    caption=f'Last {len(dec)} lead decisions in interfaces/CHANGELOG.md ({esc(ctx.src("CL").version)}, sha256/16 {esc(ctx.src("CL").sha16)}).'))
    return '\n'.join(o)


# =============================================================================================
# section 2: key performance
# =============================================================================================
def sec_performance(ctx, doc, a, D):
    idx = D['tpi']
    o = [doc.h(1, '2 Key performance')]
    basis = ctx.v('CMB', '/operating_points/basis', tag='SIM')
    o.append('<p>All performance values are model predictions (quasi-1D port model with CEA thermochemistry), with the regression law '
             'ASSUMED until the T1–T4 static fires. None is measured. Model basis: ' + tvtxt(basis).html + '</p>')
    o.append(doc.h(2, '2.1 Rated point and throttle floor'))
    cols = [(f, f'{lab}, {f * 100:g} %' + (f' ({1 / f:g}:1)' if f < 1 else '')) for f, lab in
            ((1.0, 'Rated'), (0.2, 'Floor target'), (0.25, 'Floor requirement'), (0.125, 'Stretch floor'))]
    rows = []

    def row(label, key, unit, conv=None, fmt=None, kind=None):
        cells = [label]
        tvs = []
        for f, _ in cols:
            tv = tp(ctx, idx, f, key, unit, conv)
            tvs.append(tv)
            if kind == 'p':
                cells.append(Cell(pres(ctx, tv), [tv]))
            else:
                cells.append(Cell(tv.h(fmt=fmt), [tv]))
        rows.append(cells)
        return tvs

    F = row('Thrust F (sea level)', 'F_N', 'N', fmt='.1f')
    P = row('Chamber pressure Pc', 'Pc_Pa', 'Pa', kind='p')
    row('Mixture ratio O/F', 'OF', '', fmt='.2f')
    isp = row('Specific impulse Isp (sea level)', 'Isp_SL_s', 's', fmt='.1f')
    rows.append(['Specific impulse as exhaust velocity'] + [Cell(t.h(fmt='.0f'), [t]) for t in
                [ctx.d(i.value * G0 if i.value is not None else None, 'N·s/kg', 'Isp × g0, g0 = 9.80665 m/s² (defined constant)', [i]) for i in isp]])
    mo = row('Oxidiser mass flow', 'mdot_ox_kg_s', 'kg/s', fmt='.4f')
    mf = row('Fuel mass flow', 'mdot_fuel_kg_s', 'kg/s', fmt='.4f')
    rows.append(['Total mass flow'] + [Cell(t.h(fmt='.4f'), [t]) for t in
                [ctx.d((x.value + y.value) if (x.value is not None and y.value is not None) else None, 'kg/s', 'ṁ_ox + ṁ_fuel', [x, y]) for x, y in zip(mo, mf)]])
    row('Pintle lift', 'pintle_lift_m', 'mm', conv=(1000, 0, 'm to mm'), fmt='.3f')
    row('Injector stiffness dP/Pc', 'dP_inj_over_Pc', '', fmt='.2f')
    req = [ctx.v('CMB', '/operating_points/max_thrust/F_N', 'N'), ctx.v('CMB', '/operating_points/floor_target_20pct/F_N', 'N'),
           ctx.v('CMB', '/operating_points/floor_requirement_25pct/F_N', 'N'), ctx.v('CMB', '/operating_points/floor_stretch_12p5pct/F_N', 'N')]
    rows.append(['Requirement or target thrust'] + [num_cell(t, '.1f') for t in req])
    cap = D['cl'].item(170, 1)
    st = [cap,
          ctx.v('CMB', '/operating_points/floor_target_20pct/status', tag='SIM'),
          ctx.v('CMB', '/operating_points/floor_requirement_25pct/status', tag='SIM'),
          ctx.v('CMB', '/operating_points/floor_stretch_12p5pct/status', tag='SIM')]
    rows.append(['Model status at the point', Cell('ENG-01 at the 25 bar cap: see the note below ' + st[0].pill() + st[0].ref(), [st[0]])]
                + [tvtxt(t, 120) for t in st[1:]])
    o.append(dtable(['Quantity'] + [c[1] for c in cols], rows, widths=['24%', '19%', '19%', '19%', '19%'],
                    caption='Operating points from combustion.json /operating_points/throttle_points_20C_initial_port (tank state and port as in the model basis above). '
                            'Column fractions are the selection keys of the point list.'))
    o.append(note_box(f'<b>ENG-01 at the software cap.</b> {tvtxt(cap).html}', 'info'))
    D['thr_plot_tvs'] = F + P
    fails = []
    fl = ctx.raw('CMB', '/operating_points/pressure_limits/full_stroke_failure_S230/v', default=[]) or []
    eng12a = md_bullet(ctx, 'REQ', 'Amendments after rev 2', 'ENG-12:', 'REQ')
    arm_max = rx_text(ctx, eng12a, r'at ARM 15-(\d+) C', '°C', tag='REQ')
    n_out = 0
    for k, r in enumerate(fl):
        fb = '/operating_points/pressure_limits/full_stroke_failure_S230'
        if arm_max.value is not None and r.get('T_tank_C') is not None and r['T_tank_C'] > arm_max.value:
            n_out += 1
            continue
        tvF = ctx.v('CMB', f'{fb}/v/{k}/F_N', 'N', tag='SIM', tag_ptr=fb)
        tvP = ctx.v('CMB', f'{fb}/v/{k}/Pc_bar', 'bar', tag='SIM', tag_ptr=fb)
        tvT = ctx.v('CMB', f'{fb}/v/{k}/T_tank_C', '°C', tag='SIM', tag_ptr=fb)
        tvC = ctx.v('CMB', f'{fb}/v/{k}/Cd', '', tag='SIM', tag_ptr=fb)
        fails.append({'F': tvF.value, 'Pc': tvP.value, 'tvs': [tvF, tvP, tvT, tvC]})
    pts = []
    for f in sorted(idx, reverse=True):
        pts.append({'F': tp(ctx, idx, f, 'F_N', 'N'), 'Pc': tp(ctx, idx, f, 'Pc_Pa', 'Pa'), 'OF': tp(ctx, idx, f, 'OF'),
                    'Isp': tp(ctx, idx, f, 'Isp_SL_s', 's'), 'dP': tp(ctx, idx, f, 'dP_inj_over_Pc')})
    capv = ctx.v('CMB', '/decisions/normal_software_Pc_cap_Pa', 'Pa')
    meopv = ctx.v('CMB', '/decisions/chamber_MEOP_Pa', 'Pa')
    stiff = rx(ctx, 'CMB', '/stability/criteria', r'dP/Pc >= ([\d.]+)', '', tag='DERIVED')
    marks = [(F[1].value, 'floor target'), (F[0].value, 'rated')]
    tts = [f['tvs'][2].value for f in fails if len(f['tvs']) > 2]
    cds = [f['tvs'][3].value for f in fails if len(f['tvs']) > 3]
    flab = 'pintle stuck at full stroke (SIM, v2.3 line-loss model)' + (f', tank {min(tts):g}–{max(tts):g} °C, Cd {min(cds):g}–{max(cds):g}' if tts and cds else '')
    mb0 = ctx.v('CMB', '/meop_basis_v2p4/v/basis_bar', 'bar', tag_ptr='/meop_basis_v2p4')
    src = plot_throttle(a, pts, fails, capv.value / 1e5, meopv.value / 1e5, stiff.value, marks, flab,
                        basis=(mb0.value, f'MEOP basis v2.4 {mb0.value:g} bar (thrust not published)') if mb0.value is not None else None)
    ref_ids = [t.tid for p in pts for t in p.values()] + [t.tid for f in fails for t in f['tvs']] + [capv.tid, meopv.tid, stiff.tid, mb0.tid, arm_max.tid]
    o.append(fig_html(src, 'Throttle characteristics over the operating-point list (SIM) and the stuck-pintle full-stroke cases. '
                      'Dotted lines mark the floor-target and rated points; dashed lines the software cap, the MEOP and the injector-stiffness rule; '
                      f'the dash-dot line is the v2.4 MEOP basis (§2.4). Stuck-pintle rows with a tank above the ARM limit ({arm_max.num()} °C, ENG-12 amendment) '
                      f'are not credible ignition states and are not plotted ({n_out} of {len(fl)} rows).', ref_ids, 'wide'))

    o.append(doc.h(2, '2.2 Nozzle and chamber'))
    nz = [
        ('Throat diameter D<sub>t</sub>', ctx.v('CMB', '/gas_path/nozzle/throat_diameter_m', 'mm', conv=(1000, 0, 'm to mm')), '.2f'),
        ('Exit diameter D<sub>e</sub>', ctx.v('CMB', '/gas_path/nozzle/exit_diameter_m', 'mm', conv=(1000, 0, 'm to mm')), '.2f'),
        ('Expansion ratio ε', ctx.v('CMB', '/gas_path/nozzle/expansion_ratio', tag_ptr='/decisions/expansion_ratio'), '.2f'),
        ('Throat area A<sub>t</sub>', ctx.v('CMB', '/gas_path/nozzle/throat_area_m2', 'mm²', conv=(1e6, 0, 'm² to mm²')), '.2f'),
        ('Exit-to-ambient pressure ratio at rated point', ctx.v('CMB', '/gas_path/nozzle/pe_over_pa_at_max'), '.3f'),
        ('Characteristic velocity c* (delivered, η<sub>c*</sub> 0.92)', ctx.v('CMB', '/operating_points/max_thrust/cstar_delivered_m_s', 'm/s'), '.0f'),
        ('Ratio of specific heats, chamber', ctx.v('CMB', '/operating_points/max_thrust/gamma_chamber'), '.4f'),
        ('Molar mass, chamber', ctx.v('CMB', '/operating_points/max_thrust/MW_chamber', 'kg/kmol'), '.2f'),
        ('Gas-path length, injector face to exit', ctx.v('CMB', '/gas_path/overall/gas_path_length_injector_face_to_exit_m', 'mm', conv=(1000, 0, 'm to mm')), '.1f'),
        ('Free chamber volume, initial', ctx.v('CMB', '/gas_path/overall/free_chamber_volume_initial_m3', 'cm³', conv=(1e6, 0, 'm³ to cm³')), '.1f'),
        ('Characteristic length L*, initial', ctx.v('CMB', '/gas_path/overall/L_star_initial_m', 'm'), '.3f'),
        ('Chamber gas-side diameter (pre/post chamber)', ctx.v('CMB', '/gas_path/chamber_gas_diameter_m', 'mm', conv=(1000, 0, 'm to mm')), '.1f'),
        ('Case tube OD × wall', None, None),
    ]
    rows = []
    for lab, tv, f in nz:
        if tv is None:
            od = ctx.v('CMB', '/gas_path/case/OD_m', 'mm', conv=(1000, 0, 'm to mm'))
            wl = ctx.v('CMB', '/gas_path/case/wall_m', 'mm', conv=(1000, 0, 'm to mm'))
            rows.append([lab, cat(od.h('.2f'), ' × ', wl.h('.3f'), Cell('', [od, wl]))])
            continue
        rows.append([lab, Cell(tv.h(fmt=f), [tv])])
    t0 = ctx.v('CMB', '/operating_points/max_thrust/Tc_ideal_K', 'K')
    t1 = ctx.v('CMB', '/operating_points/max_thrust/T0_delivered_K', 'K')
    rows.append(['Chamber temperature, ideal (CEA)', Cell(temp_k(t0, 0), [t0])])
    rows.append(['Stagnation temperature, delivered (η<sub>c*</sub>²)', Cell(temp_k(t1, 0), [t1])])
    rows.append(['Throat insert material', tvtxt(ctx.v('CMB', '/gas_path/nozzle/graphite'), 220)])
    o.append(dtable(['Quantity', 'Value'], rows, widths=['46%', '54%'], caption='Nozzle and chamber at the rated point (combustion.json).'))

    o.append(doc.h(2, '2.3 Burn, starts and relight'))
    lw = [ctx.v('CMB', f'/light_windows/v/{k}', 's', tag_ptr='/light_windows') for k in ('flight_first_start', 'flight_relight', 'stand')]
    rows = [
        ['Starts per flight', tvtxt(ctx.v('CMB', '/igniter/starts_per_flight'))],
        ['Restart requirement (ENG-04)', tvtxt(req_row(ctx, 'ENG-04'), 700)],
        ['Light window W from the lift command: flight first start / flight relight / stand',
         cat(lw[0].h('.2f'), ' / ', lw[1].h('.2f'), ' / ', lw[2].h('.2f'))],
        ['Relight planning value (flight software)', num_cell(ctx.v('GNC', '/requirements/ignition/relight_planning_value_s', 's'), '.2f')],
        ['Planning value on an UNPRIMED flag (option c)', num_cell(ctx.v('GNC', '/requirements/ignition/relight_planning_value_s/option_c_unprimed_s', 's'), '.2f')],
        ['A1 burn time, nominal 6-DOF (FSW v2.6 basis)', num_cell(ctx.v('GNC', '/flight_profile/mission_plan_v3/v/A1/nominal_fsw_v2.6_planning_1.4s/burn_time_s', 's', tag='SIM'), '.2f')],
        ['N2O vented per relight purge, plan maximum', num_cell(ctx.v('CMB', '/relight_purge/v/N2O_vented_g/plan_max', 'g', tag_ptr='/relight_purge'), '.0f')],
        ['Grain and throat insert life (ENG-06)', tvtxt(req_row(ctx, 'ENG-06'), 600)],
    ]
    o.append(dtable(['Item', 'Value'], rows, widths=['40%', '60%']))

    o.append(doc.h(2, '2.4 Pressure limits and physical worst case'))
    if ctx.ovr:
        r7 = next((e for e in ctx.ovr.entries if e['id'] == 'OVR-07' and e['status'] == 'ACTIVE'), None)
        rv = next((t for t in (r7['srcs'] if r7 else []) if t.sid == 'RV2'), None)
        if rv is not None:
            of8 = rx_text(ctx, rv, r'O/F (\d+)', '', tag='DERIVED')
            if of8.value is not None:
                D['fa1_plot_note'] = f'single point at ASSUMED O/F {of8.value:g}; envelope pending (OVR-07)'
    cap25 = ctx.v('CMB', '/decisions/normal_software_Pc_cap_Pa', 'Pa')
    ab30 = ctx.v('CMB', '/decisions/ecu_overpressure_abort_Pa', 'Pa')
    hw = rx(ctx, 'ELE', '/sensors/pressure_transducers/hw_ovp', r'=\s*([\d.]+) bar abs', 'bar', note='nominal trip of the hardware comparator')
    ll_r = ctx.v('CMB', '/late_light_and_meop/v/decomposition_peak_bar/pad_15C/rounded', 'bar', tag_ptr='/late_light_and_meop')
    ll_s = ctx.v('CMB', '/late_light_and_meop/v/decomposition_peak_bar/pad_15C/sharp', 'bar', tag_ptr='/late_light_and_meop')
    mb = ctx.v('CMB', '/meop_basis_v2p4/v/basis_bar', 'bar', tag_ptr='/meop_basis_v2p4')
    mm_ = ctx.v('CMB', '/meop_basis_v2p4/v/margin_to_MEOP_bar', 'bar', tag_ptr='/meop_basis_v2p4')
    meop = ctx.v('CMB', '/decisions/chamber_MEOP_Pa', 'Pa')
    fa = ctx.v('CMB', '/late_light_and_meop/v/fuel_assisted_relight_bar/burn_1ms', 'bar', tag_ptr='/late_light_and_meop')
    fas = ctx.v('CMB', '/late_light_and_meop/v/fuel_assisted_status', tag_ptr='/late_light_and_meop')
    bn = ctx.v('CMB', '/operating_points/pressure_limits/blocked_nozzle_bound_Pa', 'Pa')
    proof = ctx.v('CMB', '/decisions/proof_pressure_Pa', 'Pa')
    pmin = ctx.v('CMB', '/meop_basis_v2p4/v/proof_margin_min_bar', 'bar', tag_ptr='/meop_basis_v2p4')
    tmeop = ctx.v('CMB', '/operating_points/tank_MEOP_Pa', 'Pa')
    trange = ctx.v('CMB', '/operating_points/tank_pressure_range_Pa', 'bar', conv=(1e-5, 0, 'Pa to bar'))
    cl = D['cl']
    eng09a = md_bullet(ctx, 'REQ', 'Amendments after rev 2', 'ENG-09:', 'REQ')
    t_il = rx_text(ctx, eng09a, r'T_tank <= (\d+) C', '°C', tag='REQ')
    c172_4 = cl.item(172, 4)
    p_il = rx_text(ctx, c172_4, r'(\d+) C / ([\d.]+) bar abs', 'bar', tag='LEAD', group=2)
    guard = ctx.missing('Tank interlock guard band = total channel uncertainty (Electronics states it; CHANGELOG 172 (4))', 'TO-DEFINE')
    c172_2 = cl.item(172, 2)
    fa_int = rx_text(ctx, c172_2, r'quasi-static (\d+) bar abs', 'bar', tag='LEAD')
    fa_note = ctx.ovr.note_for('OVR-07') if ctx.ovr else None
    tlow = ctx.d(trange.value[0] if isinstance(trange.value, list) else None, 'bar', 'lower end of combustion.json tank_pressure_range_Pa', [trange])
    F1 = D['fa1'] = fa1_envelope(ctx, D)
    if F1:
        pk = F1['pk']
        fa1_rows = [
            ['FA-1 envelope, head peak: baseline / sharp entrance / upper bracket (v2.4a)',
             cat(pres_bar(ctx, pk[0]), ' / ', pres_bar(ctx, pk[1]), ' / ', pres_bar(ctx, pk[2]), Cell('', pk)), 'SIM on an ASSUMED construct (§2.5)'],
            ['FA-1 structural load (lead decision): quasi-static at head and aft, all parts', Cell(pres_bar(ctx, F1['load'], 0), [F1['load']]),
             f'replaces the interim check (CHANGELOG {F1["n"]})'],
            ['FA-1 parts with a natural period in the decided band: design / sensitivity pressure',
             cat(pres_bar(ctx, F1['p_des'], 0), ' / ', pres_bar(ctx, F1['p_sens'], 0), Cell('', [F1['p_des'], F1['p_sens']])),
             'Mechanical margins reported, not reviewed (§2.5)' if F1.get('mech') else 'Mechanical margins PENDING (§2.5)']]
        fa1_lad = [('FA-1 envelope, head peak', (pk[0].value, pk[2].value) if None not in (pk[0].value, pk[2].value) else None, C_BAD,
                    'baseline to upper bracket (SIM, ASSUMED construct)'),
                   ('FA-1 structural load', F1['load'].value, C_ACC2, 'quasi-static, head and aft, all parts (LEAD)'),
                   ('FA-1 design / sensitivity', (F1['p_des'].value, F1['p_sens'].value) if None not in (F1['p_des'].value, F1['p_sens'].value) else None,
                    C_ACC2, 'parts in the decided period band (LEAD)')]
        fa1_refs = pk + [F1['load'], F1['p_des'], F1['p_sens']]
        fa1_cap = ('Pressure ladder. FA-1 is shown as the Combustion v2.4a envelope (SIM on an ASSUMED construct) and the lead structural-load decision '
                   '(§2.5); the single point in combustion.json v2.4 is annotated (OVR-07) and not plotted. FA-1 is accepted for design continuation only '
                   '(CHANGELOG 170 (2)).')
    else:
        fa1_rows = [['FA-1 interim structural check until the load envelope is published', Cell(pres_bar(ctx, fa_int, 0), [fa_int]), 'quasi-static at head and aft (CHANGELOG 172 (2))']]
        fa1_lad = [('FA-1 relight pulse, 1 ms', tuple(fa.value) if isinstance(fa.value, list) else fa.value, C_BAD, D.get('fa1_plot_note', 'SIM on ASSUMED inputs')),
                   ('FA-1 interim structural check', fa_int.value, C_ACC2, 'quasi-static, head and aft (LEAD)')]
        fa1_refs = [fa, fa_int]
        fa1_cap = ('Pressure ladder. The FA-1 fuel-assisted relight pulse is a single point at an ASSUMED fuel fraction; its load is being restated as an '
                   'envelope, with an interim quasi-static structural check meanwhile (CHANGELOG 172 (2), OVR-07). FA-1 is accepted for design continuation only '
                   '(CHANGELOG 170 (2)).')
    rows = [
        ['Normal chamber pressure cap (software)', Cell(pres(ctx, cap25), [cap25]), 'LEAD decision; ENG-01/ENG-09'],
        ['ECU over-pressure abort', Cell(pres(ctx, ab30), [ab30]), 'decided channel and persistence: §7.6 (OVR-01)'],
        ['Hardware comparator trip (Pc transducer, nominal)', Cell(pres_bar(ctx, hw, 2), [hw]), 'absolute; band in electronics.json'],
        ['Late-light decomposition peak at the pad (key pad_15C): rounded / sharp port entrance', cat(pres_bar(ctx, ll_r), ' / ', pres_bar(ctx, ll_s), Cell('', [ll_r, ll_s])), 'rounded entrance REQUIRED (CHANGELOG 160 (4))'],
        ['MEOP basis (v2.4) at the ignition interlock, and its margin to MEOP', cat(pres_bar(ctx, mb, 2), ' at T<sub>tank</sub> ≤ ', t_il.h(), '; margin ', mm_.h('.2f'), Cell('', [mb, t_il, mm_])),
         'stuck pintle at full stroke, worst corner of the bands; replaces the v2.3 basis (§13.2)'],
        ['Chamber MEOP', Cell(pres(ctx, meop), [meop]), 'kept with the ignition interlock (ENG-09 amendment)'],
        ['Fuel-assisted relight pulse (FMEA FA-1, key burn_1ms)', cat(pres_bar(ctx, fa), fa_note or '', Cell('', [fa])), tvtxt(fas, 120)],
        *fa1_rows,
        ['Blocked-nozzle bound (chamber at tank vapour pressure)', Cell(pres(ctx, bn), [bn]), 'below yield (FEA PENDING)'],
        ['Proof pressure (ENG-09) and its minimum margin above the MEOP basis', cat(pres(ctx, proof), '; margin ≥ ', pmin.h('.1f'), Cell('', [proof, pmin])), 'hydro proof, founders'],
        ['Tank MEOP', Cell(pres(ctx, tmeop), [tmeop]), 'tank not yet in CAD'],
        ['Tank pressure at ARM, saturated: lower end / ignition interlock', cat(pres_bar(ctx, tlow), ' / ', pres_bar(ctx, p_il, 2), ' less the guard band ', guard.h(), Cell('', [tlow, p_il, guard])),
         'interlock per CHANGELOG 172 (4); the combustion.json range still spans the old ARM range (OVR-04)'],
    ]
    o.append(dtable(['Limit', 'Value', 'Note'], rows, label_cols=1, widths=['38%', '34%', '28%'], free_cols=(2,),
                    caption='Pressure ladder (absolute unless noted). The note column is an editorial pointer, not data.'))
    # note column is a generator remark, counted as label: rebuild stats for column 2 strings
    lad = [('Normal Pc cap (software)', cap25.value / 1e5, C_OK, 'LEAD'),
           ('ECU over-pressure abort', ab30.value / 1e5, C_WARN, 'LEAD'),
           ('HW comparator (nominal)', hw.value, C_WARN, 'DERIVED'),
           ('Late-light peak, rounded entrance', ll_r.value, C_GREY, 'SIM'),
           ('Late-light peak, sharp entrance', ll_s.value, C_GREY, 'SIM'),
           ('MEOP basis v2.4 (ignition interlock)', mb.value, C_ACC, 'SIM'),
           ('Chamber MEOP', meop.value / 1e5, C_BAD, 'LEAD'),
           *fa1_lad,
           ('Blocked-nozzle bound', bn.value / 1e5, C_GREY, 'DERIVED'),
           ('Proof', proof.value / 1e5, C_ACC2, 'LEAD'),
           ('Tank MEOP', tmeop.value / 1e5, C_GREY, 'LEAD')]
    lad = [x for x in lad if x[1] is not None]
    src = plot_pressure_ladder(a, lad)
    o.append(fig_html(src, fa1_cap, [t.tid for t in [cap25, ab30, hw, ll_r, ll_s, mb, meop] + fa1_refs + [bn, proof, tmeop]], 'wide'))
    grng = ctx.v('MEC', '/gimbal/range_deg', '°')
    lat5 = ctx.d(F[0].value * math.sin(math.radians(grng.value)), 'N', f'F_rated × sin(gimbal range {grng.value:g}°)', [F[0], grng])
    wF = ctx.missing('Physical worst-case thrust at the v2.4 MEOP basis: combustion.json v2.4 publishes the basis pressure only', 'MISSING')
    latw = ctx.missing('Lateral thrust at the gimbal range for the physical worst case (needs the worst-case thrust)', 'MISSING')
    cd_b = rx_text(ctx, c172_4, r'full-stroke Cd <= ([\d.]+)', '', tag='LEAD')
    rows = [
        ['Basis', tvtxt(ctx.v('CMB', '/decisions/chamber_MEOP_Pa/tag', tag='LEAD'), 260)],
        ['Chamber pressure at the basis (pintle stuck at full stroke)', cat(pres_bar(ctx, mb, 2), ' at T<sub>tank</sub> ≤ ', t_il.h(), Cell('', [mb, t_il]))],
        ['Thrust at the basis', Cell(wF.h(), [wF])],
        ['Full-stroke injector Cd accepted in CF-1/CF-3 (otherwise MEOP is restated)', num_cell(cd_b, '.2f')],
        ['Lateral thrust at the gimbal range: rated / worst case', cat(lat5.h('.1f'), ' / ', latw.h(), Cell('', [lat5, latw]))],
        *([['Relight thrust transient (FA-1): interim structural load, confirmed bounding by the envelope', cat(F1['f_int'].h('.1f'), ' × ', F1['t_int'].h('g'))]] if F1 else []),
        ['Airframe ICD statement (ICD §3)', tvtxt(md_row(ctx, 'ICD', '3. Loads', 'Physical worst-case thrust', 1, tag_col=2), 300)],
        ['Pressure-part requirement (ENG-09)', tvtxt(req_row(ctx, 'ENG-09'), 700)],
        ['ENG-09 amendment', tvtxt(eng09a, 300)],
    ]
    o.append(dtable(['Physical worst case', 'Value'], rows, widths=['32%', '68%'],
                    caption='The v2.3 stuck-pintle basis assumed a tank above the ignition interlock, which is no longer a credible ignition state; the thrust at '
                            'the v2.4 basis is not published, so the structural thrust case stays open (§13.3, C-07).'))
    D['worst'] = {'F': wF, 'P': mb}
    if F1:
        o += sec_fa1(ctx, doc, F1)
    return '\n'.join(o)


def fig_html(src, caption, refs, cls=''):
    refs = [r for r in refs if r]
    rtxt = ''
    if refs:
        rr = sorted(set(refs), key=lambda s: int(s[1:]))
        rtxt = ' <span class="figref">Data: ' + ', '.join(f'<a class="tr" href="#{r}">{r}</a>' for r in rr[:40]) + \
               (f' and {len(rr) - 40} more' if len(rr) > 40 else '') + '</span>'
    return f'<figure class="{cls}"><img src="{src}"><figcaption>{caption}{rtxt}</figcaption></figure>'


# =============================================================================================
# section 3: throttle and thrust vector control
# =============================================================================================
def sec_throttle_tvc(ctx, doc, a, D):
    o = [doc.h(1, '3 Throttle and thrust vector control')]
    o.append(doc.h(2, '3.1 Throttle'))
    E = '/eng03_pintle_rate/rate_map/summary'
    rows = [
        ['Throttle requirement (ENG-02)', tvtxt(req_row(ctx, 'ENG-02'), 600)],
        ['Throttle floor flown by GNC (fraction of rated)', num_cell(ctx.v('GNC', '/requirements/throttle/floor_frac_required_max', '%', conv=(100, 0, 'fraction to %')), '.0f')],
        ['Injector', tvtxt(ctx.v('CMB', '/gas_path/injector/type'))],
        ['Pintle seat diameter / stroke', cat(ctx.v('CMB', '/gas_path/injector/seat_diameter_m', 'mm', conv=(1000, 0, 'm to mm')).h('.2f'), ' / ',
                                              ctx.v('CMB', '/gas_path/injector/stroke_m', 'mm', conv=(1000, 0, 'm to mm')).h('.2f'),
                                              Cell('', [ctx.recent[-1], ctx.recent[-2]]))],
        ['Discharge coefficient Cd (two-phase N2O)', num_cell(ctx.v('CMB', '/gas_path/injector/Cd'), '.2f')],
        ['Cd acceptance criterion', tvtxt(ctx.v('CMB', '/gas_path/injector/Cd_acceptance', tag='DERIVED'), 260)],
        ['Pintle drive', tvtxt(ctx.v('ELE', '/actuators/pintle_throttle/model', tag_ptr='/actuators/pintle_throttle/tags'))],
        ['Pintle servo mass', num_cell(ctx.v('ELE', '/actuators/pintle_throttle/datasheet_class/mass_g', 'g', tag_ptr='/actuators/pintle_throttle/tags'), '.0f')],
        ['Pintle supply rail', tvtxt(ctx.v('ELE', '/actuators/pintle_throttle/rail', tag='DESIGN'))],
        ['Pintle position resolution', num_cell(ctx.v('CMB', '/valves_and_actuators/pintle_actuator/position_resolution_m', 'µm', conv=(1e6, 0, 'm to µm')), '.0f')],
        ['Throttle response requirement (ENG-03)', tvtxt(req_row(ctx, 'ENG-03'), 700)],
        ['Start ramp', num_cell(ctx.v('ELE', '/eng03_pintle_rate/start_ramp', 'N/s'), '.0f')],
        ['Opening rate, minimum over the map: nominal / corner', cat(ctx.v('ELE', f'{E}/nominal/open_min_N_per_s', 'N/s', tag='SIM', tag_ptr='/eng03_pintle_rate/rate_map/reduced_model_for_gnc/B_two_state/tags').h('.0f'), ' / ',
                                                                    ctx.v('ELE', f'{E}/corner/open_min_N_per_s', 'N/s', tag='SIM').h('.0f'), Cell('', ctx.recent[-2:]))],
        ['Closing rate, minimum over the map (corner)', num_cell(ctx.v('ELE', f'{E}/corner/close_min_N_per_s', 'N/s', tag='SIM'), '.0f')],
        ['Map states opening at ≥ 2500 N/s: nominal / corner', cat(ctx.v('ELE', f'{E}/nominal/states_open_ge_2500', tag='SIM').h(), ' / ',
                                                                  ctx.v('ELE', f'{E}/corner/states_open_ge_2500', tag='SIM').h(), Cell('', ctx.recent[-2:]))],
        ['Chamber filling time constant', num_cell(ctx.v('CMB', '/operating_points/chamber_fill_time_constant_s', 'ms', conv=(1000, 0, 's to ms')), '.1f')],
        ['Shutdown requirement (ENG-05)', tvtxt(req_row(ctx, 'ENG-05'), 600)],
        ['Actuator speed finding (Combustion)', tvtxt(ctx.v('CMB', '/valves_and_actuators/pintle_actuator/speed_checks/conclusion', tag='SIM'), 420)],
    ]
    o.append(dtable(['Item', 'Value'], rows, widths=['34%', '66%']))

    o.append(doc.h(2, '3.2 Thrust vector control'))
    S = '/actuators/tvc_A'
    rows = [
        ['Architecture', tvtxt(ctx.v('MEC', '/gimbal/architecture'), 400)],
        ['Gimbal range (vector norm) / mechanical stop', cat(ctx.v('MEC', '/gimbal/range_deg', '°').h('.1f'), ' / ', ctx.v('MEC', '/gimbal/mechanical_stop_deg', '°').h('.1f'), Cell('', ctx.recent[-2:]))],
        ['Pivot location', tvtxt(ctx.v('MEC', '/gimbal/pivot_location'), 300)],
        ['Pivot to injector face / to nozzle exit', cat(ctx.v('MEC', '/gimbal/pivot_from_injector_face_m', 'mm', conv=(1000, 0, 'm to mm')).h('.1f'), ' / ',
                                                        ctx.v('MEC', '/gimbal/pivot_from_nozzle_exit_m', 'mm', conv=(1000, 0, 'm to mm')).h('.1f'), Cell('', ctx.recent[-2:]))],
        ['Gimbal bearings', tvtxt(ctx.v('MEC', '/gimbal/bearings'))],
        ['TVC actuators', tvtxt(ctx.v('ELE', f'{S}/model', tag='DATASHEET'))],
        ['Actuator mass (each)', num_cell(ctx.v('ELE', f'{S}/mass_kg', 'kg'), '.3f')],
        ['Actuator stall torque / no-load speed at 7.4 V', cat(ctx.v('ELE', f'{S}/stall_torque_Nm/v/7.4V', 'N·m', tag_ptr=f'{S}/stall_torque_Nm').h('.2f'), ' / ',
                                                               ctx.v('ELE', f'{S}/noload_speed_dps/v/7.4V', '°/s', tag_ptr=f'{S}/noload_speed_dps').h('.0f'), Cell('', ctx.recent[-2:]))],
        ['Actuator command rate', num_cell(ctx.v('ELE', f'{S}/update_rate_Hz', 'Hz'), '.0f')],
        ['Linkage ratio n (servo angle / engine angle)', num_cell(ctx.v('MEC', '/tvc_actuation/gear_ratio_n'), '.1f')],
        ['Engine-angle resolution / backlash', cat(ctx.v('MEC', '/tvc_actuation/resolution_deg_engine', '°').h('.4f'), ' / ',
                                                   ctx.v('MEC', '/tvc_actuation/backlash_deg_engine', '°').h('.4f'), Cell('', ctx.recent[-2:]))],
        ['Required slew (ENG-07)', num_cell(ctx.v('GNC', '/requirements/gimbal/rate_min_dps', '°/s'), '.0f')],
        ['Required gimbal angular acceleration', num_cell(ctx.v('GNC', '/requirements/gimbal/angular_accel_min_rad_s2', 'rad/s²'), '.1f')],
        ['Slew status, mechanical.json v2', tvtxt(ctx.v('MEC', '/tvc_actuation/ENG-07_rate_status', tag='DERIVED'), 300)],
        ['Design engine moment: ENG-10 / Mechanical as built / GNC parts load',
         cat(Cell(tvtxt(req_row(ctx, 'ENG-10'), 160).html, [ctx.recent[-1]]), '<br>',
             ctx.v('MEC', '/tvc_actuation/design_loads/v/M_engine_GS_Nm', 'N·m', tag_ptr='/tvc_actuation/design_loads').h('.2f'), ' / ',
             ctx.v('GNC', '/design_limit_loads/hinge_moment_design_Nm', 'N·m').h('.1f'), Cell('', ctx.recent[-2:]))],
        ['Axis stiffness, structure + rods at centre (α / β)', num_cell(ctx.v('MEC', '/tvc_actuation/axis_stiffness_table/v/centre/mech_T', 'N·m/rad', tag='SIM', tag_ptr='/tvc_actuation/axis_stiffness_Nm_per_rad'), '.0f')],
        ['Stiffness requirement (ENG-11)', tvtxt(req_row(ctx, 'ENG-11'), 400)],
        ['Rocking mode, first (range over poses)', num_cell(ctx.v('MEC', '/tvc_actuation/rocking_mode_Hz', 'Hz'), '.1f')],
        ['Stiffness and rocking-mode status', tvtxt(ctx.v('MEC', '/tvc_actuation/ENG-11_status', tag='DERIVED'), 420)],
    ]
    o.append(dtable(['Item', 'Value'], rows, widths=['34%', '66%']))
    # slew vs load (Mechanical calc v2)
    cases = ctx.raw('SLEW', '/cases', default={}) or {}
    loads = ctx.raw('SLEW', '/loads_Nm', default={}) or {}
    names = {}
    volts = sorted({c.split('|')[0] for c in cases}, key=lambda s: float(s.rstrip('V')))
    lrows, plot_cases, refs = [], [], []
    for lk in loads:
        lt = ctx.v('SLEW', ptr_join('loads_Nm', lk), 'N·m', tag='DERIVED', tag_ptr='/method')
        cells = [names.get(lk, lk), num_cell(lt, '.2f')]
        dv = {}
        for v in volts:
            key = f'{v}|{lk}'
            if key in cases:
                t = ctx.v('SLEW', ptr_join('cases', key, 'worst_any_motion_at_7deg', 'dps'), '°/s', tag='DERIVED', tag_ptr='/method')
                refs.append(t.tid)
                cells.append(num_cell(t, '.1f'))
                dv[float(v.rstrip('V'))] = t.value
            else:
                cells.append(ctx.missing(f'slew {key}'))
        lrows.append(cells)
        if lk != 'no_load':
            plot_cases.append((f'{names.get(lk, lk)}\n{lt.value:.2f} N·m', dv))
    o.append(dtable(['Hinge load case', 'Load'] + [f'Slew at {v} [°/s]' for v in volts], lrows, widths=['30%', '16%'] + ['18%'] * len(volts),
                    caption=f'Worst-direction engine slew at 7° (any motion), Mechanical actuator_slew_v2 ({esc(src_label(ctx, "SLEW"))}). '
                            'Linear servo torque–speed lines (ASSUMED shape).'))
    reqv = ctx.raw('GNC', '/requirements/gimbal/rate_min_dps/v', default=100.0)
    src = plot_slew(a, plot_cases, reqv)
    o.append(fig_html(src, 'Engine slew at 7° by hinge load case and plug voltage. ENG-07 is OPEN and marginal at the v2 load '
                      '(REQUIREMENTS amendment); B-TVC-1 measures it.', refs, 'wide'))
    return '\n'.join(o)


# =============================================================================================
# section 4: geometry and mass
# =============================================================================================
def sec_geometry_mass(ctx, doc, a, D):
    o = [doc.h(1, '4 Geometry and mass')]
    o.append(note_box('<b>Renders are visualisation only.</b> They are produced by gen/render_views.sh from the tessellated GLB display mesh '
                      f'of CAD {esc(a.cad_version)} (GLB sha256/16 {esc(ctx.src("GLB").sha16)}). They are not drawings and carry no tolerances. '
                      'Dimensions printed on them are bounding-box extents from the assembly manifest; the STEP solids are the CAD of record.', 'warn'))
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
        ['Mechanical build record, neutral assembly bounds', tvtxt(ctx.v('PROP', '/results/assembly/neutral/bounds_mm', 'mm', tag='DERIVED'))],
        ['Swept radial envelope, worst band (Mechanical checks)', tvtxt(ctx.v('CHK', '/swept_worst_band', tag='TO-VERIFY'), 400)],
        ['Airframe bay requirement (ICD §2)', tvtxt(md_row(ctx, 'ICD', '2. Engine bay', 'Engine bay inner diameter', 1, tag_col=2))],
        ['Engine zone (ICD §2)', tvtxt(md_row(ctx, 'ICD', '2. Engine bay', 'Engine zone, engine frame', 1, tag_col=2), 300)],
    ]
    o.append(dtable(['Dimension', 'Value'], rows, widths=['42%', '58%'],
                    caption=f'Envelope from the union of the {g["n_inst"]} instance bounding boxes in the assembly manifest (engine frame, mm, origin at the gimbal pivot, +z forward). '
                            'An axis-aligned box does not bound the radial extent: the radial sweep check is listed separately.'))
    o.append(doc.h(2, '4.2 Assembly views'))
    if R.get('iso'):
        o.append(f'<figure class="render iso"><img src="{R["iso"]["file"]}"><figcaption>Isometric view, CAD {esc(a.cad_version)}, neutral pose '
                 f'(render {esc(R["iso"]["png_sha16"])}). Visualisation only.</figcaption></figure>')
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
                 'Visualisation of display geometry, not a drawing.'
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
    o.append('<p class="small">Each family is rendered at its assembly position (not exploded). Line counts and masses are sums over the BOM lines '
             'of the family (qty × unit mass, DERIVED by this generator; the transport lock is excluded).</p>')

    o.append(doc.h(2, '4.4 Mass'))
    MP = '/states'
    states = ['wet', 'mid', 'burnout', 'nograin']
    groups = ['engine', 'ring', 'horn', 'pushrod', 'fixed', 'all']
    rows = []
    for gname in groups:
        cells = [f'{GROUP_NAMES.get(gname, gname)}']
        for s_ in states:
            t = ctx.v('MP', f'{MP}/{s_}/{gname}/m_kg', 'kg', tag='DERIVED', note='CAD volume × density and COTS masses (massprops)')
            cells.append(num_cell(t, '.4f'))
        rows.append(cells)
    o.append(dtable(['Group', 'Wet (full grain)', 'Mid-burn', 'Burn-out', 'No grain'], rows, widths=['32%', '17%', '17%', '17%', '17%'],
                    caption=f'Mass by subassembly and state, massprops {esc(src_label(ctx, "MP"))}. Group "all" is the CAD model total.'))
    # family sums + exclusions
    fam_rows = []
    for fam, info in D['families'].items():
        fam_rows.append([f'{fam} · {FAMILY_NAMES.get(fam, fam)}', Cell(info['n_tv'].h(), [info['n_tv']]), num_cell(info['mass_tv'], '.4f')])
    fam_rows.append(['Sum of BOM lines (excl. transport lock)', '', num_cell(D['bom_sum_tv'], '.4f')])
    o.append(dtable(['BOM family', 'Lines', 'Mass'], fam_rows, widths=['56%', '14%', '30%'], free_cols=(),
                    caption='Mass by BOM part family (DERIVED: Σ qty × unit mass over the BOM lines).'))
    ex = D['exclusions']
    o.append(dtable(['Not in the CAD mass', 'Mass', 'Status / source'], [[e[0], e[1], e[2]] for e in ex], widths=['34%', '24%', '42%'],
                    caption='Items excluded from the CAD mass. They are not zero: each is carried at its source value or as UNKNOWN.'))
    src = plot_mass(a, [(f'{f} {FAMILY_NAMES.get(f, f)}', info['mass_tv'].value) for f, info in D['families'].items()], D['excl_plot'])
    o.append(fig_html(src, 'CAD mass by BOM family (solid) and items outside the CAD mass (hatched; ranges where the source gives one).',
                      [i['mass_tv'].tid for i in D['families'].values()] + D['excl_refs'], 'wide'))
    o.append(doc.h(2, '4.5 Airframe interface (ICD summary)'))
    keys2 = ['Engine bay inner diameter', 'Engine zone, engine frame', 'Nozzle exit below the pivot', 'Gimbal range', 'Airframe attachment',
             'Ring fit', 'Ring fasteners', 'Main-valve module (MV-P, balanced poppet)', 'Feed across the gimbal']
    keys3 = ['Rated thrust', 'Over-thrust abort', 'Physical worst-case thrust', 'Chamber MEOP / proof', 'Lateral thrust at 7°', 'TVC design moment',
             'Peak axial specific force in flight', 'Touchdown, leg contact', 'Axis stiffness, structure plus rods']
    keys4 = ['Liftoff mass', 'Dry mass / N2O / grain', 'Engine hardware mass and CG']
    rows = []
    for sec, keys in (('2. Engine bay', keys2), ('3. Loads', keys3), ('4. Mass', keys4)):
        rows.append(subrow(f'ICD §{sec}', 2))
        for k in keys:
            rows.append([k, tvtxt(md_row(ctx, 'ICD', sec, k, 1, tag_col=2), 330)])
    o.append(dtable(['Item', 'Value (ICD text)'], rows, widths=['28%', '72%'],
                    caption=f'Selected rows of 00-requirements/ICD-AIRFRAME.md ({esc(src_label(ctx, "ICD"))}). Tag column of the ICD kept as the source tag.'))
    orow = []
    for r in md_table_rows(ctx.src('ICD').text or '', '12. Open items'):
        if r and r[0].startswith('ICD-'):
            orow.append([r[0], tvtxt(ctx.t('ICD', f'§12 row "{r[0]}" col 1', r[1], 'TO-DEFINE', tag_raw='ICD open item'), 240),
                         tvtxt(ctx.t('ICD', f'§12 row "{r[0]}" col 2', r[2] if len(r) > 2 else '', 'DESIGN', tag_raw='ICD owner'))])
    o.append(dtable(['ICD item', 'Open item', 'Owner'], orow, widths=['10%', '62%', '28%'], caption='ICD open items (§12).'))
    o.append(doc.h(2, '4.6 CAD fit and interference checks'))
    poses = ctx.raw('CHK', '/poses', default=[]) or []
    rows = []
    for k, p in enumerate(poses):
        base = f'/poses/{k}'
        rows.append([p.get('pose', str(k)),
                     num_cell(ctx.v('CHK', base + '/interference_not_whitelisted', tag='DERIVED'), 'd'),
                     num_cell(ctx.v('CHK', base + '/unexpected_close_lt_3mm', tag='DERIVED'), 'd'),
                     num_cell(ctx.v('CHK', base + '/min_unexpected_mm', 'mm', tag='DERIVED'), '.3f'),
                     cat(ctx.v('CHK', base + '/wall_min_mm', 'mm', tag='DERIVED').h('.1f'), ' by ', ctx.v('CHK', base + '/wall_min_by', tag='DERIVED').h(pill=False))])
    o.append(dtable(['Pose', 'Interferences (not whitelisted)', 'Unexpected gaps < 3 mm', 'Smallest unexpected gap', 'Smallest wall gap'], rows,
                    widths=['16%', '18%', '18%', '20%', '28%'],
                    caption=f'Software geometric checks by Mechanical ({esc(src_label(ctx, "CHK"))}). A clean software check is not a physical fit check; '
                            'the smallest wall gap is reported by part; a part that mounts on the airframe wall (P-clip) touches it by design (see the swept-envelope row above, TO-VERIFY).'))
    return '\n'.join(o)


def md_bullet(ctx, sid, section_prefix, starts, ev, maxlen=None):
    """Bullet of a markdown section selected by its leading text."""
    for ln in md_section_lines(ctx.src(sid).text or '', section_prefix):
        t = ln.strip()
        if t.startswith('- ') and t[2:].startswith(starts):
            return ctx.t(sid, f'§{section_prefix} bullet "{starts}"', t[2:], ev, tag_raw=f'{sid} bullet')
    ctx.issue('WARN', f'bullet not found {sid} §{section_prefix} {starts!r}')
    return ctx.missing(f'{sid} §{section_prefix} bullet {starts}')


# =============================================================================================
# section 5: parts list
# =============================================================================================
def price_cell(r):
    p = r.l.get('unit_price') or ''
    if r.pstate in ('TO-QUOTE',):
        h = '<span class="q">TO-QUOTE</span>'
    elif r.pstate == 'TO-QUOTE-REF':
        m = re.search(r'reference:?\s*([^)]*)', p)
        h = '<span class="q">TO-QUOTE</span> <span class="small">ref. ' + esc((m.group(1) if m else p)[:70]) + ' (not a DK quote)</span>'
    elif r.pstate == 'DATED-REF':
        h = '<span class="small">' + esc(p[:90]) + '</span> <span class="q">DK delivery TO-QUOTE</span>'
    else:
        h = '<span class="miss">INVALID PRICE FIELD</span>'
    return Cell(h, [r.row_tv])


def sec_bom(ctx, doc, a, D):
    o = [doc.h(1, '5 Parts list')]
    b = ctx.src('BOM').data
    deliv = ctx.v('BOM', '/delivery', tag='REQ')
    curr = ctx.v('BOM', '/currency', tag='DESIGN')
    nl = ctx.v('BOM', '/n_lines', tag='DERIVED')
    ni = ctx.v('BOM', '/n_instances', tag='DERIVED')
    rows = [['Delivery address for quotations', tvtxt(deliv)], ['Price status', tvtxt(curr)],
            ['BOM lines / placed instances', cat(nl.h('d'), ' / ', ni.h('d'))],
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
            nm = esc(l.get('name', ''))
            nm = nm if len(nm) <= 110 else nm[:108].rsplit(' ', 1)[0] + ' …'
            sup = esc((l.get('supplier') or '')[:80])
            o2 = ' <span class="o2">O<sub>2</sub></span>' if str(l.get('oxygen_clean')) == 'True' else ''
            lock = ' <span class="q">transport lock, not placed, excluded from mass</span>' if l.get('groups') == 'lock' else ''
            rows.append([
                Cell(f'<span class="pn">{esc(r.pn)}</span>{r.row_tv.ref()}', [r.row_tv]),
                Cell(f'{nm}{o2}{lock}<div class="sup">{sup}</div>', [r.row_tv]),
                Cell(esc(l.get('qty', '')), [r.row_tv]),
                Cell(esc(short_mat(l.get('material_name'), l.get('material'))) + ('<div class="sup">COTS</div>' if str(l.get('cots')) == 'True' else ''), [r.row_tv]),
                Cell('<span class="small">' + esc((l.get('process') or '')[:70]) + '</span>', [r.row_tv]),
                Cell(r.mass_tv.h('.4f', unit=False), [r.mass_tv]),
                price_cell(r)])
        o.append(dtable(['PN', 'Part and supplier', 'Qty', 'Material', 'Process', 'Unit mass [kg]', 'Price'], rows, label_cols=0, cls='bom',
                        widths=['9%', '33%', '4%', '13%', '15%', '11%', '15%'],
                        caption=(f'{fam} family: {info["n_tv"].value} lines, {info["mass_tv"].value:.4f} kg (Σ qty × unit mass).' if info else None)))
    extra = [r for r in D['bom'] if r.kind != 'lines']
    if extra:
        k += 1
        o.append(doc.h(2, f'5.{k} Provisions and contingency (not in the CAD model)'))
        rows = []
        for r in extra:
            l = r.l
            rows.append([Cell(f'<span class="pn">{esc(r.pn)}</span>{r.row_tv.ref()}', [r.row_tv]),
                         Cell(esc(l.get('name', '')[:120]) + f'<div class="sup">{esc((l.get("supplier") or "")[:80])}</div>', [r.row_tv]),
                         Cell(esc(l.get('qty', '')), [r.row_tv]),
                         Cell(esc(l.get('groups', '')), [r.row_tv]),
                         Cell(r.mass_tv.h('.4f', unit=False), [r.mass_tv]), price_cell(r)])
        pm = ctx.v('BOM', '/provision_mass_estimate_kg/estimate_range_kg', 'kg', tag='ASSUMED', tag_ptr='/provision_mass_estimate_kg/note')
        o.append(dtable(['PN', 'Item', 'Qty', 'Status', 'Unit mass [kg]', 'Price'], rows, label_cols=0, cls='bom',
                        widths=['10%', '44%', '5%', '15%', '11%', '15%']))
        o.append(note_box(f'Bleed provision mass estimate (excluding the valves): {pm.h(".3f")}. Valve mass is a MASS RISK (§4.4).', 'info'))
    return '\n'.join(o)


# =============================================================================================
# section 6: materials and thermal protection
# =============================================================================================
def sec_materials(ctx, doc, a, D):
    o = [doc.h(1, '6 Materials and thermal protection')]
    o.append(doc.h(2, '6.1 Materials'))
    mats = ctx.v('MEC', '/materials')
    if isinstance(mats.value, list):
        o.append('<ul class="mats">' + ''.join(f'<li>{esc(m)}</li>' for m in mats.value) + f'</ul><p class="small">Source: mechanical.json {mats.pill()}{mats.ref()}</p>')
    rows = []
    for mname, info in sorted(D['mat_usage'].items(), key=lambda kv: -kv[1]['mass_tv'].value):
        rows.append([esc(mname), Cell(info['n_tv'].h(), [info['n_tv']]), num_cell(info['mass_tv'], '.4f'), Cell(info['o2_tv'].h(), [info['o2_tv']])])
    o.append(dtable(['Material (BOM material_name)', 'Lines', 'Mass', 'Oxygen-clean lines'], rows, widths=['52%', '12%', '20%', '16%'],
                    caption='Material usage over the BOM lines (DERIVED by this generator; transport lock excluded).'))
    o.append(doc.h(2, '6.2 Thermal protection and thermal loads'))
    T = '/thermal_and_loads'
    pf = ctx.v('CMB', f'{T}/peak_convective_heat_flux_W_m2', 'MW/m²', conv=(1e-6, 0, 'W/m² to MW/m²'))
    hg = ctx.v('CMB', f'{T}/peak_h_g_W_m2K', 'W/(m²·K)')
    taw = ctx.v('CMB', f'{T}/T_aw_throat_K', 'K')
    pfi = ctx.v('CMB', f'{T}/peak_incident_flux_cold_wall_transient_W_m2', 'MW/m²', conv=(1e-6, 0, 'W/m² to MW/m²'))
    cot = ctx.v('ELE', f'/abort_matrix/causes/{D["cause_idx"].get("OVER_TEMP", 0)}/thresholds/kCaseOverTemp_K', 'K')
    nht = ctx.v('ELE', f'/abort_matrix/causes/{D["cause_idx"].get("OVER_TEMP", 0)}/thresholds/kNozzleHolderOverTemp_K', 'K')
    rows = [
        ['Grain-zone liner thickness', num_cell(ctx.v('CMB', '/gas_path/liner_grain_zone/thickness_m', 'mm', conv=(1000, 0, 'm to mm')), '.1f')],
        ['Pre-chamber liner and structural amendments', tvtxt(md_bullet(ctx, 'REQ', 'Amendments after rev 2', 'Structure/thermal', 'LEAD'), 420)],
        ['Post-chamber insulator', tvtxt(ctx.v('CMB', '/gas_path/post_chamber_insulator'), 300)],
        ['Peak convective heat flux at the throat (Bartz, 600 K wall)', num_cell(pf, '.2f')],
        ['Peak gas-side heat-transfer coefficient', num_cell(hg, '.0f')],
        ['Adiabatic wall temperature at the throat', Cell(temp_k(taw, 0), [taw])],
        ['Incident flux on a cold wall at start (nominal–conservative)', num_cell(pfi, '.2f')],
        ['Throat insert replacement rule', tvtxt(ctx.v('CMB', f'{T}/throat_replacement_rule'))],
        ['Insert life plan (ENG-06, newest)', tvtxt(req_row(ctx, 'ENG-06'), 300)],
        ['Nozzle gasket NZ-03 finding', tvtxt(ctx.v('CMB', '/nozzle_joint/v/NZ03_gasket', tag_ptr='/nozzle_joint'))],
        ['Proposed joint J1', tvtxt(ctx.v('CMB', '/nozzle_joint/v/proposal_J1', tag_ptr='/nozzle_joint'))],
        ['Joint leak control', tvtxt(ctx.v('CMB', '/nozzle_joint/v/H19_control', tag_ptr='/nozzle_joint'))],
        ['Case over-temperature abort (MV open) / nozzle-holder limit', cat(temp_k(cot, 2), ' / ', temp_k(nht, 2), Cell('', [cot, nht]))],
        ['Thermal FEA status', tvtxt(ctx.v('MEC', '/open_items/3', tag='PENDING'))],
    ]
    o.append(dtable(['Item', 'Value'], rows, widths=['36%', '64%']))
    return '\n'.join(o)


# =============================================================================================
# section 7: combustion
# =============================================================================================
ABORT_MAP = [  # (id, title, CHANGELOG items, combustion key, firmware pointer kind/name)
    ('A2', 'No light within the window W', [], 'A2', ('cause', 'NO_IGNITION')),
    ('A4', 'Chamber over-pressure abort', [(160, 2), (166, 4)], 'A4', ('cause', 'PC_OVERPRESSURE')),
    ('A5', 'Late-light monitor', [(160, 1)], 'A5', ('ptr', '/start_monitors_v2p9/A5')),
    ('A7', 'Pc plausibility bands, START high side', [(160, 3), (166, 7)], 'A7', ('ptr', '/start_monitors_v2p9/A7')),
    ('A14', 'Bleed valve fault / closure not confirmed', [(168, 2), (168, 3)], 'A14', ('cause', 'BLEED_FAULT')),
    ('A15', 'Anomaly during PURGE', [], 'A15', ('none', None)),
    ('A16', 'Torch loss between E1 and E2 (both sensors)', [(164, 8)], 'A16', ('none', None)),
    ('E1', 'Torch confirmation 2oo2 and closure gate', [(166, 3)], None, ('cause', 'TORCH_FAULT')),
    ('LR', 'Light-rule baseline fallback', [(166, 1)], None, ('ptr', '/light_rule_v2p9/rule')),
    ('TC', 'Invalid case thermocouple', [(166, 6)], None, ('cause', 'OVER_TEMP')),
    ('RST', 'ECU reset in flight', [(166, 8)], None, ('cause', 'WATCHDOG')),
    ('DRG', 'Drogue release predicate (FC)', [(168, 1), (175, 5)], None, ('ptr', '/drogue_release_support/rule_owner')),
    ('SAFE', 'Stand safing after a no-light', [(172, 1)], None, ('proc', None)),
]


def sec_combustion(ctx, doc, a, D):
    cl = D['cl']
    o = [doc.h(1, '7 Combustion')]
    if ctx.ovr and any(e['status'] == 'ACTIVE' for e in ctx.ovr.entries):
        o.append(note_box('<b>Reading this section.</b> combustion.json v2.4 is the source of every value here. Where it still carries wording that a newer lead '
                          'decision replaced, the old words are <del class="stale">struck through</del> and the decision is <ins class="dec">inserted</ins> with '
                          'its override id (§13.1). The Combustion v2.4a patch is to remove them (CHANGELOG 172 (6)).', 'info'))
    o.append(doc.h(2, '7.1 Design point'))
    rows = [
        ['Fuel', tvtxt(ctx.v('CMB', '/decisions/fuel'))],
        ['Oxidiser load and tank volume', cat(ctx.v('CMB', '/decisions/N2O_load_and_tank/v/m_N2O_kg', 'kg', tag_ptr='/decisions/N2O_load_and_tank').h('.2f'), ' in ',
                                              ctx.v('CMB', '/decisions/N2O_load_and_tank/v/V_tank_m3', 'L', conv=(1000, 0, 'm³ to L'), tag_ptr='/decisions/N2O_load_and_tank').h('.2f'), Cell('', ctx.recent[-2:]))],
        ['Tank conditioning', tvtxt(ctx.v('CMB', '/decisions/tank_pressurisation'), 300)],
        ['Model basis', tvtxt(ctx.v('CMB', '/operating_points/basis', tag='SIM'), 300)],
        ['Combustion and nozzle efficiencies η<sub>c*</sub> / η<sub>cf</sub>', cat(rx(ctx, 'CMB', '/operating_points/basis', r'eta_c\* ([\d.]+)', tag='ASSUMED').h('.3f'), ' / ',
                                                                                   rx(ctx, 'CMB', '/operating_points/basis', r'eta_cf ([\d.]+)', tag='ASSUMED').h('.3f'), Cell('', ctx.recent[-2:]))],
        ['Oxidiser flux at the head, rated, initial port', num_cell(ctx.v('CMB', '/operating_points/max_thrust/G_ox_initial_kg_m2s', 'kg/(m²·s)'), '.0f')],
        ['Regression law (form)', tvtxt(ctx.v('CMB', '/gas_path/grain/regression_law/form', tag='ASSUMED'))],
        ['Regression coefficient a / exponent n', cat(ctx.v('CMB', '/gas_path/grain/regression_law/a', 'm/s·(kg/m²s)^-n').h('.3e'), ' / ', ctx.v('CMB', '/gas_path/grain/regression_law/n').h('.2f'), Cell('', ctx.recent[-2:]))],
        ['Regression law note', tvtxt(ctx.v('CMB', '/gas_path/grain/regression_law/note', tag='ASSUMED'), 300)],
        ['T1–T4 measurement specification', tvtxt(ctx.t('T14', 'header (version line)', f'02-combustion/T1-T4-REGRESSION-SPEC.md, {ctx.src("T14").version}', 'DESIGN', tag_raw='document header'))],
    ]
    o.append(dtable(['Item', 'Value'], rows, widths=['32%', '68%']))

    o.append(doc.h(2, '7.2 Fuel grain'))
    G = '/gas_path/grain'
    segs = [D['bom_by_pn'].get('ENG-GR-01'), D['bom_by_pn'].get('ENG-GR-02')]
    seg_len = []
    for pn in ('ENG-GR-01', 'ENG-GR-02'):
        lo, hi, n = manifest_extent(ctx, pn_prefix=pn + '#')
        seg_len.append(man_tv(ctx, (hi[2] - lo[2]) if n else None, f'z extent of {pn}', pn_prefix=pn + '#'))
    gn = ' '.join((r.l.get('name', '') + ' ' + (r.l.get('notes') or '')) for r in segs if r)
    stated = bool(re.search(r'round|radius|fillet|\br\s*(>=|≥)?\s*4', gn, re.I))
    rnd_cad = ctx.t('BOM', '/lines/*[ENG-GR-01, ENG-GR-02]/name+notes (generator text search)',
                    'stated in the BOM' if stated else 'not stated in the BOM name or notes of ENG-GR-01/02: rounded entrance TO-VERIFY in CAD',
                    'DERIVED' if stated else 'TO-VERIFY', tag_raw='generator check of BOM text')
    if not stated:
        ctx.unknowns.append({'what': f'Rounded port entrance r >= 4 mm (CHANGELOG 160 (4)) not stated in BOM {a.cad_version} GR-01/02', 'status': 'TO-VERIFY', 'tid': rnd_cad.tid})
    D['rnd_cad'] = rnd_cad
    rows = [
        ['Segments (BOM)', cat(*[Cell(f'{esc(r.l.get("name", ""))} {r.row_tv.ref()}<br>', [r.row_tv]) for r in segs if r])],
        ['Segment length from the CAD manifest (GR-01 / GR-02)', cat(seg_len[0].h('.1f'), ' / ', seg_len[1].h('.1f'))],
        ['Grain outer diameter / total length', cat(ctx.v('CMB', f'{G}/outer_diameter_m', 'mm', conv=(1000, 0, 'm to mm')).h('.1f'), ' / ',
                                                   ctx.v('CMB', f'{G}/length_m', 'mm', conv=(1000, 0, 'm to mm')).h('.1f'), Cell('', ctx.recent[-2:]))],
        ['Port', cat(ctx.v('CMB', f'{G}/port/type').h(), ', initial Ø ', ctx.v('CMB', f'{G}/port/initial_diameter_m', 'mm', conv=(1000, 0, 'm to mm')).h('.1f'), Cell('', ctx.recent[-2:]))],
        ['Initial web', num_cell(ctx.v('CMB', f'{G}/port/initial_web_m', 'mm', conv=(1000, 0, 'm to mm')), '.2f')],
        ['Port entrance (decided)', tvtxt(cl.item(160, 4), 400)],
        ['Port entrance in CAD / BOM', Cell(rnd_cad.h(), [rnd_cad])],
        ['Density (printed ABS)', num_cell(ctx.v('CMB', f'{G}/density_kg_m3', 'kg/m³'), '.0f')],
        ['Grain mass: Combustion / CAD', cat(ctx.v('CMB', f'{G}/mass_kg', 'kg').h('.3f'), ' / ', ctx.v('MP', '/grain_mass_wet_kg', 'kg', tag='DERIVED').h('.4f'), Cell('', ctx.recent[-2:]))],
        ['Residual web rule', tvtxt(ctx.v('CMB', f'{G}/residual_web_rule'))],
        ['Retention', tvtxt(ctx.v('CMB', f'{G}/retention', tag='DESIGN'), 300)],
    ]
    o.append(dtable(['Item', 'Value'], rows, widths=['32%', '68%']))

    o.append(doc.h(2, '7.3 Injector and feed'))
    V = '/valves_and_actuators'
    rows = [
        ['Feed architecture', tvtxt(ctx.v('CMB', f'{V}/architecture', tag='DESIGN'), 400)],
        ['Injector flow model', tvtxt(ctx.v('CMB', '/gas_path/injector/flow_model', tag='LITERATURE'))],
        ['Filter', tvtxt(ctx.v('CMB', '/gas_path/injector/filter'))],
        ['Isolation valve: minimum Cv / MEOP / closing time', cat(ctx.v('CMB', f'{V}/isolation_valve/Cv_min').h('.1f'), ' / ',
                                                                  Cell(pres(ctx, ctx.v('CMB', f'{V}/isolation_valve/MEOP_Pa', 'Pa')), [ctx.recent[-1]]), ' / ',
                                                                  ctx.v('CMB', f'{V}/isolation_valve/close_time_max_s', 's').h('.2f'), Cell('', [ctx.recent[-1], ctx.recent[-3]]))],
        ['Relief: trapped liquid, back-relief and tank', tvtxt(ctx.v('CMB', f'{V}/isolation_valve/trapped_liquid_relief'))],
        ['Coast seat-leak ceiling (v2.4)', tvtxt(md_line(ctx, 'RCMB', '- **Coast leak ceiling:**', 'DERIVED'))],
        ['Hose across the gimbal', tvtxt(ctx.v('CMB', f'{V}/hose', tag='DERIVED'), 300)],
        ['Priming rule (first start)', tvtxt(ctx.v('CMB', f'{V}/priming_rule/v/0', tag_ptr=f'{V}/priming_rule'), 300)],
        ['Pc tap and sense line', cat(tvtxt(ctx.v('CMB', '/gas_path/pc_tap/location', tag='DESIGN')), '<br>', tvtxt(ctx.v('CMB', '/gas_path/pc_tap/sense_line')))],
        ['Pintle seat and seal review', tvtxt(ctx.v('CMB', f'{V}/pintle_actuator/lead_decision_v2p3', tag='LEAD'), 420)],
    ]
    o.append(dtable(['Item', 'Value'], rows, widths=['32%', '68%']))

    o.append(doc.h(2, '7.4 Igniter'))
    I = '/igniter'
    ts = f'{I}/torch_sizing'
    el = f'{I}/electrical'
    igm = ctx.v('CMB', f'{I}/mass_kg', 'kg')
    ig_bom = D['bom_by_pn'].get('ENG-IG-01')
    rows = [
        ['Type', tvtxt(ctx.v('CMB', f'{I}/type', tag='DESIGN'))],
        ['Torch chamber pressure / O/F / throat diameter', cat(ctx.v('CMB', f'{ts}/v/Pc_torch_bar', 'bar', tag='DERIVED', tag_ptr=ts).h('.1f'), ' / ',
                                                               ctx.v('CMB', f'{ts}/v/OF', tag='DERIVED', tag_ptr=ts).h('.1f'), ' / ',
                                                               ctx.v('CMB', f'{ts}/v/throat_d_m', 'mm', conv=(1000, 0, 'm to mm'), tag='DERIVED', tag_ptr=ts).h('.1f'), Cell('', ctx.recent[-3:]))],
        ['Torch flows N2O / propane', cat(ctx.v('CMB', f'{ts}/v/mdot_n2o_kg_s', 'g/s', conv=(1000, 0, 'kg/s to g/s'), tag='DERIVED', tag_ptr=ts).h('.3f'), ' / ',
                                          ctx.v('CMB', f'{ts}/v/mdot_propane_kg_s', 'g/s', conv=(1000, 0, 'kg/s to g/s'), tag='DERIVED', tag_ptr=ts).h('.3f'), Cell('', ctx.recent[-2:]))],
        ['Orifice diameters N2O / propane', cat(ctx.v('CMB', f'{I}/N2O_orifice_d_m', 'mm', conv=(1000, 0, 'm to mm')).h('.3f'), ' / ',
                                                ctx.v('CMB', f'{I}/propane_orifice_d_m', 'mm', conv=(1000, 0, 'm to mm')).h('.3f'), Cell('', ctx.recent[-2:]))],
        ['Spark: supply / energy / rate', cat(ctx.v('CMB', f'{el}/v/spark_supply_V', 'V', tag_ptr=el).h('.0f'), ' / ', ctx.v('CMB', f'{el}/v/spark_energy_J', 'J', tag_ptr=el).h('.2f'), ' / ',
                                              ctx.v('CMB', f'{el}/v/rate_Hz', 'Hz', tag_ptr=el).h('.0f'), Cell('', ctx.recent[-3:]))],
        ['Envelope', tvtxt(ctx.v('CMB', f'{I}/envelope/v/mount', tag_ptr=f'{I}/envelope'), 260)],
        ['Igniter system mass: Combustion / BOM ENG-IG-01', cat(igm.h('.2f'), ' / ', ig_bom.mass_tv.h('.3f') if ig_bom else 'MISSING', Cell('', [igm] + ([ig_bom.mass_tv] if ig_bom else [])))],
        ['Starts per flight', tvtxt(ctx.v('CMB', f'{I}/starts_per_flight'))],
    ]
    o.append(dtable(['Item', 'Value'], rows, widths=['32%', '68%']))

    o.append(doc.h(2, '7.5 Start, relight and shutdown sequences'))
    SQ = f'{I}/sequence/v'
    seq = ctx.raw('CMB', SQ + '/start', default=[]) or []
    rows = []
    ev_t = {}
    for k, e in enumerate(seq):
        ep = ctx.v('CMB', f'{SQ}/start/{k}/epoch', tag='LEAD', tag_ptr=f'{I}/sequence')
        tt = ctx.v('CMB', f'{SQ}/start/{k}/t_s', 's', tag='LEAD', tag_ptr=f'{I}/sequence')
        ac = ctx.v('CMB', f'{SQ}/start/{k}/action', tag='LEAD', tag_ptr=f'{I}/sequence')
        ev_t[e.get('epoch')] = tt
        rows.append([Cell(f'<b>{esc(ep.value)}</b>', [ep]), num_cell(tt, '.3f') if tt.value is not None else Cell('—', [tt]), tvtxt(ac, 560)])
    o.append(dtable(['Epoch', 't [s]', 'Action'], rows, label_cols=0, widths=['14%', '9%', '77%'],
                    caption='Start and relight sequence (combustion.json v2.4 /igniter/sequence; times relative to E0 where stated by the source).'))
    pt = '/relight_purge/v/timing_s'
    pur = {k: ctx.v('CMB', f'{pt}/{k}', 's', tag_ptr='/relight_purge') for k in ('PURGE_command_rel_E0', 'MV_ramp', 'flow', 'flow_end_rel_E0')}
    evs = [(ev_t[k].value, k) for k in ('E0', 'E1', 'torch gate', 'E2') if k in ev_t and ev_t[k].value is not None]
    W = ev_t.get('W')
    tg = ev_t.get('torch gate')
    plan = ctx.v('GNC', '/requirements/ignition/relight_planning_value_s', 's')
    windows = [(f'W {W.value:g} s from the lift command (FSW planning value {plan.value:g} s)', tg.value, W.value)] if (W and tg and W.value is not None and tg.value is not None) else []
    src = plot_sequence(a, evs, {'t0': pur['PURGE_command_rel_E0'].value, 'ramp': pur['MV_ramp'].value, 'flow': pur['flow'].value,
                                 'end': pur['flow_end_rel_E0'].value}, windows)
    o.append(fig_html(src, 'A1 relight timeline: forced purge before E0, torch, ignition lift at E1, light E2 and the Pc-confirm deadline. '
                      'E2 is shown at the value listed by the source sequence (not a bound).', [t.tid for t in pur.values()] + [t.tid for t in ev_t.values()], 'wide'))
    lists = [('ARM preconditions', 'arm_preconditions'), ('Relight', 'relight'), ('Shutdown', 'shutdown'), ('Abort if no ignition', 'abort_if_no_ignition')]
    rows = []
    for lab, key in lists:
        items = ctx.raw('CMB', f'{SQ}/{key}', default=[]) or []
        for j, _ in enumerate(items):
            tv = ctx.v('CMB', f'{SQ}/{key}/{j}', tag='LEAD', tag_ptr=f'{I}/sequence')
            rows.append([lab if j == 0 else '', tvtxt(tv, 380)])
    o.append(dtable(['Phase', 'Rule'], rows, widths=['18%', '82%']))
    fa1 = ctx.v('CMB', f'{SQ}/fa1_supervision/v/status', tag='LEAD', tag_ptr=f'{SQ}/fa1_supervision')
    o.append(note_box(f'<b>FA-1 (fuel-assisted relight pulse).</b> {tvtxt(fa1).html} {tvtxt(cl.item(170, 2)).html}'
                      f'<br><b>Load restated as an envelope (CHANGELOG 172 (2)).</b> {tvtxt(cl.item(172, 2)).html}'
                      + (f'<br><b>Envelope published and structural load decided (CHANGELOG {D["fa1"]["n"]}; §2.5).</b> {tvtxt(D["fa1"]["dec"]).html}'
                         if D.get('fa1') else ''), 'warn'))

    o.append(doc.h(2, '7.6 Abort set'))
    lines_ = sorted({n for _, _, its, _, _ in ABORT_MAP for n, _ in its} | {160, 164})
    o.append('<p>The decided abort set is the newest lead decision for each item (CHANGELOG lines ' + ', '.join(str(n) for n in lines_[:-1]) +
             f' and {lines_[-1]}). The Combustion matrix (combustion.json {esc(ctx.src("CMB").version or "")}) and the firmware v2.9 implementation '
             '(electronics.json v2) are shown beside it; where they differ, the decision governs and the difference is listed in §13.</p>')
    cm = '/abort_matrix_v2p4/v'
    rows = []
    for aid, title, items, ckey, fw in ABORT_MAP:
        dec = [cl.item(n, k) for n, k in items]
        dcell = cat(*[Cell(f'<div class="dec"><b>L{n}({k})</b> {tvtxt(t, 330).html}</div>', [t]) for (n, k), t in zip(items, dec)]) if dec else Cell('<span class="small">no specific lead item; Combustion matrix applies</span>', [])
        if not dec and ckey:
            # keep the decided set honest: the matrix itself carries the lead tag
            mt = ctx.v('CMB', '/abort_matrix_v2p4/tag', tag='LEAD') if ctx.raw('CMB', '/abort_matrix_v2p4/tag', default=None) else None
            dcell = Cell('<span class="small">no item of its own; governed by the matrix tag: </span>' + (tvtxt(mt, 160).html if mt else ''), [mt] if mt else [])
        ccell = tvtxt(ctx.v('CMB', f'{cm}/{ckey}', tag_ptr='/abort_matrix_v2p4'), 240) if ckey else Cell('<span class="small">—</span>', [])
        if fw[0] == 'cause' and fw[1] in D['cause_idx']:
            ci = D['cause_idx'][fw[1]]
            fcell = cat(f'<b>{esc(fw[1])}</b> ', tvtxt(ctx.v('ELE', f'/abort_matrix/causes/{ci}/trigger', tag='DESIGN'), 200))
            th = ctx.raw('ELE', f'/abort_matrix/causes/{ci}/thresholds', default={}) or {}
            for kk in th:
                t = ctx.v('ELE', f'/abort_matrix/causes/{ci}/thresholds/{kk}')
                fcell = cat(fcell, f'<div class="small">{esc(kk)} = ', t.h(), '</div>')
        elif fw[0] == 'ptr':
            fcell = tvtxt(ctx.v('ELE', fw[1], tag_default='DESIGN'), 240)
        elif fw[0] == 'proc':
            pr = ctx.t('generator', f'abort map {aid}: firmware column', 'ground procedure, not a firmware cause', 'DESIGN', tag_raw='generator classification of the decided item')
            fcell = Cell(f'<span class="small">{esc(pr.value)}</span> {pr.ref()}', [pr])
        else:
            nf = ctx.t('ELE', '/abort_matrix/causes (generator search)', 'no matching cause in firmware v2.9', 'MISSING', tag_raw='generator search of the cause list')
            fcell = Cell(nf.h(), [nf])
        rows.append([Cell(f'<b>{aid}</b><div class="small">{esc(title)}</div>', []), dcell, ccell, fcell])
    o.append(dtable(['ID', 'Decided (CHANGELOG)', 'Combustion v2.4 matrix', 'Firmware v2.9 (SIL only)'], rows, label_cols=1, cls='abort',
                    widths=['11%', '35%', '24%', '30%']))
    act = ctx.v('ELE', '/abort_matrix/actions', tag='LEAD')
    o.append(note_box(f'<b>Abort action.</b> {tvtxt(act).html}', 'info'))

    o.append(doc.h(2, '7.7 Stability'))
    st = '/stability/points_initial_port'
    pts = ctx.raw('CMB', st + '/v', default={}) or {}
    rows = []
    for fr in pts:
        base = f'{st}/v/{fr}'
        cells = [Cell(f'{float(fr) * 100:.1f} %', [])]
        for key, unit, f in (('dP_over_Pc', '', '.2f'), ('GM_tau5ms', '', '.1f'), ('GM_tau10ms', '', '.1f'), ('f_1L_Hz', 'Hz', '.0f'),
                             ('f_Helmholtz_Hz', 'Hz', '.0f'), ('f_thermal_lag_Hz', 'Hz', '.2f')):
            cells.append(num_cell(ctx.v('CMB', f'{base}/{key}', unit, tag_ptr=st), f))
        rows.append(cells)
    o.append(dtable(['Throttle', 'dP/Pc', 'Chug gain margin, 5 ms', 'Chug gain margin, 10 ms', '1L acoustic', 'Helmholtz', 'Thermal lag'], rows,
                    caption='Stability indicators at the initial port (SIM).'))
    o.append(note_box(tvtxt(ctx.v('CMB', '/stability/criteria', tag='DERIVED')).html + '<br>' + tvtxt(ctx.v('CMB', '/stability/hybrid_LF_note', tag='TO-VERIFY')).html, 'info'))
    return '\n'.join(o)


# =============================================================================================
# more readers
# =============================================================================================
def md_line(ctx, sid, starts, ev, maxlen=None):
    """First line of a markdown source starting with the given text (locator: line number)."""
    for n, ln in enumerate((ctx.src(sid).text or '').splitlines(), 1):
        if ln.startswith(starts):
            return ctx.t(sid, f'line {n}', re.sub(r'^-\s+', '', ln.strip()), ev, tag_raw=f'{sid} line {n}')
    ctx.issue('WARN', f'line not found {sid} {starts!r}')
    return ctx.missing(f'{sid} line starting {starts}')


def md_section_text(ctx, sid, heading_prefix, ev):
    """All non-empty lines under a markdown heading, bullet markers removed, joined (locator: the heading)."""
    ls = [re.sub(r'^\s*-\s+', '', ln).strip() for ln in md_section_lines(ctx.src(sid).text or '', heading_prefix) if ln.strip()]
    if not ls:
        ctx.issue('WARN', f'section not found {sid} §{heading_prefix}')
        return ctx.missing(f'{sid} §{heading_prefix}')
    return ctx.t(sid, f'§{heading_prefix} (whole section)', ' '.join(ls), ev, tag_raw=f'{sid} §{heading_prefix}')


def md_first_para(ctx, sid, heading_prefix, ev):
    """First non-empty paragraph line under a markdown heading."""
    for ln in md_section_lines(ctx.src(sid).text or '', heading_prefix):
        if ln.strip():
            return ctx.t(sid, f'§{heading_prefix} first paragraph', ln.strip(), ev, tag_raw=f'{sid} §{heading_prefix}')
    ctx.issue('WARN', f'section not found {sid} §{heading_prefix}')
    return ctx.missing(f'{sid} §{heading_prefix}')


def rx_text(ctx, tv, pattern, unit='', tag=None, group=1, note=''):
    """Number extracted with a recorded regex from a text value already traced (CHANGELOG item, markdown row)."""
    s = tv.value if isinstance(tv.value, str) else None
    m = re.search(pattern, s) if s else None
    loc = f'{tv.ptr} [regex {pattern}]'
    if not m:
        ctx.issue('WARN', f'regex not matched {tv.sid}:{tv.ptr} {pattern}')
        t = TV(ctx, None, unit, 'MISSING', tv.tag_raw, tv.sid, loc, status='MISSING', note='pattern not found')
        ctx.unknowns.append({'what': f'{tv.sid}:{loc}', 'status': 'MISSING', 'tid': t.tid})
        return t
    return TV(ctx, float(m.group(group)), unit, tag or tv.ev, tv.tag_raw, tv.sid, loc, note=note)


def wilson(p, n, z=1.959964):
    """Wilson score interval for a binomial proportion."""
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def hash_status(ctx, a, hashes):
    """Compare a review's file hashes with the current hub files (generator check, not approval)."""
    same, changed, missing = [], [], []
    for rel, h in (hashes or {}).items():
        p = os.path.join(a.hub, rel)
        if not os.path.isfile(p):
            missing.append(rel)
        elif sha16_file(p) == h:
            same.append(rel)
        else:
            changed.append(rel)
    return same, changed, missing


def img_fig(ctx, a, fid, caption, cls='', prefix='fig_'):
    s = ctx.sources.get(fid)
    if s is None or not s.exists:
        tv = ctx.missing(f'figure {fid}')
        return f'<div class="miss">figure {esc(fid)} MISSING {tv.ref()}</div>'
    os.makedirs(os.path.join(a.out, 'assets'), exist_ok=True)
    fn = prefix + os.path.basename(s.path)
    shutil.copyfile(s.path, os.path.join(a.out, 'assets', fn))
    return (f'<figure class="{cls}"><img src="assets/{esc(fn)}"><figcaption>{caption} '
            f'<span class="figref">Source {esc(fid)}: {esc(os.path.relpath(s.path, a.hub))} (sha256/16 {esc(s.sha16)}).</span></figcaption></figure>')


# =============================================================================================
# section 8: plume CFD
# =============================================================================================
def sec_plume(ctx, doc, a, D):
    o = [doc.h(1, '8 Plume CFD')]
    P = 'PVAL'
    De = ctx.v('CMB', '/gas_path/nozzle/exit_diameter_m', 'm')
    stl = md_line(ctx, 'RPL', 'Version ', 'SIM')
    o.append(note_box('<b>Simulation, not measurement.</b> ' + tvtxt(stl, 700).html, 'info'))

    def mm(tv):
        return ctx.d(tv.value * De.value * 1000 if (tv.value is not None and De.value) else None, 'mm',
                     'x/De × De (exit diameter from combustion.json, tagged v1 geometry)', [tv, De])

    S = lambda ptr, unit='', tag='SIM': ctx.v(P, ptr, unit, tag=tag, note='validation_v2.json carries no tags: CFD outputs SIM, 1-D and correlation values DERIVED')
    o.append(doc.h(2, '8.1 Key results at the rated point'))
    xmd, xlc = S('/correlations/own_f_2s_rans/x_md_cfd', 'De'), S('/correlations/own_f_2s_rans/x_md_lewis_carlson', 'De', 'DERIVED')
    sp1, sp3, ppt = S('/correlations/own_f_2s_rans/spacing_first_mach', 'De'), S('/correlations/own_f_2s_rans/spacing_mean3_mach', 'De'), \
        S('/correlations/own_f_2s_rans/spacing_pp_tam', 'De', 'DERIVED')
    core = S('/gci/core_length_Z095_De/fine', 'De')
    t10, t20 = S('/gci/T_axis_10De_K/fine', 'K'), S('/gci/T_axis_20De_K/fine', 'K')
    fcfd, f1d, fdev = S('/thrust_vs_1d/own_f_2s_rans/F_cfd', 'N'), S('/one_d/F_ideal_lambda_N', 'N', 'DERIVED'), S('/thrust_vs_1d/own_f_2s_rans/dev_vs_ideal_lambda_pct', '%')
    mcfd, m1d, mdev = S('/thrust_vs_1d/own_f_2s_rans/mdot_cfd', 'kg/s'), S('/one_d/mdot', 'kg/s', 'DERIVED'), S('/thrust_vs_1d/own_f_2s_rans/mdot_dev_pct', '%')
    rows = [
        ['Operating point of every grid level', tvtxt(md_bullet(ctx, 'RPL', '0. Checkpoint', 'v1 (combustion.json v1)', 'SIM'), 300)],
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
        ['v2 design point (coarse grid): Mach disk CFD / correlation; thrust deviation',
         cat(S('/v2op/x_md_cfd', 'De').h('.3f'), ' / ', S('/v2op/x_md_lewis_carlson', 'De', 'DERIVED').h('.3f'), '; ', S('/v2op/thrust_dev_vs_ideal_lambda_pct', '%').h('.2f'))],
        ['v2 point remark', tvtxt(S('/v2op/note'), 320)],
    ]
    o.append(dtable(['Quantity', 'Value'], rows, widths=['38%', '62%'],
                    caption=f'Plume CFD results ({esc(src_label(ctx, "PVAL"))}, fine grid at the v1 point unless stated; lengths in exit diameters De).'))
    o.append(doc.h(2, '8.2 Fields'))
    o.append(img_fig(ctx, a, 'PF-MACH', '<b>Mach number, near field</b> (SIM, fine grid, v1 point).', 'wide'))
    o.append(img_fig(ctx, a, 'PF-SCHL', '<b>Numerical schlieren</b> |∇ρ| (SIM, fine grid, v1 point): Mach disk, reflected shocks and the shock-cell train.', 'wide'))
    o.append(img_fig(ctx, a, 'PF-TEMP', '<b>Static temperature, full domain</b> (SIM, frozen chemistry, no afterburning). The far field is not statistically stationary.', 'wide'))
    o.append(img_fig(ctx, a, 'PF-AXIS', '<b>Centreline profiles</b> (SIM, fine grid).', 'half'))
    o.append(img_fig(ctx, a, 'PF-V2MACH', '<b>Mach number at the v2 design point</b> (SIM, coarse grid). v2-v1 differences carry the grid error of the coarse level.', 'wide'))
    o.append(doc.h(2, '8.3 Afterburning and model limits'))
    rows = [['Afterburning at the v1 point', tvtxt(md_bullet(ctx, 'RPL', '0. Checkpoint', 'adds 172', 'SIM'), 400)],
            ['Afterburning at the v2 point', tvtxt(md_bullet(ctx, 'RPL', '0. Checkpoint', 'adds nothing', 'SIM'), 400)],
            ['Afterburning at the stretch floor', tvtxt(md_bullet(ctx, 'RPL', '0. Checkpoint', 'adds up to', 'SIM'), 300)]]
    for k in ('**Soot and radiation', '**Finite-rate chemistry', '**Exhaust gas model', '**Geometry and setting', '**Duration', '**No acoustics'):
        rows.append(['Limit: ' + k.strip('*'), tvtxt(md_bullet(ctx, 'RPL', '10. What the model cannot show', k, 'SIM'), 360)])
    o.append(dtable(['Item', 'Report statement'], rows, widths=['24%', '76%']))
    o.append(doc.h(2, '8.4 Illustration'))
    o.append(img_fig(ctx, a, 'PF-ART', '<b>Illustration, not simulation.</b> Blender render of revolved CFD fields with exposure, colour and emitter chosen '
                     'for appearance (ARTISTIC); it is not a radiation prediction and carries no data.', 'wide art'))
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
            rid = ctx.v('SUP', f'/reviews/{i}/id', tag='DERIVED')
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


# =============================================================================================
# section 9: structural FEA (PENDING until hub/04-fea margins or mechanical.json v2.1)
# =============================================================================================
FEA_SCHEMA = [('case', 'load case ID (loadcases file)'), ('part', 'BOM part number'), ('material', 'material code'),
              ('state', 'critical state or instant'), ('MS', 'margin of safety on yield (combined, at temperature)'),
              ('MS_ult', 'margin of safety on ultimate'), ('T_part_max_C', 'peak part temperature'), ('T_limit_C', 'usable temperature limit'),
              ('SF_y', 'yield factor applied'), ('SF_u', 'ultimate factor applied'), ('criterion', 'criterion text'), ('status', 'result statement')]
FEA_GLOBS = ['04-fea/**/*margin_table*.csv']


def find_fea_tables(ctx, a):
    files = []
    for g in FEA_GLOBS:
        files += sorted(glob.glob(os.path.join(a.hub, g), recursive=True))
    files = [f for f in files if os.sep + 'history' + os.sep not in f]
    out = []
    for k, f in enumerate(files, 1):
        sid = f'FEA{k}'
        ctx.add(sid, f, 'FEA margin table (hub 04-fea)', 'csv', required=False)
        rows = list(csv.DictReader(io.StringIO(ctx.src(sid).text or '')))
        out.append((sid, f, rows))
    return out


def sec_fea(ctx, doc, a, D):
    o = [doc.h(1, '9 Structural FEA')]
    tables = find_fea_tables(ctx, a)
    mec_v = ctx.v('MEC', '/version', tag='DESIGN')
    mec_m = None
    if isinstance(mec_v.value, str) and re.match(r'v2\.(\d+)', mec_v.value) and int(re.match(r'v2\.(\d+)', mec_v.value).group(1)) >= 1:
        mec_m = ctx.raw('MEC', '/structural_margins', default=None)
    pend = ctx.missing('Structural FEA margins (hub 04-fea margin table or mechanical.json v2.1 /structural_margins)', 'PENDING',
                       note='no published margin table found by the generator')
    if not tables and not mec_m:
        o.append(note_box(f'<b>PENDING.</b> No structural margin has been published to the hub. The generator looked for '
                          f'<code>{esc(", ".join(FEA_GLOBS))}</code> under the hub and for <code>/structural_margins</code> in '
                          f'mechanical.json ≥ v2.1 (current: {mec_v.h()}). The pressure parts and the gimbal structure therefore carry no '
                          f'verified margin in this draft {pend.pill()}{pend.ref()}. Stiffness and modal results from mechanical.json v2 are in §3.2.', 'warn'))
    else:
        ctx.unknowns = [u for u in ctx.unknowns if u.get('tid') != pend.tid]
    o.append(doc.h(2, '9.1 Load cases (inputs)'))
    cases = ctx.raw('FEALC', '/cases', default=[]) or []
    rows = []
    for i, c in enumerate(cases):
        b = f'/cases/{i}'
        cid = ctx.v('FEALC', b + '/id', tag='DESIGN')
        ttl = ctx.v('FEALC', b + '/title', tag='DESIGN')
        pc = ctx.v('FEALC', b + '/chamber_Pa', 'Pa', tag='DESIGN') if c.get('chamber_Pa') is not None else None
        th = ctx.v('FEALC', b + '/thrust_N', 'N', tag='DESIGN') if c.get('thrust_N') is not None else None
        sy = ctx.v('FEALC', b + '/criterion/SF_y', tag='REQ') if isinstance(c.get('criterion'), dict) and c['criterion'].get('SF_y') is not None else None
        su = ctx.v('FEALC', b + '/criterion/SF_u', tag='REQ') if isinstance(c.get('criterion'), dict) and c['criterion'].get('SF_u') is not None else None
        nm = Cell(f'<b>{esc(cid.value)}</b>{cid.ref()}', [cid])
        rows.append([nm, tvtxt(ttl, 120),
                     Cell(pres(ctx, pc), [pc]) if pc else Cell('<span class="small">not applicable</span>', [ttl]),
                     num_cell(th, '.1f') if th else Cell('<span class="small">not applicable</span>', [ttl]),
                     cat(sy.h('.1f') if sy else '—', ' / ', su.h('.1f') if su else '—', Cell('', [x for x in (sy, su, ttl) if x]))])
    o.append(dtable(['Case', 'Title', 'Chamber pressure', 'Thrust', 'SF yield / ultimate'], rows, label_cols=0,
                    widths=['8%', '42%', '20%', '13%', '17%'], caption=f'04-fea/loadcases_v1.json ({esc(src_label(ctx, "FEALC"))}). The thrust of LC2F is listed in §13.'))
    cl = D['cl']
    add = [['LC-TB70 (throat block, assembled FEA)', tvtxt(cl.item(166, 10, contains='LC-TB70'), 300)],
           ['Throat-block event in the firmware SIL', tvtxt(ctx.v('ELE', '/open_issues/3', tag='SIM'), 300)],
           ['FA-1 fuel-assisted relight pulse check', tvtxt(cl.item(164, 8, contains='Mechanical adds'), 300)],
           ['FA-1 flight acceptance condition', tvtxt(cl.item(170, 2), 300)],
           ['FA-1 load envelope and interim check (supersedes the single-point check above)', tvtxt(cl.item(172, 2), 600)]] + \
          ([['FA-1 structural load decided on the v2.4a envelope (supersedes the interim check; §2.5)', tvtxt(D['fa1']['dec'], 900)]] if D.get('fa1') else [])
    o.append(dtable(['Load case required by a lead decision', 'Decision text'], add, widths=['30%', '70%'],
                    caption='Load cases decided after loadcases_v1 and not yet in a published load-case file.'))
    o.append(doc.h(2, '9.2 Margin table'))
    if tables:
        for sid, f, rows_ in tables:
            o.append(fea_margin_tables(ctx, sid, rows_))
    elif mec_m:
        o.append(tvtxt(ctx.v('MEC', '/structural_margins', tag='SIM'), 2000).html)
    else:
        rows = []
        for i, c in enumerate(cases):
            cid = ctx.v('FEALC', f'/cases/{i}/id', tag='DESIGN')
            t = ctx.missing(f'FEA margins for load case {c.get("id")}', 'PENDING')
            rows.append([Cell(f'<b>{esc(cid.value)}</b>{cid.ref()}', [cid]), Cell(t.h(), [t])])
        o.append(dtable(['Load case', 'Governing margins'], rows, widths=['20%', '80%'],
                        caption='Placeholder: one row per load case until a margin table is published.'))
    F1 = D.get('fa1') or {}
    if F1.get('mech'):
        o.append(note_box(f'<b>Margins reported in the decision log, outside a published margin table (Mechanical result, CHANGELOG {F1["n_mech"]}; '
                          f'FA-1 loads of §2.5).</b> {tvtxt(F1["mech"], 1800).html} <span class="small">Not the assembled FEA of record and not '
                          f'independently reviewed; the CAD changes it proposes are not in CAD {esc(a.cad_version)}.</span> {F1["mech_rev"].h()}', 'warn'))
    o.append('<p class="small">Schema the generator reads (one row per load case, part and state; the governing row per part is the minimum MS):</p>')
    o.append(table(['Field', 'Meaning'], [[f'<code>{esc(k)}</code>', esc(v)] for k, v in FEA_SCHEMA], cls='schema', widths=['22%', '78%']))
    o.append(note_box('A margin table is a simulation result. A positive margin is not a proof test: the hydrostatic proof (LC4) and the '
                      'founders\' pressure tests remain the physical gates for the pressure parts.', 'info'))
    return '\n'.join(o)


def fea_margin_tables(ctx, sid, rows_):
    """Governing (minimum MS) row per part and the list of negative margins, each cell traced to its CSV row."""
    gov = {}
    neg = []
    for i, r in enumerate(rows_):
        ms = fnum(r.get('MS'))
        if ms is None:
            continue
        key = r.get('part', '?')
        if key not in gov or ms < fnum(gov[key][1].get('MS')):
            gov[key] = (i, r)
        if ms < 0:
            neg.append((i, r))
    def rowcells(i, r):
        loc = f'row {i + 2} (case={r.get("case")}, part={r.get("part")})'
        msv = TV(ctx, fnum(r.get('MS')), '', 'SIM', f'{sid} CSV', sid, loc + '/MS')
        msu = TV(ctx, fnum(r.get('MS_ult')), '', 'SIM', f'{sid} CSV', sid, loc + '/MS_ult', status='not given')
        txt = TV(ctx, f"{r.get('case')} · {r.get('material')} · {r.get('state')} · T {r.get('T_part_max_C')} / {r.get('T_limit_C')} °C", '', 'SIM', f'{sid} CSV', sid, loc)
        st = TV(ctx, (r.get('status') or '')[:220], '', 'SIM', f'{sid} CSV', sid, loc + '/status')
        return [Cell(f'<span class="pn">{esc(r.get("part"))}</span>', [txt]), Cell(txt.h(pill=False), [txt]), num_cell(msv, '.2f'), num_cell(msu, '.2f'), tvtxt(st, 220)]
    out = [dtable(['Part', 'Case · material · state · T max / limit', 'MS yield', 'MS ult.', 'Status'],
                  [rowcells(i, r) for _, (i, r) in sorted(gov.items(), key=lambda kv: fnum(kv[1][1].get('MS')))],
                  label_cols=0, widths=['10%', '34%', '9%', '9%', '38%'], caption=f'Governing margin per part ({esc(sid)}).')]
    if neg:
        out.append(dtable(['Part', 'Case · material · state · T max / limit', 'MS yield', 'MS ult.', 'Status'], [rowcells(i, r) for i, r in neg],
                          label_cols=0, widths=['10%', '34%', '9%', '9%', '38%'], caption=f'All negative margins ({len(neg)} rows).'))
    return '\n'.join(out)


# =============================================================================================
# section 10: electronics
# =============================================================================================
def sec_electronics(ctx, doc, a, D):
    o = [doc.h(1, '10 Electronics and control')]
    cl = D['cl']
    i = next((k for k, r in enumerate(ctx.raw('SUP', '/reviews', default=[]) or []) if r.get('id') == 'REV-ELEC-1'), None)
    if i is not None:
        vd = ctx.v('SUP', f'/reviews/{i}/verdict', tag='DERIVED')
        bl = ctx.v('SUP', f'/reviews/{i}/blocking', tag='DERIVED')
        o.append(note_box(f'<b>Firmware v2.9 and electronics.json v2: REVISE per REV-ELEC-1</b> ({vd.h()}). Blocking findings: {tvtxt(bl).html} '
                          f'Lead disposition: {tvtxt(cl.item(166, 10, contains="v2.10")).html} Values below are the published v2 interface; '
                          'where a lead decision changes them, §7.6 and §13 show the decided value.', 'warn'))
    E = 'ELE'
    o.append(doc.h(2, '10.1 Engine control unit and firmware'))
    rows = [
        ['Architecture', tvtxt(ctx.v(E, '/ecu/architecture'))],
        ['Microcontroller', tvtxt(ctx.v(E, '/ecu/mcu', tag='DESIGN'))],
        ['PCB outline / enclosure reservation', cat(ctx.v(E, '/ecu/pcb_outline_mm', 'mm').h('.1f'), ' / ', ctx.v(E, '/ecu/enclosure_envelope_mm', 'mm').h('.0f'))],
        ['ECU mass (range)', cat(ctx.v(E, '/ecu/mass_kg', 'kg').h('.2f'), ' (', ctx.v(E, '/ecu/mass_kg/range', 'kg', tag='ASSUMED').h('.2f'), ')')],
        ['Schematic', tvtxt(ctx.v(E, '/ecu/schematic/version', tag='DESIGN'))],
        ['Schematic checks', cat(tvtxt(ctx.v(E, '/ecu/schematic/erc')), '<br>', tvtxt(ctx.v(E, '/ecu/schematic/netlist_crosscheck')))],
        ['Placeholders (not for fabrication)', tvtxt(ctx.v(E, '/ecu/schematic/placeholders', tag='TO-VERIFY'))],
        ['Firmware version / target', cat(ctx.v(E, '/firmware/version', tag='DESIGN').h(), ' — ', tvtxt(ctx.v(E, '/firmware/target', tag='TO-VERIFY')))],
        ['Firmware unit tests (v2.9)', tvtxt(ctx.v(E, '/firmware/unit_tests/v2.9', tag='SIM'))],
        ['Interface status', tvtxt(ctx.v(E, '/status', tag='DESIGN'), 500)],
        ['Constants generated from', tvtxt(ctx.v(E, '/inputs/generated_headers', tag='DESIGN'), 400)],
        ['CAN link', tvtxt(ctx.v(E, '/can_interface/physical'), 240)],
    ]
    o.append(dtable(['Item', 'Value'], rows, widths=['28%', '72%']))
    o.append(doc.h(2, '10.2 Sensors'))
    PT = '/sensors/pressure_transducers'
    rows = [
        ['Pressure transducers (selection)', tvtxt(ctx.v(E, f'{PT}/selection'))],
        ['Connectors', tvtxt(ctx.v(E, f'{PT}/connectors', tag='DESIGN'), 300)],
        ['Hardware over-pressure comparator', tvtxt(ctx.v(E, f'{PT}/hw_ovp'))],
        ['Transducer fault window', cat(ctx.v(E, f'{PT}/fault_window/min', 'V').h('.2f'), ' – ', ctx.v(E, f'{PT}/fault_window/max', 'V', tag='DESIGN').h('.2f'))],
        ['Thermocouples', tvtxt(ctx.v(E, '/sensors/thermocouples/channels', tag='DESIGN'), 500)],
        ['Case over-temperature abort / relight refusal', cat(Cell(temp_k(ctx.v(E, '/sensors/thermocouples/case_abort', 'K'), 2), [ctx.recent[-1]]), ' / ',
                                                             Cell(temp_k(ctx.v(E, '/sensors/thermocouples/relight_refusal', 'K'), 2), [ctx.recent[-1]]))],
        ['Other temperatures', tvtxt(ctx.v(E, '/sensors/temperature_other', tag='DESIGN'), 300)],
        ['Encoders', tvtxt(ctx.v(E, '/sensors/encoders', tag='DESIGN'))],
        ['Load cell (stand)', tvtxt(ctx.v(E, '/sensors/load_cell/model', tag='TO-VERIFY'))],
        ['IMU', tvtxt(ctx.v(E, '/sensors/imu', tag='TO-VERIFY'))],
    ]
    o.append(dtable(['Item', 'Value'], rows, widths=['28%', '72%']))
    o.append(doc.h(2, '10.3 Loop rates, latency and link loss'))
    L = '/loop_rates_and_latency'
    keys = [('pc_control_Hz', 'Pc control loop'), ('pc_adc_Hz', 'Pc ADC sampling'), ('tvc_shaping_Hz', 'TVC command shaping'), ('servo_pwm_Hz', 'Servo PWM'),
            ('fc_command_Hz', 'FC command rate'), ('telemetry_fast_Hz', 'Telemetry, fast'), ('telemetry_slow_Hz', 'Telemetry, slow'), ('sd_log_Hz', 'SD log'),
            ('safety_monitor_Hz', 'Safety monitor'), ('tlm_relight_Hz', 'Relight-state telemetry'), ('fc_thrust_Hz', 'FC thrust estimate')]
    rows = [[lab, num_cell(ctx.v(E, f'{L}/{k}', 'Hz'), '.0f')] for k, lab in keys]
    rows += [['Hardware watchdog', num_cell(ctx.v(E, f'{L}/hw_watchdog', 's'), '.3f')],
             ['Link degraded / lost after', cat(ctx.v(E, '/link_loss/degraded_after', 's').h('.3f'), ' / ', ctx.v(E, '/link_loss/lost_after', 's').h('.3f'))],
             ['Latency terms', tvtxt(ctx.v(E, f'{L}/latency_s', 's'), 300)]]
    o.append(dtable(['Item', 'Value'], rows, widths=['40%', '60%']))
    o.append(doc.h(2, '10.4 Light rule and start monitors (firmware v2.9)'))
    LR = '/light_rule_v2p9'
    rows = [
        ['Light rule', tvtxt(ctx.v(E, f'{LR}/rule'), 600)],
        ['Rise over the baseline P0 / confirmation ticks / baseline samples', cat(ctx.v(E, f'{LR}/kIgnRise_Pa', 'Pa').h('.0f'), ' / ', ctx.v(E, f'{LR}/kIgnConfirmRelN').h('.0f'), ' / ',
                                                                                    ctx.v(E, f'{LR}/kIgnPreN').h('.0f'))],
        ['Floor and baseline check', cat(tvtxt(ctx.v(E, f'{LR}/kIgnFloorAbs_Pa')), '<br>', tvtxt(ctx.v(E, f'{LR}/kIgnBaseCheck_Pa')))],
        ['Decided baseline fallback (RE-02)', tvtxt(cl.item(166, 1), 500)],
        ['SIL, A1 relight MC: lit runs / light-rule aborts / false lights on unlit runs',
         cat(ctx.v(E, f'{LR}/sil_a1_relight_mc/runs_lit', tag='SIM').h('d'), ' / ', ctx.v(E, f'{LR}/sil_a1_relight_mc/light_rule_aborts', tag='SIM').h('d'), ' / ',
             ctx.v(E, f'{LR}/sil_a1_relight_mc/unlit_false_lights', tag='SIM').h('d'))],
        ['SIL, E2 after the light: median / maximum', cat(ctx.v(E, f'{LR}/sil_a1_relight_mc/E2_minus_light_ms/p50', 'ms', tag='SIM').h('.0f'), ' / ',
                                                        ctx.v(E, f'{LR}/sil_a1_relight_mc/E2_minus_light_ms/max', 'ms', tag='SIM').h('.0f'))],
        ['SIL basis', tvtxt(ctx.v(E, f'{LR}/sil_a1_relight_mc/tag', tag='SIM'), 300)],
        ['A3 start monitor', tvtxt(ctx.v(E, '/start_monitors_v2p9/A3'), 400)],
        ['A7 plausibility bands', tvtxt(ctx.v(E, '/start_monitors_v2p9/A7'), 400)],
        ['E3 (end of start)', tvtxt(ctx.v(E, '/start_monitors_v2p9/E3'), 300)],
    ]
    o.append(dtable(['Item', 'Value'], rows, widths=['30%', '70%']))
    o.append(doc.h(2, '10.5 Abort and refusal causes (firmware v2.9)'))
    cs = ctx.raw(E, '/abort_matrix/causes', default=[]) or []
    rows = []
    for k, c in enumerate(cs):
        b = f'/abort_matrix/causes/{k}'
        code = ctx.v(E, b + '/code', tag='DESIGN')
        cause = ctx.v(E, b + '/cause', tag='DESIGN')
        trig = ctx.v(E, b + '/trigger', tag='DESIGN')
        th = []
        for kk in (c.get('thresholds') or {}):
            t = ctx.v(E, f'{b}/thresholds/{kk}')
            th.append(Cell(f'<div class="small">{esc(kk)} = {t.h()}</div>', [t]))
        rows.append([Cell(f'{esc(code.num())}{code.ref()}', [code]), Cell(f'<b>{esc(cause.value)}</b>{cause.ref()}', [cause]), tvtxt(trig, 220),
                     cat(*th) if th else Cell('<span class="small">no threshold</span>', [trig])])
    o.append(dtable(['Code', 'Cause', 'Trigger', 'Thresholds'], rows, label_cols=0, cls='abort',
                    widths=['6%', '17%', '42%', '35%'], caption=f'{len(cs)} causes in electronics.json /abort_matrix/causes. REVISE per REV-ELEC-1; decided changes in §7.6.'))
    o.append(note_box(f'<b>Abort action.</b> {tvtxt(ctx.v(E, "/abort_matrix/actions", tag="LEAD")).html}', 'info'))
    o.append(doc.h(2, '10.6 Power'))
    PB = '/power_budget'
    rows = [['Battery', tvtxt(ctx.v(E, f'{PB}/battery', tag='DESIGN'))],
            ['Logic power, typical / peak', tvtxt(ctx.v(E, f'{PB}/logic_W', 'W'))],
            ['Energy per flight day', num_cell(ctx.v(E, f'{PB}/flight_day_Wh', 'Wh'), '.2f')],
            ['Energy per static-fire session', num_cell(ctx.v(E, f'{PB}/static_fire_session_Wh', 'Wh'), '.2f')],
            ['Peak current (three servos stalled)', num_cell(ctx.v(E, f'{PB}/peak_current_A', 'A'), '.1f')],
            ['Minimum voltage at the ECU', num_cell(ctx.v(E, f'{PB}/min_voltage_at_ECU_V', 'V'), '.2f')],
            ['Fusing', tvtxt(ctx.v(E, f'{PB}/fusing', tag='DESIGN'))],
            ['ARM bus peak vs fuse', tvtxt(ctx.v(E, f'{PB}/arm_bus_peak_vs_F301'), 300)]]
    o.append(dtable(['Item', 'Value'], rows, widths=['30%', '70%']))
    o.append(doc.h(2, '10.7 Head-end bleed provision and fail-safe states'))
    HB = '/head_end_bleed_provision'
    rows = [['Architecture', tvtxt(ctx.v(E, f'{HB}/architecture'), 400)],
            ['Pad built-in test', tvtxt(ctx.v(E, f'{HB}/pad_bit', tag='DESIGN'))],
            ['Purge', tvtxt(ctx.v(E, f'{HB}/purge'), 400)],
            ['Stuck-open bleed during a burn', tvtxt(ctx.v(E, f'{HB}/in_burn_stuck_open', tag='SIM'), 400)],
            ['Valve coil', tvtxt(ctx.v(E, f'{HB}/coil', tag='TO-VERIFY'), 300)]]
    fs = ctx.raw(E, '/fail_safe_states', default={}) or {}
    for k in fs:
        if k.startswith('superseded'):
            continue
        rows.append([f'Fail-safe: {esc(k)}', tvtxt(ctx.v(E, ptr_join('fail_safe_states', k), tag='DESIGN'), 300)])
    o.append(dtable(['Item', 'Value'], rows, widths=['30%', '70%']))
    o.append(doc.h(2, '10.8 Electronics open issues'))
    oi = ctx.raw(E, '/open_issues', default=[]) or []
    rows = []
    for k, x in enumerate(oi):
        b = f'/open_issues/{k}'
        rows.append([Cell(f'<b>{esc(x.get("id"))}</b>', [ctx.v(E, b + '/id', tag='DESIGN')]), tvtxt(ctx.v(E, b + '/severity', tag='DESIGN')),
                     tvtxt(ctx.v(E, b + '/issue', tag='TO-VERIFY'), 260), tvtxt(ctx.v(E, b + '/owner', tag='DESIGN'), 80)])
    o.append(dtable(['ID', 'Severity', 'Issue', 'Owner'], rows, label_cols=0, widths=['13%', '12%', '57%', '18%'],
                    caption=f'electronics.json /open_issues ({len(oi)} items).'))
    return '\n'.join(o)


# =============================================================================================
# section 11: mission and landing
# =============================================================================================
def sec_mission(ctx, doc, a, D):
    o = [doc.h(1, '11 Mission and landing')]
    cl = D['cl']
    G = 'GNC'
    o.append(doc.h(2, '11.1 Reference vehicle'))
    RV = '/reference_vehicle'
    rows = [
        ['Reference vehicle', tvtxt(ctx.v(G, f'{RV}/name', tag='ASSUMED'), 300)],
        ['Length / body diameter', cat(ctx.v(G, f'{RV}/length_overall_m', 'm').h('.2f'), ' / ', ctx.v(G, f'{RV}/body_diameter_m', 'm').h('.3f'))],
        ['Dry mass', num_cell(ctx.v(G, f'{RV}/dry_mass_kg', 'kg'), '.3f')],
        ['Fuel grain / N2O load / tank volume', cat(ctx.v(G, f'{RV}/fuel_grain_mass_kg', 'kg').h('.3f'), ' / ', ctx.v(G, f'{RV}/n2o_load_kg', 'kg').h('.2f'), ' / ',
                                                  ctx.v(G, f'{RV}/tank_volume_L', 'L').h('.3f'))],
        ['Lift-off mass / landing mass (nominal A1)', cat(ctx.v(G, f'{RV}/liftoff_mass_kg', 'kg').h('.3f'), ' / ', ctx.v(G, f'{RV}/landing_mass_kg', 'kg').h('.3f'))],
        ['Lift-off thrust-to-weight', tvtxt(ctx.v(G, '/lift_capability/rv1c_liftoff_T_W', tag_ptr='/lift_capability/tag'), 200)],
        ['Landing legs', tvtxt(ctx.v(G, f'{RV}/landing_legs'), 260)],
        ['Fins', tvtxt(ctx.v(G, f'{RV}/fins'), 200)],
        ['Tail-first aerodynamics', tvtxt(ctx.v(G, f'{RV}/aero/unknowns', tag='TO-VERIFY'), 260)],
    ]
    o.append(dtable(['Item', 'Value'], rows, widths=['30%', '70%'], caption='gnc.json v3 /reference_vehicle (parametric; the real airframe is owned outside the engine team).'))
    o.append(doc.h(2, '11.2 Mission plan'))
    MP = '/flight_profile/mission_plan_v3/v'
    nom = f'{MP}/A1/nominal_relight_planning_1.81s'
    apv = ctx.v(G, f'{MP}/A1/apogee_target_m', 'm', tag='REQ')
    n_g2 = cl.find('On GNC rev2')
    if n_g2:
        c_ap = cl.item(n_g2, 1)
        ap_new = rx_text(ctx, c_ap, r'A1 apogee target (\d+) m', 'm', tag='LEAD')
        apo_rows = [['A1 apogee target (newest lead decision)', cat(num_cell(ap_new, '.0f'), ' ', tvtxt(c_ap, 300))],
                    ['A1 apogee target in gnc.json v3 (planning value, superseded; §13.3 C-08)', Cell(f'<del class="stale">{apv.h(".0f")}</del>', [apv])],
                    ['A1 apogee trim rule', tvtxt(cl.item(168, 4), 400)],
                    ['Launch-commit condition added (newest lead decision)', tvtxt(cl.item(n_g2, 4, contains='launch-commit'), 300)]]
    else:
        apo_rows = [['A1 apogee target (planning)', num_cell(apv, '.0f')],
                    ['A1 apogee trim (newest lead decision)', tvtxt(cl.item(168, 4), 400)]]
    rows = [
        ['A1 role and profile', cat(tvtxt(ctx.v(G, f'{MP}/A1/role', tag='REQ')), ': ', tvtxt(ctx.v(G, f'{MP}/A1/profile', tag='REQ'), 300))],
        *apo_rows,
        ['A1 nominal: apogee / relight height / burn time / N2O burned / reserve',
         cat(ctx.v(G, f'{nom}/h_max', 'm', tag='SIM').h('.1f'), ' / ', ctx.v(G, f'{nom}/h_ign', 'm', tag='SIM').h('.1f'), ' / ',
             ctx.v(G, f'{nom}/burn_time_s', 's', tag='SIM').h('.2f'), ' / ', ctx.v(G, f'{nom}/n2o_burned', 'kg', tag='SIM').h('.3f'), ' / ',
             ctx.v(G, f'{nom}/reserve_frac', '', tag='SIM').h('.3f'))],
        ['B1 role', tvtxt(ctx.v(G, f'{MP}/B1/role', tag='REQ'))],
        ['B1 hop cap', cat(ctx.v(G, f'{MP}/B1/h_target_m', 'm').h('.0f'), ' — ', tvtxt(ctx.v(G, f'{MP}/B1/h_target_status', tag='LEAD'), 300))],
        ['B1 sizing height', num_cell(ctx.v(G, f'{MP}/B1/h_sizing_m', 'm'), '.0f')],
        ['B1 cap rule', tvtxt(cl.item(161, 7), 300)],
        ['B2', cat(tvtxt(ctx.v(G, f'{MP}/B2/role', tag='REQ')), ', ', ctx.v(G, f'{MP}/B2/h_target_m', 'm', tag='REQ').h('.0f'))],
        ['Order of first flights', tvtxt(ctx.v(G, f'{MP}/first_flights', tag='REQ'))],
        ['Launch commit (wind)', tvtxt(cl.item(161, 6), 300)],
        ['Mission statement (REQUIREMENTS)', tvtxt(md_bullet(ctx, 'REQ', 'Amendments after rev 2', 'Mission B1', 'LEAD'), 400)],
    ]
    o.append(dtable(['Item', 'Value'], rows, widths=['32%', '68%']))
    o.append(doc.h(2, '11.3 Landing Monte Carlo'))
    RP = '/relight_planning_v28'
    tag = ctx.v(G, f'{RP}/tag', tag='SIM')
    nrun = rx(ctx, G, f'{RP}/tag', r'(\d+) runs', 'runs', tag='SIM', note='runs per case')
    base = f'{MP}/A1/relight_v2.8/P_by_line_state_at_planning_value'
    bases = [('A1_none', 'A1, no throat growth'), ('A1_pc', 'A1, throat growth'), ('A1J_none', 'A1 ENG-07d basis, no growth'), ('A1J_pc', 'A1 ENG-07d basis, growth')]
    states = [('liq', 'liquid line'), ('vapU', 'vapour, upper'), ('vapF', 'vapour, full')]
    rows, prow = [], []
    n = nrun.value or 0
    def pcell(tv, label, color):
        if tv.value is None or not n:
            return Cell(tv.h(), [tv])
        lo, hi = wilson(tv.value, n)
        ci = ctx.d([round(lo, 4), round(hi, 4)], '', f'Wilson 95 % interval, n = {n:g} runs (from the GNC tag)', [tv, nrun])
        prow.append((label, tv.value, lo, hi, color))
        return cat(tv.h('.3f'), ' <span class="small">[', ci.h('.3f', pill=False), ']</span>')
    for bk, blab in bases:
        cells = [blab]
        for sk, slab in states:
            t = ctx.v(G, f'{base}/{bk}/P_by_state/{sk}', '', tag='SIM', tag_ptr=f'{RP}/tag')
            cells.append(pcell(t, f'{blab}, {slab}', C_ACC))
        t = ctx.v(G, f'{base}/{bk}/P_fault_1p37', '', tag='SIM', tag_ptr=f'{RP}/tag')
        cells.append(pcell(t, f'{blab}, fault path', C_BAD))
        oc = ctx.v(G, f'{RP}/v/sweep_and_full_by_base/{bk}/1.41/P_fault_1p37', '', tag='SIM', tag_ptr=f'{RP}/tag')
        cells.append(pcell(oc, f'{blab}, fault path, option (c)', C_OK))
        rows.append(cells)
    pv = ctx.v(G, f'{RP}/v/planning_value_s', 's')
    oc_s = ctx.v(G, '/requirements/ignition/relight_planning_value_s/option_c_unprimed_s', 's')
    o.append(dtable(['Basis', 'Liquid line', 'Vapour, upper', 'Vapour, full', 'Fault path (plan value)', 'Fault path, option (c)'], rows,
                    widths=['21%', '15%', '15%', '15%', '17%', '17%'],
                    caption=f'P(landing success), A1 relight at the planning value {esc(pv.num())} s ({pv.ref()}); option (c) plans '
                            f'{esc(oc_s.num())} s ({oc_s.ref()}) on an UNPRIMED flag. Wilson 95 % intervals DERIVED by the generator.'))
    b1 = rx(ctx, G, '/b1_regression_band/v/lead_cap/finding', r'P ([\d.]+) \[([\d.]+), ([\d.]+)\]', '', tag='SIM', group=1)
    b1lo = rx(ctx, G, '/b1_regression_band/v/lead_cap/finding', r'P ([\d.]+) \[([\d.]+), ([\d.]+)\]', '', tag='SIM', group=2)
    b1hi = rx(ctx, G, '/b1_regression_band/v/lead_cap/finding', r'P ([\d.]+) \[([\d.]+), ([\d.]+)\]', '', tag='SIM', group=3)
    if b1.value is not None:
        prow.append(('B1 at the hop cap, regression band + growth', b1.value, b1lo.value, b1hi.value, C_ACC2))
    o.append(dtable(['Case', 'Value'], [
        ['B1 at the provisional hop cap: P with regression band and throat growth [interval as published]', cat(b1.h('.3f'), ' [', b1lo.h('.3f', pill=False), ', ', b1hi.h('.3f', pill=False), ']')],
        ['B1 finding', tvtxt(ctx.v(G, '/b1_regression_band/v/lead_cap/finding', tag='SIM'), 420)]], widths=['36%', '64%']))
    if prow:
        src = plot_landing(a, prow)
        o.append(fig_html(src, 'Landing success by basis and line state at the relight (6-DOF Monte Carlo, SIM). Red: drained-segment fault path at '
                          'the planning value; green: the same fault path with option (c).', [nrun.tid, b1.tid], 'wide'))
    sup = ctx.raw('SUP', '/reviews', default=[]) or []
    j = next((k for k, r in enumerate(sup) if r.get('id') == 'REV-GNC-2'), None)
    rows = [['Monte Carlo basis', tvtxt(tag, 500)],
            ['Planning status', tvtxt(ctx.v(G, f'{RP}/v/status', tag='LEAD'), 400)],
            ['Not physical acceptance', tvtxt(ctx.v(G, '/publication_note/not_physical_acceptance', tag='SIM'), 300)]]
    if j is not None:
        rows.append(['RG-01 (relight evidence)', cat(ctx.v('SUP', f'/reviews/{j}/verdict', tag='DERIVED').h(), ': ',
                                                     tvtxt(ctx.v('SUP', f'/reviews/{j}/blocking', tag='DERIVED')))])
    rows.append(['RG-01 re-fly', tvtxt(cl.item(164, 9), 200)])
    o.append(dtable(['Item', 'Value'], rows, widths=['24%', '76%']))
    o.append(note_box('<b>RG-01 OPEN.</b> The A1 relight probabilities above come from the v2.8 relight study on the earlier segment basis. '
                      'The re-fly on the decided purge path and the re-routed coil (CHANGELOG 164) had not been published when this draft was generated; '
                      'the values are planning evidence, not a relight claim. CF-4 is the physical gate.', 'warn'))
    return '\n'.join(o)


# =============================================================================================
# section 12: verification status
# =============================================================================================
def sec_verification(ctx, doc, a, D):
    o = [doc.h(1, '12 Verification status')]
    cl = D['cl']
    note = ctx.v('SUP', '/note', tag='DESIGN')
    o.append(note_box(f'<b>Nothing in this datasheet is physical approval.</b> {tvtxt(note).html} No value here is a measurement. '
                      'Review verdicts, matching file hashes, clean CAD checks, passing unit tests and this document\'s own trace check '
                      'are digital evidence only.', 'warn'))
    o.append(doc.h(2, '12.1 Review register'))
    sup = ctx.raw('SUP', '/reviews', default=[]) or []
    rows = []
    for k, r in enumerate(sup):
        b = f'/reviews/{k}'
        rid = ctx.v('SUP', b + '/id', tag='DERIVED')
        dt = ctx.v('SUP', b + '/date', tag='DERIVED')
        vd = ctx.v('SUP', b + '/verdict', tag='DERIVED')
        dl = ctx.v('SUP', b + '/deliverable', tag='DERIVED')
        blk = ctx.v('SUP', b + '/blocking', tag='DERIVED') if r.get('blocking') else None
        same, changed, missing = hash_status(ctx, a, r.get('hashes_sha256_16'))
        hs = ctx.d(f'{len(same)} of {len(same) + len(changed) + len(missing)} reviewed files unchanged'
                   + (f'; changed since review: {", ".join(changed)}' if changed else '')
                   + (f'; not in the hub: {", ".join(missing)}' if missing else ''), '', 'sha256/16 of each reviewed hub file vs the register entry', [], ev='DERIVED')
        isnot = ('Not physical approval; not a review of any file changed after the listed hashes'
                 + ('; the reviewed files have since changed, so the verdict covers an earlier state' if changed else '')
                 + ('; not acceptance of the open findings' if blk else '') + '.')
        disp = ctx.v('SUP', b + '/lead_disposition', tag='LEAD') if r.get('lead_disposition') else None
        rows.append([Cell(f'<b>{esc(rid.value)}</b>{rid.ref()}<div class="small">{esc(dt.value)}</div>', [rid, dt]),
                     tvtxt(dl, 200),
                     cat(f'<b>{esc(vd.value)}</b> ', vd.pill(), vd.ref(), Cell('', [vd]),
                         ('<div class="small">Blocking: ' + tvtxt(blk, 300).html + '</div>') if blk else '', Cell('', [blk] if blk else [])),
                     cat(f'<span class="small">{esc(isnot)}</span><div class="small">', hs.h(pill=False), '</div>', Cell('', [hs]),
                         ('<div class="small">Lead disposition: ' + disp.h() + '</div>') if disp else '', Cell('', [disp] if disp else []))])
    o.append(dtable(['Review', 'Deliverable', 'Verdict', 'What it is not; file state'], rows, label_cols=0, widths=['12%', '30%', '28%', '30%'],
                    caption=f'reviews/SUPERVISION.json ({esc(ctx.src("SUP").sha16)}), {len(sup)} entries in register order. A verdict covers the hashed files only.'))
    o.append(doc.h(2, '12.2 Open items and blockers'))
    i_rg = next((k for k, r in enumerate(sup) if r.get('id') == 'REV-GNC-2'), None)
    i_el = next((k for k, r in enumerate(sup) if r.get('id') == 'REV-ELEC-1'), None)
    i_c2 = next((k for k, r in enumerate(sup) if r.get('id') == 'REV-COMB-2'), None)
    n_g2 = cl.find('On GNC rev2')
    if i_c2 is not None:
        rc2 = ('REV-COMB-2', 'Independent re-review of combustion v2.4', str(sup[i_c2].get('verdict')),
               [ctx.v('SUP', f'/reviews/{i_c2}/major', tag='DERIVED'), ctx.v('SUP', f'/reviews/{i_c2}/lead_disposition', tag='LEAD'), cl.item(172, 6)])
    else:
        rc2 = ('REV-COMB-2', 'Independent re-review of combustion v2.4', 'IN PROGRESS', [cl.item(170, 6)])
    items = [
        ('RG-01', 'A1 relight evidence on the current design basis' + (' (rev2 re-fly staged, SIM; independent review REV-GNC-3 pending)' if n_g2 else ''), 'BLOCKING',
         [ctx.v('SUP', f'/reviews/{i_rg}/blocking', tag='DERIVED') if i_rg is not None else ctx.missing('REV-GNC-2'), cl.item(164, 9), cl.item(161, 12)] +
         ([cl.whole(n_g2 - 1, 700), cl.item(n_g2, 8)] if n_g2 and cl.line(n_g2 - 1).get('owner') == 'gnc' else ([cl.item(n_g2, 8)] if n_g2 else []))),
        ('FA-1', 'Fuel-assisted relight pulse above proof at its upper bound (single control)',
         'DESIGN CONTINUATION ONLY' + ('; margins reported, not reviewed' if (D.get('fa1') or {}).get('mech') else ''),
         [ctx.v('CMB', '/fmea_input/v/FA-1/hazard', tag='DERIVED', tag_ptr='/fmea_input'), cl.item(170, 2), cl.item(172, 2)] +
         ([D['fa1']['dec'], D['fa1']['margins']] + ([D['fa1']['mech_rev']] if D['fa1'].get('mech') else []) if D.get('fa1') else [])),
        ('CF-4', 'Relight-purge cold flow (gate for the A1 relight claim)', 'NOT RUN (founders)',
         [ctx.v('CMB', '/cf4_gate/v/claim', tag='LEAD', tag_ptr='/cf4_gate'), cl.item(164, 5)]),
        ('IGN-1', 'Torch reliability, photodiode false positives, light spike on hardware', 'NOT RUN (founders)',
         [md_section_text(ctx, 'BENCH', 'IGN-1 / T1', 'DESIGN'), cl.item(160, 1, contains='IGN-1')]),
        ('B-PC-1', 'Pc chain residual and drift; sets the light-rule floor', 'NOT RUN (founders)',
         [md_row(ctx, 'BENCH', '1. Order and gates', '3', 2), cl.item(166, 5, contains='B-PC-1'), cl.item(166, 9)]),
        ('BLEED-MASS', 'Head-end bleed valve mass (MASS RISK, not baseline)', 'TO-VERIFY',
         [cl.item(164, 7), ctx.v('ELE', '/open_issues/18/issue', tag='TO-VERIFY')] + ([cl.item(n_g2, 2)] if n_g2 else [])),
        ('ENG-11', 'Gimbal axis stiffness and rocking mode', 'NOT MET (structure only)',
         [ctx.v('MEC', '/tvc_actuation/ENG-11_status', tag='DERIVED')] if ctx.raw('MEC', '/tvc_actuation/ENG-11_status', default=None) is not None else [req_row(ctx, 'ENG-11')]),
        ('ENG-07', 'Gimbal slew at the v2 hinge load', 'MARGINAL',
         [ctx.v('MEC', '/tvc_actuation/ENG-07_rate_status', tag='DERIVED')]),
        ('FEA', 'Structural margins of the pressure parts and gimbal', 'PENDING', [ctx.missing('Structural FEA margins (see §9)', 'PENDING')]),
        ('ENVELOPE', 'Swept radial envelope at the airframe wall', 'TO-VERIFY', [ctx.v('CHK', '/swept_worst_band', tag='TO-VERIFY')]),
        ('GRAIN-R4', 'Rounded port entrance r ≥ 4 mm shown in CAD/BOM', 'TO-VERIFY', [D.get('rnd_cad') or ctx.missing('rounded entrance check')]),
        rc2,
        ('COMB-v2.4a', 'Combustion interface patch for the stale values (override table §13.1)', 'IN PROGRESS', [cl.item(172, 6), D['ovr_summary']]),
        ('INTERLOCK-GB', 'Guard band of the tank interlock (channel uncertainty)', 'TO-DEFINE', [cl.item(172, 4)]),
        ('ELEC-v2.10', 'Electronics v2.10 answering REV-ELEC-1', 'IN PROGRESS',
         [ctx.v('SUP', f'/reviews/{i_el}/blocking', tag='DERIVED') if i_el is not None else ctx.missing('REV-ELEC-1'), cl.item(166, 10, contains='v2.10')]),
    ]
    rows = []
    for iid, what, st, tvs in items:
        ev = cat(*[Cell(f'<div class="dec">{tvtxt(t, 260).html}</div>', [t]) for t in tvs if t is not None])
        stv = ctx.t('generator', f'open-item status {iid}', st, 'TO-VERIFY' if st in ('TO-VERIFY', 'MARGINAL') else
                    ('PENDING' if (st in ('PENDING', 'IN PROGRESS') or st.startswith('REVISE') or st == 'CONDICIONADO') else ('TO-DEFINE' if st == 'TO-DEFINE' else 'MISSING')),
                    tag_raw='status summarised by the generator from the evidence in the row')
        rows.append([Cell(f'<b>{esc(iid)}</b><div class="small">{esc(what)}</div>', []), Cell(f'<b>{esc(st)}</b>', [stv]), ev])
    o.append(dtable(['Item', 'Status', 'Evidence (quoted)'], rows, widths=['20%', '13%', '67%']))
    o.append(doc.h(2, '12.3 Requirement verification methods'))
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
                acell.append(Cell(f'<div class="dec">{tvtxt(tva, 260).html}</div>', [tva]))
        rows.append([f'<b>{esc(r[0])}</b>', tvtxt(rq, 230), cat(*acell) if acell else Cell('<span class="small">none</span>', []), tvtxt(vm, 120)])
    o.append(dtable(['ID', 'Requirement (rev 2 text, start)', 'Amendments after rev 2 (sentences naming the ID)', 'Verification method'], rows,
                    widths=['7%', '42%', '33%', '18%'], free_cols=(2,),
                    caption=f'00-requirements/REQUIREMENTS.md §2 and its amendments ({esc(src_label(ctx, "REQ"))}). No requirement has been verified physically.'))
    o.append(doc.h(2, '12.4 Founder test list'))
    rows = []
    for r in md_table_rows(ctx.src('BENCH').text or '', '1. Order and gates'):
        if not r or not r[0].isdigit():
            continue
        rows.append([f'Bench step {esc(r[0])}', tvtxt(md_row(ctx, 'BENCH', '1. Order and gates', r[0], 1, ev='DESIGN')),
                     tvtxt(md_row(ctx, 'BENCH', '1. Order and gates', r[0], 2, ev='DESIGN'), 200), tvtxt(md_row(ctx, 'BENCH', '1. Order and gates', r[0], 3, ev='DESIGN'), 120)])
    for r in md_table_rows(ctx.src('REQ').text or '', '4. Gating early bench tests'):
        if not r or r[0] in ('Test',):
            continue
        rows.append(['Early purchase (REQ §4)', Cell(f'<b>{esc(r[0])}</b>', [md_row(ctx, 'REQ', '4. Gating early bench tests', r[0], 0, ev='REQ')]),
                     tvtxt(md_row(ctx, 'REQ', '4. Gating early bench tests', r[0], 2, ev='REQ'), 220), tvtxt(md_row(ctx, 'REQ', '4. Gating early bench tests', r[0], 1, ev='REQ'), 160)])
    pcs = ctx.raw('CMB', '/cf4_gate/v/pass_criteria', default=[]) or []
    for k, _ in enumerate(pcs):
        t = ctx.v('CMB', f'/cf4_gate/v/pass_criteria/{k}', tag='LEAD', tag_ptr='/cf4_gate')
        rows.append(['CF-4 pass criterion', Cell('<b>CF-4</b>', [t]), tvtxt(t, 200), Cell(f'02-combustion/CF-4-SPEC.md {esc(ctx.src("CF4").version or "")}', [t])])
    for st in ('Grain mass before', 'Port diameter at six', 'Time histories', 'At least two oxidiser'):
        t = md_bullet(ctx, 'T14', 'T1-T4 regression', st, 'DESIGN')
        rows.append(['T1–T4 measurement', Cell('<b>T1–T4</b>', [t]), tvtxt(t, 260), Cell(f'02-combustion/T1-T4-REGRESSION-SPEC.md {esc(ctx.src("T14").version or "")}', [t])])
    o.append(dtable(['Kind', 'Test', 'Gate or measurement', 'Needs / source'], rows, label_cols=1, widths=['13%', '13%', '50%', '24%'],
                    caption='Physical tests executed by the founders. None has been run. Cost: TO-QUOTE, delivered to Sønderborg, DK-6400.'))
    return '\n'.join(o)


# =============================================================================================
# section 13: open contradictions (registered when the sources actually disagree)
# =============================================================================================
def register_contradictions(ctx, a, D):
    cl = D['cl']
    sup = ctx.raw('SUP', '/reviews', default=[]) or []
    # C1: combustion interface reviewed vs current (no entry when any review hashed the current file)
    hk = ptr_join('interfaces/combustion.json')[1:]
    revs = [k for k, r in enumerate(sup) if 'interfaces/combustion.json' in (r.get('hashes_sha256_16') or {})]
    covered = [k for k in revs if sup[k]['hashes_sha256_16']['interfaces/combustion.json'] == ctx.src('CMB').sha16]
    if revs and not covered:
        i = revs[-1]
        ctx.contra('C-01', 'Combustion interface: reviewed state vs current file',
                   [(f'{sup[i].get("id")} reviewed hash', ctx.v('SUP', f'/reviews/{i}/hashes_sha256_16/{hk}', tag='DERIVED')),
                    ('current combustion.json version', ctx.v('CMB', '/version', tag='DESIGN'))],
                   'current combustion.json is used throughout', 'no review covers the current file; a re-review is needed.')
    # C2: grain mass
    gc = ctx.v('CMB', '/gas_path/grain/mass_kg', 'kg')
    gm = ctx.v('MP', '/grain_mass_wet_kg', 'kg', tag='DERIVED')
    if gc.value is not None and gm.value is not None and abs(gc.value - gm.value) > 0.005:
        gb = D['bom_by_pn'].get('ENG-GR-01')
        side3 = ctx.t('BOM', ptr_join('lines', gb.idx, 'notes'), gb.l.get('notes') or '', 'DESIGN', tag_raw='BOM notes') if gb else ctx.missing('BOM GR-01 notes')
        ctx.contra('C-02', 'Fuel grain mass: Combustion vs CAD density',
                   [('Combustion v2.4', gc), ('CAD v3.4.1 mass properties', gm), ('BOM GR-01 notes', side3), ('ENG-12', req_row(ctx, 'ENG-12'))],
                   'Combustion value (ENG-12)', 'CAD material density differs from the Combustion and BOM-note density; weigh every grain (ENG-12).')
    # C3: 30 bar abort persistence
    ci = D['cause_idx'].get('PC_OVERPRESSURE')
    if ci is not None:
        fw = ctx.v('ELE', f'/abort_matrix/causes/{ci}/thresholds/kPcOverPressureTime_s', 's')
        dec = cl.item(166, 4)
        dms = rx_text(ctx, dec, r'(\d+) ms persistence', 'ms', tag='LEAD')
        if fw.value is not None and dms.value is not None and abs(fw.value * 1000 - dms.value) > 1e-6:
            ctx.contra('C-03', '30 bar over-pressure abort: persistence and channel',
                       [('firmware v2.9', fw), ('CHANGELOG 160 (2)', cl.item(160, 2)), ('CHANGELOG 166 (4)', dec),
                        ('combustion.json v2.4 A4', ctx.v('CMB', '/abort_matrix_v2p4/v/A4', tag_ptr='/abort_matrix_v2p4'))],
                       'CHANGELOG 166 (4): filtered channel, 5 ms', 'Electronics v2.10 to implement (REV-ELEC-1).')
    # C4: A5 monitor deleted vs firmware
    a5 = ctx.v('ELE', '/start_monitors_v2p9/A5')
    d160 = cl.item(160, 1)
    if isinstance(a5.value, str) and 'unchanged' in a5.value and isinstance(d160.value, str) and 'DELETED' in d160.value:
        ctx.contra('C-04', 'A5 late-light monitor: deleted by decision, still an abort in firmware v2.9',
                   [('CHANGELOG 160 (1)', d160), ('firmware v2.9', a5)], 'deleted (LIGHT_SPIKE log event)', 'REV-ELEC-1 RE-01 blocking; Electronics v2.10.')
    # C5: option (c) key in gnc.json v3
    eo = ctx.v('ELE', '/relight_interface/fc_planning_from_gnc/option_c_unprimed_s', tag_default='DESIGN')
    go = ctx.v('GNC', '/requirements/ignition/relight_planning_value_s/option_c_unprimed_s', 's')
    if isinstance(eo.value, str) and eo.value.startswith('NOT') and go.value is not None:
        ctx.contra('C-05', 'Relight option (c) planning value: present in gnc.json v3 or not',
                   [('electronics.json v2', eo), ('gnc.json v3', go), ('CHANGELOG 161 (9)', cl.item(161, 9))],
                   'present (lead verified, CHANGELOG 161 (9))', 'Electronics fixes the lookup (OI-GNC-V3).')
    # C6: head-end bleed status inside electronics.json
    hs = ctx.v('ELE', '/relight_interface/head_end_bleed/status', tag_default='DESIGN')
    if isinstance(hs.value, str) and 'no design' in hs.value:
        ctx.contra('C-06', 'Head-end bleed: "fallback, no design" vs decided purge path',
                   [('electronics.json /relight_interface', hs), ('electronics.json /head_end_bleed_provision', ctx.v('ELE', '/head_end_bleed_provision/architecture')),
                    ('CHANGELOG 164 (1)', cl.item(164, 1))], 'CHANGELOG 164 (1): decided purge path', 'stale text in electronics.json v2; Electronics v2.10.')
    # C7: structural thrust case: LC2F and ICD bases vs the decided ignition interlock and the v2.4 MEOP basis
    k2f = next((k for k, c in enumerate(ctx.raw('FEALC', '/cases', default=[]) or []) if c.get('id') == 'LC2F'), None)
    W = D.get('worst', {})
    if k2f is not None and W.get('P') is not None:
        lt = ctx.v('FEALC', f'/cases/{k2f}/thrust_N', 'N', tag='DESIGN')
        lsrc = ctx.v('FEALC', f'/cases/{k2f}/src/thrust', tag='DESIGN')
        icd = md_row(ctx, 'ICD', '3. Loads', 'Physical worst-case thrust', 1, tag_col=2)
        e9 = md_bullet(ctx, 'REQ', 'Amendments after rev 2', 'ENG-09:', 'REQ')
        hot = [t for t in (lsrc, icd) if isinstance(t.value, str) and re.search(r'\b30\s*°?\s*C\b', t.value)]
        if lt.value is not None and hot and isinstance(e9.value, str) and 'T_tank <=' in e9.value:
            ctx.contra('C-07', 'Structural thrust case: LC2F and ICD bases vs the decided ignition interlock',
                       [('loadcases_v1 LC2F thrust', lt), ('LC2F source', lsrc), ('ICD §3', icd), ('ENG-09 amendment', e9),
                        ('combustion.json v2.4 MEOP basis', W['P']), ('thrust at the v2.4 basis', W['F'])],
                       'v2.4 MEOP basis (pressure); the thrust at that basis is MISSING',
                       'Combustion to publish the thrust at the MEOP basis; Mechanical to restate LC2F and the ICD row. Until then no thrust value is shown as bounding.')
    # C8: A1 apogee
    ap = ctx.v('GNC', '/flight_profile/mission_plan_v3/v/A1/apogee_target_m', 'm', tag='REQ')
    tr = cl.item(168, 4)
    n_g2 = cl.find('On GNC rev2')
    if n_g2 and ap.value is not None:
        c_ap = cl.item(n_g2, 1)
        ctx.contra('C-08', 'A1 apogee: planning target vs the target adopted after the purge sizing',
                   [('gnc.json v3', ap), ('REQUIREMENTS §1 mission', md_line(ctx, 'REQ', '4. Coast nose-first', 'REQ')),
                    ('CHANGELOG 168 (4) trim rule', tr), (f'CHANGELOG {n_g2} (1)', c_ap)], f'CHANGELOG {n_g2} (1)',
                   'gnc.json v3.1 (published after REV-GNC-3) and the REQUIREMENTS mission text to restate the target.')
    elif ap.value is not None and isinstance(tr.value, str) and 'trim' in tr.value:
        ctx.contra('C-08', 'A1 apogee: planning target vs trim adopted after the purge sizing',
                   [('gnc.json v3', ap), ('CHANGELOG 168 (4)', tr)], 'CHANGELOG 168 (4)', 'GNC re-fly sizes the trim.')
    # C9: igniter mass scope
    ig = D['bom_by_pn'].get('ENG-IG-01')
    im = ctx.v('CMB', '/igniter/mass_kg', 'kg')
    if ig and ig.unit is not None and isinstance(im.value, list) and not (im.value[0] <= ig.unit <= im.value[1]):
        ctx.contra('C-09', 'Igniter mass: Combustion system estimate vs BOM line',
                   [('combustion.json v2.4', im), ('BOM ENG-IG-01', ig.mass_tv), ('BOM ENG-IG-01 row', ig.row_tv)],
                   'both shown (scopes differ)', 'BOM line covers body and plug; solenoids and propane supply to be placed in the BOM or the exclusions.')
    # C10: mechanical interface basis vs CAD of the datasheet
    ms = ctx.v('MEC', '/status', tag='DESIGN')
    if isinstance(ms.value, str) and 'v3.3' in ms.value and a.cad_version != 'v3.3':
        ctx.contra('C-10', 'Mechanical interface basis vs CAD of this datasheet',
                   [('mechanical.json v2', ms), ('CAD build', ctx.v('PROP', '/cad_version', tag='DESIGN')), ('Mechanical open item', ctx.v('MEC', '/open_items/0', tag='PENDING'))],
                   f'CAD {a.cad_version} for geometry, BOM and mass; mechanical.json v2 for stiffness and loads until v2.1', 'mechanical.json v2.1 pending.')
    # C13: BOM total vs its own note (transport lock)
    bs = ctx.v('BOM', '/mass_sum_kg', 'kg', tag='DERIVED')
    if bs.value is not None and abs(bs.value - D['bom_sum_tv'].value) > 1e-3:
        expl = abs(bs.value - D['bom_sum_tv'].value - D['bom_lock_tv'].value) < 1e-3
        ctx.contra('C-13', 'CAD mass: BOM mass_sum_kg vs the sum of its lines',
                   [('BOM mass_sum_kg', bs), ('BOM mass_sum_note', ctx.v('BOM', '/mass_sum_note', tag='DERIVED')),
                    ('generator sum, transport lock excluded', D['bom_sum_tv']), ('transport-lock lines', D['bom_lock_tv'])],
                   'generator sum with the transport lock excluded, as the BOM note states',
                   ('the difference equals the transport-lock lines: mass_sum_kg includes them although the note excludes them. ' if expl else
                    'the difference is not explained by the transport-lock lines. ') + 'Mechanical to restate mass_sum_kg or the note.')
    # C14: FA-1 load decision vs the CAD parts of this datasheet (Mechanical margin result)
    F1 = D.get('fa1') or {}
    if F1.get('mech'):
        r9 = D['bom_by_pn'].get('ENG-TC-09')
        sides = [('FA-1 load decision', F1['dec'], 400),
                 (f'Mechanical result, CHANGELOG {F1["n_mech"]} (sentences on yield, joints and bearings, quoted in full)', F1['mech_key'], 1200)]
        if r9 is not None:
            sides.append((f'BOM ENG-TC-09 material (CAD {a.cad_version})', ctx.v('BOM', ptr_join(r9.kind, r9.idx) + '/material_name', tag='DESIGN')))
        ctx.contra('C-14', f'FA-1 load vs the parts of CAD {a.cad_version}: margins reported by Mechanical', sides,
                   f'CAD {a.cad_version} as built (no lead decision on the result yet)',
                   'lead decision on the Mechanical result; CAD v3.5 with the proposed part changes and its independent review; the datasheet '
                   'is regenerated on that CAD.')
    # C12: combustion.json wording behind the lead decisions (override table)
    act = [e for e in (ctx.ovr.entries if ctx.ovr else []) if e['status'] == 'ACTIVE']
    if act:
        i2 = next((k for k, r in enumerate(sup) if r.get('id') == 'REV-COMB-2'), None)
        sides = [('combustion.json version', ctx.v('CMB', '/version', tag='DESIGN'))]
        if i2 is not None:
            sides.append(('REV-COMB-2 majors', ctx.v('SUP', f'/reviews/{i2}/major', tag='DERIVED')))
        sides.append(('CHANGELOG 172 (6)', cl.item(172, 6)))
        ctx.contra('C-12', 'combustion.json v2.4 wording behind the lead decisions', sides,
                   'the decisions, via overrides ' + ', '.join(e['id'] for e in act) + ' (§13.1)',
                   'Combustion v2.4a patch; drop each override when the generator reports it REDUNDANT.')
    # C11: firmware constants generated from combustion v2.3
    gh = ctx.raw('ELE', '/inputs/generated_headers', default={}) or {}
    rows = [r for v in gh.values() for r in (v if isinstance(v, list) else []) if isinstance(r, list) and r and r[0] == 'combustion.json']
    if rows and any(len(r) > 2 and r[2] != ctx.src('CMB').sha16 for r in rows):
        ctx.contra('C-11', 'Firmware constants generated from an earlier combustion interface',
                   [('electronics.json generated headers', ctx.v('ELE', '/inputs/generated_headers', tag='DESIGN')), ('current combustion.json', ctx.v('CMB', '/version', tag='DESIGN'))],
                   'combustion.json v2.4', 'regenerate engine_params.h in Electronics v2.10.')


def sec_overrides(ctx, doc, a, D):
    ov = ctx.ovr
    o = [doc.h(2, '13.1 Decision overrides')]
    if not ov or not ov.entries:
        o.append('<p>No override table loaded: every interface value is shown as published.</p>')
        return '\n'.join(o)
    src = ctx.src('OVR')
    o.append(f'<p>Table gen/decision_overrides.json ({esc(ov.version or "")}, sha256/16 {esc(src.sha16)}). Each decision is quoted from its source; '
             'the generator checks that the cited text contains the key phrases and every number of the decision, and applies a target only while '
             'the stale wording is still in it. An entry with no active target is reported REDUNDANT and can be dropped.</p>')
    rows = []
    for e in ov.entries:
        srcs = cat(*[Cell(f'<div class="dec"><span class="mono small">{esc(SRC_FILE.get(t.sid, t.sid))} {esc(t.ptr or "")}</span><br>'
                          f'{tvtxt(t, 320, ovr="annot").html}</div>', [t]) for t in e['srcs']])
        tl = []
        for t in e['targets']:
            tl.append(f'{SRC_FILE.get(t["sid"], t["sid"])} {t["ptr"]}: {t["mode"]}, {t["status"]}, shown {t["shown"]}×')
        if e.get('annot'):
            tl.append(f'annotation of every displayed text quoting the single-point value: {e["annot"]["status"]}, shown {e["annot"]["shown"]}×')
        tt = ctx.t('generator', f'override {e["id"]} targets (this build)', '; '.join(tl), 'DERIVED', tag_raw='generator target check on this build')
        st = ctx.t('generator', f'override {e["id"]} status (this build)', e['status'], 'DERIVED', tag_raw='generator check on this build')
        rows.append([Cell(f'<b id="{esc(e["id"])}">{esc(e["id"])}</b><div class="small">{esc(e["topic"])}</div><div class="small">basis: {esc(e["basis"])}</div>', []),
                     cat(tvtxt(e['value_tv'], None, ovr=False), f'<div class="small"><b>{esc(st.value)}</b> {st.ref()}</div>', Cell('', [st])),
                     srcs,
                     Cell('<div class="small">' + '<br>'.join(esc(x) for x in tl) + f'</div> {tt.ref()}', [tt])])
    o.append(dtable(['Override', 'Decision shown', 'Cited sources (quoted)', 'Targets: key, mode, state, displays'], rows, cls='ovr',
                    widths=['13%', '27%', '36%', '24%']))
    o.append(doc.h(2, '13.2 Superseded values withheld'))
    rows = []
    for e in ov.sups:
        keys = '; '.join(f'{SRC_FILE.get(p["sid"], p["sid"])} {p["ptr"]}: {p["status"]}' for p in e['pointers']) or 'no key listed'
        kt = ctx.t('generator', f'withheld {e["id"]} keys (this build)', keys, 'DERIVED', tag_raw='generator check on this build')
        nm = ov.mask_hits.get(e['id'], 0)
        mt = ctx.t('generator', f'withheld {e["id"]} masks (this build)', f'{nm} displayed field{"" if nm == 1 else "s"} masked', 'DERIVED',
                   tag_raw='generator count on this build')
        co = ctx.t('generator', f'withheld {e["id"]} corroboration', 'yes' if e['corroborated'] else ('no' if e['corroborated'] is False else 'not checked'), 'DERIVED',
                   tag_raw='key present in combustion.json /superseded_v2p4 (the author\'s withdrawal list)')
        rows.append([Cell(f'<b id="{esc(e["id"])}">{esc(e["id"])}</b><div class="small">{esc(e["topic"])}</div>', []),
                     Cell(f'{esc(e["replacement"])}<div class="small">basis: {esc(e["basis"])}</div>', []),
                     Cell(f'<span class="small mono">{esc(kt.value)}</span> {kt.ref()}', [kt]),
                     Cell(f'{esc(mt.value)} {mt.ref()}', [mt]), Cell(f'{esc(co.value)} {co.ref()}', [co])])
    o.append(dtable(['ID', 'Shown instead', 'Keys withheld', 'Text masks', 'In the author\'s withdrawal list'], rows, label_cols=2, cls='fixed',
                    widths=['20%', '24%', '32%', '12%', '12%'],
                    caption='Values the Combustion author withdrew in REPORT v2.4 §13 that are still live in combustion.json v2.4 (REV-COMB-2 R2-05). '
                            'They are not shown in this datasheet; masked text reads "[withheld: superseded value, SUP-xx]".'))
    return '\n'.join(o)


def sec_contradictions(ctx, doc, a, D):
    o = [doc.h(1, '13 Decision overrides and open contradictions')]
    o.append(sec_overrides(ctx, doc, a, D))
    o.append(doc.h(2, '13.3 Open contradictions'))
    o.append('<p>Each entry cites every side. The column "shown in this datasheet" names the value used elsewhere in the document '
             '(the newest decided one). Entries are generated only when the current sources actually disagree.</p>')
    rows = []
    for c in sorted(ctx.contradictions, key=lambda c: int(re.sub(r'\D', '', c['id']) or 0)):
        sides = cat(*[Cell(f'<div class="dec"><b>{esc(sd[0])}:</b> {tvtxt(sd[1], sd[2] if len(sd) > 2 else 260).html}</div>', [sd[1]])
                      for sd in c['sides']])
        res = ctx.t('generator', f'contradiction {c["id"]}', f'{c["newest"]}. {c["resolution"]}', 'DERIVED', tag_raw='generator summary of the cited sides')
        rows.append([Cell(f'<b>{esc(c["id"])}</b><div class="small">{esc(c["title"])}</div>', []), sides, Cell(f'{esc(res.value)} {res.ref()}', [res])])
    if rows:
        o.append(dtable(['ID', 'Sides (quoted)', 'Shown in this datasheet; next step'], rows, widths=['18%', '57%', '25%']))
    else:
        o.append('<p>No contradiction detected in the current sources.</p>')
    return '\n'.join(o)


# =============================================================================================
# section 14: unknowns register
# =============================================================================================
def sec_unknowns(ctx, doc, a, D):
    o = [doc.h(1, '14 Unknowns register')]
    o.append('<p>Every value the sources mark MISSING, TO-DEFINE, PENDING or TO-VERIFY, plus every key the generator looked for and did not find. '
             'They are listed so that none is mistaken for a design value.</p>')
    seen = set()
    rows = []
    for tv in ctx.traces:
        if tv.ev in ('MISSING', 'TO-DEFINE', 'PENDING', 'TO-VERIFY') and tv.tid not in seen:
            seen.add(tv.tid)
            what = f'{tv.sid or "—"}: {tv.ptr or tv.note or ""}'
            val = tv.num() if tv.value is not None else (tv.status or tv.ev)
            if isinstance(tv.value, str):
                val = tv.value
            rows.append((tv.ev, tv.sid or '', tv.tid, what, ctx.ovr.annot_plain(val) if ctx.ovr else val))
    rows.sort(key=lambda r: (['MISSING', 'PENDING', 'TO-DEFINE', 'TO-VERIFY'].index(r[0]), r[1], int(r[2][1:])))
    counts = {k: sum(1 for r in rows if r[0] == k) for k in ('MISSING', 'PENDING', 'TO-DEFINE', 'TO-VERIFY')}
    o.append('<p class="small">' + ' · '.join(f'{ev_pill(k)} {v}' for k, v in counts.items()) + '</p>')
    body = [[f'<a class="tr" href="#{r[2]}">{r[2]}</a>', ev_pill(r[0]), f'<span class="mono">{esc(r[3][:150])}</span>',
             esc(str(r[4])[:260] + ('…' if len(str(r[4])) > 260 else ''))] for r in rows]
    o.append(table(['Trace', 'Class', 'Source key', 'Value or text'], body, cls='dt unk', widths=['7%', '10%', '33%', '50%']))
    D['unknown_counts'] = counts
    return '\n'.join(o)


# =============================================================================================
# section 15: revision history and sources
# =============================================================================================
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
        base = a.hub if s.path.startswith(a.hub) else (a.cad_dir if s.path.startswith(a.cad_dir) else (DS_ROOT if s.path.startswith(DS_ROOT) else ''))
        rel = os.path.relpath(s.path, base) if base else s.path
        where = 'hub' if base == a.hub else ('CAD' if base == a.cad_dir else ('datasheet' if base == DS_ROOT else 'other'))
        rows.append([f'<b>{esc(sid)}</b>', esc(s.role), f'<span class="mono">{esc(where)}: {esc(rel)}</span>', esc(s.version or '—'),
                     f'<span class="mono">{esc(s.sha16 or "MISSING")}</span>', esc(s.mtime or '—'), str(s.reads)])
    o.append(table(['ID', 'Role', 'Path', 'Version', 'sha256/16', 'Modified (UTC)', 'Reads'], rows, cls='dt src',
                   widths=['7%', '24%', '30%', '9%', '13%', '13%', '4%']))
    o.append(f'<p class="small">Hub root: <span class="mono">{esc(a.hub)}</span>. CAD root: <span class="mono">{esc(a.cad_dir)}</span>. '
             f'The same table, with absolute paths, is written to out/sources.json.</p>')
    return '\n'.join(o)


# =============================================================================================
# appendix A: value trace
# =============================================================================================
def sec_trace(ctx, doc, a, D):
    o = [doc.h(1, 'Appendix A Value trace')]
    o.append('<p class="small">Every traced value used in this document: trace id, value as displayed, evidence class, source and version, '
             'key (JSON pointer, markdown row, CHANGELOG line and item, or generator formula) and the source tag text. Identical source keys share one id.</p>')
    rows = []
    for tv in ctx.traces:
        s = ctx.sources.get(tv.sid)
        src = f'{tv.sid} {s.version or ""}'.strip() if s else (tv.sid or '—')
        if isinstance(tv.value, str):
            val = tv.value if len(tv.value) <= 90 else tv.value[:88] + '…'
        elif isinstance(tv.value, dict) or (isinstance(tv.value, list) and not all(isinstance(x, (int, float)) for x in tv.value)):
            r_ = readable(tv.value)
            val = r_ if len(r_) <= 90 else r_[:88] + '…'
        else:
            val = tv.num() + (f' {tv.unit}' if tv.unit and tv.value is not None else '')
        if ctx.ovr:
            val = ctx.ovr.annot_plain(val)
        key = tv.ptr or (f'formula: {tv.formula}' if tv.formula else '')
        extra = tv.tag_raw or ''
        if tv.inputs:
            extra += ' ← ' + ', '.join(tv.inputs[:8]) + (' …' if len(tv.inputs) > 8 else '')
        if tv.note and tv.note not in extra:
            extra += f' [{tv.note}]'
        rows.append(f'<tr id="{tv.tid}"><td class="mono">{tv.tid}</td><td>{esc(val)}</td><td>{ev_pill(tv.ev)}</td><td>{esc(src)}</td>'
                    f'<td class="mono">{esc(key[:160])}</td><td>{esc(extra[:200])}</td></tr>')
    o.append('<table class="dt trace"><colgroup><col style="width:6%"><col style="width:20%"><col style="width:9%"><col style="width:11%">'
             '<col style="width:26%"><col style="width:28%"></colgroup><thead><tr><th>ID</th><th>Value</th><th>Class</th><th>Source</th><th>Key</th>'
             '<th>Source tag / formula</th></tr></thead><tbody>' + '\n'.join(rows) + '</tbody></table>')
    return '\n'.join(o)


# =============================================================================================
# preparation: CAD-derived values, renders, BOM aggregates, exclusions
# =============================================================================================
def check_renders(ctx, a):
    rm = ctx.src('RMAN').data or {}
    if not rm:
        return
    if rm.get('glb_sha256_16') != ctx.src('GLB').sha16:
        ctx.issue('ERROR', f'renders are stale: render manifest GLB {rm.get("glb_sha256_16")} vs current GLB {ctx.src("GLB").sha16}; re-run gen/render_views.sh')
    if rm.get('bom_sha256_16') != ctx.src('BOM').sha16:
        ctx.issue('ERROR', f'renders are stale: render manifest BOM {rm.get("bom_sha256_16")} vs current BOM {ctx.src("BOM").sha16}')
    if rm.get('cad_version') != a.cad_version:
        ctx.issue('ERROR', f'render manifest CAD version {rm.get("cad_version")} vs requested {a.cad_version}')
    for v in rm.get('views', []):
        p = os.path.join(a.renders, v['png'])
        if not os.path.exists(p):
            ctx.issue('ERROR', f'render {v["png"]} listed but missing')
        elif sha16_file(p) != v.get('png_sha256_16'):
            ctx.issue('WARN', f'render {v["png"]} changed after the manifest was written')


def prepare(ctx, a):
    D = {'generated': now_utc()}
    D['cl'] = Changelog(ctx, 'CL')
    idx = pts_index(ctx)
    D['tpi'] = idx
    D['rated'] = {'F': tp(ctx, idx, 1.0, 'F_N', 'N'), 'Isp': tp(ctx, idx, 1.0, 'Isp_SL_s', 's')}
    D['rated_low'] = rx_text(ctx, D['cl'].item(170, 1), r'~(\d+) N at', 'N', tag='DERIVED',
                             note='rated thrust if T1 measures eta_cf at the low end of its band (CHANGELOG 170 (1))')
    pc = tp(ctx, idx, 1.0, 'Pc_Pa', 'Pa')
    D['pc_rated_cell'] = Cell(pres(ctx, pc), [pc])
    D['floor_F'] = tp(ctx, idx, 0.2, 'F_N', 'N')
    D['mass_wet_all'] = ctx.v('MP', '/states/wet/all/m_kg', 'kg', tag='DERIVED', note='CAD model total, wet (full grain)')
    # envelope from the manifest
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
    by = {}
    for r in bom:
        if r.kind == 'lines' and r.pn not in by:
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
    bs = ctx.raw('BOM', '/mass_sum_kg', default=None)
    if bs is not None and abs(bs - tot) > 1e-3:
        ctx.issue('WARN', f'BOM mass_sum_kg {bs} differs from the generator sum {tot:.4f} (lock lines {D["bom_lock_tv"].value:.4f} kg; listed as C-13)')
    mw = D['mass_wet_all'].value
    if mw is not None and abs(mw - tot) > 0.01:
        ctx.issue('INFO', f'massprops wet total {mw} vs BOM line sum {tot:.4f} (different scopes possible)')
    D['cost_tv'] = TV(ctx, None, 'EUR', 'MISSING', 'BOM /currency: prices not given, every line TO-QUOTE unless dated', 'BOM', '/currency',
                      note='total not summed: no line carries a DK-6400 quotation', status='TO-QUOTE (not summed)')
    ctx.unknowns.append({'what': 'Total cost (every BOM line TO-QUOTE, delivery Sønderborg DK-6400)', 'status': 'MISSING', 'tid': D['cost_tv'].tid})
    # material usage
    mu = {}
    for r in lines:
        k = r.l.get('material_name') or r.l.get('material') or 'unspecified'
        mu.setdefault(k, []).append(r)
    D['mat_usage'] = {k: {'n_tv': ctx.d(len(v), '', f'count of BOM lines with material_name "{k}"', [r.row_tv for r in v]),
                          'mass_tv': ctx.d(sum(r.line_mass or 0 for r in v), 'kg', f'Σ qty × unit mass, material "{k}"', [r.mass_tv for r in v]),
                          'o2_tv': ctx.d(sum(1 for r in v if str(r.l.get('oxygen_clean')) == 'True'), '', f'count of oxygen-clean lines, material "{k}"', [r.row_tv for r in v])}
                      for k, v in mu.items()}
    D['cause_idx'] = {c.get('cause'): i for i, c in enumerate(ctx.raw('ELE', '/abort_matrix/causes', default=[]) or [])}
    # exclusions from the CAD mass (not zero: carried at their source value or UNKNOWN)
    cl = D['cl']
    ex, ep, er = [], [], []
    tank = ctx.v('MEC', '/fixed_module/tank/tube_mass_kg', 'kg', tag='DERIVED')
    ex.append(['N2O tank: tube only (bulkheads, valves, fittings not designed)', num_cell(tank, '.3f'), tvtxt(ctx.v('MEC', '/fixed_module/tank/concept', tag='DERIVED'), 160)])
    ep.append(('N2O tank, tube only', tank.value))
    er.append(tank.tid)
    prng = ctx.v('BOM', '/provision_mass_estimate_kg/estimate_range_kg', 'kg', tag='ASSUMED')
    ex.append(['Head-end bleed provision, excluding valves (BOM ENG-BL lines)', num_cell(prng, '.3f'), tvtxt(ctx.v('BOM', '/provision_mass_estimate_kg/note', tag='ASSUMED'), 200)])
    ep.append(('Bleed provision excl. valves', tuple(prng.value) if isinstance(prng.value, list) else prng.value))
    er.append(prng.tid)
    vdec = cl.item(164, 7)
    vn = rx_text(ctx, vdec, r'(\d+) x ([\d.]+) kg', '', tag='LEAD', group=1)
    vm = rx_text(ctx, vdec, r'(\d+) x ([\d.]+) kg', 'kg', tag='LEAD', group=2)
    vt = ctx.d(vn.value * vm.value if (vn.value and vm.value) else None, 'kg', 'n valves × mass per valve (MASS RISK, not baseline)', [vn, vm], ev='TO-VERIFY')
    ex.append(['Bleed valves (MASS RISK, not baseline)', num_cell(vt, '.2f'), tvtxt(vdec, 260)])
    ep.append(('Bleed valves, MASS RISK', vt.value))
    er.append(vt.tid)
    nm = ctx.v('MEC', '/fixed_module/not_modelled', tag='MISSING')
    nmm = ctx.missing('mass of the items listed as not modelled in mechanical.json v2 (CAD v3.3 basis)', 'MISSING')
    ex.append(['Other items not modelled (mechanical.json v2 list)', Cell(nmm.h(), [nmm]), tvtxt(nm, 300)])
    ep.append(('Other items not modelled', None))
    er.append(nmm.tid)
    ecu = ctx.v('ELE', '/ecu/mass_kg', 'kg')
    ecur = ctx.v('ELE', '/ecu/mass_kg/range', 'kg', tag='ASSUMED')
    ex.append(['Engine ECU (on the fixed structure, not in CAD)', cat(ecu.h('.2f'), ' (', ecur.h('.2f', pill=False), ')'), tvtxt(ctx.v('ELE', '/ecu/architecture'), 160)])
    ep.append(('Engine ECU', tuple(ecur.value) if isinstance(ecur.value, list) else ecu.value))
    er.append(ecu.tid)
    n2o = ctx.v('CMB', '/decisions/N2O_load_and_tank/v/m_N2O_kg', 'kg', tag_ptr='/decisions/N2O_load_and_tank')
    ex.append(['N2O load (propellant)', num_cell(n2o, '.2f'), tvtxt(ctx.v('CMB', '/decisions/N2O_load_and_tank/tag', tag='LEAD'), 160)])
    er.append(n2o.tid)
    D['exclusions'], D['excl_plot'], D['excl_refs'] = ex, ep, er
    return D


# =============================================================================================
# page design (print CSS)
# =============================================================================================
CSS = r'''
@page { size: A4; }
:root { --ink:#1d2733; --ink2:#44515e; --mut:#6b7885; --rule:#cfd6dd; --rule2:#e6eaee; --acc:#0b3a5c; --acc2:#0b5c8c; --bg2:#f4f6f8; }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { margin: 0; font-family: "Inter DS", Inter, "DejaVu Sans", sans-serif; font-size: 8.3pt; line-height: 1.38; color: var(--ink); background: #fff;
       font-feature-settings: "tnum" 1, "cv11" 1; }
h1 { font-size: 15pt; font-weight: 700; color: var(--acc); margin: 0 0 3.5mm; padding-bottom: 1.6mm; border-bottom: 1.2pt solid var(--acc);
     break-before: page; break-after: avoid; letter-spacing: -0.01em; }
h2 { font-size: 10.4pt; font-weight: 650; color: var(--acc); margin: 5mm 0 2mm; break-after: avoid; }
h3 { font-size: 9pt; font-weight: 650; margin: 3.5mm 0 1.5mm; break-after: avoid; }
p { margin: 0 0 2.2mm; }
code, .mono { font-family: "DejaVu Sans Mono", monospace; font-size: 0.9em; }
a { color: inherit; text-decoration: none; }
.small { font-size: 0.86em; color: var(--ink2); }
.miss { color: #b4232a; font-weight: 650; }
.v { font-weight: 600; }
.u { color: var(--ink2); }
.alt { color: var(--ink2); }
.qt { }
.tr { font-size: 5.6pt; color: #8a96a3; margin-left: 1.2pt; vertical-align: 0.6pt; font-family: "DejaVu Sans Mono", monospace; }
.ev { display: inline-block; font-size: 5.3pt; font-weight: 650; letter-spacing: 0.02em; padding: 0.15pt 2.4pt; border-radius: 2pt;
      vertical-align: 0.8pt; line-height: 1.25; white-space: nowrap; margin-left: 1.5pt; }
.ev-sim { background:#e1eefa; color:#0b5c8c; } .ev-derived { background:#e3f1ea; color:#2f6f4f; } .ev-assumed { background:#fff0d4; color:#8a5a00; }
.ev-datasheet { background:#eee8fb; color:#5b3fa3; } .ev-to-verify { background:#ffe3c7; color:#9a4a00; } .ev-literature { background:#eceff2; color:#44515e; }
.ev-design { background:#e8edf3; color:#24384d; } .ev-req { background:#fbe6e6; color:#8c1d24; } .ev-lead { background:#ddf1ee; color:#155e57; }
.ev-missing, .ev-to-define, .ev-pending { background:#b4232a; color:#fff; } .ev-none { background:#ddd; color:#444; }
.ev-superseded { background:#e4e7ea; color:#4d5965; }
del.stale { color: #7b8794; text-decoration: line-through; text-decoration-color: #b4232a; }
ins.dec { text-decoration: none; background: #ddf1ee; color: #0f4f49; padding: 0 1.2pt; border-radius: 1.5pt; }
a.ovr, .ovr-m a { font-weight: 700; color: #155e57; font-size: 0.9em; }
.ovr-m { font-size: 0.75em; margin-left: 0.6pt; }
.ovr-note { display: block; font-size: 0.86em; color: #155e57; margin-top: 0.6pt; }
.stale-src { font-size: 0.86em; color: #6b7785; margin-top: 0.8pt; }
table.ovr td { font-size: 6.9pt; }
table.fixed, table.ovr { table-layout: fixed; width: 100%; }
table.fixed td, table.ovr td { overflow-wrap: anywhere; }
table { border-collapse: collapse; width: 100%; margin: 1.5mm 0 3.5mm; }
caption { caption-side: top; text-align: left; font-size: 7.2pt; color: var(--ink2); padding: 0 0 1.2mm; }
th { text-align: left; font-weight: 650; font-size: 7.2pt; color: var(--acc); background: var(--bg2); border-bottom: 0.8pt solid var(--acc);
     padding: 1.4pt 3pt; vertical-align: bottom; }
td { padding: 1.5pt 3pt; border-bottom: 0.4pt solid var(--rule2); vertical-align: top; font-size: 7.6pt; }
tr { break-inside: avoid; }
thead { display: table-header-group; }
tr.sub td { background: var(--bg2); font-weight: 650; color: var(--acc); font-size: 7.2pt; padding-top: 2pt; }
table.dt td:first-child { color: var(--ink); }
table.bom td { font-size: 6.8pt; padding: 1.2pt 2.4pt; }
table.bom .sup { font-size: 6pt; color: var(--mut); }
table.abort td { font-size: 6.9pt; }
table.trace td, table.unk td { font-size: 6.1pt; padding: 0.8pt 2pt; border-bottom: 0.3pt solid var(--rule2); word-break: break-word; }
table.trace th, table.unk th { font-size: 6.4pt; }
table.src td { font-size: 6.4pt; word-break: break-all; }
table.schema td { font-size: 6.8pt; }
.dec { margin: 0 0 1.2pt; }
.pn { font-family: "DejaVu Sans Mono", monospace; font-size: 6.6pt; font-weight: 600; }
.q { display: inline-block; font-size: 5.6pt; font-weight: 700; color: #9a4a00; background: #ffe3c7; padding: 0.1pt 2.2pt; border-radius: 2pt; }
.o2 { display: inline-block; font-size: 5.6pt; font-weight: 700; color: #0b5c8c; border: 0.5pt solid #0b5c8c; padding: 0 1.8pt; border-radius: 2pt; margin-left: 2pt; }
.box { border-left: 2.2pt solid; padding: 2mm 3mm; margin: 2mm 0 3.5mm; break-inside: avoid; font-size: 7.8pt; }
.box-info { border-color: #0b5c8c; background: #f0f6fb; }
.box-warn { border-color: #c06a00; background: #fff6ea; }
figure { margin: 2mm 0 4mm; break-inside: avoid; }
figure img, figure svg { display: block; max-width: 100%; }
figure.wide img { width: 100%; }
figure.half img { width: 62%; margin: 0 auto; }
figure.art img { width: 100%; }
figcaption { font-size: 7pt; color: var(--ink2); margin-top: 1.2mm; }
.figref { color: var(--mut); font-size: 6.2pt; }
.legend { display: grid; grid-template-columns: 1fr 1fr; gap: 1.2mm 6mm; margin: 1mm 0 3mm; font-size: 7.4pt; }
ul.mats { columns: 2; font-size: 7.4pt; margin: 0 0 2mm; padding-left: 4mm; }
.ortho-pair { display: flex; gap: 3mm; break-inside: avoid; }
.ortho-pair .ortho { flex: 1; }
.ortho-pair svg { width: 100%; height: auto; max-height: 150mm; }
.render.iso img { height: 150mm; margin: 0 auto; }
.render.section svg { height: 214mm; width: auto; margin: 0 auto; }
.render.layout svg { width: 100%; height: auto; }
.famgrid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 2.5mm; margin: 2mm 0 3mm; }
.fam { border: 0.4pt solid var(--rule); padding: 1.5mm; break-inside: avoid; }
.fam .fimg { height: 34mm; display: flex; align-items: center; justify-content: center; }
.fam .fimg img { max-height: 34mm; max-width: 100%; }
.fam .fcap { font-size: 6.4pt; margin-top: 1mm; line-height: 1.3; }
/* cover */
section.cover { height: 262mm; display: flex; flex-direction: column; break-after: page; }
.cv-band { background: var(--acc); color: #fff; padding: 7mm 8mm 6mm; }
.cv-prog { font-size: 7.6pt; letter-spacing: 0.08em; text-transform: uppercase; opacity: 0.85; }
.cv-title { font-size: 25pt; font-weight: 750; margin-top: 2mm; letter-spacing: -0.015em; }
.cv-sub { font-size: 9.4pt; margin-top: 1.5mm; opacity: 0.92; }
.cv-main { display: flex; gap: 6mm; flex: 1; padding-top: 5mm; min-height: 0; }
.cv-hero { width: 40%; display: flex; flex-direction: column; align-items: center; justify-content: flex-start; }
.cv-hero img.hero { max-height: 192mm; max-width: 100%; }
.cv-cap { font-size: 6.4pt; color: var(--mut); margin-top: 2mm; text-align: center; }
.cv-side { width: 60%; display: flex; flex-direction: column; gap: 3mm; }
.cv-draft { align-self: flex-start; font-size: 11pt; font-weight: 800; color: #b4232a; border: 1.4pt solid #b4232a; padding: 1mm 3mm; letter-spacing: 0.06em; }
.cv-warn { font-size: 7.8pt; border-left: 2.4pt solid #b4232a; background: #fdf0f0; padding: 2mm 3mm; }
.tiles { display: grid; grid-template-columns: 1fr 1fr; gap: 2mm; }
.tile { border: 0.5pt solid var(--rule); padding: 2mm 2.5mm; }
.tile .tl { font-size: 6.6pt; color: var(--mut); text-transform: uppercase; letter-spacing: 0.04em; }
.tile .tv { font-size: 10.5pt; margin-top: 0.8mm; }
.tile .tv .v { font-weight: 700; }
.tile .tsub { font-size: 6.3pt; color: var(--ink2); margin-top: 0.6mm; }
.tile .tsub .v { font-weight: 600; }
table.cv-cfg td, table.cv-cfg th { font-size: 6.8pt; padding: 1pt 2.5pt; }
.cv-gen { font-size: 6.6pt; color: var(--mut); }
/* contents */
section.toc { break-after: page; }
h1.toc-h { break-before: avoid; }
.toc-l1 { font-weight: 650; margin-top: 1.6mm; font-size: 8.6pt; }
.toc-l2 { padding-left: 6mm; font-size: 7.8pt; }
.toc-l1 a, .toc-l2 a { display: flex; align-items: baseline; }
.toc .dots { flex: 1; border-bottom: 0.6pt dotted #9aa5b1; margin: 0 1.5mm; transform: translateY(-1.5pt); }
.toc .pg { font-variant-numeric: tabular-nums; min-width: 6mm; text-align: right; }
'''


# =============================================================================================
# HTML assembly, PDF printing (Chromium via Playwright) and the contents pass
# =============================================================================================
def html_doc(title, body):
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{esc(title)}</title>'
            f'<meta name="generator" content="{GEN_NAME} {GEN_VERSION}"><style>{CSS}</style></head><body>{body}</body></html>')


def print_pdf(a, html_path, pdf_path, D):
    hdr = (f'<div style="font-family:\'Inter DS\',Inter,sans-serif;font-size:6.6px;color:#55626f;width:100%;padding:0 14mm;display:flex;justify-content:space-between;">'
           f'<span><b style="color:#0b3a5c">{esc(DOC_ID)}</b> · {esc(a.rev)} · <b style="color:#b4232a">DRAFT</b></span>'
           f'<span>Not physical approval · CAD {esc(a.cad_version)}</span></div>')
    ftr = (f'<div style="font-family:\'Inter DS\',Inter,sans-serif;font-size:6.6px;color:#55626f;width:100%;padding:0 14mm;display:flex;justify-content:space-between;">'
           f'<span>Generated {esc(D["generated"])} · {GEN_NAME} {GEN_VERSION} · digital design data only</span>'
           f'<span>Page <span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
    cfg = {'header': hdr, 'footer': ftr, 'margin': {'top': '17mm', 'bottom': '15mm', 'left': '14mm', 'right': '14mm'}}
    cfgp = os.path.join(a.build, 'print_config.json')
    json.dump(cfg, open(cfgp, 'w'))
    env = dict(os.environ)
    env.setdefault('PLAYWRIGHT_BROWSERS_PATH', a.pw_browsers)
    if getattr(a, 'fontconf', None):
        env['FONTCONFIG_FILE'] = a.fontconf
    r = subprocess.run([a.node, os.path.join(HERE, 'print_pdf.mjs'), html_path, pdf_path, cfgp], env=env, capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError('PDF printing failed: ' + r.stderr[-2000:])
    return r.stdout.strip()


def pdf_pages_text(pdf_path):
    r = subprocess.run(['pdftotext', '-layout', pdf_path, '-'], capture_output=True, text=True)
    return r.stdout.split('\f')


def pdf_npages(pdf_path):
    r = subprocess.run(['pdfinfo', pdf_path], capture_output=True, text=True)
    m = re.search(r'Pages:\s+(\d+)', r.stdout)
    return int(m.group(1)) if m else None


def norm_line(s):
    return re.sub(r'[^0-9a-z]+', '', s.lower())


def locate_heads(doc, pages):
    """Page of each heading: first exact (normalised) line match, scanning forward from the previous heading's page.
    Contents lines end with a page number, so they never match exactly."""
    start, missing = 1, []
    for hd in doc.heads:
        target = norm_line(hd['text'])
        found = None
        for i in range(start, len(pages)):
            for ln in pages[i].splitlines():
                if norm_line(ln) == target:
                    found = i + 1
                    break
            if found:
                break
        if found is None:
            for i in range(start, len(pages)):
                for ln in pages[i].splitlines():
                    nl = norm_line(ln)
                    if nl.startswith(target) and not nl[len(target):].isdigit():
                        found = i + 1
                        break
                if found:
                    break
        hd['page'] = found
        if found:
            start = found - 1
        else:
            missing.append(hd['text'])
    return missing


# =============================================================================================
# main
# =============================================================================================
def main(argv=None):
    ap = argparse.ArgumentParser(description='ARGOS H1 engine datasheet generator')
    ap.add_argument('--cad-version', default='v3.4.1')
    ap.add_argument('--cad-dir', default=DEFAULT_CAD_DIR)
    ap.add_argument('--hub', default=DEFAULT_HUB)
    ap.add_argument('--rev', default='rev0-draft')
    ap.add_argument('--note', default='first draft generated from the hub state; FEA, RG-01 re-fly, Electronics v2.10 and the Combustion v2.4a '
                                      'interface patch pending (FA-1 envelope data folded in)')
    ap.add_argument('--out', default=os.path.join(DS_ROOT, 'out'))
    ap.add_argument('--renders', default=None, help='render folder (default build/renders/<cad-version>)')
    ap.add_argument('--decisions', type=int, default=8, help='number of recent lead decisions listed in §1.3')
    ap.add_argument('--no-pdf', action='store_true')
    ap.add_argument('--node', default='/opt/node22/bin/node')
    ap.add_argument('--pw-browsers', default='/opt/pw-browsers')
    ap.add_argument('--overrides', default=os.path.join(HERE, 'decision_overrides.json'),
                    help='decision override table (JSON); "none" shows every interface value as published')
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
        D['ovr_summary'] = ctx.missing('decision override table not loaded (combustion.json wording shown as published)', 'MISSING')
    # revision history carried from the previous sources.json (other revision labels only)
    hist = []
    prev = os.path.join(a.out, 'sources.json')
    if os.path.exists(prev):
        try:
            hist = [h for h in json.load(open(prev)).get('revision_history', []) if h.get('rev') != a.rev]
        except (ValueError, OSError):
            hist = []
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
    for fn in sorted(glob.glob(os.path.join(a.out, 'assets', '*.svg'))):
        leak_scan(ctx, 'assets/' + os.path.basename(fn), open(fn, encoding='utf-8', errors='replace').read())
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
        leak_scan(ctx, 'the PDF text', '\n'.join(ptxt))
        annot_scan(ctx, ptxt)
        if toc_info['missing']:
            ctx.issue('WARN', f'headings not located in the PDF text: {toc_info["missing"]}')
    # records
    srcs = {sid: {'path': s.path, 'role': s.role, 'kind': s.kind, 'version': s.version, 'sha256_16': s.sha16, 'size': s.size,
                  'mtime_utc': s.mtime, 'exists': s.exists, 'required': s.required, 'reads': s.reads} for sid, s in ctx.sources.items()}
    json.dump({'document': DOC_ID, 'revision': a.rev, 'generated_utc': D['generated'], 'generator': f'gen/{GEN_NAME} {GEN_VERSION}',
               'generator_sha256_16': sha16_file(os.path.abspath(__file__)), 'cad_version': a.cad_version, 'hub': a.hub, 'cad_dir': a.cad_dir,
               'renders': a.renders, 'sources': srcs, 'revision_history': hist,
               'note': 'Digital design data only; nothing here is physical approval.'}, open(os.path.join(a.out, 'sources.json'), 'w'), indent=1)
    tr = [{'id': t.tid, 'value': t.value if not isinstance(t.value, float) or math.isfinite(t.value) else str(t.value), 'unit': t.unit, 'class': t.ev,
           'tag_raw': t.tag_raw, 'source': t.sid, 'key': t.ptr, 'note': t.note, 'formula': t.formula, 'inputs': t.inputs, 'status': t.status,
           'masked': t.masked} for t in ctx.traces]
    json.dump({'document': DOC_ID, 'revision': a.rev, 'n': len(tr), 'traces': tr}, open(os.path.join(a.out, 'trace.json'), 'w'), indent=0, default=str)
    cls_counts = {}
    for t in ctx.traces:
        cls_counts[t.ev or 'UNTAGGED'] = cls_counts.get(t.ev or 'UNTAGGED', 0) + 1
    qa = {'generated_utc': D['generated'], 'cells': {'data_cells': CELL_STATS['data_cells'], 'traced': CELL_STATS['traced'],
                                                     'untraced': CELL_STATS['untraced']},
          'traces': len(ctx.traces), 'classes': cls_counts, 'untagged': [t.tid for t in ctx.traces if not t.ev],
          'issues': ctx.qa, 'contradictions': [c['id'] + ' ' + c['title'] for c in ctx.contradictions],
          'unknowns': D.get('unknown_counts'), 'pages': npages, 'toc': toc_info,
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
          f'issues: {n_err} errors, {sum(1 for q in ctx.qa if q["level"] == "WARN")} warnings')
    return 1 if n_err else 0


if __name__ == '__main__':
    sys.exit(main())

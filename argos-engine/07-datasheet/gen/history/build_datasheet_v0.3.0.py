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
GEN_VERSION = '0.3.0'
DOC_ID = 'ARGOS-H1-ENGINE-DATASHEET'
DEFAULT_HUB = '/home/claude/work/shared-fallback/engine'
DEFAULT_CAD_DIR = '/home/claude/work/shared-fallback/engine/03-cad/v3.5.2'
HERE = os.path.dirname(os.path.abspath(__file__))
DS_ROOT = os.path.dirname(HERE)
G0 = 9.80665  # standard gravity, m/s2 (defined constant, not data)


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
        resolve_class(self)  # v0.3.0: ten tags or DECIDED; no default class
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
        return ev_pill(self.ev, self.tag_raw, getattr(self, 'basis', None), self.status if self.value is not None else None)

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
                tag_raw = f'(class set at the call site: {tag})'
        else:
            ev = normalise_tag(tag_raw)
            if ev is None and tag_raw is None and tag_default is not None:
                ev, tag_raw = tag_default, f'(no source tag; class set at the call site: {tag_default})'
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
            'ELE': 'electronics.json', 'GNC': 'gnc.json', 'MEC': 'mechanical.json', 'FA1': 'fa1_envelope_v2p4a.json',
            'F3D': 'REPORT-FEA3D-v352.md', 'DSIC': 'DATASHEET-INPUTS-COMBUSTION.md', 'DSIG': 'DATASHEET-INPUTS-GNC.md',
            'MMXMD': 'margin_matrix_v352.md (rows v8)', 'TXT5': 'item_c_tf1_texts_v352_v5.json', 'BOM': 'BOM_v3.5.2.json',
            'MP': 'massprops_v3.5.2.json', 'MDEL': 'massdelta_v3.5.2_vs_v3.5.1.json', 'F4J': 'f4_v352.json', 'SET': 'set_v3.5.2.json',
            'BENCH': 'bench_plan_v4.md', 'RCMB': 'combustion REPORT.md', 'RPL': 'plume REPORT.md', 'PVAL': 'validation_v2.json'}


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


# =============================================================================================
# section 2: key performance
# =============================================================================================


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


# =============================================================================================
# section 4: geometry and mass
# =============================================================================================


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


# =============================================================================================
# section 6: materials and thermal protection
# =============================================================================================


# =============================================================================================
# section 7: combustion
# =============================================================================================


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


# =============================================================================================
# section 9: structural FEA (PENDING until hub/04-fea margins or mechanical.json v2.1)
# =============================================================================================


# =============================================================================================
# section 10: electronics
# =============================================================================================


# =============================================================================================
# section 11: mission and landing
# =============================================================================================


# =============================================================================================
# section 12: verification status
# =============================================================================================


# =============================================================================================
# section 13: open contradictions (registered when the sources actually disagree)
# =============================================================================================


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
                    caption='Values the Combustion author withdrew in REPORT v2.4 §13 (their list: combustion.json /superseded_v2p4), wherever combustion.json '
                            f'{esc(ctx.src("CMB").version or "")} still carries them. '
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


# =============================================================================================
# appendix A: value trace
# =============================================================================================


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


# =============================================================================================
# rev1 code (v0.3.0): new_00_infra.py, new_10_prepare.py, new_30_sec_a.py, new_40_sec_geo.py, new_50_sec_fea.py, new_60_sec_cmb.py, new_65_sec_plume.py, new_70_sec_ele.py, new_80_sec_ver.py, new_90_main.py, new_95_appendix.py
# =============================================================================================
# ---------------------------------------------------------------------------------------------
# v0.3.0 infrastructure: evidence model, CHANGELOG reader, markdown row finders, rev1 sources,
# print header
# ---------------------------------------------------------------------------------------------
PAGE_STATEMENT = 'SIM / CALC / DERIVED; not physical approval; no hardware has been tested'
CL_MARK = re.compile(r'^\(?(founder )?(decisions?|result|review|note|handback|direction)\b', re.I)
CL_DEC = re.compile(r'^\(?(founder )?decisions?\b', re.I)

# Evidence model (lead rulings 2026-10-21 12:13Z item 4 and 12:17Z). Every number carries one of the ten
# evidence tags, or the source-class pill DECIDED (a design value, decided limit or requirement: chosen, not
# measured or computed), or it is counted as UNTAGGED in qa_report. The generator sets no default class:
# a class comes from the source tag, from the quoted text, or from an explicit class at the call site
# (recorded in the trace as 'class set at the call site').
TEN_TAGS = ['SIM', 'CALC', 'DERIVED', 'ASSUMED', 'DATASHEET', 'LITERATURE', 'AS RECALLED', 'TO-VERIFY', 'MISSING', 'ESTIMATE']
EV_CLASSES = TEN_TAGS + ['DECIDED']
SOURCE_CLASS_NAMES = {'LEAD': 'Lead decision', 'DESIGN': 'Design value', 'REQ': 'Requirement'}
STATUS_CLASSES = ('PENDING', 'SUPERSEDED', 'TO-DEFINE')
TEN_WORD = re.compile(r'(?<![A-Za-z0-9_\-])(SIM|CALC|DERIVED|ASSUMED|DATASHEET|LITERATURE|AS RECALLED|TO-VERIFY|TO-CONFIRM|MISSING|ESTIMATE|FEA|CEA)'
                      r'(?![A-Za-z0-9_\-])')
WORD_MAP = {'TO-CONFIRM': 'TO-VERIFY', 'FEA': 'SIM', 'CEA': 'SIM'}
CLASS_WORD = re.compile(r'\[(SIM|CALC|DERIVED|ESTIMATE|ASSUMED|DATASHEET|LITERATURE|AS RECALLED|TO-VERIFY)\b')
UNLESS_TAGGED = re.compile(r'\b((?:SIM|CALC|DERIVED|ESTIMATE)(?:\s*/\s*(?:SIM|CALC|DERIVED|ESTIMATE))*) unless tagged')
QUANTITY = re.compile(r'(?<![\w.\-])[+\-−]?\d+(?:\.\d+)?\s?(?:%|bar|kg|g|kN|N\s?m|N·m|N|mm|cm|m|ms|s|K|°C|C|MPa|GPa|kPa|Pa|V|mV|W|Hz|L|'
                      r'm/s²|m/s2|m/s|rad/s|rad|°|deg|J|A)(?![\w/])'
                      r'|(?<![\w.\-])[+\-−]\d+\.\d+(?![\w.])|(?<![\w.\-])\d+\.\d{2,}(?![\w.])')


def ten_words(s, limit=3):
    """Distinct words of the ten evidence tags in a text, in order of first appearance (FEA / CEA read as SIM)."""
    out = []
    for m in TEN_WORD.finditer(s or ''):
        w = WORD_MAP.get(m.group(1), m.group(1))
        if w not in out:
            out.append(w)
    return out[:limit]


def is_number(v):
    if isinstance(v, bool):
        return False
    if isinstance(v, (int, float)):
        return True
    return isinstance(v, (list, tuple)) and len(v) > 0 and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v)


def has_quantity(s):
    return bool(QUANTITY.search(s or ''))


def ev_ok(ev):
    """True for one of the ten tags or a ' / ' list of them."""
    return bool(ev) and all(p.strip() in TEN_TAGS for p in str(ev).split(' / '))


def _gen_free(tag_raw):
    return re.sub(r'\((?:class set|no source tag)[^)]*\)', '', str(tag_raw or ''))


def _plain_text(v):
    if isinstance(v, str):
        return v
    if isinstance(v, (dict, list)):
        try:
            return readable(v)
        except Exception:
            return json.dumps(v, default=str)
    return ''


BASIS_PHRASE = re.compile(r"\b(?:on|from)\s+(?:the\s+|a\s+|an\s+)?(?:author's\s+)?(SIM|CALC|DERIVED|ASSUMED|DATASHEET|LITERATURE|AS RECALLED|ESTIMATE)\b")


def own_and_basis_words(tag_raw):
    """Evidence words that tag the value itself, and the words of a basis phrase ('on SIM', 'from SIM') that
    describe what a decided value rests on."""
    t = _gen_free(tag_raw)
    basis = list(dict.fromkeys(m.group(1) for m in BASIS_PHRASE.finditer(t)))
    return ten_words(BASIS_PHRASE.sub(' ', t)), basis


def basis_of(tv, kind):
    """Source-class text of a DECIDED value: 'Lead decision, line N (k)', 'Design value, <file> <version>',
    'Requirement, ENG-xx' (lead ruling 12:17Z (1))."""
    raw = _gen_free(tv.tag_raw)
    s = tv.ctx.sources.get(tv.sid) if tv.sid else None
    fname = SRC_FILE.get(tv.sid) or (os.path.basename(s.path) if s else (tv.sid or 'generator'))
    where = f'{fname} {(s.version if s and s.version else "")}'.strip()
    if tv.sid == 'CL':
        m = re.match(r'L(\d+)(?:\((\d+)\))?', tv.ptr or '')
        ln = (m.group(1) + (f' ({m.group(2)})' if m.group(2) else '')) if m else '?'
        owner = raw.split(' ')[0] if raw.strip() else 'lead'
        return (f'Lead decision, line {ln}' if owner == 'lead' else f'{owner.capitalize()} line {ln}'), raw.strip()
    if kind == 'LEAD':
        m = re.search(r'(?:CHANGELOG|line|lines|l\.)\s*(\d{2,3})(?:\s*\((\d+[a-z]?)\))?', raw) or re.search(r'(?<![\d.])(\d{3})\s*\((\d+[a-z]?)\)', raw)
        if m:
            return f'Lead decision, line {m.group(1)}' + (f' ({m.group(2)})' if m.group(2) else ''), f'tag in {where}: {raw.strip()}'
        m = re.search(r'(20\d\d-\d\d-\d\d)', raw)
        if m:
            return f'Lead decision of {m.group(1)}', f'tag in {where}: {raw.strip()}'
        return f'Lead decision, per {where}', f'tag in {where}: {raw.strip()}'
    if kind == 'REQ':
        m = re.search(r'\b(ENG-\d+[a-z]?)\b', raw + ' ' + str(tv.ptr or ''))
        return 'Requirement' + (f', {m.group(1)}' if m else f', {where}'), f'tag in {where}: {raw.strip()}'
    return f'Design value, {where}', (f'tag in {where}: {raw.strip()}' if raw.strip() else f'{where}')


def resolve_class(tv):
    """Final evidence class of a traced value (called by TV.__init__). The v0.2.0 source classes LEAD / DESIGN /
    REQ become DECIDED with their source text, unless the source tag (for a number) or the quoted text (for a
    text) names one of the ten tags for the value itself; status words become a status."""
    ev, val = tv.ev, tv.value
    tv.basis = getattr(tv, 'basis', None)
    tv.basis_detail = getattr(tv, 'basis_detail', None)
    tv.basis_kind = getattr(tv, 'basis_kind', None)
    tv.ident = bool(isinstance(val, int) and not isinstance(val, bool) and str(tv.ptr or '').endswith('/code'))
    if ev in STATUS_CLASSES:
        tv.status = tv.status or ev
        if val is None:
            ev = 'MISSING'
        elif tv.formula:
            ev = 'DERIVED'
        else:
            w = ten_words(_gen_free(tv.tag_raw)) + ten_words(_plain_text(val))
            w = list(dict.fromkeys(w))[:3]
            ev = ' / '.join(w) if w else ('MISSING' if ev == 'TO-DEFINE' else None)
    if ev in SOURCE_CLASS_NAMES or ev == 'DECIDED':
        kind = ev if ev in SOURCE_CLASS_NAMES else (tv.basis_kind or 'LEAD')
        tv.basis_kind = kind
        nk = normalise_tag(_gen_free(tv.tag_raw).strip() or None)
        if nk in SOURCE_CLASS_NAMES and kind == 'DESIGN':
            kind = nk                      # the source tag names a lead decision or a requirement
        tv.basis_kind = kind
        own, bw = own_and_basis_words(tv.tag_raw)
        if not tv.basis:
            tv.basis, tv.basis_detail = basis_of(tv, kind)
            if bw:
                tv.basis += '; basis ' + ' / '.join(bw)
        if val is None:
            ev = 'MISSING'
        elif is_number(val):
            ev = own[0] if own else 'DECIDED'
        else:
            # a decision, design or requirement text is DECIDED; tags quoted inside it stay visible in the quoted text
            # (lead 2026-10-21 12:52Z: line 264 items DECIDED); only the source tag's own words can replace DECIDED
            ev = ' / '.join(own[:3]) if own else 'DECIDED'
    elif ev is not None and not ev_ok(ev) and ev != 'REF':
        tv.ctx.issue('WARN', f'class {ev!r} is not one of the ten tags at {tv.sid}:{tv.ptr}')
        ev = None
    tv.ev = ev


def ev_pill(ev, tag_raw=None, basis=None, status=None):
    """Evidence pill: one of the ten tags (or a ' / ' list of them), DECIDED with its source text, REF (a
    reference text, no pill) or UNTAGGED."""
    st = f' <span class="ev ev-status">{esc(status)}</span>' if status and status != ev else ''
    if ev == 'REF':
        return st.strip()
    if not ev:
        return '<span class="ev ev-none" title="no tag">UNTAGGED</span>' + st
    title = f' title="{esc(tag_raw)}"' if tag_raw else ''
    b = f'<span class="evb">{esc(basis)}</span>' if basis else ''
    if ev == 'DECIDED':
        return f'<span class="ev ev-decided"{title}>DECIDED</span>{b}{st}'
    first = re.sub(r'[^a-z]+', '-', str(ev).split(' / ')[0].lower()).strip('-')
    return f'<span class="ev ev-{first}"{title}>{esc(ev)}</span>{b}{st}'


def normalise_tag(raw):
    """Map a source tag string onto the evidence classes (the ten tags) or a source class (LEAD, DESIGN, REQ),
    which resolve_class turns into DECIDED. None when the tag names no class."""
    if raw is None:
        return None
    t = str(raw).strip()
    u = t.upper()
    if not u:
        return None
    if u.startswith('TO-VERIFY') or u.startswith('TO-CONFIRM') or u.startswith('DATASHEET-PENDING') or u.startswith('TO-CHECK'):
        return 'TO-VERIFY'
    if u.startswith('TO-DEFINE'):
        return 'TO-DEFINE'
    if u.startswith('PENDING'):
        return 'PENDING'
    if u.startswith('UNKNOWN') or u.startswith('OPEN') or u.startswith('MISSING'):
        return 'MISSING'
    if u.startswith('AS RECALLED'):
        return 'AS RECALLED'
    if u.startswith('CALC'):
        return 'CALC'
    if u.startswith('SIM') or u.startswith('FEA') or u.startswith('CEA'):
        return 'SIM'
    if u.startswith('ESTIMATE') or u.startswith('[ESTIMATE'):
        return 'ESTIMATE'
    if u.startswith('DERIVED'):
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
    m = re.search(r'\b(SIM|CALC|DERIVED|ESTIMATE|ASSUMED|DATASHEET|LITERATURE|AS RECALLED|TO-VERIFY|DESIGN|REQ|LEAD)\b', u)
    if m:
        return m.group(1)  # first class word inside a free-text tag
    return None


def cl_class(rec, txt=None):
    """Class of a CHANGELOG text. A lead line is a decision record: source class LEAD (DECIDED unless the quoted
    text carries one of the ten tags, see resolve_class). A specialist's line: its first bracketed tag word, else its
    own 'X unless tagged' statement; else no class (counted as untagged)."""
    owner = (rec.get('owner') or '').strip()
    if owner == 'lead':
        return 'LEAD'
    t = txt if txt is not None else (rec.get('text') or '')
    m = CLASS_WORD.search(t)
    if m:
        return m.group(1)
    m = UNLESS_TAGGED.search(rec.get('text') or '')
    if m:
        return re.sub(r'\s*/\s*', ' / ', m.group(1))
    w = ten_words(t, 1)
    return w[0] if w else None


WORKPATH = re.compile(r"(?:the |a )?(?:lead|author's|author|coordinator) scratchpad(?: [\w./\-]+)?|/home/claude[\w./\-]*|/tmp/[\w./\-]*")


def redact_paths(txt):
    """Quoted text with every working-path mention replaced by a visible marker (the quote is otherwise verbatim)."""
    if not isinstance(txt, str):
        return txt, 0
    n = len(WORKPATH.findall(txt))
    return (WORKPATH.sub('[working copy; path not printed]', txt), n) if n else (txt, 0)


class Changelog:
    """Line-numbered CHANGELOG reader (v0.3.0: an explicit class may be given for a quoted item or sentence; working-path
    mentions in a quote are replaced by a visible marker)."""

    def __init__(self, ctx, sid):
        self.ctx, self.sid = ctx, sid
        self.lines = ctx.src(sid).text.splitlines() if ctx.src(sid).text else []

    def line(self, n):
        raw = self.lines[n - 1]
        parts = raw.split(' | ')
        rec = {'n': n, 'raw': raw, 'sha16': sha16_text(raw)}
        if len(parts) >= 4 and re.match(r'^\d{4}-\d\d-\d\d$', parts[0]) and CL_MARK.match(parts[2]):
            rec.update(date=parts[0], owner=parts[1], what=parts[2], text=' | '.join(parts[3:]), why='')
        elif len(parts) >= 4 and re.match(r'^\d{4}-\d\d-\d\d$', parts[0]):
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

    def _tag(self, rec):
        return f"{rec.get('owner')} {rec.get('what')} {rec.get('date')} (line sha {rec['sha16']})"

    def _t(self, ptr, txt, ev, tag):
        txt2, n = redact_paths(txt)
        return self.ctx.t(self.sid, ptr, txt2, ev, tag_raw=tag, note=(f'{n} working-path mention(s) replaced by a marker' if n else ''))

    def item(self, n, k, sentence=None, contains=None, ev=None, why=None):
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
        tag = self._tag(rec) + (f'; class set at the call site: {why}' if ev and why else '')
        return self._t(ptr, txt, ev or cl_class(rec, txt), tag)

    def clip(self, n, k, start, end, ev=None, why=None):
        """Verbatim part of item (k) of line n from the first occurrence of start to the end of the next occurrence of
        end (used where a sentence of the item also names a working path that is not printed)."""
        rec = self.line(n)
        if k is None:
            txt = rec['text']
        else:
            its = self.items(n)
            txt = re.sub(r'^\(%d\)\s*' % k, '', its.get(k, ''))
        i = txt.find(start)
        j = txt.find(end, i + len(start) - len(end) if len(end) < len(start) else i) if i >= 0 else -1
        if i < 0 or j < 0:
            self.ctx.issue('WARN', f'CHANGELOG line {n} item ({k}): no text from {start!r} to {end!r}')
            return self.ctx.missing(f'CHANGELOG L{n} item ({k}) text from "{start}"')
        tag = self._tag(rec) + (f'; class set at the call site: {why}' if ev and why else '')
        return self._t(f'L{n}' + (f'({k})' if k is not None else '') + f'[from "{start}" to "{end}"]', txt[i:j + len(end)],
                       ev or cl_class(rec, txt[i:j + len(end)]), tag)

    def whole(self, n, maxlen=None):
        rec = self.line(n)
        txt = rec['text'] if maxlen is None or len(rec['text']) <= maxlen else rec['text'][:maxlen].rsplit(' ', 1)[0] + ' …'
        return self._t(f'L{n}', txt, cl_class(rec), self._tag(rec))

    def find(self, needle, owner='lead', what='(decision)'):
        """Line number of the newest entry by owner/what whose text contains needle (None if absent)."""
        for i in range(len(self.lines), 0, -1):
            rec = self.line(i)
            if rec.get('owner') == owner and (rec.get('what') == what or (what == '(decision)' and CL_DEC.match(rec.get('what') or ''))) \
                    and needle in rec['text']:
                return i
        return None

    def part(self, n, contains=None, ev=None, why=None):
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
        tag = self._tag(rec) + (f'; class set at the call site: {why}' if ev and why else '')
        return self._t(ptr, txt, ev or cl_class(rec, txt), tag)

    def decisions(self, owner='lead', last=None):
        out = []
        for i in range(1, len(self.lines) + 1):
            rec = self.line(i)
            if rec.get('owner') == owner and CL_DEC.match(rec.get('what') or ''):
                out.append(rec)
        return out[-last:] if last else out


def rx(ctx, sid, ptr, pattern, unit='', tag=None, conv=None, group=1, note=''):
    """Number extracted from a text value at a JSON pointer with an explicit regex (recorded). v0.3.0: no
    default class; without a tag here or in the source the value is UNTAGGED."""
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
    ev = tag or normalise_tag(tag_raw)
    return TV(ctx, val, unit, ev, tag_raw or (f'(class set at the call site: {tag})' if tag else None), sid, loc, note=note)


def rx_text(ctx, tv, pattern, unit='', tag=None, group=1, note=''):
    """Number extracted with a recorded regex from a text value already traced (CHANGELOG item, markdown row).
    v0.3.0: without an explicit class the number takes the text's class; a DECIDED text passes its source class
    (lead decision, design value, requirement) so that the number gets its own basis text."""
    s = tv.value if isinstance(tv.value, str) else None
    m = re.search(pattern, s) if s else None
    loc = f'{tv.ptr} [regex {pattern}]'
    if not m:
        ctx.issue('WARN', f'regex not matched {tv.sid}:{tv.ptr} {pattern}')
        t = TV(ctx, None, unit, 'MISSING', tv.tag_raw, tv.sid, loc, status='MISSING', note='pattern not found')
        ctx.unknowns.append({'what': f'{tv.sid}:{loc}', 'status': 'MISSING', 'tid': t.tid})
        return t
    ev = tag or ((getattr(tv, 'basis_kind', None) or 'LEAD') if tv.ev == 'DECIDED' else tv.ev)
    traw = tv.tag_raw
    if tag and tag != tv.ev and tag not in SOURCE_CLASS_NAMES:
        traw = (f'{traw}; ' if traw else '') + f'(class set at the call site: {tag})'
    return TV(ctx, float(m.group(group)), unit, ev, traw, tv.sid, loc, note=note)


def md_row(ctx, sid, section_prefix, key, col, ev=None, tag_col=None, maxlen=None):
    """Text cell of a markdown table row selected by its first-column key (v0.3.0: no default class)."""
    rows = md_table_rows(ctx.src(sid).text or '', section_prefix)
    for r in rows:
        if r and re.sub(r'\*', '', r[0]).strip() == key:
            if col >= len(r):
                break
            txt = re.sub(r'\*\*', '', r[col]).strip()
            tag_raw = r[tag_col].strip() if (tag_col is not None and tag_col < len(r)) else None
            e = ev or normalise_tag(tag_raw.split('/')[0] if tag_raw else None)
            return ctx.t(sid, f'§{section_prefix or "*"} row "{key}" col {col}', txt, e, tag_raw=tag_raw)
    ctx.issue('WARN', f'markdown row not found {sid} §{section_prefix} {key!r}')
    return ctx.missing(f'{sid} §{section_prefix} row {key}')


def md_rows_all(text, section_prefix=None, exact=False):
    """(line number, cells) of every table row in a section (heading text starting with the prefix)."""
    out, in_sec = [], section_prefix is None
    for i, ln in enumerate((text or '').splitlines(), 1):
        if ln.startswith('#'):
            if section_prefix is not None:
                h = ln.lstrip('#').strip()
                in_sec = (h == section_prefix) if exact else h.startswith(section_prefix)
            continue
        if in_sec and ln.startswith('|') and not re.match(r'^\|\s*-', ln):
            out.append((i, [c.strip() for c in ln.strip().strip('|').split(' | ')]))
    return out


def md_find(ctx, sid, section_prefix, conds, col, ev=None, tag_col=None, tag_raw=None, note='', strip_bold=True):
    """Text cell of the one markdown table row whose columns match conds {col: exact text}; the locator
    names the section, the matched columns and the column read."""
    rows = md_rows_all(ctx.src(sid).text or '', section_prefix)
    hit = []
    for ln, r in rows:
        ok = True
        for c, want in conds.items():
            got = re.sub(r'\*\*', '', r[c]).strip() if c < len(r) else None
            if got != want:
                ok = False
                break
        if ok:
            hit.append((ln, r))
    loc = f'§{section_prefix or "*"} row ' + ' & '.join(f'c{c}="{w}"' for c, w in conds.items()) + f' col {col}'
    if len(hit) != 1:
        ctx.issue('WARN', f'markdown row {sid} {loc}: {len(hit)} matches')
        return ctx.missing(f'{sid} {loc}')
    ln, r = hit[0]
    if col >= len(r):
        ctx.issue('WARN', f'markdown row {sid} {loc}: no column {col}')
        return ctx.missing(f'{sid} {loc}')
    txt = re.sub(r'\*\*', '', r[col]).strip() if strip_bold else r[col].strip()
    traw = tag_raw or (r[tag_col].strip() if (tag_col is not None and tag_col < len(r)) else None)
    e = ev or normalise_tag(traw.split('/')[0] if traw else None)
    return ctx.t(sid, loc + f' (line {ln})', txt, e, tag_raw=traw, note=note)


def md_rows_where(ctx, sid, section_prefix, col0_re=None):
    """Rows of a section (optionally those whose first cell matches a regex), header row dropped."""
    rows = md_rows_all(ctx.src(sid).text or '', section_prefix)
    if rows and col0_re is None:
        rows = rows[1:]
    return [(ln, r) for ln, r in rows if col0_re is None or re.match(col0_re, re.sub(r'\*\*', '', r[0]).strip())]


def md_cell_ln(ctx, sid, ln, r, col, ev, tag_raw=None, label=None, note=''):
    """Text cell of a markdown row already located by line number (used when walking a whole table)."""
    txt = re.sub(r'\*\*', '', r[col]).strip() if col < len(r) else ''
    lab = label or re.sub(r'\*\*', '', r[0]).strip()
    return ctx.t(sid, f'line {ln} row "{lab[:60]}" col {col}', txt, ev, tag_raw=tag_raw, note=note)


def md_text_lines(ctx, sid, lo, hi, ev, tag_raw=None, note=''):
    """Verbatim text of source lines lo..hi (1-based) of a markdown file."""
    L = (ctx.src(sid).text or '').splitlines()
    txt = ' '.join(x.strip() for x in L[lo - 1:hi]).strip()
    return ctx.t(sid, f'lines {lo}-{hi}', txt, ev, tag_raw=tag_raw, note=note)


def md_line_starting(ctx, sid, starts, ev, tag_raw=None, after_heading=None, maxlen=None):
    """First line (after an optional heading) that starts with a given text."""
    L = (ctx.src(sid).text or '').splitlines()
    on = after_heading is None
    for i, ln in enumerate(L, 1):
        if after_heading is not None and ln.startswith('#') and ln.lstrip('#').strip().startswith(after_heading):
            on = True
            continue
        if on and ln.strip().lstrip('-* ').startswith(starts):
            t = ln.strip().lstrip('-* ').strip().replace('**', '')
            return ctx.t(sid, f'line {i} (starts "{starts[:40]}")', t, ev, tag_raw=tag_raw)
    ctx.issue('WARN', f'{sid}: no line starting {starts!r}')
    return ctx.missing(f'{sid} line starting {starts}')


def inl(c):
    """Inline html of a traced value or cell inside prose."""
    if isinstance(c, TV):
        return tvtxt(c).html if isinstance(c.value, str) else c.h()
    if isinstance(c, Cell):
        return c.html
    return str(c)


def jt(ctx, sid, ptr, ev=None, maxlen=None, tag_ptr=None, note=''):
    """JSON text value as a traced cell (class from its own tag, else ev)."""
    tv = ctx.v(sid, ptr, tag=ev, tag_ptr=tag_ptr, note=note)
    return tvtxt(tv, maxlen)


def jn(ctx, sid, ptr, unit='', fmt=None, ev=None, conv=None, note=''):
    tv = ctx.v(sid, ptr, unit, conv=conv, tag=ev, note=note)
    return num_cell(tv, fmt)


def val_class(txt):
    """Cell colour class for a margin text: negative first number -> neg; < +0.05 -> thin."""
    m = re.match(r'\s*([+\-−]?\d+\.\d+|>\+\d+)', txt or '')
    if not m:
        return ''
    s = m.group(1).replace('−', '-')
    if s.startswith('>'):
        return 'pos'
    v = float(s)
    m2 = re.match(r'\s*[+\-−]?\d+\.\d+\s*/\s*([+\-−]?\d+\.\d+)', txt or '')
    v2 = float(m2.group(1).replace('−', '-')) if m2 else v
    lo = min(v, v2)
    return 'neg' if lo < 0 else ('thin' if lo < 0.05 else 'pos')


MD_VERSION_PATS = {
    'RCMB': [r'^Version (\d+(?:\.\d+)+[a-z]?)'], 'CF4': [r'^Version (\d+(?:\.\d+)+[a-z]?)'], 'T14': [r'\(RG-03\), (v[\d.]+)'],
    'DSIC': [r'^Version (v[\d.]+[a-z]?)'], 'DSIG': [r'\(gnc\.json (v[\d.]+)'], 'REQ': [r'requirements, (rev \d+)'],
    'ICD': [r'\((draft [\d.]+)\)'], 'BENCH': [r'test plan (v\d+)'], 'BENCH5': [r'test plan (v\d+)', r'(v5)'], 'RELE': [r'(v\d+(?:\.\d+)+) handback'],
    'RPL': [r'Text revision (v[\d.]+\w*)', r'Version (v[\d.]+\w*)'], 'F3D': [r'(FINAL handback of the v3\.5\.2 re-check)'],
    'RGNC5': [r'^# (REVIEW-GNC-R5 \(REV-GNC-7\))'], 'RCMB4': [r'^# (REVIEW-COMBUSTION-R4 \(REV-COMB-4\))'],
    'RELE3': [r'^# (REVIEW-ELECTRONICS-R3 \(REV-ELEC-3\))'], 'MMXMD': [r'^# (FEA3D margin matrix v3\.5\.2)'],
    'MOUNTMD': [r'(v3\.5\.2 re-check with RM2-11 folded)'],
}


def md_version2(sid, text):
    head = '\n'.join((text or '').splitlines()[:14])
    for p in MD_VERSION_PATS.get(sid, []):
        m = re.search(p, head, re.M)
        if m:
            return m.group(1)
    return None


def register_sources(ctx, a):
    H, C, V = a.hub, a.cad_dir, a.cad_version
    J = os.path.join
    F3 = J(H, '04-fea/assembly3d_v352')
    R8 = J(H, '04-fea/assembly3d_v352_rows_v8')
    M2 = J(H, '04-fea/v352')
    add = ctx.add
    # interfaces and decision records
    add('CMB', J(H, 'interfaces/combustion.json'), 'Combustion interface v2.4d (design point, grain, injector, igniter, sequences, FA-1 rulings)')
    add('MEC', J(H, 'interfaces/mechanical.json'), 'Mechanical interface (its _v352 sections govern for CAD v3.5.2)')
    add('ELE', J(H, 'interfaces/electronics.json'), 'Electronics interface v4 (ECU, sensors, firmware v2.11, abort causes)')
    add('GNC', J(H, 'interfaces/gnc.json'), 'Space/GNC interface v3.2 (reference vehicle, mission, ENG-11)')
    add('CL', J(H, 'interfaces/CHANGELOG.md'), 'Decision log (line-numbered)', 'md')
    add('REQ', J(H, '00-requirements/REQUIREMENTS.md'), 'Engine requirements', 'md')
    add('ICD', J(H, '00-requirements/ICD-AIRFRAME.md'), 'ICD-AIRFRAME draft 0.2 (2026-10-13; out of the finish scope since 2026-10-19, CHANGELOG 222; not updated): used only where no current source covers a value', 'md')
    add('SUP', J(H, 'reviews/SUPERVISION.json'), 'Independent review register')
    if a.overrides:
        add('OVR', a.overrides, 'Decision override table (datasheet generator input)')
    add('REV0S', J(DS_ROOT, 'out/sources.json'), 'Datasheet rev0-draft sources record (kept; CAD v3.4.1)', required=False)
    # combustion and plume
    add('RCMB', J(H, '02-combustion/REPORT.md'), 'Combustion report', 'md')
    add('DSIC', J(H, '02-combustion/DATASHEET-INPUTS-COMBUSTION.md'), 'Combustion datasheet inputs', 'md')
    add('CF4', J(H, '02-combustion/CF-4-SPEC.md'), 'CF-4 relight-purge cold-flow specification', 'md')
    add('T14', J(H, '02-combustion/T1-T4-REGRESSION-SPEC.md'), 'T1-T4 regression measurement specification', 'md')
    add('FA1SP', J(H, '02-combustion/data/v2p4b/fa1_pressure_spectra_published_v2p4b.csv'),
        'FA-1 equivalent-static-pressure spectra, 406 periods (Combustion v2.4b data, SIM histories, DERIVED spectra)', 'csv')
    add('RCMB4', J(H, 'reviews/REVIEW-COMBUSTION-R4.md'), 'Independent review REV-COMB-4 (text)', 'md')
    add('RPL', J(H, '05-plume-cfd/REPORT.md'), 'Plume CFD report', 'md')
    add('PVAL', J(H, '05-plume-cfd/validation/results/validation_v2.json'), 'Plume CFD validation results')
    for fid, rel, _ in PLUME_FIGS:
        add(fid, find_hub_file(H, rel), 'Plume figure', 'img', required=False)
    # GNC
    add('DSIG', J(H, '01-systems-gnc/DATASHEET-INPUTS-GNC.md'), 'GNC datasheet inputs (gnc.json v3.2)', 'md')
    add('RGNC5', J(H, 'reviews/REVIEW-GNC-R5.md'), 'Independent review REV-GNC-7 (text)', 'md')
    # electronics
    add('RELE', J(H, '06-electronics/REPORT-v2.11-HANDBACK.md'), 'Electronics v2.11 handback report', 'md')
    add('BENCH', J(H, '06-electronics/staging_v2.11/docs/bench_plan_v4.md'), 'Electronics bench and test plan v4, the plan of electronics.json v4: REVISE (text), not for the founders before v5 (CHANGELOG 253 (5)); v5 comes with electronics v4.1 (PENDING REVIEW)', 'md')
    add('RELE3', J(H, 'reviews/REVIEW-ELECTRONICS-R3.md'), 'Independent review REV-ELEC-3 (text)', 'md')
    add('ELE41', J(H, '06-electronics/staging_v2.12/results/electronics_v4.1.json'), 'Electronics interface candidate v4.1 (Electronics v2.12, staged): '
        'PENDING REVIEW until the REV-ELEC-4 verdict (CHANGELOG 264 (1)); no value of it is used in this draft', required=False)
    add('BENCH5', J(H, '06-electronics/staging_v2.12/docs/bench_plan_v5.md'), 'Electronics bench and test plan v5 (staged with v4.1): '
        'PENDING REVIEW with v4.1; not used for values in this draft', 'md', required=False)
    # 3D FEA v3.5.2 (FEA3D-2) and the rows-v8 margin matrix
    add('F3D', J(F3, 'REPORT-FEA3D-v352.md'), 'FEA3D v3.5.2 report (FEA3D-2, final)', 'md')
    add('F3DMAN', J(F3, 'MANIFEST.json'), 'FEA3D v3.5.2 manifest')
    add('MOUNT', J(F3, 'results/v352/engine_mount_data_v352.json'), 'Engine mounting data v3.5.2 (hole loads)')
    add('MOUNTMD', J(F3, 'results/v352/tables/engine_mount_data_v352.md'), 'Engine mounting data v3.5.2, datasheet tables', 'md')
    add('KTAB', J(F3, 'results/v352/k_table_r3_v352.json'), 'Axis stiffness K table at R3 (v3.5.2)')
    add('ROCK', J(F3, 'results/v352/rocking_servo_J_v352.json'), 'Rocking modes vs servo J (v3.5.2)')
    add('MODAL', J(F3, 'results/v352/modal_ca2c_vs_ca2b_v352.json'), 'Modal ca2c vs ca2b (v3.5.2)')
    add('F4J', J(F3, 'results/v352/f4_v352.json'), 'F4 joints J-FD01 / J-FD09 (v3.5.2)')
    add('CDJ', J(F3, 'results/v352/jfwd_cD_result_v352.json'), 'Mesh-convergence check cD (J-FWD seat)')
    add('ENV6', J(F3, 'results/v352/jfwd_soak_envelope_v352_v6.json'), 'J-FWD soak envelope v6 (final)')
    add('ICDMF', J(F3, 'results/v352/icd_momentfree_v352.json'), 'Moment-free hole-load estimate (v3.5.2)')
    add('MMX', J(R8, 'tables/margin_matrix_v352.json'), 'Margin matrix v3.5.2 on J-FWD rows v8 (every part x every case)')
    add('MMXMD', J(R8, 'tables/margin_matrix_v352.md'), 'Margin matrix v3.5.2 on rows v8 (published table)', 'md')
    add('MMXD', J(R8, 'delta_vs_assembly3d_v352.json'), 'Margin matrix delta, rows v8 vs the FEA3D-2 matrix')
    # Mechanical J-FWD rows, texts and follow-ups (04-fea/v352)
    add('ROWS8', J(M2, 'jfwd_in718_rows_v352_v8.json'), 'J-FWD IN718 rows v8 (Mechanical)')
    add('BAND', J(M2, 'jfwd_pq_band_v352_v1.json'), 'Seat-line P+Q select-fit band v1 (Mechanical, R2-B)')
    add('TAPW', J(M2, 'jfwd_tapwall_v352_v3.json'), 'TC-02 torch-tap wall at FA1S, v3 (Mechanical, R4-01)')
    add('TB70', J(M2, 'lc_tb70_envelope_v2.json'), 'LC-TB70 envelope v2: Z3 v2 and the J-FWD replace rule (Mechanical)')
    add('TXT5', J(M2, 'texts/item_c_tf1_texts_v352_v5.json'), 'Item C / T-F1 texts v5 (drawing, founder and datasheet texts)')
    add('LCF', J(M2, 'jfwd_screw_lcf_v352_v3.json'), 'J-FWD screw LCF v3 (Mechanical)')
    add('FIL', J(M2, 'jfwd_head_fillet_v352_v2.json'), 'J-FWD screw head fillet v2 (Mechanical)')
    add('SPR', J(M2, 'jfwd_spring_v352_v5.json'), 'HW-170 disc spring v5 (Mechanical)')
    add('C1S', J(M2, 'c1seat/c1_seat_v352_v1.json'), 'C1 seat (Mechanical F1)', required=False)
    add('TPB', J(M2, 'c1seat/torch_port_bl08_v352_v1.json'), 'Torch-port rise F2 (Mechanical; not a bound)', required=False)
    add('MMAN', J(M2, 'MANIFEST_v352.sha256'), 'Mechanical 04-fea/v352 manifest', 'text')
    # CAD v3.5.2 FINAL
    add('BOM', J(C, f'BOM_{V}.json'), f'Bill of materials (CAD {V})')
    add('MP', J(C, f'massprops_{V}.json'), f'Mass properties (CAD {V})')
    add('MDEL', J(C, f'massdelta_{V}_vs_v3.5.1.json'), f'Mass delta {V} vs v3.5.1')
    add('SET', J(C, f'set_{V}.json'), f'CAD set record ({V})')
    add('MAN', J(C, f'assembly/assembly_manifest_{V}.json'), f'Assembly manifest, instance bounds (CAD {V})')
    add('GLB', J(C, f'assembly/ENGINE_{V}_neutral.glb'), f'Assembly GLB, visualisation geometry (CAD {V})', 'bin')
    add('HWD', J(C, 'data/hardware_v352.json'), 'Hardware data v3.5.2 (fasteners, springs)')
    add('CHK', J(C, 'checks/test_final352_v1.json'), 'Final-set check (round trips, changed parts, BOM delta)')
    add('CLR', J(C, 'checks/clear_interim352_v2.json'), 'Interference and clearance check at 18 poses (geometry unchanged in the final)')
    add('GLBR', J(C, f'checks/glb_readback_{V}.json'), 'GLB read-back check')
    add('DRW', J(C, 'texts/jfwd_drawing_texts_v352_v2.json'), 'J-FWD drawing texts v2 (TC-01 / TC-02 / HW-101 notes)')
    add('CADMAN', J(C, f'MANIFEST_{V}.sha256'), f'CAD {V} manifest', 'text')
    add('RMAN', J(a.renders, 'render_manifest.json'), 'Render manifest (this generator)')
    add('RSCR', J(HERE, 'render_views_blender.py'), 'Render script (Blender, this generator)', 'text')
    for sid, s in ctx.sources.items():
        if s.version is None and s.text is not None:
            s.version = md_version2(sid, s.text)
        if sid == 'CL' and s.text is not None:
            s.version = f'{len(s.text.splitlines())} lines'
        if sid == 'SUP' and isinstance(s.data, dict):
            s.version = f'{len(s.data.get("reviews") or [])} reviews'
        if sid == 'GLB':
            s.version = V
        if sid == 'PVAL' and s.version is None:
            m = re.search(r'_(v\d+)\.json$', s.path)
            s.version = m.group(1) if m else None
        if sid in ('MAN', 'SET', 'BOM', 'MP', 'MDEL') and s.data is not None:
            s.version = (s.data.get('cad_version') or V) + (f' {s.data.get("version")}' if s.data.get('version') and sid == 'SET' else '')
        if sid in ('CADMAN', 'MMAN') and s.text is not None:
            s.version = f'{len([x for x in s.text.splitlines() if x.strip()])} rows'
        if sid in ('ROWS8', 'BAND', 'TAPW', 'TB70', 'TXT5', 'LCF', 'FIL', 'SPR', 'DRW', 'ENV6', 'MMX', 'MMXD', 'CHK', 'CLR') and s.version is None:
            m = re.search(r'_(v\d+)\.json$', s.path)
            s.version = m.group(1) if m else (s.data.get('date') if isinstance(s.data, dict) else None)
        if sid == 'FA1SP' and s.text is not None:
            s.version = f'{len(s.text.splitlines()) - 1} periods'
        if s.kind == 'img' and s.version is None:
            s.version = 'figure'


def print_pdf(a, html_path, pdf_path, D):
    st = 'font-family:\'Inter DS\',Inter,sans-serif;font-size:6.4px;color:#55626f;width:100%;padding:0 14mm;display:flex;justify-content:space-between;'
    hdr = (f'<div style="{st}"><span><b style="color:#0b3a5c">{esc(DOC_ID)}</b> · {esc(a.rev)} · <b style="color:#b4232a">DRAFT</b> · CAD {esc(a.cad_version)}</span>'
           f'<span><b style="color:#b4232a">{esc(PAGE_STATEMENT)}</b></span></div>')
    ftr = (f'<div style="{st}"><span>Generated {esc(D["generated"])} · {GEN_NAME} {GEN_VERSION} · digital design data only · {esc(PAGE_STATEMENT)}</span>'
           f'<span>Page <span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
    cfg = {'header': hdr, 'footer': ftr, 'margin': {'top': '17mm', 'bottom': '15mm', 'left': '14mm', 'right': '14mm'}}
    cfgp = os.path.join(a.build, 'print_config_rev1.json')
    json.dump(cfg, open(cfgp, 'w'))
    env = dict(os.environ)
    env.setdefault('PLAYWRIGHT_BROWSERS_PATH', a.pw_browsers)
    if getattr(a, 'fontconf', None):
        env['FONTCONFIG_FILE'] = a.fontconf
    cmd = [a.node, os.path.join(HERE, 'print_pdf.mjs'), html_path, pdf_path, cfgp]
    if a.nice:
        cmd = ['nice', '-n', str(a.nice)] + cmd
    r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        raise RuntimeError('PDF printing failed: ' + r.stderr[-2000:])
    return r.stdout.strip()


CSS_REV1 = r'''
.ev-calc { background:#e6ebf8; color:#2b4a8c; } .ev-estimate { background:#fbeee0; color:#8a4b00; }
.stmt { font-size: 7.4pt; font-weight: 700; color: #b4232a; }
table.mx td { font-size: 6.3pt; padding: 1pt 1.6pt; white-space: nowrap; }
table.mx th { font-size: 6.3pt; padding: 1pt 1.6pt; }
table.mx td.neg, td.neg { background: #fbe3e3; color: #8c1d24; font-weight: 650; }
table.mx td.thin, td.thin { background: #fff3dc; }
table.mx td.pos { }
table.tight td { font-size: 6.8pt; padding: 1.1pt 2.2pt; }
table.tight th { font-size: 6.8pt; }
table.mount td { font-size: 6.1pt; padding: 0.9pt 1.4pt; white-space: nowrap; }
table.mount th { font-size: 6.1pt; padding: 0.9pt 1.4pt; }
.fn { font-size: 6.2pt; color: var(--ink2); margin: -2mm 0 3mm; }
.fn p { margin: 0 0 0.6mm; }
.neg-tag { display: inline-block; font-size: 5.6pt; font-weight: 750; color: #fff; background: #b4232a; padding: 0.1pt 2.2pt; border-radius: 2pt; }
.open-tag { display: inline-block; font-size: 5.6pt; font-weight: 750; color: #9a4a00; background: #ffe3c7; padding: 0.1pt 2.2pt; border-radius: 2pt; }
.closed-tag { display: inline-block; font-size: 5.6pt; font-weight: 750; color: #155e57; background: #ddf1ee; padding: 0.1pt 2.2pt; border-radius: 2pt; }
.box-neg { border-color: #b4232a; background: #fdf0f0; }
.cols2 { columns: 2; column-gap: 6mm; }
.kpi { display: grid; grid-template-columns: repeat(4, 1fr); gap: 2mm; margin: 2mm 0 3mm; }
.kpi .tile .tv { font-size: 9.6pt; }
.ev-decided { background:#ffffff; color:#24384d; border:0.5pt solid #24384d; }
.evb { font-size: 5.4pt; color: #24384d; margin-left: 1.2pt; font-style: italic; }
.ev-status { background:#ffe3c7; color:#9a4a00; margin-left: 1pt; }
.ev-as-recalled { background:#f3e8dc; color:#6b4a2a; }
.ev-tagbox { display:inline-block; margin: 0 1.5mm 1mm 0; }
'''


def md_heading(ctx, sid, starts, ev, tag_raw=None):
    """Text of the first heading line that starts with a given text."""
    for i, ln in enumerate((ctx.src(sid).text or '').splitlines(), 1):
        if ln.startswith('#') and ln.lstrip('#').strip().startswith(starts):
            return ctx.t(sid, f'heading line {i}', ln.lstrip('#').strip(), ev, tag_raw=tag_raw)
    ctx.issue('WARN', f'{sid}: no heading starting {starts!r}')
    return ctx.missing(f'{sid} heading {starts}')


def md_sentence(ctx, sid, heading_prefix, contains, ev, tag_raw=None, note=''):
    """The sentence of a markdown section (heading text starting with heading_prefix) that contains a phrase,
    with its line number (a sentence ends at '. ', ': ' or '; ' followed by a capital or at the end of the line)."""
    lines = (ctx.src(sid).text or '').splitlines()
    on = False
    for i, ln in enumerate(lines, 1):
        if ln.startswith('#'):
            on = ln.lstrip('#').strip().startswith(heading_prefix)
            continue
        if on and contains in ln:
            k = ln.index(contains)
            starts = [0] + [m.end() for m in re.finditer(r'(?<=[.;:])\s+(?=[A-Z(*`])', ln[:k])]
            j0 = starts[-1]
            m = re.compile(r'(?<=[A-Za-z0-9)\]`*"\'])[.;](?=\s+[A-Z(*`]|\s*$)').search(ln, k + len(contains))
            j1 = m.end() if m else len(ln)
            txt = re.sub(r'\*\*', '', ln[j0:j1]).strip()
            return ctx.t(sid, f'§{heading_prefix} line {i} [sentence containing "{contains}"]', txt, ev, tag_raw=tag_raw, note=note)
    ctx.issue('WARN', f'{sid}: no sentence containing {contains!r} under {heading_prefix!r}')
    return ctx.missing(f'{sid} §{heading_prefix} sentence containing {contains}')


PRIVATE_PATH = re.compile(r'/home/claude|/tmp/|scratchpad|/dev/shm|/root/|/opt/|/mnt/|/usr/')


def path_scan(ctx, label, text):
    """ERROR for every private or absolute path visible in an output text (lead 12:13Z items 2 and 9: printed paths are
    hub-relative only)."""
    t = re.sub(r'<style.*?</style>', ' ', text, flags=re.S)
    t = re.sub(r'<[^>]+>', ' ', t)
    n = 0
    for m in PRIVATE_PATH.finditer(t):
        n += 1
        if n <= 12:
            ctx.issue('ERROR', f'private or absolute path visible in {label}: …{t[max(0, m.start() - 60):m.end() + 40]!r}…')
    return n


def hub_rel(a, path):
    """Hub-relative form of a path (argos-engine hub); None when the path is outside the hub."""
    p = os.path.abspath(path)
    h = os.path.abspath(a.hub)
    if p == h or p.startswith(h + os.sep):
        return os.path.relpath(p, h)
    return None


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
        self.row_tv = TV(ctx, f"{self.pn}: {line.get('name', '')[:60]}", '', 'DESIGN', 'BOM hardware row (standard part, not modelled)', 'BOM', ptr,
                         note='row trace: name, qty, host, size, grade, torque, tightening method, unit_mass_kg, mass_source, unit_price')
        if self.unit is not None:
            self.mass_tv = TV(ctx, self.unit, 'kg', self.mclass or 'CALC', line.get('mass_source'), 'BOM', ptr + '/unit_mass_kg')
        else:
            st = 'MISSING' if self.mclass in (None, 'MISSING') else self.mclass
            self.mass_tv = TV(ctx, None, 'kg', st, line.get('mass_source'), 'BOM', ptr + '/unit_mass_kg', status=st if st != 'ASSUMED' else 'negligible')
        self.line_mass = (self.unit * self.qty) if (self.unit is not None and self.qty is not None) else None
        if self.pstate == 'INVALID':
            ctx.issue('ERROR', f'BOM hardware {self.pn}: price field violates the price rule: {line.get("unit_price")!r}')


def prepare(ctx, a):
    D = {'generated': now_utc()}
    D['cl'] = cl = Changelog(ctx, 'CL')
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
    pend.append(('Electronics v2.12: firmware v2.12 and the electronics.json v4.1 candidate are PENDING REVIEW (REV-ELEC-4); interfaces/electronics.json v4 '
                 'stays the source of record', cl.clip(264, 1, 'interfaces/electronics.json stays v4', 'as PENDING REVIEW.')))
    pend.append(('REV-ELEC-4 verdict (PENDING; never assumed)', cl.clip(264, 8, 'v4.1 is promoted only after its verdict', 'its verdict.')))
    pend.append(('T4 re-run: the length of the shorter T4 relight (OPEN, 261 (2) and 264 (5))', cl.clip(264, 5, 'Combustion sets the length', "soak-back.")))
    D['pending'] = pend
    mx_negatives(ctx, D)
    D['pending_inputs'] = [p[0] for p in pend]
    D['pending_n'] = ctx.d(len(pend), '', 'count of inputs pending at this build (§1.4)', [p[1] for p in pend], ev='PENDING')
    return D


# ---------------------------------------------------------------------------------------------
# sections 1-3 (v0.3.0): identification, key performance, throttle and TVC
# ---------------------------------------------------------------------------------------------
EV_DOC = [('SIM', 'model run (CFD, FE, Monte Carlo, quasi-1D, CEA, SIL)'), ('CALC', 'hand calculation on model loads or standard geometry'),
          ('DERIVED', 'computed from other traced values (by a specialist, a reviewer or this generator)'),
          ('ASSUMED', 'an input adopted without a measurement or a source'), ('DATASHEET', 'maker data'), ('LITERATURE', 'published data, cited'),
          ('AS RECALLED', 'a value quoted from memory by its author; to be sourced'), ('TO-VERIFY', 'needed from, or to be confirmed by, the named owner'),
          ('MISSING', 'not available; never estimated by the generator'), ('ESTIMATE', 'an estimate named as such by its source'),
          ('DECIDED', 'a design value, decided limit or requirement: chosen, not measured or computed; where the source gives a basis, that basis '
                      'and its tag are shown beside it (source class: design value, lead decision line N, or requirement)'),
          ('REF', 'a reference or provenance text (a source, a review id, a "no number changed" statement): it carries no value and no pill')]
EV_STATUS_DOC = [('PENDING', 'an input that has not landed (never assumed)'), ('SUPERSEDED', 'withdrawn by a newer decision, shown only as history'),
                 ('TO-DEFINE', 'not yet defined by its owner (the value is MISSING)')]


def src_tv(ctx, sid):
    s = ctx.src(sid)
    return TV(ctx, f'{s.version or "–"} · sha256/16 {s.sha16 or "MISSING"}', '', 'DERIVED', f'generator: version and sha256/16 of source {sid} at this build',
              sid, '(file)', note=os.path.basename(s.path))


def plot_pressure_ladder(a, items):
    """items: [(label, bar value or (lo, hi), colour, note)] horizontal ladder on a log scale."""
    plt = mpl_setup()
    n = len(items)
    fig, ax = plt.subplots(figsize=(6.9, 0.2 * n + 0.75))
    for i, (lab, v, c, note) in enumerate(items):
        y = n - 1 - i
        if v is None:
            ax.text(1.05, y, f'{lab}: MISSING', va='center', fontsize=6, color=C_BAD)
            continue
        if isinstance(v, (tuple, list)):
            ax.barh(y, v[1] - v[0], left=v[0], height=0.6, color=c, alpha=0.85)
            ax.text(v[1] * 1.03, y, f'{v[0]:g}–{v[1]:g} bar  {note}', va='center', fontsize=5.8)
        else:
            ax.barh(y, v, height=0.6, color=c, alpha=0.85)
            ax.text(v * 1.03, y, f'{v:g} bar  {note}', va='center', fontsize=5.8)
    ax.set_yticks(range(n))
    ax.set_yticklabels([it[0] for it in items][::-1], fontsize=6.2)
    ax.set_xscale('log')
    ax.set_xlim(1, 1200)
    ax.set_xlabel('pressure [bar abs] (log scale)')
    ax.grid(axis='y', visible=False)
    fig.tight_layout()
    return save_plot(fig, a, 'plot_pressure_ladder')


def plot_fa1_spectrum(a, T, series, fa1s, bands):
    plt = mpl_setup()
    fig, ax = plt.subplots(figsize=(6.9, 2.9))
    for lab, ys, c, ls in series:
        ax.plot(T, ys, color=c, lw=1.0, ls=ls, label=lab)
    if fa1s is not None:
        ax.axhline(fa1s, color=C_BAD, lw=0.9, ls='--', label=f'FA1S {fa1s:g} bar abs (design case)')
    for (t0, t1, v) in bands:
        if v is not None:
            ax.plot([t0, t1], [v, v], color=C_OK, lw=1.6, solid_capstyle='butt')
    ax.plot([], [], color=C_OK, lw=1.6, label='decided band values (LEAD 230 (2))')
    ax.set_xscale('log')
    ax.set_xlabel('SDOF period T [ms]')
    ax.set_ylabel('equivalent static pressure [bar abs]')
    ax.set_xlim(0.02, 50)
    ax.legend(fontsize=6, loc='lower center', ncol=2)
    fig.tight_layout()
    return save_plot(fig, a, 'plot_fa1_spectrum')


def plot_throttle(a, pts):
    """pts: list of dicts fraction, F, Pc_bar, Isp, OF."""
    plt = mpl_setup()
    fig, axs = plt.subplots(1, 3, figsize=(6.9, 2.2))
    fr = [p['fraction'] * 100 for p in pts]
    axs[0].plot(fr, [p['F'] for p in pts], 'o-', color=C_ACC, ms=3, lw=1)
    axs[0].set_xlabel('throttle [%]')
    axs[0].set_ylabel('thrust [N] (SL)')
    axs[1].plot([p['F'] for p in pts], [p['Pc_bar'] for p in pts], 'o-', color=C_ACC2, ms=3, lw=1)
    axs[1].set_xlabel('thrust [N]')
    axs[1].set_ylabel('Pc [bar abs]')
    axs[2].plot([p['F'] for p in pts], [p['Isp'] for p in pts], 'o-', color=C_WARN, ms=3, lw=1)
    axs[2].set_xlabel('thrust [N]')
    axs[2].set_ylabel('Isp SL [s]')
    for ax in axs:
        ax.tick_params(labelsize=6)
    fig.tight_layout()
    return save_plot(fig, a, 'plot_throttle')


def sec_identification(ctx, doc, a, D):
    o = [doc.h(1, '1 Identification')]
    cl = D['cl']
    o.append(note_box(f'<b class="stmt">{esc(PAGE_STATEMENT)}.</b> This datasheet is generated from the engine programme hub by '
                      f'gen/{GEN_NAME} {GEN_VERSION}. Every value in a data column is a traced value (T###, Appendix A) with its evidence class. '
                      'No value is MEASURED: the engine has not been built or fired. Missing data are shown as MISSING, TO-DEFINE or PENDING and never '
                      'estimated here.', 'warn'))
    o.append(doc.h(2, '1.1 Document and configuration'))
    cfg = [('CAD set (FINAL v3.5.2)', 'SET'), ('CAD manifest', 'CADMAN'), ('Assembly GLB (renders)', 'GLB'), ('Bill of materials', 'BOM'),
           ('Mass properties', 'MP'), ('Combustion interface', 'CMB'), ('Combustion datasheet inputs', 'DSIC'), ('Mechanical interface', 'MEC'),
           ('Mechanical 04-fea/v352 manifest', 'MMAN'), ('GNC interface', 'GNC'), ('GNC datasheet inputs', 'DSIG'), ('Electronics interface', 'ELE'),
           ('FEA3D v3.5.2 report', 'F3D'), ('Margin matrix of record (rows v8)', 'MMX'), ('Decision log', 'CL'), ('Review register', 'SUP'),
           ('Requirements', 'REQ'), ('Airframe ICD', 'ICD')]
    rows = [[lab, Cell(f'<span class="mono small">{esc(src_tv(ctx, sid).value)}</span>{src_tv(ctx, sid).ref()}', [src_tv(ctx, sid)])] for lab, sid in cfg]
    rows.insert(1, ['CAD set status', tvtxt(ctx.v('SET', '/status', tag='DESIGN'), 520)])
    o.append(dtable(['Item', 'Version · sha256/16 (this build)'], rows, widths=['32%', '68%'],
                    caption=f'{esc(DOC_ID)} {esc(a.rev)}, CAD {esc(a.cad_version)}. Full source list with paths in §15.2.'))
    o.append(doc.h(2, '1.2 What changed since rev0'))
    r0 = 'REV0S'
    rows = []
    for lab, sid in (('CAD', None), ('Combustion interface', 'CMB'), ('Mechanical interface', 'MEC'), ('GNC interface', 'GNC'),
                     ('Electronics interface', 'ELE'), ('Decision log', 'CL')):
        if sid is None:
            old = ctx.v(r0, '/cad_version', tag='DERIVED', note='rev0 sources.json')
            new = TV(ctx, a.cad_version, '', 'DESIGN', 'CAD version of this build (render manifest and CAD folder)', 'RMAN', '/cad_version')
        else:
            old = ctx.v(r0, f'/sources/{sid}/version', tag='DERIVED', note='rev0 sources.json')
            new = TV(ctx, ctx.src(sid).version, '', 'DERIVED', f'version of source {sid} at this build', sid, '(file version)')
        rows.append([lab, num_cell(old), num_cell(new)])
    rows.append(['Parts changed vs v3.5.1', Cell('–', []), tvtxt(ctx.v('SET', '/changed_parts_vs_v3.5.1', tag='DESIGN'))])
    rows.append(['Mass change and the GNC trigger', Cell('–', []), tvtxt(ctx.v('MEC', '/gimballed_mass_properties_v352/delta_vs_v3.5.1/gnc_trigger/verdict', tag='DERIVED'), 500)])
    e11 = cl.item(258, 1)
    w0 = rx_text(ctx, e11, r'rev0 datasheet row 8 window (\d+)-(\d+) is withdrawn', 'N m/rad', tag='DERIVED', group=2,
                 note='upper end of the rev0 window (DERIVED on CAD v3.5.1, withdrawn by line 258 (1))')
    rows.append(['ENG-11 servo stiffness: upper end of the design-to window',
                 Cell(f'{w0.h(".0f")} <span class="ev ev-status">SUPERSEDED</span>', [w0]), eng11_cell(ctx, D)])
    rows.append(['Case-TC limits', Cell('–', []), tvtxt(cl.part(257, '423.15'), 500)])
    rows.append(['3D FEA of the assembled engine', Cell('–', []), tvtxt(md_find(ctx, 'F3D', 'REPORT FEA3D v3.5.2', {0: 'Status'}, 1, ev='DERIVED',
                                                                                 tag_raw='FEA3D-2 report header'), 300)])
    o.append(dtable(['Item', 'rev0 (2026-10-13)', 'rev1 (this build)'], rows, widths=['24%', '24%', '52%'], cls='tight',
                    caption='Rev0 values from the rev0 sources.json (07-datasheet/out/sources.json, kept); rev1 values from this build.'))
    o.append(doc.h(2, '1.3 Evidence classes'))
    o.append(table(['Class', 'Meaning'], [[(ev_pill(k) if k != 'REF' else '<b>REF</b>'), esc(v)] for k, v in EV_DOC]
                   + [[f'<span class="ev ev-status">{esc(k)}</span>', esc(v)] for k, v in EV_STATUS_DOC], cls='dt tight', widths=['16%', '84%']))
    o.append('<p class="small">Every number carries one of the ten evidence tags (SIM, CALC, DERIVED, ASSUMED, DATASHEET, LITERATURE, AS RECALLED, '
             'TO-VERIFY, MISSING, ESTIMATE) or the source-class pill DECIDED. The tag comes from the source tag or the quoted text; where neither '
             'gives one, the trace names the class set at the call site. This generator sets no default class: a value without a class is counted '
             'as UNTAGGED in qa_report. A lead line that quotes a SIM, DERIVED or CALC number keeps that number\'s tag; DECIDED applies only to the '
             'chosen value itself. PENDING, SUPERSEDED and TO-DEFINE are statuses shown beside the tag. A review verdict, a matching number or a '
             'passing check is not physical approval.</p>')
    o.append(doc.h(2, '1.4 At a glance: found negatives, open rulings and pending inputs'))
    nb = D.get('neg_by_class', {})
    o.append(note_box(f'<b>Found negatives.</b> {D["neg_total"].h()} margin-matrix cells are negative ('
                      + ', '.join(f'{esc(k)} {v.h(pill=False)}' for k, v in sorted(nb.items())) + '); every one is listed with its class and closure in §9.3. '
                      'Named: TC-04 (BT), the TC-01 J-FWD seat-line P+Q (DC; the R2-B select fit closes it only in the CALC band model), the J-FWD screw LCF '
                      '(C6 OPEN: single-use screws), the screw head fillet from zero (§9.4). The mesh convergence of the seat-line P+Q is not shown (§9.1.1).', 'neg'))
    rows = []
    for lab, tv in D['pending']:
        rows.append([esc(lab), tvtxt(tv, 600)])
    o.append(dtable(['Pending input', 'Status (quoted)'], rows, widths=['34%', '66%'], cls='tight',
                    caption='Inputs still pending at this build; their values are shown as PENDING (REVIEW) where used.'))
    o.append(doc.h(2, '1.5 Recent lead decisions'))
    decs = cl.decisions('lead', last=a.decisions)
    rows = [[f'L{d["n"]}', esc(d.get('date') or ''), tvtxt(cl.whole(d['n'], maxlen=900))] for d in decs]
    o.append(dtable(['Line', 'Date', 'Decision text (first 900 characters; full line in the CHANGELOG)'], rows, label_cols=2,
                    widths=['6%', '10%', '84%'], cls='tight', caption=f'The last {len(decs)} lead decision lines of the CHANGELOG ({esc(src_label(ctx, "CL"))}).'))
    return '\n'.join(o)


def sec_performance(ctx, doc, a, D):
    o = [doc.h(1, '2 Key performance')]
    o.append(doc.h(2, '2.1 Combustion datasheet inputs'))
    allr = md_rows_all(ctx.src('DSIC').text or '', None)
    rows = []
    for ln, r in allr[1:]:
        if len(r) < 5:
            continue
        item = re.sub(r'\*\*', '', r[0]).strip()
        tag = r[3].strip()
        ev = normalise_tag(tag.split(';')[0].split('(')[0])
        rows.append([Cell(f'<b>{esc(item)}</b>', []), tvtxt(md_cell_ln(ctx, 'DSIC', ln, r, 1, ev, tag_raw=tag)),
                     tvtxt(md_cell_ln(ctx, 'DSIC', ln, r, 2, ev, tag_raw=tag), 700), tvtxt(md_cell_ln(ctx, 'DSIC', ln, r, 4, 'REF', tag_raw='source column'), 300)])
    o.append(dtable(['Item', 'Value', 'Condition / basis', 'Source'], rows, cls='tight', widths=['13%', '37%', '34%', '16%'],
                    caption=f'Every row of 02-combustion/DATASHEET-INPUTS-COMBUSTION.md ({esc(src_label(ctx, "DSIC"))}), quoted; the pill is the row\'s tag.'))
    notes = [ln for ln in (ctx.src('DSIC').text or '').splitlines() if ln.startswith('- ')]
    L = (ctx.src('DSIC').text or '').splitlines()
    nrows = [[tvtxt(ctx.t('DSIC', f'notes line {L.index(n) + 1}', n[2:].strip(), 'DESIGN', tag_raw='datasheet inputs note'), 900)] for n in notes]
    o.append(dtable(['Notes of the combustion datasheet inputs (quoted)'], nrows, label_cols=0, widths=['100%'], cls='tight'))
    o.append(doc.h(2, '2.2 Throttle points (20 C tank, initial port)'))
    pts = ctx.raw('CMB', '/operating_points/throttle_points_20C_initial_port', default=[]) or []
    rows, plot_pts, refs = [], [], []
    for i, p in enumerate(pts):
        b = f'/operating_points/throttle_points_20C_initial_port/{i}'

        def g(k, unit='', conv=None):
            return ctx.v('CMB', f'{b}/{k}', unit, conv=conv, tag='SIM', tag_ptr='/operating_points/basis')
        F, Pc, OF, Isp = g('F_N', 'N'), g('Pc_Pa', 'bar', (1e-5, 0, 'Pa to bar')), g('OF'), g('Isp_SL_s', 's')
        mo, mf, lift, dpp = g('mdot_ox_kg_s', 'g/s', (1000, 0, 'kg/s to g/s')), g('mdot_fuel_kg_s', 'g/s', (1000, 0, 'kg/s to g/s')), \
            g('pintle_lift_m', 'mm', (1000, 0, 'm to mm')), g('dP_inj_over_Pc')
        fr = g('fraction')
        rows.append([num_cell(fr, '.3f'), num_cell(F, '.1f'), num_cell(Pc, '.2f'), num_cell(OF, '.2f'), num_cell(Isp, '.1f'),
                     num_cell(mo, '.1f'), num_cell(mf, '.2f'), num_cell(lift, '.3f'), num_cell(dpp, '.2f')])
        refs += [F.tid, Pc.tid, Isp.tid]
        if None not in (F.value, Pc.value, Isp.value, fr.value):
            plot_pts.append({'fraction': fr.value, 'F': F.value, 'Pc_bar': Pc.value, 'Isp': Isp.value})
    o.append(dtable(['Fraction', 'Thrust', 'Pc', 'O/F', 'Isp SL', 'N2O flow', 'ABS flow', 'Pintle lift', 'dP_inj / Pc'], rows, label_cols=0, cls='tight',
                    caption=f'combustion.json /operating_points/throttle_points_20C_initial_port; basis: {esc(str(ctx.raw("CMB", "/operating_points/basis", default="")))[:300]}'))
    if plot_pts:
        o.append(fig_html(plot_throttle(a, plot_pts), 'Throttle points: thrust vs throttle fraction, chamber pressure and sea-level Isp vs thrust (SIM).', refs, 'wide'))
    o.append(doc.h(2, '2.3 Pressure ladder'))
    lim = '/operating_points/pressure_limits'
    cap = ctx.v('CMB', lim + '/normal_cap_Pa/v', 'bar', conv=(1e-5, 0, 'Pa to bar'), tag_ptr=lim + '/normal_cap_Pa')
    ab = ctx.v('CMB', lim + '/abort_Pa/v', 'bar', conv=(1e-5, 0, 'Pa to bar'), tag_ptr=lim + '/abort_Pa')
    meop = ctx.v('CMB', lim + '/chamber_MEOP_Pa/v', 'bar', conv=(1e-5, 0, 'Pa to bar'), tag_ptr=lim + '/chamber_MEOP_Pa')
    proof = ctx.v('CMB', lim + '/proof_Pa/v', 'bar', conv=(1e-5, 0, 'Pa to bar'), tag_ptr=lim + '/proof_Pa')
    mb = ctx.v('CMB', '/meop_basis_v2p4/v/basis_bar', 'bar', tag_ptr='/meop_basis_v2p4')
    bm = '/fa1_spectra_damped_v2p4b/v/head_all_band_maxima_bar_abs'
    bands = [(ctx.v('CMB', f'{bm}/{k}/zeta0', 'bar', tag='SIM', tag_ptr='/fa1_spectra_damped_v2p4b', note='undamped (zeta 0) band maximum, head, all cases'))
             for k in ('T_le_0p1ms', 'T_0p1_to_1ms', 'T_1_to_20ms', 'T_20_to_50ms')]
    fa1s = rx_text(ctx, ctx.v('CMB', '/fa1_p_torch_v2p4c/v/design_case', tag_ptr='/fa1_p_torch_v2p4c'), r'FA1S ([\d.]+) bar', 'bar')
    fproof = rx_text(ctx, md_find(ctx, 'DSIC', None, {0: 'Pc transducer proof'}, 1, ev='LEAD', tag_raw='LEAD (249 (4), 230 (2))'), r'>= ([\d.]+) bar abs', 'bar', tag='LEAD')
    c1 = rx_text(ctx, md_find(ctx, 'DSIC', None, {0: 'Pc transducer proof'}, 1, ev='DATASHEET', tag_raw='DATASHEET (C1 rating)'), r'XTL-190SM-2000A pick, ([\d.]+) bar', 'bar', tag='DATASHEET')
    items = [('Software Pc cap (normal)', cap.value, C_ACC, cap.ev), ('ECU over-pressure abort', ab.value, C_WARN, ab.ev),
             ('MEOP basis (late light, 24 C interlock)', mb.value, C_GREY, mb.ev), ('Chamber MEOP', meop.value, C_BAD, meop.ev),
             ('Proof pressure', proof.value, C_BAD, proof.ev),
             ('FA-1 band, T <= 0.1 ms', bands[0].value, C_ACC2, bands[0].ev), ('FA-1 band, 0.1-1 ms', bands[1].value, C_ACC2, bands[1].ev),
             ('FA-1 band, 1-20 ms', bands[2].value, C_ACC2, bands[2].ev), ('FA1S design case (gas-filled passages)', fa1s.value, C_BAD, fa1s.ev),
             ('Flight Pc transducer proof (minimum)', fproof.value, C_OK, fproof.ev), ('C1 Kulite rating (proof, maker 1.5x rule)', c1.value, C_OK, c1.ev)]
    rows = [[lab, num_cell(tv, '.2f')] for lab, tv in zip([i[0] for i in items], [cap, ab, mb, meop, proof, bands[0], bands[1], bands[2], fa1s, fproof, c1])]
    o.append(dtable(['Pressure level', 'Value'], rows, widths=['55%', '45%'], cls='tight'))
    o.append(fig_html(plot_pressure_ladder(a, [(i[0], i[1], i[2], i[3]) for i in items]),
                      'Pressure ladder (bar abs; log scale), each level with its class: limits (DECIDED, lead decisions), the MEOP basis (SIM), FA-1 '
                      'equivalent-static band maxima (SIM on ASSUMED inputs; the decided band values of line 230 (2) are rounded up from these), the FA1S '
                      'design case (DERIVED) and the transducer ratings.',
                      [t.tid for t in (cap, ab, mb, meop, proof, fa1s, fproof, c1)] + [b.tid for b in bands], 'wide'))
    o.append(doc.h(2, '2.4 FA-1 hard start: equivalent static pressure spectrum'))
    sp = ctx.src('FA1SP')
    T, cols = [], {}
    if sp.text:
        lines = [l for l in sp.text.splitlines() if l.strip()]
        hdr = lines[0].split(',')
        want = ['head|all|zeta0', 'head|all|zeta0.02', 'head|all|zeta0.05', 'head|baseline|zeta0']
        idxs = {w: hdr.index(w) for w in want if w in hdr}
        for l in lines[1:]:
            c = l.split(',')
            T.append(float(c[0]))
            for w, j in idxs.items():
                cols.setdefault(w, []).append(float(c[j]))
    sptv = TV(ctx, f'{len(T)} periods, columns head|all|zeta0, zeta0.02, zeta0.05, head|baseline|zeta0', '', 'SIM', 'SIM histories (ASSUMED inputs); DERIVED spectra',
              'FA1SP', '(csv columns period_ms, head|all|zeta*, head|baseline|zeta0)', note='plotted as published')
    series = [('head, all cases, ζ 0', cols.get('head|all|zeta0', []), C_ACC, '-'), ('head, all cases, ζ 0.02', cols.get('head|all|zeta0.02', []), C_ACC2, '-'),
              ('head, all cases, ζ 0.05', cols.get('head|all|zeta0.05', []), C_GREY, '-'), ('head, baseline cases, ζ 0', cols.get('head|baseline|zeta0', []), C_WARN, ':')]
    series = [s for s in series if s[1]]
    bandseg = [(0.02, 0.1, 94), (0.1, 1, 121), (1, 20, 147), (20, 50, 94)]
    dec = rx_text(ctx, md_find(ctx, 'DSIC', None, {0: 'FA-1 hard start: structural load'}, 2, ev='LEAD', tag_raw='LEAD (230 (2))'),
                  r'band values ([\d]+) / ([\d]+) / ([\d]+) / ([\d]+) bar abs DECIDED', 'bar', tag='LEAD', group=1)
    dvals = []
    m = re.search(r'band values ([\d]+) / ([\d]+) / ([\d]+) / ([\d]+) bar abs DECIDED', str(md_find(ctx, 'DSIC', None, {0: 'FA-1 hard start: structural load'}, 2,
                                                                                                    ev='LEAD', tag_raw='LEAD (230 (2))').value))
    if m:
        dvals = [float(x) for x in m.groups()]
        bandseg = [(s[0], s[1], dvals[i]) for i, s in enumerate(bandseg)]
    else:
        bandseg = [(s[0], s[1], None) for s in bandseg]
    if T:
        o.append(fig_html(plot_fa1_spectrum(a, T, series, fa1s.value, bandseg),
                          f'FA-1 equivalent static pressure at the head vs SDOF period ({len(T)} periods, {min(T):g}-{max(T):g} ms, counted from the file), '
                          f'undamped and damped (damping ASSUMED); red: the FA1S design case, {esc(fa1s.num(".2f"))} bar abs; green: the decided band '
                          'values for structural SDOF paths (line 230 (2)). SIM histories on ASSUMED inputs, DERIVED spectra (Combustion v2.4b data, '
                          'unchanged by the text-only v2.4c and v2.4d folds: table below).', [sptv.tid, fa1s.tid, dec.tid], 'wide'))
        o.append(dtable(['Currency check of the FA-1 spectrum data', 'Record'], fa1_currency_rows(ctx), widths=['30%', '70%'], cls='tight'))
    else:
        o.append(f'<p class="miss">FA-1 spectra file missing {sptv.ref()}</p>')
    return '\n'.join(o)


def sec_throttle_tvc(ctx, doc, a, D):
    o = [doc.h(1, '3 Throttle and thrust vector control')]
    cl = D['cl']
    o.append(doc.h(2, '3.1 Throttle'))
    rows = []
    for k in ('floor_requirement_25pct', 'floor_target_20pct', 'floor_stretch_12p5pct', 'thrust_ceiling_rule', 'chamber_fill_time_constant_s'):
        rows.append([esc(k.replace('_', ' ')), tvtxt(ctx.v('CMB', f'/operating_points/{k}', tag='SIM'), 500)])
    rows.append(['throttle architecture', tvtxt(ctx.v('CMB', '/decisions/throttle_architecture', tag='LEAD'), 500)])
    o.append(dtable(['Item', 'Value (combustion.json)'], rows, widths=['24%', '76%'], cls='tight'))
    o.append(doc.h(2, '3.2 Gimbal and TVC requirements (GNC v3.2 datasheet inputs)'))
    rows = []
    for key in ('6', '7', '8'):
        ln_r = [x for x in md_rows_all(ctx.src('DSIG').text or '', None) if x[1] and x[1][0].strip() == key]
        if not ln_r:
            rows.append([key, ctx.missing(f'DSIG row {key}')])
            continue
        ln, r = ln_r[0]
        tag = r[3].strip() if len(r) > 3 else None
        ev = normalise_tag(tag)
        val = eng11_cell(ctx, D) if key == '8' else tvtxt(md_cell_ln(ctx, 'DSIG', ln, r, 2, ev, tag_raw=tag, label=r[1].strip()))
        rows.append([Cell(f'<b>{esc(r[1].strip())}</b>', []), val,
                     tvtxt(md_cell_ln(ctx, 'DSIG', ln, r, 4, ev, tag_raw=tag, label=r[1].strip()), 600)])
    o.append(dtable(['Item', 'Value for the datasheet', 'Basis'], rows, widths=['14%', '50%', '36%'], cls='tight',
                    caption=f'01-systems-gnc/DATASHEET-INPUTS-GNC.md rows 6-8 ({esc(src_label(ctx, "DSIG"))}).'))
    o.append(note_box('<b>ENG-11 changed since rev0.</b> ' + inl(cl.item(258, 1)) + ' The rev0 window is SUPERSEDED and not used.', 'warn'))
    o.append(doc.h(2, '3.3 Axis stiffness band and rocking modes (FEA3D, R3 poses)'))
    rr = '/range_over_posted_R3_poses'
    rows = []
    for key, lab in (('FE_coupled_alpha', 'FE, α'), ('FE_coupled_beta', 'FE, β'), ('k_s58_coupled_alpha', 'with servo k_s 58, α'),
                     ('k_s58_coupled_beta', 'with servo k_s 58, β'), ('k_s174_coupled_alpha', 'with servo k_s 174, α'), ('k_s174_coupled_beta', 'with servo k_s 174, β')):
        lo = ctx.v('KTAB', f'{rr}/{key}/min', 'N m/rad', tag='SIM' if key.startswith('FE') else 'DERIVED')
        hi = ctx.v('KTAB', f'{rr}/{key}/max', 'N m/rad', tag='SIM' if key.startswith('FE') else 'DERIVED')
        lp = ctx.v('KTAB', f'{rr}/{key}/min_pose', tag='DERIVED')
        hp = ctx.v('KTAB', f'{rr}/{key}/max_pose', tag='DERIVED')
        rows.append([lab, cat(lo.h('.0f'), ' (', lp.h(pill=False), ') – ', hi.h('.0f'), ' (', hp.h(pill=False), ')')])
    o.append(dtable(['Axis stiffness K over the 17 R3 poses', 'min (pose) – max (pose)'], rows, widths=['40%', '60%'], cls='tight',
                    caption='Per-pose values in §9.7. Servo k_s ASSUMED (TO-VERIFY at B-TVC-1).'))
    o.append(doc.h(2, '3.4 TVC actuation record (mechanical.json v2.1, not re-derived for v3.5.2)'))
    rows = []
    for k in ('concept', 'gear_ratio_n', 'servo_angle_range_deg', 'rate_engine_dps_under_3.19Nm', 'ENG-07_rate_status', 'hinge_moment_design_Nm', 'ENG-11_status'):
        rows.append([esc(k.replace('_', ' ')), tvtxt(ctx.v('MEC', f'/tvc_actuation/{k}', tag='DESIGN', note='v2.1 record; not_re_derived_v352'), 400)])
    for k in ('architecture', 'range_deg', 'mechanical_stop_deg', 'bearings'):
        rows.append([esc('gimbal ' + k.replace('_', ' ')), tvtxt(ctx.v('MEC', f'/gimbal/{k}', tag='DESIGN', note='v2.1 record; not_re_derived_v352'), 400)])
    o.append(dtable(['Item', 'Value (v2.1 record)'], rows, widths=['26%', '74%'], cls='tight',
                    caption='These v2.1 sections were not re-derived for v3.5.2 (mechanical.json not_re_derived_v352); where they conflict with a _v352 section, the _v352 section governs.'))
    return '\n'.join(o)


def eng11_cell(ctx, D):
    """ENG-11 as the lead requires it written (12:13Z item 7; line 258 (1)): design-to 100-110 N m/rad at the ASSUMED servo
    J 1.6e-3 kg m2, not robust across J. The numbers are traced to DSIG row 8; the J is ASSUMED."""
    if 'eng11' in D:
        return D['eng11']
    hit = [x for x in md_rows_all(ctx.src('DSIG').text or '', None) if x[1] and x[1][0].strip() == '8']
    if not hit:
        m = ctx.missing('DSIG row 8 (ENG-11)')
        D['eng11'] = Cell(m.h(), [m])
        return D['eng11']
    ln, r = hit[0]
    tag = r[3].strip() if len(r) > 3 else None
    row = md_cell_ln(ctx, 'DSIG', ln, r, 2, normalise_tag(tag), tag_raw=tag, label='ENG-11 servo output stiffness K_s')
    lo = rx_text(ctx, row, r'Design-to (\d+)-(\d+) N m/rad', 'N m/rad', group=1)
    hi = rx_text(ctx, row, r'Design-to (\d+)-(\d+) N m/rad', 'N m/rad', group=2)
    J = rx_text(ctx, row, r'servo J ([\d.]+e-\d+) kg m2', 'kg m²', tag='ASSUMED',
                note='the "nominal servo J" of DSIG row 8 is the ASSUMED value (lead 12:13Z item 7; CHANGELOG 258 (1), 262 (4))')
    rob = md_find_sentence(ctx, row, 'not robust')
    D['eng11'] = cat('design-to ', lo.h('.0f', unit=False), '–', hi.h('.0f'), ' at the ASSUMED servo J ', J.h('.1e'),
                     ', not robust across J: ', tvtxt(rob, 600))
    return D['eng11']


def md_find_sentence(ctx, tv, contains):
    """The sentence of an already traced text that contains a phrase (same source and key, sentence selector added)."""
    s = tv.value if isinstance(tv.value, str) else ''
    k = s.find(contains)
    if k < 0:
        ctx.issue('WARN', f'no sentence containing {contains!r} in {tv.sid}:{tv.ptr}')
        return ctx.missing(f'{tv.sid} sentence containing {contains}')
    starts = [0] + [m.end() for m in re.finditer(r'(?<=[.;:])\s+(?=[A-Z(*`])', s[:k])]
    m = re.compile(r'(?<=[A-Za-z0-9)\]`*"\'])[.;](?=\s+[A-Z(*`]|\s*$)').search(s, k + len(contains))
    txt = s[starts[-1]:(m.end() if m else len(s))].strip()
    return TV(ctx, txt, '', tv.ev if tv.ev != 'DECIDED' else tv.basis_kind, tv.tag_raw, tv.sid, f'{tv.ptr} [sentence containing "{contains}"]')


def fa1_currency_rows(ctx):
    """FA-1 spectrum data of record: the file named by combustion.json (same sha) and the text-only v2.4c / v2.4d folds
    (lead 12:13Z item 11)."""
    sp = ctx.src('FA1SP')
    rel = '02-combustion/data/v2p4b/fa1_pressure_spectra_published_v2p4b.csv'
    named = ctx.v('CMB', '/fa1_spectra_damped_v2p4b/v/files/' + rel.replace('~', '~0').replace('/', '~1'), tag='REF')
    chk = ctx.d(('same file: ' if named.value == sp.sha16 else 'DIFFERENT file: ') + f'combustion.json {ctx.src("CMB").version} names {rel} with '
                f'sha256/16 {named.value}; the file read here has {sp.sha16}', '', 'generator check: sha named by combustion.json vs the file read', [named])
    s17 = md_sentence(ctx, 'RCMB', '17. v2.4c', 'Text only', 'REF', tag_raw='combustion REPORT.md §17 (v2.4c) header paragraph')
    s18 = md_sentence(ctx, 'RCMB', '18. v2.4d', 'Text only', 'REF', tag_raw='combustion REPORT.md §18 (v2.4d) header paragraph')
    s183 = md_sentence(ctx, 'RCMB', '18.3 Not changed', 'FA-1 grid histories', 'REF', tag_raw='combustion REPORT.md §18.3')
    return [['File named by combustion.json', tvtxt(chk, 400)], ['v2.4c fold (REPORT §17)', tvtxt(s17, 300)],
            ['v2.4d fold (REPORT §18)', tvtxt(s18, 300)], ['FA-1 data after v2.4d (REPORT §18.3)', tvtxt(s183, 300)]]


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
   <div class="cv-draft">DRAFT · {esc(a.rev)}</div>
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
                                                               f'<span class="small">{esc((r.l.get("name") or "")[:110])}</span> {r.row_tv.pill()}{r.row_tv.ref()}', [r.row_tv])])
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
        rows.append(['Over-thrust abort threshold (firmware v2.11 config)', num_cell(ctx.v('ELE', f'/abort_matrix/causes/{ci}/thresholds/kOverThrust_N', 'N'), '.0f')])
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
    k += 1
    o.append(doc.h(2, f'5.{k} Standard hardware (fasteners, springs, bearings; BOM /hardware, CALC masses)'))
    rows = []
    for r in D['hw']:
        l = r.l
        nm = esc(l.get('name', ''))
        nm = nm if len(nm) <= 120 else nm[:118].rsplit(' ', 1)[0] + ' …'
        notes = l.get('notes') or ''
        m = re.search(r'torque ([^;(]+)', notes)
        tq = esc(m.group(1).strip()[:40]) if m else ''
        rows.append([Cell(f'<span class="pn">{esc(r.pn)}</span>{r.row_tv.ref()}', [r.row_tv]),
                     Cell(f'{nm}<div class="sup">{esc((l.get("supplier_pn") or l.get("supplier") or "")[:90])}</div>', [r.row_tv]),
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
    o.append(doc.h(2, f'5.{k} Ground support tools, provisions and contingency (not flight mass)'))
    rows = []
    for r in D['gse'] + [x for x in D['bom'] if x.kind != 'lines']:
        l = r.l
        rows.append([Cell(f'<span class="pn">{esc(r.pn)}</span>{r.row_tv.ref()}', [r.row_tv]),
                     Cell(esc(l.get('name', '')[:140]) + f'<div class="sup">{esc((l.get("supplier") or "")[:80])}</div>', [r.row_tv]),
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
    st = ctx.v('TXT5', '/T-F1_exposure_basis_R9/criteria_status', tag='LEAD')
    av = ctx.v('TXT5', '/T-F1_exposure_basis_R9/abort_value', tag='LEAD')
    al = ctx.raw('TXT5', '/T-F1_engmat_10000h_values_used_by_the_cells', default={}) or {}
    rows = [['T-F1 founder action (text v5)', tvtxt(tf, 1400)], ['Criteria status', tvtxt(st, 400)], ['Abort value', tvtxt(av)]]
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
        ['Case-TC abort A / start and relight limit / nozzle-holder limit (firmware v2.11)', cat(temp_k(cot, 2), ' / ', temp_k(crl, 2), ' / ', temp_k(nht, 2), Cell('', [cot, crl, nht]))],
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
        parts.append(f'{r.pn} ({(r.l.get("name") or "")[:70]})')
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
                out.append(f'{it["inst"]}: {rr:.2f} mm from the axis ({((br.l.get("name") if br else "") or "")[:110]})')
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


# ---------------------------------------------------------------------------------------------
# section 9: structural analysis, 3D FEA of the assembled engine on CAD v3.5.2 (FEA3D-2) and the
# rows-v8 margin matrix; J-FWD joint rows; mounting data; stiffness and modes; F4 joints
# ---------------------------------------------------------------------------------------------
MX_GROUPS = [('Static, pressure and FA-1 cases', ['LC1', 'LC2', 'LC2F', 'FA1Q', 'FA1D', 'FA1U', 'FA1S', 'FA1T']),
             ('Landing, gimbal-stop and thermal cases', ['LC3 cold', 'LC3 hot bound', 'GS', 'TD', 'LC6 F2', 'F2 hot bound', 'LC6 soak']),
             ('Thermal-abort states, joints and the part minimum', ['TB70', 'TBS', 'J-FWD', 'J-FD01', 'J-FD09', 'min'])]
MX_TAG = 'margin matrix v3.5.2 on rows v8 (lead re-run; 234 (4) all-node rule; MS = allowable / (SF x stress) - 1)'
NUMRE = re.compile(r'[+\-−]?\d+\.\d+')


def mx_display(txt, fn, label):
    """Matrix cell text -> compact html: the 'y / u' pair and flags; a long parenthetical goes to a footnote."""
    t = txt.strip()
    if t in ('-', ''):
        return '–'
    main, note = t, None
    k = t.find('(')
    if k > 0:
        main, note = t[:k].rstrip(), t[k:]
    main = re.sub(r'(?<![\w.])-(?=\d)', '−', main)
    h = esc(main)
    if note and len(note) <= 18:
        h += f' <span class="small">{esc(note)}</span>'
    elif note:
        fn.append(f'{label}: {txt}')
        h += f'<sup>{len(fn)}</sup>'
    return h


def mx_numbers(txt):
    v = [float(x.replace('−', '-')) for x in NUMRE.findall(txt or '')[:2]]
    return v


def plot_min_margin(a, rows):
    """rows: [(part, value, col, cls)] lowest margin per part (bar chart, negatives red)."""
    plt = mpl_setup()
    n = len(rows)
    fig, ax = plt.subplots(figsize=(6.9, 0.165 * n + 0.75))
    cap = 2.0
    for i, (p, v, col, cls) in enumerate(rows):
        y = n - 1 - i
        if v is None:
            ax.text(0.01, y, 'MISSING', va='center', fontsize=5.8, color=C_BAD)
            continue
        vv = min(v, cap)
        c = C_BAD if v < 0 else (C_WARN if v < 0.05 else C_ACC)
        ax.barh(y, vv, height=0.66, color=c)
        lab = f'{v:+.3f}  {col}' + (f'  [{cls}]' if cls else '')
        if v > cap:
            ax.text(cap + 0.03, y, f"> {lab}", va='center', fontsize=5.6, color='#333')
        elif v < 0:
            ax.text(0.03, y, lab, va='center', fontsize=5.6, color='#8c1d24')
        else:
            ax.text(vv + 0.03, y, lab, va='center', fontsize=5.6, color='#333')
    ax.set_yticks(range(n))
    ax.set_yticklabels([r[0] for r in rows][::-1], fontsize=6.0)
    ax.axvline(0, color='#333', lw=0.7)
    ax.axvline(0.05, color=C_WARN, lw=0.6, ls=':')
    ax.set_xlim(-0.7, cap + 1.15)
    ax.set_xlabel('lowest margin of safety over every case (MS_y or MS_u, the lower); bars clipped at +2.0')
    ax.grid(axis='y', visible=False)
    fig.tight_layout()
    return save_plot(fig, a, 'plot_min_margin')


def mx_part_rows(ctx):
    rows = md_rows_where(ctx, 'MMXMD', 'FEA3D margin matrix v3.5.2')
    hdr = md_rows_all(ctx.src('MMXMD').text or '', 'FEA3D margin matrix v3.5.2')[0][1]
    return hdr, rows


def mx_json_row(ctx, part):
    for i, r in enumerate(ctx.raw('MMX', '/rows', default=[]) or []):
        if r.get('part') == part.split(' (')[0] or r.get('part') == part:
            return i, r
    return None, None


def sec_fea_matrix(ctx, doc, a, D, o):
    hdr, rows = mx_part_rows(ctx)
    colidx = {c: j for j, c in enumerate(hdr)}
    o.append(doc.h(2, '9.2 Margin matrix: every part × every load case'))
    o.append(f'<p>{inl(md_line_starting(ctx, "MMXMD", "Cell = MS_y", "DERIVED", tag_raw=MX_TAG))}</p>')
    o.append(note_box('Read the matrix as found: a negative cell is a FOUND NEGATIVE of the model and is never shown as passing. '
                      'Cells are MS_y / MS_u (yield / ultimate; one value for brittle parts). Red cells are negative; amber cells are below +0.05. '
                      '"–" means the case is not evaluated for that part (§9.2.4). Classes and closures of every negative cell are in §9.3.', 'neg'))
    nmis = 0
    for gi, (gname, cols) in enumerate(MX_GROUPS):
        fn = []
        body = []
        for ln, r in rows:
            part = re.sub(r'\*\*', '', r[0]).strip()
            cells = [Cell(f'<b>{esc(part)}</b>', [])]
            ji, jr = mx_json_row(ctx, part)
            for c in cols:
                j = colidx.get(c)
                if j is None or j >= len(r):
                    cells.append(ctx.missing(f'matrix column {c}'))
                    continue
                txt = re.sub(r'\*\*', '', r[j]).strip()
                ev = 'DERIVED' if c == 'min' else ('CALC' if c == 'J-FWD' else 'SIM')
                tv = md_cell_ln(ctx, 'MMXMD', ln, r, j, ev, tag_raw=MX_TAG, label=part)
                html_ = mx_display(txt, fn, f'{part} {c}')
                if html_ == '–':
                    cells.append(Cell('–', [tv]))
                else:
                    cells.append(Cell(f'{html_}{tv.ref()}', [tv], cls=val_class(txt)))
                # generator cross-check of the md cell against the matrix JSON (same publication)
                if jr is not None and c != 'min' and txt not in ('-', '') and not txt.startswith('>'):
                    jv = ((jr.get('cells') or {}).get(c) or {}).get('value')
                    mv = mx_numbers(txt)
                    if isinstance(jv, list) and mv:
                        jn_ = [x for x in jv if isinstance(x, (int, float))]
                        if jn_ and abs(jn_[0] - mv[0]) > 0.0015:
                            nmis += 1
                            ctx.issue('WARN', f'matrix md vs json differ: {part} {c}: md {txt!r} json {jv}')
            body.append(cells)
        heads = ['Part'] + [esc(c) for c in cols]
        w0 = '13%'
        wc = f'{87 / len(cols):.1f}%'
        o.append(dtable(heads, body, cls='mx', widths=[w0] + [wc] * len(cols),
                        caption=f'Table 9.{gi + 1}: {esc(gname)} (MS_y / MS_u; flags r, a, c, p, s, w as defined in the matrix text above; MF / BT classes; '
                                f'source MMXMD {esc(src_label(ctx, "MMXMD"))}).'))
        if fn:
            o.append('<div class="fn">' + ''.join(f'<p><sup>{i + 1}</sup> {esc(t)}</p>' for i, t in enumerate(fn)) + '</div>')
    D['mx_mismatch'] = nmis
    # lowest margin per part (JSON min) chart
    prow, refs = [], []
    neg_parts = []
    for i, jr in enumerate(ctx.raw('MMX', '/rows', default=[]) or []):
        tv = ctx.v('MMX', f'/rows/{i}/min/0', tag='DERIVED', note='lowest cell of the part (matrix json min)')
        col = ctx.v('MMX', f'/rows/{i}/min/1', tag='DERIVED')
        refs += [tv.tid, col.tid]
        cls_ = ''
        cell = ((jr.get('cells') or {}).get(col.value) or {})
        if isinstance(cell, dict) and cell.get('class'):
            cls_ = cell.get('class')
        prow.append((jr.get('part'), tv.value, f'{col.value} {ctx.raw("MMX", f"/rows/{i}/min/2", default="")}', cls_))
        if tv.value is not None and tv.value < 0:
            neg_parts.append(jr.get('part'))
    src = plot_min_margin(a, prow)
    o.append(fig_html(src, 'Lowest margin of safety per part over every load case (the matrix "min" field; red = negative, amber = below +0.05; '
                           'class of the governing cell in brackets where the matrix gives one). Bars are clipped at +2.0. DERIVED from SIM / CALC cells.',
                      refs, 'wide'))
    D['neg_parts'] = neg_parts
    # columns not evaluated
    o.append(doc.h(3, '9.2.4 Cells shown "–" and why'))
    items = []
    for ln, r in []:
        pass
    L = (ctx.src('MMXMD').text or '').splitlines()
    on = False
    for i, ln in enumerate(L, 1):
        if ln.startswith('## '):
            on = ln.startswith("## Cells shown '-' and why")
            continue
        if on and ln.startswith('- '):
            items.append(ctx.t('MMXMD', f'§Cells shown "-" and why line {i}', ln[2:].strip(), 'DERIVED', tag_raw=MX_TAG))
    o.append(dtable(['Column', 'Why'], [[Cell(esc(re.sub(r'\*\*', '', it.value).split(':')[0]), []), tvtxt(it)] for it in items],
                    widths=['14%', '86%']))


def mx_negatives(ctx, D):
    """Negative-cell table of the matrix (computed once in prepare; section 1 and section 9 both use it)."""
    if 'neg_body' in D:
        return D['neg_body']
    rows = md_rows_where(ctx, 'MMXMD', 'Negative cells and their classes')
    body, by_cls = [], {}
    for ln, r in rows:
        part = re.sub(r'\*\*', '', r[0]).strip()
        tvs = [md_cell_ln(ctx, 'MMXMD', ln, r, j, ev, tag_raw=MX_TAG + '; negative-cell table', label=part)
               for j, ev in ((1, 'SIM'), (2, 'SIM'), (3, 'SIM'), (4, 'DERIVED'), (5, 'DERIVED'), (6, 'REF'))]
        by_cls.setdefault(tvs[3].value, []).append(tvs[3])
        body.append([Cell(f'<b>{esc(part)}</b>', []), tvtxt(tvs[0]), Cell(f'<b>{esc(tvs[1].value.replace("-", "−"))}</b>{tvs[1].ref()}', [tvs[1]], cls='neg'),
                     tvtxt(tvs[2], 120), Cell(f'<span class="neg-tag">{esc(tvs[3].value)}</span>{tvs[3].ref()}', [tvs[3]]), tvtxt(tvs[4], 260), tvtxt(tvs[5])])
    D['neg_total'] = ctx.d(len(body), '', 'count of rows of the matrix table "Negative cells and their classes"',
                           [c for row in body for c in row if isinstance(c, TV)])
    D['neg_by_class'] = {k: ctx.d(len(by_cls[k]), '', f'count of negative cells with class {k}', by_cls[k]) for k in sorted(by_cls)}
    D['neg_body'] = body
    return body


def sec_fea_negatives(ctx, doc, a, D, o):
    o.append(doc.h(2, '9.3 Found negatives: every negative cell, its class and its closure'))
    body = mx_negatives(ctx, D)
    ntot = D['neg_total']
    cnt = [cat(f'<b>{esc(k)}</b> ', t.h(pill=False)) for k, t in D['neg_by_class'].items()]
    cls_doc = {'BT': 'bad-tet node (mesh defect; lead 21:15:29Z (4))', 'MF': 'model fidelity (a named sub-model governs; lead 21:15:29Z (3))',
               'BR': 'brittle part (graphite), thermal', 'DC': 'design change route (J-FWD seat line)', 'TS-183': 'thermal stress, 183 (1) (c) LCF / (d) time at temperature',
               'TS-212': 'thermal stress, 212 (1) (d) time at temperature', 'CH': 'char layer against an ASSUMED strength'}
    o.append(f'<p>{ntot.h(pill=True)} cells of the matrix are negative. By class (REV-MECH-2 section 10 classes; class rules of CHANGELOG 234 (4)): '
             + ' · '.join(c.html for c in cnt) + '.</p>')
    o.append(dtable(['Part', 'Column', 'Cell y / u', 'Governing record', 'Class', 'Closure (what closes it)', 'Ref'], body, label_cols=1, cls='tight',
                    widths=['8%', '9%', '10%', '22%', '6%', '33%', '12%'],
                    caption='Every negative matrix cell (MMXMD, section "Negative cells and their classes"). The class decides the closure route; '
                            'no class turns a negative into a pass.'))
    o.append('<p class="small">Class key (matrix class rules): ' + '; '.join(f'<b>{esc(k)}</b> {esc(v)}' for k, v in cls_doc.items()) + '. '
             'The key is a reading aid written for this datasheet; the class of each cell is the traced value in the table.</p>')
    sec_fea_info_negatives(ctx, doc, a, D, o)


def sec_fea_info_negatives(ctx, doc, a, D, o):
    """Negative cells of the information columns (margin_matrix_v352.json /info_columns): shown as information, not governing
    (lead 2026-10-21 12:13Z item 13); a cell without a class is flagged."""
    info = ctx.raw('MMX', '/info_columns', default=[]) or []
    body, unc = [], []
    for i, r in enumerate(ctx.raw('MMX', '/rows', default=[]) or []):
        for c in info:
            cell = (r.get('cells') or {}).get(c)
            if not isinstance(cell, dict):
                continue
            v = cell.get('value')
            vals = [x for x in (v if isinstance(v, list) else [v]) if isinstance(x, (int, float)) and not isinstance(x, bool)]
            if not vals or min(vals) >= 0:
                continue
            b = ptr_join('rows', i, 'cells', c)
            ty = ctx.v('MMX', b + '/value/0', tag='SIM', note=f'{r.get("part")} {c}: y')
            u = v[1] if isinstance(v, list) and len(v) > 1 else None
            tu = ctx.v('MMX', b + '/value/1', tag='SIM', note=f'{r.get("part")} {c}: u') if u is not None else None
            cls = ctx.v('MMX', b + '/class', tag='DERIVED')
            clo = ctx.v('MMX', b + '/closure', tag='DERIVED')
            flag = cls.value in (None, 'UNCLASSIFIED')
            if flag:
                unc.append((r.get('part'), c, ty, cls, clo))
            yu = f'<b>{esc(fmt_num(ty.value, "+.3f").replace("-", "−"))}</b> / ' + (esc(fmt_num(tu.value, '+.3f').replace('-', '−')) if tu is not None else 'n/a')
            body.append([Cell(f'<b>{esc(r.get("part"))}</b>', []), Cell(esc(c), [ty]), Cell(f'{yu} {ty.pill()}{ty.ref()}' + (tu.ref() if tu is not None else ''), [ty] + ([tu] if tu else []), cls='neg'),
                         Cell((f'<span class="neg-tag">{esc(cls.value)}</span>' if flag else f'<b>{esc(cls.value)}</b>') + f' {cls.pill()}{cls.ref()}', [cls]), tvtxt(clo, 220)])
    D['info_neg_total'] = ctx.d(len(body), '', 'count of negative cells in the information columns of margin_matrix_v352.json', [c for row in body for c in row if isinstance(c, TV)])
    o.append(doc.h(3, '9.3.1 Negative cells in the information columns (information, not governing)'))
    o.append(f'<p>{D["info_neg_total"].h()} more cells are negative in the information columns ({esc(", ".join(info))}). They are shown as information: '
             'they do not govern and are not in the count above.'
             + (' <b>Flagged:</b> ' + '; '.join(f'{esc(p)} {esc(c)} {t.h(".3f")} has no class ({esc(cl_.value)}; closure: {esc(str(co.value))})'
                                                for p, c, t, cl_, co in unc) + '.' if unc else '') + '</p>')
    o.append(dtable(['Part', 'Column', 'Cell y / u', 'Class', 'Closure (quoted)'], body, label_cols=1, cls='tight', widths=['9%', '17%', '16%', '14%', '44%'],
                    caption='margin_matrix_v352.json (rows v8), information columns /info_columns; cell values and classes as published.'))


def sec_fea_named(ctx, doc, a, D, o):
    o.append(doc.h(2, '9.4 Named findings stated plainly'))
    hdr, rows = mx_part_rows(ctx)
    colidx = {c: j for j, c in enumerate(hdr)}

    def cell(part, col):
        for ln, r in rows:
            if re.sub(r'\*\*', '', r[0]).strip() == part:
                return md_cell_ln(ctx, 'MMXMD', ln, r, colidx[col], 'SIM', tag_raw=MX_TAG, label=part)
        return ctx.missing(f'matrix {part} {col}')
    t1 = cell('TC-01', 'J-FWD')
    neg = [r for ln, r in md_rows_where(ctx, 'MMXMD', 'Negative cells and their classes') if r[0].strip() == 'TC-04']
    f3d10 = md_find(ctx, 'F3D', '13. Open items and owners', {0: '10'}, 2, ev='DERIVED', tag_raw='FEA3D-2 report §13 item 10')
    f3d10o = md_find(ctx, 'F3D', '13. Open items and owners', {0: '10'}, 3, ev='LEAD', tag_raw='FEA3D-2 report §13 item 10 owner')
    c96 = ctx.v('TXT5', '/item_C/C9_founder_texts_remap_v352/(6)_TC-02_select_fit_band_R2', tag='CALC')
    c6 = ctx.v('TXT5', '/item_C/C6_founder_action_list_related', tag='CALC')
    fil = ctx.v('FIL', '/verdict', tag='CALC', tag_ptr='/status')
    lcf_st = ctx.v('LCF', '/status_183_1c', tag='LEAD')
    k30 = ctx.v('LCF', '/governing/i_firing|Kf3.0|worst_of_histories|3750/MS_cycles_vs_50', tag='CALC')
    k30n = ctx.v('LCF', '/governing/i_firing|Kf3.0|worst_of_histories|3750/N_allow', tag='CALC')
    k30z = ctx.v('LCF', '/governing/ii_assembly_from_zero|Kf3.0|worst_of_histories|3750/MS_cycles_vs_50', tag='CALC')
    k30zn = ctx.v('LCF', '/governing/ii_assembly_from_zero|Kf3.0|worst_of_histories|3750/N_allow', tag='CALC')
    hw = cell('HW-101 (J-FWD)', 'J-FWD')
    rows_ = [
        ['TC-04 hot-bound cells (class BT)', cat(f3d10, Cell('', [])), tvtxt(f3d10o)],
        ['TC-01 J-FWD seat-line P+Q (class DC)',
         cat(Cell('Matrix cell (drawn fit): ', []), Cell(f'<b class="miss">{esc(t1.value)}</b>{t1.ref()}', [t1]),
             '<br>R2-B select fit and the band (Mechanical, CALC on SIM): ', tvtxt(c96, 1700)),
         Cell('Founder / shop: select-fit process with U TO-DEFINE (R2-B, CHANGELOG 254 (1)); Mechanical / FEA3D: convergence (not shown)', [c96])],
        ['J-FWD screw LCF at the thread root (C6 OPEN, single-use screws)',
         cat(lcf_st, '<br>Kf 3.0, per firing: N_allow ', k30n, ', MS ', k30, '; assembly from zero: N_allow ', k30zn, ', MS ', k30z,
             '<br>', tvtxt(c6, 2300)),
         Cell('Mechanical (closure path 2) / founder (path 3, qualification test TO-DEFINE); until then every J-FWD screw is single-use', [c6])],
        ['J-FWD screw head-to-shank fillet from zero', tvtxt(fil, 1400), Cell('Mechanical: Kt page and T-head Kt TO-SOURCE', [fil])],
        ['HW-101 IN718 screw, J-FWD cell (positive; rows v8)', cat(hw), Cell('Mechanical (rows v8, R6 basis)', [hw])],
    ]
    o.append(dtable(['Finding', 'What the sources say (quoted)', 'Owner / route'], rows_, widths=['17%', '63%', '20%'], cls='tight',
                    caption='Named findings of the brief, each quoted from its source. The TC-01 seat-line P+Q is a FOUND NEGATIVE at the drawn fit; '
                            'the R2-B select fit closes it only in the CALC-on-SIM band model and only if the select-fit process is carried out.'))
    if neg:
        o.append('<p class="small">TC-04 negative cells as listed in §9.3: ' + ', '.join(esc(f'{r[1]} {r[2]}') for r in neg) + '.</p>')


def jfwd_rows_table(ctx, pi, part, sel, title, cls='tight'):
    base = f'/rows/{pi}/cells/J-FWD/rows'
    rs = ctx.raw('MMX', base, default=[]) or []
    body = []
    for k, r in enumerate(rs):
        if not sel(r):
            continue
        p = f'{base}/{k}'
        st = ctx.v('MMX', p + '/state', tag='DERIVED')
        desc = ctx.v('MMX', p + '/row', tag_ptr=p + '/tag')
        y = ctx.v('MMX', p + '/MS_y', tag_ptr=p + '/tag') if 'MS_y' in r else None
        u = ctx.v('MMX', p + '/MS_u', tag_ptr=p + '/tag') if 'MS_u' in r else None
        pre = ctx.v('MMX', p + '/preload_N', 'N', tag_ptr=p + '/tag') if r.get('preload_N') is not None else None
        crit = ctx.v('MMX', p + '/criterion', tag='LEAD') if r.get('criterion') else None
        note = ctx.v('MMX', p + '/note', tag_ptr=p + '/tag') if r.get('note') else None

        def ms(tv):
            if tv is None:
                return Cell('–', [])
            if tv.value is None:
                return Cell('–', [tv])
            c = 'neg' if tv.value < 0 else ('thin' if tv.value < 0.05 else '')
            return Cell(f'{esc(fmt_num(tv.value, "+.3f"))}{tv.ref()}', [tv], cls=c)
        extra = []
        if crit is not None:
            extra.append(crit)
        if note is not None:
            extra.append(note)
        body.append([Cell(f'{esc(st.value)}{st.ref()}', [st]), tvtxt(desc, 150), ms(y), ms(u),
                     Cell(esc(str(pre.value)) + pre.ref(), [pre]) if pre is not None else Cell('–', []),
                     Cell(f'{esc(str(r.get("tag") or ""))} {desc.pill()}', [desc]),
                     cat(*[Cell(f'<div class="small">{esc(str(e.value)[:140])}{e.ref()}</div>', [e]) for e in extra]) if extra else Cell('–', [])])
    return body


def sec_fea_jfwd(ctx, doc, a, D, o):
    o.append(doc.h(2, '9.5 J-FWD joint rows (TC-01 / TC-02 / HW-101 screw)'))
    o.append(f'<p>{inl(md_heading(ctx, "MMXMD", "J-FWD column rows", "DERIVED", tag_raw=MX_TAG))}. '
             'The criterion rows set the matrix cell; the hand-form LC2N / LC2M rows are shown beside them as information (lead 03:30:46Z, CHANGELOG 250 (2)); '
             'every other information row follows in a third table. Values are from the matrix JSON (MMX), row by row.</p>')
    heads = ['State', 'Row', 'MS_y', 'MS_u', 'Preload', 'Tag', 'Criterion / note']
    widths = ['7%', '41%', '7%', '7%', '7%', '10%', '21%']
    for part in ('TC-01', 'TC-02', 'HW-101 (J-FWD)'):
        pi, jr = mx_json_row(ctx, part)
        if pi is None:
            o.append(f'<p class="miss">{esc(part)}: no J-FWD rows found</p>')
            continue
        cv = ctx.v('MMX', f'/rows/{pi}/cells/J-FWD/value', tag='CALC', note='J-FWD cell = minimum over the criterion rows')
        o.append(doc.h(3, f'9.5.{("TC-01", "TC-02", "HW-101 (J-FWD)").index(part) + 1} {part}: J-FWD cell {fmt_num(cv.value[0], "+.3f")} / {fmt_num(cv.value[1], "+.3f")}'
                       if isinstance(cv.value, list) and len(cv.value) == 2 and None not in cv.value else f'9.5 {part}'))
        crit = jfwd_rows_table(ctx, pi, part, lambda r: not r.get('info'), 'criterion')
        lc2 = jfwd_rows_table(ctx, pi, part, lambda r: r.get('info') and r.get('state') in ('LC2N', 'LC2M'), 'LC2 info')
        oth = jfwd_rows_table(ctx, pi, part, lambda r: r.get('info') and r.get('state') not in ('LC2N', 'LC2M'), 'other info')
        o.append(dtable(heads, crit, label_cols=0, cls='tight', widths=widths,
                        caption=f'{esc(part)}: criterion rows ({len(crit)}); cell {cv.h(pill=False)}.'))
        if lc2:
            o.append(dtable(heads, lc2, label_cols=0, cls='tight', widths=widths,
                            caption=f'{esc(part)}: hand-form LC2N / LC2M rows, INFORMATION beside the criterion (rule (A), lead 03:30:46Z) ({len(lc2)}).'))
        if oth:
            o.append(dtable(heads, oth, label_cols=0, cls='tight', widths=widths,
                            caption=f'{esc(part)}: other information rows ({len(oth)}); they do not set the cell.'))


def sec_fea_mount(ctx, doc, a, D, o):
    o.append(doc.h(2, '9.6 Mounting data: loads at the 16 airframe holes'))
    rule = ctx.v('MOUNT', '/datasheet_v352_governing/rule', tag='DERIVED')
    o.append(f'<p>{inl(md_line_starting(ctx, "MOUNTMD", "Generated", "SIM", tag_raw="FEA3D mounting data (SIM unless tagged)"))}</p>')
    o.append(f'<p>Governing rule: {inl(rule)} The CHANGELOG ruling: {inl(D["cl"].item(249, 6))}</p>')
    sec = 'v3.5.2 model: DATASHEET per-hole values, governing'
    allr = md_rows_all(ctx.src('MOUNTMD').text or '', sec)
    if not allr:
        o.append('<p class="miss">mounting table not found</p>')
        return
    hdr = allr[0][1]
    rows = allr[1:]
    o.append(f'<p class="small">{inl(md_line_starting(ctx, "MOUNTMD", "Cell = max shear", "DERIVED", tag_raw="FEA3D mounting data legend"))}</p>')
    for gi, (lo, hi) in enumerate(((1, 8), (8, len(hdr)))):
        body = []
        for ln, r in rows:
            lab = re.sub(r'\*\*', '', r[0]).strip()
            cells = [Cell(f'<span class="mono">{esc(lab)}</span>', [])]
            for j in range(lo, hi):
                tv = md_cell_ln(ctx, 'MOUNTMD', ln, r, j, 'DERIVED', tag_raw='FEA3D mounting rows: SIM as found, moment-free estimate DERIVED (! = estimate governs)', label=lab)
                cells.append(Cell(f'{esc(tv.value)}{tv.ref()}', [tv]))
            body.append(cells)
        o.append(dtable(['Hole (x, y, z mm)'] + [esc(h) for h in hdr[lo:hi]], body, cls='mount',
                        widths=['17%'] + [f'{83 / (hi - lo):.1f}%'] * (hi - lo),
                        caption=f'Per-hole governing loads, part {gi + 1} of 2: max shear / max |axial| / max pull-out [N] per case; '
                                f'"!" = the moment-free estimate governs that value by 0.5 N or more; "*" = a compliant-airframe value exceeds the rigid one '
                                f'(MOUNTMD {esc(src_label(ctx, "MOUNTMD"))}).'))
    # totals on the airframe (rigid)
    body = []
    for case in (ctx.raw('MOUNT', '/datasheet_v352_governing/groups', default={}) or {}):
        base = f'/datasheet_v352_governing/groups/{case}/total_on_airframe_rigid'
        F = ctx.v('MOUNT', base + '/max_abs_F_N', 'N', tag='DERIVED', tag_ptr=f'/datasheet_v352_governing/groups/{case}/tag')
        M = ctx.v('MOUNT', base + '/max_abs_M_Nmm', 'N mm', tag='DERIVED', tag_ptr=f'/datasheet_v352_governing/groups/{case}/tag')
        body.append([esc(case), Cell(esc(', '.join(fmt_num(x, '.1f') for x in (F.value or []))) + F.ref(), [F]),
                     Cell(esc(', '.join(fmt_num(x, '.0f') for x in (M.value or []))) + M.ref(), [M])])
    o.append(dtable(['Case', 'Total force on the airframe, max |Fx|, |Fy|, |Fz| [N]', 'Total moment, max |Mx|, |My|, |Mz| [N mm]'], body,
                    widths=['16%', '42%', '42%'], cls='tight', caption='Resultant of the 16 hole loads on the airframe, rigid airframe, per case (DERIVED).'))
    ms = [('Included FE model mass, v3.5.2 (L1)', '/mass/v352/model_kg'), ('Engine group in the model', '/mass/v352/engine'),
          ('Excluded airframe-wall equipment (loads go to the wall directly)', '/mass/v352/excluded_kg')]
    o.append(dtable(['Mounting data header', 'Value'], [[l, num_cell(ctx.v('MOUNT', p, 'kg', tag='DERIVED'), '.3f')] for l, p in ms], widths=['60%', '40%']))


def sec_fea_stiff(ctx, doc, a, D, o):
    o.append(doc.h(2, '9.7 Gimbal axis stiffness (R3 poses) and rocking modes'))
    o.append(f'<p>{inl(ctx.v("KTAB", "/evidence", tag="SIM"))}</p>')
    body = []
    for i, r in enumerate(ctx.raw('KTAB', '/rows', default=[]) or []):
        b = f'/rows/{i}/values'
        cells = [Cell(f'<b>{esc(r.get("pose"))}</b> <span class="small">{esc(str(r.get("kind") or ""))}</span>', [])]
        for key in ('FE_coupled_alpha', 'FE_coupled_beta', 'k_s58_coupled_alpha', 'k_s58_coupled_beta', 'k_s174_coupled_alpha', 'k_s174_coupled_beta'):
            tv = ctx.v('KTAB', f'{b}/{key}/R3', 'N m/rad', tag='DERIVED' if key.startswith('k_s') else 'SIM')
            cells.append(num_cell(tv, '.0f', unit=False))
        fr = ctx.v('KTAB', f'/rows/{i}/fraction_max', tag='DERIVED')
        cells.append(num_cell(fr, '.3f'))
        body.append(cells)
    o.append(dtable(['Pose', 'FE α', 'FE β', 'k_s 58: α', 'k_s 58: β', 'k_s 174: α', 'k_s 174: β', 'Fraction max'], body, cls='tight',
                    widths=['22%', '10%', '10%', '11%', '11%', '11%', '11%', '14%'],
                    caption='Axis stiffness K at the 17 R3 poses [N m/rad], coupled values: FE alone (SIM) and with the servo in series at k_s 58 and 174 N m/rad '
                            '(ASSUMED, TO-VERIFY at B-TVC-1). Fraction = the pose change over the stop045 change (KTAB).'))
    body = []
    for ks in ('58', '174'):
        for J in ('J_free', 'J_low', 'J_nom', 'J_high'):
            tv = ctx.v('ROCK', f'/pose_range_Hz/{ks}/{J}', 'Hz', tag_ptr='/tag')
            body.append([f'k_s {ks} N m/rad, {J.replace("_", " ")}', Cell(esc(' – '.join(fmt_num(x, '.1f') for x in (tv.value or []))) + ' Hz ' + tv.pill() + tv.ref(), [tv])])
    Jv = ctx.v('ROCK', '/J_kgm2', 'kg m2', tag_ptr='/tag')
    o.append(dtable(['Servo stiffness and inertia case', 'Rocking-mode range over the 17 poses'], body, widths=['45%', '55%'], cls='tight',
                    caption=f'Lumped 2-DOF rocking frequencies (ROCK; rigid airframe). Servo J values: {esc(readable(Jv.value))} {Jv.ref()}.'))


def sec_fea_f4(ctx, doc, a, D, o):
    o.append(doc.h(2, '9.8 Secondary joints J-FD01 / J-FD09 (F4)'))
    body = []
    for jn_ in ('J-FD01', 'J-FD09'):
        b = f'/joints/{jn_}'
        hwv = ctx.v('F4J', b + '/hardware', tag='DESIGN')
        tq = ctx.v('F4J', b + '/preload/T_Nm', 'N m', tag='DESIGN')
        fnom = ctx.v('F4J', b + '/preload/F_nom_N', 'N', tag='DERIVED')
        for var in (ctx.raw('F4J', b + '/worst', default={}) or {}):
            w = f'{b}/worst/{var}'
            wb = ctx.v('F4J', w + '/bounding/MS', tag='SIM')
            wc = ctx.v('F4J', w + '/bounding/case', tag='SIM')
            wa = ctx.v('F4J', w + '/bounding/area', tag='SIM')
            wp = ctx.v('F4J', w + '/phi02/MS', tag='SIM')
            body.append([f'<b>{jn_}</b>', tvtxt(hwv, 200), cat(tq.h('.1f'), ' / ', fnom.h('.0f')),
                         cat(f'<span class="small">{esc(var)}:</span> ', wa.h(pill=False)),
                         cat(wb.h('+.3f'), '<br><span class="small">', wc.h(pill=False), '</span>'), num_cell(wp, '+.3f')])
    o.append(dtable(['Joint', 'Hardware', 'Torque / nominal preload', 'Variant / area', 'Worst bolt MS_y (bounding)', 'MS_y with Φ 0.2'], body, cls='tight',
                    widths=['8%', '34%', '14%', '14%', '18%', '12%'],
                    caption='F4 secondary joints on the v3.5.2 hardware (F4J; preload scatter ±25 % and K 0.20 ASSUMED). The matrix cells J-FD01 / J-FD09 are in Table 9.3.'))


def sec_fea_followups(ctx, doc, a, D, o):
    o.append(doc.h(2, '9.9 Mechanical follow-ups after FEA3D-2: tap wall v3, LC-TB70 v2, C1 seat'))
    st = ctx.v('TAPW', '/status', tag='CALC')
    vd = ctx.v('TAPW', '/verdict', tag='CALC', tag_ptr='/status')
    g = '/rows/3750/governing'
    rows = [['Governing (TC-02 thread, SOAK52)', cat(ctx.v('TAPW', g + '/TC02_thread_T/MS_y', tag='CALC').h('+.3f'), ' / ',
                                                    ctx.v('TAPW', g + '/TC02_thread_T/MS_u', tag='CALC').h('+.3f'))],
            ['Screw-temperature sensitivity (SOAK70)', cat(ctx.v('TAPW', g + '/worst_with_screw_T_sensitivity/MS_y', tag='CALC').h('+.3f'), ' / ',
                                                           ctx.v('TAPW', g + '/worst_with_screw_T_sensitivity/MS_u', tag='CALC').h('+.3f'))],
            ['Verdict', tvtxt(vd, 900)], ['Status', tvtxt(st, 400)]]
    o.append(dtable(['TC-02 torch-tap wall at FA1S (R4-01)', 'Value'], rows, widths=['30%', '70%'], cls='tight',
                    caption=f'Tap wall v3 (TAPW {esc(src_label(ctx, "TAPW"))}); R4-01 CLOSED in CHANGELOG 259 (1).'))
    rows = [['Z3 v2 (ruled)', tvtxt(ctx.v('TB70', '/Z3_v2_text', tag='LEAD'), 1500)],
            ['J-FWD replace rule on Q_JFWD', tvtxt(ctx.v('TB70', '/jfwd_rule_v2_text', tag='LEAD'), 1500)],
            ['F4 TB-state abort set', tvtxt(ctx.v('TB70', '/F4_abort_set/verdict', tag='CALC'), 700)],
            ['Status', tvtxt(ctx.v('TB70', '/status', tag='CALC'), 500)]]
    o.append(dtable(['LC-TB70 envelope v2', 'Text (quoted)'], rows, widths=['22%', '78%'], cls='tight',
                    caption=f'LC-TB70 envelope v2 (TB70 {esc(src_label(ctx, "TB70"))}); ruled in CHANGELOG 258 (3).'))


def sec_fea(ctx, doc, a, D):
    o = [doc.h(1, '9 Structural analysis: 3D FEA of the assembled engine (CAD v3.5.2)')]
    o.append(note_box(f'<b>{esc(PAGE_STATEMENT)}.</b> Every margin below is a model result (SIM), a hand calculation on model loads (CALC) or a value derived '
                      'from them (DERIVED). Negatives are shown as found. ' + inl(md_line_starting(ctx, 'F3D', 'Delivered by', 'DERIVED',
                                                                                                  tag_raw='FEA3D-2 report §0 checkpoint')), 'warn'))
    o.append(doc.h(2, '9.1 Model, loads and status'))
    rows = []
    for k in ('Status', 'Author', 'Configuration', 'Tool', 'Units', 'Tags'):
        tv = md_find(ctx, 'F3D', 'REPORT FEA3D v3.5.2', {0: k}, 1, ev='DERIVED', tag_raw='FEA3D-2 report header table')
        rows.append([k, tvtxt(tv, 900)])
    rows.append(['Independent review', tvtxt(D['cl'].item(262, 3))])
    rows.append(['Margin matrix of record', cat(md_line_starting(ctx, 'MMXMD', 'Cell = MS_y', 'DERIVED', tag_raw=MX_TAG), Cell('', []))])
    rows.append(['Matrix delta vs the FEA3D-2 table', cat(tvtxt(ctx.v('MMXD', '/why', tag='DERIVED', tag_ptr='/tag'), 600))])
    o.append(dtable(['Item', 'Value'], rows, widths=['18%', '82%'], cls='tight',
                    caption=f'FEA3D v3.5.2 report header (F3D {esc(src_label(ctx, "F3D"))}) and the rows-v8 matrix of record.'))
    o.append(doc.h(3, '9.1.1 Mesh convergence status'))
    rows = [['Seat-line P+Q (J-FWD)', tvtxt(md_line_starting(ctx, 'F3D', 'MF note', 'SIM', tag_raw='FEA3D-2 report §5.3 MF note', after_heading='5. Mesh convergence'))],
            ['Check cD (finer mesh, FINAL TC-01)', tvtxt(D['cl'].item(252, 1))],
            ['Ruling on cD', tvtxt(D['cl'].item(250, 10), 900)]]
    o.append(dtable(['Point', 'Status (quoted)'], rows, widths=['22%', '78%'], cls='tight',
                    caption='The seat-line P+Q is NOT shown mesh-converged; s6 + C1 stand in every state (CHANGELOG 250 (10), 252 (1)).'))
    sec_fea_matrix(ctx, doc, a, D, o)
    sec_fea_negatives(ctx, doc, a, D, o)
    sec_fea_named(ctx, doc, a, D, o)
    sec_fea_jfwd(ctx, doc, a, D, o)
    sec_fea_mount(ctx, doc, a, D, o)
    sec_fea_stiff(ctx, doc, a, D, o)
    sec_fea_f4(ctx, doc, a, D, o)
    sec_fea_followups(ctx, doc, a, D, o)
    o.append(doc.h(2, '9.10 FEA3D-2 open items and owners'))
    rows = []
    for ln, r in md_rows_where(ctx, 'F3D', '13. Open items and owners'):
        lab = re.sub(r'\*\*', '', r[0]).strip()
        rows.append([Cell(f'<b>{esc(lab)}</b>', [])] + [tvtxt(md_cell_ln(ctx, 'F3D', ln, r, j, ev, tag_raw='FEA3D-2 report §13 open items'), 420)
                                                      for j, ev in ((1, 'DERIVED'), (2, 'SIM'), (3, 'LEAD'), (4, 'DERIVED'))])
    o.append(dtable(['#', 'Item', 'Status / numbers', 'Owner', 'Closure'], rows, cls='tight', widths=['4%', '20%', '40%', '14%', '22%'],
                    caption='FEA3D-2 §13 as published (05:45Z). Item 2 quotes +0.301 for the HW-101 cell: the rows-v8 matrix of record gives +0.278 (§9.5.3; '
                            'contradiction register §13.3).'))
    o.append(doc.h(2, '9.11 Not run, superseded, and runs that wait for the lead'))
    L = (ctx.src('F3D').text or '').splitlines()
    on, items = False, []
    for i, ln in enumerate(L, 1):
        if ln.startswith('## '):
            on = ln.startswith('## 11. Not run')
            continue
        if on and ln.startswith('- '):
            items.append(ctx.t('F3D', f'§11 line {i}', ln[2:].strip(), 'DERIVED', tag_raw='FEA3D-2 report §11'))
    o.append(dtable(['Item (quoted)'], [[tvtxt(t, 700)] for t in items], label_cols=0, cls='tight', widths=['100%'],
                    caption='FEA3D-2 §11: nothing in this list is a margin.'))
    return '\n'.join(o)


# ---------------------------------------------------------------------------------------------
# section 7 (v0.3.0): combustion, sequences, purge, abort set, FA-1 rulings, tests
# ---------------------------------------------------------------------------------------------
def sec_combustion(ctx, doc, a, D):
    cl = D['cl']
    o = [doc.h(1, '7 Combustion, sequences and the abort set')]
    if ctx.ovr and any(e['status'] == 'ACTIVE' for e in ctx.ovr.entries):
        o.append(note_box(f'<b>Reading this section.</b> combustion.json {esc(ctx.src("CMB").version or "")} is the source of every value here unless a row names '
                          'another source. Where a quoted text still carries wording that a newer lead decision replaced, the old words are '
                          '<del class="stale">struck through</del> and the decision is <ins class="dec">inserted</ins> with its override id (§13.1).', 'info'))
    o.append(doc.h(2, '7.1 Design point'))
    rows = [
        ['Fuel', tvtxt(ctx.v('CMB', '/decisions/fuel'))],
        ['Oxidiser load and tank volume', cat(ctx.v('CMB', '/decisions/N2O_load_and_tank/v/m_N2O_kg', 'kg', tag_ptr='/decisions/N2O_load_and_tank').h('.2f'), ' in ',
                                              ctx.v('CMB', '/decisions/N2O_load_and_tank/v/V_tank_m3', 'L', conv=(1000, 0, 'm³ to L'), tag_ptr='/decisions/N2O_load_and_tank').h('.2f'), Cell('', ctx.recent[-2:]))],
        ['Tank conditioning', tvtxt(ctx.v('CMB', '/decisions/tank_pressurisation'), 400)],
        ['Ignition interlock guard band', tvtxt(ctx.v('CMB', '/interlock_guard_band/v/thresholds', tag_ptr='/interlock_guard_band'), 300)],
        ['Model basis', tvtxt(ctx.v('CMB', '/operating_points/basis', tag='SIM'), 300)],
        ['Combustion and nozzle efficiencies η<sub>c*</sub> / η<sub>cf</sub>', cat(rx(ctx, 'CMB', '/operating_points/basis', r'eta_c\* ([\d.]+)', tag='ASSUMED').h('.3f'), ' / ',
                                                                                   rx(ctx, 'CMB', '/operating_points/basis', r'eta_cf ([\d.]+)', tag='ASSUMED').h('.3f'), Cell('', ctx.recent[-2:]))],
        ['Oxidiser flux at the head, rated, initial port', num_cell(ctx.v('CMB', '/operating_points/max_thrust/G_ox_initial_kg_m2s', 'kg/(m²·s)'), '.0f')],
        ['Regression law (form)', tvtxt(ctx.v('CMB', '/gas_path/grain/regression_law/form', tag='ASSUMED'))],
        ['Regression coefficient a / exponent n', cat(ctx.v('CMB', '/gas_path/grain/regression_law/a', 'm/s·(kg/m²s)^-n').h('.3e'), ' / ', ctx.v('CMB', '/gas_path/grain/regression_law/n').h('.2f'), Cell('', ctx.recent[-2:]))],
        ['Regression law note', tvtxt(ctx.v('CMB', '/gas_path/grain/regression_law/note', tag='ASSUMED'), 300)],
        ['MEOP basis (SIM)', tvtxt(ctx.v('CMB', '/meop_basis_v2p4'), 300)],
        ['Stored energy (flight tank)', tvtxt(ctx.v('CMB', '/stored_energy/v/flight_tank_20C', tag_ptr='/stored_energy'), 200)],
    ]
    o.append(dtable(['Item', 'Value'], rows, widths=['32%', '68%']))

    o.append(doc.h(2, '7.2 Fuel grain'))
    G = '/gas_path/grain'
    segs = [D['bom_by_pn'].get('ENG-GR-01'), D['bom_by_pn'].get('ENG-GR-02')]
    seg_len = []
    for pn in ('ENG-GR-01', 'ENG-GR-02'):
        lo, hi, n = manifest_extent(ctx, pn_prefix=pn + '#')
        seg_len.append(man_tv(ctx, (hi[2] - lo[2]) if n else None, f'z extent of {pn}', pn_prefix=pn + '#'))
    rows = [
        ['Segments (BOM)', cat(*[Cell(f'{esc(r.l.get("name", ""))} {r.row_tv.ref()}<br>', [r.row_tv]) for r in segs if r])],
        ['Segment length from the CAD manifest (GR-01 / GR-02)', cat(seg_len[0].h('.1f'), ' / ', seg_len[1].h('.1f'))],
        ['Grain outer diameter / total length', cat(ctx.v('CMB', f'{G}/outer_diameter_m', 'mm', conv=(1000, 0, 'm to mm')).h('.1f'), ' / ',
                                                   ctx.v('CMB', f'{G}/length_m', 'mm', conv=(1000, 0, 'm to mm')).h('.1f'), Cell('', ctx.recent[-2:]))],
        ['Port', cat(ctx.v('CMB', f'{G}/port/type').h(), ', initial Ø ', ctx.v('CMB', f'{G}/port/initial_diameter_m', 'mm', conv=(1000, 0, 'm to mm')).h('.1f'), Cell('', ctx.recent[-2:]))],
        ['Initial web', num_cell(ctx.v('CMB', f'{G}/port/initial_web_m', 'mm', conv=(1000, 0, 'm to mm')), '.2f')],
        ['Port entrance (decided)', tvtxt(cl.item(160, 4), 400)],
        ['Density (printed ABS)', num_cell(ctx.v('CMB', f'{G}/density_kg_m3', 'kg/m³'), '.0f')],
        ['Grain mass: Combustion / CAD', cat(ctx.v('CMB', f'{G}/mass_kg', 'kg').h('.3f'), ' / ', ctx.v('MP', '/grain_mass_wet_kg', 'kg', tag='DERIVED').h('.4f'), Cell('', ctx.recent[-2:]))],
        ['Residual web rule', tvtxt(ctx.v('CMB', f'{G}/residual_web_rule'))],
        ['Retention', tvtxt(ctx.v('CMB', f'{G}/retention', tag='DESIGN'), 300)],
    ]
    o.append(dtable(['Item', 'Value'], rows, widths=['32%', '68%']))

    o.append(doc.h(2, '7.3 Injector, feed and igniter'))
    V = '/valves_and_actuators'
    I = '/igniter'
    ts = f'{I}/torch_sizing'
    el = f'{I}/electrical'
    igm = ctx.v('CMB', f'{I}/mass_kg', 'kg')
    ig_bom = D['bom_by_pn'].get('ENG-IG-01')
    rows = [
        ['Feed architecture', tvtxt(ctx.v('CMB', f'{V}/architecture', tag='DESIGN'), 400)],
        ['Injector flow model', tvtxt(ctx.v('CMB', '/gas_path/injector/flow_model', tag='LITERATURE'))],
        ['Filter', tvtxt(ctx.v('CMB', '/gas_path/injector/filter'))],
        ['Isolation valve: minimum Cv / MEOP / closing time', cat(ctx.v('CMB', f'{V}/isolation_valve/Cv_min').h('.1f'), ' / ',
                                                                  Cell(pres(ctx, ctx.v('CMB', f'{V}/isolation_valve/MEOP_Pa', 'Pa')), [ctx.recent[-1]]), ' / ',
                                                                  ctx.v('CMB', f'{V}/isolation_valve/close_time_max_s', 's').h('.2f'), Cell('', [ctx.recent[-1], ctx.recent[-3]]))],
        ['Relief: trapped liquid, back-relief and tank', tvtxt(ctx.v('CMB', f'{V}/isolation_valve/trapped_liquid_relief'))],
        ['Tank relief (v2.4a)', tvtxt(ctx.v('CMB', '/relief_v2p4a'), 400)],
        ['Hose across the gimbal', tvtxt(ctx.v('CMB', f'{V}/hose', tag='DERIVED'), 300)],
        ['Pc tap and sense line', cat(tvtxt(ctx.v('CMB', '/gas_path/pc_tap/location', tag='DESIGN')), '<br>', tvtxt(ctx.v('CMB', '/gas_path/pc_tap/sense_line')))],
        ['Igniter type', tvtxt(ctx.v('CMB', f'{I}/type', tag='DESIGN'))],
        ['Torch chamber pressure / O/F / throat diameter', cat(ctx.v('CMB', f'{ts}/v/Pc_torch_bar', 'bar', tag='DERIVED', tag_ptr=ts).h('.1f'), ' / ',
                                                               ctx.v('CMB', f'{ts}/v/OF', tag='DERIVED', tag_ptr=ts).h('.1f'), ' / ',
                                                               ctx.v('CMB', f'{ts}/v/throat_d_m', 'mm', conv=(1000, 0, 'm to mm'), tag='DERIVED', tag_ptr=ts).h('.1f'), Cell('', ctx.recent[-3:]))],
        ['Torch flows N2O / propane', cat(ctx.v('CMB', f'{ts}/v/mdot_n2o_kg_s', 'g/s', conv=(1000, 0, 'kg/s to g/s'), tag='DERIVED', tag_ptr=ts).h('.3f'), ' / ',
                                          ctx.v('CMB', f'{ts}/v/mdot_propane_kg_s', 'g/s', conv=(1000, 0, 'kg/s to g/s'), tag='DERIVED', tag_ptr=ts).h('.3f'), Cell('', ctx.recent[-2:]))],
        ['Spark: supply / energy / rate', cat(ctx.v('CMB', f'{el}/v/spark_supply_V', 'V', tag_ptr=el).h('.0f'), ' / ', ctx.v('CMB', f'{el}/v/spark_energy_J', 'J', tag_ptr=el).h('.2f'), ' / ',
                                              ctx.v('CMB', f'{el}/v/rate_Hz', 'Hz', tag_ptr=el).h('.0f'), Cell('', ctx.recent[-3:]))],
        ['Igniter system mass: Combustion / BOM ENG-IG-01', cat(igm.h('.2f'), ' / ', ig_bom.mass_tv.h('.3f') if ig_bom else 'MISSING', Cell('', [igm] + ([ig_bom.mass_tv] if ig_bom else [])))],
        ['Starts per flight', tvtxt(ctx.v('CMB', f'{I}/starts_per_flight'))],
        ['Light windows W from the lift command', cat(ctx.v('CMB', '/light_windows/v/flight_first_start', 's', tag_ptr='/light_windows').h('.2f'), ' first start · ',
                                                      ctx.v('CMB', '/light_windows/v/flight_relight', 's', tag_ptr='/light_windows').h('.2f'), ' relight · ',
                                                      ctx.v('CMB', '/light_windows/v/stand', 's', tag_ptr='/light_windows').h('.2f'), ' stand')],
    ]
    o.append(dtable(['Item', 'Value'], rows, widths=['32%', '68%']))

    o.append(doc.h(2, '7.4 Start and relight sequence'))
    SQ = f'{I}/sequence/v'
    seq = ctx.raw('CMB', SQ + '/start', default=[]) or []
    rows = []
    for k, e in enumerate(seq):
        ep = ctx.v('CMB', f'{SQ}/start/{k}/epoch', tag='LEAD', tag_ptr=f'{I}/sequence')
        tt = ctx.v('CMB', f'{SQ}/start/{k}/t_s', 's', tag='LEAD', tag_ptr=f'{I}/sequence')
        ac = ctx.v('CMB', f'{SQ}/start/{k}/action', tag='LEAD', tag_ptr=f'{I}/sequence')
        rows.append([Cell(f'<b>{esc(ep.value)}</b>', [ep]), num_cell(tt, '.3f') if tt.value is not None else Cell('—', [tt]), tvtxt(ac, 1600)])
    o.append(dtable(['Epoch', 't [s]', 'Action'], rows, label_cols=0, widths=['12%', '8%', '80%'], cls='tight',
                    caption=f'Start and relight sequence (combustion.json {esc(ctx.src("CMB").version or "")} /igniter/sequence; times relative to E0 where the source states one).'))
    F = '/igniter_sequence_fields_v2p4c/v/fields'
    fl = ctx.raw('CMB', F, default=[]) or []
    rows = []
    for k, f in enumerate(fl):
        tv = ctx.v('CMB', f'{F}/{k}', f.get('unit', ''))
        val = tv.value
        vs = (', '.join(f'{x:g}' for x in val) if isinstance(val, list) and all(isinstance(x, (int, float)) for x in val) else
              (f'{val:g}' if isinstance(val, (int, float)) and not isinstance(val, bool) else str(val)))
        rows.append([Cell(f'<span class="mono small">{esc(f.get("id", ""))}</span>', []),
                     Cell(f'<span class="v">{esc(vs)}</span><span class="u">&#8239;{esc(f.get("unit", ""))}</span> {tv.pill()}{tv.ref()}', [tv]),
                     tvtxt(ctx.v('CMB', f'{F}/{k}/src', tag='DESIGN'), 160)])
    o.append(dtable(['Field', 'Value', 'Source (as written)'], rows, widths=['30%', '26%', '44%'], cls='tight',
                    caption='One field per value (combustion.json /igniter_sequence_fields_v2p4c, the generated-table input for Electronics); the pill is each field\'s own tag.'))
    rows = []
    for lab, key in (('ARM preconditions', 'arm_preconditions'), ('Relight', 'relight'), ('Shutdown', 'shutdown'), ('Abort if no ignition', 'abort_if_no_ignition')):
        items = ctx.raw('CMB', f'{SQ}/{key}', default=[]) or []
        for j, _ in enumerate(items):
            tv = ctx.v('CMB', f'{SQ}/{key}/{j}', tag='LEAD', tag_ptr=f'{I}/sequence')
            rows.append([lab if j == 0 else '', tvtxt(tv, 700)])
    o.append(dtable(['Phase', 'Rule'], rows, widths=['18%', '82%'], cls='tight'))
    o.append(note_box('<b>Stand safing after a no-light.</b> ' + tvtxt(ctx.v('CMB', '/stand_safing_v2p4a', tag_ptr='/stand_safing_v2p4a'), 500).html, 'info'))

    o.append(doc.h(2, '7.5 Relight purge (decided schedule and conditions)'))
    P = '/purge_decision_v2p4c/v'
    rows = [['Commit rule', tvtxt(ctx.v('CMB', '/purge_commit_rule_v2p4b/v/rule', tag_ptr='/purge_commit_rule_v2p4b'), 400)],
            ['Decision', tvtxt(ctx.v('CMB', f'{P}/decision', tag_ptr='/purge_decision_v2p4c'), 400)],
            ['Scheduled flow / both-open overlap / both-open cap / flow at the cap',
             cat(ctx.v('CMB', f'{P}/flow_s', 's', tag_ptr='/purge_decision_v2p4c').h('.2f'), ' / ', ctx.v('CMB', f'{P}/both_open_overlap_s', 's', tag_ptr='/purge_decision_v2p4c').h('.2f'), ' / ',
                 ctx.v('CMB', f'{P}/cap_both_open_s', 's', tag_ptr='/purge_decision_v2p4c').h('.2f'), ' / ', ctx.v('CMB', f'{P}/flow_at_cap_s', 's', tag_ptr='/purge_decision_v2p4c').h('.2f'))],
            ['Needed flow, unlined line (283.15 / 289.5 / 297.15 K)', tvtxt(ctx.v('CMB', f'{P}/needed_flow_unlined_s', 's', tag='DERIVED'))],
            ['Margins at 2.43 s, unlined', tvtxt(ctx.v('CMB', f'{P}/margins_at_2p43s_unlined_s', 's', tag='DERIVED'))],
            ['Vented N2O bound (law) at 2.43 s', tvtxt(ctx.v('CMB', f'{P}/vented_N2O_bound_law_g', 'g', tag='DERIVED'))],
            ['Vented N2O at Cd 0.80, fixed schedule', cat(tvtxt(ctx.v('CMB', f'{P}/vented_N2O_Cd0p80_fixed_schedule_g', 'g', tag='ESTIMATE')), '<br>',
                                                         tvtxt(ctx.v('CMB', f'{P}/vented_N2O_Cd0p80_tag', tag='ESTIMATE'), 300))],
            ['A1 reserve test (REV-GNC-7)', tvtxt(ctx.v('CMB', f'{P}/a1_reserve_test_REV_GNC_7', tag='DERIVED'), 500)],
            ['Condition (a), LEAD 256 (2)', tvtxt(ctx.v('CMB', f'{P}/conditions_LEAD_256_2/a', tag='LEAD'))],
            ['Condition (b), LEAD 256 (2)', tvtxt(ctx.v('CMB', f'{P}/conditions_LEAD_256_2/b', tag='LEAD'))],
            ['Condition (c), LEAD 256 (2)', tvtxt(ctx.v('CMB', f'{P}/conditions_LEAD_256_2/c', tag='LEAD'))],
            ['Condition (d), LEAD 257 (2)', tvtxt(ctx.v('CMB', f'{P}/condition_d_LEAD_257_2', tag='LEAD'), 1400)],
            ['Condition (d1), LEAD 258 (2)', tvtxt(ctx.v('CMB', f'{P}/conditions_LEAD_258_2/d1', tag='LEAD'), 600)],
            ['Condition (d2), LEAD 258 (2)', tvtxt(ctx.v('CMB', f'{P}/conditions_LEAD_258_2/d2', tag='LEAD'), 600)],
            ['PURGE command time (open)', tvtxt(ctx.v('CMB', f'{P}/PURGE_command_time', tag='DERIVED'), 400)],
            ['CF-4', tvtxt(ctx.v('CMB', f'{P}/CF4', tag='LEAD'), 500)],
            ['Electronics constants', tvtxt(ctx.v('CMB', f'{P}/electronics', tag='DESIGN'), 500)],
            ['Vented-mass reserve', tvtxt(ctx.v('CMB', f'{P}/reserve', tag='LEAD'), 500)]]
    o.append(dtable(['Item', 'Value'], rows, widths=['28%', '72%'], cls='tight',
                    caption='combustion.json /purge_decision_v2p4c (decided by LEAD 253 (7)(ii), final in 256 (2); conditions 256 (2), 257 (2), 258 (2)). '
                            'The v2.4b records were run with 2.5 s of flow (the analysed basis, more flow than decided).'))

    o.append(doc.h(2, '7.6 Abort set (Combustion matrix; firmware causes in §10.5)'))
    cm = '/abort_matrix_v2p4/v'
    rows = []
    for k in (ctx.raw('CMB', cm, default={}) or {}):
        if k.endswith('_superseded'):
            continue
        rows.append([Cell(f'<b>{esc(k)}</b>', []), tvtxt(ctx.v('CMB', ptr_join('abort_matrix_v2p4', 'v', k), tag_ptr='/abort_matrix_v2p4'), 700)])
    o.append(dtable(['ID', 'Combustion abort matrix (as published)'], rows, widths=['14%', '86%'], cls='tight',
                    caption=f'combustion.json /abort_matrix_v2p4 ({esc(str(ctx.raw("CMB", "/abort_matrix_v2p4/tag", default="")))}). The F4 PC_SENSOR HIGH abort and the '
                            'Q_JFWD logging are routed to Electronics v2.12 (LEAD 258 (4)): PENDING.'))
    o.append(note_box(f'<b>Abort action (firmware v2.11, SIL only).</b> {tvtxt(ctx.v("ELE", "/abort_matrix/actions", tag="LEAD"), 600).html}', 'info'))

    o.append(doc.h(2, '7.7 FA-1 hard start: rulings of record'))
    Z = '/z3_jfwd_rulings_v2p4d/v'
    rows = [subrow('Z3 v2 (FA-1 class; LEAD 258 (3))', 2)]
    rows += [[esc(k.replace('_', ' ')), tvtxt(ctx.v('CMB', f'{Z}/Z3_v2/{k}', tag_ptr='/z3_jfwd_rulings_v2p4d'), 800)] for k in ('decision', 'grid', 'flight', 'not_adopted')]
    rows.append(subrow('J-FWD replace rule on Q_JFWD (LEAD 258 (3))', 2))
    rows += [[esc(k.replace('_', ' ')), tvtxt(ctx.v('CMB', f'{Z}/jfwd_replace_rule/{k}', tag_ptr='/z3_jfwd_rulings_v2p4d'), 800)]
             for k in ('decision', 'grid', 'why', 'normal_lights', 'measured_traces', 'basis', 'band', 'replaces', 'electronics')]
    rows.append(subrow('Open before flight acceptance (LEAD 258 (3))', 2))
    ob = ctx.raw('CMB', f'{Z}/open_before_flight_acceptance', default=[]) or []
    rows += [[f'open item {j + 1}', tvtxt(ctx.v('CMB', f'{Z}/open_before_flight_acceptance/{j}', tag='TO-VERIFY'), 400)] for j in range(len(ob))]
    rows.append(subrow('Torch passage pressure and the J-FWD rows', 2))
    rows.append(['P_torch design case (FA1S)', tvtxt(ctx.v('CMB', '/fa1_p_torch_v2p4c/v/design_case', tag='LEAD'), 600)])
    rows.append(['Mechanical row (tap wall v3)', tvtxt(ctx.v('CMB', '/fa1_p_torch_v2p4c/v/mechanical_row', tag='CALC'), 600)])
    rows.append(['Grid statistics status', tvtxt(ctx.v('CMB', '/fa1_grid_statistics_v2p4c/v/status', tag='LEAD'), 400)])
    rows.append(['Combustion side', tvtxt(ctx.v('CMB', f'{Z}/combustion_side', tag_ptr='/z3_jfwd_rulings_v2p4d'), 500)])
    o.append(dtable(['Item', 'Value (quoted)'], rows, widths=['22%', '78%'], cls='tight',
                    caption='combustion.json /z3_jfwd_rulings_v2p4d and /fa1_p_torch_v2p4c. Grid counts are on an ASSUMED construct, not probabilities. '
                            'The FA-1 pressure spectrum is in §2.4; the J-FWD criterion rows in §9.5.'))

    o.append(doc.h(2, '7.8 Stability'))
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

    o.append(doc.h(2, '7.9 Test specifications: CF-4 and T1-T4'))
    rows = [['CF-4 claim', tvtxt(ctx.v('CMB', '/cf4_gate/v/claim', tag='LEAD', tag_ptr='/cf4_gate'))],
            ['CF-4 specification', tvtxt(ctx.v('CMB', '/cf4_gate/spec_version', tag='DESIGN'))]]
    pcs = ctx.raw('CMB', '/cf4_gate/v/pass_criteria', default=[]) or []
    for k, _ in enumerate(pcs):
        rows.append([f'CF-4 pass criterion {k + 1}', tvtxt(ctx.v('CMB', f'/cf4_gate/v/pass_criteria/{k}', tag='LEAD', tag_ptr='/cf4_gate'), 600)])
    rows.append(['T1-T4 law rule', tvtxt(ctx.v('CMB', '/t1t4_law_v2/v/rule', tag_ptr='/t1t4_law_v2'), 400)])
    rows.append(['T1-T4 specification', tvtxt(md_heading(ctx, 'T14', 'T1-T4', 'DESIGN', tag_raw='document heading'), 200)])
    rows.append(['T4 duration (N-07) and re-size', tvtxt(ctx.v('CMB', '/t4_duration_note_v2p4c/v/status', tag='LEAD'), 900)])
    rows.append(['T4 decision (CHANGELOG 261 (2))', tvtxt(cl.item(261, 2), 900)])
    rows.append(['Test budgets', tvtxt(ctx.v('CMB', '/test_budgets_v2p4b', tag_ptr='/test_budgets_v2p4b'), 500)])
    o.append(dtable(['Item', 'Value (quoted)'], rows, widths=['24%', '76%'], cls='tight',
                    caption='Physical tests are run by the founders; none has been run. The T4 rows of T1-T4 v3.2 stay the DC-D computation [SIM] until Combustion re-runs them (OPEN).'))
    return '\n'.join(o)


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


# ---------------------------------------------------------------------------------------------
# sections 10-11 (v0.3.0): electronics (electronics.json v4, firmware v2.11 SIL), mission (GNC v3.2)
# ---------------------------------------------------------------------------------------------
def thr_cells(ctx, sid, base, th):
    out = []
    for kk in (th or {}):
        ptr = ptr_join(*[x for x in base.strip('/').split('/') if x], kk)
        node = ctx.raw(sid, ptr, default=None)
        raw = node.get('tag') if isinstance(node, dict) else None
        t = ctx.v(sid, ptr, tag='DESIGN' if (raw is not None and normalise_tag(raw) is None) else None)
        out.append(Cell(f'<div class="small">{esc(kk)} = {t.h()}</div>', [t]))
    return out


def sec_electronics(ctx, doc, a, D):
    o = [doc.h(1, '10 Electronics and control')]
    cl = D['cl']
    E = 'ELE'
    pend = {lab: tv for lab, tv in D['pending']}
    o.append(note_box('<b>electronics.json v4 (firmware v2.11, SIL only) is the published interface and the source of record of this section.</b> '
                      + inl(cl.item(253, 5)) + ' <b>PENDING:</b> ' + ' '.join(inl(tv) for tv in pend.values())
                      + ' <b>Lead rulings on the v2.12 handback (CHANGELOG 264, §10.8):</b> they decide the C1 thermal zero (R3-01, option (b)), the A1 BASE_AMB outcome, '
                      'the P_torch transducer, the T4 relight and the A1 flight T0 range; the v2.12 firmware and the v4.1 values that implement them are PENDING REVIEW '
                      '(REV-ELEC-4) and are not shown as values here.', 'warn'))
    o.append(doc.h(2, '10.1 Engine control unit and firmware'))
    rows = [
        ['Interface status', tvtxt(ctx.v(E, '/status', tag='DESIGN'), 900)],
        ['Architecture', tvtxt(ctx.v(E, '/ecu/architecture'))],
        ['Microcontroller', tvtxt(ctx.v(E, '/ecu/mcu', tag='DESIGN'), 300)],
        ['PCB outline / enclosure reservation', cat(ctx.v(E, '/ecu/pcb_outline_mm', 'mm', tag_default='DESIGN').h(), ' / ', ctx.v(E, '/ecu/enclosure_envelope_mm', 'mm', tag_default='DESIGN').h())],
        ['ECU mass', tvtxt(ctx.v(E, '/ecu/mass_kg', 'kg', tag_default='ASSUMED'), 300)],
        ['Schematic', tvtxt(ctx.v(E, '/ecu/schematic', tag='DESIGN'), 500)],
        ['Firmware version', tvtxt(ctx.v(E, '/firmware/version', tag='DESIGN'))],
        ['Firmware target', tvtxt(ctx.v(E, '/firmware/target', tag='TO-VERIFY'), 400)],
        ['Firmware unit tests', tvtxt(ctx.v(E, '/firmware/unit_tests', tag='SIM'), 400)],
        ['SIL record v2.11', tvtxt(ctx.v(E, '/firmware/sil_record_v2p11', tag='SIM'), 400)],
        ['CAN link', tvtxt(ctx.v(E, '/can_interface/physical'), 240)],
        ['Change summary v3 to v4', tvtxt(ctx.v(E, '/change_summary_v3_to_v4/0', tag='DESIGN'), 300)],
    ]
    o.append(dtable(['Item', 'Value'], rows, widths=['26%', '74%'], cls='tight'))
    o.append(doc.h(2, '10.2 Sensors'))
    PT = '/sensors/pressure_transducers'
    TC = '/sensors/thermocouples'
    rows = [
        ['Pressure transducers (selection, electronics.json v4)', tvtxt(ctx.v(E, f'{PT}/selection'), 500)],
        ['P_torch transducer: lead 264 (4) supersedes the v4 selection', ptorch_cell(ctx, D)],
        ['Hardware over-pressure comparator', tvtxt(ctx.v(E, f'{PT}/hw_ovp'), 300)],
        ['Coast re-zero', tvtxt(ctx.v(E, f'{PT}/coast_rezero', tag_default='DESIGN'), 400)],
        ['Thermocouple channels', tvtxt(ctx.v(E, f'{TC}/channels', tag='DESIGN'), 500)],
        ['Case abort / relight refusal', cat(Cell(temp_k(ctx.v(E, f'{TC}/case_abort', 'K'), 2), [ctx.recent[-1]]), ' / ',
                                             Cell(temp_k(ctx.v(E, f'{TC}/relight_refusal', 'K'), 2), [ctx.recent[-1]]))],
        ['Case abort rule', tvtxt(ctx.v(E, f'{TC}/case_abort_rule', tag_default='LEAD'), 500)],
        ['Persistence', tvtxt(ctx.v(E, f'{TC}/persistence', tag_default='DESIGN'), 200)],
        ['Start and ARM limit / stand ARM maximum', cat(tvtxt(ctx.v(E, f'{TC}/start_and_arm_limit', tag_default='LEAD'), 200), '<br>', tvtxt(ctx.v(E, f'{TC}/stand_arm_max', tag_default='LEAD'), 200))],
        ['Nozzle-holder limit', tvtxt(ctx.v(E, f'{TC}/nozzle_holder_limit', tag_default='ASSUMED'), 200)],
        ['Photodiode', tvtxt(ctx.v(E, '/sensors/photodiode', tag='DESIGN'), 300)],
        ['Encoders', tvtxt(ctx.v(E, '/sensors/encoders', tag='DESIGN'), 200)],
        ['Stand dynamic Pc channel', tvtxt(ctx.v(E, '/sensors/stand_dynamic_pc', tag='DESIGN'), 300)],
    ]
    o.append(dtable(['Item', 'Value'], rows, widths=['26%', '74%'], cls='tight'))
    o.append(doc.h(2, '10.3 Limits of firmware v2.11'))
    lims = ctx.raw(E, '/limits_v2p11', default=[]) or []
    rows = []
    for k, l in enumerate(lims):
        b = f'/limits_v2p11/{k}'
        val = ctx.v(E, b + '/value', (l.get('value') or {}).get('unit', '') if isinstance(l.get('value'), dict) else '', tag_default='DESIGN')
        rows.append([Cell(f'<b>{esc(l.get("limit", ""))}</b>', []), tvtxt(val, 200), tvtxt(ctx.v(E, b + '/basis', tag='DERIVED'), 500)])
    o.append(dtable(['Limit', 'Value', 'Basis (quoted)'], rows, widths=['24%', '22%', '54%'], cls='tight',
                    caption='electronics.json /limits_v2p11. Values are firmware constants (config.h), SIL only.'))
    o.append(doc.h(2, '10.4 Light rule and start monitors'))
    LR = '/light_rule'
    rows = [['Light rule', tvtxt(ctx.v(E, f'{LR}/rule'), 900)]]
    for kk in ('kIgnRise_Pa', 'kIgnConfirmRelN', 'kIgnPreN', 'kIgnResidual_Pa', 'kIgnBaseCheck_Pa', 'kIgnFloorAbs_Pa'):
        rows.append([esc(kk), tvtxt(ctx.v(E, f'{LR}/{kk}', tag_default='DESIGN'), 300)])
    for kk in ('A3', 'A7', 'E3', 'A7_flight_blank', 'light_spike_record'):
        rows.append([f'Start monitor {esc(kk)}', tvtxt(ctx.v(E, f'/start_monitors/{kk}', tag_default='DESIGN'), 500)])
    o.append(dtable(['Item', 'Value'], rows, widths=['24%', '76%'], cls='tight'))
    o.append(doc.h(2, '10.5 Abort and refusal causes (firmware v2.11)'))
    cs = ctx.raw(E, '/abort_matrix/causes', default=[]) or []
    rows = []
    for k, c in enumerate(cs):
        b = f'/abort_matrix/causes/{k}'
        code = ctx.v(E, b + '/code', tag='DESIGN')
        cause = ctx.v(E, b + '/cause', tag='DESIGN')
        trig = ctx.v(E, b + '/trigger', tag='DESIGN')
        th = thr_cells(ctx, E, b + '/thresholds', c.get('thresholds'))
        rows.append([Cell(f'{esc(code.num())}{code.ref()}', [code]), Cell(f'<b>{esc(cause.value)}</b>{cause.ref()}', [cause]), tvtxt(trig, 260),
                     cat(*th) if th else Cell('<span class="small">no threshold</span>', [trig])])
    o.append(dtable(['Code', 'Cause', 'Trigger', 'Thresholds'], rows, label_cols=0, cls='abort tight',
                    widths=['6%', '16%', '44%', '34%'], caption=f'{len(cs)} causes in electronics.json /abort_matrix/causes (SIL only; no hardware).'))
    o.append(doc.h(2, '10.6 Power, head-end bleed provision and fail-safe states'))
    PB = '/power_budget'
    rows = [['Battery', tvtxt(ctx.v(E, f'{PB}/battery', tag='DESIGN'))],
            ['Logic power, typical / peak', tvtxt(ctx.v(E, f'{PB}/logic_W', 'W'))],
            ['Energy per flight day', num_cell(ctx.v(E, f'{PB}/flight_day_Wh', 'Wh'), '.2f')],
            ['Energy per static-fire session', num_cell(ctx.v(E, f'{PB}/static_fire_session_Wh', 'Wh'), '.2f')],
            ['Peak current', tvtxt(ctx.v(E, f'{PB}/peak_current_A', 'A'), 200)],
            ['Minimum voltage at the ECU', tvtxt(ctx.v(E, f'{PB}/min_voltage_at_ECU_V', 'V'), 200)],
            ['Fusing', tvtxt(ctx.v(E, f'{PB}/fusing', tag='DESIGN'), 300)]]
    HB = '/head_end_bleed_provision'
    for kk in ('architecture', 'schedule', 'closure_rule', 'cap_decision_230_3', 'hardware_both_open_timer', 'pad_bit'):
        rows.append([esc('bleed: ' + kk.replace('_', ' ')), tvtxt(ctx.v(E, f'{HB}/{kk}', tag_default='DESIGN'), 500)])
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
        rows.append([esc(kk.replace('_', ' ')), tvtxt(ctx.v(E, ptr_join('lead_rulings_v2p11', kk), tag='LEAD'), 500)])
    rows.append(['Routed to v2.12 (LEAD 258 (4))', tvtxt(cl.item(258, 4), 600)])
    rows.append(['Electronics v2.12 (LEAD 261 (3))', tvtxt(cl.item(261, 3), 700)])
    o.append(dtable(['Item', 'Value (quoted)'], rows, widths=['24%', '76%'], cls='tight',
                    caption='electronics.json /lead_rulings_v2p11 and the CHANGELOG items that route work to Electronics v2.12 (PENDING; its interface is electronics.json v4.1, not yet reviewed).'))
    o.append(doc.h(2, '10.8 Lead rulings on the Electronics v2.12 handback (CHANGELOG 264); v4.1 PENDING REVIEW'))
    o.append(rulings_264(ctx, D))
    o.append(doc.h(2, '10.9 Electronics open issues'))
    oi = ctx.raw(E, '/open_issues', default=[]) or []
    rows = []
    for k, x in enumerate(oi):
        b = f'/open_issues/{k}'
        rows.append([Cell(f'<b>{esc(x.get("id"))}</b>', [ctx.v(E, b + '/id', tag='DESIGN')]), tvtxt(ctx.v(E, b + '/severity', tag='DESIGN')),
                     tvtxt(ctx.v(E, b + '/issue', tag='TO-VERIFY'), 300), tvtxt(ctx.v(E, b + '/owner', tag='DESIGN'), 80),
                     tvtxt(ctx.v(E, b + '/closure', tag='DESIGN'), 160)])
    o.append(dtable(['ID', 'Severity', 'Issue', 'Owner', 'Closure'], rows, label_cols=0, widths=['13%', '9%', '46%', '12%', '20%'], cls='tight',
                    caption=f'electronics.json /open_issues ({len(oi)} items).'))
    return '\n'.join(o)


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
                    caption=f'01-systems-gnc/DATASHEET-INPUTS-GNC.md ({esc(src_label(ctx, "DSIG"))}); rows 6-8 (gimbal, slew, ENG-11) are in §3.2. '
                            '<b>Vehicle basis of rows 1-5 and 9: massprops v3.5.1</b> (the basis column names it); the CAD v3.5.2 mass change is in the table below.'))
    gm = gnc_mass_cells(ctx, D)
    rows = [['GNC vehicle basis (row 4): liftoff mass / liftoff T/W (massprops v3.5.1)', cat(gm['lift'].h('.2f'), ' / ', gm['tw'].h('.2f'))],
            ['Landing-mass change v3.5.2 vs v3.5.1: as built / without the conditional TC-09 thinning', cat(gm['dl'].h('+.4f'), ' / ', gm['dl0'].h('+.4f'))],
            ["GNC's re-fly trigger (landing-mass growth)", num_cell(gm['trig'], '.2f')],
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
    return cat(tvtxt(i4, 700), '<br>New unit: proof ', pr.h('.1f'), ' against the required ', rq.h('.2f'),
               '. Its thresholds are re-based in a later Electronics round (OPEN, §12.4).')


def rulings_264(ctx, D):
    """Lead rulings on the Electronics v2.12 handback (CHANGELOG 264 (1)-(8)); each item DECIDED (lead decision, line 264 (k)),
    the numbers it quotes keep their own tags (lead 2026-10-21 12:52Z)."""
    cl = D['cl']
    rows = []
    rows.append(['Electronics v2.12 staged (Electronics, line 263)',
                 tvtxt(cl.part(263, 'candidate results/electronics_v4.1.json', ev='REF', why='provenance record of the staged candidate'), 500)])
    rows.append(['Source of record and the v4.1 candidate (264 (1))',
                 tvtxt(cl.clip(264, 1, 'interfaces/electronics.json stays v4', 'as PENDING REVIEW.'), 500)])
    i2 = cl.item(264, 2)
    rows.append(['R3-01 Pc zero, OI-C1-SEAT-DRIFT (264 (2))', tvtxt(i2, 2400)])
    rz = rx_text(ctx, i2, r'kPcRezeroMax_Pa stays ([\d.]+) bar', 'bar')
    bc = rx_text(ctx, i2, r'kIgnBaseCheck_Pa ([\d.]+) / [\d.]+ bar', 'bar')
    bc2 = rx_text(ctx, i2, r'kIgnBaseCheck_Pa [\d.]+ / ([\d.]+) bar', 'bar')
    rows.append(['Pc re-zero limit on the compensated residual; BASE check, default / B-PC-1-shown build (264 (2))',
                 cat(rz.h('.2f'), '; ', bc.h('.2f'), ' / ', bc2.h('.2f'))])
    rows.append(['A1 BASE_AMB outcome (264 (3))', tvtxt(cl.item(264, 3), 800)])
    rows.append(['P_torch transducer, OI-PTORCH-PROOF (264 (4))', tvtxt(cl.item(264, 4), 1600)])
    rows.append(['T4 relight, OI-T4-RESIZE (264 (5))', tvtxt(cl.item(264, 5), 900)])
    i6 = cl.item(264, 6)
    t0a = rx_text(ctx, i6, r'T0 (\d+)-\d+ C', '°C')
    t0b = rx_text(ctx, i6, r'T0 \d+-(\d+) C', '°C')
    for t in (t0a, t0b):
        if t.value is not None and t.basis:
            t.basis += '; an ASSUMED design range (264 (6))'
    rows.append(['A1 flight T0 range (264 (6))', cat(tvtxt(i6, 500), '<br>Range ', t0a.h('.0f'), ' to ', t0b.h('.0f'))])
    rows.append(['OI-JFWD-FLIGHT, PROVISIONAL (264 (7))', tvtxt(cl.item(264, 7), 800)])
    rows.append(['REV-ELEC-4 and work not done (264 (8))', tvtxt(cl.clip(264, 8, 'v4.1 is promoted only after its verdict', 'can affect.'), 500)])
    return dtable(['Ruling', 'Text (quoted) and values'], rows, widths=['24%', '76%'], cls='tight',
                  caption='CHANGELOG line 264 (lead). Each item is a lead decision (DECIDED, Lead decision, line 264 (k)); numbers quoted in an item keep their own '
                          'tags. The firmware v2.12 and electronics.json v4.1 that implement them are PENDING REVIEW (REV-ELEC-4); interfaces/electronics.json v4 '
                          'stays the source of record.')


# ---------------------------------------------------------------------------------------------
# section 12 (v0.3.0): verification status, founder actions, open items; contradictions register
# ---------------------------------------------------------------------------------------------
def r2b_ruling(D):
    """LEAD RULING R2-B as quoted verbatim in Mechanical's line 254: a lead decision (DECIDED), its basis text names where it is quoted."""
    if 'r2b' not in D:
        t = D['cl'].part(254, 'LEAD RULING R2-B', ev='LEAD', why='the sentence quotes LEAD RULING R2-B verbatim')
        if t.value is not None:
            t.basis = 'Lead ruling R2-B (2026-10-21T07:37:34Z), quoted verbatim in Mechanical line 254'
        D['r2b'] = t
    return D['r2b']


def sup_index(ctx, rid):
    return next((k for k, r in enumerate(ctx.raw('SUP', '/reviews', default=[]) or []) if r.get('id') == rid), None)


def sec_verification(ctx, doc, a, D):
    o = [doc.h(1, '12 Verification status')]
    cl = D['cl']
    note = ctx.v('SUP', '/note', tag='DESIGN')
    o.append(note_box(f'<b class="stmt">{esc(PAGE_STATEMENT)}.</b> {tvtxt(note).html} No value here is a measurement. '
                      'Review verdicts, matching file hashes, clean CAD checks, passing unit tests and this document\'s own trace check '
                      'are digital evidence only.', 'warn'))
    o.append(doc.h(2, '12.1 Review status of the deliverables used here'))
    rows = []
    for rid, what, line in (('REV-COMB-4', 'Combustion v2.4b (delta re-review); folded in v2.4c / v2.4d', 256),
                            ('REV-ELEC-3', 'Electronics v2.11 (firmware v2.11, electronics.json v4)', 253),
                            ('REV-GNC-7', 'GNC rev4b / gnc.json v3.2', 258),
                            ('REV-MECH-2', 'Mechanical FEA and CAD (v3.5 era)', None)):
        i = sup_index(ctx, rid)
        if i is None:
            m = ctx.missing(f'{rid} in the review register')
            rows.append([Cell(f'<b>{esc(rid)}</b>', []), esc(what), Cell(m.h(), [m]), ''])
            continue
        vd = ctx.v('SUP', f'/reviews/{i}/verdict', tag='DERIVED')
        disp = cl.part(line, rid) if line else ctx.v('SUP', f'/reviews/{i}/lead_disposition', tag='LEAD') if ctx.raw('SUP', f'/reviews/{i}/lead_disposition', default=None) else ctx.missing(f'{rid} lead disposition', 'TO-VERIFY')
        rows.append([Cell(f'<b>{esc(rid)}</b>', []), esc(what), Cell(f'<b>{esc(vd.value)}</b> {vd.pill()}{vd.ref()}', [vd]), tvtxt(disp, 500)])
    pe = cl.clip(264, 8, 'v4.1 is promoted only after its verdict', 'its verdict.')
    rows.append([Cell('<b>REV-ELEC-4</b>', []), 'Electronics v2.12 (firmware v2.12, electronics.json v4.1 candidate)',
                 Cell(f'<b>PENDING</b> (started; CHANGELOG 264 (8)) {pe.pill()}{pe.ref()}', [pe]),
                 tvtxt(cl.clip(264, 1, 'interfaces/electronics.json stays v4', 'as PENDING REVIEW.'), 400)])
    fr = cl.item(262, 3)
    rows.append([Cell('<b>FEA3D-2</b>', []), '3D FEA of the v3.5.2 assembly (REPORT-FEA3D-v352.md) and the rows-v8 matrix',
                 Cell('<b>no independent review held in this finish run</b>', [fr]), tvtxt(fr, 300)])
    ds = cl.clip(262, 2, 'REV-DS-1, the independent review', 'no draft PDF exists yet.')
    rows.append([Cell('<b>REV-DS-1</b>', []), 'This datasheet (rev1)', Cell(f'<b>PENDING</b> (review of this draft) {ds.pill()}{ds.ref()}', [ds]), tvtxt(ds, 300)])
    o.append(dtable(['Review', 'Deliverable', 'Verdict', 'Lead disposition / plan (quoted)'], rows, label_cols=2, widths=['12%', '24%', '20%', '44%'], cls='tight',
                    caption='Verdicts from reviews/SUPERVISION.json; dispositions from the CHANGELOG. A verdict covers the hashed files only (§12.2).'))
    o.append(doc.h(2, '12.2 Review register'))
    sup = ctx.raw('SUP', '/reviews', default=[]) or []
    rows = []
    for k, r in enumerate(sup):
        b = f'/reviews/{k}'
        rid = ctx.v('SUP', b + '/id', tag='DERIVED')
        dt = ctx.v('SUP', b + '/date', tag='DERIVED')
        vd = ctx.v('SUP', b + '/verdict', tag='DERIVED')
        dl = ctx.v('SUP', b + '/deliverable', tag='DERIVED')
        same, changed, missing = hash_status(ctx, a, r.get('hashes_sha256_16'))
        hs = ctx.d(f'{len(same)} of {len(same) + len(changed) + len(missing)} reviewed files unchanged'
                   + (f'; changed since review: {", ".join(changed)}' if changed else '')
                   + (f'; not in the hub: {", ".join(missing)}' if missing else ''), '', 'sha256/16 of each reviewed hub file vs the register entry', [], ev='DERIVED')
        rows.append([Cell(f'<b>{esc(rid.value)}</b>{rid.ref()}<div class="small">{esc(dt.value)}</div>', [rid, dt]), tvtxt(dl, 200),
                     cat(f'<b>{esc(vd.value)}</b> ', vd.pill(), vd.ref(), Cell('', [vd])),
                     cat('<span class="small">', hs.h(pill=False), '</span>', Cell('', [hs]))])
    o.append(dtable(['Review', 'Deliverable', 'Verdict', 'Reviewed files now (generator check)'], rows, label_cols=0, widths=['12%', '36%', '22%', '30%'], cls='tight',
                    caption=f'reviews/SUPERVISION.json ({esc(ctx.src("SUP").sha16)}), {len(sup)} entries in register order. Not physical approval.'))

    o.append(doc.h(2, '12.3 Founder actions (traced to their decision)'))
    MR = '/jfwd_v352/founder_rules'
    fa = [
        ('IN718 M5 J-FWD screw: quote, and the M6 fallback', [cl.part(240, ['RULED: the J-FWD screw is IN718 M5', 'FALLBACK only if IN718'])]),
        ('HW-170 disc spring: quote with relaxation data at about 160 C', [cl.part(243, 'Spring A (Schnorr 001 500 A in 1.4568)'), ctx.v('MEC', f'{MR}/HW-170_single_use', tag='LEAD')]),
        ('J-F1: torque cap 3750 N per flight lot and the Prescale footprint check (TO-VERIFY)', [cl.part(245, ['J-F1 MAXIMUM PRELOAD IS CAPPED AT 3750 N', 'Prescale'])]),
        ('J-F1b: 175 C peak with the dwell (method TO-DEFINE)', [ctx.v('MEC', f'{MR}/J-F1b', tag='LEAD'), cl.part(254, 'J-F1b method TO-DEFINE')]),
        ('LOCTITE 243 service range (TO-VERIFY)', [cl.part(248, 'LOCTITE 243 tap zone'), cl.part(254, 'LOCTITE 243 range TO-VERIFY')]),
        ('Single-use J-FWD screws and springs; removed-screw inspection', [ctx.v('MEC', f'{MR}/single_use', tag='LEAD'), cl.part(243, 'Founder rule until C6 closes')]),
        ('Post-abort joint replacement rule', [ctx.v('MEC', f'{MR}/post_abort_joint_replacement', tag='LEAD'), cl.part(248, 'FOUNDER RULE: after any case-TC')]),
        ('HW-170 orientation', [ctx.v('MEC', f'{MR}/HW-170_orientation', tag='DERIVED')]),
        ('Stand T0 <= 24 C rule and its checklist row', [cl.item(249, 2), ctx.v('MEC', f'{MR}/stand_T0_cross_reference', tag='LEAD')]),
        ('B-TC-1 case-TC channel (tau and the static terms; CJTO trim, mean-shift EMI pass)', [cl.part(249, 'B-TC-1 (founder'), cl.item(253, 11)]),
        ('T-F1 at the A 175 exposure (gate before the first static fire; (d) OPEN)', [cl.part(249, 'T-F1 founder text on the A 175 rows'), ctx.v('TXT5', '/T-F1_exposure_basis_R9/criteria_status', tag='LEAD')]),
        ('Shoulder-screw registration (F2) and the index pin (F5)', [cl.part(245, ['F2 ADOPTED into C4', 'F5: clocking'])]),
        ('Preload-retention audit', [cl.part(240, 'PRELOAD-RETENTION AUDIT ADOPTED')]),
        ('TC-02 spigot select fit (R2-B; U TO-DEFINE)', [r2b_ruling(D), ctx.v('TXT5', '/item_C/C9_founder_texts_remap_v352/(6)_TC-02_select_fit_band_R2', tag='CALC')]),
        ('S01 / S02 and the screws replaced after any FA-1-class event', [cl.item(240, 6), ctx.v('MEC', f'{MR}/C6', tag='LEAD')]),
        ('J-FWD build procedure C4', [ctx.v('MEC', f'{MR}/C4_procedure', tag='LEAD')]),
        ('Kulite F-10, B-PC-1 zero coefficient per serial, F-13 soak and thermometer (253 (11))', [cl.item(253, 11)]),
        ('B-PC-1: the Pc-zero coefficient per serial and T_cal, with the bench plan v5 acceptance (264 (2))',
         [cl.clip(264, 2, 'with the per-serial coefficient and T_cal from B-PC-1', 'at k = 3)'), cl.item(264, 2, contains='Residuals stay OPEN')]),
        ('F-10: the thermal-zero maximum from Kulite (264 (2))', [cl.item(264, 2, contains='Residuals stay OPEN')]),
        ('Confirm the A1 flight T0 design range against the launch-site climate (264 (6))', [cl.item(264, 6)]),
        ('Decide OI-JFWD-FLIGHT at flight acceptance, with T-F1 (264 (7))', [cl.item(264, 7)]),
        ('Buy the P_torch unit, a C1-family Kulite (264 (4)); TO-QUOTE delivered to Sønderborg DK-6400', [cl.clip(264, 4, 'the BOM gains one C1-family unit', 'DK-6400.')]),
        ('Q_JFWD > 60.0 bar abs: inspection and TC-02 tap gauging before the next run', [ctx.v('CMB', '/z3_jfwd_rulings_v2p4d/v/jfwd_replace_rule/decision', tag='LEAD'),
                                                                                       cl.part(258, 'Q_JFWD')]),
        ('Stand no-event B-DPC-1 record for a noise-floor rule (TO-VERIFY)', [ctx.v('CMB', '/z3_jfwd_rulings_v2p4d/v/jfwd_replace_rule/measured_traces', tag='TO-VERIFY')]),
    ]
    rows = []
    for what, tvs in fa:
        rows.append([Cell(f'<b>{esc(what)}</b>', []), cat(*[Cell(f'<div class="dec">{tvtxt(t, 520).html}</div>', [t]) for t in tvs])])
    fb = ctx.raw('ELE', '/bench_plan/founder_block', default=[]) or []
    fbc = cat(*[Cell(f'<div class="small"><b>{esc(x.get("id"))}</b> ' + tvtxt(ctx.v('ELE', f'/bench_plan/founder_block/{j}/action', tag='DESIGN')).html + '</div>',
                     [ctx.v('ELE', f'/bench_plan/founder_block/{j}/action', tag='DESIGN')]) for j, x in enumerate(fb)])
    b5 = cl.clip(253, 5, 'bench plan v4 is REVISE', 'before v5.')
    rows.append([Cell('<b>Electronics founder block F-1 to F-14 (bench plan v4 section 0; electronics.json v4)</b>', []),
                 cat(Cell(f'<div class="dec"><b>Status:</b> {tvtxt(b5).html} v5 is staged with electronics.json v4.1 and is PENDING REVIEW (§1.4).</div>', [b5]), fbc)])
    o.append(dtable(['Founder action', 'Decision and text (quoted)'], rows, widths=['26%', '74%'], cls='tight',
                    caption='The founders run every physical step; none has been run. Purchases: TO-QUOTE delivered to Sønderborg DK-6400. '
                            'Bench plan v4 is REVISE (text) and does not go to the founders before v5 (CHANGELOG 253 (5)).'))

    o.append(doc.h(2, '12.4 Open items with owners'))
    Z = '/z3_jfwd_rulings_v2p4d/v/open_before_flight_acceptance'
    ob = ctx.raw('CMB', Z, default=[]) or []
    items = [('Before flight acceptance (LEAD 258 (3))', [ctx.v('CMB', f'{Z}/{j}', tag='TO-VERIFY') for j in range(len(ob))], 'LEAD / Mechanical'),
             ('Noise-floor rule for the J-FWD trigger on measured traces', [ctx.v('CMB', '/z3_jfwd_rulings_v2p4d/v/jfwd_replace_rule/measured_traces', tag='TO-VERIFY')], 'founders (B-DPC-1) / review'),
             ('OI-T4-RESIZE: the T4 re-run with the shorter relight', [cl.item(261, 2), cl.clip(264, 5, 'Combustion sets the length', 'soak-back.'),
                                                                    cl.clip(264, 5, 'T4 then demonstrates', 'say so.')], 'Combustion / Mechanical'),
             ('OI-C1-SEAT-DRIFT residuals (B-PC-1; F-10; the seat-TC mount; the P_mid temperature, MISSING)', [cl.item(264, 2, contains='Residuals stay OPEN')],
              'founders / Mechanical'),
             ('A1 pad no-go rule (NEW RULE, not implemented yet)', [cl.item(264, 2, contains='NEW RULE')], 'Electronics, after REV-ELEC-4'),
             ('OI-PTORCH-PROOF: re-base of the torch thresholds on the C1 zero', [cl.clip(264, 4, 'OPEN for the next Electronics round', 'DK-6400.')],
              'Electronics; Combustion / Mechanical (torch heat)'),
             ('Electronics v2.12 work NOT DONE: the v2.12 SIL MANIFEST; the S1-S11 / S14-S17 re-runs', [cl.clip(264, 8, 'The author did NOT produce', 'can affect.')],
              'Electronics; REV-ELEC-4 judges'),
             ('Items routed to Electronics v2.12 (in the v2.12 candidate, PENDING REVIEW)', [cl.item(258, 4)], 'Electronics'),
             ('Found negatives of the margin matrix', [D['neg_total']], 'per class, §9.3'),
             ('FEA3D open items', [md_heading(ctx, 'F3D', '13. Open items and owners', 'DERIVED', tag_raw='FEA3D-2 report heading')], 'per item, §9.10'),
             ('GNC open items 11a-11q', [md_find(ctx, 'DSIG', None, {0: '11a'}, 1, ev='TO-VERIFY', tag_raw='GNC datasheet inputs row 11a')], 'per item, §11.2'),
             ('Electronics open issues (electronics.json v4)', [ctx.d(len(ctx.raw('ELE', '/open_issues', default=[]) or []), '', 'count of electronics.json /open_issues', [], ev='DERIVED')], 'per item, §10.9'),
             ('Airframe items kept for when the airframe is tackled (ICD-AIRFRAME out of the finish scope)', [cl.part(222, 'The items that were queued for it')],
              'airframe work, deferred by the founder (222)')]
    rows = []
    for what, tvs, own in items:
        rows.append([Cell(f'<b>{esc(what)}</b>', []), cat(*[Cell(f'<div class="dec">{tvtxt(t, 600).html}</div>', [t]) for t in tvs]), esc(own)])
    o.append(dtable(['Item', 'Status (quoted)', 'Owner'], rows, widths=['24%', '60%', '16%'], cls='tight', free_cols=(2,)))

    o.append(doc.h(2, '12.5 Requirement verification methods'))
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
                    widths=['7%', '42%', '33%', '18%'], free_cols=(2,), cls='tight',
                    caption=f'00-requirements/REQUIREMENTS.md §2 and its amendments ({esc(src_label(ctx, "REQ"))}). No requirement has been verified physically.'))
    o.append(doc.h(2, '12.6 Founder test list'))
    rows = []
    for r in md_table_rows(ctx.src('BENCH').text or '', '1. Order and gates'):
        if not r or not (r[0].isdigit() or r[0] == 'F'):
            continue
        rows.append([f'Bench step {esc(r[0])}', tvtxt(md_row(ctx, 'BENCH', '1. Order and gates', r[0], 1, ev='DESIGN')),
                     tvtxt(md_row(ctx, 'BENCH', '1. Order and gates', r[0], 2, ev='DESIGN'), 220), tvtxt(md_row(ctx, 'BENCH', '1. Order and gates', r[0], 3, ev='DESIGN'), 160)])
    for r in md_table_rows(ctx.src('REQ').text or '', '4. Gating early bench tests'):
        if not r or r[0] in ('Test',):
            continue
        rows.append(['Early purchase (REQ §4)', Cell(f'<b>{esc(r[0])}</b>', [md_row(ctx, 'REQ', '4. Gating early bench tests', r[0], 0, ev='REQ')]),
                     tvtxt(md_row(ctx, 'REQ', '4. Gating early bench tests', r[0], 2, ev='REQ'), 220), tvtxt(md_row(ctx, 'REQ', '4. Gating early bench tests', r[0], 1, ev='REQ'), 160)])
    b5 = cl.clip(253, 5, 'bench plan v4 is REVISE', 'before v5.')
    o.insert(len(o) - 0, note_box('<b>Bench plan v4 status.</b> ' + inl(b5) + ' Bench plan v5 is staged with the electronics.json v4.1 candidate and is PENDING REVIEW '
                                  '(REV-ELEC-4); the rows below are bench plan v4, the plan of electronics.json v4.', 'warn'))
    o.append(dtable(['Kind', 'Test', 'Gate or measurement', 'Needs / source'], rows, label_cols=1, widths=['13%', '17%', '46%', '24%'], cls='tight',
                    caption=f'Bench plan v4 section 1 ({esc(src_label(ctx, "BENCH"))}; REVISE, CHANGELOG 253 (5)) and REQ §4. CF-4 and T1-T4 criteria: §7.9. None has been run. Cost: TO-QUOTE, delivered to Sønderborg, DK-6400.'))
    return '\n'.join(o)


def register_contradictions(ctx, a, D):
    cl = D['cl']
    # C-01: FEA3D-2 text vs the rows-v8 matrix of record (HW-101 J-FWD u cell)
    f2 = md_find(ctx, 'F3D', '13. Open items and owners', {0: '2'}, 2, ev='DERIVED', tag_raw='FEA3D-2 report §13 item 2')
    ch = ctx.v('MMXD', '/cell_value_changes/0', tag='DERIVED')
    if isinstance(f2.value, str) and '+0.301' in f2.value and isinstance(ch.value, dict) and ch.value.get('new_MS_y_MS_u', [None, None])[1] == 0.278:
        ctx.contra('C-01', 'HW-101 J-FWD u cell: FEA3D-2 report text vs the rows-v8 matrix of record',
                   [('FEA3D-2 report §13 item 2', f2), ('rows-v8 matrix delta', ch), ('rows-v8 why', ctx.v('MMXD', '/why', tag='DERIVED'))],
                   'the rows-v8 matrix value (Eq. 22 governing, rows v8; §9.5.3)', 'the report text predates the re-map; Mechanical / FEA3D to align the report wording.')
    # C-02: electronics.json v4 status text vs the promotion
    st = ctx.v('ELE', '/status', tag='DESIGN')
    if isinstance(st.value, str) and 'STAGED for the lead' in st.value:
        ctx.contra('C-02', 'electronics.json v4 status: "STAGED" vs promoted',
                   [('electronics.json /status', st), ('CHANGELOG 253 (5)', cl.item(253, 5))],
                   'promoted v4 is the published interface (OVR-10)', 'Electronics v2.12 (electronics.json v4.1) to restate the status text.')
    # C-03: combustion datasheet note "until gnc.json v3.2" vs v3.2 published without a 210 m A1 record
    nt = md_line_starting(ctx, 'DSIC', 'A1 apogee target 210 m is decided', 'DESIGN', tag_raw='combustion datasheet inputs note')
    g11h = md_find(ctx, 'DSIG', None, {0: '11h'}, 2, ev='TO-VERIFY', tag_raw='GNC datasheet inputs row 11h')
    if isinstance(nt.value, str) and 'until gnc.json v3.2' in nt.value:
        ctx.contra('C-03', 'A1 mission-burn records: "300 m comparators until gnc.json v3.2" vs v3.2 published without a 210 m record',
                   [('combustion datasheet inputs note', nt), ('GNC datasheet inputs 11h', g11h), ('CHANGELOG 260 (1)', cl.part(260, 'GNC.JSON v3.2 PUBLISHED'))],
                   'the 300 m A1 records stay the comparators; the 210 m A1 duty-cycle record is OPEN (GNC)', 'GNC to fly the 210 m record; Combustion to restate the note.')
    # C-04: BOM / hardware strings superseded by drawing-note rulings
    tc2 = D['bom_by_pn'].get('ENG-TC-02')
    hw1 = D['bom_by_pn'].get('ENG-HW-101')
    if tc2 is not None and '57.20 f7' in (tc2.l.get('notes') or ''):
        cl2 = next(x.strip() for x in tc2.l['notes'].split(';') if '57.20 f7' in x)
        n2 = ctx.t('BOM', ptr_join('lines', tc2.idx, 'notes') + '[clause containing "57.20 f7"]', cl2, 'DESIGN', tag_raw='BOM line notes (clause quoted)')
        ctx.contra('C-04', 'TC-02 plug fit: BOM notes "57.20 f7" vs the R2-B select fit',
                   [('BOM ENG-TC-02 notes', n2), ('CHANGELOG 254 (1)', r2b_ruling(D)),
                    ('matrix TC-01 J-FWD cell (drawn fit)', md_find(ctx, 'MMXMD', 'Negative cells and their classes', {0: 'TC-01', 1: 'J-FWD'}, 2, ev='SIM', tag_raw='rows-v8 matrix negative-cell table'))],
                   'R2-B select fit; the drawn 57.20 f7 fit is FOUND NEGATIVE', 'Mechanical: drawing texts carry R2-B (texts v5 C9 (6)); the BOM note is generated from the part script (no geometry change).')
    if hw1 is not None and '60 bar abs' in (hw1.l.get('notes') or ''):
        cl1 = next(x.strip() for x in hw1.l['notes'].split(';') if '60 bar abs' in x)
        n1 = ctx.t('BOM', ptr_join('hardware', 'lines', hw1.idx, 'notes') + '[clause containing "60 bar abs"]', cl1, 'DESIGN', tag_raw='BOM hardware notes (clause quoted)')
        ctx.contra('C-05', 'HW-101 action: "after any Pc above 60 bar abs" vs the Q_JFWD replace rule',
                   [('BOM ENG-HW-101 notes', n1), ('combustion.json z3_jfwd_rulings_v2p4d', ctx.v('CMB', '/z3_jfwd_rulings_v2p4d/v/jfwd_replace_rule/replaces', tag='LEAD'))],
                   'the Q_JFWD rule (LEAD 258 (3)); the BOM string is superseded (no hardware-data, BOM or geometry edit)', 'Mechanical to restate the hardware string at the next hardware-data revision.')
    # C-06: T4 rows vs the re-size
    t4 = md_line_starting(ctx, 'T14', '| T4, DC-D duty cycle', 'SIM', tag_raw='T1-T4 spec §3 T4 row')
    ctx.contra('C-06', 'T4: the T1-T4 rows (DC-D, 7.02 kg) vs the re-sized shortest firing (about 2.0 kg)',
               [('T1-T4 spec T4 row', t4), ('combustion.json t4_duration_note_v2p4c', ctx.v('CMB', '/t4_duration_note_v2p4c/v/status', tag='LEAD')),
                ('CHANGELOG 261 (2)', cl.item(261, 2))],
               'T4 re-sized (LEAD 261 (2)); the rows stay the DC-D computation [SIM] until re-run', 'Combustion re-runs the T4 rows (OPEN; not in the finish run).')
    # C-07: bench plan path
    bp = ctx.v('ELE', '/bench_plan/file', tag='DESIGN')
    if isinstance(bp.value, str) and bp.value.startswith('06-electronics/docs/bench_plan_v4.md') and not os.path.isfile(os.path.join(a.hub, '06-electronics/docs/bench_plan_v4.md')):
        loc = TV(ctx, ctx.src('BENCH').path.replace(a.hub + '/', ''), '', 'DERIVED', 'generator: file found at this path (sha256/16 ' + (ctx.src('BENCH').sha16 or '') + ')', 'BENCH', '(file)')
        ctx.contra('C-07', 'Bench plan v4 location: electronics.json path vs the hub tree',
                   [('electronics.json /bench_plan/file', bp), ('file in the hub', loc)], 'the staging copy (same sha as named)', 'Electronics v2.12 to state the hub path.')
    # C-08: CF-4 baseline text
    cb = ctx.v('CMB', '/cf4_gate/v/baseline_v2p4b', tag='DESIGN')
    if isinstance(cb.value, str) and 'not yet published' in cb.value:
        ctx.contra('C-08', 'CF-4 baseline: "mechanical.json v2.2 not yet published" vs mechanical.json v2.4 published',
                   [('combustion.json /cf4_gate/baseline_v2p4b', cb), ('mechanical.json version', ctx.v('MEC', '/version', tag='DESIGN'))],
                   'mechanical.json v2.4 is published; the CF-4 bleed-path basis stays the frozen v3.5.1 path as written', 'Combustion to restate at the next text revision.')
    # C-09: BOM mass sum vs the generator sum (only if they differ)
    bs, gs = D['bom_mass_sum'], D['bom_sum_tv']
    if isinstance(bs.value, (int, float)) and isinstance(gs.value, (int, float)) and abs(bs.value - gs.value) > 5e-4:
        ctx.contra('C-09', 'BOM mass_sum_kg vs the sum of its lines', [('BOM /mass_sum_kg', bs), ('generator sum', gs)], 'both shown (§4.4)', 'Mechanical to check the BOM header sum.')
    # C-10: P_torch transducer: electronics.json v4 selection vs lead 264 (4)
    sel = ctx.v('ELE', '/sensors/pressure_transducers/selection')
    if isinstance(sel.value, dict) and '070BG' in str(sel.value.get('P_TORCH')):
        ctx.contra('C-10', 'P_torch transducer: electronics.json v4 (TE M3234-000005-070BG) vs lead 264 (4) (C1-family Kulite XTL-190SM-2000A)',
                   [('electronics.json v4 /sensors/pressure_transducers/selection', sel), ('CHANGELOG 264 (4)', cl.clip(264, 4, 'P_torch (J901', 'same part as P_mid (ENG-BL-08) and C1.'))],
                   'lead 264 (4): the C1-family Kulite; its proof [DATASHEET] and the required proof [DERIVED] are quoted with their tags in §10.2',
                   'Electronics: thresholds re-based and the selection restated in the next round after REV-ELEC-4 (OPEN).')


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
          'issues': ctx.qa, 'contradictions': [c['id'] + ' ' + c['title'] for c in ctx.contradictions],
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
          f'contradictions {len(ctx.contradictions)}')
    if diff:
        print(f'diff vs {diff["against_revision"]}: changed {diff["n_changed"]}, added {diff["n_added"]}, removed {diff["n_removed"]}')
    return 1 if n_err else 0


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


def sec_trace(ctx, doc, a, D):
    o = [doc.h(1, 'Appendix A Value trace')]
    o.append('<p class="small">Every traced value used in this document: trace id, value as displayed, class, source and version, '
             'key (JSON pointer, markdown row, CHANGELOG line and item, or generator formula) and the source tag text. A DECIDED value also shows '
             'its source class (design value, lead decision or requirement). Identical source keys share one id.</p>')
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
        if getattr(tv, 'basis_detail', None) and tv.ev == 'DECIDED' and tv.basis_detail not in extra:
            extra = tv.basis_detail
        if tv.inputs:
            extra += ' ← ' + ', '.join(tv.inputs[:8]) + (' …' if len(tv.inputs) > 8 else '')
        if tv.note and tv.note not in extra:
            extra += f' [{tv.note}]'
        pill = ev_pill(tv.ev, None, getattr(tv, 'basis', None), tv.status if tv.value is not None else None)
        rows.append(f'<tr id="{tv.tid}"><td class="mono">{tv.tid}</td><td>{esc(val)}</td><td>{pill}</td><td>{esc(src)}</td>'
                    f'<td class="mono">{esc(key[:160])}</td><td>{esc(extra[:200])}</td></tr>')
    o.append('<table class="dt trace"><colgroup><col style="width:6%"><col style="width:20%"><col style="width:11%"><col style="width:10%">'
             '<col style="width:25%"><col style="width:28%"></colgroup><thead><tr><th>ID</th><th>Value</th><th>Class</th><th>Source</th><th>Key</th>'
             '<th>Source tag / formula</th></tr></thead><tbody>' + '\n'.join(rows) + '</tbody></table>')
    return '\n'.join(o)


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
            f'<meta name="generator" content="{GEN_NAME} {GEN_VERSION}"><style>{CSS}{CSS_REV1}</style></head><body>{body}</body></html>')


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


if __name__ == '__main__':
    sys.exit(main())

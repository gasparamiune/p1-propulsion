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


def clipw(s, n):
    """A display text cut to at most n characters at a word boundary, with a visible ' …' (never a silent cut; rev1 phase 2)."""
    s = '' if s is None else str(s)
    if len(s) <= n:
        return s
    k = s.rfind(' ', 0, n - 1)
    return (s[:k] if k > n // 2 else s[:n - 1]).rstrip(' ,;:(') + ' …'


def src_digits(v):
    """A source number at its own precision (REV-DS-1 D1-08): the shortest repr of the value with the float noise of a unit
    conversion removed (about 10 significant digits kept) and no trailing '.0'."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, int) or not math.isfinite(v):
        return str(v)
    if v == 0:
        return '0'
    r = round(v, max(0, 9 - int(math.floor(math.log10(abs(v))))))
    s = repr(r)
    if 'e' in s or 'E' in s:
        s = format(r, '.10g')
    return s[:-2] if s.endswith('.0') else s


# display rules for quoted source text (lead 2026-10-21 14:05Z): the printed quote changes, the trace keeps the source string
DISPLAY_SUBS = [
    (re.compile(r'\*Por revisar\*'), 'to be reviewed', None),                                  # D1-12: plain English, no markdown
    (re.compile(r'(?<!REPORT )(?<!REPORT)§\s?(\d+(?:\.\d+)*)'), r'combustion REPORT §\1', {'CMB'}),  # D1-11: combustion.json cross-references
]


def display_text(tv, s):
    if not isinstance(s, str):
        return s
    for rx_, rep, sids in DISPLAY_SUBS:
        if sids is None or tv.sid in sids:
            s = rx_.sub(rep, s)
    return s


def gnote(html_, tvs=()):
    """A bracketed generator note after a quoted value: the quote stays verbatim; the note states what a later lead line decides
    about it, each cited line with its trace reference (rev1 phase 2; lead 2026-10-21 13:47Z, REV-DS-1 batch 1)."""
    return Cell(f'<span class="gnote">[{html_}]</span>', [t for t in tvs if isinstance(t, TV)])


def as_design(tv, basis, why):
    """A decided number whose source tag names the lead although the lead has not accepted it: its source class is the
    specialist's design value (DECIDED, design value), never a lead decision (lead 2026-10-21 13:47Z, REV-DS-1 D1-03).
    Applied right after the value is read, so its trace entry carries the class."""
    if tv.ev == 'DECIDED':
        tv.basis_kind = 'DESIGN'
        tv.basis = basis
        tv.basis_detail = f'source tag: {tv.tag_raw}; class set at the call site: DESIGN ({why})'
        tv.tag_raw = f'{tv.tag_raw} (class set at the call site: DESIGN; {why})'
    return tv


def sub_tv(ctx, tv, start, end):
    """Verbatim part of a traced text, from the first occurrence of start to the end of the next occurrence of end; it keeps the
    class and basis of the text it is cut from (used where a register side quotes one clause of a long cell; rev1 phase 2)."""
    s = tv.value if isinstance(tv.value, str) else ''
    i = s.find(start)
    j = s.find(end, i) if i >= 0 else -1
    if i < 0 or j < 0:
        ctx.issue('WARN', f'{tv.sid}:{tv.ptr}: no text from {start!r} to {end!r}')
        return ctx.missing(f'{tv.sid} {tv.ptr} text from "{start}"')
    t = TV(ctx, s[i:j + len(end)], '', tv.ev, tv.tag_raw, tv.sid, f'{tv.ptr} [from "{start}" to "{end}"]', note=tv.note, status=tv.status)
    t.ev, t.basis, t.basis_detail, t.basis_kind = tv.ev, getattr(tv, 'basis', None), getattr(tv, 'basis_detail', None), getattr(tv, 'basis_kind', None)
    return t


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
    t = TV(ctx, val, unit, ev, tag_raw or (f'(class set at the call site: {tag})' if tag else None), sid, loc, note=note)
    if not conv:
        t.src_txt = m.group(group)  # v0.3.1: printed with the digits of the source text (REV-DS-1 D1-08)
    return t


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
    t = TV(ctx, float(m.group(group)), unit, ev, traw, tv.sid, loc, note=note)
    t.src_txt = m.group(group)  # v0.3.1: printed with the digits of the source text (REV-DS-1 D1-08)
    return t


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
    'RELE3': [r'^# (REVIEW-ELECTRONICS-R3 \(REV-ELEC-3\))'], 'RELE4': [r'^# (REVIEW-ELECTRONICS-R4 \(REV-ELEC-4\))'],
    'RDS1': [r'^# (REVIEW-DATASHEET-R1 \(REV-DS-1\))'], 'MMXMD': [r'^# (FEA3D margin matrix v3\.5\.2)'],
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
    promo = bool(getattr(a, 'ele41_line', None))
    if promo:
        # promoted-v4.1 build (lead GO 2026-10-21 14:48:44Z; CHANGELOG 266 (6), (7))
        add('ELE', J(H, 'interfaces/electronics.json'), 'Electronics interface v4.1 (ECU, sensors, firmware v2.12 SIL, abort causes): promoted, CHANGELOG 266 (7); '
            'option (b) is carved out of every start with ignition until a reviewed v2.13 delta (266 (6)); line 266 governs v4.1 where they differ')
        add('ELE4', J(H, '06-electronics/staging_v2.11/results/electronics_v4.json'), 'Electronics interface v4 (firmware v2.11), the file published before line 266 '
            '(kept as staging_v2.11/results/electronics_v4.json, 266 (7)): used only for the superseded sides of the contradiction register')
    else:
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
    if promo:
        SRC_FILE['BENCH'] = 'bench_plan_v5.md'  # the plan of the promoted v4.1 (display name of the source in traces and overrides)
        add('BENCH', J(H, '06-electronics/staging_v2.12/docs/bench_plan_v5.md'), 'Electronics bench and test plan v5, the plan of electronics.json v4.1: ACCEPT WITH '
            'COMMENTS (REV-ELEC-4); it does not go to the founders before the corrections of CHANGELOG 266 (7) (E4-02, E4-06)', 'md')
    else:
        add('BENCH', J(H, '06-electronics/staging_v2.11/docs/bench_plan_v4.md'), 'Electronics bench and test plan v4, the plan of electronics.json v4: REVISE (text), not for the founders before v5 (CHANGELOG 253 (5)); v5 comes with electronics v4.1 (PENDING REVIEW)', 'md')
    add('RELE3', J(H, 'reviews/REVIEW-ELECTRONICS-R3.md'), 'Independent review REV-ELEC-3 (text)', 'md')
    if promo:
        add('RELE4', J(H, 'reviews/REVIEW-ELECTRONICS-R4.md'), 'Independent review REV-ELEC-4 of Electronics v2.12 (text; the corrections that line 266 (7) applies)', 'md')
    else:
        add('ELE41', J(H, '06-electronics/staging_v2.12/results/electronics_v4.1.json'), 'Electronics interface candidate v4.1 (Electronics v2.12, staged): '
            'PENDING REVIEW until the REV-ELEC-4 verdict (CHANGELOG 264 (1)); no value of it is used in this draft', required=False)
        add('BENCH5', J(H, '06-electronics/staging_v2.12/docs/bench_plan_v5.md'), 'Electronics bench and test plan v5 (staged with v4.1): '
            'PENDING REVIEW with v4.1; not used for values in this draft', 'md', required=False)
    add('RDS1', J(H, 'reviews/REVIEW-DATASHEET-R1.md'), 'Independent review REV-DS-1 of this datasheet\'s rev1-draft (text)', 'md')
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
    # the status word before the revision, as on the cover ('PRELIMINARY · rev1'; REV-DS-1 final-build checklist, staged item)
    hdr = (f'<div style="{st}"><span><b style="color:#0b3a5c">{esc(DOC_ID)}</b> · <b style="color:#b4232a">{esc(a.status)}</b> · {esc(a.rev)} · CAD {esc(a.cad_version)}</span>'
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
.gnote { display: block; font-size: 0.86em; color: #155e57; margin-top: 0.6pt; }
p.hnote { font-size: 6.6pt; margin: 0 0 1.2mm; }
tr.grp td { background: #eef2f6; font-weight: 700; font-size: 6.6pt; }
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


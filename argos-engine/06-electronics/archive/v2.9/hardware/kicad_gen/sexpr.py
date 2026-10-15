"""Minimal S-expression reader/writer for KiCad 7 files (ARGOS engine ECU, 06-electronics, v1 2026-10-12).

Nodes are Python lists; atoms are str (bare symbols) or Q (quoted strings) or numbers kept as their
source text (so a round trip does not change formatting of library data)."""
import re

class Q(str):
    """A quoted string atom."""
    pass

_tok = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))', re.S)

def parse(text):
    pos = 0
    stack = [[]]
    n = len(text)
    while pos < n:
        m = _tok.match(text, pos)
        if not m:
            if text[pos:].strip() == '':
                break
            raise ValueError('parse error at %d: %r' % (pos, text[pos:pos + 40]))
        pos = m.end()
        if m.group(1):
            stack.append([])
        elif m.group(2):
            node = stack.pop()
            stack[-1].append(node)
        elif m.group(3) is not None:
            s = m.group(3)
            s = re.sub(r'\\(.)', lambda mm: {'n': '\n', 't': '\t'}.get(mm.group(1), mm.group(1)), s)
            stack[-1].append(Q(s))
        else:
            stack[-1].append(m.group(4))
    assert len(stack) == 1
    return stack[0]

def q(s):
    s = str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
    return '"' + s + '"'

def fmt_num(v):
    if isinstance(v, str):
        return v
    if isinstance(v, bool):
        return 'yes' if v else 'no'
    if isinstance(v, int):
        return str(v)
    s = ('%.4f' % v).rstrip('0').rstrip('.')
    if s in ('-0', ''):
        s = '0'
    return s

def dumps(node, indent=0, inline_heads=('at', 'xy', 'size', 'start', 'end', 'mid', 'center', 'radius', 'width',
                                         'type', 'length', 'offset', 'font', 'justify', 'stroke', 'fill', 'color',
                                         'diameter', 'effects', 'uuid', 'lib_id', 'unit', 'in_bom', 'on_board', 'dnp',
                                         'reference', 'page', 'pin_numbers', 'pin_names', 'number', 'name', 'shape',
                                         'thickness', 'drill', 'layers', 'layer', 'convert', 'exclude_from_sim')):
    """Serialise. Short leaf lists and the listed heads print on one line."""
    if not isinstance(node, list):
        if isinstance(node, Q):
            return q(node)
        return fmt_num(node)
    if not node:
        return '()'
    head = node[0]
    parts = [dumps(x, indent + 1) for x in node]
    flat = '(' + ' '.join(parts) + ')'
    has_list = any(isinstance(x, list) for x in node[1:])
    if (not has_list and len(flat) < 120) or (isinstance(head, str) and head in inline_heads and len(flat) < 160):
        return flat
    out = '(' + parts[0]
    pad = '  ' * (indent + 1)
    for x, p in zip(node[1:], parts[1:]):
        if isinstance(x, list):
            out += '\n' + pad + p
        else:
            out += ' ' + p
    out += '\n' + '  ' * indent + ')'
    return out

def find(node, head):
    for x in node:
        if isinstance(x, list) and x and x[0] == head:
            return x
    return None

def find_all(node, head):
    return [x for x in node if isinstance(x, list) and x and x[0] == head]

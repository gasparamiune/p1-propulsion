"""KiCad 7 schematic/library writer for the ARGOS engine ECU (06-electronics), v1 2026-10-12; v1.1 2026-10-13 (ECU v2.3):
DNP flag per part (part['dnp'] -> symbol (dnp yes)), and stacked pins (several pin numbers at one location, e.g. the
three hidden S pins of a SON-8 MOSFET) get one stub and one label instead of identical overlapping copies.

Writes KiCad 7.0 files (schematic format 20230121, symbol library 20220914, footprint 20221018) that
open in KiCad 7, 8 and 9. Connectivity style: every connected pin gets a short wire stub that ends in a
net label (local), a global label (net used on several sheets) or a power symbol (rails). Unused pins
get a no-connect flag. This keeps the drawing editable: moving a symbol in KiCad drags its stubs.

Coordinates: library symbols use Y up; schematic uses Y down (mm). Symbol rotation r (deg) is CCW as
seen on screen: screen vector (1,0) -> (cos r, -sin r).
"""
import copy
import math
import os
import uuid as uuidlib

from sexpr import Q, parse, dumps, find, find_all

STOCK_SYM_DIR = '/usr/share/kicad/symbols'
GRID = 1.27
STUB = 2.54
FONT = 1.27
CHAR_W = 1.2        # mm per character of the KiCad 7 stroke font at 1.27 mm (measured 1.10-1.18 for capitals)
PWR_TIP = 2.54      # length of the power-symbol graphic from its pin (rails: arrow, GND: triangle)

_uuid_ns = uuidlib.UUID('5b9e2a6e-41d7-4a43-9f43-6d1c7c1f2a01')


def uid(*parts):
    """Deterministic UUID so that regenerating the project does not churn every object."""
    return str(uuidlib.uuid5(_uuid_ns, '/'.join(str(p) for p in parts)))


def snap(v, g=GRID):
    return round(round(v / g) * g, 4)


def rot_vec(x, y, r):
    """Rotate a SCREEN vector by r degrees CCW as displayed (Y down)."""
    c = round(math.cos(math.radians(r)), 9)
    s = round(math.sin(math.radians(r)), 9)
    return (x * c + y * s, -x * s + y * c)


# ----------------------------------------------------------------------------------------- library
class SymbolLibrary:
    """Loads stock symbols, flattens 'extends', and holds custom symbols. All symbols end up in one
    project library (nickname PROJECT) so the project does not depend on the user's stock library version."""

    def __init__(self, project_lib):
        self.project_lib = project_lib
        self._stock = {}
        self.symbols = {}      # name -> flattened node (name unprefixed)
        self.origin = {}       # name -> 'Lib:Name' source or 'custom'

    def _stock_lib(self, lib):
        if lib not in self._stock:
            path = os.path.join(STOCK_SYM_DIR, lib + '.kicad_sym')
            self._stock[lib] = parse(open(path, encoding='utf-8').read())[0]
        return self._stock[lib]

    def _get_raw(self, lib, name):
        for s in find_all(self._stock_lib(lib), 'symbol'):
            if s[1] == name:
                return s
        raise KeyError('%s:%s not found' % (lib, name))

    def _flatten(self, lib, name):
        raw = copy.deepcopy(self._get_raw(lib, name))
        ext = find(raw, 'extends')
        if not ext:
            return raw
        parent = self._flatten(lib, ext[1])
        pname = parent[1]
        out = [raw[0], Q(name)]
        # flags from parent (pin_numbers, pin_names, power, in_bom, on_board, exclude_from_sim)
        for x in parent[2:]:
            if isinstance(x, list) and x[0] in ('property', 'symbol'):
                continue
            out.append(copy.deepcopy(x))
        # properties: child overrides parent
        props = {}
        order = []
        for p in find_all(parent, 'property'):
            props[str(p[1])] = copy.deepcopy(p)
            order.append(str(p[1]))
        for p in find_all(raw, 'property'):
            if str(p[1]) not in props:
                order.append(str(p[1]))
            props[str(p[1])] = copy.deepcopy(p)
        for k in order:
            out.append(props[k])
        for sub in find_all(parent, 'symbol'):
            sub = copy.deepcopy(sub)
            sub[1] = Q(name + str(sub[1])[len(pname):])
            out.append(sub)
        return out

    def add_stock(self, lib, name, alias=None):
        key = alias or name
        if key in self.symbols:
            return key
        node = self._flatten(lib, name)
        if alias:
            node = self._rename(node, alias)
        self.symbols[key] = node
        self.origin[key] = '%s:%s' % (lib, name)
        return key

    @staticmethod
    def _rename(node, new):
        old = str(node[1])
        node = copy.deepcopy(node)
        node[1] = Q(new)
        for sub in find_all(node, 'symbol'):
            sub[1] = Q(new + str(sub[1])[len(old):])
        for p in find_all(node, 'property'):
            if p[1] == 'Value':
                p[2] = Q(new)
        return node

    def add_custom(self, node, note='custom'):
        name = str(node[1])
        self.symbols[name] = node
        self.origin[name] = note
        return name

    def lib_id(self, name):
        return '%s:%s' % (self.project_lib, name)

    def write_library(self, path):
        root = ['kicad_symbol_lib', ['version', '20220914'], ['generator', 'kicad_symbol_editor']]
        for name in sorted(self.symbols):
            root.append(self.symbols[name])
        with open(path, 'w', encoding='utf-8') as f:
            f.write(dumps(root) + '\n')

    def cache_node(self, name):
        """lib_symbols entry for a schematic: name prefixed with the library nickname."""
        node = copy.deepcopy(self.symbols[name])
        node[1] = Q(self.lib_id(name))
        return node

    # ------------------------------------------------------------------- geometry helpers
    def pins(self, name, unit=1, convert=1):
        """Pins of one unit (and common unit 0) for body style `convert`."""
        out = []
        node = self.symbols[name]
        for sub in find_all(node, 'symbol'):
            sname = str(sub[1])
            u, c = sname.rsplit('_', 2)[-2:]
            u, c = int(u), int(c)
            if u not in (0, unit) or c not in (0, convert):
                continue
            for p in find_all(sub, 'pin'):
                at = find(p, 'at')
                ln = float(find(p, 'length')[1])
                out.append({
                    'type': str(p[1]), 'shape': str(p[2]),
                    'x': float(at[1]), 'y': float(at[2]), 'ang': float(at[3]) if len(at) > 3 else 0.0,
                    'len': ln, 'name': str(find(p, 'name')[1]), 'number': str(find(p, 'number')[1]),
                    'hidden': 'hide' in p,
                })
        return out

    def units(self, name):
        us = set()
        for sub in find_all(self.symbols[name], 'symbol'):
            u = int(str(sub[1]).rsplit('_', 2)[-2])
            if u > 0:
                us.add(u)
        return sorted(us) or [1]

    def is_power(self, name):
        return any(isinstance(x, list) and x and x[0] == 'power' for x in self.symbols[name])

    def body_bbox(self, name, unit=1, convert=1):
        """Bounding box (library coords, Y up) of graphics + pins of a unit."""
        xs, ys = [], []
        node = self.symbols[name]
        for sub in find_all(node, 'symbol'):
            u, c = [int(v) for v in str(sub[1]).rsplit('_', 2)[-2:]]
            if u not in (0, unit) or c not in (0, convert):
                continue
            for g in sub[2:]:
                if not isinstance(g, list):
                    continue
                h = g[0]
                if h == 'rectangle':
                    for k in ('start', 'end'):
                        e = find(g, k)
                        xs.append(float(e[1])); ys.append(float(e[2]))
                elif h == 'polyline' or h == 'bezier':
                    pts = find(g, 'pts')
                    for xy in find_all(pts, 'xy'):
                        xs.append(float(xy[1])); ys.append(float(xy[2]))
                elif h == 'circle':
                    cx = find(g, 'center'); r = float(find(g, 'radius')[1])
                    xs += [float(cx[1]) - r, float(cx[1]) + r]; ys += [float(cx[2]) - r, float(cx[2]) + r]
                elif h == 'arc':
                    for k in ('start', 'mid', 'end'):
                        e = find(g, k)
                        if e:
                            xs.append(float(e[1])); ys.append(float(e[2]))
                elif h == 'pin':
                    at = find(g, 'at'); ln = float(find(g, 'length')[1])
                    a = math.radians(float(at[3]) if len(at) > 3 else 0)
                    x0, y0 = float(at[1]), float(at[2])
                    xs += [x0, x0 + ln * math.cos(a)]; ys += [y0, y0 + ln * math.sin(a)]
        if not xs:
            return (-1.27, -1.27, 1.27, 1.27)
        return (min(xs), min(ys), max(xs), max(ys))


# ----------------------------------------------------------------------------------------- schematic
class Sheet:
    def __init__(self, name, filename, title, paper='A3', page=1):
        self.name = name
        self.filename = filename
        self.title = title
        self.paper = paper
        self.page = page
        self.items = []         # sexpr nodes (wires, labels, symbols, text, no_connect)
        self.used_symbols = set()
        self.instances = []     # (ref, part, unit, pos) for reporting
        self.uuid = uid('sheet-file', filename)
        self.comments = []


PAPER = {'A4': (297.0, 210.0), 'A3': (420.0, 297.0), 'A2': (594.0, 420.0), 'A1': (841.0, 594.0)}


def effects(size=FONT, justify=None, hide=False, bold=False):
    font = ['font', ['size', size, size]]
    if bold:
        font.append('bold')
    e = ['effects', font]
    if justify:
        e.append(['justify'] + justify.split())
    if hide:
        e.append('hide')
    return e


def prop(name, value, x, y, ang=0, justify=None, hide=False, size=FONT):
    return ['property', Q(name), Q(value), ['at', x, y, ang], effects(size, justify, hide)]


class Schematic:
    """A hierarchical project: root sheet + sub-sheets, written as KiCad 7 files."""

    def __init__(self, project, lib, date, rev, company):
        self.project = project
        self.lib = lib
        self.date = date
        self.rev = rev
        self.company = company
        self.root_uuid = uid('root', project)
        self.sheets = []
        self.pwr_count = 0
        self.flg_count = 0
        self.netlist = {}       # (ref, pin) -> net, for verification
        self.pin_types = {}     # (ref, pin) -> electrical type
        self.parts = {}         # ref -> dict(fields)
        self.label_scope = {}   # net -> set(sheet names)

    def add_sheet(self, sheet):
        sheet.page = len(self.sheets) + 2
        self.sheets.append(sheet)
        return sheet

    def sheet_path(self, sheet):
        return '/%s/%s' % (self.root_uuid, uid('sheet-symbol', sheet.filename))

    # ------------------------------------------------------------------ primitives
    def wire(self, sheet, x1, y1, x2, y2):
        sheet.items.append(['wire', ['pts', ['xy', x1, y1], ['xy', x2, y2]],
                            ['stroke', ['width', 0], ['type', 'default']],
                            ['uuid', uid(sheet.filename, 'wire', x1, y1, x2, y2)]])

    def no_connect(self, sheet, x, y):
        sheet.items.append(['no_connect', ['at', x, y], ['uuid', uid(sheet.filename, 'nc', x, y)]])

    def text(self, sheet, s, x, y, size=FONT, bold=False, ang=0, justify='left bottom'):
        sheet.items.append(['text', Q(s), ['at', x, y, ang], effects(size, justify, bold=bold),
                            ['uuid', uid(sheet.filename, 'text', s, x, y)]])

    def label(self, sheet, net, x, y, outward, is_global, shape='bidirectional'):
        ang = {'R': 0, 'U': 90, 'L': 180, 'D': 270}[outward]
        if is_global:
            just = {'R': 'left', 'U': 'left', 'L': 'right', 'D': 'right'}[outward]
            sheet.items.append(['global_label', Q(net), ['shape', shape], ['at', x, y, ang], ['fields_autoplaced'],
                                effects(FONT, just), ['uuid', uid(sheet.filename, 'glabel', net, x, y)],
                                ['property', Q('Intersheetrefs'), Q('${INTERSHEET_REFS}'), ['at', x, y, ang],
                                 effects(FONT, just, hide=True)]])
        else:
            just = {'R': 'left bottom', 'U': 'left bottom', 'L': 'right bottom', 'D': 'right bottom'}[outward]
            sheet.items.append(['label', Q(net), ['at', x, y, ang], ['fields_autoplaced'], effects(FONT, just),
                                ['uuid', uid(sheet.filename, 'label', net, x, y)]])

    def _symbol_node(self, sheet, symname, ref, value, x, y, rot, unit, fields, footprint='', datasheet='~',
                     ref_xy=None, val_xy=None, hide_value=False, in_bom=True, on_board=True, field_ang=0, dnp=False):
        su = uid(sheet.filename, 'sym', ref, unit)
        node = ['symbol', ['lib_id', Q(self.lib.lib_id(symname))], ['at', x, y, rot], ['unit', unit],
                ['in_bom', 'yes' if in_bom else 'no'], ['on_board', 'yes' if on_board else 'no'],
                ['dnp', 'yes' if dnp else 'no'], ['uuid', su]]
        rx, ry, rj = ref_xy if ref_xy else (x, y - 5.08, 'left')
        vx, vy, vj = val_xy if val_xy else (x, y + 5.08, 'left')
        is_pwr = ref.startswith('#')
        # field_ang is relative to the symbol: KiCad draws a 90-deg field of a 90/270-deg rotated symbol horizontally
        node.append(prop('Reference', ref, rx, ry, field_ang, None if rj == 'center' else rj, hide=is_pwr))
        node.append(prop('Value', value, vx, vy, field_ang, None if vj == 'center' else vj, hide=hide_value))
        node.append(prop('Footprint', footprint, x, y, 0, None, hide=True))
        node.append(prop('Datasheet', datasheet, x, y, 0, None, hide=True))
        for k, v in fields.items():
            node.append(prop(k, v, x, y, 0, None, hide=True))
        for p in self.lib.pins(symname, unit):
            node.append(['pin', Q(p['number']), ['uuid', uid(sheet.filename, 'pin', ref, unit, p['number'])]])
        node.append(['instances', ['project', Q(self.project),
                                   ['path', Q(self.sheet_path(sheet)), ['reference', Q(ref)], ['unit', unit]]]])
        return node

    def pin_screen(self, symname, unit, x, y, rot):
        """Pins in schematic coordinates with outward direction letter."""
        out = []
        for p in self.lib.pins(symname, unit):
            dx, dy = rot_vec(p['x'], -p['y'], rot)
            px, py = snap(x + dx), snap(y + dy)
            a = math.radians(p['ang'])
            # pin points toward the body along angle a (lib coords); outward is the opposite
            ox, oy = rot_vec(-math.cos(a), math.sin(a), rot)   # lib->screen flips y
            if abs(ox) > abs(oy):
                d = 'R' if ox > 0 else 'L'
            else:
                d = 'D' if oy > 0 else 'U'
            q = dict(p)
            q.update({'sx': px, 'sy': py, 'out': d})
            out.append(q)
        return out

    def screen_bbox(self, symname, unit, x, y, rot):
        x0, y0, x1, y1 = self.lib.body_bbox(symname, unit)
        pts = [rot_vec(px, -py, rot) for px, py in ((x0, y0), (x0, y1), (x1, y0), (x1, y1))]
        xs = [x + p[0] for p in pts]; ys = [y + p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))

    # ------------------------------------------------------------------ power symbols
    def power_symbol(self, sheet, net, x, y, outward, flag=False):
        """Place power symbol `net` (custom power symbols named like the net) with its pin at (x, y),
        body pointing along `outward`."""
        symname = 'PWR_FLAG' if flag else self.power_symbol_name(net)
        sheet.used_symbols.add(symname)
        is_gnd = (not flag) and net in ('GND',)
        if flag:
            rot = {'U': 0, 'L': 90, 'D': 180, 'R': 270}[outward]
            self.flg_count += 1
            ref = '#FLG%02d' % self.flg_count
        elif is_gnd:
            rot = {'D': 0, 'R': 90, 'U': 180, 'L': 270}[outward]
            self.pwr_count += 1
            ref = '#PWR%03d' % self.pwr_count
        else:
            rot = {'U': 0, 'L': 90, 'D': 180, 'R': 270}[outward]
            self.pwr_count += 1
            ref = '#PWR%03d' % self.pwr_count
        # value text beyond the symbol graphic, always drawn horizontally (field angle 90 on 90/270-deg symbols)
        field_ang = 90 if rot in (90, 270) else 0
        label = 'PWR_FLAG' if flag else net
        if outward in ('L', 'R'):
            sgn = 1 if outward == 'R' else -1
            vx, vy = snap(x + sgn * (PWR_TIP + 0.8 + len(label) * CHAR_W / 2), 0.01), y
        else:
            sgn = 1 if outward == 'D' else -1
            vx, vy = x, snap(y + sgn * (PWR_TIP + 1.6), 0.01)
        node = self._symbol_node(sheet, symname, ref, label, x, y, rot, 1, {},
                                 footprint='', datasheet='~' if flag else '', ref_xy=(x, y, 'center'),
                                 val_xy=(vx, vy, 'center'), field_ang=field_ang)
        sheet.items.append(node)
        return ref

    def power_symbol_name(self, net):
        return 'PWR_' + net.replace('+', 'P').replace('-', 'N').replace('.', 'V')

    # ------------------------------------------------------------------ parts
    def place(self, sheet, part, x, y):
        """Place all units of `part` (dict) at (x, y) [unit k offset by part['unit_dx']]; draw stubs/labels."""
        sym = part['sym']
        rot = part.get('rot', 0)
        units = part.get('units') or [1]
        bboxes = []
        for k, unit in enumerate(units):
            ux = x + k * part.get('unit_dx', 30.48)
            uy = y + k * part.get('unit_dy', 0.0)
            ux, uy = snap(ux), snap(uy)
            pins = self.pin_screen(sym, unit, ux, uy, rot)
            bb = self.screen_bbox(sym, unit, ux, uy, rot)
            bboxes.append(bb)
            ref_xy, val_xy, field_ang = self.field_layout(part, bb, pins, rot)
            fields = dict(part.get('fields', {}))
            node = self._symbol_node(sheet, sym, part['ref'], part['value'], ux, uy, rot, unit, fields,
                                     footprint=part.get('footprint', ''), datasheet=part.get('datasheet', '~'),
                                     ref_xy=ref_xy, val_xy=val_xy, field_ang=field_ang, dnp=part.get('dnp', False))
            sheet.items.append(node)
            sheet.used_symbols.add(sym)
            sheet.instances.append((part['ref'], unit, ux, uy))
            drawn = {}          # v1.1: (x, y) of a pin already given a stub -> its net (stacked pins share it)
            for p in pins:
                key = (part['ref'], p['number'])
                if p['type'] == 'no_connect':
                    continue
                net = part['nets'].get(p['number'])
                if net is None and p['name'] in part['nets']:
                    net = part['nets'][p['name']]
                self.pin_types[key] = p['type']
                if net is None or net == '':
                    if p['hidden']:
                        continue
                    self.no_connect(sheet, p['sx'], p['sy'])
                    self.netlist[key] = None
                    continue
                self.netlist[key] = net
                pos = (p['sx'], p['sy'])
                if pos in drawn:
                    if drawn[pos] != net:
                        raise ValueError('%s: stacked pins at %s on two nets (%s, %s)' % (part['ref'], pos, drawn[pos], net))
                    continue
                drawn[pos] = net
                d = p['out']
                dx, dy = {'R': (1, 0), 'L': (-1, 0), 'U': (0, -1), 'D': (0, 1)}[d]
                stub = part.get('stub', STUB)
                ex, ey = snap(p['sx'] + dx * stub), snap(p['sy'] + dy * stub)
                self.wire(sheet, p['sx'], p['sy'], ex, ey)
                self.attach_net(sheet, net, ex, ey, d)
        self.parts[part['ref']] = part
        x0 = min(b[0] for b in bboxes); y0 = min(b[1] for b in bboxes)
        x1 = max(b[2] for b in bboxes); y1 = max(b[3] for b in bboxes)
        return (x0, y0, x1, y1)

    @staticmethod
    def field_layout(part, bb, pins, rot):
        """Reference/Value positions (absolute, schematic coords) and field angle for one placed unit.
        Two-terminal parts with pins left/right: centred above/below. Other small parts: right of the body.
        ICs/connectors: left corners, moved to the right corners when pins leave the top/bottom edge.
        Field angle 90 on a 90/270-deg rotated symbol makes KiCad draw the text horizontally."""
        outs = {p['out'] for p in pins if p['type'] != 'no_connect' and not p['hidden']}
        field_ang = 90 if rot in (90, 270) else 0
        if part.get('small') and outs <= {'L', 'R'}:
            cx = snap((bb[0] + bb[2]) / 2, 0.01)
            return (cx, snap(bb[1] - 1.4, 0.01), 'center'), (cx, snap(bb[3] + 1.4, 0.01), 'center'), field_ang
        if part.get('small'):
            return ((snap(bb[2] + 0.6, 0.01), snap(bb[1] + 0.6, 0.01), 'left'),
                    (snap(bb[2] + 0.6, 0.01), snap(bb[3] - 0.6, 0.01), 'left'), field_ang)
        rx = bb[2] + 0.6 if 'U' in outs else bb[0]
        vx = bb[2] + 0.6 if 'D' in outs else bb[0]
        return ((snap(rx, 0.01), snap(bb[1] - 1.6, 0.01), 'left'),
                (snap(vx, 0.01), snap(bb[3] + 1.6, 0.01), 'left'), field_ang)

    def attach_net(self, sheet, net, x, y, d):
        if net in self.power_nets:
            self.power_symbol(sheet, net, x, y, d)
        else:
            is_global = len(self.net_sheets.get(net, ())) > 1
            self.label(sheet, net, x, y, d, is_global, shape=self.global_shape.get((net, sheet.name), 'bidirectional'))

    # ------------------------------------------------------------------ writing
    def _header(self, sheet, title, paper, comments):
        tb = ['title_block', ['title', Q(title)], ['date', Q(self.date)], ['rev', Q(self.rev)],
              ['company', Q(self.company)]]
        for i, c in enumerate(comments[:9]):
            tb.append(['comment', i + 1, Q(c)])
        return tb

    def write_sheet(self, sheet, outdir):
        node = ['kicad_sch', ['version', '20230121'], ['generator', 'eeschema'], ['uuid', sheet.uuid],
                ['paper', Q(sheet.paper)], self._header(sheet, sheet.title, sheet.paper, sheet.comments)]
        ls = ['lib_symbols'] + [self.lib.cache_node(s) for s in sorted(sheet.used_symbols)]
        node.append(ls)
        node += sheet.items
        with open(os.path.join(outdir, sheet.filename), 'w', encoding='utf-8') as f:
            f.write(dumps(node) + '\n')

    def write_root(self, outdir, root_items, root_comments, sheet_boxes, paper='A3'):
        node = ['kicad_sch', ['version', '20230121'], ['generator', 'eeschema'], ['uuid', self.root_uuid],
                ['paper', Q(paper)], self._header(None, self.project_title, paper, root_comments)]
        node.append(['lib_symbols'])
        node += root_items
        for sh, (x, y, w, h) in zip(self.sheets, sheet_boxes):
            su = uid('sheet-symbol', sh.filename)
            node.append(['sheet', ['at', x, y], ['size', w, h], ['fields_autoplaced'],
                         ['stroke', ['width', 0.1524], ['type', 'solid']],
                         ['fill', ['color', 0, 0, 0, 0.0]],
                         ['uuid', su],
                         ['property', Q('Sheetname'), Q(sh.name), ['at', x, snap(y - 0.7, 0.01), 0],
                          effects(FONT, 'left bottom')],
                         ['property', Q('Sheetfile'), Q(sh.filename), ['at', x, snap(y + h + 0.6, 0.01), 0],
                          effects(FONT, 'left top')],
                         ['instances', ['project', Q(self.project),
                                        ['path', Q('/' + self.root_uuid), ['page', Q(str(sh.page))]]]]])
        node.append(['sheet_instances', ['path', Q('/'), ['page', Q('1')]]])
        with open(os.path.join(outdir, self.project + '.kicad_sch'), 'w', encoding='utf-8') as f:
            f.write(dumps(node) + '\n')

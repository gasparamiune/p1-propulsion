#!/usr/bin/env python3
"""Generate the ARGOS engine ECU KiCad 7 project (06-electronics/hardware/kicad/), v2 2026-10-12.

usage: python3 make_ecu_kicad.py <outdir>
Outputs: argos_ecu.kicad_pro, argos_ecu.kicad_sch (root) + 6 sheets, argos_ecu.kicad_sym (project symbol
library, all symbols used, flattened), argos_ecu.pretty/ (custom footprints), sym-lib-table, fp-lib-table,
intended_netlist.json (for the independent netlist comparison in check_netlist.py).
The generated project is meant to be opened, edited and continued in KiCad 7/8/9 by hand; this script is
the reproducible starting point, not a substitute for KiCad editing.
"""
import json
import math
import textwrap
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexpr import Q, dumps                                    # noqa: E402
from kicad_writer import (SymbolLibrary, Schematic, Sheet, PAPER, snap, uid, STUB, CHAR_W, PWR_TIP)  # noqa: E402
import custom_symbols as cs                                   # noqa: E402
import ecu_design as D                                        # noqa: E402

DATE = '2026-10-12'
REV = 'v2.2'   # v2.1 2026-10-12: Pc transducer 0-1000 psig + hardware over-pressure trip (lead decision, MEOP 45 bar)
               # v2.2 2026-10-12: OVP filter 220 nF (sense-line resonance), roll RCS pair connectors (4-pin)
COMPANY = 'ARGOS H1 engine - 06-electronics'
KICAD_VERSION_USED = '7.0.11 (Ubuntu 24.04 package 7.0.11+dfsg-1build4)'
FLAGS = {'Power': ['GND', 'VBAT', 'VLOGIC', '+5V'], 'Safety_Arming': ['ARM_BUS'], 'Actuators': ['TVC_PWR']}


def build_library(sheets):
    lib = SymbolLibrary(D.PROJECT)
    lib.add_custom(cs.teensy41(), 'custom: ' + cs.PIN_SOURCES['Teensy41'])
    lib.add_custom(cs.ads131m04_pw(), 'custom: ' + cs.PIN_SOURCES['ADS131M04_PW'])
    lib.add_custom(cs.pololu_u3v70f12(), 'custom: ' + cs.PIN_SOURCES['Pololu_U3V70F12'])
    for net in D.POWER_NETS:
        lib.add_custom(cs.power_rail(net, ground=(net == 'GND')), 'custom power symbol')
    lib.add_stock('power', 'PWR_FLAG')
    for _, _, _, groups in sheets:
        for _, parts in groups:
            for p in parts:
                if p['lib']:
                    lib.add_stock(p['lib'], p['sym'])
    return lib


def net_usage(sheets):
    use = {}
    for sname, _, _, groups in sheets:
        for _, parts in groups:
            for p in parts:
                for n in p['nets'].values():
                    if n:
                        use.setdefault(n, set()).add(sname)
    return use


def global_shapes(sch, sheets, lib):
    """Global-label shape per (net, sheet) from the pin types on that sheet."""
    shapes = {}
    for sname, _, _, groups in sheets:
        types = {}
        for _, parts in groups:
            for p in parts:
                for unit in (p['units'] or [1]):
                    for pin in lib.pins(p['sym'], unit):
                        n = p['nets'].get(pin['number'])
                        if n:
                            types.setdefault(n, set()).add(pin['type'])
        for n, ts in types.items():
            if ts & {'output', 'power_out', 'tri_state'}:
                s = 'output'
            elif ts & {'bidirectional'}:
                s = 'bidirectional'
            elif ts and ts <= {'input', 'passive'} and 'input' in ts:
                s = 'input'
            else:
                s = 'passive'
            shapes[(n, sname)] = s
    return shapes


def envelope(sch, part):
    """Extents (dx0, dy0, dx1, dy1) relative to the symbol origin, including stubs, labels and fields."""
    xs, ys = [], []
    sym, rot = part['sym'], part.get('rot', 0)
    for k, unit in enumerate(part['units'] or [1]):
        ox, oy = k * part.get('unit_dx', 30.48), k * part.get('unit_dy', 0.0)
        bb = sch.screen_bbox(sym, unit, ox, oy, rot)
        xs += [bb[0], bb[2]]; ys += [bb[1], bb[3]]
        # fields (same rule as Schematic.place)
        pins = sch.pin_screen(sym, unit, ox, oy, rot)
        for (fx, fy, just), txt in zip(sch.field_layout(part, bb, pins, rot)[:2], (part['ref'], part['value'])):
            w = len(txt) * CHAR_W
            x0 = fx - w / 2 if just == 'center' else fx
            xs += [x0, x0 + w]; ys += [fy - 0.9, fy + 0.9]
        for p in pins:
            if p['type'] == 'no_connect' or (p['hidden'] and not part['nets'].get(p['number'])):
                continue
            net = part['nets'].get(p['number'])
            dx, dy = {'R': (1, 0), 'L': (-1, 0), 'U': (0, -1), 'D': (0, 1)}[p['out']]
            if not net:
                xs += [p['sx'] - 1, p['sx'] + 1]; ys += [p['sy'] - 1, p['sy'] + 1]
                continue
            ex, ey = p['sx'] + dx * STUB, p['sy'] + dy * STUB
            if net in sch.power_nets:
                if dx:      # horizontal text beyond the tip
                    xs += [ex, ex + dx * (PWR_TIP + 1.0 + len(net) * CHAR_W)]; ys += [ey - 1.6, ey + 1.6]
                else:       # text above/below the tip
                    w = max(len(net) * CHAR_W / 2, 1.6)
                    xs += [ex - w, ex + w]; ys += [ey, ey + dy * (PWR_TIP + 2.6)]
            else:
                is_g = len(sch.net_sheets.get(net, ())) > 1
                L = len(net) * CHAR_W + (3.4 if is_g else 1.0)
                tx, ty = ex + dx * L, ey + dy * L
                xs += [ex, tx]; ys += [ey, ty]
                if dx:
                    ys += [ey - 1.6, ey + 1.0]
                else:
                    xs += [ex - 1.6, ex + 1.0]
    return (min(xs), min(ys), max(xs), max(ys))


def layout_sheet(sch, sheet, groups, paper_order=('A3', 'A2', 'A1')):
    """Shelf-pack parts into one block per group (rows up to a maximum block width), then fill columns in
    group order. Tries several block widths per paper size and keeps the smallest paper that fits."""
    GAP_X, GAP_Y = 5.08, 5.08
    TITLE_CW, TITLE_LH = 1.75, 3.0     # 1.8 mm bold title font: mm per character, line pitch
    measured = [(title, [(p, envelope(sch, p)) for p in parts]) for title, parts in groups]

    def pack(block_w_max, y_span):
        blocks = []
        for title0, items in measured:
            lines = textwrap.wrap(title0, max(30, int(block_w_max / TITLE_CW)))
            title = '\n'.join(lines)
            TITLE_H = 2.0 + TITLE_LH * len(lines) + 2.0
            rows, row, row_w, row_h = [], [], 0.0, 0.0
            for p, e in items:
                w, h = e[2] - e[0], e[3] - e[1]
                if row and row_w + w > block_w_max:
                    rows.append((row, row_w, row_h))
                    row, row_w, row_h = [], 0.0, 0.0
                row.append((p, e, w, h))
                row_w += w + GAP_X
                row_h = max(row_h, h)
            if row:
                rows.append((row, row_w, row_h))
            bw = max(max(r[1] for r in rows), max(len(s) for s in lines) * TITLE_CW + 2)
            bh = TITLE_H + sum(r[2] + GAP_Y for r in rows)
            blocks.append((title, rows, bw, bh, TITLE_H))
        cols, col, col_h, col_w = [], [], 0.0, 0.0
        for b in blocks:
            if col and col_h + b[3] > y_span:
                cols.append((col, col_w))
                col, col_h, col_w = [], 0.0, 0.0
            col.append(b)
            col_h += b[3] + 7.62
            col_w = max(col_w, b[2])
        if col:
            cols.append((col, col_w))
        total_w = sum(c[1] + 12.7 for c in cols) - 12.7
        tall = max(b[3] for b in blocks) > y_span
        max_h = max(sum(b[3] + 7.62 for b in c[0]) for c in cols)
        return cols, total_w, tall, max_h

    chosen = None
    for paper in paper_order:
        W, H = PAPER[paper]
        x_min, y_min = 20.32, 22.86
        x_max, y_max = W - 15.0, H - 45.0          # keep clear of the title block band at the bottom
        fits = []
        for bwm in (100.0, 125.0, 150.0, 175.0, 200.0, 225.0, 250.0):
            cols, total_w, tall, max_h = pack(bwm, y_max - y_min)
            if total_w <= (x_max - x_min) and not tall:
                fits.append((max_h, bwm, cols))
        if fits:
            fits.sort(key=lambda f: (f[0], f[1]))       # lowest columns = most even use of the sheet
            chosen = (paper, fits[0][2], x_min, y_min)
            break
    if not chosen:
        raise RuntimeError('sheet %s does not fit on %s' % (sheet.name, paper_order[-1]))
    paper, cols, x_min, y_min = chosen
    sheet.paper = paper
    placements = []
    x = x_min
    for col, cw in cols:
        y = y_min
        for title, rows, bw, bh, title_h in col:
            placements.append(('title', title, snap(x, 2.54), snap(y, 1.27)))
            yy = y + title_h
            for row, rw, rh in rows:
                xx = x
                for p, e, w, h in row:
                    ox = snap(xx - e[0], 2.54)
                    oy = snap(yy - e[1], 2.54)
                    placements.append(('part', p, ox, oy))
                    xx += w + GAP_X
                yy += rh + GAP_Y
            y += bh + 7.62
        x += cw + 12.7
    return placements


def write_project_file(outdir, sheet_list):
    """KiCad project file: ERC severities (nothing ignored), net classes default, sheet list."""
    sev = {k: 'error' for k in [
        'bus_definition_conflict', 'bus_entry_needed', 'bus_to_bus_conflict', 'bus_to_net_conflict',
        'conflicting_netclasses', 'different_unit_footprint', 'different_unit_net', 'duplicate_reference',
        'duplicate_sheet_names', 'endpoint_off_grid', 'extra_units', 'global_label_dangling', 'hier_label_mismatch',
        'label_dangling', 'lib_symbol_issues', 'missing_bidi_pin', 'missing_input_pin', 'missing_power_pin',
        'missing_unit', 'multiple_net_names', 'net_not_bus_member', 'no_connect_connected', 'no_connect_dangling',
        'pin_not_connected', 'pin_not_driven', 'pin_to_pin', 'power_pin_not_driven', 'similar_labels',
        'simulation_model_issue', 'unannotated', 'unit_value_mismatch', 'unresolved_variable', 'wire_dangling']}
    for k in ('endpoint_off_grid', 'lib_symbol_issues', 'multiple_net_names', 'similar_labels',
              'missing_bidi_pin', 'missing_input_pin', 'missing_unit', 'pin_to_pin'):
        sev[k] = 'warning'
    # No SPICE models are assigned in this design schematic: keep KiCad 7's default 'ignore' for this one check.
    # Run 1 with it enabled (102 warnings, all 'no simulation model') is kept in erc/ as evidence.
    sev['simulation_model_issue'] = 'ignore'
    pro = {
        'board': {'design_settings': {}},
        'boards': [],
        'cvpcb': {'equivalence_files': []},
        'erc': {
            'erc_exclusions': [],
            'meta': {'version': 0},
            'pin_map': [[0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 2], [0, 2, 0, 1, 0, 0, 1, 0, 2, 2, 2, 2],
                        [0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 2], [0, 1, 0, 0, 0, 0, 1, 1, 2, 1, 1, 2],
                        [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 2], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2],
                        [1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 2], [0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 2],
                        [0, 2, 1, 2, 0, 0, 1, 0, 2, 2, 2, 2], [0, 2, 0, 1, 0, 0, 1, 0, 2, 0, 0, 2],
                        [0, 2, 1, 1, 0, 0, 1, 0, 2, 0, 0, 2], [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]],
            'rule_severities': sev,
        },
        'libraries': {'pinned_footprint_libs': [], 'pinned_symbol_libs': []},
        'meta': {'filename': D.PROJECT + '.kicad_pro', 'version': 1},
        'net_settings': {'classes': [{'bus_width': 12, 'clearance': 0.2, 'diff_pair_gap': 0.25, 'diff_pair_via_gap': 0.25,
                                      'diff_pair_width': 0.2, 'line_style': 0, 'microvia_diameter': 0.3,
                                      'microvia_drill': 0.1, 'name': 'Default', 'pcb_color': 'rgba(0, 0, 0, 0.000)',
                                      'schematic_color': 'rgba(0, 0, 0, 0.000)', 'track_width': 0.25,
                                      'via_diameter': 0.8, 'via_drill': 0.4, 'wire_width': 6}],
                         'meta': {'version': 3}, 'net_colors': None, 'netclass_assignments': None,
                         'netclass_patterns': []},
        'pcbnew': {'last_paths': {}, 'page_layout_descr_file': ''},
        'schematic': {'annotate_start_num': 0, 'drawing': {'default_line_thickness': 6.0, 'default_text_size': 50.0,
                                                           'field_names': [], 'intersheets_ref_own_page': False,
                                                           'intersheets_ref_prefix': '', 'intersheets_ref_short': False,
                                                           'intersheets_ref_show': False, 'intersheets_ref_suffix': '',
                                                           'junction_size_choice': 3, 'label_size_ratio': 0.375,
                                                           'pin_symbol_size': 25.0, 'text_offset_ratio': 0.15},
                      'legacy_lib_dir': '', 'legacy_lib_list': [], 'meta': {'version': 1}, 'net_format_name': '',
                      'page_layout_descr_file': '', 'plot_directory': '', 'spice_current_sheet_as_root': False,
                      'spice_external_command': 'spice "%I"', 'spice_model_current_sheet_as_root': True,
                      'spice_save_all_currents': False, 'spice_save_all_voltages': False, 'subpart_first_id': 65,
                      'subpart_id_separator': 0},
        'sheets': sheet_list,
        'text_variables': {'ECU_REV': REV, 'KICAD_GEN': 'hardware/kicad_gen/make_ecu_kicad.py'},
    }
    with open(os.path.join(outdir, D.PROJECT + '.kicad_pro'), 'w') as f:
        json.dump(pro, f, indent=2)


def write_lib_tables(outdir):
    with open(os.path.join(outdir, 'sym-lib-table'), 'w') as f:
        f.write('(sym_lib_table\n  (lib (name "%s")(type "KiCad")(uri "${KIPRJMOD}/%s.kicad_sym")(options "")'
                '(descr "ARGOS ECU project symbols (flattened copies of KiCad 7.0.11 stock + custom)"))\n)\n'
                % (D.PROJECT, D.PROJECT))
    with open(os.path.join(outdir, 'fp-lib-table'), 'w') as f:
        f.write('(fp_lib_table\n  (lib (name "%s")(type "KiCad")(uri "${KIPRJMOD}/%s.pretty")(options "")'
                '(descr "ARGOS ECU custom footprints"))\n)\n' % (D.PROJECT, D.PROJECT))


def fp_node(name, descr, tags, pads, outline, courtyard, texts):
    node = ['footprint', Q(name), ['version', '20221018'], ['generator', 'pcbnew'], ['layer', Q('F.Cu')],
            ['descr', Q(descr)], ['tags', Q(tags)], ['attr', 'through_hole']]
    node += texts
    for (x0, y0, x1, y1) in outline:
        node.append(['fp_line', ['start', x0, y0], ['end', x1, y1], ['stroke', ['width', 0.12], ['type', 'solid']],
                     ['layer', Q('F.SilkS')], ['tstamp', uid('fp', name, 'silk', x0, y0, x1, y1)]])
    (cx0, cy0, cx1, cy1) = courtyard
    for (a, b, c, d) in ((cx0, cy0, cx1, cy0), (cx1, cy0, cx1, cy1), (cx1, cy1, cx0, cy1), (cx0, cy1, cx0, cy0)):
        node.append(['fp_line', ['start', a, b], ['end', c, d], ['stroke', ['width', 0.05], ['type', 'solid']],
                     ['layer', Q('F.CrtYd')], ['tstamp', uid('fp', name, 'crt', a, b, c, d)]])
    node += pads
    return node


def write_footprints(outdir):
    pdir = os.path.join(outdir, D.PROJECT + '.pretty')
    os.makedirs(pdir, exist_ok=True)
    # Teensy 4.1 on two 1x24 female sockets: rows 15.24 mm apart, 2.54 mm pitch, DIP-style numbering.
    pads = []
    for i in range(24):
        y = i * 2.54
        pads.append(['pad', Q(str(i + 1)), 'thru_hole', 'rect' if i == 0 else 'circle', ['at', 0, y], ['size', 1.7, 1.7],
                     ['drill', 1.0], ['layers', Q('*.Cu'), Q('*.Mask')], ['tstamp', uid('t41pad', i + 1)]])
        pads.append(['pad', Q(str(48 - i)), 'thru_hole', 'circle', ['at', 15.24, y], ['size', 1.7, 1.7],
                     ['drill', 1.0], ['layers', Q('*.Cu'), Q('*.Mask')], ['tstamp', uid('t41pad', 48 - i)]])
    # board outline 61.0 x 17.8 mm (PJRC drawing value, ASSUMED until drawing re-checked); USB end at pin 1 side
    bx0, bx1 = 7.62 - 8.9, 7.62 + 8.9
    by0, by1 = -2.54 - 1.0, -2.54 - 1.0 + 61.0
    outline = [(bx0, by0, bx1, by0), (bx1, by0, bx1, by1), (bx1, by1, bx0, by1), (bx0, by1, bx0, by0),
               (4.0, by0 - 1.5, 11.24, by0 - 1.5)]
    texts = [['fp_text', 'reference', Q('REF**'), ['at', 7.62, by0 - 3.5], ['layer', Q('F.SilkS')],
              ['effects', ['font', ['size', 1, 1], ['thickness', 0.15]]], ['tstamp', uid('t41', 'ref')]],
             ['fp_text', 'value', Q('Teensy41_Socket'), ['at', 7.62, by1 + 1.5], ['layer', Q('F.Fab')],
              ['effects', ['font', ['size', 1, 1], ['thickness', 0.15]]], ['tstamp', uid('t41', 'val')]],
             ['fp_text', 'user', Q('USB'), ['at', 7.62, by0 + 2.5], ['layer', Q('F.SilkS')],
              ['effects', ['font', ['size', 1, 1], ['thickness', 0.15]]], ['tstamp', uid('t41', 'usb')]]]
    node = fp_node('Teensy41_Socket', 'PJRC Teensy 4.1 on 2x 1x24 2.54 mm female headers, rows 15.24 mm; edge pins only; '
                   'pad n = DIP-style (1-24 left row from USB end, 25-48 right row from SD end). Outline 61 x 17.8 mm',
                   'teensy 4.1 socket', pads, outline, (bx0 - 0.5, by0 - 4.5, bx1 + 0.5, by1 + 0.5), texts)
    with open(os.path.join(pdir, 'Teensy41_Socket.kicad_mod'), 'w') as f:
        f.write(dumps(node) + '\n')
    # Pololu U3V70F12: wire-attach pads (module mounted off-board or on standoffs; Pololu hole pattern not drawn)
    pads = []
    names = [('1', 'VIN'), ('2', 'EN'), ('3', 'GND'), ('4', 'VOUT'), ('5', 'GND')]
    for i, (num, nm) in enumerate(names):
        pads.append(['pad', Q(num), 'thru_hole', 'circle', ['at', i * 5.08, 0], ['size', 3.0, 3.0], ['drill', 1.6],
                     ['layers', Q('*.Cu'), Q('*.Mask')], ['tstamp', uid('pol', num)]])
    texts = [['fp_text', 'reference', Q('REF**'), ['at', 10.16, -3.0], ['layer', Q('F.SilkS')], ['tstamp', uid('pol', 'ref')],
              ['effects', ['font', ['size', 1, 1], ['thickness', 0.15]]]],
             ['fp_text', 'value', Q('Pololu_U3V70_WireAttach'), ['at', 10.16, 3.0], ['layer', Q('F.Fab')],
              ['effects', ['font', ['size', 1, 1], ['thickness', 0.15]]], ['tstamp', uid('pol', 'val')]]]
    texts += [['fp_text', 'user', Q(nm), ['at', i * 5.08, 2.2], ['layer', Q('F.SilkS')], ['tstamp', uid('pol', 'lbl', nm, i)],
               ['effects', ['font', ['size', 0.8, 0.8], ['thickness', 0.12]]]] for i, (num, nm) in enumerate(names)]
    node = fp_node('Pololu_U3V70_WireAttach', 'Wire-attach pads (18 AWG) for Pololu U3V70F12 boost module; '
                   'module hole pattern NOT from a Pololu drawing - mount module separately', 'pololu boost wire',
                   pads, [], (-2.0, -4.5, 22.32, 4.0), texts)
    with open(os.path.join(pdir, 'Pololu_U3V70_WireAttach.kicad_mod'), 'w') as f:
        f.write(dumps(node) + '\n')


def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    sheets = [(name, fn, title, builder()) for (name, fn, title, builder) in D.SHEETS]
    lib = build_library(sheets)
    sch = Schematic(D.PROJECT, lib, DATE, REV, COMPANY)
    sch.project_title = 'ARGOS engine ECU %s - root' % REV
    sch.power_nets = set(D.POWER_NETS)
    sch.net_sheets = net_usage(sheets)
    sch.global_shape = global_shapes(sch, sheets, lib)
    sheet_objs = []
    for name, fn, title, groups in sheets:
        sh = sch.add_sheet(Sheet(name, fn, 'ARGOS ECU %s - %s' % (REV, title)))
        sh.comments = ['Generated by hardware/kicad_gen/make_ecu_kicad.py (%s); edit freely in KiCad' % DATE,
                       'KiCad used: %s' % KICAD_VERSION_USED,
                       'Status: design schematic. ERC clean is NOT hardware validation. Not built, not tested.']
        placements = layout_sheet(sch, sh, groups)
        for kind, obj, x, y in placements:
            if kind == 'title':
                sch.text(sh, obj, x, y, size=1.8, bold=True, justify='left top')
            else:
                sch.place(sh, obj, x, y)
        # PWR_FLAGs: bottom-left free band
        fx = 25.4
        fy = snap(PAPER[sh.paper][1] - 30.48, 2.54)     # on the 1.27 mm connection grid
        for net in FLAGS.get(name, []):
            sch.text(sh, 'PWR_FLAG ' + net, fx - 2.54, fy - 10.16, size=1.0)
            sch.power_symbol(sh, net, fx, fy, 'D' if net == 'GND' else 'U')
            sch.power_symbol(sh, net, fx, fy, 'U' if net == 'GND' else 'D', flag=True)
            fx += 22.86
        sheet_objs.append(sh)
    for sh in sheet_objs:
        sch.write_sheet(sh, outdir)
    # root sheet: sheet symbols + notes
    root_items = []
    notes = [
        'ARGOS H1 engine ECU %s (Teensy 4.1, separate from the flight computer, CAN 1 Mbit/s)' % REV,
        'Six hierarchical sheets; nets connect by global labels and power symbols (net names = interface names in REPORT.md).',
        'Generated %s by hardware/kicad_gen/make_ecu_kicad.py from hardware/kicad_gen/ecu_design.py, then editable by hand.' % DATE,
        'KiCad used: %s. Files use the KiCad 7 format and open in KiCad 7, 8 and 9 (8/9 upgrade on save).' % KICAD_VERSION_USED,
        'ERC: KiCad 7 eeschema ERC run headless (kicad-cli 7 has no sch erc); report: erc/argos_ecu_erc.rpt.',
        'All symbols live in the project library argos_ecu.kicad_sym (flattened copies of KiCad 7.0.11 stock symbols + custom).',
        'Status: design schematic only. Not built, no PCB layout routed, no bench test. ERC clean is not hardware validation.',
        'Safety chain: arming plug (physical) -> fused ARM bus switch = ARM_REQ AND watchdog OK AND OVP_OK -> ARM-only 5 V gate rail.',
        'OVP_OK: LMV331 comparator on PC_SIG (~31 bar g, ratiometric) clears a 74LVC1G175 latch; only an ARM_REQ rising edge sets it.',
    ]
    y = 25.4
    for i, s in enumerate(notes):
        root_items.append(['text', Q(s), ['at', 20.32, y, 0], ['effects', ['font', ['size', 1.8 if i == 0 else 1.4,
                           1.8 if i == 0 else 1.4]] + (['bold'] if i == 0 else []), ['justify', 'left', 'bottom']],
                           ['uuid', uid('root', 'note', i)]])
        y += 5.08 if i == 0 else 3.81
    boxes = []
    x0, y0 = 20.32, 76.2
    for i, sh in enumerate(sheet_objs):
        col, row = i % 3, i // 3
        boxes.append((snap(x0 + col * 76.2, 2.54), snap(y0 + row * 45.72, 2.54), 63.5, 30.48))
    sch.write_root(outdir, root_items, ['Root: overview and sheet index', 'KiCad used: %s' % KICAD_VERSION_USED,
                                        'Status: design schematic, not hardware-validated'], boxes)
    lib.write_library(os.path.join(outdir, D.PROJECT + '.kicad_sym'))
    write_lib_tables(outdir)
    write_footprints(outdir)
    write_project_file(outdir, [[uid('sheet-symbol', sh.filename), sh.name] for sh in sheet_objs])
    # intended netlist for independent comparison
    intended = {
        'generator': 'make_ecu_kicad.py', 'date': DATE, 'rev': REV,
        'pins': {'%s.%s' % k: v for k, v in sorted(sch.netlist.items())},
        'pin_types': {'%s.%s' % k: v for k, v in sorted(sch.pin_types.items())},
        'parts': {ref: {'value': p['value'], 'footprint': p['footprint'], 'sym': p['sym'],
                        'lib_source': lib.origin.get(p['sym']), 'fields': p['fields'], 'sheet': None}
                  for ref, p in sorted(sch.parts.items())},
        'sheets': {sh.name: {'file': sh.filename, 'paper': sh.paper, 'refs': sorted({r for r, *_ in sh.instances})}
                   for sh in sheet_objs},
        'power_nets': D.POWER_NETS, 'pwr_flags': FLAGS,
        'teensy_pinmap': {k: {'net': v[0], 'dir': v[1], 'function': v[2], 'pad': cs.teensy_pad(k)}
                          for k, v in D.TEENSY_PINMAP.items()},
    }
    for sname, info in intended['sheets'].items():
        for r in info['refs']:
            intended['parts'][r]['sheet'] = sname
    with open(os.path.join(outdir, 'intended_netlist.json'), 'w') as f:
        json.dump(intended, f, indent=1)
    print('wrote %d sheets, %d parts, %d pins, %d symbols' % (len(sheet_objs), len(sch.parts), len(sch.netlist),
                                                              len(lib.symbols)))
    for sh in sheet_objs:
        print('  %-16s %-4s %3d parts' % (sh.name, sh.paper, len({r for r, *_ in sh.instances})))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'kicad')

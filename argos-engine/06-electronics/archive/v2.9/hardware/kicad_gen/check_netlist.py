"""Cross-check of the generated KiCad project (ARGOS engine ECU, 06-electronics), v1 2026-10-12.

Independent of KiCad's own ERC (which is run in the eeschema GUI, see gui_erc.sh): this script
  1. compares the netlist exported by `kicad-cli sch export netlist` with intended_netlist.json written by the
     generator from ecu_design.py (every intended pin must land on the intended net, nothing extra),
  2. re-applies KiCad 7's default pin-to-pin matrix and its "pin not driven" rules to the exported nets,
  3. flags named nets with fewer than two pins (KiCad reports them as label errors),
  4. checks that every footprint named on a symbol exists in the stock or project footprint libraries.
Usage: python3 check_netlist.py <kicad_dir> <exported.net> <out_prefix>
Writes <out_prefix>.json and <out_prefix>.txt; exit code 1 on any error-level finding."""
import json
import os
import sys
from collections import defaultdict

from sexpr import parse, find, find_all

STOCK_FP_DIR = '/usr/share/kicad/footprints'

# KiCad 7 default pin conflict matrix (erc_settings.cpp, m_defaultPinMap), same order as ELECTRICAL_PINTYPE.
TYPES = ['input', 'output', 'bidirectional', 'tri_state', 'passive', 'free', 'unspecified', 'power_in',
         'power_out', 'open_collector', 'open_emitter', 'no_connect']
_ = 'OK'
W = 'WARN'
E = 'ERR'
MATRIX = [
    # I  O  Bi 3S Pas NIC UnS PwrI PwrO OC OE NC
    [_, _, _, _, _, _, W, _, _, _, _, E],   # I
    [_, E, _, W, _, _, W, _, E, E, E, E],   # O
    [_, _, _, _, _, _, W, _, W, _, W, E],   # Bi
    [_, W, _, _, _, _, W, W, E, W, W, E],   # 3S
    [_, _, _, _, _, _, W, _, _, _, _, E],   # Pas
    [_, _, _, _, _, _, _, _, _, _, _, E],   # NIC
    [W, W, W, W, W, _, W, W, W, W, W, E],   # UnS
    [_, _, _, W, _, _, W, _, _, _, _, E],   # PwrI
    [_, E, W, E, _, _, W, _, E, E, E, E],   # PwrO
    [_, E, _, W, _, _, W, _, E, _, _, E],   # OC
    [_, E, W, W, _, _, W, _, E, _, _, E],   # OE
    [E, E, E, E, E, E, E, E, E, E, E, E],   # NC
]
DRIVEN = {'input', 'power_in'}
DRIVERS = {'output', 'power_out', 'passive', 'tri_state', 'bidirectional'}
POWER_DRIVERS = {'power_out'}


def s(node, head, default=None):
    n = find(node, head)
    return str(n[1]) if n and len(n) > 1 else default


def load_netlist(path):
    root = parse(open(path, encoding='utf-8').read())[0]
    comps = {}
    for c in find_all(find(root, 'components'), 'comp'):
        ref = s(c, 'ref')
        libsrc = find(c, 'libsource')
        comps[ref] = {'value': s(c, 'value'), 'footprint': s(c, 'footprint', ''),
                      'lib': s(libsrc, 'lib') if libsrc else None, 'part': s(libsrc, 'part') if libsrc else None}
    nets = {}
    for n in find_all(find(root, 'nets'), 'net'):
        name = s(n, 'name')
        nodes = []
        for nd in find_all(n, 'node'):
            ptype = s(nd, 'pintype')
            flagged = ptype.endswith('+no_connect')     # KiCad appends this when a no-connect flag sits on the pin
            nodes.append({'ref': s(nd, 'ref'), 'pin': s(nd, 'pin'), 'type': ptype.replace('+no_connect', ''),
                          'nc_flag': flagged, 'func': s(nd, 'pinfunction', '')})
        nets[name] = nodes
    return comps, nets


def base_name(net):
    """'/Power/VBAT_F' -> 'VBAT_F'; global and power nets have no prefix."""
    if net.startswith('/'):
        return net.rstrip('/').split('/')[-1]
    return net


def fp_exists(fp, kicad_dir):
    if not fp or ':' not in fp:
        return False
    lib, name = fp.split(':', 1)
    if lib == 'argos_ecu':
        p = os.path.join(kicad_dir, 'argos_ecu.pretty', name + '.kicad_mod')
    else:
        p = os.path.join(STOCK_FP_DIR, lib + '.pretty', name + '.kicad_mod')
    return os.path.isfile(p)


def main(kicad_dir, netfile, out_prefix):
    intended = json.load(open(os.path.join(kicad_dir, 'intended_netlist.json')))
    want_pins = dict(intended['pins'])
    want_types = dict(intended['pin_types'])
    want_parts = dict(intended['parts'])
    comps, nets = load_netlist(netfile)

    findings = []

    def add(level, check, msg, **kw):
        d = {'level': level, 'check': check, 'msg': msg}
        d.update(kw)
        findings.append(d)

    # ---------------------------------------------------------------- 1. components
    for ref in sorted(set(want_parts) - set(comps)):
        add(E, 'component_missing', '%s intended but not in exported netlist' % ref)
    for ref in sorted(set(comps) - set(want_parts)):
        add(E, 'component_extra', '%s in netlist but not intended' % ref)
    for ref in sorted(set(want_parts) & set(comps)):
        w, g = want_parts[ref], comps[ref]
        if w['value'] != g['value']:
            add(E, 'value_mismatch', '%s value %r != intended %r' % (ref, g['value'], w['value']))
        if w['footprint'] != g['footprint']:
            add(E, 'footprint_mismatch', '%s footprint %r != intended %r' % (ref, g['footprint'], w['footprint']))
        if not fp_exists(g['footprint'], kicad_dir):
            add(E, 'footprint_not_found', '%s footprint %r not found in libraries' % (ref, g['footprint']))

    # ---------------------------------------------------------------- 2. pin -> net mapping
    got = {}
    got_types = {}
    got_flag = {}
    for name, nodes in nets.items():
        for nd in nodes:
            key = '%s.%s' % (nd['ref'], nd['pin'])
            if key in got:
                add(E, 'pin_on_two_nets', '%s on %s and %s' % (key, got[key], name))
            got[key] = name
            got_types[key] = nd['type']
            got_flag[key] = nd['nc_flag']
    for key, want in sorted(want_pins.items()):
        if key not in got:
            add(E, 'pin_missing', '%s (intended %s) absent from netlist' % (key, want))
            continue
        g = got[key]
        if want is None:
            if not g.startswith('unconnected-'):
                add(E, 'nc_pin_connected', '%s intended no-connect but on net %s' % (key, g))
            elif not got_flag[key]:
                add(E, 'nc_flag_missing', '%s intended no-connect but has no no-connect flag' % key)
        else:
            if base_name(g) != want:
                add(E, 'wrong_net', '%s on %s, intended %s' % (key, g, want))
            if got_flag[key]:
                add(E, 'nc_flag_on_used_pin', '%s carries a no-connect flag but is on %s' % (key, g))
        if want_types.get(key) and got_types.get(key) != want_types[key]:
            add(W, 'pin_type_changed', '%s type %s, generator recorded %s' % (key, got_types[key], want_types[key]))
    n_nc_type = 0
    for key in sorted(set(got) - set(want_pins)):
        if got_types[key] == 'no_connect' and got[key].startswith('unconnected-'):
            n_nc_type += 1          # library pin of electrical type no_connect (NC/DNC pad): left open, no flag
            add('INFO', 'nc_type_pin', '%s is a no_connect-type library pin, left open (%s)' % (key, got[key]))
        else:
            add(E, 'pin_extra', '%s on %s not in intended netlist (hidden pin?)' % (key, got[key]))

    # local nets that are split by mistake (same base name, several sheets, should be one global net)
    by_base = defaultdict(list)
    for name in nets:
        if not name.startswith('unconnected-'):
            by_base[base_name(name)].append(name)
    for b, names in sorted(by_base.items()):
        if len(names) > 1:
            add(E, 'split_net', 'net %s appears as %d separate nets: %s' % (b, len(names), ', '.join(names)))

    # ---------------------------------------------------------------- 3. pin matrix and drivers
    pwr_flag_nets = set()
    for sheet, lst in dict(intended['pwr_flags']).items():
        pwr_flag_nets.update(lst)
    summary = {}
    for name, nodes in sorted(nets.items()):
        types = [nd['type'] for nd in nodes]
        b = base_name(name)
        has_flag = b in pwr_flag_nets   # PWR_FLAG symbols are excluded from the netlist; add a power_out
        tset = list(types) + (['power_out'] if has_flag else [])
        # pin-to-pin
        seen = set()
        for i in range(len(tset)):
            for j in range(i + 1, len(tset)):
                a, c = tset[i], tset[j]
                lvl = MATRIX[TYPES.index(a)][TYPES.index(c)]
                if lvl != _ and (a, c, lvl) not in seen:
                    seen.add((a, c, lvl))
                    add(lvl, 'pin_to_pin', 'net %s: %s pin connected to %s pin' % (name, a, c))
        # drivers (KiCad skips nets that carry a no-connect flag, e.g. an EN pin left open on purpose)
        if any(nd['nc_flag'] for nd in nodes):
            summary[name] = {'pins': len(nodes), 'types': sorted(set(types)), 'pwr_flag': has_flag, 'nc_flag': True}
            continue
        if any(t == 'input' for t in tset) and not any(t in DRIVERS for t in tset):
            add(E, 'pin_not_driven', 'net %s: input pin(s) without a driver' % name)
        if any(t == 'power_in' for t in tset) and not any(t in POWER_DRIVERS for t in tset):
            add(E, 'power_pin_not_driven', 'net %s: power_in pin(s) without power_out or PWR_FLAG' % name)
        if not name.startswith('unconnected-') and len(nodes) < 2:
            add(E, 'single_pin_net', 'named net %s has %d pin(s): %s' %
                (name, len(nodes), ', '.join('%s.%s' % (n['ref'], n['pin']) for n in nodes)))
        summary[name] = {'pins': len(nodes), 'types': sorted(set(types)), 'pwr_flag': has_flag}

    # power nets must not be local (they would split per sheet)
    for pn in intended['power_nets']:
        if pn not in nets:
            add(E, 'power_net_missing', 'power net %s not in netlist' % pn)

    # Teensy pin map consistency
    for pin, info in dict(intended['teensy_pinmap']).items():
        key = 'U201.%s' % info['pad']
        if key not in got:
            add(E, 'teensy_pin_missing', 'Teensy pin %s (pad %s) not in netlist' % (pin, info['pad']))
        elif info['net'] and base_name(got[key]) != info['net']:
            add(E, 'teensy_pin_wrong_net', 'Teensy pin %s on %s, pin map says %s' % (pin, got[key], info['net']))

    n_err = sum(1 for f in findings if f['level'] == E)
    n_warn = sum(1 for f in findings if f['level'] == W)
    res = {
        'tool': 'hardware/kicad_gen/check_netlist.py v1', 'netlist': os.path.basename(netfile),
        'components': len(comps), 'nets': len(nets),
        'unconnected_marked_nets': sum(1 for n in nets if n.startswith('unconnected-')),
        'pins_in_netlist': len(got), 'pins_intended': len(want_pins),
        'errors': n_err, 'warnings': n_warn, 'findings': findings, 'net_summary': summary,
        'note': 'Cross-check only. KiCad GUI ERC (erc/argos_ecu_erc.rpt) is the authoritative ERC. '
                'Neither is hardware validation.'}
    json.dump(res, open(out_prefix + '.json', 'w'), indent=1)
    with open(out_prefix + '.txt', 'w') as f:
        f.write('ARGOS ECU netlist cross-check (check_netlist.py v1)\n')
        f.write('components %d, nets %d (%d single-pin no-connect nets), pins %d of %d intended\n' %
                (len(comps), len(nets), res['unconnected_marked_nets'], len(got), len(want_pins)))
        f.write('errors %d, warnings %d\n\n' % (n_err, n_warn))
        for fd in findings:
            f.write('%-5s %-22s %s\n' % (fd['level'], fd['check'], fd['msg']))
    print(open(out_prefix + '.txt').read()[:6000])
    return 1 if n_err else 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:4]))

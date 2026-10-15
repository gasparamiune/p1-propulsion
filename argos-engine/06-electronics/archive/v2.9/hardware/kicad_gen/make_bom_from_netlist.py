"""Grouped component list from the KiCad-exported netlist (ARGOS engine ECU, 06-electronics), v1 2026-10-12;
v1.1 2026-10-13: DNP parts (field 'DNP', ECU v2.3 provisions) are grouped separately and flagged in a 'dnp' column.

KiCad 7.0 kicad-cli has no 'sch export bom' (KiCad 8+), so this reads the netlist written by
`kicad-cli sch export netlist` and groups symbols by (value, footprint, MPN).
Usage: python3 make_bom_from_netlist.py <exported.net> <out.csv>
The priced BOM (calc/bom_v2.py) joins this list with prices; this file carries no prices."""
import csv
import sys
from collections import OrderedDict

from sexpr import parse, find, find_all


def s(node, head, default=''):
    n = find(node, head)
    return str(n[1]) if n and len(n) > 1 else default


def natural(ref):
    i = 0
    while i < len(ref) and not ref[i].isdigit():
        i += 1
    return (ref[:i], int(ref[i:]) if ref[i:].isdigit() else 0)


def main(netfile, out_csv):
    root = parse(open(netfile, encoding='utf-8').read())[0]
    groups = OrderedDict()
    for c in find_all(find(root, 'components'), 'comp'):
        ref = s(c, 'ref')
        fields = {}
        fl = find(c, 'fields')
        if fl:
            for f in find_all(fl, 'field'):
                name = s(f, 'name')
                fields[name] = str(f[2]) if len(f) > 2 else ''
        sheet = ''
        for p in find_all(c, 'property'):
            if s(p, 'name') == 'Sheetname':
                sheet = s(p, 'value')
        key = (s(c, 'value'), s(c, 'footprint'), fields.get('MPN', ''), fields.get('DNP', ''))
        g = groups.setdefault(key, {'refs': [], 'functions': [], 'specs': [], 'sheets': set()})
        g['refs'].append(ref)
        if fields.get('Function'):
            g['functions'].append(fields['Function'])
        if fields.get('Spec'):
            g['specs'].append(fields['Spec'])
        g['sheets'].add(sheet)
    rows = []
    for (value, fp, mpn, dnp), g in groups.items():
        refs = sorted(g['refs'], key=natural)
        funcs = list(OrderedDict.fromkeys(g['functions']))
        specs = list(OrderedDict.fromkeys(g['specs']))
        rows.append({'refs': ' '.join(refs), 'qty': len(refs), 'value': value, 'footprint': fp, 'mpn': mpn, 'dnp': dnp,
                     'sheets': ' '.join(sorted(g['sheets'])), 'function': ' | '.join(funcs)[:300],
                     'spec_source': ' | '.join(specs)[:300]})
    rows.sort(key=lambda r: natural(r['refs'].split()[0]))
    with open(out_csv, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print('%d symbols in %d lines (%d DNP symbols) -> %s' % (sum(r['qty'] for r in rows), len(rows),
                                                          sum(r['qty'] for r in rows if r['dnp']), out_csv))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

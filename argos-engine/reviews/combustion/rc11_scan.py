"""RC-11 evidence-rigour scan (reviewer, not the author).  Read-only text scan of the deliverables:
02-combustion/REPORT.md, 02-combustion/HANDBACK-SUMMARY.md, 05-plume-cfd/REPORT.md, interfaces/combustion.json.
Reports: MEASURED usage, 'measured' claims, price strings (currency, 'from'/'desde'/'starting at', zero prices),
TO-QUOTE and Sønderborg/DK-6400 mentions, AS RECALLED / LITERATURE-UNVERIFIED lines, and combustion.json leaf objects
that carry a value 'v' without a 'tag'.
Usage: python -I rc11_scan.py -> rc11_scan.json
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.abspath(os.path.join(HERE, '..', '..'))
FILES = ['02-combustion/REPORT.md', '02-combustion/HANDBACK-SUMMARY.md', '05-plume-cfd/REPORT.md', 'interfaces/combustion.json']
PAT = {
    'MEASURED_tag': r'\bMEASURED\b',
    'measured_word': r'\bmeasured\b',
    'currency_amount': r'(EUR|DKK|USD|GBP|€|\$|kr\.?)\s?\d|\d[\d.,]*\s?(EUR|DKK|USD|€|kr\b)',
    'from_price': r'\b(from|desde|starting at|ab)\s+(EUR|DKK|USD|€|\$)',
    'zero_price': r'(EUR|DKK|USD|€|\$)\s?0(\.0+)?\b|"price[^"]*"\s*:\s*0(\.0+)?\b',
    'TO_QUOTE': r'TO-QUOTE',
    'Sonderborg': r'S[øo]nderborg|DK-?6400',
    'AS_RECALLED': r'AS RECALLED',
    'LIT_UNVERIFIED': r'LITERATURE-UNVERIFIED',
}


def untagged(o, path='', acc=None):
    acc = [] if acc is None else acc
    if isinstance(o, dict):
        if 'v' in o and not any(k in o for k in ('tag', 'src', 'source')):
            acc.append(path)
        for k, v in o.items():
            untagged(v, f'{path}.{k}', acc)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            untagged(v, f'{path}[{i}]', acc)
    return acc


def main():
    out = dict(reviewer='independent reviewer (agent), not the author', date='2026-10-12', files={})
    for f in FILES:
        lines = open(os.path.join(HUB, f), encoding='utf-8').read().splitlines()
        res = {}
        for k, p in PAT.items():
            hits = [(i + 1, l.strip()[:220]) for i, l in enumerate(lines) if re.search(p, l, re.I if k not in ('MEASURED_tag', 'TO_QUOTE', 'AS_RECALLED', 'LIT_UNVERIFIED') else 0)]
            res[k] = dict(count=len(hits), hits=hits[:60])
        out['files'][f] = res
        print(f"== {f}: " + ', '.join(f"{k} {v['count']}" for k, v in res.items()))
    d = json.load(open(os.path.join(HUB, 'interfaces/combustion.json')))
    ut = untagged(d)
    out['combustion_json_untagged_v'] = ut
    print('combustion.json objects with v but no tag:', len(ut), ut[:30])
    json.dump(out, open(os.path.join(HERE, 'rc11_scan.json'), 'w'), indent=1, ensure_ascii=False)


if __name__ == '__main__':
    main()

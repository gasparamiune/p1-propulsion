import json, sys
d = json.load(open(sys.argv[1], encoding='utf-8'))
def get(path):
    o = d
    for part in path:
        o = o[part]
    return o
for spec in sys.argv[2:]:
    parts = []
    for tok in spec.split('/'):
        if tok == '': continue
        parts.append(int(tok) if tok.lstrip('-').isdigit() else tok)
    try:
        v = get(parts)
    except Exception as e:
        print('##', spec, 'ERR', e); continue
    s = json.dumps(v, ensure_ascii=False)
    print('##', spec, '(%d chars)' % len(s)); print(s[:3000]); print()

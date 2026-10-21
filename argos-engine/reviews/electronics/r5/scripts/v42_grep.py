import json, sys, re
d = json.load(open(sys.argv[1], encoding='utf-8'))
pat = re.compile(sys.argv[2])
lim = int(sys.argv[3]) if len(sys.argv) > 3 else 400
def walk(o, path):
    if isinstance(o, dict):
        for k, v in o.items():
            if pat.search(str(k)): print('KEY', path + '/' + str(k), '::', json.dumps(v, ensure_ascii=False)[:lim])
            walk(v, path + '/' + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o): walk(v, path + '[%d]' % i)
    elif isinstance(o, str):
        if pat.search(o): print(path, '::', o[:lim])
walk(d, '')

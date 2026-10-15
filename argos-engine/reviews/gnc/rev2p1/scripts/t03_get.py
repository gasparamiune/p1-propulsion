import json, sys, textwrap
d = json.load(open(sys.argv[1]))
n = int(sys.argv[2]) if sys.argv[2].isdigit() else None
paths = sys.argv[3:] if n is not None else sys.argv[2:]
n = n or 400
def get(x, p):
    import re
    for tok in re.findall(r"/([^/\[]+)|\[(\d+)\]", p):
        k, i = tok
        x = x[int(i)] if i else x[k]
    return x
for p in paths:
    v = get(d, p)
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    print(f"== {p} (len {len(s)})")
    print(textwrap.fill(s[:n], 250))

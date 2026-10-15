import json,sys,re
J=sys.argv[1]; pats=[re.compile(p) for p in sys.argv[2:]]
d=json.load(open(J))
def walk(o,p=""):
    if isinstance(o,dict):
        for k,v in o.items(): yield from walk(v,f"{p}/{k}")
    elif isinstance(o,list):
        for i,v in enumerate(o): yield from walk(v,f"{p}/{i}")
    elif isinstance(o,str): yield p,o
for p,s in walk(d):
    for r in pats:
        for m in r.finditer(s):
            a=max(0,m.start()-160); b=min(len(s),m.end()+160)
            print(f"[{r.pattern}] {p} :: ...{s[a:b]}...")

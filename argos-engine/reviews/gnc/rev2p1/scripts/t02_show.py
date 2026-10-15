import json, sys, textwrap
r = json.load(open(sys.argv[1]))
names = sys.argv[2].split(",")
sts = sys.argv[3].split(",") if len(sys.argv) > 3 else ["NONE", "FAR", "MARK", "ANC"]
w = int(sys.argv[4]) if len(sys.argv) > 4 else 300
for n in names:
    for p, pos, st, dist, ctx in r[n]:
        if st in sts:
            c = ctx.replace("\n", " ")
            c = c[max(0, 150 - w // 2): 150 + w // 2 + 20] if len(c) > w else c
            print(f"[{n}|{st}|{dist}] {p[:120]}\n    {c}")

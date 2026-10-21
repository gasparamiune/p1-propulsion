"""REV-GNC-7: compare the reviewer's reproduction rows (log lines) with the author's staged eng11fe_<V>.json rows."""
import json, re, sys, os
H = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/rev4b/eng11_fe/results"
logs = sys.argv[1:]
rx = re.compile(r"^(\w+) (alpha|beta) +Ks +(\d+): (PASS|fail) GM (\S+)(?: +(\S+))?")
mine = {}
for lg in logs:
    for ln in open(lg):
        m = rx.match(ln.strip())
        if m:
            v, a, ks, st, gm, wc = m.groups()
            mine[(v, a, int(ks))] = (st, gm, wc)
out = {}
for (v, a, ks), (st, gm, wc) in sorted(mine.items()):
    f = os.path.join(H, f"eng11fe_{v}.json")
    if not os.path.exists(f):
        out.setdefault(v, []).append((a, ks, "no author file")); continue
    d = json.load(open(f))
    r = d["rows"].get(f"{a}|Ks{ks}")
    if r is None:
        out.setdefault(v, []).append((a, ks, "row absent in author file")); continue
    out.setdefault(v, []).append((a, ks, st, gm, wc, r))
for v, rows in out.items():
    n = 0; same = 0
    for row in rows:
        if len(row) == 3:
            print(v, row); continue
        a, ks, st, gm, wc, r = row
        ast = "PASS" if r.get("pass_6dB") else "fail"
        agm = r.get("gm_up_min_dB")
        awc = r.get("first_fail")
        n += 1
        ok = (ast == st)
        if st == "PASS":
            try: ok = ok and abs(float(agm) - float(gm)) < 1e-3
            except Exception: ok = False
        else:
            ok = ok and (awc == wc)
        same += ok
        if not ok: print("DIFF", v, a, ks, "mine", st, gm, wc, "author", ast, agm, str(awc)[:120])
    print(f"{v}: {same}/{n} rows identical (status and, for PASS, GM to 1e-3 dB)")

# REV-GNC-4: independent recompute of the 69 named comparators (comparators_rev2p1.json) from the manifest-verified rev2
# RG-01 tables, pairing by the 'run' column; reviewer statistics (rvlib), no author code imported.
import json, sys, os, hashlib, gzip, csv
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rv"))
import rvlib as L
STG = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1"
C = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
# manifest check of every table used, by the reviewer
man = {}
for line in open(f"{STG}/rev2/MANIFEST_rev2.sha256"):
    h, p = line.split(None, 1); man[p.strip().lstrip("./")] = h
def tab(base, arm):
    rel = f"results/rg01_refly/rf_{base}_{arm.replace('|', '_')}.csv.gz"
    p = f"{STG}/rev2/{rel}"
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    if man.get(rel) != h: raise SystemExit(f"MANIFEST MISMATCH {rel}")
    with gzip.open(p, "rt") as f: rows = list(csv.DictReader(f))
    return {int(float(r["run"])): float(r["ok"]) > 0.5 for r in rows}, rel
out, nbad, used = [], 0, set()
for i, r in enumerate(C["rows"]):
    a_all, b_all = [], []
    pb = {}
    for base in r["bases"]:
        A, ra = tab(base, r["comparator"]); B, rb = tab(base, r["case"]); used |= {ra, rb}
        if set(A) != set(B): raise SystemExit(f"run sets differ {i} {base}")
        ks = sorted(A); a = [A[k] for k in ks]; b = [B[k] for k in ks]
        m = L.mcnemar(a, b); pb[base] = m; a_all += a; b_all += b
    m = L.mcnemar(a_all, b_all)
    s = r["pooled"]
    diffs = []
    for k_me, k_au in (("lost", "lost"), ("gained", "gained"), ("loses", "loses")):
        if m[k_me] != s[k_au]: diffs.append((k_au, m[k_me], s[k_au]))
    if abs(m["p"] - s["p_exact"]) > 1e-9 * max(1, s["p_exact"]) and abs(m["p"] - s["p_exact"]) > 1e-300: diffs.append(("p", m["p"], s["p_exact"]))
    if round(m["P_case"], 6) != round(s["P_case"], 6) or round(m["P_ref"], 6) != round(s["P_comparator"], 6): diffs.append(("P", (m["P_case"], m["P_ref"]), (s["P_case"], s["P_comparator"])))
    if len(a_all) != s["n"]: diffs.append(("n", len(a_all), s["n"]))
    for base, mb in pb.items():
        sb = r["per_base"][base]
        if (mb["lost"], mb["gained"], mb["loses"]) != (sb["lost"], sb["gained"], sb["loses"]): diffs.append((base, (mb["lost"], mb["gained"]), (sb["lost"], sb["gained"])))
    nbad += bool(diffs)
    out.append(dict(i=i, claim=r["claim"], reviewer=f"-{m['lost']}/+{m['gained']} p {m['p']:.4g}{' LOSES' if m['loses'] else ''}", diffs=diffs))
    print(f"{i:2d} {r['claim'][:26]:26s} {out[-1]['reviewer']:28s} {'OK' if not diffs else 'DIFF ' + str(diffs)}")
print("rows", len(out), "with differences", nbad, "tables used (manifest-verified by reviewer)", len(used))
json.dump(dict(source=sys.argv[1], source_sha256_16=hashlib.sha256(open(sys.argv[1], 'rb').read()).hexdigest()[:16],
               rows=out, rows_with_differences=nbad, tables_verified=len(used)), open(OUT, "w"), indent=1)

import json, csv, sys, collections
H = "/home/claude/work/shared-fallback/engine"
bom = list(csv.DictReader(open(f"{H}/03-cad/BOM_v3.5.csv")))
mj = json.load(open(sys.argv[1]))
B = collections.defaultdict(list)
for r in bom: B[r["pn"]].append(r)
def mass(pn):
    rows = B.get(pn, [])
    return sum(float(r["qty"] or 0) * float(r["unit_mass_kg"] or 0) for r in rows), rows
allpn = set()
for m in mj["mapping"]:
    pns = m.get("v35_pn")
    if not pns: continue
    tot = 0; tags = collections.Counter(); miss = []
    for pn in pns:
        allpn.add(pn)
        s, rows = mass(pn)
        if not rows: miss.append(pn)
        tot += s
        for r in rows: tags[r["mass_source"]] += float(r["qty"] or 0) * float(r["unit_mass_kg"] or 0)
    print(f"{m['item'][:44]:44s} author {m['v35_m_kg']:.5f} reviewer BOM {tot:.5f} diff {tot - m['v35_m_kg']:+.5f} tags { {k: round(v, 5) for k, v in tags.items()} } missing {miss}")
# bleed valves
for pn, rows in B.items():
    if pn.startswith("ENG-BL"):
        for r in rows: print("   ", pn, r["name"][:50], r["qty"], r["unit_mass_kg"], r["mass_source"])
# BOM items in 'fixed' groups not mapped by the author
print("groups present:", collections.Counter(g for r in bom for g in (r["groups"] or "").split(";")).most_common(20))

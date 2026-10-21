"""REV-GNC-6 v08: the ENG-11 6-DOF claim 'no arm loses a landing, K_s 58 included' (rev4 [12]) re-computed from the staged
e11_* tables against the P2 liq|G73|v351|h210 table (runs 0-499, same seed and draw), exact McNemar, both on flown
success (ok) and on the line-208 criterion (ok AND >= 80 g).  The author's vs_ref figures are printed beside mine.
SIM tables -> DERIVED.  Usage: python -I v08_eng11_fly.py <out.json>"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rv6lib as L

OUT = sys.argv[1]
F = f"{L.R4}/out_rev4/eng11/fly_v351_h210"
auth = json.load(open(f"{F}/eng11_fly.json"))
res = dict(script="v08_eng11_fly (REV-GNC-6)", tag="DERIVED from SIM tables", arms={})
ref = {b: L.read(L.case_files(b, "liq", "v351", 210)[0]) for b in L.MAIN}
for fn in sorted(os.listdir(F)):
    m = re.fullmatch(r"e11_(A1J?_[a-z]+)_(.+)\.csv\.gz", fn)
    if not m:
        continue
    b, arm = m.groups()
    rows = L.read(f"{F}/{fn}")
    n = len(rows)
    e = dict(file=[fn, L.sha16(f"{F}/{fn}")], n=n)
    for lab, onset in (("ok", None), ("ok80", 80.0)):
        oc = L.outcome(rows, onset)
        orf = {k: v for k, v in L.outcome(ref[b], onset).items() if k < n}
        s = L.stats(*L.counts(orf, oc))
        e[lab] = dict(P_ref=s["P_ref"], P_case=s["P_case"], lost=s["lost"], gained=s["gained"], p=s["p"], loses=s["loses"], ub95_pp=s["ub95_pp"])
    a = auth["arms"].get(arm, {}).get("per_base", {}).get(b, {}).get("vs_ref")
    e["author_vs_ref"] = a
    res["arms"][f"{b}|{arm}"] = e
res["any_loses_ok"] = any(v["ok"]["loses"] for v in res["arms"].values())
res["any_loses_ok80"] = any(v["ok80"]["loses"] for v in res["arms"].values())
json.dump(res, open(OUT, "w"), indent=1)
for k, v in res["arms"].items():
    a = v["author_vs_ref"] or {}
    print(f"{k:22s} ok -{v['ok']['lost']}/+{v['ok']['gained']} p {v['ok']['p']} | ok80 -{v['ok80']['lost']}/+{v['ok80']['gained']} p {v['ok80']['p']} UB95 {v['ok80']['ub95_pp']} | author -{a.get('lost')}/+{a.get('gained')}")
print("any loses (ok / ok80):", res["any_loses_ok"], res["any_loses_ok80"])

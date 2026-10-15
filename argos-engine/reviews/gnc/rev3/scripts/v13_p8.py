"""REV-GNC-5 v13: independent recount of P8 / F9 (RG-08 late flip to UNPRIMED) from the staged rev3 tables: P per main base and
pooled exact McNemar of liqF / pwF / liqP / pwP against the same-state decided arm at 285 m (liq|G73|h285, pw|G73|h285), all
winds and W10 < 6 m/s.  SIM tables -> DERIVED.  Usage: python -I v13_p8.py <out.json>"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rv5lib as L
out = dict(script="v13_p8 (REV-GNC-5)", tag="SIM tables; DERIVED", arms={})
for st in ("liq", "pw"):
    ref = f"{st}|G73|h285"
    for x in ("F", "P"):
        nm = f"{st}{x}|G73|h285"
        prs = [L.paired(L.load3(b, ref), L.load3(b, nm)) for b in L.MAIN]
        d = L.pooled(prs)
        lost = gained = n = 0
        for b in L.MAIN:
            ra, rb = L.load3(b, ref), L.load3(b, nm); oa, ob = L.ok(ra), L.ok(rb)
            for i, r in enumerate(rb):
                if float(r["wind"]) < 6.0:
                    n += 1; lost += oa[i] and not ob[i]; gained += ob[i] and not oa[i]
        out["arms"][nm] = dict(per_base_P=[round(p["P_case"], 4) for p in prs], pooled=d, W10_lt6=dict(n=n, lost=lost, gained=gained, p=L.p_exact(lost, gained)))
json.dump(out, open(sys.argv[1], "w"), indent=1)
for k, v in out["arms"].items():
    print(f"{k:16s} P {v['per_base_P']} pooled {L.fmt(v['pooled'])} | W10<6 -{v['W10_lt6']['lost']}/+{v['W10_lt6']['gained']} p {v['W10_lt6']['p']:.3g}")

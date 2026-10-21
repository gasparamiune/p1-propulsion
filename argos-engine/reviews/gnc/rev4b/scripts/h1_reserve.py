"""REV-GNC-7 (h)(ii): A1 210 m N2O reserve at touchdown from the staged rev4 P2 per-run files (G73 / G80 booked purge)."""
import csv, gzip, json, hashlib, sys
import numpy as np
D = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/rev4/out_rev4/p2"
out = {}
def load(fn):
    p = f"{D}/{fn}"
    rows = list(csv.DictReader(gzip.open(p, "rt")))
    return p, rows
for base in ("A1_none", "A1J_pc"):
    for st in ("liq", "pw"):
        res = {}
        for G in ("G73", "G80"):
            fn = f"rf_{base}_{st}_{G}_v351_h210.csv.gz"
            try:
                p, rows = load(fn)
            except FileNotFoundError:
                continue
            ll = np.array([float(r["liq_left"]) for r in rows]) * 1000
            pm = np.array([float(r["prg_mass"]) for r in rows]) * 1000
            ok = np.array([float(r["ok"]) for r in rows])
            ex = np.array([float(r["exhausted"]) for r in rows])
            rel = np.array([float(r["relight_ok"]) for r in rows])
            run = [int(r["run"]) for r in rows]
            res[G] = dict(file=fn, sha16=hashlib.sha256(open(p, "rb").read()).hexdigest()[:16], N=len(rows), P_ok=float(ok.mean()),
                          relight_ok=float(rel.mean()), exhausted=int(ex.sum()),
                          prg_mass_g=dict(min=round(float(pm.min()), 2), p50=round(float(np.median(pm)), 2), max=round(float(pm.max()), 2)),
                          liq_left_g=dict(min=round(float(ll.min()), 1), p01=round(float(np.percentile(ll, 1)), 1), p05=round(float(np.percentile(ll, 5)), 1),
                                          p50=round(float(np.median(ll)), 1)),
                          n_below_80g=int((ll < 80).sum()), n_below_59g=int((ll < 59).sum()),
                          worst5=[(run[i], round(float(ll[i]), 1), int(ok[i]), int(ex[i])) for i in np.argsort(ll)[:5]],
                          _ll=ll, _run=run, _ok=ok)
        if "G73" in res and "G80" in res and res["G73"]["_run"] == res["G80"]["_run"]:
            d = res["G80"]["_ll"] - res["G73"]["_ll"]
            res["shift_G80_minus_G73_g"] = dict(min=round(float(d.min()), 2), p50=round(float(np.median(d)), 2), max=round(float(d.max()), 2))
            lost = int(((res["G73"]["_ok"] == 1) & (res["G80"]["_ok"] == 0)).sum()); gained = int(((res["G73"]["_ok"] == 0) & (res["G80"]["_ok"] == 1)).sum())
            res["paired_ok_G80_vs_G73"] = dict(lost=lost, gained=gained)
        for G in ("G73", "G80"):
            if G in res:
                for k in ("_ll", "_run", "_ok"):
                    res[G].pop(k)
        out[f"{base}|{st}"] = res
json.dump(out, open(sys.argv[1], "w"), indent=1)
for k, v in out.items():
    print(k)
    for G in ("G73", "G80"):
        if G in v:
            x = v[G]
            print(f"  {G}: N {x['N']} P {x['P_ok']:.4f} relight {x['relight_ok']:.4f} exh {x['exhausted']} prg {x['prg_mass_g']} liq {x['liq_left_g']} <80g {x['n_below_80g']} <59g {x['n_below_59g']} worst {x['worst5'][:3]}")
    if "shift_G80_minus_G73_g" in v:
        print("  shift", v["shift_G80_minus_G73_g"], v["paired_ok_G80_vs_G73"])

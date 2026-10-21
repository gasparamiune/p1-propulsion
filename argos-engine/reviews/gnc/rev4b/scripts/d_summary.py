"""REV-GNC-7 (d)/(c): windows per variant from the m2_eng11_fe-format JSONs (reviewer runs and, for comparison, the author's)."""
import json, glob, os, sys
def windows(ks):
    ks = sorted(ks); out = []; s = None
    for i, k in enumerate(ks):
        if s is None: s = k
        if i == len(ks) - 1 or ks[i + 1] - k > 5.01: out.append((s, k)); s = None
    return out
def fmt(w, lo=90, hi=160):
    if not w: return "NONE"
    return ", ".join((("<= " if a <= lo else "") + f"{a:g}" + ("-" + (">= " if b >= hi else "") + f"{b:g}" if b != a else ("->= " if b >= hi else "")) ) for a, b in w)
res = {}
for f in sys.argv[2:]:
    for p in sorted(glob.glob(f)):
        d = json.load(open(p))
        if "variant" not in d or "rows" not in d: continue
        v = d["variant"]; rows = d["rows"]
        ksall = sorted({float(k.split("Ks")[1]) for k in rows})
        pa = {a: [float(k.split("Ks")[1]) for k, r in rows.items() if k.startswith(a + "|") and r.get("pass_6dB")] for a in ("alpha", "beta")}
        both = sorted(set(pa["alpha"]) & set(pa["beta"]))
        gm = {a: {f"{float(k.split('Ks')[1]):g}": r.get("gm_up_min_dB") for k, r in rows.items() if k.startswith(a + "|")} for a in ("alpha", "beta")}
        ff = {k: r.get("first_fail") for k, r in rows.items() if not r.get("pass_6dB")}
        res[f"{os.path.basename(os.path.dirname(p))}/{v}"] = dict(file=p, done=d.get("done"), J=d["J_kgm2"], spec=d["spec"], Ks_grid=ksall,
            alpha_windows=fmt(windows(pa["alpha"])), beta_windows=fmt(windows(pa["beta"])), both_axes=fmt(windows(both)), both_Ks=both,
            gm_min_in_both={f"{k:g}": min(gm["alpha"][f"{k:g}"], gm["beta"][f"{k:g}"]) for k in both}, first_fail=ff)
json.dump(res, open(sys.argv[1], "w"), indent=1)
for k, r in res.items():
    print(f"{k:28s} J {r['J']:.2e} done {r['done']}  alpha {r['alpha_windows']:24s} beta {r['beta_windows']:24s} BOTH {r['both_axes']}")

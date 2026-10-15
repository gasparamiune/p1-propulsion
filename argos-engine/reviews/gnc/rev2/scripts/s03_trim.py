import sys; sys.path.insert(0, ".")
from rvlib import *
B2 = ("A1_none", "A1J_pc")
def pooled(ref, case, bases=B2):
    a, b = [], []
    for bs in bases:
        ra, rb = load(bs, ref), load(bs, case)
        if ra is None or rb is None: return None
        a += ok(ra); b += ok(rb)
    return mcnemar(a, b)
for arm, ref in (("pw|G73|L400o", "pw|G73|L400"), ("liq|G73|L400o", "liq|G73|L400"), ("liq|G73|L400o", "liq|none|L400")):
    print(f"{arm} vs {ref}: {fmt(pooled(ref, arm))}")
print("== trim arms")
for h in (290, 285, 280):
    for st in ("liq", "pw"):
        a = f"{st}|G73|h{h}"
        print(f"{a:14s} vs {st}|G73: {fmt(pooled(st+'|G73', a))} || vs liq|none(300): {fmt(pooled('liq|none', a))}")
# failure mode detail for h285/h290/h280 'no_touchdown_or_crash'
def fm(r):
    if float(r["landed"]) < 0.5 or float(r.get("crash", 0)) > 0.5: return "ntd_crash"
    if float(r["exhausted"]) > 0.5: return "exh"
    if float(r["tipover"]) > 0.5: return "tip"
    return "other"
print("== crash/no-touchdown runs in trim arms and their 300 m twins")
cols = ["run","ok","landed","crash","td_vz","td_vh","exhausted","liq_left","h_ign","relight_ok","t_relight","start_delay","pgg_h0","pgg_hE0","pgg_dly","pgg_src","rel_t","min_h_cut","wind","h_max","prg_mass","t_end","starts"]
for b in B2:
    for st in ("liq", "pw"):
        for h in (290, 285, 280):
            r = load(b, f"{st}|G73|h{h}"); r0 = load(b, f"{st}|G73")
            for x in r:
                if fm(x) == "ntd_crash":
                    i = int(x["run"]); y = r0[i]
                    print(f"{b} {st} h{h} run {i}:", {k: round(float(x[k]),3) for k in cols if k in x})
                    print(f"      300m twin:", {k: round(float(y[k]),3) for k in cols if k in y})

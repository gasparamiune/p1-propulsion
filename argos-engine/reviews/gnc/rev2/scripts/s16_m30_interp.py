"""Reviewer DERIVED: usable reserve (liq_left - 3 % of m_n2o, the author's definition) of the tail runs vs apogee target and +0.60 kg,
to judge the lead's 0.30 kg trigger (no 0.30 kg arm flown)."""
import sys; sys.path.insert(0, "."); from rvlib import *
B2 = ("A1_none", "A1J_pc")
arms = ["liq|G73", "liq|G73|h290", "liq|G73|h285", "liq|G73|h280", "liq|G73|h275", "liq|G73|m60", "liq|G73|m60|h290", "liq|G73|m60|h280", "liq|G73|m60|h275",
        "pw|G73|h285", "pw|G73|m60|h280"]
for b in B2:
    print("==", b)
    for a in arms:
        r = load(b, a)
        if r is None: print(f"  {a:18s} not flown"); continue
        us = {int(f(x, "run")): 1e3 * (f(x, "liq_left") - 0.03 * f(x, "m_n2o")) for x in r}
        low = sorted(us.items(), key=lambda kv: kv[1])[:4]
        print(f"  {a:18s} " + " ".join(f"r{k}:{v:6.1f}" for k, v in low) + " | r14 %.1f r108 %.1f r490 %.1f" % (us[14], us[108], us[490]))

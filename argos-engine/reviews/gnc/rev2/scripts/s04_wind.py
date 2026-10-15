import sys; sys.path.insert(0, ".")
from rvlib import *
import numpy as np
for b in ("A1_none", "A1J_pc"):
    for arm in ("liq|none", "liq|G73", "liq|G73|h285", "pw|G73", "pw|G73|h285"):
        r = load(b, arm); w = np.array([f(x, "wind") for x in r]); o = np.array(ok(r))
        print(f"{b} {arm:14s} wind p50 {np.percentile(w,50):.2f} p99 {np.percentile(w,99):.2f} max {w.max():.2f} n(w>=6) {np.sum(w>=6)}; fails {np.sum(~o)}, fails w>=6 {np.sum(~o & (w>=6))}; P(w<6) {o[w<6].mean():.4f} ({np.sum(o[w<6])}/{np.sum(w<6)})")

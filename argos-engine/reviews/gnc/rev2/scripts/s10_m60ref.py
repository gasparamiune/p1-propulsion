import sys; sys.path.insert(0, "."); from rvlib import *
B2 = ("A1_none", "A1J_pc")
for arm in ("liq|G73|m60", "pw|G73|m60"):
    for ref in ("liq|none", "liq|none|m60", "liq|G73", "pw|G73"):
        A, Bb = [], []; per = []
        for b in B2:
            ra, rb = load(b, ref), load(b, arm); m = mcnemar(ok(ra), ok(rb)); per.append(f"{b} -{m['lost']}/+{m['gained']} p {m['p']:.3f}{' LOSES' if m['loses'] else ''}")
            A += ok(ra); Bb += ok(rb)
        print(f"{arm:12s} vs {ref:13s}: {' | '.join(per)} || pooled {fmt(mcnemar(A, Bb))}")

"""rv06_purge_reserve v1.0 (REV-GNC-R1, independent reviewer, 2026-10-13).

Question (lead decision CHANGELOG l.160 (5)): the purge is planned at <= 76 g per A1 relight in the A1 reserve; "GNC re-fly checks
the A1 reserve at 76 g (PS10 had 2+2 exhausted draws); if exhaustion remains, line the segment (saves ~0.3 s) or trim A1 apogee".
What do GNC's own published tables say about the purge mass that the A1 reserve tolerates without exhaustion?

Data (hub-published, same seed-101 draws, decided release rule, stored v2.8 FSW, balanced vent):
  rel_<base>_rel1      decided rule, no purge (rev1 results/release_rule)
  pc_<base>_PS08/PS10  pre-scheduled purge at 20.1 / 31.3 g/s, flown durations 2.58-3.43 s (rev1 results/purge_cost)
Method (reviewer, first order): per run, d_liq = liq_left(rel1) - liq_left(PS) against prg_mass; fit d_liq = alpha * prg_mass
through the origin on the runs that land in both arms (result: alpha 1.011-1.013, i.e. the reserve falls by the purged mass and
about 1 % more; the lighter landing gives no visible relief at this resolution);
usable reserve u_i = liq_left(rel1)_i - u3 with u3 the unusable 3 % (ASSUMED in GNC's model, read from the exhausted runs of the
PS arms as their liq_left); the largest purge mass with no new exhaustion is then about min_i u_i / alpha (DERIVED; valid near
the fitted range only). Purge masses evaluated: Combustion's plan 76 g; 31.25 g/s x 2.5 s = 78.1 g (all liquid); lining the
segment (-0.3 s) 31.25 x 2.2 = 68.8 g; and the PS10 p50 94.5 g.
Output: rv06_purge_reserve.json. Reads only.
"""
import csv
import gzip
import io
import json
import os

import numpy as np

REV1 = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/rev1/results"
HERE = os.path.dirname(os.path.abspath(__file__))


def rows(p):
    return list(csv.DictReader(io.StringIO(gzip.open(p).read().decode())))


def col(r, k):
    return np.array([float(x[k]) for x in r])


def main():
    out = dict(version="rv06_purge_reserve v1.0", bases={})
    for base in ("A1_none", "A1J_pc"):
        ref = rows(f"{REV1}/release_rule/rel_{base}_rel1.csv.gz")
        b = dict()
        lr = col(ref, "liq_left")
        okr = col(ref, "ok") > 0.5
        exr = col(ref, "exhausted") > 0.5
        for arm in ("PS08", "PS10"):
            r = rows(f"{REV1}/purge_cost/pc_{base}_{arm}.csv.gz")
            lp, pm, ok, ex = col(r, "liq_left"), col(r, "prg_mass"), col(r, "ok") > 0.5, col(r, "exhausted") > 0.5
            both = okr & ok & ~exr & ~ex
            d = lr - lp
            alpha = float(np.sum(d[both] * pm[both]) / np.sum(pm[both] ** 2))
            resid = d[both] - alpha * pm[both]
            u3 = float(np.median(lp[ex])) if ex.any() else None
            b[arm] = dict(alpha=alpha, resid_sd_g=float(1e3 * np.std(resid)), n_fit=int(both.sum()),
                          prg_mass_g=dict(min=float(1e3 * pm.min()), p50=float(1e3 * np.median(pm)), max=float(1e3 * pm.max())),
                          exhausted_runs=[int(i) for i in np.where(ex)[0]], liq_left_of_exhausted_g=[float(1e3 * x) for x in lp[ex]],
                          unusable_g_from_exhausted=None if u3 is None else 1e3 * u3)
        u3 = b["PS10"]["unusable_g_from_exhausted"] or b["PS08"]["unusable_g_from_exhausted"]
        usable = 1e3 * lr - u3
        order = np.argsort(usable)
        alpha = b["PS10"]["alpha"]
        b["decided_rule"] = dict(liq_left_min_g=float(1e3 * lr.min()), unusable_g=u3,
                                 lowest_usable_g=[dict(run=int(i), usable_g=float(usable[i])) for i in order[:5]],
                                 exhausted_in_ref=int(exr.sum()))
        umin = float(usable[order[0]])
        b["purge_mass_limit_g_first_order"] = umin / alpha
        b["predicted_new_exhaustions"] = {f"{m:.1f}g": int(np.sum(usable < alpha * m)) for m in (50.0, 60.5, 68.8, 76.0, 78.1, 94.5)}
        out["bases"][base] = b
    out["reading"] = ("alpha is about 1.01 (the reserve falls by the purged mass and about 1 % more); the first-order limit is the "
                      "purge mass at which the lowest-reserve draw reaches the unusable residual; predicted_new_exhaustions counts "
                      "runs whose usable reserve is below alpha x purge mass (DERIVED from GNC's tables; the re-fly decides)")
    with open(os.path.join(HERE, "rv06_purge_reserve.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1)[:6000])


if __name__ == "__main__":
    main()

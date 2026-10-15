"""rg14_corner_mc v1 (independent GNC review, 2026-10-13): Monte Carlo of B1 at the 62 m cap CONDITIONAL on the governing
regression corner, instead of averaging over the band.

Why: the regression law (a, n) and the delivered thrust per flow of a built engine are fixed properties of that engine
(epistemic), but the published case rbl_B1_lead62_pc_k2 draws (a, n) uniformly per run, so its P 0.996 averages engines.
Only 17 of its 500 runs have a < 0.8 and n > 0.6. The cap was set on the nominal flight at (a 0.6, n 0.68, g 0.11).
Cases (author's code unchanged, rg05 harness; seed 101, 500 runs; every other dispersion identical to the published run
table, since the band and growth come from their own generators):
  corner     : reg_a 0.6, reg_n 0.68, throat_g 0.11 fixed (J_ref of the no-band 62 m flight, as in rbl)
  corner_k97 : the same with thrust_scale x 0.97 on every run (a 3 % C_F c* shortfall, inside the MC's own N(1, 0.05))
Output: rg14_corner_mc.json. One process.
"""
import csv
import gzip
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import rg05_sens as S  # noqa: E402

PUB = "/home/claude/work/shared-fallback/engine/01-systems-gnc/results/regband/mc6_runs_rbl_B1_lead62_pc_k2_rb.csv.gz"


def main():
    jl = float(S.TG.j_ref(dict(S.RBM.B1, h_target=62.0))[0])
    over = dict(S.RBM.B1, h_target=62.0, m_fixed=S.PC.M_TANK, throat_jref=jl, throat_loop=1, throat_g=0.11, reg_a=0.6, reg_n=0.68)
    with gzip.open(PUB, "rt") as f:
        pub_ok = [bool(int(float(r["ok"]))) for r in csv.DictReader(f)]
    out = dict(script="rg14_corner_mc v1", J_ref=jl, cases={})
    base_rows = None
    for nm, mod in (("corner a0.6 n0.68 g0.11", {}), ("corner + thrust x0.97", dict(thrust=0.97))):
        t0 = time.time()
        rows = S.fly_case(over, mod)
        s = S.summ(rows)
        lost = sum(1 for a, b in zip(pub_ok, rows) if a and not b["ok"])
        gained = sum(1 for a, b in zip(pub_ok, rows) if (not a) and b["ok"])
        s.update(vs_published_band=dict(lost=lost, gained=gained, p_exact=S.mcnemar(lost, gained)))
        if base_rows is not None:
            s.update(vs_corner=S.paired(base_rows, rows))
        else:
            base_rows = rows
        out["cases"][nm] = s
        print(nm, json.dumps(s), f"{time.time() - t0:.0f}s", flush=True)
        json.dump(out, open(os.path.join(HERE, "rg14_corner_mc.json"), "w"), indent=1)


if __name__ == "__main__":
    main()

"""m2_bit29_runner v1.0 (GNC rev2, 2026-10-13): subprocess helper of m2_bitcheck_v29.
Flies prepared cases with whatever gncsim package is first on sys.path (--sim DIR puts DIR first), so that the rev1
simulator copy (sim6 v2.8-dev) and the rev2 one (v2.9-dev) can be run on identical (cfg, disp) inputs, and runs the
strict-input checks (N1-N4) in a clean process with a modified environment.
Usage: python m2_bit29_runner.py --sim DIR --jobs IN.pkl --out OUT.pkl        (fly jobs [(name, cfg, disp)])
       python m2_bit29_runner.py --sim DIR --sources A1_none                  (load interface files, build the base)"""
import os
import pickle
import sys


def main():
    a = sys.argv[1:]
    sim = a[a.index("--sim") + 1] if "--sim" in a else None
    if sim:
        sys.path.insert(0, sim)
    here = os.path.dirname(os.path.abspath(__file__))
    from gncsim import run6 as R, sim6 as s6
    print("SIM", s6.SIM6_VERSION, os.path.dirname(os.path.abspath(R.__file__)), flush=True)
    if "--sources" in a:
        sys.path.insert(1, here)
        src = R.sources()
        print("VERSIONS", src["comb"].get("version"), src["el"].get("version"), src["mech"].get("version"), flush=True)
        import m2_eng03_rate as E
        import json
        over, _, bj = E.base_ref(a[a.index("--sources") + 1])
        m = json.load(open(bj))["m_n2o_mc_kg"]
        cfg = R.cfg_of(**dict({k: v for k, v in over.items() if k != "m_fixed"}, m_n2o=float(m)))
        R.build(cfg)
        print("BUILD_OK", flush=True)
        return
    jobs = pickle.load(open(a[a.index("--jobs") + 1], "rb"))
    out = {}
    for name, c, disp in jobs:
        c = {k: v for k, v in c.items() if k in R.DEF}        # keys this simulator version knows
        res = R.fly(c, disp, nrec=10)[0]
        out[name] = {k: float(res[k]) for k in s6.RES_NAMES}
    pickle.dump(dict(sim=s6.SIM6_VERSION, res=out), open(a[a.index("--out") + 1], "wb"))
    print("DONE", len(out), flush=True)


if __name__ == "__main__":
    main()

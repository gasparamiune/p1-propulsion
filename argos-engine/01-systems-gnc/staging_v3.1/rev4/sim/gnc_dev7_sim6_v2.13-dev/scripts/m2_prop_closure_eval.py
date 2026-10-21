"""m2_prop_closure_eval v1.1 (2026-10-12; v1.1 adds base pc2n = mechanical.json v2 WITHOUT the ratchet, paired
against pc2 for the ratchet effect on mech v2): evaluation of the propellant-closure Monte Carlo (m2_prop_closure.py).
For every evaluated basis (folder + suffix): P (Wilson 95 %), failure modes, propellant-limited failures (exhausted, or
usable liquid at touchdown below 5 g), liquid left p01 / min, paired exact McNemar of each case against the same cycle
at 2.00 kg, and across bases for the same case name (same draws, seed 101): ratchet effect (pcr vs pc) and the
mechanical.json v2 effect (pc2 vs pcr). Also the nominal closure table (N2O needed with the +25 % rule, v2 rule, hop /
apogee limits at 2.00 kg, larger tank) per basis.
Env: GNC_PC_BASES ('label=folder:suffix;...'; default pc, pcr in out/prop_closure and pc2 in out/prop_closure_m2),
GNC_OUT (default out/prop_closure_eval). Output: <out>/prop_closure_eval.json"""
import csv
import json
import os
import numpy as np
from scipy.stats import binomtest

S = "/home/claude/work/space/out"
DEF_BASES = (f"pc={S}/prop_closure:pc;pcr={S}/prop_closure:pcr;pc2={S}/prop_closure_m2:pc2;"
             f"pc2n={S}/prop_closure_m2n:pc2n")
OUT = os.environ.get("GNC_OUT", f"{S}/prop_closure_eval")
TRAP = 0.03
CYC = ("A1", "A2", "B1")


def wilson(k, n, z=1.96):
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    hw = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [max(0.0, c - hw), min(1.0, c + hw)]


def rows(folder, suf, case):
    p = os.path.join(folder, f"mc6_runs_{case}_{suf}.csv")
    return list(csv.DictReader(open(p))) if os.path.exists(p) else None


def pair(a, b):
    oa = np.array([int(r["ok"]) for r in a]) > 0
    ob = np.array([int(r["ok"]) for r in b]) > 0
    lost, gained = int(np.sum(oa & ~ob)), int(np.sum(~oa & ob))
    p = binomtest(lost, lost + gained, 0.5).pvalue if lost + gained else 1.0
    return dict(lost=lost, gained=gained, p=float(p), P_a=float(oa.mean()), P_b=float(ob.mean()),
                significant=bool(p < 0.05))


def case_stats(r, m_load):
    ok = np.array([int(x["ok"]) for x in r]) > 0
    liq = np.array([float(x["liq_left"]) for x in r])
    exh = np.array([float(x["exhausted"]) for x in r]) > 0.5
    usable = liq - TRAP * m_load
    prop_lim = (~ok) & (exh | (usable < 0.005))
    return dict(n=len(r), P=float(ok.mean()), ci95=wilson(int(ok.sum()), len(ok)), n_fail=int((~ok).sum()),
                n_fail_propellant_limited=int(prop_lim.sum()), n_exhausted=int(exh.sum()),
                liq_left_p01=float(np.percentile(liq, 1)), liq_left_min=float(liq.min()),
                usable_left_p01=float(np.percentile(usable, 1)))


def main():
    bases = {}
    for tok in os.environ.get("GNC_PC_BASES", DEF_BASES).split(";"):
        lab, rest = tok.split("=")
        folder, suf = rest.split(":")
        bases[lab] = (folder, suf)
    res = dict(version="m2_prop_closure_eval v1.1", trapped_frac=TRAP, bases={})
    for lab, (folder, suf) in bases.items():
        pj = os.path.join(folder, f"prop_closure_{suf}.json")
        sj = os.path.join(folder, f"mc6_summary_{suf}.json")
        if not (os.path.exists(pj) and os.path.exists(sj)):
            print(f"{lab}: missing {pj} or {sj}")
            continue
        pc = json.load(open(pj))
        summ = json.load(open(sj))["cases"]
        b = dict(sim=pc.get("sim"), interfaces=pc.get("interfaces"), flight_software=pc.get("flight_software"),
                 nominal={k: dict(needed_kg=pc["closure"][k]["needed_kg"], v2_rule_kg=pc["closure"][k]["v2_rule_kg"],
                                  reserve_at_2kg=pc["closure"][k]["at_2kg"]["reserve_frac"],
                                  burned_at_2kg=pc["closure"][k]["at_2kg"]["n2o_burned"],
                                  vapour_left_at_2kg=pc["closure"][k]["at_2kg"]["vapour_left"],
                                  isp_at_2kg=pc["closure"][k]["at_2kg"]["isp_delivered_s"],
                                  m_liftoff_at_2kg=pc["closure"][k]["at_2kg"]["m_liftoff"],
                                  TW_at_2kg=pc["closure"][k]["at_2kg"]["TW_liftoff"])
                          for k in pc["closure"]},
                 limits_at_2kg={k: pc["trades"].get(f"{k}_max_h_target_closing_at_2kg_m") for k in CYC},
                 larger_tank={k: dict(load_kg=v["closing_load_kg"], tank_V_L=v["at_load"]["tank_V_L"],
                                      m_liftoff=v["at_load"]["m_liftoff"], TW=v["at_load"]["TW_liftoff"],
                                      others=v["other_cycles_at_this_load"])
                              for k, v in pc["trades"].get("larger_tank", {}).items()},
                 floors=pc["trades"].get("floors"), cases={})
        for c, o in summ.items():
            r = rows(folder, suf, c)
            if r is None:
                continue
            st = case_stats(r, float(o["m_n2o_mc_kg"]))
            st.update(note=o.get("note"), m_n2o_kg=o["m_n2o_mc_kg"], m_liftoff_kg=o["m_liftoff_kg"], tank_V_L=o["tank_V_L"],
                      fail_modes=o["summary"]["fail_modes"])
            cyc = c.split("_")[1]
            ref = f"pc_{cyc}_2kg"
            if c != ref:
                rr = rows(folder, suf, ref)
                if rr is not None:
                    st["vs_" + ref] = pair(rr, r)
            b["cases"][c] = st
        res["bases"][lab] = b
        print(f"== {lab} ({folder}, {suf}) sim {b['sim']} interfaces {b['interfaces']}")
        for k in ("A1", "A2", "B1", "B2"):
            if k in b["nominal"]:
                n = b["nominal"][k]
                print(f"   {k}: needed (+25 %) {n['needed_kg']:.3f} kg | v2 rule {n['v2_rule_kg']:.3f} | reserve at 2.00 kg "
                      f"{100 * n['reserve_at_2kg']:.1f} % | burned {n['burned_at_2kg']:.3f} vapour {n['vapour_left_at_2kg']:.3f} | "
                      f"Isp {n['isp_at_2kg']:.1f} s | liftoff {n['m_liftoff_at_2kg']:.3f} kg T/W {n['TW_at_2kg']:.2f}")
        print(f"   limits at 2.00 kg: {b['limits_at_2kg']}")
        for c, st in b["cases"].items():
            v = next((st[k] for k in st if k.startswith("vs_")), None)
            print(f"   {c:18s} P {st['P']:.3f} [{st['ci95'][0]:.3f},{st['ci95'][1]:.3f}] fails {st['n_fail']} "
                  f"(propellant-limited {st['n_fail_propellant_limited']}) liq p01 {st['liq_left_p01']:.3f}"
                  + (f" | vs 2kg -{v['lost']}/+{v['gained']} p {v['p']:.2g}" if v else ""))
    # across bases, same case name
    cross = {}
    labs = list(res["bases"])
    for a, b_ in (("pc", "pcr"), ("pcr", "pc2"), ("pc", "pc2"), ("pc2n", "pc2")):
        if a in bases and b_ in bases and a in res["bases"] and b_ in res["bases"]:
            for c in res["bases"][a]["cases"]:
                if c in res["bases"][b_]["cases"]:
                    ra = rows(bases[a][0], bases[a][1], c)
                    rb = rows(bases[b_][0], bases[b_][1], c)
                    if ra and rb:
                        cross[f"{b_}_vs_{a}|{c}"] = pair(ra, rb)
    res["cross"] = cross
    print("== across bases (same draws)")
    for k, v in cross.items():
        print(f"   {k:32s} P {v['P_a']:.3f} -> {v['P_b']:.3f}  -{v['lost']}/+{v['gained']} p {v['p']:.2g}")
    res["bases_order"] = labs
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "prop_closure_eval.json"), "w") as f:
        json.dump(res, f, indent=1, default=float)


if __name__ == "__main__":
    main()

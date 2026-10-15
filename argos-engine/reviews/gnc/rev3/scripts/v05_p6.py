"""REV-GNC-5 v05: independent recomputation of the P6 late-commit table from the staged rev3 tables (SIM tables, DERIVED
statistics): P (Wilson) per arm and base, realised commit lead (plain-trigger time - commit, runs where the plain trigger
fired before E0), T_fire after the plain trigger, E0 height, P by realised-lead bin pooled over the contingency arms, paired
exact McNemar against the decided horizon and against liq|none, and the gate-delay tolerance re-derived (the 2.90 s lower
bound for non-fired runs is checked against E0 - commit in the same run). Output JSON + log."""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rv5lib as L

out = dict(script="v05_p6 (REV-GNC-5)", tag="SIM tables; DERIVED statistics", arms={}, by_lead={}, paired={}, gate={})
ANT = (13, 17, 21, 25)
for plat in ("", "L400|"):
    names = [f"e19|G73|{plat}h285"] + [f"e19|G73|{plat}ant{a}|h285" for a in ANT]
    for nm in names:
        for b in L.MAIN:
            rows = L.load3(b, nm)
            o = L.ok(rows); n = len(o); k = sum(o)
            t0 = L.col(rows, "pgg_t0"); tgo = L.col(rows, "pgg_tgo"); tE0 = L.col(rows, "pgg_tE0")
            fired = [g > 0 for g in tgo]
            lead = [g - c for g, c, f in zip(tgo, t0, fired) if f]
            tf = [e - g for e, g, f in zip(tE0, tgo, fired) if f]
            out["arms"][f"{b}|{nm}"] = dict(n=n, P=round(k / n, 4), wilson=[round(x, 4) for x in L.wilson(k, n)],
                                            fired=sum(fired), lead_min_p50_max=L.q(lead), tfire_after_plain=L.q(tf),
                                            E0_h=L.q(L.col(rows, "pgg_hE0")), table_sha16=L.sha16(L.path3(b, nm)))
            ref = L.load3(b, f"e19|G73|{plat}h285"); ref2 = L.load3(b, f"liq|none|{plat}h285")
            if nm != f"e19|G73|{plat}h285":
                out["paired"][f"{b}|{nm} vs e19|G73|{plat}h285"] = L.paired(ref, rows)
                out["paired"][f"{b}|{nm} vs liq|none|{plat}h285"] = L.paired(ref2, rows)
    # P by realised lead (pooled over contingency arms and both bases); runs whose plain trigger did not fire before E0
    # carry lead >= E0 - commit (checked) and go to a separate bin
    bins = ((2.9, 99.0), (2.4, 2.9), (2.1, 2.4), (1.9, 2.1), (1.7, 1.9), (1.5, 1.7), (1.3, 1.5), (0.0, 1.3))
    acc = {f"{lo}-{hi}": [0, 0] for lo, hi in bins}; acc["not_fired"] = [0, 0]
    for a in ANT:
        for b in L.MAIN:
            rows = L.load3(b, f"e19|G73|{plat}ant{a}|h285")
            for r, o in zip(rows, L.ok(rows)):
                tgo = float(r["pgg_tgo"]); t0 = float(r["pgg_t0"])
                if tgo <= 0:
                    acc["not_fired"][0] += 1; acc["not_fired"][1] += o; continue
                ld = tgo - t0
                for lo, hi in bins:
                    if lo <= ld < hi:
                        acc[f"{lo}-{hi}"][0] += 1; acc[f"{lo}-{hi}"][1] += o
                        break
    out["by_lead"]["L400" if plat else "nominal"] = {k: dict(n=v[0], ok=v[1], P=(round(v[1] / v[0], 4) if v[0] else None),
                                                         wilson=([round(x, 4) for x in L.wilson(v[1], v[0])] if v[0] else None))
                                                     for k, v in acc.items()}
# gate-delay tolerance (DERIVED): commit = max(predictor, gate open); slack = commit - gate open; lead_nom = fired lead,
# else E0 - commit (lower bound actually present in the run) and the author's 2.90 s
for nm in ("e19|G73|h285", "liq|G73|h285", "pw|G73|h285", "pl|G73|h285", "e19|G73|L400|h285", "liq|none|h285"):
    for b in L.ALL4:
        rows = L.load3(b, nm)
        if not rows:
            continue
        t0 = L.col(rows, "pgg_t0"); top = L.col(rows, "pgg_topen"); tgo = L.col(rows, "pgg_tgo"); tE0 = L.col(rows, "pgg_tE0")
        if max(t0) <= 0:
            continue
        sl = [c - o for c, o in zip(t0, top)]
        fired = [g > 0 for g in tgo]
        ln_auth = [(g - c) if f else 2.90 for g, c, f in zip(tgo, t0, fired)]
        ln_e0 = [(g - c) if f else (e - c) for g, c, e, f in zip(tgo, t0, tE0, fired)]
        out["gate"][f"{b}|{nm}"] = dict(n=len(rows), fired=sum(fired), slack_min=round(min(sl), 3),
                                       nonfired_E0_minus_commit=L.q([e - c for e, c, f in zip(tE0, t0, fired) if not f]),
                                       fired_lead=L.q([g - c for g, c, f in zip(tgo, t0, fired) if f]),
                                       Dcrit_min={str(Lx): [round(min(s + l for s, l in zip(sl, ln_auth)) - Lx, 3),
                                                            round(min(s + l for s, l in zip(sl, ln_e0)) - Lx, 3)]
                                                  for Lx in (2.4, 2.1, 1.9, 1.3)})
json.dump(out, open(sys.argv[1], "w"), indent=1)
print("P table (A1_none / A1J_pc):")
for plat in ("", "L400|"):
    for nm in [f"e19|G73|{plat}ant{a}|h285" for a in ANT] + [f"e19|G73|{plat}h285"]:
        a = out["arms"][f"A1_none|{nm}"]; c = out["arms"][f"A1J_pc|{nm}"]
        print(f"  {nm:28s} {a['P']:.3f} / {c['P']:.3f}  lead p50 {a['lead_min_p50_max'][1] if a['lead_min_p50_max'] else '-'} / "
              f"{c['lead_min_p50_max'][1] if c['lead_min_p50_max'] else '-'}  fired {a['fired']}/{c['fired']}  E0 h p50 {a['E0_h'][1]} / {c['E0_h'][1]}")
print("paired:")
for k, d in out["paired"].items():
    print(f"  {k:62s} {L.fmt(dict(d, loses=d['P_case'] < d['P_ref'] and d['p'] < 0.05))}")
print("P by realised lead:", json.dumps(out["by_lead"]))
print("gate (Dcrit min [author 2.90 rule, E0 bound]):")
for k, d in out["gate"].items():
    print(f"  {k:28s} fired {d['fired']:3d} slack_min {d['slack_min']} nonfired E0-commit {d['nonfired_E0_minus_commit']} Dcrit {d['Dcrit_min']}")

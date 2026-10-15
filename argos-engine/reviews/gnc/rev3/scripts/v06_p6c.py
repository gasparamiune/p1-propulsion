"""REV-GNC-5 v06: independent recomputation of the P6c comparator (unpurged relight with an ECU release hold) from the
staged rev3 SIM tables and the Combustion reviewer's population table (reviews/combustion/r3/r3_unpurged_classes.json).
P_GNC (Wilson) per arm/base, paired exact McNemar against the release-at-E2 reference (nrLO|none|h285) and against
liq|none|h285, pooled over both main bases; profile time and truth thrust under the profile; residual released-then-A3
per group from the hold-by-mode table (200 N ramp) and the frame rule for 500 N; P_total = P_success x P_GNC per group
for the 'best' (author: ramp) and 'worst' (lift flow) population means.  SIM tables + Combustion DERIVED table ->
DERIVED.  Nothing here is physical evidence.  Usage: python -I v06_p6c.py <out.json>"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rv5lib as L

UC = f"{L.HUB}/reviews/combustion/r3/r3_unpurged_classes.json"
POP = json.load(open(UC))["population_0_2deg"]
CL = json.load(open(f"{L.R3}/results/rev3_results.json"))["P6_late_commit"]["comparator_line194"]
ARMS = {"rh220": (0.22, None), "rh250": (0.25, None), "rh300": (0.30, None),
        "rh300c200": (0.30, 200), "rh400c200": (0.40, 200), "rh190c500": (0.19, 500)}
out = dict(script="v06_p6c (REV-GNC-5)", tag="SIM tables + Combustion review table; DERIVED", unpurged_classes_sha16=L.sha16(UC),
           arms={}, pooled={}, groups={}, ptotal={}, cmp_author={})
for g, d in POP.items():
    lat = d["latest_A3_trip_after_E2_s"]
    hb = d["hold_by_mode"]
    out["groups"][g] = dict(P_success_best=d["mean_best"]["P_success"], P_success_worst=d["mean_worst"]["P_success"],
                            latest_trip=lat,
                            frame_rule_200N_H030=(0.30 >= lat["ramp_to_200N"] + 0.010), margin_200N_H030_ms=round((0.30 - lat["ramp_to_200N"] - 0.010) * 1e3, 2),
                            frame_rule_500N_H019=(0.19 >= lat["ramp_to_500N"] + 0.010), margin_500N_H019_ms=round((0.19 - lat["ramp_to_500N"] - 0.010) * 1e3, 2),
                            hold_ramp200={h: hb[f"{h}|ramp_to_200N"] for h in ("0.22", "0.25", "0.30", "0.40")},
                            hold_liftflow={h: hb[f"{h}|lift_flow_held"] for h in ("0.22", "0.25", "0.30", "0.40", "0.65")})
for arm, (H, Fc) in ARMS.items():
    nm = f"nrLO|none|{arm}|h285"
    pr_e2, pr_liq = [], []
    for b in L.MAIN:
        rows = L.load3(b, nm); o = L.ok(rows); k = sum(o); n = len(o)
        ref = L.load3(b, "nrLO|none|h285"); ref2 = L.load3(b, "liq|none|h285")
        d1 = L.paired(ref, rows); d2 = L.paired(ref2, rows)
        pr_e2.append(d1); pr_liq.append(d2)
        tp = L.col(rows, "pv3_rhp_s") if "pv3_rhp_s" in rows[0] else []
        fm = L.col(rows, "pv3_Frhp_max") if "pv3_Frhp_max" in rows[0] else []
        out["arms"][f"{b}|{nm}"] = dict(n=n, P=round(k / n, 4), wilson=[round(x, 4) for x in L.wilson(k, n)],
                                        vs_release_at_E2=d1, vs_liq_none=d2, profile_time=L.q(tp), F_truth_max_under_profile=L.q(fm),
                                        table_sha16=L.sha16(L.path3(b, nm)))
        a = CL["arms"].get(nm, {}).get(b, {})
        va = a.get("vs_nrLO_release_at_E2", {})
        out["cmp_author"][f"{b}|{nm}"] = dict(P_author=a.get("P_GNC"), P_mine=round(k / n, 4),
                                              lost_gained_author=[va.get("lost"), va.get("gained")], lost_gained_mine=[d1["lost"], d1["gained"]],
                                              p_author=va.get("p_exact"), p_mine=d1["p"],
                                              tprof_author=a.get("profile_time_s"), Fmax_author=a.get("F_truth_max_under_profile_N"))
    out["pooled"][nm] = dict(vs_release_at_E2=L.pooled(pr_e2), vs_liq_none=L.pooled(pr_liq))
    # P_total per group (min over the two main bases of P_GNC), only for profiles in the hold table (200 N) or the frame rule
    pg = [out["arms"][f"{b}|{nm}"]["P"] for b in L.MAIN]
    pt = {}
    for g, d in out["groups"].items():
        if Fc == 200:
            hz = d["hold_ramp200"].get(f"{H:.2f}")
            pt[g] = dict(best=[round(d["P_success_best"] * p, 4) for p in pg], worst=[round(d["P_success_worst"] * p, 4) for p in pg],
                         residual_released_then_A3_ramp200=hz)
        elif Fc == 500:
            pt[g] = dict(best_if_500N_equals_best=[round(d["P_success_best"] * p, 4) for p in pg], covered_by_frame_rule=d["frame_rule_500N_H019"],
                         note="no per-record 500 N P_success in the population table")
        else:
            pt[g] = dict(residual_released_then_A3_liftflow=d["hold_liftflow"].get(f"{H:.2f}"),
                         note="guidance-command profile (~100 N plateau): not in the hold table")
    out["ptotal"][nm] = pt
# expected per-flight gain of the unpurged alternative at a gate-fault probability q (DERIVED; P=0 for the decided path in the
# gate-fault band by line 204 (1)); upper bound uses the best population mean and the larger P_GNC
best = max(d["P_success_best"] for d in out["groups"].values())
pmax = max(out["arms"][f"{b}|nrLO|none|rh300c200|h285"]["P"] for b in L.MAIN)
out["expected_gain_upper_pp"] = {str(q): round(100 * q * best * pmax, 3) for q in (0.001, 0.01, 0.05)}
json.dump(out, open(sys.argv[1], "w"), indent=1, default=float)
print("groups:")
for g, d in out["groups"].items():
    print(f"  {g:10s} Psucc best {d['P_success_best']:.4f} worst {d['P_success_worst']:.4f} latest {json.dumps({k: round(v, 4) for k, v in d['latest_trip'].items()})}"
          f" frame200@0.30 {d['frame_rule_200N_H030']} ({d['margin_200N_H030_ms']} ms) frame500@0.19 {d['frame_rule_500N_H019']} ({d['margin_500N_H019_ms']} ms)")
    print(f"     ramp200 hold residual: " + "; ".join(f"{h}: mean {v['mean']:.4g} max {v['max']:.4g} cons {v['conservative_mean']:.4g}/{v['conservative_max']:.4g}" for h, v in d['hold_ramp200'].items()))
print("arms (mine vs author):")
for k, d in out["cmp_author"].items():
    a = out["arms"][k]
    print(f"  {k:40s} P {d['P_mine']} (auth {d['P_author']}) E2 -{d['lost_gained_mine'][0]}/+{d['lost_gained_mine'][1]} p {d['p_mine']:.4g} (auth {d['lost_gained_author']} {d['p_author']})"
          f" | vs liq|none {L.fmt(a['vs_liq_none'])} | tprof {a['profile_time']} Fmax {a['F_truth_max_under_profile']}")
print("pooled:")
for k, d in out["pooled"].items():
    print(f"  {k:30s} vsE2 {L.fmt(d['vs_release_at_E2'])} | vs liq|none {L.fmt(d['vs_liq_none'])}")
print("P_total:")
for k, d in out["ptotal"].items():
    print(" ", k, json.dumps(d)[:700])
print("expected gain upper (pp/flight):", out["expected_gain_upper_pp"])

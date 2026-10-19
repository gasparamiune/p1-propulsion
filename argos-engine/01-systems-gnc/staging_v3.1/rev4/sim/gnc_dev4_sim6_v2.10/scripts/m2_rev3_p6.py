"""m2_rev3_p6 v1.0 (GNC rev3, 2026-10-13): P6 late purge commit (lead CHANGELOG lines 181 (2), 186 (1)) - evaluation of the
rev3 contingency flights, the gate-delay tolerance, the release-hold alternative and the L* table in Combustion's outcome
classes.

Inputs (all read, none flown here): m2_rev3_fly v2.1 tables (sim6 v2.10-dev): e19|G73|L400|ant<X>|h285 (P6) and
e19|G73|ant<X>|h285 (P6b) - the commit predictor horizon X = 1.3 / 1.7 / 2.1 / 2.5 s puts the commit about X before the plain
relight trigger, the flight software then delays T_fire until 1.9 s of flow (amendment G, pgg_Tmin); their references
e19|G73(|L400)|h285 (decided horizon 2.90 s) and liq|none(|L400)|h285; nrLO|none|rh220 / rh250 (unpurged relight with the
drogue release held to >= E2 + 0.22 / 0.25 s) against nrLO|none|h285 (release at E2) and liq|none|h285. Combustion v2.4a
unpurged_outcomes_v2p4a.json (outcome classes per line state: no light, A3 before release, released then A3, success) and the
v2.4 line-state table used by the flights (rg01_line_states_v2p4.json, P_abort per state).
Method: (A) per arm and base: P (Wilson 95 %), the realised commit lead (first plain-trigger time - commit), T_fire after the
plain trigger, flow, E0 height, touchdown speed, failure modes; paired exact McNemar against the references. (B) P against
the realised lead, pooled over the contingency arms and bases, in lead bins. (C) gate-delay tolerance (DERIVED from the
nominal predictor tables): the commit happens at max(predictor time, gate opening); a gate opening delayed by D moves the
commit only when D > slack (commit - gate opening in the nominal run); the delay that brings the lead below L is
D_crit(L) = slack + lead_nom - L, with lead_nom = the plain-trigger lead when the plain trigger fired before E0, else the
lower bound 2.90 s. (D) the release-hold alternative: GNC trajectory P (SIM) and Combustion's classes (DERIVED/SIM):
P_total = P_success(class) x P_GNC; hazard = P_released_then_A3 (Combustion: release at E2); with the hold >= E2 + 0.22 s
the class moves to A3 before release only under Combustion's DERIVED gap-arrival bound (0.193 s, flow held at the lift) plus
the 0.022 s A3 detection. (E) the L* table: lead bins x decided action (186 (1)) x Combustion class x GNC P (nominal start and
the L400 bracket). Not modelled in the flights: lights during the vapour gap and the A3 abort itself (the classes stay
Combustion's), canopy dynamics (quasi-steady massless drogue), a commit the ECU refuses, valve-time dispersion. SIM on
DERIVED / ASSUMED inputs; no hardware data; not a physical approval.
Output: <out>/p6_late_commit.json."""
import hashlib
import json
import os
import sys
from collections import OrderedDict
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m2_rev3_fly as RF  # noqa: E402
import m2_rg01_refly as F  # noqa: E402
from gncsim import run6 as R  # noqa: E402

VERSION = "m2_rev3_p6 v1.0"
UNP = "/home/claude/work/shared-fallback/engine/02-combustion/data/v2p4a/unpurged_outcomes_v2p4a.json"
UNP_SHA16 = "18a639d61b58ce8a"
ANT = (13, 17, 21, 25)
BINS = ((2.9, 99.0), (2.4, 2.9), (1.9, 2.4), (1.3, 1.9), (0.0, 1.3))
GAP_BOUND_S = 0.193      # Combustion v2.4a (lead line 186 (1) basis): gap arrival with the flow held at the lift
A3_DETECT_S = 0.022      # Combustion v2.4a constants.A3_detect_s


def col(rows, k):
    return np.array([float(r[k]) for r in rows])


def q(x, ps=(0, 1, 50, 99, 100), nd=3):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if x.size == 0:
        return None
    return OrderedDict((("min" if p == 0 else "max" if p == 100 else f"p{p:02d}"), round(float(np.percentile(x, p)), nd))
                       for p in ps)


def wil(k, n):
    return [round(float(v), 4) for v in R.wilson(int(k), int(n))] if n else None


def arm_entry(rows):
    ok = col(rows, "ok") > 0.5
    tgo, t0, tE0 = col(rows, "pgg_tgo"), col(rows, "pgg_t0"), col(rows, "pgg_tE0")
    fired = tgo > 0.0
    fm = {}
    for r, o in zip(rows, ok):
        if not o:
            k = F.fail_mode(r)
            fm[k] = fm.get(k, 0) + 1
    w = col(rows, "wind")
    return OrderedDict(
        n=len(rows), P=round(float(ok.mean()), 4), P_wilson=wil(ok.sum(), len(rows)),
        P_W10_lt6=round(float(ok[w < 6.0].mean()), 4), n_W10_lt6=int(np.sum(w < 6.0)),
        commit_source={str(int(k)): int(np.sum(col(rows, "pgg_src") == k)) for k in (1, 2, 3)},
        plain_fired_before_E0=int(fired.sum()),
        lead_commit_to_plain_s=q((tgo - t0)[fired]), tfire_after_plain_s=q((tE0 - tgo)[fired]),
        flow_s=q(col(rows, "pgg_fl")), E0_height_m=q(col(rows, "pgg_hE0"), (0, 50, 100), 1),
        plain_height_m=q(col(rows, "pgg_hgo")[fired], (0, 50, 100), 1),
        td_vz_m_s=q(col(rows, "td_vz"), (0, 1, 50, 99, 100), 2), exhausted=int(np.sum(col(rows, "exhausted") > 0.5)),
        fail_modes=fm)


def main():
    if RF.sha16(UNP) != UNP_SHA16:
        raise RuntimeError(f"{UNP} sha256/16 {RF.sha16(UNP)} != pinned {UNP_SHA16}")
    U = json.load(open(UNP))
    cs = F.comb_states()
    out = OrderedDict(version=VERSION, date="2026-10-13", method=__doc__.split("\n\n")[1].strip(),
                      sources=OrderedDict(unpurged_outcomes=f"{UNP} ({UNP_SHA16})", line_states_v2p4=f"{F.COMB} ({F.COMB_SHA16})",
                                          tables=RF.OUT, fly=RF.VERSION),
                      contingency=OrderedDict(), lead_bins=OrderedDict(), gate_delay=OrderedDict(),
                      release_hold=OrderedDict(), lstar_table=[], findings=[], missing=[])
    # ---------------------------------------------------------------------------------------------------- (A) per arm
    pooled = {"L400": [], "nominal": []}
    for plat, pre in (("L400", "e19|G73|L400"), ("nominal", "e19|G73")):
        ref_name = f"{pre}|h285"
        for x in (None,) + ANT:
            name = ref_name if x is None else f"{pre}|ant{x}|h285"
            for base in F.BASES_MAIN:
                rows, p, org = RF.table(base, name)
                if not rows:
                    out["missing"].append(f"{base}|{name}")
                    continue
                e = arm_entry(rows)
                e["table"] = dict(path=p, origin=org, sha256_16=RF.sha16(p))
                if x is not None:
                    for rn in (ref_name, ("liq|none|L400|h285" if plat == "L400" else "liq|none|h285")):
                        rr, rp, ro = RF.table(base, rn)
                        if rr:
                            d = RF.pair(rr, rows)
                            e[f"vs_{rn}"] = OrderedDict((k, d[k]) for k in ("P_ref", "P_case", "lost", "gained", "p_exact", "loses"))
                    tgo, t0 = col(rows, "pgg_tgo"), col(rows, "pgg_t0")
                    fired = tgo > 0.0
                    pooled[plat].append((tgo - t0, fired, col(rows, "ok") > 0.5))
                out["contingency"][f"{base}|{name}"] = e
    # ---------------------------------------------------------------------------------------------------- (B) lead bins
    for plat, L in pooled.items():
        if not L:
            continue
        lead = np.concatenate([a for a, f, o in L])
        fired = np.concatenate([f for a, f, o in L])
        ok = np.concatenate([o for a, f, o in L])
        tab = OrderedDict()
        for lo, hi in BINS:
            m = fired & (lead >= lo) & (lead < hi)
            n, k = int(m.sum()), int(ok[m].sum())
            tab[f"{lo:.1f}-{hi:.1f} s" if hi < 50 else f">= {lo:.1f} s"] = OrderedDict(n=n, ok=k, P=round(k / n, 4) if n else None,
                                                                                    P_wilson=wil(k, n))
        tab["plain trigger after E0 (lead > ~2.9 s)"] = OrderedDict(n=int((~fired).sum()), ok=int(ok[~fired].sum()))
        out["lead_bins"][plat] = tab
    # ---------------------------------------------------------------------------------------------------- (C) gate delay
    for name in ("e19|G73|h285", "liq|G73|h285", "pw|G73|h285"):
        for base in F.BASES_MAIN:
            rows, p, org = RF.table(base, name)
            if not rows:
                out["missing"].append(f"{base}|{name} (gate delay)")
                continue
            t0, top, tgo = col(rows, "pgg_t0"), col(rows, "pgg_topen"), col(rows, "pgg_tgo")
            slack = t0 - top
            fired = tgo > 0.0
            lead_nom = np.where(fired, tgo - t0, 2.90)
            e = OrderedDict(table=dict(path=p, sha256_16=RF.sha16(p)), n=len(rows),
                            gate_open_height_m=q(col(rows, "pgg_hopen"), (0, 50, 100), 1),
                            commit_height_m=q(col(rows, "pgg_h0"), (0, 50, 100), 1),
                            slack_commit_minus_gate_open_s=q(slack),
                            lead_nominal_s=q(lead_nom), plain_fired_before_E0=int(fired.sum()))
            for L in (2.4, 1.9, 1.3):
                e[f"D_crit_lead_below_{L}s"] = q(slack + lead_nom - L, (0, 1, 50))
            out["gate_delay"][f"{base}|{name}"] = e
    # ---------------------------------------------------------------------------------------------------- (D) release hold
    for name in ("nrLO|none|h285", "nrLO|none|rh220|h285", "nrLO|none|rh250|h285"):
        for base in F.BASES_MAIN:
            rows, p, org = RF.table(base, name)
            if not rows:
                out["missing"].append(f"{base}|{name}")
                continue
            ok = col(rows, "ok") > 0.5
            relt = col(rows, "rel_t")
            fm = {}
            for r, o in zip(rows, ok):
                if not o:
                    k = F.fail_mode(r)
                    fm[k] = fm.get(k, 0) + 1
            e = OrderedDict(table=dict(path=p, origin=org, sha256_16=RF.sha16(p)), n=len(rows), P_GNC=round(float(ok.mean()), 4),
                            P_wilson=wil(ok.sum(), len(rows)), release_after_light_ms=q(1e3 * relt[relt >= 0], (0, 50, 99, 100), 1),
                            hold_acted=int(np.sum(col(rows, "pv2_rhb") > 0.5)) if "pv2_rhb" in rows[0] else None,
                            td_vz_m_s=q(col(rows, "td_vz"), (1, 50, 99), 2), fail_modes=fm)
            if "rh" in name:
                for rn in ("nrLO|none|h285", "liq|none|h285"):
                    rr, rp, ro = RF.table(base, rn)
                    if rr:
                        d = RF.pair(rr, rows)
                        e[f"vs_{rn}"] = OrderedDict((k, d[k]) for k in ("P_ref", "P_case", "lost", "gained", "p_exact", "loses"))
            out["release_hold"][f"{base}|{name}"] = e
    ns = U["named_states"]
    pop = U["population_0_2deg"]
    cls = OrderedDict()
    for st in ("purge_not_run_unlined_LO_0-2deg_worst", "purge_not_run_lined_LO_0-2deg_worst",
               "purge_not_run_unlined_HI_0-2deg_worst", "purge_not_run_unlined_0-2deg_least"):
        c = ns[st]["paused"]["lift_flow_held"]
        cls[st] = OrderedDict((k, round(float(c[k]), 4)) for k in ("P_no_light", "P_A3_before_release", "P_released_then_A3",
                                                                   "P_success"))
    for k in ("both_linings|LO", "both_linings|HI"):
        cls[f"population {k} (records, NOT probability-weighted)"] = OrderedDict(
            P_success_worst_convention=round(pop[k]["mean_P_success_worst_case"], 4),
            P_success_best_convention=round(pop[k]["mean_P_success_best_case"], 4),
            P_released_then_A3_worst=round(pop[k]["mean_P_released_then_A3_worst_case"], 4))
    pg = [e["P_GNC"] for k, e in out["release_hold"].items() if "rh220" in k]
    pg_min = min(pg) if pg else None
    out["release_hold"]["combustion_classes_lift_flow_held"] = cls
    out["release_hold"]["hold_vs_gap_bound"] = OrderedDict(
        gap_arrival_bound_s=GAP_BOUND_S, A3_detection_s=A3_DETECT_S, sum_s=round(GAP_BOUND_S + A3_DETECT_S, 3),
        margin_rh220_s=round(0.22 - GAP_BOUND_S - A3_DETECT_S, 3), margin_rh250_s=round(0.25 - GAP_BOUND_S - A3_DETECT_S, 3),
        tag="DERIVED (Combustion bound, flow held at the lift); the flights do not model the gap or A3; the bound under the "
            "flown command profile during the hold is TO-VERIFY (Combustion)")
    out["release_hold"]["P_total_DERIVED"] = OrderedDict(
        rule="P_total = P_success(class, Combustion) x P_GNC(rh220, SIM, min over the two bases)",
        P_GNC_rh220_min=pg_min,
        worst_LO=0.0, worst_HI=0.0,
        population_LO=[round(cls["population both_linings|LO (records, NOT probability-weighted)"][k] * pg_min, 4)
                       for k in ("P_success_worst_convention", "P_success_best_convention")] if pg_min is not None else None,
        population_HI=[round(cls["population both_linings|HI (records, NOT probability-weighted)"][k] * pg_min, 4)
                       for k in ("P_success_worst_convention", "P_success_best_convention")] if pg_min is not None else None,
        no_relight_reference=0.0,
        note="no gain at the worst states (P_success 0 under LO and HI); a gain exists only in non-worst states, and the "
             "population means are over bracket records, not a probability; the expected gain is therefore not stated")
    # ---------------------------------------------------------------------------------------------------- (E) L* table
    def armP(plat, x):
        pre = "e19|G73|L400" if plat == "L400" else "e19|G73"
        nm = f"{pre}|h285" if x is None else f"{pre}|ant{x}|h285"
        v = [out["contingency"].get(f"{b}|{nm}", {}).get("P") for b in F.BASES_MAIN]
        return None if any(z is None for z in v) else v
    rows_ = [
        (">= 2.9 s (decided predictor)", "PURGE (2.5 s flow), T_fire = commit + 2.90 s", "purged Tp2.5 worst: P_success 1.0 "
         "(v2.4a); v2.4 P_abort 0", None),
        ("2.4-2.9 s (contingency)", "PURGE; flow 2.0-2.5 s; T_fire <= ~0.15 s after the plain trigger", "purged Tp2.2 robust "
         "edge: P_success 1.0 (v2.4a); e19 = Tp1.9 robust edge, v2.4 P_abort 0", 25),
        ("1.9-2.4 s (contingency)", "PURGE; flow 1.9-2.1 s; T_fire ~0.2-0.4 s after the plain trigger", "e19 = Tp1.9 robust "
         "edge (v2.4 P_abort 0); 1.9-2.2 s class not tabulated in v2.4a: TO-VERIFY (Combustion)", 21),
        ("1.3-1.9 s (contingency)", "PURGE (lead >= L* = 1.3 s); FSW holds T_fire until 1.9 s of flow: 0.6-1.0 s after the "
         "plain trigger", "e19 (flow 1.9 s)", 17),
        ("1.3 s (edge, ant13)", "PURGE at the L* edge; T_fire ~1.0 s after the plain trigger", "e19 (flow 1.9 s)", 13),
        ("< 1.3 s", "no purge, no unpurged relight (186 (1)): drogue descent, vehicle loss; alternative = unpurged relight "
         "with the release held to >= E2 + 0.22 s", "PURGE NOT RUN: worst LO / HI P_success 0 (v2.4a); population LO "
         "0.20-0.44, HI 0.00-0.02 (records, not probability-weighted)", "rh"),
    ]
    for lab, act, cl, x in rows_:
        e = OrderedDict(lead_bin=lab, decided_action=act, combustion_class=cl)
        if x == "rh":
            e["P_GNC_nominal_start"] = [out["release_hold"].get(f"{b}|nrLO|none|rh220|h285", {}).get("P_GNC") for b in F.BASES_MAIN]
            e["P_total_decided"] = 0.0
            e["P_total_alternative_DERIVED"] = out["release_hold"]["P_total_DERIVED"]
        else:
            e["P_GNC_nominal_start_A1_none_A1J_pc"] = armP("nominal", x)
            e["P_GNC_L400_bracket_A1_none_A1J_pc"] = armP("L400", x)
        out["lstar_table"].append(e)
    # ---------------------------------------------------------------------------------------------------- findings
    f = out["findings"]
    for plat in ("L400", "nominal"):
        for x in ANT:
            v = armP(plat, x)
            if v is not None:
                ld = out["contingency"].get(f"A1_none|{'e19|G73|L400' if plat == 'L400' else 'e19|G73'}|ant{x}|h285", {})
                f.append(f"{plat} start, horizon {x / 10:.1f} s: P {v[0]:.3f} / {v[1]:.3f} (A1_none / A1J_pc), lead p50 "
                         f"{(ld.get('lead_commit_to_plain_s') or {}).get('p50')} s, T_fire after the plain trigger p50 "
                         f"{(ld.get('tfire_after_plain_s') or {}).get('p50')} s, E0 height p50 "
                         f"{(ld.get('E0_height_m') or {}).get('p50')} m, touchdown vz p50 {(ld.get('td_vz_m_s') or {}).get('p50')} m/s")
    gd = [e["slack_commit_minus_gate_open_s"]["min"] for e in out["gate_delay"].values()]
    if gd:
        f.append(f"gate-delay tolerance: the gate may open up to {min(gd):.2f} s late (minimum slack over "
                 f"{len(gd)} tables) without moving the commit; a later opening moves the commit one for one")
    p = os.path.join(RF.OUT, "p6_late_commit.json")
    json.dump(out, open(p, "w"), indent=1, default=float)
    print("wrote", p, RF.sha16(p))
    for k, e in out["contingency"].items():
        print(f"{k:36s} P {e['P']:.3f} lead {e['lead_commit_to_plain_s'] and e['lead_commit_to_plain_s']['p50']} late "
              f"{e['tfire_after_plain_s'] and e['tfire_after_plain_s']['p50']} hE0 {e['E0_height_m']['p50']} td_vz "
              f"{e['td_vz_m_s']['p50']} fm {e['fail_modes']}")
    for plat, t in out["lead_bins"].items():
        print(plat, json.dumps(t))
    for k, e in out["gate_delay"].items():
        print(k, "slack", e["slack_commit_minus_gate_open_s"], "Dcrit1.3", e["D_crit_lead_below_1.3s"])
    for k, e in out["release_hold"].items():
        if isinstance(e, dict) and "P_GNC" in e:
            print(k, e["P_GNC"], {kk: (vv["lost"], vv["gained"], round(vv["p_exact"], 4)) for kk, vv in e.items() if kk.startswith("vs_")},
                  "rel_ms", e["release_after_light_ms"], "hold", e["hold_acted"])
    print(json.dumps(out["release_hold"]["P_total_DERIVED"]))
    for x in f:
        print("FINDING", x)
    if out["missing"]:
        print("missing", out["missing"])


if __name__ == "__main__":
    main()

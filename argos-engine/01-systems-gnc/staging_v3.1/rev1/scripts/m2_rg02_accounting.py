"""m2_rg02_accounting v1 (GNC, 2026-10-13): review REV-GNC-1 RG-02, no-light accounting rebuilt per line state.

    P_total = sum_s pi_s * P_6DOF|s,lit * (1 - p_abort,s) * (1 - p_nl,ign)

Inputs (no new flights): the 44 cm3 rows of m2_relight_seg44 v1.5 (staging_v3.1/results/relight_seg44/relight_seg44_v1.5.json:
P|lit,s from 1000 paired 6-DOF runs per state and plan, A1 + A1J bases; p_abort,s = Combustion's ECU abort probability at the
window, relight_vapour_states_v2p4 re-issue 05:31) and, for the superseded 21.4 cm3 segment, the v2.8 rows (context_v28 of the
same file) with the reviewer's RC-03 abort probabilities at W 0.65 s (REVIEW-GNC rg01: vapF 4.12 %, vapU 0.07 %, liquid 0).
Unknowns carried as parameters, NOT invented:
  pi_s       line-state probability at RELIGHT: no source. Mechanical RELAY-2 puts the retained vapour at >= 34 cm3 (lower bound,
             875 J soak-back) without a fix, so the liquid state is not expected unless fix (a) or (d) works; the table gives every
             state and the minimum over the vapour states and over all states (robust values), not a weighted mean.
  p_nl,ign   no-light probability of the torch / igniter per attempt with flow established: no source (gnc.json v3 placeholders
             0.005-0.05); evaluated at 0, 0.005, 0.02, 0.05 (TO-DEFINE: Combustion / Electronics torch qualification).
Output: <out>/rg02_accounting_v1.json."""
import hashlib
import json
import os

HUB = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/results/relight_seg44/relight_seg44_v1.5.json"
OUT = os.environ.get("GNC_RG02_OUT", "/home/claude/work/space/out/rg02")
VERSION = "m2_rg02_accounting v1"
P_NL = (0.0, 0.005, 0.02, 0.05)
RC03_ABORT_W065 = {"liq": 0.0, "vapU": 0.0007, "vapF": 0.0412}   # REVIEW-GNC rg01 (21.4 cm3 segment, E1->E2 max 0.667 s)


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def table_for(by_state, vap_states):
    rows = {}
    for s, x in by_state.items():
        rows[s] = dict(P_lit=x.get("P_lit_late") if x.get("P_lit_late") is not None else x.get("P_lit_all"),
                       P_lit_all_runs=x.get("P_lit_all"), p_abort=x["P_abort"], P_total_s=x["P_total"],
                       P_total_s_ci95=x.get("P_total_ci95"), n=x.get("n"), n_surviving_abort=x.get("n_surv"))
    comp = {}
    for pnl in P_NL:
        per = {s: r["P_total_s"] * (1.0 - pnl) for s, r in rows.items()}
        vs = [per[s] for s in vap_states if s in per]
        comp[f"p_nl={pnl}"] = dict(per_state=per, min_over_vapour_states=min(vs) if vs else None,
                                   min_over_all_states=min(per.values()))
    return dict(states=rows, composite=comp)


def main():
    d = json.load(open(HUB))
    out = dict(version=VERSION, date="2026-10-13", formula="P_total = sum_s pi_s P_6DOF|s,lit (1 - p_abort,s) (1 - p_nl,ign)",
               source=dict(path=HUB, sha256_16=sha16(HUB), version=d["version"], sim=d["sim"]),
               unknowns=dict(pi_s="no source; Mechanical RELAY-2 lower bound >= 34 cm3 retained vapour without a fix (liquid "
                                  "state not expected): per-state values and minima are reported, no weighted mean",
                             p_nl_ign="no source (gnc.json v3 placeholders 0.005-0.05); TO-DEFINE by torch qualification"),
               p_nl_values=list(P_NL), options_44cm3={})
    vap = ["vapLO", "vapHI", "vap44F"]
    for opt, v in d["governing_pocket"]["matrix"].items():
        out["options_44cm3"][opt] = dict(plan_s=v.get("plan_s"), W_s=v.get("W_s"), **table_for(v["by_state"], vap))
    for opt, v in d["min_window_options"]["options"].items():
        out["options_44cm3"][opt] = dict(plan_s=v.get("plan_s"), **table_for(v["by_state"], vap))
    # superseded 21.4 cm3 segment, v2.8 rows (reviewer R7 check): vapF at 0.81 s conditional on light x (1 - p_abort)
    c = d["context_v28"]
    v28 = {}
    for b, x in c["vapF_p0.81"].items():
        v28[b] = dict(P_lit_vapF_081=x["P"], P_total_vapF=x["P"] * (1.0 - RC03_ABORT_W065["vapF"]))
    out["v28_rows_21cm3_superseded"] = dict(abort_W065=RC03_ABORT_W065, abort_source="REVIEW-GNC rg01 (RC-03 E1->E2)",
                                            by_base=v28, note="reproduces the reviewer's R7: 0.949-0.953; the 21.4 cm3 basis is "
                                                              "superseded by the 44 cm3 rows above")
    out["demonstration_rule"] = ("ground relight attempts count toward the 3/N rule only when the segment state reproduces the "
                                 "flight state at RELIGHT (soak-back vapour >= Mechanical's bound, or the fix (a)/(d) active as "
                                 "flown); a liquid-line ground start does not demonstrate a vapour-state flight relight")
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "rg02_accounting_v1.json")
    with open(p, "w") as f:
        json.dump(out, f, indent=1, default=float)
    for opt, v in out["options_44cm3"].items():
        cm = v["composite"]
        print(f"{opt:42s} " + " ".join(f"{s} {r['P_total_s']:.3f}" for s, r in v["states"].items()) +
              f" | min vap p_nl 0/0.02/0.05: {cm['p_nl=0.0']['min_over_vapour_states']:.3f}/"
              f"{cm['p_nl=0.02']['min_over_vapour_states']:.3f}/{cm['p_nl=0.05']['min_over_vapour_states']:.3f}")
    print("v2.8 rows:", {b: round(x["P_total_vapF"], 4) for b, x in v28.items()})
    print("wrote", p)


if __name__ == "__main__":
    main()

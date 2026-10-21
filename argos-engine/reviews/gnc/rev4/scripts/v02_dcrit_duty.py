"""REV-GNC-6 v02: (a) gate-delay tolerance D_crit at the 210 m trim re-derived from the staged P2 tables (v351 h200-h235,
both states, all bases flown), with the 285 m v3d reference for comparison; zero-slack commits; realised commit leads
below 2.4 / 2.1 / 1.9 s in NOMINAL flights and what happens to the line-208 band if the 204 (1) counting rule ('a commit
lead below about 2.1 s is not counted as a landing') is applied to those nominal runs; (b) an ASSUMED-transfer estimate of
the P cost of a uniform gate delay D at 210 m using the REV-GNC-5 285 m P-by-realised-lead curve (nominal start) - a
reviewer estimate, not a flown result; (c) the A1 engine-on time (burn_time) p99 at 210 m vs 285 m and the 8.258 s A1
sizing counter (line 213 'duty cycle shortens').  SIM tables -> DERIVED.  Usage: python -I v02_dcrit_duty.py <out.json>"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rv6lib as L

OUT = sys.argv[1]
res = dict(script="v02_dcrit_duty (REV-GNC-6)", tag="DERIVED from SIM tables; (b) uses an ASSUMED transfer of the 285 m P-by-lead curve")
THR = (2.4, 2.1, 1.9, 1.3)


def lead_info(rows):
    sl, ln, fired, lead_real = [], [], [], []
    for r in rows:
        t0, top, tgo, tE0 = (float(r[k]) for k in ("pgg_t0", "pgg_topen", "pgg_tgo", "pgg_tE0"))
        s = t0 - top
        f = tgo > 0
        l_auth = (tgo - t0) if f else 2.90
        l_e0 = (tgo - t0) if f else (tE0 - t0)
        sl.append(s); ln.append((l_auth, l_e0)); fired.append(f)
    return sl, ln, fired


def summarise(rows):
    sl, ln, fired = lead_info(rows)
    out = dict(n=len(rows), fired=sum(fired), slack_min=round(min(sl), 4), n_slack_zero=sum(1 for s in sl if s <= 1e-9),
               n_slack_lt_0p1=sum(1 for s in sl if s < 0.1),
               lead_nom={k: round(v, 4) for k, v in zip(("min", "p01", "p50"), (min(x[0] for x in ln), L.q([x[0] for x in ln], 1), L.q([x[0] for x in ln], 50)))},
               nonfired_E0_minus_commit_min=(round(min(x[1] for x, f in zip(ln, fired) if not f), 4) if not all(fired) else None))
    for T in THR:
        d = [s + x[0] - T for s, x in zip(sl, ln)]
        d2 = [s + x[1] - T for s, x in zip(sl, ln)]
        out[f"Dcrit_{T}"] = dict(min=round(min(d), 3), p01=round(L.q(d, 1), 3), p05=round(L.q(d, 5), 3), p50=round(L.q(d, 50), 3),
                                 min_E0bound=round(min(d2), 3), n_below_zero=sum(1 for x in d if x < 0))
    # nominal runs whose realised lead (fired runs: tgo - t0) is below a threshold, and their outcome
    for T in (2.4, 2.1, 1.9):
        idx = [i for i, (x, f) in enumerate(zip(ln, fired)) if f and x[0] < T]
        out[f"nominal_lead_below_{T}"] = dict(n=len(idx), ok=sum(float(rows[i]["ok"]) > 0.5 for i in idx),
                                              runs=[int(float(rows[i]["run"])) for i in idx][:20],
                                              leads=[round(ln[i][0], 3) for i in idx][:20])
    return out


gate = {}
for st in ("liq", "pw"):
    for h in (200, 205, 210, 215, 220, 225, 230, 235):
        for b in L.ALL4:
            cf = L.case_files(b, st, "v351", h)
            if not cf:
                continue
            gate[f"{b}|{st}|v351|h{h}"] = dict(summarise(L.rows_of(cf)), tables=[(os.path.basename(p), L.sha16(p)) for p in cf])
    for b in L.ALL4:
        gate[f"{b}|{st}|G73|h285(v3d ref)"] = dict(summarise(L.rows_of(L.ref_files(b, st))),
                                                   tables=[(os.path.basename(p), L.sha16(p)) for p in L.ref_files(b, st)])
res["gate"] = gate

# band with the 204 (1) counting rule applied to nominal runs (lead < 2.1 s counted as not landed), both arms
def outcome_rule(rows, onset=80.0, T=2.1):
    d = {}
    sl, ln, fired = lead_info(rows)
    for r, x, f in zip(rows, ln, fired):
        o = float(r["ok"]) > 0.5 and (1e3 * float(r["liq_left"]) - onset >= 0.0)
        if f and x[0] < T:
            o = False
        d[int(float(r["run"]))] = o
    return d


rule = {}
for st in ("liq", "pw"):
    ev = {}
    for h in (200, 205, 210, 215, 220):
        prs = []
        for b in L.MAIN:
            ref = outcome_rule(L.rows_of(L.ref_files(b, st)))
            case = outcome_rule(L.rows_of(L.case_files(b, st, "v351", h)))
            prs.append(L.counts(ref, case))
        s = L.stats(*L.pooled_counts(prs))
        ev[h] = dict(lost=s["lost"], gained=s["gained"], p=s["p"], ub95_pp=s["ub95_pp"], passes=L.rule_pass(s))
    rule[st] = ev
res["band_with_204_1_counting_rule"] = rule

# (b) ASSUMED transfer: REV-GNC-5 P-by-lead (285 m, nominal start, pooled contingency arms; reviews/gnc/rev3/results/v05_p6.json)
v05 = json.load(open(f"{L.HUB}/reviews/gnc/rev3/results/v05_p6.json"))
curve = []
for k, v in v05["by_lead"]["nominal"].items():
    if k == "not_fired" or v["P"] is None:
        continue
    lo, hi = (float(x) for x in k.split("-"))
    curve.append((lo, hi, v["P"]))
curve.sort()
P_top = max(p for lo, hi, p in curve if lo >= 2.4)


def p_of(lead):
    for lo, hi, p in curve:
        if lo <= lead < hi:
            return p
    return P_top if lead >= 2.9 else 0.0


cost = {}
for b in L.MAIN:
    for st in ("liq", "pw"):
        rows = L.rows_of(L.case_files(b, st, "v351", 210))
        sl, ln, fired = lead_info(rows)
        okk = [float(r["ok"]) > 0.5 for r in rows]
        for D in (0.25, 0.5, 0.75, 1.0, 1.5, 2.0):
            exp_loss = 0.0
            nbin = 0
            for s, x, o in zip(sl, ln, okk):
                lead0 = x[0]                       # nominal realised lead (fired) or 2.90 s (author convention)
                lead_d = lead0 - max(0.0, D - s)   # a gate delay D first uses the slack, then cuts the lead
                if not o:
                    continue
                r0, r1 = p_of(lead0) if lead0 < 2.9 else P_top, p_of(lead_d)
                if lead_d < 2.4:
                    nbin += 1
                exp_loss += max(0.0, (r0 - r1) / r0)
            cost[f"{b}|{st}|h210|D{D}"] = dict(n_runs_lead_below_2p4=nbin, expected_P_loss_pp=round(100 * exp_loss / len(rows), 3))
res["gate_delay_cost_ASSUMED_transfer"] = dict(curve_285m_nominal=curve, P_top=P_top, cost=cost,
                                               note="reviewer estimate; the P-by-lead curve was flown at 285 m (v3d); its transfer to 210 m / v3.5.1 is ASSUMED")

# (c) A1 engine-on time
duty = {}
for b in L.ALL4:
    for st in ("liq", "pw"):
        for lab, files in ((f"v351|h210", L.case_files(b, st, "v351", 210)), ("v3d|h285", L.ref_files(b, st))):
            if not files:
                continue
            parts = {}
            for p in files:
                bt = [float(r["burn_time"]) for r in L.read(p)]
                parts[os.path.basename(p)] = dict(n=len(bt), p50=round(L.q(bt, 50), 4), p99=round(L.q(bt, 99), 4), max=round(max(bt), 4))
            allbt = [float(r["burn_time"]) for r in L.rows_of(files)]
            duty[f"{b}|{st}|{lab}"] = dict(parts=parts, all=dict(n=len(allbt), p99=round(L.q(allbt, 99), 4), max=round(max(allbt), 4)))
res["duty_burn_time"] = dict(sizing_counter_A1_s=8.258, table=duty)
json.dump(res, open(OUT, "w"), indent=1)
for k, v in gate.items():
    if "liq" in k and ("h210" in k or "h285" in k or "h205" in k or "h215" in k):
        print(k, "n", v["n"], "fired", v["fired"], "slack0", v["n_slack_zero"], "lead", v["lead_nom"], "Dcrit2.1", v["Dcrit_2.1"], "Dcrit2.4", v["Dcrit_2.4"]["min"],
              "lead<2.1", v["nominal_lead_below_2.1"]["n"], v["nominal_lead_below_2.1"]["ok"], "lead<2.4", v["nominal_lead_below_2.4"]["n"])
print("band with counting rule", json.dumps(rule))
for k, v in cost.items():
    print("cost", k, v)
for k, v in duty.items():
    print("duty", k, v["all"], {kk: vv["p99"] for kk, vv in v["parts"].items()})

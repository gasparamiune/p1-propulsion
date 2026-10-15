"""m2_relight_v28 v1.2 (GNC, 2026-10-13; v1.2: fault-spread cases and the option (c) / stale-flag evaluation, after the lead
decisions of 2026-10-13 (planning value 0.81 s adopted; option (c) adopted provisionally: Electronics publishes PRIMED/UNPRIMED
at >= 10 Hz in the coast, the FC plans 1.41 s on UNPRIMED, GNC verifies it paired and decides the stale/missing-flag plan);
v1.1: fault-path cases run without the nominal sizing gate of m2_mc6.run_case, which returned no runs for them in v1): A1 relight on the v2.8 relight design (lead decisions 2026-10-13, interfaces/CHANGELOG.md:
Finding A = option (b) accepted as one design: the FC sends RELIGHT at the planned T_fire, valve and torch at E0, lift at E1 on
torch confirmation; flight worst sequence E0 -> Pc-confirm deadline 0.81 s = torch gate 0.16 s + W 0.65 s; fault path (segment
emptied by a seat leak, prep re-run) 1.37 s; lead request: re-derive the planning value (0.6 + 0.81 = 1.41 s, or a better rule
now that the command time is deterministic), re-run the early/late brackets on the physical spread, report P for the 1.37 s
fault case).

Start-delay model on the 6-DOF (sim6/run6 v2.7.1-dev option t_ign_q): the 6-DOF lights (thrust onset) at the drawn delay after
the relight command; the delay is drawn from Combustion's RC-03 E0 -> E2 (Pc confirmation) distribution of the line state:
  E0->E2 quantiles = Combustion E0_E3 5 % quantiles (Pc loop K15) - (median E0_E3 - median E0_E2); the construction reproduces
  Combustion's E0_E2 p95 and max within 3 ms (checked and stored below). Cases 'preopened' = valve open before the lift, the
  Finding A configuration (the lead's relayed numbers: liquid 0.315 / 0.462 / 0.499, vapour U01 0.470 / 0.719 / 0.798, full vapour
  0.625 / 0.772 / 0.809 s median / p99 / max). The 6-DOF thrust then rises with its own closed-loop lag (~0.1 s to 90 %, like
  Combustion's E2 -> E3 0.092 s). Draws from their own generator (seed 20261018): the other draws (seed 101) and the growth
  draws are unchanged, every case pairs run by run with the 1.81 s runs (m2_relight_181) and with each other.
Planning value t_ign_est (the FSW's planned command-to-light delay in the relight trigger): swept; the lead's 1.41 s (0.6 + 0.81);
GNC rules: the deadline 0.81 s (latest light that is not aborted) and lower values.
Parts (GNC_V28_PARTS, default nominal,sweep,full,fspread,eval):
  nominal  nominal A1 flights (no dispersion) at the median / min / max delay of each state for each planning value
  sweep    planning value x line state on the A1 pc2 and ENG-07d bases without growth (500 runs each)
  full     the selected planning values (GNC_V28_FULL, default 1.41 and the GNC proposal) on all four bases (with growth), and the
           1.37 s fault case (fixed delay)
  fspread  (v1.2) fault-path SPREAD on the A1 pc2 and ENG-07d bases without growth: start delay = the line state's E0->E2 table
           + the prep re-run 0.56 s (DERIVED: fault 1.37 - flight worst 0.81; the spread after the prep is ASSUMED to follow the
           preopened tables), at the planning values GNC_V28_FS (default 1.41 and 0.81)
  eval     merge into relight_v28.json (paired exact McNemar against the 1.81 s LATE runs, Wilson CI, start-delay error vs
           outcome, sizing counter vs the A1 sizing cycle); v1.2: option_c = paired option (c) verification (fault path at 1.41
           vs 0.81 s, fault spread, false-UNPRIMED cost on primed lines), stale/missing-flag break-even prior q* with a joint
           bootstrap over the shared run draws, maximin table, and the GNC stale-flag rule
Env: GNC_IFACE, GNC_ACT_RATE, GNC_V28_OUT (default out/relight_v28), GNC_V28_PARTS, GNC_V28_CASES, GNC_V28_FULL (comma list
of planning values), GNC_V28_FS (comma list, fault-spread planning values), GNC_RC03 (Combustion relight_latency_sup_v2p4.json)."""
import csv
import hashlib
import json
import os
import sys
import time
import numpy as np

os.environ.setdefault("GNC_PC_RATCHET", "1")
os.environ.setdefault("GNC_OUT", "/home/claude/work/space/out/prop_closure_m2")
os.environ.setdefault("GNC_SUFFIX", "pc2")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_mc6 as M  # noqa: E402
import m2_prop_closure as PC  # noqa: E402
import m2_mechv2_mc as MV  # noqa: E402
import m2_throat_mc as TG  # noqa: E402

VERSION = "m2_relight_v28 v1.2"
S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_V28_OUT", f"{S}/relight_v28")
PARTS = os.environ.get("GNC_V28_PARTS", "nominal,sweep,full,fspread,eval").split(",")
HUB_RC03 = "/home/claude/work/shared-fallback/engine/02-combustion/data/v2/v2p4/relight_latency_sup_v2p4.json"
WORK_RC03 = "/home/claude/work/combustion/data/v2/v2p4/relight_latency_sup_v2p4.json"
RC03 = os.environ.get("GNC_RC03") or (HUB_RC03 if os.path.isfile(HUB_RC03) else WORK_RC03)
STATES = {"liq": "relight_valve_preopened_liquid|0.125|loopK15",
          "vapU": "relight_valve_preopened_vapour_U01|0.125|loopK15",
          "vapF": "relight_valve_preopened_full_vapour|0.125|loopK15"}
# Electronics v2.8 / lead decisions 2026-10-13 (interfaces/CHANGELOG.md)
SEQ_WORST = 0.81      # torch gate 0.16 + W 0.65 (flight worst sequence E0 -> Pc-confirm deadline)
SEQ_FAULT = 1.37      # fault path (segment emptied by a seat leak, prep re-run): a fault case
LEAD_PLAN = 0.6 + SEQ_WORST
PREP_RERUN = SEQ_FAULT - SEQ_WORST   # DERIVED 0.56 s: the fault path's prep re-run ahead of the flight sequence
FS_PLANS = tuple(float(x) for x in os.environ.get("GNC_V28_FS", f"{LEAD_PLAN},{SEQ_WORST}").split(","))
FLAG_STALE_S = 0.3    # ASSUMED staleness limit of the ECU flag (3 frames at the 10 Hz minimum rate; to be set with Electronics)
SWEEP_PLANS = (0.45, 0.55, 0.65, SEQ_WORST, LEAD_PLAN)
SEQ_SRC = ("Electronics v2.8 relight sequence (CHANGELOG 2026-10-13: flight worst 0.81 s = torch gate 0.16 + W 0.65; fault path "
           "1.37 s; SIL E0->RUN 0.26 s liquid / 0.50 s vapour) + lead decisions 2026-10-13 (v2.8 design accepted; planning value "
           "0.6 + 0.81 = 1.41 s or a better GNC rule) + Combustion RC-03 E0->E2 (relight_latency_sup_v2p4.json)")
RL181 = f"{S}/relight_181"
BASES = ("A1_none", "A1_pc", "A1J_none", "A1J_pc")


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def jl(p):
    try:
        return json.load(open(p))
    except (OSError, ValueError):
        return None


def rows_csv(p):
    return list(csv.DictReader(open(p))) if os.path.exists(p) else None


def e0e2_tables():
    d = json.load(open(RC03))
    out = {}
    for st, key in STATES.items():
        c = d["cases"][key]
        q3 = np.array(c["E0_E3_quantiles_5pct_s"], dtype=float)
        off = c["E0_E3_s"]["median"] - c["E0_E2_s"]["median"]
        q2 = q3 - off
        out[st] = dict(case=key, quantiles_5pct_s=q2.tolist(), e2_to_e3_offset_s=off,
                       check=dict(p95_constructed=float(q2[19]), p95_given=c["E0_E2_s"]["p95"], max_constructed=float(q2[20]),
                                  max_given=c["E0_E2_s"]["max"], median_given=c["E0_E2_s"]["median"],
                                  p99_given=c["E0_E2_s"]["p99"]))
    return out


def base_over(base):
    """A1 configurations of m2_relight_181 (k_est_asc 2), without the start-delay terms."""
    tg = json.load(open(f"{S}/throat_growth/throat_growth.json"))
    jr = tg["j_ref"]
    if base.startswith("A1J"):
        o = dict(MV.CASES["m2_J1.6_n15"][0], k_est_asc=2)
        b = "A1J"
    else:
        o = dict(PC.DC["A1"], m_fixed=PC.M_TANK, k_est_asc=2)
        b = "A1"
    if base.endswith("_pc"):
        o.update(throat_jref=jr[b], throat_loop=1, throat_g_band=TG.BAND)
    return o


def case_over(base, state, plan, tabs, fixed=None, add=0.0):
    o = base_over(base)
    if fixed is not None:
        o.update(t_ign_q=tuple([float(fixed)] * 21), t_ign_add=0.0, t_ign_est=float(plan))
    else:
        o.update(t_ign_q=tuple(float(x) + float(add) for x in tabs[state]["quantiles_5pct_s"]), t_ign_add=0.0, t_ign_est=float(plan))
    return o


def cname(base, state, plan):
    return f"v28_{state}_p{plan:.2f}_{base}_k2"


def run_case_fixed(name, over, note, seed=101):
    """the Monte Carlo of m2_mc6.run_case for a fixed load, without its nominal sizing gate: run_case returns no runs when the
    nominal flight of the configuration does not close (v1 first run: the 1.37 s fault path at planning values <= 0.81 s
    crashes in the nominal flight, so run_case returned no Monte Carlo; kept as evidence in the log). Same draws, same
    run_one / flat_row / summarize as run_case (the sizing never changes a fixed-load Monte Carlo)."""
    t0 = time.time()
    over = dict(over)
    m = float(over.pop("m_fixed"))
    cfg = R.cfg_of(**dict(over, m_n2o=m))
    D = R.draw(np.random.default_rng(seed), M.N, cfg)
    rows = [R.flat_row(i, dr, res, R.success(res), cfg) for i, dr in enumerate(D) for res in (R.run_one(cfg, dr),)]
    info = R.build(cfg)[5]
    return dict(case=name, note=note, sim=s6.SIM6_VERSION, m_n2o_mc_kg=m, m_liftoff_kg=info["m_liftoff"],
                load_rule="fixed (lead decision); nominal sizing gate skipped", summary=R.summarize(rows),
                cpu_s=time.time() - t0), rows


def run_cases(cs):
    for name, (over, note) in cs.items():
        p = os.path.join(OUT, f"mc6_runs_{name}_v28.csv")
        if os.path.exists(p) and os.path.getsize(p) > 100 and os.environ.get("GNC_V28_FORCE") != "1":
            print("exists", name, flush=True)
            continue
        o, rows = (run_case_fixed if ("_fault_" in name or name.startswith("v28_fs")) else M.run_case)(name, over, note)
        if not rows:
            print(f"{name}: NO Monte Carlo (run_case: nominal sizing does not close)", flush=True)
            continue
        M.write_csv(p, rows)
        keep = {k: o.get(k) for k in ("case", "note", "m_n2o_mc_kg", "m_liftoff_kg", "cpu_s", "sim")}
        keep["fail_modes"] = o["summary"]["fail_modes"]
        keep["config"] = {k: over.get(k) for k in ("t_ign_est", "t_ign_add", "throat_g_band", "throat_jref", "k_est_asc")}
        keep["t_ign_q"] = list(over.get("t_ign_q") or [])
        with open(os.path.join(OUT, f"v28_case_{name}.json"), "w") as f:
            json.dump(keep, f, indent=1, default=float)
        print(f"{name}: P {np.mean([r['ok'] for r in rows]):.3f} fails {o['summary']['fail_modes']} ({o['cpu_s']:.0f} s)", flush=True)


def part_nominal(tabs):
    nom = {}
    A1b = dict(PC.DC["A1"], k_est_asc=2)
    for plan in SWEEP_PLANS:
        for st, tb in tabs.items():
            q = tb["quantiles_5pct_s"]
            for lab, d_ in (("min", q[0]), ("median", float(np.interp(0.5, np.linspace(0, 1, 21), q))), ("max", q[-1])):
                r = PC.nominal(dict(A1b, t_ign=float(d_), t_ign_est=float(plan)), PC.M_TANK)
                nom[f"A1|{st}|{lab}|plan{plan:.2f}"] = dict(start_delay_s=float(d_), planning_value_s=plan, landed_ok=r["landed_ok"],
                                                            closes=r["closes"], reserve_frac=r["reserve_frac"],
                                                            burn_time_s=r["burn_time_s"], h_ign=r["h_ign"], n2o_burned=r["n2o_burned"])
                print(f"nominal plan {plan:.2f} {st:4s} {lab:6s} delay {d_:.3f}: reserve {100 * r['reserve_frac']:.1f} % burn "
                      f"{r['burn_time_s']:.2f} s cmd h {r['h_ign']:.1f} m landed {r['landed_ok']} closes {r['closes']}", flush=True)
        r = PC.nominal(dict(A1b, t_ign=SEQ_FAULT, t_ign_est=float(plan)), PC.M_TANK)
        nom[f"A1|fault|{SEQ_FAULT:.2f}|plan{plan:.2f}"] = dict(start_delay_s=SEQ_FAULT, planning_value_s=plan, landed_ok=r["landed_ok"],
                                                               closes=r["closes"], reserve_frac=r["reserve_frac"],
                                                               burn_time_s=r["burn_time_s"], h_ign=r["h_ign"])
        print(f"nominal plan {plan:.2f} fault 1.37 s: reserve {100 * r['reserve_frac']:.1f} % landed {r['landed_ok']}", flush=True)
    with open(os.path.join(OUT, "relight_v28_nominal.json"), "w") as f:
        json.dump(nom, f, indent=1, default=float)


def sweep_cases(tabs):
    cs = {}
    for base in ("A1_none", "A1J_none"):
        for st in tabs:
            for plan in SWEEP_PLANS:
                cs[cname(base, st, plan)] = (case_over(base, st, plan, tabs),
                                             f"{base} k_est_asc 2, start delay ~ Combustion RC-03 E0->E2 {st}, planning value {plan:.2f} s")
        for plan in SWEEP_PLANS:   # fault path at every swept planning value (nominal flights: lands only at plan 1.41 s)
            cs[f"v28_fault_p{plan:.2f}_{base}_k2"] = (case_over(base, None, plan, tabs, fixed=SEQ_FAULT),
                                                      f"{base} k_est_asc 2, FAULT path: start delay {SEQ_FAULT} s fixed, "
                                                      f"planning value {plan:.2f} s")
    return cs


def full_cases(tabs, plans):
    cs = {}
    for base in BASES:
        for plan in plans:
            for st in tabs:
                cs[cname(base, st, plan)] = (case_over(base, st, plan, tabs),
                                             f"{base} k_est_asc 2, start delay ~ RC-03 E0->E2 {st}, planning value {plan:.2f} s")
            cs[f"v28_fault_p{plan:.2f}_{base}_k2"] = (case_over(base, None, plan, tabs, fixed=SEQ_FAULT),
                                                      f"{base} k_est_asc 2, FAULT path: start delay {SEQ_FAULT} s fixed, planning "
                                                      f"value {plan:.2f} s")
    return cs


def fs_cases(tabs, plans=FS_PLANS):
    """v1.2 fault-path spread: delay = state table + PREP_RERUN (0.69-1.37 s over the three states)."""
    cs = {}
    for base in ("A1_none", "A1J_none"):
        for plan in plans:
            for st in tabs:
                cs[cname(base, "fs" + st, plan)] = (case_over(base, st, plan, tabs, add=PREP_RERUN),
                                                    f"{base} k_est_asc 2, FAULT-path spread: start delay = RC-03 E0->E2 {st} + prep "
                                                    f"re-run {PREP_RERUN:.2f} s, planning value {plan:.2f} s")
    return cs


def option_c(tabs, pg=SEQ_WORST, pf=LEAD_PLAN, nboot=2000, seed=20261019):
    """Option (c) verification (paired, same draws) and the stale/missing-flag decision.
    fault_paired:      fault path (1.37 s) at pf vs pg, per base (TG.pair: base = pg runs, case = pf runs; 'gained' = saved by (c))
    fault_spread:      fault-path spread at pf vs pg, per state (none bases)
    false_unprimed:    primed line at pf vs pg (the cost of a wrong UNPRIMED flag or of planning pf on a stale flag)
    break_even:        prior q of an UNPRIMED line at which E[P] of the two plans is equal:
                       q* = dN / (dN + dF), dN = P_primed(pg) - P_primed(pf), dF = P_fault(pf) - P_fault(pg);
                       95 % interval from a joint bootstrap over run indices (the four cases share the seed-101 draws)
    maximin:           worst P over the three primed states and the fault path for each plan"""
    def ok(name):
        rr = rows_csv(os.path.join(OUT, f"mc6_runs_{name}_v28.csv"))
        return None if not rr else np.array([float(r["ok"]) for r in rr]) > 0.5

    def rr_(name):
        return rows_csv(os.path.join(OUT, f"mc6_runs_{name}_v28.csv"))
    out = dict(plan_primed_s=pg, plan_unprimed_s=pf, method=option_c.__doc__, by_base={})
    rng = np.random.default_rng(seed)
    for base in BASES:
        b = {}
        fa, fb = rr_(f"v28_fault_p{pg:.2f}_{base}_k2"), rr_(f"v28_fault_p{pf:.2f}_{base}_k2")
        if fa and fb:
            b["fault_paired"] = dict(TG.pair(fa, fb), base_case=f"v28_fault_p{pg:.2f}_{base}_k2",
                                     case=f"v28_fault_p{pf:.2f}_{base}_k2")
            for k in ("lost_runs", "gained_runs"):
                b["fault_paired"][f"n_{k}"] = len(b["fault_paired"].pop(k))
        for st in tabs:
            a, c = rr_(cname(base, "fs" + st, pg)), rr_(cname(base, "fs" + st, pf))
            if a and c:
                d = dict(TG.pair(a, c), base_case=cname(base, "fs" + st, pg), case=cname(base, "fs" + st, pf))
                for k in ("lost_runs", "gained_runs"):
                    d[f"n_{k}"] = len(d.pop(k))
                b.setdefault("fault_spread_paired", {})[st] = d
            a, c = rr_(cname(base, st, pg)), rr_(cname(base, st, pf))
            if a and c:
                d = dict(TG.pair(a, c), base_case=cname(base, st, pg), case=cname(base, st, pf))
                for k in ("lost_runs", "gained_runs"):
                    d[f"n_{k}"] = len(d.pop(k))
                b.setdefault("false_unprimed_paired", {})[st] = d
        f0, f1 = ok(f"v28_fault_p{pg:.2f}_{base}_k2"), ok(f"v28_fault_p{pf:.2f}_{base}_k2")
        if f0 is not None and f1 is not None:
            mm = {pg: [float(f0.mean())], pf: [float(f1.mean())]}
            for st in tabs:
                n0, n1 = ok(cname(base, st, pg)), ok(cname(base, st, pf))
                if n0 is None or n1 is None:
                    continue
                mm[pg].append(float(n0.mean()))
                mm[pf].append(float(n1.mean()))
                dN, dF = float(n0.mean() - n1.mean()), float(f1.mean() - f0.mean())
                qs = max(dN, 0.0) / (max(dN, 0.0) + dF) if (max(dN, 0.0) + dF) > 0 else None
                N = len(n0)
                bq = []
                for _ in range(nboot):
                    i = rng.integers(0, N, N)
                    dn, df = n0[i].mean() - n1[i].mean(), f1[i].mean() - f0[i].mean()
                    if dn + df > 0:
                        bq.append(max(dn, 0.0) / (max(dn, 0.0) + df))
                b.setdefault("break_even_prior", {})[st] = dict(
                    P_primed_plan_primed=float(n0.mean()), P_primed_plan_unprimed=float(n1.mean()),
                    P_fault_plan_primed=float(f0.mean()), P_fault_plan_unprimed=float(f1.mean()), dN=dN, dF=dF, q_star=qs,
                    q_star_ci95_bootstrap=[float(np.percentile(bq, 2.5)), float(np.percentile(bq, 97.5))] if bq else None)
            b["maximin"] = {f"{k:.2f}": dict(worst_P=min(v), P_list_fault_then_states=v) for k, v in mm.items()}
        if b:
            out["by_base"][base] = b
    qs = [v["q_star"] for b in out["by_base"].values() for v in b.get("break_even_prior", {}).values() if v["q_star"] is not None]
    out["q_star_range"] = [min(qs), max(qs)] if qs else None
    out["stale_flag_rule_gnc"] = dict(
        rule=(f"flag fresh (age <= {FLAG_STALE_S} s, ASSUMED: 3 frames at the 10 Hz minimum): PRIMED -> plan {pg:.2f} s, UNPRIMED -> "
              f"plan {pf:.2f} s. Flag stale or missing at T_fire: hold the last valid flag received since the MECO valve closure "
              f"(UNPRIMED -> {pf:.2f} s, PRIMED -> {pg:.2f} s); no valid flag since MECO -> {pg:.2f} s. The plan is evaluated every "
              f"frame (trigger when the predicted time to go <= plan + rise) and latched at T_fire; a flip to UNPRIMED after the "
              f"{pf:.2f} s trigger point fires at once."),
        decision=(f"GNC decision, the safer plan for a stale or missing flag: hold the last valid flag, default {pg:.2f} s. A stale "
                  f"flag is one fault (the ECU->FC link or the ECU publisher); holding PRIMED is wrong only if a second, independent "
                  f"fault (an emptying of the primed segment that the ECU did not report before the flag went stale) coincides with "
                  f"it, which costs the fault-path loss. A held UNPRIMED errs only in the safe direction: the segment re-primes only "
                  f"through the NC valve (opening, or an inflow seat leak), and an unreported re-prime costs the false-UNPRIMED loss "
                  f"(P stays >= the false_unprimed rows), not the fault-path loss. Planning {pf:.2f} s on every stale flag (maximin) "
                  f"costs that loss on every primed flight with a stale flag to cover a double fault; it is the better expected choice "
                  f"only when the probability of an unreported emptying exceeds q* (q_star_range)."),
        conditions=["the ECU publishes a distinct UNKNOWN (P_feed invalid) state, or publishes UNPRIMED whenever it will run the "
                    "prep at RELIGHT; the FC treats UNKNOWN as UNPRIMED",
                    "the flag is valid only after the MECO valve closure (no flag value from the ascent burn)",
                    "the staleness limit and the flag rate are Electronics' to confirm (ASSUMED 0.3 s, >= 10 Hz)",
                    "the seat-leak drain time of the segment is unknown: if Electronics shows that an emptying can start and finish "
                    "inside the staleness limit, the double-fault argument weakens and the maximin plan should be reconsidered"],
        status="GNC decision as asked by the lead (2026-10-13); simulation only")
    return out


def part_eval(tabs, plans):
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, iface=R.IFACE, sequence=dict(
        worst_s=SEQ_WORST, fault_s=SEQ_FAULT, lead_planning_value_s=LEAD_PLAN, source=SEQ_SRC),
        rc03=dict(file=RC03, in_hub=RC03 == HUB_RC03, sha256_16=sha16(RC03), tables=tabs),
        mapping="6-DOF thrust onset at the drawn E0->E2 delay after the relight command; t_ign_est = planning value",
        nominal=jl(os.path.join(OUT, "relight_v28_nominal.json")))
    a1s = json.load(open(f"{S}/duty_cycles_v3/duty_cycles_index_v3.json"))
    sz = max((c.get("engine_on_counter_s") or 0.0) for c in a1s["cycles"] if c["name"].startswith("DC-A1_full_flight_disp_p99"))
    mc = {}
    names = sorted(set(list(sweep_cases(tabs)) + list(full_cases(tabs, plans)) + list(fs_cases(tabs))))
    for name in names:
        rr = rows_csv(os.path.join(OUT, f"mc6_runs_{name}_v28.csv"))
        cj = jl(os.path.join(OUT, f"v28_case_{name}.json"))
        if not rr or not cj:
            continue
        base = name.split("_k2")[0].split("_", 3)[-1]
        st_ = TG.stats(rr, cj["m_n2o_mc_kg"], None)
        st_.update(note=cj["note"], fail_modes=cj["fail_modes"], planning_value_s=cj["config"]["t_ign_est"])
        sd = np.array([float(r["start_delay"]) for r in rr])
        st_["start_delay_min_p50_max_s"] = [float(sd.min()), float(np.median(sd)), float(sd.max())]
        err = sd - cj["config"]["t_ign_est"]
        ok = np.array([float(r["ok"]) for r in rr]) > 0.5
        st_["light_minus_plan_s_min_max"] = [float(err.min()), float(err.max())]
        for lab, m in (("early_gt_0.5s", err < -0.5), ("early_0.25_0.5s", (err >= -0.5) & (err < -0.25)),
                       ("within_0.25s", np.abs(err) <= 0.25), ("late_gt_0.25s", err > 0.25)):
            st_.setdefault("P_by_light_minus_plan", {})[lab] = dict(n=int(m.sum()), P=float(ok[m].mean()) if m.any() else None)
        bt = np.array([float(r["burn_time"]) for r in rr])
        st_["engine_on_counter_p99_max_s"] = [float(np.percentile(bt, 99)), float(bt.max())]
        st_["engine_on_counter_over_a1_sizing"] = dict(sizing_counter_s=sz, n_over=int(np.sum(bt > sz)))
        ref = rows_csv(os.path.join(RL181, f"mc6_runs_rl181_{base}_k2_rl181.csv"))
        if ref:
            st_["vs_late_1p81"] = dict(TG.pair(ref, rr), comparator=f"rl181_{base}_k2")
        mc[name] = st_
        v = st_.get("vs_late_1p81", {})
        print(f"{name:30s} P {st_['P']:.3f} [{st_['ci95'][0]:.3f},{st_['ci95'][1]:.3f}] vs LATE 1.81 {v.get('P_base', float('nan')):.3f}: "
              f"-{v.get('lost')}/+{v.get('gained')} p {v.get('p', float('nan')):.2g} | light-plan {err.min():+.2f}..{err.max():+.2f} s | "
              f"counter p99 {st_['engine_on_counter_p99_max_s'][0]:.2f} | usable p01 {st_['usable_left_p01_kg']:.3f} | {st_['fail_modes']}",
              flush=True)
    out["monte_carlo"] = mc
    out["option_c"] = option_c(tabs)
    oc = out["option_c"]
    for base, b in oc["by_base"].items():
        fp = b.get("fault_paired")
        if fp:
            print(f"(c) {base:9s} fault 1.37 s: plan {SEQ_WORST:.2f} P {fp['P_base']:.3f} -> plan {LEAD_PLAN:.2f} P {fp['P_case']:.3f} "
                  f"(-{fp['lost']}/+{fp['gained']}, p {fp['p']:.2g})", flush=True)
        for st, v in b.get("break_even_prior", {}).items():
            print(f"    {st:4s} primed {v['P_primed_plan_primed']:.3f} -> {v['P_primed_plan_unprimed']:.3f}; q* {v['q_star']:.3f} "
                  f"CI {v['q_star_ci95_bootstrap']}", flush=True)
        for st, v in b.get("fault_spread_paired", {}).items():
            print(f"    fault spread {st:4s}: plan {SEQ_WORST:.2f} P {v['P_base']:.3f} -> plan {LEAD_PLAN:.2f} P {v['P_case']:.3f} "
                  f"(-{v['lost']}/+{v['gained']}, p {v['p']:.2g})", flush=True)
        if "maximin" in b:
            print("    maximin", {k: round(v["worst_P"], 3) for k, v in b["maximin"].items()}, flush=True)
    print("q* range", oc["q_star_range"], flush=True)
    with open(os.path.join(OUT, "relight_v28.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", os.path.join(OUT, "relight_v28.json"))


def main():
    os.makedirs(OUT, exist_ok=True)
    tabs = e0e2_tables()
    for st, t in tabs.items():
        c = t["check"]
        print(f"{st}: E0->E2 min {t['quantiles_5pct_s'][0]:.3f} median {c['median_given']:.3f} p95 {c['p95_constructed']:.4f} "
              f"(given {c['p95_given']:.4f}) max {c['max_constructed']:.4f} (given {c['max_given']:.4f})", flush=True)
    plans = [float(x) for x in os.environ.get("GNC_V28_FULL", f"{LEAD_PLAN},{SEQ_WORST}").split(",")]
    sel = os.environ.get("GNC_V28_CASES")
    if "nominal" in PARTS:
        part_nominal(tabs)
    if "sweep" in PARTS:
        cs = sweep_cases(tabs)
        if sel:
            cs = {k: v for k, v in cs.items() if k in sel.split(",")}
        run_cases(cs)
    if "full" in PARTS:
        cs = full_cases(tabs, plans)
        if sel:
            cs = {k: v for k, v in cs.items() if k in sel.split(",")}
        run_cases(cs)
    if "fspread" in PARTS:
        cs = fs_cases(tabs)
        if sel:
            cs = {k: v for k, v in cs.items() if k in sel.split(",")}
        run_cases(cs)
    if "eval" in PARTS:
        part_eval(tabs, plans)


if __name__ == "__main__":
    main()

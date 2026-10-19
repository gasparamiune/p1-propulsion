"""m2_start_transient v1.1 (GNC, 2026-10-13; v1.1: eval only - oxidiser bound falls back on the ignition-lift
flow cap when Combustion's drogue_hold_check_v2p4.json is absent, and the persistence branch on vs off is paired directly): review REV-GNC-1 RG-01 start-transient re-fly with the decided drogue-release rule
(LEAD 2026-10-13: release at E2 AND [Pc >= 3.0 bar abs OR the >= 0.8 bar rise held continuously until E2 + 0.10 s]), sim6
v2.8-dev amendment S (m2_bitcheck_v28 v1.5 part S).

Question: with the fuel-starved start plateau that Combustion reports for the A relight (ignition_detect_v2p4 part B; relayed
bracket Pc 2.4-3.6 bar abs for 0.1-0.4 s after the light), does the decided rule keep P, and what does the persistence branch
buy against waiting for 3.0 bar? Plateau = delivered thrust held at the map thrust of the plateau Pc (2.4 bar: 27.3 N;
2.9 bar: 35.6 N; 3.6 bar: 47.8 N, Pc-equivalent) for st_T after the 6-DOF light, rising afterwards at the modelled rate limits.
Arms (all rel_mode 1, release pressure 3.0 bar abs, E2 at the 6-DOF light):
  L100      2.4 bar x 0.1 s, branch on (rel_to 0.10 s)
  L400      2.4 bar x 0.4 s, branch on: release on the persistence branch at E2 + 0.10 s, then 0.3 s of plateau thrust
  L400_nto  2.4 bar x 0.4 s, branch off (rel_to 0): release only at Pc >= 3.0 bar after the plateau (comparator for the branch)
  M400      2.9 bar x 0.4 s, branch on (just below the release pressure)
  H400      3.6 bar x 0.4 s, branch on: the Pc branch releases at once, then 0.4 s of plateau thrust
  L400_te   L400 with the relight planner allowing for the plateau (t_ign_est + 0.3 s): FSW mitigation candidate
Comparators (seed 101, 500 runs, paired exact McNemar): the decided rule without a plateau = the release_rule rel1 tables
(bitcheck v1.5 S1: reproduced exactly with the branch on, so the rel1 table IS the decided rule on the v2.8 start), and the
stored v2.8 tables. Decision rule: loses = P below the comparator and exact p < 0.05; within_1pct reported beside it.
Not modelled (amendment S): the oxidiser flow at the ignition lift during the plateau (the map books the flow of the plateau
thrust; bounded here with Combustion's ignition-lift oxidiser flow when drogue_hold_check_v2p4.json exists), Pc sensor error,
combustion roughness, the pad-start plateau. Relight NOT CLOSED (RG-01): a rule and transient sensitivity check, not a relight
acceptance.
Env: GNC_IFACE, GNC_ACT_RATE (v3c set), GNC_ST_PARTS (mc,eval), GNC_ST_SPLIT k/n, GNC_ST_ARMS (default all), GNC_ST_OUT.
Output: <out>/st_<base>_<arm>.csv, <out>/start_transient.json"""
import csv
import hashlib
import json
import os
import sys
import time
import numpy as np

S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_ST_OUT", f"{S}/start_transient")
os.environ.setdefault("GNC_PC_RATCHET", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_eng03_rate as E  # noqa: E402
import m2_mc6 as M  # noqa: E402

VERSION = "m2_start_transient v1.1"
PARTS = os.environ.get("GNC_ST_PARTS", "mc,eval").split(",")
SPLIT = os.environ.get("GNC_ST_SPLIT", "0/1")
N = 500
BASES = ("A1_none", "A1J_pc")
REL = f"{S}/release_rule"
COMB_DH = "/home/claude/work/combustion/data/v2/v2p4/drogue_hold_check_v2p4.json"
ARMS = {"L100": dict(rel_mode=1, rel_to=0.10, st_on=1, st_Pc=2.4e5, st_T=0.1),
        "L400": dict(rel_mode=1, rel_to=0.10, st_on=1, st_Pc=2.4e5, st_T=0.4),
        "L400_nto": dict(rel_mode=1, rel_to=0.0, st_on=1, st_Pc=2.4e5, st_T=0.4),
        "M400": dict(rel_mode=1, rel_to=0.10, st_on=1, st_Pc=2.9e5, st_T=0.4),
        "H400": dict(rel_mode=1, rel_to=0.10, st_on=1, st_Pc=3.6e5, st_T=0.4),
        "L400_te": dict(rel_mode=1, rel_to=0.10, st_on=1, st_Pc=2.4e5, st_T=0.4, _te=0.3)}
SEL = os.environ.get("GNC_ST_ARMS", "")
if SEL:
    ARMS = {k: v for k, v in ARMS.items() if k in SEL.split(",")}


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def cfg_of(base, te=0.0):
    over, csvp, bj = E.base_ref(base)
    m = json.load(open(bj))["m_n2o_mc_kg"]
    kw = dict({k: v for k, v in over.items() if k != "m_fixed"}, m_n2o=float(m))
    if te:
        kw["t_ign_est"] = float(kw.get("t_ign_est", R.DEF["t_ign_est"])) + te
    return R.cfg_of(**kw), csvp


def part_mc():
    os.makedirs(OUT, exist_ok=True)
    k, n = (int(x) for x in SPLIT.split("/"))
    jobs = [(b, a) for a in ARMS for b in BASES]
    for base, arm in jobs[k::n]:
        p = os.path.join(OUT, f"st_{base}_{arm}.csv")
        if os.path.exists(p) and os.path.getsize(p) > 100 and os.environ.get("GNC_ST_FORCE") != "1":
            print("exists", base, arm, flush=True)
            continue
        cfg, _ = cfg_of(base, ARMS[arm].get("_te", 0.0))
        D = R.draw(np.random.default_rng(101), N, cfg)
        t0 = time.time()
        rows = []
        for i in range(N):
            c, disp = R.run_cfg(cfg, D[i])
            c.update({kk: v for kk, v in ARMS[arm].items() if not kk.startswith("_")})
            res = R.fly(c, disp, nrec=10)[0]
            row = R.flat_row(i, D[i], res, R.success(res), cfg)
            row.update({kk: float(res[kk]) for kk in ("rel_t", "rel_Fpc", "rel_br", "rel_vz", "st_vz_end", "st_h_end")})
            rows.append(row)
        M.write_csv(p, rows)
        ok = np.array([r["ok"] for r in rows]) > 0.5
        print(f"{base:8s} {arm:9s}: P {ok.mean():.3f} ({time.time() - t0:.0f} s)", flush=True)


def rows_csv(p):
    return list(csv.DictReader(open(p))) if os.path.exists(p) else None


def col(rows, k):
    return np.array([float(r[k]) for r in rows])


def mcnemar(a, b):
    from scipy.stats import binomtest
    lost, gained = int(np.sum(a & ~b)), int(np.sum(~a & b))
    p = float(binomtest(lost, lost + gained, 0.5).pvalue) if lost + gained else 1.0
    return dict(P_ref=float(a.mean()), P_case=float(b.mean()), lost=lost, gained=gained, p_exact=p, n=int(len(a)),
                loses=bool(b.mean() < a.mean() and p < 0.05), within_1pct=bool(b.mean() - a.mean() >= -0.01))


def pct(x, qs=(1, 50, 99)):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if not len(x):
        return None
    return dict({f"p{q:02d}": float(np.percentile(x, q)) for q in qs}, min=float(x.min()), max=float(x.max()), n=int(x.size))


def fail_mode(r):
    if float(r["landed"]) < 0.5 or float(r.get("crash", 0)) > 0.5:
        return "no_touchdown_or_crash"
    if float(r["exhausted"]) > 0.5:
        return "exhausted"
    if float(r["tipover"]) > 0.5:
        return "tipover"
    if abs(float(r["td_vz"])) > R.CRIT["vz"]:
        return "vz"
    if float(r["td_vh"]) > R.CRIT["vh"]:
        return "vh"
    if float(r["td_tilt"]) > R.CRIT["tilt"]:
        return "tilt"
    return "rate"


def oxid_bound():
    """Oxidiser not booked during the plateau: Combustion's ignition-lift oxidiser flow x st_T (upper bound: the whole plateau
    flow counted as unbooked; the map does book the flow of the plateau thrust)."""
    if not os.path.exists(COMB_DH):
        cap = 37.4
        return dict(available=True, src="ignition-lift oxidiser flow cap 37.4 g/s: Combustion CF-3 temperature-dependent lift "
                                         "table (DERIVED), as quoted in the LEAD light-rule decision of 2026-10-13 (interfaces/"
                                         f"CHANGELOG.md); {COMB_DH} not found at evaluation time",
                    mox_A1_g_s_min_max=[None, cap], unbooked_bound_g={f"{T:.1f}s": cap * T for T in (0.1, 0.4)},
                    rule="ignition-lift oxidiser flow cap x plateau duration: upper bound of the unbooked mass (the map books the "
                         "flow of the plateau thrust, so the true unbooked mass is smaller)")
    d = json.load(open(COMB_DH))
    rows = d.get("rows") or d.get("corners") or []
    mox = [float(r["mox_g_s"]) for r in rows if isinstance(r, dict) and "mox_g_s" in r and str(r.get("state", "")).startswith("A1")]
    if not mox:
        return dict(available=False, note="no A1 rows with mox_g_s in the Combustion file")
    return dict(available=True, src=f"{COMB_DH} (sha256/16 {sha16(COMB_DH)})", mox_A1_g_s_min_max=[min(mox), max(mox)],
                unbooked_bound_g={f"{T:.1f}s": max(mox) * T for T in (0.1, 0.4)},
                rule="ignition-lift oxidiser flow max (A1 relight rows) x plateau duration: upper bound of the unbooked mass")


def part_eval():
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, method=__doc__.split("\n\n")[1].strip(),
               rule=("release at E2 AND [Pc >= 3.0 bar abs OR the >= 0.8 bar rise held continuously until E2 + 0.10 s] "
                     "(LEAD 2026-10-13)"), oxidiser_bound=oxid_bound(), cases={})
    for base in BASES:
        cfg, refp = cfg_of(base)
        ref = rows_csv(refp)
        relp = os.path.join(REL, f"rel_{base}_rel1.csv")
        rel = rows_csv(relp)
        okr, okd = col(ref, "ok") > 0.5, col(rel, "ok") > 0.5
        for arm, spec in ARMS.items():
            rows = rows_csv(os.path.join(OUT, f"st_{base}_{arm}.csv"))
            if not rows:
                continue
            par = R.build(dict(cfg, **{k: v for k, v in spec.items() if not k.startswith("_")}))[0]
            PN = {n: i for i, n in enumerate(s6.PAR_NAMES)}
            ok = col(rows, "ok") > 0.5
            br = col(rows, "rel_br")
            rt = col(rows, "rel_t")
            fails = [dict(run=int(r["run"]), mode=fail_mode(r), wind=round(float(r["wind"]), 2), td_vz=float(r["td_vz"]),
                          td_vh=float(r["td_vh"]), td_tilt=float(r["td_tilt"]), rel_t=float(r["rel_t"]), rel_br=float(r["rel_br"]),
                          st_vz_end=float(r["st_vz_end"]), decided_rule_ok=bool(okd[int(r["run"])]))
                     for r, o in zip(rows, ok) if not o]
            fm = {}
            for f in fails:
                fm[f["mode"]] = fm.get(f["mode"], 0) + 1
            e = dict(arm={k: v for k, v in spec.items()}, st_F_N=float(par[PN["st_F"]]), rel_F_N=float(par[PN["rel_F"]]),
                     rel_Frise_N=float(par[PN["rel_Frise"]]), t_ign_est_s=float(par[PN["t_ign_est"]]),
                     vs_decided_rule_no_plateau=mcnemar(okd, ok), vs_stored_v28=mcnemar(okr, ok),
                     P_wilson=[float(x) for x in R.wilson(int(ok.sum()), len(ok))],
                     release_branch_counts={"pc_or_v28": int(np.sum(br == 1.0)), "persistence": int(np.sum(br == 2.0)),
                                            "none": int(np.sum(br == 0.0))},
                     release_after_light_ms=pct(1e3 * rt[rt >= 0]), rel_vz=pct(col(rows, "rel_vz")[rt >= 0]),
                     st_vz_end=pct(col(rows, "st_vz_end")), st_h_end=pct(col(rows, "st_h_end")),
                     td_vz=pct(col(rows, "td_vz")), td_vh=pct(col(rows, "td_vh")), td_tilt=pct(col(rows, "td_tilt")),
                     liq_left_g=pct(1e3 * col(rows, "liq_left")),
                     liq_left_shift_vs_decided_g=pct(1e3 * (col(rows, "liq_left") - col(rel, "liq_left"))),
                     exhausted=int(np.sum(col(rows, "exhausted") > 0.5)), fail_modes=fm, failures=fails)
            out["cases"][f"{base}|{arm}"] = e
            m_ = e["vs_decided_rule_no_plateau"]
            print(f"{base:8s} {arm:9s}: P {m_['P_case']:.3f} vs decided {m_['P_ref']:.3f} (-{m_['lost']}/+{m_['gained']}, p "
                  f"{m_['p_exact']:.3g}{' LOSES' if m_['loses'] else ''}) | vs v2.8 -{e['vs_stored_v28']['lost']}/+"
                  f"{e['vs_stored_v28']['gained']} | branch {e['release_branch_counts']} | rel p50/p99 "
                  f"{e['release_after_light_ms']['p50']:.0f}/{e['release_after_light_ms']['p99']:.0f} ms | vz end p01 "
                  f"{(e['st_vz_end'] or {}).get('p01', float('nan')):.2f} | liq p01 {e['liq_left_g']['p01']:.0f} g | fm {fm}",
                  flush=True)
    # pooled A1_none + A1J_pc per arm against the decided rule
    pooled = {}
    for arm in ARMS:
        a, b = [], []
        for base in BASES:
            rows = rows_csv(os.path.join(OUT, f"st_{base}_{arm}.csv"))
            rel = rows_csv(os.path.join(REL, f"rel_{base}_rel1.csv"))
            if rows and rel:
                a.append(col(rel, "ok") > 0.5)
                b.append(col(rows, "ok") > 0.5)
        if a:
            pooled[arm] = mcnemar(np.concatenate(a), np.concatenate(b))
            m_ = pooled[arm]
            print(f"pooled {arm:9s}: P {m_['P_case']:.4f} vs {m_['P_ref']:.4f} -{m_['lost']}/+{m_['gained']} p {m_['p_exact']:.3g}"
                  f"{' LOSES' if m_['loses'] else ''}", flush=True)
    out["pooled_vs_decided_rule"] = pooled
    # the persistence branch itself: L400 (branch on) against L400_nto (branch off), same draws, same plateau
    br = {}
    a_, b_ = [], []
    for base in BASES:
        r0 = rows_csv(os.path.join(OUT, f"st_{base}_L400_nto.csv"))
        r1 = rows_csv(os.path.join(OUT, f"st_{base}_L400.csv"))
        if r0 and r1:
            o0, o1 = col(r0, "ok") > 0.5, col(r1, "ok") > 0.5
            br[base] = mcnemar(o0, o1)
            a_.append(o0)
            b_.append(o1)
    if a_:
        br["pooled"] = mcnemar(np.concatenate(a_), np.concatenate(b_))
        m_ = br["pooled"]
        print(f"branch on vs off (L400_nto -> L400) pooled: -{m_['lost']}/+{m_['gained']} p {m_['p_exact']:.3g}", flush=True)
    out["persistence_branch_on_vs_off_L400"] = br
    out["comparators"] = {b: dict(decided_rule_no_plateau=f"{REL}/rel_{b}_rel1.csv (sha256/16 {sha16(f'{REL}/rel_{b}_rel1.csv')})",
                                  stored_v28=f"{cfg_of(b)[1]} (sha256/16 {sha16(cfg_of(b)[1])})") for b in BASES}
    with open(os.path.join(OUT, "start_transient.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", os.path.join(OUT, "start_transient.json"), flush=True)


def main():
    if "mc" in PARTS:
        part_mc()
    if "eval" in PARTS:
        part_eval()


if __name__ == "__main__":
    main()

"""m2_purge_cost v1.0.1 (GNC, 2026-10-13; v1.0.1: eval labels only - the sim6 prg_tilt_* values are the body tilt from the
vertical, not the theta of the LEAD criterion): the pre-scheduled forced purge flown in the A1 reserve with the decided drogue-release
rule (LEAD decision 2026-10-13 on the Electronics v2.9 handback, interfaces/CHANGELOG.md: "PURGE is PRE-SCHEDULED (ends before
T_fire) as baseline, so the 0.81 s plan holds ... GNC flies the purge N2O cost (~76 g at 1.0 mm, ~50 g at 0.8 mm) in A1 reserve";
vent balanced or axial = no side force). Bounding check ahead of the full RG-01 re-fly (which waits for Combustion's P_abort and
start-delay tables on the re-routed coil with the purge at theta <= 2 deg).

Model (sim6 v2.8-dev amendment P, m2_bitcheck_v28 part P): the purge starts on the relight trigger evaluated prg_T + prg_lead
earlier and ends at the lift (prg_prio 1: the lift keeps the plain trigger); the tank loses prg_mdot of LIQUID for the whole
purge (upper bound of the mass); the flight software books prg_mdot_hat = prg_mdot into m_hat (prg_book 1); prg_jet 0 = no side
force (balanced vent; an axial vent adds about prg_mdot x 105.8 m/s = 2-3 N along the axis, not modelled). The ECU's
pre-scheduled purge runs a fixed 2.5 s and closes before T_fire, so the modelled purge (2.5 + 0.5 s anticipation, to the lift)
OVER-states the duration and the mass: this is a bounding arm, not the flight sequence.
Flows (DERIVED, Electronics hbleed_provision_v1 via electronics.json v2 da067408c1594814 / REPORT-v2.9-HANDBACK.md: 11.3 /
20.1 / 31.3 g/s through 0.6 / 0.8 / 1.0 mm; LEAD: ~76 g at 1.0 mm, ~50 g at 0.8 mm per 2.5 s purge):
  PS10       1.0 mm: prg_mdot 0.0313 kg/s (flown mass >= 76 g)
  PS08       0.8 mm: prg_mdot 0.0201 kg/s (flown mass >= 50 g)
  PS10_L400  PS10 + the Combustion fuel-starved start plateau 2.4 bar abs x 0.4 s (amendment S, branch on): purge mass and
             plateau together
All arms rel_mode 1 (release at E2 AND [Pc >= 3.0 bar abs OR rise held to E2 + 0.10 s]).
Comparator (seed 101, 500 runs, paired exact McNemar): the decided rule without purge and without plateau = the release_rule
rel1 tables (m2_bitcheck_v28 v1.5 S1: reproduced exactly with the branch on). Decision rule: loses = P below the comparator and
exact p < 0.05; within_1pct reported beside it.
Not modelled: vapour phase at the bleed (liquid booked: upper bound), the ECU's fixed 2.5 s timer and close-before-T_fire margin,
axial vent thrust, purge-start spurious triggers beyond those amendment P reproduces (P30 finding), Pc sensor error.
Relight NOT CLOSED (RG-01).
Env: GNC_IFACE, GNC_ACT_RATE (v3c set), GNC_PCOST_PARTS (mc,eval), GNC_PCOST_SPLIT k/n, GNC_PCOST_OUT.
Output: <out>/pc_<base>_<arm>.csv, <out>/purge_cost.json"""
import csv
import hashlib
import json
import os
import sys
import time
import numpy as np

S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_PCOST_OUT", f"{S}/purge_cost")
os.environ.setdefault("GNC_PC_RATCHET", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_eng03_rate as E  # noqa: E402
import m2_mc6 as M  # noqa: E402

VERSION = "m2_purge_cost v1.0.1"
PARTS = os.environ.get("GNC_PCOST_PARTS", "mc,eval").split(",")
SPLIT = os.environ.get("GNC_PCOST_SPLIT", "0/1")
N = 500
BASES = ("A1_none", "A1J_pc")
REL = f"{S}/release_rule"
ELEC = "/home/claude/work/shared-fallback/engine/interfaces/electronics.json"
DEC = dict(rel_mode=1, rel_to=0.10)
PRG = dict(prg_on=1, prg_T=2.5, prg_lead=0.5, prg_book=1, prg_jet=0, prg_prio=1)
ARMS = {"PS10": dict(DEC, **PRG, prg_mdot=0.0313, prg_mdot_hat=0.0313),
        "PS08": dict(DEC, **PRG, prg_mdot=0.0201, prg_mdot_hat=0.0201),
        "PS10_L400": dict(DEC, **PRG, prg_mdot=0.0313, prg_mdot_hat=0.0313, st_on=1, st_Pc=2.4e5, st_T=0.4)}
KEYS = ("rel_t", "rel_Fpc", "rel_br", "rel_vz", "st_vz_end", "st_h_end", "prg_t0", "prg_dur", "prg_wait", "prg_mass", "prg_h0",
        "prg_tilt_max", "prg_tilt_lift", "prg_rate_max")


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def cfg_of(base):
    over, csvp, bj = E.base_ref(base)
    m = json.load(open(bj))["m_n2o_mc_kg"]
    kw = dict({k: v for k, v in over.items() if k != "m_fixed"}, m_n2o=float(m))
    return R.cfg_of(**kw), csvp


def part_mc():
    os.makedirs(OUT, exist_ok=True)
    k, n = (int(x) for x in SPLIT.split("/"))
    jobs = [(b, a) for a in ARMS for b in BASES]
    for base, arm in jobs[k::n]:
        p = os.path.join(OUT, f"pc_{base}_{arm}.csv")
        if os.path.exists(p) and os.path.getsize(p) > 100 and os.environ.get("GNC_PCOST_FORCE") != "1":
            print("exists", base, arm, flush=True)
            continue
        cfg, _ = cfg_of(base)
        D = R.draw(np.random.default_rng(101), N, cfg)
        t0 = time.time()
        rows = []
        for i in range(N):
            c, disp = R.run_cfg(cfg, D[i])
            c.update(ARMS[arm])
            res = R.fly(c, disp, nrec=10)[0]
            row = R.flat_row(i, D[i], res, R.success(res), cfg)
            row.update({kk: float(res[kk]) for kk in KEYS})
            rows.append(row)
        M.write_csv(p, rows)
        ok = np.array([r["ok"] for r in rows]) > 0.5
        print(f"{base:8s} {arm:10s}: P {ok.mean():.3f} ({time.time() - t0:.0f} s)", flush=True)


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


def part_eval():
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, method=__doc__.split("\n\n")[0].strip(),
               model=__doc__.split("\n\n")[1].strip(),
               sources=dict(electronics_json=f"{ELEC} (sha256/16 {sha16(ELEC)})" if os.path.exists(ELEC) else "absent",
                            lead="interfaces/CHANGELOG.md 2026-10-13 lead decision on the Electronics handback (1)"),
               theta_note=("the LEAD criterion theta <= 2 deg at RELIGHT is the angle between the body axis and the specific "
                           "force at the hose station (m2_relight_attitude: arm A1|PS10_nojet for this purge); the purge "
                           "block below reports sim6 prg_tilt_* = the body tilt from the vertical under the drogue, a "
                           "different quantity that does not set the liquid position"), cases={})
    for base in BASES:
        cfg, _ = cfg_of(base)
        relp = os.path.join(REL, f"rel_{base}_rel1.csv")
        rel = rows_csv(relp)
        okd = col(rel, "ok") > 0.5
        for arm, spec in ARMS.items():
            rows = rows_csv(os.path.join(OUT, f"pc_{base}_{arm}.csv"))
            if not rows:
                continue
            ok = col(rows, "ok") > 0.5
            fails = [dict(run=int(r["run"]), mode=fail_mode(r), wind=round(float(r["wind"]), 2), td_vz=float(r["td_vz"]),
                          td_vh=float(r["td_vh"]), td_tilt=float(r["td_tilt"]), liq_left_g=1e3 * float(r["liq_left"]),
                          prg_mass_g=1e3 * float(r["prg_mass"]), decided_rule_ok=bool(okd[int(r["run"])]))
                     for r, o in zip(rows, ok) if not o]
            fm = {}
            for f in fails:
                fm[f["mode"]] = fm.get(f["mode"], 0) + 1
            tl = col(rows, "prg_tilt_lift")
            e = dict(arm=spec, vs_decided_rule=mcnemar(okd, ok), P_wilson=[float(x) for x in R.wilson(int(ok.sum()), len(ok))],
                     purge=dict(started=int(np.sum(col(rows, "prg_t0") >= 0)), mass_g=pct(1e3 * col(rows, "prg_mass")),
                                duration_s=pct(col(rows, "prg_dur")[col(rows, "prg_dur") >= 0]),
                                start_height_m=pct(col(rows, "prg_h0")[col(rows, "prg_t0") >= 0]),
                                body_tilt_from_vertical_max_during_deg=pct(col(rows, "prg_tilt_max")),
                                body_tilt_from_vertical_at_lift_deg=pct(tl),
                                body_rate_max_during_dps=pct(col(rows, "prg_rate_max"))),
                     release_after_light_ms=pct(1e3 * col(rows, "rel_t")[col(rows, "rel_t") >= 0]),
                     release_branch_counts={"pc": int(np.sum(col(rows, "rel_br") == 1.0)),
                                            "persistence": int(np.sum(col(rows, "rel_br") == 2.0))},
                     td_vz=pct(col(rows, "td_vz")), td_vh=pct(col(rows, "td_vh")), td_tilt=pct(col(rows, "td_tilt")),
                     liq_left_g=pct(1e3 * col(rows, "liq_left")),
                     liq_left_shift_vs_decided_g=pct(1e3 * (col(rows, "liq_left") - col(rel, "liq_left"))),
                     exhausted=int(np.sum(col(rows, "exhausted") > 0.5)),
                     exhausted_decided=int(np.sum(col(rel, "exhausted") > 0.5)), fail_modes=fm, failures=fails)
            out["cases"][f"{base}|{arm}"] = e
            m_ = e["vs_decided_rule"]
            pu = e["purge"]
            print(f"{base:8s} {arm:10s}: P {m_['P_case']:.3f} vs decided {m_['P_ref']:.3f} (-{m_['lost']}/+{m_['gained']}, p "
                  f"{m_['p_exact']:.3g}{' LOSES' if m_['loses'] else ''}) | purge {pu['started']} mass p50/max "
                  f"{pu['mass_g']['p50']:.1f}/{pu['mass_g']['max']:.1f} g dur {pu['duration_s']['min']:.2f}-"
                  f"{pu['duration_s']['max']:.2f} s | body tilt@lift p99/max {pu['body_tilt_from_vertical_at_lift_deg']['p99']:.2f}/"
                  f"{pu['body_tilt_from_vertical_at_lift_deg']['max']:.2f} deg | liq p01 "
                  f"{e['liq_left_g']['p01']:.0f} g shift p50 {e['liq_left_shift_vs_decided_g']['p50']:.1f} g | exhausted "
                  f"{e['exhausted']} (decided {e['exhausted_decided']}) | fm {fm}", flush=True)
    pooled = {}
    for arm in ARMS:
        a, b = [], []
        for base in BASES:
            rows = rows_csv(os.path.join(OUT, f"pc_{base}_{arm}.csv"))
            rel = rows_csv(os.path.join(REL, f"rel_{base}_rel1.csv"))
            if rows and rel:
                a.append(col(rel, "ok") > 0.5)
                b.append(col(rows, "ok") > 0.5)
        if a:
            pooled[arm] = mcnemar(np.concatenate(a), np.concatenate(b))
            m_ = pooled[arm]
            print(f"pooled {arm:10s}: P {m_['P_case']:.4f} vs {m_['P_ref']:.4f} -{m_['lost']}/+{m_['gained']} p "
                  f"{m_['p_exact']:.3g}{' LOSES' if m_['loses'] else ''}", flush=True)
    out["pooled_vs_decided_rule"] = pooled
    out["comparators"] = {b: f"{REL}/rel_{b}_rel1.csv (sha256/16 {sha16(f'{REL}/rel_{b}_rel1.csv')})" for b in BASES}
    with open(os.path.join(OUT, "purge_cost.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", os.path.join(OUT, "purge_cost.json"), flush=True)


def main():
    if "mc" in PARTS:
        part_mc()
    if "eval" in PARTS:
        part_eval()


if __name__ == "__main__":
    main()

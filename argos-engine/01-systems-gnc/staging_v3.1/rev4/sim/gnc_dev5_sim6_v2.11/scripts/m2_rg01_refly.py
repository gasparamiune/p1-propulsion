"""m2_rg01_refly v1.3 (GNC rev2, 2026-10-13; v1.1: late arms for amendments a and c and the apogee trim, apogee and Pc-invalid statistics; v1.2: amendment c arms at the low open-loop factor pcf_k 0.875; v1.3: amendment c arms with the L400 plateau; earlier tables unchanged): REV-GNC-1 RG-01 re-fly on Combustion's RG-01 line-state tables, with the
decided purge sequence, the decided drogue-release predicate, ONE declared flight FSW (REV-GNC-2 N1) and the purge mass in the
A1 reserve at the ECU cap.

Decided baseline flown (LEAD, interfaces/CHANGELOG.md lines 142, 154, 156, 160, 161, 164, 166, 168):
  relight      deterministic RELIGHT at the planned T_fire (E0); plan 0.81 s (NOT frozen); W 0.65 s (Combustion tables);
               no retry. Flag UNKNOWN = UNPRIMED: prep path, plan 1.41 s (arms liqP / pwP).
  purge        sim6 v2.9-dev amendment G: PURGE committed at E0 - 2.90 s by the gated commit predictor (quasi-steady drogue
               descent, constant-velocity extrapolation beyond the plain lag), flow 0.35 s after the command for 2.5 s,
               closed 0.05 s before E0, ECU flow cap 2.5 s, T_fire never before 1.9 s of flow (the plain trigger may bring it
               forward, the FSW delays it instead). Balanced/axial vent: no side force (prg_jet 0). Mass booked (prg_book 1).
               G73: 73.0 g per purge (29.2 g/s x 2.5 s; Combustion line 163 bound at the ECU cap, lead line 166 (3)).
               G76: 76 g (lead plan allowance, line 160 (5)). PS10: the rev1 bounding arm (amendment P, 31.3 g/s from the
               early trigger to the lift, 2.6-3.4 s, 81-107 g) kept as the upper bound.
  release      RELEASE iff RUN AND b4 AND [(Pc valid AND >= 300 kPa abs) OR b7 OR (Pc invalid AND t >= t_E2 + 0.10 s)],
               latched (line 168 (1)); Pc valid in this study: amendments R + S (rel_mode 1, rel_to 0.10 s), b7 on the
               (noise-free) Pc-equivalent thrust. Plateau bracket: L400 = fuel-starved start 2.4 bar abs x 0.4 s
               (Combustion line 155 worst corner 2.60-2.62 bar lies above it); L400o = L400 with the measured-P0 offset
               +0.71 bar (lead line 166 (1): the relative E2 is unchanged, the absolute 3.0 bar branch then fires at a true
               2.29 bar abs).
  FSW          FSW-R2 (one configuration for every arm and base): stored v2.8 base FSW (m2_eng03_rate.base_ref, k_est_asc 2)
               + decided release rule + flown mass estimator tot_cal_comp (m2_mass_est_v2.run_cfg_case: ARM weighing,
               Pc offset, start allowance, flow calibration, growth model g_hat 0.09 with the base J_ref, lever-arm /
               direction compensation kest_comp 1) + fct_comp 1 (FC_THRUST not armed on A1: lead line 168 (5); flt_on 0).
Line states (Combustion rg01_line_states_v2p4.json part2_line_states_for_gnc; start delay = E0 -> E2 given-light 5 %
quantiles drawn per run from the run6 own generator (seed 20261018): the same quantile u in every state and arm (paired)):
  liq   liquid_line (reference: primed, liquid to the seat)                          P_abort 0      max 0.499 s
  pw    purged_unlined_Tp2.5_0-2deg_worst (8.15 cm3 pocket)                            P_abort 0      max 0.626 s
  pl    purged_unlined_Tp2.5_0-2deg_least (4.77 cm3)                                   P_abort 0      max 0.573 s
  e19   purged_unlined_Tp1.9_robust_edge_0-2deg_worst (14.88 cm3; sensitivity)          P_abort 0      max 0.730 s
  nrLO  purge_not_run_unlined_LO_0-2deg_worst (FAILURE STATE, no purge mass)            P_abort 0.242  given-light max 0.628 s
  nrHI  purge_not_run_unlined_HI_0-2deg_worst (FAILURE STATE)                           P_abort 1.000  (not flown: P_total 0)
  bf    bleed_fault_closure_unconfirmed (FAILURE STATE): pw delays + stuck-open bleed 31.24 g/s ADDITIVE from E0 to the end
        of the flight (amendment P blf_ph 4, blf_mode 0, balanced vent bl_vj 0); FC action on BLEED_FAULT LOG-ONLY (l.168 (2))
  liqP / pwP  flag UNKNOWN -> prep path: delay + 0.56 s (Electronics v2.8 prep re-run, DERIVED), plan 1.41 s
Accounting (RG-02): P_total,s = P|lit,s x (1 - P_abort,s) x (1 - p_nl), per state, no weighted mean (pi_s unknown);
p_nl,ign unknown (TO-DEFINE, torch qualification): 0 / 0.005 / 0.02 / 0.05.
Comparators (paired exact McNemar, seed 101, 500 runs): (a) liq|none on the same base and plateau = the liquid plan without
purge (total cost of the RG-01 fix); (b) liq with the same purge arm (line-state effect alone); continuity: liq|none against
the stored-FSW decided-rule table (release_rule rel1, v2.8 liquid table).
Mass sensitivity (task 5, LEAD line 164 (7)): +0.60 kg point mass on the fixed engine module (2 x 0.30 kg bleed valves, MASS
RISK), ballast_z = middle of the mechanical.json engine bay zone (ASSUMED location), arms *_m60.
Apogee trim (lead line 168 (4)): h_target arms *_h<m> (>= 275 m adopted without decision).
Not modelled: vapour re-growth between the end of the flow and E0 when E0 is late, valve-time dispersion, the ECU timer,
canopy pendulum (drogue quasi-steady, massless), purge vapour fraction (liquid booked: mass upper bound at the given total),
Pc sensor error, IGN-1/T1 ignition-delay data (tables ASSUMED delays). SIM only, no physical validation.
Env: GNC_IFACE, GNC_ACT_RATE, GNC_IFACE_PIN (rev2 pin list), GNC_RG01_PARTS (mc,eval), GNC_RG01_SPLIT k/n, GNC_RG01_ARMS
(comma list of arm names), GNC_RG01_OUT.
Output: <out>/rf_<base>_<arm>.csv, <out>/rg01_refly.json"""
import csv
import hashlib
import json
import os
import sys
import time
import numpy as np

S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_RG01_OUT", f"{S}/rev2/rg01_refly")
os.environ.setdefault("GNC_PC_RATCHET", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_eng03_rate as E  # noqa: E402
import m2_mass_est_v2 as MV  # noqa: E402
import m2_mc6 as M  # noqa: E402

VERSION = "m2_rg01_refly v1.3"
PARTS = os.environ.get("GNC_RG01_PARTS", "mc,eval").split(",")
SPLIT = os.environ.get("GNC_RG01_SPLIT", "0/1")
N = 500
COMB = os.path.join(os.environ.get("GNC_COMB_V2P4", "/home/claude/work/shared-fallback/engine/02-combustion/data/v2p4"), "rg01_line_states_v2p4.json")   # hub v2.4 pinned copy (HASHES.txt)
COMB_SHA16 = "2939549811d4c381"
REL = f"{S}/release_rule"                                       # stored-FSW decided-rule tables (continuity only)
TG = f"{S}/throat_growth/throat_growth.json"
STATE_KEYS = {"liq": "liquid_line", "pw": "purged_unlined_Tp2.5_0-2deg_worst", "pl": "purged_unlined_Tp2.5_0-2deg_least",
              "e19": "purged_unlined_Tp1.9_robust_edge_0-2deg_worst", "nrLO": "purge_not_run_unlined_LO_0-2deg_worst",
              "nrHI": "purge_not_run_unlined_HI_0-2deg_worst", "bf": "purged_unlined_Tp2.5_0-2deg_worst"}
PREP_S = 0.56          # DERIVED Electronics v2.8 prep re-run (1.37 - 0.81 s), as rev1 m2_relight_seg44 prepLO / prepHI
PLAN = 0.81            # DESIGN plan value (NOT frozen)
PLAN_PREP = 1.41       # DESIGN lead line 161 (3): UNKNOWN = UNPRIMED
DEC = dict(rel_mode=1, rel_to=0.10, fct_comp=1)
GSEQ = dict(prg_on=1, pgg_on=1, prg_book=1, prg_jet=0)
PURGE = {"none": {},
         "G73": dict(GSEQ, prg_mdot=0.0292, prg_mdot_hat=0.0292),
         "G76": dict(GSEQ, prg_mdot=0.0304, prg_mdot_hat=0.0304),
         "G73z": dict(GSEQ, prg_mdot=0.0, prg_mdot_hat=0.0292),   # PURGE NOT RUN: sequence + booking flown, no flow
         "PS10": dict(prg_on=1, prg_T=2.5, prg_lead=0.5, prg_book=1, prg_jet=0, prg_prio=1, prg_mdot=0.0313, prg_mdot_hat=0.0313)}
PLAT = {"": {}, "L400": dict(st_on=1, st_Pc=2.4e5, st_T=0.4), "L400o": dict(st_on=1, st_Pc=2.4e5, st_T=0.4, rel_Pc=2.29e5)}
BLEED = dict(blf_on=1, blf_ph=4, blf_mdot=0.03124, blf_mode=0, bl_vj=0.0)
M60 = 0.60             # MASS RISK LEAD line 164 (7)
BASES_MAIN = ("A1_none", "A1J_pc")
BASES_EXTRA = ("A1_pc", "A1J_none")


def _arms():
    a = {}
    for st, pu in (("liq", "none"), ("liq", "G73"), ("liq", "G76"), ("liq", "PS10"), ("pw", "G73"), ("pw", "G76"), ("pw", "PS10"),
                   ("pl", "G73"), ("e19", "G73"), ("nrLO", "none"), ("nrLO", "G73z"), ("bf", "G73"), ("liqP", "G73"), ("pwP", "G73")):
        a[f"{st}|{pu}"] = dict(state=st, purge=pu, plat="", bases=BASES_MAIN + (BASES_EXTRA if (st, pu) in (
            ("liq", "none"), ("liq", "G73"), ("pw", "G73"), ("pl", "G73"), ("e19", "G73")) else ()))
    for st, pu in (("liq", "none"), ("liq", "G73"), ("pw", "G73"), ("e19", "G73"), ("bf", "G73")):
        a[f"{st}|{pu}|L400"] = dict(state=st, purge=pu, plat="L400", bases=BASES_MAIN)
    for st, pu in (("liq", "G73"), ("pw", "G73")):
        a[f"{st}|{pu}|L400o"] = dict(state=st, purge=pu, plat="L400o", bases=BASES_MAIN)
    for st, pu in (("liq", "none"), ("liq", "G73"), ("pw", "G73")):
        a[f"{st}|{pu}|m60"] = dict(state=st, purge=pu, plat="", bases=BASES_MAIN, m60=True)
    # amendment (a) quantification (after the re-fly): late commit on the plain trigger (T_fire delayed to t_go + 2.30 s)
    # and commit height floors (lowest safe commit height); amendment (c): Pc invalid from E2 (pcf_dt 0) per release rule
    for nm, ex in (("ant0", dict(pgg_ant=0.0)), ("hf100", dict(pgg_ant=0.0, pgg_hfl=100.0)),
                   ("hf90", dict(pgg_ant=0.0, pgg_hfl=90.0)), ("hf80", dict(pgg_ant=0.0, pgg_hfl=80.0)),
                   ("hf70", dict(pgg_ant=0.0, pgg_hfl=70.0)), ("hf60", dict(pgg_ant=0.0, pgg_hfl=60.0)),
                   ("pcfR0", dict(pcf_on=1, pcf_dt=0.0, pcf_rule=0)), ("pcfR1", dict(pcf_on=1, pcf_dt=0.0, pcf_rule=1)),
                   ("pcfR2", dict(pcf_on=1, pcf_dt=0.0, pcf_rule=2)), ("pcfR3", dict(pcf_on=1, pcf_dt=0.0, pcf_rule=3)),
                   ("pcfR1fo", dict(pcf_on=1, pcf_dt=0.0, pcf_rule=1, pcf_fo=1)),
                   ("pcfR2fo", dict(pcf_on=1, pcf_dt=0.0, pcf_rule=2, pcf_fo=1)),
                   ("pcfR3fo", dict(pcf_on=1, pcf_dt=0.0, pcf_rule=3, pcf_fo=1)),
                   # v1.2: open-loop thrust/flow per command at the low Cd-band end (pcf_k 0.875) with the engine lit
                   ("pcfR1k875", dict(pcf_on=1, pcf_dt=0.0, pcf_rule=1, pcf_k=0.875)),
                   ("pcfR2k875", dict(pcf_on=1, pcf_dt=0.0, pcf_rule=2, pcf_k=0.875)),
                   # v1.3: Pc invalid from E2 with the 2.4 bar x 0.4 s plateau (L400): accelerometer confirmation near pcf_tmax
                   ("pcfR1L400", dict(pcf_on=1, pcf_dt=0.0, pcf_rule=1, st_on=1, st_Pc=2.4e5, st_T=0.4)),
                   ("pcfR2L400", dict(pcf_on=1, pcf_dt=0.0, pcf_rule=2, st_on=1, st_Pc=2.4e5, st_T=0.4))):
        # late commit / height floor: the flow can be cut to 1.9 s -> Tp1.9 robust-edge delay table (conservative for every run)
        st_ = "e19" if nm.startswith(("ant0", "hf")) else "pw"
        a[f"{st_}|G73|{nm}"] = dict(state=st_, purge="G73", plat="", bases=BASES_MAIN, gex=ex, late=True)
    for h in (290, 285, 280, 275):
        for st, pu in (("liq", "G73"), ("pw", "G73")):
            a[f"{st}|{pu}|h{h}"] = dict(state=st, purge=pu, plat="", bases=BASES_MAIN, h_target=float(h), late=True)
            a[f"{st}|{pu}|m60|h{h}"] = dict(state=st, purge=pu, plat="", bases=BASES_MAIN, h_target=float(h), m60=True, late=True)
    return a


ARMS = _arms()


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def comb_states():
    if sha16(COMB) != COMB_SHA16:
        raise RuntimeError(f"{COMB} sha256/16 {sha16(COMB)} != pinned {COMB_SHA16}")
    v = json.load(open(COMB))["part2_line_states_for_gnc"]["v"]
    out = {}
    for s, k in STATE_KEYS.items():
        x = v[k] if k in v else None
        q = list(x["E0_E2_given_light_quantiles_5pct_s"]) if x else []
        out[s] = dict(key=k, P_abort=float(x["P_abort_W0p65"]), q=q, E0_E2_all=x["E0_E2_all_s"],
                      seq=x.get("sequence_P1_S1_C1_S2_C2_cm3"))
    for s in ("liq", "pw"):
        out[s + "P"] = dict(out[s], key=out[s]["key"] + " + prep path 0.56 s", q=[float(z) + PREP_S for z in out[s]["q"]])
    return out


def engine_bay_mid():
    """z [m] of the +0.60 kg mass risk: the fixed (non-gimballed) engine module, ledger item P07 'fixed TVC module'
    (DESIGN placement for the bleed-valve mass risk, lead line 164 (7)); returns (z, bay_zone, z_pivot)."""
    info = R.build(base_cfg("A1_none")[0])[5]
    g = info.get("geo") or {}
    z = [float(it["z"]) for it in info["ledger"] if str(it.get("name", "")).startswith("P07")]
    if len(z) != 1:
        raise RuntimeError("fixed engine module P07 not found in the mass ledger")
    return z[0], g.get("bay_zone"), g.get("z_pivot")


_BC = {}


def base_cfg(base, state="liq", extra=None):
    """(cfg, m_n2o) of a base with the state's start-delay table and plan; extra = cfg overrides (h_target, ballast)."""
    over, csvp, bj = E.base_ref(base)
    m = float(json.load(open(bj))["m_n2o_mc_kg"])
    st = comb_states()[state]
    o = {k: v for k, v in over.items() if k != "m_fixed"}
    o.update(t_ign_q=tuple(float(x) for x in st["q"]), t_ign_add=0.0,
             t_ign_est=PLAN_PREP if state.endswith("P") else PLAN, m_n2o=m)
    if extra:
        o.update(extra)
    return R.cfg_of(**o), m


def arm_extra(spec, bay_z):
    ex = {}
    if spec.get("h_target"):
        ex["h_target"] = spec["h_target"]
    if spec.get("m60"):
        ex["ballast"] = M60
        ex["ballast_z"] = bay_z
    return ex


def fly_arm(base, name, bay_z):
    spec = ARMS[name]
    st = spec["state"]
    stc = "pw" if st == "bf" else st
    cfg, m = base_cfg(base, stc, arm_extra(spec, bay_z))
    jr = json.load(open(TG))["j_ref"]
    MV.TG_JREF_DEFAULT = float(jr["A1J" if base.startswith("A1J") else "A1"])
    D = R.draw(np.random.default_rng(101), N, cfg)
    ms = MV.case_specs()["tot_cal_comp"]
    rows = []
    for i in range(N):
        c, disp = MV.run_cfg_case(cfg, D[i], ms, i, "base")
        c.update(DEC)
        c.update(PURGE[spec["purge"]])
        c.update(PLAT[spec["plat"]])
        if spec.get("gex"):
            c.update(spec["gex"])
        if st == "bf":
            c.update(BLEED)
        res = R.fly(c, disp, nrec=10)[0]
        row = R.flat_row(i, D[i], res, R.success(res), cfg)
        row["m_n2o"] = m
        row["mest_kcal"] = float(c.get("mest_kcal", float("nan")))
        rows.append(row)
    return rows


def part_mc():
    os.makedirs(OUT, exist_ok=True)
    sel = os.environ.get("GNC_RG01_ARMS")
    names = [n for n in ARMS if (not sel or n in sel.split(","))]
    if not sel:
        names = [n for n in names if not ARMS[n].get("late")]
    jobs = [(b, n) for n in names for b in ARMS[n]["bases"]]
    k, n_ = (int(x) for x in SPLIT.split("/"))
    bay_z, bz, zp = engine_bay_mid()
    print(f"engine bay zone {bz} z_pivot {zp} -> ballast_z {bay_z}", flush=True)
    for base, name in jobs[k::n_]:
        p = os.path.join(OUT, f"rf_{base}_{name.replace('|', '_')}.csv")
        if os.path.exists(p) and os.path.getsize(p) > 100 and os.environ.get("GNC_RG01_FORCE") != "1":
            print("exists", base, name, flush=True)
            continue
        t0 = time.time()
        rows = fly_arm(base, name, bay_z)
        M.write_csv(p, rows)
        ok = np.array([r["ok"] for r in rows]) > 0.5
        ex = int(np.sum([r["exhausted"] > 0.5 for r in rows]))
        print(f"{base:9s} {name:18s}: P {ok.mean():.3f} exhausted {ex} ({time.time() - t0:.0f} s)", flush=True)


# ------------------------------------------------------------------------------------------------------------- evaluation
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


def usable_g(rows):
    """usable liquid reserve at the end of the flight [g]: liq_left - the unusable residual (sim6 resid = 0.03 x the liquid
    mass at t0, ASSUMED; read here as 0.03 x m_n2o, the loaded N2O)."""
    return 1e3 * (col(rows, "liq_left") - 0.03 * col(rows, "m_n2o"))


def arm_stats(rows, st, cs):
    ok = col(rows, "ok") > 0.5
    fm = {}
    for r, o in zip(rows, ok):
        if not o:
            k_ = fail_mode(r)
            fm[k_] = fm.get(k_, 0) + 1
    us = usable_g(rows)
    lo = np.argsort(us)[:5]
    e = dict(P=float(ok.mean()), n=int(len(ok)), P_wilson=[float(x) for x in R.wilson(int(ok.sum()), len(ok))], fail_modes=fm,
             exhausted=int(np.sum(col(rows, "exhausted") > 0.5)),
             usable_reserve_g=pct(us, (1, 5, 50)), usable_reserve_lowest5=[dict(run=int(rows[j]["run"]), g=float(us[j]),
                                                                                 ok=bool(ok[j])) for j in lo],
             usable_reserve_runs_14_108={str(j): float(us[j]) for j in (14, 108) if j < len(us)},
             start_delay_s=pct(col(rows, "start_delay"), (50, 99)), purge_mass_g=pct(1e3 * col(rows, "prg_mass"), (50, 99)),
             td_vz=pct(col(rows, "td_vz"), (1, 50, 99)), h_ign=pct(col(rows, "h_ign"), (1, 50, 99)),
             apogee_m=pct(col(rows, "h_max"), (1, 50, 99)),
             release_after_light_ms=pct(1e3 * col(rows, "rel_t")[col(rows, "rel_t") >= 0], (50, 99)),
             release_branch={"pc": int(np.sum(col(rows, "rel_br") == 1.0)), "persistence": int(np.sum(col(rows, "rel_br") == 2.0))})
    if "pgg_src" in rows[0] and np.any(col(rows, "pgg_t0") > 0):
        e["purge_sequence"] = dict(
            commit_source={str(int(k)): int(np.sum(col(rows, "pgg_src") == k)) for k in (1, 2, 3)},
            commit_height_m=pct(col(rows, "pgg_h0"), (1, 50, 99)), flow_s=pct(col(rows, "pgg_fl"), (1, 50, 99)),
            E0_height_m=pct(col(rows, "pgg_hE0"), (1, 50, 99)),
            tfire_delay_vs_plain_s=pct(col(rows, "pgg_dly")[col(rows, "pgg_tgo") >= 0], (50, 99)),
            plain_fired_before_E0=int(np.sum(col(rows, "pgg_tgo") >= 0)),
            plain_margin_at_E0_m=pct(col(rows, "pgg_mrg"), (1, 50, 99)),
            gate_open_height_m=pct(col(rows, "pgg_hopen"), (1, 50, 99)),
            gate_open_to_commit_s=pct(col(rows, "pgg_t0") - col(rows, "pgg_topen"), (1, 50)),
            spurious=int(np.sum(col(rows, "pgg_spur") > 0.5)), aq_max=pct(col(rows, "pgg_aqmax"), (50, 99)))
    if "pcf_t0" in rows[0] and np.any(col(rows, "pcf_t0") > 0):
        e["pc_invalid"] = dict(onset_after_light_s=pct(col(rows, "pcf_t0") - col(rows, "t_relight") - col(rows, "start_delay"), (50,)),
                               released_interim=int(np.sum(col(rows, "pcf_rel") == 1.0)),
                               released_accel=int(np.sum(col(rows, "pcf_rel") == 2.0)), aborted=int(np.sum(col(rows, "pcf_abt") > 0.5)),
                               release_after_light_ms=pct(1e3 * col(rows, "pcf_relt")[col(rows, "pcf_relt") >= 0], (50, 99)),
                               Facc_max_N=pct(col(rows, "pcf_Facc_max"), (1, 50, 99)), no_release=int(np.sum(col(rows, "rel_t") < 0)),
                               td_vz_no_release=pct(col(rows, "td_vz")[col(rows, "rel_t") < 0], (1, 50, 99)))
    if st == "bf":
        e["bleed"] = dict(mass_g=pct(1e3 * col(rows, "blf_mass"), (50, 99)), time_s=pct(col(rows, "blf_time"), (50, 99)))
    e["failures"] = [dict(run=int(r["run"]), mode=fail_mode(r), wind=round(float(r["wind"]), 2), usable_g=float(u),
                          td_vz=float(r["td_vz"]), start_delay=float(r["start_delay"]))
                     for r, o, u in zip(rows, ok, us) if not o][:40]
    pa = cs[st if st != "bf" else "pw"]["P_abort"] if st not in ("liqP", "pwP") else cs[st]["P_abort"]
    e["P_abort"] = pa
    e["P_total"] = {f"p_nl={x}": float(ok.mean() * (1.0 - pa) * (1.0 - x)) for x in (0.0, 0.005, 0.02, 0.05)}
    return e


def part_eval():
    cs = comb_states()
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, run6=R.__doc__.split("\n")[0][:120],
               method=__doc__.split("\n\n")[0].strip(), model=__doc__.split("\n\n")[1].strip(),
               sources=dict(rg01_line_states=f"{COMB} (sha256/16 {sha16(COMB)})",
                            throat_growth=f"{TG} (sha256/16 {sha16(TG)})",
                            pins=os.environ.get("GNC_IFACE_PIN"), iface=os.environ.get("GNC_IFACE"),
                            act_rate=os.environ.get("GNC_ACT_RATE")),
               states={k: dict(key=v["key"], P_abort=v["P_abort"], E0_E2_given_light_max_s=(max(v["q"]) if v["q"] else None),
                               E0_E2_all=v["E0_E2_all"]) for k, v in cs.items()},
               plan_check={}, cases={}, paired={}, pooled={}, continuity={})
    bases_all = BASES_MAIN + BASES_EXTRA
    for name, spec in ARMS.items():
        for base in spec["bases"]:
            rows = rows_csv(os.path.join(OUT, f"rf_{base}_{name.replace('|', '_')}.csv"))
            if rows:
                out["cases"][f"{base}|{name}"] = arm_stats(rows, spec["state"], cs)
    # paired comparisons
    for name, spec in ARMS.items():
        tail = name.split("|")[2:]
        plat = spec["plat"]
        ref_a = "liq|none" + ("|" + plat if plat else "") + ("|m60" if spec.get("m60") and not spec.get("h_target") else "")
        if spec.get("h_target") or spec.get("gex"):
            ref_a = f"{spec['state']}|{spec['purge']}" + ("|m60" if spec.get("m60") else "")
        ref_b = f"liq|{spec['purge']}" + ("|" + "|".join(tail) if tail else "")
        A, B, Cb = [], [], []
        for base in spec["bases"]:
            r = rows_csv(os.path.join(OUT, f"rf_{base}_{name.replace('|', '_')}.csv"))
            ra = rows_csv(os.path.join(OUT, f"rf_{base}_{ref_a.replace('|', '_')}.csv"))
            rb = rows_csv(os.path.join(OUT, f"rf_{base}_{ref_b.replace('|', '_')}.csv")) if ref_b in ARMS else None
            if not r:
                continue
            ok = col(r, "ok") > 0.5
            d = {}
            if ra and ref_a != name:
                d["vs_" + ref_a] = mcnemar(col(ra, "ok") > 0.5, ok)
                d["reserve_shift_vs_" + ref_a + "_g"] = pct(usable_g(r) - usable_g(ra), (1, 50))
                A.append((col(ra, "ok") > 0.5, ok))
            if rb and ref_b != name and ref_b != ref_a:
                d["vs_" + ref_b] = mcnemar(col(rb, "ok") > 0.5, ok)
                B.append((col(rb, "ok") > 0.5, ok))
            if spec.get("gex") and spec["state"] != "pw":
                rp = rows_csv(os.path.join(OUT, f"rf_{base}_pw_G73.csv"))
                if rp:
                    d["vs_pw|G73(decided)"] = mcnemar(col(rp, "ok") > 0.5, ok)
            out["paired"][f"{base}|{name}"] = d
            if base in BASES_MAIN:
                Cb.append(base)
        if A:
            pa = [x for x, b_ in zip(A, spec["bases"]) if b_ in BASES_MAIN]
            if len(pa) == len(BASES_MAIN):
                out["pooled"][f"{name}|vs_{ref_a}|main2"] = mcnemar(np.concatenate([x[0] for x in pa]), np.concatenate([x[1] for x in pa]))
            if len(A) > len(pa):
                out["pooled"][f"{name}|vs_{ref_a}|all{len(A)}"] = mcnemar(np.concatenate([x[0] for x in A]),
                                                                          np.concatenate([x[1] for x in A]))
        if B:
            out["pooled"][f"{name}|vs_{ref_b}"] = mcnemar(np.concatenate([x[0] for x in B]), np.concatenate([x[1] for x in B]))
    # continuity: FSW-R2 liquid plan against the stored-FSW decided-rule tables (rel1, v2.8 liquid table)
    for base in BASES_MAIN:
        r = rows_csv(os.path.join(OUT, f"rf_{base}_liq_none.csv"))
        s = rows_csv(os.path.join(REL, f"rel_{base}_rel1.csv"))
        if r and s:
            out["continuity"][base] = dict(note="FSW-R2 (flown estimator, rg01 liquid table) vs stored v2.8 FSW decided-rule table",
                                           paired=mcnemar(col(s, "ok") > 0.5, col(r, "ok") > 0.5),
                                           stored=f"{REL}/rel_{base}_rel1.csv (sha256/16 {sha16(os.path.join(REL, f'rel_{base}_rel1.csv'))})")
    # plan check (0.81 s plan against the largest drawn start delay per state)
    for st in ("liq", "pw", "pl", "e19", "nrLO"):
        q = cs[st]["q"]
        out["plan_check"][st] = dict(E0_E2_given_light_max_s=max(q), plan_s=PLAN, margin_s=PLAN - max(q),
                                     E0_E2_all_max_s=cs[st]["E0_E2_all"]["max"])
    with open(os.path.join(OUT, "rg01_refly.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", os.path.join(OUT, "rg01_refly.json"), flush=True)
    for k, e in out["cases"].items():
        print(f"{k:34s} P {e['P']:.3f} ex {e['exhausted']} res p01/min {e['usable_reserve_g']['p01']:.0f}/"
              f"{e['usable_reserve_g']['min']:.0f} g r14/108 {e['usable_reserve_runs_14_108']} fm {e['fail_modes']}", flush=True)
    for k, e in out["pooled"].items():
        print(f"pooled {k:50s} {e['P_case']:.4f} vs {e['P_ref']:.4f} -{e['lost']}/+{e['gained']} p {e['p_exact']:.3g}"
              f"{' LOSES' if e['loses'] else ''}", flush=True)


def main():
    if "mc" in PARTS:
        part_mc()
    if "eval" in PARTS:
        part_eval()


if __name__ == "__main__":
    main()

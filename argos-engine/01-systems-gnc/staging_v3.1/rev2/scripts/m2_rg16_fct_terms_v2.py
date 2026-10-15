"""m2_rg16_fct_terms v2.1 (GNC rev2, 2026-10-13; v2.1: eval adds budget form B, per-flight random terms; the fct runs are v2.0): REV-GNC-2 item 4 - the RG-16 FC_THRUST mass terms on the decided purge
path (2 x 0.707 mm restrictors, all-liquid 31.24 g/s; Combustion purge_vented_mass_v2p4, flow from E0 - 2.55 s to E0 - 0.05 s),
both sides, in the adopted budget form (3 sigma RSS of the random terms + sum of the bias bounds, LEAD line 168) and as the
realised Monte Carlo check (method of v1.0.1).

Terms (m_hat = flown estimator of m2_mass_est v2; offsets applied as a CONSTANT m_hat offset from ARM, conservative):
  PURGE BOOKING, missed-detection side (m_hat under-reads): booked - vented. Booking bound = the path's all-liquid flow over
    the ECU-capped 2.5 s, 31.24 x 2.5 = 78.1 g (DERIVED upper bound of what the FSW can book; FSW-R2 books 73.0 g) minus the
    smallest vented mass at t_flow 2.5 s (34.3 g, Combustion table, SIM on ASSUMED Cd / slip) = 43.8 g (DERIVED); flown as the
    coordinator's bound -45 g.
  PURGE NOT BOOKED, over-read side: + the largest vented mass, max(table 72.9 g, flown truth 29.2 g/s x 2.5 s = 73.0 g) = 73.0 g.
  STUCK-OPEN BLEED (fault, over-read side; outside the nominal budget): + the largest bled mass at 31.24 g/s: A1 from the relight
    lift (re-fly bf|G73 arms, A1_none and A1J_pc), B1 from the first ignition (m2_b1_m60 arm blf31).
Cases: A1 flown on the decided path (FSW-R2 decided release rule + decided purge sequence G73) WITH its own comparators (same
    case, no offset, same path); B1 on the m2_fc_thrust B1 configuration with the rev1 comparator fct_mest_v2.json (B1 has no
    purge; sim options-off identity m2_bitcheck_v29).
Budget line per side (relative thrust-estimate error in the FC window, F_acc = m_hat x a):
    random 1 sigma = RSS(mass-estimate random, m2_mest_budget v1 A1_none fc; FC frame random = (eps p50 - eps p1) / 2.326 of
    the comparator, DERIVED, includes run-to-run spread -> conservative)
    bias = mass-estimate bias bound (m2_mest_budget v1) + purge term / m_FC_min + |median accelerometer offset b_sys| of the comparator
    miss side passes if 670 N x (1 - total) > 650 N; over-read side passes if F_true,max,FC x (1 + total) < 650 N.
Env: m2r2_env.sh; GNC_RG16_PARTS (fct,eval), GNC_RG16_OUT (out/rev2/rg16_v2), GNC_RG16_SPLIT (0/1), GNC_MEST2_NFCT (200)."""
import hashlib
import json
import os
import sys
import numpy as np

S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_RG16_OUT", f"{S}/rev2/rg16_v2")
PARTS = os.environ.get("GNC_RG16_PARTS", "fct,eval").split(",")
SPLIT = os.environ.get("GNC_RG16_SPLIT", "0/1")
os.environ.setdefault("GNC_PC_RATCHET", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import sim6 as s6  # noqa: E402
import m2_mass_est_v2 as MV  # noqa: E402
import m2_rg01_refly as F  # noqa: E402

VERSION = "m2_rg16_fct_terms v2.1"
FCT0 = dict(MV.FCT_CASES)
VENT = os.path.join(os.environ.get("GNC_COMB_V2P4", "/home/claude/work/shared-fallback/engine/02-combustion/data/v2p4"),
                    "purge_vented_mass_v2p4.json")
VENT_SHA16 = "0038561f71a51502"
BASEFCT_B1 = f"{S}/mass_est_v2/fct_mest_v2.json"
BUDGET = f"{S}/mass_est_v2/mest_budget_v1.json"
REFLY = f"{S}/rev2/rg01_refly"
B1M = f"{S}/rev2/b1_m60"
TP = 2.5
BOOK_BOUND_G = 45.0          # coordinator bound for the booking residual (REV-GNC-2 item 4)
PATH_A1 = dict(F.DEC, **F.PURGE["G73"])


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def vent_terms():
    if sha16(VENT) != VENT_SHA16:
        raise RuntimeError(f"{VENT} sha256/16 {sha16(VENT)} != pinned {VENT_SHA16}")
    d = json.load(open(VENT))
    row = [r for r in d["rows"] if abs(float(r["t_flow_s"]) - TP) < 1e-9][0]
    liq = float(d["flows_g_s"]["all_liquid"])
    booked_max = liq * TP
    return dict(source=f"{VENT} (sha256/16 {sha16(VENT)})", t_flow_s=TP, vented_g=dict(min=row["min_g"], p50=row["p50_g"],
                p99=row["p99_g"], max=row["max_g"]), all_liquid_g_s=liq, booked_bound_g=booked_max,
                booked_FSW_R2_g=1e3 * PATH_A1["prg_mdot_hat"] * TP,
                residual_bound_g=booked_max - float(row["min_g"]), residual_FSW_R2_g=1e3 * PATH_A1["prg_mdot_hat"] * TP - float(row["min_g"]),
                flown_miss_offset_g=max(BOOK_BOUND_G, booked_max - float(row["min_g"])),
                not_booked_g=max(float(row["max_g"]), 1e3 * PATH_A1["prg_mdot"] * TP), tag="DERIVED (Combustion v2.4 SIM table)")


def bled_max_g():
    a1 = []
    for b in F.BASES_MAIN:
        r = F.rows_csv(os.path.join(REFLY, f"rf_{b}_bf_G73.csv"))
        if r:
            a1.append(float(np.max(F.col(r, "blf_mass"))))
    rb = F.rows_csv(os.path.join(B1M, "b1_blf31.csv"))
    return dict(A1=1e3 * max(a1) if a1 else None, B1=1e3 * float(np.max(F.col(rb, "blf_mass"))) if rb else None,
                A1_src=f"{REFLY}/rf_*_bf_G73.csv", B1_src=f"{B1M}/b1_blf31.csv")


def cases():
    v = vent_terms()
    b = bled_max_g()
    C = {}
    for nm in ("H_cal", "H_cal_comp", "Llo_re", "Llo_cmd", "Lhi_re", "Lhi_cmd"):
        C[("A1", f"{nm}_path")] = (nm, dict(FCT0[nm], w_bias=0.0, extra=PATH_A1))
    for nm in ("H_cal", "H_cal_comp", "Llo_re", "Llo_cmd"):
        C[("A1", f"{nm}_pbk")] = (nm, dict(FCT0[nm], w_bias=-1e-3 * v["flown_miss_offset_g"], extra=PATH_A1))
    for nm in ("H_cal", "Lhi_re", "Lhi_cmd"):
        C[("A1", f"{nm}_pnb")] = (nm, dict(FCT0[nm], w_bias=1e-3 * v["not_booked_g"], extra=PATH_A1))
    if b["A1"] is not None:
        C[("A1", "H_cal_blf31")] = ("H_cal", dict(FCT0["H_cal"], w_bias=1e-3 * b["A1"], extra=PATH_A1))
    if b["B1"] is not None:
        for nm in ("H_cal", "H_cal_comp"):
            C[("B1", f"{nm}_blf31")] = (nm, dict(FCT0[nm], w_bias=1e-3 * b["B1"]))
    return C


_ORIG = MV.run_cfg_case


def run_cfg_case_bias(cfg, dr, spec, i, prior):
    c, disp = _ORIG(cfg, dr, spec, i, prior)
    wb = float(spec.get("w_bias", 0.0))
    if wb != 0.0:
        c = dict(c, mest_w=float(c.get("mest_w", 0.0)) + wb)
    if spec.get("extra"):
        c = dict(c, **spec["extra"])
    return c, disp


def part_fct():
    MV.run_cfg_case = run_cfg_case_bias
    MV.OUT = OUT
    os.makedirs(OUT, exist_ok=True)
    k, n = (int(x) for x in SPLIT.split("/"))
    jr = json.load(open(F.TG))["j_ref"]
    for (prof, name), (_, spec) in list(cases().items())[k::n]:
        MV.TG_JREF_DEFAULT = float(jr[prof])
        MV.FCT_CASES = {name: spec}
        MV.SPLIT = "0/2" if prof == "A1" else "1/2"
        MV.part_fct()


def side_budget(d, mrow, term_g, m_min, sign):
    """Budget line of one case: relative errors (fractions)."""
    q = d["eps_pooled"]["values"]          # quantiles at EPS_Q (0.1, 1, 5, 50, 95, 99, 99.9)
    s_frame = (q[3] - q[1]) / 2.326 if sign < 0 else (q[5] - q[3]) / 2.326
    s_mass = mrow["random_rss_1sigma"]
    rnd = float(np.hypot(s_frame, s_mass))
    bias = mrow["bias_linear_bound"] + term_g * 1e-3 / m_min + abs(float(d["b_sys_at_onsets"]["values"][3]))
    # form B (per-flight random terms only: the run-to-run spread of the systematic error at the onsets b_sys, RSS the
    # mass-estimate random; single-frame noise left to the 3-frame persistence, which the realised Monte Carlo checks)
    qb = d["b_sys_at_onsets"]["values"]
    s_run = (qb[3] - qb[1]) / 2.326 if sign < 0 else (qb[5] - qb[3]) / 2.326
    rnd_b = float(np.hypot(s_run, s_mass))
    return dict(random_1sigma=rnd, frame_1sigma=s_frame, mass_1sigma=s_mass, bias_sum=bias, total=3.0 * rnd + bias,
                purge_term=term_g * 1e-3 / m_min,
                formB_per_flight=dict(run_1sigma=s_run, random_1sigma=rnd_b, bias_sum=bias, total=3.0 * rnd_b + bias))


def part_eval():
    v, b = vent_terms(), bled_max_g()
    bud = json.load(open(BUDGET))["bases"]["A1_none"]["line"]["fc"]
    m_min = []
    for base in F.BASES_MAIN:
        r = F.rows_csv(os.path.join(REFLY, f"rf_{base}_liq_G73.csv"))
        if r:
            m_min.append(float(np.min(F.col(r, "m_land"))))
    m_min = min(m_min) if m_min else None
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, method=__doc__.split("\n\n")[1].strip(),
               threshold_N=MV.T_ABORT, stuck_N=MV.F_STUCK, vent=v, bled_max_g=b, m_FC_min_kg=m_min,
               mass_budget_A1_fc=dict(bud, source=f"{BUDGET} (sha256/16 {sha16(BUDGET)})"), cases={}, budget={})
    base_b1 = json.load(open(BASEFCT_B1))["cases"]
    for (prof, name), (bname, spec) in cases().items():
        p = os.path.join(OUT, f"fct2_{prof}_{name}.json")
        if not os.path.exists(p):
            continue
        d = json.load(open(p))
        rows = d.pop("runs", [])
        if prof == "A1":
            pc = os.path.join(OUT, f"fct2_A1_{bname}_path.json")
            cmp_ = json.load(open(pc)) if os.path.exists(pc) else None
        else:
            cmp_ = base_b1.get(f"B1|{bname}")
        s670 = d["stuck"]["670"]
        e = dict(w_bias_g=1e3 * spec["w_bias"], comparator=(f"A1|{bname}_path" if prof == "A1" else f"rev1 B1|{bname}"),
                 held_max_N=d["held_max_fc_N"]["max"], margin_to_650_N=d["held_max_fc_N"]["margin_to_650_N"],
                 runs_above_650=d["held_max_fc_N"]["runs_above_650"], b_sys_min=d["b_sys_at_onsets"]["min"],
                 b_sys_p50=d["b_sys_at_onsets"]["values"][3], miss670=f"{s670['misses']}/{s670['cases']}",
                 pre_onset_alarms_670=s670["pre_onset_alarms"], miss876=f"{d['stuck']['876']['misses']}/{d['stuck']['876']['cases']}",
                 P=d["P"], mhe_fc_min_max=d["mhe_fc_min_max"],
                 Ftrue_max_fc_N=float(np.nanmax([r_["Ftrue_max_fc_N"] or np.nan for r_ in rows])) if rows else None)
        if cmp_ is not None and name != f"{bname}_path":
            e.update(cmp_held_max_N=cmp_["held_max_fc_N"]["max"], cmp_miss670=f"{cmp_['stuck']['670']['misses']}/"
                     f"{cmp_['stuck']['670']['cases']}", cmp_b_sys_min=cmp_["b_sys_at_onsets"]["min"], cmp_P=cmp_["P"])
        out["cases"][f"{prof}|{name}"] = e
        print(f"{prof}|{name:16s} w {e['w_bias_g']:+7.1f} g | held max {e['held_max_N']:.1f} N (margin {e['margin_to_650_N']:.1f}; "
              f">650 {e['runs_above_650']}) | b_sys min {100 * e['b_sys_min']:+.2f} % | 670 miss {e['miss670']} pre "
              f"{e['pre_onset_alarms_670']} | 876 miss {e['miss876']} | P {e['P']:.3f} | cmp held {e.get('cmp_held_max_N')}", flush=True)
    # budget lines on the A1 decided path (H_cal comparator on the path; FSW-R2 compensated estimator = H_cal_comp)
    for cname in ("H_cal_path", "H_cal_comp_path"):
        p = os.path.join(OUT, f"fct2_A1_{cname}.json")
        if not os.path.exists(p) or m_min is None:
            continue
        d = json.load(open(p))
        rows = d.pop("runs", [])
        Ftm = float(np.nanmax([r_["Ftrue_max_fc_N"] or np.nan for r_ in rows]))
        miss = side_budget(d, bud, v["flown_miss_offset_g"], m_min, -1)
        over_nb = side_budget(d, bud, v["not_booked_g"], m_min, +1)
        over_bk = side_budget(d, bud, 0.0, m_min, +1)
        out["budget"][cname] = dict(
            F_true_max_fc_N=Ftm,
            miss_side=dict(miss, stuck_N=670.0, detected_F_N=670.0 * (1.0 - miss["total"]),
                           passes=bool(670.0 * (1.0 - miss["total"]) > 650.0), allowed_total=1.0 - 650.0 / 670.0,
                           formB_passes=bool(670.0 * (1.0 - miss["formB_per_flight"]["total"]) > 650.0)),
            over_read_booked=dict(over_bk, worst_estimate_N=Ftm * (1.0 + over_bk["total"]),
                                  passes=bool(Ftm * (1.0 + over_bk["total"]) < 650.0)),
            over_read_not_booked=dict(over_nb, worst_estimate_N=Ftm * (1.0 + over_nb["total"]),
                                      passes=bool(Ftm * (1.0 + over_nb["total"]) < 650.0)))
        bb = out["budget"][cname]
        print(f"budget {cname}: miss total {100 * miss['total']:.2f} % (allowed {100 * bb['miss_side']['allowed_total']:.2f}) "
              f"-> {bb['miss_side']['passes']} (form B {100 * miss['formB_per_flight']['total']:.2f} % -> {bb['miss_side']['formB_passes']}); over booked {100 * over_bk['total']:.2f} % -> {bb['over_read_booked']['worst_estimate_N']:.1f} N "
              f"{bb['over_read_booked']['passes']}; not booked {100 * over_nb['total']:.2f} % -> "
              f"{bb['over_read_not_booked']['worst_estimate_N']:.1f} N {bb['over_read_not_booked']['passes']}", flush=True)
    with open(os.path.join(OUT, "rg16_fct_terms_v2.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", os.path.join(OUT, "rg16_fct_terms_v2.json"), flush=True)


if __name__ == "__main__":
    if "fct" in PARTS:
        part_fct()
    if "eval" in PARTS:
        part_eval()

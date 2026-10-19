"""m2_rev4_report v1.0 (GNC rev4, 2026-10-19): builds the rev4 results file and the corrected gnc.json v3.2 proposal set
from the rev4 evidence files (no flight here; every number is read from an evidence file named with its sha256/16, or is
quoted from one checked in this session and marked so).
Outputs (work area): out/rev4/rev4_results.json and out/rev4/v32/v32_proposals_rev4.json.
The lead publishes gnc.json; v3.2 goes through REV-GNC-5's delta re-check first (lead 208 (6), 10-19 order). GNC does not
write hub/interfaces/gnc.json. Labels: SIM (flown in sim6), DERIVED (computed from SIM tables or linear models), ASSUMED,
DATASHEET, TO-VERIFY. Nothing here is physical approval; there is no hardware data."""
import hashlib
import json
import os
import time
from collections import OrderedDict

VERSION = "m2_rev4_report v1.0"
SP = "/home/claude/work/space"
O = f"{SP}/out/rev4"
HUB = "/home/claude/work/shared-fallback/engine"
REV3R = f"{HUB}/01-systems-gnc/staging_v3.1/rev3/results/rev3_results.json"
F = dict(
    p2=f"{O}/p2/p2_rev4.json", lm=f"{O}/p2/landing_mass_coverage_h210.json",
    e11f=f"{O}/eng11/fly_v351_h210/eng11_fly.json", e11pose=f"{O}/eng11/lin_v351/eng11_pose.json",
    e11ends=f"{O}/eng11/lin_v351/eng11_ends.json", e11final=f"{O}/eng11/lin_v351/eng11_final.json", e11place=f"{O}/eng11/lin_v351/eng11_place.json",
    e11sens=f"{O}/eng11/lin_v351/eng11_sens.json", e11ksmin=f"{O}/eng11/lin_v351/eng11_ksmin.json",
    e11kstruct=f"{O}/eng11/lin_v351/eng11_kstruct.json", e11mink=f"{O}/eng11/lin_v351/eng11_mink.json",
    e11grid=f"{O}/eng11/lin_v351/eng11_grid.json", e11self=f"{O}/eng11/lin_v351/eng11_selfcheck.json",
    re24=f"{O}/re24/v351_h210/re24.json", bc_func=f"{O}/bitcheck_v213/bitcheck_v213_func.json",
    bc_off=f"{O}/bitcheck_v213/bitcheck_v213_offparts.json", bc_fail=f"{O}/bitcheck_v213/bitcheck_v213_func_v1.0_FAILS.json",
    pl=f"{O}/payload/payload_rev4.json", pl5=f"{O}/payload_n500/payload_rev4.json", plchk=f"{O}/payload/payload_check.json",
    r2s=f"{O}/r2_starve/r2_starve.json", v32fix=f"{O}/v32/v32_recompute.json", dcrit=f"{O}/v32/dcrit_210.json",
    wmark=f"{O}/wmark/WITHDRAWN_INDEX.json", rev3=REV3R,
    mass351=f"{O}/mass_v351/mass_v351_vs_v3d.json", mass352=f"{O}/mass_v352/mass_v352_vs_v3d.json")


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16] if os.path.exists(p) else None


def J(k):
    return json.load(open(F[k])) if os.path.exists(F[k]) else None


def ev(*ks):
    return [dict(path=F[k], sha256_16=sha16(F[k])) for k in ks if os.path.exists(F[k])]


def r(x, n=3):
    return None if x is None else round(float(x), n)


# ------------------------------------------------------------------------------------------------ summarisers
def s_p2(p2):
    out = OrderedDict(rule=p2["rule_l208"], delta_pp=p2["delta_pp"], onset_g=p2["onset_g"], variants=OrderedDict())
    for vn, v in p2["variants"].items():
        e = OrderedDict(label=v["label"], landing_mass_delta_kg=v.get("landing_mass_delta_kg"),
                        band_all_states_m=v.get("band_l208_all_states_m"), lowest_flown_m=v.get("lowest_flown_m"), states=OrderedDict())
        for st, s in v["states"].items():
            rl = s["rule_l208"]
            se = OrderedDict(band_m=rl["band_m"], pattern=rl["pattern"], bands=OrderedDict())
            for h, b in s["bands"].items():
                l = b["l208"]
                be = OrderedDict(n=l["n"], P_ref=l["P_ref"], P_case=l["P_case"], lost=l["lost"], gained=l["gained"],
                                 p_exact=l["p_exact"], deficit_pp=l["deficit_pp"], ub95_pp=l["ub95_pp"],
                                 ub95_newcombe_pp=l.get("ub95_newcombe_pp"))
                for extra in ("four_base_pooled_informational", "G80_vs_v3d_ref", "G80_vs_same_band_G73"):
                    if extra in b:
                        be[extra] = b[extra]
                se["bands"][h] = be
            e["states"][st] = se
        hf = [int(h) for st in v["states"].values() for h in st["bands"]]
        if hf and max(hf) <= 215 and vn != "v351":
            e["note"] = (f"flown only at {min(hf)}-{max(hf)} m: a band equal to the highest flown band is upper-censored "
                         "(the true band may be higher)")
        out["variants"][vn] = e
    return out


def s_payload(pl, pl5):
    """Per arm: prefer the N=500/base evaluation when it exists, keep the N=250 result beside it."""
    arms = OrderedDict()
    for src, d in (("N250", pl), ("N500", pl5)):
        if not d:
            continue
        for nm, a in d["mc"]["arms"].items():
            e = arms.setdefault(nm, OrderedDict(payload_kg=a["payload_kg"], h_target_m=a["h_target_m"], m_n2o_kg=a["m_n2o_kg"]))
            v = a["vs_v3d_ref_l208"]
            e[src] = OrderedDict(
                N_per_base=d["mc"]["N_per_base"],
                P80_per_base={b: r(x["P_80g"]) for b, x in a["per_base"].items()},
                exhausted_per_base={b: x["exhausted"] for b, x in a["per_base"].items()},
                h_ign_p50_m={b: r(x["h_ign_m"]["p50"], 1) for b, x in a["per_base"].items()},
                fail_modes={b: {k: n for k, n in x["fail_modes"].items() if n} for b, x in a["per_base"].items()},
                pooled_vs_v3d_ref=OrderedDict((k, v[k]) for k in ("n", "P_ref", "P_case", "lost", "gained", "p_exact",
                                                                  "deficit_pp", "ub95_pp", "ub95_newcombe_pp")),
                line208_pass=bool((not v["loses"]) and v["ub95_pp"] <= 1.0),
                vs_P2_v351_h210=a["vs_P2_v351_h210"])
    for nm, e in arms.items():
        best = e.get("N500") or e.get("N250")
        e["decision_N"] = best["N_per_base"]
        e["line208_pass_at_decision_N"] = best["line208_pass"]
    return arms


def s_grid(g):
    if not g:
        return None
    out = OrderedDict(bending_Hz_by_condition={k: r(v, 2) for k, v in g["bending_Hz_by_condition"].items()}, axes=OrderedDict())
    for a in ("alpha", "beta"):
        rows = [x for x in g["grid"] if x["axis"] == a]
        out["axes"][a] = OrderedDict(
            grid=[OrderedDict(K_s=x["K_s"], pass_6dB=x["pass_6dB"], gm_up_min_dB=r(x["gm_up_min_dB"], 2),
                              pm_abs_min_deg=r(x["pm_abs_min_deg"], 1), sm_min=r(x["sm_min"], 3),
                              f_landing_pose_range_Hz=[r(y, 2) for y in x["f_landing_pose_range_Hz"]],
                              f_full_pose_range_Hz=(None if x["f_full_pose_range_Hz"] is None else [r(y, 2) for y in x["f_full_pose_range_Hz"]]),
                              rigid_pm_abs_min_deg=(None if not x.get("rigid_with_lowest_notch") else r(x["rigid_with_lowest_notch"].get("pm_abs_min_deg"), 1)),
                              worst=x["worst"]) for x in rows],
            passing_K_s=[x["K_s"] for x in rows if x["pass_6dB"]], failing_K_s=[x["K_s"] for x in rows if not x["pass_6dB"]])
        out["axes"][a]["bending_shift_test"] = [OrderedDict(K_s=x["K_s"], wb_scale=x["wb_scale"], pass_6dB=x["pass_6dB"],
                                                            gm_up_min_dB=r(x["gm_up_min_dB"], 2), worst=x["worst"])
                                                for x in g["shift"] if x["axis"] == a]
    return out


def s_r2s(d):
    out = OrderedDict(N=d["N"], base=d["base"], state=d["state"], sim=d["sim"], iface=d["iface"], settings=d["settings"],
                      plateau=d["plateau"], windows=OrderedDict())
    for nm, c in d["cases"].items():
        out["windows"][nm] = OrderedDict(window_s=c["window_s"], threshold_N=c["threshold_N"],
                                         starve_threshold_s=c["starve_threshold_s"],
                                         by_st_T={k: dict(released=v["all"]["released"], aborted=v["all"]["aborted"],
                                                          landed=v["all"]["landed"], rel_t_max_s=r(v["all"]["rel_t_max_s"], 3),
                                                          W10lt6_released=f"{v['W10lt6']['released']}/{v['W10lt6']['n']}")
                                                  for k, v in c["by_st_T"].items()})
    return out


# ------------------------------------------------------------------------------------------------ main
def main():
    p2, pl, pl5, r2s, dc, lm, v32f, rev3 = J("p2"), J("pl"), J("pl5"), J("r2s"), J("dcrit"), J("lm"), J("v32fix"), J("rev3")
    grid = s_grid(J("e11grid"))
    pay = s_payload(pl, pl5)
    now = time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime())
    res = OrderedDict(id="GNC-rev4", version=VERSION, date="2026-10-19", generated_utc=now, owner="01-systems-gnc",
                      status="AUTHOR RESULT, not reviewed; REV-GNC-5 delta re-check before gnc.json v3.2",
                      labels="SIM / DERIVED / ASSUMED / DATASHEET / TO-VERIFY on every figure; no hardware data; not physical approval",
                      why="lead CHANGELOG 208 (6), 209, 213, 214; lead messages 2026-10-13 18:55Z (payload) and ~19:05Z (R2 v2); "
                          "coordinator order 2026-10-19 ('Lets finish this')",
                      evidence_files={k: dict(path=v, sha256_16=sha16(v)) for k, v in F.items() if os.path.exists(v)})
    res["A1_apogee_P2"] = s_p2(p2)
    res["landing_mass_coverage"] = OrderedDict(
        tag="DERIVED from SIM tables (P2 v351 h210, N=1000/base, 80 g onset)", per_base_state=lm,
        statement=("COVERED: the rev4 210 m landing set flies the v3.5.1 landing mass. Dispersed touchdown mass 14.18-18.13 kg "
                   "(p01 14.50, p50 16.03, p99 17.47 kg); 42-43 % of runs land at >= 16.15 kg (the lead's v3.5.1 landing "
                   "estimate) with P(80 g) 0.974-0.986 in that sub-population (0.986-0.991 below it; unpaired, not a test). "
                   "52-53 % of runs exceed the 16.0 kg upper bound of gnc.json v3.1 landing_mass_window_kg, so the v3.2 window "
                   "must be widened to the flown range (proposal [11])."),
        nominal_touchdown_mass_kg=dict(value=16.111, tag="SIM deterministic, dm 0, tank at 0.58 m, A1_none liq 210 m",
                                       source=F["pl"]))
    res["ENG11"] = OrderedDict(
        sixdof=dict(tag="SIM, N=500/base, liq|G73|v351|h210, 10 arms (S 3133/5353/7406 x K_s 58/116, K_s 174, spread)",
                    result="no arm loses against the P2 table (all p >= 0.25), including K_s 58; K_s 58 raises the A1J_pc "
                           "max_gim_acc p99 to 776-998 deg/s2 (K_s 116/174: 197-238; reference p99 1210); pooled P 0.983-0.987",
                    note="the 6-DOF uses the sim's own actuator/structure model and does not represent the linear-model "
                         "flex corner set; it does not overrule the linear GM requirement", evidence=ev("e11f")),
        linear=OrderedDict(
            tag="DERIVED (linear CSI, m2_eng11 v1.1 + m2_eng11_grid v1.0); K_s, J, mount damping and the first bending "
                "mode ASSUMED; V5c structure DERIVED from FEA",
            metric="ENG-07d: closed loop stable and upper GM >= 6 dB at every floor20 corner (9 poses x 2 axes x zeta "
                   "0.02/0.05/0.10 x notch error 0.95/1/1.05 x landing/full conditions)",
            grid=grid,
            bisection_parts_superseded=("ksmin (alpha fixed 157.0, beta fixed 95.4 N m/rad) and mink assume monotone "
                                        "pass/fail in K_s or structure scale, which the grid refutes; kept as found, "
                                        "SUPERSEDED by the grid"),
            evidence=ev("e11self", "e11ends", "e11pose", "e11place", "e11sens", "e11ksmin", "e11kstruct", "e11mink", "e11grid", "e11final")))
    res["RE24"] = OrderedDict(tag="SIM, gnc_dev7 sim6 v2.13-dev amendment J, N=500/base, liq|G73|v351|h210; jam bound "
                                  "ASSUMED (Electronics S6/SIL v2.10 monitor 1.5 deg + 40 ms x model rate, 50 ms)",
                              evidence=ev("re24", "bc_func", "bc_off", "bc_fail"))
    res["payload"] = OrderedDict(
        tag="SIM (flights) / DERIVED (iso-margin, T/W, tank sizing) / ASSUMED (point payload at A05 z 1.15 m, tank layout)",
        vehicle=pl["vehicle"] if pl else None, payload_model=pl["payload"] if pl else None,
        criterion=pl["criterion"] if pl else None, check=J("plchk"),
        deterministic=dict(iso=pl["deterministic"]["summary_apogee"] if pl else None,
                           load=pl["deterministic"]["summary_load"] if pl else None),
        mc=pay, evidence=ev("pl", "pl5", "plchk"))
    res["R2v2"] = OrderedDict(starve=s_r2s(r2s) if r2s else None, evidence=ev("r2s"))
    res["gate_delay_210m"] = OrderedDict(tag="DERIVED from SIM tables (P2 v351 h210 liq/pw G73, four bases)",
                                         D_crit_min_per_base=dc["D_crit_min_per_base"] if dc else None,
                                         comparator_285m=dc["comparator_285m_rev3"] if dc else None, evidence=ev("dcrit"))
    res["withdrawn_markers"] = OrderedDict(index=J("wmark"), evidence=ev("wmark"))
    res["v32_recompute"] = OrderedDict(evidence=ev("v32fix"))
    res["findings"] = OrderedDict(
        R4_F1_A1_band="A1 line-208 band 210 m on v3.5.1 at N=1000/base (liq 210, pw 220; liq 215 fails the 1.0 pp bound by "
                      "0.03 pp: a statistical boundary, not a physical margin). G80 at 210 passes; v351t 210 (liq) / >=215 (pw); "
                      "v352 >=215 on both states (upper-censored: flown at 210/215 only). SIM",
        R4_F2_landing_mass="the 210 m set covers the 16.15 kg v3.5.1 landing estimate (42-43 % of runs at or above it); 52-53 % of "
                           "runs exceed the v3.1 16.0 kg window bound: widen the window (proposal [11]). DERIVED from SIM",
        R4_F3_ENG11="K_s 58 fails; both axes pass at 100-130, 190, 220-270 N m/rad at the ASSUMED bending mode; failures above "
                    "130 follow the bending mode (+/-10 % shift flips 6/16 corners); no K_s robust to -10 % bending; bisection "
                    "numbers superseded. DERIVED (linear), ASSUMED K_s/J/bending",
        R4_F4_RE24="an undetected jam at the SIL bound loses no landing (31/31 runs per base and servo equal their no-jam twins); "
                   "0 false aborts in 1000; detected landing-burn jams land 0.14-0.15 continued, 0.08-0.09 with abort. SIM",
        R4_F5_gate_delay_210m="the 285 m gate-delay tolerance (D_crit 3.765 s at 2.1 s) does not carry to 210 m: D_crit min "
                              "0.164 s (A1_none) / -0.154 s (pc bases), p01 0.58-0.67 s; 16/1000 runs commit with zero slack; "
                              "P cost of gate delay at 210 m not flown. DERIVED from SIM tables",
        R4_F6_duty_cycle="line 213 'A1 duty cycle shortens' not supported on v3.5.1: A1 p99 engine-on 8.37-8.51 s (A1_none) vs "
                         "8.37 s at 285 m on v3d and the 8.258 s A1 sizing counter. DERIVED from SIM tables",
        R4_F7_payload="with the 2.0 kg tank the relight timeline sets a floor near 180 m (payload-0 fails the bound at 170 m, "
                      "loses at 155 m); +0.5 kg band 190 m (20 m, 40 m/kg); +1 kg no band; +2/+3 kg no band. To 210 m: +1 kg "
                      "with 2.20 kg N2O (3.48 L, inner 0.58-1.069 m) PASS; +2 kg not met with 2.45 or 2.55 kg (touchdown "
                      "tilt / lateral losses, no exhaustion; the 2.45 kg tank reaches the A05 station). N=500/base decision "
                      "arms. SIM/DERIVED/ASSUMED",
        R4_F8_R2v2="0.5 s window starve threshold 0.30 s (does not cover the 0.4 s top of the starve range), 0.8 s window 0.60 s; "
                   "mode-3 filter not flushed at the Pc-invalid onset; the 20.85 N bound holds no FC frame noise. SIM/DERIVED",
        R4_F9_bitcheck_v213="v1.0 functional FAILs B2/B5 were wrong test expectations (kinematics error linear in angle; 50-tick "
                            "persistence), v1.1 ALL PASS; v1.0 FAIL output kept as evidence")
    res["to_verify_next_closure"] = [
        "210 m coverage set (e19, L400, wind sweep) not flown - GNC",
        "gate-delay injection arm at 210 m (P cost of a late commit) - GNC",
        "210 m A1 duty-cycle record re-flown with the recorder - GNC",
        "vehicle first bending mode (full / landing) measured or from airframe FE - airframe owner / Mechanical",
        "K_s, J and reflected-inertia convention measured at B-TVC-1 - founders / Electronics",
        "S17 sweep against GNC R2 v2 (onsets 1-50 ms, frame phase, noise) and the mode-3 filter flush - Electronics then GNC",
        "lit-side R2 statistics on Combustion v2.4b (F_cold + grain_q1d start history) - Combustion then GNC",
        "payload own inertia, station and the longer-tank layout - payload owner / Mechanical",
        "v351t / v352 bands above 215 m (upper-censored) - GNC if the lead wants them",
        "bleed valve mass (2 x 0.30 kg ASSUMED) - Mechanical / supplier datasheet"]
    res["not_run"] = ["coverage at 210 m", "gate-delay injection at 210 m", "210 m duty-cycle record", "ENG-11 second-notch study",
                      "payload own-inertia arms", "R2 v2 with a flushed mode-3 filter"]
    res["superseded_or_withdrawn_in_rev4"] = [
        "ENG-11 v1.0 'ends' run (m2_eng11 v1.0, superseded_rev4/): SUPERSEDED by v1.1 (phase margin as min |PM|, modulus margin)",
        "m2_eng11 v1.1 ksmin / mink bisection numbers: SUPERSEDED by m2_eng11_grid v1.0",
        "v352L arm (DERIVED -0.31 kg lever): WITHDRAWN by line 209 (realised -91.6 g), not flown",
        "m2_bitcheck_v213 v1.0 functional criteria B2/B5: SUPERSEDED by v1.1 (v1.0 FAIL output kept)",
        "m2_re24 v1.0: SUPERSEDED by v1.1 (run gate only; flight code unchanged)",
        "m2_rev4_payload v1.0: SUPERSEDED by v1.1 (relight-timeline diagnostics; same flights)",
        "out/rev4/p2/p2_v351.json (pre-v1.2 evaluation): deleted, replaced by p2_rev4.json"]
    res["installed"] = "nothing new installed"
    os.makedirs(f"{O}/v32", exist_ok=True)
    p = f"{O}/rev4_results.json"
    json.dump(res, open(p, "w"), indent=1, default=float)
    print("wrote", p, sha16(p))


if __name__ == "__main__":
    main()

"""m2_rev4_v32new v1.0 (GNC rev4, 2026-10-19): NEW gnc.json v3.2 proposal items [11]-[16] from the rev4 evidence (not
reviewed; REV-GNC-5 delta re-check). Numbers are read from the evidence files. Output out/rev4/v32/v32_new_items_rev4.json,
merged into v32_proposals_rev4.json by m2_rev4_v32prop. Also writes out/rev4/eng11/lin_v351/eng11_final.json (the ENG-11
requirement with its margins and the modal-separation reading of the K_s grid, DERIVED)."""
import hashlib
import json
import os
from collections import OrderedDict

VERSION = "m2_rev4_v32new v1.0"
SP = "/home/claude/work/space"
O = f"{SP}/out/rev4"


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16] if os.path.exists(p) else None


def E(*ps):
    return [dict(path=p, sha256_16=sha16(p)) for p in ps if os.path.exists(p)]


def sep(rng, fb):
    """relative distance of the bending frequency fb from the closed interval rng (0 if inside)."""
    lo, hi = rng
    if lo <= fb <= hi:
        return 0.0
    return min(abs(fb - lo), abs(fb - hi)) / fb


def eng11_final():
    g = json.load(open(f"{O}/eng11/lin_v351/eng11_grid.json"))
    pose = json.load(open(f"{O}/eng11/lin_v351/eng11_pose.json"))["result"]["fixed_c1_Q1_-12"]
    sens = json.load(open(f"{O}/eng11/lin_v351/eng11_sens.json"))["result"]
    fb = g["bending_Hz_by_condition"]
    fb_full = min(v for k, v in fb.items() if k.startswith("full"))
    fb_land = min(v for k, v in fb.items() if k.startswith("landing"))
    rows = []
    for x in g["grid"]:
        s_full = sep(x["f_full_pose_range_Hz"], fb_full) if x["f_full_pose_range_Hz"] else None
        rows.append(OrderedDict(axis=x["axis"], K_s=x["K_s"], pass_6dB=x["pass_6dB"], gm_up_min_dB=round(x["gm_up_min_dB"], 2),
                                pm_abs_min_deg=round(x["pm_abs_min_deg"], 1), sm_min=round(x["sm_min"], 3),
                                f_full_pose_Hz=[round(v, 2) for v in x["f_full_pose_range_Hz"]],
                                f_landing_pose_Hz=[round(v, 2) for v in x["f_landing_pose_range_Hz"]],
                                sep_full_rock_vs_bending=None if s_full is None else round(s_full, 4),
                                rigid_pm_abs_min_deg=(None if not x.get("rigid_with_lowest_notch") else
                                                      round(x["rigid_with_lowest_notch"]["pm_abs_min_deg"], 1)),
                                worst=x["worst"]))
    both = sorted(set(r["K_s"] for r in rows if r["axis"] == "alpha" and r["pass_6dB"]) &
                  set(r["K_s"] for r in rows if r["axis"] == "beta" and r["pass_6dB"]))
    # contiguous passing windows on the common set (grid step 10)
    wins, cur = [], []
    for k in both:
        if cur and k - cur[-1] > 10.0 + 1e-9:
            wins.append(cur); cur = []
        cur.append(k)
    if cur:
        wins.append(cur)
    # separation reading: smallest separation among passing rows whose failure would be bending-driven, largest among failing rows
    fail_full = [r for r in rows if not r["pass_6dB"] and "|full|" in r["worst"] and "finless" in r["worst"]]
    pass_rows = [r for r in rows if r["pass_6dB"]]
    sep_fail_max = max((r["sep_full_rock_vs_bending"] for r in fail_full), default=None)
    sep_pass_min = min((r["sep_full_rock_vs_bending"] for r in pass_rows), default=None)
    shift = [OrderedDict(axis=x["axis"], K_s=x["K_s"], wb_scale=x["wb_scale"], pass_6dB=x["pass_6dB"],
                         gm_up_min_dB=round(x["gm_up_min_dB"], 2), worst=x["worst"]) for x in g["shift"]]
    nom = {f"{r['axis']}|{r['K_s']:g}": r["pass_6dB"] for r in rows}
    for k in ("87", "116", "145", "174"):
        for a in ("alpha", "beta"):
            key = f"{a}|Ks{k}"
            if key in pose:
                nom[f"{a}|{k}"] = pose[key]["floor20"]["pass_6dB"]
    moved = [OrderedDict(axis=s["axis"], K_s=s["K_s"], wb_scale=s["wb_scale"], nominal_pass=nom.get(f"{s['axis']}|{s['K_s']:g}"),
                         shifted_pass=s["pass_6dB"]) for s in shift]
    n_flip = sum(1 for m in moved if m["nominal_pass"] is not None and m["nominal_pass"] != m["shifted_pass"])
    sens_116 = {k: {kk: (vv["floor20"]["pass_6dB"], round(vv["floor20"]["gm_up_min_dB"], 2)) for kk, vv in v.items() if "Ks116" in kk}
                for k, v in sens.items()}
    out = OrderedDict(
        version=VERSION, tag="DERIVED (linear CSI on the V5c FE stiffness; K_s, J, mount damping and the first bending mode ASSUMED)",
        bending_Hz=dict(full=round(fb_full, 2), landing=round(fb_land, 2), source="m2_csi uniform PETG tube, E 2.0 GPa ASSUMED"),
        common_passing_K_s=both, common_windows=[[w[0], w[-1]] for w in wins], grid=rows, shift_test=moved,
        shift_flips=n_flip, sep_full_failing_max=sep_fail_max, sep_passing_min=sep_pass_min, sens_at_Ks116=sens_116,
        hypothesis_H_B=("failures between passing K_s come from the full-tank engine rocking mode coinciding with the ASSUMED "
                        "first bending mode; SUPPORTED if shifting the bending frequency by +/-10 % moves the failing K_s "
                        f"(observed: {n_flip} of {len(moved)} shifted corners change pass/fail)"),
        evidence=E(f"{O}/eng11/lin_v351/eng11_grid.json", f"{O}/eng11/lin_v351/eng11_pose.json", f"{O}/eng11/lin_v351/eng11_sens.json"))
    p = f"{O}/eng11/lin_v351/eng11_final.json"
    json.dump(out, open(p, "w"), indent=1, default=float)
    return out, p


def main():
    fin, pfin = eng11_final()
    res = json.load(open(f"{O}/rev4_results.json"))
    lm = res["landing_mass_coverage"]["per_base_state"]
    pay = res["payload"]["mc"]
    det = res["payload"]["deterministic"]
    re24 = json.load(open(f"{O}/re24/v351_h210/re24.json"))
    items = []
    # [11] landing mass window
    mins = min(v["m_land_min"] for v in lm.values()); maxs = max(v["max"] for v in lm.values())
    p01 = min(v["p01"] for v in lm.values()); p99 = max(v["p99"] for v in lm.values())
    items.append(OrderedDict(
        index=11, path="/landing_mass_window_kg (and the planning landing mass)", REV_GNC_5_verdict="NEW (not reviewed)",
        proposal_rev4=(f"Widen landing_mass_window_kg to the flown A1 set at 210 m on v3.5.1: dispersed touchdown mass "
                       f"{mins:.2f}-{maxs:.2f} kg (p01 {p01:.2f}, p99 {p99:.2f} kg) over the main bases and line states (N=1000 "
                       "per base). The v3.1 upper bound 16.0 kg is exceeded by 52-53 % of the flown runs; the lead's v3.5.1 "
                       "landing estimate 16.15 kg lies inside the flown set (42-43 % of runs at or above it, P(80 g) "
                       "0.974-0.986 there against 0.986-0.991 below; unpaired, not a test). Nominal deterministic touchdown "
                       "mass 16.11 kg (A1_none liq, tank at 0.58 m)."),
        status="NEW, for REV-GNC-5 delta re-check", tags="DERIVED from SIM tables",
        evidence=E(f"{O}/p2/landing_mass_coverage_h210.json", f"{O}/p2/p2_rev4.json")))
    # [12] ENG-11 requirement
    ww = fin["common_windows"]
    g_alpha = {r["K_s"]: r for r in fin["grid"] if r["axis"] == "alpha"}
    g_beta = {r["K_s"]: r for r in fin["grid"] if r["axis"] == "beta"}
    w0 = ww[0] if ww else None
    marg = ""
    if w0:
        ks = [k for k in fin["common_passing_K_s"] if w0[0] <= k <= w0[1]]
        gm_a = min(g_alpha[k]["gm_up_min_dB"] for k in ks); gm_b = min(g_beta[k]["gm_up_min_dB"] for k in ks)
        pm_a = min(g_alpha[k]["pm_abs_min_deg"] for k in ks); pm_b = min(g_beta[k]["pm_abs_min_deg"] for k in ks)
        sm_ = min(min(g_alpha[k]["sm_min"], g_beta[k]["sm_min"]) for k in ks)
        rpm = min(min(g_alpha[k]["rigid_pm_abs_min_deg"] or 99, g_beta[k]["rigid_pm_abs_min_deg"] or 99) for k in ks)
        marg = (f"Inside {w0[0]:g}-{w0[1]:g} N m/rad the worst floor20 corner gives upper GM {gm_a:.2f} dB (alpha) / {gm_b:.2f} dB "
                f"(beta), smallest |PM| over all gain crossings {pm_a:.1f} / {pm_b:.1f} deg, modulus margin >= {sm_:.3f}, rigid-loop "
                f"|PM| with the lowest notch >= {rpm:.1f} deg. ")
    items.append(OrderedDict(
        index=12, path="/tvc/ENG-11 structure-servo stiffness requirement (to mechanical.json / electronics.json owners via the lead)",
        REV_GNC_5_verdict="NEW (not reviewed)",
        proposal_rev4=(
            "ENG-11 final (DERIVED, linear, V5c structure as is, nominal J 1.6e-3 kg m2, V5c kinematics, fixed ECU notch Q 1 / "
            "-12 dB on the B-TVC-1 centre-pose mode +/-5 %, ENG-07d GM >= 6 dB on every floor20 corner): K_s 58 N m/rad "
            "FAILS (GM 3.09 dB alpha / 0.34 dB beta). On a 10 N m/rad grid 70-270 both axes pass together at "
            f"{', '.join(f'{a:g}-{b:g}' for a, b in ww)} N m/rad and fail at 140-180 and 200-210. {marg}"
            "Below 100 the failures are the landing-floor / max-q corners (beta needs >= 100, alpha >= 80) and do not move "
            "with the bending mode. The failures above 130 sit where an engine rocking mode at full tank meets the ASSUMED "
            f"first bending mode ({fin['bending_Hz']['full']} Hz full / {fin['bending_Hz']['landing']} Hz landing, PETG tube "
            f"E 2.0 GPa ASSUMED): scaling the bending frequency by 0.9 / 1.1 flips {fin['shift_flips']} of "
            f"{len(fin['shift_test'])} tested corners; at 0.9 x bending beta fails at K_s 116 / 145 / 174 (GM 0.28 / 1.70 / "
            "1.29 dB) and alpha at 116 (2.15 dB), while alpha 145 passes at both shifts. The grid gives no simple separation "
            "rule (beta passes at 220-270 with its pose range spanning the bending frequency). No K_s in 58-174 N m/rad is "
            "robust to a -10 % bending error with one fixed notch. The 100-130 window also fails at the J 2.7e-3 corner (K_s "
            "116 beta 5.9 dB) and with the n48 kinematics convention (beta 2.8 dB). Margins above 6 dB are 0.03-0.3 dB. "
            "FINAL REQUIREMENT PROPOSED: (1) servo output stiffness K_s >= 100 N m/rad, measured at B-TVC-1 together with J "
            "and the reflected-inertia convention (replaces the interim 'K_s >= 116'); (2) the vehicle first bending mode "
            "(full and landing) is MEASURED or computed from the airframe (TO-VERIFY: airframe owner / Mechanical; the PETG "
            "tube value is a placeholder), and the TVC margins are re-run on it before K_s is frozen. At the ASSUMED bending "
            "mode, K_s 100-130 N m/rad is the window to design to. The ksmin / mink bisection numbers of m2_eng11 v1.1 "
            "(alpha 157.0, beta 95.4 N m/rad) are SUPERSEDED: they assume monotone pass/fail. The 6-DOF Monte Carlo (SIM, "
            "N=500/base) loses no landing for any arm, K_s 58 included; it does not carry the linear flex corner set, so the "
            "requirement rests on the linear margins. Gimbal pocketing (206 (5)) may proceed only with an S-3D re-run giving "
            "V5c-class structure stiffness at every pose. RESEARCH PROPOSAL: a second ECU notch on the measured bending mode; "
            "hypothesis: it removes the coincidence failures; comparator: the single notch; evidence: this grid and the "
            "0.9 / 1.1 shift re-run with the second notch; refutation: any floor20 corner below 6 dB for K_s 100-270 at "
            "0.9-1.1 x bending."),
        status="NEW, for REV-GNC-5 delta re-check", tags="DERIVED (linear) / SIM (6-DOF) / ASSUMED (K_s, J, bending, damping)",
        evidence=E(pfin, f"{O}/eng11/lin_v351/eng11_grid.json", f"{O}/eng11/lin_v351/eng11_pose.json",
                   f"{O}/eng11/lin_v351/eng11_sens.json", f"{O}/eng11/lin_v351/eng11_ends.json",
                   f"{O}/eng11/lin_v351/eng11_ksmin.json", f"{O}/eng11/lin_v351/eng11_mink.json",
                   f"{O}/eng11/fly_v351_h210/eng11_fly.json")))
    # [13] RE-24
    a = re24["arms"]
    items.append(OrderedDict(
        index=13, path="/flight_software/gimbal_fault_monitor (RE-24)", REV_GNC_5_verdict="NEW (not reviewed)",
        proposal_rev4=(
            "RE-24 answer (SIM, sim6 v2.13-dev amendment J, bit-check v1.1 ALL PASS, liq|G73|v351|h210, N=500 per base, jam "
            "bound ASSUMED from Electronics S6/SIL v2.10: 1.5 deg + 40 ms x model rate, 50 ms): an UNDETECTED gimbal jam at the "
            "bound does not lose a landing: 31 undetected landing-burn jam runs per base per servo, every one lands exactly as "
            f"its no-jam twin (A1_none servo A 30/31 vs ref 30, servo B 29/31 vs 29; A1J_pc 31/31 vs 31, 30/31 vs 30; p = 1). "
            "Nominal flights: 0 false GIMBAL_FAULT aborts in 1000 (mon2), largest no-jam excursion of the monitor metric "
            f"{a['A1_none']['rec0']['x50_deg']['max']:.2f} deg against 1.5 deg. Detected jams are another matter: a landing-"
            f"burn jam lands in {a['A1_none']['lbA1']['vs_rec0']['P_case']:.3f}-{a['A1J_pc']['lbA1']['vs_rec0']['P_case']:.3f} "
            f"of runs if flown on and {a['A1_none']['lbA2']['vs_rec0']['P_case']:.3f}-{a['A1J_pc']['lbB2']['vs_rec0']['P_case']:.3f} "
            "with the monitor's abort (detected A1_none servo A: continue 42/469, abort 13/469); a coast or ascent jam is lost "
            "either way (P 0.000-0.002). Landed fraction by time-to-go at the jam: [0, 1) s 59/84, [1, 2) s 12/210, >= 2 s about 0. "
            "So the abort costs landings in the last ~1 s; whether to inhibit the GIMBAL_FAULT abort near touchdown is a "
            "safety decision for the lead (a jammed engine at up to ~20 deg may leave the range safety envelope) and is not "
            "proposed here. Not modelled: stall current sag on the shared supply, encoder faults, a roll recovery mode."),
        status="NEW, for REV-GNC-5 delta re-check", tags="SIM / ASSUMED (SIL bound)",
        evidence=E(f"{O}/re24/v351_h210/re24.json", f"{O}/bitcheck_v213/bitcheck_v213_func.json",
                   f"{O}/bitcheck_v213/bitcheck_v213_offparts.json", f"{O}/bitcheck_v213/bitcheck_v213_func_v1.0_FAILS.json")))
    # [14] R2 v2 answers
    items.append(OrderedDict(
        index=14, path="/rev2/amendment_V_pc_invalid (R2 v2): answers to the lead (2026-10-13 ~19:05Z) and REV-ELEC-2 R2-01 / line 216 (1)",
        REV_GNC_5_verdict="NEW (not reviewed)",
        proposal_rev4=(
            "(a) Counting start and flush, as implemented in sim6 V2 (gnc_dev6/7): E2 = the 6-DOF light (rel_dt 0); Pc is "
            "invalid from E2 + pcf_dt (pcf_dt 0 in the decided set). Counting starts on the first 1 ms step at which both hold "
            "and the 100 Hz frames are then taken every 10 ms from that step (frame phase tied to the counting start, not to a "
            "free-running FC clock: TO-VERIFY against the flight FC). Mode 3 (the R2 v2 candidate): the axial specific force is "
            "filtered continuously (first order, fct_tau 20 ms) from the drogue phase and is NOT flushed at E2 or at the Pc-"
            "invalid onset; the reference and the descent rate are sampled at E2 and the drag term is compensated by "
            "(vz/vz(E2))^2. Release needs 3 consecutive frames >= 37.16 N (3-frame running minimum) and the engine lit; not "
            "confirmed by E2 + pcf_tmax -> abort (hold). Consequence: lit thrust before a later flame-out stays in the filter "
            "for about 3 tau = 60 ms, so a vehicle that lights and dies 10-20 ms after E2 can meet the 3-frame rule on carried-"
            "over thrust; GNC's flown flame-out population is the never-lit cold-flow design bound with onsets 0 / 5 / 10 ms "
            "and does not contain this case. The sim also gates release on the engine-lit truth (ECU RUN), which a real ECU "
            "without valid Pc cannot know; GNC's 'released dead vehicle' counts are therefore computed from the window "
            "statistics, not from flown releases. Proposal: re-initialise the mode-3 filter at the Pc-invalid onset (or start "
            "counting at onset + 3 tau) and re-run the R2 v2 statistics after Electronics' S17 sweep (onsets 1-50 ms x frame "
            "phases x noise). (b) The 20.85 N W10 < 6 bound is the largest sim R2 estimate over the W10 < 6 flame-out runs "
            "(rev2, 0.5 s). It contains the modelled ADIS16470 white noise (100 ug/rtHz ASSUMED, about 0.06 N rms on the "
            "estimate after the 20 ms filter at ~16 kg, DERIVED) and the bias / scale / mass-estimate dispersions. It does NOT "
            "contain an FC frame noise of 5 N rms (about 90 x the modelled level), drogue canopy breathing (quasi-steady "
            "massless drogue), FC timing jitter, or structural vibration of an unlit vehicle (the sim's vibration term scales "
            "with thrust). Back-of-envelope (DERIVED, independent frames ASSUMED): 5 N rms frame noise raises the window "
            "maximum of the 3-frame minimum by about +4 N (median) to +8 N (p99) over 50 frames, which is the whole +5.3 to "
            "+6.0 N W10 < 6 margin, so a frame-noise budget is needed before the 'no released dead vehicle' claim is used. "
            "(c) Starve threshold (rev4, item [6]): 0.30 s at the 0.5 s window (all lit runs released; 5/60 aborted at 0.40 s), "
            "0.60 s at the 0.8 s window (W10 < 6: 0.65 s). GNC's R2 v2 releases 0.08-0.12 s after the plateau ends, about 0.1 s "
            "later than Electronics' stand-in (0.46-0.48 s at 0.5 s), so the 0.5 s window has no margin over the top of the "
            "0.1-0.4 s starve range and the 0.8 s window has >= 0.20 s. The ECU backstop (line 216 (2)(b): the hold ends by "
            "E2 + 0.8 s + margin) is compatible: GNC's latest release at the 0.8 s window is E2 + 0.80 s (st_T 0.6-0.7 s), so "
            "the R2 v2 decision precedes the backstop by the stated margin (>= 2 FC frames + link latency, Electronics)."),
        status="NEW, for REV-GNC-5 delta re-check", tags="SIM (code reading + flights) / DERIVED / ASSUMED",
        evidence=E(f"{O}/r2_starve/r2_starve.json", f"{SP}/gnc_dev7/gncsim/sim6.py")))
    # [15] payload record
    def arm(nm):
        return pay.get(nm)

    def line(nm, label):
        e = arm(nm)
        if not e:
            return f"{label}: not flown"
        b = e.get("N500") or e.get("N250")
        v = b["pooled_vs_v3d_ref"]
        return (f"{label}: P(80 g) {b['P80_per_base']['A1_none']:.3f} / {b['P80_per_base']['A1J_pc']:.3f}, pooled -{v['lost']}/"
                f"+{v['gained']} p {v['p_exact']:.3g} UB95 {v['ub95_pp']:.2f} pp -> {'PASS' if b['line208_pass'] else 'FAIL'} "
                f"(N={b['N_per_base']}/base)")
    iso = det["iso"]
    load = det["load"]
    txt = ("Payload sensitivity (record for the lead / founder; SIM flights, DERIVED iso-margin and T/W, ASSUMED point payload "
           "at the A05 station z 1.15 m and tank layout; v3.5.1 vehicle, 2.00 kg N2O tank moved to 0.58 m, CG +7.5 mm; "
           "criterion = sim6 landing success AND >= 80 g liquid at touchdown, judged by the line-208 rule against the v3d "
           "reference). (a) Apogee for the same propellant margin as the 0 kg 210 m vehicle (deterministic): "
           + "; ".join(f"+{k} kg {iso[k]['h_iso_min_m']:.0f} m ({iso[k]['apogee_loss_per_kg_m']:.0f} m/kg)" for k in ("0.5", "1", "2", "3"))
           + ". Liftoff CG shift from the payload (above the 0 kg vehicle, which carries +7.5 mm from the tank move): +0.5 kg "
             "+14.1 mm, +1 kg +27.4 mm, +2 kg +52.0 mm, +3 kg +74.2 mm (DERIVED). The Monte Carlo shows a second floor the "
             "margin does not see: below about 180 m the relight timeline (drogue settle 1.0 s + 0.5 s quasi-steady + 2.90 s "
             "commit-to-fire) starts the landing burn too low (h_ign p50 about 30-35 m at 155 m, 0.4 m at 115 m), so the "
             "payload-0 vehicle itself fails the bound at 170 m and loses at 155 m. Bands by the line-208 rule with the sweep "
             "floor at 180 m: 0 kg 210 m; +0.5 kg 190 m (180 and 190 m pass, 200 m fails the bound, 210 m loses), i.e. 20 m "
             "for 0.5 kg (40 m/kg; the equal-margin estimate 181 m is conservative); +1 kg NO band (180 m fails the bound, "
             "190-210 m lose: the propellant ceiling falls below the timeline floor); +2 and +3 kg NO band (P 0 at their "
             "equal-margin apogees 115 / 90 m). Flown: "
           + "; ".join(line(nm, lab) for nm, lab in (
               ("liq|G73|v351|pl0|tz58|h210", "0 kg 210 m"), ("liq|G73|v351|pl0|tz58|h180", "0 kg 180 m"),
               ("liq|G73|v351|pl0|tz58|h170", "0 kg 170 m"), ("liq|G73|v351|pl0.5|tz58|h210", "+0.5 kg 210 m"),
               ("liq|G73|v351|pl0.5|tz58|h200", "+0.5 kg 200 m"), ("liq|G73|v351|pl0.5|tz58|h190", "+0.5 kg 190 m"),
               ("liq|G73|v351|pl0.5|tz58|h180", "+0.5 kg 180 m"), ("liq|G73|v351|pl1|tz58|h210", "+1 kg 210 m"),
               ("liq|G73|v351|pl1|tz58|h200", "+1 kg 200 m"), ("liq|G73|v351|pl1|tz58|h190", "+1 kg 190 m"),
               ("liq|G73|v351|pl1|tz58|h180", "+1 kg 180 m"), ("liq|G73|v351|pl2|tz58|h210", "+2 kg 210 m"),
               ("liq|G73|v351|pl2|tz58|h115", "+2 kg 115 m"), ("liq|G73|v351|pl3|tz58|h90", "+3 kg 90 m")))
           + ". (b) Load to carry the payload to 210 m: "
           + "; ".join(f"+{k} kg: {load[k]['m_n2o_sized_kg']:.2f} kg N2O, {load[k]['tank_V_L']:.2f} L at 85 % fill, inner span "
                       f"{load[k]['tank_inner_span_m'][0]:.2f}-{load[k]['tank_inner_span_m'][1]:.3f} m (tube "
                       f"{load[k]['tank_tube_length_m']:.3f} m){', CLASHES with the A05 station at 1.15 m' if load[k]['clash_with_A05_station'] else ''}"
                       for k in ("1", "2"))
           + "; flown: " + "; ".join(line(nm, lab) for nm, lab in (
               ("liq|G73|v351|pl1|tz58|h210|m2.20", "+1 kg 2.20 kg"), ("liq|G73|v351|pl2|tz58|h210|m2.45", "+2 kg 2.45 kg"),
               ("liq|G73|v351|pl2|tz58|h210|m2.55", "+2 kg 2.55 kg")))
           + ". So +1 kg reaches 210 m with 2.20 kg N2O (line-208 PASS at N=500/base); +2 kg does NOT meet the criterion "
             "with 2.45 or 2.55 kg: the residual losses at 2.55 kg are touchdown tilt / lateral speed with no exhaustion "
             "(landing mass 18.6 kg, liftoff CG about +65 mm, floor ratio about 0.55), so more N2O does not fix it; +2 kg needs a landing-"
             "control and structure study, not only a bigger tank. (c) Liftoff T/W, touchdown T/W and landing floor ratio "
             "(DERIVED, rated 500 N, nominal flights): 0 kg 2.92 / 3.16 / 0.633; with the 2.0 kg tank +0.5 kg 2.84 / 3.08 / "
             "0.616, +1 kg 2.76 / 3.00 / 0.600, +2 kg 2.62 / 2.85 / 0.570, +3 kg 2.49 / 2.72 / 0.543; sized loads +1 kg at "
             "2.20 kg 2.72 / 2.95 / 0.590, +2 kg at 2.45 kg 2.53 / 2.75 / 0.550. Monte Carlo N: 250 per base for the screen "
             "(all arms), 500 per base for the decision arms (same seed, first 250 runs identical). Separate table; SIM, not "
             "physical approval; the tank length, the payload station, its inertia and the structure for a longer tank are "
             "Mechanical's and the payload owner's (TO-VERIFY).")
    items.append(OrderedDict(index=15, path="/payload_sensitivity (record, informational)", REV_GNC_5_verdict="NEW (not reviewed)",
                             proposal_rev4=txt, status="NEW record, for REV-GNC-5 delta re-check",
                             tags="SIM / DERIVED / ASSUMED", evidence=E(f"{O}/payload/payload_rev4.json", f"{O}/payload_n500/payload_rev4.json",
                                                                         f"{O}/payload/payload_check.json")))
    p = f"{O}/v32/v32_new_items_rev4.json"
    json.dump(OrderedDict(version=VERSION, date="2026-10-19", items=items), open(p, "w"), indent=1, default=float)
    print("wrote", p, sha16(p), "and", pfin, sha16(pfin))
    print("ENG-11 common windows", fin["common_windows"], "flips", fin["shift_flips"], "/", len(fin["shift_test"]),
          "sep fail max", fin["sep_full_failing_max"], "sep pass min", fin["sep_passing_min"])


if __name__ == "__main__":
    main()

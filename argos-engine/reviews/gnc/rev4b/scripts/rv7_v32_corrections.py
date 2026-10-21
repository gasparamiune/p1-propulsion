"""REV-GNC-7 exact corrections for gnc.json v3.2 (candidate 43d58c4aff164b86) and for DATASHEET-INPUTS-GNC.md (9aacdefaaa0df250),
as a machine-readable list, and a TRIAL application to the candidate (v2, 2026-10-21).
Usage: python -I rv7_v32_corrections.py <candidate.json> <corrections_out.json> <trial_out.json> [<run_dir_d_r3> [<run_dir_ks58_174>]]
The window texts are computed from the reviewer's ENG-07d run JSONs (m2_eng11_fe format; default /dev/shm/rev_gnc7/out/d_r3), so the
numbers in the texts are the run numbers; a variant that is not complete is written as 'NOT RUN' / 'partial' and listed in
'incomplete_variants'.  The K band values are read from k_table_r3_v352.json (sha-checked).
The TRIAL file is a reviewer check copy only: it is NOT gnc.json and NOT for publication; the lead applies the corrections and
publishes.  Each gnc.json operation is one of:
  replace  : in the leaf at 'path', the text 'old' (must occur exactly once) becomes 'new'
  set      : the leaf at 'path' is set to 'new' (a new key, or a full replacement of the leaf)
  rename   : the key at 'path' is renamed to 'new_key' (value kept: superseded text kept as history)
  append   : 'new' is appended to the list at 'path'
The datasheet operations ('datasheet_ops') are exact replace pairs on the .md text (applied here only to check that each 'old'
occurs once).  Evidence tags inside the texts; nothing here is physical approval."""
import copy
import hashlib
import json
import os
import sys

H = "/home/claude/work/shared-fallback/engine"
KT = f"{H}/04-fea/assembly3d_v352/results/v352/k_table_r3_v352.json"
KT_SHA16 = "f3c7cfbcfb98bcd7"
DS = f"{H}/01-systems-gnc/staging_v3.1/rev4b/DATASHEET-INPUTS-GNC.md"
DS_SHA16 = "9aacdefaaa0df250"
R3 = "04-fea/assembly3d_v352/results/v352/k_table_r3_v352.json (f3c7cfbcfb98bcd7)"
RV7 = "REV-GNC-7 (reviews/REVIEW-GNC-R5.md; reviews/gnc/rev4b/, MANIFEST_REV-GNC-7.sha256)"
RUN_D = "/dev/shm/rev_gnc7/out/d_r3"
RUN_K = "/dev/shm/rev_gnc7/out/d_r3_ks58_174"
INCOMPLETE = []


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def _windows(ks):
    ks = sorted(ks); out = []; s = None
    for i, k in enumerate(ks):
        if s is None: s = k
        if i == len(ks) - 1 or ks[i + 1] - k > 5.01: out.append((s, k)); s = None
    return out


def _fmt(w, lo=90, hi=160):
    if not w: return "none"
    return ", ".join((("<= " if a <= lo else "") + f"{a:g}" + ("-" + (">= " if b >= hi else "") + f"{b:g}" if b != a else ("->= " if b >= hi else ""))) for a, b in w)


def runwin(v, d=None, n_rows=30):
    """Both-axes / alpha / beta window texts of a reviewer variant; 'NOT RUN' / partial flagged."""
    p = os.path.join(d or RUN_D, f"eng11fe_{v}.json")
    if not os.path.exists(p):
        INCOMPLETE.append(v)
        return dict(both="NOT RUN", alpha="NOT RUN", beta="NOT RUN", complete=False, gm={}, rows={})
    j = json.load(open(p)); rows = j["rows"]
    pa = {a: [float(k.split("Ks")[1]) for k, r in rows.items() if k.startswith(a + "|") and r.get("pass_6dB")] for a in ("alpha", "beta")}
    both = sorted(set(pa["alpha"]) & set(pa["beta"]))
    complete = bool(j.get("done")) and len(rows) >= n_rows
    tag = "" if complete else f" (partial, {len(rows)} of {n_rows} rows)"
    if not complete: INCOMPLETE.append(v)
    gm = {k: min(rows[f"alpha|Ks{k:g}"]["gm_up_min_dB"], rows[f"beta|Ks{k:g}"]["gm_up_min_dB"]) for k in both}
    if not complete and d is not None: INCOMPLETE[-1] = f"{v} ({os.path.basename(d)})"
    return dict(both=_fmt(_windows(both)) + tag, alpha=_fmt(_windows(pa["alpha"])) + tag, beta=_fmt(_windows(pa["beta"])) + tag,
                complete=complete, gm=gm, rows=rows, both_ks=both)


def band():
    if sha16(KT) != KT_SHA16:
        raise RuntimeError("k_table_r3_v352.json sha mismatch")
    t = json.load(open(KT)); rng = t["range_over_posted_R3_poses"]
    v = {}
    for q in ("FE_coupled", "FE_diagonal", "k_s58_coupled", "k_s58_diagonal", "k_s174_coupled", "k_s174_diagonal"):
        v[f"{q}_N_m_per_rad"] = {a: dict(min=rng[f"{q}_{a}"]["min"], min_pose=rng[f"{q}_{a}"]["min_pose"], max=rng[f"{q}_{a}"]["max"],
                                         max_pose=rng[f"{q}_{a}"]["max_pose"]) for a in ("alpha", "beta")}
    return t, v


def texts():
    T = {}
    W = {k: runwin(k) for k in ("R3P_JC", "R3Hi_JC", "R3Lo_JC", "R3P_JLO", "R3Hi_JLO", "R3Lo_JLO", "R3P_JHI", "R3Hi_JHI", "R3Lo_JHI", "R3C_JC", "R3G_JC")}
    K = runwin("R3P_JC", RUN_K, n_rows=4)
    T["W"] = W
    gm_in = [W["R3P_JC"]["gm"][k] for k in (100.0, 105.0, 110.0) if k in W["R3P_JC"]["gm"]]
    gm_txt = f"{min(gm_in):.3f}-{max(gm_in):.3f}" if gm_in else "n/a"
    # all-three-J intersections per plant (pose-wise, band maximum, band minimum)
    def inter(a, b, c):
        if not (W[a]["complete"] and W[b]["complete"] and W[c]["complete"]):
            return "NOT COMPLETE"
        s = sorted(set(W[a]["both_ks"]) & set(W[b]["both_ks"]) & set(W[c]["both_ks"]))
        return _fmt(_windows(s))
    I3 = dict(P=inter("R3P_JC", "R3P_JLO", "R3P_JHI"), Hi=inter("R3Hi_JC", "R3Hi_JLO", "R3Hi_JHI"), Lo=inter("R3Lo_JC", "R3Lo_JLO", "R3Lo_JHI"))
    T["I3"] = I3
    i3txt = (f"all three J together: pose-wise {I3['P']}, band maximum {I3['Hi']}, band minimum {I3['Lo']}")
    T["ENG11_NEW"] = (
        "design-to window 100 <= K_s <= 110 N m/rad (two-sided) for the servo output stiffness at the ASSUMED J 1.6e-3 kg m2 (servo "
        "output shaft, added to I_piv), cons kinematics and the ASSUMED first bending 24.3 Hz full / 25.64 Hz landing: the 227 (3) "
        "window (100-130, V5c plant, CAD v3.3) re-verified on the FE plant (227 (3), RV6-14), i.e. the part of it that passes on both "
        "plants (234 (5): the FE plant is not preferred over V5c until the beta cause is found). FE plant CAD v3.5.2: the R3 pose "
        f"table ({R3}; S = FE coupled R3 per pose, g = V5c on the 9 cone poses / CAD kinematics at the 8 stops, cone + stop envelope) "
        f"passes {W['R3P_JC']['both']} N m/rad on both axes (alpha {W['R3P_JC']['alpha']}, beta {W['R3P_JC']['beta']}; worst upper GM "
        f"{gm_txt} dB inside 100-110); at the ends of the R3 K band (k_band_r3_v352: S at the band value at every pose, one fixed ECU "
        f"notch referenced on the R3 centre pose) it passes {W['R3Hi_JC']['both']} at the band maximum and {W['R3Lo_JC']['both']} at "
        "the band minimum, so 100 N m/rad is the only grid value of the design-to window that passes at both band ends [DERIVED, "
        f"linear ENG-07d with m2_eng11_fe v1.0 / m2_eng11 v1.1 unchanged, {RV7}; K_s grid 90-160 step 5, edges +-5 N m/rad]; the "
        "upper edge is the coincidence of the full-tank rocking mode with the first bending (failing corners at 23.90-24.55 Hz pose-wise and at both band ends, zeta "
        f"0.02, notch e 0.95). Not robust: on the R3 plant J 2.7e-3 gives {W['R3P_JHI']['both']} (band maximum "
        f"{W['R3Hi_JHI']['both']}, band minimum {W['R3Lo_JHI']['both']}) and J 0.76e-3 gives {W['R3P_JLO']['both']} (band maximum "
        f"{W['R3Hi_JLO']['both']}, band minimum {W['R3Lo_JLO']['both']}); {i3txt}; the J 2.7e-3 lower edge is the max-q corner (full "
        "tank, 500 N, worst actuator, fins, zeta 0.10, 16.3-19.2 Hz), the J 0.76e-3 lower edge the bending coincidence (as on the CAD "
        "v3.5.1 FE plant, rigid airframe, T_REF: 130->= 160 / <= 90-120 / 120->= 160, and 125->= 160 at J 2.7e-3 with the compliant "
        "airframe + hot E -10 % (A10); on that compliant + hot set all three J pass 130-140, 160); with the first bending at 0.9 x the window is empty (CAD v3.5.1 FE plant, eng11_fe C01). Superseded plant bases "
        "(records): V5c 100-130 (CAD v3.3); CAD v3.5.1 FE <= 90-120 (eng11_fe, 24 variants), whose 'design-to 100-120' does not hold "
        "on CAD v3.5.2 (115 and 120 fail pose-wise on beta, 105-120 at the band maximum on alpha). acceptance: ENG-07d (stable, "
        "upper GM >= 6 dB at every floor20 corner, continuous pose envelope, notch as flown) re-run on the B-TVC-1 measured K_s (with "
        "its uncertainty), J, reflected-inertia convention and rocking modes at the poses and on the measured or airframe-FE first "
        "bending mode (full and landing); K_s is frozen only on a PASS; on a FAIL the notch set (second notch on the measured bending "
        "mode) is changed and the margins re-run before any K_s change")
    t, v = band()
    bst = t["beta_sign_trend"]
    def kr(r):
        return f"alpha {r['alpha']}, beta {r['beta']}"
    ks_txt = (f"at K_s 58 / 174 N m/rad (the with-servo K quantities of the table) the pose-wise loop gives: K_s 58 alpha "
              f"{'PASS' if K['rows'].get('alpha|Ks58', {}).get('pass_6dB') else 'fail'}, beta "
              f"{'PASS' if K['rows'].get('beta|Ks58', {}).get('pass_6dB') else 'fail'} (worst-actuator corners at zeta 0.10: alpha max-q with fins, 17.492 Hz, GM 5.840 dB; beta no-aero, 15.202 Hz, GM 5.935 dB); K_s 174 alpha "
              f"{'PASS' if K['rows'].get('alpha|Ks174', {}).get('pass_6dB') else 'fail'}, beta "
              f"{'PASS' if K['rows'].get('beta|Ks174', {}).get('pass_6dB') else 'fail'} (bending coincidence, 24.341 Hz, GM 5.964 dB)") if K["rows"] else "K_s 58 / 174: NOT RUN"
    T["K_BAND"] = {
        "v": v,
        "units": "N m/rad",
        "definition": ("K band = range_over_posted_R3_poses (lead 250 (6)): min and max over the 17 posted v3.5.2 R3 poses (8 stops at "
                       "8 deg, neutral, 8 range-cone poses at 7 deg; 17 of 17 posted, all ACCEPTED, lead 18:40:44Z) per quantity, with the "
                       "pose; FE = structure + rod chain with the servo rigid (coupled = other axis moment-free, the S of the ENG-07d "
                       "loop; diagonal = other axis held); k_s58 / k_s174 = with the servo output compliance in series at K_s 58 / 174 "
                       "N m/rad (FEA3D post_k with the RM2-05 effective horn radius per servo and pose, 234 (5)); alpha = outer axis X, "
                       "beta = inner ring axis Y"),
        "loop_check": (f"ENG-07d (stable, upper GM >= 6 dB at every floor20 corner, cone + stop envelope) with one fixed ECU notch (Q 1 "
                       f"/ -12 dB at e 0.95 / 1 / 1.05 x the R3 centre landing mode), K_s 90-160 step 5, both axes: J 1.6e-3 pose-wise "
                       f"{W['R3P_JC']['both']}, band maximum {W['R3Hi_JC']['both']}, band minimum {W['R3Lo_JC']['both']}; J 0.76e-3 "
                       f"pose-wise {W['R3P_JLO']['both']}, band maximum {W['R3Hi_JLO']['both']}, band minimum {W['R3Lo_JLO']['both']}; "
                       f"J 2.7e-3 pose-wise {W['R3P_JHI']['both']}, band maximum {W['R3Hi_JHI']['both']}, band minimum "
                       f"{W['R3Lo_JHI']['both']}; {i3txt}; {ks_txt} [DERIVED, linear, {RV7}]"),
        "information": ("beta sign trend (the table's beta_sign_trend, fraction of the stop045 delta per pose): beta > 0 "
                        f"{bst['beta > 0']['fraction_min']}-{bst['beta > 0']['fraction_max']}, beta = 0 {bst['beta = 0']['fraction_min']}-"
                        f"{bst['beta = 0']['fraction_max']}, beta < 0 {bst['beta < 0']['fraction_min']}-{bst['beta < 0']['fraction_max']}: "
                        "the fraction follows the sign of beta, and the RM2-05 band built from the stop045 delta does not bound every "
                        "pose (the table's statement; stop000, beta+, combined045 and combined315 ACCEPTED above the original band, "
                        "lead 18:40:44Z). R3 is stiffer than the RM2-05 corrected v3.5.1 values: S_R3 / S_v351 = 1.089-1.150 (alpha), "
                        "1.022-1.098 (beta) over the 17 poses. The R3-implied servo factor 1 / (58 (1 / k_s58 - 1 / S)) equals the "
                        "loop's g within 0.05 % at neutral (23.04 = n^2), at the beta stops stop000 / stop180 and at the 7 deg beta "
                        "poses; it is 0.996 of it at stop135 / 225 (cone 135 / 225: 0.997 alpha, 0.989-0.990 beta), 0.966 / 0.948-0.949 "
                        "(alpha / beta) at the 7 deg alpha poses, 0.935 at the alpha stops stop090 / 270, 0.936 / 0.923 at cone 045 / "
                        "315 and 0.840 at stop045 / 315 (the loop takes V5c g on the cone and CAD kinematics at the stops) [DERIVED]"),
        "tag": ("SIM (FE unit steps on the v3.5.2 R3 pose runs, FEA3D) + DERIVED (servo in series; K_s 58 / 174 ASSUMED, TO-VERIFY "
                "B-TVC-1); loop check DERIVED (linear); not physical approval"),
        "src": R3,
    }
    T["S17"] = (
        "Electronics v2.11 S17 CONFIRMED pcf_tmax 0.8 s for the W10 < 6 m/s envelope, not returned (227 (5); interfaces/electronics.json v4 "
        "11f7896ad0d0613b drogue_release_support.r2v2_sweep.verdict_227_5; SIM S17v2_r2v2_sweep.json 404a19d7064b336f, GNC R2 v2 evaluated offline): "
        "with the ECU R2 hold and the mode-3 flush, 0 of 2000 dead evaluations are released at either window, minimum margin +5.789 N "
        "at 0.5 s and +4.954 N at 0.8 s (normal and starved040 families, photodiode main-chamber view, reference none); of the 2000 "
        "dead evaluations per window 1360 leave RUN (ECU FLAMEOUT) before any R2 decision and 640 are decided by R2. 0.8 s holds only "
        "with ALL of: (a) the ECU R2 hold with the FC DROGUE report (without it 320 of 1000 normal dead runs are released); (b) the "
        "mode-3 flush at the Pc-invalid onset (without it 264 / 326 normal and 160 / 172 starved040 of 1000 dead runs are released at "
        "0.5 / 0.8 s); (c) the photodiode main-chamber view proven (FLAMEOUT_OPT armed) or the R2 reference re-taken at the ECU E2 or at "
        "the light: photodiode-blind families release 20 / 42 (normal_noopt) and 42 / 98 (starved040_noopt) of 1000 dead runs at 0.5 / "
        "0.8 s, noise-free margin -1.788 / -2.136 N at 0.8 s (OI-PHOTODIODE-VIEW); (d) the FC Pc branch (release on a frame with Pc valid "
        "and filtered Pc >= 3.0 bar abs) off until the flame-out window has passed, or its threshold moved with a stated margin: Pc_f "
        "at E2 is 3.04 bar abs, so the branch releases every normal-family run at the E2 frame, lit or about to flame out 1-50 ms "
        "later, outside R2 (OI-FC-PC-BRANCH); (e) FC frame noise inside the budget for P(dead release) <= 1e-3: <= 2.51 N rms iid (1.65 "
        "N AR(1), rho 0.61) at 0.8 s, <= 3.06 N rms iid (2.00 N AR(1)) at 0.5 s; 5 N rms is not admissible (P 6.9 % / 22.9 %); (f) the "
        "cold-flow bound: at cold-flow apparent thrust x 1.3 (basis: the Combustion v2.4a adiabatic bound) the hold + flush margins "
        "fall to +2.077 / +1.242 N and the iid budget to 1.10 / 0.63 N rms at 0.5 / 0.8 s (REV-ELEC-3 R3-04); (g) inside W10 < 6 m/s "
        "only (all winds: 320 of 1000 normal dead runs released at 0.8 s). Lit side: a starved plateau is released at all 10 frame "
        "phases up to 0.75 s at the 0.8 s window (0.45 s at 0.5 s), 0.35 s over GNC's 0.4 s starve top. Low lit corners (230 (5), "
        "OI-FMIN-LIT; REV-COMB-4 R4-03): at the 0.21776 mm start-level lift 3 of 72 Combustion P4c corners never reach 37.16 N within "
        "0.8 s (F_min 33.14 N with torch 0; Cd0.65|a0.6|n0.68|ri0.3|eta0.85 crosses at E2 + 0.857 s, the other two stay below 37.16 N "
        "to the end of the 1.0 s record); with the flush such a lit run is not released (lit thrust capped at 33.14 N: no lit run "
        "released; without the flush 274 of 1000 are), the drogue is held and the relight is aborted at t_E2 + 0.8 s "
        "(drogue_release_hold; ECU R2 backstop E2 + 0.85 s); 37.16 N and 0.8 s are kept: a 0.887 s window rescues one of the three "
        "corners and costs dead-side margin, and a 33.14 N threshold sits below the dead-side maximum at cold flow x 1.3 (35.92 N at "
        "0.8 s) [SIM S17 / DERIVED]; the outcome is a lost relight (the outcome class of relight_conditions.unprimed_or_unknown_line) in "
        "the Pc-invalid branch only; the start-level lift is TO-VERIFY at CF-3 (230 (4)). GNC has not re-flown the R2 v2 statistics "
        "with the flush on the v2.11 implementation (open_items[47])")
    T["LOST"] = (
        "An unprimed or UNKNOWN-line relight with the bleed fitted is REFUSED for A1 (fail-safe; lead 253 (7)(iv)); OI-UNPURGED-RELIGHT "
        "stays open (253 (7)(iv)) until Combustion has a model of that case. Mission outcome (GNC): no relight on that pass; the ECU "
        "never enters RUN, so the drogue is never released (RELEASE iff RUN AND b4 AND [...]) and no dead vehicle is released; the "
        "vehicle descends on the drogue to touchdown at about -22 m/s (rev2 amendment V, SIM: drogue descent of a vehicle whose engine "
        "is out, touchdown p50 -21.8 m/s, p01 -24.3 m/s, about 0.46 x the impact energy of a released dead vehicle; rev2 runs, transfer "
        "to 210 m / v3.5.1 ASSUMED); a vehicle loss (P 0 for that flight), the outcome class of a pass below L* (lead 186 (1)), of a lit "
        "run held by R2 below 37.16 N (OI-FMIN-LIT) and of a C1-drift relight abort (R3-01). Its probability is P(unprimed or UNKNOWN "
        "line at the relight), not quantified by GNC (owner Combustion / Electronics: PRIMED flag)")
    T["PURGE"] = (
        "PURGE FINAL (lead 256 (2) and 257 (2); combustion.json v2.4c purge_decision_v2p4c): scheduled flow 2.43 s (both-open overlap "
        "2.38 s + 0.05 s) with the 2.39 s both-open cap (2.44 s of flow at the cap); needed flow 2.2 / 1.9 / 1.8 s at 283.15 / 289.5 / "
        "297.15 K unlined (lined, 283.15 K needs 2.5 s); margins at 2.43 s 0.23 / 0.53 / 0.63 s (0.18 / 0.13 s at 283.15 K with the "
        "FD-01 element bounds); vented N2O at the ASSUMED Cd 0.70 66.7 / 70.8 / 75.1 g at 2.43 s (bound law 66.4 / 70.7 / 75.4 g, "
        "75.75 g at the cap) [DERIVED by REV-COMB-4 on Combustion's SIM model]. At Cd 0.80 the fixed schedule vents about 80.5 g at "
        "289.5 K and 85.5 g (85.8 g at the cap) at 297.15 K [ESTIMATE]. A1 reserve (line-208 test against the v3d reference, A1 210 m, "
        "v351, N = 500 per base, dip onset 80 g; vented mass above the flown G73 / G80 as a per-run liquid shift, ESTIMATE above 80 g; "
        "REV-GNC-7): 76 g UB95 0.854 pp liquid / 0.617 pp powered, PASS; 80.5 g 0.972 / 0.617 pp, PASS (margin 0.028 pp); the liquid "
        "test first fails at 82.1 g (1.089 pp); 85.5-85.8 g 1.206 pp liquid, FAIL (powered 0.736 pp passes) [DERIVED from SIM]; "
        "relight_ok 1.000 in every flown base (G73 / G80). The 76 g basis stays (G73 decided, G80 sensitivity). Condition (d) (257 (2)): "
        "after CF-4 / B-BLEED-1, kPurgeFlow_s and the cap are re-set from the measured Cd x A by the measured-time form with the mass "
        "flow at 297.15 K, never above 2.43 / 2.39 s, so the 297.15 K vent stays <= 76 g at any measured Cd x A (REV-GNC-7 check, "
        "scheduled overlap 10 ms under the cap: vent at the cap <= 75.99 g for Cd x A ratios 1.0-2.0; 283.15 K margin 0.23 / 0.21 / "
        "0.21 / 0.19 / 0.18 s at ratios 1.00 / 1.08 / 1.13 / 1.20 / 1.30, 0.10-0.18 s with the FD-01 element bounds over 1.0-1.3, "
        "positive to ratio 2.0; need scaling 1 / (Cd x A) ASSUMED); the re-set takes the upper 95 % bound of the measured N2O Cd x A (a "
        "cap set from a ratio measured 7.9 % low vents 82.0 g at 297.15 K, just under the 82.1 g where the line-208 test first fails), "
        "and CF-4 shows the 283.15 K need at the re-set flow (else the cold corner stays model-only and the 1 / (Cd x A) need scaling "
        "ASSUMED); without the re-set: measured Cd x A <= 1.08 x the Cd 0.70 value (vent <= 82 g at the cap), else GNC re-runs the A1 "
        "reserve test at the measured vent. Below a ratio of 1 condition (b) of 256 (2) governs (>= 0.91, >= 0.95 with the FD-01 bound). "
        "The 14.5 g value and the reserve_frac_minus_purge_bound entries are superseded evidence (note_rev2)")
    T["N07"] = (
        "N-07 (REV-ELEC-3, routed to REV-GNC-7 by 256 (5)): no GNC objective needs the DC-D v2 duty (49.27 s thrust-on in burns of 31.76 "
        "/ 7.75 / 9.76 s; 6.31 kg N2O on the v2 map, 7.02 kg on the S230 map) as one firing in Combustion's T4. GNC's static-fire "
        "objectives (flight_profile.test_campaign[1] 'T1 static fires (DC-D)', requests[15], over_thrust_fc_thrust.v.refutation[0] and "
        ".v.unknowns[1]) need DC-D segments, not its length: throttle map and Pc loop (staircase 500 -> 62.5 N, throttle 1.0 -> 0.125, "
        "0.90-12.50 s, 1.47 kg N2O; steps 100 <-> 500 N, 12.50-16.52 s, 0.59 kg; sweep 175-399 N, 16.52-24.51 s, 1.16 kg; burn 2 triangle up "
        "to 428 N, 0.94 kg; burn 3 hold at 130 N, throttle 0.26, 0.60 kg), F_acc against the load cell at >= 450 N and the IMU vibration "
        "at F_max (10.13 s at >= 450 N in DC-D v2, 5.9 s of it in the 500 N hold of 24.51-30.52 s, 1.44 kg), gimbal sweeps, "
        "thrust-vector alignment, roll torque and rocking mode under thrust, and >= 30 starts for the ignition-latency distribution (a "
        "count; 3 per DC-D run) [DERIVED from the DC-D v2 file 9c5d7cf391d8297b, v2 basis]. Each can be flown as its own segment or "
        "firing inside the A = 150 C limit (N-07: the DC-D first burn would cross at about 23.5 s, merged bound); the DC-D v2 relights "
        "(coasts 10.25 / 8.25 s after a 31.76 s burn) do not represent the A1 relight (A1 p99 record: 3.78 s at 0.88, coast to 22.79 s, "
        "4.59 s at 0.47), so the A1-like relight objective sits with REV-COMB-4's shortest T4 firing (B1 p99 burn 21.76 s, coast about "
        "19 s, one relight of about 4.6 s at about 0.47; about 2.0 kg). qualification_check (DC-D 2.089 x the dispersed longest burn) "
        "is a record of the v2 sequence, not a GNC requirement. Naming: GNC's test_campaign T4 is the drogue drop test; Combustion's T4 "
        "is the DC-D firing of the T1-T4 regression series")
    return T


ENG11_OLD_SEG = ("design-to window 100 <= K_s <= 130 N m/rad (two-sided) for the servo output stiffness on the V5c plant (CAD v3.3) at the "
                 "ASSUMED J 1.6e-3 kg m2 (servo output shaft, added to I_piv), cons kinematics and the ASSUMED first bending 24.3 Hz full / "
                 "25.64 Hz landing; acceptance: ENG-07d (stable, upper GM >= 6 dB at every floor20 corner, continuous pose envelope, notch as "
                 "flown) re-run on the B-TVC-1 measured K_s (with its uncertainty), J, reflected-inertia convention and rocking modes at the "
                 "poses and on the measured or airframe-FE first bending mode (full and landing); K_s is frozen only on a PASS; on a FAIL the "
                 "notch set (second notch on the measured bending mode) is changed and the margins re-run before any K_s change. Plant basis: "
                 "on the 3D FE structure of CAD v3.5.1 the top of the window falls to about 126 (alpha) / 129 (beta) N m/rad (DERIVED "
                 "frequency map, uniform pose scaling ASSUMED); GNC re-verifies the window on the FE plant before it is quoted as design-to "
                 "(RV6-14 re-run, staged apart in 01-systems-gnc/staging_v3.1/rev4b/eng11_fe/, not folded here)")


def corrections(T):
    E = []
    for p in ("requirements/gimbal/tvc_actuator/ENG-11_servo_output_stiffness/v", "requirements/gimbal/tvc_actuator/B-TVC-1/v/acceptance", "status"):
        E.append(dict(op="replace", path=p, old=ENG11_OLD_SEG, new=T["ENG11_NEW"], finding="RV7-01"))
    E.append(dict(op="replace", path="requirements/gimbal/tvc_actuator/ENG-11_servo_output_stiffness/tag",
                  old="J convention VERIFIED (227 (2))",
                  new="J convention VERIFIED (227 (2)); plant basis CAD v3.5.2 R3 pose table checked by REV-GNC-7 (DERIVED, rv7_eng11_r3 v1.0 on "
                      "m2_eng11_fe v1.0 / m2_eng11 v1.1, unchanged)", finding="RV7-01"))
    E.append(dict(op="set", path="requirements/gimbal/tvc_actuator/ENG-11_servo_output_stiffness/k_band_r3_v352", new=T["K_BAND"], finding="RV7-03"))
    W = T["W"]
    E.append(dict(op="set", path="open_items/43",
                  new=("rev4b (227 (3); RV6-14): ENG-11 window on the 3D FE plant: CAD v3.5.1 re-run by GNC (eng11_fe, 24 variants: J 1.6e-3 "
                       f"<= 90-120) and CAD v3.5.2 checked by REV-GNC-7 on the R3 pose table (J 1.6e-3 {W['R3P_JC']['both']}; band ends "
                       f"{W['R3Hi_JC']['both']} / {W['R3Lo_JC']['both']}; J 2.7e-3 {W['R3P_JHI']['both']}; J 0.76e-3 {W['R3P_JLO']['both']}) "
                       "[DERIVED]: CLOSED for the datasheet sentence (requirements.gimbal.tvc_actuator.ENG-11_servo_output_stiffness, "
                       "design-to 100-110 N m/rad); remaining: B-TVC-1 (open_items[46]) and the bending mode (open_items[44]). Owner: lead "
                       "(datasheet sentence)"), finding="RV7-01"))
    old_rc1 = "Electronics v2.11 carries 0.8 s into its S17 sweep and confirms it or returns it to the lead."
    new_rc1 = ("Electronics v2.11 S17 CONFIRMED 0.8 s for the W10 < 6 m/s envelope (227 (5)) with conditions "
               "(relight_conditions.s17_v2p11_conditions).")
    E.append(dict(op="replace", path="requirements/ignition/relight_conditions/v", old=old_rc1, new=new_rc1, finding="RV7-02"))
    old_rc2 = ("Electronics implements it in v2.11 and runs S17 (onsets 1-50 ms x frame phases x noise); GNC re-runs the R2 v2 statistics "
               "with the flush afterwards; Electronics states the FC frame-noise budget against the +5.3 to +6.0 N mode-3 margin (227 (6)).")
    new_rc2 = ("implemented in the v2.11 S17 evaluator (the ECU has no mode-3 filter: the flight implementation is the FC owner's); FC "
               "frame-noise budget <= 2.51 N rms iid at 0.8 s (s17_v2p11_conditions (e)); GNC re-runs the R2 v2 statistics with the flush "
               "(open_items[47]).")
    E.append(dict(op="replace", path="requirements/ignition/relight_conditions/v", old=old_rc2, new=new_rc2, finding="RV7-02"))
    E.append(dict(op="set", path="requirements/ignition/relight_conditions/s17_v2p11_conditions", new=T["S17"], finding="RV7-02"))
    E.append(dict(op="set", path="requirements/ignition/relight_conditions/unprimed_or_unknown_line", new=T["LOST"], finding="RV7-05"))
    E.append(dict(op="set", path="requirements/ignition/relight_conditions/tag",
                  new="DESIGN (LEAD CHANGELOG lines 168 (1), 181 (4), 186 (1)-(2), 227 (5)-(6), 253 (7)(iv)); S17 v2.11 CONFIRMED with "
                      "conditions (SIM, Electronics v2.11; REV-ELEC-3 R3-04; REV-COMB-4 R4-03 / OI-PHOTODIODE-VIEW)", finding="RV7-02"))
    old_d = "Electronics v2.11 carries 0.8 s into its S17 sweep and confirms it or returns it to the lead;"
    new_d = ("Electronics v2.11 S17 CONFIRMED 0.8 s for W10 < 6 m/s with conditions (relight_conditions.s17_v2p11_conditions: hold, "
             "flush, photodiode view or re-taken reference, FC Pc branch off or moved with margin, FC noise <= 2.51 N rms iid, cold flow "
             "x 1.3 margin +1.242 N, W10 < 6 only);")
    for p in ("flight_software/rev2p1_entries/drogue_release_pc_invalid/v", "rev2/amendment_V_pc_invalid/status_rev4b"):
        E.append(dict(op="replace", path=p, old=old_d, new=new_d, finding="RV7-02"))
    E.append(dict(op="replace", path="flight_software/rev2p1_entries/drogue_release_pc_invalid/v",
                  old="Electronics implements it in v2.11 and runs S17 (onsets 1-50 ms x frame phases x noise); GNC re-runs the R2 v2 statistics with the flush afterwards",
                  new="implemented in the v2.11 S17 evaluator (flight implementation: FC owner); GNC re-runs the R2 v2 statistics with the flush (open_items[47])",
                  finding="RV7-02"))
    E.append(dict(op="replace", path="rev2/amendment_V_pc_invalid/status_rev4b",
                  old="Electronics implements it in v2.11 and runs S17 (onsets 1-50 ms x frame phases x noise); GNC re-runs the R2 v2 statistics with the flush afterwards; frame-noise budget by Electronics (227 (6));",
                  new="implemented in the v2.11 S17 evaluator (flight implementation: FC owner); GNC re-runs the R2 v2 statistics with the flush (open_items[47]); FC frame-noise budget <= 2.51 N rms iid at 0.8 s (S17 v2.11);",
                  finding="RV7-02"))
    E.append(dict(op="replace", path="flight_software/rev4b_entries/r2_frame_noise_budget/v",
                  old="against the v3.1 R2 margin (16.31 N = 37.16 - 20.85 N) the probability is about 0.",
                  new=("against the v3.1 R2 margin (16.31 N = 37.16 - 20.85 N) the probability is about 0. Electronics v2.11 S17 [SIM + "
                       "DERIVED, iid ASSUMED]: on the plant's dead-side maxima (margins +5.789 / +4.954 N) the budget for P(dead "
                       "release) <= 1e-3 is 3.06 / 2.51 N rms iid (2.00 / 1.65 N AR(1), rho 0.61) at 0.5 / 0.8 s; 5 N rms gives P 6.9 % / "
                       "22.9 % (GNC's design maxima reproduce the 6.5 / 18.4 % above); at cold flow x 1.3 the budget is 1.10 / 0.63 N rms; "
                       "the photodiode-blind families have no budget without a re-taken reference (4.28 N rms iid at 0.8 s with the "
                       "reference at the light)."), finding="RV7-02"))
    E.append(dict(op="set", path="checkpoint_rev4b/unknowns/4",
                  new="S17 v2.11 folded: pcf_tmax 0.8 s for W10 < 6 m/s CONFIRMED with conditions (227 (5); "
                      "relight_conditions.s17_v2p11_conditions); open: OI-FC-PC-BRANCH, OI-PHOTODIODE-VIEW, OI-FMIN-LIT, the measured FC "
                      "frame noise and GNC's R2 v2 re-run with the flush", finding="RV7-08"))
    E.append(dict(op="set", path="checkpoint_rev4b/next_closure/1",
                  new="GNC: 210 m gate-delay arm before flight acceptance (227 (8)); R2 v2 re-run with the flush on the v2.11 implementation "
                      "(open_items[47])", finding="RV7-02"))
    E.append(dict(op="set", path="open_items/47",
                  new="rev4b (227 (6)): mode-3 flush implemented in the Electronics v2.11 S17 evaluator and S17 run (onsets 1-50 ms x 10 "
                      "frame phases x noise; 0 of 2000 dead evaluations released with hold + flush; FC frame-noise budget <= 2.51 / "
                      "3.06 N rms iid at 0.8 / 0.5 s, 0.63 / 1.10 N rms at cold flow x 1.3) [SIM]; open: the flight implementation "
                      "(FC owner) and GNC's re-run of the R2 v2 statistics with the flush. Owner: FC owner, then GNC", finding="RV7-02"))
    E.append(dict(op="set", path="open_items/48",
                  new="rev4b (227 (5)): pcf_tmax 0.8 s CONFIRMED by Electronics v2.11 S17 for W10 < 6 m/s with conditions "
                      "(relight_conditions.s17_v2p11_conditions); the lit side on Combustion v2.4b / v2.4c: 3 of 72 P4c corners below "
                      "37.16 N in the window (OI-FMIN-LIT). CLOSED as a GNC input; the conditions are open items. Owner: lead (record)",
                  finding="RV7-02"))
    for t in [
        "OI-FC-PC-BRANCH (Electronics v2.11, REV-ELEC-3 R3-04): the FC Pc branch of the release predicate ((Pc valid AND Pc >= 300 kPa "
        "abs)) releases every normal-family run at the E2 frame in S17 (Pc_f at E2 3.04 bar abs, 0.04 bar above the threshold), "
        "including runs that flame out 1-50 ms later, outside R2 (no drogue held): a released-dead-vehicle path with Pc valid. GNC / FC "
        "owner states the branch margin or moves it (branch off until the flame-out window has passed, or a threshold with margin over "
        "the E2 value), then GNC re-flies the release statistics. Owner: GNC / FC owner",
        "OI-PHOTODIODE-VIEW (HIGH; REV-COMB-4, Electronics v2.11): pcf_tmax 0.8 s (W10 < 6 m/s, 227 (5)) holds on the dead side only with the photodiode "
        "main-chamber view (FLAMEOUT_OPT armed) or the GNC reference re-taken at the ECU E2 / light; photodiode-blind families release "
        "42 / 98 of 1000 dead runs at 0.8 s (normal_noopt / starved040_noopt, flush on, reference none) [SIM S17]. Closes at IGN-1. "
        "Owner: Combustion / Mechanical (view), GNC (reference option)",
        "OI-FMIN-LIT (230 (5); Electronics v2.11; REV-COMB-4 R4-03): at the 0.21776 mm start-level lift 3 of 72 P4c corners never reach "
        "37.16 N within the 0.8 s window (F_min 33.14 N torch 0; one crosses at E2 + 0.857 s); with the flush such a lit run is not "
        "released, the drogue is held and the relight is aborted at t_E2 + 0.8 s: a lost relight in the Pc-invalid branch; 37.16 N and "
        "0.8 s are kept (a 33.14 N threshold is below the 35.92 N dead-side maximum at cold flow x 1.3). The start-level lift is "
        "TO-VERIFY at CF-3 (230 (4)). Owner: GNC / lead, Combustion (CF-3)",
        "R3-01 (REV-ELEC-3 MAJOR; lead 253 (7)(iii) HELD): the C1 transducer thermal zero is not in the re-zero / BASE limits; a negative "
        "drift loses the A1 relight (PC_SENSOR) at k = maximum / typical coefficient >= 1.46 (node T1_head_top_bracket_foot) / 1.02 "
        "(head_bore_N2O) in the kBpc1Shown build and >= 2.18 / 1.53 in the default build; a positive drift of 1.05 bar or more gives "
        "TORCH_FAULT at k >= about 3.1 / 2.15; re-zero2 is rejected at k >= 1.024 / 0.648 (REVIEWER DERIVED on Mechanical's A1 seat "
        "history, typical 0.0248 bar/K; the maximum coefficient is MISSING, F-10). Outcome when it trips: lost relight, drogue descent, "
        "vehicle loss. GNC's A1 P does not include it (the SIL has no thermal drift; S13 A 0 / 500 BASE_AMB is structural). Owner: "
        "Electronics v2.12 (R3-01 items 1-8), Mechanical (seat node), founders (F-10); GNC re-flies the relight outcome on the S13 A "
        "re-run with the drift model",
        "PURGE condition (d) (257 (2)): kPurgeFlow_s and the both-open cap re-set from the CF-4 / B-BLEED-1 measured N2O Cd x A (upper "
        "95 % bound) with the mass flow at 297.15 K, never above 2.43 / 2.39 s, and CF-4 shows the 283.15 K need at the re-set flow; "
        "without the re-set, measured Cd x A <= 1.08 x the Cd 0.70 value or GNC re-runs the A1 reserve test at the measured vent "
        "(purge_bound.note_256_2). Owner: Combustion / Electronics (CF-4, constants), GNC (reserve test if needed)",
    ]:
        E.append(dict(op="append", path="open_items", new=t, finding="RV7-02/04/05/06"))
    E.append(dict(op="replace", path="fmea_inputs_rev2p1/status_rev4b", old="frame-noise budget pending (227 (6))",
                  new="FC frame-noise budget <= 2.51 N rms iid at 0.8 s (Electronics v2.11 S17, 0 of 2000 dead evaluations released with "
                      "hold + flush, margin +4.954 N; +1.242 N at cold flow x 1.3); with the FC Pc branch on, a run that flames out 1-50 ms "
                      "after E2 is released at the E2 frame (OI-FC-PC-BRANCH)", finding="RV7-02"))
    E.append(dict(op="append", path="fmea_inputs_rev2p1/v",
                  new="unprimed or UNKNOWN line at the A1 relight with the bleed fitted: relight refused (253 (7)(iv)); no RUN, no drogue "
                      "release, drogue descent to touchdown at about -22 m/s (rev2 amendment V), vehicle loss; probability not "
                      "quantified (PRIMED flag owner)", finding="RV7-05"))
    E.append(dict(op="replace", path="requirements/launch_commit_rev2p1/v/1/why_rev4b",
                  old="the frame-noise budget is pending (227 (6); at 5 N rms iid ASSUMED the bounding run releases with probability 18.4 % at 0.8 s, RV6-07 DERIVED)",
                  new="the FC frame-noise budget is <= 2.51 N rms iid at 0.8 s (Electronics v2.11 S17; at 5 N rms iid ASSUMED the bounding "
                      "run releases with probability 18.4 % on GNC's design maxima, 22.9 % on the S17 plant)", finding="RV7-02"))
    E.append(dict(op="rename", path="flight_software/relight_sequence_placeholder/v/purge_bound/note_rev4b",
                  new_key="note_rev4b_superseded_256_2", finding="RV7-04"))
    E.append(dict(op="set", path="flight_software/relight_sequence_placeholder/v/purge_bound/note_256_2", new=T["PURGE"], finding="RV7-04"))
    E.append(dict(op="set", path="v32_items_rev4b/items/9/status_after_rev_gnc_7",
                  new="text superseded by 256 (2) / 257 (2) (2.43 s flow, 2.39 s cap, condition (d)): purge_bound.note_256_2", finding="RV7-04"))
    E.append(dict(op="replace", path="lead_decisions_2026-10-19/rev4b_lines_204_227/reference_lines/203 (3)",
                  old="purge: ECU both-open cap <= 2.55 s (v32_items_rev4b [9])",
                  new="purge: ECU both-open cap <= 2.55 s (v32_items_rev4b [9]; superseded by 256 (2): 2.43 s flow, 2.39 s cap, purge_bound.note_256_2)",
                  finding="RV7-04"))
    E.append(dict(op="set", path="duty_cycles/note_n07_rev_gnc_7", new=T["N07"], finding="RV7-12"))
    E.append(dict(op="replace", path="status",
                  old="(9) Carried from v3.1 unchanged:",
                  new=("(9a) REV-GNC-7 folds (lead 250 (6), 253 (7), 256 (2), 257 (2)): the R3 K band and the ENG-11 check on CAD v3.5.2 "
                       "(requirements.gimbal.tvc_actuator.ENG-11_servo_output_stiffness.k_band_r3_v352); the S17 v2.11 conditions of "
                       "pcf_tmax 0.8 s for W10 < 6 m/s (227 (5); requirements.ignition.relight_conditions.s17_v2p11_conditions); the lost-relight outcome "
                       "(relight_conditions.unprimed_or_unknown_line); the final purge with condition (d) (purge_bound.note_256_2); "
                       "open items OI-FC-PC-BRANCH, OI-PHOTODIODE-VIEW, OI-FMIN-LIT, R3-01 and purge condition (d). (9) Carried from "
                       "v3.1 unchanged:"), finding="RV7-08"))
    return E


def datasheet_ops(T):
    W = T["W"]
    row8_old = ("**Design-to 100-120 N m/rad at the nominal servo J 1.6e-3 kg m2 (cons): the V5c window (100-130) intersected with the CAD "
                "v3.5.1 FE window (<= 90-120).** It is **not robust**: it moves with J (FE, cons: 0.76e-3 130->= 160; 2.7e-3 120->= 160), "
                "the inertia convention (n48 at J 1.6e-3: none) and the rotor model (two-mass: 150->= 160), and it is empty at 0.9 x first "
                "bending.")
    row8_new = ("**Design-to 100-110 N m/rad at the nominal servo J 1.6e-3 kg m2 (cons): the V5c window (100-130, CAD v3.3) intersected "
                f"with the CAD v3.5.2 FE window (R3 pose table: {W['R3P_JC']['both']}).** Only 100 N m/rad also passes at both ends of the "
                f"R3 K band (band maximum {W['R3Hi_JC']['both']}, band minimum {W['R3Lo_JC']['both']}). It is **not robust**: it moves "
                f"with J (R3 pose table, cons: 0.76e-3 {W['R3P_JLO']['both']}; 2.7e-3 {W['R3P_JHI']['both']}; no K_s passes at all three "
                "J), the inertia convention (n48 at J 1.6e-3, CAD v3.5.1: none) and the rotor model (two-mass, CAD v3.5.1: 150->= 160), "
                "and it is empty at 0.9 x first bending (CAD v3.5.1).")
    ev_old = ("DERIVED (linear ENG-07d, one fixed ECU notch, K_s grid 90-160 step 5, edges +-5 N m/rad); PROPOSAL for the lead (227 (3) "
              "keeps the decision); REV-GNC-7 check pending")
    ev_new = ("DERIVED (linear ENG-07d, one fixed ECU notch, K_s grid 90-160 step 5, edges +-5 N m/rad); CAD v3.5.2 R3 plant and band "
              "ends checked by REV-GNC-7 (the 100-120 of CAD v3.5.1 does not hold on CAD v3.5.2); PROPOSAL for the lead (227 (3) keeps "
              "the decision)")
    ops = [
        dict(row="5 (basis paragraph)", old="The ENG-11 FE-plant re-run is staged separately in `rev4b/eng11_fe/` and is not folded into the v3.2 text.",
             new="The ENG-11 FE-plant re-run (CAD v3.5.1, `rev4b/eng11_fe/`) and REV-GNC-7's check on the CAD v3.5.2 R3 pose table and K "
                 "band are folded into the v3.2 text (ENG-11_servo_output_stiffness, k_band_r3_v352).", finding="RV7-09"),
        dict(row="8", old=row8_old, new=row8_new, finding="RV7-09 / (e)"),
        dict(row="8 (evidence)", old=ev_old, new=ev_new, finding="RV7-09"),
        dict(row="8 (source)", old="J_2.7_cons_FE 125->= 160;", new="J_2.7_cons_FE 125->= 160 (set by A10, compliant + hot E -10 %; the row's 120->= 160 is the rigid T_REF variant A03);",
             finding="RV7-09"),
        dict(row="11b", old="The re-run is delivered as DERIVED in `rev4b/eng11_fe/` (row 8). It needs the REV-GNC delta check before the datasheet quotes a window.",
             new=("The CAD v3.5.1 re-run (`rev4b/eng11_fe/`) and REV-GNC-7's CAD v3.5.2 check are done (row 8; design-to 100-110 N m/rad "
                  "on CAD v3.5.2). Remaining: B-TVC-1 and the bending mode."), finding="RV7-09"),
        dict(row="11f", old=("Electronics v2.11 implements the mode-3 filter re-initialisation at the Pc-invalid onset and runs S17. Electronics "
                             "states the FC frame-noise budget against the +5.3 to +6.0 N mode-3 margin. pcf_tmax 0.8 s is confirmed or returned "
                             "to the lead. Combustion v2.4b supplies the lit side."),
             new=("Electronics v2.11 S17 CONFIRMED pcf_tmax 0.8 s for W10 < 6 m/s with conditions: the ECU R2 hold, the mode-3 flush, "
                  "the photodiode main-chamber view (or the reference re-taken), the FC Pc branch off or moved with margin "
                  "(OI-FC-PC-BRANCH), FC frame noise <= 2.51 N rms iid at 0.8 s, cold flow x 1.3 margin +1.242 N. Lit side: 3 of 72 "
                  "P4c corners stay below 37.16 N (OI-FMIN-LIT). GNC re-runs R2 v2 with the flush."), finding="RV7-09"),
        dict(row="carried unchanged", old="- pcf_tmax is 0.8 s for the W10 < 6 m/s envelope (227 (5)).",
             new="- (changed in v3.2, not carried: v3.1 had 0.5 s, line 181 (4)) pcf_tmax is 0.8 s for the W10 < 6 m/s envelope (227 (5)), "
                 "CONFIRMED by Electronics v2.11 S17 with conditions (row 11f).", finding="RV7-09"),
    ]
    return ops


def get_parent(d, path):
    parts = path.split("/")
    x = d
    for t in parts[:-1]:
        x = x[int(t)] if isinstance(x, list) else x[t]
    return x, parts[-1]


def apply(d, E):
    log = []
    for e in E:
        par, k = get_parent(d, e["path"])
        if e["op"] == "replace":
            cur = par[int(k)] if isinstance(par, list) else par[k]
            n = cur.count(e["old"])
            if n != 1:
                raise RuntimeError(f"{e['path']}: old text found {n} times")
            val = cur.replace(e["old"], e["new"])
            if isinstance(par, list): par[int(k)] = val
            else: par[k] = val
        elif e["op"] == "set":
            if isinstance(par, list): par[int(k)] = e["new"]
            else: par[k] = e["new"]
        elif e["op"] == "rename":
            par[e["new_key"]] = par.pop(k)
        elif e["op"] == "append":
            tgt = par[int(k)] if isinstance(par, list) else par[k]
            tgt.append(e["new"])
        log.append((e["op"], e["path"]))
    return log


def main():
    global RUN_D, RUN_K
    src, out_corr, out_trial = sys.argv[1:4]
    if len(sys.argv) > 4: RUN_D = sys.argv[4]
    if len(sys.argv) > 5: RUN_K = sys.argv[5]
    raw = open(src, "rb").read()
    if hashlib.sha256(raw).hexdigest()[:16] != "43d58c4aff164b86":
        raise RuntimeError("candidate sha mismatch")
    d = json.loads(raw)
    T = texts()
    E = corrections(T)
    t = copy.deepcopy(d)
    log = apply(t, E)
    t["review_trial_marker"] = "REV-GNC-7 TRIAL: candidate 43d58c4aff164b86 with the REV-GNC-7 corrections applied by the reviewer for t10_postcheck_v3; NOT gnc.json, NOT for publication"
    if sha16(DS) != DS_SHA16:
        raise RuntimeError("datasheet sha mismatch")
    md = open(DS, encoding="utf-8").read()
    D = datasheet_ops(T)
    for o in D:
        n = md.count(o["old"])
        if n != 1:
            raise RuntimeError(f"datasheet row {o['row']}: old text found {n} times")
    W = {k: {kk: vv for kk, vv in v.items() if kk in ("both", "alpha", "beta", "complete")} for k, v in T["W"].items()}
    json.dump(dict(tool="rv7_v32_corrections v2", candidate_sha16="43d58c4aff164b86", datasheet_sha16=DS_SHA16, run_dir=RUN_D,
                   windows=W, all_three_J=T["I3"], incomplete_variants=sorted(set(INCOMPLETE)), n_ops=len(E), ops=E,
                   datasheet_ops=D), open(out_corr, "w"), indent=1, ensure_ascii=False)
    json.dump(t, open(out_trial, "w"), indent=1, ensure_ascii=False)
    print(len(E), "gnc.json operations applied;", len(D), "datasheet operations checked; incomplete:", sorted(set(INCOMPLETE)))
    for k, v in W.items(): print(f"  {k:10s} both {v['both']:34s} alpha {v['alpha']:30s} beta {v['beta']}")
    print("  all three J:", T["I3"])


if __name__ == "__main__":
    main()

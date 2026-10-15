"""m2_gnc_json_v31_rev2 v1.1 (GNC rev2, 2026-10-13; v1.1: adds amendment G late-commit arms, amendment V arms, apogee trim,
amendment K re-fly results, B1 default grain gate, B1 per-phase O/F export, purge-outlet inputs, bit-check run 1 + run 2,
API of the v2.9-dev options read from run6; refuses to write while a conclusion text is unfilled): gnc.json v3.1 STAGING rev2 =
the v3.1 staging file (staging_v3.1/gnc_v3.1_staging.json, hash recorded) + the rev1 interface items (rev1_items.json) + the
rev2 results (RG-01 re-fly on the declared flight FSW, decided purge sequence, amendments G / K / V, +0.60 kg mass risk,
RG-16 terms on the decided path, bit-check v29) + the lead decisions of CHANGELOG lines 161, 164, 166, 168, 170, 172 and the
REV-GNC-2 text fixes. interfaces/gnc.json is NOT written.
Every result is referenced by path and sha256/16; the summary values are copied from those files, nothing is recomputed here.
Env: GNC_GJ31R2_DEST (default out/rev2/gnc_json/gnc_v3.1_staging_rev2.json)."""
import ast
import copy
import hashlib
import json
import os

S = "/home/claude/work/space/out"
HUB = "/home/claude/work/shared-fallback/engine"
BASE = f"{HUB}/01-systems-gnc/staging_v3.1/gnc_v3.1_staging.json"
ITEMS = f"{HUB}/01-systems-gnc/staging_v3.1/rev1/results/rev1_items/rev1_items.json"
RUN6 = "/home/claude/work/space/gnc_dev29/gncsim/run6.py"
DEST = os.environ.get("GNC_GJ31R2_DEST", f"{S}/rev2/gnc_json/gnc_v3.1_staging_rev2.json")
RES = {"rg01_refly": f"{S}/rev2/rg01_refly/rg01_refly.json",
       "bitcheck_v29_run1": f"{S}/rev2/bitcheck_v29/bitcheck_v29_run1_FAIL.json",
       "bitcheck_v29_run2": f"{S}/rev2/bitcheck_v29/bitcheck_v29.json",
       "b1_m60": f"{S}/rev2/b1_m60/b1_m60.json", "b1_of": f"{S}/rev2/b1_of/b1_of_phases.json",
       "rg16_v2": f"{S}/rev2/rg16_v2/rg16_fct_terms_v2.json",
       "kfz_pcl": f"{S}/rev2/kfz_pcl/kfz_pcl.json", "kfz_fault_f": f"{S}/rev2/kfz_fault_f/kfz_fault_f.json",
       "purge_outlet": f"{S}/rev2/purge_outlet/purge_outlet_inputs.json"}
PINS = "/home/claude/work/space/gnc_dev29/data/pins/pins_rev2.sha256"
VERSION = "m2_gnc_json_v31_rev2 v1.1"
PREDICATE = ("RELEASE iff RUN AND b4 AND [(Pc valid AND Pc >= 300 kPa abs) OR b7 OR (d2-d3 = 0xFFFF AND t >= t_E2 + 0.10 s)], "
             "latched; b7 sets on the valid filtered channel only (LEAD CHANGELOG line 168, restating line 161)")
TODO = "TO-FILL"
# ---- conclusion texts (GNC PROPOSALS / findings; filled after the results were read; the builder refuses TO-FILL) ----
TXT = {
    "G_late": "FINDING + PROPOSAL (amendment a). The rule 'never T_fire before 1.9 s of flow; delay T_fire instead' is safe only for an early commit. Commit-floor sweep on state e19 (Tp1.9 robust-edge table, conservative when the flow is cut), A1_none / A1J_pc, seed 101, 500 runs each: commit at the plain trigger (T_fire delayed 2.30 s, E0 at ~0.1 m) P 0.000/0.000; forced commit at 100 m P 0.992/0.986 (T_fire delay <= 0.64 s; pooled -3/+4 vs the decided e19 commit, p 1.0); 90 m 0.946/0.932 (delay <= 1.02 s; -51/+2, p 3e-13, LOSES); 80 m 0.446/0.458; 70 m 0.018/0.022 (60 m not flown). DERIVED: a T_fire delay up to ~0.6 s behind the plain trigger costs no measurable P; ~1 s loses ~6 %. Lowest safe forced-commit height ~100 m on this vehicle and drogue. PROPOSAL (lead decision): commit no later than plain trigger - 1.7 s (0.35 + 1.9 + 0.05 - 0.6); if not committed by then, do not purge (PURGE NOT RUN LO: P|lit 0.986/0.980, with the sequence flown 0.994/0.986; P_abort 0.242; P_total 0.742-0.753) instead of delaying T_fire (P 0.000 at the plain trigger). Comparator: the decided delay rule. Refutation: Combustion shows an unpurged start at that point carries a hazard outside its abort model (TO-VERIFY). The decided predictor never needed it: commit >= 2.66 s before the plain trigger in every run where the plain trigger fired.",
    "G_combustion_height_cost": 'Combustion v2.4 ask - height cost of the T_fire-delay rule. Decided path (FSW-R2, G73; purge windows identical across pw / pl / liq / e19): commit source = predictor in 2000/2000 runs (A1_none, A1J_pc, A1_pc, A1J_none on e19), commit height 88.8-129.6 m, >= 2.66 s before the plain trigger, so the 1.9 s floor never bound (flow >= 2.387 s, purge 69.7-73.0 g). In the 161 / 166 of 500 runs per base where the plain trigger fired before the planned T_fire, T_fire moved to the plain trigger + 0.127 s (valve close 0.077 s + 0.05 s stop): E0 came p50 0.47-0.58 m, p99 2.86-2.88 m, max 3.04 m below the height at the plain trigger, with no P loss (pw|G73 vs liq|none pooled -7/+4, p 0.55). Late commits: finding above (delay up to 2.30 s; 42.8 m on the nominal 1 ms record, bit-check G2).',
    "V": 'RECOMMENDATION (amendment c, PROPOSAL to the lead): replace the time-only 0xFFFF term of the adopted predicate (the interim rule, R1) by an accelerometer confirmation (R2): with d2-d3 = 0xFFFF, release when m_est x (filtered axial specific force - its drogue-descent baseline frozen at E0) >= 37.16 N on 3 consecutive 100 Hz frames with the ECU in RUN; if not confirmed by t_E2 + pcf_tmax, hold the drogue and abort. Evidence (pw|G73, Pc invalid from E2, A1_none / A1J_pc, 500 runs each, paired with pw|G73): engine lit - R1 0.990/0.986 (pooled -1/+4), R2 0.990/0.984 (-2/+4), R2 releases 40-70 ms after the light (R1: 100 ms); open-loop factor 0.875 - R1 0.992/0.988, R2 0.990/0.988 (0 aborts); with the 2.4 bar x 0.4 s plateau - R1 0.982/0.972, R2 0.986/0.976 (released 440-470 ms after the light, 0 aborts). Undetected flame-out at E2 (ECU stays in RUN) - R1 releases a dead vehicle in 1000/1000 runs (touchdown p50 -32.3 m/s, p01 -35.7 m/s); R2 holds the drogue in 1000/1000 (largest accelerometer estimate 33.0 N < 37.16 N) and the vehicle descends on the drogue (touchdown p50 -21.8 m/s, p01 -24.3 m/s; ~0.46 x the impact energy). Both flame-out outcomes are vehicle losses (P 0). R3 (always hold) loses every lit flight (0/1000 vs 0.985); R0 (no Pc-free term) 0.392/0.396. Margins are thin and must be widened before adoption: flame-out estimate max 33.0 N vs 37.16 N threshold (11 %); plateau release max 470 ms vs the 500 ms deadline -> PROPOSAL pcf_tmax 0.8 s (not flown). TO-VERIFY: accelerometer noise and bias at the IMU, drogue snatch and canopy pendulum (massless quasi-steady canopy in sim6), flame-out cold flow (not modelled), onsets after E2 (only pcf_dt 0 flown; the valid Pc branch releases 6-12 ms after the light, which bounds the window).',
    "trim": 'A1 apogee trim ADOPTED under LEAD line 168 (4) (>= 275 m adopted without a decision): h_target 300 -> 285 m (apogee p50 304.5-304.9 -> 289.4-289.9 m). At 285 m the decided path has 0 exhausted runs in liq|G73 and pw|G73 on A1_none and A1J_pc (untrimmed: 2/2 and 1/0); minimum usable reserve 4.8 / 9.6 g (liquid table) and 15.0 / 19.3 g (purged worst); P 0.990/0.986 and 0.990/0.988; pooled against the untrimmed arms liq -8/+13 (p 0.38), pw -7/+11 (p 0.48). 290 m leaves 1 exhausted run (A1_none liquid); 280 m also clears with reserve minima 9.5-27.7 g. Cost: 15 m of apogee target. Mass risk +0.60 kg (conditional): exhaustions remain at every flown target (liq|G73|m60 6/7 at 300 m, 5/5 at 290, 3/4 at 280, 3/3 at 275; pw|G73|m60 6/7, 5/4, 3/3, 3/3) and 2/2 already without a purge (liq|none|m60); runs 14, 108 and 490 end at the 3 % residual even at 275 m -> a trim below 275 m or another fix (propellant load, landing reserve) is a LEAD decision if the mass materialises.',
    "K": 'FINDING (amendment b, LEAD line 113 (2) freeze): H-K REFUTED. Re-fly with kfz_on 1, paired with the stored K-off tables. Mass-estimator Pc-lost arms (Pc lost from the pad, open-loop factor 1.143 or 0.875): A1_none pcllo re / cmd / re_comp 0.992 -> 0.858 (-67/+0), 0.994 -> 0.840 (-79/+2), 0.996 -> 0.860 (-68/+0); B1_62 pclhi 0.986 -> 0.704 (-145/+4), 0.994 -> 0.690 (-154/+2), 0.994 -> 0.704 (-147/+2); A1 pclhi and B1 pcllo no loss. Fault arms (m2_fault_f, 50 Pc-lost arms, 8000 runs): A1 identical; B1 ascent Lhi_blind 0.095 -> 0.025 (-14/+0), MISS 0.110 -> 0.030 (-8/+0), GEO 0.110 -> 0.000 (-11/+0) with 11 false geofence trips; floor GEO 26 false; landing Lhi_blind detections 200 -> 179, GEO 82 false; total detections 5960 -> 5918. Mechanism: with Pc invalid the freeze stops k_hat learning the open-loop thrust error from the accelerometer (k_hat stays 1.000 when Pc is lost from the pad), so the landing burn runs on a 12.5 % thrust error (A1 low end) and the B apex predictor overshoots (B1land Lhi_blind apex p50 64.5 -> 81.3 m, max 111.1 m) and trips the geofence before the fault. The K-off tables keep k_hat learning against F/tsc, which equals the throttle-map thrust of the current pintle position: the flight software can form it from its command / encoder without Pc, apart from map error (not modelled). PROPOSAL: do not fly the freeze; with Pc invalid, re-reference k_hat and the apex predictor to the throttle-map thrust of the commanded / measured pintle position and keep learning (a freeze only for short dropouts, length TO-DEFINE); Pc valid as a launch-commit condition. Comparator: K freeze and K off. Refutation: a McNemar loss against K off once a throttle-map error band is added (new amendment, not flown). FSW-R2 does not include K; no RG-01 result depends on it.',
    "b1_gate": "B1 62 m is carried on the DEFAULT pre-flight grain gate (LEAD line 172 (3)): 'lead rule (a_meas >= 1.25 AND n_meas <= 0.40) OR a_meas >= 1.25 -> change the grain', i.e. every engine with a_meas >= 1.25 is re-grained. Kept 364/500 (72.8 %). FSW-R2 B1 (W1p web limit, limit action on): P 0.989 [0.972, 0.996], 0 exhausted, usable reserve min 109.6 g; web at the end of the record >= 2.62 mm, limit acted in 1/364 runs (34/500 without the gate), 0/364 below 1 mm; +0.60 kg 0.989 (-2/+2, p 1.0), reserve shift p50 -10.7 g, min -31.2 g. The rev1 statement '0/364 below 1 mm' was the W1p_tot scan; this is the rev2 W1p re-fly. Per-phase O/F of the B1 records: rev2.b1_of_phases (ascent 9.8-10.1, apex/floor 5.0-5.3, descent 4.8-5.1, landing 8.3-9.3, terminal 5.3-5.9 mass-weighted; minimum instantaneous 2.06).",
    "outlet": "Inputs for Combustion's tank-outlet coverage check during PURGE (no coverage verdict: tank and outlet geometry and fill are not GNC data). Decided path, 500 runs per base: tilt from the vertical inside the flow p50 1.6 deg, p99 5.2-5.3 deg, max 6.9 deg; transverse body rate p99 11.8-13.0 deg/s, max 16.1 deg/s; roll rate up to 35.4 deg/s (10 ms records); purge window identical in the pw and pl states. 10 ms records of run 0 and of the largest-tilt and largest-rate runs (identical re-flights, 12/12 checks): axial specific force 0.89-1.12 g; angle between the body axis and the specific force <= 2.65 deg (0.1 s mean; <= 2.71 deg raw) = quasi-static free-surface tilt relative to the tank axis; descent 21-25 m/s; flow from 95-115 m down to 43-54 m; liquid 846-1170 g at the flow start and 766-1089 g at its end. Not modelled: slosh (lumped liquid), lateral specific force beyond the record, canopy pendulum.",
}


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def J(p):
    return json.load(open(p)) if os.path.exists(p) else None


def ref(p):
    return f"{p} (sha256/16 {sha16(p)})" if os.path.exists(p) else f"{p} (ABSENT)"


def api(prefixes):
    """{name: {default, tag}} of the run6 options with the given prefixes (run6 source: DEF and the S() registry)."""
    tree = ast.parse(open(RUN6).read())
    dflt, tags = {}, {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "DEF" for t in node.targets) \
                and isinstance(node.value, ast.Call):
            for kw in node.value.keywords:
                try:
                    dflt[kw.arg] = ast.literal_eval(kw.value)
                except ValueError:
                    dflt[kw.arg] = ast.unparse(kw.value)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "S" and len(node.args) >= 3 \
                and isinstance(node.args[0], ast.Constant) and isinstance(node.args[2], ast.Constant):
            tags[node.args[0].value] = node.args[2].value
    return {k: dict(default=dflt.get(k), tag=tags.get(k)) for k in sorted(set(dflt) | set(tags)) if k.startswith(prefixes)}


def case_row(e, paired=None):
    d = dict(P=round(e["P"], 4), P_wilson=[round(x, 4) for x in e["P_wilson"]], P_abort=e["P_abort"], P_total=e["P_total"],
             exhausted=e["exhausted"], usable_reserve_min_g=round(e["usable_reserve_g"]["min"], 1),
             usable_reserve_p01_g=round(e["usable_reserve_g"]["p01"], 1), reserve_runs_14_108_g=e["usable_reserve_runs_14_108"],
             fail_modes=e["fail_modes"], apogee_p01_p50_p99_m=[round(e["apogee_m"][q], 1) for q in ("p01", "p50", "p99")]
             if e.get("apogee_m") else None)
    if e.get("purge_sequence"):
        ps = e["purge_sequence"]
        d["purge_sequence"] = dict(commit_source=ps["commit_source"], commit_h_p01_p50_p99=[round(ps["commit_height_m"][q], 1)
                                   for q in ("p01", "p50", "p99")], E0_h_p01_p50=[round(ps["E0_height_m"][q], 1) for q in ("p01", "p50")],
                                   flow_s_min_max=[round(ps["flow_s"]["min"], 3), round(ps["flow_s"]["max"], 3)],
                                   plain_fired_before_E0=ps["plain_fired_before_E0"], spurious=ps["spurious"],
                                   tfire_delay_vs_plain_s=ps.get("tfire_delay_vs_plain_s"))
    if e.get("pc_invalid"):
        d["pc_invalid"] = e["pc_invalid"]
    if paired:
        d["paired"] = paired
    return d


def rg01_table(r, pred=lambda k: True):
    if not r:
        return None
    return {k: case_row(e, r["paired"].get(k)) for k, e in r["cases"].items() if pred(k)}


def pooled(r, pred):
    return {k: v for k, v in ((r or {}).get("pooled") or {}).items() if pred(k)}


def bitcheck(r1, r2):
    latest = {}
    for tag, r in (("run1", r1), ("run2", r2)):
        for k, v in ((r or {}).get("parts") or {}).items():
            latest[k] = dict(passed=v.get("passed"), run=tag)
    return dict(run1=dict(source=ref(RES["bitcheck_v29_run1"]), tool=(r1 or {}).get("tool"), parts_run=(r1 or {}).get("parts_run"),
                          parts={k: v.get("passed") for k, v in ((r1 or {}).get("parts") or {}).items()},
                          note="run 1 failed two TEST expectations (G1 liquid vs vehicle mass drop, N4 KeyError name); "
                               "simulator unchanged between run 1 and run 2 (file times; code hashes recorded by run 2)"),
                run2=dict(source=ref(RES["bitcheck_v29_run2"]), tool=(r2 or {}).get("tool"), parts_run=(r2 or {}).get("parts_run"),
                          parts={k: v.get("passed") for k, v in ((r2 or {}).get("parts") or {}).items()},
                          code_sha256_16=(r2 or {}).get("code_sha256_16")),
                latest_per_part=latest, all_latest_passed=bool(latest) and all(v["passed"] for v in latest.values()))


def b1_of_summary(o):
    if not o:
        return None
    s = {}
    for n, r in o["records"].items():
        s[n] = dict(sha256_16=r["sha256_16"], hash_matches_listing=r["hash_matches_listing"],
                    phases={e["label"]: dict(OF_mass_weighted=(round(e["OF_mass_weighted"], 2) if e["OF_mass_weighted"] else None),
                                             OF_min=(round(e["OF_min"], 2) if e.get("OF_min") is not None else None),
                                             OF_max=(round(e["OF_max"], 2) if e.get("OF_max") is not None else None),
                                             fuel_flow_time_s=round(e["fuel_flow_time_s"], 2))
                            for e in r["phases"].values()})
    return s


def main():
    left = [k for k, v in TXT.items() if TODO in v]
    if left:
        raise SystemExit(f"conclusion texts not filled: {left}")
    g = json.load(open(BASE))
    out = copy.deepcopy(g)
    items = J(ITEMS)
    R = {k: J(p) for k, p in RES.items()}
    rg = R["rg01_refly"]
    out["version"] = "v3.1-staging-rev2"
    out["date"] = "2026-10-13"
    out["staging"] = dict(v=("STAGING rev2 for the lead: not interfaces/gnc.json. Folds rev1_items, the RG-01 re-fly on the declared "
                             "flight FSW and the lead decisions to CHANGELOG line 172; carries every v3.1 staging section unchanged "
                             "except the fields listed in changes_rev2. SIM results only: no physical validation."),
                          base=ref(BASE), builder=VERSION)
    ch = []
    # text fix 1: relight_conditions (REV-ELEC-1 / l.166 (1), l.168)
    rc = out["requirements"]["ignition"]["relight_conditions"]
    old = rc["v"]
    rc["v"] = old.replace("drogue release only on Pc >= 50 % of floor Pc", "drogue release on the adopted predicate: " + PREDICATE)
    if rc["v"] == old:
        rc["v"] = old + " | rev2: drogue release on the adopted predicate: " + PREDICATE
    rc["v_superseded_rev2"] = old
    rc["tag_rev2"] = "DESIGN (LEAD CHANGELOG lines 161, 168)"
    ch.append("requirements.ignition.relight_conditions: drogue text replaced by the adopted release predicate (l.168); old text kept")
    # text fix 2: purge bound 14.5 g -> <= 76 g per purge, Combustion <= 73.0 g at the 2.5 s ECU cap
    pb = out["flight_software"]["relight_sequence_placeholder"]["v"]["purge_bound"]
    pb["superseded_rev2"] = True
    pb["n2o_bound_per_purge_kg_rev2"] = 0.076
    pb["ecu_cap_mass_kg_rev2"] = 0.0730
    pb["note_rev2"] = ("superseded: <= 76 g per purge (LEAD lines 164/166), Combustion <= 73.0 g at the 2.5 s ECU duration cap "
                       "(rg01_line_states_v2p4 / purge_vented_mass_v2p4: vented 34.3-72.9 g at t_flow 2.5 s). The 14.5 g value "
                       "and the reserve_frac_minus_purge_bound entries computed with it are kept as superseded evidence; the A1 "
                       "reserve with the purge is rev2.rg01_refly.")
    ch.append("flight_software.relight_sequence_placeholder.purge_bound: superseded by <= 76 g / 73.0 g (old value kept)")
    # A1 apogee trim (LEAD line 168 (4): >= 275 m adopted without a decision)
    rb = out["flight_profile"]["recommended_baseline"]
    rb["note_rev2"] = ("rev2: A1 apogee target h_target 300 -> 285 m (apogee p50 ~289.5 m) ADOPTED under LEAD line 168 (4) to remove the "
                       "purge-mass exhaustions on the decided path (rev2.apogee_trim); decided purge sequence (G73, PURGE at E0 - 2.90 s); "
                       "drogue release on the adopted predicate (requirements.ignition.relight_conditions); FSW-R2 (rev2.fsw_declared)")
    rb["h_target_A1_m_rev2"] = 285.0
    ch.append("flight_profile.recommended_baseline: A1 apogee target 285 m (note_rev2, h_target_A1_m_rev2); v3 notes kept")
    # inputs_read refresh (RG-12, N4)
    pins = {}
    for ln in open(PINS):
        h, n = ln.split(None, 1)
        pins[n.strip()] = h[:16]
    out["inputs_read"]["rev2_2026-10-13"] = dict(
        pin_list=ref(PINS), files=pins,
        iface_dir="/home/claude/work/space/iface_v3d (combustion.json = hub v2.4; electronics.json = v1 pin, hub v2 has no "
                  "dynamics_for_GNC -> N5 dependency)",
        strict_mode="run6 v2.9-dev GNC_STRICT 1: unreadable interface file -> error; sha256 checked against the pin list; versions "
                    "asserted (combustion v2.4, electronics v1, mechanical v2)",
        changelog=ref(f"{HUB}/interfaces/CHANGELOG.md") + " read to line 172",
        review=ref(f"{HUB}/reviews/REVIEW-GNC-R1.md"))
    ch.append("inputs_read.rev2_2026-10-13: every rev2 input pinned by sha256 (pin list), strict mode, N5 dependency stated")
    out["rev1_items"] = dict(source=ref(ITEMS), v=items)
    ch.append("rev1_items folded (rev1_items.json v1.2)")
    is_late = lambda k: any(s in k for s in ("|ant0", "|hf", "|pcfR", "|h2"))  # noqa: E731
    rev2 = dict(
        fsw_declared=dict(name="FSW-R2", v=("stored v2.8 flight-software base (m2_eng03_rate.base_ref, k_est_asc 2) + flown mass "
                                            "estimator tot_cal_comp (mest_mode 1, kest_comp 1, weighing 20 g 1 sigma, flow calibration "
                                            "1.5 %, growth model g_hat 0.09) + decided release predicate (rel_mode 1, rel_to 0.10 s) + "
                                            "fct_comp 1 (FC_THRUST not armed on A1) + decided purge sequence (sim6 amendment G: PURGE "
                                            "committed T_fire - 2.90 s, flow 2.5 s ECU cap, 29.2 g/s booked 73.0 g, gate + "
                                            "constant-velocity commit predictor, T_fire never before 1.9 s of flow)"),
                          tag="DESIGN (REV-GNC-2 N1)"),
        rg01_refly=dict(source=ref(RES["rg01_refly"]), table=rg01_table(rg, lambda k: not is_late(k)),
                        pooled=pooled(rg, lambda k: not is_late(k)), continuity=(rg or {}).get("continuity"),
                        plan_check=(rg or {}).get("plan_check"), states=(rg or {}).get("states")),
        api_v29=dict(note="sim6/run6 v2.9-dev options; every option off by default and bit-identical when off (bit-check v29 A0/A1)",
                     G=api(("pgg_",)), K=api(("kfz_",)), V=api(("pcf_",))),
        amendment_G_late_commit=dict(arms=rg01_table(rg, lambda k: "|ant0" in k or "|hf" in k),
                                     pooled=pooled(rg, lambda k: "|ant0" in k or "|hf" in k), finding=TXT["G_late"],
                                     combustion_ask_height_cost=TXT["G_combustion_height_cost"]),
        amendment_V_pc_invalid=dict(arms=rg01_table(rg, lambda k: "|pcfR" in k), pooled=pooled(rg, lambda k: "|pcfR" in k),
                                    recommendation=TXT["V"]),
        apogee_trim=dict(arms=rg01_table(rg, lambda k: "|h2" in k), pooled=pooled(rg, lambda k: "|h2" in k),
                         references=rg01_table(rg, lambda k: k.split("|", 1)[1] in ("liq|G73", "pw|G73", "liq|G73|m60", "pw|G73|m60",
                                                                                    "liq|none", "liq|none|m60")
                                               and k.split("|", 1)[0] in ("A1_none", "A1J_pc")),
                         decision=TXT["trim"]),
        bitcheck_v29=bitcheck(R["bitcheck_v29_run1"], R["bitcheck_v29_run2"]),
        b1_mass_risk=dict(source=ref(RES["b1_m60"]), v=R["b1_m60"]),
        b1_default_grain_gate=dict(source=ref(RES["b1_m60"]), v=(R["b1_m60"] or {}).get("default_gate"), statement=TXT["b1_gate"],
                                   tag="DESIGN (LEAD CHANGELOG line 172 (3))"),
        b1_of_phases=dict(source=ref(RES["b1_of"]), csv=ref(RES["b1_of"].replace(".json", ".csv")), summary=b1_of_summary(R["b1_of"]),
                          tag="SIM records (sim6 engine model: map O/F x regression band of the record draw); DERIVED sums"),
        purge_outlet_inputs=dict(source=ref(RES["purge_outlet"]), distributions=(R["purge_outlet"] or {}).get("distributions"),
                                 records=(R["purge_outlet"] or {}).get("records"),
                                 checks_passed=(R["purge_outlet"] or {}).get("all_checks_passed"), statement=TXT["outlet"]),
        rg16_v2=dict(source=ref(RES["rg16_v2"]), budget=(R["rg16_v2"] or {}).get("budget"), cases=(R["rg16_v2"] or {}).get("cases"),
                     vent=(R["rg16_v2"] or {}).get("vent"), bled_max_g=(R["rg16_v2"] or {}).get("bled_max_g"),
                     status="FC_THRUST NOT armed on A1 (LEAD line 168: until RG-16 passes)"),
        amendment_K=dict(pcl=ref(RES["kfz_pcl"]), fault_f=ref(RES["kfz_fault_f"]),
                         pcl_arms=(R["kfz_pcl"] or {}).get("arms"), fault_f_totals=(R["kfz_fault_f"] or {}).get("totals"),
                         fault_f_arms=(R["kfz_fault_f"] or {}).get("arms"), finding=TXT["K"]),
        text_fixes_rev1=[
            "withdrawn: Unknowns row 'live hub combustion.json no longer has igniter.sequence' (REFUTED, review 4.3); combustion "
            "v2.4 rewrites igniter.sequence, run6 does not read it",
            "withdrawn: RG-12 note 'the live hub combustion.json has drifted'; stated instead: electronics.json v2 breaks run6.build "
            "(no dynamics_for_GNC) -> TVC dynamics stay on the electronics v1 pin (N5)",
            "s2.8: the 19/500 runs below 1 mm of web (W1p_tot, total-flux law) were flown WITH the limit action (web_act 1), not "
            "without it",
            "s2.10: bounds per arm: 0/200 -> 1.49 % (exact one-sided 95 %) or 1.9 % (Wilson); the pooled 0/800 and 0/1192 share draws "
            "and are not tighter than the per-arm bound",
            "bit-check v1.5 'ALL PASSED' covered parts A, C-F, P, R and S (B empty; G, H, W, X last run at v1.3 on the pre-R code); "
            "rev2 bit-check v29 lists the parts it ran",
            "start_transient.json: arm L400_te flew t_ign_est 1.11 s (label 0.81 s wrong; P values unaffected)",
            "B1 carried on the DEFAULT pre-flight grain gate (lead rule OR a_meas >= 1.25 -> change the grain; LEAD line 172 (3)) "
            "instead of the lead rule alone; see rev2.b1_default_grain_gate"])
    out["rev2"] = rev2
    ch.append("rev2 section added (FSW-R2, RG-01 re-fly, API v2.9-dev, amendments G / V / K, apogee trim, bit-check v29 runs 1-2, B1 "
              "mass risk, B1 default grain gate, B1 per-phase O/F, purge-outlet inputs, RG-16 v2, text fixes)")
    out["changes_rev2"] = ch
    out.setdefault("lead_decisions_2026-10-13", {})
    if isinstance(out["lead_decisions_2026-10-13"], dict):
        out["lead_decisions_2026-10-13"]["rev2_lines_161_172"] = (
            "CHANGELOG 161 (release predicate, purge sequence, FC-1), 164 (purge ECU sequence, mass risk 0.60 kg), 166 (REV-ELEC-1 "
            "ECU changes), 168 (REV-GNC-2: one FSW, pins, ECU cap, RG-16 form adopted, restated predicate, BLEED_FAULT log-only), "
            "170 (25 bar Pc cap stays; hub v2p4 tables are the re-fly inputs), 172 (REV-COMB-2: RG-16 vented minima flown as is; "
            "B1 default grain gate; B1 per-phase O/F export)")
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    with open(DEST, "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("base", ref(BASE))
    print("wrote", ref(DEST))
    print("absent results:", [k for k, v in R.items() if v is None])


if __name__ == "__main__":
    main()

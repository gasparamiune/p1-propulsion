"""REV-GNC-4 t17: positive / negative controls for t10_postcheck v2 (reviewer test fixture, scratch only).
Builds MOCK fixtures from the staged rev2.1 JSON by phrase-level substitutions that restate lead lines 181/186 and the
REV-GNC-4 corrections. The fixtures test the checker's false-positive / false-negative behaviour only. They are NOT a
proposed gnc.json text, are never published, and every inserted string carries '[MOCK]'.
Usage: python -I t17_mock_fix.py <staged.json> <out_dir>  -> writes mock_pass.json and mock_stale_c10.json"""
import json, re, sys, copy, os
src, outd = sys.argv[1], sys.argv[2]
d0 = json.load(open(src))
def sub(obj, path, old, new, count=1):
    """replace a literal phrase in the string leaf at path (keys separated by '/'); fail loudly if absent"""
    keys = path.split("/"); x = obj
    for k in keys[:-1]: x = x[int(k)] if isinstance(x, list) else x[k]
    last = int(keys[-1]) if isinstance(x, list) else keys[-1]
    s = x[last]
    if old not in s: raise SystemExit(f"phrase not found at {path}: {old[:80]!r}")
    x[last] = s.replace(old, new, count)
def build():
    d = copy.deepcopy(d0)
    L186 = "[MOCK] L* = 1.3 s for both brackets (lead 186 (1)); below L* no purge and no unpurged relight on that pass (drogue descent, vehicle loss in the FMEA); GNC flies the alternative: unpurged relight with drogue release held to >= E2 + 0.22 s"
    sub(d, "status", "L* = 1.7 s if an unpurged start is LO, 1.3 s if HI; FSW interim 1.7 s", L186)
    sub(d, "requirements/ignition/relight_conditions/v", "interim 1.7 s; else the relight proceeds unpurged, lead 181 (2))",
        "[MOCK] L* = 1.3 s; else no purge and no unpurged relight on that pass, lead 186 (1)); [MOCK] R2 command hold: open-loop command held at the start level (62.5 N) while the drogue is attached with Pc invalid (lead 186 (2))")
    sub(d, "flight_software/rev2p1_entries/purge_commit_rule/v", "(interim 1.7 s; 1.3 s if HI); else no purge, relight unpurged",
        "[MOCK] = 1.3 s (both brackets, lead 186 (1)); else no purge and no unpurged relight on that pass")
    sub(d, "rev2/amendment_G_late_commit/finding",
        "L* = 1.7 s if an unpurged start is LO (break-even against PURGE NOT RUN LO, P_total ~0.75) and 1.3 s if HI (skipping gives P_total 0); FSW interim 1.7 s until",
        "[MOCK] L* = 1.3 s for both brackets (lead 186 (1)); the premise P_total ~0.75 for an unpurged LO start is REFUTED by Combustion v2.4a; formerly until")
    sub(d, "rev2/amendment_G_late_commit/finding", "is pending a lead decision and would move L* (rev3 P6 adds it as a third case)",
        "[MOCK] was decided by the lead in 186 (1)")
    sub(d, "rev2/amendment_G_late_commit/finding", "plain trigger fired (2000 runs;", "plain trigger fired ([MOCK] 649 of 2000 runs;")
    sub(d, "open_items/32", "(not decided by the lead)", "([MOCK] decided by the lead in 186 (1): no purge and no unpurged relight below L* = 1.3 s)")
    sub(d, "pending_inputs_rev2p1/combustion_unpurged_start/v", "NOT decided by the lead; affects L* (lead 175 (3) refutation clause)",
        "[MOCK] decided by the lead in 186 (1) (L* = 1.3 s; below L* no purge and no unpurged relight)")
    p = "rev1_items/v/drogue_release_rule/fc_implementation/predicate"
    x = d["rev1_items"]["v"]["drogue_release_rule"]["fc_implementation"]; x["predicate"] = "SUPERSEDED by R2 ([MOCK] lead 181 (4), 186 (2)): " + x["predicate"]
    sub(d, "rev1_items/v/purge_cost_A1_reserve/decision", "0.81 s plan holds", "0.81 s plan holds ([MOCK] scoped to the predictor path, lead 181 (2))")
    sub(d, "conventions/stations", "RV-1c: pivot at 0.2223 m = mechanical.json frames.rv1_station_of_pivot_m",
        "[MOCK] vehicle v3d: pivot at 0.203 m = mechanical.json v2 frames.rv1_station_of_pivot_m")
    sub(d, "pending_inputs_rev2p1/cold_flow_bound", "rev3 P4 carries 0 / 5 / 10 N parametric until then",
        "[MOCK] bounded by Combustion v2.4a (DERIVED 12.5-13.3 N at the start level; lead 186 (2)); rev3 P4 flies F_cold")
    sub(d, "checkpoint_rev2p1/unknowns/2", "cold-flow apparent thrust unbounded",
        "[MOCK] cold-flow apparent thrust bounded only by a DERIVED adiabatic estimate (12.5-13.3 N at the start level); heat pick-up TO-VERIFY")
    sub(d, "requirements/launch_commit_rev2p1/v/1/why", "(REVIEWER reviews/gnc/rev2/logs/s04_wind.out (40ac5dc493ea98e1))",
        "([MOCK] REVIEWER reviews/gnc/rev2/logs/s03_trim.out (819a79cf0db42fda); REVIEW-GNC-R2.md 4.2)")
    sub(d, "pending_inputs_rev2p1/vibration_spectrum", "RG-16 margin 0.012 %", "[MOCK] RG-16 margin 0.012 percentage points (REVIEWER)")
    sub(d, "checkpoint_rev2p1/unknowns/1", "RG-16 margin 0.012 %", "[MOCK] RG-16 margin 0.012 percentage points (REVIEWER)")
    d["flight_profile"]["mission_plan_v3"]["status_rev2p2"] = "[MOCK] HISTORY at 300 m; A1 target 285 m (lead 175 (1), 181 (6))"
    d["propellant_closure_v3"]["status_rev2p2"] = "[MOCK] HISTORY at 300 m; A1 target 285 m (lead 175 (1), 181 (6))"
    d["lead_decisions_2026-10-13"]["rev2p1_lines_175_183"]["folded"]["186 (1)"] = "[MOCK] L* = 1.3 s both brackets"
    d["lead_decisions_2026-10-13"]["rev2p1_lines_175_183"]["folded"]["186 (2)"] = "[MOCK] R2 command hold 62.5 N"
    d["publication_note"]["built_on"] += "; [MOCK] rev2 / rev2.1 evidence on sim6/run6 v2.9-dev with iface_v3d (combustion.json v2.4)"
    d["rev3_plan"] = {f"P{i}": f"[MOCK] rev3 item {i}" for i in range(1, 10)}
    d["status"] += " [MOCK] Every P, reserve and closure figure here is at ledger v3d; at CAD v3.5 the A1 285 m closure is not demonstrated."
    d["rev2"]["amendment_V_pc_invalid"]["reviewer_probes"]["inside_W10_lt6_N"].update({"base": "A1_none", "A1J_pc_t05_max": 20.85})
    d["fmea_inputs_rev2p1"]["v"][3] = "SUPERSEDED by 186 (1): " + d["fmea_inputs_rev2p1"]["v"][3]
    d["fmea_inputs_rev2p1"]["v"].append("[MOCK] unpurged start at the worst PURGE NOT RUN states: P 0 under LO and HI; below L* = 1.3 s no relight on that pass: drogue descent, vehicle loss (lead 186 (1))")
    d["fmea_inputs_rev2p1"]["v"][4] += " [MOCK] no cold flow modelled; DERIVED cold-flow bound 35.6-37.5 N at a 200 N command, 12.5-13.3 N at the start level (lead 186 (2))"
    d["version"] = "v3.1"
    sub(d, "status", "v3.1 STAGING rev2.1 (2026-10-13): NOT PUBLISHED.", "[MOCK] v3.1 (2026-10-13).")
    d["supersedes"] = "[MOCK] gnc.json v3"
    sub(d, "checkpoint_rev2p1/delivered_reviewed_date", "status Por revisar", "[MOCK] status Revisado")
    return d
os.makedirs(outd, exist_ok=True)
ok = build()
json.dump(ok, open(f"{outd}/mock_pass.json", "w"), indent=1, ensure_ascii=False)
bad = copy.deepcopy(ok)   # negative control: one stale unpurged-relight fallback put back
bad["flight_software"]["rev2p1_entries"]["purge_commit_rule"]["v"] += "; else no purge, relight unpurged"
json.dump(bad, open(f"{outd}/mock_stale_c10.json", "w"), indent=1, ensure_ascii=False)
print("wrote", f"{outd}/mock_pass.json", f"{outd}/mock_stale_c10.json")

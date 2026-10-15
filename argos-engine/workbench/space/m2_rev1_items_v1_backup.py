"""m2_rev1_items v1 (GNC, 2026-10-13): the interface-facing values of the GNC rev1 set (response to REV-GNC-1), collected from
the result files so that the lead can fold them into gnc.json v3.1 without retyping. Every value is read from a result file
whose sha256/16 is recorded beside it; nothing here is a new computation. gnc.json v3 is NOT modified (review in progress).
Tags: SIM = 6-DOF Monte Carlo result; DERIVED = computed from sourced inputs; PROPOSAL = GNC proposal awaiting a lead decision;
DESIGN = adopted design value (LEAD decision cited).
Output: <out>/rev1_items.json"""
import hashlib
import json
import os

S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_ITEMS_OUT", f"{S}/rev1_items")
VERSION = "m2_rev1_items v1"


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def J(p):
    return json.load(open(p)), f"{p} (sha256/16 {sha16(p)})"


def main():
    os.makedirs(OUT, exist_ok=True)
    e7, e7s = J(f"{S}/eng07_6v6/eng07_6v6.json")
    st, sts = J(f"{S}/start_transient/start_transient.json")
    rr, rrs = J(f"{S}/release_rule/release_rule.json")
    fr, frs = J(f"{S}/fsw_record/fsw_config_record_v1.json")
    pb, pbs = J(f"{S}/purge_bleed/purge_bleed.json")
    rg, rgs = J(f"{S}/rg16_terms/rg16_fct_terms.json")
    ga, gas = J(f"{S}/rg11a_growth/rg11a_growth.json")
    gu, gus = J(f"{S}/gust_criterion/gust_criterion.json")
    cr, crs = J(f"{S}/cap_rule/cap_rule.json")
    lim = e7["EI_limit"]["v3.4.1 re-route|RR66"]
    limp = e7["EI_limit"]["v3.4.1 re-route|PR66"]
    pooled = e7["pooled"]
    items = dict(
        version=VERSION, date="2026-10-13", status="STAGED (rev1); gnc.json v3 unchanged while REV-GNC-1 runs",
        hose_stiffness_6V6=dict(
            tag="SIM", source=e7s,
            statement=("re-routed coil (CAD v3.4.1): pressurised hose EI <= 0.25 N m2, i.e. K_max <= 23.4 N m/rad (scalar at the "
                       "largest eigenvalue of the coupled K, including any other line across the gimbal), flown at the 6.6 V "
                       "degraded plug without a loss by the decision rule on both actuator methods; EI 0.5 (K 46.7) loses at 6.6 V "
                       "and at 7.4 V on both methods. The lead criterion K_max <= 17.2 N m/rad at 7.4 V is stricter and is "
                       "supported. B-FD-1 measures the pressurised EI: its upper bound must not exceed 0.25 N m2"),
            rule_method=dict(points=[(p["EI"], p["hose_K"], p["cmd_rate"], p["lost"], p["gained"], p["p_exact"]) for p in lim["points"]],
                             EI_largest_not_losing=lim["EI_largest_not_losing"], EI_smallest_losing=lim["EI_smallest_losing"]),
            physical_method=dict(points=[(p["EI"], p["hose_K"], p["lost"], p["gained"], p["p_exact"]) for p in limp["points"]],
                                 EI_largest_not_losing=limp["EI_largest_not_losing"], EI_smallest_losing=limp["EI_smallest_losing"]),
            supply_7V4_at_EI_0p5={k: {kk: pooled[k][kk] for kk in ("P_arm", "P_ref", "lost", "gained", "p_exact", "loses")}
                                  for k in ("RR74_EI05", "PR74_EI05") if k in pooled},
            point_format="(EI N m2, K N m/rad, [command slew deg/s,] lost, gained, p) pooled A1 + B1 62 m, 1000 paired runs"),
        drogue_release_rule=dict(
            tag="DESIGN (LEAD 2026-10-13) / SIM", sources=[rrs, sts, frs],
            rule=fr["release_rule_decided"]["rule"],
            fsw_values=dict(rel_Pc_Pa=3.0e5, rel_F_N=st["cases"]["A1_none|L400"]["rel_F_N"], rise_Pa=0.8e5,
                            rel_rise_Pc_Pa_abs=2.11325e5, rel_Frise_N=st["cases"]["A1_none|L400"]["rel_Frise_N"], rel_to_s=0.10),
            start_transient_pooled_vs_decided=st["pooled_vs_decided_rule"],
            persistence_branch_on_vs_off=st["persistence_branch_on_vs_off_L400"].get("pooled"),
            note=("plateau = Combustion fuel-starved start 2.4-3.6 bar abs for 0.1-0.4 s; no plateau arm loses P against the decided "
                  "rule without a plateau; the branch is P-neutral against waiting for 3.0 bar; its value is the bounded hold")),
        relight_planner=dict(
            tag="SIM", source=sts,
            statement="do NOT add the start plateau to the relight planning value: t_ign_est + 0.3 s LOSES (pooled)",
            evidence=st["pooled_vs_decided_rule"].get("L400_te")),
        purge_trigger_gate=dict(
            tag="PROPOSAL", source=pbs,
            finding=("prg_T 3.0 s: 6 of 500 runs start the purge 10.15-10.54 s into the flight at h 301-304 m (drogue deployment) "
                     "because the trigger extrapolates h and v over lag + prg_T + prg_lead with the measured acceleration (about "
                     "-g just after deployment); duration up to 13.9 s, purge mass up to 278 g; all 6 landed"),
            P30_duration_s=pb["arms"]["A1|P30"]["purge"]["duration_s"], P25_duration_s=pb["arms"]["A1|P25"]["purge"]["duration_s"],
            gate=("evaluate the extended purge trigger only once the drogue descent is quasi-steady (|a_z,est - a_drogue| small for "
                  "a hold time, or t >= t_drogue + settle), use constant velocity beyond the plain lag, and cap the purge duration "
                  "at prg_T + margin; to be flown before the purge sequence is frozen")),
        mass_budget_rg16=dict(
            tag="SIM / DERIVED", source=rgs,
            purge_booking_residual_bound_g=rg["combustion_purge"]["residual_bound_g"],
            offsets_kg=rg["offsets_kg"],
            held_max_N={k: v["held_max_N"] for k, v in rg["cases"].items()},
            misses_670N={k: v["stuck"]["670"]["misses"] for k, v in rg["cases"].items()},
            statement=("with the adopted estimator (rocket-equation Pc-lost rule + lever/direction compensation) every case keeps "
                       "the held maximum <= 593.9 N (margin >= 56 N to 650 N) and misses no 670 N stuck case; the stuck-open bleed "
                       "is a FAULT outside the nominal budget (no FSW model, no detector)")),
        growth_beyond_Jref_rg11a=dict(tag="SIM", source=gas, mc=ga.get("mc"),
                                      cap={k: v.get("cap_m") for k, v in ga["cases"].items() if "cap_m" in v}),
        launch_commit_proposal=dict(
            tag="PROPOSAL (site data TO-DEFINE)", source=gus,
            rule=f"W10 < {gu['W_lim_10m']} m/s AND sigma_u(3 m) <= {gu['S_lim_3m']} m/s",
            sensor="anemometer at 3.0 m above the pad (sonic or fast cup); W10 from the 3 m mean by the power law alpha 0.14 or a "
                   "10 m mast",
            averaging=("mean and standard deviation over the 10 min before ARM (LITERATURE convention for mean wind and turbulence "
                       "intensity, e.g. IEC 61400-1 10-min sigma); the 6-DOF imposes sigma_u as the Dryden intensity, so the "
                       "equivalence of the two is a model-form ASSUMPTION")),
        cap_rule_proposal=dict(tag="PROPOSAL", source=crs, rule=cr["method"].split("Pre-T1-T4")[0].strip()),
        fsw_record=dict(source=frs, bases={k: dict(fsw_sha16=v["fsw_sha16"], par_sha16_nominal=v["par_sha16_nominal"])
                                           for k, v in fr["bases"].items()}, sim6=fr["sources"]["sim6"], run6=fr["sources"]["run6"]))
    p = os.path.join(OUT, "rev1_items.json")
    with open(p, "w") as f:
        json.dump(items, f, indent=1, default=float)
    print("wrote", p, sha16(p))


if __name__ == "__main__":
    main()

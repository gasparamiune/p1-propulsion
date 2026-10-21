"""m2_fsw_record v1.3 (GNC, 2026-10-13): review REV-GNC-1 RG-13, a versioned and hashed record of the flight-software (FSW)
configuration flown in sim6 for each flight base of the rev1 set, so that each result can name the FSW it flew and a SIL/HIL
harness can compare the firmware configuration with it.
v1.2: the drogue release rule keys (sim6 amendment R: rel_mode, rel_F, rel_dt) are recorded as flown (the rev1 bases fly the
v2.8 model rel_mode 0; m2_release_rule v1.2 showed the adopted rule P-neutral, pooled -1/+2), a base with the adopted rule
(rel_mode 1) is added, and the LEAD decision of 2026-10-13 on the release rule is recorded with its parameters and its sim6
status in 'release_rule_decided' (the persistence branch is not a sim6 parameter yet: it is flown in the RG-01 start-transient
re-fly).
v1.3: sim6 amendment S implements the persistence branch (rel_to, rel_Frise are FSW keys now; rel_to 0 = branch off in every
earlier base, as flown); base A1_none_v28_liq0.81_decided added (rel_mode 1, rel_to 0.10 s: the decided rule, comparator of
m2_start_transient); the v1.2 record (sim6 7c2e87c138b9b140) is superseded (every fsw_sha16 changes with the two new keys and
every par_sha16 with the longer parameter vector).
v1.4: Electronics v2.9 handback (electronics.json v2 da067408c1594814): the decided release rule is mapped onto the ECU telemetry
(TLM_FAST 0x100 d1 = state in b0-b3, decoders mask d1 & 0x0F; b4 E2 of this start, b5 rise now, b6 rise held since E2, b7 rise
held to E2 + 0.10 s, latched) in 'release_rule_decided.fc_implementation'; the FC relight-planning source and key paths are
recorded in 'relight_planning_source' (the gnc.json v3 keys are nested under requirements.ignition.relight_planning_value_s and
were not removed); base A1_none_v28_liq0.81_decided_purgePS10 added (the pre-scheduled purge booked at 31.3 g/s, LEAD decision on
the handback, flown in m2_purge_cost v1). FSW_KEYS unchanged: every earlier fsw_sha16 and par_sha16 is unchanged.
v1.4 also: the LEAD decision that the hold bit is evaluated on the FILTERED channel only and Combustion's drogue_hold_check_v2p4
are cited in the release-rule mapping; stored v2.8 bases (A1_none, A1J_pc, rbl_B1_lead62_pc_k2) and an 'as_flown' table
(fsw_sha16 of run 0 of every relight-path study arm, built by the study's own code) are added. CORRECTION: the v1.3 note
that base A1_none_v28_liq0.81_decided is the comparator of m2_start_transient was wrong (that base carries the RG-16 flown
mass estimator; the start-transient, release-rule and purge-cost arms fly the stored v2.8 FSW, paired with comparators on
that same FSW); m2_purge_bleed flew the flown-mass-estimator FSW without fct_comp (base purge2.5 records fct_comp 1).

What is recorded per base:
  fsw         the FSW keys as built into the sim6 parameter vector by run6.build (v1.1: values taken from the vector the
              sim flies, so constants that run6 sets internally are included; keys without a sim6 parameter from the cfg) -
              the FSW keys of the run6 configuration (guidance, control, estimators, sequencing, detector thresholds and
              enables, purge sequence), as flown for run 0 of the seed-101 draws (the per-flight calibration inputs are
              marked: they are set at ARM from measured engine data, the rule is recorded, the run-0 value is an example)
  fsw_sha16   sha256 (first 16 hex) of the canonical JSON of 'fsw' (sorted keys, floats repr)
  par_sha16   sha256 of the full sim6 parameter vector of the nominal flight of the base (truth model + FSW), as built by
              run6.build (identifies the simulator state, not only the FSW)
  env         GNC_PC_RATCHET as seen by this process and the att_ref_mode it produced (the ratchet is set by
              os.environ.setdefault in the scripts: RG-13; the record makes the value explicit and checkable)
  sources     sha16 of sim6.py and run6.py
check(): recomputes fsw_sha16 for a configuration and compares it with the record (raises on a mismatch); scripts and the
SIL/HIL harness call it before a run. Excluded from 'fsw': truth error injections of the simulator (mest_w, mest_dq, mest_s1,
mest_s2, the dispersions, the fault and bleed truth models).
Output: <out>/fsw_config_record_v1.json"""
import hashlib
import json
import os
import sys
import numpy as np

S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_FSW_OUT", f"{S}/fsw_record")
os.environ.setdefault("GNC_PC_RATCHET", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import run6 as R, sim6 as s6  # noqa: E402
import m2_mass_est_v2 as MV  # noqa: E402
import m2_web_limit as WL  # noqa: E402
import m2_eng03_rate as E  # noqa: E402

VERSION = "m2_fsw_record v1.4"
ELEC = "/home/claude/work/shared-fallback/engine/interfaces/electronics.json"
GNC_V3 = "/home/claude/work/shared-fallback/engine/interfaces/gnc.json"
COMB_DH = "/home/claude/work/combustion/data/v2/v2p4/drogue_hold_check_v2p4.json"
FSW_KEYS = ("profile h_target Fmax floor tau slew deadb t_ign_est t_rise t_off kd ht vt kv hslam hcut hover_k hs_margin k_est "
            "k_est_tau k_est_asc floor_comp_min att_wn att_zeta att_ki att_wn_asc tilt_max_land tilt_max_asc tilt_term "
            "tilt_term_hi lat_mode lat_wn lat_zeta vert_mode div_margin t_hmin dff dff_tau gim_lpf_w gim_lpf_z gim_cmd_rate "
            "gim_cmd_acc gim_aw_thr gim_aw_tau gim_notch_f gim_notch_q gim_notch_db gim_notch_track att_ref_rate att_ref_win "
            "att_ref_rate2 att_ref_mode roll_comp_tau kt_lat t_hand toff_model meco_td meco_td_max meco_td_hold relight_start "
            "thr_ff_rise mest_mode mest_kcal mest_ghat mest_jref mest_pcl_t mest_pcl_re mest_tau kest_comp web_on web_lim "
            "web_kf web_nf1 web_nf2 web_kcal web_ghat web_jref web_act bpred_pc det_fct det_op det_pf det_geo fct_thr fct_n "
            "fct_tau fct_hz fct_comp det_op_Pabs det_op_t det_pf_t det_pf_err_m geo_dh prg_on prg_T prg_lead prg_mdot_hat "
            "prg_book prg_prio rel_mode rel_F rel_dt rel_to rel_Frise").split()
RELEASE_RULE = dict(
    rule="release the drogue at E2 AND [measured Pc >= 3.0 bar abs OR the >= 0.8 bar rise held continuously until E2 + 0.10 s]",
    E2="relative light confirmation: Pc rise >= 0.8 bar above the pre-lift baseline, held 10 ms (Combustion ignition_detect_v2p4: "
       "E2 14.0-15.5 ms after main ignition)",
    Pc_abs_floor_Pa=3.0e5, rise_Pa=0.8e5, rise_hold_s=0.010, persistence_timeout_s=0.10, worst_case_hold_after_E2_s=0.10,
    decided="LEAD 2026-10-13: GNC proposal (b) with the persistence check; a fixed absolute floor alone (proposal (a)) cannot "
            "separate lit from unlit at the +/-0.6 bar residual",
    evidence="m2_release_rule v1.2 (release_rule.json): release held after the light 0 / 100 / 200 / 400 ms -> pooled A1_none + "
             "A1J_pc lost/gained -1/+2, -4/+4, -11/+5 (p 0.21), -21/+6 (p 0.0059); the worst-case hold of this rule (0.10 s) is "
             "the P-neutral 100 ms bracket",
    sim6_status="amendment R implements 'E2 AND Pc >= 3.0 bar abs' (rel_mode 1; rel_F = map thrust at 3.0 bar abs, run6 "
                "DERIVED 37.2 N; rel_dt = E2 after the 6-DOF light). Amendment S implements the persistence branch: rel_to 0.10 s, "
                "rise evaluated as the Pc-equivalent thrust >= rel_Frise = map thrust at baseline + 0.8 bar = 2.113 bar abs "
                "(ISA 1.013 bar ASSUMED + torch 0.3 bar B-PC-1 target, upper) = 22.9 N; one step below it after E2 loses the "
                "branch. m2_bitcheck_v28 v1.5 part S: with the v2.8 thrust ramp the branch never acts (S1: 1000 runs, 0 "
                "persistence releases, every stored rel1 value reproduced); with a plateau below 3.0 bar it releases at E2 + "
                "0.10 s (S2); a plateau above 3.0 bar releases on Pc (S3); a plateau below the rise threshold loses the branch "
                "(S4). Flown with the plateau in m2_start_transient v1 (RG-01 start-transient re-fly)",
    flown_in_rev1="rel_mode 0 (v2.8 model: truth F > 0.5 floor) in every rev1 base except the m2_release_rule arms (rel_mode 1, "
                  "rel_to 0), the m2_start_transient arms (rel_mode 1, rel_to 0.10 except arm L400_nto) and the m2_purge_cost "
                  "arms (rel_mode 1, rel_to 0.10)",
    fc_implementation=dict(
        tag="DESIGN (GNC mapping of the LEAD rule onto the Electronics v2.9 telemetry; firmware v2.9 SIL only, not flown in "
            "hardware)",
        frame=("TLM_FAST CAN 0x100 ECU->FC, 500 Hz, len 8: d0 seq; d1 = state in b0-b3 (EVERY FC decoder masks d1 & 0x0F; the "
               "unmasked byte is no longer the state) + flags b4 E2 of this start, b5 rise now (firmware v2.9: filtered AND "
               "raw >= P0 + 0.8 bar), b6 rise held since E2 (cleared at the first tick without it, stays clear for the start), "
               "b7 rise held to E2 + kDrogueRiseHold_s 0.10 s (latched); d2-d3 Pc u16 kPa abs (0xFFFF = invalid, RG-15); d4-d5 "
               "pintle lift; d6-d7 fault bits incl. PC_SENSOR. LEAD 2026-10-13 (CHANGELOG, after the Combustion drogue-hold "
               "check): the hold (b6/b7) is evaluated on the FILTERED channel only, E2 keeps filtered AND raw; to be "
               "implemented when Electronics resumes (firmware v2.9 still uses filtered AND raw for the hold)"),
        predicate=("while the drogue is attached in the A relight, on each new TLM_FAST frame (sequence advanced): RELEASE iff "
                   "b4 AND [(d2-d3 != 0xFFFF AND d2-d3 >= 300 kPa abs) OR b7]; b5 and b6 are logged, not used; the decision is "
                   "latched (one release command, never re-attached)"),
        e2_source="b4 is set in the frame of the RUN entry; the E2 time is EVENT 0x120 STATE (RUN entry) t_ms",
        sil_evidence=("Electronics SIL A1 relight (firmware v2.9, N 273 lit): rise held to E2 + 0.10 s in 273/273; E2 -> Pc "
                      "3.0 bar abs p50/p95/max 3/34/43 ms; E2 16-18 ms after the light (LEAD 2026-10-13: accepted); the SIL "
                      "plant has no fuel-starved plateau"),
        sim6_equivalence=("sim6 rel_mode 1 + rel_to 0.10: E2 at the 6-DOF light (rel_dt 0), i.e. 16-18 ms EARLIER than the "
                          "firmware; release bracket: +100 ms pooled -4/+4, +200 ms -11/+5 (p 0.21), +400 ms -21/+6 (p 0.0059) -> "
                          "the 16-18 ms offset is inside the P-neutral bracket. Rise in sim6 = truth Pc-equivalent thrust >= "
                          "rel_Frise (P0 = 1.313 bar abs ASSUMED); in firmware v2.9 the hold uses filtered AND raw over the "
                          "measured P0, so roughness or a dip clears b6/b7 and the release falls back on the 3.0 bar branch "
                          "(the LEAD filtered-only decision removes the raw-channel path); that direction is bounded by arm "
                          "L400_nto (branch off; pooled -13/+6 p 0.167 vs the decided rule without plateau; branch on vs off "
                          "-10/+12 p 0.832). Combustion drogue_hold_check_v2p4 (70820e0038be39a7, SIM quasi-steady, 288 lit "
                          "corners): rise >= 0.8 bar held from E2 to E2 + 0.10 s on every lit corner, min margin 0.74 bar "
                          "(0.48 bar with the torch +0.3 bar in the baseline only); no unlit case reaches 0.8 bar (max 0.51); "
                          "worst corner (fuel-starved A1 relight) Pc 2.60-2.62 bar abs, between the flown plateau arms L "
                          "(2.4 bar) and M (2.9 bar), neither of which loses; roughness tolerance 0.48 bar zero-to-peak, "
                          "unmeasured until IGN-1/T1"),
        open_item=("Pc channel invalid inside [E2, release] (window <= 43 ms in SIL, up to 0.10 s on a plateau): neither "
                   "branch can complete and the drogue stays attached while the engine runs; the decided rule does not define "
                   "this case and sim6 has no Pc-invalid model in the release logic -> fault arm required (RG-15 extension); "
                   "no value is proposed here")))
RELIGHT_PLANNING = dict(
    tag="REQ (LEAD decisions 2026-10-13) / DESIGN (Electronics v2.9 telemetry)",
    keys_in_gnc_v3=dict(
        planning_value_s="requirements.ignition.relight_planning_value_s.v = 0.81 s",
        unprimed_plan_s="requirements.ignition.relight_planning_value_s.option_c_unprimed_s.v = 1.41 s (option (c) PROVISIONAL)",
        stale_or_missing_rule="requirements.ignition.relight_planning_value_s.stale_or_missing_flag.v",
        mirrors=["relight_planning_v28.v.planning_value_s", "relight_planning_v28.v.planning_value_fault_path_s",
                 "relight_planning_v28.v.option_c_fault_aware_plan.stale_or_missing_flag",
                 "flight_profile.mission_plan_v3.v.A1.relight_v2.8.{planning_value_s, planning_value_unprimed_s, "
                 "stale_or_missing_flag}"]),
    finding=("the keys were NOT removed from gnc.json v3: they are nested one level below requirements.ignition (as published "
             "in CHANGELOG line 98); the Electronics generator calc/make_interface_json_v2.py looks them up at "
             "requirements.ignition.option_c_unprimed_s / .stale_or_missing_flag (one level too high) and therefore reports "
             "OI-GNC-V3; the same nested keys are carried in the v3.1 staging set; no key is renamed in v3.1"),
    ecu_input=("TLM_RELIGHT CAN 0x102 ECU->FC, 50 Hz in every state: d2 flags PRIMED b0 (= DIRECT_PATH; NOT a vapour "
               "detector), VALID b1, READY b2, LOCKOUT b3, S1_FAULT b4, STAND b5, POST_ABORT b6, UNKNOWN b7; states NONE "
               "(VALID 0), PRIMED, UNPRIMED, UNKNOWN"),
    fc_mapping=("frame fresh (age <= 0.3 s ASSUMED, 15 frames at 50 Hz) with CRC and sequence valid and VALID = 1: PRIMED -> "
                "0.81 s; PRIMED = 0 -> 1.41 s; VALID = 0 or no fresh frame -> the gnc.json v3 stale_or_missing_flag rule (hold "
                "the last valid flag since the MECO valve closure; none -> 0.81 s); evaluated every frame, latched at T_fire"),
    proposal_unknown_state=("PROPOSAL (GNC, not flown): UNKNOWN (b7) -> 1.41 s, because the ECU takes the prep path in that "
                            "state (electronics.json v2 relight_interface.fault_path: 'prep (P_feed invalid, UNKNOWN)', command "
                            "-> E2 0.90-0.98 s on the 13.5/19.0 cm3 slugs); Electronics to confirm the path; LEAD decision"),
    purge=("pre-scheduled purge (LEAD 2026-10-13): ends before T_fire, so the plan stays 0.81 s on the direct path (Electronics "
           "SIL: command -> E2 0.19 s after a pre-scheduled purge); its N2O cost is flown in m2_purge_cost v1"))
PER_FLIGHT = dict(mest_kcal="1 / measured isp_scale from T1-T4 flow calibration (run-0 value includes the calibration error)",
                  web_kf="1.1 x a_meas (lead rule, burn limit at t(web = 1 mm))", web_nf1="n_meas - 0.05",
                  web_nf2="n_meas + 0.05", web_kcal="flow calibration as mest_kcal", mest_jref="nominal-flight J of the cycle",
                  web_jref="nominal-flight J of the cycle")


def sha16_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def canon(v):
    if isinstance(v, (bool, np.bool_)):
        return bool(v)
    if isinstance(v, (int, np.integer)):
        return int(v)
    if isinstance(v, (float, np.floating)):
        return float(v)
    if v is None or isinstance(v, str):
        return v
    if isinstance(v, (list, tuple, np.ndarray)):
        return [canon(x) for x in v]
    if isinstance(v, dict):
        return {str(k): canon(x) for k, x in sorted(v.items())}
    return str(v)


PIDX = {n: i for i, n in enumerate(s6.PAR_NAMES)}


def fsw_of(c, disp=None):
    """FSW values from the sim6 parameter vector built for (c, disp); cfg-only keys from c."""
    par = R.build(c, disp if disp is not None else dict(R.DISP))[0]
    f = {k: canon(par[PIDX[k]]) for k in FSW_KEYS if k in PIDX}
    f.update({k: canon(c[k]) for k in FSW_KEYS if k not in PIDX and k in c})
    return f, hashlib.sha256(json.dumps(f, sort_keys=True).encode()).hexdigest()[:16]


def stored_cfg(b):
    """v1.4: the stored v2.8 base as the E.base_ref studies build it (m2_release_rule.cfg_of, m2_start_transient.cfg_of)."""
    over, csvp, bj = E.base_ref(b)
    m = json.load(open(bj))["m_n2o_mc_kg"]
    return R.cfg_of(**dict({k: v for k, v in over.items() if k != "m_fixed"}, m_n2o=float(m))), csvp


def as_flown(rec_bases):
    """v1.4 (RG-13): the FSW each relight-path study arm flew (run 0 of the seed-101 draws), built by the study's own
    configuration code, with the keys that differ from the named record base (per-flight inputs included in the diff)."""
    import m2_release_rule as RL
    import m2_start_transient as ST
    import m2_purge_cost as PC
    import m2_purge_bleed as PB
    out = {}

    def put(study, arm, base, ref, c, disp):
        f, h = fsw_of(c, disp)
        rf = rec_bases[ref]["fsw"]
        out[f"{study}|{base}|{arm}"] = dict(fsw_sha16=h, record_base=ref,
                                            differs_from_record_base={k: [rf.get(k), f.get(k)] for k in sorted(set(rf) | set(f))
                                                                      if rf.get(k) != f.get(k)})
    for base in ("A1_none", "A1J_pc"):
        ref = f"{base}_v28_stored"
        cfg, _ = RL.cfg_of(base)
        D = R.draw(np.random.default_rng(101), 500, cfg)
        for arm, spec in RL.ARMS.items():
            c, disp = R.run_cfg(cfg, D[0])
            c.update({k: v for k, v in spec.items() if not k.startswith("_")})
            put("m2_release_rule", arm, base, ref, c, disp)
        for arm, spec in ST.ARMS.items():
            cfg_t, _ = ST.cfg_of(base, spec.get("_te", 0.0))
            c, disp = R.run_cfg(cfg_t, R.draw(np.random.default_rng(101), 500, cfg_t)[0])
            c.update({k: v for k, v in spec.items() if not k.startswith("_")})
            put("m2_start_transient", arm, base, ref, c, disp)
        for arm, spec in PC.ARMS.items():
            c, disp = R.run_cfg(cfg, D[0])
            c.update(spec)
            put("m2_purge_cost", arm, base, ref, c, disp)
    spec = MV.case_specs()["tot_cal_comp"]
    jr = json.load(open(f"{S}/throat_growth/throat_growth.json"))["j_ref"]
    for name, arm in PB.ARMS.items():
        prof = name.split("|")[0]
        MV.TG_JREF_DEFAULT = float(jr[prof])       # as m2_purge_bleed.part_mc sets it per arm
        cfg, D, Z = PB.base(prof)
        c, disp = MV.run_cfg_case(cfg, D[0], spec, 0, "base")
        if prof == "B1":
            c.update(WL.web_over(D[0], Z[0], WL.CASES["W1p"], float(cfg.get("throat_jref") or 0.0))[0])
        c.update({k: v for k, v in arm.items() if not k.startswith("_")})
        put("m2_purge_bleed", name.split("|")[1], prof, "A1_none_v28_liq0.81" if prof == "A1" else "B1_62m_W1p", c, disp)
    return out


def bases():
    """name -> (c run 0, cfg for the nominal PAR vector, note)."""
    out = {}
    D101 = {}

    def draws(key, cfg):
        if key not in D101:
            D101[key] = R.draw(np.random.default_rng(101), 500, cfg)
        return D101[key]

    MV.COMB = MV.comb_draws(500)
    spec = MV.case_specs()["tot_cal_comp"]
    jr = json.load(open(f"{S}/throat_growth/throat_growth.json"))["j_ref"]
    # A1 (relight NOT CLOSED: the plan 0.81 s is not frozen, RG-01)
    MV.TG_JREF_DEFAULT = float(jr["A1"])
    cA = MV.base_cfg("A1_none")
    c0, d0 = MV.run_cfg_case(cA, draws("A1", cA)[0], spec, 0, "base")
    out["A1_none_v28_liq0.81"] = (dict(c0, fct_comp=1), d0, cA, "A1 v2.8 liquid plan 0.81 s (NOT FROZEN, RG-01), flown mass "
                                                         "estimator tot_cal_comp, FC_THRUST compensated")
    c1 = dict(c0, fct_comp=1, prg_on=1, prg_T=2.5, prg_lead=0.5, prg_mdot_hat=0.0200, prg_book=1, prg_prio=1)
    out["A1_none_v28_liq0.81_purge2.5"] = (c1, d0, cA, "as A1_none_v28_liq0.81 with the RG-01 forced purge (amendment P, "
                                                   "prg_prio 1 PROPOSAL)")
    out["A1_none_v28_liq0.81_rel1"] = (dict(c0, fct_comp=1, rel_mode=1), d0, cA,
                                       "as A1_none_v28_liq0.81 with the adopted drogue release rule, sim6 part (amendment R "
                                       "rel_mode 1: E2 AND Pc >= 3.0 bar abs, persistence branch off as flown in "
                                       "m2_release_rule)")
    out["A1_none_v28_liq0.81_decided"] = (dict(c0, fct_comp=1, rel_mode=1, rel_to=0.10), d0, cA,
                                          "as A1_none_v28_liq0.81 with the DECIDED drogue release rule (LEAD 2026-10-13): "
                                          "amendment R rel_mode 1 + amendment S persistence branch rel_to 0.10 s, on the RG-16 "
                                          "flown-mass-estimator FSW. v1.4: NOT the FSW flown by m2_start_transient / "
                                          "m2_release_rule / m2_purge_cost (those fly the stored v2.8 FSW, see "
                                          "A1_none_v28_stored and 'as_flown'); the v1.3 note calling it the start-transient "
                                          "comparator was wrong")
    # v1.4: the stored v2.8 FSW (E.base_ref), flown by m2_release_rule, m2_start_transient, m2_purge_cost, m2_eng07_6v6,
    # m2_cap_rule and m2_gust_criterion
    for nm, b in (("A1_none_v28_stored", "A1_none"), ("A1J_pc_v28_stored", "A1J_pc"),
                  ("rbl_B1_lead62_pc_k2_v28_stored", "rbl_B1_lead62_pc_k2")):
        cs, _ = stored_cfg(b)
        c_, d_ = R.run_cfg(cs, draws(nm, cs)[0])
        out[nm] = (c_, d_, cs, f"stored v2.8 base {b} (m2_eng03_rate.base_ref): FSW as flown by the comparators and arms of "
                               f"the release, start-transient, purge-cost, ENG-07, cap and gust studies (run 0 of seed 101)")
    # B1 62 m flight FSW (burn limit action 1 + Pc-based apex predictor)
    MV.TG_JREF_DEFAULT = float(jr["B1"])
    cfgB, _, _, _ = WL.base_cfg()
    DB = draws("B1", cfgB)
    Z = WL.meas_draws(500)
    cB, dB = MV.run_cfg_case(cfgB, DB[0], spec, 0, "base")
    cB.update(WL.web_over(DB[0], Z[0], WL.CASES["W1p"], float(cfgB.get("throat_jref") or 0.0))[0])
    out["B1_62m_W1p"] = (dict(cB, fct_comp=1), dB, cfgB, "B1 62 m, regression band and growth, burn limit action 1, Pc-based apex "
                                                     "predictor (m2_web_limit W1p), flown mass estimator tot_cal_comp")
    return out


def relight_keys_check():
    """v1.4: read the relight-planning keys from gnc.json v3 and the v3.1 staging set (read-only) and from electronics.json v2;
    report where they are and the value at each path (the record states what the files hold, not what a note says)."""
    STG = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/gnc_v3.1_staging.json"
    GEN = "/home/claude/work/electronics/calc/make_interface_json_v2.py"
    out = {}
    for tag_, p in (("gnc_v3", GNC_V3), ("gnc_v3.1_staging", STG)):
        if not os.path.exists(p):
            out[tag_] = dict(path=p, present=False)
            continue
        ig = json.load(open(p))["requirements"]["ignition"]
        rp = ig["relight_planning_value_s"]
        out[tag_] = dict(path=f"{p} (sha256/16 {sha16_file(p)})",
                         nested=dict(planning_value_s=rp.get("v"),
                                     option_c_unprimed_s=(rp.get("option_c_unprimed_s") or {}).get("v"),
                                     stale_or_missing_flag_present=isinstance(rp.get("stale_or_missing_flag"), dict)),
                         flat_keys_present=dict(option_c_unprimed_s="option_c_unprimed_s" in ig,
                                                stale_or_missing_flag="stale_or_missing_flag" in ig))
    if os.path.exists(ELEC):
        e = json.load(open(ELEC))
        out["electronics_json"] = dict(path=f"{ELEC} (sha256/16 {sha16_file(ELEC)})",
                                       fc_planning_from_gnc=e.get("relight_interface", {}).get("fc_planning_from_gnc"))
    if os.path.exists(GEN):
        ln = [i + 1 for i, s in enumerate(open(GEN).read().splitlines()) if "ign.get('option_c_unprimed_s')" in s]
        out["electronics_generator"] = dict(path=f"{GEN} (sha256/16 {sha16_file(GEN)}, read-only)", lookup_lines=ln,
                                            lookup="requirements.ignition.option_c_unprimed_s (one level above the published key)")
    return out


def part_record():
    os.makedirs(OUT, exist_ok=True)
    rr = json.loads(json.dumps(RELEASE_RULE))
    rr["fc_implementation"]["sources"] = dict(
        electronics_json=f"{ELEC} (sha256/16 {sha16_file(ELEC)})" if os.path.exists(ELEC) else "absent",
        lead="interfaces/CHANGELOG.md 2026-10-13 lead decisions on the release rule, on the Electronics handback "
             "((4) E2 latency accepted, (6) d1 mask) and on the filtered-only hold bit",
        combustion_drogue_hold=(f"{COMB_DH} (sha256/16 {sha16_file(COMB_DH)}, read-only)" if os.path.exists(COMB_DH)
                                else "absent"))
    rp = dict(RELIGHT_PLANNING, files=relight_keys_check())
    rec = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, method=__doc__.split("\n\n")[1].strip(),
               sources=dict(sim6=sha16_file(s6.__file__), run6=sha16_file(R.__file__)),
               env=dict(GNC_PC_RATCHET=os.environ.get("GNC_PC_RATCHET")), per_flight_inputs=PER_FLIGHT,
               release_rule_decided=rr, relight_planning_source=rp, bases={})
    for name, (c, disp, cfg, note) in bases().items():
        f, h = fsw_of(c, disp)
        par = R.build(dict(cfg, noise=False, wind=0.0, gust=False), dict(R.DISP))[0]
        missing = [k for k in FSW_KEYS if k not in f]
        rec["bases"][name] = dict(note=note, fsw=f, fsw_sha16=h, keys_not_in_cfg=missing,
                                  par_sha16_nominal=hashlib.sha256(np.asarray(par, dtype=np.float64).tobytes()).hexdigest()[:16],
                                  att_ref_mode=f.get("att_ref_mode"))
        print(f"{name:32s} fsw {h} par {rec['bases'][name]['par_sha16_nominal']} att_ref_mode {f.get('att_ref_mode')} "
              f"k_est_asc {f.get('k_est_asc')} bpred_pc {f.get('bpred_pc')} web_act {f.get('web_act')} fct_thr {f.get('fct_thr')} "
              f"prg_on {f.get('prg_on')} rel_mode {f.get('rel_mode')} rel_F {f.get('rel_F')} | not in cfg {len(missing)}", flush=True)
    rec["as_flown"] = as_flown(rec["bases"])
    rec["as_flown_note"] = ("v1.4: FSW of run 0 of each relight-path study arm, built by the study's own code; the release, "
                            "start-transient and purge-cost arms fly the stored v2.8 FSW (mest_mode 0, kest_comp 0, fct_comp 0) "
                            "and are paired with comparators on that same FSW; m2_purge_bleed flies the flown-mass-estimator "
                            "FSW without fct_comp. Studies not listed here name their base in their own script docstring")
    for k, v in rec["as_flown"].items():
        print(f"as_flown {k:42s} fsw {v['fsw_sha16']} vs {v['record_base']}: {sorted(v['differs_from_record_base'])}", flush=True)
    p = os.path.join(OUT, "fsw_config_record_v1.json")
    with open(p, "w") as fo:
        json.dump(rec, fo, indent=1)
    print("written", p, sha16_file(p))


def check(c, base, disp=None, path=os.path.join(OUT, "fsw_config_record_v1.json")):
    """Raise if the FSW part of configuration c differs from the recorded base (per-flight inputs excluded)."""
    rec = json.load(open(path))["bases"][base]["fsw"]
    f, _ = fsw_of(c, disp)
    diff = {k: (rec.get(k), f.get(k)) for k in set(rec) | set(f) if k not in PER_FLIGHT and rec.get(k) != f.get(k)}
    if diff:
        raise RuntimeError(f"FSW configuration differs from record {base}: {diff}")
    return True


if __name__ == "__main__":
    part_record()

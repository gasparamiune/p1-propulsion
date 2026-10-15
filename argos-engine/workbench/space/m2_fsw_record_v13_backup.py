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

VERSION = "m2_fsw_record v1.3"
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
                  "rel_to 0) and the m2_start_transient arms (rel_mode 1, rel_to 0.10 except arm L400_nto)")
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
                                          "amendment R rel_mode 1 + amendment S persistence branch rel_to 0.10 s")
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


def part_record():
    os.makedirs(OUT, exist_ok=True)
    rec = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, method=__doc__.split("\n\n")[1].strip(),
               sources=dict(sim6=sha16_file(s6.__file__), run6=sha16_file(R.__file__)),
               env=dict(GNC_PC_RATCHET=os.environ.get("GNC_PC_RATCHET")), per_flight_inputs=PER_FLIGHT,
               release_rule_decided=RELEASE_RULE, bases={})
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

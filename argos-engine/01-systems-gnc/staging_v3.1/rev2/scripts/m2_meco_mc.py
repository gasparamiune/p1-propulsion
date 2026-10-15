"""MECO throttle-down, lift-ramp tail-off and relight start-level study (lead decisions 2026-10-12 on the MKS HV69
pintle drive, ~0.25 s full stroke). Same 500 draws (seed 101) as every other case.
  toff_model 1  : shutdown on Combustion's lift-thrust table at the HV69 closing speed (gncsim.tailoff, fitted lags)
  meco_td x     : guidance commands x F_max before MECO; MECO when the predicted apogee (tail-off from the current
                  level) reaches the target and the measured thrust is <= meco_td_max (0.75) F_max
  relight_start : relight start level held until 90 % of it, then guidance throttles (0 = start at the floor)
  t_ign_add     : shift of the MC start-delay draw U(0.2, 0.6) s (torch-delay / floor-start stress)
  t_ign_est     : relight planning value (latest start delay the guidance plans on; default 0.6 s)
v2: NC-closed relight cases (lead 2026-10-12): sequence times from combustion.json (nc_sequence).
v2.1: case mr_td72_nc_ecu with the ECU firmware PREPRESS duration read from Electronics config.h (ecu_prepress).
v2.2: cases *_rat with the reference-governor ratchet (att_ref_mode 1).
Env: GNC_MR_CASES (comma list), GNC_OUT (default out/meco), GNC_SUFFIX (default mr)."""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("GNC_OUT", "/home/claude/work/space/out/meco")
os.environ.setdefault("GNC_SUFFIX", "mr")
import m2_mc6 as M  # noqa: E402
from gncsim import run6 as R, sim6 as s6  # noqa: E402


def nc_sequence():
    """v2 (lead 2026-10-12 22:18Z): relight with the NC isolation valve closed through the MECO coast (until B-PNT-1 shows
    the pintle seat is leak-tight). Sequence times read from combustion.json (igniter.sequence, speed_checks at the
    0.25 s stroke): 'slots' = the published unprimed-line timeline before the torch (first step t_s < 0: bleed lift
    0.10 mm, isolation-valve ramp >= 0.3 s, pintle back to seat, vapour-first), 'min' = valve ramp (the primed-line step
    before the torch) + bleed-lift travel + return to seat. Both are added on top of the start-delay draw (t_ign_add)
    and to the relight planning value (t_ign_est), unless stated."""
    comb = R.sources()["comb"]
    st = comb["igniter"]["sequence"]["v"]["start"]
    # rev2 (2026-10-13): combustion.json v2.4 rewrote igniter.sequence.start (PURGE at E0 - 2.9 s, a step with t_s None):
    # skip steps without a time; under v2.4 'slots' is the purge lead, NOT the v2.3 unprimed-line timeline. The rev2 RG-01
    # re-fly does not use NCS (it sets t_ign_add / t_ign_est itself); legacy NCS arms are not re-run on v2.4.
    pre = sorted(float(x["t_s"]) for x in st if x.get("t_s") is not None and float(x["t_s"]) < 0.0)
    sc = comb["valves_and_actuators"]["pintle_actuator"]["speed_checks"]["v"]["start_rule"]["v"]["0.250"]
    return dict(slots=-pre[0], min=-pre[-1] + sc["bleed_lift_0p10mm_s"] + sc["return_to_seat_s"],
                comb_version=str(comb.get("version")), meaning=("v2.3 unprimed-line timeline" if str(comb.get("version")) == "v2.3"
                                                                else "NOT the v2.3 meaning (sequence rewritten); unused in rev2"),
                source="combustion.json igniter.sequence.start + valves_and_actuators.pintle_actuator.speed_checks (0.25 s)")


def ecu_prepress(path=os.environ.get("GNC_FW_CONFIG", "/home/claude/work/electronics/firmware/src/core/config.h")):
    """v2.1: duration of the ECU firmware PREPRESS state before the torch (IGNITION entry) on a relight with the NC valve
    closed through the coast, read from Electronics' config.h (read-only): unprimed line = bleed settle + opener ramp +
    cock hold; primed = opener ramp + cock hold (the feed-primed and chamber-vented waits after that are not bounded
    below the PREPRESS timeouts). Returns None if the file or a constant is missing."""
    import hashlib
    import re
    try:
        txt = open(path).read()
    except OSError:
        return None
    def c(name):
        m = re.search(r"constexpr\s+float\s+" + name + r"\s*=\s*([0-9.eE+-]+)f?;", txt)
        return float(m.group(1)) if m else None
    v = {k: c(k) for k in ("kBleedSettle_s", "kMvOpenRampSlow_s", "kMvCockHold_s", "kPrepressTimeout_s")}
    if any(x is None for x in v.values()):
        return None
    return dict(v, unprimed_s=v["kBleedSettle_s"] + v["kMvOpenRampSlow_s"] + v["kMvCockHold_s"],
                primed_s=v["kMvOpenRampSlow_s"] + v["kMvCockHold_s"], path=path,
                sha256=hashlib.sha256(txt.encode()).hexdigest())


NCS = nc_sequence()
ECU = ecu_prepress()
T_EST0 = R.DEF["t_ign_est"]

PROV = dict(M.BASE, rcs=False, m_fixed=2.00)
FIX = dict(gim_cmd_acc=2000.0, att_ref_rate=40.0)
TD = dict(toff_model=1, meco_td=0.72)
ACT = dict(act_model=1, servo_V=6.6, act_n=4.8, supply_chain=M.ACT_CHAINS["D"], supply_Vrest=None)
CASES = {
    "AD_prov_2kg": (dict(PROV), "LEAD BASELINE (v2.5 shutdown: first-order 35 ms, MECO from 100 %)"),
    "mr_toff": (dict(PROV, toff_model=1), "lift-ramp tail-off (HV69 0.25 s), MECO from 100 % (fails ENG-05 by design)"),
    "mr_td72": (dict(PROV, **TD), "lift-ramp tail-off + pre-MECO throttle-down 72 % (gate 75 %)"),
    "mr_td70": (dict(PROV, toff_model=1, meco_td=0.70), "lift-ramp tail-off + pre-MECO throttle-down 70 %"),
    "mr_td72_fix": (dict(PROV, **TD, **FIX), "td72 + control fix acc2000_ref40"),
    "mr_td72_fix_rs20": (dict(PROV, **TD, **FIX, relight_start=0.20), "td72 + fix + relight start rule 20 % (= floor)"),
    "mr_td72_tign10": (dict(PROV, **TD, t_ign_add=0.10), "td72, start delay U(0.3, 0.7) s"),
    "mr_td72_tign20": (dict(PROV, **TD, t_ign_add=0.20), "td72, start delay U(0.4, 0.8) s"),
    "mr_td72_tign30": (dict(PROV, **TD, t_ign_add=0.30), "td72, start delay U(0.5, 0.9) s"),
    "mr_f125": (dict(PROV, floor=0.125), "12.5 % floor, v2.5 shutdown, start at the floor (sim start model)"),
    "mr_f125_td72_floorstart": (dict(PROV, floor=0.125, **TD, t_ign_add=0.09),
                                "12.5 % floor, td72, start at the floor with Combustion's +0.09 s (t90 0.523 vs 0.433 s)"),
    "mr_f125_td72_rs20": (dict(PROV, floor=0.125, **TD, relight_start=0.20),
                          "12.5 % floor, td72, relight rule: start at 20 %, hold to 90 %, then throttle"),
    "mr_J2.7_fix": (dict(PROV, **ACT, act_Jint=2.7e-3, **FIX), "n 4.8, 6.6 V, J_int 2.7e-3, fix (v2.5 shutdown)"),
    "mr_J2.7_fix_td72": (dict(PROV, **ACT, act_Jint=2.7e-3, **FIX, **TD, relight_start=0.20),
                         "n 4.8, 6.6 V, J_int 2.7e-3, fix + td72 + relight rule (full v2.6 FSW)"),
    "mr_J1.6_fix_td72": (dict(PROV, **ACT, act_Jint=1.6e-3, **FIX, **TD, relight_start=0.20),
                         "n 4.8, 6.6 V, J_int 1.6e-3 (Electronics central), full v2.6 FSW"),
    "mr_fins_f20_td72_fix": (dict(M.BASE, **TD, **FIX, relight_start=0.20), "RCS-fitted baseline (sized load), full v2.6 FSW"),
    "mr_fins_f20": (dict(M.BASE), "RCS-fitted baseline (sized load), v2.5"),
    # NC valve closed through the coast (lead 2026-10-12): sequence time added to the start delay and to the planning value
    "mr_td72_ncmin": (dict(PROV, **TD, t_ign_add=NCS["min"], t_ign_est=T_EST0 + NCS["min"]),
                      f"td72, NC-closed relight, minimum sequence +{NCS['min']:.3f} s (valve ramp + bleed lift + reseat), planned"),
    "mr_td72_nc": (dict(PROV, **TD, t_ign_add=NCS["slots"], t_ign_est=T_EST0 + NCS["slots"]),
                   f"td72, NC-closed relight, Combustion's unprimed timeline +{NCS['slots']:.2f} s, planned"),
    "mr_td72_nc_unplanned": (dict(PROV, **TD, t_ign_add=NCS["slots"]),
                             f"td72, NC-closed relight +{NCS['slots']:.2f} s, planning value NOT updated (evidence)"),
    "mr_td72_nc_m10": (dict(PROV, **TD, t_ign_add=NCS["slots"] + 0.10, t_ign_est=T_EST0 + NCS["slots"]),
                       "td72, NC-closed timeline planned, +0.10 s unplanned extra delay (margin probe)"),
    "mr_td72_nc_m20": (dict(PROV, **TD, t_ign_add=NCS["slots"] + 0.20, t_ign_est=T_EST0 + NCS["slots"]),
                       "td72, NC-closed timeline planned, +0.20 s unplanned extra delay (margin probe)"),
    "mr_td72_nc_m30": (dict(PROV, **TD, t_ign_add=NCS["slots"] + 0.30, t_ign_est=T_EST0 + NCS["slots"]),
                       "td72, NC-closed timeline planned, +0.30 s unplanned extra delay (margin probe)"),
    "mr_fsw_J1.6": (dict(PROV, **ACT, act_Jint=1.6e-3, **FIX, **TD, relight_start=0.20),
                    "full v2.6 FSW, n 4.8, 6.6 V, J 1.6e-3 (= mr_J1.6_fix_td72)"),
    "mr_fsw_J1.6_nc": (dict(PROV, **ACT, act_Jint=1.6e-3, **FIX, **TD, relight_start=0.20, t_ign_add=NCS["slots"],
                            t_ign_est=T_EST0 + NCS["slots"]), "full v2.6 FSW, J 1.6e-3, NC-closed relight timeline, planned"),
    "mr_f125_rs20_nc": (dict(PROV, floor=0.125, **TD, relight_start=0.20, t_ign_add=NCS["slots"], t_ign_est=T_EST0 + NCS["slots"]),
                        "12.5 % floor, td72, relight rule 20 %, NC-closed timeline, planned"),
    # v2.1: the ECU firmware v2.6 PREPRESS duration (unprimed line) flown under the 1.4 s planning value (early side)
    "mr_td72_nc_ecu": (dict(PROV, **TD, t_ign_add=(ECU["unprimed_s"] if ECU else NCS["slots"]), t_ign_est=T_EST0 + NCS["slots"]),
                       f"td72, NC-closed relight, ECU v2.6 PREPRESS {ECU['unprimed_s'] if ECU else float('nan'):.2f} s "
                       f"(bleed settle + opener ramp + cock hold, Electronics config.h) under the {T_EST0 + NCS['slots']:.1f} s "
                       "planning value"),
    "mr_AF_fix_td72_nc": (dict(M.CASES["AF_prov_2kg"][0], **FIX, **TD, relight_start=0.20, t_ign_add=NCS["slots"],
                               t_ign_est=T_EST0 + NCS["slots"]), "A-F, full v2.6 FSW, NC-closed relight timeline, planned"),
    "mr_AF": (dict(M.CASES["AF_prov_2kg"][0]), "A-F free fall + TVC flip on the lead tank, v2.5"),
    # v2.1: A-F isolation of the NC-closed relight timeline and of the v2.6 shutdown/relight rules without the tracker/governor
    "mr_AF_nc": (dict(M.CASES["AF_prov_2kg"][0], t_ign_add=NCS["slots"], t_ign_est=T_EST0 + NCS["slots"]),
                 "A-F, v2.5 flight software + NC-closed relight timeline (planned)"),
    "mr_AF_td72_nc": (dict(M.CASES["AF_prov_2kg"][0], **TD, relight_start=0.20, t_ign_add=NCS["slots"], t_ign_est=T_EST0 + NCS["slots"]),
                      "A-F, lift-ramp shutdown + td72 + relight rule + NC timeline, no tracker / governor"),
    "mr_AF_fix": (dict(M.CASES["AF_prov_2kg"][0], **FIX), "A-F + control fix only"),
    "mr_AF_fix_td72": (dict(M.CASES["AF_prov_2kg"][0], **FIX, **TD, relight_start=0.20), "A-F, full v2.6 FSW"),
    "mr_B": (dict(M.CASES["B_prov_2kg_h100"][0]), "B continuous-burn hop 100 m on the lead tank, v2.5"),
    "mr_B_fix": (dict(M.CASES["B_prov_2kg_h100"][0], **FIX), "B hop + control fix only"),
    "mr_B_fix_toff": (dict(M.CASES["B_prov_2kg_h100"][0], **FIX, toff_model=1), "B hop, fix + lift-ramp touchdown shutdown"),
    # v2.2: reference-governor ratchet (att_ref_mode 1, sim6 v2.6): A-F fails with the governor when the NC timeline moves
    # the ignition into a different phase of the free-fall tumble (prop-closure finding); the same cases with the ratchet
    "mr_AF_fix_td72_nc_rat": (dict(M.CASES["AF_prov_2kg"][0], **FIX, **TD, relight_start=0.20, t_ign_add=NCS["slots"],
                                   t_ign_est=T_EST0 + NCS["slots"], att_ref_mode=1),
                              "A-F, full v2.6 FSW + governor ratchet, NC-closed relight timeline, planned"),
    "mr_fsw_J1.6_nc_rat": (dict(PROV, **ACT, act_Jint=1.6e-3, **FIX, **TD, relight_start=0.20, t_ign_add=NCS["slots"],
                                t_ign_est=T_EST0 + NCS["slots"], att_ref_mode=1),
                           "full v2.6 FSW + governor ratchet, J 1.6e-3, NC-closed relight timeline, planned"),
    "mr_B_fix_toff_rat": (dict(M.CASES["B_prov_2kg_h100"][0], **FIX, toff_model=1, att_ref_mode=1),
                          "B hop, fix + lift-ramp touchdown shutdown + governor ratchet"),
}


def main():
    out_dir = os.environ["GNC_OUT"]; suf = os.environ["GNC_SUFFIX"]
    os.makedirs(out_dir, exist_ok=True)
    names = os.environ.get("GNC_MR_CASES", "").split(",")
    p_sum = os.path.join(out_dir, f"mc6_summary_{suf}.json")
    allsum = json.load(open(p_sum))["cases"] if os.path.exists(p_sum) else {}
    for name in names:
        if not name:
            continue
        over, note = CASES[name]
        out, rows = M.run_case(name, over, note)
        allsum[name] = out
        M.write_csv(os.path.join(out_dir, f"mc6_runs_{name}_{suf}.csv"), rows)
        s = out["summary"]
        print(f"{name:26s} P {s['success']:.3f} [{s['ci95'][0]:.3f},{s['ci95'][1]:.3f}] fails {s['fail_modes']} "
              f"sized {out['m_n2o_sized_kg']:.4f} ({out['cpu_s']:.0f}s)", flush=True)
        with open(p_sum, "w") as f:
            json.dump(dict(version=f"m2_meco {suf}", sim=s6.SIM6_VERSION, n=M.N, cases=allsum), f, indent=1, default=float)


if __name__ == "__main__":
    main()

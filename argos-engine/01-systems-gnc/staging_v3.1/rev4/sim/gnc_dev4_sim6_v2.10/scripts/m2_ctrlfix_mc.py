"""m2_ctrlfix_mc v1.1. Control-side fix study for the saturated TVC limit cycle (lead request 2026-10-12): the lead baseline with the
torque/speed-limited servo pair (n 4.8, 6.6 V both-stall plug voltage, as-drawn supply chain, sag), servo rotor inertia
J_int, and candidate ECU/FSW fixes. Same 500 draws (seed 101) as every other case. Env: GNC_CF_CASES (comma list),
GNC_OUT (default out/ctrlfix), GNC_SUFFIX (default cf). Run: nice -n 10 python scripts/m2_ctrlfix_mc.py
"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("GNC_OUT", "/home/claude/work/space/out/ctrlfix")
os.environ.setdefault("GNC_SUFFIX", "cf")
import m2_mc6 as M  # noqa: E402
from gncsim import sim6 as s6  # noqa: E402

BASE_ACT = dict(M.BASE, rcs=False, m_fixed=2.00, act_model=1, servo_V=6.6, act_n=4.8,
                supply_chain=M.ACT_CHAINS["D"], supply_Vrest=None)
FIX = {
    "nofix": {},
    "acc3000": dict(gim_cmd_acc=3000.0),
    "acc2000": dict(gim_cmd_acc=2000.0),
    "acc1500": dict(gim_cmd_acc=1500.0),
    "aw2": dict(gim_aw_thr=2.0),
    "acc2000_aw2": dict(gim_cmd_acc=2000.0, gim_aw_thr=2.0),
    "acc2000_aw3": dict(gim_cmd_acc=2000.0, gim_aw_thr=3.0),
    "acc3000_aw2": dict(gim_cmd_acc=3000.0, gim_aw_thr=2.0),
    "acc2000_aw1.5": dict(gim_cmd_acc=2000.0, gim_aw_thr=1.5),
    "ref40": dict(att_ref_rate=40.0),
    "ref20": dict(att_ref_rate=20.0),
    "acc2000_ref40": dict(gim_cmd_acc=2000.0, att_ref_rate=40.0),
    "acc2000_ref20": dict(gim_cmd_acc=2000.0, att_ref_rate=20.0),
    "acc3000_ref40": dict(gim_cmd_acc=3000.0, att_ref_rate=40.0),
    "acc2000_ref30": dict(gim_cmd_acc=2000.0, att_ref_rate=30.0),
    "acc2000_ref60": dict(gim_cmd_acc=2000.0, att_ref_rate=60.0),
    "acc1500_ref40": dict(gim_cmd_acc=1500.0, att_ref_rate=40.0),
    "acc2000_ref40w1.5r100": dict(gim_cmd_acc=2000.0, att_ref_rate=40.0, att_ref_win=1.5, att_ref_rate2=100.0),
    "acc2000_ref40w1r100": dict(gim_cmd_acc=2000.0, att_ref_rate=40.0, att_ref_win=1.0, att_ref_rate2=100.0),
    "acc2000_ref40w1.5r60": dict(gim_cmd_acc=2000.0, att_ref_rate=40.0, att_ref_win=1.5, att_ref_rate2=60.0),
    # v1.1 (ENG-07d controller option): landing attitude-loop bandwidth reduced (att_wn 6 rad/s DESIGN -> 4.5 / 5)
    "acc2000_ref40_wn4.5": dict(gim_cmd_acc=2000.0, att_ref_rate=40.0, att_wn=4.5),
    "acc2000_ref40_wn5": dict(gim_cmd_acc=2000.0, att_ref_rate=40.0, att_wn=5.0),
}
CASES = {"AD_prov_2kg": (dict(M.BASE, rcs=False, m_fixed=2.00), "LEAD BASELINE (reference servo model)"),
         "AD_prov_2kg_fix": (dict(M.BASE, rcs=False, m_fixed=2.00, gim_cmd_acc=2000.0, att_ref_rate=40.0),
                             "LEAD BASELINE (reference servo model) + fix acc2000_ref40"),
         "AD_fins_f20_fix": (dict(M.BASE, gim_cmd_acc=2000.0, att_ref_rate=40.0),
                             "RCS-fitted baseline (sized load) + fix acc2000_ref40"),
         "AD_fins_f20": (dict(M.BASE), "RCS-fitted baseline (sized load)")}
for J in (0.0, 1.0e-3, 1.6e-3, 2.0e-3, 2.7e-3, 4.0e-3, 5.0e-3, 8.0e-3):
    for fk, fx in FIX.items():
        name = f"cf_J{J * 1e3:g}_{fk}"
        CASES[name] = (dict(BASE_ACT, act_Jint=J, **fx),
                       f"n 4.8, 6.6 V hold (sag, as drawn), J_int {J:g} kg m2, fix {fk}: {json.dumps(fx)}")


def main():
    out_dir = os.environ["GNC_OUT"]; suf = os.environ["GNC_SUFFIX"]
    os.makedirs(out_dir, exist_ok=True)
    names = os.environ.get("GNC_CF_CASES", "").split(",")
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
        print(f"{name:28s} P {s['success']:.3f} [{s['ci95'][0]:.3f},{s['ci95'][1]:.3f}] fails {s['fail_modes']} "
              f"({out['cpu_s']:.0f}s)", flush=True)
        with open(p_sum, "w") as f:
            json.dump(dict(version=f"m2_ctrlfix {suf}", sim=s6.SIM6_VERSION, n=M.N, cases=allsum), f, indent=1, default=float)


if __name__ == "__main__":
    main()

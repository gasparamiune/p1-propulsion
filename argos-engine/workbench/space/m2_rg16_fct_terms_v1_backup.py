"""m2_rg16_fct_terms v1 (GNC, 2026-10-13): review REV-GNC-1 RG-16 items 1 and 4 completed with the two mass terms that the
forced purge (RG-01 provision, lead decision 2026-10-13) and the stuck-open head-end bleed add to the flight-software mass
estimate, and the FC_THRUST 650 N threshold re-checked against them on both sides.

Terms (m_hat = the flown estimator of m2_mass_est v2; e = m_hat / m_exact - 1):
  PURGE BOOKING (A1 relight only; B1, B2, C, D have no purge). The FSW books the commanded purge at prg_mdot_hat x t (sim6
    amendment P, prg_book 1). Booked at the liquid flow of the 0.8 mm orifice (20.0 g/s, Combustion purge_sizing_v2p4, DERIVED)
    the booking over-states the vented mass because the segment vents vapour first: residual = booked - vented = 4.6-19.0 g at
    Tp 2.0 s and 4.9-23.1 g at Tp 3.0 s (Combustion purge_table_v2p4 rows 0.8|*: vented 20.98-35.36 g / 36.86-55.12 g, DERIVED).
    The orifice passes at most its liquid flow and at least its vapour flow (5.44 g/s), so the residual does not decrease with
    Tp and grows by at most 20.0 - 5.44 = 14.56 g/s beyond the last table point: the flown purges last up to Tp_max = the
    largest prg_dur of pb_A1_P25 (the purge runs between two evaluations of the trigger, 2.77-3.32 s p1-p99), so the bound is
    23.1 g + (Tp_max - 3.0 s) x 14.56 g/s (DERIVED, bounded extrapolation). Sign: m_hat UNDER-reads (missed-detection side of
    FC_THRUST). Comparator: the purge NOT booked, m_hat over-reads by the vented mass: sim6 truth (liquid for the whole purge,
    upper bound) prg_mass max of pb_A1_P25_nobook.
  STUCK-OPEN BLEED (fault; outside the nominal budget; the bleed is confirmed closed before E1, lead decision 2026-10-13):
    m_hat over-reads by the bled mass (no FSW model, no detector): blf_mass max of pb_A1_S194_0 (relight lift onward) and
    pb_B1_B194_0 (from the first ignition), 19.4 g/s additive bracket (the largest Combustion flow, 0.8 mm).
Method: each term is applied as a CONSTANT m_hat offset from ARM (mest_w + w_bias) in the m2_mass_est v2 fct part (same draws,
noise model, frames, 3-frame hold and stuck-ramp test as fct_mest_v2.json; m2_fc_thrust v1.1 configurations A1 0.81 s liquid /
B1 85 m; 200 runs per case). A constant offset from ARM bounds a term that appears only after the purge (A1) or grows during the
burn (bleed): it applies the full offset to every FC frame, including the first burn of A1 (conservative on both sides).
Comparator for each case: the same case without the offset (fct_mest_v2.json, m2_mass_est v2 part fct).
Cases (profile|case = base fct case + w_bias kg):
  A1|H_cal_pbk, A1|H_cal_comp_pbk, A1|Llo_re_pbk, A1|Llo_cmd_pbk, A1|Llo_re_comp_pbk   -0.0231 (booked purge, worst residual)
  A1|H_cal_pnb, A1|Lhi_re_pnb, A1|Lhi_cmd_pnb, A1|Lhi_re_comp_pnb                         + purge mass max (purge not booked)
  A1|H_cal_blf                                                                             + bled mass max of A1 S194_0
  B1|H_cal_blf, B1|H_cal_comp_blf                                                          + bled mass max of B1 B194_0
Env: GNC_IFACE, GNC_ACT_RATE (v3c set), GNC_RG16_PARTS (fct,eval), GNC_RG16_OUT (out/rg16_terms), GNC_MEST2_NFCT (200).
Output: <out>/fct2_<profile>_<case>.json (m2_mass_est v2 format), <out>/rg16_fct_terms.json"""
import csv
import hashlib
import json
import os
import sys
import numpy as np

S = "/home/claude/work/space/out"
OUT = os.environ.get("GNC_RG16_OUT", f"{S}/rg16_terms")
PARTS = os.environ.get("GNC_RG16_PARTS", "fct,eval").split(",")
os.environ.setdefault("GNC_PC_RATCHET", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gncsim import sim6 as s6  # noqa: E402
import m2_mass_est_v2 as MV  # noqa: E402

VERSION = "m2_rg16_fct_terms v1"
FCT0 = dict(MV.FCT_CASES)          # the m2_mass_est v2 cases (part_fct narrows MV.FCT_CASES to one case per call)
PB = f"{S}/purge_bleed"
BASEFCT = f"{S}/mass_est_v2/fct_mest_v2.json"
COMB_TABLE = "/home/claude/work/combustion/data/v2/v2p4/purge_table_v2p4.json"
COMB_SIZING = "/home/claude/work/combustion/data/v2/v2p4/purge_sizing_v2p4.json"
M_LIQ_FLOW = None


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def comb_terms():
    """Booking residual at the 0.8 mm orifice booked at its liquid flow: booked - vented over the Combustion table rows."""
    t = json.load(open(COMB_TABLE))
    sz = json.load(open(COMB_SIZING))
    q = float(sz["flows"]["0.8mm"]["mdot_liquid_g_s"])
    vent = {"2.0": [], "3.0": []}
    for k, v in t["rows"].items():
        if not k.startswith("0.8|"):
            continue
        for st in ("wet", "dry"):
            if st in v:
                vent["2.0"] += list(v[st]["N2O_g_Tp2"])
                vent["3.0"] += list(v[st]["N2O_g_Tp3"])
    out = dict(orifice_mm=0.8, liquid_flow_g_s=q, vapour_flow_g_s=float(sz["flows"]["0.8mm"]["mdot_vapour_g_s"]),
               vented_g={tp: [min(x), max(x)] for tp, x in vent.items()},
               residual_booked_minus_vented_g={tp: [q * float(tp) - max(x), q * float(tp) - min(x)] for tp, x in vent.items()},
               sources=dict(purge_table=f"{COMB_TABLE} (sha256/16 {sha16(COMB_TABLE)})",
                            purge_sizing=f"{COMB_SIZING} (sha256/16 {sha16(COMB_SIZING)})"), tag="DERIVED (Combustion v2.4)")
    tp_max = float(pb_col("A1_P25", "prg_dur").max())
    r3 = max(out["residual_booked_minus_vented_g"]["3.0"])
    out["Tp_max_flown_s"] = tp_max
    out["residual_bound_g"] = r3 + max(0.0, tp_max - 3.0) * (q - out["vapour_flow_g_s"])
    out["residual_bound_rule"] = "residual(3.0 s) max + (Tp_max - 3.0) x (liquid - vapour flow)"
    return out


def pb_col(name, k):
    p = os.path.join(PB, f"pb_{name}.csv")
    return np.array([float(r[k]) for r in csv.DictReader(open(p))])


def offsets():
    c = comb_terms()
    pnb = float(pb_col("A1_P25_nobook", "prg_mass").max())
    a1b = float(pb_col("A1_S194_0", "blf_mass").max())
    b1b = float(pb_col("B1_B194_0", "blf_mass").max())
    return dict(pbk=-1e-3 * c["residual_bound_g"], pnb=pnb, blf_A1=a1b, blf_B1=b1b), c


def cases():
    o, _ = offsets()
    F = FCT0
    C = {}
    for b in ("H_cal", "H_cal_comp", "Llo_re", "Llo_cmd", "Llo_re_comp"):
        C[("A1", f"{b}_pbk")] = (b, dict(F[b], w_bias=o["pbk"]))
    for b in ("H_cal", "Lhi_re", "Lhi_cmd", "Lhi_re_comp"):
        C[("A1", f"{b}_pnb")] = (b, dict(F[b], w_bias=o["pnb"]))
    C[("A1", "H_cal_blf")] = ("H_cal", dict(F["H_cal"], w_bias=o["blf_A1"]))
    for b in ("H_cal", "H_cal_comp"):
        C[("B1", f"{b}_blf")] = (b, dict(F[b], w_bias=o["blf_B1"]))
    return C


_ORIG = MV.run_cfg_case


def run_cfg_case_bias(cfg, dr, spec, i, prior):
    c, disp = _ORIG(cfg, dr, spec, i, prior)
    wb = float(spec.get("w_bias", 0.0))
    if wb != 0.0:
        c = dict(c, mest_w=float(c.get("mest_w", 0.0)) + wb)
    return c, disp


def part_fct():
    MV.run_cfg_case = run_cfg_case_bias
    MV.OUT = OUT
    os.makedirs(OUT, exist_ok=True)
    for (prof, name), (_, spec) in cases().items():
        MV.FCT_CASES = {name: spec}
        MV.SPLIT = "0/2" if prof == "A1" else "1/2"     # jobs = [(A1, name), (B1, name)][k::2]
        MV.part_fct()


def part_eval():
    base = json.load(open(BASEFCT))["cases"]
    o, c = offsets()
    out = dict(version=VERSION, date="2026-10-13", sim=s6.SIM6_VERSION, method=__doc__.split("\n\n")[1].strip(),
               threshold_N=MV.T_ABORT, stuck_N=MV.F_STUCK, offsets_kg=o, combustion_purge=c,
               comparator=f"{BASEFCT} (sha256/16 {sha16(BASEFCT)})", cases={})
    for (prof, name), (bname, spec) in cases().items():
        p = os.path.join(OUT, f"fct2_{prof}_{name}.json")
        if not os.path.exists(p):
            continue
        d = json.load(open(p))
        d.pop("runs", None)
        b = base[f"{prof}|{bname}"]
        e = dict(w_bias_kg=spec["w_bias"], base_case=f"{prof}|{bname}",
                 held_max_N=d["held_max_fc_N"]["max"], margin_to_650_N=d["held_max_fc_N"]["margin_to_650_N"],
                 runs_above_650=d["held_max_fc_N"]["runs_above_650"], base_held_max_N=b["held_max_fc_N"]["max"],
                 b_sys_min=d["b_sys_at_onsets"]["min"], b_sys_p01=d["b_sys_at_onsets"]["values"][0],
                 base_b_sys_min=b["b_sys_at_onsets"]["min"], stuck=d["stuck"], base_stuck=b["stuck"], P=d["P"], base_P=b["P"],
                 mhe_fc_min_max=d["mhe_fc_min_max"], base_mhe_fc_min_max=b["mhe_fc_min_max"])
        out["cases"][f"{prof}|{name}"] = e
        s670, b670 = d["stuck"]["670"], b["stuck"]["670"]
        print(f"{prof}|{name:18s} w_bias {1e3 * spec['w_bias']:+7.1f} g | held max {e['held_max_N']:.1f} N (base "
              f"{e['base_held_max_N']:.1f}; margin {e['margin_to_650_N']:.1f}) | b_sys min {100 * e['b_sys_min']:+.2f} % (base "
              f"{100 * e['base_b_sys_min']:+.2f}) | 670 N miss {s670['misses']}/{s670['cases']} (base {b670['misses']}) pre "
              f"{s670['pre_onset_alarms']} | P {e['P']:.3f} (base {e['base_P']:.3f})", flush=True)
    with open(os.path.join(OUT, "rg16_fct_terms.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)
    print("wrote", os.path.join(OUT, "rg16_fct_terms.json"), flush=True)


if __name__ == "__main__":
    if "fct" in PARTS:
        part_fct()
    if "eval" in PARTS:
        part_eval()

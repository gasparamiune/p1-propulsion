"""Fin-misalignment roll torque (hand calculation, not in sim6): sets the fin alignment tolerance for the airframe
ICD and checks it against the roll-RCS torque.

Barrowman per-fin normal-force slope with body interference (same formula as gncsim/aero.py), the fin's spanwise
centre of pressure as the roll arm, and the fin roll damping (local angle of attack p*y/V). A cant angle delta on
each fin gives M = n * q S CNa_1 delta y; the steady roll rate where the damping balances it is p = delta V / y
(independent of q), reached with the time constant I_roll / D, D = n * q S CNa_1 y^2 / V.

Inputs: RV-1c fin geometry (gncsim.vehicle, ASSUMED fins), the baseline MC max dynamic pressure and MECO speed
(GNC_OUT/mc6_summary_v2.json), the roll inertia and RCS torque of the baseline vehicle (run6.build).
Output: GNC_RES/fin_roll_v2.json. Run: python scripts/m2_fin_roll.py
"""
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R, sim6 as s6, vehicle as veh  # noqa: E402

OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/m2")
RES = os.environ.get("GNC_RES", "/home/claude/work/space/out/results_v2")
SUFFIX = os.environ.get("GNC_SUFFIX", "v2")
os.makedirs(RES, exist_ok=True)


def main():
    S = json.load(open(os.path.join(OUT, f"mc6_summary_{SUFFIX}.json")))
    b = S["cases"]["AD_fins_f20"]
    cfg = R.cfg_of(profile="A-D", fins=True, floor=0.20, m_n2o=b["m_n2o_mc_kg"])
    par, apar, comp, mp, tab, info = R.build(cfg)
    geo = info["geo"]
    d = geo["d"]
    r = d / 2.0
    cr, ct, s, xs = geo["fin_cr"], geo["fin_ct"], geo["fin_span"], geo["fin_sweep"]
    n = geo["n_fins"]
    Sref = np.pi * d * d / 4.0
    lm = np.sqrt(s * s + (xs + 0.5 * ct - 0.5 * cr) ** 2)
    cna_set = (4.0 * n * (s / d) ** 2) / (1.0 + np.sqrt(1.0 + (2.0 * lm / (cr + ct)) ** 2))
    kint = 1.0 + r / (s + r)
    cna_1 = cna_set / (n / 2.0) * kint          # one fin, normal to its own plane, with interference
    y_cp = r + s / 3.0 * (cr + 2.0 * ct) / (cr + ct)   # spanwise centre of a trapezoidal fin
    q = b["summary"]["max_q_p99"]
    V = b["nominal"]["v_meco"]
    Ir = info["Ir0"]
    m_rcs = par[s6.P_rcs_torque]
    out = dict(version="fin_roll v2", sim_vehicle=info["vehicle"], d_m=d, fins=dict(n=n, cr=cr, ct=ct, span=s, sweep=xs),
               cna_one_fin_per_rad=cna_1, interference=kint, y_cp_m=y_cp, q_max_p99_Pa=q, V_at_MECO_mps=V,
               I_roll_liftoff_kgm2=Ir, rcs_torque_Nm=m_rcs, cases=[],
               tag="DERIVED hand calculation (Barrowman fin slope + strip roll damping); fins ASSUMED; not modelled in sim6",
               note="steady roll rate p = delta V / y_cp does not depend on q; the torque scales with q")
    D = n * q * Sref * cna_1 * y_cp ** 2 / V
    for cant_deg in (0.05, 0.1, 0.2, 0.5):
        dl = np.radians(cant_deg)
        M_one = q * Sref * cna_1 * dl * y_cp
        M_all = n * M_one
        p_ss = dl * V / y_cp
        p_rcs = max(M_all - m_rcs, 0.0) / D
        out["cases"].append(dict(cant_deg=cant_deg, torque_one_fin_Nm=M_one, torque_all_fins_same_sense_Nm=M_all,
                                 torque_rss_random_Nm=np.sqrt(n) * M_one, damping_Nm_s=D, tau_s=Ir / D,
                                 steady_roll_rate_all_fins_dps=np.degrees(p_ss),
                                 steady_roll_rate_with_rcs_dps=np.degrees(p_rcs),
                                 ratio_to_rcs_torque=M_all / m_rcs if m_rcs > 0 else None))
        print(f"cant {cant_deg:.2f} deg: one fin {M_one:.4f} N m, all same {M_all:.4f} N m (RCS {m_rcs:.4f}), "
              f"steady p {np.degrees(p_ss):.1f} deg/s, with RCS {np.degrees(p_rcs):.1f} deg/s, tau {Ir / D:.2f} s")
    json.dump(out, open(os.path.join(RES, "fin_roll_v2.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()

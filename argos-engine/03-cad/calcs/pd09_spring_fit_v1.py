"""PD-09 pintle return spring (flat spiral, open coils): does the lead-decided torque fit the CAD v3.4 envelope?  (v1, 2026-10-13, Mechanical)

Requirement (lead decision 2026-10-12, pintle_v2p3.SPRING): T = 0.25 N m at the seated crank angle (15 deg) + 0.12 N m/rad, +/-10 %,
up to the stop 113.09 deg -> T_max = 0.455 N m nominal, 0.501 N m at +10 %.
Envelope (parts_pintle PD-02 / PD-04): cavity 22 H11 x 6 mm, spring envelope OD 21 / hub 8, hub length 4.5 mm (the PD-04 hub y 19.5-24.0
carries the inner-end slot; the encoder magnet pocket and the 1.2 mm magnet-to-chip gap fix the shaft end, so the strip width is <= 4.5 mm).
Found: the PD-09 part note carried "strip 4.5 x 0.25" (ESTIMATE): sigma = 6 M / (b t^2) = 9.7 GPa at 0.455 N m -> impossible.  This script
sizes the strip that the requirement needs (no change to the requirement, the envelope or the HV69: coordinator 2026-10-13 keeps them).
Formulas (open-coil spiral spring, outer end CLAMPED, uniform moment; Wahl / spring-maker practice): rate k = E b t^3 / (12 L);
stress sigma = K_end 6 M / (b t^2) with K_end 1.0 clamped (2.0 if the outer end is pinned in a loose slot); open-coil packing rule: strip
plan area L t <= ~50 % of the annulus (coils must not touch over the stroke) -- a design guideline, the maker confirms.
Output: calcs/pd09_spring_fit_v1.json.  DERIVED from ASSUMED material values; the spring maker's design and a torque test (B-PNT-1) govern.
"""
from __future__ import annotations
import json, math
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "pd09_spring_fit_v1.json"
T0, K, TOL = 0.25, 0.12, 0.10
PHI_SEAT, PHI_STOP = 15.0, 113.09
E = 185e3                         # MPa, 1.4310 spring strip (LITERATURE-approx 180-190 GPa)
SIG = {"0.7xRm1700": 1190.0, "0.7xRm1900": 1330.0}   # MPa allowable bending, ASSUMED 0.7 Rm of EN 10151 1.4310 +C1700 / +C1900 strip (TO-VERIFY)
R_OUT, R_HUB, B_MAX = 10.5, 4.0, 4.5
RHO = 7.9e-6                      # kg/mm3


def size(b, sig, k_end):
    Tm = (T0 + K * math.radians(PHI_STOP - PHI_SEAT)) * (1 + TOL) * 1e3      # N mm
    t = math.sqrt(6 * Tm * k_end / (b * sig))
    L = E * b * t ** 3 / (12 * K * 1e3)
    A_ann = math.pi * (R_OUT ** 2 - R_HUB ** 2)
    fill = L * t / A_ann
    turns = L / (2 * math.pi * 0.5 * (R_OUT + R_HUB))
    return {"b_mm": b, "sigma_allow_MPa": sig, "K_end": k_end, "t_mm": round(t, 3), "L_active_mm": round(L, 1), "turns": round(turns, 2),
            "fill_of_annulus": round(fill, 3), "fits_50pct_rule": bool(fill <= 0.50), "mass_g": round(L * b * t * RHO * 1e3, 1),
            "preload_wind_deg": round(math.degrees(T0 / K), 1), "stroke_deg": round(PHI_STOP - PHI_SEAT, 2)}


def main():
    Tn = T0 + K * math.radians(PHI_STOP - PHI_SEAT)
    rows = [size(B_MAX, s, ke) for s in SIG.values() for ke in (1.0, 2.0)]
    tol = {"strip_t_+/-0.008mm_on_0.72": round(3 * 0.008 / 0.72 * 100, 1), "E_+/-2pct": 2.0, "width_+/-0.03mm": round(0.03 / 4.5 * 100, 1),
           "active_length_end_fixation_+/-2pct": 2.0, "preload_wind_+/-5deg_of_119deg_(T0_only)": round(5 / 119.4 * 100, 1)}
    rss = math.sqrt(sum(v ** 2 for v in tol.values()))
    out = {"id": "pd09_spring_fit", "version": "v1", "date": "2026-10-13", "owner": "mechanical", "script": "03-cad/src/calcs/pd09_spring_fit_v1.py",
           "method": __doc__.split("\n\n")[1], "requirement": {"T_seat_Nm": T0, "k_Nm_per_rad": K, "tol": TOL, "T_stop_nom_Nm": round(Tn, 4),
                                                                 "T_stop_plus10_Nm": round(Tn * 1.1, 4)},
           "envelope_mm": {"cavity": "22 H11 x 6", "spring_OD": 2 * R_OUT, "hub": 2 * R_HUB, "b_max": B_MAX},
           "found_defect": "PD-09 note 'strip 4.5 x 0.25' gives 9.7 GPa at 0.455 N m: corrected to the sized strip below (CAD v3.4 note)",
           "sizing": rows,
           "torque_tolerance_pct": {"contributors": tol, "RSS": round(rss, 1), "worst_case_sum": round(sum(tol.values()), 1),
                                    "verdict": "+/-10 % is achievable as a maker specification with set-up adjustment of the preload wind; "
                                               "the RSS of the listed contributors is below 10 %, the arithmetic worst case is above it"},
           "verdict": f"fits only with the outer end CLAMPED and a high-strength strip (+C1900 class): t {rows[2]['t_mm']} mm x 4.5, "
                      f"{rows[2]['L_active_mm']} mm active, {rows[2]['turns']} turns, fill {rows[2]['fill_of_annulus']} of the annulus (at the 0.50 "
                      "guideline: no margin); a pinned outer end or +C1700 strip does not fit.  Hold: the "
                      "spring maker designs it (TO-QUOTE DK-6400) and B-PNT-1 measures T(phi); if the maker cannot meet it, the cavity grows "
                      "(housing PD-02 change) -- not a redesign of the requirement",
           "tag": "DERIVED from ASSUMED material allowables (TO-VERIFY with the maker)"}
    OUT.write_text(json.dumps(out, indent=1))
    for r in rows:
        print(r)
    print(out["torque_tolerance_pct"])


if __name__ == "__main__":
    main()

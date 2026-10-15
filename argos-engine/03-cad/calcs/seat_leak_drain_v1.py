"""Seat / seal leakage of the MV-to-pintle-seat segment and the time to drain it from primed (P_feed >= 0.5 P_tank) to unprimed
(Mechanical, v1, 2026-10-13; lead question for GNC/Electronics relight logic).

Physics: with the MV and the pintle closed the segment is a rigid volume of saturated N2O.  While any liquid is left the pressure
stays at Psat(T_liquid) ~ P_tank, so 'unprimed' (P < 0.5 P_tank) needs essentially the whole inventory to leave: liquid-full mass
minus the vapour mass left at 0.5 P_tank.  Fastest (worst) case = liquid leaking at the pintle seat the whole time (cold: no boiling
at the seat; the manifold column drains onto the seat; when the hot head dries the manifold the leak becomes vapour, ~1/3 of the
mass rate for the same gap) and NO inflow past the MV seat (an MV leak refills the segment).

Leak models (no vendor leak data exists for these seats; every rate is tagged):
  L1  ANSI/FCI 70-2 Class V (metal seat): 5e-4 mL/min water per inch of seat diameter per psi dP (STANDARD, AS RECALLED);
      converted to liquid N2O with viscous (micro-gap) scaling Q ~ dP/mu -> upper bound (flashing in the gap lowers it).
      Equivalent uniform gap from the slot law (w = pi d, land 0.3 mm) is reported, and the N2 gas leak through the same gap.
  L2  'debris' worst credible: one 15 um particle (filter rating, lead 2026-10-12) holding the seat open over ~0.10 mm of
      circumference -> orifice 15 um x 0.10 mm, Cd 0.6, incompressible liquid (upper bound; HEM flashing lowers it 2-3x). ASSUMED.
  L3  stem seal (spring-energised PTFE, static, 3 mm rod): ASSUMED <= 0.1 mL/h liquid (vendors quote 'no visible leakage' for
      liquids; no number available) -> shown to be negligible.
  L4  MV-P PCTFE soft seat: ANSI/FCI 70-2 Class VI (bubble-tight soft seat) is the B-MV-1 acceptance; it is an INFLOW to the
      segment and is set to zero for the drain time (conservative).
"""
from __future__ import annotations
import json, math
from pathlib import Path
import CoolProp.CoolProp as CP

OUT = Path(__file__).resolve().parent / "seat_leak_drain_v1.json"
V_SEG_CM3 = 44.0          # lead 2026-10-13 option A estimate; CAD v3.4 solids re-measure it (checks/inlet_e1m_volumes.json)
D_SEAT_MM = 5.5           # combustion.json pintle seat
LAND_MM = 0.30            # TC-03 seat land 0.3 mm (DESIGN); bluing contact >= 0.24 mm
PSI = 6894.757
MU_W = 1.0016e-3          # water 20 C, Pa s (LITERATURE)
COAST_S = 30.0            # ASSUMED upper bound of an in-flight coast between burns (GNC owns the real value)
MU_L_N2O = 0.070e-3       # Pa s, saturated liquid N2O 15-25 C: 0.07-0.10 mPa s (ESDU 91022 class, AS RECALLED, TO-VERIFY); lower end
                          # used because a lower viscosity gives the larger viscous leak (conservative for the drain time)


def props(TC):
    T = TC + 273.15
    Ps = CP.PropsSI("P", "T", T, "Q", 0, "NitrousOxide")
    rl = CP.PropsSI("D", "T", T, "Q", 0, "NitrousOxide")
    mul = MU_L_N2O                                                       # CoolProp has no N2O viscosity model
    rv_half = CP.PropsSI("D", "T", T, "P", 0.5 * Ps, "NitrousOxide")
    return dict(T_C=TC, Psat_bar=Ps / 1e5, rho_l=rl, mu_l=mul, rho_v_half=rv_half)


def main():
    res = {"id": "seat_leak_drain", "version": "v1", "date": "2026-10-13", "owner": "mechanical", "script": "03-cad/src/calcs/seat_leak_drain_v1.py",
           "inputs": {"V_segment_cm3": V_SEG_CM3, "seat_d_mm": D_SEAT_MM, "land_mm": LAND_MM, "coast_s_ASSUMED": COAST_S}, "cases": {}}
    w = math.pi * D_SEAT_MM * 1e-3
    for TC in (15.0, 20.0, 25.0):
        p = props(TC)
        dP = p["Psat_bar"] * 1e5 - 1.0e5                                       # segment at Psat, chamber ~1 bar
        dm = V_SEG_CM3 * 1e-6 * (p["rho_l"] - p["rho_v_half"])                # kg to leave before P < 0.5 Psat
        # L1 Class V
        q_w = 5e-4 * (D_SEAT_MM / 25.4) * (dP / PSI) / 60.0 * 1e-6           # m3/s water
        q_n = q_w * MU_W / p["mu_l"]
        m1 = q_n * p["rho_l"]
        h = (12 * MU_W * LAND_MM * 1e-3 * q_w / (w * dP)) ** (1 / 3)          # equivalent uniform gap
        mu_n2 = CP.PropsSI("V", "T", 293.15, "P", 1e5, "Nitrogen")
        Rn2 = 8.314462 / 0.0280134
        P1 = p["Psat_bar"] * 1e5
        m_n2 = w * h ** 3 * (P1 ** 2 - 1e5 ** 2) / (24 * mu_n2 * Rn2 * 293.15 * LAND_MM * 1e-3)
        sccm = m_n2 / CP.PropsSI("D", "T", 273.15, "P", 101325, "Nitrogen") * 1e6 * 60
        # L2 debris
        m2 = 0.6 * 15e-6 * 0.10e-3 * math.sqrt(2 * p["rho_l"] * dP)
        # L3 stem seal
        m3 = 0.1e-6 / 3600 * p["rho_l"]
        res["cases"][f"{TC:.0f}C"] = {
            "Psat_bar": round(p["Psat_bar"], 2), "rho_l": round(p["rho_l"], 1), "mu_l_mPas": round(p["mu_l"] * 1e3, 4),
            "mass_liquid_full_g": round(V_SEG_CM3 * p["rho_l"] * 1e-3, 1), "mass_left_at_half_P_g": round(V_SEG_CM3 * p["rho_v_half"] * 1e-3, 2),
            "dm_to_unprime_g": round(dm * 1e3, 1),
            "L1_classV": {"water_mL_min": round(q_w * 6e7, 4), "N2O_liquid_mL_min": round(q_n * 6e7, 3), "mdot_mg_s": round(m1 * 1e6, 2),
                          "equiv_gap_um": round(h * 1e6, 3), "N2_gas_same_gap_sccm": round(sccm, 1),
                          "t_unprime_s": round(dm / m1), "t_unprime_min": round(dm / m1 / 60, 1)},
            "L2_debris_15um": {"mdot_mg_s": round(m2 * 1e6, 1), "t_unprime_s": round(dm / m2), "t_unprime_min": round(dm / m2 / 60, 1)},
            "L3_stem_seal_ASSUMED": {"mdot_mg_s": round(m3 * 1e6, 4), "t_unprime_h": round(dm / m3 / 3600, 0)},
            "mdot_needed_to_unprime_in_coast_g_s": round(dm / COAST_S * 1e3, 2)}
    c = res["cases"]
    tmin = min(min(v["L1_classV"]["t_unprime_s"], v["L2_debris_15um"]["t_unprime_s"]) for v in c.values())
    res["verdict"] = (f"leakage cannot unprime the segment within a flight coast: shortest drain {tmin:.0f} s (debris-held seat, liquid, "
                      f"25 C) vs coast <= {COAST_S:.0f} s ASSUMED; unpriming in {COAST_S:.0f} s needs >= ~1 g/s, i.e. a stuck-open seat "
                      "(an effective hole ~0.1 mm2), which is a pintle failure, not leakage")
    res["acceptance_proposal"] = {
        "B-PNT-1 pintle seat": "seat closed by the spiral spring alone (no servo torque), GN2 at 56 bar (Psat 25 C) upstream, chamber side "
                               "at ambient, RT and after a 150 C soak of the head: <= 10 sccm GN2 (pressure decay or flowmeter on the chamber side); "
                               "liquid N2O equivalent ~1 mg/s (same gap, viscous) -> > 8 h to unprime 44 cm3 and <= 0.6 g of N2O into the "
                               "chamber over a 10 min hold (hard-start inventory criterion 20 g)",
        "B-PNT-1 stem seal": "<= 1 sccm GN2 at 56 bar static, RT and 150 C (spring-energised PTFE class)",
        "B-MV-1 MV-P seat": "ANSI/FCI 70-2 Class VI with GN2 at 56 bar and at 84.2 bar (MAWP), RT and 60 C (bay soak)",
        "CF-3": "record P_feed (J602) and the segment TCs during every closed hold: the decay rate gives the in-situ leak (target: no "
                "measurable decay over 10 min while liquid remains, consistent with the B-PNT-1 number)",
        "tag": "DESIGN (proposal for lead approval)"}
    OUT.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()

"""Thermal isolation of the segment's route metal by a PTFE lining: lumped estimate (v1, 2026-10-13, Mechanical).

Coordinator 2026-10-13 (optional): how much would isolating the MV module outlet chamber, the TEE and the hose ends cut the 534-1789 J
module/route heat of Combustion's reroute_vapour_v2p4 (option: >= 1 mm PTFE lining)?
Model (lumped, per heat source type):
  (1) STORED heat: metal parts at dT0 above the liquid at MECO release m c dT0 (1 - exp(-t/tau)), tau = R m c, R = 1/(h A) unlined or
      1/(h A) + t_l/(k_l A) lined.  The lining's own sensible heat (rho c t A dT0) is released with its own diffusion time
      4 t^2/(pi^2 alpha) (slab, metal side ~adiabatic over seconds) - it is at the metal temperature at MECO.
  (2) INFLOW from the bay air through the outer surface during the coast: Q = dT / (R_ext + R_l + R_h); R_ext from h_ext 10 W/m2K on the
      outer area (ASSUMED): the lining is in series with a much larger outer resistance and changes little; external insulation is the
      lever for this part.
Inputs: wetted areas from the CAD v3.4.1 fluid primitives (parts_feed.fluid_spec: module outlet side 2,070 mm2, TEE 496 mm2, hose-end
sleeves 1,010 mm2), metal masses from the make_all v3.4.1 BOM (FS-01A 6061 52.1 g, FD-05 316L 42.1 g, FD-08F 13.5 g, sleeves 2 x 25 g
ESTIMATE); liquid-side h 1000-5000 W/m2K ASSUMED (natural convection to nucleate boiling of near-saturated N2O); PTFE k 0.25 W/m/K,
rho 2200, c 1000 (LITERATURE as recalled); coast 18.7 s (A1, segment_heat_coast_v1), first 8.3 s (Combustion: 68-71 % of the heat).
Output: calcs/ptfe_lining_estimate_v1.json.  ESTIMATE (lumped; Combustion's own split uses older hardware: -6 JIC ends, 0.252 m hose,
316L module body - to be updated with the v3.4.1 BOM).
"""
from __future__ import annotations
import json, math
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "ptfe_lining_estimate_v1.json"
A = {"module outlet side (FS-01A chamber, ports, line passage)": 2.070e-3, "TEE FD-05 bores": 0.496e-3, "hose-end sleeves FD-07A/B": 1.010e-3}
MC = {"FS-01A 6061 52.1 g x 896": 0.0521 * 896, "FD-05 316L 42.1 g x 500": 0.0421 * 500, "FD-08F 316L 13.5 g x 500": 0.0135 * 500,
      "FD-07A/B sleeves 2 x 25 g x 500 (ESTIMATE)": 0.050 * 500}
K_L, RHO_L, C_L = 0.25, 2200.0, 1000.0
T_COAST, T_EARLY = 18.7, 8.3


def main():
    At = sum(A.values())
    mc = sum(MC.values())
    rows = []
    for h in (1000.0, 5000.0):
        for t_l in (0.0, 0.5e-3, 1.0e-3, 2.0e-3):
            R = 1.0 / (h * At) + (t_l / (K_L * At) if t_l else 0.0)
            tau = R * mc
            f18, f8 = 1 - math.exp(-T_COAST / tau), 1 - math.exp(-T_EARLY / tau)
            mcl = RHO_L * C_L * t_l * At
            alpha = K_L / (RHO_L * C_L)
            tau_l = 4 * t_l ** 2 / (math.pi ** 2 * alpha) if t_l else 0.0
            g18 = 1 - math.exp(-T_COAST / tau_l) if t_l else 0.0
            g8 = 1 - math.exp(-T_EARLY / tau_l) if t_l else 0.0
            rows.append({"h_W_m2K": h, "lining_mm": t_l * 1e3, "R_K_W": round(R, 3), "tau_s": round(tau, 1),
                         "metal_fraction_delivered_18.7s": round(f18, 3), "metal_fraction_delivered_8.3s": round(f8, 3),
                         "lining_mc_J_K": round(mcl, 2), "lining_tau_s": round(tau_l, 2),
                         "J_per_K_dT0_18.7s": round(mc * f18 + mcl * g18, 1), "J_per_K_dT0_8.3s": round(mc * f8 + mcl * g8, 1)})
    ratio = {}
    for h in (1000.0, 5000.0):
        base = [r for r in rows if r["h_W_m2K"] == h and r["lining_mm"] == 0.0][0]
        for r in rows:
            if r["h_W_m2K"] == h and r["lining_mm"] > 0:
                ratio[f"h{h:.0f}_t{r['lining_mm']:.1f}mm"] = {"coast": round(r["J_per_K_dT0_18.7s"] / base["J_per_K_dT0_18.7s"], 3),
                                                              "first_8.3s": round(r["J_per_K_dT0_8.3s"] / base["J_per_K_dT0_8.3s"], 3)}
    out = {"id": "ptfe_lining_estimate", "version": "v1", "date": "2026-10-13", "owner": "mechanical", "script": "03-cad/src/calcs/ptfe_lining_estimate_v1.py",
           "method": __doc__, "area_m2": A, "A_total_m2": At, "mc_J_K": MC, "mc_total_J_K": round(mc, 1), "rows": rows,
           "stored_heat_ratio_lined_over_unlined": ratio,
           "inflow_note": "bay-air inflow during the coast: R_ext = 1/(10 W/m2K x outer area ~0.01 m2) ~ 10 K/W >> R_lining 1.1 K/W -> a lining "
                          "cuts this part by ~10 % only; external insulation of the module/line is the lever for it (ESTIMATE)",
           "tag": "ESTIMATE (lumped; h and outer area ASSUMED; PTFE properties as recalled)"}
    OUT.write_text(json.dumps(out, indent=1))
    for r in rows:
        print(r)
    print(json.dumps(ratio, indent=0))


if __name__ == "__main__":
    main()

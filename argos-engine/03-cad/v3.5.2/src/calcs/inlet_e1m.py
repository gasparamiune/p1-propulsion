"""E1-M oxidiser inlet for CAD v3.4 (Mechanical, 2026-10-13): hydraulics (C1), Combustion conditions C1-C6, valve-to-seat
trapped volume, trapped-liquid heating and the relief / remote-vent requirements (RC items).

Concept E1-M (Mechanical variant of Combustion example E1, top entry; low inlet ROUTING O3b accepted by Combustion
low_inlet_check_v2p3 with conditions C1-C7):
  riser 3/8 x 0.035 in 316L (O3b coil end, z 62 above the pivot) -> straight up the case OD at r 39.5 (shield foil between
  riser and case) -> S-bend to r 37 just below the head -> socket-welded into a 316L saddle BLOCK screwed to a flat on the
  head-cap OD at 180 deg -> 8 mm passages in the block -> RADIAL 14 mm filter bore in the head cap holding a serviceable
  15 um cartridge (C5: downstream of the hose and of the riser weld) -> collecting annulus -> AXIAL 8 mm drilling at r 16 to the
  head top face -> O-ring face transfer into a bonnet boss -> axial 8 mm up to the bore top -> 8 mm cross-drilling entering
  the 10 mm manifold bore flush with its top (C2: flow-through, no dead leg above the entry).
  Pressure taps: upstream of the filter at the outer end of the block radial passage, downstream at the outer end of the
  bonnet cross-drilling (filter dP and manifold pressure for CF-3).

Hydraulic method = Combustion low_inlet_check_v2p3 (K-method, f 0.0218, Cd/K handbook ranges ASSUMED, same rest-of-line
items) so the numbers compare one-to-one with its V0 (v3.3 bonnet) / E1 / E2 rows.  Geometry below is the single source for
the CAD v3.4 features (parts_engine.py imports E1M) and is DESIGN (dimensions chosen here), not measured.  Volumes are
analytic ESTIMATES until the CAD v3.4 solids are measured (03-cad/checks/inlet_e1m_volumes.json replaces them).
"""
from __future__ import annotations
import json, math, hashlib, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "inlet_e1m_v1.json"
COMB_MIRROR = Path("/home/claude/work/mechanical/iface_snapshot/mirror/engine/02-combustion/data/v2/low_inlet_check_v2p3.json")

# ------------------------------------------------------------------------------------------------ geometry (DESIGN, mm)
# z values relative to the head stations: zt = head top face, zb = head-cap bottom (cap r 31.75 between zb and zt, 28 mm)
E1M = {
    "az_deg": 180.0,
    "flat_r": 30.5,                     # spot-faced flat on the cap OD for the block (half-chord 8.8 mm)
    "filter_bore": {"d": 14.0, "z_rel_zb": 14.0, "r_bottom": 9.5},     # radial bore, axis at zb + 14, flat bottom at r 9.5
    "cartridge": {"cap_od": 13.9, "cap_t": 3.0, "inlet_d": 8.0, "element_od": 12.0, "element_id": 7.0, "element_len": 16.0,
                  "rating_um": 15, "area_target_mm2": 1450, "seal_bore": "AS568-013 FKM on the cap OD (radial)",
                  "seal_face": "AS568-010 FKM, block face to cap (inlet)"},
    "axial_head": {"d": 8.0, "r": 16.0},                                # head top face -> filter bore
    "transfer_oring": "AS568-012 FKM 75 face seal in the bonnet bottom face around the 8 mm port (r 16)",
    "bonnet_boss": {"d": 16.0, "r": 16.0},                               # replaces the v3.3 riser boss (d 24 at r 22)
    "bonnet_axial": {"d": 8.0},
    "cross": {"d": 8.0, "top_flush_with_bore_top": True},               # axis 4 mm below the 10 mm bore top
    "block": {"z0_rel_zb": 0.5, "z1_rel_zb": 26.5, "half_w": 8.0, "passage_d": 8.0, "socket_r": 38.0, "socket_depth": 10.0,
              "screws": "2x M4 x 12 A4-70 (z zb+3.7 and zb+24.3 on the flat), Loctite 243", "material": "316L"},
    "riser": {"od": 9.525, "wall": 0.889, "r_run": 39.5, "r_socket": 38.0, "z_start_pivot": 80.0, "material": "316L 3/8 x 0.035 in seamless",
              "note": "lower end = weld of the -6 JIC adapter (FD-05, nose down at z 62-80, r 42); the O3b hose starts at z ~60 through a -6 JIC 90 deg swivel elbow hose end"},
    "shield": "0.2 mm polished 316 foil between case and riser on 2 stand-off clips (radiation; RC-04 sizes it)",
}
WALL_RULE = {"sweep_r_max_mm": "(67 - z sin 8 deg)/cos 8 deg above the pivot (140 mm bay, 3 mm moving clearance)"}

N2O_15C = 820.7; N2O_20C = 785.1; N2O_25C = 742.9           # kg/m3 (Combustion low_inlet_check_v2p3 CoolProp rows)
F_DARCY = 0.0218                                             # Combustion basis (smooth drawn tube, Re ~1e5)


def area(d):
    return math.pi * d * d / 4.0


def stations():
    """CAD v3.3 stations at the current pivot (iterated) - read from the CAD so the calc follows the model."""
    sys.path.insert(0, str(HERE.parent))
    import build
    P, S, reg, clog = build.build(include=("engine", "gimbal"), iterate_cg=True)      # pivot at the mid-burn CG (as the assembly)
    return {k: float(S[k]) for k in ("head_top", "head_bot", "z_ins_top", "bonnet_top")}


def path_items(st, mdot, rho):
    """K-method items of the E1-M inlet path from the riser socket to the manifold bore (filter element excluded: it is the
    Cv >= 2.2 item of the rest of the line, OI-7)."""
    g = E1M
    zt, zb = st["head_top"], st["head_bot"]
    bore_top = zt + 26.0                                                    # 10 mm bore in the bonnet ends at zb0 + 26 (v3.3)
    z_f = zb + g["filter_bore"]["z_rel_zb"]
    z_x = bore_top - g["cross"]["d"] / 2.0
    d8 = g["block"]["passage_d"]
    A8 = area(d8)
    ann = area(g["filter_bore"]["d"]) - area(g["cartridge"]["element_od"])
    L = {"block_vertical": (z_f - (zb + g["block"]["z0_rel_zb"] + g["block"]["socket_depth"])) + d8 / 2,
         "block_radial": g["block"]["socket_r"] - g["flat_r"],
         "head_axial": zt - (z_f + g["filter_bore"]["d"] / 2.0),
         "bonnet_axial": (z_x + d8 / 2.0) - zt,
         "cross": g["axial_head"]["r"] - 5.0}
    rows = []

    def add(name, A, K=0.0, Lf=0.0, D=None):
        v = mdot / (rho * A * 1e-6)
        q = 0.5 * rho * v * v
        Kf = F_DARCY * Lf / D if Lf else 0.0
        rows.append({"name": name, "A_mm2": round(A, 2), "v_m_s": round(v, 3), "q_kPa": round(q / 1e3, 3), "K": K, "K_fric": round(Kf, 4),
                     "dp_kPa": round((K + Kf) * q / 1e3, 3)})
    add("riser 7.75 ID -> 8 mm block bore (expansion, K ~0)", A8, 0.0)
    add("90 deg drilled intersection into the radial 8 mm passage", A8, 1.1)
    add(f"block 8 mm friction ({L['block_vertical']:.1f} + {L['block_radial']:.1f} mm)", A8, 0.0, L["block_vertical"] + L["block_radial"], d8)
    add("dump into the cartridge core (8 mm inlet)", A8, 1.0)
    # collecting annulus between element OD and bore: flow grows from 0 to full over the element length -> mean q ~ 1/3 of the
    # exit q; Dh = 2 x radial gap; friction over the element length, plus K 1.1 for the turn into the axial drilling
    gap = (g["filter_bore"]["d"] - g["cartridge"]["element_od"]) / 2.0
    v_ann = mdot / (rho * ann * 1e-6)
    q_ann = 0.5 * rho * v_ann ** 2
    k_ann = 0.03 * g["cartridge"]["element_len"] / (2 * gap) / 3.0
    rows.append({"name": f"collecting annulus {ann:.1f} mm2 (gap {gap:.1f} mm, laminar-ish f 0.03, mean q/3)", "A_mm2": round(ann, 2),
                 "v_m_s": round(v_ann, 3), "q_kPa": round(q_ann / 1e3, 3), "K": 0.0, "K_fric": round(k_ann, 4), "dp_kPa": round(k_ann * q_ann / 1e3, 3)})
    add("turn from the annulus into the axial 8 mm drilling", A8, 1.1)
    add(f"axial 8 mm friction head + bonnet ({L['head_axial']:.1f} + {L['bonnet_axial']:.1f} mm)", A8, 0.0, L["head_axial"] + L["bonnet_axial"], d8)
    add("face-seal transfer head -> bonnet (0.2 mm misalignment step)", A8, 0.2)
    add("90 deg into the 8 mm cross-drilling", A8, 1.1)
    add(f"cross-drilling friction ({L['cross']:.1f} mm)", A8, 0.0, L["cross"], d8)
    add("exit into the 10 mm bore (top entry)", A8, 1.0)
    return rows, L, {"z_filter_axis": z_f, "z_cross_axis": z_x, "bore_top": bore_top, "annulus_mm2": ann}


def riser_len(st):
    r = E1M["riser"]
    zb = st["head_bot"]
    z_sock = zb + E1M["block"]["z0_rel_zb"]
    s1 = 3.0 + math.hypot(12.0, 42.0 - r["r_run"]) + 0.5                # 3 mm straight + S-bend r 42 -> 39.5 over 12 mm above the adapter weld
    s2 = math.hypot(15.0, r["r_run"] - r["r_socket"]) + 0.5              # S-bend r 39.5 -> 38 over the last 15 mm
    straight = (z_sock - 15.0) - (r["z_start_pivot"] + 15.0)
    return s1 + straight + s2 + E1M["block"]["socket_depth"], {"s_bend_1": round(s1, 1), "straight": round(straight, 1), "s_bend_2": round(s2, 1)}


def rest_of_line(rho, mdot, L_riser_m, comb):
    """Combustion v2p3 rest-of-line items scaled to (rho, mdot); riser friction re-done for the E1-M riser length."""
    base = comb["1_losses_budget_flash"]["V0_v33_bonnet_reference"]["0p26_15C"]["rest_items_Pa"]
    sc = (N2O_15C / rho) * (mdot / 0.26) ** 2
    items = {k: v * sc for k, v in base.items()}
    d = E1M["riser"]["od"] - 2 * E1M["riser"]["wall"]
    v = mdot / (rho * area(d) * 1e-6)
    q = 0.5 * rho * v * v
    items.pop("riser_0p07m_plus_S_bend")
    items["riser_E1M_friction_plus_2_S_bends"] = (F_DARCY * L_riser_m * 1e3 / d + 2 * 0.2) * q
    return items


def trapped(Vcm3):
    import CoolProp.CoolProp as CP
    out = {}
    for TC in (15.0, 20.0, 25.0):
        T0 = TC + 273.15
        rho = CP.PropsSI("D", "T", T0, "Q", 0, "NitrousOxide")
        Ps = CP.PropsSI("P", "T", T0, "Q", 0, "NitrousOxide")
        lo, hi = T0 + 1e-3, T0 + 30.0
        for _ in range(80):                                               # isochoric heating of liquid-full volume to 7.5 MPa
            mid = 0.5 * (lo + hi)
            if CP.PropsSI("P", "T", mid, "D", rho, "NitrousOxide") > 7.5e6:
                hi = mid
            else:
                lo = mid
        dPdT = (CP.PropsSI("P", "T", T0 + 0.5, "D", rho, "NitrousOxide") - CP.PropsSI("P", "T", T0 + 0.01, "D", rho, "NitrousOxide")) / 0.49
        beta = -(CP.PropsSI("D", "T", T0 + 0.25, "P", Ps + 2e5, "NitrousOxide") - CP.PropsSI("D", "T", T0 - 0.25, "P", Ps + 2e5, "NitrousOxide")) / 0.5 / rho
        out[f"{TC:.0f}C"] = {"rho_kg_m3": round(rho, 1), "mass_g": round(rho * Vcm3 * 1e-3, 2), "dPdT_isochoric_bar_K": round(dPdT / 1e5, 3),
                             "dT_liquid_full_to_7p5MPa_K": round(0.5 * (lo + hi) - T0, 2), "beta_1_K": round(beta, 5)}
    return out


def main():
    comb = json.loads(COMB_MIRROR.read_text())
    st = stations()
    g = E1M
    res = {"id": "inlet_e1m", "version": "v1", "date": "2026-10-13", "owner": "Mechanical", "script": "03-cad/src/calcs/inlet_e1m.py",
           "basis": {"method": "Combustion low_inlet_check_v2p3 K-method (same f, K ranges, rest-of-line items)",
                     "combustion_file_sha256_16": hashlib.sha256(COMB_MIRROR.read_bytes()).hexdigest()[:16],
                     "stations_mm": {k: round(v, 3) for k, v in st.items()}, "tag": "DESIGN geometry, ASSUMED K values, ESTIMATE volumes"},
           "geometry": E1M, "sweep_rule": WALL_RULE}
    Lr, Lparts = riser_len(st)
    res["riser"] = {"length_mm": round(Lr, 1), "parts_mm": Lparts, "ID_mm": round(g["riser"]["od"] - 2 * g["riser"]["wall"], 3),
                    "A_mm2": round(area(g["riser"]["od"] - 2 * g["riser"]["wall"]), 2)}
    cases = {"0p26_15C": (0.26, N2O_15C), "0p241_20C": (0.241, N2O_20C), "0p26_25C": (0.26, N2O_25C)}
    hyd = {}
    for nm, (md, rho) in cases.items():
        rows, L, zz = path_items(st, md, rho)
        inlet = sum(r["dp_kPa"] for r in rows) * 1e3
        rest = rest_of_line(rho, md, Lr * 1e-3, comb)
        tot = inlet + sum(rest.values())
        budget = 270400.0 if md == 0.26 else 232300.0
        hyd[nm] = {"inlet_path_Pa": round(inlet), "sections": rows, "rest_items_Pa": {k: round(v) for k, v in rest.items()},
                   "rest_of_line_Pa": round(sum(rest.values())), "total_line_Pa": round(tot), "budget_Pa": budget, "within_budget": tot <= budget}
    res["lengths_mm"] = {k: round(v, 2) for k, v in L.items()}
    res["stations_derived_mm"] = {k: round(v, 3) for k, v in zz.items()}
    res["hydraulics"] = hyd
    ref = comb["1_losses_budget_flash"]
    res["compare_15C_0p26"] = {"V0_v33_inlet_Pa": ref["V0_v33_bonnet_reference"]["0p26_15C"]["inlet_dp_Pa"],
                               "E1_example_inlet_Pa": ref["E1_top_entry_7mm"]["0p26_15C"]["inlet_dp_Pa"],
                               "E2_example_inlet_Pa": ref["E2_low_4feeds_4p5mm"]["0p26_15C"]["inlet_dp_Pa"],
                               "E1M_inlet_Pa": hyd["0p26_15C"]["inlet_path_Pa"]}
    # ------------------------------------------------------------------ volumes (ESTIMATE until measured on the v3.4 solids)
    c = g["cartridge"]
    fb = g["filter_bore"]
    bore_len = g["flat_r"] - fb["r_bottom"]
    v_bore = area(fb["d"]) * bore_len
    v_cart_solid = area(c["cap_od"]) * c["cap_t"] - area(c["inlet_d"]) * c["cap_t"] + 0.30 * (area(c["element_od"]) - area(c["element_id"])) * c["element_len"] \
        + 2 * (area(c["element_od"]) - area(c["element_id"])) * 1.0
    A8 = area(8.0)
    vol = {"hose_O3b": 12.35, "fittings_coil_end": 1.0, "adapter_FD05_18mm": round(area(7.75) * 18.0 / 1e3, 3),
           "riser": area(g["riser"]["od"] - 2 * g["riser"]["wall"]) * (Lr - g["block"]["socket_depth"]) / 1e3,
           "block_passages": (A8 * (L["block_vertical"] + L["block_radial"] + 4.0)) / 1e3,
           "filter_bore_open": (v_bore - v_cart_solid) / 1e3,
           "head_axial": A8 * L["head_axial"] / 1e3, "bonnet_axial": A8 * L["bonnet_axial"] / 1e3,
           "cross_and_tap_stub": A8 * (L["cross"] + 4.0) / 1e3,
           "manifold_10mm_bore_annulus": 4.51}
    vol = {k: round(v, 3) for k, v in vol.items()}
    Vt = sum(vol.values())
    res["valve_to_seat_volume_cm3"] = {"items": vol, "total": round(Vt, 2),
                                       "tag": "ESTIMATE: hose 12.35 / fittings 1.0 / manifold 4.51 from Combustion v2p3 (DERIVED/ASSUMED); E1-M items analytic from the design geometry; cartridge solid fraction 30 % ASSUMED",
                                       "vs_combustion_O3b_valve_at_coil": 21.42}
    res["trapped_liquid"] = trapped(Vt)
    # ------------------------------------------------------------------ conditions
    secs = [r["A_mm2"] for r in hyd["0p26_15C"]["sections"]]
    rest15 = hyd["0p26_15C"]
    res["conditions"] = {
        "C1": {"min_section_mm2": min(secs + [res["riser"]["A_mm2"]]), "req_mm2": 35.0,
               "v_max_m_s_25C": max(r["v_m_s"] for r in hyd["0p26_25C"]["sections"]),
               "inlet_path_bar_15C": round(rest15["inlet_path_Pa"] / 1e5, 3), "req_bar": 1.28, "target_bar": 1.0,
               "line_total_bar_15C": round(rest15["total_line_Pa"] / 1e5, 3), "line_req_bar": 2.70,
               "pass": bool(min(secs) >= 35.0 and rest15["inlet_path_Pa"] <= 128200 and rest15["total_line_Pa"] <= 270000)},
        "C2": {"entry": "top of the 10 mm bore (cross-drilling top edge flush with the bore top)", "dead_leg_above_entry_cm3": 0.0,
               "pass": True, "note": "flow-through manifold; filter bore is in series (flow-through), not a dead leg"},
        "C3": {"applies": False, "note": "single top entry as v3.3 (no low entry): feed symmetry as v3.3 / Combustion E1"},
        "C4": {"pass": True, "note": "no N2O passage borders a chamber-gas seal: filter bore, axial drillings and transfer are in solid metal above "
                                      "the plug glands; every N2O seal (block face, cartridge cap, transfer, bonnet face) separates N2O from AMBIENT"},
        "C5": {"pass": True, "note": "15 um cartridge in the head cap, downstream of the hose and of the riser socket weld; v3.3 bonnet screen seat deleted"},
        "C6": {"valve_to_seat_cm3": round(Vt, 2), "relief_required": True, "see": "relief_spec"},
        "C7": {"owner": "sequence owners (GNC / Electronics)", "note": "pre-purge or T-gated check; volume +7 cm3 vs O3b estimate -> purge time scales ~ with volume"},
    }
    # ------------------------------------------------------------------ relief / vent requirements (RC items)
    beta20 = res["trapped_liquid"]["20C"]["beta_1_K"]
    dTdt = 2.0                                                              # K/s, ASSUMED upper bound for the wetted metal right after shutdown
    q_th = Vt * 1e-6 * beta20 * dTdt
    res["relief_spec"] = {
        "trapped_volume_relief": {
            "location": "teed at the NC valve outlet (coil fixed end, OFF the gimbal): one liquid volume valve->seat, no internal check, so one "
                        "device covers hose + riser + block + filter + manifold",
            "P_set": "PARAMETER P_set_trapped: must lie above the highest normal static pressure at that point (tank MEOP 7.0 MPa) and reach full "
                     "flow at <= 7.5 MPa (Combustion C6): window 7.0-7.5 MPa incl. set tolerance and accumulation (e.g. 7.2 MPa +/-3 %): "
                     "TIGHT -> lead decision: lower the tank relief set / MEOP or accept a burst disc at 7.5 MPa",
            "capacity": {"thermal_expansion_cm3_s": round(q_th * 1e6, 3), "basis": f"V {Vt:.1f} cm3 x beta {beta20} 1/K x dT/dt {dTdt} K/s (ASSUMED bound)",
                         "required_g_s_with_x2": round(2 * q_th * 785.1 * 1e3, 3), "tag": "DERIVED"},
            "destination": "overboard through a short tube pointing aft-outboard, away from the torch, the hot case and the servo bay",
            "candidate": "proportional relief valve, 1/8-1/4 in, soft seat FKM, N2O/oxygen-clean (Swagelok R3A class AS RECALLED, TO-QUOTE, "
                         "Sønderborg DK-6400); mass ~60-110 g ASSUMED (off the gimbal)",
            "alternative_rejected": "check valve in parallel with the NC valve back to the tank: a forward leak of the check bypasses the NC "
                                    "isolation valve (ENG-05/ENG-16 fail-safe shutoff) -> not baselined"},
        "tank_relief": {"P_set": "PARAMETER P_set_tank (set below the tank proof, T-vent per ENG-09)", "destination": "overboard, away from hot parts",
                        "note": "Combustion/lead own the set point; Mechanical needs mass and envelope for the airframe ICD"},
        "remote_vent": {"type": "NC solenoid valve on the tank vapour space, ground-commanded (ENG-16 remote vent)",
                        "requirements": ">= 7.5 MPa rating, N2O-compatible seals, orifice >= 1 mm, coil 12 V class, fails closed",
                        "mass_g": "UNKNOWN (TO-QUOTE; ~80-200 g class ASSUMED)", "envelope": "UNKNOWN (TO-QUOTE)", "port": "1/8 NPT or G1/8 class (TO-QUOTE)"},
    }
    res["open_items"] = ["measure the v3.4 solids (volumes, sweep of the block / riser S-bend) -> checks/inlet_e1m_volumes.json",
                         "cartridge vendor (custom pleated 15 um, area >= 1450 mm2, Cv >= 2.2 incl. housing): TO-QUOTE",
                         "relief set-point window 7.0-7.5 MPa conflicts with set tolerance: lead decision",
                         "riser + block thermal (RC-04): case OD 130-312 C under the riser path (B1 v2 hi) -> shield sizing on the v3 histories"]
    OUT.write_text(json.dumps(res, indent=1))
    print(json.dumps({"inlet_bar_15C": res["conditions"]["C1"]["inlet_path_bar_15C"], "line_bar_15C": res["conditions"]["C1"]["line_total_bar_15C"],
                      "C1_pass": res["conditions"]["C1"]["pass"], "V_valve_to_seat_cm3": round(Vt, 2), "riser_mm": res["riser"]["length_mm"],
                      "trapped": res["trapped_liquid"], "compare": res["compare_15C_0p26"], "out": str(OUT)}, indent=1))


if __name__ == "__main__":
    main()

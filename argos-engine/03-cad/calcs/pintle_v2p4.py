"""Pintle drive v3.4 - jam load at the confirmed pintle-rail bound, v2.4 (03-cad/src/calcs, 2026-10-13, Mechanical).

Lead decision 2026-10-13 (CHANGELOG) on Electronics pintle_rail_v3 (hub 06-electronics/results/pintle_rail_v3.json, sha256/16
694e471732ad070a, mirrored in iface_snapshot/mirror/engine/06-electronics/results):
  DESIGN JAM   needle held closed, HV69 stalled opening at 7.70 V (7.62 V static worst + 1 % line-step allowance, ASSUMED until
               B-PWR-2), -10 % spring, pin friction 0 -> link tension 831.6 N.  Criterion as v2.3: bearing / guide static
               capacity s0 >= 1.0, every stress <= Fty (exceptional event, parts replaced after any recorded jam).
  FAILURE CASE FB-open fault clamped by the LTC4365 OV disconnect (trip 8.06-8.34 V): the v2.3 8.4 V row 933.7 N (bounds 8.34 V,
               924.9 N) -> no yield, no rupture, bearing s0 >= 1.0.  The 8.46 V spike lasts <= 6 us (then the servo is
               unpowered): far below the motor's electrical/mechanical time constants, so it adds no static load.
  LOAD RELEASE 7.97 V peak, current falling (not coincident with a stall), below the HV69 8.2 V rating: no mechanical load case.
Everything else of v2.3 (C1/C2, guide and eye selection, break-out, MECO, travel fallbacks, filter) is unchanged: this script imports
pintle_v2p3 read-only, copies the v2.3 record (pintle_inline_v34_v2p3.json, sha256/16 9356082d62c4f2ef) and replaces only the jam
sections.  Planned CAD v3.4 dimensions used for the link eye are tagged PLANNED-v3.4 and are checked again on the solid.
"""
from __future__ import annotations
import json, math, hashlib, copy
from pathlib import Path

HERE = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(HERE))
import pintle_v2p3 as p3

ELEC = Path("/home/claude/work/mechanical/iface_snapshot/mirror/engine/06-electronics/results/pintle_rail_v3.json")
V23 = HERE / "pintle_inline_v34_v2p3.json"

RAIL_V = {
    "7.4": "HV69 table point (stall 0.90 N m); C2 basis",
    "7.505": "Electronics v2.1 regulator upper tolerance (history)",
    "7.6": "v2.3 design value (history)",
    "7.62": "Electronics pintle_rail_v3: static worst case (divider B 24.9k/4.75k 0.1 % 10 ppm/K, linear 7.616 V, RSS 7.600 V) - DERIVED",
    "7.7": "Electronics pintle_rail_v3: static worst + 1 % line step during a stall (ASSUMED allowance, <= ~1 ms, B-PWR-2 measures) - "
           "DESIGN JAM (lead 2026-10-13)",
    "8.2": "HV69 voltage rating / stall-table top (retailer copies of MKS data)",
    "8.34": "Electronics pintle_rail_v3: LTC4365 OV trip maximum (FB-open fault can park the rail just below it) - FAILURE CASE",
    "8.4": "v2.3 'regulator failed through' row (EXTRAPOLATED stall torque) - the lead's failure-case load 933.7 N, bounds 8.34 V",
}
DESIGN_V, FAIL_V = 7.70, 8.34
F_FAIL_LEAD = 933.7          # lead 2026-10-13: "Check 933.7 N at 8.34 V (your 8.4 V row) as a failure case"
F_DESIGN_LEAD = 831.6        # lead 2026-10-13: "Design jam load is 831.6 N at 7.70 V"

MAT = {
    "17-4PH_H900": {"Ftu": 1310.0, "Fty": 1170.0, "tag": "AMS 5643 minimum 190/170 ksi, AS RECALLED - TO-VERIFY against MMPDS / mill cert"},
    "17-4PH_H1150": {"Ftu": 931.0, "Fty": 724.0, "tag": "AMS 5643 minimum 135/105 ksi, AS RECALLED (v2.3 cites engmat Fty 724) - TO-VERIFY"},
    "AL6061-T6": {"Ftu": 290.0, "Fty": 241.0, "Fsu": 186.0, "tag": "MMPDS-class minimum 42/35/27 ksi, AS RECALLED - TO-VERIFY"},
    "shear_rule": "steel: shear yield 0.577 Fty (von Mises), shear rupture 0.60 Ftu (ASSUMED ratio); Al: Fsu as listed, shear yield 0.577 Fty",
}
DU_STATIC_MPa = (250.0, "PTFE-lined steel-backed (DU class) bush static load limit, commonly quoted ~250 MPa - AS RECALLED, maker value TO-VERIFY")
LINK_EYE = {"OD_mm": 8.0, "bush_bore_mm": 4.5, "t_mm": 4.0, "shank_mm": [4.0, 3.0], "material": "17-4PH_H1150",
            "tag": "PLANNED-v3.4: link 28 mm centres, eyes OD 8 x 4 mm with a 3 x 4.5 x 4 PTFE-lined bush (maker part TO-SELECT), shank 4 x 3 mm"}
LAYOUT = {"a_mm": 9.0 - 2.0, "b_mm": 9.0 - 2.5, "y_l_mm": 11.0, "crank_pin_span_mm": 6.0, "crank_pin_d_mm": 3.0, "stem_thread_engagement_mm": 4.5,
          "tag": "v2.3 layout (link plane to bearing A / B centres, link offset y_l, crank pin span) - ASSUMED, re-checked on the v3.4 solid"}


def F_link(V, mu_p=0.0, r_p=1.5):
    """v2.3 jam formula (identical): (T_stall(V) - 0.9 T0) / (dx/dphi at closed + mu_p r_p pin_factor)."""
    dx0 = p3.dxdphi(p3.CRANK["phi_closed"]) * 1e-3
    return (p3.stall(V) - (1 - p3.SPRING["tol"]) * p3.SPRING["T0_Nm"]) / (dx0 + mu_p * r_p * 1e-3 * p3.pin_factor(p3.CRANK["phi_closed"]))


def ms(allow, stress):
    return round(allow / stress - 1.0, 2)


def components(F):
    """Static margins of every part in the jam load path at link tension F (N)."""
    a_, b_ = LAYOUT["a_mm"], LAYOUT["b_mm"]
    RA, RB = F * b_ / (a_ + b_), F * a_ / (a_ + b_)
    gH = p3.GUIDES["MGN09H"]
    psi = p3.psi_of(p3.CRANK["phi_closed"])
    M = F * LAYOUT["y_l_mm"] * 1e-3
    side = F * math.tan(psi)
    H9, H11, AL = MAT["17-4PH_H900"], MAT["17-4PH_H1150"], MAT["AL6061-T6"]
    d_cp = LAYOUT["crank_pin_d_mm"]
    s_cp_b = F * LAYOUT["crank_pin_span_mm"] / 4.0 / (math.pi * d_cp ** 3 / 32.0)
    tau_cp = F / (math.pi / 4 * d_cp ** 2)
    tau_lp = F / (2 * math.pi / 4 * 3.0 ** 2)
    s_stem = F / p3.A_STEM
    s_thr = F / 5.03
    tau_cthr = F / (math.pi * 3.0 * LAYOUT["stem_thread_engagement_mm"] * 0.6)
    p_bush = F / (3.0 * 4.0)
    e = LINK_EYE
    s_net = F / ((e["OD_mm"] - e["bush_bore_mm"]) * e["t_mm"])
    A_so = 2 * e["t_mm"] * (e["OD_mm"] / 2 - e["bush_bore_mm"] / 2 * math.cos(math.radians(40.0)))
    tau_so = F / A_so
    s_shank = F / (e["shank_mm"][0] * e["shank_mm"][1])
    rows = {
        "bearing_A_NB701": {"P0_N": round(RA, 1), "C0r_N": p3.CRANK_BEARINGS["A_NB701"][3], "s0": round(p3.CRANK_BEARINGS["A_NB701"][3] / RA, 2)},
        "bearing_B_6800": {"P0_N": round(RB, 1), "C0r_N": p3.CRANK_BEARINGS["B_6800"][3], "s0": round(p3.CRANK_BEARINGS["B_6800"][3] / RB, 2)},
        "guide_MGN09H": {"M_Nm": round(M, 2), "M0Y_Nm": gH["M0Y_Nm"], "s0_moment": round(gH["M0Y_Nm"] / M, 2), "side_load_N": round(side, 1),
                         "s0_combined": round(1.0 / (side / gH["C0_N"] + M / gH["M0Y_Nm"]), 2),
                         "note": "along-rail force is not carried by the block (rolling guide): it passes link -> carriage -> stem"},
        "crank_pin_bending_H900": {"MPa": round(s_cp_b, 1), "MS_yield": ms(H9["Fty"], s_cp_b), "MS_ult": ms(H9["Ftu"], s_cp_b),
                                   "model": "3 mm pin, span 6 mm simply supported, M = F L / 4 (conservative)"},
        "crank_pin_shear_H900": {"MPa": round(tau_cp, 1), "MS_yield": ms(0.577 * H9["Fty"], tau_cp), "MS_ult": ms(0.60 * H9["Ftu"], tau_cp)},
        "link_pins_double_shear_H900": {"MPa": round(tau_lp, 1), "MS_yield": ms(0.577 * H9["Fty"], tau_lp), "MS_ult": ms(0.60 * H9["Ftu"], tau_lp)},
        "eye_bush_bearing_pressure": {"MPa": round(p_bush, 1), "limit_MPa": DU_STATIC_MPa[0], "ratio": round(p_bush / DU_STATIC_MPa[0], 2),
                                      "tag": DU_STATIC_MPa[1]},
        "link_eye_net_tension_H1150": {"MPa": round(s_net, 1), "MS_yield": ms(H11["Fty"], s_net), "MS_ult": ms(H11["Ftu"], s_net),
                                       "note": "nominal net section (OD - bore) t; lug peak Kt ~2.5-3 local, covered by MS_yield > 1.5"},
        "link_eye_shear_out_H1150": {"MPa": round(tau_so, 1), "MS_yield": ms(0.577 * H11["Fty"], tau_so), "MS_ult": ms(0.60 * H11["Ftu"], tau_so),
                                     "model": "A = 2 t (e - D/2 cos 40 deg), e = OD/2"},
        "link_shank_tension_H1150": {"MPa": round(s_shank, 1), "MS_yield": ms(H11["Fty"], s_shank), "MS_ult": ms(H11["Ftu"], s_shank)},
        "stem_3mm_tension_H1150": {"MPa": round(s_stem, 1), "MS_yield": ms(H11["Fty"], s_stem), "MS_ult": ms(H11["Ftu"], s_stem)},
        "stem_M3_thread_tensile_H1150": {"MPa": round(s_thr, 1), "MS_yield": ms(H11["Fty"], s_thr), "MS_ult": ms(H11["Ftu"], s_thr),
                                         "model": "tensile stress area 5.03 mm2 (ISO 898)"},
        "carriage_internal_thread_shear_AL6061T6": {"MPa": round(tau_cthr, 1), "MS_yield": ms(0.577 * AL["Fty"], tau_cthr), "MS_ult": ms(AL["Fsu"], tau_cthr),
                                                    "model": "pi d L 0.6, d 3, L 4.5 mm (v2.3); a steel insert is not needed on strength"},
    }
    return rows


def verdict(rows, failure):
    bad = []
    for k, r in rows.items():
        for key in ("s0", "s0_moment", "s0_combined"):
            if key in r and r[key] < 1.0:
                bad.append(f"{k} {key} {r[key]}")
        if "MS_yield" in r and r["MS_yield"] < 0:
            bad.append(f"{k} yield MS {r['MS_yield']}")
        if failure and "MS_ult" in r and r["MS_ult"] < 0:
            bad.append(f"{k} rupture MS {r['MS_ult']}")
        if "ratio" in r and r["ratio"] > 1.0:
            bad.append(f"{k} ratio {r['ratio']}")
    return {"pass": not bad, "failures": bad}


def main():
    v23 = json.loads(V23.read_text())
    out = copy.deepcopy(v23)
    elec = json.loads(ELEC.read_text())
    out.update({"version": "v2.4", "date": "2026-10-13", "script": "03-cad/src/calcs/pintle_v2p4.py (imports pintle_v2p3 read-only)",
                "supersedes": "pintle_inline_v34_v2p3.json (kept as history, sha256/16 %s)" % hashlib.sha256(V23.read_bytes()).hexdigest()[:16]})
    out["inputs"]["rail_voltages"] = RAIL_V
    out["inputs"]["electronics_rail"] = {"file": "06-electronics/results/pintle_rail_v3.json", "sha256_16": hashlib.sha256(ELEC.read_bytes()).hexdigest()[:16],
                                         "V_rail_max_static_V": elec["publish"]["V_rail_max_static_V"],
                                         "V_rail_line_step_during_stall_V": elec["publish"]["V_rail_line_step_during_stall_V"],
                                         "V_rail_failure_static_max_V": elec["publish"]["V_rail_failure_static_max_V"],
                                         "V_rail_failure_peak_V": elec["publish"]["V_rail_failure_peak_V"],
                                         "V_rail_peak_load_release_V": elec["publish"]["V_rail_peak_load_release_V"],
                                         "jam_detection": elec["publish"]["jam_detection"]}
    out["inputs"]["materials"] = MAT
    out["inputs"]["link_eye_planned"] = LINK_EYE
    out["inputs"]["layout"] = LAYOUT
    out["criteria"]["jam"] = ("DESIGN: needle held closed, HV69 stalled opening at 7.70 V, -10 % spring, pin friction 0: bearing/guide s0 >= 1.0 and every "
                              "stress <= Fty (exceptional event, parts replaced after any recorded jam). FAILURE CASE: 933.7 N (LTC4365-clamped FB-open "
                              "fault, 8.34 V bounded by the 8.4 V row): no yield, no rupture, bearing s0 >= 1.0")
    jam = {}
    for V in (7.4, 7.505, 7.6, 7.62, 7.70, 8.2, 8.34, 8.4):
        row = {"T_stall_Nm": round(p3.stall(V), 4), "extrapolated": V > 8.2, "F_link_N_mu_p_0": round(F_link(V), 1),
               "F_link_N_plain_mu_0.15": round(F_link(V, 0.15), 1), "basis": RAIL_V.get(f"{V:g}", "")}
        jam[f"{V:g}V"] = row
    F_d_calc = jam["7.7V"]["F_link_N_mu_p_0"]
    F_d = max(F_DESIGN_LEAD, F_d_calc)          # lead value 831.6 N (linear between the rounded 7.6/8.2 V rows); this formula gives 831.5 N
    F_f_calc = jam["8.34V"]["F_link_N_mu_p_0"]
    F_f = max(F_FAIL_LEAD, F_f_calc)
    assert abs(F_d_calc - 831.6) < 0.15, F_d_calc
    assert abs(jam["8.4V"]["F_link_N_mu_p_0"] - 933.7) < 0.05
    out["jam"] = {"by_rail_voltage": jam, "design_F_link_N": F_d, "failure_F_link_N": F_f,
                  "basis": "DESIGN 7.70 V (Electronics pintle_rail_v3 static worst 7.62 V + 1 % line-step allowance, lead 2026-10-13), -10 % spring, "
                           "pin friction 0 (friction cannot be relied on to absorb the stall torque). FAILURE 933.7 N = the 8.4 V row, which bounds "
                           f"the LTC4365 trip maximum 8.34 V ({F_f_calc:.1f} N)",
                  "direction": v23["jam"]["direction"],
                  "stall_extrapolation": "HV69 stall table ends at 8.2 V (1.00 N m); 8.34 / 8.4 V use the 7.4-8.2 V slope (EXTRAPOLATED)",
                  "history": {"v2.3_design_F_link_N": v23["jam"]["design_F_link_N"], "v2.3_basis": v23["jam"]["basis"]}}
    # link eyes and guide tables restated at the new design jam (selection unchanged)
    F_hold = (1 + p3.SPRING["tol"]) * p3.SPRING["T0_Nm"] / (p3.dxdphi(p3.CRANK["phi_closed"]) * 1e-3)
    for nm, e in p3.EYES.items():
        r = out["link_eyes"][nm]
        if e["C0r_N"]:
            r["s0_jam"] = round(e["C0r_N"] / F_d, 2)
            r["capacity_ok"] = bool(r["s0_closed_hold"] >= 2.0 and r["s0_jam"] >= 1.0)
        else:
            p = F_d / (e["pin_d_mm"] * e["eye_w_mm"])
            r["bearing_pressure_jam_MPa"] = round(p, 1)
            r["pin_double_shear_jam_MPa"] = round(F_d / (2 * math.pi / 4 * e["pin_d_mm"] ** 2), 1)
            r["capacity_note"] = ("static bearing pressure %.0f MPa at the 7.70 V jam: PTFE-lined steel-backed (DU class) static limit is a maker value "
                                  "(TO-VERIFY, commonly quoted ~250 MPa AS RECALLED); hardened pin H900" % p)
        r["selectable"] = bool(r["capacity_ok"] and r["fits_swept_cone"])
    gs = out["guide_selection"]
    y_l = LAYOUT["y_l_mm"]
    gs["M_jam_Nm"] = round(F_d * y_l * 1e-3, 2)
    for nm, gd in p3.GUIDES.items():
        b = gs["blocks"][nm]
        b["s0_M_jam"] = round(gd["M0Y_Nm"] / (F_d * y_l * 1e-3), 2)
        b["ok"] = bool(b["s0_M_jam"] >= 1.0 and b["s0_M_hold"] >= 2.0)
    sel_ok = [nm for nm, b in gs["blocks"].items() if b["ok"]]
    gs["selection_check_v2p4"] = {"blocks_ok_at_7V70": sel_ok, "MGN09H_still_selected": "MGN09H" in sel_ok}
    # component margins
    rows_d = components(F_d)
    rows_f = components(F_f)
    out["jam_component_margins"] = {"F_link_N": F_d, "case": "DESIGN jam 7.70 V", "rows": rows_d, "verdict": verdict(rows_d, False),
                                    "rule": v23["jam_component_margins"]["rule"],
                                    "history_v2p3_at_817N": {k: v for k, v in v23["jam_component_margins"].items() if k not in ("allowables", "rule")}}
    out["jam_failure_case"] = {"F_link_N": F_f, "case": "FAILURE: FB-open fault clamped by the LTC4365 OV disconnect (8.06-8.34 V); 933.7 N bounds 8.34 V",
                               "criteria": "no yield (MS_yield >= 0), no rupture (MS_ult >= 0), bearing / guide s0 >= 1.0; no factor of safety "
                                           "(failure case, parts replaced)", "rows": rows_f, "verdict": verdict(rows_f, True),
                               "hv69_note": "8.34 V exceeds the HV69 8.2 V rating: servo survival is an Electronics/MKS item; the mechanical load path "
                                            "holds. Firmware v2.6 stall detection 0.10 s, ABORT releases the ARM bus after a further 0.10 s"}
    worst = {}
    for lab, rows in (("design", rows_d), ("failure", rows_f)):
        s0s = {k: min(v[x] for x in ("s0", "s0_moment", "s0_combined") if x in v) for k, v in rows.items() if any(x in v for x in ("s0", "s0_moment", "s0_combined"))}
        msy = {k: v["MS_yield"] for k, v in rows.items() if "MS_yield" in v}
        msu = {k: v["MS_ult"] for k, v in rows.items() if "MS_ult" in v}
        worst[lab] = {"min_s0": min(s0s.items(), key=lambda kv: kv[1]), "min_MS_yield": min(msy.items(), key=lambda kv: kv[1]),
                      "min_MS_ult": min(msu.items(), key=lambda kv: kv[1])}
    out["jam_summary"] = worst
    out["changes_from_v2p3"] = [
        "jam design load 817.0 N (7.6 V) -> 831.6 N (7.70 V, Electronics pintle_rail_v3 + lead 2026-10-13); every s0 / stress restated",
        "new failure case 933.7 N (LTC4365-clamped FB-open fault, 8.34 V bounded by the 8.4 V row): no yield, no rupture, s0 >= 1.0",
        "link-eye (PLANNED-v3.4 OD 8 x 4 mm, bush bore 4.5), link shank and crank-pin shear rows added to the load-path check",
        "C1/C2, guide and eye selection, break-out, MECO, travel fallbacks and filter unchanged (copied from v2.3)"]
    oi = [x for x in v23["open_items"] if not x.startswith("Electronics: confirm the pintle-rail")]
    oi.append("B-PWR-2 (Electronics): the 1 % line-step allowance behind 7.70 V is ASSUMED; if the measured static or transient upper value "
              f"exceeds 7.70 V, re-state the jam (no margin is close: min s0 at 7.70 V = {worst['design']['min_s0'][1]:.2f})")
    oi.append("MKS: HV69 behaviour above its 8.2 V rating (failure case 8.34 V) and storage temperature")
    out["open_items"] = oi
    p = HERE / "pintle_inline_v34_v2p4.json"
    p.write_text(json.dumps(out, indent=1, default=float))
    print("jam rows", json.dumps(jam))
    print("design", F_d, json.dumps(out["jam_component_margins"]["verdict"]), json.dumps(worst["design"]))
    print("failure", F_f, json.dumps(out["jam_failure_case"]["verdict"]), json.dumps(worst["failure"]))
    for k, v in rows_d.items():
        print("  D", k, {x: y for x, y in v.items() if x not in ("note", "model", "tag")})
    for k, v in rows_f.items():
        print("  F", k, {x: y for x, y in v.items() if x not in ("note", "model", "tag")})
    print("guide", gs["selection_check_v2p4"], "eyes", {k: (v.get("s0_jam"), v.get("bearing_pressure_jam_MPa"), v["selectable"]) for k, v in out["link_eyes"].items()})
    print(p, hashlib.sha256(p.read_bytes()).hexdigest()[:16])


if __name__ == "__main__":
    main()

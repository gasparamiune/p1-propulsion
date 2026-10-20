"""TC-02 plug glands S01 / S02 (2x AS568-226 FKM 90A).  Mechanical, 2026-10-20, v3 (v2 script kept as gland_fwd_v352_v2.py).
v3 (lead 09:47Z): (A2) the extrusion BASIS CHECK - from each document's own wording, whether the Apple axis, the FNST table and our
0.2772 are radial gap or diametral clearance, every comparison on one consistent basis, the chart's own pressure quantity (fluid
pressure) for the FA-1 event, the PTD5705 third-source search; (B) the back-up ring data, status per the basis check; (C) item C as
APPROVED for v3.5.2 rev 5 (callout as written, the fitting aid with the flush condition written against the bore, the assembly step as
written, the 15 deg x 3.5 lead-in adopted, why the holes cannot be moved).  v2 (kept): (A) FA1S against a second maker's chart (lead
08:40Z item 2), (B) the PTFE back-up ring option data, (C) the O-ring passage over the ten d5.5 J-FWD holes (lead 09:15Z item C).  The
v1 rows (gap budget, squeeze / stretch / fill, positions, thermal) are carried unchanged from gland_fwd_v352_v1.json (v1 script kept as
gland_fwd_v352_v1.py).  DATASHEET values as cited; every other number DERIVED.

v3 sources added (accessed 2026-10-20):
 [D1] (same document, read again for the wording) Freudenberg-NOK 'O-Ring Design Quick Reference' p. 6, table 'Maximum Recommended
      Extrusion Gap in Inches (mm)', columns 'Elastomer Hardness (durometer)', 90: .025 (.64) / .023 (.58) / .018 (.46) / .015 (.38) /
      .012 (.30) at 500 / 750 / 1000 / 1250 / 1500 psi; the gap is defined as 'Bore - Piston' (piston seals) / 'Bore - Rod' (rod
      seals); 'Unless the hardware can ensure the bore and the piston or rod remain concentric, we have to assume that all of the gap
      possible can shift to one side.'; scope 'static applications with pressures less than 1500 psi'; 'For pressures greater than
      1500 psi consult Freudenberg-NOK Sealing Technologies.'  URL https://fst.com/~/media/files/fst,-d-,com/markets/mobility/
      broschueren/fnst%20o-ring%20reference%20as568%20sizes.ashx (WebFetch).
 [D2] (same PDF, full text searched by gland/pdf_grep_p.py): axis 'Total Diametrical Clearance (in.)', pressure axis 'Fluid Pressure
      (psi)'; p. 2-3 text uses only 'diametrical clearance gap' / 'diametrical gap'; the 7 pages contain no 'radial', 'eccentric',
      'concentric', cycle count or test temperature for Illustration 5.2.  Re-read at the [D1] pressures and at 1343 psi by
      gland/apple_fig52_read_v2.py (same digitisation code as v1).
 [D9] Apple Rubber, Seal Design Guide 'Table A, O-Ring Gland Design' https://www.applerubber.com/src/pdf/table-a.pdf (WebFetch, text
      extraction jumbled): column headings 'Diametrical Clearance' and, separately, 'Eccentricity Max.'; NOTE 'Table A contains general
      sealing guidelines.'  Used only for its headings (Apple limits eccentricity separately from the clearance); no value is used.
 [D5] PTD5705-EN third-source search (lead 09:47Z): the readable text (WebFetch, 64,951 characters) ends part-way into p. 24
      (3.1.2 piston seal static); it holds no extrusion-gap chart or table (only the table 3.1 headings 'without anti-extrusion ring' /
      'one anti-extrusion ring'); Section 10.2 'Gap extrusion - the effects of pressurisation' is in the contents but its body is
      beyond the readable part; direct download refused by the proxy (403); the Parker ORD 5700 copy on test.parker.com did not fetch.
      -> no third source.
 [C1] interfaces/combustion.json: fa1_spectra_v2p4b period_domain_bar_abs T_le_0p1ms head|all 93.64 bar abs (P_eq(T) = p_amb + max k x,
      the maximum over T <= 0.1 ms, which bounds the head pressure peak itself, P_eq(T -> 0)); fa1_envelope_v2p4a head peak 83.0-88.0
      bar abs, above 45 bar <= 4.45 ms, above 67.5 bar <= 1.3 ms, above 90 bar 0 ms; fmea_input FA-1 'never above 90 bar'.  SIM on
      ASSUMED inputs (Combustion).
 [L194] CHANGELOG 194: "Mechanical's FA1S step case (DLF 2.0, about 151 bar abs)": a structural step-equivalent pressure.
 [L231] CHANGELOG 231: FA-1 is an abnormal state under 188 (9), 'a one-off abnormal event'; the J-FWD joint is inspected or its screws
      replaced after any FA-1-class over-pressure."""
_V2_DOC = """v2 sources (all accessed 2026-10-20; datasheet / handbook text quoted from the maker's document, never recalled):
 [D1] Freudenberg-NOK 'O-Ring Design Quick Reference' p. 6 (v1): 90 durometer gap 0.64 / 0.58 / 0.46 / 0.38 / 0.30 mm at
      500 / 750 / 1000 / 1250 / 1500 psi; above 1500 psi 'consult Freudenberg-NOK'; no temperature statement.
 [D2] Apple Rubber Products, Seal Design Guide, 'Critical Operating Environmental Factors', p. 3, Illustration 5.2 'Extrusion Limit'
      (Fluid Pressure (psi) vs Total Diametrical Clearance (in.), curves 70 / 80 / 90 Shore A); text: 'If the point representing the
      intersection of the lines of sealed pressure and diametrical clearance falls to the right of the material's hardness curve, either
      the material hardness must be increased, or back-up rings will be required.'  No basis (cycles, temperature) is printed.
      URL https://applerubber.s3.us-east-1.amazonaws.com/sdg/pdf/CriticalOperatingEnvironmentalFactors.pdf (7 pages).  Digitised from
      the PDF's vector paths by gland/apple_fig52_read.py (curve identity by the legend tints; the page's own two worked examples at
      1000 psi / 0.016 in reproduce: 70 A 0.0139-0.0147 in < 0.016 'to the right', 80 A 0.0215-0.0223 in > 0.016 'acceptable').
 [D3] Dichtomatik (Freudenberg FST), backup rings product page https://dichtomatik.fst.com/products/static-seals/backup-rings/ and
      solution sheet https://dichtomatik.fst.com/-/media/files/dichtomatik/solution-sheets/en/dichtomatik_backup-ring.pdf (read through
      WebFetch; direct download refused by the proxy): STR, white, PTFE, >= 51 Shore D, -200 to +260 C, <= 40 MPa; 'The maximum
      permissible operating pressure depends on clearance, design of the backup ring and operating conditions'; endless or 30 deg slotted.
 [D4] Greene Tweed, O-Ring & Back-Up Ring Catalog 20 (c) 2020, https://www.gtweed.com/wp-content/uploads/2020/06/o-ring-catalog-en-pb.pdf
      (WebFetch): AS5857 static gland, -2xx (0.139 in): gland width 0.185 / 0.250 / 0.320 in (+0.010 / -0.000) for 0 / 1 / 2 back-up
      rings, corner radii 0.010 / 0.025; 'Split BURs are required for use in closed gland configurations'; 'solid BURs are recommended
      for use in open gland configurations'; installation: 'a lead-in chamfer for all mating hardware is strongly recommended', 'The
      hardware should also be de-burred'; dash 226 maximum diametrical clearance read as 0.007 in (extraction ambiguous: TO-CONFIRM).
 [D5] Parker Hannifin (Praedifa), O-Ring Handbook PTD5705-EN, https://www.parker.com/content/dam/Parker-com/Literature/Praedifa/Catalogs/
      Catalog_O-Ring-Handbook_PTD5705-EN.pdf (WebFetch): 2.5.1 p. 17 'chamfers are necessary on all leading edges', 'All edges must be
      free from burrs and sharp edges bevelled', Fig. 2.24 15-20 deg, 'Dimension x should be greater than dimension y'; 2.5.2 p. 18
      'Traversing of cross drilled ports': 'An O-Ring can be sheared when a spool or rod moves in a bore broken by cross drilled ports.
      The deformed O-Ring returns to its original round cross-section as it enters the port and is sheared as it leaves the drilled
      area.  To avoid this, connection holes should be repositioned.'  Fig. 2.26 'If repositioning should not be possible, an internal
      chamfer is recommended.'  Fig. 2.27 'A balancing groove in the area of the bore is the best solution.'; 2.5.3 'Grease used to ease
      assembly must also be compatible.'; 2.5.5 rolling / spiral failure; 2.5.6 p. 18 'O-Rings should not be drawn over sharp edges.
      Threads, slits, bores, glands, splines, etc. must be removed or covered.  Fitting aids assist assembly and avoid sharp edges.';
      2.5.7 Fig. 2.31 'Fitting aid is supplemented by a sleeve to protect the seal from sharp edges.'; static groove table 3.1 p. 20,
      d2 3.53: b1 4.80-5.00 / b2 5.80-6.00 / b3 6.80-7.00 mm (0 / 1 / 2 back-up rings).  No cross-bore size limit and no chamfer
      dimension are given.
 [D6] Parker O-Ring eHandbook 'Installation Damage', https://parker.com/promotionsite/oring-ehandbook/us/en/ehome/Installation-Damage
      (WebFetch): 'Break all sharp edges on metal components.', 'Provide a 20 deg lead-in chamfer.', lubricant, 'O-ring twisted/pinched
      during installation' as a cause.  (The full ORD 5700 PDF could not be read: parker.com / arizona.edu downloads are refused by the
      proxy and the WebFetch copy truncates before Section III.)
 [D7] ERIKS, Technical Handbook O-rings, ch. 13 'O-ring Assembling Conditions' (o-ring.info PDF, WebFetch): 'Never force the O-ring
      over sharp threads, keyways, slots and other sharp edges.', 'Prevent the O-ring from being twisted.', lubricated parts; 15-20 deg.
 [D8] Apple Rubber, Seal Design Guide 'O-Ring Installation' (web page, WebFetch): lubricate with a compatible lubricant, 'make certain to
      remove any twists', 'Do not turn or twist pistons into cylinders as this may bunch or cut o-rings', stretch <= 100 % in
      installation; and Apple p. 3 (D2 PDF) CS reduction for stretch CS_R = CS - CS (1 - sqrt(100 / (100 + % stretch))).
 [L236] CHANGELOG 236 (lead): 'FA1S (js4, 151.04 bar abs, 45.6 C, SF 1.0 / 1.0)': the FA1S case temperature.
 [M1] engmat densities (project table): AL6061-T6 2700, PTFE 2200 kg/m3."""
import json, math, hashlib, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/04-fea/src")
import engmat

J = Path("/home/claude/work/mechanical/v352/jfwd")
G = Path("/home/claude/work/mechanical/v352/gland")
OUT = J / "gland_fwd_v352_v3.json"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
V1 = json.loads((J / "gland_fwd_v352_v1.json").read_text())
D2 = json.loads((G / "apple_fig52_read_v1.json").read_text())
D2b = json.loads((G / "apple_fig52_read_v2.json").read_text())       # v3: same digitisation, more pressures
CMB = json.loads(Path("/home/claude/work/shared-fallback/engine/interfaces/combustion.json").read_text())
IN2MM = 25.4
RHO_AL = engmat.MATERIALS["AL6061-T6"]["rho"]["v"] * 1e-6      # g/mm3
RHO_PTFE = engmat.MATERIALS["PTFE"]["rho"]["v"] * 1e-6

# ---------------- (A) FA1S extrusion against [D2]
fa = V1["extrusion"]["FA1S_151.04_bar_abs"]
gap = fa["gap_bore_minus_piston_mm"]["total"]
b90 = D2["bands"]["90 Shore A"]
r2176 = b90["readings"]["2176_psi"]
lim = sorted(r2176["log"]["clearance_mm"] + r2176["linear"]["clearance_mm"])
lim_lo, lim_hi = lim[0], lim[-1]
p_at_gap = sorted(b90["pressure_at_gap"]["0.2772_mm"]["psi_log"] + b90["pressure_at_gap"]["0.2772_mm"]["psi_linear"])
cmp_ = {}
for psi, d1 in ((1000, 0.46), (1500, 0.30)):
    rr = b90["readings"][f"{psi}_psi"]["log"]["clearance_mm"]
    cmp_[f"{psi}_psi"] = {"D1_FNST_90_mm": d1, "D2_Apple_90A_mm": rr, "ratio_D1_over_D2_lower": round(d1 / min(rr), 3)}
ratio = cmp_["1500_psi"]["ratio_D1_over_D2_lower"]
A = {"pressure_psi_gauge": fa["p_gauge_psi"], "case_temperature_C": 45.6, "case_temperature_source": "[L236] FA1S (js4) 151.04 bar abs, 45.6 C",
     "gap_diametral_mm": gap, "gap_parts_mm": fa["gap_bore_minus_piston_mm"],
     "allowable_D2_90A_mm": [lim_lo, lim_hi], "allowable_basis": "lower band edge of the 90 Shore A curve at 2176 psi (log / linear interpolation "
     "between the 2000 and 3000 psi labels; the chart's labels are equally spaced, not log-uniform)",
     "MS_D2": round(lim_lo / gap - 1.0, 3), "verdict_D2": "PASS" if gap <= lim_lo else "FAIL",
     "D2_pressure_at_the_gap_psi": [p_at_gap[0], p_at_gap[-1]],
     "maker_comparison_90": cmp_,
     "cross_check_DERIVED_information": {"method": "[D2] 2176-psi limit x the [D1]/[D2] ratio at 1500 psi (the last [D1] row): not a sourced limit",
                                         "limit_mm": round(lim_lo * ratio, 3), "MS": round(lim_lo * ratio / gap - 1.0, 3)},
     "MEOP_proof_D2_info": {"note": "[D1] governs MEOP / proof (v1: MS +2.17 / +1.28); [D2] 90 A is wider at those pressures"},
     "notes": ["[D2] prints no basis (cycles, temperature); FA1S is the FA-1 overpressure case at 45.6 C [L236], so the ring is near "
               "room temperature at that pressure (the ring reaches 163.0 / 155.8 C GVLO / GVHI only late in the burn at MEOP)",
               "the two makers differ: at 1500 psi [D1] 0.30 mm vs [D2] 0.627-0.647 mm (ratio 0.48)",
               "gap: drawing maximum rest 0.156 + pressure growth 0.121 (E at the land's burn-maximum temperature) + thermal 0 = 0.2772"]}

# ---------------- (A2) v3 basis check (lead 09:47Z)
PSI_PER_BAR = 14.5038
P_AMB = 1.01325
fa1_peq = CMB["fa1_spectra_v2p4b"]["v"]["period_domain_bar_abs"]["T_le_0p1ms"]
p_fl_abs = max(v["value"] for k, v in fa1_peq.items() if k.startswith("head"))          # 93.64 bar abs, head|all
p_fl_psi = (p_fl_abs - P_AMB) * PSI_PER_BAR
env = CMB["fa1_envelope_v2p4a"]["v"]["by_reading_entrance_tf1ms_OF4_12"]
D1_90 = {500: 0.64, 750: 0.58, 1000: 0.46, 1250: 0.38, 1500: 0.30}                      # [D1] mm as printed
def apple90(psi):
    r = D2b["bands"]["90 Shore A"]["readings"][f"{psi}_psi"]
    v = sorted(r["log"]["clearance_mm"] + r["linear"]["clearance_mm"])
    return v[0], v[-1]
assert abs(p_fl_psi - 1343.0) < 1.0, p_fl_psi                                             # the Apple v2 reading is at 1343 psi
rest, dp = fa["gap_bore_minus_piston_mm"]["drawing_max_rest"], fa["gap_bore_minus_piston_mm"]["plus_pressure"]
gap_one_side = {"FNST_rule_full_diametral_on_one_side": gap,
                "concentric_half": round(gap / 2.0, 4),
                "information_assembly_eccentric_then_clamped": round(rest + dp / 2.0, 4)}
recon = {}
for psi, d1 in D1_90.items():
    lo, hi = apple90(psi)
    recon[f"{psi}_psi"] = {"D1_mm": d1, "D2_total_mm": [lo, hi], "D1_over_D2_total": round(d1 / lo, 3), "D1_over_D2_half": round(d1 / (lo / 2.0), 3)}
def ms(lim, g):
    return round(lim / g - 1.0, 3)
rows = {}
for tag, psi in (("FA1S_step_equivalent_2176_psi", 2176), ("FA1_fluid_peak_bound_1343_psi", 1343)):
    lo, hi = apple90(psi)
    r = {"pressure_psi_gauge": round(fa["p_gauge_psi"] if psi == 2176 else p_fl_psi, 1),
         "diametral_basis": {"D2_Apple_total_mm": [lo, hi], "MS_D2": [ms(lo, gap), ms(hi, gap)]},
         "one_side_basis": {"D2_Apple_total_over_2_mm": [round(lo / 2, 4), round(hi / 2, 4)], "our_one_side_mm": gap,
                            "MS_D2": [ms(lo / 2, gap), ms(hi / 2, gap)]}}
    if psi <= 1500:
        nxt = min(p for p in D1_90 if p >= psi)
        prv = max(p for p in D1_90 if p <= psi)
        d1i = D1_90[prv] + (D1_90[nxt] - D1_90[prv]) * (psi - prv) / (nxt - prv) if nxt != prv else D1_90[nxt]
        r["D1_FNST"] = {"row_used": f"{nxt} psi (next tabulated pressure above, no interpolation)", "limit_mm": D1_90[nxt],
                        "MS": ms(D1_90[nxt], gap), "information_linear_interpolation_mm": round(d1i, 4), "MS_interp": ms(d1i, gap),
                        "basis": "[D1]'s own rule: the full bore - piston (0.2772) is the gap on one side; the same on both bases"}
    else:
        r["D1_FNST"] = {"limit_mm": None, "status": "outside [D1]'s scope (static, < 1500 psi; 'consult Freudenberg-NOK' above)"}
    rows[tag] = r
A2 = {
 "wording": {
  "D2_Apple_axis": "DIAMETRAL clearance: 'Total Diametrical Clearance (in.)'; text 'the extrusion limit of o-rings under pressure is "
                   "determined by the size of the diametrical clearance gap and the hardness of the o-ring material'.  Apple states no "
                   "eccentricity convention for the chart (no 'radial' / 'eccentric' / 'concentric' in the 7 pages); its Table A [D9] "
                   "limits 'Eccentricity Max.' in a separate column from 'Diametrical Clearance'.  Pressure axis: 'Fluid Pressure (psi)'.  "
                   "No cycle count, duration or temperature is printed.",
  "D1_FNST_table": "DIAMETRAL by definition ('Extrusion gap = Bore - Piston'), applied as the gap on ONE SIDE by its own rule: 'Unless "
                   "the hardware can ensure the bore and the piston or rod remain concentric, we have to assume that all of the gap "
                   "possible can shift to one side.'  The table ('Maximum Recommended Extrusion Gap', by pressure in psi) is therefore a "
                   "one-side gap limit entered with the whole diametral clearance.  Scope: static, < 1500 psi.",
  "ours_0.2772": "DIAMETRAL clearance: bore - piston under the FA1S step case = drawing maximum at rest 0.156 (57.25 H8 bore maximum "
                 "57.296 - 57.20 f7 plug minimum 57.140) + 2 x (case 0.0559 + plug 0.0047) radial = 0.1212.  The hardware does NOT ensure "
                 "concentricity: the plug is one 57.20 f7 diameter in the 57.25 H8 bore (the gland clearance IS the fit clearance), with "
                 "no separate centring feature; the ten radial screws clamp it where it was assembled.  So by [D1]'s rule the gap on one "
                 "side is the full 0.2772."},
 "one_side_gaps_mm": gap_one_side,
 "maker_reconciliation_90": {"rows": recon,
     "finding": "neither basis reconciles the two makers across [D1]'s range: [D1] / [D2] total runs 0.83 -> 0.48 and [D1] / ([D2] / 2) "
                "1.67 -> 0.96 from 500 to 1500 psi.  The halved Apple value meets [D1] only at 1500 psi; the difference is a maker "
                "difference in curve shape, not a units difference that halving removes."},
 "pressure_basis": {
     "chart_quantity": "both sources are entered with the FLUID pressure ([D2] axis 'Fluid Pressure (psi)'; [D1] rows by system pressure)",
     "FA1S": "151.04 bar abs is the structural step case (DLF 2.0) [L194]: it sizes the case response (the 0.1212 gap growth is kept from "
             "it, conservative) but it is not a fluid pressure",
     "FA1_fluid_bound_bar_abs": p_fl_abs,
     "FA1_fluid_bound_psi_gauge": round(p_fl_psi, 1),
     "FA1_fluid_source": "[C1] fa1_spectra_v2p4b T_le_0p1ms head|all (bounds the peak); envelope v2p4a head 83.0-88.0 bar abs",
     "FA1_time_at_pressure_ms": {"above_45_bar_max": max(e["above45_head_ms"] for e in env), "above_67p5_bar_max": max(e["above67p5_head_ms"] for e in env),
                                 "above_90_bar_max": max(e["above90_head_ms"] for e in env)},
     "MEOP_proof": "unchanged from v1 ([D1] MS +2.17 / +1.28 at 638 / 964 psi, full bore - piston)"},
 "comparisons": rows,
 "event_count": {"FA1S": "1 abnormal event per occurrence (FA-1, a one-off abnormal event under 188 (9) [L231]); a single head pulse, "
                         "above 45 bar <= 4.45 ms, above 67.5 bar <= 1.3 ms, never above 90 bar in the v2.4a envelope; occurrence "
                         "'unknown' (fmea_input)",
                 "chart_basis": "[D2] prints no cycle count, duration or temperature; [D1] none either: no credit is taken for the single "
                                "short event"},
 "PTD5705_third_source": "not available: the readable PDF has no extrusion-gap chart ([D5] v3 note)",
}
_fl = rows["FA1_fluid_peak_bound_1343_psi"]
_st = rows["FA1S_step_equivalent_2176_psi"]
A2["verdict"] = {
 "consistent_basis": "one side, by [D1]'s own rule (the full bore - piston on one side, no concentricity ensured), at the charts' own "
                     "pressure quantity (fluid pressure)",
 "gland1_FA1S_MS": _fl["D1_FNST"]["MS"],
 "governing": f"[D1] FNST 90 at its {_fl['D1_FNST']['row_used']}: {_fl['D1_FNST']['limit_mm']} mm vs 0.2772 -> MS {_fl['D1_FNST']['MS']:+.3f} PASS",
 "second_maker": f"[D2] Apple 90 A at 1343 psi: total {_fl['diametral_basis']['D2_Apple_total_mm']} mm -> MS {_fl['diametral_basis']['MS_D2'][0]:+.3f} "
                 f"(diametral as worded); halved {_fl['one_side_basis']['D2_Apple_total_over_2_mm']} -> MS {_fl['one_side_basis']['MS_D2'][0]:+.3f} "
                 "(one side): PASS on either reading",
 "FNST_scaled_minus_0.093": "DROPPED as a check (it extrapolated [D1] beyond its scope to 2176 psi, above every published fluid-pressure "
                            "bound at the head: FA-1 <= 93.64 bar abs [C1]); kept in this file as information",
 "if_2176_psi_is_held_as_fluid_pressure": f"[D2] halved {_st['one_side_basis']['D2_Apple_total_over_2_mm']} vs 0.2772 -> MS "
                                          f"{_st['one_side_basis']['MS_D2'][0]:+.3f} / {_st['one_side_basis']['MS_D2'][1]:+.3f} (FAILS at the lower "
                                          f"band edge); diametral as worded {_st['diametral_basis']['MS_D2'][0]:+.3f}; [D1] none -> the BUR comes back "
                                          "with the event count above (option data in B)",
 "for_the_lead": "the fluid-pressure entry for FA1S is a basis change for this gland check only; the lead rules",
 "proposed_rule": "after any FA-1-class event, replace S01 / S02 together with the J-FWD inspection / screw replacement of [L231]"}

# ---------------- (B) PTFE back-up ring option (information for the lead's ruling; no CAD change)
ZF, GW, LAND_W = 103.5134, 4.85, 3.0
HOLE_Z0, M5_Z0 = 127.5134 - 2.75, 127.5134 - 2.5
L_GLAND = (2.80, 2.86)
D_MEAN_BUR = (57.25 + 51.65) / 2.0
D_MEAN_GRV = (57.20 + 51.65) / 2.0
DEPTH_GRV = (57.20 - 51.65) / 2.0
opts = {}
for nm, w, w_src in (("none_current", 4.85, "CAD v3.5.2 4.85 +0.13 / 0 ([D5] b1 4.80-5.00; [D4] 0.185 +0.010 in = 4.70-4.95)"),
                     ("one_BUR_D5", 5.85, "[D5] static table 3.1 b2 5.80-6.00 mm (drawing 5.85 +0.13 / 0 keeps the v1 band inside it)"),
                     ("one_BUR_D4_AS5857", 6.35, "[D4] AS5857 0.250 +0.010 / -0.000 in = 6.35-6.60 mm")):
    g1 = (ZF + 3.0, ZF + 3.0 + w)
    g2 = (g1[1] + LAND_W, g1[1] + LAND_W + w)
    t_bur = w - GW
    m_bur = 2 * RHO_PTFE * math.pi * D_MEAN_BUR * L_GLAND[0] * t_bur
    m_grv = -2 * RHO_AL * math.pi * D_MEAN_GRV * DEPTH_GRV * (w - GW)
    opts[nm] = {"groove_width_mm": w, "source": w_src, "S01_z_mm": [round(g1[0], 3), round(g1[1], 3)], "S02_z_mm": [round(g2[0], 3), round(g2[1], 3)],
                "land_S01_S02_mm": LAND_W, "S02_fwd_wall_to_J-FWD_hole_edge_mm": round(HOLE_Z0 - g2[1], 3),
                "S02_fwd_wall_to_M5_major_mm": round(M5_Z0 - g2[1], 3),
                "BUR_axial_thickness_allowance_mm": round(t_bur, 2),
                "mass_delta_g": {"2_PTFE_BUR": round(m_bur, 2), "2_wider_TC-02_grooves": round(m_grv, 2), "net": round(m_bur + m_grv, 2)}}
B = {"status": "v3: NO BUR (lead 09:47Z) if the lead accepts the A2 fluid-pressure entry (gland-1 FA1S MS %+.3f, [D1] in scope); if "
               "2176 psi is held as the fluid pressure, the one-side [D2] check fails at the lower band edge (%+.3f) and this option "
               "data comes back with the A2 event count" % (_fl["D1_FNST"]["MS"], _st["one_side_basis"]["MS_D2"][0]),
     "status_v2": "INFORMATION for the lead's ruling: the rule's trigger (fail or not sourced) is not met by [D2]",
     "placement": "one ring per gland on the low-pressure side = the FORWARD side of S01 and of S02 (the chamber is aft of the injector face; "
                  "the annulus forward of S02 vents through the J-FWD holes)",
     "rating_D3": {"maker": "Dichtomatik (Freudenberg FST)", "type": "STR, PTFE, white, >= 51 Shore D", "T_C": [-200, 260], "p_max_MPa": 40,
                   "qualifier": "'The maximum permissible operating pressure depends on clearance, design of the backup ring and operating conditions'",
                   "vs_case": {"FA1S_MPa_gauge": round(fa["p_gauge_bar"] / 10.0, 2), "ring_T_max_C": max(V1["thermal_rev4"][g]["ring_T_max_C"] for g in V1["thermal_rev4"])}},
     "ring_type": "the TC-02 grooves are closed (one-piece plug): [D4] 'Split BURs are required for use in closed gland configurations' -> "
                  "[D3] STR GS (30 deg slotted); a solid PTFE ring cannot be stretched over the 57.20 plug into the 51.65 groove",
     "options": opts,
     "notes": ["the back-up ring also passes the ten J-FWD holes on assembly; a slotted ring's scarf ends must not catch a hole edge "
               "(covered holes, item C, address this too)",
               "mass from the gland section (radial 2.80 x the width allowance, mean diameter 54.45) at PTFE 2200 kg/m3, groove removal at "
               "6061 2700 kg/m3; the TC-02 plug length unchanged",
               "AS5857 dash-226 maximum diametral clearance read as 0.007 in (0.178 mm) [D4, TO-CONFIRM]: the 0.156 mm drawing maximum is "
               "inside it at rest; under FA1S the gap is 0.2772"]}

# ---------------- (C) O-ring passage over the J-FWD holes
CS, CS_TOL = 3.53, 0.10
GROOVE_R = (51.576 / 2.0, 51.650 / 2.0)
BORE_R = (57.250 / 2.0, 57.296 / 2.0)
stretch = [V1["gland"]["stretch_pct"][0], V1["gland"]["stretch_pct"][1]]
cs_red = lambda cs, st: cs * math.sqrt(100.0 / (100.0 + st))          # [D8]/[D2] p. 3 formula
y_max = GROOVE_R[1] + cs_red(CS + CS_TOL, stretch[0]) - BORE_R[0]    # ring protrusion beyond the bore before entry, worst stack
y_nom = 0.5 * (GROOVE_R[0] + GROOVE_R[1]) + cs_red(CS, 0.5 * sum(stretch)) - 0.5 * (BORE_R[0] + BORE_R[1])
x_leadin = 3.0 * math.tan(math.radians(15.0))
C = {"geometry": {"holes": "10x d5.5 radial through the TC-01 wall at z 127.513 (zf + 24.0), bore r 28.625-28.648, TC-02 inserted from the "
                           "forward end through the 15 deg x 3.0 mm lead-in (parts_engine.py); S01 / S02 travel past the hole row to zf + 3.0 / "
                           "zf + 10.85 (CAD v3.5.2)",
                  "ring_protrusion_y_mm": {"worst": round(y_max, 3), "nominal": round(y_nom, 3),
                                           "basis": "groove r + CS reduced for stretch ([D8] formula) - bore r; this is also the most the ring "
                                                    "section can spring into a hole (free CS minus the gland depth)"},
                  "leadin_height_x_mm": round(x_leadin, 3),
                  "leadin_check_D5_Fig2.24_x_gt_y": {"x_minus_y_worst_mm": round(x_leadin - y_max, 4), "x_minus_y_nominal_mm": round(x_leadin - y_nom, 3),
                                                     "verdict": ("MET at nominal; NOT MET at the worst stack by %.4f mm (x = y to within 0.001)" % (y_max - x_leadin))
                                                     if y_max > x_leadin else "MET at nominal and at the worst stack",
                                                     "proposal": "TC-01 lead-in 15 deg x 3.5 mm (x = %.3f, %.3f above the worst y); drawing dimension only, the "
                                                                 "lead rules before the CAD edit" % (3.5 * math.tan(math.radians(15.0)), 3.5 * math.tan(math.radians(15.0)) - y_max)}},
     "passage_check": {"guide": "[D5] 2.5.2 / 2.5.6 (+ [D6], [D7], [D8] general)", "hole_size_limit": "none given by any of the guides read",
                       "finding": "the guide requires more than an edge break: the cross bores must be repositioned, chamfered internally "
                                  "(Fig. 2.26) or relieved by a balancing groove (Fig. 2.27, 'best'), or, at assembly, 'removed or covered' "
                                  "(2.5.6).  Repositioning is not possible (the glands must lie between the chamber and the holes, and TC-02 "
                                  "enters from the forward end).  An internal chamfer that guides a ring springing up to y into the hole would, "
                                  "by the lead-in rule x > y at 15-20 deg, be about 0.8 mm deep and 2.2-3.0 mm wide around a 5.5 hole in a "
                                  "3.12 wall, inside the fit-contact annulus FEA3D found at the hole edge (r' 2.43-3.08): a structural change.  "
                                  "A balancing groove in the TC-01 bore at the screw plane would remove the fit contact there: also structural.",
                       "proposal": "keep the holes and the bore as drawn; COVER the ten holes during the TC-02 insertion with a fitting aid "
                                   "([D5] 2.5.6 / 2.5.7) and add the bore-side edge callout (1) and the assembly step (3); no CAD edit of the "
                                   "engine parts; the fitting aid is a tool drawing (TO-DRAW, Mechanical) if the lead agrees"},
     "callout_1": ("TC-01, 10x d5.5 J-FWD holes, BORE SIDE: break edge R0.2-R0.4 blended and polished (no chamfer, no step), free of burrs "
                   "and raised metal; deburr after match-drilling with TC-02 and after any rework, before anodise; 100 % inspection at 10x "
                   "before assembly (no burr, nick or raised metal at the hole edges or on the bore within 3 mm of a hole); the d10.5 "
                   "spot-face flat-to-OD edge break 0.1 max stays.  Sizing: R0.2 removes the drilling burr root; R0.4 keeps the edge "
                   "within 0.4 mm of the FE sharp corner, so the fit-contact annulus (r' 2.43-3.08) is not moved materially (FEA3D keeps "
                   "its sharp-corner model)."),
     "fitting_aid_2": ("10x hole plugs, PTFE or POM, d5.5 -0.02/-0.05 shank, inner end machined to the bore radius R28.6 and set flush "
                       "with the bore (+0 / -0.05) from the OD, retained by an OD band; fitted after deburr / inspection, before TC-02 "
                       "insertion; withdrawn only after both O-rings (and back-up rings, if adopted) are past the hole row (TC-02 seated on "
                       "its shoulder), then the screws are fitted.  An equivalent sleeve-type aid is acceptable."),
     "assembly_step_3": ["clean the bore, the lead-in and the plug; inspect the hole edges and the lead-in at 10x (callout 1)",
                         "fit the ten flush plugs (fitting aid 2)",
                         "lubricate the O-rings and the bore lightly with a lubricant compatible with FKM and with the oxidiser service: "
                         "TO-SELECT (datasheet before use; [D5] 2.5.3: 'Grease used to ease assembly must also be compatible.')",
                         "stretch each O-ring evenly into its groove (installed stretch 1.43-3.44 %, v1) with a cone or mandrel; no sharp "
                         "tools; remove any twist ([D8], [D7])",
                         "clock TC-02 to the TC-01 hole pattern BEFORE the rings enter the lead-in (match-drilled pair marks); push TC-02 "
                         "in axially without rotation ([D8]: 'Do not turn or twist pistons into cylinders'), steadily, to its shoulder",
                         "withdraw the plugs; look through each hole at the TC-02 OD for rubber debris (a cut ring leaves debris at the hole); "
                         "any debris: withdraw TC-02, replace both rings",
                         "fit and torque the J-FWD screws per J-F1; closure leak check at the existing proof / leak test (reject on any leak)"]}

# ---------------- (C2) v3: item C as APPROVED by the lead 09:47Z for v3.5.2 rev 5 (texts for the TC-01 drawing, the GSE line and the
# assembly procedure; the CAD edit is the 15 deg x 3.5 lead-in only)
x35 = 3.5 * math.tan(math.radians(15.0))
Z1_FWD = ZF + 36.0                              # TC-01 forward end (bolt_edge_chamber 12 mm from tube_fwd = zf + 36)
HOLE_FWD_EDGE = 127.5134 + 2.75
C2 = {"status": "APPROVED (lead 09:47Z), no structural change; into v3.5.2 rev 5 with the TC-01 drawing callouts, scheduled around T-F2",
      "callout_1_TC01_drawing": C["callout_1"],
      "leadin": {"adopted": "TC-01 forward bore lead-in 15 deg x 3.5 mm (rev 4: 3.0)", "x_mm": round(x35, 3),
                 "x_minus_y_worst_mm": round(x35 - y_max, 3),
                 "clear_of_hole_row_mm": round((Z1_FWD - 3.5) - HOLE_FWD_EDGE, 2),
                 "basis": "[D5] Fig. 2.24 'Dimension x should be greater than dimension y' at the worst stack (y %.3f)" % y_max},
      "fitting_aid_2_GSE": ("GSE line (tool, outside flight mass), TO-DRAW (Mechanical); TO-QUOTE, or made in-house from POM rod.  10x hole "
                            "plugs for the d5.5 J-FWD holes: shank d5.5 -0.02/-0.05; INNER END contoured to the bore radius R28.6 (axis "
                            "parallel to the TC-01 bore axis) and set 0 to 0.05 mm BELOW the bore surface, never proud - the flush "
                            "condition is written against the bore, not the OD; DEPTH SET POSITIVELY by a shoulder that seats on the d10.5 "
                            "spot face; KEYED (anti-rotation flat on the head engaging the OD band) so the contour stays aligned with the "
                            "bore axis; HELD BY THE BAND (the band bears on the plug heads) so a passing ring cannot push a plug outward; "
                            "fitted after the hole-edge inspection, removed only after both O-rings have passed the hole row (TC-02 on its "
                            "shoulder).  Acceptance before use: each plug end checked 0 to 0.05 below the bore with the plug seated and keyed."),
      "assembly_step_3": ["clean the bore, the lead-in and the plug; inspect the hole edges and the lead-in at 10x (callout 1)",
                          "fit the ten plugs of fitting aid 2, keyed and banded; check each end 0 to 0.05 below the bore, never proud",
                          "lubricate the O-rings and the bore lightly with a lubricant compatible with FKM and with N2O: TO-SELECT with a "
                          "datasheet (maker, part number, URL) before use ([D5] 2.5.3)",
                          "stretch each O-ring evenly into its groove (installed stretch 1.43-3.44 %, v1) with a cone or mandrel; no sharp "
                          "tools; remove any twist ([D8], [D7])",
                          "CLOCK TC-02 to the TC-01 hole pattern BEFORE the rings reach the lead-in (match-drilled pair marks); then PUSH "
                          "axially WITHOUT ROTATION ([D8]), steadily, to the shoulder",
                          "remove the plugs only now (both rings past the row); look through each hole at the TC-02 OD for rubber debris; "
                          "ANY debris: withdraw TC-02 and REPLACE BOTH rings, then repeat from the clean step",
                          "then the J-F1 torque, then the closure proof / leak test (reject on any leak)"],
      "why_the_holes_cannot_move": ("[D5] 2.5.2 asks first to reposition the cross bores.  Not possible here: the two rings must sit "
                                    "between the chamber and the holes so the holes and taps stay dry (forward of S02, vented), and "
                                    "TC-02 can only enter TC-01 from the forward end - so both rings necessarily travel past the hole "
                                    "row on insertion.  [D5] Fig. 2.26 / 2.27 (internal chamfer, balancing groove) would change the "
                                    "fit-contact annulus at the hole edge (structural); [D5] 2.5.6 'removed or covered' is met by "
                                    "fitting aid 2."),
      "rev5_items": ["TC-01 lead-in 3.0 -> 3.5 mm (parts_engine.py, the only geometry change)",
                     "TC-01 drawing: callout 1 at the 10x d5.5 holes (bore side) and a note referencing assembly step 3",
                     "BOM: GSE line 'J-FWD hole plugs (fitting aid 2), 10x, POM' outside the flight mass, TO-DRAW / TO-QUOTE",
                     "assembly procedure: step 3 as above"]}

out = {"id": "gland_fwd_v352", "version": "v3", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip() + "\n\n" + _V2_DOC.strip(),
       "inputs": {"gland_fwd_v352_v1.json": sha(J / "gland_fwd_v352_v1.json"), "gland_fwd_v352_v1.py": sha(J / "gland_fwd_v352_v1.py"),
                  "gland_fwd_v352_v2.py": sha(J / "gland_fwd_v352_v2.py"), "gland_fwd_v352_v2.json": sha(J / "gland_fwd_v352_v2.json"),
                  "apple_fig52_read_v1.json": sha(G / "apple_fig52_read_v1.json"), "apple_fig52_read.py": sha(G / "apple_fig52_read.py"),
                  "apple_fig52_read_v2.json": sha(G / "apple_fig52_read_v2.json"), "apple_fig52_read_v2.py": sha(G / "apple_fig52_read_v2.py"),
                  "pdf_grep_p.py": sha(G / "pdf_grep_p.py"), "pdf_text_p.py": sha(G / "pdf_text_p.py"),
                  "combustion.json": sha("/home/claude/work/shared-fallback/engine/interfaces/combustion.json"),
                  "D2_pdf_sha256_16": "6d89407fdfa50cba", "D2_digitise": {k: D2[k] for k in ("x_grid_lines_pt", "pt_per_0.008in", "x_origin_grid_pt", "legend_tints")}},
       "v1_rows_carried": {"extrusion": V1["extrusion"], "gland": V1["gland"], "positions": V1["positions"]},
       "A2_basis_check_v3": A2, "A_FA1S_extrusion_v2": A, "B_backup_ring_option": B, "C2_item_C_approved_v3": C2,
       "C_passage_over_JFWD_holes_v2": C}
s = json.dumps(out, indent=1, default=float)
OUT.write_text(s)
print(OUT.name, hashlib.sha256(s.encode()).hexdigest()[:16])
print(json.dumps({k: A2[k] for k in ("one_side_gaps_mm", "maker_reconciliation_90", "comparisons", "verdict")}, indent=1))
print(json.dumps(A2["pressure_basis"], indent=1))
print(json.dumps(C2["leadin"], indent=1))

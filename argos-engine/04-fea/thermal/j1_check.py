"""Nozzle joint J1 thermal check on the axisymmetric FE (04-fea/thermal, v1, 2026-10-13, Mechanical).

Lead 2026-10-13: "J1 is the baseline for your FE re-run ... Confirm that NZ-02 is carbon-phenolic."  Combustion nozzle_joint_v2p4
(b5f396c7155c06c4) requirements: hot layer T_service >= FE peak + 100 K (they wrote >= 1700 C from the mica-gasket FE peak 1595 C),
bearing 10.6 MPa at BN with strength >= 2x at temperature (structural FEA), k_through <= ~1 W/m/K "keeps the lip at or below the
present 250 C in-burn"; seal layer at the lip face: in-burn face temperature + 100 K <= class rating (lead rule).
Runs (run_thermal.py v1.2, hi flux bound, perfect contact = upper bound of conduction through the stack, TC-06 bore 49.9 mm, TC-03 IN718):
  J1:   DC-B1v3p99_tg711_hi_SS316L_L2.5_v12pre36IN_J1, DC-A1dispp99_tg711_hi_SS316L_L2.5_v12pre36IN_J1
  MICA: DC-B1v3p99_tg711_hi_SS316L_L2.5_v11pre36IN,    DC-A1dispp99_tg711_hi_SS316L_L2.5_v11pre36IN   (comparator, 1.0 mm mica gasket)
Material data: engmat v1.2 (carbon-phenolic k 0.9-2.5 W/m/K 20-2000 C LITERATURE-approx; flexible graphite through-thickness 5-4 W/m/K
LITERATURE-approx; mica 0.3-0.4 ASSUMED).  Output: thermal/j1_check_v1.json.  SIM (FE) on ASSUMED/LITERATURE-approx data; no test.
v1.1 (2026-10-13): J1b screen (lead: "carbon-phenolic hot layer + a mica/vermiculite insulating layer behind it ... + graphite seal, to bring
the lip toward <= 250 C and the seal below a 500 C class"): B1 p99 hi-bound runs with an NZ-05 mica layer of 0.5 mm (J1B05) and 1.0 mm
(J1B10) between the 2.0 mm carbon-phenolic hot layer and the 0.5 mm flexible-graphite lip seal (the stack grows by the mica thickness; the
insert sits that much further forward).  Criteria: NZ-04 in-burn + 100 K <= 500 C class (in-burn <= 400 C); lip bore edge in-burn <= 250 C
(Combustion goal); mica hot face <= 900 C (phlogopite class ASSUMED, supplier rating TO-QUOTE; with the lead +100 K rule the grade must be
rated >= peak + 100 K).  A1 was not re-run for J1b (B1 bounds the in-burn temperatures, as for J1).  Output: thermal/j1_check_v1p1.json.
"""
from __future__ import annotations
import json, hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = Path("/home/claude/work/mechanical/runs/thermal")
OUT = HERE / "j1_check_v1p1.json"
J1B = {"J1B05": ("DC-B1v3p99_tg711_hi_SS316L_L2.5_v13pre36IN_J1B05", 0.5), "J1B10": ("DC-B1v3p99_tg711_hi_SS316L_L2.5_v13pre36IN_J1B10", 1.0)}
MICA_CLASS_ASSUMED = 900.0     # C, phlogopite mica (ASSUMED class; supplier rating required)
PAIRS = {"B1": ("DC-B1v3p99_tg711_hi_SS316L_L2.5_v12pre36IN_J1", "DC-B1v3p99_tg711_hi_SS316L_L2.5_v11pre36IN"),
         "A1": ("DC-A1dispp99_tg711_hi_SS316L_L2.5_v12pre36IN_J1", "DC-A1dispp99_tg711_hi_SS316L_L2.5_v11pre36IN")}
MON = ["NZ03_hot_top_r16", "NZ04_seal_r16", "NZ04_seal_r20", "TC09_lip_top_bore_edge", "T1_TC09_lip_bore_well", "T1_TC09_lip_well",
       "TC09_step", "TC09_barrel", "NZ01_throat", "NZ01_OD", "NZ03_mica", "aft_land_oring", "case_aft_inner"]
PARTS = ["ENG-NZ-01", "ENG-NZ-02", "ENG-NZ-03", "ENG-NZ-04", "ENG-TC-09", "ENG-TC-03", "ENG-TC-01"]
SEAL_CLASS_ASSUMED = 500.0     # engmat FLEX-GRAPHITE-OI T_max ASSUMED (OI grades ~450-650 C as recalled); supplier rating required


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def load(lab):
    s = json.loads((RUNS / lab / "summary.json").read_text())
    return s


def main():
    out = {"id": "j1_check", "version": "v1.1", "date": "2026-10-13", "owner": "mechanical", "script": "04-fea/thermal/j1_check.py",
           "method": __doc__, "runs": {}, "compare": {}}
    for dc, (j1, mica) in PAIRS.items():
        a, b = load(j1), load(mica)
        out["runs"][dc] = {"J1": {"label": j1, "summary_sha16": sha16(RUNS / j1 / "summary.json")},
                           "MICA": {"label": mica, "summary_sha16": sha16(RUNS / mica / "summary.json")}}
        cm = {}
        for m in MON:
            ra, rb = a["monitors"].get(m), b["monitors"].get(m)
            cm[m] = {"J1_max_C": ra and ra["T_max_C"], "J1_flight_C": ra and ra["T_max_flight_C"],
                     "MICA_max_C": rb and rb["T_max_C"], "MICA_flight_C": rb and rb["T_max_flight_C"]}
        cp = {}
        for p in PARTS:
            ea, eb = a["envelope"].get(p), b["envelope"].get(p)
            cp[p] = {"J1": ea and {k: ea[k] for k in ("T_max_C", "t_max_s", "at_r_z_mm", "T_max_in_flight_C", "T_max_soak_C")},
                     "MICA": eb and {k: eb[k] for k in ("T_max_C", "T_max_in_flight_C", "T_max_soak_C")}}
        out["compare"][dc] = {"monitors": cm, "parts": cp}
    B = out["compare"]["B1"]["parts"]
    A = out["compare"]["A1"]["parts"]
    seal_ib = max(B["ENG-NZ-04"]["J1"]["T_max_in_flight_C"], A["ENG-NZ-04"]["J1"]["T_max_in_flight_C"])
    hot = max(B["ENG-NZ-03"]["J1"]["T_max_C"], A["ENG-NZ-03"]["J1"]["T_max_C"])
    nz02 = max(B["ENG-NZ-02"]["J1"]["T_max_C"], A["ENG-NZ-02"]["J1"]["T_max_C"])
    lip_ib = {dc: out["compare"][dc]["monitors"]["TC09_lip_top_bore_edge"]["J1_flight_C"] for dc in PAIRS}
    out["findings"] = {
        "hot_layer_NZ03_peak_C": hot, "hot_layer_T_service_required_C": round(hot + 100.0, 1),
        "hot_layer_note": "FE peak with J1 is below the 1595 C mica-joint value that set Combustion's >= 1700 C; requirement becomes >= FE + 100 K; "
                          "carbon-phenolic char capability at this temperature in O2-bearing exhaust TO-VERIFY",
        "seal_NZ04_inburn_max_C": seal_ib, "seal_NZ04_soak_max_C": max(B["ENG-NZ-04"]["J1"]["T_max_soak_C"], A["ENG-NZ-04"]["J1"]["T_max_soak_C"]),
        "seal_class_required_C (in-burn + 100 K)": round(seal_ib + 100.0, 1),
        "seal_vs_assumed_class": f"in-burn rule FAILS at the ASSUMED {SEAL_CLASS_ASSUMED:.0f} C class (needs >= {seal_ib + 100.0:.0f} C); "
                                 "an OI grade with a supplier rating >= that value is required (TO-QUOTE / TO-VERIFY)",
        "lip_inburn_bore_edge_C": lip_ib,
        "lip_vs_combustion_goal": "Combustion's k <= ~1 W/m/K goal 'keeps the lip <= 250 C in-burn' is NOT met by the modelled carbon-phenolic "
                                  "(k 0.9 -> 1.6 W/m/K at 20 -> 1000 C): lip bore edge in-burn rises vs the mica gasket (see compare)",
        "NZ02_peak_C": nz02,
        "NZ02_material": "CONFIRMED carbon-phenolic (CAD v3.4.1 baseline): peak below the 1551 C of the phenolic-sleeve run; glass-phenolic would "
                         "melt its glass and silica-phenolic is to be kept below ~1500 C against graphite (Combustion, as recalled)",
        "TC03_IN718_peak_C": max(B["ENG-TC-03"]["J1"]["T_max_C"], A["ENG-TC-03"]["J1"]["T_max_C"]),
        "contact_model": "perfect contact (conforming mesh): UPPER bound of conduction into the lip; a contact conductance would lower the lip "
                         "and raise the hot-layer face",
    }
    # ---------------- v1.1: J1b screen (B1)
    j1 = load(PAIRS["B1"][0])
    jb = {}
    for lab, (run, t_mica) in J1B.items():
        s_ = load(run)
        M, E = s_["monitors"], s_["envelope"]
        mica_peak = max(M["NZ05_mica_top_r16"]["T_max_C"], M["NZ05_mica_top_r20"]["T_max_C"], E["ENG-NZ-05"]["T_max_C"])
        seal_ib = E["ENG-NZ-04"]["T_max_in_flight_C"]
        lip_ib = M["TC09_lip_top_bore_edge"]["T_max_flight_C"]
        jb[lab] = {"run": run, "summary_sha16": sha16(RUNS / run / "summary.json"), "mica_t_mm": t_mica,
                   "extra_stack_length_mm": t_mica,
                   "monitors": {k: {"max_C": M[k]["T_max_C"], "flight_C": M[k]["T_max_flight_C"], "t_max_s": M[k]["t_max_s"]}
                                for k in ("NZ05_mica_top_r16", "NZ05_mica_top_r20", "NZ04_seal_r16", "NZ04_seal_r20", "TC09_lip_top_bore_edge",
                                          "T1_TC09_lip_bore_well", "T1_TC09_lip_well", "NZ03_hot_top_r16", "NZ01_OD", "TC09_step")},
                   "parts": {p: {k: E[p][k] for k in ("T_max_C", "t_max_s", "at_r_z_mm", "T_max_in_flight_C", "T_max_soak_C")}
                             for p in ("ENG-NZ-01", "ENG-NZ-02", "ENG-NZ-03", "ENG-NZ-04", "ENG-NZ-05", "ENG-TC-09")},
                   "criteria": {
                       "seal_NZ04_inburn_C": seal_ib, "seal_class_required_C": round(seal_ib + 100.0, 1),
                       "seal_vs_500C_class": "PASS" if seal_ib + 100.0 <= 500.0 else "FAIL",
                       "lip_bore_edge_inburn_C": lip_ib, "lip_vs_250C": "PASS" if lip_ib <= 250.0 else "FAIL",
                       "mica_hot_face_peak_C": mica_peak, "mica_vs_900C_class_ASSUMED": "PASS" if mica_peak <= MICA_CLASS_ASSUMED else
                       ("AT LIMIT (within 0.5 %)" if mica_peak <= 1.005 * MICA_CLASS_ASSUMED else "FAIL"),
                       "mica_grade_required_C (+100 K rule)": round(mica_peak + 100.0, 1),
                       "hot_layer_NZ03_peak_C": E["ENG-NZ-03"]["T_max_C"], "hot_layer_T_service_required_C": round(E["ENG-NZ-03"]["T_max_C"] + 100.0, 1),
                       "NZ04_soak_peak_C": E["ENG-NZ-04"]["T_max_soak_C"], "TC09_soak_peak_C": E["ENG-TC-09"]["T_max_soak_C"]}}
    out["j1b_screen"] = {
        "basis": "B1 p99 hi bound, perfect contact; J1 comparator " + PAIRS["B1"][0],
        "J1_reference": {"seal_NZ04_inburn_C": B["ENG-NZ-04"]["J1"]["T_max_in_flight_C"],
                         "lip_bore_edge_inburn_C": out["compare"]["B1"]["monitors"]["TC09_lip_top_bore_edge"]["J1_flight_C"],
                         "hot_layer_NZ03_peak_C": B["ENG-NZ-03"]["J1"]["T_max_C"]},
        "variants": jb,
        "verdict": ("J1b with 0.5 mm mica (J1B05) meets the seal rule (in-burn %.1f C -> class >= %.0f C) and the lip goal (%.1f C in burn); its mica hot "
                    "face peaks at %.1f C, at the ASSUMED 900 C phlogopite class (grade rated >= %.0f C needed with the +100 K rule, TO-QUOTE). "
                    "1.0 mm mica (J1B10) cools the seal/lip further but puts the mica at %.1f C (FAILS the 900 C class). The hot layer runs hotter "
                    "with mica behind it (NZ-03 %.1f / %.1f C vs J1 %.1f C)." % (
                        jb["J1B05"]["criteria"]["seal_NZ04_inburn_C"], jb["J1B05"]["criteria"]["seal_class_required_C"],
                        jb["J1B05"]["criteria"]["lip_bore_edge_inburn_C"], jb["J1B05"]["criteria"]["mica_hot_face_peak_C"],
                        jb["J1B05"]["criteria"]["mica_grade_required_C (+100 K rule)"], jb["J1B10"]["criteria"]["mica_hot_face_peak_C"],
                        jb["J1B05"]["criteria"]["hot_layer_NZ03_peak_C"], jb["J1B10"]["criteria"]["hot_layer_NZ03_peak_C"],
                        B["ENG-NZ-03"]["J1"]["T_max_C"])),
        "structural_baseline": "J1 stays the working baseline of the structural FEA (lead); its lip is hotter in burn (conservative for the lip "
                               "strength); a J1b adoption adds t_mica to the stack (CAD change: holder depth or exit plane).",
        "not_modelled": "contact conductances (perfect contact = upper bound of conduction through the stack), mica anisotropy, char shrinkage, "
                        "A1 duty cycle for J1b"}
    out["tag"] = "SIM (2-D FE, hi bound, perfect contact); material data ASSUMED / LITERATURE-approx; no test"
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out["findings"], indent=1))


if __name__ == "__main__":
    main()

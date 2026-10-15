"""Lead CHANGELOG 206 (7): classification of the v3.5.1 S-AX negatives TC-02 (TB70 ult -0.15, LC2 ult -0.02) and NZ-03 (TB70 -0.16)
under the line-183 (1) criterion and RM1-03, with a fix proposal.  Mechanical, 2026-10-13, v1.  Inputs: the valid v3.5.1 S-AX L1 run
(results/sax_results_L1_thv351_TB1GC_cad351_v1.json, mesh b780ed547ad8f3ba, CAD v3.5.1, thermal v351_TB1GC) and its SCL table.
183 (1) criterion as applied here: (a) primary (load-controlled) MS >= 0 at the case SF (yield 1.5 / ultimate 2.0 for the nominal states incl.
TB70 per lead 188 (9)); (b) P+Q <= 2 Fty(T) (shakedown); (c) LCF >= 50 cycles with a factor 2 on strain or 20 on cycles; (d) temperature:
usable-temperature condition, to be replaced by the RM1-06 sourced time-at-temperature allowables.  Negative values stay SHOWN AS FOUND."""
import json, math, hashlib
from pathlib import Path
R = Path("/home/claude/work/mechanical/v351/engine/04-fea/structural/results")
FR = R / "sax_results_L1_thv351_TB1GC_cad351_v1.json"
FS = R / "sax_scl_table_L1_thv351_TB1GC_cad351_v1.csv"
OUT = Path("/home/claude/work/mechanical/v351/class/tc02_nz03_classification_v1.json")
sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()[:16]
d = json.loads(FR.read_text())
import csv
scl = [r for r in csv.DictReader(FS.open()) if r["part"] == "ENG-TC-02" and r["case"] in ("LC2", "TB70")]
def row(case, part, st=None, s="regular"):
    rr = [r for r in d["rows"] if r["case"] == case and r["part"] == part and r.get("set") == s and (st is None or r["state"] == st)]
    return min(rr, key=lambda r: r["MS_ult"] if isinstance(r.get("MS_ult"), (int, float)) else r["MS"])
iface = [x for x in d["interfaces_governing"] if x["pair"] == ["ENG-TC-02", "ENG-TC-03"]]
# ---------------- LCF, Manson universal slopes (Manson 1965): de = 3.5 Su/E N^-0.12 + D^0.6 N^-0.6, D = ln(1/(1-RA)); RA 0.30 ASSUMED (6061-T6 lower bound)
def n_cycles(de, Su, E, RA=0.30):
    D = math.log(1.0 / (1.0 - RA))
    lo, hi = 1.0, 1e12
    f = lambda N: 3.5 * Su / E * N ** -0.12 + D ** 0.6 * N ** -0.6 - de
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        if f(mid) > 0: lo = mid
        else: hi = mid
    return mid
E_T = {149.2: 64.6e3, 181.2: 62.1e3}     # MPa, engmat AL6061-T6 E table interpolated (100 C 66.2, 150 C 63.4, 200 C 60.0 GPa)
out = {"id": "tc02_nz03_classification", "version": "v1", "date": "2026-10-13", "owner": "mechanical", "request": "lead CHANGELOG 206 (7)",
       "inputs": {"sax_results": {"file": "04-fea/structural/results/sax_results_L1_thv351_TB1GC_cad351_v1.json", "sha256_16": sha(FR)},
                  "scl_table": {"file": "04-fea/structural/results/sax_scl_table_L1_thv351_TB1GC_cad351_v1.csv", "sha256_16": sha(FS)},
                  "mesh_sha256_16": "b780ed547ad8f3ba", "cad": "v3.5.1 config.V351_ON (geom_v351)", "thermal": "v351_TB1GC (B1 / A1 full runs)"},
       "criterion_183_1": __doc__.split("183 (1) criterion as applied here: ")[1].split("Negative")[0].strip(), "items": {}}
for case in ("LC2", "TB70"):
    r = row(case, "ENG-TC-02")
    T = round(r["T_C"], 1)
    E = E_T[149.2] if case == "LC2" else E_T[181.2]
    Fty = r["allowable_MPa"]
    Ftu = (r["MS_ult"] + 1.0) * 2.0 * r["vm_MPa"]             # back-computed Ftu(T) used by S-AX (ASM 10 000 h ratio x ASTM minimum)
    de = r["vm_MPa"] / E                                      # elastic equivalent strain range RT-unloaded -> state (no yield: vm < Fty)
    N2 = n_cycles(2.0 * de, Ftu, E)
    N1 = n_cycles(de, Ftu, E)
    s = [x for x in scl if x["case"] == case]
    out["items"][f"TC-02 {case}"] = {
        "as_found": {"MS_yield_combined": round(r["MS"], 4), "MS_ult_combined": round(r["MS_ult"], 4), "state": r["state"], "at_r_z_mm": r["at_r_z_mm"],
                     "vm_MPa": round(r["vm_MPa"], 1), "vm_mech_MPa": round(r["vm_mech_MPa"], 2), "vm_thermal_MPa": round(r["vm_thermal_MPa"], 1),
                     "s1_MPa": round(r["s1_MPa"], 1), "s3_MPa": round(r["s3_MPa"], 1), "T_C": T, "T_part_max_C": round(r["T_part_max_C"], 1),
                     "Fty_T_MPa": round(Fty, 1), "Ftu_T_MPa": round(Ftu, 1), "SF": [r["SF_y"], r["SF_u"]],
                     "allowable_basis": "ASTM B221 minimum x ASM typical ratio after 10 000 h at temperature (engmat AL6061-T6)"},
        "location": "TC-02 seat bore r 7.0 at the seat plane (z_seat 108.513): 1.09 mm above the end of the TC-02/TC-03 axial tie "
                    "(interface r 7.0, z 107.5-117.5, tied in z, free in r); S-AX singular-point exclusion radius 1.0 mm",
        "class": "SECONDARY (thermal, self-limiting): mechanical part " + f"{r['vm_mech_MPa']:.1f} of {r['vm_MPa']:.1f} MPa; compressive (s3 {r['s3_MPa']:.1f}, s1 {r['s1_MPa']:.1f} MPa)",
        "183_1": {"a_primary": {"MS_primary_only_node": round(r["MS_primary_only"], 3),
                                "SCL": [{"scl": x["scl"], "Pm_vm": float(x["P_Pm_vm"]), "PmPb_vm": float(x["P_PmPb_vm"]), "MS_Pm_y": float(x["MS_Pm_y"]),
                                         "MS_PmPb_u": float(x["MS_PmPb_u"])} for x in s], "verdict": "PASS"},
                  "b_shakedown": {"MS_PQ_nodal": round(r["MS_PQ_nodal_shakedown"], 3), "SCL_MS_PQ_min": round(min(float(x["MS_PQ_shakedown"]) for x in s), 2), "verdict": "PASS"},
                  "c_LCF": {"method": "Manson universal slopes, Su = Ftu(T) as used by S-AX, E(T) engmat, RA 0.30 ASSUMED (6061-T6 lower bound); "
                                      "strain range = elastic vm / E (RT unloaded -> state; elastic since vm < Fty)",
                            "strain_range": round(de, 6), "N_at_2x_strain": float(f"{N2:.3g}"), "N_over_20": float(f"{N1 / 20:.3g}"), "required": 50,
                            "verdict": "PASS", "evidence": "CALC (universal-slopes LITERATURE method; material constants ASSUMED/engmat)"},
                  "d_temperature": {"T_node_C": T, "T_part_max_C": round(r["T_part_max_C"], 1), "usable_C": 150.0,
                                    "exposure": "B1: part max 160.3 C at 21.5 s (end of burn), soak max 141.2 C (v351_TB1GC log); TB (stand abort) 189.7 C",
                                    "verdict": "OPEN (RM1-06): allowables are 10 000 h values; sourced short-time data needed"}},
        "RM1_03": "OPEN: the peak sits 1.09 mm from the end of an axial tie between dissimilar materials at different temperatures (Al 6061 head, "
                  "GlidCop insert); a frictional contact model (axial slip, radial contact) can lower or raise it. The SCLs through the head "
                  "(head_bore_wall, head_r15, head_r26_gland_land) carry P+Q <= 17.3 MPa (MS_PQ >= 22.6).",
        "required_for_combined_positive": {"Ftu_T_MPa": round(2.0 * r["vm_MPa"], 1), "fraction_of_Ftu_RT_min_260": round(2.0 * r["vm_MPa"] / 260.0, 3),
                                            "current_fraction": round(Ftu / 260.0, 3)},
        "verdict": f"Not a 183 (1) failure on (a)-(c); (d) and RM1-03 OPEN; MS_ult {r['MS_ult']:.3f} SHOWN AS FOUND"}
# ---------------- NZ-03
r = row("TB70", "ENG-NZ-03")
F = 5.81 * math.pi * 25.0 ** 2               # N, TB70 'BL' 5.81 MPa on the 50.0 insert bore (S-AX combo: P pi r_bore^2 on the lip)
A = math.pi * (24.9 ** 2 - 15.3 ** 2)         # mm2, NZ-03 annulus r 15.3-24.9 (geom_v351 section)
sm = F / A
Sc = 20.0
out["items"]["NZ-03 TB70"] = {
    "as_found": {"MS": round(r["MS"], 4), "state": r["state"], "at_r_z_mm": r["at_r_z_mm"], "s3_mech_MPa": round(r["s3_mech_MPa"], 3),
                 "s3_total_MPa": round(r["s3_MPa"], 1), "T_C": round(r["T_C"], 1), "zone": r["zone"], "char_fraction": r["char_nodes_fraction"],
                 "allowable_MPa": r["allowable_MPa"], "allowable_basis": "ASSUMED char compressive strength 20 MPa (no data)", "SF": [r["SF_y"], r["SF_u"]],
                 "SF_basis": "TB70 at 1.5 / 2.0 per lead 188 (9) (SF_RULE_188); TBS (63.1 bar static) at 1.0 / 1.5: MS +0.034"},
    "location": "NZ-03 top face (insert shoulder plane z -229.605) at r 20.98: 1.02 mm inside the NZ-01 shoulder outer edge (r 22.0, graphite / "
                "carbon-phenolic NZ-02 step) - next to the 1.0 mm singular-point exclusion radius",
    "class": "PRIMARY (load-controlled bearing of the nozzle stack on the TC-09 lip through the J1 layer), in the CHAR zone (T 1312 C, char fraction 0.79)",
    "hand_check": {"F_N": round(F, 0), "A_annulus_mm2": round(A, 1), "mean_bearing_MPa": round(sm, 2),
                   "MS_mean_SF2_Sc20": round(Sc / 2.0 / sm - 1.0, 3), "MS_node_SF2_Sc20": round(Sc / 2.0 / abs(r["s3_mech_MPa"]) - 1.0, 3),
                   "peak_over_mean": round(abs(r["s3_mech_MPa"]) / sm, 3), "evidence": "DERIVED (F = BL x pi 25^2; annulus from the section)"},
    "183_1": {"a_primary": {"MS": round(r["MS"], 4), "verdict": "NEGATIVE vs an ASSUMED allowable (SHOWN AS FOUND)"},
              "b_c": "not applicable as a relief: the stress is primary (bearing); shakedown/LCF cannot clear it",
              "d_temperature": "char zone: strength at temperature is the open datum (no test)"},
    "RM1_03": "OPEN: the node value (11.9 MPa) is 1.26 x the mean bearing (9.4 MPa) because of the shoulder-edge stiffness step; contact FE "
              "(graphite shoulder on a compliant char layer) sets the real distribution between the mean and the node value",
    "required_char_strength_MPa": {"node_SF2": round(2.0 * abs(r["s3_mech_MPa"]), 1), "mean_SF2": round(2.0 * sm, 1), "node_SF1p5": round(1.5 * abs(r["s3_mech_MPa"]), 1)},
    "verdict": "183 (1) (a) NEGATIVE at the node against an ASSUMED allowable; positive on the mean bearing (+0.063); SHOWN AS FOUND"}
out["fix_proposal"] = {
    "TC-02": [{"id": "T-F1 (data, no hardware)", "action": "RM1-06: sourced short-time elevated-temperature allowables for 6061-T6 (exposure seconds-minutes); "
               f"clears the combined ultimate if Ftu(149 C) >= {2.0*row('LC2','ENG-TC-02')['vm_MPa']:.1f} MPa (0.765 Ftu,RT,min) and Ftu(181 C) >= "
               f"{2.0*row('TB70','ENG-TC-02')['vm_MPa']:.1f} MPa (0.661); today 10 000 h values 0.755 / 0.561", "mass": "0"},
              {"id": "T-F2 (model)", "action": "RM1-03 contact FE of TC-02/TC-03 (axial friction mu 0.2-0.6 bound, radial contact) to remove or confirm the tie-end peak", "mass": "0"},
              {"id": "T-F3 (design fallback)", "action": "0.5 mm x 45 deg relief at the TC-02 seat-bore entry (moves the tie end off the hot corner) and/or "
               "TC-02 in 2219-T87 (LOX-tank heritage alloy, better elevated-temperature strength; density 2.84 vs 2.70: about +5 % of the head mass; "
               "allowables to be sourced before adoption, research proposal)", "mass": "+5 % TC-02 if 2219"}],
    "NZ-03": [{"id": "N-F1 (data)", "action": "char compressive-strength test at >= 1300 C on the NZ-03 carbon-phenolic: >= 23.8 MPa clears the node at SF 2.0, "
               ">= 18.8 MPa the mean bearing", "mass": "0"},
              {"id": "N-F2 (design, load spreader)", "action": "R 1.0 on the NZ-01 shoulder outer edge + a 0.25 mm flexible-graphite foil between the "
               "insert shoulder and NZ-03 so the bearing approaches the 9.4 MPa mean (MS +0.06 at 20 MPa / SF 2.0); re-run thermal (foil k) and S-AX", "mass": "< 1 g"},
              {"id": "N-F3 (with M2c)", "action": "J1 stack redesign together with the NZ-04 733 C finding: a thicker hot layer keeps a virgin (stronger) "
               "zone under the char and lowers NZ-04; needs its own thermal + S-AX run", "mass": "TBD"}],
    "recommendation": "T-F1 + T-F2 and N-F1 + N-F2 first (no hardware change or < 1 g); keep both negatives SHOWN AS FOUND until cleared"}
s = json.dumps(out, indent=1)
OUT.write_text(s)
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16])
for k, v in out["items"].items():
    print(k, "|", v["class"][:90], "|", v["verdict"])
    if "183_1" in v and "c_LCF" in v["183_1"]:
        print("   LCF", v["183_1"]["c_LCF"]["strain_range"], v["183_1"]["c_LCF"]["N_at_2x_strain"], v["183_1"]["c_LCF"]["N_over_20"], "req", v["required_for_combined_positive"])
print(out["items"]["NZ-03 TB70"]["hand_check"], out["items"]["NZ-03 TB70"]["required_char_strength_MPa"])

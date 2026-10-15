"""Nozzle joint J1 vs J2 on the Combustion v2.4 loads (coordinator C item 3; Combustion REPORT §6.5, combustion.json key nozzle_joint).
Mechanical, v1, 2026-10-13.  Inputs: the A1 design thermal runs (2-D axisymmetric FE, run_thermal v1.3, 'hi' bound) for J1 (rev B), J2
(zirconia washer NZ-03, same stack geometry) and J1 with the v3.5 IN718 TC-09, plus the S-AX level-1 results on those thermal states.
Limits marked AS RECALLED are not sourced here (TO-VERIFY).  Perfect contact is assumed at every interface in the thermal model (no
contact resistance): the hot-layer peak is bounded by the NZ-01 shoulder temperature, which the table also lists.
Usage: python nozzle_joint_fe.py -> nozzle_joint_fe_v1.json (this folder)."""
import glob, hashlib, json, os
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = Path("/home/claude/work/mechanical/runs/thermal")
RES = HERE.parent / "structural" / "results"
RUN = {"J1": "DC-A1dispp99_tg711_hi_SS316L_L2.5_v13pre36IN_J1revB", "J2": "DC-A1dispp99_tg711_hi_SS316L_L2.5_v13pre36IN_J2revB",
       "J1_TC09IN718": "DC-A1dispp99_tg711_hi_SS316L_L2.5_v13pre36IN_J1revB_TC09IN"}
SAX = {"J1": RES / "sax_results_L1_v1.json", "J1_TC09IN718": RES / "sax_results_L1_TC09IN718_thJ1revB_TC09IN_v1.json"}
LIMITS = {"lip_in_burn_C": (250.0, "Combustion REPORT §6.5 screening criterion for the 316L lip"),
          "ZIRCONIA-FS_service_C": (2000.0, "AS RECALLED fully stabilised zirconia, TO-VERIFY (thermal shock governs, not temperature)"),
          "FLEX-GRAPHITE-OI_oxidising_C": (450.0, "AS RECALLED flexible graphite in an oxidising gas, TO-VERIFY maker"),
          "bearing_nominal_MPa": (10.6, "Combustion v2.4 nominal joint bearing; criterion allowable >= 2x")}
PARTS = ("ENG-NZ-01", "ENG-NZ-02", "ENG-NZ-03", "ENG-NZ-04", "ENG-TC-09")
CASES = ("OP", "BL", "FA1Q", "FA1QB", "FA1U", "FA1UB", "TB70")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def sax_min(path):
    d = json.loads(Path(path).read_text())
    out = {}
    for g in d["governing"]:
        if g["part"] in PARTS and g.get("set") == "regular" and any(g["case"].startswith(c) for c in CASES):
            k = g["part"]
            if k not in out or g["MS"] < out[k]["MS"]:
                out[k] = {"MS": round(g["MS"], 3), "MS_ult": None if g.get("MS_ult") is None else round(g["MS_ult"], 3), "case": g["case"],
                          "state": g["state"], "material": g.get("material"), "T_C": round(g.get("T_C", 0.0), 1), "role": g.get("role")}
    return out, sha(path)


def main():
    j2 = sorted(glob.glob(str(RES / "sax_results_L1*J2*_v1.json")), key=os.path.getmtime)
    if j2:
        SAX["J2"] = Path(j2[-1])
    res = {"id": "nozzle_joint_fe", "version": "v1", "date": "2026-10-13", "owner": "mechanical", "script": "04-fea/thermal/nozzle_joint_fe.py",
           "status": "SIM (2-D thermal FE upper-bound heat transfer + axisymmetric linear FE); perfect contact; physical validation pending",
           "limits": {k: {"v": v[0], "tag": v[1]} for k, v in LIMITS.items()}, "variants": {}}
    for v, lab in RUN.items():
        env = json.loads((RUNS / lab / "envelope.json").read_text())["parts"]
        row = {"thermal_run": lab, "envelope_sha256_16": sha(RUNS / lab / "envelope.json"),
               "T_C": {p: {k: env[p][k] for k in ("T_max_in_flight_C", "T_max_soak_C", "at_r_z_mm")} for p in PARTS if p in env}}
        lip = env["ENG-TC-09"]["T_max_in_flight_C"]
        row["lip_in_burn_check"] = {"T_C": lip, "limit_C": 250.0, "pass": lip <= 250.0,
                                    "note": "TC-09 max in flight (A1 incl. relight); the 250 C screen applies to 316L; for IN718 the S-AX margin at "
                                            "temperature is the criterion"}
        row["hot_layer_bound_by_NZ01_shoulder"] = env["ENG-NZ-01"]["T_max_soak_C"]
        if v in SAX and SAX[v].exists():
            row["sax_min"], row["sax_sha256_16"] = sax_min(SAX[v])
        else:
            row["sax_min"] = "PENDING"
        res["variants"][v] = row
    t1, t2 = res["variants"]["J1"]["T_C"], res["variants"]["J2"]["T_C"]
    res["summary"] = {
        "J2_vs_J1": f"J2 (zirconia washer) lowers NZ-03 peak {t1['ENG-NZ-03']['T_max_soak_C']:.0f} -> {t2['ENG-NZ-03']['T_max_soak_C']:.0f} C but RAISES "
                    f"the TC-09 lip in flight {t1['ENG-TC-09']['T_max_in_flight_C']:.0f} -> {t2['ENG-TC-09']['T_max_in_flight_C']:.0f} C and NZ-04 "
                    f"{t1['ENG-NZ-04']['T_max_in_flight_C']:.0f} -> {t2['ENG-NZ-04']['T_max_in_flight_C']:.0f} C (in flight)",
        "lip_250C_screen": {v: r["lip_in_burn_check"]["pass"] for v, r in res["variants"].items()},
        "recommendation": "keep J1 with the v3.5 IN718 TC-09; J2 does not improve the lip; NZ-03 service temperature and NZ-04 seal class "
                          "against the soak peaks are OPEN (material data TO-VERIFY)"}
    (HERE / "nozzle_joint_fe_v1.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res["summary"], indent=1))
    for v, r in res["variants"].items():
        print(v, r["lip_in_burn_check"], json.dumps(r["sax_min"])[:600])


if __name__ == "__main__":
    main()

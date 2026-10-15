#!/usr/bin/env python3
"""REV-MECH-1, 2026-10-13 - CAD v3.5 integrity spot checks (own code; no author module imported).

1. STEP spot checks (selected PNs): sha256/16 of the file vs roundtrip_parts_v3.5.json, length unit declared in the STEP header,
   independent re-import (cadquery/OCP), solid count, BRepCheck validity, volume and bbox vs the author's round-trip record,
   STL watertightness and STL/STEP volume ratio, BOM unit mass vs volume x density (density from materials_v1p4.json).
2. BOM arithmetic: sum(qty x unit mass) of the flight lines, GSE lines, null-mass lines; vs massprops_v3.5 'all' (wet).
3. Coverage: every BOM PN has a STEP and an STL; every STEP in parts/ is a BOM PN or a declared sub-solid; GSE PN absent from the
   assembly manifest.
Usage: python -I rm1_cad_spotcheck.py <03-cad dir> <materials_json> <out_json>
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import cadquery as cq
import trimesh
from OCP.BRepCheck import BRepCheck_Analyzer

PNS = ["ENG-TC-01", "ENG-TC-02", "ENG-TC-09", "ENG-NZ-01", "ENG-GM-01", "ENG-GM-03", "ENG-GM-09", "ENG-BL-02", "ENG-FD-01",
       "ENG-GM-16"]


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def main():
    cad, mats, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    rt = {r["pn"]: r for r in json.loads((cad / "checks/roundtrip_parts_v3.5.json").read_text())["rows"]}
    bom = json.loads((cad / "BOM_v3.5.json").read_text())
    lines = {l["pn"]: l for l in bom["lines"]}
    M = json.loads(mats.read_text())["materials"]
    res = {"who": "REV-MECH-1", "date": "2026-10-13", "step_spot_checks": [], "bom": {}, "coverage": {}}
    for pn in PNS:
        f = cad / "parts" / f"{pn}.step"
        hdr = f.read_text(errors="ignore")[:20000]
        unit = re.findall(r"SI_UNIT\(\s*\.(\w+)\.\s*,\s*\.METRE\.\)", hdr)
        shp = cq.importers.importStep(str(f))
        sol = shp.solids().vals()
        valid = all(BRepCheck_Analyzer(s.wrapped).IsValid() for s in sol)
        vol = sum(s.Volume() for s in sol)
        bb = shp.val().BoundingBox() if len(sol) == 1 else cq.Compound.makeCompound(sol).BoundingBox()
        st = trimesh.load(str(cad / "parts" / f"{pn}.stl"), force="mesh")
        l = lines.get(pn, {})
        rho = None
        mat = l.get("material")
        if mat in M and M[mat].get("rho"):
            r_ = M[mat]["rho"]
            rho = r_["v"][0] if isinstance(r_, dict) and isinstance(r_.get("v"), list) else (r_["v"] if isinstance(r_, dict) else r_)
        row = {"pn": pn, "sha256_16": sha16(f), "sha_matches_record": sha16(f) == rt[pn]["sha256_16"],
               "step_length_unit": unit[:2], "solids": len(sol), "valid": valid, "volume_mm3": vol,
               "record_volume_mm3": rt[pn]["volume_mm3"], "volume_rel_diff": abs(vol - rt[pn]["volume_mm3"]) / rt[pn]["volume_mm3"],
               "bbox_mm": [bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax],
               "stl_watertight": bool(st.is_watertight), "stl_volume_ratio": float(st.volume / vol) if st.is_watertight else None,
               "bom_material": mat, "bom_unit_mass_kg": l.get("unit_mass_kg"), "bom_mass_source": l.get("mass_source"),
               "rho_kg_m3_materials": rho,
               "mass_from_volume_kg": None if rho is None else vol * 1e-9 * rho}
        if row["mass_from_volume_kg"] and l.get("unit_mass_kg"):
            row["bom_vs_volume_rel_diff"] = abs(l["unit_mass_kg"] - row["mass_from_volume_kg"]) / l["unit_mass_kg"]
        res["step_spot_checks"].append(row)
        print(json.dumps(row))
    # BOM arithmetic
    tot_all, tot_flight, nulls = 0.0, 0.0, []
    gse = {g["pn"] for g in bom.get("gse_lines_excluded_from_flight_mass", [])}
    for l in bom["lines"]:
        m = l.get("unit_mass_kg")
        if m is None:
            nulls.append(l["pn"])
            continue
        tot_all += m * l["qty"]
        if l["pn"] not in gse:
            tot_flight += m * l["qty"]
    mp = json.loads((cad / "massprops_v3.5.json").read_text())
    res["bom"] = {"n_lines": len(bom["lines"]), "sum_all_lines_kg": tot_all, "sum_flight_kg": tot_flight,
                  "recorded_mass_sum_kg": bom["mass_sum_kg"], "recorded_flight_kg": bom["mass_sum_flight_kg"], "gse": sorted(gse),
                  "null_mass_lines": nulls, "massprops_wet_all_kg": mp["states"]["wet"]["all"]["m_kg"],
                  "massprops_wet_groups_kg": {k: v["m_kg"] for k, v in mp["states"]["wet"].items()},
                  "grain_mass_wet_kg": mp.get("grain_mass_wet_kg"),
                  "n_instances_bom": bom["n_instances"], "n_instances_massprops_all": mp["states"]["wet"]["all"]["n"]}
    # fastener / seal lines present?
    fast = [l["pn"] for l in bom["lines"] if re.search(r"\b(screw|bolt|nut|washer|dowel|o-ring|AS568)\b", l.get("name", ""), re.I)]
    res["bom"]["lines_naming_fasteners_or_orings"] = fast
    # coverage
    steps = sorted(p.stem for p in (cad / "parts").glob("*.step"))
    stls = sorted(p.stem for p in (cad / "parts").glob("*.stl"))
    subs = set()
    for l in bom["lines"]:
        for s in re.split(r"[ ,;]+", l.get("sub_solids") or ""):
            if s.startswith("ENG-"):
                subs.add(s)
    man = json.loads((cad / "assembly/assembly_manifest_v3.5.json").read_text())
    inst_pn = {i["inst"].split("#")[0] for i in man["instances"]}
    res["coverage"] = {"n_step": len(steps), "n_stl": len(stls), "bom_pn_without_step": sorted(set(lines) - set(steps)),
                       "bom_pn_without_stl": sorted(set(lines) - set(stls)),
                       "step_not_in_bom": sorted(set(steps) - set(lines)), "declared_sub_solids": sorted(subs),
                       "step_not_in_bom_nor_sub_solid": sorted(set(steps) - set(lines) - subs),
                       "gse_in_assembly": sorted(gse & inst_pn), "bom_pn_not_in_assembly": sorted(set(lines) - inst_pn),
                       "assembly_instances": len(man["instances"])}
    out.write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps(res["bom"], indent=1, default=float))
    print(json.dumps(res["coverage"], indent=1))


if __name__ == "__main__":
    main()

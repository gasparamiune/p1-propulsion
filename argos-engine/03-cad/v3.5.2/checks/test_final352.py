"""FINAL v3.5.2 03-cad set check (lead release 19:09:50Z): what the FINAL build changed against the hub interim r4h6 set and the frozen
v3.5.1 set, before publication.  Software check on the CAD files, not physical validation.  Mechanical, 2026-10-20, v1.
(1) part files: STL sha256 of every final part against 03-cad/v3.5.1/parts (the changed-vs-v3.5.1 list of set_v3.5.2.json) and against the
    hub interim 03-cad/v3.5.2/parts (what this publication replaces);
(2) ENG-TC-01 (the only part whose geometry differs from the interim): STEP volumes, final minus interim (must be empty: material removal
    only) and interim minus final (the removed volume = the rev-5 d11.2 flats against the d10.5 flats), bounding boxes;
(3) assembly placements: byte-identical to the interim file (verified 149 / 149 in checks/verify_placements352_v1.json);
(4) BOM: lines whose content differs from the hub interim BOM, and the added lines;
(5) the build log of the final run (stages, round-trips)."""
import hashlib, json, sys
from pathlib import Path
import cadquery as cq

D = Path("/home/claude/work/mechanical/v352/engine/03-cad")
H = Path("/home/claude/work/shared-fallback/engine/03-cad")
OUT = Path("/home/claude/work/mechanical/v352/checks/test_final352_v1.json")


def sha(p, n=16):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:n]


parts = sorted(p.stem for p in (D / "parts").glob("*.step"))
assert len(parts) == 112, len(parts)
vs351, vs_interim, same_as_interim = [], [], []
for pn in parts:
    s = sha(D / "parts" / f"{pn}.stl")
    a = H / "v3.5.1/parts" / f"{pn}.stl"
    b = H / "v3.5.2/parts" / f"{pn}.stl"
    if not a.exists() or sha(a) != s:
        vs351.append({"pn": pn, "final_stl": s, "v351_stl": sha(a) if a.exists() else None})
    if b.exists():
        (same_as_interim if sha(b) == s else vs_interim).append({"pn": pn, "final_stl": s, "interim_stl": sha(b)})
assert [r["pn"] for r in vs_interim] == ["ENG-TC-01"], vs_interim

fin = cq.importers.importStep(str(D / "parts/ENG-TC-01.step")).val()
itm = cq.importers.importStep(str(H / "v3.5.2/parts/ENG-TC-01.step")).val()
added = fin.cut(itm)
removed = itm.cut(fin)
bbf, bbi = fin.BoundingBox(), itm.BoundingBox()
tc01 = {"final_step_sha256_16": sha(D / "parts/ENG-TC-01.step"), "interim_step_sha256_16": sha(H / "v3.5.2/parts/ENG-TC-01.step"),
        "V_final_mm3": round(fin.Volume(), 3), "V_interim_mm3": round(itm.Volume(), 3), "dV_mm3": round(fin.Volume() - itm.Volume(), 3),
        "final_minus_interim_mm3": round(added.Volume(), 6), "interim_minus_final_mm3": round(removed.Volume(), 3),
        "bbox_final_mm": [round(x, 4) for x in (bbf.xmin, bbf.ymin, bbf.zmin, bbf.xmax, bbf.ymax, bbf.zmax)],
        "bbox_interim_mm": [round(x, 4) for x in (bbi.xmin, bbi.ymin, bbi.zmin, bbi.xmax, bbi.ymax, bbi.zmax)],
        "valid_final": bool(fin.isValid())}
import math
sl = []
for so in added.Solids():
    c = so.Center()
    az = math.atan2(c.y, c.x)
    nx, ny = math.cos(az), math.sin(az)
    proj = [v.X * nx + v.Y * ny for v in so.Vertices()]
    sl.append({"V_mm3": round(so.Volume(), 6), "az_deg": round(math.degrees(az) % 360, 2), "r_centre_mm": round(math.hypot(c.x, c.y), 4),
               "thickness_along_flat_normal_mm": round(max(proj) - min(proj), 6), "z_extent_mm": round(so.BoundingBox().zlen, 4)})
tc01["final_minus_interim_pieces"] = sl
tc01["final_minus_interim_rule"] = ("material removal only, apart from coincident-face slivers on the r_flat 31.313 planes (the interim d10.5 "
                                    "flat and the final d11.2 flat are coplanar; STEP-precision boolean residue): every piece thinner than 0.001 mm "
                                    "along the flat normal and centred on r 31.313 +/- 0.001")
assert all(x["thickness_along_flat_normal_mm"] < 1e-3 and abs(x["r_centre_mm"] - 31.313) < 1e-3 for x in sl), sl
assert tc01["final_minus_interim_mm3"] < 0.1, tc01
assert tc01["valid_final"]

pl = {"final_sha256_16": sha(D / "assembly/placements_v3.5.2.json"), "interim_sha256_16": sha(H / "v3.5.2/assembly/placements_v3.5.2.json")}
pl["byte_identical"] = pl["final_sha256_16"] == pl["interim_sha256_16"]
assert pl["byte_identical"]

bf = json.loads((D / "BOM_v3.5.2.json").read_text())
bi = json.loads((H / "v3.5.2/BOM_v3.5.2.json").read_text())


def rows(b):
    r = {}
    for L in b["lines"]:
        r[("part", L["pn"])] = L
    for L in b["hardware"]["lines"] if isinstance(b.get("hardware"), dict) and "lines" in b["hardware"] else []:
        r[("hw", L["pn"])] = L
    for L in b.get("gse_tool_lines", []):
        r[("gse_tool", L["pn"])] = L
    return r


rf, ri = rows(bf), rows(bi)
bom = {"final_json_sha256_16": sha(D / "BOM_v3.5.2.json"), "interim_json_sha256_16": sha(H / "v3.5.2/BOM_v3.5.2.json"),
       "final_csv_sha256_16": sha(D / "BOM_v3.5.2.csv"), "interim_csv_sha256_16": sha(H / "v3.5.2/BOM_v3.5.2.csv"),
       "added": sorted("/".join(k) for k in rf if k not in ri), "removed": sorted("/".join(k) for k in ri if k not in rf),
       "changed": {"/".join(k): sorted(f for f in set(rf[k]) | set(ri[k]) if rf[k].get(f) != ri[k].get(f)) for k in rf if k in ri and rf[k] != ri[k]},
       "n_lines_final": bf["n_lines"], "n_lines_interim": bi["n_lines"], "mass_sum_kg_final": bf["mass_sum_kg"], "mass_sum_kg_interim": bi["mass_sum_kg"]}
log = json.loads((D / "checks/make_all_log_v3.5.2.json").read_text())
rt = json.loads((D / "checks/roundtrip_parts_v3.5.2.json").read_text())
ra = json.loads((D / "checks/roundtrip_assembly_v3.5.2.json").read_text())
gl = json.loads((D / "checks/glb_readback_v3.5.2.json").read_text())
out = {"id": "test_final352", "version": "v1", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
       "source": {"config.py": sha(D / "src/config.py"), "parts_engine.py": sha(D / "src/parts_engine.py"), "make_all.py": sha(D / "src/make_all.py"),
                  "hardware_v352.json": sha(D / "src/data/hardware_v352.json")},
       "make_all_log": log, "roundtrip_parts": {"n": rt["n"], "n_passed": rt["n_passed"]},
       "roundtrip_assembly_sha256_16": sha(D / "checks/roundtrip_assembly_v3.5.2.json"), "glb_readback_sha256_16": sha(D / "checks/glb_readback_v3.5.2.json"),
       "parts_changed_vs_v351": vs351, "parts_vs_hub_interim": {"differ": vs_interim, "n_identical": len(same_as_interim),
                                                                 "identical": [r["pn"] for r in same_as_interim]},
       "ENG-TC-01_final_vs_interim": tc01, "placements": pl, "bom_vs_hub_interim": bom}
assert rt["n"] == rt["n_passed"] == 112
s = json.dumps(out, indent=1, default=str)
OUT.write_text(s)
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16])
print(json.dumps({k: out[k] for k in ("parts_vs_hub_interim", "ENG-TC-01_final_vs_interim", "placements")}, indent=1)[:2500])
print("changed vs v3.5.1:", [r["pn"] for r in vs351])
print(json.dumps(bom, indent=1)[:3000])

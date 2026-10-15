"""N-F2 CAD check (v3.5.2, lead CHANGELOG 212): NZ-01 shoulder fillet, NZ-06 foil, stack stations, solid validity, volumes and masses vs the
TC-09-only v3.5.2 build (V352_TC09_ON).  Mechanical, 2026-10-13."""
import sys, json, hashlib
sys.path.insert(0, "/home/claude/work/mechanical/v352/engine/03-cad/src")
import config, build, engmat
out = {"id": "test_nf2", "version": "v1", "date": "2026-10-13", "owner": "mechanical", "builds": {}}
for tag, ov in (("v352_TC09only", config.V352_TC09_ON), ("v352_NF2", config.V352_ON)):
    P, S, reg, clog = build.build(include=("engine",), iterate_cg=False, overrides=dict(ov))
    b = {"stations_mm": {k: round(float(S[k]), 4) for k in ("lip_top", "insert_shoulder", "insert_top", "insert_bot", "aft_bottom", "gasket_t", "nz_seal_t", "nz_hot_layer_t") if k in S},
         "nz_foil_t_mm": S.get("nz_foil_t", 0.0), "nz01_shoulder_R_mm": S.get("nz01_shoulder_R_mm"), "parts": {}}
    for pn in ("ENG-NZ-01", "ENG-NZ-02", "ENG-NZ-03", "ENG-NZ-04", "ENG-NZ-06", "ENG-TC-09"):
        if pn not in reg.parts:
            continue
        p = reg.parts[pn]
        sh = p.shape
        bb = sh.BoundingBox()
        V = float(sh.Volume())
        b["parts"][pn] = {"material": p.material, "valid": bool(sh.isValid()), "n_solids": len(sh.Solids()) if hasattr(sh, "Solids") else None,
                          "volume_mm3": round(V, 3), "mass_g": round(V * 1e-9 * engmat.rho(p.material) * 1e3, 4),
                          "bbox_local_mm": [round(x, 3) for x in (bb.xmin, bb.ymin, bb.zmin, bb.xmax, bb.ymax, bb.zmax)],
                          "name": p.name}
        if pn == "ENG-NZ-01":
            b["parts"][pn]["n_torus_faces"] = sum(1 for f in sh.Faces() if f.geomType() == "TORUS")
    out["builds"][tag] = b
a, c = out["builds"]["v352_TC09only"], out["builds"]["v352_NF2"]
out["delta_g"] = {pn: round(c["parts"].get(pn, {}).get("mass_g", 0.0) - a["parts"].get(pn, {}).get("mass_g", 0.0), 4) for pn in set(a["parts"]) | set(c["parts"])}
out["delta_total_g"] = round(sum(out["delta_g"].values()), 4)
s = json.dumps(out, indent=1)
open("/home/claude/work/mechanical/v352/checks/test_nf2_v1.json", "w").write(s)
print(s[:3500]); print("sha256/16", hashlib.sha256(s.encode()).hexdigest()[:16])

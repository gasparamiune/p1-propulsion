"""Scratch driver: build only the gimbal parts (GM-01 / GM-02) from a given CAD src dir with the v3.5.2 overrides; export STEPs;
print the collar fillet logs and volumes."""
import sys, time, json, math
from pathlib import Path
SRC = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve(); OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(SRC)); sys.path.insert(0, str(SRC.parents[1] / "04-fea" / "src"))
import config, layout
from partlib import Registry
import parts_gimbal
import cadquery as cq
t0 = time.time()
P, clog = config.build()
for k, val in config.V352_ON.items():
    P[k] = {"v": val, "tag": "TRADE", "src": "drv"}
P["z_head_mid"] = {"v": 0.155513, "tag": "DERIVED", "src": "make_all v352 CG iteration"}
S = layout.stations(P)
reg = Registry()
parts_gimbal.build_gimbal_parts(P, S, reg, None)
print("build gimbal %.1f s" % (time.time() - t0))
res = {}
for p in reg:
    if p.pn in ("ENG-GM-01", "ENG-GM-02"):
        sh = p.shape
        cq.exporters.export(cq.Workplane().add(sh), str(OUT / f"{p.pn}.step"))
        res[p.pn] = {"volume_mm3": round(sh.Volume(), 3), "valid": sh.isValid(), "n_solids": len(sh.Solids()), "n_faces": len(sh.Faces()), "n_edges": len(sh.Edges())}
res["fillet_logs"] = S.get("collar_root_v351_fillets")
res["corner_logs"] = S.get("collar_root_v352_corner")
(OUT / "drv_result.json").write_text(json.dumps(res, indent=1, default=str))
print(json.dumps(res, indent=1, default=str))
print("arm_far_top_profile_v352", json.dumps(S.get("arm_far_top_profile_v352")))
print("cheek_v_fill_v352", json.dumps(S.get("cheek_v_fill_v352")))
print("cheek_bw_corner_v352", json.dumps(S.get("cheek_bw_corner_v352")))
res["cheek_bw_corner_v352"] = S.get("cheek_bw_corner_v352"); res["arm_far_top_profile_v352"] = S.get("arm_far_top_profile_v352")
(OUT / "drv_result.json").write_text(json.dumps(res, indent=1, default=str))

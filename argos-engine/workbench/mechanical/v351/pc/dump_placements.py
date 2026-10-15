"""Instance placements of CAD v3.5.1 (config.V351_ON, same build as make_all attempt 3): per instance the 4x4 transform from the part STEP
frame (part local, mm) to the engine frame (mm, +Z forward/up, origin = gimbal pivot) at the neutral pose, group and rigid body."""
import sys, json, hashlib
from pathlib import Path
sys.path.insert(0, "/home/claude/work/mechanical/v351/engine/03-cad/src")
import numpy as np
import config, build
P, S, reg, clog = build.build(include=("engine", "gimbal", "feed"), iterate_cg=True, overrides=dict(config.V351_ON))
out = {"id": "placements", "cad_version": "v3.5.1", "date": "2026-10-13", "owner": "mechanical",
       "frame": "engine frame, mm, +Z forward (up on the stand), origin = gimbal pivot (z_head_mid %.3f mm); per-part STEP files are in the part "
                "local frame; x_engine = T @ x_part (homogeneous, mm)" % (P["z_head_mid"]["v"] * 1000.0),
       "pose": "neutral (alpha = beta = 0); horns/pushrods/hoses/lines follow tvc_pose_frames / posed_flex at other poses (see the assembly STEP stop045)",
       "instances": []}
for p in reg:
    for i, (T, g) in enumerate(p.placements):
        out["instances"].append({"pn": p.pn, "idx": i, "group": g, "body": build.body_of(g, i, p.pn), "material": p.material,
                                 "T_4x4_mm": np.round(np.array(T, float), 6).tolist()})
Path(sys.argv[1]).write_text(json.dumps(out, indent=1))
print(len(out["instances"]), "instances; z_head_mid", P["z_head_mid"]["v"])

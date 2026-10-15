import sys, json, numpy as np
from pathlib import Path
sys.path.insert(0, "/home/claude/work/mechanical/v351/engine/04-fea/structural")
import sax
RT = Path("/home/claude/work/mechanical/runs/thermal")
RS = Path("/home/claude/work/mechanical/runs/structural")
out = {}
smesh = {"v341revB": RS / "L1" / "mesh.npz", "v351": RS / "L1_thv351_TB1GC_cad351" / "mesh.npz"}
ztop_s = {}
for k, f in smesh.items():
    z = np.load(f, allow_pickle=True)
    X, pn = z["X"], z["pn"]
    E = z["E"]
    nodes = np.unique(E[pn == "ENG-TC-02"])
    ztop_s[k] = float(X[nodes, 1].max())
for tag, cadk in (("v13pre36IN_J1revB", "v341revB"), ("v13pre36IN_J1revB_TC09IN", "v341revB"), ("v13pre36IN_J2revB", "v341revB"), ("v351_TB1GC", "v351")):
    for dc in ("DC-B1v3p99_tg711_hi_SS316L_L2.5_", "DC-A1dispp99_tg711_hi_SS316L_L2.5_"):
        rd = RT / (dc + tag)
        Xt, Et, pnt = sax.thermal_mesh(rd)
        nt = np.unique(Et[pnt == "ENG-TC-02"])
        zt = float(Xt[nt, 1].max())
        meta = json.loads(next(rd.glob("*_meta.json")).read_text())
        mon = float(meta["case"]["monitors"]["head_top_r12"][1])
        out[rd.name] = {"thermal_TC02_top_z": round(zt, 4), "structural_TC02_top_z": round(ztop_s[cadk], 4), "dz_exact_mm": round(zt - ztop_s[cadk], 4),
                        "dz_used_monitor_mm": round(mon - ztop_s[cadk], 4) if False else None, "monitor_z": mon}
for k, v in out.items():
    print(k, v)
json.dump(out, open("/home/claude/work/mechanical/v351/prov/dz_check_v1.json", "w"), indent=1)

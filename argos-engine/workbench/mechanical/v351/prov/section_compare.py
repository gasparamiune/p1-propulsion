"""Provenance check (lead relay 17:0xZ): is the S-AX section cached at 09:32 (geom_v341revB, used by every v3.5 S-AX run) the same as
the section of the CAD v3.5 run-6 configuration (config.V34_ON now) and of the thermal-run configuration (BASE + the thermal overrides)?
Per part: area and area centroid (r, z) of the section faces; z compared after aligning the head top (as sax.thermal_dz does)."""
import sys, os, json, math
from pathlib import Path
sys.path.insert(0, "/home/claude/work/mechanical/v351/engine/04-fea/structural")
sys.path.insert(0, "/home/claude/work/mechanical/v351/engine/03-cad/src")
sys.path.insert(0, "/home/claude/work/mechanical/v351/engine/04-fea/thermal")
import cadquery as cq
OUT = Path("/home/claude/work/mechanical/v351/prov")
def props(faces):
    d = {}
    for f in faces:
        fa = f["face"]
        A = fa.Area()
        c = fa.Center()
        e = d.setdefault(f["pn"], {"A": 0.0, "Ar": 0.0, "Az": 0.0, "n": 0, "mat": f["material"]})
        e["A"] += A; e["Ar"] += A * c.x; e["Az"] += A * c.y; e["n"] += 1
    return {k: {"area_mm2": round(v["A"], 3), "r_c": round(v["Ar"] / v["A"], 4), "z_c": round(v["Az"] / v["A"], 4), "n_faces": v["n"], "material": v["mat"]}
            for k, v in sorted(d.items())}
res = {}
# (1) cached v3.4.1 rev B section (09:32)
import sax
fc, ic = sax.geometry(cache=Path("/home/claude/work/mechanical/runs/structural/geom_v341revB"))
res["cache_09:32_geom_v341revB"] = {"head_top": ic["head_top"], "parts": props(fc)}
# (2) the same builder on the current config.V34_ON (= CAD v3.5 run 6) into a scratch cache
tmp = OUT / "geom_v34on_now"
fn, inn = sax.geometry(cache=tmp, rebuild=True)
res["now_V34_ON_cad_v3.5"] = {"head_top": inn["head_top"], "parts": props(fn)}
# (3) thermal-run section (BASE config + the overrides of the v13 J1 rev B thermal runs), same section angle as the thermal model
import ax_section
ov = {"D_pre": 0.0499, "tc03_material": "IN718", "nozzle_joint": "J1", "insert_sleeve_material": "CARBON-PHENOLIC"}
ft, it, _ = ax_section.section(overrides=ov)
res["thermal_BASE_plus_overrides"] = {"head_top": it["head_top"], "overrides": ov, "parts": props(ft)}
json.dump(res, open(OUT / "section_compare_v1.json", "w"), indent=1)
a, b, t = res["cache_09:32_geom_v341revB"], res["now_V34_ON_cad_v3.5"], res["thermal_BASE_plus_overrides"]
print("head_top", a["head_top"], b["head_top"], t["head_top"])
for pn in a["parts"]:
    x, y, z = a["parts"][pn], b["parts"].get(pn, {}), t["parts"].get(pn, {})
    print(f"{pn:10s} cache A {x['area_mm2']:9.2f} rc {x['r_c']:7.3f} zc-ht {x['z_c']-a['head_top']:8.3f} | V34_ON now A {y.get('area_mm2',0):9.2f} rc {y.get('r_c',0):7.3f} zc-ht {y.get('z_c',0)-b['head_top']:8.3f}"
          f" | thermal A {z.get('area_mm2',0):9.2f} rc {z.get('r_c',0):7.3f} zc-ht {z.get('z_c',0)-t['head_top']:8.3f}")

"""Boolean difference volume between two STEP solids (A - B, B - A) in mm3: the port check dev STEP vs the scratch D6 STEP. Mechanical 2026-10-20."""
import sys, json
import cadquery as cq
a = cq.importers.importStep(sys.argv[1]).val(); b = cq.importers.importStep(sys.argv[2]).val()
print(json.dumps({"a": sys.argv[1], "b": sys.argv[2], "V_a": round(a.Volume(), 4), "V_b": round(b.Volume(), 4),
                  "V_a_minus_b": round(a.cut(b).Volume(), 6), "V_b_minus_a": round(b.cut(a).Volume(), 6)}))

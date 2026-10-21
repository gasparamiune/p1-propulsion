"""rv7_repro v1.0 (REV-GNC-7 reviewer): runs m2_eng11_fe v1.0 variants unchanged (original c71 inputs), optionally on a
subset of K_s rows (RV7_KS), for the reproduction of the staged rev4b results.  Env: RV7_VARIANTS, GNC_E11FE_OUT, RV7_KS."""
import os
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m2_eng11_fe as F  # noqa: E402
if os.environ.get("RV7_KS"):
    F.KS = tuple(float(x) for x in os.environ["RV7_KS"].split(","))
os.makedirs(F.OUT, exist_ok=True)
ctx = F.Ctx()
print(f"rv7_repro v1.0 on {F.VERSION}; KS {F.KS}", flush=True)
for vid in [v for v in os.environ.get("RV7_VARIANTS", "").split(",") if v]:
    F.run_variant(ctx, vid)
    print(f"== {vid} done", flush=True)

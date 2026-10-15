"""m2_tailoff_fit v1 (2026-10-12): fit the GNC reduced shutdown model (gncsim.tailoff) to Combustion's
actuator_rate_check_v2.json shutdown runs and store the constants with the source sha256 in
data/tailoff/tailoff_fit_v1.json (read by run6 v2.6 for toff_model = 1).
Env: GNC_IFACE (interfaces folder holding combustion.json >= v2.2), GNC_ACT_RATE (optional file override),
GNC_TOFF_STROKES (comma list of full-stroke times, default 0.25,0.24,0.149,0.4)."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import tailoff  # noqa: E402

IFACE = os.environ.get("GNC_IFACE", "/home/claude/work/shared-fallback/engine/interfaces")
comb = json.load(open(os.path.join(IFACE, "combustion.json")))
chk, sha, path = tailoff.load_checks(comb)
strokes = [float(x) for x in os.environ.get("GNC_TOFF_STROKES", "0.25,0.24,0.149,0.4").split(",")]
out = dict(version="v1", date=time.strftime("%Y-%m-%d"), model=tailoff.__doc__.strip().split("\n\n")[1],
           tag="DERIVED (GNC fit of the reduced model to Combustion SIM grain_q1d v2 shutdown runs)", fits=[])
if os.path.exists(tailoff.FIT_PATH):
    old = json.load(open(tailoff.FIT_PATH))
    out["fits"] = [f for f in old.get("fits", []) if f["source_sha256"] != sha]
for fs in strokes:
    t0 = time.time()
    f = tailoff.fit(chk, fs)
    f.update(source=path, source_sha256=sha, source_version=chk.get("version"),
             combustion_json_version=comb.get("version"))
    out["fits"].append(f)
    print(f"full stroke {fs:.3f} s: v_s {f['speed_mm_s']:.2f} mm/s  l_cut {f['l_cut_mm']:.3f} mm  lag_a "
          f"{1e3 * f['lag_a_s']:.0f} ms  lag_c {1e3 * f['lag_c_s']:.0f} ms  ({time.time() - t0:.0f} s)")
    for r in f["residuals"]:
        print(f"   F0 {r['F0_N']:6.1f} N: t10 {r['t10_gnc_s']:.3f} vs {r['t10_comb_s']:.3f} s ({r['t10_err_ms']:+.1f} ms), "
              f"impulse {r['imp_gnc_Ns']:6.2f} vs {r['imp_comb_Ns']:6.2f} N s ({r['imp_err_pct']:+.1f} %)")
os.makedirs(os.path.dirname(tailoff.FIT_PATH), exist_ok=True)
with open(tailoff.FIT_PATH, "w") as fo:
    json.dump(out, fo, indent=1)
print("wrote", tailoff.FIT_PATH)

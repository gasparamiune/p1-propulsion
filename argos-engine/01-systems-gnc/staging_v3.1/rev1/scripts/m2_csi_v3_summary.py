"""Print the m2_csi_v3 result tables (base corners, notch grid, structural sweep). Env GNC_OUT, GNC_CSI_TAG."""
import json
import os
OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/csi_v3")
TAG = os.environ.get("GNC_CSI_TAG", "fea")
d = json.load(open(os.path.join(OUT, f"csi_v3_{TAG}.json")))
f = lambda v: "-" if v is None else f"{v:.1f}"  # noqa: E731
print("mass properties:", {k: {kk: round(vv, 4) if isinstance(vv, float) else vv for kk, vv in v.items()} for k, v in d["mass_properties"].items()})
for k, s in d.get("base", {}).items():
    print(f"BASE {k:22s} unstable {s['n_unstable']:3d}/{s['n']} <6dB {s['n_below_6dB']:3d} GMmin {f(s['gm_up_min_dB'])} "
          f"gain@rock max {s['gain_at_rock_max_dB']:.1f} dB f {s['f_rock_Hz'][0]:.1f}-{s['f_rock_Hz'][1]:.1f} Hz")
    for w in s["worst"][:3]:
        print(f"      {w['corner']:60s} stable {w['stable']} GM {f(w['gm_up_dB'])} PMmin {f(w['pm_min_deg'])} g@rock {w['gain_at_rock_dB']:.1f} f {w['f_rock_Hz']:.1f}")
if "rigid" in d:
    for k, r in d["rigid"].items():
        print("RIGID", k, "unstable", r["n_unstable"], "PM min", f(r["pm_min_deg"]), "GM min", f(r["gm_up_min_dB"]))
for k, s in d.get("notch", {}).items():
    print(f"NOTCH {k:34s} unstable {s['n_unstable']:3d}/{s['n']} <6dB {s['n_below_6dB']:3d} GMmin {f(s['gm_up_min_dB'])}")
for k, v in d.get("notch_rigid_cost", {}).items():
    print("NOTCH-RIGID", k, v)
for k, rows in d.get("sweep", {}).items():
    for r in rows:
        print(f"SWEEP {k:34s} K_struct {r['K_struct']:10.0f} K {r['K_series'][0]:.0f}-{r['K_series'][1]:.0f} unstable "
              f"{r['n_unstable']} <6dB {r['n_below_6dB']} GMmin {f(r['gm_up_min_dB'])} f {r['f_rock_Hz'][0]:.1f}-{r['f_rock_Hz'][1]:.1f}")

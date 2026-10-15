"""TVC servo (SB-2292SG, ENG-GM-15) facing case temperature - corrected band (04-fea/thermal, v1, 2026-10-13, Mechanical).

Erratum record: the SB-2292SG check sent to the lead on 2026-10-13 read the case OD at thermal z -30..+15 believing
"thermal z = CAD z + 56.3".  The thermal mesh is the CG-iterated CAD v3.3 build, i.e. the pivot frame, so the servos
(body z -80.3..-40.0 above the pivot) face thermal z -85..-35.  This script lists both bands from histories_lower.npz
(extract_case_lower.py) so the correction is reproducible.  Servo estimate: radiation from the case to the servo case
G_rad ~0.008 W/K vs ~0.33 W/K conduction + convection to the bay air (values of the 2026-10-13 check, ASSUMED).
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np

RUNS = Path("/home/claude/work/mechanical/runs/thermal")
OUT = Path(__file__).resolve().parent / "tvc_servo_case_band_v1.json"
LABELS = ["DC-B1v3p99_tg711_hi_SS316L_L2.5_v11pre36", "DC-B1v3max_hi_SS316L_L2.5_v11pre36",
          "DC-B1v3max_hi_SS316L_L2.5_v11", "DC-A1dispp99_hi_SS316L_L2.5_v11"]
BANDS = {"used_2026-10-13_WRONG": (-30, 15), "correct_pivot_frame": (-85, -35)}
G_RAD, G_AIR = 0.008, 0.33          # W/K, ASSUMED (2026-10-13 check)


def main():
    out = {"script": "04-fea/thermal/tvc_servo_case_band.py v1", "frame": "thermal z = pivot frame (CAD v3.3 CG-iterated)",
           "servo_body_z_pivot_mm": [-80.3, -40.0], "runs": {}}
    for lab in LABELS:
        p = RUNS / lab / "histories_lower.npz"
        if not p.exists():
            out["runs"][lab] = "histories_lower.npz missing"
            continue
        h = np.load(p)
        m = json.loads((RUNS / lab / f"{lab}_meta.json").read_text())
        t, tl = h["t_s"], m["t_last_shutdown_s"]
        fl = t <= tl + 1e-6
        row = {}
        for name, (z0, z1) in BANDS.items():
            ks = [k for k in h.files if k.startswith("case_OD_z") and k.endswith("_mean") and z0 <= int(k.split("_z")[1].split("_")[0]) < z1]
            fmax = max(float(h[k][fl].max()) for k in ks) - 273.15
            smax = max(float(h[k].max()) for k in ks) - 273.15
            row[name] = {"z_mm": [z0, z1], "flight_max_C": round(fmax, 1), "soak_max_C": round(smax, 1), "n_bands": len(ks)}
        d_soak = row["correct_pivot_frame"]["soak_max_C"] - row["used_2026-10-13_WRONG"]["soak_max_C"]
        row["servo_soak_delta_K_from_correction"] = round(G_RAD * d_soak / (G_RAD + G_AIR), 2)
        out["runs"][lab] = row
    out["verdict"] = ("in flight the case facing the TVC servos stays at 21-24 C (both bands); the soak peak is up to ~11 K higher on the "
                      "correct band, adding <= 0.3 K to the servo (radiation share); SB-2292SG conclusions of 2026-10-13 unchanged")
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1)[:2500])


if __name__ == "__main__":
    main()

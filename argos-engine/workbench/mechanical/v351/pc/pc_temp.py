"""Line 203 / coordinator item 2: Pc transducer temperature from MECO to RELIGHT (close-coupled seat on the head top, r 25 / 142 deg)
from the v3.5.1 thermal runs (monitor T1_head_top_bracket_foot r 25.5 on the head top; head_top_r12 for comparison)."""
import numpy as np, json, glob
from pathlib import Path
RT = Path("/home/claude/work/mechanical/runs/thermal")
out = {}
for run in ["DC-A1dispp99_tg711_hi_SS316L_L2.5_v351_TB1GC", "DC-B1v3p99_tg711_hi_SS316L_L2.5_v351_TB1GC"]:
    m = json.load(open(glob.glob(str(RT / run / "*_meta.json"))[0]))
    seg = m["segments_s"]
    lines = (RT / run / "monitors.csv").read_text().splitlines()
    hdr = lines[1].split(",")
    a = np.array([[float(x) for x in l.split(",")] for l in lines[2:] if l.strip()])
    t = a[:, 0]
    res = {"segments_s": seg, "monitor_positions": {k: m["case"]["monitors"][k] for k in ("T1_head_top_bracket_foot", "head_top_r12", "head_bore_N2O")},
           "monitors_csv": str(RT / run / "monitors.csv"), "series": {}}
    for col in ["T1_head_top_bracket_foot", "head_top_r12", "bonnet_face_oring", "head_bore_N2O", "head_oring_upper"]:
        T = a[:, hdr.index(col)] - 273.15
        o = {}
        if len(seg) > 1:
            meco, rel = seg[0][1], seg[1][0]
            w = (t >= meco) & (t <= rel)
            o.update({"at_MECO_C": round(float(np.interp(meco, t, T)), 1), "max_MECO_to_RELIGHT_C": round(float(T[w].max()), 1),
                      "t_of_max_s": round(float(t[w][np.argmax(T[w])]), 2), "at_RELIGHT_C": round(float(np.interp(rel, t, T)), 1),
                      "max_burn2_C": round(float(T[(t >= rel) & (t <= seg[1][1])].max()), 1)})
        ws = t >= seg[-1][1]
        o.update({"at_last_shutdown_C": round(float(np.interp(seg[-1][1], t, T)), 1), "max_soak_C": round(float(T[ws].max()), 1),
                  "t_of_soak_max_s": round(float(t[ws][np.argmax(T[ws])]), 1), "max_all_C": round(float(T.max()), 1)})
        res["series"][col] = o
        print(run[:12], f"{col:26s}", o)
    out[run] = res
json.dump(out, open("/home/claude/work/mechanical/v351/pc/pc_transducer_temperature_v1.json", "w"), indent=1)

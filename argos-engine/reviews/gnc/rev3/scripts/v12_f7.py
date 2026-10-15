"""REV-GNC-5 v12: independent recount of F7 (R2 v2 flame-out side) from the staged rev3 statistics tables: design flame-out
set pw|G73|r2s_fo_cb / fo_cb_dt05 / fo_cb_dt10 (both main bases), mode 3 (E2 re-reference + drag compensation), windows 0.5 /
0.8 s (columns pv2_s5_3 / pv2_s8_3; runs whose R2 window opened, statistic > -998); max, p99 and count >= T_rev2 for all
winds and W10 < 6 m/s; sensitivities.  SIM tables -> DERIVED.  Usage: python -I v12_f7.py <out.json>"""
import json, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rv5lib as L
T = 37.15933451611584
out = dict(script="v12_f7 (REV-GNC-5)", tag="SIM tables; DERIVED", T_rev2=T, sets={})
for setname, arms in (("design", ("fo_cb", "fo_cb_dt05", "fo_cb_dt10")), ("fo_cb130", ("fo_cb130",)), ("fo_cn", ("fo_cn",)),
                      ("fo_none", ("fo_none",)), ("fo_cb_nohold", ("fo_cb_nohold",))):
    for win in ("s5", "s8"):
        for m in (0, 3):
            s_all, s_in = [], []
            for a in arms:
                for b in L.MAIN:
                    rows = L.load3(b, f"pw|G73|r2s_{a}|h285")
                    s = np.array(L.col(rows, f"pv2_{win}_{m}")); w = np.array(L.col(rows, "wind"))
                    act = np.array(L.col(rows, "pv2_s8_0")) > -998.0
                    s_all.append(s[act]); s_in.append(s[act & (w < 6.0)])
            A = np.concatenate(s_all); I = np.concatenate(s_in)
            out["sets"][f"{setname}|{win}|mode{m}"] = dict(n_all=int(len(A)), max_all=round(float(A.max()), 3), above_T_all=int((A >= T).sum()),
                                                          margin_all=round(T - float(A.max()), 3), n_in=int(len(I)), max_in=round(float(I.max()), 3),
                                                          above_T_in=int((I >= T).sum()), margin_in=round(T - float(I.max()), 3))
json.dump(out, open(sys.argv[1], "w"), indent=1)
for k, d in out["sets"].items():
    print(f"{k:24s} all n {d['n_all']} max {d['max_all']} (margin {d['margin_all']}, >=T {d['above_T_all']}) | W10<6 n {d['n_in']} max {d['max_in']} (margin {d['margin_in']}, >=T {d['above_T_in']})")

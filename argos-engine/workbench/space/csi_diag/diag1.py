import os, sys, json, numpy as np, control as ct
sys.path.insert(0, "/home/claude/work/space/gnc_dev/scripts"); sys.path.insert(0, "/home/claude/work/space/gnc_dev")
import m2_csi_v3 as V, m2_csi as C
relay = json.load(open(V.RELAY)); n = relay["n_linkage"]["v"]
conds, meta, srcs = V.build_conditions(relay)
def crossings(case, notch):
    L = ct.series(C.cmd_filter(case), C.loop_flex(case))
    if notch: L = ct.series(V.notch_tf(*notch), L)
    gm, pm, sm, wpc, wgc, wms = ct.stability_margins(L, returnall=True)
    return [(round(float(w)/(2*np.pi),2), round(20*np.log10(g),1)) for g, w in zip(np.atleast_1d(gm), np.atleast_1d(wpc)) if np.isfinite(g) and g>0], \
           [(round(float(w)/(2*np.pi),2), round(float(p),1)) for p, w in zip(np.atleast_1d(pm), np.atleast_1d(wgc))]
for J in (0.0, 1.6e-3):
  for cn in ("landing|floor62N|act_fast|noaero", "landing|floor100N|act_nom|noaero", "landing|hover|act_nom|noaero", "landing|max500N|act_fast|noaero", "full|max500N|act_fast|noaero"):
    for K in (729.0, 1145.0):
        for zr in (0.02,):
            c = V.flex_case(conds[cn], K, zr, J, n); fr = c["w_rock"]/(2*np.pi)
            for lab, nt in (("lpf", None), ("Q1-12 mis.85", (0.85*fr, 1.0, -12.0)), ("Q1-12 mis1", (fr,1.0,-12.0)), ("Q1-12 mis1.15",(1.15*fr,1.0,-12.0)), ("Q2-20 mis.85",(0.85*fr,2.0,-20.0)), ("Q2-20 mis1.15",(1.15*fr,2.0,-20.0)), ("Q3-20 mis1",(fr,3.0,-20.0))):
                r = V.evaluate(c, True, nt); g, p = crossings(c, nt)
                print(f"J{J*1e3:g} {cn:34s} K{K:.0f} z{zr} f{fr:.1f} {lab:14s} stable {r['stable']} GMup {r['gm_up_dB'] if r['gm_up_dB'] is None else round(r['gm_up_dB'],1)} g@rock {r['gain_at_rock_dB']:.1f} | GM crossings (Hz,dB) {g} | PM crossings (Hz,deg) {p}")

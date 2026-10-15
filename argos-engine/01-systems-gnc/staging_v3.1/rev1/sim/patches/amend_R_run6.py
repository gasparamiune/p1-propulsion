"""Apply run6 amendment R (drogue release rule parameters) to a run6.py file (path argument). Requires amendments M, W, F and P.
v1 (GNC, 2026-10-13)."""
import sys

p = sys.argv[1]
s = open(p).read()


def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, (old[:80], n)
    s = s.replace(old, new)


rep("bleed jet bl_vj / bl_az): parameters passed to sim6, off by default;",
    "bleed jet bl_vj / bl_az) and R (drogue release rule rel_mode / rel_Pc / rel_dt): parameters passed to sim6, off by default;")
rep("bl_az=0.0, gim_notch_f=0.0,", "bl_az=0.0, rel_mode=0, rel_Pc=3.0e5, rel_dt=0.0, gim_notch_f=0.0,")
rep('''    S("det_op_t", float(cfg["det_op_t"]), "DESIGN firmware kPcOverPressureTime_s persistence [s] (Pc filter lag not modelled)")
''', '''    S("det_op_t", float(cfg["det_op_t"]), "DESIGN firmware kPcOverPressureTime_s persistence [s] (Pc filter lag not modelled)")
    # v2.8-dev amendment R (coordinator relay 2026-10-13, light-detection fix): drogue release rule
    S("rel_mode", float(cfg["rel_mode"]), "CONFIG 0 = v2.8 model (F > 0.5 floor); 1 = adopted rule: E2 (relative light "
                                          "confirmation) AND measured Pc >= rel_Pc")
    if not (pcm_[0] < float(cfg["rel_Pc"]) < pcm_[-1]):
        raise ValueError("amendment R: the map Pc(F) must bracket the release pressure")
    S("rel_F", float(np.interp(float(cfg["rel_Pc"]), pcm_, Fgm_)),
      f"DERIVED map thrust at the drogue-release pressure {cfg['rel_Pc'] / 1e5:.2f} bar abs (LEAD 2026-10-13 fixed value, not "
      "tied to the floor; combustion map Pc(F), port-independent) [N, Pc-equivalent]")
    S("rel_dt", float(cfg["rel_dt"]), "ASSUMED E2 (relative rule: +0.8 bar over the pre-lift baseline, 10 ms) after the 6-DOF "
                                      "light [s]; 0 = the relative E2 (14.0-15.5 ms after main ignition, Combustion "
                                      "ignition_detect_v2p4) precedes the 6-DOF light drawn on the old 3.0 bar rule")
''')
open(p, "w").write(s)
print("amendment R applied to", p)

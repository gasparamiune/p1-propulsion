"""m2_r2_starve v1.0 (GNC rev4, 2026-10-19): R2 v2 starve threshold per confirmation window (REV-ELEC-2 R2-16; lead line
216 (1) and lead message 2026-10-13 ~19:05Z item (c): Electronics' stand-in gives 0.46-0.48 s at the 0.5 s window).

Question: the longest fuel-starved start plateau after which a LIT vehicle is still released by R2 v2 inside the window
(longer plateaus: lit vehicle held and aborted at E2 + window). Flown in GNC's 6-DOF with the R2 v2 candidate exactly as
the rev3 P4 statistics / P4c confirmation arms: sim6 v2.13-dev (gnc_dev7; amendment J off = v2.12, m2_bitcheck_v213),
v3d interface set with the rev3 pins (as rev3 P4), A1_none, line state pw, purge G73, 285 m trim, seed 101, runs 0..N-1,
amendment V Pc invalid from E2 (pcf_dt 0), command hold 62.5 N (pv2_hold), open-loop factor pcf_k 0.875, baseline mode 3
(E2 re-reference + drogue-drag compensation), pcf_n 3 frames, start plateau st_on with st_Pc 2.4 bar abs for st_T s (the
L400 bracket generalised to st_T 0-0.80 s). Threshold: the R2 threshold kept by R2 v2, rel_F = 37.16 N (pcf_Facc; rev3 P4c
and RV5-09: mode-3 flame-out maxima 34.88 N at 0.5 s / 39.45 N at 0.8 s all winds, 31.18 / 31.86 N at W10 < 6 m/s).
Output: out/rev4/r2_starve/r2_starve.json: per window, threshold and st_T the released / aborted counts (all runs and
W10 < 6 m/s), release time after E2 (p50 / max), and the starve threshold = largest st_T with every lit run released.
SIM on DERIVED / ASSUMED inputs (plateau level and length are Combustion's bracket, not measured). Not physical approval."""
import json
import os
import sys
import time
from collections import OrderedDict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m2_rg01_refly as F  # noqa: E402
from gncsim import run6 as R, sim6 as s6  # noqa: E402

VERSION = "m2_r2_starve v1.0"
OUT = os.environ.get("GNC_R2S_OUT", "/home/claude/work/space/out/rev4/r2_starve")
N = int(os.environ.get("GNC_R2S_N", "60"))
BASE = "A1_none"
ST_T = (0.0, 0.2, 0.3, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8)
CASES = (("w0.5", 0.5, 37.16), ("w0.8", 0.8, 37.16))
PC2C = dict(pcf_on=1, pcf_dt=0.0, pcf_rule=2, pv2_on=1, pv2_hold=1, pv2_Fh=62.5, pv2_bl=3, pcf_k=0.875)


def main():
    os.makedirs(OUT, exist_ok=True)
    p_out = os.path.join(OUT, "r2_starve.json")
    if os.path.exists(p_out) and os.environ.get("GNC_R2S_FORCE", "0") != "1":
        try:
            prev = json.load(open(p_out))
            if prev.get("version") == VERSION and prev.get("sim") == s6.SIM6_VERSION and int(prev.get("N", -1)) == N:
                print("r2_starve: output exists for this version/sim/N, skipped (GNC_R2S_FORCE=1 re-runs)", flush=True)
                return
        except Exception:
            pass
    lock = os.path.join(OUT, "r2_starve.lock")
    if os.path.exists(lock):
        try:
            pid = int(open(lock).read().strip())
            os.kill(pid, 0)
            print(f"r2_starve: another instance (PID {pid}) is running, skipped", flush=True)
            return
        except (ValueError, ProcessLookupError, PermissionError):
            pass
    open(lock, "w").write(str(os.getpid()))
    t0 = time.time()
    cfg, m = F.base_cfg(BASE, "pw", dict(h_target=285.0))
    jr = json.load(open(F.TG))["j_ref"]
    F.MV.TG_JREF_DEFAULT = float(jr["A1"])
    D = R.draw(np.random.default_rng(101), N, cfg)
    ms = F.MV.case_specs()["tot_cal_comp"]
    res = OrderedDict(version=VERSION, date=time.strftime("%Y-%m-%d"), sim=s6.SIM6_VERSION, iface=os.environ.get("GNC_IFACE"),
                      pin=os.environ.get("GNC_IFACE_PIN"), base=BASE, state="pw", N=N, settings=PC2C,
                      plateau="st_on 1, st_Pc 2.4e5 Pa, st_T varied (L400 = 0.4 s)", cases=OrderedDict())
    wind = np.array([float(D[i]["_wind"]) for i in range(N)])  # W10: run6 draw U(0, 8) m/s at 10 m (cfg wind)
    calm = wind < 6.0
    for nm, w, T in CASES:
        ce = OrderedDict(window_s=w, threshold_N=T, by_st_T=OrderedDict())
        for stT in ST_T:
            rel, relt, abt, ok = [], [], [], []
            for i in range(N):
                c, disp = F.MV.run_cfg_case(cfg, D[i], ms, i, "base")
                c.update(F.DEC)
                c.update(F.PURGE["G73"])
                if stT > 0.0:
                    c.update(st_on=1, st_Pc=2.4e5, st_T=stT)
                c.update(PC2C)
                c.update(pcf_tmax=w, pcf_Facc=T)
                r = R.fly(c, disp, nrec=10)[0]
                rel.append(float(r["pcf_rel"]) > 1.5)
                relt.append(float(r["pcf_relt"]))
                abt.append(float(r["pcf_abt"]) > 0.5)
                ok.append(bool(R.success(r)))
            rel, abt, relt, ok = np.array(rel), np.array(abt), np.array(relt), np.array(ok)
            e = OrderedDict()
            for sub, msk in (("all", np.ones(N, bool)), ("W10lt6", calm)):
                rt = relt[msk & rel]
                e[sub] = dict(n=int(msk.sum()), released=int((rel & msk).sum()), aborted=int((abt & msk).sum()),
                              landed=int((ok & msk).sum()),
                              rel_t_p50_s=(float(np.median(rt)) if len(rt) else None), rel_t_max_s=(float(rt.max()) if len(rt) else None))
            ce["by_st_T"][f"{stT:g}"] = e
            print(f"{nm:12s} T {T:6.3f} st_T {stT:4.2f}: released {e['all']['released']}/{N} (W10<6 {e['W10lt6']['released']}/"
                  f"{e['W10lt6']['n']}) aborted {e['all']['aborted']} rel_t max {e['all']['rel_t_max_s']}", flush=True)
        ce["starve_threshold_s"] = OrderedDict()
        for sub in ("all", "W10lt6"):
            allok_below = None
            for k in sorted(float(x) for x in ce["by_st_T"]):
                v = ce["by_st_T"][f"{k:g}"][sub]
                if v["released"] == v["n"]:
                    allok_below = k
                else:
                    break
            ce["starve_threshold_s"][sub] = allok_below
        res["cases"][nm] = ce
    res["wall_s"] = round(time.time() - t0, 1)
    p = os.path.join(OUT, "r2_starve.json")
    json.dump(res, open(p, "w"), indent=1, default=float)
    print("wrote", p, flush=True)


if __name__ == "__main__":
    main()

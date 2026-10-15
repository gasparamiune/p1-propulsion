"""REV-GNC-3 reviewer probes of amendment V (R2) on base A1_none, 500 runs, seed 101, same draws as the author's arms.
Arms (added to the author's ARMS table in memory only; flown with the author's fly_arm on the verified scratch copy):
  pw|G73|rvR2fo_t08     undetected flame-out at E2, R2, pcf_tmax 0.8 s (lead line 175 (5) proposal; author flew 0.5 s)
  pw|G73|rvR2L400k_t05  R2 with the 2.4 bar x 0.4 s plateau AND the low open-loop factor pcf_k 0.875, pcf_tmax 0.5 s (not flown)
  pw|G73|rvR2L400k_t08  the same at pcf_tmax 0.8 s
  pw|G73|rvR2L400_t08   R2 + L400 at pcf_tmax 0.8 s (author flew 0.5 s: pcfR2L400)
Writes CSVs to $RV_VOUT and prints per-arm statistics; pairing against the author's stored tables in the hub staging.
"""
import os
import sys
import time
import numpy as np

RUN = os.environ["RV_RUN"]
sys.path.insert(0, RUN)
sys.path.insert(0, os.path.join(RUN, "scripts"))
import m2_rg01_refly as F  # noqa: E402

OUTV = os.environ["RV_VOUT"]
os.makedirs(OUTV, exist_ok=True)
L400 = dict(st_on=1, st_Pc=2.4e5, st_T=0.4)
PROBES = {
    "pw|G73|rvR2fo_t08": dict(pcf_on=1, pcf_dt=0.0, pcf_rule=2, pcf_fo=1, pcf_tmax=0.8),
    "pw|G73|rvR2L400k_t05": dict(pcf_on=1, pcf_dt=0.0, pcf_rule=2, pcf_k=0.875, pcf_tmax=0.5, **L400),
    "pw|G73|rvR2L400k_t08": dict(pcf_on=1, pcf_dt=0.0, pcf_rule=2, pcf_k=0.875, pcf_tmax=0.8, **L400),
    "pw|G73|rvR2L400_t08": dict(pcf_on=1, pcf_dt=0.0, pcf_rule=2, pcf_tmax=0.8, **L400),
}
sel = sys.argv[1:] or list(PROBES)
for nm in sel:
    F.ARMS[nm] = dict(state="pw", purge="G73", plat="", bases=("A1_none",), gex=PROBES[nm], late=True)
bay_z = F.engine_bay_mid()[0]
for nm in sel:
    p = os.path.join(OUTV, f"rf_A1_none_{nm.replace('|', '_')}.csv")
    t0 = time.time()
    rows = F.fly_arm("A1_none", nm, bay_z)
    F.M.write_csv(p, rows)
    r = F.rows_csv(p)
    ok = F.col(r, "ok") > 0.5
    rel = F.col(r, "pcf_rel")
    relt = F.col(r, "pcf_relt")
    fmx = F.col(r, "pcf_Facc_max")
    abt = F.col(r, "pcf_abt") > 0.5
    print(f"{nm:22s}: P {ok.mean():.3f} | released interim {int(np.sum(rel == 1))} accel {int(np.sum(rel == 2))} | aborted {int(abt.sum())} | "
          f"release after light ms p50/max {np.percentile(1e3 * relt[relt >= 0], 50) if np.any(relt >= 0) else float('nan'):.0f}/"
          f"{1e3 * relt.max() if np.any(relt >= 0) else float('nan'):.0f} | Facc_max p50/max {np.median(fmx):.2f}/{fmx.max():.2f} N | "
          f"td_vz p50 {np.median(F.col(r, 'td_vz')):.2f} | exhausted {int(np.sum(F.col(r, 'exhausted') > 0.5))} ({time.time() - t0:.0f} s)", flush=True)

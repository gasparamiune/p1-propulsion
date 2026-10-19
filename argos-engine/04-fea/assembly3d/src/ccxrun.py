"""Run CalculiX under nice 15 with peak-memory monitoring (VmHWM from /proc/<pid>/status); kill by PID only if a cap is exceeded."""
import os, subprocess, time, json
from pathlib import Path

def run_ccx(job, wd, threads=2, mem_cap_gb=6.5, timeout_s=4 * 3600, log=None):
    wd = Path(wd)
    env = dict(os.environ, OMP_NUM_THREADS=str(threads), CCX_NPROC_EQUATION_SOLVER=str(threads), CCX_NPROC_STIFFNESS=str(threads),
               CCX_NPROC_RESULTS=str(threads))
    out = open(wd / f"{job}.log", "w")
    t0 = time.time()
    p = subprocess.Popen(["nice", "-n", "15", "ccx", "-i", job], cwd=str(wd), env=env, stdout=out, stderr=subprocess.STDOUT)
    peak, killed = 0, None
    while p.poll() is None:
        try:
            # nice spawns ccx via exec, so the PID is ccx itself
            for line in open(f"/proc/{p.pid}/status"):
                if line.startswith("VmHWM:"):
                    peak = max(peak, int(line.split()[1]))
        except FileNotFoundError:
            pass
        if peak > mem_cap_gb * 1024 * 1024:
            killed = f"memory cap {mem_cap_gb} GB exceeded"; p.kill(); break
        if time.time() - t0 > timeout_s:
            killed = "timeout"; p.kill(); break
        time.sleep(0.5)
    p.wait(); out.close()
    txt = (wd / f"{job}.log").read_text(errors="replace")
    res = {"job": job, "seconds": round(time.time() - t0, 1), "peak_rss_GB": round(peak / 1024 / 1024, 3), "returncode": p.returncode,
           "killed": killed, "errors": [l for l in txt.splitlines() if "*ERROR" in l][:10],
           "warnings": sorted(set(l.strip() for l in txt.splitlines() if "*WARNING" in l))[:10], "threads": threads}
    if log:
        with open(log, "a") as f:
            f.write(json.dumps(res) + "\n")
    return res

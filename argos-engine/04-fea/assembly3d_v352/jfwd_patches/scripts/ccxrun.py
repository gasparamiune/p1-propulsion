"""Run CalculiX with peak-memory monitoring; kill by PID only if the cap is exceeded.

Memory cap (2026-10-20, lead brief v3.5.2): RSS watch, not an address-space limit.  `prlimit --as` caps virtual address space, which
for ccx (SPOOLES / OpenMP thread stacks and reserved arenas) is well above the resident set, so it can abort a solve that would fit;
instead VmHWM (peak resident set) is read from /proc/<pid>/status every 0.5 s and the solver (own PID only) is killed at the cap
(FEA3D_MEMCAP GB, 8.0 in the v3.5.2 chains).  Before each solve the machine's ccx processes are listed (`pgrep -a ccx`, VmRSS of each):
the solve starts only when fewer than 2 ccx run machine-wide and their RSS + the expected peak (FEA3D_EXPECT_GB) <= 9 GB; otherwise it
waits (polling 30 s).  nice FEA3D_NICE (10), OMP_NUM_THREADS = CCX_NPROC_EQUATION_SOLVER = 2.
2026-10-20 03:2xZ: (a) at most ONE ccx of mine at a time (flock runs/.fea3d_ccx.lock + no other ccx with its cwd in my work tree);
(b) no new ccx while free disk < 2.0 GB floor + the run's expected output (lead 03:14Z).
2026-10-20, first edit 15:42:42Z (file mtime; lead 15:37Z (R6)(b)): the flat 2.4 GiB start gate of the chain E runs is REPLACED by a
per-run gate
    free >= 1.86 GiB (the 2.0 GB floor) + 1.25 x the run's predicted write still to come + 0.10 GiB.
2026-10-20 16:02:28Z (date -u; lead 15:55Z (2): the gate is applied to each run's peak write while it solves): the predicted write is the
run's transient peak 'peak_MB' in runs/disk_peak_E.json (raw deck + the whole frd before extraction + the solved files; MB = 1e6 B) less
what its run folder already holds (so the gate falls as the run's states land); a run with no peak prediction uses its 'solved_MB' in
runs/disk_pred_E.json.  Runs without either (J-FWD sub-models, new runs) keep the old rule (2.0 + FEA3D_EXPECT_DISK_GB, default 0.4).  A hold file runs/.fea3d_disk_hold (written by disk_cmp_E.py when a run comes in > 20 % over its prediction: "a run more than
20 % over its prediction stops further starts until I rule") stops every further start of mine until it is removed.  Each chain E solve
start is logged to runs/disk_alert_E.log: INFO with free / gate / margin, ALERT when the margin is below 0.10 GiB or the start is held.
The wait-log line keeps its legacy text 'disk free X GB (need Y)' (values in GiB) for the disk watch."""
import os, subprocess, time, json
from pathlib import Path


def ccx_procs():
    """Every ccx process on the machine: [(pid, cmdline, VmRSS kB)]."""
    out = subprocess.run(["pgrep", "-a", "ccx"], capture_output=True, text=True).stdout
    res = []
    for line in out.splitlines():
        pid, _, cmd = line.partition(" ")
        try:
            if open(f"/proc/{pid}/comm").read().strip() != "ccx":
                continue
            rss = 0
            for l in open(f"/proc/{pid}/status"):
                if l.startswith("VmRSS:"):
                    rss = int(l.split()[1])
            res.append((int(pid), cmd.strip(), rss))
        except (FileNotFoundError, ProcessLookupError, ValueError):
            pass
    return res


DISK_FLOOR_GB = 2.0      # lead 2026-10-20 03:14Z: no new ccx below 2.0 GB free on /


def disk_free_gb(path="/"):
    st = os.statvfs(path)
    return st.f_bavail * st.f_frsize / 1024 ** 3


GIB = 1024 ** 3
GATE_FLOOR_GIB, GATE_FACTOR, GATE_MARGIN_GIB = 1.86, 1.25, 0.10      # lead 15:37Z (R6)(b)
RUNS_DIR = Path("/home/claude/work/fea3d/runs")
PRED_FILE = RUNS_DIR / "disk_pred_E.json"
PEAK_FILE = RUNS_DIR / "disk_peak_E.json"
HOLD_FILE = RUNS_DIR / ".fea3d_disk_hold"
ALERT_LOG = RUNS_DIR / "disk_alert_E.log"


def _du_mb(p):
    t = 0
    for r, _, fs in os.walk(p):
        for f in fs:
            try:
                t += os.path.getsize(os.path.join(r, f))
            except OSError:
                pass
    return t / 1e6


def _chain_run(logf):
    """(run, state) when the wait log is runs/<run>/<state>/<job>.wait.log of my run tree (a chain E / F1 run), else (None, None)."""
    try:
        q = Path(logf).resolve()
        if q.parent.parent.parent == RUNS_DIR:
            return q.parent.parent.name, q.parent.name
    except (OSError, TypeError):
        pass
    return None, None


def disk_gate(logf=None):
    """(need_GiB, basis text, run, state).  Per-run gate (lead 15:37Z (R6)(b)) for runs with a prediction; the old rule otherwise."""
    run, state = _chain_run(logf) if logf else (None, None)
    pred, kind = None, None
    if run:
        for fp, key in ((PEAK_FILE, "peak_MB"), (PRED_FILE, "solved_MB")):
            try:
                pred = json.loads(fp.read_text())["runs"].get(run, {}).get(key)
            except (OSError, ValueError, KeyError):
                pred = None
            if pred is not None:
                kind = key
                break
    if pred is None:
        need = DISK_FLOOR_GB + float(os.environ.get("FEA3D_EXPECT_DISK_GB", "0.4"))
        return need, f"flat {DISK_FLOOR_GB} + FEA3D_EXPECT_DISK_GB (no prediction)", run, state
    held = _du_mb(RUNS_DIR / run)
    remaining = max(float(pred) - held, 0.0)
    need = GATE_FLOOR_GIB + GATE_FACTOR * remaining * 1e6 / GIB + GATE_MARGIN_GIB
    return need, (f"per-run {GATE_FLOOR_GIB} + {GATE_FACTOR} x {remaining:.1f} MB still to write ({kind} {float(pred):.1f}, held "
                  f"{held:.1f}) + {GATE_MARGIN_GIB}"), run, state


def _alert(line):
    try:
        with open(ALERT_LOG, "a") as f:
            f.write(line + "\n")
    except OSError:
        pass


def wait_for_slot(expect_gb, limit_gb=9.0, max_ccx=2, poll_s=30, logf=None):
    """Machine slot: fewer than max_ccx ccx machine-wide, their RSS + expected peak <= limit_gb, free disk >= the gate (disk_gate: per-run
    for chain E runs with a prediction, lead 15:37Z; else the 2.0 GB floor + FEA3D_EXPECT_DISK_GB) and no disk hold file."""
    t0, n = time.time(), 0
    held_logged = False
    while True:
        need_disk, basis, run, state = disk_gate(logf)
        procs = ccx_procs()
        other_gb = sum(r for _, _, r in procs) / 1048576.0
        free = disk_free_gb()
        hold = HOLD_FILE.exists()
        now = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        if len(procs) < max_ccx and other_gb + expect_gb <= limit_gb and free >= need_disk and not hold:
            if run:
                margin = free - need_disk
                _alert(f"{now} {'ALERT' if margin < GATE_MARGIN_GIB else 'INFO'} solve start {run}/{state}: free {free:.3f} GiB, gate "
                       f"{need_disk:.3f} GiB ({basis}), margin {margin:+.3f} GiB"
                       + ("  <- within 0.1 GiB of the gate (tell the lead)" if margin < GATE_MARGIN_GIB else ""))
            return {"other_ccx": [{"pid": p, "cmd": c, "rss_GB": round(r / 1048576.0, 3)} for p, c, r in procs],
                    "other_rss_GB": round(other_gb, 3), "expected_peak_GB": expect_gb, "limit_GB": limit_gb, "waited_s": round(time.time() - t0, 1),
                    "disk_free_GB": round(free, 3), "disk_needed_GB": round(need_disk, 3), "disk_gate_basis": basis}
        if run and not held_logged and (free < need_disk or hold):
            _alert(f"{now} ALERT start HELD {run}/{state}: free {free:.3f} GiB, gate {need_disk:.3f} GiB ({basis})"
                   + (f"; disk hold file present: {HOLD_FILE.read_text().strip()[:200]}" if hold else "") + " (tell the lead)")
            held_logged = True
        if logf and n % 10 == 0:
            with open(logf, "a") as f:
                f.write(f"{now} waiting for a ccx slot: {len(procs)} ccx, RSS {other_gb:.2f} GB + expected {expect_gb} GB; disk free {free:.2f} GB "
                        f"(need {need_disk:.2f}) [GiB; {basis}]" + (" HOLD FILE" if hold else "") + "\n")
        n += 1
        time.sleep(poll_s)


MINE = "/home/claude/work/fea3d"
LOCK = Path(MINE) / "runs" / ".fea3d_ccx.lock"


def my_ccx():
    """ccx processes started from my work tree (cwd under /home/claude/work/fea3d)."""
    out = []
    for pid, cmd, rss in ccx_procs():
        try:
            if os.readlink(f"/proc/{pid}/cwd").startswith(MINE):
                out.append(pid)
        except OSError:
            pass
    return out


PRIORITY = Path(MINE) / "runs" / ".fea3d_priority"   # 2026-10-20 04:28Z: a token here (<= 3 h old) reserves my slot for that job family


def _deferred():
    """True when a priority token is set (file <= 3 h old) and this process does not carry it (FEA3D_PRIORITY_TOKEN)."""
    try:
        if time.time() - PRIORITY.stat().st_mtime > 3 * 3600:
            return False
        tok = PRIORITY.read_text().strip()
    except OSError:
        return False
    return bool(tok) and tok != os.environ.get("FEA3D_PRIORITY_TOKEN", "")


def own_slot(logf=None, poll_s=None):
    """2026-10-20: at most ONE ccx of mine machine-wide (chains and sub-model scripts alike): exclusive flock on runs/.fea3d_ccx.lock,
    held until the solve ends, and no other ccx running from my work tree.  Returns the open lock file (closing it releases the lock).
    04:28Z: poll interval FEA3D_SLOT_POLL (default 15 s); a process without the current priority token defers to the token holder."""
    import fcntl
    poll_s = float(os.environ.get("FEA3D_SLOT_POLL", "15")) if poll_s is None else poll_s
    fh = open(LOCK, "a+")
    t0, n = time.time(), 0
    while True:
        try:
            if not _deferred():
                fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                if not my_ccx():
                    return fh, round(time.time() - t0, 1)
                fcntl.flock(fh, fcntl.LOCK_UN)
        except BlockingIOError:
            pass
        if logf and n % 20 == 0:
            with open(logf, "a") as f:
                f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} waiting for my own ccx slot (lock / running: {my_ccx()})\n")
        n += 1
        time.sleep(poll_s)


def run_ccx(job, wd, threads=2, mem_cap_gb=6.5, timeout_s=4 * 3600, log=None):
    wd = Path(wd)
    threads = min(int(threads), 2)
    nice = os.environ.get("FEA3D_NICE", "10")
    expect = float(os.environ.get("FEA3D_EXPECT_GB", str(mem_cap_gb)))
    lock_fh, own_wait = own_slot(logf=wd / f"{job}.wait.log")
    pre = wait_for_slot(min(expect, mem_cap_gb), logf=wd / f"{job}.wait.log")
    pre["own_slot_wait_s"] = own_wait
    env = dict(os.environ, OMP_NUM_THREADS=str(threads), CCX_NPROC_EQUATION_SOLVER=str(threads), CCX_NPROC_STIFFNESS=str(threads),
               CCX_NPROC_RESULTS=str(threads))
    out = open(wd / f"{job}.log", "w")
    t0 = time.time()
    p = subprocess.Popen(["nice", "-n", nice, "ccx", "-i", job], cwd=str(wd), env=env, stdout=out, stderr=subprocess.STDOUT)
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
            killed = f"memory cap {mem_cap_gb} GB exceeded (VmHWM watch)"; p.kill(); break
        if time.time() - t0 > timeout_s:
            killed = "timeout"; p.kill(); break
        time.sleep(0.5)
    p.wait(); out.close()
    lock_fh.close()
    txt = (wd / f"{job}.log").read_text(errors="replace")
    res = {"job": job, "pid": p.pid, "seconds": round(time.time() - t0, 1), "peak_rss_GB": round(peak / 1024 / 1024, 3), "returncode": p.returncode,
           "killed": killed, "errors": [l for l in txt.splitlines() if "*ERROR" in l][:10],
           "warnings": sorted(set(l.strip() for l in txt.splitlines() if "*WARNING" in l))[:10], "threads": threads, "nice": int(nice),
           "mem_cap_GB": mem_cap_gb, "cap_method": "VmHWM (peak RSS) watch, 0.5 s, kill own PID at the cap", "pre_solve_check": pre,
           "start_utc": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(t0))}
    if log:
        with open(log, "a") as f:
            f.write(json.dumps(res) + "\n")
    return res

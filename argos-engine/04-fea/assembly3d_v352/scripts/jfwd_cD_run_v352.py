"""cD runner (FEA3D-2, 2026-10-21; lead 2026-10-21T02:01:34Z (C): "Run folder in /dev/shm: option (b), APPROVED as a runner change for cD
only ... prlimit --as 8 GB, nice 19, 2 threads, and it starts only after js5b's post is done (one ccx of yours)").
Same as jfwd_deck.run -> ccxrun.run_ccx (own slot: flock runs/.fea3d_ccx.lock; machine slot: < 2 ccx machine-wide, other ccx RSS +
expected <= 9 GB, the per-run disk gate from runs/disk_peak_jfwd.json, no hold file; VmHWM watch with own-PID kill at the cap), except:
  - ccx runs in the RAM folder /dev/shm/fea3d2_cD/runs/<job> (its cwd: the deck and every ccx output live there); the disk run folder
    jfwd/runs/<job> keeps meta.json, the wait log, ccx_run.json and DONE, and the symlinks <job>.inp / <job>.frd into the RAM folder
    (the posts read the frd there);
  - the command is prlimit --as=8 GiB nice -n 19 ccx -i <job> (prlimit and nice exec, so the PID is ccx itself);
  - 'run <job>' and 'end <job> rc=' lines go to runs/jfwdA.log as in the tail stages.
usage: jfwd_cD_run_v352.py JOB expect=GB cap=8.0 timeout_h=4.0"""
import sys, os, json, time, subprocess, hashlib
from pathlib import Path

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import ccxrun  # noqa: E402

W = Path("/home/claude/work/fea3d")
RAM_ROOT = Path("/dev/shm/fea3d2_cD/runs")
AS_BYTES = 8 * 1024 ** 3
NICE = 19
THREADS = 2


def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()[:16]


def jlog(s):
    with open(W / "runs" / "jfwdA.log", "a") as f:
        f.write(s + "\n")


def main(job, expect, cap, timeout_h):
    disk = W / "jfwd" / "runs" / job
    ram = RAM_ROOT / job
    meta = json.loads((disk / "meta.json").read_text())
    inp = ram / f"{job}.inp"
    assert inp.is_file() and not inp.is_symlink(), inp
    assert (disk / f"{job}.inp").is_symlink() and (disk / f"{job}.inp").resolve() == inp.resolve(), "disk .inp symlink"
    assert (disk / f"{job}.frd").is_symlink() and (disk / f"{job}.frd").resolve() == (ram / f"{job}.frd").resolve(), "disk .frd symlink"
    d = sha16(inp)
    assert d == meta["deck_sha16"], ("deck sha", d, meta["deck_sha16"])
    os.environ["FEA3D_EXPECT_GB"] = str(expect)
    now = lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())  # noqa: E731
    st = os.statvfs("/")
    jlog(f"{now()} run {job} expect={expect} cap={cap} timeout_h={timeout_h} post=seat (cD runner: RAM folder {ram}; prlimit --as {AS_BYTES}, "
         f"nice {NICE}, {THREADS} threads; df {st.f_bavail * st.f_frsize // 2 ** 20}M; ccx: {';'.join(c for _, c, _ in ccxrun.ccx_procs())})")
    logf = disk / f"{job}.wait.log"
    lock_fh, own_wait = ccxrun.own_slot(logf=logf)
    pre = ccxrun.wait_for_slot(min(expect, cap), logf=logf)
    pre["own_slot_wait_s"] = own_wait
    env = dict(os.environ, OMP_NUM_THREADS=str(THREADS), CCX_NPROC_EQUATION_SOLVER=str(THREADS), CCX_NPROC_STIFFNESS=str(THREADS),
               CCX_NPROC_RESULTS=str(THREADS))
    out = open(ram / f"{job}.log", "w")
    t0 = time.time()
    p = subprocess.Popen(["prlimit", f"--as={AS_BYTES}", "nice", "-n", str(NICE), "ccx", "-i", job], cwd=str(ram), env=env, stdout=out,
                         stderr=subprocess.STDOUT)
    jlog(f"{now()} cD {job}: solve started (pid {p.pid}, cwd {ram})")
    peak, killed = 0, None
    while p.poll() is None:
        try:
            for line in open(f"/proc/{p.pid}/status"):
                if line.startswith("VmHWM:"):
                    peak = max(peak, int(line.split()[1]))
        except FileNotFoundError:
            pass
        if peak > cap * 1024 * 1024:
            killed = f"memory cap {cap} GB exceeded (VmHWM watch)"
            p.kill()
            break
        if time.time() - t0 > timeout_h * 3600:
            killed = "timeout"
            p.kill()
            break
        time.sleep(0.5)
    p.wait()
    out.close()
    lock_fh.close()
    txt = (ram / f"{job}.log").read_text(errors="replace")
    res = {"job": job, "pid": p.pid, "seconds": round(time.time() - t0, 1), "peak_rss_GB": round(peak / 1024 / 1024, 3), "returncode": p.returncode,
           "killed": killed, "errors": [ln for ln in txt.splitlines() if "*ERROR" in ln][:10],
           "warnings": sorted(set(ln.strip() for ln in txt.splitlines() if "*WARNING" in ln))[:10], "threads": THREADS, "nice": NICE,
           "mem_cap_GB": cap, "cap_method": "VmHWM (peak RSS) watch, 0.5 s, kill own PID at the cap; plus prlimit --as 8 GiB",
           "prlimit_as_bytes": AS_BYTES, "run_folder_ram": str(ram), "deck_sha16": d, "pre_solve_check": pre,
           "runner": "scripts/jfwd_cD_run_v352.py (lead 2026-10-21T02:01:34Z (C): /dev/shm run folder, cD only)",
           "start_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0))}
    (disk / "ccx_run.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps({k: res.get(k) for k in ("job", "seconds", "peak_rss_GB", "returncode", "killed", "errors")}, default=str), flush=True)
    jlog(f"{now()} end {job} rc={p.returncode}")
    return 0 if p.returncode == 0 and not killed else 1


if __name__ == "__main__":
    kw = dict(a.split("=", 1) for a in sys.argv[2:])
    sys.exit(main(sys.argv[1], float(kw.get("expect", 7.4)), float(kw.get("cap", 8.0)), float(kw.get("timeout_h", 4.0))))

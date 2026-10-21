"""cD watch (FEA3D-2, 2026-10-21; lead 2026-10-21T02:01:34Z (C): "Track its RAM in the WATCH lines").  Read-only except its lines in
runs/tail_F.log and, on the 20 % rule, the hold file runs/.fea3d_disk_hold.  Every 10 s: the cD ccx (cwd in the RAM folder), its VmRSS /
VmHWM, the RAM folder size, MemAvailable, /dev/shm use, free disk on / and the disk run folder size (symlinks not followed).
  WATCH  at the start, then every 30 min: free disk, disk folder vs predicted 44 MB, RAM folder vs predicted 190 MB, ccx RSS / HWM vs the
         estimate 6.73 GiB (cap 8.0), MemAvailable, /dev/shm used;
  ALERT  RAM folder > 1.2 x 190 MB or disk folder > 1.2 x 44 MB (hold file written: no further start of mine until the lead rules);
         HWM > 7.41 GiB (above the estimate with its 10 %); MemAvailable < 1.5 GiB; free disk < 2.0 GiB;
  PEAK   once the stage prints '<job> stage end' (or 'stage stops'): largest RAM / disk folder, peak HWM, lowest free / MemAvailable.
usage: watch_cD_v352.py JOB   (background, nice 19; ends after PEAK, or after 6 h)"""
import os, sys, time, subprocess
from pathlib import Path

W = Path("/home/claude/work/fea3d")
LOG = W / "runs" / "tail_F.log"
HOLD = W / "runs" / ".fea3d_disk_hold"
GIB = 1024 ** 3
PRED_RAM_MB, PRED_DISK_MB, RSS_EST, RSS_10, CAP = 190.0, 44.0, 6.73, 7.41, 8.0


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def say(s):
    with open(LOG, "a") as f:
        f.write(f"{now()} {s}\n")


def du_mb(p, follow=False):
    t = 0
    for r, _, fs in os.walk(p):
        for f in fs:
            q = os.path.join(r, f)
            try:
                t += os.path.getsize(q) if follow else os.lstat(q).st_size
            except OSError:
                pass
    return t / 1e6


def meminfo():
    m = {}
    for ln in open("/proc/meminfo"):
        k, v = ln.split(":", 1)
        m[k] = int(v.split()[0])
    return m


def shm_used_mb():
    st = os.statvfs("/dev/shm")
    return (st.f_blocks - st.f_bfree) * st.f_frsize / 1e6


def ccx_of(ram):
    for pid in subprocess.run(["pgrep", "-x", "ccx"], capture_output=True, text=True).stdout.split():
        try:
            if os.readlink(f"/proc/{pid}/cwd") == str(ram):
                st = {ln.split(":")[0]: int(ln.split()[1]) for ln in open(f"/proc/{pid}/status") if ln.startswith(("VmRSS", "VmHWM"))}
                return int(pid), st.get("VmRSS", 0) / 1048576.0, st.get("VmHWM", 0) / 1048576.0
        except (OSError, ValueError, IndexError):
            continue
    return None, 0.0, 0.0


def main(job):
    ram = Path("/dev/shm/fea3d2_cD/runs") / job
    disk = W / "jfwd" / "runs" / job
    t0 = time.time()
    s = {"ram_max": 0.0, "disk_max": 0.0, "hwm": 0.0, "free_min": 9e9, "mem_min": 9e9, "alerts": set(), "last": 0.0, "seen": False}
    say(f"WATCH {job}: cD watch start (RAM folder {ram}, disk folder {disk})")
    while time.time() - t0 < 6 * 3600:
        txt = LOG.read_text(errors="ignore")
        st = os.statvfs("/")
        free = st.f_bavail * st.f_frsize / GIB
        mem = meminfo()["MemAvailable"] / 1048576.0
        dr = du_mb(ram) if ram.exists() else 0.0
        dd = du_mb(disk) if disk.exists() else 0.0
        pid, rss, hwm = ccx_of(ram)
        if pid:
            s["seen"] = True
        s["ram_max"], s["disk_max"], s["hwm"] = max(s["ram_max"], dr), max(s["disk_max"], dd), max(s["hwm"], hwm)
        s["free_min"], s["mem_min"] = min(s["free_min"], free), min(s["mem_min"], mem)
        line = (f"free {free:.3f} GiB, disk folder {dd:.1f} MB of predicted {PRED_DISK_MB} MB, RAM folder {dr:.1f} MB (largest {s['ram_max']:.1f}) "
                f"of predicted {PRED_RAM_MB} MB, ccx " + (f"pid {pid} RSS {rss:.2f} GiB (HWM {hwm:.2f}; estimate {RSS_EST}, cap {CAP})" if pid else "not running")
                + f", MemAvailable {mem:.2f} GiB, /dev/shm used {shm_used_mb():.1f} MB")
        if time.time() - s["last"] >= 1800:
            s["last"] = time.time()
            say(f"WATCH {job}: {line}")
        checks = ((dr > 1.2 * PRED_RAM_MB, "ram20", f"RAM folder {dr:.1f} MB > 1.2 x predicted {PRED_RAM_MB} MB", True),
                  (dd > 1.2 * PRED_DISK_MB, "disk20", f"disk folder {dd:.1f} MB > 1.2 x predicted {PRED_DISK_MB} MB", True),
                  (hwm > RSS_10, "hwm", f"ccx HWM {hwm:.2f} GiB > {RSS_10} GiB (the estimate with its 10 %; cap {CAP})", False),
                  (mem < 1.5, "mem", f"MemAvailable {mem:.2f} GiB < 1.5 GiB", False),
                  (free < 2.0, "free", f"free disk {free:.3f} GiB < 2.0 GiB", False))
        for cond, key, msg, hold in checks:
            if cond and key not in s["alerts"]:
                s["alerts"].add(key)
                if hold:
                    try:
                        HOLD.write_text(f"{now()} watch_cD_v352 {job}: {msg} (lead 15:37Z: no further start until the lead rules)\n")
                    except OSError:
                        pass
                say(f"ALERT {job}: {msg}" + ("; hold file written" if hold else "") + " (tell the lead)")
        if f"{job} stage end" in txt or f"cD {job}: stage stops" in txt:
            say(f"PEAK {job}: largest RAM folder {s['ram_max']:.1f} MB vs predicted {PRED_RAM_MB} MB ({(s['ram_max'] / PRED_RAM_MB - 1) * 100:+.0f} %); "
                f"disk folder {dd:.1f} MB (largest {s['disk_max']:.1f}) vs predicted {PRED_DISK_MB} MB ({(s['disk_max'] / PRED_DISK_MB - 1) * 100:+.0f} %); "
                f"ccx HWM {s['hwm']:.2f} GiB vs estimate {RSS_EST} ({(s['hwm'] / RSS_EST - 1) * 100:+.0f} %); lowest free {s['free_min']:.3f} GiB; "
                f"lowest MemAvailable {s['mem_min']:.2f} GiB")
            return
        time.sleep(10)
    say(f"WATCH {job}: cD watch end after 6 h without a stage end (tell the lead)")


if __name__ == "__main__":
    main(sys.argv[1])

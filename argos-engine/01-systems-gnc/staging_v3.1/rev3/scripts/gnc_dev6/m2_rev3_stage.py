"""m2_rev3_stage v1.2 (GNC rev3, 2026-10-13; v1.2: the lead freed the disk (coordinator message: about 1.9 GB, 200 MB hold rule
kept), so the rg16w frame streams and the bit-check .npz streams are staged under streams/ again, and the 285 m duty-cycle
record is staged under duty_cycles/; NOT_STAGED_rev3.txt now lists only the temporary scratch of the v2.9 suite. v1.1: the
rg16w frame streams were listed in NOT_STAGED_rev3.txt instead of copied, disk): copies the rev3 evidence into the hub folder
01-systems-gnc/staging_v3.1/rev3/ and writes MANIFEST_rev3.sha256 (sha256 + relative path of every staged file, sorted).

Writes only under staging_v3.1/rev3/ (never rev1 / rev2 / rev2p1 / rev2p2, never interfaces/gnc.json). Files are copied
byte for byte (shutil.copyfile); the tables are the gzip -n copies already in the work area (meta/*.json table_sha16 = the
uncompressed CSV as flown; the evaluations were re-run on the .gz files, references only changed). A free-space check refuses
to copy below 200 MB after the copy (lead hold rule). Every action is printed (log: out/rev3/rev3_stage.log, outside logs/ so that the log being written is not itself staged).
Usage: python m2_rev3_stage.py [--dry]"""
import glob
import hashlib
import os
import shutil
import sys

SP = "/home/claude/work/space"
OUT = f"{SP}/out/rev3"
DEST = "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/rev3"
DRY = "--dry" in sys.argv


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def plan():
    m = []

    def add(src, rel):
        if os.path.isfile(src):
            m.append((src, rel))
        else:
            print("ABSENT (not staged):", src)

    add(f"{OUT}/rev3_results.json", "results/rev3_results.json")
    for p in ("rev3_fly.json", "p6_late_commit_v1p1.json", "p6_late_commit.json", "reserve_dip.json", "r2v2_eval.json", "hold_trace.json"):
        add(f"{OUT}/fly/{p}", f"results/eval/{p}")
    add(f"{OUT}/p5/p5_latency.json", "results/eval/p5_latency.json")
    add(f"{OUT}/rg16w/rg16w.json", "results/eval/rg16w.json")
    add(f"{OUT}/mass_v35/mass_v35_vs_v3d.json", "results/eval/mass_v35_vs_v3d.json")
    for d in ("bitcheck_v210", "bitcheck_v211", "bitcheck_v212", "bitcheck_v29_rev3"):
        for p in sorted(glob.glob(f"{OUT}/{d}/*.json")):
            add(p, f"results/{d}/{os.path.basename(p)}")
    for p in sorted(glob.glob(f"{OUT}/fly/rf_*.csv.gz")):
        add(p, f"tables/fly/{os.path.basename(p)}")
    for p in sorted(glob.glob(f"{OUT}/fly/meta/*.json")):
        add(p, f"tables/fly/meta/{os.path.basename(p)}")
    for p in sorted(glob.glob(f"{OUT}/p5/*.csv.gz")):
        add(p, f"tables/p5/{os.path.basename(p)}")
    for p in sorted(glob.glob(f"{OUT}/dc_record_285/*")):
        add(p, f"duty_cycles/{os.path.basename(p)}")
    for p in sorted(glob.glob(f"{OUT}/rg16w/*.npz") + glob.glob(f"{OUT}/bitcheck_v21*/*.npz")):
        add(p, f"streams/{os.path.basename(os.path.dirname(p))}/{os.path.basename(p)}")
    scripts = {
        "gnc_dev3": ("m2_rev3_fly.py", "m2r3_env.sh", "m2_mass_v35.py", "m2_rev3_dc_record.py"),
        "gnc_dev4": ("m2_rev3_fly.py", "m2_rev3_r2v2_eval.py", "m2_rev3_p6.py", "patch_sim6_v210.py", "patch_run6_v210.py",
                     "m2_bitcheck_v210.py", "run_bitcheck_v210.sh", "run_rev3_queue.sh", "run_rev3_queue2.sh", "run_rev3_queue3b.sh",
                     "run_rev3_queue3c.sh"),
        "gnc_dev5": ("m2_rev3_p5.py", "m2_rev3_rg16w.py", "patch_sim6_v211.py", "patch_run6_v211.py", "m2_bitcheck_v211.py",
                     "run_bitcheck_v211.sh", "run_rev3_queue3.sh"),
        "gnc_dev6": ("m2_rev3_fly.py", "m2_rev3_p6.py", "m2_rev3_reserve_dip.py", "m2_rev3_hold_trace.py", "patch_sim6_v212.py",
                     "patch_run6_v212.py", "m2_bitcheck_v212.py", "run_bitcheck_v212.sh", "m2_bitcheck_v29.py", "run_rev3_queue4.sh",
                     "run_rev3_queue4b.sh", "run_rev3_queue5.sh", "m2_rev3_results.py", "m2_rev3_stage.py"),
    }
    for t, names in scripts.items():
        for n in names:
            add(f"{SP}/{t}/scripts/{n}", f"scripts/{t}/{n}")
    for p in sorted(glob.glob(f"{SP}/rev3_notes/*.py")):
        add(p, f"scripts/notes/{os.path.basename(p)}")
    add(f"{OUT}/logs/m2_rev3_fly_v1.0_snapshot.py", "scripts/notes/m2_rev3_fly_v1.0_snapshot.py")
    for p in sorted(glob.glob(f"{SP}/pins_rev3/*.sha256")):
        add(p, f"pins/{os.path.basename(p)}")
    for p in sorted(glob.glob(f"{SP}/gnc_dev6/gncsim/*.py")):
        add(p, f"sim/gncsim_v2.12-dev/{os.path.basename(p)}")
    for p in sorted(glob.glob(f"{SP}/iface_v35a/*")):
        add(p, f"sim/iface_v35a/{os.path.basename(p)}")
    for p in sorted(glob.glob(f"{OUT}/logs/*.log")):
        add(p, f"logs/{os.path.basename(p)}")
    return m


def main():
    m = plan()
    ns = sorted(p for p in glob.glob(f"{SP}/scratch_bit29_rev3/**/*", recursive=True) if os.path.isfile(p))
    tot0 = sum(os.path.getsize(s) for s, _ in m)
    free = shutil.disk_usage(os.path.dirname(DEST)).free
    print(f"free {free / 1e6:.0f} MB before, {(free - tot0) / 1e6:.0f} MB after the copy")
    if free - tot0 < 200e6:
        raise SystemExit("HOLD: less than 200 MB would remain free after staging (lead hold rule); nothing copied")
    if not DRY:
        os.makedirs(DEST, exist_ok=True)
        with open(os.path.join(DEST, "NOT_STAGED_rev3.txt"), "w") as f:
            f.write("# GNC rev3: work-area files NOT copied to the hub. Only the temporary scratch of the v2.9 suite (job pickles and the\n"
                    "# scratch copy of the rev1 simulator, regenerated by m2_bitcheck_v29 on every run); every result, table, stream,\n"
                    "# script and log of rev3 is staged. sha256  size_bytes  path\n")
            for p in ns:
                f.write(f"{sha(p)}  {os.path.getsize(p)}  {p}\n")
    rels = [r for _, r in m]
    assert len(rels) == len(set(rels)), "duplicate destination paths"
    tot = sum(os.path.getsize(s) for s, _ in m)
    print(f"{len(m)} files, {tot / 1e6:.1f} MB -> {DEST}{' (dry run)' if DRY else ''}")
    if DRY:
        return
    for s, r in m:
        d = os.path.join(DEST, r)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copyfile(s, d)
        if sha(s) != sha(d):
            raise RuntimeError(f"copy mismatch {s} -> {d}")
    lines = []
    for root, _, fs in os.walk(DEST):
        for f in fs:
            p = os.path.join(root, f)
            rel = os.path.relpath(p, DEST)
            if rel == "MANIFEST_rev3.sha256":
                continue
            lines.append(f"{sha(p)}  {rel}")
    lines.sort(key=lambda x: x.split("  ", 1)[1])
    mp = os.path.join(DEST, "MANIFEST_rev3.sha256")
    with open(mp, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("wrote", mp, sha(mp)[:16], "entries", len(lines))


if __name__ == "__main__":
    main()

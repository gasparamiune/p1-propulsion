"""m2_stage_hub_rev1 v1.2 (GNC, 2026-10-13): stage the GNC response to REV-GNC-1 (rev1 set) into the hub, in the GNC subfolder
01-systems-gnc/staging_v3.1/rev1/ only (gnc.json v3, REPORT-v3 and the lead's staging reports are not touched).

Copies (atomic: write to a temporary name in the target folder, fsync, os.replace):
  sim/gncsim_v2.8-dev_MWFPRS/  every .py of the dev simulator package (sim6 v2.8-dev amendments M, W, F, P, R, S)
  sim/patches/                 the amendment scripts F, P, R, the amendment S diffs and the pre-merge / pre-R / pre-S
                               simulator backups (traceability)
  scripts/                     every m2_*.py of the dev tree (all code, as run)
  results/<name>/              curated JSON results; Monte Carlo CSVs gzip-compressed (*.csv.gz)
  REPORT-GNC-REV1.md           the rev1 report (checkpoint + revision response)
  MANIFEST_rev1.sha256         sha256 of every staged file (relative paths)
Then re-reads every staged file after GNC_STAGE_WAIT s (default 10) and compares it with the manifest; exits non-zero on any
difference. Temporary files are removed on failure.
Env: GNC_STAGE_DST (default the hub rev1 folder), GNC_STAGE_WAIT, GNC_STAGE_REPORT (path of the report to stage).
v1.1: GNC_STAGE_ONLY (comma list of RESULTS names): stage only those results (no sim, scripts or report), each with its own
results/<name>/MANIFEST.sha256 and the same read-back; the full staging (no filter) rewrites MANIFEST_rev1.sha256 with every
file. RESULTS add relight_attitude, rg16_terms and the eng07_6v6 v1.1 eval.
v1.2: sim folder MWFPRS (amendment S), patches *.diff staged, RESULTS add start_transient and v28_checks_v15 (bitcheck v1.5)."""
import glob
import gzip
import hashlib
import os
import shutil
import sys
import time

SPACE = "/home/claude/work/space"
DEV = f"{SPACE}/gnc_dev28"
OUTR = f"{SPACE}/out"
DST = os.environ.get("GNC_STAGE_DST", "/home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/rev1")
WAIT = float(os.environ.get("GNC_STAGE_WAIT", "10"))
REPORT = os.environ.get("GNC_STAGE_REPORT", f"{SPACE}/report/REPORT-GNC-REV1.md")
VERSION = "m2_stage_hub_rev1 v1.2"

# curated results: (source folder under out/, files (globs), gzip the CSVs)
RESULTS = {
    "fault_f": (["fault_f.json", "fault_*.csv"], True),
    "purge_bleed": (["purge_bleed.json", "pb_*.csv"], True),
    "rg07": (["rg07_b1_eng07d.json", "rg07_*.csv"], True),
    "cap_rule": (["cap_rule.json", "cap_grid.json", "cap_kscan.json", "cond_*.csv"], True),
    "release_rule": (["release_rule.json", "rel_*.csv"], True),
    "fsw_record": (["fsw_config_record_v1.json"], False),
    "v28_checks_v13": (["bitcheck_v28.json"], False),
    "v28_checks_v14": (["bitcheck_v28.json"], False),
    "v28_checks_v15": (["bitcheck_v28.json"], False),
    "start_transient": (["start_transient.json", "st_*.csv"], True),
    "web_limit": (["web_limit.json", "web_check.json", "web_*.csv", "records/*"], True),
    "gust_criterion": (["gust_criterion.json", "gust_classify.json", "gust_*.csv"], True),
    "eng07_6v6": (["eng07_6v6.json", "identity_check.json", "mc6_runs_*.csv"], True),
    "mass_est_v2": (["mass_est_v2.json", "fct_mest_v2.json", "mest_budget_v1.json"], False),
    "khat_offset": (["khat_offset.json"], False),
    "rg02": (["rg02_accounting_v1.json"], False),
    "relight_attitude": (["relight_attitude_v1.json", "identity_check.json", "ra_runs_*.csv"], True),
    "rg16_terms": (["rg16_fct_terms.json"], False),
    "gnc_json/rebuild_v3_check": (["rebuild_check_v1.json"], False),
}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def atomic_write_bytes(dst, data):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    tmp = dst + ".tmp_stage"
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, dst)


def atomic_copy(src, dst, gz=False):
    with open(src, "rb") as f:
        data = f.read()
    if gz:
        data = gzip.compress(data, compresslevel=9, mtime=0)
    atomic_write_bytes(dst, data)


def plan():
    jobs = []
    for p in sorted(glob.glob(f"{DEV}/gncsim/*.py")):
        jobs.append((p, f"sim/gncsim_v2.8-dev_MWFPRS/{os.path.basename(p)}", False))
    for p in sorted(glob.glob(f"{SPACE}/patches/*.py") + glob.glob(f"{SPACE}/patches/*.diff")):
        jobs.append((p, f"sim/patches/{os.path.basename(p)}", False))
    for p in sorted(glob.glob(f"{DEV}/scripts/m2_*.py")):
        jobs.append((p, f"scripts/{os.path.basename(p)}", False))
    for name, (pats, gzcsv) in RESULTS.items():
        src_dir = f"{OUTR}/{name}"
        for pat in pats:
            for p in sorted(glob.glob(os.path.join(src_dir, pat))):
                if not os.path.isfile(p):
                    continue
                rel = os.path.relpath(p, src_dir)
                gz = gzcsv and p.endswith(".csv")
                jobs.append((p, f"results/{name.replace('/', '_')}/{rel}" + (".gz" if gz else ""), gz))
    if os.path.isfile(REPORT):
        jobs.append((REPORT, "REPORT-GNC-REV1.md", False))
    return jobs


ONLY = [x for x in os.environ.get("GNC_STAGE_ONLY", "").split(",") if x]


def main_only():
    man = {}
    try:
        for name in ONLY:
            pats, gzcsv = RESULTS[name]
            src_dir = f"{OUTR}/{name}"
            sub = {}
            for pat in pats:
                for p in sorted(glob.glob(os.path.join(src_dir, pat))):
                    if not os.path.isfile(p):
                        continue
                    gz = gzcsv and p.endswith(".csv")
                    rel = f"results/{name.replace('/', '_')}/{os.path.relpath(p, src_dir)}" + (".gz" if gz else "")
                    atomic_copy(p, os.path.join(DST, rel), gz)
                    sub[rel] = sha(os.path.join(DST, rel))
            mrel = f"results/{name.replace('/', '_')}/MANIFEST.sha256"
            atomic_write_bytes(os.path.join(DST, mrel), ("# " + VERSION + " " + time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                                                         + "\n" + "\n".join(f"{h}  {r}" for r, h in sorted(sub.items())) + "\n").encode())
            man.update(sub)
            man[mrel] = sha(os.path.join(DST, mrel))
    finally:
        for t in glob.glob(os.path.join(DST, "**", "*.tmp_stage"), recursive=True):
            os.remove(t)
    print(f"staged {len(man)} files ({','.join(ONLY)}) into {DST}; waiting {WAIT:.0f} s before the read-back", flush=True)
    time.sleep(WAIT)
    bad = [r for r, h in man.items() if sha(os.path.join(DST, r)) != h]
    print("read-back:", "OK" if not bad else f"MISMATCH {bad[:10]}", flush=True)
    for r, h in sorted(man.items()):
        print(f"  {h[:16]}  {r}")
    sys.exit(1 if bad else 0)


def main():
    if ONLY:
        return main_only()
    jobs = plan()
    os.makedirs(DST, exist_ok=True)
    man = {}
    try:
        for src, rel, gz in jobs:
            dst = os.path.join(DST, rel)
            atomic_copy(src, dst, gz)
            man[rel] = sha(dst)
        lines = [f"{h}  {r}" for r, h in sorted(man.items())]
        atomic_write_bytes(os.path.join(DST, "MANIFEST_rev1.sha256"),
                           ("# " + VERSION + " " + time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()) + "\n" + "\n".join(lines)
                            + "\n").encode())
    finally:
        for t in glob.glob(os.path.join(DST, "**", "*.tmp_stage"), recursive=True):
            os.remove(t)
    print(f"staged {len(man)} files into {DST}; waiting {WAIT:.0f} s before the read-back", flush=True)
    time.sleep(WAIT)
    bad = [r for r, h in man.items() if sha(os.path.join(DST, r)) != h]
    print("read-back:", "OK" if not bad else f"MISMATCH {bad[:10]}", flush=True)
    print("manifest sha256/16", sha(os.path.join(DST, "MANIFEST_rev1.sha256"))[:16], flush=True)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

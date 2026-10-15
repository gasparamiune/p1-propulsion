"""m2_stage_hub_v31 v1.1 (GNC, 2026-10-13): copy the v3.1 STAGING set into the hub folder 01-systems-gnc/staging_v3.1/.

v1.1: the fc_thrust section adds the mass-estimate sensitivity (m2_fc_thrust_mest v1: fc_thrust_mest.json, fc_thrust_mest_v1.png,
the script); the gnc_json section stages the v3.1 builder m2_gnc_json_v31.py (v1 listed the v3 builder by mistake). Files
staged by v1 are unchanged.

gnc.json v3, REPORT-v3.md and every v3 file stay untouched while the independent GNC review runs (lead 2026-10-13): this script
writes only below 01-systems-gnc/staging_v3.1/. Each file is copied atomically (temporary name + rename), a CSV declared 'gz' is
gzip-compressed (hub convention for Monte Carlo CSVs; mtime 0 so the archive is reproducible), nothing is deleted, and
MANIFEST_staging_v3.1.sha256 lists every staged file with its sha256 (of the staged bytes).
Sections (GNC_S31_SECTIONS, default all): combustion_data (A1 coast acceleration, B1 62 m records, T_tank check), fc_thrust,
gnc_json. A section whose sources are missing is reported and skipped.
Env: GNC_HUB (default /home/claude/work/shared-fallback/engine), GNC_STAGE_COPY (1 = copy; default 0 = dry run)."""
import gzip
import hashlib
import os
import shutil
import sys

VERSION = "m2_stage_hub_v31 v1.1"
HUB = os.environ.get("GNC_HUB", "/home/claude/work/shared-fallback/engine")
DEST = os.path.join(HUB, "01-systems-gnc", "staging_v3.1")
S = "/home/claude/work/space/out"
SC = "/home/claude/work/space/gnc_dev/scripts"
COPY = os.environ.get("GNC_STAGE_COPY", "0") == "1"
SECTIONS = {
    "combustion_data": [
        (f"{S}/coast_accel_a1/coast_accel_a1_v1.json", "results/a1_coast_accel/", None),
        (f"{S}/coast_accel_a1/coast_accel_a1_envelope_meco_v1.csv", "results/a1_coast_accel/", None),
        (f"{S}/coast_accel_a1/coast_accel_a1_envelope_relight_v1.csv", "results/a1_coast_accel/", None),
        (f"{S}/coast_accel_a1/coast_accel_a1_runs_v1.csv", "results/a1_coast_accel/", None),
        (f"{S}/coast_accel_a1/coast_accel_a1_series_v1.csv", "results/a1_coast_accel/", None),
        (f"{S}/coast_accel_a1/coast_accel_a1_v1.png", "results/a1_coast_accel/", None),
        (f"{S}/duty_cycles_v3_1/DC-B1_hop_62m_disp_p99_kest2_v3.csv", "duty_cycles/", None),
        (f"{S}/duty_cycles_v3_1/DC-B1_hop_62m_disp_max_kest2_v3.csv", "duty_cycles/", None),
        (f"{S}/duty_cycles_v3_1/DC-B1_hop_62m_disp_p99_kest2_tg711_v3.csv", "duty_cycles/", None),
        (f"{S}/duty_cycles_v3_1/DC-B1_hop_62m_disp_max_kest2_tg711_v3.csv", "duty_cycles/", None),
        (f"{S}/duty_cycles_v3_1/duty_cycles_records_b1_62m_v3.1.json", "duty_cycles/", None),
        (f"{S}/duty_cycles_v3_1/mc/mc6_runs_tgl_B1_lead62_none_k2.csv", "results/b1_62m_mc/", "gz"),
        (f"{S}/duty_cycles_v3_1/mc/case_tgl_B1_lead62_none_k2.json", "results/b1_62m_mc/", None),
        (f"{S}/ttank_arm_check/ttank_arm_check_v1.json", "results/ttank_arm_check/", None),
        (f"{SC}/m2_coast_accel_a1.py", "sim/scripts/", None),
        (f"{SC}/m2_coast_accel_plot.py", "sim/scripts/", None),
        (f"{SC}/m2_dc_b1_62m_record.py", "sim/scripts/", None),
        (f"{SC}/m2_ttank_arm_check.py", "sim/scripts/", None),
        (f"{SC}/m2_stage_hub_v31.py", "sim/scripts/", None),
    ],
    "fc_thrust": [
        (f"{S}/fc_thrust/fc_thrust.json", "results/fc_thrust/", None),
        (f"{S}/fc_thrust/fc_thrust_v1.1.png", "results/fc_thrust/", None),
        (f"{SC}/m2_fc_thrust.py", "sim/scripts/", None),
        (f"{SC}/m2_fc_thrust_plot.py", "sim/scripts/", None),
        (f"{S}/fc_thrust/fc_thrust_mest.json", "results/fc_thrust/", None),
        (f"{S}/fc_thrust/fc_thrust_mest_v1.png", "results/fc_thrust/", None),
        (f"{SC}/m2_fc_thrust_mest.py", "sim/scripts/", None),
    ],
    "gnc_json": [
        (f"{S}/gnc_json/gnc_v3.1_staging.json", "", None),
        (f"{SC}/m2_gnc_json_v31.py", "sim/scripts/", None),
        (f"{SC}/m2_stage_hub_v31.py", "sim/scripts/", None),
    ],
}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def stage(src, sub, mode):
    name = os.path.basename(src) + (".gz" if mode == "gz" else "")
    dst_dir = os.path.join(DEST, sub)
    dst = os.path.join(dst_dir, name)
    if not COPY:
        return dst, None
    os.makedirs(dst_dir, exist_ok=True)
    tmp = dst + ".gnc_tmp"
    if mode == "gz":
        with open(src, "rb") as fi, open(tmp, "wb") as fo:
            with gzip.GzipFile(filename=os.path.basename(src), mode="wb", fileobj=fo, mtime=0) as gz:
                shutil.copyfileobj(fi, gz)
    else:
        shutil.copyfile(src, tmp)
    os.replace(tmp, dst)
    return dst, sha(dst)


def main():
    sel = os.environ.get("GNC_S31_SECTIONS")
    secs = [s for s in SECTIONS if not sel or s in sel.split(",")]
    man_p = os.path.join(DEST, "MANIFEST_staging_v3.1.sha256")
    man = {}
    if os.path.exists(man_p):
        for line in open(man_p):
            if line.strip() and not line.startswith("#"):
                h, rel = line.rstrip("\n").split("  ", 1)
                man[rel] = h
    for s in secs:
        miss = [src for src, _, _ in SECTIONS[s] if not os.path.exists(src)]
        if miss:
            print(f"section {s}: SKIPPED, missing {miss}", flush=True)
            continue
        for src, sub, mode in SECTIONS[s]:
            dst, h = stage(src, sub, mode)
            rel = os.path.relpath(dst, DEST)
            print(f"{'staged' if COPY else 'would stage'} {rel}" + (f"  {h[:16]}" if h else ""), flush=True)
            if h:
                man[rel] = h
    if COPY:
        tmp = man_p + ".gnc_tmp"
        with open(tmp, "w") as f:
            f.write(f"# {VERSION}: sha256 of the staged bytes, path relative to 01-systems-gnc/staging_v3.1/\n")
            for rel in sorted(man):
                f.write(f"{man[rel]}  {rel}\n")
        os.replace(tmp, man_p)
        print("manifest", man_p, len(man), "files")


if __name__ == "__main__":
    sys.exit(main())

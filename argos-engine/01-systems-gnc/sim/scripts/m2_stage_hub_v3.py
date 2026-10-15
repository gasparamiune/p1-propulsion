"""m2_stage_hub_v3 v1.3 (GNC, 2026-10-13; v1.3: only hub scripts older than the v3 work (mtime before 2026-10-13T00:00Z, i.e.
published with gnc.json v2) go to history, and the files already in the hub history folder are staged unchanged; v1.2 also
filed two v3 scripts copied minutes earlier as history: removed from the hub, kept as evidence here; v1.2: a hub script that
the new staging would overwrite with different content is kept unchanged under sim/history/scripts_hub_v2/ (the gnc.json v2
scripts); v1.1: the two diagnostic figures gnc.json names under results/ctrlfix are staged
from the diagnostics folder (EXTRA), and the script check resolves each gnc.json "scripts" entry at its own path, wildcards
included; v1 compared basenames against sim/scripts only and reported the gncsim entries as missing): stage the GNC hub
folder 01-systems-gnc for gnc.json v3.

Builds a staging tree (GNC_STAGE, default /home/claude/work/space/stage_hub/01-systems-gnc) with
  sim/gncsim/      the current GNC simulation package (sim6/run6 v2.7.1-dev + tailoff + regband + the unchanged modules)
  sim/history/gncsim_hub_v2/   the gncsim files that the hub held before (published with gnc.json v2), kept unchanged
  sim/scripts/     every m2 script named in gnc.json v3 "scripts" plus the helpers they import
  sim/data/        tailoff fit, regression-band model, relay files
  results/<sub>/   curated results: every JSON summary of the studies gnc.json v3 cites, the Monte Carlo run tables gzipped
                   (csv.gz), the figures named in the file
  vehicle/         reference vehicle v3d files
and checks that every '01-systems-gnc/...' path written in gnc.json v3 exists in the staging tree. Copying to the hub is a
separate step (GNC_STAGE_COPY=1): files are copied (never deleted), each through a temporary name and an atomic rename.
Env: GNC_GJ3 (built gnc.json v3), GNC_STAGE, GNC_STAGE_COPY."""
import glob
import gzip
import hashlib
import json
import os
import re
import shutil
import sys

W = "/home/claude/work/space"
DEV = f"{W}/gnc_dev"
O = f"{W}/out"
HUB_ROOT = "/home/claude/work/shared-fallback/engine"
HUB = f"{HUB_ROOT}/01-systems-gnc"
STAGE = os.environ.get("GNC_STAGE", f"{W}/stage_hub/01-systems-gnc")
GJ3 = os.environ.get("GNC_GJ3", f"{O}/gnc_json/gnc_v3.json")

# results folders: hub name -> (local folder, file filter or None for every file)
RESULTS = {
    "throat_growth": (f"{O}/throat_growth", None),
    "throat_growth_a1k2": (f"{O}/throat_growth_a1k2", None),
    "abort_tailoff": (f"{O}/abort_tailoff", None),
    "v27_checks": (f"{O}/v27_checks", None),
    "relight_seq_sens": (f"{O}/relight_seq_sens", None),
    "relight_181": (f"{O}/relight_181", None),
    "relight_v28": (f"{O}/relight_v28", None),
    "regband": (f"{O}/regband", None),
    "v271_checks": (f"{O}/v271_checks", None),
    "fc_thrust": (f"{O}/fc_thrust", lambda f: f.endswith(".json")),
    "prop_closure": (f"{O}/prop_closure_m2", None),
    "prop_closure_eval": (f"{O}/prop_closure_eval", None),
    "mech_v2_check": (f"{O}/mech_v2_check", None),
    "mechv2_mc": (f"{O}/mechv2_mc", None),
    "csi_v3c": (f"{O}/csi_v3c", None),
    "csi_v3": (f"{O}/csi_v3", lambda f: f == "csi_v3_fea.json"),
    "n_sweep": (f"{O}/n_sweep", None),
    "v26_checks_v3c": (f"{O}/v26_checks_v3c", None),
    "v26_checks": (f"{O}/v26_checks", None),
    "results_v3a": (f"{O}/results_v3a", None),
    "duty_cycles_v3_checks": (f"{O}/duty_cycles_v3", lambda f: f.endswith(".json") and not f.startswith("duty_cycles_index")),
    "ctrlfix": (f"{O}/ctrlfix", lambda f: f.endswith(".json") or f == "sat_run323_J0.0027_acc2000_aw2.png"),
    "meco": (f"{O}/meco", lambda f: f.endswith(".json")),
}
V3_WORK_START = 1791849600.0   # 2026-10-13T00:00:00Z: hub scripts older than this were published with gnc.json v2
EXTRA = {   # staged path -> source (files gnc.json names that live outside the result folders)
    "results/ctrlfix/sat_run323_J0.0027_acc2000_aw2.png": f"{W}/diag/sat_run323_J0.0027_acc2000_aw2.png",
    "results/ctrlfix/sat_run323_J0.0027_acc2000.png": f"{W}/diag/sat_run323_J0.0027_acc2000.png",
}
DATA = {
    "tailoff/tailoff_fit_v1.json": f"{DEV}/data/tailoff/tailoff_fit_v1.json",
    "regband/regband_model_v1.json": f"{DEV}/data/regband/regband_model_v1.json",
    "relay/lead_relay_mech_fea_k_20261012.json": f"{DEV}/data/relay/lead_relay_mech_fea_k_20261012.json",
}


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def put(src, dst, gz=False):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if gz:
        with open(src, "rb") as fi, gzip.GzipFile(dst + ".gz", "wb", mtime=0) as fo:
            shutil.copyfileobj(fi, fo)
        return dst + ".gz"
    shutil.copy2(src, dst)
    return dst


def stage():
    if os.path.isdir(STAGE):
        shutil.rmtree(STAGE)
    os.makedirs(STAGE)
    man = {"files": {}}
    # sim/gncsim
    for f in sorted(os.listdir(f"{DEV}/gncsim")):
        if f.endswith(".py"):
            man["files"][os.path.relpath(put(f"{DEV}/gncsim/{f}", f"{STAGE}/sim/gncsim/{f}"), STAGE)] = sha16(f"{DEV}/gncsim/{f}")
    # README: the v3 README replaces sim/README.md; the hub's v2.5 README is kept as sim/README_v2.5.md
    put(f"{DEV}/hub_docs/README_sim_v3.md", f"{STAGE}/sim/README.md")
    if not os.path.exists(f"{HUB}/sim/README_v2.5.md") and os.path.exists(f"{HUB}/sim/README.md"):
        if "Version: sim v2.5" in open(f"{HUB}/sim/README.md").read():
            put(f"{HUB}/sim/README.md", f"{STAGE}/sim/README_v2.5.md")
    # history: the hub's previous gncsim (published with gnc.json v2), unchanged
    for f in sorted(os.listdir(f"{HUB}/sim/gncsim")):
        if f.endswith(".py"):
            put(f"{HUB}/sim/gncsim/{f}", f"{STAGE}/sim/history/gncsim_hub_v2/{f}")
    # sim/scripts: every script named in gnc.json v3 + the m2 helpers they import
    g = json.load(open(GJ3))
    names = {os.path.basename(s) for s in g.get("scripts", []) if "/sim/scripts/" in s}
    for f in sorted(os.listdir(f"{DEV}/scripts")):
        if f.endswith(".py") and (f in names or f.startswith("m2_")):
            man["files"][os.path.relpath(put(f"{DEV}/scripts/{f}", f"{STAGE}/sim/scripts/{f}"), STAGE)] = sha16(f"{DEV}/scripts/{f}")
    for rel, src in EXTRA.items():
        if os.path.exists(src):
            man["files"][os.path.relpath(put(src, f"{STAGE}/{rel}"), STAGE)] = sha16(src)
    # history: hub scripts (published with gnc.json v2) that the new versions replace, unchanged
    kept = []
    hist = f"{HUB}/sim/history/scripts_hub_v2"
    if os.path.isdir(hist):
        for f in sorted(os.listdir(hist)):
            put(f"{hist}/{f}", f"{STAGE}/sim/history/scripts_hub_v2/{f}")
            kept.append(f)
    if os.path.isdir(f"{HUB}/sim/scripts"):
        for f in sorted(os.listdir(f"{HUB}/sim/scripts")):
            src_h, new_s = f"{HUB}/sim/scripts/{f}", f"{STAGE}/sim/scripts/{f}"
            if (os.path.isfile(src_h) and os.path.exists(new_s) and sha16(src_h) != sha16(new_s) and f not in kept
                    and os.path.getmtime(src_h) < V3_WORK_START):
                put(src_h, f"{STAGE}/sim/history/scripts_hub_v2/{f}")
                kept.append(f)
    man["history_scripts_hub_v2"] = kept
    # sim/data
    for rel, src in DATA.items():
        if os.path.exists(src):
            man["files"][os.path.relpath(put(src, f"{STAGE}/sim/data/{rel}"), STAGE)] = sha16(src)
    # results
    for sub, (src, flt) in RESULTS.items():
        if not os.path.isdir(src):
            print("missing results folder", src)
            continue
        for f in sorted(os.listdir(src)):
            p = os.path.join(src, f)
            if not os.path.isfile(p) or (flt and not flt(f)) or f.endswith((".npy", ".log", ".tmp")):
                continue
            gz = f.endswith(".csv") and os.path.getsize(p) > 100_000
            man["files"][os.path.relpath(put(p, f"{STAGE}/results/{sub}/{f}", gz), STAGE)] = sha16(p)
    # vehicle v3d
    for f in sorted(os.listdir(f"{O}/vehicle_v3d")):
        p = f"{O}/vehicle_v3d/{f}"
        if os.path.isfile(p):
            man["files"][os.path.relpath(put(p, f"{STAGE}/vehicle/{f}"), STAGE)] = sha16(p)
    # references in gnc.json v3 that must exist (in the staging tree or already in the hub)
    refs = set()

    def walk(x):
        if isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
        elif isinstance(x, str):
            for m in re.finditer(r"01-systems-gnc/[A-Za-z0-9_./\-]+", x):
                refs.add(m.group(0).rstrip(".,;)"))
    walk(g)
    miss = []
    for r in sorted(refs):
        rel = r[len("01-systems-gnc/"):]
        if not (os.path.exists(f"{STAGE}/{rel}") or os.path.exists(f"{STAGE}/{rel}.gz") or os.path.exists(f"{HUB}/{rel}")):
            miss.append(r)
    miss_scripts = []
    for s_ in g.get("scripts", []):
        rel = s_[len("01-systems-gnc/"):] if s_.startswith("01-systems-gnc/") else s_
        if not (glob.glob(f"{STAGE}/{rel}") or glob.glob(f"{HUB}/{rel}")):
            miss_scripts.append(s_)
    man["references"] = dict(n=len(refs), missing=miss, missing_scripts=miss_scripts)
    tot = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(STAGE) for f in fs)
    man["bytes"] = tot
    print(f"staged {len(man['files'])} files, {tot / 1e6:.1f} MB; references {len(refs)}, missing {miss}; scripts missing {miss_scripts}")
    with open(f"{W}/stage_hub/stage_manifest.json", "w") as f:
        json.dump(man, f, indent=1)
    return man


def copy_to_hub():
    n = 0
    for dp, _, fs in os.walk(STAGE):
        for f in fs:
            src = os.path.join(dp, f)
            rel = os.path.relpath(src, STAGE)
            dst = os.path.join(HUB, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.exists(dst) and sha16(dst) == sha16(src):
                continue
            tmp = dst + ".gnc_tmp"
            shutil.copy2(src, tmp)
            os.replace(tmp, dst)
            n += 1
    print("copied", n, "files to", HUB)


if __name__ == "__main__":
    m = stage()
    if os.environ.get("GNC_STAGE_COPY") == "1":
        if m["references"]["missing"] or m["references"]["missing_scripts"]:
            sys.exit("not copying: missing references")
        copy_to_hub()

"""Copy FEA3D deliverables to the engine hub and write a MANIFEST.json (sha256 first 16 hex, bytes, source) per folder.

Writes ONLY under hub/04-fea/assembly3d/ or hub/04-fea/s3d_v351/ (brief 188 / successor brief).  Never touches other hub paths.
usage: publish.py assembly3d|s3d_v351 [note=...] [exclude=glob;glob]  (exclude: source file names left out of this release)      (file lists below; missing optional files are skipped and listed in the manifest)
"""
from __future__ import annotations
import sys, json, hashlib, shutil, time
from pathlib import Path

W = Path("/home/claude/work/fea3d")
HUB = Path("/home/claude/work/shared-fallback/engine")
ALLOWED = {"assembly3d": HUB / "04-fea" / "assembly3d", "s3d_v351": HUB / "04-fea" / "s3d_v351"}

SRC = ["scripts/*.py", "chains/chain_B.sh", "chains/chain_C.sh", "chains/post_cones.sh", "chains/final_f2.sh"]

LISTS = {
    "assembly3d": {
        "REPORT-FEA3D.md": "REPORT-FEA3D.md",
        "tables/": "results/tables/*",
        "results/": ["results/f1_post_lc1v351_c71.json", "results/f1_post_fa1_c71.json", "results/f1_post_lc3_pose_stop*_c71.json",
                     "results/f1_lc3_hot_bound_c71.json", "results/f1_convergence.json", "results/f1_post_tc03_thread.json",
                     "results/f1_post_lc1v351_compliant_c71.json", "results/f1_post_lc3_pose_stop045_compliant_c71.json",
                     "results/f1_post_lc3_pose_stop045_gm02r*_c71.json", "results/f1_post_lc3_pose_stop315_gm01r*_c71.json", "results/f1_lever_root_*_c71.json",
                     "results/f1_lc3_summary_c71.json", "results/k_*.json", "results/modal_*.json", "results/f4_*.json", "results/fbd_*.json", "results/cmp_*.json", "results/icd_airframe_v21_fea3d.json", "results/s3d_summary_v351.json",
                     "results/modal_*_modes.csv", "results/k_range_v351.json", "results/engine_mount_data_v351.json", "results/fa1_band_sensitivity.json"],
        "tests/modal_diag/": ["tests/modal_diag/*.py"],
        "runs/modal_v351ca2b_c71/": ["runs/modal_v351ca2b_c71/model.json", "runs/modal_v351ca2b_c71/mass.json"],
        "results/legacy_asm_v1.1/": ["results/f1_post_lc1v351_design_rigid.json", "results/f1_post_fa1_v351.json",
                                     "results/f1_post_lc3_pose_stop???.json", "results/f1_lc3_hot_bound_legacy_v11.json", "results/f1_lc3_summary_legacy_v11.json"],
        "tables_legacy_v1.1/": "results/tables_legacy_v11/*",
        "tests/conn71/": ["tests/conn71/*.py", "tests/conn71/*.inp", "tests/conn71/*.dat", "tests/conn71/*.log", "tests/conn71/*.json"],
        "figs/": "figs/f1/*.png",
        "runs/": ["runs/lc1v351_c71/model.json", "runs/lc1v351_c71/mass.json", "runs/lc1v351_c71/pressure.json",
                  "runs/queue_B.txt", "runs/chain_B.log", "runs/queue_C.txt", "runs/chain_C.log"],
        "src/": SRC,
        "PROGRESS.md": "PROGRESS.md",
    },
    "s3d_v351": {
        "REPORT-S3D.md": "s3d/REPORT-S3D.md",
        "results/": ["results/s3d_pose_*_c71.json", "results/s3d_summary_v351.json", "results/f1_post_lc3_pose_stop*_c71.json",
                     "results/f1_post_lc3_pose_stop*_gm0*r*_c71.json", "results/f1_lever_root_*_c71.json", "results/f1_post_fa1_c71.json",
                     "results/f1_lc3_hot_bound_s3d.json", "results/k_cone_c71.json", "results/k_stop_c71.json", "results/k_range_v351.json",
                     "results/engine_mount_data_v351.json"],
        "tables/": ["results/tables/s3d_*.md", "results/tables/engine_mount_data_v351.md", "results/tables/k_range_v351.md", "results/tables/margin_matrix_v351.md"],
        "figs/": "figs/s3d/*.png",
        "src/": SRC,
    },
}


def sha16(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


def main(folder, note="", exclude=""):
    import fnmatch
    excl = [x for x in exclude.split(";") if x]
    dst = ALLOWED[folder]
    dst.mkdir(parents=True, exist_ok=True)
    files, missing = {}, []
    for rel, srcs in LISTS[folder].items():
        srcs = [srcs] if isinstance(srcs, str) else srcs
        for pat in srcs:
            hits = sorted(W.glob(pat)) if any(c in pat for c in "*?[") else ([W / pat] if (W / pat).exists() else [])
            if not hits:
                missing.append(pat)
                continue
            for src in hits:
                if src.is_dir() or any(fnmatch.fnmatch(src.name, x) for x in excl):
                    continue
                tgt = dst / rel if not rel.endswith("/") else dst / rel / src.name
                tgt.parent.mkdir(parents=True, exist_ok=True)
                assert str(tgt.resolve()).startswith(str(dst.resolve())), tgt
                shutil.copy2(src, tgt)
                files[str(tgt.relative_to(dst))] = {"sha256_16": sha16(tgt), "bytes": tgt.stat().st_size, "source": str(src)}
    # files of an earlier sync that are no longer in the list are NOT deleted; they are listed as superseded (not part of this release)
    stale = {str(q.relative_to(dst)): sha16(q) for q in sorted(dst.rglob("*"))
             if q.is_file() and q.name != "MANIFEST.json" and str(q.relative_to(dst)) not in files}
    man = {"script": "fea3d scripts/publish.py v1.1", "synced_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "note": note or ("FEA3D successor deliverables (lead 188). Solver bulk (.frd/.dat/.inp, fields.npz, meshes) stays in "
                            "/home/claude/work/fea3d/runs and /home/claude/work/fea3d/mesh (not published). All numbers tagged in the report; "
                            "SIM results are not physical approval."),
           "optional_not_present": missing,
           "superseded_not_in_this_release": stale, "files": files}
    (dst / "MANIFEST.json").write_text(json.dumps(man, indent=1))
    print(f"published {len(files)} files to {dst}; MANIFEST sha16 {sha16(dst / 'MANIFEST.json')}; missing optional: {missing}; superseded (kept, not in release) {len(stale)}")


if __name__ == "__main__":
    o = dict(x.split("=", 1) for x in sys.argv[2:])
    main(sys.argv[1], o.get("note", ""), o.get("exclude", ""))

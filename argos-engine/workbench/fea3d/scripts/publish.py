"""Copy FEA3D deliverables to the engine hub and write a MANIFEST.json (sha256 first 16 hex, bytes, source) per folder.

Writes ONLY under hub/04-fea/assembly3d/ or hub/04-fea/s3d_v351/ (brief 188 / successor brief).  Never touches other hub paths.
usage: publish.py assembly3d|s3d_v351 [note=...]      (file lists below; missing optional files are skipped and listed in the manifest)
"""
from __future__ import annotations
import sys, json, hashlib, shutil, time
from pathlib import Path

W = Path("/home/claude/work/fea3d")
HUB = Path("/home/claude/work/shared-fallback/engine")
ALLOWED = {"assembly3d": HUB / "04-fea" / "assembly3d", "s3d_v351": HUB / "04-fea" / "s3d_v351"}

SRC = ["scripts/*.py", "chains/chain_B.sh"]

LISTS = {
    "assembly3d": {
        "REPORT-FEA3D.md": "REPORT-FEA3D.md",
        "tables/": "results/tables/*",
        "results/": ["results/f1_post_lc1v351_design_rigid.json", "results/f1_post_fa1_v351.json", "results/f1_post_lc3_pose_stop*.json",
                     "results/f1_lc3_hot_bound.json", "results/f1_convergence.json", "results/f1_post_tc03_thread.json",
                     "results/f1_post_lc1v351_compliant.json", "results/k_*.json", "results/modal_*.json", "results/f4_*.json"],
        "figs/": "figs/f1/*.png",
        "runs/": ["runs/lc1v351_design_rigid/model.json", "runs/lc1v351_design_rigid/mass.json", "runs/lc1v351_design_rigid/pressure.json",
                  "runs/queue_B.txt", "runs/chain_B.log"],
        "src/": SRC,
        "PROGRESS.md": "PROGRESS.md",
    },
    "s3d_v351": {
        "REPORT-S3D.md": "s3d/REPORT-S3D.md",
        "results/": ["results/s3d_*.json", "results/f1_post_lc3_pose_stop*.json", "results/k_*.json"],
        "figs/": "figs/s3d/*.png",
    },
}


def sha16(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


def main(folder, note=""):
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
                if src.is_dir():
                    continue
                tgt = dst / rel if not rel.endswith("/") else dst / rel / src.name
                tgt.parent.mkdir(parents=True, exist_ok=True)
                assert str(tgt.resolve()).startswith(str(dst.resolve())), tgt
                shutil.copy2(src, tgt)
                files[str(tgt.relative_to(dst))] = {"sha256_16": sha16(tgt), "bytes": tgt.stat().st_size, "source": str(src)}
    man = {"script": "fea3d scripts/publish.py v1.0", "synced_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "note": note or ("FEA3D successor deliverables (lead 188). Solver bulk (.frd/.dat/.inp, fields.npz, meshes) stays in "
                            "/home/claude/work/fea3d/runs and /home/claude/work/fea3d/mesh (not published). All numbers tagged in the report; "
                            "SIM results are not physical approval."),
           "optional_not_present": missing, "files": files}
    (dst / "MANIFEST.json").write_text(json.dumps(man, indent=1))
    print(f"published {len(files)} files to {dst}; MANIFEST sha16 {sha16(dst / 'MANIFEST.json')}; missing optional: {missing}")


if __name__ == "__main__":
    o = dict(x.split("=", 1) for x in sys.argv[2:])
    main(sys.argv[1], o.get("note", ""))

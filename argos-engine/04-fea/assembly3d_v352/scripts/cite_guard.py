"""Cite guard (fea3d 2026-10-20 ~13:40Z; lead 13:32Z rule for every agent: "a prune or a lossless repack first searches for the file's sha
and path in the hub (incl. the CHANGELOG and reviews/), reviews-mech-r1/r2, the GitHub archive and the images page, and skips any hit").

For each file: patterns = its sha256 (full and /16) and its path tail relative to the nearest 'runs' directory (runs/<run>/<state>/<file>
-> '<run>/<state>/<file>'; jfwd/runs/<job>/<file> -> '<job>/<file>'), plus any extra patterns given (e.g. an older sha16 of the same
file).  Searched in every text file (< 50 MB, binary suffixes skipped) of
  hub      /home/claude/work/shared-fallback (the CHANGELOG, manifests and reviews/ are inside)
  reviews  /home/claude/work/reviews-mech-r1, /home/claude/work/reviews-mech-r2
  archive  /home/claude/p1-propulsion working tree (.git skipped) and every commit of every ref (git grep over rev-list --all)
  images   /home/claude/p1-propulsion/argos-engine/gallery/argos-engine-images.html (part of the archive; reported on its own)
  lead_cl  the lead's scratchpad cl/ (CHANGELOG snapshots; added 14:25Z per the lead 14:11Z (i)(3) corpus)
check(paths) -> {path: [hits]}; a file with any hit must be skipped by the caller.  Read-only.
usage: cite_guard.py PATH [PATH ...]   (exit 0: no hit; exit 3: at least one file cited)"""
from __future__ import annotations
import sys, hashlib, subprocess
from pathlib import Path

CORPORA = {"hub": [Path("/home/claude/work/shared-fallback")],
           "reviews": [Path("/home/claude/work/reviews-mech-r1"), Path("/home/claude/work/reviews-mech-r2")],
           "archive": [Path("/home/claude/p1-propulsion")],
           "lead_cl": [Path("/tmp/claude-0/-home-claude/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/cl")]}
ARCH = Path("/home/claude/p1-propulsion")
IMAGES = ARCH / "argos-engine" / "gallery" / "argos-engine-images.html"
SKIP = (".step", ".stp", ".stl", ".glb", ".npz", ".npy", ".frd", ".gz", ".xz", ".pdf", ".png", ".jpg", ".jpeg", ".dxf", ".svg", ".zip",
        ".bin", ".pack", ".idx", ".so", ".pyc")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def tail(p):
    parts = Path(p).resolve().parts
    i = max(k for k, s in enumerate(parts) if s == "runs")
    return "/".join(parts[i + 1:])


def check(paths, extra=None):
    pats = {}
    for p in paths:
        s = sha(p)
        pats[str(p)] = {"sha_full": s, "sha16": s[:16], "tail": tail(p)}
        for k, v in ((extra or {}).get(str(p)) or {}).items():
            pats[str(p)][k] = v
    hits = {str(p): [] for p in paths}
    for cname, roots in CORPORA.items():
        for root in roots:
            for q in root.rglob("*"):
                if ".git" in q.parts:
                    continue
                try:
                    if not q.is_file() or q.stat().st_size > 50_000_000 or q.suffix.lower() in SKIP:
                        continue
                    t = q.read_text(errors="ignore")
                except Exception:
                    continue
                for p, d in pats.items():
                    for k, v in d.items():
                        if v in t:
                            hits[p].append(f"{cname}:{q} [{k}]")
    revs = subprocess.run(["git", "-C", str(ARCH), "rev-list", "--all"], capture_output=True, text=True).stdout.split()
    allp = sorted({v for d in pats.values() for v in d.values()})
    args = ["git", "-C", str(ARCH), "grep", "-I", "-F", "-l"]
    for v in allp:
        args += ["-e", v]
    g = subprocess.run(args + revs, capture_output=True, text=True) if revs else None
    for L in ([x for x in g.stdout.splitlines() if x.strip()] if g else []):
        rev, _, fn = L.partition(":")
        blob = subprocess.run(["git", "-C", str(ARCH), "show", f"{rev}:{fn}"], capture_output=True, text=True, errors="ignore").stdout
        for p, d in pats.items():
            for k, v in d.items():
                if v in blob:
                    hits[p].append(f"archive_git:{rev[:10]}:{fn} [{k}]")
    img = IMAGES.read_text(errors="ignore") if IMAGES.exists() else ""
    for p, d in pats.items():
        for k, v in d.items():
            if v in img:
                hits[p].append(f"images:{IMAGES} [{k}]")
    return hits, pats


if __name__ == "__main__":
    h, pats = check(sys.argv[1:])
    n = 0
    for p, v in h.items():
        print(f"{p}: sha16 {pats[p]['sha16']} tail {pats[p]['tail']} hits {len(v)}" + (f" {v[:6]}" if v else ""), flush=True)
        n += bool(v)
    sys.exit(3 if n else 0)

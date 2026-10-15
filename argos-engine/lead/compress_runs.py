"""Disk relief 2026-10-13 (lead via coordinator): compress large superseded/extracted run files under /home/claude/work/mechanical/runs
with xz -1 (single thread, nice 19), never files referenced by the hub (manifests, reviews, results) or in use; manifest with hashes."""
import hashlib, json, os, re, subprocess, sys, time
from pathlib import Path
RUNS = Path("/home/claude/work/mechanical/runs")
HUB = Path("/home/claude/work/shared-fallback/engine")
MAN = RUNS / "ARCHIVE_MANIFEST_20261013.json"
refs = set()
for p in HUB.rglob("*"):
    if p.is_file() and p.suffix in (".json", ".md", ".py", ".sha256", ".csv", ".log", ".txt") and p.stat().st_size < 50e6:
        try:
            s = p.read_text(errors="ignore")
        except Exception:
            continue
        for m in re.finditer(r"runs/[A-Za-z0-9_./+-]+", s):
            refs.add(m.group(0).rstrip("./"))
def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()[:16]
keep_in_use = ("v351_TB1GC",)          # thermal states of the running v3.5.1 S-AX: compress after its post/seals/png
cands = []
for pat in ("*.frd", "*.12d"):
    cands += [p for p in RUNS.rglob(pat) if p.stat().st_size > 1e6]
cands += [p for p in (RUNS / "stiff").rglob("*.inp") if p.stat().st_size > 1e6]
done = json.loads(MAN.read_text())["files"] if MAN.exists() else []
out = []
for p in sorted(cands):
    rel = "runs/" + str(p.relative_to(RUNS))
    if any(k in rel for k in keep_in_use):
        print("SKIP in use", rel); continue
    if rel in refs:
        print("SKIP referenced by hub", rel); continue
    sz = p.stat().st_size
    h0 = sha16(p)
    t0 = time.time()
    r = subprocess.run(["nice", "-n", "19", "xz", "-1", "-T1", str(p)], capture_output=True, text=True)
    if r.returncode != 0:
        print("FAIL", rel, r.stderr); continue
    px = Path(str(p) + ".xz")
    out.append({"original": rel, "original_bytes": sz, "original_sha256_16": h0, "archive": rel + ".xz",
                "archive_bytes": px.stat().st_size, "archive_sha256_16": sha16(px), "s": round(time.time() - t0, 1)})
    print(f"{rel}: {sz/1e6:.1f} -> {px.stat().st_size/1e6:.1f} MB ({time.time()-t0:.0f} s)", flush=True)
MAN.write_text(json.dumps({"id": "runs_archive_manifest", "date": "2026-10-13", "owner": "mechanical",
                           "why": "root disk nearly full (lead via coordinator 16:5xZ): xz -1 of extracted/superseded solver files; restore with xz -d (byte-identical, original sha256/16 listed)",
                           "deleted": [{"path": "runs/structural/L1_thv351_TB1GC_cad351_SUPERSEDED_v341mesh", "bytes": 311347503,
                                        "why": "own superseded S-AX run (v3.4.1 rev B mesh re-used under the v3.5.1 thermal states; not referenced by the hub); its margin/SCL tables are kept in 04-fea/structural/results/*_SUPERSEDED_v341mesh.*"}],
                           "files": done + out}, indent=1))
print("freed MB", round(sum(o["original_bytes"] - o["archive_bytes"] for o in out) / 1e6, 1))

#!/usr/bin/env python3
"""REV-MECH-2, 2026-10-19 - verify an author MANIFEST.json (files: {relpath: {sha256..., bytes...}} or similar) against the files on
disk (own code).  Reports missing, mismatched and extra files.
Usage: python -I rm2_verify_manifest.py <deliverable_dir> <out_json>
"""
import hashlib
import json
import sys
from pathlib import Path


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    d, out = Path(sys.argv[1]), Path(sys.argv[2])
    m = json.loads((d / "MANIFEST.json").read_text())
    files = m["files"]
    res = {"superseded_not_in_this_release": m.get("superseded_not_in_this_release"), "dir": str(d), "manifest_sha256_16": sha(d / "MANIFEST.json")[:16], "n_listed": len(files), "ok": 0, "mismatch": [],
           "missing": [], "extra_on_disk": [], "entry_format": None}
    for rel, ent in files.items():
        if res["entry_format"] is None:
            res["entry_format"] = sorted(ent.keys()) if isinstance(ent, dict) else type(ent).__name__
        want = (ent.get("sha256") or ent.get("sha256_16")) if isinstance(ent, dict) else ent
        nbytes = ent.get("bytes") if isinstance(ent, dict) else None
        p = d / rel
        if not p.exists():
            res["missing"].append(rel)
            continue
        got = sha(p)
        size_ok = (nbytes is None) or (p.stat().st_size == nbytes)
        if want and (got == want or got[:len(want)] == want) and size_ok:
            res["ok"] += 1
        else:
            res["mismatch"].append({"file": rel, "manifest": want, "disk": got[:16]})
    listed = set(files)
    for p in d.rglob("*"):
        if p.is_file():
            rel = str(p.relative_to(d))
            if rel not in listed and rel != "MANIFEST.json":
                res["extra_on_disk"].append(rel)
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: (v if not isinstance(v, list) else (len(v), v[:12])) for k, v in res.items()}, indent=1))


if __name__ == "__main__":
    main()

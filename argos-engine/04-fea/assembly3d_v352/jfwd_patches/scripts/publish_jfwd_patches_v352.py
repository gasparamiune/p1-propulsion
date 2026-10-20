"""Publish the J-FWD seat-patch evidence to the hub as NEW files only (fea3d, written 2026-10-20T16:06:27Z (date -u); lead 16:04Z:
"publish it to the hub as NEW files only.  Do not rewrite any existing hub file; the jfwd_interim INDEX 76f9852492a597dd is cited by
line 240").

Destinations (under hub 04-fea/assembly3d_v352/):
  results/v352/   the three soak-envelope files (v1 1d970741cb95a885, v2 336568296bdb896f, v3 0872de4ea7e3601d) and the A_ROW flat
                  bearing outputs v1 / v2 (bdb34ca4af677bca, a22a235548867570)
  jfwd_patches/   per patch run (a) seat_s5L8_mu0, (a') seat_s5L8_mu0_go, (a'') seat_s5L12_mu0_go, (b2) seat_s6L12_mu0: the small post
                  JSONs and the ccx run record (ccx_run.json, .sta, .cvg, .dat, .log) and COMPRESSED.txt (frd raw / gz sha record);
                  the (b2') seat_s9L12_mu0 and (b1) seat_s9L12_mu02 decks as built at 13:09Z with their meta.json; the scripts that
                  produced them (current work-tree versions, plus the two builder versions behind envelope v2 and A_ROW v1); the
                  mesh / model / patch build records (JSON + the small patch-set npz); INDEX.json; MANIFEST.sha256
Rules: a destination that already exists stops the publish before anything is written; every copy is byte-identical to its source
(shutil.copy2, sha256 compared after the copy); no fields.npz, frd or frd.gz; every file under 100 MB; nothing is pruned, repacked
or deleted.
usage: publish_jfwd_patches_v352.py STAMP   (STAMP = `date -u +%FT%TZ` taken just before)"""
from __future__ import annotations
import sys, os, json, hashlib, shutil
from pathlib import Path

W = Path("/home/claude/work/fea3d")
SP = Path("/tmp/claude-0/-home-claude/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad")
HUB = Path("/home/claude/work/shared-fallback/engine/04-fea/assembly3d_v352")
DP, DR = HUB / "jfwd_patches", HUB / "results" / "v352"
RUNS = {"seat_s5L8_mu0": "(a)", "seat_s5L8_mu0_go": "(a')", "seat_s5L12_mu0_go": "(a'')", "seat_s6L12_mu0": "(b2)"}
DECKS = {"seat_s9L12_mu0": "(b2') s9 mu 0 (deck 31678e81850ebee4; lead 15:37Z (R3): judged by the 5 % rule at PRELOAD and FA1S)",
         "seat_s9L12_mu02": "(b1) s9 mu 0.2 as built 13:09Z (deck e491b04b2b559c99, no repeats): to be superseded by the form (A) "
                            "rebuild under a new job name (lead 15:37Z (R3)); kept as the record of what was built"}
SCRIPTS = ["jfwd_patch_judge.py", "jfwd_lig_station.py", "jfwd_envelope.py", "jfwd_envelope_b2.py", "jfwd_patch_summary.py",
           "jfwd_histcheck.py", "jfwd_runcmp.py", "jfwd_seat_cmp.py", "jfwd_seatforce.py", "jfwd_shank.py", "jfwd_seat.py", "jfwd_sub.py",
           "jfwd_deck.py", "jfwd_post.py", "jfwd_midbay.py", "jfwd_cforce.py", "jfwd_ligament.py", "jfwd_mat.py",
           "jfwd_flat_bearing_arow.py", "mesh3d.py", "asm3d.py", "fe3d.py", "ccxrun.py", "publish_jfwd_patches_v352.py"]
OLD_BUILDERS = {"jfwd_envelope_v2builder_f90d7341a1dccb64.py": (SP / "jfwd_envelope.py.bak_1605",
                                                               "jfwd_envelope.py as it produced envelope v2 336568296bdb896f (before the v3 edit)"),
                "jfwd_flat_bearing_arow_v1builder_85c62b183b5e9f43.py": (SP / "jfwd_flat_bearing_arow.py.bak_1556",
                                                                         "jfwd_flat_bearing_arow.py as it produced A_ROW v1 bdb34ca4af677bca")}
BUILD = ["mesh_s5.json", "mesh_s6.json", "mesh_s9.json", "model_s5.json", "model_s6.json", "model_s9.json", "seat_s5L8.json",
         "seat_s5L8.npz", "seat_s5L12.json", "seat_s5L12.npz", "seat_s6L12.json", "seat_s6L12.npz", "seat_s9L12.json", "seat_s9L12.npz"]
RESULTS = {"jfwd_soak_envelope_v352_v1.json": "envelope v1 (superseded record)",
           "jfwd_soak_envelope_v352.json": "envelope v2, sharp only (superseded record; adopted 13:14Z, superseded 15:37Z (R1))",
           "jfwd_soak_envelope_v352_v3.json": "envelope v3 ADOPTED (lead 15:37Z (R1), accepted 15:55Z; CHANGELOG 241)",
           "jfwd_flat_bearing_arow_v352.json": "A_ROW flat bearing v1 on envelope v2 (information, A4-80 FE head force)",
           "jfwd_flat_bearing_arow_v352_v2.json": "A_ROW flat bearing v2 on envelope v3 (information, A4-80 FE head force; its doc text "
                                                  "says '(15:56Z)', the file was written 15:52:56Z, see its date field)"}
EXCLUDE_SUFFIX = (".frd", ".frd.gz", ".inp", ".12d", ".npz")
LIMIT = 100e6


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def plan():
    items = []          # (src, dst, run, role)
    for run, lab in RUNS.items():
        d = W / "jfwd" / "runs" / run
        for p in sorted(d.iterdir()):
            if p.is_dir() or p.name == "DONE" or p.name.endswith(EXCLUDE_SUFFIX) or p.name == "spooles.out":
                continue
            role = "ccx run record" if (p.name == "ccx_run.json" or p.suffix in (".sta", ".cvg", ".dat", ".log")) else \
                   ("frd compression record (raw / gz sha)" if p.name == "COMPRESSED.txt" else "post JSON")
            items.append((p, DP / run / p.name, f"{lab} {run}", role))
    for run, lab in DECKS.items():
        d = W / "jfwd" / "runs" / run
        items.append((d / f"{run}.inp", DP / run / f"{run}.inp", lab, "deck"))
        items.append((d / "meta.json", DP / run / "meta.json", lab, "deck build record"))
    for s in SCRIPTS:
        items.append((W / "scripts" / s, DP / "scripts" / s, "scripts", "script (work-tree version at publish)"))
    for n, (src, note) in OLD_BUILDERS.items():
        items.append((src, DP / "scripts" / n, "scripts", note))
    for b in BUILD:
        items.append((W / "jfwd" / b, DP / "build_records" / b, "build records", "mesh / model / patch-set build record"))
    for n, note in RESULTS.items():
        items.append((W / "results" / "v352" / n, DR / n, "results/v352", note))
    return items


def main(stamp):
    items = plan()
    bad = [str(d) for _, d, _, _ in items if d.exists()]
    missing = [str(s) for s, _, _, _ in items if not s.exists()]
    big = [str(s) for s, _, _, _ in items if s.exists() and s.stat().st_size >= LIMIT]
    forbidden = [str(s) for s, _, _, _ in items if s.name == "fields.npz" or ".frd" in s.name]
    for k, v in (("destination exists", bad), ("source missing", missing), ("over 100 MB", big), ("forbidden", forbidden)):
        if v:
            raise SystemExit(f"STOP ({k}): {v}")
    for p in (DP / "INDEX.json", DP / "MANIFEST.sha256"):
        if p.exists():
            raise SystemExit(f"STOP (destination exists): {p}")
    rows = []
    for src, dst, run, role in items:
        h0 = sha(src)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        h1 = sha(dst)
        if h0 != h1:
            raise SystemExit(f"STOP: copy differs {src} -> {dst}")
        rows.append({"file": os.path.relpath(dst, DP), "sha256_16": h1[:16], "sha256": h1, "bytes": dst.stat().st_size, "run": run,
                     "role": role, "source": str(src)})
    index = {"id": "jfwd_patches_INDEX_v352", "owner": "fea3d", "date_utc": stamp,
             "doc": __doc__.split("usage:")[0].strip(), "evidence": "SIM (patch runs) + DERIVED (posts, envelope); copies byte-identical to "
             "the fea3d work tree (sha256 compared at copy)", "runs": {**{r: l for r, l in RUNS.items()}, **DECKS},
             "not_published": "fields.npz, frd, frd.gz and the (a)-(b2) decks (raw / gz shas in each run's COMPRESSED.txt and meta.json)",
             "files": rows, "n_files": len(rows), "total_bytes": sum(r["bytes"] for r in rows)}
    (DP / "INDEX.json").write_text(json.dumps(index, indent=1))
    lines = [f"{r['sha256']}  {r['file']}" for r in rows]
    hi = sha(DP / "INDEX.json")
    lines.append(f"{hi}  INDEX.json")
    (DP / "MANIFEST.sha256").write_text("\n".join(lines) + "\n")
    print(f"published {len(rows)} files + INDEX.json + MANIFEST.sha256; data bytes {index['total_bytes']}; INDEX {hi[:16]}; "
          f"MANIFEST {sha(DP / 'MANIFEST.sha256')[:16]}")


if __name__ == "__main__":
    main(sys.argv[1])

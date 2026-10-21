"""Independent diff check of the stream-built js5b deck (fea3d, written 2026-10-20T20:06:38Z (date -u)); called by tail_F_js5b.sh v2.

Lead 19:53:27Z (2): on the re-test PASS the stage's diff check becomes "source + the N_CFACE *NSET (14,255 nodes) + ', NSET=N_CFACE' on
exactly 7 *CONTACT FILE lines + ', FREQUENCY=1000' on exactly the output-card lines you list (state the count), nothing else"; (3)(a)2:
the stage reads the source deck only as a stream (gunzip -c <deck>.inp.gz), checks the stream's full raw sha before the build, and
diffs the generated deck against that stream.  The listed output-card lines: the 7 '*NODE FILE', 7 '*EL FILE' and 7 '*CONTACT FILE'
lines of js5b's 7 output steps = 21 lines (the SEAT step has none; the 8 '*NODE PRINT, NSET=N_REF' lines are not changed).
Checks, all required: the stream's sha256 = the source raw sha; the generated deck = the stream + one '*NSET, NSET=N_CFACE' block right
before the first *STEP (14,255 unique node ids, = meta n_cface) + exactly 21 changed lines: '*CONTACT FILE' -> '*CONTACT FILE,
NSET=N_CFACE, FREQUENCY=1000' (7), '*NODE FILE' -> '*NODE FILE, FREQUENCY=1000' (7), '*EL FILE' -> '*EL FILE, FREQUENCY=1000' (7), nothing
else; no plain card line left; 'FREQUENCY' nowhere else in the deck; meta (source raw sha, 7 cards, frequency 1000 on 21 lines, 21
lines changed) and the meta deck sha16 = the file's.  Read-only.
usage: js5b_deck_check_v352.py SRC_INP_GZ NEW_DIR JOB"""
import sys, json, gzip, hashlib
from pathlib import Path

RAW = "fd5c555220cab42719d432cdb6c605220020f9198c734a1845bbd5674ad6d36d"
FQ = ", FREQUENCY=1000"
EXPECT = {"*CONTACT FILE": "*CONTACT FILE, NSET=N_CFACE" + FQ, "*NODE FILE": "*NODE FILE" + FQ, "*EL FILE": "*EL FILE" + FQ}
N_EACH, N_CFACE = 7, 14255


def main(srcgz, nd, job):
    h, parts = hashlib.sha256(), []
    with gzip.open(srcgz, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
            parts.append(b)
    src_sha = h.hexdigest()
    a = b"".join(parts).decode().split("\n")
    deck = Path(nd) / f"{job}.inp"
    raw_new = deck.read_bytes()
    b = raw_new.decode().split("\n")
    meta = json.loads((Path(nd) / "meta.json").read_text())
    m = meta["restricted_contact_output"]
    starts = [i for i, L in enumerate(b) if L.upper().startswith("*NSET, NSET=N_CFACE")]
    i0 = starts[0] if len(starts) == 1 else None
    k = m["nset_lines_added"]
    ids = [int(x) for L in b[i0 + 1:i0 + k] for x in L.split(",") if x.strip()] if i0 is not None else []
    rest = b[:i0] + b[i0 + k:] if i0 is not None else b
    first_step = next(i for i, L in enumerate(a) if L.upper().startswith("*STEP"))
    chg = [i for i, (x, y) in enumerate(zip(a, rest)) if x != y]
    by = {}
    for i in chg:
        by[a[i]] = by.get(a[i], 0) + 1
    checks = {
        "stream_raw_sha256": src_sha == RAW,
        "nset_block_once_before_first_step": i0 == first_step,
        "same_length_without_nset": len(a) == len(rest),
        "changed_21": len(chg) == 3 * N_EACH,
        "changed_only_listed_cards": all(a[i] in EXPECT and rest[i] == EXPECT[a[i]] for i in chg),
        "7_of_each": by == {c: N_EACH for c in EXPECT},
        "new_lines_count": all(sum(L == v for L in b) == N_EACH for v in EXPECT.values()),
        "no_plain_card_left": not any(L.strip().upper() in EXPECT for L in b),
        "frequency_nowhere_else": sum("FREQUENCY" in L.upper() for L in b) == 3 * N_EACH,
        "n_cface": len(ids) == len(set(ids)) == m["n_cface"] == N_CFACE,
        "meta": (m["source_raw_sha256"] == RAW and m["contact_file_cards_changed"] == N_EACH and m["frequency"] == 1000
                 and m["frequency_lines"] == 3 * N_EACH and m["lines_changed"] == 3 * N_EACH),
        "meta_deck_sha16": meta["deck_sha16"] == hashlib.sha256(raw_new).hexdigest()[:16]}
    ok = all(checks.values())
    print(f"restricted + FREQUENCY deck check {'OK' if ok else 'FAILED'}: {job}.inp {meta['deck_sha16']} = stream of {Path(srcgz).name} "
          f"(raw sha256 {src_sha}) + *NSET N_CFACE ({len(ids)} nodes, {k - 1} id lines, before line {first_step + 1}) + {len(chg)} changed lines "
          f"{by} (source lines {[i + 1 for i in chg]}); nothing else differs; failed: {[c for c, v in checks.items() if not v]}", flush=True)
    return 0 if ok else 4


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))

"""Lossless deck repack, P7 (R3 / hb3 decks .gz -> .xz) and P2 (four J-FWD raw decks -> .gz) (fea3d, written 2026-10-20T18:15:33Z
(date -u)).

Lead 18:04:32Z (Outlook v5): "ADOPTED ... P7 and P2 (both lossless)", on these conditions, per file: "decompress and check the raw
sha256 against the posted raw sha before the original goes; skip any file whose stored-file sha (16 or full) or path is cited anywhere
under the citation rule, or that a live reader still opens as .gz; touch nothing in the hub (shared-fallback); one REPACKED log line per
file with both shas; nice 19, 1 thread."

Scope (as proposed 18:01:14Z, nothing wider):
  P7  runs/pose_<pose>_v352r3R3/B1_21.65/f1.inp.gz of a POSTED v3.5.2 R3 pose run (DONE, and 'post <run> end' in runs/post_E.log)
      and runs/lc1v352hbg3|hbh3/<state>/f1.inp.gz once 'hb3_post trim <run> rc 0' is in runs/post_E.log  ->  f1.inp.xz  (xz -6 -T1).
  P2  jfwd/runs/<job>/<job>.inp for the four J-FWD decks of the proposal (js5b_mu0_T3750_g078 and js4b_mu0_T3750: superseded;
      seat_s9L8_mu0 / seat_s9L8_mu02: commented out of their queue)  ->  <job>.inp.gz  (gzip -6).
Per file, in this order (any failed step skips the file and leaves it as it was):
  1. path: only under /home/claude/work/fea3d; anything under /home/claude/work/shared-fallback (the hub) is refused;
  2. live readers: P7: every work-tree script and chain that names 'f1.inp.gz' must be one of KNOWN_GZ below (each reviewed: it does
     not open an R3 / hb3 deck as .gz, or it reads .xz as well); any other one stops the repack before the first file.
     P2: the job must not be named on an uncommented line of any runs/jfwd_queue*.txt, nor by a running process;
  3. cite check: cite_guard.check (the 13:32Z corpora: hub incl. the CHANGELOG and reviews/, reviews-mech-r1/r2, the archive tree and
     every commit, the images page, the lead's scratchpad cl/) on the stored file (sha256 full and /16, path tail), plus the path tail
     without the compression suffix, the bare file name (P2) and the raw sha (P7, full and /16); any hit -> skip (cited);
  4. the raw sha256 of the content (P7: streamed gunzip; P2: the file itself) is POSTED first: one JSON line in
     runs/deck_raw_sha_v352.jsonl;
  5. compress into <final>.tmp next to the original (the script runs at nice 19; xz -6 -T1 / gzip -6, one thread);
  6. verify: decompress the tmp file and compare its sha256 with the posted raw sha READ BACK from the register; re-hash the original:
     unchanged; the tmp file is a valid single stream (xz -t / gzip -t);
  7. os.replace(tmp, final), then the original is unlinked;
  8. one REPACKED line in runs/REPACKED_deck_v352.txt: original -> new path, stored sha256 before and after (full), raw sha256
     (verified by decompression), bytes before / after, tool, seconds.
A mismatch or a changed original keeps the original and removes the tmp file (MISMATCH / 'original changed' in the output).
Readers of a repacked deck: release_c71.py check1 reads f1.inp.xz (lzma) since 18:12:35Z; a re-solve needs `xz -dc f1.inp.xz > f1.inp`
in place of `gunzip -c f1.inp.gz > f1.inp` (raw sha unchanged, in the REPACKED line).
2026-10-20T18:55:40Z (date -u), lead 18:50:09Z (3): X1 (the 4 R2 decks) and X2 (17 decks: lc1v352 x4, lc1v352g x6, lc1v352h x6,
fa1v352n x1) ADOPTED: "follow the P7 per-file procedure: re-run the cite check immediately before each file, and skip on any hit or any
live reader; verify the raw sha by decompression; leave the hub untouched; one REPACKED line each; nice 19, 1 thread."  Modes x1 / x2
(.gz -> .xz like P7, the exact file lists X1_FILES / X2_FILES below, nothing wider).  Their cite check runs per file, right before that
file's repack (option percite=1 does the same for p7; x1 / x2 always do it).  Live readers per file (x1 / x2, and p7 with percite=1):
the KNOWN_GZ review as for P7, plus no process with the file open (/proc/*/fd) and no running process whose arguments name its run
folder.  Reviewed 18:55Z for the 21 files: no work-tree script or chain opens these decks (run_f1 / chains write and gzip only;
fa1_band_sensitivity hashes modal decks only; release_c71 reads R3 / c71 decks only), and nothing under /home/claude/work/mechanical
names them.
2026-10-20T19:17:11Z (date -u), lead 18:50:09Z (2): "G: gzip -n the js5b deck once the .sta shows step 1 ... Post the raw sha first, verify
by decompression, and write one REPACKED line."  Mode g (only=JOB, JOB in G_JOBS): jfwd/runs/JOB/JOB.inp -> JOB.inp.gz (gzip -6 -n) once
JOB.sta has a step-1 increment line (ccx reads the whole deck at its start and does not keep it open: checked on the (b1) ccx at
19:16Z, open files .log / .dat / .sta / .cvg / spooles.out only); no process may have the deck open (/proc/*/fd); no J-FWD post reads
the .inp (reviewed: jfwd_post / seatforce / shank / seat_cmp / histcheck / runcmp / lig_station / ligament / midbay / cells read the frd,
the npz models and meta.json); per-file cite check as x1 / x2.
2026-10-20T20:11:46Z (date -u), lead 19:53:27Z (3): citation rule for LOSSLESS repacks (amends the 13:32Z lossless clause; releases and
prunes untouched): "a hit on a file's RAW sha used only as a content identifier (CHANGELOG text, lead notes, a post's provenance field,
a raw-sha or REPACKED record) does NOT block a LOSSLESS repack ... A hit still blocks when it is: (i) a LIVE reader that will open the raw
path (a queued stage or deck, a builder, a post script, the images page); (ii) a path-based verifier of the raw path (a MANIFEST row, a
sha256sum -c list, a guard that hashes the path); (iii) a published path someone is told to fetch (the hub, the GitHub clone tree, the
images-page source).  The cite check still runs right before each file.  Classify every hit in the REPACKED line as identifier, (i), (ii)
or (iii); any (i)-(iii) hit skips the file.  The REPACKED line carries the old path, the new path, the full 64-hex raw sha, the
compressed sha and the verify command."  classify() below, for every mode from now on: a raw-sha hit (and, for a raw file, its stored
sha = its raw sha) is 'identifier'; a hit on a COMPRESSED file's stored sha is not a raw-sha identifier and blocks ('unclassified');
a path hit (tail / tail_raw / name) in the hub, the archive tree or its history, the images page or the reviews is (iii) ((ii) when the
hub file is a MANIFEST or a sha256 list); a path hit in a script of the lead's cl/ is (i) / (ii); a path hit in the lead's cl/ note text
is 'identifier' (the file named in note text; not a reader, a verifier or a published fetch path).  New modes:
  a   (3)(a): jfwd/runs/js5b_in718_mu0_T3750_g078/js5b_in718_mu0_T3750_g078.inp -> .inp.gz (gzip -6 -n -c), verified by
      `gunzip -c | sha256sum`, raw removed; only once runs/tail_F_js5b.sh is v2 46df0c92de3f5f7e (reads the source only as
      `gunzip -c <deck>.inp.gz`) and no other live reader names the raw deck (work-tree scripts / chains / stage scripts / queue lines,
      Mechanical's tree, running processes, open files);
  tb  (3)(b): runs/tb352g/TB/f1.inp.gz, runs/tb352h/TB/f1.inp.gz -> f1.inp.xz, as X1 / X2; live readers as X1 / X2 plus the queued soaks:
      runs/tail_F_soaks.sh must not name tb352g / tb352h, scripts/run_f1.py (the soak builder; its sax= mapping reads Mechanical's
      L1_thv352_* fields) must not, and no soak deck already written may *INCLUDE or name them.
2026-10-20T20:45Z (date -u), lead 20:44:07Z (3): "lossless-xz the three decks (js5_mu0_T3750_g078.inp, seat_s6L12_mu0.inp,
seat_s6L8_mu0.inp) under the X1 / X2 procedure with a cite check right before each, one REPACKED line each".  Mode j3 (J3_JOBS): the RAW
deck jfwd/runs/JOB/JOB.inp -> JOB.inp.xz (xz -6 -T1 -c), verified by `xz -dc | sha256sum` = the posted raw sha (= the stored sha of
the raw file); only a DONE job (or the never-run seat_s6L8_mu0 deck); live readers per file (j3_live_readers): work-tree scripts /
chains / stage scripts naming the job beyond J3_REVIEWED (each reviewed: none opens the .inp), uncommented queue lines (queue_A
lines 4 / 26 commented 20:44:45Z), Mechanical's tree (any file naming the deck file JOB.inp, or a script naming the job and mentioning
'.inp'; refined between the 20:46:04Z skip and the 20:47:43Z re-run (log stamps) after the first pass skipped js5 / s6L12 on Mechanical files that name the JOB only: result JSONs, logs and
JSON-reading scripts, reviewed read-only), running processes, open files; hits classified as for mode a (raw file).
Modes a / g / p2 / p7 / x1 / x2 / tb are unchanged by this addition.
usage: nice -n 19 python -I -B repack_deck_v352.py p7|p2|x1|x2|g|a|tb|j3 [only=RUN,RUN] [dry=1] [percite=1]
       (stdout: append to runs/repack_lzma.log, watched)"""
from __future__ import annotations
import sys, os, re, json, time, gzip, hashlib, subprocess
from pathlib import Path

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import cite_guard as CG  # noqa: E402

W = Path("/home/claude/work/fea3d")
RUNS = W / "runs"
HUB = Path("/home/claude/work/shared-fallback")
REG = RUNS / "deck_raw_sha_v352.jsonl"
LOG = RUNS / "REPACKED_deck_v352.txt"
P2_JOBS = ["js5b_mu0_T3750_g078", "js4b_mu0_T3750", "seat_s9L8_mu02", "seat_s9L8_mu0"]
G_JOBS = ["js5b_in718_mu0_T3750_g078_cf"]                                              # lead 18:50:09Z (2)
A_JOB = "js5b_in718_mu0_T3750_g078"                                                     # lead 19:53:27Z (3)(a)
A_STAGE = ("runs/tail_F_js5b.sh", "46df0c92de3f5f7e")                                   # v2: source read as a gunzip stream only
TB_FILES = ["runs/tb352g/TB/f1.inp.gz", "runs/tb352h/TB/f1.inp.gz"]                     # lead 19:53:27Z (3)(b)
J3_JOBS = ["js5_mu0_T3750_g078", "seat_s6L12_mu0", "seat_s6L8_mu0"]                     # lead 20:44:07Z (3)
J3_REVIEWED = {   # work-tree files that name a J3 job, reviewed 2026-10-20T20:44Z (date -u): none opens the job's raw .inp
    "repack_deck_v352.py": "this script",
    "jfwd_flat_bearing_arow.py": "reads post JSONs (no .inp)", "jfwd_envelope.py": "reads post JSONs (no .inp)",
    "jfwd_envelope_b2.py": "reads post JSONs (no .inp)", "margin_matrix_v352.py": "reads results JSONs (no .inp)",
    "post_ago.sh": "runs posts (frd / npz / meta; no .inp)", "post_seat_generic.sh": "runs posts (frd / npz / meta; no .inp)",
    "after_b2L12.sh": "posts of (b2) (no .inp)", "tail_F_b1.sh": "(b1) stage: hashes / runs its own deck only",
    "tail_F_b2p.sh": "(b2') stage: hashes / runs its own deck seat_s9L12_mu0 only",
    "disk_outlook_E_v6.py": "projection table (job names, sizes); never opens a J-FWD deck",
    "publish_jfwd_patches_v352.py": "publishes run records with .inp EXCLUDED; its DECKS are seat_s9L12_mu0 / seat_s9L12_mu02 only",
    "jfwd_seat.py": "seat builder: reads the global job's meta.json / frd / dat / model npz, never its .inp"}
MECH = Path("/home/claude/work/mechanical")
X1_FILES = [f"runs/pose_{q}_v352r3R2/B1_21.65/f1.inp.gz" for q in ("alpha+", "alpha-", "stop045", "stop315")]   # lead 18:50:09Z (3)
X2_FILES = (["runs/fa1v352n/A1_22.2/f1.inp.gz"] + [f"runs/lc1v352/{s}/f1.inp.gz" for s in ("B1_1", "B1_19", "B1_2", "B1_21.65")]
            + [f"runs/lc1v352g/{s}/f1.inp.gz" for s in ("B1_1", "B1_19", "B1_2", "B1_21.65", "B1_51.7", "B1_70.7")]
            + [f"runs/lc1v352h/{s}/f1.inp.gz" for s in ("B1_1", "B1_19", "B1_2", "B1_21.65", "B1_43.7", "B1_70.7")])
KNOWN_GZ = {   # work-tree files that name 'f1.inp.gz', reviewed 2026-10-20T18:15:33Z (date -u)
    "release_c71.py": "check1 reads the R3 deck as .xz or .gz (must contain lzma.open); regen_record: c71 decks only (not in scope)",
    "fa1_band_sensitivity.py": "modal run decks only (run=modal_*)",
    "modal_deckcheck_ca2c.py": "modal decks given as arguments",
    "modal_delta_ca2c_v352.py": "modal decks only (ca2b / ca2c, cited, never repacked)",
    "trim_fields_c.py": "doc text only", "disk_outlook_E_v5.py": "doc text only", "repack_deck_v352.py": "this script",
    # 2026-10-20T18:42:12Z (date -u): added after the pass-2 STOP (18:41:53Z): the v6 projection globs and stat()s the gz decks for their
    # sizes and never opens them
    "disk_outlook_E_v6.py": "projection: globs / stat() of the gz decks only, never opens them",
    # 2026-10-20T19:15:21Z (date -u): added after the x2 per-file skips at 19:15:06Z: the hub note script hashes (gzip.open) only the decks
    # named in the release log's (A) 2 regeneration records, i.e. runs/pose_*_c71/B1_21.65/f1.inp.gz (c71 decks: never repacked)
    "c71_release_note_v352.py": "reads c71 decks only (runs/pose_*_c71/B1_21.65/f1.inp.gz from the release log), never an R2 / R3 / hb3 / X2 deck",
    "run_f1.py": "writes and gzips the deck; never reads it back", "chain_A.sh": "gzip f1.inp (writer)", "chain_A2.sh": "writer",
    "chain_A3.sh": "writer", "chain_A4.sh": "writer", "chain_B.sh": "writer", "chain_C.sh": "writer", "chain_D.sh": "writer",
    "chain_E.sh": "writer"}


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def sha_cmd(cmd):
    """sha256 and byte count of a command's stdout (streamed)."""
    h, n = hashlib.sha256(), 0
    pr = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    for b in iter(lambda: pr.stdout.read(1 << 22), b""):
        h.update(b)
        n += len(b)
    if pr.wait() != 0:
        raise RuntimeError(f"{cmd} rc {pr.returncode}")
    return h.hexdigest(), n


def live_gz_readers():
    bad = []
    for p in sorted(list((W / "scripts").glob("*.py")) + list((W / "chains").glob("*.sh"))):
        try:
            s = p.read_text(errors="ignore")
        except OSError:
            continue
        if "f1.inp.gz" not in s:
            continue
        if p.name not in KNOWN_GZ:
            bad.append(f"{p.name}: names f1.inp.gz, not reviewed")
        elif p.name == "release_c71.py" and "lzma.open" not in s:
            bad.append("release_c71.py: check1 does not read .xz")
    return bad


def open_by_process(p):
    """PIDs with the file open (any /proc/<pid>/fd link resolving to it)."""
    rp, out = str(Path(p).resolve()), []
    for d in Path("/proc").iterdir():
        if not d.name.isdigit():
            continue
        try:
            for fd in (d / "fd").iterdir():
                try:
                    if os.readlink(fd) == rp:
                        out.append(int(d.name))
                        break
                except OSError:
                    pass
        except OSError:
            pass
    return out


def x_candidates(mode, only):
    lst = X1_FILES if mode == "x1" else X2_FILES
    out, why = [], {}
    procs = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True).stdout.splitlines()
    for rel in lst:
        f = W / rel
        run = f.parent.parent.name
        if only and run not in only and rel not in only:
            continue
        if not f.exists():
            why[str(f)] = "not there (already repacked or missing)"
            continue
        named = [L.strip()[:120] for L in procs if re.search(rf"(?<![A-Za-z0-9_+-]){re.escape(run)}(?![A-Za-z0-9_+-])", L)
                 and "repack_deck_v352" not in L]
        if named:
            why[str(f)] = f"run folder named by a running process: {named[:2]}"
        else:
            out.append(f)
    return out, why


def g_candidates(only):
    out, why = [], {}
    for j in (only or []):
        f = W / "jfwd" / "runs" / j / f"{j}.inp"
        sta = f.with_suffix(".sta")
        if j not in G_JOBS:
            why[str(f)] = "not a G job (lead 18:50:09Z (2): js5b only)"
        elif not f.exists():
            why[str(f)] = "not there (already gzipped or missing)"
        elif not (sta.exists() and re.search(r"^\s*1\s+\d+\s+\d+\s+\d+\s+\S+", sta.read_text(errors="ignore"), re.M)):
            why[str(f)] = "the .sta shows no step-1 increment yet"
        else:
            out.append(f)
    return out, why


def p7_candidates(only):
    plog = (RUNS / "post_E.log").read_text(errors="ignore")
    out = []
    for rd in sorted(RUNS.glob("pose_*_v352r3R3")):
        if only and rd.name not in only:
            continue
        f = rd / "B1_21.65" / "f1.inp.gz"
        if (rd / "DONE").exists() and f"post {rd.name} end" in plog and f.exists():
            out.append(f)
    for b in ("lc1v352hbg3", "lc1v352hbh3"):
        if (only and b not in only) or f"hb3_post trim {b} rc 0" not in plog:
            continue
        out += sorted((RUNS / b).glob("*/f1.inp.gz"))
    return out


def p2_candidates(only):
    live = []
    for q in RUNS.glob("jfwd_queue*.txt"):
        live += [L.split()[0] for L in q.read_text().splitlines() if L.strip() and not L.lstrip().startswith("#")]
    procs = subprocess.run(["ps", "-eo", "args"], capture_output=True, text=True).stdout
    out, why = [], {}
    for j in P2_JOBS:
        if only and j not in only:
            continue
        f = W / "jfwd" / "runs" / j / f"{j}.inp"
        if not f.exists():
            continue
        if j in live:
            why[str(f)] = "named on a live queue line"
        elif re.search(rf"(?<![A-Za-z0-9_]){re.escape(j)}(?![A-Za-z0-9_])", procs):
            why[str(f)] = "named by a running process"
        else:
            out.append(f)
    return out, why


def classify(hit, raw_file):
    """lead 19:53:27Z (3): the class of one cite_guard hit ('corpus:file [key]'): identifier / (i) / (ii) / (iii) / unclassified."""
    m = re.match(r"^(\w+):(.*) \[(\w+)\]$", hit)
    if not m:
        return "unclassified"
    corpus, where, key = m.groups()
    if key in ("raw_full", "raw16") or (key in ("sha_full", "sha16") and raw_file):
        return "identifier"
    if key in ("sha_full", "sha16"):
        return "unclassified"                      # stored sha of a compressed file: not a raw-sha content identifier -> blocks
    name = where.rsplit("/", 1)[-1].lower()
    if corpus == "hub":
        return "(ii)" if ("manifest" in name or name.endswith((".sha256", ".sha256sum", "sha256sums"))) else "(iii)"
    if corpus in ("archive", "archive_git", "images", "reviews"):
        return "(iii)"
    if corpus == "lead_cl":
        return "(i)/(ii)" if name.endswith((".py", ".sh")) else "identifier"
    return "unclassified"


def a_live_readers():
    """mode a: [(reader, why)] that would open the raw source deck jfwd/runs/A_JOB/A_JOB.inp."""
    bad = []
    st = W / A_STAGE[0]
    if sha_file(st)[:16] != A_STAGE[1]:
        bad.append((A_STAGE[0], f"sha16 {sha_file(st)[:16]} is not the stream-reading v2 {A_STAGE[1]}"))
    pat = re.compile(rf"{re.escape(A_JOB)}(?![A-Za-z0-9_])")
    reviewed = {"repack_deck_v352.py": "this script", "tail_F_js5b.sh": "v2: gunzip -c <deck>.inp.gz only (sha checked above)",
                "disk_outlook_E_v3.py": "projection table (job name, node count, sizes); never opens the deck",
                "disk_outlook_E_v4.py": "projection table (job name, node count, sizes); never opens the deck"}
    for p in sorted(list((W / "scripts").glob("*.py")) + list((W / "chains").glob("*.sh")) + list(RUNS.glob("*.sh"))):
        try:
            t = p.read_text(errors="ignore")
        except OSError:
            continue
        if pat.search(t) and p.name not in reviewed:
            bad.append((str(p.relative_to(W)), "names the source job, not reviewed"))
    for q in RUNS.glob("jfwd_queue*.txt"):
        for L in q.read_text().splitlines():
            if L.strip() and not L.lstrip().startswith("#") and pat.search(L):
                bad.append((str(q.relative_to(W)), f"uncommented queue line: {L.strip()[:80]}"))
    if MECH.exists():
        r = subprocess.run(["grep", "-rlI", A_JOB, str(MECH)], capture_output=True, text=True)
        bad += [(x, "Mechanical's tree names the source job") for x in r.stdout.split()]
    procs = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True).stdout.splitlines()
    bad += [("process", L.strip()[:120]) for L in procs if pat.search(L) and "repack_deck_v352" not in L]
    return bad


def j3_live_readers(job):
    """mode j3 (lead 20:44:07Z (3)): [(reader, why)] that would open the raw deck jfwd/runs/JOB/JOB.inp: work-tree scripts / chains / stage
    scripts naming the job beyond J3_REVIEWED, uncommented queue lines, Mechanical's tree, running processes."""
    bad = []
    pat = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(job)}(?![A-Za-z0-9_])")
    for p in sorted(list((W / "scripts").glob("*.py")) + list((W / "chains").glob("*.sh")) + list(RUNS.glob("*.sh"))):
        try:
            t = p.read_text(errors="ignore")
        except OSError:
            continue
        if pat.search(t) and p.name not in J3_REVIEWED:
            bad.append((str(p.relative_to(W)), "names the job, not reviewed"))
    for q in RUNS.glob("jfwd_queue*.txt"):
        for L in q.read_text().splitlines():
            if L.strip() and not L.lstrip().startswith("#") and pat.search(L):
                bad.append((str(q.relative_to(W)), f"uncommented queue line: {L.strip()[:80]}"))
    if MECH.exists():
        # edited between the 20:46:04Z skip and the 20:47:43Z re-run (log stamps, date -u): the first j3 pass (20:46:02Z) skipped js5 and s6L12 because Mechanical's tree NAMES the jobs:
        # reviewed read-only, those are result JSONs / logs and scripts (jfwd_relax_v352*.py, jfwd_in718_rows_v352*.py, jfwd_fix_v352*.py)
        # that read my post JSONs (e.g. runcmp_js5_mu0_T3750_g078.json); none mentions '.inp' and no file names a deck file 'JOB.inp'.
        # Rule from here: block on any Mechanical file naming the deck file (JOB.inp, also as .inp.gz / .inp.xz), or on a Mechanical
        # script (.py / .sh) that names the job and mentions '.inp' anywhere.
        r = subprocess.run(["grep", "-rlIF", f"{job}.inp", str(MECH)], capture_output=True, text=True)
        bad += [(x, "Mechanical's tree names the raw deck file") for x in r.stdout.split()]
        r = subprocess.run(["grep", "-rlI", job, str(MECH)], capture_output=True, text=True)
        for x in r.stdout.split():
            try:
                if x.endswith((".py", ".sh")) and ".inp" in Path(x).read_text(errors="ignore"):
                    bad.append((x, "Mechanical script names the job and mentions .inp"))
            except OSError:
                bad.append((x, "Mechanical file names the job and could not be read"))
    procs = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True).stdout.splitlines()
    bad += [("process", L.strip()[:120]) for L in procs if pat.search(L) and "repack_deck_v352" not in L]
    return bad


def tb_live_readers():
    """mode tb: the queued soaks (lead 19:53:27Z (3)(b)) on top of the X1 / X2 checks."""
    bad = []
    pat = re.compile(r"tb352[gh](?![A-Za-z0-9_])")
    for p in (RUNS / "tail_F_soaks.sh", W / "scripts" / "run_f1.py"):
        if pat.search(p.read_text(errors="ignore")):
            bad.append((str(p.relative_to(W)), "names tb352g / tb352h"))
    for d in sorted(RUNS.glob("soak352*")):
        for f in list(d.glob("*/f1.inp")) + list(d.glob("*/f1.inp.gz")):
            t = (gzip.open(f, "rt", errors="ignore") if f.suffix == ".gz" else open(f, errors="ignore")).read()
            if "*INCLUDE" in t.upper() or pat.search(t):
                bad.append((str(f.relative_to(W)), "soak deck *INCLUDEs or names a tb352 file"))
    return bad


def main(mode, only=None, dry=False, percite=False):
    print(f"{now()} repack_deck_v352 {mode} start (pid {os.getpid()}, nice {os.nice(0)}{', per-file cite check' if percite or mode in ('x1', 'x2') else ''})",
          flush=True)
    xz_mode = mode in ("p7", "x1", "x2", "tb")          # .gz -> .xz
    rawxz = mode == "j3"                                  # raw -> .xz (lead 20:44:07Z (3))
    percite = percite or mode in ("x1", "x2", "a", "tb", "j3")
    if xz_mode:
        bad = live_gz_readers()
        if bad:
            print(f"{now()} STOP live reader check: {bad}", flush=True)
            return 2
    if mode == "p7":
        cand, why = p7_candidates(only), {}
    elif mode in ("x1", "x2"):
        cand, why = x_candidates(mode, only)
    elif mode == "p2":
        cand, why = p2_candidates(only)
    elif mode == "g":
        cand, why = g_candidates(only)
        percite = True
    elif mode == "a":
        f = W / "jfwd" / "runs" / A_JOB / f"{A_JOB}.inp"
        cand, why = ([f], {}) if f.exists() else ([], {str(f): "not there (already gzipped or missing)"})
    elif mode == "tb":
        cand, why = [], {}
        procs = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True).stdout.splitlines()
        for rel in TB_FILES:
            f = W / rel
            run = f.parent.parent.name
            named = [L.strip()[:120] for L in procs if re.search(rf"(?<![A-Za-z0-9_+-]){re.escape(run)}(?![A-Za-z0-9_+-])", L)
                     and "repack_deck_v352" not in L]
            if not f.exists():
                why[str(f)] = "not there (already repacked or missing)"
            elif named:
                why[str(f)] = f"run folder named by a running process: {named[:2]}"
            else:
                cand.append(f)
    elif mode == "j3":
        cand, why = [], {}
        for j in J3_JOBS:
            if only and j not in only:
                continue
            d = W / "jfwd" / "runs" / j
            f = d / f"{j}.inp"
            if not f.exists():
                why[str(f)] = "not there (already repacked or missing)"
            elif not ((d / "DONE").exists() or j == "seat_s6L8_mu0"):
                why[str(f)] = "no DONE marker (only finished runs, and the never-run seat_s6L8_mu0 deck, are in scope)"
            else:
                cand.append(f)
    else:
        raise SystemExit(f"unknown mode {mode}")
    for p, w in why.items():
        print(f"{now()} skip (live) {p}: {w}", flush=True)
    for p in cand:
        if HUB in p.resolve().parents or W not in p.resolve().parents:
            raise SystemExit(f"STOP: {p} is outside the work tree or in the hub")
    if not cand:
        print(f"{now()} nothing to repack", flush=True)
        return 0
    # raw shas first (P7 / X: needed as cite patterns too)
    raw = {}
    for p in cand:
        raw[str(p)] = sha_cmd(["gzip", "-dc", str(p)]) if xz_mode else (sha_file(p), p.stat().st_size)
    extra = {}
    for p in cand:
        t = CG.tail(p)
        e = {"tail_raw": re.sub(r"\.gz$", "", t)}
        if xz_mode:
            e.update({"raw_full": raw[str(p)][0], "raw16": raw[str(p)][0][:16]})
        else:
            e["name"] = p.name
        extra[str(p)] = e
    hits = {}
    if not percite:
        t0 = time.time()
        hits, pats = CG.check(cand, extra)
        print(f"{now()} cite check of {len(cand)} files: {sum(bool(v) for v in hits.values())} cited ({time.time() - t0:.0f} s)", flush=True)
    done = 0
    for p in cand:
        if percite:                                     # lead 18:50:09Z (3): the cite check right before each file
            bad = live_gz_readers() if xz_mode else []
            bad += a_live_readers() if mode == "a" else (tb_live_readers() if mode == "tb" else
                                                         (j3_live_readers(p.parent.name) if mode == "j3" else []))
            opn = open_by_process(p)
            if bad or opn:
                print(f"{now()} skip (live reader) {p}: {bad or ''} {('open by pid ' + str(opn)) if opn else ''}", flush=True)
                continue
            t0 = time.time()
            h1, _ = CG.check([p], {str(p): extra[str(p)]})
            hits[str(p)] = h1.get(str(p))
            print(f"{now()} cite check {p.relative_to(W)}: {'CITED' if hits[str(p)] else '0 hits'} ({time.time() - t0:.0f} s)", flush=True)
        cls = [(classify(h, raw_file=not xz_mode), h) for h in (hits.get(str(p)) or [])]      # lead 19:53:27Z (3)
        blocking = [(c, h) for c, h in cls if c != "identifier"]
        if blocking:
            print(f"{now()} skip (cited: {len(blocking)} blocking hit(s) under lead 19:53:27Z (3)) {p}: {blocking[:4]}", flush=True)
            continue
        if cls:
            print(f"{now()} cite hits of {p.relative_to(W)}: {len(cls)}, all 'identifier' (lead 19:53:27Z (3)): {[h for _, h in cls][:6]}", flush=True)
        final = p.with_name(p.name[:-3] + ".xz") if xz_mode else p.with_name(p.name + (".xz" if rawxz else ".gz"))
        if final.exists():
            print(f"{now()} skip (target exists) {final}", flush=True)
            continue
        if dry:
            print(f"{now()} would repack {p} -> {final.name} ({p.stat().st_size / 1e6:.2f} MB, raw sha256 {raw[str(p)][0][:16]})", flush=True)
            continue
        s_before, a = sha_file(p), p.stat().st_size
        raw_sha, raw_n = raw[str(p)]
        if (xz_mode and sha_cmd(["gzip", "-dc", str(p)])[0] != raw_sha) or (rawxz and s_before != raw_sha):
            print(f"{now()} original changed during the cite check, kept {p}", flush=True)
            continue
        rec = {"time": now(), "for": mode.upper(), "path": str(p.relative_to(W)), "stored_sha256": s_before, "raw_sha256": raw_sha,
               "raw_bytes": raw_n, "target": str(final.relative_to(W))}
        with open(REG, "a") as f:                       # 4. the raw sha is posted before anything is written
            f.write(json.dumps(rec) + "\n")
        tmp = final.with_name(final.name + ".tmp")
        t1 = time.time()
        with open(tmp, "wb") as fo:                     # 5. compress (one thread; the script runs at nice 19)
            if xz_mode:
                g = subprocess.Popen(["gzip", "-dc", str(p)], stdout=subprocess.PIPE)
                x = subprocess.run(["xz", "-6", "-T1", "-c"], stdin=g.stdout, stdout=fo)
                g.stdout.close()
                rc = (g.wait(), x.returncode)
            elif rawxz:
                x = subprocess.run(["xz", "-6", "-T1", "-c", str(p)], stdout=fo)
                rc = (0, x.returncode)
            else:
                x = subprocess.run(["gzip", "-6", "-n", "-c", str(p)], stdout=fo)
                rc = (0, x.returncode)
        posted = None
        for L in REG.read_text().splitlines():          # 6. verify against the posted raw sha, read back from the register
            d = json.loads(L)
            if d["path"] == rec["path"] and d["time"] == rec["time"] and d["stored_sha256"] == s_before:
                posted = d["raw_sha256"]
        test = subprocess.run(["xz" if (xz_mode or rawxz) else "gzip", "-t", str(tmp)]).returncode
        back, back_n = sha_cmd(["xz" if (xz_mode or rawxz) else "gzip", "-dc", str(tmp)])
        if rc != (0, 0) or test != 0 or posted is None or back != posted or back_n != raw_n:
            tmp.unlink(missing_ok=True)
            print(f"{now()} MISMATCH, kept original {p}: rc {rc} test {test} posted {posted and posted[:16]} back {back[:16]} "
                  f"bytes {back_n} vs {raw_n}", flush=True)
            continue
        if sha_file(p) != s_before:
            tmp.unlink(missing_ok=True)
            print(f"{now()} original changed during repack, kept {p}", flush=True)
            continue
        os.replace(tmp, final)                          # 7. only now does the original go
        p.unlink()
        b, s_after = final.stat().st_size, sha_file(final)
        vcmd = ("xz -dc " if (xz_mode or rawxz) else "gunzip -c ") + str(final.relative_to(W)) + " | sha256sum"
        cls_txt = ("; ".join(f"{c}: {h}" for c, h in cls) if cls else "none")
        line = (f"{now()} | REPACKED {mode.upper()} | {p.relative_to(W)} -> {final.relative_to(W)} | stored sha256 {s_before} -> {s_after} "
                f"| raw sha256 {raw_sha} ({raw_n} B; verified by decompression against the posted raw sha, runs/deck_raw_sha_v352.jsonl) "
                f"| {a} -> {b} B ({(a - b) / 1e6:.2f} MB saved) | " + ("gzip -dc | xz -6 -T1" if xz_mode else ("xz -6 -T1" if rawxz else "gzip -6 -n"))
                + f", nice {os.nice(0)}, 1 thread, {time.time() - t1:.0f} s | "
                + f"verify: {vcmd} = raw sha256 {raw_sha} | cite hits (lead 19:53:27Z (3)): {len(cls)}: {cls_txt} | "
                + ("lead 19:53:27Z (3)(a) (js5b source deck gzipped after the stage re-install to the gunzip stream, 46df0c92de3f5f7e; cite check right before the file)" if mode == "a"
                   else "lead 19:53:27Z (3)(b) (tb352g / tb352h decks, X1 / X2 procedure, queued soaks checked; cite check right before the file)" if mode == "tb"
                   else "lead 20:44:07Z (3) (own finished J-FWD runs' raw decks -> xz, X1 / X2 procedure, queue_A lines 4 / 26 commented 20:44:45Z; cite check right before the file)" if mode == "j3"
                   else "lead 18:50:09Z (X1 / X2 adopted; cite check right before the file)" if mode in ("x1", "x2")
                   else "lead 18:50:09Z (2) (G: the js5b deck gzipped once the .sta shows step 1; cite check right before the file)" if mode == "g"
                   else "lead 18:04:32Z (P7 / P2 adopted)" + ("; cite check right before the file" if percite else "")))
        with open(LOG, "a") as f:                       # 8. one REPACKED line per file
            f.write(line + "\n")
        print(f"{now()} repacked {p.relative_to(W)} -> {final.name}: {a / 1e6:.2f} -> {b / 1e6:.2f} MB, sha16 {s_before[:16]} -> "
              f"{s_after[:16]}, raw {raw_sha[:16]} verified", flush=True)
        done += 1
    print(f"{now()} repack_deck_v352 {mode}: repacked {done} of {len(cand)} files", flush=True)
    return 0


if __name__ == "__main__":
    kw = dict(a.split("=", 1) for a in sys.argv[2:] if "=" in a)
    sys.exit(main(sys.argv[1], [r for r in kw.get("only", "").split(",") if r] or None, kw.get("dry", "0") == "1",
                  kw.get("percite", "0") == "1"))

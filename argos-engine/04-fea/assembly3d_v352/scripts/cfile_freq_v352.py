"""FREQUENCY=1000 re-test (TO-VERIFY 2) and the stream-built restricted js5b deck (fea3d, written 2026-10-20T20:01:11Z (date -u)).

Lead 19:53:27Z (2): "RULED: FREQUENCY=1000 on js5b's output cards, ONLY after a re-test PASS ... Re-test (TO-VERIFY 2, seconds, your
scratch, nice >= 10, 1 thread, delete your scratch after): a small deck carrying the same output cards js5b will carry (*NODE FILE,
*EL FILE, *CONTACT FILE with NSET=<set>), at least two steps, one forced to 2 or more increments (for example a fixed increment of half
the step).  Run it once with FREQUENCY=1000 and once without.  PASS needs all four:
 a. with FREQUENCY: exactly one frd block per step, written at the step end (check the 1PSTEP increment numbers);
 b. each of those blocks equals, value for value, the last-increment block of the same step in the run without FREQUENCY, for every
    output variable including the contact block;
 c. the contact output holds only the NSET nodes in both runs;
 d. no FREQUENCY or NSET warning in .dat / .sta / stdout."
Lead 20:00:17Z: one-off exception to 'at most one ccx of yours' for this test only: beside (b1), 1 thread, nice 19, prlimit 1 GB, own
scratch (deleted after), 60 s wall maximum (own test PID killed on overrun), combined ccx RSS <= 9 GB; hold if (b1)'s RSS > 7.5 GB at the
start.

Test model: the TO-VERIFY 1 model (cfile_nset_v352: base block A 4 x 4 x 1 mm, blocks B and C 1 x 3 x 1 mm on its top, C3D10, two
*CONTACT PAIR, TYPE=SURFACE TO SURFACE, linear penalty 5e5, *CLEARANCE 0.004 on the C pair, mu 0; N_CFACE generated from the deck's own
pairs) with js5b's step layout and output cards: SEAT (no field output) and three output steps S2 (*STATIC 1.0: one increment), S3
(*STATIC, DIRECT 0.5: two increments), S4 (*STATIC, DIRECT 0.25: four increments).  Every step: *NODE PRINT, NSET=N_REF / U, RF (as
js5b; no FREQUENCY on it).  Output steps: *NODE FILE / U, *EL FILE / S, *CONTACT FILE, NSET=N_CFACE / CDIS, CSTR.  The 'freq' deck adds
', FREQUENCY=1000' to those three card lines of every output step and nothing else (diff-checked).  Checks (a)-(d) as ruled, plus:
(pre) the 'nofreq' run wrote one block per increment (so the test exercises the multi-increment case); (e) the two runs' .dat and the
increment sequences of their .sta are identical (FREQUENCY on the file cards does not change the solution).

usage: cfile_freq_v352.py test                 build, run (beside (b1) under the 20:00:17Z conditions), check, delete the scratch
       cfile_freq_v352.py jsdeck SRC NEW [freq=1000] [out=DIR] [srcgz=PATH] [raw_sha=HEX64]
                                               restricted js5b deck from the gzip STREAM of jfwd/runs/SRC/SRC.inp.gz (lead 19:53:27Z
                                               (3)(a)2): the stream's full raw sha256 is checked first; N_CFACE from the stream's own
                                               pairs; ', NSET=N_CFACE' on every *CONTACT FILE line; with freq=N also ', FREQUENCY=N' on
                                               every *NODE FILE / *EL FILE / *CONTACT FILE line; diff-checked against the stream."""
from __future__ import annotations
import sys, os, re, json, time, gzip, hashlib, shutil, subprocess
from pathlib import Path

W = Path("/home/claude/work/fea3d")
sys.path.insert(0, str(W / "scripts"))
import cfile_nset_v352 as CN    # noqa: E402  (test geometry, N_CFACE generator, NSET writer; read-only use)

SCRATCH = Path("/tmp/claude-0/-home-claude/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/freqtest_v352")
OUT = W / "results" / "v352" / "cfile_freq_test_v352.json"
FREQ = 1000
WALL_S = 60
CAP_AS = 1 << 30                 # prlimit --as 1 GB
B1_HOLD_GB = 7.5


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


# ------------------------------------------------------------------------------------------------------------------- test decks
def test_decks():
    nA, eA = CN._block(0.0, 4.0, 0.0, 4.0, 0.0, 1.0, 4, 4, 2, 0, 0)
    nB, eB = CN._block(0.5, 1.5, 0.5, 3.5, 1.0, 2.0, 2, 6, 2, max(nA), max(eA))
    nC, eC = CN._block(2.5, 3.5, 0.5, 3.5, 1.0, 2.0, 2, 6, 2, max(nB), max(eB))
    nodes = {**nA, **nB, **nC}
    tol = 1e-9
    sA1 = CN._faces_on(eA, nodes, lambda x, y, z: abs(z - 1.0) < tol and x <= 2.0 + tol)
    sA2 = CN._faces_on(eA, nodes, lambda x, y, z: abs(z - 1.0) < tol and x >= 2.0 - tol)
    sB = CN._faces_on(eB, nodes, lambda x, y, z: abs(z - 1.0) < tol)
    sC = CN._faces_on(eC, nodes, lambda x, y, z: abs(z - 1.0) < tol)
    bot = [n for n in nA if abs(nA[n][2]) < tol]
    topB = sorted(n for n in nB if abs(nB[n][2] - 2.0) < tol)
    topC = sorted(n for n in nC if abs(nC[n][2] - 2.0) < tol)
    L = ["*HEADING", "fea3d cfile_freq_v352 test deck (lead 19:53:27Z (2), TO-VERIFY 2): FREQUENCY=1000 on js5b's output cards",
         "*NODE, NSET=NALL"]
    L += [f"{n}, {x:.6f}, {y:.6f}, {z:.6f}" for n, (x, y, z) in sorted(nodes.items())]
    for nm, els in (("E_A", eA), ("E_B", eB), ("E_C", eC)):
        L.append(f"*ELEMENT, TYPE=C3D10, ELSET={nm}")
        L += [", ".join(str(v) for v in [e] + c) for e, c in sorted(els.items())]
    L += ["*MATERIAL, NAME=AL", "*ELASTIC", "70000.0, 0.33", "*EXPANSION, ZERO=293.15", "2.3e-05",
          "*SOLID SECTION, ELSET=E_A, MATERIAL=AL", "*SOLID SECTION, ELSET=E_B, MATERIAL=AL", "*SOLID SECTION, ELSET=E_C, MATERIAL=AL"]
    L += CN.nset_lines("N_ABOT", sorted(bot)) + CN.nset_lines("N_BTOP", topB) + CN.nset_lines("N_CTOP", topC) + ["*NSET, NSET=N_REF", str(topB[0])]
    for nm, fl in (("S_B_S", sB), ("S_A_M1", sA1), ("S_C_S", sC), ("S_A_M2", sA2)):
        L.append(f"*SURFACE, NAME={nm}, TYPE=ELEMENT")
        L += [f"{e}, S{k}" for e, k in fl]
    L += ["*CONTACT PAIR, INTERACTION=SI, TYPE=SURFACE TO SURFACE", "S_B_S, S_A_M1",
          "*CONTACT PAIR, INTERACTION=SI, TYPE=SURFACE TO SURFACE", "S_C_S, S_A_M2",
          "*CLEARANCE, MASTER=S_A_M2, SLAVE=S_C_S, VALUE=0.004",
          "*SURFACE INTERACTION, NAME=SI", "*SURFACE BEHAVIOR, PRESSURE-OVERCLOSURE=LINEAR", "5.000e+05",
          "*INITIAL CONDITIONS, TYPE=TEMPERATURE", "NALL, 293.15"]
    steps = [("SEAT", "*STATIC", "1.0, 1.0, 1e-6, 1.0", -0.001, -0.001, 293.15, False),
             ("S2", "*STATIC", "1.0, 1.0, 1e-6, 1.0", -0.003, -0.003, 313.15, True),
             ("S3", "*STATIC, DIRECT", "0.5, 1.0", -0.005, -0.008, 333.15, True),
             ("S4", "*STATIC, DIRECT", "0.25, 1.0", -0.006, -0.010, 353.15, True)]
    body = []
    for nm, kw, inc, dB, dC, T, out in steps:
        body += ["*STEP, INC=200", kw, inc, "*BOUNDARY" + ("" if nm == "SEAT" else ", OP=NEW"),
                 "N_ABOT, 1, 3", "N_BTOP, 1, 2", "N_CTOP, 1, 2", f"N_BTOP, 3, 3, {dB}", f"N_CTOP, 3, 3, {dC}",
                 "*TEMPERATURE", f"NALL, {T}", "*NODE PRINT, NSET=N_REF", "U, RF"]
        if out:
            body += ["@NODE_FILE@", "U", "@EL_FILE@", "S", "@CONTACT_FILE@", "CDIS, CSTR"]
        body += ["*END STEP"]
    SCRATCH.mkdir(parents=True, exist_ok=True)
    base = "\n".join(L) + "\n"
    (SCRATCH / "nset_probe.inp").write_text(base + "\n".join(b.replace("@NODE_FILE@", "*NODE FILE").replace("@EL_FILE@", "*EL FILE")
                                                                  .replace("@CONTACT_FILE@", "*CONTACT FILE") for b in body) + "\n")
    ids, rep = CN.contact_face_nodes(SCRATCH / "nset_probe.inp")
    (SCRATCH / "nset_probe.inp").unlink()
    decks = {}
    for k, fq in (("nofreq", ""), ("freq", f", FREQUENCY={FREQ}")):
        b2 = [x.replace("@NODE_FILE@", "*NODE FILE" + fq).replace("@EL_FILE@", "*EL FILE" + fq)
              .replace("@CONTACT_FILE@", "*CONTACT FILE, NSET=N_CFACE" + fq) for x in body]
        txt = "\n".join(L + CN.nset_lines("N_CFACE", ids) + b2) + "\n"
        (SCRATCH / k).mkdir(exist_ok=True)
        (SCRATCH / k / "t.inp").write_text(txt)
        decks[k] = txt.split("\n")
    a, b = decks["nofreq"], decks["freq"]
    changed = [(x, y) for x, y in zip(a, b) if x != y]
    diff_ok = (len(a) == len(b) and len(changed) == 9 and
               all(y == x + f", FREQUENCY={FREQ}" and x.split(",")[0] in ("*NODE FILE", "*EL FILE", "*CONTACT FILE") for x, y in changed))
    return {"n_nodes": len(nodes), "n_elements": len(eA) + len(eB) + len(eC), "n_cface": len(ids), "cface_ids": ids, "nset_report": rep,
            "deck_sha16": {k: sha16(SCRATCH / k / "t.inp") for k in decks}, "deck_bytes": {k: (SCRATCH / k / "t.inp").stat().st_size for k in decks},
            "diff_freq_vs_nofreq": {"ok": diff_ok, "lines_changed": len(changed), "changed": [f"{x} -> {y}" for x, y in changed]},
            "steps": [{"name": s[0], "static": s[1], "inc": s[2], "field_output": s[6]} for s in steps]}


# ------------------------------------------------------------------------------------------------------------------- run
def ccx_list():
    out = []
    for pid in subprocess.run(["pgrep", "-x", "ccx"], capture_output=True, text=True).stdout.split():
        rss = 0
        try:
            for line in open(f"/proc/{pid}/status"):
                if line.startswith("VmRSS:"):
                    rss = int(line.split()[1])
            args = open(f"/proc/{pid}/cmdline").read().replace("\0", " ").strip()
            cwd = os.readlink(f"/proc/{pid}/cwd")
        except OSError:
            continue
        out.append({"pid": int(pid), "rss_GB": round(rss / 1024 / 1024, 3), "args": args, "cwd": cwd})
    return out


def run_one(k):
    d = SCRATCH / k
    pre = ccx_list()
    b1 = [p for p in pre if "seat_s9L12_mu02A" in p["args"]]
    others = [p for p in pre if p not in b1]
    if others:
        return {"held": f"another ccx runs: {others}", "pre": pre}
    if b1 and b1[0]["rss_GB"] > B1_HOLD_GB:
        return {"held": f"(b1) RSS {b1[0]['rss_GB']} GB > {B1_HOLD_GB} GB", "pre": pre}
    if sum(p["rss_GB"] for p in pre) + CAP_AS / 2 ** 30 > 9.0:
        return {"held": "combined RSS + 1.0 GB cap > 9 GB", "pre": pre}
    env = dict(os.environ, OMP_NUM_THREADS="1", CCX_NPROC_EQUATION_SOLVER="1", CCX_NPROC_STIFFNESS="1", CCX_NPROC_RESULTS="1")
    t0 = time.time()
    with open(d / "t.log", "w") as out:
        p = subprocess.Popen(["prlimit", f"--as={CAP_AS}", "nice", "-n", "19", "ccx", "-i", "t"], cwd=str(d), env=env, stdout=out,
                             stderr=subprocess.STDOUT)
        peak, comm, killed = 0, None, None
        while p.poll() is None:
            try:
                comm = open(f"/proc/{p.pid}/comm").read().strip()
                for line in open(f"/proc/{p.pid}/status"):
                    if line.startswith("VmHWM:"):
                        peak = max(peak, int(line.split()[1]))
            except OSError:
                pass
            if time.time() - t0 > WALL_S:
                killed = f"wall {WALL_S} s exceeded: own test PID {p.pid} killed"
                p.kill()
                break
            time.sleep(0.1)
        p.wait()
    return {"pid": p.pid, "comm": comm, "returncode": p.returncode, "seconds": round(time.time() - t0, 2), "peak_rss_GB": round(peak / 2 ** 20, 4),
            "killed": killed, "start_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0)), "pre": pre,
            "limits": "prlimit --as 1 GiB, nice 19, OMP_NUM_THREADS = CCX_NPROC_* = 1"}


# ------------------------------------------------------------------------------------------------------------------- frd / sta / dat
def frd_blocks(p):
    """[{name, pstep: (output counter, increment, step), hdr100, time, n_hdr, comps, records {node: line}}] in file order."""
    out, cur, pstep, hdr = [], None, None, None
    with open(p, errors="ignore") as f:
        for L in f:
            if L.startswith("    1PSTEP"):
                t = L.split()
                pstep = (int(t[1]), int(t[2]), int(t[3]))
            elif L.startswith("  100C"):
                hdr = L.rstrip("\n")
            elif L.startswith(" -4"):
                cur = {"name": L[5:13].strip(), "pstep": pstep, "hdr100": hdr, "time": float(hdr[12:24]) if hdr else None,
                       "n_hdr": int(hdr[24:36]) if hdr else None, "comps": [], "records": {}}
                out.append(cur)
                pstep, hdr = None, None
            elif L.startswith(" -5") and cur is not None:
                cur["comps"].append(L[5:13].strip())
            elif L.startswith(" -1") and cur is not None:
                cur["records"][int(L[3:13])] = L.rstrip("\n")
            elif L.startswith(" -3"):
                cur = None
    return out


def sta_incs(p):
    """{step: [increment numbers]} from the .sta table (STEP INC ATT ITRS TOT TIME STEP TIME INC TIME)."""
    out = {}
    for L in Path(p).read_text(errors="ignore").splitlines():
        m = re.match(r"^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)", L)
        if m:
            out.setdefault(int(m.group(1)), []).append(int(m.group(2)))
    return out


def msgs(d):
    res = {}
    for nm in ("t.dat", "t.sta", "t.log"):
        q = d / nm
        txt = q.read_text(errors="ignore") if q.exists() else ""
        res[nm] = [L.strip()[:200] for L in txt.splitlines() if "WARNING" in L.upper() or "ERROR" in L.upper()][:40]
    return res


def check(info, runs):
    S = set(info["cface_ids"])
    out_steps = [i + 1 for i, s in enumerate(info["steps"]) if s["field_output"]]
    B = {k: frd_blocks(SCRATCH / k / "t.frd") if (SCRATCH / k / "t.frd").exists() else [] for k in ("nofreq", "freq")}
    # every output variable ccx writes (20:06Z: the first execution listed DISP / STRESS / CONTACT only; ccx also writes the ERROR block
    # with S, in both runs): the names come from the run without FREQUENCY
    names = sorted({b["name"] for b in B["nofreq"]})
    assert "CONTACT" in names and "DISP" in names and "STRESS" in names, names
    sta = {k: sta_incs(SCRATCH / k / "t.sta") if (SCRATCH / k / "t.sta").exists() else {} for k in ("nofreq", "freq")}
    M = {k: msgs(SCRATCH / k) for k in ("nofreq", "freq")}
    r = {"rc0_both": all(runs[k].get("returncode") == 0 and not runs[k].get("killed") for k in runs)}
    tab = {k: [{"name": b["name"], "pstep_counter_inc_step": b["pstep"], "time": b["time"], "n_hdr": b["n_hdr"], "n_records": len(b["records"])}
               for b in B[k]] for k in B}
    # pre: the run without FREQUENCY wrote one block per increment of every output step (so the multi-increment case is exercised)
    pre_det = {}
    pre_ok = True
    for s in out_steps:
        incs = sta["nofreq"].get(s, [])
        for nm in names:
            got = sorted(b["pstep"][1] for b in B["nofreq"] if b["name"] == nm and b["pstep"] and b["pstep"][2] == s)
            pre_det[f"step {s} {nm}"] = {"sta_increments": incs, "frd_block_increments": got}
            pre_ok = pre_ok and bool(incs) and got == sorted(incs)
    multi = [s for s in out_steps if len(sta["nofreq"].get(s, [])) >= 2]
    r["pre"] = {"pass": bool(pre_ok and multi), "steps_with_2_or_more_increments": {s: len(sta["nofreq"].get(s, [])) for s in multi},
                "detail": pre_det}
    # (a) FREQUENCY run: exactly one block per output variable per output step, at the step's last increment (1PSTEP), none elsewhere
    a_det, a_ok = {}, True
    for s in out_steps:
        last_f = max(sta["freq"].get(s, [0]))
        last_n = max(sta["nofreq"].get(s, [0]))
        for nm in names:
            bl = [b for b in B["freq"] if b["name"] == nm and b["pstep"] and b["pstep"][2] == s]
            ok = len(bl) == 1 and bl[0]["pstep"][1] == last_f == last_n
            a_det[f"step {s} {nm}"] = {"n_blocks": len(bl), "pstep_increments": [b["pstep"][1] for b in bl], "sta_last_increment_freq": last_f,
                                       "sta_last_increment_nofreq": last_n, "time": [b["time"] for b in bl], "ok": ok}
            a_ok = a_ok and ok
    stray = [b["pstep"] for b in B["freq"] if not b["pstep"] or b["pstep"][2] not in out_steps or b["name"] not in names]
    r["a"] = {"pass": bool(a_ok and not stray and len(B["freq"]) == len(out_steps) * len(names)), "n_blocks_freq": len(B["freq"]),
              "expected": len(out_steps) * len(names), "stray_blocks": stray, "per_step": a_det}
    # (b) value for value against the last-increment block of the same step in the run without FREQUENCY
    b_det, b_ok = {}, True
    for s in out_steps:
        for nm in names:
            bf = [b for b in B["freq"] if b["name"] == nm and b["pstep"] and b["pstep"][2] == s]
            bn = [b for b in B["nofreq"] if b["name"] == nm and b["pstep"] and b["pstep"][2] == s]
            if not bf or not bn:
                b_det[f"step {s} {nm}"] = {"ok": False, "why": "block missing"}
                b_ok = False
                continue
            x, y = bf[-1], max(bn, key=lambda b: b["pstep"][1])
            same_rec = x["records"] == y["records"]
            diff = [n for n in set(x["records"]) | set(y["records"]) if x["records"].get(n) != y["records"].get(n)]
            ok = same_rec and x["comps"] == y["comps"] and x["time"] == y["time"] and x["n_hdr"] == y["n_hdr"]
            b_det[f"step {s} {nm}"] = {"ok": ok, "n_records": len(x["records"]), "n_differ": len(diff), "first_differ": diff[:5],
                                       "components": x["comps"], "time": [x["time"], y["time"]], "nofreq_increment": y["pstep"][1]}
            b_ok = b_ok and ok
    r["b"] = {"pass": bool(b_ok), "per_step": b_det}
    # (c) contact output: only the NSET nodes, in both runs
    c_det, c_ok = {}, True
    for k in B:
        cb = [b for b in B[k] if b["name"] == "CONTACT"]
        rows = [{"step_inc": b["pstep"][1:], "n_records": len(b["records"]), "n_hdr": b["n_hdr"], "subset_of_set": set(b["records"]) <= S,
                 "equals_set": set(b["records"]) == S} for b in cb]
        c_det[k] = rows
        c_ok = c_ok and bool(cb) and all(x["subset_of_set"] and x["n_hdr"] == x["n_records"] for x in rows)
    r["c"] = {"pass": bool(c_ok), "n_cface": len(S), "per_run": c_det}
    # (d) no FREQUENCY / NSET warning (and no error) in .dat / .sta / stdout
    flagged = {k: [m for v in M[k].values() for m in v if re.search(r"FREQUENC|NSET|ERROR", m, re.I)] for k in M}
    r["d"] = {"pass": not any(flagged.values()), "flagged": flagged, "all_warning_or_error_lines": M}
    # (e) solution unchanged by FREQUENCY on the file cards: .dat identical, .sta increment sequences identical
    dn, df = ((SCRATCH / k / "t.dat").read_text(errors="ignore").splitlines() for k in ("nofreq", "freq"))
    dat_same = dn == df
    import difflib
    dd = [x for x in difflib.unified_diff(dn, df, "nofreq/t.dat", "freq/t.dat", n=1, lineterm="")][:40]
    r["e_info"] = {"dat_identical": dat_same, "dat_lines": [len(dn), len(df)], "dat_diff_first_lines": dd,
                   "sta_increments_identical": sta["nofreq"] == sta["freq"], "sta_increments": sta["freq"], "block_names": names}
    r["blocks"] = tab
    r["verdict"] = "PASS" if (r["rc0_both"] and r["pre"]["pass"] and r["a"]["pass"] and r["b"]["pass"] and r["c"]["pass"] and r["d"]["pass"]) else "FAIL"
    return r


def test():
    t0 = time.time()
    if SCRATCH.exists():
        shutil.rmtree(SCRATCH)
    info = test_decks()
    if not info["diff_freq_vs_nofreq"]["ok"]:
        raise SystemExit(f"test decks differ beyond the FREQUENCY cards: {info['diff_freq_vs_nofreq']}")
    runs = {}
    for k in ("nofreq", "freq"):
        runs[k] = run_one(k)
        print(f"{now()} TOVERIFY2 run {k}: {json.dumps({x: runs[k].get(x) for x in ('held', 'returncode', 'seconds', 'peak_rss_GB', 'killed', 'comm')})}",
              flush=True)
        if runs[k].get("held"):
            r = {"verdict": "HELD", "runs": runs}
            print(f"{now()} TOVERIFY2 HELD: {runs[k]['held']} (tell the lead)", flush=True)
            shutil.rmtree(SCRATCH)
            return r
    r = check(info, runs)
    info.pop("cface_ids")
    out = {"id": "cfile_freq_test_v352", "date_utc": now(), "doc": __doc__.split("usage:")[0].strip(),
           "evidence": "SIM (two ccx 2.21 test runs) + DERIVED (frd / sta / dat comparison)", "test_decks": info, "runs": runs, **r,
           "scratch": str(SCRATCH), "scratch_deleted": None, "script_sha16": sha16(Path(__file__))}
    shutil.rmtree(SCRATCH)
    out["scratch_deleted"] = not SCRATCH.exists()
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"{now()} TOVERIFY2 FREQUENCY test {out['verdict']}: rc0 {r['rc0_both']} pre {r['pre']['pass']} "
          f"({r['pre']['steps_with_2_or_more_increments']}) (a) {r['a']['pass']} ({r['a']['n_blocks_freq']} blocks of {r['a']['expected']}) "
          f"(b) {r['b']['pass']} (c) {r['c']['pass']} (d) {r['d']['pass']} (e) {r['e_info']['dat_identical']}/{r['e_info']['sta_increments_identical']}; "
          f"scratch deleted {out['scratch_deleted']}; -> {OUT.relative_to(W)} {sha16(OUT)} ({time.time() - t0:.0f} s)", flush=True)
    return out


# ------------------------------------------------------------------------------------------------------------------- js5b deck from the stream
def jsdeck(src, new, freq=None, out_dir=None, srcgz=None, raw_sha=None):
    """Restricted (+ FREQUENCY) copy of a J-FWD deck built from the gzip stream of its source; nothing is read from the raw path."""
    sd = W / "jfwd" / "runs" / src
    gz = Path(srcgz) if srcgz else sd / f"{src}.inp.gz"
    nd = Path(out_dir) if out_dir else W / "jfwd" / "runs" / new
    h, chunks = hashlib.sha256(), []
    with gzip.open(gz, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
            chunks.append(b)
    src_raw = h.hexdigest()
    if raw_sha and src_raw != raw_sha:
        raise SystemExit(f"STOP: source stream raw sha256 {src_raw} != {raw_sha}")
    text = b"".join(chunks).decode()
    del chunks
    lines = text.split("\n")
    # N_CFACE from the stream's own pairs (CN.contact_face_nodes reads a path: give it the stream text through a scratch-free shim)
    ids, rep = _cface_from_lines(lines)
    first_step = next(i for i, L in enumerate(lines) if L.upper().startswith("*STEP"))
    nsl = CN.nset_lines("N_CFACE", ids)
    out = lines[:first_step] + nsl + lines[first_step:]
    n_cf = n_fq = 0
    fq = f", FREQUENCY={int(freq)}" if freq else ""
    for i, L in enumerate(out):
        u = L.strip().upper()
        if u == "*CONTACT FILE":
            out[i] = "*CONTACT FILE, NSET=N_CFACE" + fq
            n_cf += 1
            n_fq += bool(fq)
        elif fq and u in ("*NODE FILE", "*EL FILE"):
            out[i] = L.strip() + fq
            n_fq += 1
    nd.mkdir(parents=True, exist_ok=bool(out_dir))
    np_ = nd / f"{new}.inp"
    np_.write_text("\n".join(out))
    # diff check against the stream: the new deck = the stream + the NSET block + the changed card lines, nothing else
    b = np_.read_text().split("\n")
    rest = b[:first_step] + b[first_step + len(nsl):]
    changed = [i for i, (x, y) in enumerate(zip(lines, rest)) if x != y]
    allowed = {"*CONTACT FILE": "*CONTACT FILE, NSET=N_CFACE" + fq}
    if fq:
        allowed.update({"*NODE FILE": "*NODE FILE" + fq, "*EL FILE": "*EL FILE" + fq})
    ok = (len(lines) == len(rest) and b[first_step:first_step + len(nsl)] == nsl
          and all(lines[i].strip().upper() in allowed and rest[i] == allowed[lines[i].strip().upper()] for i in changed)
          and not any(L.strip().upper() in allowed for L in rest))
    if not ok:
        raise SystemExit("STOP: diff check against the source stream failed")
    by_card = {}
    for i in changed:
        by_card[lines[i].strip().upper()] = by_card.get(lines[i].strip().upper(), 0) + 1
    meta = json.loads((sd / "meta.json").read_text())
    meta.update({"job": new, "deck_sha16": sha16(np_), "restricted_contact_output": {
        "source_job": src, "source_deck_sha16": src_raw[:16], "source_raw_sha256": src_raw, "source_read_as": f"gzip stream of {gz.name}",
        "nset": "N_CFACE", "n_cface": len(ids), "nset_report": rep, "contact_file_cards_changed": n_cf,
        "frequency": int(freq) if freq else None, "frequency_lines": n_fq, "lines_changed": len(changed), "lines_changed_by_card": by_card,
        "nset_lines_added": len(nsl),
        "rule": "lead 18:50:09Z (1) / 19:09:50Z: restricted contact output (results/v352/cfile_nset_test_v352.json)"
                + ("; lead 19:53:27Z (2): FREQUENCY on the output cards after the re-test PASS (results/v352/cfile_freq_test_v352.json)" if fq else "")
                + "; lead 19:53:27Z (3)(a)2: built from the gzip stream of the source deck",
        "built_utc": now()}})
    (nd / "meta.json").write_text(json.dumps(meta, indent=1))
    print(f"{now()} jsdeck {new}: N_CFACE {len(ids)} nodes, {n_cf} *CONTACT FILE cards, FREQUENCY on {n_fq} lines, {len(changed)} lines changed "
          f"{by_card}, deck {meta['deck_sha16']} ({np_.stat().st_size / 1e6:.2f} MB), source stream raw sha256 {src_raw}", flush=True)
    return meta


def _cface_from_lines(lines):
    """CN.contact_face_nodes on in-memory lines (it reads the deck with Path.read_text): same parser, no file written."""
    class _P:
        def __init__(self, t):
            self.t = t

        def read_text(self, errors=None):
            return self.t
    orig = CN.Path
    try:
        CN.Path = lambda _p: _P("\n".join(lines))
        return CN.contact_face_nodes("<stream>")
    finally:
        CN.Path = orig


if __name__ == "__main__":
    cmd = sys.argv[1]
    kw = dict(a.split("=", 1) for a in sys.argv[2:] if "=" in a)
    if cmd == "test":
        r = test()
        sys.exit(0 if r["verdict"] == "PASS" else 3)
    elif cmd == "jsdeck":
        pos = [a for a in sys.argv[2:] if "=" not in a]
        jsdeck(pos[0], pos[1], kw.get("freq"), kw.get("out"), kw.get("srcgz"), kw.get("raw_sha"))

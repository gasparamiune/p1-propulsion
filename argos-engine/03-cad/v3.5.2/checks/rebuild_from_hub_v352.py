"""Rebuild proof of the FINAL v3.5.2 03-cad set from the hub copy of the archive (lead 19:53:27Z item 3; rulings 20:04:32Z (a), (b1),
(c), 20:16:57Z G1-G4 and 20:30:00Z P1-P3).  Software check on the CAD files, not physical validation.  Mechanical, 2026-10-20, script
revision 3, record checks/rebuild_from_hub_v352_v2.json.  History: revision 1 (68a5158d9affb2cb) stopped at 20:02:17Z on the missing
src/calcs/hose_frame.py (not a result); revision 2 (f433fa517d4c4a5c) ran 20:24:17-20:25:13Z and wrote checks/rebuild_from_hub_v352_v1.json
(d3ce49e52e7f93b5, ALL_OK false: massprops /cg_iteration[0]/t_s run time, massdelta sha field, the two assembly STEP DATA sections, and two
classification flags), kept unchanged beside this record.
Revision 3 changes (lead 20:30:00Z): P1 massprops and massdelta are compared with exactly two JSON pointers masked, massprops
/cg_iteration[0]/t_s (run time written by the generator) and massdelta /files/v352/sha256_16 (massdelta carries the massprops sha; each
side's value is asserted equal to its own massprops sha); every other field is asserted identical (order-preserving).  P2 the two assembly
STEP files are compared canonically: each DATA entity is hashed (sha256) from its type and its non-reference parameters as written
(whitespace outside strings removed; no string carries a line break), with each #reference replaced by the referenced entity's hash
(Merkle); the multisets of entity hashes and the multisets of root entities (referenced by no entity) must be equal; the entity counts,
the first differing line and the entity types whose order differs are reported; a reference cycle, a dangling reference, or any hash in one
multiset and not the other is a failure.  P3 the module sitecustomize is classified as stdlib by its /usr/lib/python3.13 path (Debian
system-Python symlink; realpath noted); /root/.cache/ezdxf/font_manager_cache.json and /root/.config/ezdxf/ezdxf.ini are listed as tool
cache / config reads by ezdxf (imported by cadquery), not design inputs; everything else stays strict.

Scratch copy (a new empty folder, deleted in a finally block on every exit path):
  <scratch>/03-cad/v3.5.2/src            = the hub 03-cad/v3.5.2/src, every file sha256-checked against the hub MANIFEST
                                           + src/engmat.py = engmat v1.7 (d41807bf675951b1, ruled (A))
                                           + src/calcs/hose_frame.py, src/calcs/hardware_v351.py = byte copies of the hub 03-cad/calcs/
                                             files (01813094106c7778, c2bed292cd7dc2d7, ruled (a))
  <scratch>/03-cad/v3.5.2/massprops_v3.5.1.json = copy of the hub 03-cad/v3.5.1/massprops_v3.5.1.json (488b47f9d55ff91b, named input;
                                           read by make_all's mass stage and by calcs/mass_delta_v352.py)
  <scratch>/03-cad/interfaces/mechanical.json = copy of the hub 03-cad/v3.5.2/history/mechanical.json.e4d3e7c9df529171 (interface v2.1,
                                           ruled (b1): the mass stage's comparison input at HERE.parents[1]/interfaces/mechanical.json)
  <scratch>/iface_snapshot/               = empty; ENGINE_IFACE_SNAPSHOT (G2: config.py writes its interface snapshot copies there)
Named config inputs (G1), read in place from the hub (package root /home/claude/work/shared-fallback/engine), sha-checked before and
after the build; any other hub file read in place fails the check:
  interfaces/ENGINE-BASELINE-v0.json v0 508faa652ccbd539, interfaces/combustion.json v2.4b fd3a7da6d27c7c66, interfaces/gnc.json v3.1
  4f3209323b0e0ed4, interfaces/electronics.json v3 38bf149f368c1d4c, 02-combustion/data/v2/nozzle_contour_v2.csv b00aed4fab46bb6f.
Build: MAKE_ALL_CAD=v352 make_all.py --stages build,parts,assembly,glb,placements,bom,mass --out <scratch set>, then
src/calcs/mass_delta_v352.py, in one child process (python -I -B, nice 19, no ccx) under an audit hook that records every file opened from
Python and sys.monitoring line coverage of the scratch src (one LINE event per location, then disabled); the imported modules are listed
from sys.modules after the run.  The parent polls free space and the scratch size every 2 s and kills only its own child below 2.20 GiB
free or above 100 MB of scratch.
Static scan (lead 20:04:32Z (c)): every site where the src code builds a path that can leave src/ (Path .parent/.parents, '..', __file__,
absolute literals, os.path / Path / open / glob / exists calls, environment reads, sys.path edits, imports at module and function level) is
listed with its file, line, enclosing function and whether the run executed it; the sites classified on / off the v3.5.2 build path in the
20:15:43Z report are checked against the coverage.
Comparison against the hub MANIFEST (a94851ae4dc22cc4): STL byte-identical; part STEP DATA sections identical (header timestamps excepted;
the OCC translator counter normalised as in publish_v352.py); the two assembly STEP files by the canonical comparison (P2); BOM json / csv
byte-identical; massprops and massdelta as P1; GLB byte-identical; assembly/placements_v3.5.2.json byte-identical on the same UTC day (it
embeds the UTC date; run before 24:00Z); assembly/assembly_manifest_v3.5.2.json byte-identical; the other build outputs (checks/*.json)
compared with run-time fields and STEP-file shas masked (stated).  Any difference is reported, never fixed here.
Claim written only on PASS (lead 20:30:00Z, exact wording): "the v3.5.2 set rebuilds from the hub copy of the archive with the five named
inputs (shas checked): STL, part STEP DATA, BOM, GLB, placements and manifests byte-identical; massprops identical except the run-time field
/cg_iteration[0]/t_s (massdelta follows); the two assembly STEP files identical up to entity order and numbering (OCCT colour/style writer
order)"; it is not a claim about a fresh GitHub checkout (not tested).
Usage: rebuild_from_hub_v352.py            (parent)
       <runner> --child <scratch>          (internal: the child, written into the scratch folder by the parent)"""
import ast, hashlib, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

HUB = Path("/home/claude/work/shared-fallback/engine")
H = HUB / "03-cad/v3.5.2"
MF_SHA = "a94851ae4dc22cc4"
ENGMAT = Path("/home/claude/work/mechanical/v352/engine/04-fea/src/engmat.py")
ENGMAT_SHA = "d41807bf675951b1"
ENGMAT16 = HUB / "04-fea/src/engmat.py"
ENGMAT16_SHA = "46ba163b864c7fc5"
ADD_A = {"src/calcs/hose_frame.py": (HUB / "03-cad/calcs/hose_frame.py", "01813094106c7778"),
         "src/calcs/hardware_v351.py": (HUB / "03-cad/calcs/hardware_v351.py", "c2bed292cd7dc2d7")}
M351 = HUB / "03-cad/v3.5.1/massprops_v3.5.1.json"
M351_SHA = "488b47f9d55ff91b"
MJ21 = H / "history/mechanical.json.e4d3e7c9df529171"
MJ21_SHA = "e4d3e7c9df529171"
NAMED = {"interfaces/ENGINE-BASELINE-v0.json": ("v0", "508faa652ccbd539"),
         "interfaces/combustion.json": ("v2.4b", "fd3a7da6d27c7c66"),
         "interfaces/gnc.json": ("v3.1", "4f3209323b0e0ed4"),
         "interfaces/electronics.json": ("v3", "38bf149f368c1d4c"),
         "02-combustion/data/v2/nozzle_contour_v2.csv": ("(Combustion data v2)", "b00aed4fab46bb6f")}
SCR = Path("/tmp/claude-0/-home-claude/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rebuild352_r3")
PY = "/opt/engine-venv/bin/python"
OUT = Path("/home/claude/work/mechanical/v352/checks/rebuild_from_hub_v352_v2.json")
REC_V1 = Path("/home/claude/work/mechanical/v352/checks/rebuild_from_hub_v352_v1.json")
REC_V1_SHA = "d3ce49e52e7f93b5"
LIM = int(2.20 * 2 ** 30)
SCR_MAX = 100e6
STAGES = "build,parts,assembly,glb,placements,bom,mass"
DEV = "/home/claude/work/mechanical"
CLAIM = ("the v3.5.2 set rebuilds from the hub copy of the archive with the five named inputs (shas checked): STL, part STEP DATA, BOM, GLB, "
         "placements and manifests byte-identical; massprops identical except the run-time field /cg_iteration[0]/t_s (massdelta follows); "
         "the two assembly STEP files identical up to entity order and numbering (OCCT colour/style writer order)")
RULES = ("lead 19:53:27Z item 3: STL byte-identical; STEP DATA sections identical (header timestamps excepted); BOM json / csv byte-identical; "
         "GLB byte-identical; lead 20:16:57Z item 3: placements_v3.5.2.json byte-identical on the same UTC day; lead 20:30:00Z P1: massprops "
         "and massdelta compared with exactly two JSON pointers masked (massprops /cg_iteration[0]/t_s, run time written by the generator; "
         "massdelta /files/v352/sha256_16, the massprops sha it carries), every other field identical; P2: the two assembly STEP files by "
         "the Merkle entity-hash multisets and root multisets (identical up to entity order and numbering); P3: sitecustomize by its stdlib "
         "path, the two ezdxf cache / config files as tool reads")
MASK_PTR = {"massprops_v3.5.2.json": "/cg_iteration/0/t_s", "massdelta_v3.5.2_vs_v3.5.1.json": "/files/v352/sha256_16"}
ASM_STEP = ("assembly/ENGINE_v3.5.2_neutral.step", "assembly/ENGINE_v3.5.2_stop045.step")
EZDXF_TOOL_READS = ("/root/.cache/ezdxf/font_manager_cache.json", "/root/.config/ezdxf/ezdxf.ini")

# sites classified in the 20:15:43Z report: (file, line, what, expected executed in the v3.5.2 build)
CLASSIFIED = [
    ("config.py", 18, "FALLBACK_ROOT absolute hub path (named inputs G1)", True),
    ("config.py", 21, "INTERFACES = ENGINE_INTERFACES or <hub>/interfaces (G1)", True),
    ("config.py", 28, "SNAPSHOT = ENGINE_IFACE_SNAPSHOT (G2)", True),
    ("config.py", 36, "_load reads the interface file in place (G1)", True),
    ("config.py", 40, "_load writes the snapshot copy (G2)", True),
    ("config.py", 71, "shared(): returns the hub path of the contour csv (G1)", True),
    ("layout.py", 24, "read_contour opens config.shared(path) (G1)", True),
    ("build.py", 17, "sys.path <03-cad>/04-fea/src (absent in the archive layout)", True),
    ("build.py", 20, "import engmat -> src/engmat.py (A)", True),
    ("make_all.py", 46, "sys.path <03-cad>/04-fea/src (absent in the archive layout)", True),
    ("make_all.py", 52, "import engmat -> src/engmat.py (A)", True),
    ("make_all.py", 57, "MAKE_ALL_CAD (named: v352)", True),
    ("make_all.py", 622, "BOM: src/data/hardware_v352.json (in the set)", True),
    ("make_all.py", 716, "mass: src/data/hardware_v352.json (in the set)", True),
    ("make_all.py", 745, "mass: CAD/massprops_v3.5.json path (absent; not needed)", True),
    ("make_all.py", 747, "mass: massprops_v3.5.json read (branch not taken)", False),
    ("make_all.py", 756, "mass: CAD/massprops_v3.5.1.json read (named input, G3)", True),
    ("make_all.py", 764, "mass: HERE.parents[1]/interfaces/mechanical.json read (b1)", True),
    ("parts_feed.py", 269, "src/data/feed_plan_v341.json read (in the set)", True),
    ("parts_feed.py", 712, "import hose_frame from src/calcs (a)", True),
    ("parts_inlet.py", 14, "from calcs.inlet_e1m import E1M (in the set)", True),
    ("calcs/mass_delta_v352.py", 31, "massprops_v3.5.1.json + massprops_v3.5.2.json read", True),
    ("config.py", 77, "mount branch open (ENGINE_USE_FALLBACK=0 only)", False),
    ("config.py", 469, "relay() body (relay inactive: combustion.json v2.4b)", False),
    ("build.py", 39, "import parts_misc (branch not taken)", False),
    ("make_all.py", 113, "build_fingerprint (checks stage)", False),
    ("make_all.py", 913, "MAKE_ALL_DRAW_PN (drawings stage)", False),
    ("make_all.py", 934, "stage_readme sources (readme stage)", False),
    ("layout.py", 139, "sys.path '.' under __main__", False),
    ("tvc_kinematics.py", 176, "sys.path '.' under __main__", False),
    ("parts_feed.py", 825, "--freeze-plan under __main__", False),
    ("parts_feed.py", 836, "--freeze-plan write under __main__", False),
    ("viz.py", 17, "import engmat in viz (viz never imported)", False),
    ("calcs/inlet_e1m.py", 60, "stations() sys.path (calc main only)", False),
    ("calcs/inlet_e1m.py", 156, "COMB_MIRROR dev-tree read (main only)", False),
    ("calcs/hardware_v352.py", 24, "dev-tree input (module not imported by the build, G4)", False),
    ("calcs/hardware_v352.py", 51, "import hardware_v351 (module not imported by the build)", False),
    ("calcs/hardware_v351.py", 27, "sys.path <03-cad>/04-fea/src for engmat (module not imported by the build, G4)", False),
    ("calcs/write_mechanical_json_v352.py", 15, "hub path of the mechanical.json writer (not a build step)", False),
    ("calcs/hose_frame.py", 197, "hose_frame main() write", False),
    ("engmat.py", 545, "engmat __main__ export", False),
]

CHILD = r'''
import json, os, sys, runpy, sysconfig, traceback
root = sys.argv[2]
S = os.path.join(root, "03-cad", "v3.5.2")
src = os.path.join(S, "src")
opens = []
def hook(ev, args):
    if ev == "open" and args and not isinstance(args[0], int):
        try:
            p = os.fsdecode(args[0])
        except Exception:
            p = repr(args[0])
        opens.append([p, "" if len(args) < 2 or args[1] is None else str(args[1]), int(args[2]) if len(args) > 2 and isinstance(args[2], int) else -1])
sys.addaudithook(hook)
mon = sys.monitoring
TOOL = mon.COVERAGE_ID
mon.use_tool_id(TOOL, "rebuild-proof-coverage")
pref = tuple(sorted({src.rstrip("/") + "/", os.path.realpath(src).rstrip("/") + "/"}))
cov = set()
def on_line(code, line):
    f = code.co_filename
    if f.startswith(pref):
        for q in pref:
            if f.startswith(q):
                cov.add((f[len(q):], line))
                break
    return mon.DISABLE
mon.register_callback(TOOL, mon.events.LINE, on_line)
mon.set_events(TOOL, mon.events.LINE)
rc = {}
def run(path, argv, key):
    sys.argv = argv
    try:
        runpy.run_path(path, run_name="__main__")
        rc[key] = 0
    except SystemExit as e:
        rc[key] = e.code if isinstance(e.code, int) else (0 if e.code is None else str(e.code))
    except BaseException as e:
        rc[key] = "EXCEPTION " + type(e).__name__ + ": " + str(e)[:300]
        rc[key + "_traceback"] = traceback.format_exc()[-3000:]
run(os.path.join(src, "make_all.py"), [os.path.join(src, "make_all.py"), "--stages", "%s", "--out", S], "make_all")
if rc.get("make_all") == 0:
    run(os.path.join(src, "calcs", "mass_delta_v352.py"), [os.path.join(src, "calcs", "mass_delta_v352.py")], "mass_delta")
mon.set_events(TOOL, 0)
mods = sorted({(os.path.abspath(m.__file__), os.path.realpath(m.__file__), n) for n, m in list(sys.modules.items())
               if isinstance(getattr(m, "__file__", None), str)})
paths = {k: os.path.realpath(v) for k, v in sysconfig.get_paths().items()}
rec = {"rc": rc, "modules": mods, "opens": sorted({tuple(o) for o in opens}), "sysconfig_paths": paths, "sys_path": sys.path,
       "executable": sys.executable, "flags": {"isolated": sys.flags.isolated, "dont_write_bytecode": sys.flags.dont_write_bytecode},
       "coverage": sorted(cov)}
with open(os.path.join(root, "child_record.json"), "w") as f:
    json.dump(rec, f)
''' % STAGES

MATS = r'''
import json, runpy, sys
g = runpy.run_path(sys.argv[1], run_name="engmat_cmp")
print(json.dumps({"version": g.get("MATERIALS_VERSION"), "materials": g["MATERIALS"]}, sort_keys=True, default=str))
'''


def sha(p, n=64):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:n]


def free():
    s = os.statvfs("/home/claude")
    return s.f_bavail * s.f_frsize


def tree_bytes(p):
    n = 0
    for dp, dn, fn in os.walk(p):
        for x in fn:
            try:
                n += os.lstat(os.path.join(dp, x)).st_size
            except OSError:
                pass
    return n


def step_data(p):
    t = Path(p).read_text(errors="replace")
    return re.sub(r"Open CASCADE STEP translator [0-9.]+ [0-9]+", "OCC-TRANSLATOR", t[t.find("DATA;"):])


def step_header(p):
    t = Path(p).read_text(errors="replace")
    return t[:t.find("DATA;")]


ENT_RE = re.compile(r"'(?:[^']|'')*'|;")
TOK_RE = re.compile(r"'(?:[^']|'')*'|\s+|#(\d+)")
ID_RE = re.compile(r"\s*#(\d+)\s*=\s*(.*)\Z", re.S)
NAME_RE = re.compile(r"([A-Z_][A-Z0-9_]*)\(")


class CanonStop(Exception):
    pass


def step_entities(p):
    """DATA section of a STEP file -> (ids in file order, {id: (canonical text with \\x00 at each reference, [referenced ids])}, raw lines).
    Canonical text = the entity's type and parameters as written, whitespace outside strings removed (the writer wraps lines between
    tokens; no string in these files carries a line break, asserted)."""
    t = Path(p).read_text(encoding="ascii")
    i0 = t.find("DATA;")
    i1 = t.rfind("ENDSEC;")
    assert i0 > 0 and i1 > i0
    body = t[i0 + len("DATA;"):i1]
    order, ents, start = [], {}, 0
    for m in ENT_RE.finditer(body):
        if m.group(0) != ";":
            continue
        rec = body[start:m.start()]
        start = m.end()
        mm = ID_RE.match(rec)
        if not mm:
            raise CanonStop(f"unparsed record in {Path(p).name}: {rec[:120]!r}")
        eid, rest = int(mm.group(1)), mm.group(2)
        out, refs, pos = [], [], 0
        for tm in TOK_RE.finditer(rest):
            out.append(rest[pos:tm.start()])
            g = tm.group(0)
            if g.startswith("'"):
                if "\n" in g or "\r" in g:
                    raise CanonStop(f"string with a line break in #{eid}")
                out.append(g)
            elif g.startswith("#"):
                refs.append(int(tm.group(1)))
                out.append("\x00")
            pos = tm.end()
        out.append(rest[pos:])
        if eid in ents:
            raise CanonStop(f"duplicate entity id #{eid} in {Path(p).name}")
        ents[eid] = ("".join(out), refs)
        order.append(eid)
    if body[start:].strip():
        raise CanonStop(f"trailing text after the last entity in {Path(p).name}")
    return order, ents, t[i0:i1].splitlines()


def merkle(ents):
    """sha256 of each entity: its canonical text with every reference replaced by the referenced entity's hash (iterative DFS; a cycle or a
    dangling reference raises CanonStop)."""
    Hh, state = {}, {}
    for root in ents:
        if root in Hh:
            continue
        stack = [[root, -1]]
        while stack:
            top = stack[-1]
            nid = top[0]
            if top[1] == -1:
                state[nid] = 1
                top[1] = 0
            refs = ents[nid][1]
            k = top[1]
            while k < len(refs) and refs[k] in Hh:
                k += 1
            top[1] = k
            if k < len(refs):
                c = refs[k]
                if c not in ents:
                    raise CanonStop(f"dangling reference #{c} from #{nid}")
                if state.get(c) == 1:
                    raise CanonStop(f"reference cycle through #{c} (from #{nid})")
                stack.append([c, -1])
                continue
            parts = ents[nid][0].split("\x00")
            assert len(parts) == len(refs) + 1
            s = parts[0] + "".join(Hh[r] + parts[i + 1] for i, r in enumerate(refs))
            Hh[nid] = hashlib.sha256(s.encode()).hexdigest()
            state[nid] = 2
            stack.pop()
    return Hh


def etype(canon):
    if canon.startswith("("):
        no_str = re.sub(r"'(?:[^']|'')*'", "''", canon)
        return "COMPLEX[" + "+".join(NAME_RE.findall(no_str)) + "]"
    return canon.split("(", 1)[0]


def step_canonical_compare(pa, pb):
    """lead 20:30:00Z P2: PASS = the multisets of entity hashes are equal and the multisets of root entities are equal."""
    from collections import Counter
    res = {"method": ("Merkle sha256 per DATA entity: type + non-reference parameters as written (whitespace outside strings removed), each "
                      "#reference replaced by the referenced entity's hash; multisets of all entity hashes and of root entities compared")}
    try:
        oa, ea, la = step_entities(pa)
        ob, eb, lb = step_entities(pb)
        res["entity_counts"] = {"hub": len(oa), "rebuild": len(ob)}
        res["data_lines"] = {"hub": len(la), "rebuild": len(lb)}
        fd = next((i for i, (x, y) in enumerate(zip(la, lb)) if x != y), None)
        if fd is None and len(la) != len(lb):
            fd = min(len(la), len(lb))
        res["first_differing_data_line"] = None if fd is None else {"index_from_DATA": fd, "hub": la[fd][:160] if fd < len(la) else None,
                                                                    "rebuild": lb[fd][:160] if fd < len(lb) else None}
        ha, hb = merkle(ea), merkle(eb)
        ca, cb = Counter(ha.values()), Counter(hb.values())
        only_a, only_b = ca - cb, cb - ca
        refd_a = {r for _, (_, refs) in ea.items() for r in refs}
        refd_b = {r for _, (_, refs) in eb.items() for r in refs}
        ra = Counter(ha[i] for i in ea if i not in refd_a)
        rb = Counter(hb[i] for i in eb if i not in refd_b)
        res["root_entities"] = {"hub": sum(ra.values()), "rebuild": sum(rb.values()), "multisets_equal": ra == rb,
                                "root_types_hub": dict(Counter(etype(ea[i][0]) for i in ea if i not in refd_a).most_common())}
        res["hash_multisets_equal"] = ca == cb
        res["n_hashes_only_in_hub"] = sum(only_a.values())
        res["n_hashes_only_in_rebuild"] = sum(only_b.values())
        if only_a or only_b:
            inv_a, inv_b = {}, {}
            for i, h in ha.items():
                inv_a.setdefault(h, i)
            for i, h in hb.items():
                inv_b.setdefault(h, i)
            res["sample_only_in_hub"] = [{"id": inv_a[h], "type": etype(ea[inv_a[h]][0]), "text": ea[inv_a[h]][0].replace("\x00", "#")[:200]}
                                         for h in list(only_a)[:8]]
            res["sample_only_in_rebuild"] = [{"id": inv_b[h], "type": etype(eb[inv_b[h]][0]), "text": eb[inv_b[h]][0].replace("\x00", "#")[:200]}
                                             for h in list(only_b)[:8]]
        seq_a, seq_b = {}, {}
        for i in oa:
            seq_a.setdefault(etype(ea[i][0]), []).append(ha[i])
        for i in ob:
            seq_b.setdefault(etype(eb[i][0]), []).append(hb[i])
        res["types_whose_order_differs"] = sorted(k for k in set(seq_a) | set(seq_b) if seq_a.get(k) != seq_b.get(k)
                                                  and Counter(seq_a.get(k, [])) == Counter(seq_b.get(k, [])))
        res["types_whose_content_differs"] = sorted(k for k in set(seq_a) | set(seq_b) if Counter(seq_a.get(k, [])) != Counter(seq_b.get(k, [])))
        res["entities_per_type_hub"] = {k: len(v) for k, v in sorted(seq_a.items())}
        res["PASS"] = bool(ca == cb and ra == rb and len(oa) == len(ob))
    except CanonStop as e:
        res["PASS"] = False
        res["STOP"] = str(e)
    return res


def json_ptr_get(o, ptr):
    for k in ptr.strip("/").split("/"):
        o = o[int(k)] if isinstance(o, list) else o[k]
    return o


def json_ptr_set(o, ptr, v):
    ks = ptr.strip("/").split("/")
    for k in ks[:-1]:
        o = o[int(k)] if isinstance(o, list) else o[k]
    if isinstance(o, list):
        o[int(ks[-1])] = v
    else:
        assert ks[-1] in o, ptr
        o[ks[-1]] = v


def jdiff(a, b, path="", out=None, cap=60):
    out = [] if out is None else out
    if len(out) >= cap:
        return out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in list(a) + [k for k in b if k not in a]:
            if k not in b:
                out.append({"path": f"{path}/{k}", "only_in": "hub"})
            elif k not in a:
                out.append({"path": f"{path}/{k}", "only_in": "rebuild"})
            else:
                jdiff(a[k], b[k], f"{path}/{k}", out, cap)
        if list(a) != list(b) and set(a) == set(b):
            out.append({"path": path or "/", "key_order": "differs"})
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            jdiff(x, y, f"{path}[{i}]", out, cap)
    elif a != b:
        out.append({"path": path or "/", "hub": str(a)[:120], "rebuild": str(b)[:120]})
    return out


TIMING = re.compile(r"[0-9]+\.[0-9]+ s\b")


def mask_other(rel, o):
    """Fields of the other build outputs that change from run to run by construction: run times ('t_s', '<n.n> s' in log lines) and the
    sha256 of STEP files (their header carries the write time; the STEP DATA comparison covers their content)."""
    def walk(x, key=None, parent_key=None):
        if isinstance(x, dict):
            y = {}
            for k, v in x.items():
                if k == "t_s":
                    y[k] = "<masked: run time>"
                elif k == "sha256_16" and (str(x.get("file", "")).endswith(".step") or str(x.get("file_step", "")).endswith(".step")):
                    y[k] = "<masked: STEP file sha (header write time)>"
                else:
                    y[k] = walk(v, k, key)
            return y
        if isinstance(x, list):
            return [walk(v, key, parent_key) for v in x]
        if isinstance(x, str) and key == "log":
            return TIMING.sub("<t> s", x)
        return x
    return walk(o)


def glb_geometry_compare(pa, pb):
    import numpy as np
    import trimesh
    A = trimesh.load(str(pa), force="scene")
    B = trimesh.load(str(pb), force="scene")
    ga, gb = A.geometry, B.geometry
    res = {"n_meshes": [len(ga), len(gb)], "names_equal": sorted(ga) == sorted(gb), "max_abs_vertex_diff": 0.0, "faces_equal": True,
           "graph_transforms_equal": True}
    if res["names_equal"]:
        for k in ga:
            va, vb = np.asarray(ga[k].vertices), np.asarray(gb[k].vertices)
            if va.shape != vb.shape:
                res["max_abs_vertex_diff"] = float("inf")
                res["faces_equal"] = False
                continue
            res["max_abs_vertex_diff"] = max(res["max_abs_vertex_diff"], float(np.abs(va - vb).max()) if va.size else 0.0)
            res["faces_equal"] = res["faces_equal"] and bool(np.array_equal(np.asarray(ga[k].faces), np.asarray(gb[k].faces)))
        for n in A.graph.nodes_geometry:
            ta, _ = A.graph[n]
            if n in B.graph.nodes_geometry:
                tb, _ = B.graph[n]
                res["graph_transforms_equal"] = res["graph_transforms_equal"] and bool(np.array_equal(ta, tb))
            else:
                res["graph_transforms_equal"] = False
    return res


IO_NAMES = {"read_text", "read_bytes", "write_text", "write_bytes", "open", "glob", "rglob", "iterdir", "exists", "is_file", "is_dir", "mkdir",
            "unlink", "rename", "touch", "relative_to", "listdir", "scandir", "walk", "join", "dirname", "abspath", "realpath", "expanduser",
            "getcwd", "chdir", "loadtxt", "genfromtxt", "savez", "copyfile", "copytree", "rmtree", "importStep", "run_path", "import_module",
            "Popen", "system", "getenv", "Path"}


def static_scan(src):
    """AST scan (no code run) of every path-building site in src/ (see the module docstring)."""
    rows = []
    for f in sorted(src.rglob("*.py")):
        txt = f.read_text()
        t = ast.parse(txt)
        par = {}
        for node in ast.walk(t):
            for c in ast.iter_child_nodes(node):
                par[c] = node
        rel = str(f.relative_to(src))
        seen = set()

        def where(node):
            ch, p, mg, cond = [], par.get(node), False, []
            while p is not None:
                if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    ch.append(p.name)
                if isinstance(p, ast.If):
                    s = ast.unparse(p.test)
                    if "__name__" in s and "__main__" in s:
                        mg = True
                    else:
                        cond.append(s[:70])
                p = par.get(p)
            return ".".join(reversed(ch)) or "<module>", mg, cond[:2]

        def add(node, kind):
            seg = (ast.get_source_segment(txt, node) or ast.unparse(node))[:140]
            key = (node.lineno, kind, seg)
            if key in seen:
                return
            seen.add(key)
            fn, mg, cond = where(node)
            rows.append({"file": rel, "line": node.lineno, "kind": kind, "in": fn, "main_guard": mg, "cond": cond, "src": seg})

        for node in ast.walk(t):
            if isinstance(node, ast.Attribute) and node.attr in ("parent", "parents"):
                p = par.get(node)
                if isinstance(p, ast.Attribute) and p.attr in ("parent", "parents"):
                    continue
                add(p if isinstance(p, ast.Subscript) and p.value is node else node, "path navigation ." + node.attr)
            elif isinstance(node, ast.Name) and node.id == "__file__":
                add(node, "__file__")
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                s = node.value
                if s.startswith("/") and len(s) > 1 and " " not in s[:40] and not s.startswith("//"):
                    add(node, "absolute path literal")
                elif ".." in s.split("/") and "/" in s:
                    add(node, "'..' path literal")
            elif isinstance(node, ast.Call):
                full = ast.unparse(node.func)
                name = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id if isinstance(node.func, ast.Name) else ""
                if "environ" in full or full in ("os.getenv", "os.putenv"):
                    add(node, "environment")
                elif full.endswith("sys.path.insert") or full.endswith("sys.path.append"):
                    add(node, "sys.path edit")
                elif name in IO_NAMES and not (name in ("join", "dirname", "abspath", "realpath") and not full.startswith("os.path")):
                    add(node, "io / path call " + full[:40])
            elif isinstance(node, ast.Subscript) and ast.unparse(node.value) == "os.environ":
                add(node, "environment")
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names] if isinstance(node, ast.Import) else ([node.module] if node.module else [])
                for n in names:
                    top = n.split(".")[0]
                    if top == "__future__" or top in sys.stdlib_module_names:
                        continue
                    fn, mg, cond = where(node)
                    if (src / f"{top}.py").exists() or ((src / top).is_dir() and (src / (n.replace(".", "/") + ".py")).exists()):
                        res = "src/"
                    elif (src / "calcs" / f"{top}.py").exists():
                        res = "src/calcs/ (sys.path insert)"
                    else:
                        res = "site-packages or not in src/"
                    rows.append({"file": rel, "line": node.lineno, "kind": "import " + n, "in": fn, "main_guard": mg, "cond": cond,
                                 "src": ast.unparse(node)[:140], "resolves": res})
    rows.sort(key=lambda r: (r["file"], r["line"]))
    return rows


def main():
    t0 = time.time()
    rec = {"id": "rebuild_from_hub_v352", "version": "v2", "date": time.strftime("%Y-%m-%d", time.gmtime()), "owner": "mechanical",
           "script_revision": 3, "basis": __doc__.strip(),
           "previous_record": {"file": "checks/rebuild_from_hub_v352_v1.json", "sha256_16": sha(REC_V1, 16), "script_revision": 2,
                               "script_sha256_16": "f433fa517d4c4a5c", "ALL_OK": False,
                               "kept": "unchanged beside this record as the record of revision 2 (lead 20:30:00Z)"},
           "lead": ("19:53:27Z item 3 (rebuild proof before the engmat (A) publish), item 2 ruled (A); 20:04:32Z (a), (b1), (c); "
                    "20:16:57Z G1-G4 and items 1-3; 20:30:00Z P1-P3 and the claim wording"),
           "start_utc": time.strftime("%H:%M:%SZ", time.gmtime()), "claim": None, "claim_comparison_rules": RULES}
    assert not SCR.exists(), ("scratch folder exists already", str(SCR))
    assert sha(REC_V1, 16) == REC_V1_SHA, "record v1 changed"
    assert not OUT.exists(), ("record v2 exists already", str(OUT))
    try:
        return run_proof(rec, t0)
    except BaseException as e:
        rec["verdict"] = {"ALL_OK": False, "stopped": f"EXCEPTION in the parent: {type(e).__name__}: {e}"[:600]}
        rec["claim"] = None
        raise
    finally:
        if SCR.exists():
            shutil.rmtree(SCR, ignore_errors=True)
        rec["scratch_deleted"] = {"deleted": not SCR.exists(), "utc": time.strftime("%H:%M:%SZ", time.gmtime()),
                                  "free_MiB_after": round(free() / 2 ** 20, 1)}
        rec["t_total_s"] = round(time.time() - t0, 1)
        s = json.dumps(rec, indent=1, default=sorted)
        OUT.write_text(s)
        print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16], "verdict:", json.dumps(rec.get("verdict"), default=sorted))


def run_proof(rec, t0):
    f0 = free()
    assert f0 - 120e6 >= LIM, ("free space too low to start", f0)
    MF = H / "MANIFEST_v3.5.2.sha256"
    assert sha(MF, 16) == MF_SHA, sha(MF, 16)
    HUBM = {ln[66:]: ln[:64] for ln in MF.read_text().splitlines() if ln}
    # ------------------------------------------------------------------------------------------- named inputs before the build (G1)
    pre = {k: sha(HUB / k, 16) for k in NAMED}
    rec["named_inputs"] = {"package_root": str(HUB), "rule": "read in place by config.py; sha256/16 checked before and after the build",
                           "inputs": {k: {"version": v, "named_sha256_16": s, "sha_before": pre[k]} for k, (v, s) in NAMED.items()}}
    if any(pre[k] != NAMED[k][1] for k in NAMED):
        rec["verdict"] = {"ALL_OK": False, "stopped": "a named input differs from its named sha before the build: nothing run"}
        return 4
    # ------------------------------------------------------------------------------------------- engmat v1.7 vs v1.6 (set-file statement)
    assert sha(ENGMAT, 16) == ENGMAT_SHA and sha(ENGMAT16, 16) == ENGMAT16_SHA
    mm = {}
    for tag, p in (("v1.7", ENGMAT), ("v1.6", ENGMAT16)):
        r = subprocess.run(["nice", "-n", "19", PY, "-I", "-B", "-c", MATS, str(p)], capture_output=True, text=True, timeout=120, cwd="/tmp")
        assert r.returncode == 0, r.stderr[-800:]
        mm[tag] = json.loads(r.stdout)
    m7, m6 = mm["v1.7"]["materials"], mm["v1.6"]["materials"]
    rec["engmat_v17_vs_hub_v16"] = {"v1.7": f"{ENGMAT_SHA} MATERIALS_VERSION {mm['v1.7']['version']}",
                                    "v1.6": f"hub 04-fea/src/engmat.py {ENGMAT16_SHA} MATERIALS_VERSION {mm['v1.6']['version']}",
                                    "added": sorted(set(m7) - set(m6)), "removed": sorted(set(m6) - set(m7)),
                                    "changed": sorted(k for k in set(m6) & set(m7) if m6[k] != m7[k])}
    # ------------------------------------------------------------------------------------------- scratch copy
    S = SCR / "03-cad/v3.5.2"
    copied = {}
    for k in sorted(x for x in HUBM if x.startswith("src/")):
        d = S / k
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(H / k, d)
        assert sha(d) == HUBM[k], k
        copied[k] = HUBM[k][:16]
    shutil.copyfile(ENGMAT, S / "src/engmat.py")
    assert sha(S / "src/engmat.py", 16) == ENGMAT_SHA
    for k, (p, s16) in ADD_A.items():
        assert sha(p, 16) == s16, k
        shutil.copyfile(p, S / k)
        assert sha(S / k, 16) == s16, k
    assert sha(M351, 16) == M351_SHA
    shutil.copyfile(M351, S / "massprops_v3.5.1.json")
    assert sha(S / "massprops_v3.5.1.json", 16) == M351_SHA
    assert sha(MJ21, 16) == MJ21_SHA and HUBM.get("history/mechanical.json.e4d3e7c9df529171", "")[:16] == MJ21_SHA
    (SCR / "03-cad/interfaces").mkdir(parents=True)
    shutil.copyfile(MJ21, SCR / "03-cad/interfaces/mechanical.json")
    assert sha(SCR / "03-cad/interfaces/mechanical.json", 16) == MJ21_SHA
    (SCR / "iface_snapshot").mkdir()
    runner = SCR / "runner_child.py"
    runner.write_text(CHILD)
    rec["scratch"] = {"root": str(SCR), "set_copy": "03-cad/v3.5.2", "src_files_copied_from_hub": len(copied), "src_copy_sha256_16": copied,
                      "added": {"src/engmat.py": f"{ENGMAT_SHA} (engmat v1.7, ruled (A))",
                                **{k: f"{s16} (byte copy of hub 03-cad/calcs/{Path(k).name}, ruled (a))" for k, (p, s16) in ADD_A.items()},
                                "massprops_v3.5.1.json": f"{M351_SHA} (copy of 03-cad/v3.5.1/massprops_v3.5.1.json, named input)",
                                "../interfaces/mechanical.json": f"{MJ21_SHA} (copy of history/mechanical.json.e4d3e7c9df529171, interface v2.1, ruled (b1); scratch only)"},
                      "iface_snapshot": "iface_snapshot/ (empty; ENGINE_IFACE_SNAPSHOT, G2)"}
    env = {k: v for k, v in os.environ.items() if not k.startswith(("ENGINE_", "PYTHON", "MAKE_ALL"))}
    env.update({"MAKE_ALL_CAD": "v352", "ENGINE_IFACE_SNAPSHOT": str(SCR / "iface_snapshot"), "ENGINE_USE_FALLBACK": "1",
                "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
    rec["env_set"] = {k: env[k] for k in ("MAKE_ALL_CAD", "ENGINE_IFACE_SNAPSHOT", "ENGINE_USE_FALLBACK", "OMP_NUM_THREADS",
                                          "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")}
    rec["env_set"]["ENGINE_INTERFACES"] = "(unset: config.py:21 default <package root>/interfaces)"
    # ------------------------------------------------------------------------------------------- child
    log = open(SCR / "child.log", "w")
    tb = time.time()
    p = subprocess.Popen(["nice", "-n", "19", PY, "-I", "-B", str(runner), "--child", str(SCR)], env=env, cwd=str(SCR),
                         stdout=log, stderr=subprocess.STDOUT)
    fmin, stopped, peak = f0, None, 0
    while p.poll() is None:
        f = free()
        fmin = min(fmin, f)
        sb = tree_bytes(SCR)
        peak = max(peak, sb)
        if f < LIM or sb > SCR_MAX:
            p.kill()
            stopped = {"free_B": f, "scratch_B": sb, "at_s": round(time.time() - tb, 1)}
            break
        time.sleep(2)
    p.wait()
    log.close()
    peak = max(peak, tree_bytes(SCR))
    rec["child"] = {"pid": p.pid, "returncode": p.returncode, "t_s": round(time.time() - tb, 1), "stopped": stopped,
                    "log_tail": (SCR / "child.log").read_text(errors="replace")[-1500:]}
    f1 = free()
    rec["disk"] = {"free_MiB_start": round(f0 / 2 ** 20, 1), "free_MiB_min": round(min(fmin, f1) / 2 ** 20, 1),
                   "free_MiB_end_before_delete": round(f1 / 2 ** 20, 1), "limit_MiB": round(LIM / 2 ** 20, 1),
                   "scratch_peak_MB": round(peak / 1e6, 2), "scratch_limit_MB": SCR_MAX / 1e6}
    if stopped or p.returncode != 0 or not (SCR / "child_record.json").exists():
        rec["verdict"] = {"ALL_OK": False, "stopped": "BUILD NOT COMPLETED (see child): nothing compared"}
        return 3
    cr = json.loads((SCR / "child_record.json").read_text())
    rec["child"].update(rc=cr["rc"], flags=cr["flags"], executable=cr["executable"])
    if cr["rc"].get("make_all") != 0 or cr["rc"].get("mass_delta") != 0:
        rec["verdict"] = {"ALL_OK": False, "stopped": "BUILD NOT COMPLETED (child rc): nothing compared"}
        return 3

    # ------------------------------------------------------------------------------------------- isolation
    scr = os.path.realpath(SCR)
    sp = cr["sysconfig_paths"]
    py_roots = sorted({sp["stdlib"], sp["platstdlib"], sp["purelib"], sp["platlib"]})
    hub_real = os.path.realpath(HUB)
    mods = {"scratch_copy": [], "stdlib_or_site_packages": 0, "stdlib_by_path_symlink_P3": [], "OTHER": []}
    for given, m, name in cr["modules"]:
        if m.startswith(scr + "/"):
            mods["scratch_copy"].append(m[len(scr) + 1:])
        elif any(m.startswith(r + "/") for r in py_roots):
            mods["stdlib_or_site_packages"] += 1
        elif (name == "sitecustomize" and given.startswith(sp["stdlib"] + "/") and not m.startswith((DEV + "/", hub_real + "/"))):
            mods["stdlib_by_path_symlink_P3"].append({"module": name, "path": given, "realpath": m})
        else:
            mods["OTHER"].append([given, m, name])
    reads = {"scratch": 0, "hub_read_in_place": {}, "python_stdlib_or_site": 0, "system": [], "DEV_TREE": [], "MNT": [],
             "tool_cache_config_reads_ezdxf_P3": [], "OTHER": [], "writes_outside_scratch": []}
    for path, mode, flags in cr["opens"]:
        rp = os.path.realpath(path) if path.startswith("/") else os.path.realpath(os.path.join(scr, path))
        wr = any(c in mode for c in "wax+") or (flags not in (-1,) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND))
        if rp.startswith(scr + "/") or rp == scr:
            reads["scratch"] += 1
            continue
        if wr and rp != "/dev/null":
            reads["writes_outside_scratch"].append([rp, mode, flags])
        if rp.startswith(hub_real + "/"):
            rel = rp[len(hub_real) + 1:]
            reads["hub_read_in_place"][rel] = sha(rp, 16) if os.path.isfile(rp) else "not a file"
        elif rp.startswith(DEV + "/") or rp == DEV:
            reads["DEV_TREE"].append(rp)
        elif rp.startswith("/mnt/"):
            reads["MNT"].append(rp)
        elif any(rp.startswith(r + "/") for r in py_roots) or rp.startswith("/opt/engine-venv/") or rp.startswith("/usr/lib/python3"):
            reads["python_stdlib_or_site"] += 1
        elif rp.startswith(("/proc/", "/sys/", "/dev/", "/etc/", "/usr/share/", "/usr/lib/")):
            reads["system"].append(rp)
        elif rp in EZDXF_TOOL_READS and not wr:
            reads["tool_cache_config_reads_ezdxf_P3"].append({"path": rp, "exists": os.path.isfile(rp),
                                                              "sha256_16": sha(rp, 16) if os.path.isfile(rp) else None})
        else:
            reads["OTHER"].append(rp)
    reads["system"] = sorted(set(reads["system"]))[:40]
    reads["tool_cache_config_reads_ezdxf_P3"] = sorted({json.dumps(x, sort_keys=True) for x in reads["tool_cache_config_reads_ezdxf_P3"]})
    reads["tool_cache_config_reads_ezdxf_P3"] = [json.loads(x) for x in reads["tool_cache_config_reads_ezdxf_P3"]]
    post = {k: sha(HUB / k, 16) for k in NAMED}
    for k in NAMED:
        rec["named_inputs"]["inputs"][k].update(sha_after=post[k], read_in_place_by_the_build=k in reads["hub_read_in_place"])
    unnamed_hub_reads = sorted(set(reads["hub_read_in_place"]) - set(NAMED))
    named_not_read = sorted(set(NAMED) - set(reads["hub_read_in_place"]))
    named_ok = (not unnamed_hub_reads and not named_not_read and all(post[k] == NAMED[k][1] for k in NAMED)
                and all(reads["hub_read_in_place"].get(k) == NAMED[k][1] for k in NAMED))
    rec["named_inputs"].update(unnamed_hub_reads=unnamed_hub_reads, named_not_read=named_not_read, named_inputs_ok=named_ok)
    rec["isolation"] = {"modules": {"n_scratch_copy": len(mods["scratch_copy"]), "scratch_copy": mods["scratch_copy"],
                                    "n_stdlib_or_site_packages": mods["stdlib_or_site_packages"],
                                    "stdlib_by_path_symlink_P3": mods["stdlib_by_path_symlink_P3"], "OTHER": mods["OTHER"],
                                    "python_roots": py_roots},
                        "files_opened_from_python": reads,
                        "note": ("the audit hook sees opens made from Python; OCCT writes the STEP / STL files in C++ to the paths make_all "
                                 "passes (all under the scratch set, listed below as outputs)")}
    iso_ok = not mods["OTHER"] and not any(m.startswith((DEV + "/", hub_real + "/")) or g.startswith((DEV + "/", hub_real + "/"))
                                           for g, m, _ in cr["modules"])
    inputs_ok = (not reads["DEV_TREE"] and not reads["MNT"] and not reads["writes_outside_scratch"] and not reads["OTHER"] and named_ok)
    rec["isolation"]["modules_ok"] = iso_ok
    rec["isolation"]["inputs_ok"] = inputs_ok

    # ------------------------------------------------------------------------------------------- static scan + coverage
    cov = {(f, ln) for f, ln in cr["coverage"]}
    scan = static_scan(S / "src")
    for r in scan:
        r["executed_in_run"] = (r["file"], r["line"]) in cov
    mism = []
    cls = []
    for f, ln, what, exp in CLASSIFIED:
        got = (f, ln) in cov
        cls.append({"site": f"{f}:{ln}", "what": what, "expected_on_build_path": exp, "executed_in_run": got})
        if got != exp:
            mism.append(f"{f}:{ln}")
    rec["static_scan"] = {"n_sites": len(scan), "n_executed": sum(r["executed_in_run"] for r in scan),
                          "classified_sites_20_15_43Z": cls, "classification_mismatches": mism,
                          "n_lines_covered_in_src": len(cov),
                          "files_with_coverage": sorted({f for f, _ in cov}),
                          "sites": [[r["file"], r["line"], r["kind"], r["in"], r["main_guard"], r["executed_in_run"]] for r in scan],
                          "sites_columns": ["file", "line", "kind", "enclosing function", "under __main__ guard", "executed in this run"]}
    cls_ok = not mism

    # ------------------------------------------------------------------------------------------- comparison with the hub MANIFEST
    produced = sorted(str(q.relative_to(S)) for q in S.rglob("*") if q.is_file() and not str(q.relative_to(S)).startswith("src/")
                      and q.name != "massprops_v3.5.1.json")
    MAIN = ("BOM_v3.5.2.json", "BOM_v3.5.2.csv", "massprops_v3.5.2.json", "massdelta_v3.5.2_vs_v3.5.1.json")
    PLC = "assembly/placements_v3.5.2.json"
    cmp = {"stl": {"n": 0, "byte_identical": 0, "differ": []}, "step": {"n": 0, "byte_identical": 0, "data_identical_header_only": 0,
                                                                      "header_fields_differing": set(), "differ": [],
                                                                      "assembly_data_identical": [], "assembly_canonical": {}},
           "main_files": {}, "glb": {}, "placements": {}, "other_outputs": {}, "produced_not_in_hub_set": [], "hub_outputs_not_produced": [],
           "hub_changed_since_manifest": []}
    for rel in produced:
        q = S / rel
        if rel not in HUBM:
            cmp["produced_not_in_hub_set"].append(rel)
            continue
        hs = HUBM[rel]
        if sha(H / rel) != hs:
            cmp["hub_changed_since_manifest"].append(rel)
            continue
        same = sha(q) == hs
        if rel.endswith(".stl"):
            cmp["stl"]["n"] += 1
            cmp["stl"]["byte_identical" if same else "differ"] = (cmp["stl"]["byte_identical"] + 1) if same else cmp["stl"]["differ"] + [rel]
        elif rel.endswith(".step"):
            cmp["step"]["n"] += 1
            if same:
                cmp["step"]["byte_identical"] += 1
            elif step_data(q) == step_data(H / rel):
                cmp["step"]["data_identical_header_only"] += 1
                if rel in ASM_STEP:
                    cmp["step"]["assembly_data_identical"].append(rel)
                for x, y in zip(step_header(H / rel).splitlines(), step_header(q).splitlines()):
                    if x != y:
                        cmp["step"]["header_fields_differing"].add(re.sub(r"\(.*", "", x.strip())[:40])
            elif rel in ASM_STEP:
                cc = step_canonical_compare(H / rel, q)
                cmp["step"]["assembly_canonical"][rel] = cc
                if not cc["PASS"]:
                    cmp["step"]["differ"].append(rel)
            else:
                cmp["step"]["differ"].append(rel)
        elif rel in MASK_PTR:
            a, b = json.loads((H / rel).read_text()), json.loads(q.read_text())
            ptr = MASK_PTR[rel]
            va, vb = json_ptr_get(a, ptr), json_ptr_get(b, ptr)
            json_ptr_set(a, ptr, "<masked>")
            json_ptr_set(b, ptr, "<masked>")
            rest_ok = json.dumps(a) == json.dumps(b)
            e = {"hub_sha256_16": hs[:16], "rebuild_sha256_16": sha(q, 16), "byte_identical": same, "masked_pointer_rfc6901": ptr,
                 "masked_values": {"hub": va, "rebuild": vb}, "every_other_field_identical_order_preserving": rest_ok}
            if not rest_ok:
                e["json_diff_masked"] = jdiff(a, b)
            cmp["main_files"][rel] = e
        elif rel in MAIN:
            e = {"hub_sha256_16": hs[:16], "rebuild_sha256_16": sha(q, 16), "byte_identical": same}
            if not same and rel.endswith(".json"):
                e["json_diff"] = jdiff(json.loads((H / rel).read_text()), json.loads(q.read_text()))
            elif not same:
                la, lb = (H / rel).read_text().splitlines(), q.read_text().splitlines()
                e["csv_lines_differing"] = [i for i, (x, y) in enumerate(zip(la, lb)) if x != y][:40] + (["line count"] if len(la) != len(lb) else [])
            cmp["main_files"][rel] = e
        elif rel.endswith(".glb"):
            e = {"hub_sha256_16": hs[:16], "rebuild_sha256_16": sha(q, 16), "byte_identical": same}
            if not same:
                e["readback_geometry"] = glb_geometry_compare(H / rel, q)
            cmp["glb"][rel] = e
        elif rel == PLC:
            a, b = json.loads((H / rel).read_text()), json.loads(q.read_text())
            e = {"hub_sha256_16": hs[:16], "rebuild_sha256_16": sha(q, 16), "byte_identical": same, "hub_date": a.get("date"),
                 "rebuild_date": b.get("date")}
            if not same:
                a2, b2 = dict(a, date="<masked>"), dict(b, date="<masked>")
                e["identical_with_date_masked"] = a2 == b2
                e["note"] = ("compared with the date field masked: the rebuild ran on another UTC day" if a.get("date") != b.get("date")
                             else "differs on the same UTC day")
                e["json_diff"] = jdiff(a, b, cap=12)
            cmp["placements"][rel] = e
        else:
            e = {"hub_sha256_16": hs[:16], "rebuild_sha256_16": sha(q, 16), "byte_identical": same}
            if not same and rel.endswith(".json"):
                a, b = json.loads((H / rel).read_text()), json.loads(q.read_text())
                e["identical_with_run_time_and_step_sha_masked"] = mask_other(rel, a) == mask_other(rel, b)
                if not e["identical_with_run_time_and_step_sha_masked"]:
                    e["json_diff_masked"] = jdiff(mask_other(rel, a), mask_other(rel, b), cap=12)
            cmp["other_outputs"][rel] = e
    for rel in sorted(HUBM):
        if (rel.startswith(("parts/", "assembly/")) or rel in MAIN) and rel not in produced:
            cmp["hub_outputs_not_produced"].append(rel)
    cmp["step"]["header_fields_differing"] = sorted(cmp["step"]["header_fields_differing"])
    rec["comparison"] = cmp
    mf = cmp["main_files"]
    ok_bom = all(rel in mf and mf[rel]["byte_identical"] for rel in ("BOM_v3.5.2.json", "BOM_v3.5.2.csv"))
    mp, md = mf.get("massprops_v3.5.2.json"), mf.get("massdelta_v3.5.2_vs_v3.5.1.json")
    ok_mass = bool(mp and md and mp["every_other_field_identical_order_preserving"] and md["every_other_field_identical_order_preserving"]
                   and md["masked_values"]["hub"] == mp["hub_sha256_16"] and md["masked_values"]["rebuild"] == mp["rebuild_sha256_16"])
    if mp and md:
        md["masked_value_check"] = {"hub_massdelta_field_equals_hub_massprops_sha": md["masked_values"]["hub"] == mp["hub_sha256_16"],
                                    "rebuild_massdelta_field_equals_rebuild_massprops_sha": md["masked_values"]["rebuild"] == mp["rebuild_sha256_16"]}
    ok_glb = len(cmp["glb"]) == 1 and all(v["byte_identical"] for v in cmp["glb"].values())
    ok_plc = len(cmp["placements"]) == 1 and all(v["byte_identical"] for v in cmp["placements"].values())
    am = cmp["other_outputs"].get("assembly/assembly_manifest_v3.5.2.json")
    ok_amf = bool(am and am["byte_identical"])
    asm_c = cmp["step"]["assembly_canonical"]
    ok_asm = all(rel in cmp["step"]["assembly_data_identical"] or (rel in asm_c and asm_c[rel]["PASS"]) for rel in ASM_STEP)
    ok_cad = (cmp["stl"]["n"] == 112 and cmp["stl"]["byte_identical"] == 112 and cmp["step"]["n"] == 114 and not cmp["step"]["differ"]
              and cmp["step"]["byte_identical"] + cmp["step"]["data_identical_header_only"] + len(asm_c) == 114 and ok_asm
              and not cmp["hub_outputs_not_produced"] and not cmp["hub_changed_since_manifest"])
    ok_other = all(v["byte_identical"] or v.get("identical_with_run_time_and_step_sha_masked") for v in cmp["other_outputs"].values())
    allok = bool(iso_ok and inputs_ok and cls_ok and ok_cad and ok_bom and ok_mass and ok_glb and ok_plc and ok_amf and ok_other
                 and not cmp["produced_not_in_hub_set"])
    rec["verdict"] = {"isolation_modules_ok": iso_ok, "inputs_ok_named_inputs_only_shas_checked": inputs_ok,
                      "static_classification_confirmed_by_coverage": cls_ok,
                      "stl_112_byte_identical_and_part_step_data_identical": ok_cad,
                      "assembly_step_identical_up_to_entity_order_and_numbering_P2": ok_asm,
                      "bom_json_csv_byte_identical": ok_bom,
                      "massprops_massdelta_identical_except_the_two_masked_pointers_P1": ok_mass,
                      "glb_byte_identical": ok_glb, "placements_byte_identical_same_utc_day": ok_plc,
                      "assembly_manifest_byte_identical": ok_amf,
                      "other_outputs_ok_run_time_and_step_sha_masked": ok_other, "ALL_OK": allok}
    rec["claim"] = CLAIM if allok else None
    if allok:
        rec["claim_scope"] = ("hub copy of the archive (package root /home/claude/work/shared-fallback/engine) with the five named inputs, "
                              "shas checked; not tested from a fresh GitHub checkout")
    return 0 if allok else 5


if __name__ == "__main__":
    sys.exit(main())

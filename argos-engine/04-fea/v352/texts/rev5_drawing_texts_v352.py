"""Rev-5 drawing texts of ENG-TC-01 and ENG-TC-02 (notes, supplier, drawing datum / fits) as the dev rev-5 CAD source generates them, for the
v3.5.2 hub update of lead 18:36:37Z item 5 ('the drawing texts (+/-0.25 deg index pin, C4 shoulder-screw registration, J-F1 torque cap at
3750 N, the Prescale item, single-use screws with the fillet in the inspection)').  Mechanical, 2026-10-20, v1.

The texts are read from an in-memory build of the dev rev-5 source (03-cad/src, config.V352_ON, MAKE_ALL_CAD=v352: make_all.stage_build(),
the same call the FINAL 03-cad set will make); no CAD file is written.  The hub 03-cad interim set stays at rev 4 until the FINAL set (lead
17:55:55Z: the final set waits for the end of chain E or >= 2.50 GiB free), so these rev-5 texts are published here, under 04-fea/v352/texts,
as the texts that the FINAL set will carry; the GSE tool lines of the v3.5.2 BOM (make_all.gse_tool_lines()) are recorded too.  Text only: no number in this file is a result; the anchors below are asserted present."""
import hashlib, json, os, sys, time
from pathlib import Path

SRC = Path("/home/claude/work/mechanical/v352/engine/03-cad/src")
OUT = Path("/home/claude/work/mechanical/v352/texts/rev5_drawing_texts_v352_v1.json")
os.environ["MAKE_ALL_CAD"] = "v352"
sys.path.insert(0, str(SRC))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


SRC_FILES = {f: sha(SRC / f) for f in ("parts_engine.py", "config.py", "build.py", "partlib.py", "make_all.py")}
import make_all                                   # noqa: E402  (after MAKE_ALL_CAD)
assert make_all.CAD_VERSION == "v3.5.2"
t0 = time.time()
P, S, reg, clog = make_all.stage_build()
t_build = round(time.time() - t0, 1)
assert S.get("jfwd_od_spot"), "rev-5 J-FWD spot face not active in this build"

parts = {}
for p in reg:
    if p.pn in ("ENG-TC-01", "ENG-TC-02"):
        parts[p.pn] = {"name": p.name, "material": p.material, "process": p.process, "supplier": p.supplier, "notes": p.notes, "dwg": p.dwg,
                       "jfwd_fits_items": [x for x in p.dwg.get("fits", []) if "J-FWD" in x]}
assert set(parts) == {"ENG-TC-01", "ENG-TC-02"}
t01 = parts["ENG-TC-01"]["notes"] + " || " + " || ".join(parts["ENG-TC-01"]["dwg"]["fits"])
t02 = parts["ENG-TC-02"]["notes"] + " || " + " || ".join(parts["ENG-TC-02"]["dwg"]["fits"])
ANCHORS = {   # lead 18:36:37Z item 5 texts -> where the rev-5 drawings carry them (asserted)
    "+/-0.25 deg index pin (F5)": [("ENG-TC-02", "within +/-0.25 deg by an index pin in the match-drill fixture"),
                                   ("ENG-TC-02", "TC-02 clocked by an index pin within +/-0.25 deg"),
                                   ("ENG-TC-01", "within +/-0.25 deg by the index pin of the match-drill fixture")],
    "C4 shoulder-screw registration (F2)": [("ENG-TC-01", "REGISTRATION by two GSE shoulder screws ENG-TC-13 (not flight), selected to the "
                                                          "pin-gauged holes, in two opposite holes first")],
    "J-F1 torque cap at 3750 N (F1)": [("ENG-TC-01", "maximum preload capped at 3750 N, T_lot = 3750 N x K_min(lot) x 5 mm")],
    "Prescale item (F1)": [("ENG-TC-01", "Fuji Prescale footprint item, TO-VERIFY")],
    "single-use screws with the fillet in the inspection (R3, 18:36:37Z)": [
        ("ENG-TC-01", "J-FWD screws SINGLE-USE until C6 closes (new at every assembly, never reused or re-torqued)"),
        ("ENG-TC-01", "inspected at 10x plus dye penetrant at the thread root AND the head-to-shank fillet")],
    "rows v7 / spring v4 basis (L 10.7 spring A, L 10.6 spring B)": [("ENG-TC-02", "(rows v7 / spring v4 basis, lead 17:55:55Z F3)"),
                                                                    ("ENG-TC-01", "(M5 x 10.6 with spring B)")]}
txt = {"ENG-TC-01": t01, "ENG-TC-02": t02}
for k, v in ANCHORS.items():
    for pn, a in v:
        assert a in txt[pn], (k, pn, a)
STALE = ["+/-0.5 deg (TO-CONFIRM", "rows v6 / spring v3"]
for s in STALE:
    assert s not in t01 and s not in t02, s

out = {"id": "rev5_drawing_texts_v352", "version": "v1", "date": time.strftime("%Y-%m-%d", time.gmtime()), "owner": "mechanical",
       "basis": __doc__.strip(), "status": "TEXT (drawing notes); the FINAL 03-cad set carries them; the hub interim set stays at rev 4",
       "source": {"dev_src": str(SRC), "sha256_16": SRC_FILES, "build_fingerprint": make_all.build_fingerprint(),
                  "build": "make_all.stage_build(), MAKE_ALL_CAD=v352, config.V352_ON (rev 5)", "t_build_s": t_build,
                  "parts_engine_pre_text_update_sha256_16": "68efe03af3e2ca80",
                  "parts_engine_hub_rev4_sha256_16": "3699993d03f835c2"},
       "lead_items_18_36_37Z_item5_anchors": {k: [{"part": pn, "text": a} for pn, a in v] for k, v in ANCHORS.items()},
       "removed_texts": {"ENG-TC-02 tap note": "'TC-02 clocked to the TC-01 pattern within +/-0.5 deg (TO-CONFIRM; tap-to-cavity walls at the "
                                               "limit in checks/test_rev5_jfwd.py)' -> +/-0.25 deg by an index pin (F5)",
                         "ENG-TC-02 notes": "'(rows v6 / spring v3 basis)' -> rows v7 / spring v4 with spring B on L 10.6"},
       "parts": parts,
       "gse_tool_lines": make_all.gse_tool_lines()}
assert {L["pn"] for L in out["gse_tool_lines"]} == {"ENG-TC-12", "ENG-TC-13"}
assert "two opposite holes" in next(L["notes"] for L in out["gse_tool_lines"] if L["pn"] == "ENG-TC-13")
s = json.dumps(out, indent=1)
OUT.write_text(s)
print(OUT, hashlib.sha256(s.encode()).hexdigest()[:16], "build", t_build, "s")
for pn in parts:
    for x in parts[pn]["jfwd_fits_items"]:
        print(pn, "|", x[:220])

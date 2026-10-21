"""Gap-conductance variant thermal fields of v3.5.2 (lead 2026-10-20 (2) variant + 03:10Z item 4: publish each field with tag and sha as soon as
it exists, for FEA3D's J-FWD sub-model and thermal joints).  Mechanical, 2026-10-20, v2 (v1 + the finished S-AX r10free GVLO / GVHI runs, all states).  No solve: reads the finished thermal run folders.
Per field: tag, run folder, sha256/16 of the .frd.gz / envelope.json / envelope_nodes.npz / meta / summary, the variant record (strip
gaps, kmul, eps_eff, k / h tables), the per-part envelope, and the S-AX run folder that maps it (L1_th<tag>_r10free_cad352: mesh.npz +
<state>/res.npz 'T' = the mapped field FEA3D's asm_build.SaxThermal reads) when it exists.  Frames: thermal z = S-AX z + 6.544 mm."""
import json, hashlib, sys
from pathlib import Path
RUNS = Path("/home/claude/work/mechanical/runs")
PRE = "DC-B1v3p99_tg711_hi_SS316L_L2.5_"
TAGS = sys.argv[1].split(",") if len(sys.argv) > 1 else ["v352_NF2b", "v352_NF2b_GVLO", "v352_NF2b_GVHI"]


def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


out = {"id": "gapvar_fields_v352", "version": "v2", "date": "2026-10-20", "owner": "mechanical", "basis": __doc__.strip(),
       "evidence": "SIM (2-D axisymmetric thermal FE, ccx 2.21) on the B1 hi-bound duty cycle DC-B1v3p99_tg711; gap strips CALC on LITERATURE / ASSUMED",
       "fields": {}}
for tag in TAGS:
    rd = RUNS / "thermal" / (PRE + tag)
    if not rd.is_dir():
        continue
    meta = json.loads(next(rd.glob("*_meta.json")).read_text())
    env = json.loads((rd / "envelope.json").read_text())["parts"]
    files = {}
    for f in sorted(rd.iterdir()):
        if f.is_file() and (f.name.endswith(".frd.gz") or f.name in ("envelope.json", "envelope_nodes.npz", "summary.json", "monitors.csv") or f.name.endswith("_meta.json")):
            files[f.name] = {"sha256_16": sha16(f), "bytes": f.stat().st_size}
    gv = meta.get("gap_variant")
    rec = {"thermal_run": str(rd), "files": files, "gap_variant": (None if not gv else {k: gv[k] for k in gv if k != "gvcc"}),
           "gvcc": (gv or {}).get("gvcc", {}).get("closure") if gv else None,
           "envelope_parts": {p: env[p] for p in ("ENG-TC-01", "ENG-TC-02", "ENG-TC-03", "ENG-TC-04", "ENG-TC-10", "ENG-TC-09", "ENG-NZ-03", "ENG-NZ-04", "GAP-J1", "GAP-J2", "GAP-J3") if p in env}}
    sx = RUNS / "structural" / (f"L1_th{tag}_r10free_cad352" if "GV" in tag else f"L1_th{tag}_cad352")
    if (sx / "mesh.npz").exists():
        st = sorted(p.name for p in sx.iterdir() if (p / "res.npz").exists())
        rec["sax_run"] = {"dir": str(sx), "mesh_npz_sha256_16": sha16(sx / "mesh.npz"), "states": st,
                          "res_npz_sha256_16": {s: sha16(sx / s / "res.npz") for s in st}}
    out["fields"][tag] = rec
p = Path("/home/claude/work/mechanical/v352/gapvar/gapvar_fields_v352_v2.json")
s = json.dumps(out, indent=1)
p.write_text(s)
print(p, hashlib.sha256(s.encode()).hexdigest()[:16])
for t, r in out["fields"].items():
    e = r["envelope_parts"]
    print(t, {k: v["sha256_16"] for k, v in r["files"].items() if k.endswith(".gz") or k == "envelope.json"}, "TC-02", e["ENG-TC-02"]["T_max_C"], e["ENG-TC-02"]["t_max_s"], "sax" if "sax_run" in r else "")

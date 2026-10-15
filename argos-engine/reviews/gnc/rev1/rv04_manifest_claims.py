"""rv04_manifest_claims v1.0 (REV-GNC-R1, independent reviewer, 2026-10-13).

Record of the reviewer's byte-level and claim checks on the GNC rev1 response (reads only; writes rv04_manifest_claims.json):
  M  full re-hash of MANIFEST_rev1.sha256 (every entry, sha256 of the bytes on disk) and the files on disk outside it
  T  the stored tables the bit-check and the re-flown arms read from the GNC work area equal the hub-published copies
  I  claim "live hub combustion.json lacks igniter.sequence": key presence in every combustion.json copy the GNC code can read
     (GNC_IFACE pin, live hub, the simulator's local fallback snapshot), the default GNC_IFACE mount, and GNC's own v3 rebuild
  K  RG-04 clarification "the reviewer's x0.90 multiplies the per-run draw": the reviewer's rg05 code and GNC's conditional tables
A hash identifies bytes only; it does not show that a statement is true.
"""
import csv
import gzip
import hashlib
import io
import json
import os

HUB = "/home/claude/work/shared-fallback/engine"
REV1 = f"{HUB}/01-systems-gnc/staging_v3.1/rev1"
W = "/home/claude/work/space"
HERE = os.path.dirname(os.path.abspath(__file__))


def sha(b):
    return hashlib.sha256(b).hexdigest()


def part_m():
    lines = open(f"{REV1}/MANIFEST_rev1.sha256").read().splitlines()
    header = [ln for ln in lines if ln.startswith("#")]
    ent = [ln.split(None, 1) for ln in lines if ln.strip() and not ln.startswith("#")]
    bad, n = [], 0
    for h, p in ent:
        n += 1
        if sha(open(os.path.join(REV1, p), "rb").read()) != h:
            bad.append(p)
    listed = {p for _, p in ent}
    on_disk = []
    for root, _, files in os.walk(REV1):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), REV1)
            if rel not in listed:
                on_disk.append(rel)
    return dict(manifest_sha16=sha(open(f"{REV1}/MANIFEST_rev1.sha256", "rb").read())[:16], header=header, entries=n,
                mismatches=len(bad), bad=bad, on_disk_not_in_manifest=sorted(on_disk),
                key_files={p: sha(open(os.path.join(REV1, p), "rb").read())[:16] for p in (
                    "results/rev1_items/rev1_items.json", "results/fsw_record/fsw_config_record_v1.json",
                    "sim/gncsim_v2.8-dev_MWFPRS/sim6.py", "sim/gncsim_v2.8-dev_MWFPRS/run6.py",
                    "results/v28_checks_v15/bitcheck_v28.json", "REPORT-GNC-rev1.md")
                    if os.path.exists(os.path.join(REV1, p))})


def part_t():
    pairs = {
        "relight_v28/mc6_runs_v28_liq_p0.81_A1_none_k2_v28.csv": f"{HUB}/01-systems-gnc/results/relight_v28/mc6_runs_v28_liq_p0.81_A1_none_k2_v28.csv.gz",
        "relight_v28/mc6_runs_v28_liq_p0.81_A1J_pc_k2_v28.csv": f"{HUB}/01-systems-gnc/results/relight_v28/mc6_runs_v28_liq_p0.81_A1J_pc_k2_v28.csv.gz",
        "regband/mc6_runs_rbl_B1_lead62_pc_k2_rb.csv": f"{HUB}/01-systems-gnc/results/regband/mc6_runs_rbl_B1_lead62_pc_k2_rb.csv.gz",
        "release_rule/rel_A1_none_rel1.csv": f"{REV1}/results/release_rule/rel_A1_none_rel1.csv.gz",
        "release_rule/rel_A1J_pc_rel1.csv": f"{REV1}/results/release_rule/rel_A1J_pc_rel1.csv.gz",
        "relight_v28/v28_case_v28_liq_p0.81_A1_none_k2.json": f"{HUB}/01-systems-gnc/results/relight_v28/v28_case_v28_liq_p0.81_A1_none_k2.json",
        "relight_v28/v28_case_v28_liq_p0.81_A1J_pc_k2.json": f"{HUB}/01-systems-gnc/results/relight_v28/v28_case_v28_liq_p0.81_A1J_pc_k2.json",
        "regband/rb_case_rbl_B1_lead62_pc_k2.json": f"{HUB}/01-systems-gnc/results/regband/rb_case_rbl_B1_lead62_pc_k2.json"}
    out = {}
    for w, h in pairs.items():
        a = open(f"{W}/out/{w}", "rb").read()
        b = gzip.open(h).read() if h.endswith(".gz") else open(h, "rb").read()
        out[w] = dict(work_sha16=sha(a)[:16], hub_sha16=sha(b)[:16], equal=(a == b))
    data = {}
    for f in ("engine_tables_v1.npz", "relay/engine_correction_v2.json", "regband/regband_model_v1.json",
              "tailoff/tailoff_fit_v1.json", "cea_N2O_ABS_eps3_v1.npz", "n2o_saturation_v1.npz"):
        a = open(f"{W}/gnc_dev28/data/{f}", "rb").read()
        b = open(f"{HUB}/01-systems-gnc/sim/data/{f}", "rb").read()
        data[f] = dict(sha16=sha(b)[:16], equal=(a == b), in_rev1_manifest=False)
    return dict(reference_tables=out, sim_data_dir=data,
                note="the rev1 manifest pins the simulator code but not its data/ directory; the hub copy in 01-systems-gnc/sim/data "
                     "equals the GNC dev tree byte for byte")


def comb_probe(p):
    try:
        b = open(p, "rb").read()
    except OSError as e:
        return dict(path=p, readable=False, error=f"{type(e).__name__}: {e}")
    d = json.loads(b)
    ig = d.get("igniter")
    seq = ig.get("sequence") if isinstance(ig, dict) else None
    return dict(path=p, readable=True, sha16=sha(b)[:16], version=d.get("version"), has_igniter=isinstance(ig, dict),
                has_igniter_sequence=isinstance(seq, dict),
                sequence_keys=sorted((seq or {}).get("v", {}).keys()) if isinstance(seq, dict) else None)


def part_i():
    probes = [comb_probe(p) for p in (f"{HUB}/interfaces/combustion.json", f"{W}/iface_v3c/combustion.json",
                                      f"{W}/gnc_dev28/data/iface_snapshot/combustion.json",
                                      f"{HUB}/01-systems-gnc/sim/data/iface_snapshot/combustion.json",
                                      "/mnt/project-files/engine/interfaces/combustion.json")]
    try:
        os.listdir("/mnt/project-files/engine/interfaces")
        mount = "readable"
    except OSError as e:
        mount = f"{type(e).__name__}: {e}"
    reb = json.load(open(f"{W}/out/gnc_json/rebuild_v3_check/gnc_v3_rebuild.json"))
    ick = reb["flight_software"]["relight_no_retry"]["v"]["interface_contradictions_kept"]
    return dict(probes=probes, default_GNC_IFACE="/mnt/project-files/engine/interfaces (sim6/run6/engine_v2/params default)",
                default_mount_status=mount,
                gnc_v3_rebuild_reads_igniter_sequence={k: v for k, v in ick.items() if k.startswith("combustion.json igniter")},
                fallback_logic="run6._json(): the GNC_IFACE file if it exists, else data/iface_snapshot (no version check, "
                               "no warning; the source label 'snapshot' is kept in run6._C but no script asserts it)")


def part_k():
    src = open(f"{HUB}/reviews/gnc/rg05_sens.py").read().splitlines()
    lines = [f"l.{i + 1}: {s.strip()}" for i, s in enumerate(src) if "thrust_scale" in s and "mod" in s]
    tabs = {}
    for k in ("1.00", "0.97", "0.95", "0.90"):
        b = gzip.open(f"{REV1}/results/cap_rule/cond_A1_k{k}.csv.gz").read()
        rows = list(csv.DictReader(io.StringIO(b.decode())))
        ts = sorted({float(r["thrust_scale"]) for r in rows})
        tabs[k] = dict(n=len(rows), P=sum(float(r["ok"]) > 0.5 for r in rows) / len(rows),
                       exhausted=sum(float(r["exhausted"]) > 0.5 for r in rows), thrust_scale_values=ts)
    return dict(reviewer_rg05_lines=lines, gnc_conditional_A1=tabs,
                run6_draw="thrust_scale ~ N(1, 0.05) per run (run6 l.402, l.1003)")


def main():
    out = dict(version="rv04_manifest_claims v1.0", date="2026-10-13", M=part_m(), T=part_t(), I=part_i(), K=part_k())
    with open(os.path.join(HERE, "rv04_manifest_claims.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(dict(M={k: out["M"][k] for k in ("manifest_sha16", "entries", "mismatches", "on_disk_not_in_manifest")},
                          T={k: v["equal"] for k, v in out["T"]["reference_tables"].items()},
                          I=[(p["path"], p.get("version"), p.get("has_igniter_sequence"), p.get("error")) for p in out["I"]["probes"]],
                          mount=out["I"]["default_mount_status"], K=out["K"]), indent=1)[:5000])


if __name__ == "__main__":
    main()

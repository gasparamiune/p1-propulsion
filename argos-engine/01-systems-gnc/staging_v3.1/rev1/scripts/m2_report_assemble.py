"""Assemble REPORT.md from the hand-written template and the M2 outputs (numbers resolved by script).

Template: report_src/REPORT_v2_template.md. Tokens {{kind:args[:fmt]}} are replaced from the result files:
  P:case                 success with Wilson 95 % interval      e.g. "P 0.984 [0.969, 0.992]"
  PM:case                P plus the paired comparison with the baseline (runs lost / gained, McNemar exact p)
  PR:case:key[:fmt]      field of the paired-comparison row (mc6_paired_v2.csv)
  T:case:key[:fmt]       field of the case table (results/mc6_cases_summary_v2.json)
  S:case:key[:fmt]       top-level field of the case in mc6_summary_v2.json (m_n2o_sized_kg, tank_V_L, ...)
  SS:case:key[:fmt]      field of the case's MC summary
  NOM:case:key[:fmt]     field of the case's nominal (no-dispersion) flight
  J:alias:path/to/key[:fmt]  any JSON output (aliases in FILES); '/' separates keys, list indices are integers
  TAB:Section title      the generated table block '## Section title' of report_tables_v2.md
  LIST:alias:path        a JSON list rendered as markdown bullets
Unresolved tokens stop the script with a list, so no placeholder reaches the report.
Output: GNC_REPORT (default /home/claude/work/space/report/REPORT.md).
Run after m2_report_tables.py: python scripts/m2_report_assemble.py
"""
import csv
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get("GNC_OUT", "/home/claude/work/space/out/m2")
RES = os.environ.get("GNC_RES", "/home/claude/work/space/out/results_v2")
DCO = os.environ.get("GNC_DC_OUT", "/home/claude/work/space/out/duty_cycles_v2")
VEH = os.environ.get("GNC_VEH_OUT", "/home/claude/work/space/out/vehicle")
TPL = os.environ.get("GNC_REPORT_TPL", os.path.join(ROOT, "report_src", "REPORT_v2_template.md"))
DEST = os.environ.get("GNC_REPORT", "/home/claude/work/space/report/REPORT.md")
GJ = os.path.join(os.path.dirname(OUT), "gnc_json", "gnc_v2.json")
FILES = {
    "gnc": GJ, "summary": os.path.join(OUT, "mc6_summary_v2.json"), "verify": os.path.join(OUT, "verify6_v2.json"),
    "csi": os.path.join(OUT, "csi_v2.json"), "ctd": os.path.join(OUT, "csi_timedomain_v2.json"),
    "dci": os.path.join(DCO, "duty_cycles_index_v2.json"), "veh": os.path.join(VEH, "vehicle_v3c.json"),
    "trade": os.path.join(RES, "trade_descent_v2.json"), "imu": os.path.join(RES, "imu_sweep_v2.json"),
    "fr": os.path.join(RES, "fin_roll_v2.json"), "er": os.path.join(RES, "engine_relay_v2.json"),
    "fx": os.path.join(RES, "mc6_failure_forensics_v2.json"), "cases": os.path.join(RES, "mc6_cases_summary_v2.json"),
}


def jl(p):
    with open(p) as f:
        return json.load(f)


def fmt(v, spec):
    if spec is None:
        if isinstance(v, float):
            return f"{v:.3g}"
        return str(v)
    if isinstance(v, str):
        try:
            v = float(v)
        except ValueError:
            return v
    if v is None:
        raise KeyError("value is null")
    return format(v, spec)


def dig(obj, path):
    for part in path.split("/"):
        if isinstance(obj, list):
            obj = obj[int(part)]
        else:
            obj = obj[part]
    return obj


def main():
    J = {k: jl(p) for k, p in FILES.items() if os.path.exists(p)}
    T = {r["case"]: r for r in J["cases"]["cases"]}
    S = J["summary"]["cases"]
    with open(os.path.join(RES, "mc6_paired_v2.csv")) as f:
        PR = {r["case"]: r for r in csv.DictReader(f)}
    with open(os.path.join(RES, "report_tables_v2.md")) as f:
        tabs_md = f.read()
    tabs = {}
    for blk in re.split(r"\n(?=## )", tabs_md):
        if blk.startswith("## "):
            title, _, body = blk.partition("\n")
            tabs[title[3:].strip()] = body.strip("\n")

    def Pc(c):
        t = T[c]
        return f"P {t['success']:.3f} [{t['ci95_lo']:.3f}, {t['ci95_hi']:.3f}]"

    def paired(c):
        p = PR.get(c)
        if not p or p.get("pairable") not in ("True", True):
            return ""
        return (f" ({int(p['base_ok_case_fail'])} runs lost / {int(p['base_fail_case_ok'])} gained against the baseline, "
                f"McNemar p = {float(p['mcnemar_exact_p']):.2g})")

    def resolve(tok):
        parts = tok.split(":")
        kind = parts[0]
        if kind == "TAB":
            return tabs[":".join(parts[1:])]
        if kind == "LIST":
            items = dig(J[parts[1]], parts[2])
            return "\n".join(f"- {x}" for x in items if x)
        if kind == "P":
            return Pc(parts[1])
        if kind == "PM":
            return Pc(parts[1]) + paired(parts[1])
        spec = None
        if kind in ("T", "S", "SS", "NOM", "PR") and len(parts) == 4:
            spec = parts[3]
        if kind == "J" and len(parts) == 4:
            spec = parts[3]
        if kind == "T":
            return fmt(T[parts[1]][parts[2]], spec)
        if kind == "PR":
            return fmt(PR[parts[1]][parts[2]], spec)
        if kind == "S":
            return fmt(S[parts[1]][parts[2]], spec)
        if kind == "SS":
            return fmt(S[parts[1]]["summary"][parts[2]], spec)
        if kind == "NOM":
            return fmt(S[parts[1]]["nominal"][parts[2]], spec)
        if kind == "J":
            return fmt(dig(J[parts[1]], parts[2]), spec)
        raise KeyError(kind)

    with open(TPL) as f:
        tpl = f.read()
    bad = []

    def sub(m):
        tok = m.group(1)
        try:
            return resolve(tok)
        except (KeyError, IndexError, ValueError, TypeError) as e:
            bad.append(f"{tok}: {e!r}")
            return m.group(0)
    out = re.sub(r"\{\{([^{}]+)\}\}", sub, tpl)
    if bad:
        print("UNRESOLVED TOKENS:\n  " + "\n  ".join(bad))
        sys.exit(1)
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    with open(DEST, "w") as f:
        f.write(out)
    print("written", DEST, len(out))


if __name__ == "__main__":
    main()

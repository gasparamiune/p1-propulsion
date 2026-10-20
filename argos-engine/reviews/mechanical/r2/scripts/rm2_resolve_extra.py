"""REV-MECH-2 (independent reviewer): extras from the reviewer's re-solve of fa1_c71/A1_22.2 steps TH + OP.

(1) Airframe-hole reaction totals (*NODE PRINT TOTALS=ONLY, 16 AF sets x 2 steps) of the re-solve .dat against FEA3D's stored
    f1.dat (same sets, same steps), and the sum of Fz per step.
(2) CalculiX's own stress error estimator (frd block ERROR, component STR(%)) at the governing nodes, both steps (an indicator of the
    local discretisation error of the L1 mesh; not a convergence proof).

usage: python -I rm2_resolve_extra.py <rs.dat> <stored f1.dat> <rs.frd> <out.json>
"""
from __future__ import annotations
import sys, re, json
from pathlib import Path

GOV = (8314, 580, 25946, 27955)


def parse_dat(p):
    out, step, key = {}, None, None
    for line in Path(p).read_text().splitlines():
        m = re.search(r"S T E P\s+(\d+)", line)
        if m:
            step = int(m.group(1))
            continue
        m = re.search(r"total force \(fx,fy,fz\) for set (\S+) and time", line)
        if m:
            key = (step, m.group(1))
            continue
        if key and line.strip():
            out[key] = [float(x) for x in line.split()]
            key = None
    return out


def err_at(frd):
    blk, res = None, {}
    with open(frd, "rt", errors="replace") as f:
        for line in f:
            if line.startswith(" -4"):
                blk = line.split()[1]
                continue
            if blk == "ERROR" and line.startswith(" -1"):
                nd = int(line[3:13])
                if nd in GOV:
                    res.setdefault(str(nd), []).append(float(line[13:25]))
            if line.startswith(" -3"):
                blk = None
    return res


def main(rsdat, f1dat, frd, outp):
    a, b = parse_dat(rsdat), parse_dat(f1dat)
    rows, mx = [], 0.0
    for k in sorted(a):
        if k[0] > 2:
            continue
        d = max(abs(x - y) for x, y in zip(a[k], b[k]))
        mx = max(mx, d)
        rows.append({"step": k[0], "set": k[1], "resolved_N": a[k], "stored_N": b[k], "max_abs_diff_N": d})
    sums = {s: {"resolved_Fz_N": round(sum(v[2] for k, v in a.items() if k[0] == s), 4),
                "stored_Fz_N": round(sum(v[2] for k, v in b.items() if k[0] == s), 4)} for s in (1, 2)}
    out = {"n_set_steps_compared": len(rows), "max_abs_diff_N": mx, "sum_Fz_per_step": sums,
           "ERROR_STR_percent_TH_OP_at_governing_nodes": err_at(frd), "rows": rows}
    Path(outp).write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:5])

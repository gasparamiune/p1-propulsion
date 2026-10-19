"""m2_repro_check v1 (2026-10-12): reproducibility check of stored Monte Carlo run files.
Compares, run by run, every numeric field two mc6 run CSVs have in common (exact equality; NaN == NaN) and reports the
mismatches. Used to show that results produced while sim6/run6 v2.6 was in development (some labelled 'sim6 v2.5' or
'v2.6-dev') are reproduced exactly by the promoted v2.6 code: the case is re-flown into another folder with the same
configuration and draws (seed 101) and the two CSVs are compared.
Usage: python scripts/m2_repro_check.py <stored.csv> <reflown.csv> [<stored.csv> <reflown.csv> ...]
Env: GNC_REPRO_OUT (optional JSON report path)."""
import csv
import json
import math
import os
import sys


def compare(a_path, b_path):
    a = list(csv.DictReader(open(a_path)))
    b = list(csv.DictReader(open(b_path)))
    keys = [k for k in a[0] if k in b[0]] if a and b else []
    mism, n = [], 0
    for i, (ra, rb) in enumerate(zip(a, b)):
        for k in keys:
            try:
                x, y = float(ra[k]), float(rb[k])
            except (TypeError, ValueError):
                continue
            n += 1
            if not (x == y or (math.isnan(x) and math.isnan(y))):
                mism.append(dict(run=i, field=k, stored=x, reflown=y))
    return dict(stored=a_path, reflown=b_path, runs=[len(a), len(b)], fields=len(keys), values_compared=n,
                mismatches=len(mism), first=mism[:10], identical=bool(len(a) == len(b) and not mism))


def main():
    args = sys.argv[1:]
    if len(args) < 2 or len(args) % 2:
        raise SystemExit(__doc__)
    res = [compare(args[i], args[i + 1]) for i in range(0, len(args), 2)]
    for r in res:
        print(os.path.basename(r["stored"]), "runs", r["runs"], "values", r["values_compared"], "mismatches", r["mismatches"],
              "IDENTICAL" if r["identical"] else r["first"][:3], flush=True)
    out = os.environ.get("GNC_REPRO_OUT")
    if out:
        with open(out, "w") as f:
            json.dump(dict(tool="m2_repro_check v1", checks=res, all_identical=all(r["identical"] for r in res)), f, indent=1)


if __name__ == "__main__":
    main()

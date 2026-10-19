"""m2_rev2p1_comparators v1.0 (GNC rev2.1, 2026-10-13; REV-GNC-3 RV3-09): every paired comparison used by a GNC rev2 claim,
with its comparator NAMED, recomputed from the STAGED rev2 tables (hub staging_v3.1/rev2/results/rg01_refly/*.csv.gz, manifest
MANIFEST_rev2.sha256 cb5d2c48e8d8fa27). No flight: statistics on stored tables only (same seed 101 draws, run index = pairing
key, checked by the 'run' and 'wind' columns of both tables).

Statistics: exact two-sided McNemar (binomial on the discordant pairs, scipy binomtest p = 0.5), Wilson 95 % on P;
"loses" = P below the comparator with p < 0.05 (adopted rule). lost = comparator ok and case failed; gained = the reverse.
Bases: main2 = A1_none + A1J_pc (pooled by concatenation of paired runs); all4 adds A1_pc and A1J_none where flown.
Comparator classes:
  C-LIQ   liq|none on the same base (and plateau / mass / target): total cost of the purge fix against the liquid plan
  C-SAME  the same arm without the factor under test (mass effect, trim effect, plateau effect, offset effect)
  C-LS    the liquid line with the same purge arm (line-state effect alone)
  C-DEC   the decided commit (e19|G73) for the late-commit arms; pw|G73 for the amendment-V arms
Output: $GNC_CMP_OUT (default out/rev3/rev2p1/comparators_rev2p1.json)."""
import csv
import gzip
import hashlib
import json
import math
import os

import numpy as np
from scipy.stats import binomtest

VERSION = "m2_rev2p1_comparators v1.0"
HUB = "/home/claude/work/shared-fallback/engine"
TAB = f"{HUB}/01-systems-gnc/staging_v3.1/rev2/results/rg01_refly"
MAN = f"{HUB}/01-systems-gnc/staging_v3.1/rev2/MANIFEST_rev2.sha256"
OUT = os.environ.get("GNC_CMP_OUT", "/home/claude/work/space/out/rev3/rev2p1/comparators_rev2p1.json")
MAIN2 = ("A1_none", "A1J_pc")
ALL4 = ("A1_none", "A1J_pc", "A1_pc", "A1J_none")

# (claim, case arm, comparator arm, class, bases, note). Bases tuple: pooled over those bases (and reported per base).
CMP = [
    # RG-01 line states and purge (report s1)
    ("RG01-purge-liq", "liq|G73", "liq|none", "C-LIQ", MAIN2, "purge mass on the liquid line (decided path)"),
    ("RG01-purge-liq-all4", "liq|G73", "liq|none", "C-LIQ", ALL4, "four-base pool; the rev2 LOSES statement"),
    ("RG01-pw", "pw|G73", "liq|none", "C-LIQ", MAIN2, "purged worst"),
    ("RG01-pw-all4", "pw|G73", "liq|none", "C-LIQ", ALL4, ""),
    ("RG01-pl", "pl|G73", "liq|none", "C-LIQ", MAIN2, "purged least"),
    ("RG01-pl-all4", "pl|G73", "liq|none", "C-LIQ", ALL4, ""),
    ("RG01-e19", "e19|G73", "liq|none", "C-LIQ", MAIN2, "Tp1.9 robust edge"),
    ("RG01-e19-all4", "e19|G73", "liq|none", "C-LIQ", ALL4, ""),
    ("RG01-pw-vs-liqG73", "pw|G73", "liq|G73", "C-LS", MAIN2, "line-state effect alone"),
    ("RG01-pl-vs-liqG73-all4", "pl|G73", "liq|G73", "C-LS", ALL4, ""),
    ("RG01-G76", "liq|G76", "liq|none", "C-LIQ", MAIN2, "76 g purge bound"),
    ("RG01-PS10-liq", "liq|PS10", "liq|none", "C-LIQ", MAIN2, "rev1 bounding purge"),
    ("RG01-pwG76", "pw|G76", "liq|none", "C-LIQ", MAIN2, ""),
    ("RG01-pwPS10", "pw|PS10", "liq|none", "C-LIQ", MAIN2, ""),
    ("RG01-prep-liq", "liqP|G73", "liq|none", "C-LIQ", MAIN2, "UNKNOWN = UNPRIMED prep path, plan 1.41 s"),
    ("RG01-prep-liq-A1none", "liqP|G73", "liq|none", "C-LIQ", ("A1_none",), "per-base loss"),
    ("RG01-prep-liq-vs-liqG73", "liqP|G73", "liq|G73", "C-SAME", MAIN2, "prep path alone"),
    ("RG01-prep-pw", "pwP|G73", "liq|none", "C-LIQ", MAIN2, ""),
    ("RG01-prep-pw-vs-pwG73", "pwP|G73", "pw|G73", "C-SAME", MAIN2, "prep path alone"),
    ("RG01-nrLO", "nrLO|none", "liq|none", "C-LIQ", MAIN2, "PURGE NOT RUN LO (P|lit only; P_abort 0.242 applies)"),
    ("RG01-nrLOz", "nrLO|G73z", "liq|none", "C-LIQ", MAIN2, "sequence and booking flown, no flow"),
    ("RG01-bf", "bf|G73", "liq|none", "C-LIQ", MAIN2, "BLEED_FAULT 31.24 g/s from E0"),
    # plateau and P0 offset (report s1)
    ("PLAT-pw", "pw|G73|L400", "liq|G73|L400", "C-LS", MAIN2, "the rev2 comparator"),
    ("PLAT-pw-liqnone", "pw|G73|L400", "liq|none|L400", "C-LIQ", MAIN2, ""),
    ("PLAT-pw-same", "pw|G73|L400", "pw|G73", "C-SAME", MAIN2, "plateau effect"),
    ("PLAT-liq", "liq|G73|L400", "liq|none|L400", "C-LIQ", MAIN2, ""),
    ("PLAT-liqnone-same", "liq|none|L400", "liq|none", "C-SAME", MAIN2, "plateau effect on the liquid plan"),
    ("PLATO-pw-ls", "pw|G73|L400o", "liq|G73|L400o", "C-LS", MAIN2, "the only comparator named in rev2"),
    ("PLATO-pw-nominal", "pw|G73|L400o", "pw|G73", "C-SAME", MAIN2, "plateau + P0 offset vs the nominal decided arm (RV3-09)"),
    ("PLATO-pw-L400", "pw|G73|L400o", "pw|G73|L400", "C-SAME", MAIN2, "offset alone (plateau on both sides)"),
    ("PLATO-liq-L400", "liq|G73|L400o", "liq|G73|L400", "C-SAME", MAIN2, "offset alone on the liquid line"),
    ("PLATO-liq-liqnone", "liq|G73|L400o", "liq|none|L400", "C-LIQ", MAIN2, ""),
    ("PLAT-e19-liqnone", "e19|G73|L400", "liq|none|L400", "C-LIQ", MAIN2, "0.81 s plan exceeded (e19 + plateau)"),
    ("PLAT-e19-liqG73", "e19|G73|L400", "liq|G73|L400", "C-LS", MAIN2, ""),
    ("PLAT-e19-same", "e19|G73|L400", "e19|G73", "C-SAME", MAIN2, "plateau effect on e19"),
    ("PLAT-bf", "bf|G73|L400", "liq|none|L400", "C-LIQ", MAIN2, ""),
    # +0.60 kg (report s3; RV3-09: purge effect at +0.60 kg vs mass effect)
    ("M60-purge-liq", "liq|G73|m60", "liq|none|m60", "C-LIQ", MAIN2, "PURGE effect at +0.60 kg (the rev2 comparator)"),
    ("M60-purge-liq-A1none", "liq|G73|m60", "liq|none|m60", "C-LIQ", ("A1_none",), "per-base loss in rev2"),
    ("M60-purge-pw", "pw|G73|m60", "liq|none|m60", "C-LIQ", MAIN2, "PURGE + line state at +0.60 kg (rev2 comparator)"),
    ("M60-mass-liqnone", "liq|none|m60", "liq|none", "C-SAME", MAIN2, "MASS effect, no purge"),
    ("M60-mass-liq", "liq|G73|m60", "liq|G73", "C-SAME", MAIN2, "MASS effect on liq|G73"),
    ("M60-mass-pw", "pw|G73|m60", "pw|G73", "C-SAME", MAIN2, "MASS effect on pw|G73"),
    ("M60-total-liq", "liq|G73|m60", "liq|none", "C-LIQ", MAIN2, "mass + purge vs the liquid plan without either"),
    ("M60-total-pw", "pw|G73|m60", "liq|none", "C-LIQ", MAIN2, ""),
    # apogee trim (report s1)
    ("TRIM-liq-h285-same", "liq|G73|h285", "liq|G73", "C-SAME", MAIN2, "trim effect (300 -> 285 m)"),
    ("TRIM-pw-h285-same", "pw|G73|h285", "pw|G73", "C-SAME", MAIN2, "trim effect"),
    ("TRIM-liq-h285-liqnone300", "liq|G73|h285", "liq|none", "C-LIQ", MAIN2, "vs the liquid plan at 300 m"),
    ("TRIM-pw-h285-liqnone300", "pw|G73|h285", "liq|none", "C-LIQ", MAIN2, ""),
    ("TRIM-liq-h290-same", "liq|G73|h290", "liq|G73", "C-SAME", MAIN2, ""),
    ("TRIM-pw-h290-same", "pw|G73|h290", "pw|G73", "C-SAME", MAIN2, ""),
    ("TRIM-liq-h280-same", "liq|G73|h280", "liq|G73", "C-SAME", MAIN2, ""),
    ("TRIM-pw-h280-same", "pw|G73|h280", "pw|G73", "C-SAME", MAIN2, ""),
    ("TRIM-m60-liq-h275-same", "liq|G73|m60|h275", "liq|G73|m60", "C-SAME", MAIN2, ""),
    ("TRIM-m60-pw-h275-same", "pw|G73|m60|h275", "pw|G73|m60", "C-SAME", MAIN2, ""),
    # amendment G late commit (report s2)
    ("G-late-hf100", "e19|G73|hf100", "e19|G73", "C-DEC", MAIN2, "forced commit at 100 m vs the decided commit"),
    ("G-late-hf90", "e19|G73|hf90", "e19|G73", "C-DEC", MAIN2, ""),
    ("G-late-hf80", "e19|G73|hf80", "e19|G73", "C-DEC", MAIN2, ""),
    ("G-late-hf70", "e19|G73|hf70", "e19|G73", "C-DEC", MAIN2, ""),
    ("G-late-ant0", "e19|G73|ant0", "e19|G73", "C-DEC", MAIN2, "commit at the plain trigger"),
    # amendment V (report s6)
    ("V-R0", "pw|G73|pcfR0", "pw|G73", "C-DEC", MAIN2, "Pc invalid from E2, decided predicate only"),
    ("V-R1", "pw|G73|pcfR1", "pw|G73", "C-DEC", MAIN2, "interim time-only term"),
    ("V-R2", "pw|G73|pcfR2", "pw|G73", "C-DEC", MAIN2, "accelerometer-gated"),
    ("V-R3", "pw|G73|pcfR3", "pw|G73", "C-DEC", MAIN2, "hold and abort"),
    ("V-R1k875", "pw|G73|pcfR1k875", "pw|G73", "C-DEC", MAIN2, "open-loop factor 0.875"),
    ("V-R2k875", "pw|G73|pcfR2k875", "pw|G73", "C-DEC", MAIN2, ""),
    ("V-R1L400", "pw|G73|pcfR1L400", "pw|G73|L400", "C-SAME", MAIN2, "with the plateau, vs the plateau arm with Pc valid"),
    ("V-R2L400", "pw|G73|pcfR2L400", "pw|G73|L400", "C-SAME", MAIN2, ""),
    ("V-R2-vs-R1", "pw|G73|pcfR2", "pw|G73|pcfR1", "C-SAME", MAIN2, "R2 vs R1 with the engine lit"),
    ("V-R2L400-vs-R1L400", "pw|G73|pcfR2L400", "pw|G73|pcfR1L400", "C-SAME", MAIN2, ""),
]


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def load(base, arm):
    p = os.path.join(TAB, f"rf_{base}_{arm.replace('|', '_')}.csv.gz")
    if not os.path.exists(p):
        return None, p
    with gzip.open(p, "rt") as f:
        return list(csv.DictReader(f)), p


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return [float("nan"), float("nan")]
    p = k / n
    den = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [(c - h) / den, (c + h) / den]


def mcnemar(a, b):
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    lost, gained = int(np.sum(a & ~b)), int(np.sum(~a & b))
    p = float(binomtest(lost, lost + gained, 0.5).pvalue) if lost + gained else 1.0
    return dict(P_comparator=float(a.mean()), P_case=float(b.mean()), lost=lost, gained=gained, p_exact=p, n=int(a.size),
                loses=bool(b.mean() < a.mean() and p < 0.05), P_case_wilson=wilson(int(b.sum()), int(b.size)))


def main():
    man = {}
    for ln in open(MAN):
        h, n = ln.split(None, 1)
        man[n.strip().lstrip("*").lstrip("./")] = h
    used, bad = {}, []
    out = dict(version=VERSION, date="2026-10-13", tables=TAB, manifest=f"{MAN} (sha256/16 {sha16(MAN)})",
               method=__doc__.split("\n\n")[1].strip(), rows=[], missing=[])
    for claim, case, comp, cls, bases, note in CMP:
        A, B, per = [], [], {}
        miss = False
        for b in bases:
            rc, pc = load(b, case)
            ra, pa = load(b, comp)
            if rc is None or ra is None:
                out["missing"].append(dict(claim=claim, base=b, case_file=pc if rc is None else None,
                                           comparator_file=pa if ra is None else None))
                miss = True
                continue
            for p_ in (pc, pa):
                rel = os.path.relpath(p_, os.path.dirname(MAN))
                h = hashlib.sha256(open(p_, "rb").read()).hexdigest()
                used[rel] = h[:16]
                if man.get(rel) != h:
                    bad.append(rel)
            # pairing key check: same run index and the same drawn wind in both tables
            if [r["run"] for r in rc] != [r["run"] for r in ra] or [r["wind"] for r in rc] != [r["wind"] for r in ra]:
                raise SystemExit(f"pairing broken: {claim} {b}")
            okc = [float(r["ok"]) > 0.5 for r in rc]
            oka = [float(r["ok"]) > 0.5 for r in ra]
            per[b] = mcnemar(oka, okc)
            per[b]["exhausted_case"] = int(sum(float(r["exhausted"]) > 0.5 for r in rc))
            per[b]["exhausted_comparator"] = int(sum(float(r["exhausted"]) > 0.5 for r in ra))
            A += oka
            B += okc
        if not A:
            continue
        row = dict(claim=claim, case=case, comparator=comp, comparator_class=cls, bases=list(bases), note=note,
                   pooled=mcnemar(A, B), per_base=per, complete=not miss)
        out["rows"].append(row)
        e = row["pooled"]
        print(f"{claim:26s} {case:18s} vs {comp:16s} [{'+'.join(bases)}] {e['P_case']:.4f} vs {e['P_comparator']:.4f} "
              f"-{e['lost']}/+{e['gained']} p {e['p_exact']:.3g}{' LOSES' if e['loses'] else ''}", flush=True)
    out["tables_used_sha256_16"] = used
    out["manifest_mismatches"] = bad
    out["all_tables_manifest_verified"] = not bad
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    print("wrote", OUT, sha16(OUT), "tables", len(used), "manifest mismatches", len(bad), "missing", len(out["missing"]))


if __name__ == "__main__":
    main()

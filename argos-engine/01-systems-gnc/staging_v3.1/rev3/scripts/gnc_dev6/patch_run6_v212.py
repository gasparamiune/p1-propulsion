"""patch_run6_v212 v1.0 (GNC rev3, 2026-10-13): run6 v2.12-dev, the parameter of sim6 v2.12-dev amendment V3 (pv2_rhF, ECU
command flown during the release hold of the unpurged-relight comparator; off by default, 0). Source run6 v2.11-dev
d6b91f1649048254; every anchor must occur exactly once."""
import hashlib
import sys

P = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/work/space/gnc_dev6/gncsim/run6.py"
SRC16 = "d6b91f1649048254"
s = open(P).read()
h = hashlib.sha256(s.encode()).hexdigest()[:16]
if h != SRC16:
    raise SystemExit(f"{P}: sha256/16 {h} != v2.11-dev {SRC16} (already patched?)")


def rep(old, new, count=1):
    global s
    n = s.count(old)
    if n != count:
        raise SystemExit(f"anchor found {n} times (expected {count}): {old[:90]!r}")
    s = s.replace(old, new)


rep('"""run6 v2.11-dev (v2.11-dev amendment L', '"""run6 v2.12-dev (v2.12-dev amendment V3 (pv2_rhF: ECU command flown during the '
    'release hold of the unpurged-relight comparator, LEAD line 194 (3)); v2.11-dev amendment L')
rep('''DEF.update(flt_dla=-1.0)
''', '''DEF.update(flt_dla=-1.0)
# v2.12-dev amendment V3 (command profile during the release hold; sim6 pv2_rhF), off by default
DEF.update(pv2_rhF=0.0)
''')
rep('''    S("pv2_rh", float(cfg["pv2_rh"]), "PROPOSAL LEAD line 186 (1) alternative (unpurged relight): no release before E2 + pv2_rh "
                                      "[s]; 0 = off")
''', '''    S("pv2_rh", float(cfg["pv2_rh"]), "PROPOSAL LEAD line 186 (1) alternative (unpurged relight): no release before E2 + pv2_rh "
                                      "[s]; 0 = off")
    S("pv2_rhF", float(cfg["pv2_rhF"]), "COMPARATOR LEAD line 194 (3) / REV-COMB-3 R3-01: ECU command [N] flown from E2 until the "
                                        "held release (200 / 500 N = Combustion's ramp profiles; sim6 v2.12-dev V3); 0 = off")
''')
open(P, "w").write(s)
print("patched", P, hashlib.sha256(s.encode()).hexdigest()[:16])

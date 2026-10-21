"""REV-MECH-2 (independent reviewer) helper, own code; reads FEA3D stored decks/fields read-only via rm2_repost / rm2_modal.
Origin: scratchpad helper dup_dload.py, copied unchanged below this docstring for the review record (2026-10-20).
"""
import sys, json
import numpy as np
from collections import Counter
sys.path.insert(0, "/home/claude/work/shared-fallback/engine/reviews/mechanical/r2/scripts")
import rm2_repost as RP
for run, state in (("fa1_c71", "A1_22.2"), ("modal_v351ca2b_c71", "B1_21.65")):
    z, meta = RP.load_deck(run, state)
    for sname in ("OP", "PM"):
        i = [s["i"] for s in meta["steps"] if s["name"] == sname][0]
        DL = z[f"DL_{i}"]
        keys = [(int(a), int(b)) for a, b, _ in DL]
        c = Counter(keys)
        dup = {k: v for k, v in c.items() if v > 1}
        CL = z[f"CL_{i}"]
        ck = Counter([(int(a), int(b)) for a, b, _ in CL])
        cdup = {k: v for k, v in ck.items() if v > 1}
        print(f"{run} {sname}: dload entries {len(DL)} unique faces {len(c)} duplicated faces {len(dup)} (max mult {max(c.values())}); "
              f"cload entries {len(CL)} unique node-dof {len(ck)} duplicated {len(cdup)} (max mult {max(ck.values()) if ck else 0})")

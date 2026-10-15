"""REV-GNC-5 v01: resolve every pin of the three rev3 pin lists against the reviewer snapshot / hub copies (read-only)."""
import hashlib, os, sys
V = sys.argv[1]; H = "/home/claude/work/shared-fallback/engine"
cands = {"v3d": [f"{V}/snap/iface_v3d"], "v35a": [f"{V}/snap/iface_v35a"]}
extra = [f"{H}/06-electronics/results", f"{H}/02-combustion/data/v2p4", f"{H}/02-combustion/data/v2p4a", f"{H}/02-combustion/data/v2/v2p4", f"{H}/03-cad/calcs"]
def h(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
bad = 0
for pl, key in (("pins_rev3.sha256", "v3d"), ("pins_rev3_v35a.sha256", "v35a"), ("pins_rev3_v35a_cold.sha256", "v35a")):
    print("==", pl, h(f"{V}/snap/pins_rev3/{pl}")[:16])
    for line in open(f"{V}/snap/pins_rev3/{pl}"):
        sha, name = line.split()
        found = [os.path.join(d, name) for d in cands[key] + extra if os.path.exists(os.path.join(d, name))]
        ok = [h(p) == sha for p in found]
        st = "OK" if found and all(ok) else ("MISSING" if not found else "MISMATCH")
        bad += st != "OK"
        print(f"   {st:8s} {name:32s} {sha[:16]} <- {found[0] if found else '-'}")
print("pin problems", bad)

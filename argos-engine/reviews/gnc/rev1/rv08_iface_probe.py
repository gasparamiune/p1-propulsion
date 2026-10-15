"""rv08_iface_probe v1.0 (REV-GNC-R1, independent reviewer, 2026-10-13).

Question: GNC rev1 says the live hub interface set has drifted ("live hub combustion.json no longer has igniter.sequence") and
pins its runs to /home/claude/work/space/iface_v3c. Which interface file actually differs, and can the rev1 simulator build its
parameter vector from the live hub set?
Method: copy the live hub interface files (combustion, electronics, mechanical, ENGINE-BASELINE) plus the pinned throttle map into
a reviewer scratch folder; in a fresh interpreter per interface set (one process at a time, nice 10, NUMBA_NUM_THREADS=1), import
run6 from the reviewer's scratch copy of the rev1 simulator (run6 35b5c808487b9339, sim6 f9094b63e64f2324) with GNC_IFACE set,
and call run6.build(run6.cfg_of(m_n2o=2.0)). Record the source labels, the electronics.json version and the result.
Reads only (hub, GNC work area); writes rv08_iface_probe.json here and the hub-copy folder in the reviewer scratch.
"""
import hashlib
import json
import os
import shutil
import subprocess

SCR = "/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad"
COPY = f"{SCR}/rev1copy"
HUB_IF = "/home/claude/work/shared-fallback/engine/interfaces"
PIN = "/home/claude/work/space/iface_v3c"
PROBE = f"{SCR}/iface_hub_probe"
HERE = os.path.dirname(os.path.abspath(__file__))
FILES = ("combustion.json", "electronics.json", "mechanical.json", "ENGINE-BASELINE-v0.json")

CODE = r"""
import json, os, sys, traceback
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[1])
from gncsim import run6 as R
r = dict(iface=R.IFACE)
try:
    src = R.sources()
    r.update(sources=[src.get("comb_src"), src.get("el_src"), src.get("mech_src")], el_version=(src.get("el") or {}).get("version"))
    out = R.build(R.cfg_of(m_n2o=2.0))
    r.update(build="OK", n_par=len(out[0]))
except Exception as e:
    tb = traceback.extract_tb(sys.exc_info()[2])[-1]
    r.update(build="FAILED", error=f"{type(e).__name__}: {e}", at=f"{os.path.basename(tb.filename)} l.{tb.lineno}: {tb.line}")
print(json.dumps(r))
"""


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def main():
    os.makedirs(PROBE, exist_ok=True)
    for f in FILES:
        shutil.copy2(os.path.join(HUB_IF, f), os.path.join(PROBE, f))
    shutil.copy2(os.path.join(PIN, "throttle_map_v2.csv"), os.path.join(PROBE, "throttle_map_v2.csv"))
    files = {f: dict(hub=sha16(os.path.join(HUB_IF, f)), pin=sha16(os.path.join(PIN, f)),
                     equal=sha16(os.path.join(HUB_IF, f)) == sha16(os.path.join(PIN, f))) for f in FILES}
    env = dict(os.environ, NUMBA_NUM_THREADS="1", NUMBA_CACHE_DIR=f"{SCR}/numba_cache_rev1",
               GNC_ACT_RATE=f"{PIN}/actuator_rate_check_v2.json")
    runs = {}
    for name, iface in (("live_hub_copy", PROBE), ("gnc_pin_iface_v3c", PIN)):
        e = dict(env, GNC_IFACE=iface)
        p = subprocess.run(["nice", "-n", "10", "/opt/engine-venv/bin/python", "-I", "-c", CODE, COPY], env=e, cwd=SCR,
                           capture_output=True, text=True, timeout=600)
        line = [ln for ln in p.stdout.splitlines() if ln.startswith("{")]
        runs[name] = json.loads(line[-1]) if line else dict(build="NO OUTPUT", stderr=p.stderr[-800:])
    out = dict(version="rv08_iface_probe v1.0", date="2026-10-13", simulator=dict(run6=sha16(f"{COPY}/gncsim/run6.py"),
               sim6=sha16(f"{COPY}/gncsim/sim6.py")), interface_files=files, runs=runs,
               reading=("the live hub and the GNC pin differ only in electronics.json (hub v2, pin v1); combustion.json is "
                        "byte-identical; run6.build reads actuators.tvc_A.dynamics_for_GNC, which electronics.json v2 removed "
                        "as superseded, so the rev1 simulator cannot build from the live hub set"))
    with open(os.path.join(HERE, "rv08_iface_probe.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()

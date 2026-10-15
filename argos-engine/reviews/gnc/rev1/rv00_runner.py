"""rv00_runner v1.0 (REV-GNC-R1, independent reviewer, 2026-10-13).

Runs one GNC rev1 script from the reviewer's scratch copy under `python -I` (isolated mode does not put the script
directory on sys.path, so it is inserted here). The copy layout is <copy>/gncsim (= rev1/sim/gncsim_v2.8-dev_MWFPRS),
<copy>/scripts (= rev1/scripts) and <copy>/data (= hub 01-systems-gnc/sim/data); every copied file was checked against
MANIFEST_rev1.sha256 (114 files, 0 mismatches) and the data files against the GNC dev tree (byte-equal).

Usage: nice -n 10 /opt/engine-venv/bin/python -I rv00_runner.py <copy>/scripts/<script>.py [args]
All output folders must be redirected by environment variables before the call (see rv01_rerun.sh); this runner
writes nothing itself and does not modify the GNC staging or the GNC work area.
"""
import os
import runpy
import sys

script = os.path.abspath(sys.argv[1])
if "/shared-fallback/engine/01-systems-gnc/" in script or script.startswith("/home/claude/work/space/"):
    raise SystemExit("refusing to run a script in place in the GNC staging or work area; run the scratch copy")
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(script))
sys.argv = [script] + sys.argv[2:]
runpy.run_path(script, run_name="__main__")

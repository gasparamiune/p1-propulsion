"""m2_eng11_fe_q v1.0 (GNC rev4b, 2026-10-19): second-queue wrapper for m2_eng11_fe v1.0 (imported unchanged).
Runs GNC_E11FE_VARIANTS like PART=run, but writes through its own temporary file name (<out>.tmpq) so that two
queues can never interleave writes on one temporary file; os.replace keeps every write atomic.  Rows are deterministic
(same code, same inputs), so a variant computed by both queues ends identical whichever process writes last; each
process's final write holds every row and done=True.  No numerical change."""
import json
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m2_eng11_fe as F  # noqa: E402


def jdump_q(obj, path):
    tmp = path + ".tmpq"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, default=str)
    os.replace(tmp, path)


F.jdump = jdump_q

if __name__ == "__main__":
    F.main()

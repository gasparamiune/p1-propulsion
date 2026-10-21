# REV-ELEC-5: reviewer copy of the v2.13 engine_ecu.cpp with the light-window hold disabled for the T_c update only (probe discrimination
# control; never a deliverable). Usage: python3 -I make_nohold.py <in engine_ecu.cpp> <out engine_ecu.cpp>
import sys
src = open(sys.argv[1]).read()
old = "  else if (!hold && !seat_step_) {"
assert src.count(old) == 1, "anchor not unique"
new = "#ifdef REV5_NO_HOLD\n  else if (!seat_step_) {   // REV-ELEC-5 reviewer variant: no hold for T_c\n#else\n" + old + "\n#endif"
open(sys.argv[2], "w").write(src.replace(old, new))
print("patched 1 site")

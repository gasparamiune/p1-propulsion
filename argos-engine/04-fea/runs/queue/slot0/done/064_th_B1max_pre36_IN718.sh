set -e
cd /home/claude/work/mechanical/engine/04-fea/thermal
# lead 2026-10-13 relay 3 (seal table, every seal B1/A1 in-burn + soak): B1 max dispersed cycle (governs B1 thermal; B1max_tg711 is 1.3 % lower)
# with the IN718 TC-03 baseline and TC-06 3.6 mm (D_pre 49.9)
/opt/engine-venv/bin/python -u run_thermal.py --dc DC-B1v3max --bound hi --level 2.5 --ov D_pre=0.0499 --mat ENG-TC-03=IN718 --tag v11pre36IN > /home/claude/work/mechanical/runs/thermal/DC-B1v3max_hi_L2.5_v11pre36IN.log 2>&1
/opt/engine-venv/bin/python -u extract_histories.py DC-B1v3max_hi_SS316L_L2.5_v11pre36IN > /home/claude/work/mechanical/runs/thermal/DC-B1v3max_hi_L2.5_v11pre36IN_extract.log 2>&1

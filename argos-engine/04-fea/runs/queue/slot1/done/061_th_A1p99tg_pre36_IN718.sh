set -e
cd /home/claude/work/mechanical/engine/04-fea/thermal
# lead 2026-10-13: ENG-TC-03 seat insert -> Inconel 718 (engmat v1.1 IN718, k 11.4 W/mK at 20 C); TC-06 3.6 mm (D_pre 49.9)
/opt/engine-venv/bin/python -u run_thermal.py --dc DC-A1dispp99_tg711 --bound hi --level 2.5 --ov D_pre=0.0499 --mat ENG-TC-03=IN718  --tag v11pre36IN > /home/claude/work/mechanical/runs/thermal/DC-A1dispp99_tg711_hi_L2.5_v11pre36IN.log 2>&1
/opt/engine-venv/bin/python -u extract_histories.py DC-A1dispp99_tg711_hi_SS316L_L2.5_v11pre36IN > /home/claude/work/mechanical/runs/thermal/DC-A1dispp99_tg711_hi_L2.5_v11pre36IN_extract.log 2>&1

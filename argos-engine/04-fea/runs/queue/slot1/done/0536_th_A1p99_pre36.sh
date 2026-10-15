set -e
cd /home/claude/work/mechanical/engine/04-fea/thermal
/opt/engine-venv/bin/python -u run_thermal.py --dc DC-A1dispp99 --bound hi --level 2.5 --ov D_pre=0.0499 --tag v11pre36 > /home/claude/work/mechanical/runs/thermal/DC-A1dispp99_hi_L2.5_v11pre36.log 2>&1
/opt/engine-venv/bin/python -u extract_histories.py DC-A1dispp99_hi_SS316L_L2.5_v11pre36 > /home/claude/work/mechanical/runs/thermal/DC-A1dispp99_hi_L2.5_v11pre36_extract.log 2>&1

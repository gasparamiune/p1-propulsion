set -e
cd /home/claude/work/mechanical/engine/04-fea/thermal
/opt/engine-venv/bin/python -u run_thermal.py --dc DC-A1dispp99_tg711 --bound hi --level 2.5 --tag v11 > /home/claude/work/mechanical/runs/thermal/DC-A1dispp99_tg711_hi_L2.5_v11.log 2>&1
/opt/engine-venv/bin/python -u extract_histories.py DC-A1dispp99_tg711_hi_SS316L_L2.5_v11 > /home/claude/work/mechanical/runs/thermal/DC-A1dispp99_tg711_hi_L2.5_v11_extract.log 2>&1

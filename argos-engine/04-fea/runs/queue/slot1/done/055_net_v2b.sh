set -e
cd /home/claude/work/mechanical/engine/04-fea/thermal
/opt/engine-venv/bin/python -u servo_mount_net.py DC-A1dispp99_tg711_hi_SS316L_L2.5_v11 DC-B1v3max_tg711_hi_SS316L_L2.5_v11 --variants V3 --vent 0,0.1,0.2,0.3,0.5 --hbay 2,5,10 --version v2 --out servo_mount_net_v2b.json > /home/claude/work/mechanical/engine/04-fea/thermal/networks/servo_mount_net_v2b.log 2>&1

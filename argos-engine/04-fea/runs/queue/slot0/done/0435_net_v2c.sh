set -e
cd /home/claude/work/mechanical/engine/04-fea/thermal
# v2c: V3 mount on the TC-06 3.6 mm (pre36) dispersed B1 histories, vent sweep incl. closed bay (lead 2026-10-13: vent REQUIRED unless pre36 passes without it)
/opt/engine-venv/bin/python -u servo_mount_net.py DC-B1v3p99_tg711_hi_SS316L_L2.5_v11pre36 DC-B1v3max_hi_SS316L_L2.5_v11pre36 --variants V3 --vent 0,0.1,0.2,0.3 --hbay 2,5,10 --version v2 --out servo_mount_net_v2c.json > /home/claude/work/mechanical/engine/04-fea/thermal/networks/servo_mount_net_v2c.log 2>&1

#!/bin/bash
# rev4 P2 queue runner: $1 = variant(s), $2 = base, $3 = iface, $4 = pin, $5 = log
cd /home/claude/work/space/gnc_dev3/scripts
source m2r3_env.sh
export GNC_IFACE=$3 GNC_IFACE_PIN=$4 GNC_ACT_RATE=$3/actuator_rate_check_v2.json
export GNC_P2_VARIANTS=$1 GNC_P2_BASES=$2 GNC_P2_PARTS=mc
nice -n 10 $PY m2_rev4_p2.py >> $5 2>&1
echo "EXIT $?" >> $5

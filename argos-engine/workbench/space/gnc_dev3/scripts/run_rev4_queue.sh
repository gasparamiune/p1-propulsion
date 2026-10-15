#!/bin/bash
# rev4 slot queue: wait for PID $1 to exit, then run each job in order. Job = "iface|pin|ENV=V ENV2=V2 ...|log".
# Jobs are passed as the remaining arguments. Each job sources m2r3_env.sh, overrides the interface set, runs nice'd.
WAIT=$1; shift
while kill -0 "$WAIT" 2>/dev/null; do sleep 15; done
cd /home/claude/work/space/gnc_dev3/scripts
for job in "$@"; do
  IFS='|' read -r IF PIN ENVS LOG <<< "$job"
  (
    source m2r3_env.sh
    export GNC_IFACE=$IF GNC_IFACE_PIN=$PIN GNC_ACT_RATE=$IF/actuator_rate_check_v2.json
    for kv in $ENVS; do export "$kv"; done
    echo "== $(date -u +%FT%TZ) start: $ENVS (iface $IF)" >> "$LOG"
    nice -n 10 $PY m2_rev4_p2.py >> "$LOG" 2>&1
    echo "EXIT $? $(date -u +%FT%TZ)" >> "$LOG"
  )
done

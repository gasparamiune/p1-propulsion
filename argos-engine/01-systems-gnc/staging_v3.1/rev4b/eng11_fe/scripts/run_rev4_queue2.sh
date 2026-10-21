#!/bin/bash
# rev4 slot queue v2 (GNC, 2026-10-13): wait for PID $1 to exit (none: 0), then run each job in order.
# Job = "dir#script#iface#pin#ENV=V ENV2=V2 ...#log" ('#' separates fields; env values may contain '|' and ';').
# nice 10; one heavy process per queue; kill by PID only.
WAIT=$1; shift
if [ "$WAIT" != "0" ]; then while kill -0 "$WAIT" 2>/dev/null; do sleep 15; done; fi
for job in "$@"; do
  IFS='#' read -r DIR SCR IF PIN ENVS LOG <<< "$job"
  (
    cd "$DIR" || exit 9
    source /home/claude/work/space/gnc_dev3/scripts/m2r3_env.sh
    export GNC_IFACE=$IF GNC_IFACE_PIN=$PIN GNC_ACT_RATE=$IF/actuator_rate_check_v2.json
    for kv in $ENVS; do export "$kv"; done
    echo "== $(date -u +%FT%TZ) start: $SCR $ENVS (iface $IF)" >> "$LOG"
    nice -n 10 $PY $SCR >> "$LOG" 2>&1
    echo "EXIT $? $(date -u +%FT%TZ)" >> "$LOG"
  )
done

#!/bin/bash
# REV-GNC-5 v04: sequential re-fly sample (one process, nice 10). Batch A on iface_v3d / pins_rev3, batch B on iface_v35a / pins_rev3_v35a.
source /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/env5.sh
cd /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5
echo "=== $(date -u +%H:%M:%S) batch A"
nice -n 10 $PY /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/scripts/guard_run.py /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/scripts/v03_refly.py /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/tree /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/out/refly \
  "A1_none:e19|G73|ant13|h285" "A1J_pc:e19|G73|ant17|h285" "A1_none:e19|G73|ant21|h285" "A1J_pc:e19|G73|L400|ant21|h285" \
  "A1_none:e19|G73|L400|ant13|h285" "A1J_pc:nrLO|none|rh300c200|h285" "A1_none:nrLO|none|rh300c200|h285" \
  "A1J_pc:nrLO|none|rh190c500|h285" "A1_none:e19|G73|L400|h285" "A1_pc:pw|G73|h285" "A1J_pc:liqF|G73|h285" \
  "A1_none:pw|G73|r2s_fo_cb|h285"
echo "exit A $?"
echo "=== $(date -u +%H:%M:%S) batch B"
export GNC_IFACE=/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/snap/iface_v35a GNC_ACT_RATE=/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/snap/iface_v35a/actuator_rate_check_v2.json GNC_IFACE_PIN=/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/snap/pins_rev3/pins_rev3_v35a.sha256
nice -n 10 $PY /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/scripts/guard_run.py /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/scripts/v03_refly.py /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/tree /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/out/refly \
  "A1_none:liq|G73|v35a|h245" "A1J_pc:liq|G73|v35t|h255" "A1_none:liq|G73|v35a|h285"
echo "exit B $?"
echo "=== $(date -u +%H:%M:%S) done"

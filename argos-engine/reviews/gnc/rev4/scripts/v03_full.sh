#!/bin/bash
# REV-GNC-6 v03 full re-fly of the decision tables (liq 210 / 215 m case, liq h285 reference; N=1000 per main base).
source /tmp/claude-0/-home-claude/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv6/scripts/env6.sh
export RV6_FULL=1
cd /tmp/claude-0/-home-claude/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv6
if [ "$1" = case ]; then
  nice -n 10 $PY scripts/guard_run.py scripts/v03_refly4.py /tmp/claude-0/-home-claude/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv6/tree3 /tmp/claude-0/-home-claude/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv6/out/refly_full case "A1_none:liq:210" "A1J_pc:liq:210" "A1_none:liq:215" "A1J_pc:liq:215"
else
  export GNC_IFACE=/tmp/claude-0/-home-claude/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv6/snap/iface_v3d GNC_ACT_RATE=/tmp/claude-0/-home-claude/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv6/snap/iface_v3d/actuator_rate_check_v2.json GNC_IFACE_PIN=/tmp/claude-0/-home-claude/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv6/snap/gnc_dev29/data/pins/pins_rev2.sha256
  nice -n 10 $PY scripts/guard_run.py scripts/v03_refly4.py /tmp/claude-0/-home-claude/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv6/tree3 /tmp/claude-0/-home-claude/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv6/out/refly_full ref "A1_none:liq" "A1J_pc:liq"
fi
echo "exit $?"

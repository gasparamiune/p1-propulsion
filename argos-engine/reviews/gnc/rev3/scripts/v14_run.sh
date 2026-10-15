#!/bin/bash
source /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/env5.sh
cd /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5
echo "=== $(date -u +%H:%M:%S) P5 re-fly"
nice -n 10 $PY /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/scripts/guard_run.py /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/scripts/v14_p5_refly.py /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/tree /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/out/p5 "A1asc|dla05|V" "B1floor|dla05|Lhi" "A1|nom|V"
echo "exit $?"
echo "=== $(date -u +%H:%M:%S) done"

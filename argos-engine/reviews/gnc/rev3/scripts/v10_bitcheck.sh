#!/bin/bash
# REV-GNC-5 v10: independent re-run of the staged m2_bitcheck_v212 v1.1 'fly' (v2.12 side of Part A) and 'func' (Part B) parts on the
# staged v2.12 tree (scratch copy, MANIFEST-verified); reviewer's own comparison against the staged v2.12 and v2.11 streams. nice 10, sequential.
source /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/env5.sh
cd /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/tree/scripts
echo "=== $(date -u +%H:%M:%S) fly v2.12 (staged tree)"
GNC_TREE=/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/tree GNC_BC_OUT=/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/out/bc/bc_v212_rv.npz nice -n 10 $PY /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/scripts/guard_run.py /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/tree/scripts/m2_bitcheck_v212.py fly
echo "exit fly $?"
echo "=== $(date -u +%H:%M:%S) func v1.1"
GNC_TREE=/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/tree nice -n 10 $PY /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/scripts/guard_run.py /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/tree/scripts/m2_bitcheck_v212.py func /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/out/bc/bitcheck_v212_func_rv.json
echo "exit func $?"
echo "=== $(date -u +%H:%M:%S) compare (reviewer code)"
nice -n 10 $PY /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/scripts/v10_bc_compare.py /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/out/bc/bc_v212_rv.npz /home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/rev3/streams/bitcheck_v212/bc_v212.npz /home/claude/work/shared-fallback/engine/01-systems-gnc/staging_v3.1/rev3/streams/bitcheck_v212/bc_v211.npz /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/res/v10_bc_compare.json
echo "exit compare $?"
echo "=== $(date -u +%H:%M:%S) done"

#!/bin/bash
# REV-GNC-5 v15: independent partial re-run of the staged v2.9 suite (m2_bitcheck_v29 v1.2, gnc_dev6) on the staged v2.12 tree:
# parts A0, G, K, V, RF (A1 needs the rev1 simulator in a subprocess, N needs iface_v3c which is not in the hub). nice 10.
source /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/env5.sh
cd /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/tree/scripts
echo "=== $(date -u +%H:%M:%S) v2.9 suite parts A0,G,K,V,RF"
GNC_RES=/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/out/bit29 GNC_BIT_SCRATCH=/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/snap/scratch_bit29 GNC_BIT_PARTS=A0,G,K,V,RF nice -n 10 $PY /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/scripts/guard_run.py /tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv5/tree/scripts/m2_bitcheck_v29.py
echo "exit $?"
echo "=== $(date -u +%H:%M:%S) done"

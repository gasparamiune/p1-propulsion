#!/bin/bash
# waits for the slot-2 batch-1 python (PID $1) to exit, then runs batch 2 and batch 4 in sequence (one process at a time)
W=/dev/shm/rev_gnc7
while kill -0 $1 2>/dev/null; do sleep 5; done
$W/scripts/run_r3.sh d_r3_b2 R3P_JHI,R3P_JLO $W/out/d_r3
$W/scripts/run_r3.sh d_r3_b4 R3P_JC $W/out/d_r3_ks58_174 58,174
$W/scripts/run_r3.sh d_r3_b4g R3G_JC $W/out/d_r3

#!/bin/bash
# waits for the slot-1 queue (PID $1) to exit, then runs batch 3 (band ends at the J extremes)
W=/dev/shm/rev_gnc7
while kill -0 $1 2>/dev/null; do sleep 5; done
$W/scripts/run_r3.sh d_r3_b3 R3Hi_JLO,R3Lo_JHI $W/out/d_r3
$W/scripts/run_r3.sh d_r3_b3b R3C_JC $W/out/d_r3

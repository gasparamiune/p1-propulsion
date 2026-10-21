#!/bin/bash
# REV-GNC-7 master queue (2026-10-21): two slots, each one sim process at a time (nice 10); every variant resumes row by row
# from its JSON (m2_eng11_fe.run_variant), so the runs stopped at 09:2xZ continue where they were.
W=/dev/shm/rev_gnc7
q1() {
  $W/scripts/run_r3.sh d_r3_b2r R3P_JHI,R3P_JLO $W/out/d_r3
  $W/scripts/run_r3.sh d_r3_b4 R3P_JC $W/out/d_r3_ks58_174 58,174
  $W/scripts/run_r3.sh d_r3_b4g R3G_JC $W/out/d_r3
  $W/scripts/run_repro.sh c_edgeA02 A02 $W/out/c_repro_A02e 105,110,125,130
  $W/scripts/run_repro.sh c_edgeB07 B07 $W/out/c_repro_B07e 90,95,115,120,145,150
  echo "Q1 DONE $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $W/logs/master.log
}
q2() {
  $W/scripts/run_r3.sh d_r3_b3r R3Hi_JLO,R3Lo_JHI $W/out/d_r3
  $W/scripts/run_r3.sh d_r3_b3b R3C_JC $W/out/d_r3
  $W/scripts/run_repro.sh c_full_r C01 $W/out/c_repro
  echo "Q2 DONE $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $W/logs/master.log
}
echo "MASTER START $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $W/logs/master.log
q1 & q2 & wait
echo "MASTER END $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $W/logs/master.log

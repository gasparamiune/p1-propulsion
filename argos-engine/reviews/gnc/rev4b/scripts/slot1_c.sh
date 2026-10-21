#!/bin/bash
W=/dev/shm/rev_gnc7
$W/scripts/run_repro.sh c_full A01,A08,A03,B01,C01 $W/out/c_repro
$W/scripts/run_repro.sh c_edgeA02 A02 $W/out/c_repro_A02e 105,110,125,130
$W/scripts/run_repro.sh c_edgeB07 B07 $W/out/c_repro_B07e 90,95,115,120,145,150

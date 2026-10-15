#!/bin/bash
# sequential coarse-level runs on core 1 (Combustion 05-plume-cfd v1)
cd /home/claude/work/combustion/cfd/own
R=/home/claude/work/combustion/cfd/ownruns; PY=/opt/engine-venv/bin/python
export NUMBA_NUM_THREADS=1
run() { name=$1; shift; echo "$(date -u +%H:%M:%S) start $name" >> $R/queue_B.log; taskset -c 1 $PY run_plume.py $R/$name "$@" > $R/$name.log 2>&1; echo "$(date -u +%H:%M:%S) end $name rc=$?" >> $R/queue_B.log; }
run c_1s_100 --level 0.5 --single --tend 4.0e-3 --frame 1e-4
run c_1s_inv_100 --level 0.5 --single --inviscid --tend 1.0e-3 --frame 5e-5
run c_2s_100_nu05 --level 0.5 --Cl 0.0355 --tend 3.0e-3
run c_2s_100_nu2 --level 0.5 --Cl 0.142 --tend 3.0e-3
run c_2s_100_nophi --level 0.5 --nophi --tend 3.0e-3
run c_2s_sweep --level 0.5 --init $R/c_2s_100/final.npz --keep_time --frac 1.0 --ramp '1.0:0.2:4.0e-3:5.5e-3,0.2:0.2:5.5e-3:6.0e-3,0.2:0.125:6.0e-3:6.5e-3,0.125:0.125:6.5e-3:8.0e-3' --tend 8.0e-3 --frame 2.5e-5
run c_2s_020 --level 0.5 --init $R/c_2s_100/final.npz --frac 0.2 --tend 3.0e-3 --frame 1e-4
run c_2s_0125 --level 0.5 --init $R/c_2s_100/final.npz --frac 0.125 --tend 3.0e-3 --frame 1e-4
echo "$(date -u +%H:%M:%S) queue done" >> $R/queue_B.log

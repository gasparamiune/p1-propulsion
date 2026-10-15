#!/bin/bash
# CFD lane (one CPU-bound process at a time; lead cap: 2 concurrent CPU jobs for Combustion in total).
# 1) wait for the medium run m_2s_100 (PID 19759) to finish
# 2) resume the paused coarse sweep c_2s_sweep (PID 28730, SIGSTOP at ~4.9 ms) and wait for it
# 3) fine level f_2s_100 from the medium final state (+0.25 ms), then the eddy-viscosity x2 and no-Phi sensitivities
cd /home/claude/work/combustion/cfd/own
R=/home/claude/work/combustion/cfd/ownruns; PY=/opt/engine-venv/bin/python; L=$R/lane_cfd.log
export NUMBA_NUM_THREADS=1
waitpid() { while kill -0 "$1" 2>/dev/null; do sleep 20; done; }
log() { echo "$(date -u +%H:%M:%S) $*" >> $L; }
run() { name=$1; shift; log "start $name"; taskset -c 0,1 nice -n 5 $PY run_plume.py $R/$name "$@" > $R/$name.log 2>&1; log "end $name rc=$?"; }

log "lane start; waiting for m_2s_100 (19759)"
waitpid 19759
log "m_2s_100 finished"
if kill -0 28730 2>/dev/null; then
  log "resume c_2s_sweep (28730)"; kill -CONT 28730; waitpid 28730; log "c_2s_sweep finished"
fi
TM=$($PY -c "import numpy as np, json; print(json.loads(str(np.load('$R/m_2s_100/final.npz')['meta']))['t'])")
TEND=$($PY -c "print($TM + 0.25e-3)")
run f_2s_100 --level 2 --init $R/m_2s_100/final.npz --keep_time --tend $TEND
run c_2s_100_nu2 --level 0.5 --Cl 0.142 --tend 3.0e-3
run c_2s_100_nophi --level 0.5 --nophi --tend 3.0e-3
log "lane done"

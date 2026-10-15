#!/bin/bash
# M2 post-processing chain (sequential, 1 core, nice 10): waits for run_m2_chain.sh, then
# vehicle outputs -> descent trade -> IMU sweep -> failure forensics -> MC analysis/plots
export NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export GNC_IFACE=/home/claude/work/shared-fallback/engine/interfaces
export GNC_SUFFIX=v2
export GNC_OUT=/home/claude/work/space/out/m2
export GNC_DC_OUT=/home/claude/work/space/out/duty_cycles_v2
export GNC_RES=/home/claude/work/space/out/results_v2
export GNC_VEH_OUT=/home/claude/work/space/out/vehicle
while pgrep -f "run_m2_chain[.]sh" > /dev/null; do sleep 20; done
cd /home/claude/work/space/gnc
PY=/opt/engine-venv/bin/python
L=/home/claude/work/space/logs
echo "post start $(date -u +%FT%TZ)"
nice -n 10 $PY scripts/m2_vehicle.py > $L/m2_vehicle_v2.log 2>&1; echo "vehicle done $? $(date -u +%FT%TZ)"
nice -n 10 $PY scripts/m2_trade.py > $L/m2_trade_v2.log 2>&1; echo "trade done $? $(date -u +%FT%TZ)"
nice -n 10 $PY scripts/m2_imu_sweep.py > $L/m2_imu_v2.log 2>&1; echo "imu done $? $(date -u +%FT%TZ)"
nice -n 10 $PY scripts/m2_failure_forensics.py > $L/m2_fx_v2.log 2>&1; echo "forensics done $? $(date -u +%FT%TZ)"
nice -n 10 $PY scripts/m2_analysis.py > $L/m2_analysis_v2.log 2>&1; echo "analysis done $? $(date -u +%FT%TZ)"
echo "post end $(date -u +%FT%TZ)"

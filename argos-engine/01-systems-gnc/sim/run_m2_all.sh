#!/bin/bash
# M2 production chain v2.4 (sequential, 1 core, nice 10): relay engine correction -> MC -> verification -> CSI ->
# CSI time domain -> duty cycles -> vehicle -> descent trade -> IMU sweep -> forensics -> analysis -> fin roll ->
# gnc.json -> report tables
export NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export GNC_IFACE=/home/claude/work/shared-fallback/engine/interfaces
export GNC_SUFFIX=v2
export GNC_OUT=/home/claude/work/space/out/m2
export GNC_DC_OUT=/home/claude/work/space/out/duty_cycles_v2
export GNC_RES=/home/claude/work/space/out/results_v2
export GNC_VEH_OUT=/home/claude/work/space/out/vehicle
cd /home/claude/work/space/gnc
PY=/opt/engine-venv/bin/python
L=/home/claude/work/space/logs
echo "start $(date -u +%FT%TZ)"
for s in m2_engine_relay:relay m2_mc6:mc6 m2_verify6:verify6 m2_csi:csi m2_csi_timedomain:csi_td m2_duty_cycles:dc \
         m2_vehicle:vehicle m2_trade:trade m2_imu_sweep:imu m2_failure_forensics:fx m2_analysis:analysis m2_fin_roll:fin_roll m2_gnc_json:gnc_json \
         m2_report_tables:tables; do
  f=${s%%:*}; n=${s##*:}
  nice -n 10 $PY scripts/$f.py > $L/m2_${n}_v2.log 2>&1; echo "$n done $? $(date -u +%FT%TZ)"
done
echo "end $(date -u +%FT%TZ)"

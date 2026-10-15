#!/bin/bash
# After the v3 queue, on the promoted code (GNC_CODE, default gnc = sim6/run6 v2.6):
# (a) re-fly the cases with a start-delay shift (t_ign_add) whose nominal / sizing flight the first v2.6-dev runs left
#     unshifted (run6 v2.6 fix); the old summary and run files are kept in out/meco/history_before_nominal_tign_fix; the
#     Monte Carlo run files must come out identical (only the nominal flight and the sized load change);
# (b) reproducibility of the v3 evidence produced while v2.6 was in development (ctrlfix cases labelled 'sim6 v2.5',
#     MECO cases labelled 'sim6 v2.6-dev'): re-fly key cases into out/repro_v26 and compare value by value;
# (c) MECO evaluation again. One core, nice 10.
set -u
export NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
S=/home/claude/work/space
PY="nice -n 10 /opt/engine-venv/bin/python"
until grep -q "^end" $S/logs/v3_queue4.log 2>/dev/null; do sleep 10; done
export GNC_IFACE=$S/iface_v3b GNC_ACT_RATE=$S/iface_v3b/actuator_rate_check_v2.json
M=$S/out/meco; H=$M/history_before_nominal_tign_fix; R=$S/out/repro_v26
mkdir -p $H $R
LOG=$S/logs/v3_repro.log
cd ${GNC_CODE:-$S/gnc}
echo "start $(date -u +%FT%TZ) code $(pwd)" > $LOG
SHIFTED=mr_td72_tign10,mr_td72_tign20,mr_td72_tign30,mr_f125_td72_floorstart,mr_td72_ncmin,mr_td72_nc,mr_td72_nc_unplanned,mr_td72_nc_m10,mr_td72_nc_m20,mr_td72_nc_m30,mr_fsw_J1.6_nc,mr_f125_rs20_nc
cp $M/mc6_summary_mr.json $H/mc6_summary_mr_before_fix.json
for c in ${SHIFTED//,/ }; do cp $M/mc6_runs_${c}_mr.csv $H/; done
GNC_OUT=$M GNC_SUFFIX=mr GNC_MR_CASES=$SHIFTED $PY scripts/m2_meco_mc.py >> $LOG 2>&1
echo "refly_shifted $? $(date -u +%FT%TZ)" >> $LOG
GNC_OUT=$M GNC_SUFFIX=mr GNC_MR_CASES=mr_td72_nc_ecu $PY scripts/m2_meco_mc.py >> $LOG 2>&1
echo "nc_ecu $? $(date -u +%FT%TZ)" >> $LOG
PAIRS=""
for c in ${SHIFTED//,/ }; do PAIRS="$PAIRS $H/mc6_runs_${c}_mr.csv $M/mc6_runs_${c}_mr.csv"; done
GNC_REPRO_OUT=$H/refly_mc_identical.json $PY scripts/m2_repro_check.py $PAIRS >> $LOG 2>&1
echo "compare_shifted $? $(date -u +%FT%TZ)" >> $LOG
GNC_OUT=$R GNC_SUFFIX=cf GNC_CF_CASES=cf_J2.7_acc2000_ref40,cf_J1.6_acc2000_ref40 $PY scripts/m2_ctrlfix_mc.py >> $LOG 2>&1
echo "ctrlfix $? $(date -u +%FT%TZ)" >> $LOG
GNC_OUT=$R GNC_SUFFIX=mr GNC_MR_CASES=mr_td72,mr_J1.6_fix_td72 $PY scripts/m2_meco_mc.py >> $LOG 2>&1
echo "meco $? $(date -u +%FT%TZ)" >> $LOG
GNC_REPRO_OUT=$R/repro_check_v26.json $PY scripts/m2_repro_check.py \
  $S/out/ctrlfix/mc6_runs_cf_J2.7_acc2000_ref40_cf.csv $R/mc6_runs_cf_J2.7_acc2000_ref40_cf.csv \
  $S/out/ctrlfix/mc6_runs_cf_J1.6_acc2000_ref40_cf.csv $R/mc6_runs_cf_J1.6_acc2000_ref40_cf.csv \
  $M/mc6_runs_mr_td72_mr.csv $R/mc6_runs_mr_td72_mr.csv \
  $M/mc6_runs_mr_J1.6_fix_td72_mr.csv $R/mc6_runs_mr_J1.6_fix_td72_mr.csv >> $LOG 2>&1
echo "compare_repro $? $(date -u +%FT%TZ)" >> $LOG
GNC_OUT=$M GNC_SUFFIX=mr $PY scripts/m2_meco_eval.py > $S/logs/meco_eval_final.log 2>&1
echo "meco_eval $? $(date -u +%FT%TZ)" >> $LOG
echo "end $(date -u +%FT%TZ)" >> $LOG

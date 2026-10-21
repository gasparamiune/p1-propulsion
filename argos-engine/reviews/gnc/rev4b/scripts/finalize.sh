#!/bin/bash
# REV-GNC-7 finalize: corrections + trial, t10 v3 on the trial and the candidate, window summary, margin table, reproduction compare.
W=/dev/shm/rev_gnc7
H=/home/claude/work/shared-fallback/engine
C=$H/01-systems-gnc/staging_v3.1/rev4b/v32/gnc_v3.2_rev4b.json
P="nice -n 10 /opt/engine-venv/bin/python -I"
rm -f $W/b/*_test.json
$P $W/scripts/rv7_v32_corrections.py $C $W/b/rv7_v32_corrections.json $W/b/gnc_v3.2_rv7_trial.json > $W/logs/rv7_v32_corrections.log 2>&1; echo "corrections rc $?" | tee -a $W/logs/rv7_v32_corrections.log
$P $W/scripts/t10_postcheck_v3.py $W/b/gnc_v3.2_rv7_trial.json $W/b/t10v3_trial_pub_rv7.json --publication --rv7 > $W/b/t10v3_trial_pub_rv7.log 2>&1; echo "EXIT $?" >> $W/b/t10v3_trial_pub_rv7.log
$P $W/scripts/t10_postcheck_v3.py $C $W/b/t10v3_candidate_pub_rv7.json --publication --rv7 > $W/b/t10v3_candidate_pub_rv7.log 2>&1; echo "EXIT $?" >> $W/b/t10v3_candidate_pub_rv7.log
$P $W/scripts/d_summary.py $W/h/d_summary.json "$W/out/d_r3/eng11fe_*.json" "$W/out/d_r3_ks58_174/eng11fe_*.json" "$W/out/c_repro/eng11fe_*.json" "$W/out/c_repro_A02e/eng11fe_*.json" "$W/out/c_repro_B07e/eng11fe_*.json" > $W/logs/d_summary.log 2>&1
$P $W/scripts/d_table.py $W/h/d_table.json $W/out/d_r3/eng11fe_R3*.json $W/out/d_r3_ks58_174/eng11fe_R3P_JC.json > $W/logs/d_table.log 2>&1
O=$W/out; $P $W/scripts/c_compare2.py $W/h/c_compare2.json $O/c_repro/eng11fe_check.json $O/c_repro/eng11fe_A01.json $O/c_repro/eng11fe_A03.json $O/c_repro/eng11fe_A08.json $O/c_repro/eng11fe_B01.json $O/c_repro/eng11fe_C01.json $O/c_repro_A02e/eng11fe_A02.json $O/c_repro_B07e/eng11fe_B07.json > $W/logs/c_compare2.log 2>&1
rm -f $W/h/*_tmp.json
cat $W/logs/rv7_v32_corrections.log; tail -n 3 $W/b/t10v3_trial_pub_rv7.log; tail -n 3 $W/b/t10v3_candidate_pub_rv7.log; cat $W/logs/c_compare2.log; cat $W/logs/d_summary.log

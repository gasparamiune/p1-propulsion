#!/bin/bash
# Stage the 01-systems-gnc deliverables (local), then copy to the hub folder given as $1 (default: fallback hub).
set -e
S=/home/claude/work/space
D=$S/deliver/01-systems-gnc
HUB=${1:-/home/claude/work/shared-fallback/engine}
mkdir -p $D/sim $D/results/mc $D/duty_cycles $D/vehicle $D/results/history
# code + data + README (no caches)
rm -rf $D/sim && mkdir -p $D/sim && cp -a $S/gnc/. $D/sim/
find $D/sim -name '__pycache__' -type d -prune -exec rm -rf {} +
find $D/sim \( -name '*.nbi' -o -name '*.nbc' -o -name '*.pyc' \) -delete
cp $S/run_m2_all.sh $S/run_m2_chain.sh $S/run_m2_append.sh $S/run_m2_post.sh $S/run_act_batch2.sh $S/run_act_batch3.sh \
   $S/run_batch4.sh $D/sim/ 2>/dev/null || true
# results
cp -a $S/out/results_v2/. $D/results/
cp $S/out/m2/mc6_summary_v2.json $S/out/m2/verify6_v2.json $S/out/m2/csi_v2.json $S/out/m2/csi_timedomain_v2.json \
   $S/out/m2/csi_loop_gain_v2.png $S/out/m2/bitcheck_v2.3_vs_v2.2.json $D/results/ 2>/dev/null || true
cp $S/out/m2/verify6_*.csv $D/results/ 2>/dev/null || true
# actuator study (sim6 v2.5): CSI variants, bit check; the 42-case summary that gnc.json v2 was built from
cp $S/out/m2/csi_v2_n48.json $S/out/m2/csi_v2_n48_J2.json $S/out/m2/csi_v2_n60_J2.json $S/out/m2/csi_loop_gain_v2_n48.png \
   $S/out/m2/csi_loop_gain_v2_n48_J2.png $S/out/m2/csi_loop_gain_v2_n60_J2.png $D/results/ 2>/dev/null || true
cp $S/out/m2/mc6_summary_v2_before_act.json $D/results/mc6_summary_v2_gncjson_v2_basis.json
cp $S/out/m2/mc6_runs_*_v2.csv $D/results/mc/
cp $S/out/gnc_json/gnc_v2.json $D/results/gnc_v2_build_copy.json
cp $S/out/gnc_json/gnc_v2_published.json $D/results/gnc_v2_published_copy.json 2>/dev/null || true
mkdir -p $D/results/history && cp $S/out/gnc_json/history/gnc_v2_build_1958_inputs_record_wrong.json $S/out/gnc_json/gnc_v1.json $D/results/history/
# checks after promoting the combustion.json v2 reader (v1 path bit-identical; v2 map vs relay)
mkdir -p $D/results/checks_combustion_v2 && cp $S/out/check_comb2/* $D/results/checks_combustion_v2/ 2>/dev/null || true
# duty cycles v2 (+ v1 already staged)
cp $S/out/duty_cycles_v2/* $D/duty_cycles/
# vehicle v3c (+ v3b history)
cp $S/out/vehicle/* $D/vehicle/
mkdir -p $D/vehicle/history_v3b && cp $S/out/archive_v2.2/vehicle/* $D/vehicle/history_v3b/
# v2.3 history (superseded by sim6 v2.4: rotational-integrator fix; kept as evidence)
H3=$D/results/history/v2.3
mkdir -p $H3
A=$S/out/archive_v2.3
cp $A/m2/mc6_summary_v2.json $H3/mc6_summary_v2.3.json
cp $A/m2/verify6_v2.json $H3/verify6_v2.3_torque_free_FAILED.json
cp $A/results_v2/mc6_cases_summary_v2.csv $H3/mc6_cases_summary_v2.3.csv
cp $A/m2/mc6_runs_AD_fins_f20_v2.csv $H3/mc6_runs_AD_fins_f20_v2.3.csv
cp $A/gnc_json/gnc_v2.json $H3/gnc_v2_draft_on_sim6_v2.3.json 2>/dev/null || true
cp $S/logs/archive_v2.3/m2_verify6_v2.log $H3/verify6_v2.3.log 2>/dev/null || true
# REPORT.md is returned to the lead as text (subagent rule); not staged here
du -sh $D; find $D -type f | wc -l
if [ "$2" = "copy" ]; then
  mkdir -p $HUB/01-systems-gnc
  cp -a $D/. $HUB/01-systems-gnc/
  du -sh $HUB/01-systems-gnc
fi

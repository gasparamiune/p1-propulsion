#!/bin/sh
# v2.13 staging (RAM): copy the changed sources, the v2.13 tools and calc scripts and the small SIL extracts into /dev/shm/elec_v213/stage
# (the overlay on staging_v2.12; build = v2.11 + the v2.12 overlay + the v2.13 overlay). Run after the SIL chain and the unit tests.
set -e
F=/dev/shm/elec_v213/src; S=/dev/shm/elec_v213/stage; O=/dev/shm/elec_v213/out; C=/dev/shm/elec_v213/calc; R=$S/results/v2p13
mkdir -p $S/firmware/src/core $S/firmware/sil $S/firmware/tools/v2p13 $S/calc/v2p13 $R/sil $S/docs
for f in config.h types.h protocol.h protocol.cpp engine_ecu.h engine_ecu.cpp; do cp -p $F/src/core/$f $S/firmware/src/core/; done
for f in sim.h sim.cpp sil_main.cpp sc_v212.inc sc_v213.inc test_v29.inc test_v212.inc test_v213.inc; do cp -p $F/sil/$f $S/firmware/sil/; done
for f in build.sh run_sil.sh chain.sh tail_ctl.sh post.sh stage.sh finalize.sh sums.py; do cp -p /dev/shm/elec_v213/tools/$f $S/firmware/tools/v2p13/; done
for f in item2_hold_gap.py s13t_compare_v2p13.py a5_s13f_summary_v2p13.py s12_compare_v2p13.py make_interface_json_v4p2.py make_bench_plan_v5p1.py make_bom_v2p5.py; do cp -p $C/$f $S/calc/v2p13/; done
cp -p /dev/shm/elec_v213/results/item2_hold_gap.json $R/
cp -p $O/test_core_out.txt $R/sil/test_core_v2p13_log.txt
cp -p $O/test_core_nohooks_out.txt $R/sil/test_core_nohooks_v2p13_log.txt
for b in silF silT; do
  B=$( [ $b = silF ] && echo bpc1_false || echo bpc1_true )
  for f in $O/$b/*.json; do
    [ -f "$f" ] || continue; n=$(basename "$f")
    case $n in sil_n2o_alone_*) cp -p "$f" $R/sil/${n%.json}_$B.json ;; *) cp -p "$f" $R/sil/ ;; esac
  done
  for s in s13f a5 s13t13ts s13t13; do
    if [ -f $O/$b/$s.log ]; then cp -p $O/$b/$s.log $R/sil/run_log_${s}_$B.txt; fi
  done
done
if [ -f $O/s12/S12_bleed.json ]; then
  cp -p $O/s12/S12_bleed.json $R/sil/S12_bleed_bpc1_false.json; cp -p $O/s12/S12_run_log.txt $R/sil/run_log_s12_bpc1_false.txt
  if [ -f $O/s12/sil_n2o_alone_bleed.json ]; then cp -p $O/s12/sil_n2o_alone_bleed.json $R/sil/sil_n2o_alone_bleed_bpc1_false.json; fi
fi
ls -la $R $R/sil

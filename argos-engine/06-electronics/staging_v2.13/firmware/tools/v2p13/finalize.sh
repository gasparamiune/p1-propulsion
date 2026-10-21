#!/bin/sh
# v2.13 finalize in RAM (light python steps): binaries list, staging copy, S13T compare, A5 / S13F summary, BOM v2.5, bench plan v5.1, v4.2 JSON
set -e
O=/dev/shm/elec_v213/out; S=/dev/shm/elec_v213/stage; C=/dev/shm/elec_v213/calc; R=$S/results/v2p13
H=/home/claude/work/shared-fallback/engine/06-electronics/staging_v2.12
U=$(date -u +%Y-%m-%dT%H:%M:%SZ)
{
  echo "# v2.13 binaries ($U), built in /dev/shm/elec_v213/build by firmware/tools/v2p13/build.sh (nice 15, single-threaded g++), sha256/16:"
  echo "# $(g++ --version | head -1); flags -std=c++17 -O2 -Wall -Wextra -Wno-unused-parameter; sil / test_core with -DECU_SIL_TEST_HOOKS; sil_bpc1 adds -DECU_BPC1_SHOWN_VARIANT"
  for b in sil sil_bpc1 test_core test_core_nohooks; do echo "$(sha256sum /dev/shm/elec_v213/build/$b | cut -c1-16)  $b  $(stat -c %s /dev/shm/elec_v213/build/$b) B  built $(date -u -r /dev/shm/elec_v213/build/$b +%Y-%m-%dT%H:%M:%SZ)"; done
} > $O/binaries_v2p13.txt
rm -rf $S/results/v2p13; sh /dev/shm/elec_v213/tools/stage.sh > $O/stage_final.txt 2>&1
cp -p $O/binaries_v2p13.txt $R/sil/binaries_v2p13.txt
python3 -B -I $C/s13t_compare_v2p13.py $H/results/v2p12/sil $R/sil $R/s13t_compare_v2p13.json
python3 -B -I $C/a5_s13f_summary_v2p13.py $R/sil $R/a5_s13f_summary_v2p13.json > $O/a5_s13f_summary_print.txt
if [ -f $R/sil/S12_bleed_bpc1_false.json ]; then python3 -B -I $C/s12_compare_v2p13.py $H/results/v2p12/sil/S12_bleed.json $R/sil/S12_bleed_bpc1_false.json $R/s12_compare_v2p13.json; fi
python3 -B -I $C/make_bom_v2p5.py $H/results/bom_v2p4.csv $S/results/bom_v2p5.csv
python3 -B -I $C/make_bench_plan_v5p1.py $H/docs/bench_plan_v5.md $S/docs/bench_plan_v5_1.md $U
python3 -B -I $C/make_interface_json_v4p2.py $U $S $S/results/electronics_v4.2.json
du -sb $S; find $S -type f | wc -l

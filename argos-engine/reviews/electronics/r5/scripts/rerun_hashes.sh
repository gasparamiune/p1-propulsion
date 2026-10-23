#!/bin/sh
# REV-ELEC-5: sha256/16 of every reviewer re-run output against the staged v2.13 file (run logs: staged copy minus its trailing "exit 0" line)
O=/dev/shm/rev_elec5/out; S=/home/claude/work/shared-fallback/engine/06-electronics/staging_v2.13/results/v2p13/sil; B=/dev/shm/rev_elec5/fw/build
h() { sha256sum "$1" | cut -c1-16; }
cmp1() { a=$(h "$1"); b=$(h "$2"); if [ "$a" = "$b" ]; then v=IDENTICAL; else v=DIFFERS; fi; echo "$v  mine $a  staged $b  $(basename "$1") <-> $(basename "$2")"; }
cmplog() { a=$(h "$1"); b=$(head -n -1 "$2" | sha256sum | cut -c1-16); last=$(tail -n 1 "$2"); if [ "$a" = "$b" ] && [ "$last" = "exit 0" ]; then v="IDENTICAL (staged has a trailing 'exit 0' line)"; else v=DIFFERS; fi; echo "$v  mine $a  staged-minus-last $b  $(basename "$1") <-> $(basename "$2")"; }
echo "# binaries (fw/build) against results/v2p13/sil/binaries_v2p13.txt"
for f in sil sil_bpc1 test_core test_core_nohooks; do echo "$(h $B/$f)  $f  staged $(grep "  $f  " $S/binaries_v2p13.txt | cut -c1-16)"; done
echo "# SIL outputs"
cmp1 $O/silF/A5_seat_step_relight_bpc1_false.json $S/A5_seat_step_relight_bpc1_false.json
cmp1 $O/silT/A5_seat_step_relight_bpc1_true.json $S/A5_seat_step_relight_bpc1_true.json
cmp1 $O/silF/S13F_tc4_fault_bpc1_false.json $S/S13F_tc4_fault_bpc1_false.json
cmp1 $O/silT/S13F_tc4_fault_bpc1_true.json $S/S13F_tc4_fault_bpc1_true.json
cmp1 $O/silF/S13T_seat_drift_bpc1_false_ts.json $S/S13T_seat_drift_bpc1_false_ts.json
cmp1 $O/silF/S13T_seat_drift_bpc1_false.json $S/S13T_seat_drift_bpc1_false.json
cmp1 $O/s12/S12_bleed.json $S/S12_bleed_bpc1_false.json
[ -f $O/silT/S13T_seat_drift_bpc1_true_ts.json ] && cmp1 $O/silT/S13T_seat_drift_bpc1_true_ts.json $S/S13T_seat_drift_bpc1_true_ts.json
cmp1 $O/silF/sil_n2o_alone_a5.json $S/sil_n2o_alone_a5_bpc1_false.json
cmp1 $O/silT/sil_n2o_alone_a5.json $S/sil_n2o_alone_a5_bpc1_true.json
cmp1 $O/silF/sil_n2o_alone_s13f.json $S/sil_n2o_alone_s13f_bpc1_false.json
cmp1 $O/silT/sil_n2o_alone_s13f.json $S/sil_n2o_alone_s13f_bpc1_true.json
cmp1 $O/silF/sil_n2o_alone_s13t13ts.json $S/sil_n2o_alone_s13t13ts_bpc1_false.json
cmp1 $O/silF/sil_n2o_alone_s13t13.json $S/sil_n2o_alone_s13t13_bpc1_false.json
cmp1 $O/s12/sil_n2o_alone_bleed.json $S/sil_n2o_alone_bleed_bpc1_false.json
[ -f $O/silT/sil_n2o_alone_s13t13ts.json ] && cmp1 $O/silT/sil_n2o_alone_s13t13ts.json $S/sil_n2o_alone_s13t13ts_bpc1_true.json
echo "# run logs"
cmplog $O/silF/run_log_a5.txt $S/run_log_a5_bpc1_false.txt
cmplog $O/silT/run_log_a5.txt $S/run_log_a5_bpc1_true.txt
cmplog $O/silF/run_log_s13f.txt $S/run_log_s13f_bpc1_false.txt
cmplog $O/silT/run_log_s13f.txt $S/run_log_s13f_bpc1_true.txt
cmplog $O/silF/run_log_s13t13ts.txt $S/run_log_s13t13ts_bpc1_false.txt
cmplog $O/silF/run_log_s13t13.txt $S/run_log_s13t13_bpc1_false.txt
cmplog $O/s12/run_log_bleed.txt $S/run_log_s12_bpc1_false.txt
[ -f $O/silT/run_log_s13t13ts.txt ] && cmplog $O/silT/run_log_s13t13ts.txt $S/run_log_s13t13ts_bpc1_true.txt
echo "# unit tests (my build): $(tail -n 2 /dev/shm/rev_elec5/run/test_core_out.txt | head -1) | no-hooks: $(tail -n 2 /dev/shm/rev_elec5/run/test_core_nohooks_out.txt | head -1)"

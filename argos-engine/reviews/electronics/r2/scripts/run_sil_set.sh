#!/bin/bash
# REV-ELEC-2: re-run a sample of the v2.10 SIL record on the reviewer's rebuild (binaries byte-identical to the author's)
S=/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rev_elec2
B=$S/fw/build
cd $S/out || exit 1
run1() {  # name binary scenario outdir
  local t0=$(date +%s.%N)
  nice -n 10 $2 $3 $4 > $4/run_log.txt 2>&1
  local rc=$?
  local t1=$(date +%s.%N)
  echo "$1 rc=$rc wall $(echo "$t1 - $t0" | bc) s" >> $S/out/times.txt
}
for sc in r2hold aborts startmc mc probef v210 coast206 bleed; do
  mkdir -p $S/out/$sc; run1 $sc $B/sil $sc $S/out/$sc
done
mkdir -p $S/out/ignruleb_base $S/out/ignruleb_bpc1
run1 ignruleb_base $B/sil ignruleb $S/out/ignruleb_base
run1 ignruleb_bpc1 $B/sil_bpc1 ignruleb $S/out/ignruleb_bpc1
echo ALLDONE >> $S/out/times.txt

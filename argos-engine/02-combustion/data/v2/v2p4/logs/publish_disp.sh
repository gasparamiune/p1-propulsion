#!/bin/bash
# copy the six dispersed-cycle outputs to the hub and verify hashes
set -e
L=/home/claude/work/combustion/data/v2
H=/home/claude/work/shared-fallback/engine/02-combustion/data/v2
mkdir -p $H/dc_gncv3
for t in DC-B1v3p99 DC-B1v3max DC-A1dispp99 DC-B1v3p99_tg711 DC-B1v3max_tg711 DC-A1dispp99_tg711; do
  cp -p $L/dc_gncv3/$t-S230_neqE1e+03_reg1.csv $H/dc_gncv3/
  cp -p $L/headend_bc_${t}_v2.csv $H/
done
cp -p $L/dc_gncv3/summary_v2p4.json $L/dc_gncv3/dispersed_checks_v2p4.json $H/dc_gncv3/
cp -p /home/claude/work/combustion/src/run_dispersed_v2p4.py /home/claude/work/combustion/src/dispersed_checks_v2p4.py /home/claude/work/shared-fallback/engine/02-combustion/src/
cd $L && for f in dc_gncv3/*.csv dc_gncv3/*.json headend_bc_DC-*v3*_v2.csv headend_bc_DC-A1disp*_v2.csv; do a=$(sha256sum $f|cut -c1-16); b=$(sha256sum $H/$f|cut -c1-16); echo "$f $a $([ "$a" = "$b" ] && echo OK || echo MISMATCH)"; done

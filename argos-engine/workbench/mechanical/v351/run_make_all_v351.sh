#!/bin/bash
# make_all CAD v3.5.1 in three chunks (2 h task limit: each chunk < 2 h); checks merge into checks_v3.5.1.json (same build fingerprint)
cd /home/claude/work/mechanical/v351/engine/03-cad/src
PY=/opt/engine-venv/bin/python
L=/home/claude/work/mechanical/runs/make_all
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
echo "chunk A start $(date -u +%FT%TZ)" >> $L/make_all_v351_driver.log
nice -n 10 $PY -u make_all.py --stages build,parts,assembly,glb,bom,mass,drawings,checks --poses neutral,alpha+,alpha-,beta+,beta- > $L/make_all_v351_A.log 2>&1
echo "chunk A exit $? $(date -u +%FT%TZ)" >> $L/make_all_v351_driver.log
nice -n 10 $PY -u make_all.py --stages checks --poses combined045,combined135,combined225,combined315,stop000,stop045 > $L/make_all_v351_B.log 2>&1
echo "chunk B exit $? $(date -u +%FT%TZ)" >> $L/make_all_v351_driver.log
nice -n 10 $PY -u make_all.py --stages checks,readme --poses stop090,stop135,stop180,stop225,stop270,stop315,stopFD07B > $L/make_all_v351_C.log 2>&1
echo "chunk C exit $? $(date -u +%FT%TZ)" >> $L/make_all_v351_driver.log
echo MAKE_ALL_V351_DONE >> $L/make_all_v351_driver.log

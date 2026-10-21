#!/bin/bash
# chain 10 (2026-10-20, lead 08:40Z 'Proceed: T-F2 rev 4, then the (b) package'): T-F2 rev-4 contact sub-model, both bounds;
# entry-h refinement levels 0.2 / 0.1 / 0.05 for 234 (4) and the C7 stick-edge zone.  Caps: one ccx of mine at a time (sequential),
# <= 2 ccx machine-wide and combined ccx RSS <= 9 GB (driver guard / rss_wait), nice 10, 1 solver thread, no new ccx below 2048 MiB free.
set -u
export SAX_CAD=v352r4 SAX_R10=free SAX_TB_ABORTS=165,150,135,120,105 SAX_RES_F32=1 SAX_DECK_GZ=1 SAX_DISK_FLOOR_MB=2048 \
       SAX_CCX_WAIT_S=3600 CON_TIMEOUT_S=900 SUB_DISK_FLOOR_MB=2048 OMP_NUM_THREADS=1
PY=/opt/engine-venv/bin/python
DRV=/home/claude/work/mechanical/v352/contact/sax_contact_tc0203_sub_v352r4.py
SAXPY=/home/claude/work/mechanical/v352/engine/04-fea/structural/sax.py
LOG=/home/claude/work/mechanical/v352/logs/chain10_tf2r4.log
cd /tmp/claude-0/-home-claude/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad || exit 9
echo "chain10 start $(date -u +%FT%TZ) pid $$" >> $LOG
rss_wait() {   # $1 = expected GB of the next ccx
  $PY -c "
import subprocess, time, sys, shutil
t0 = time.time()
while True:
    if shutil.disk_usage('/home/claude').free / 2**20 < 2048: print('HOLD disk floor', flush=True); sys.exit(3)
    o = subprocess.run(['ps', '-C', 'ccx', '-o', 'rss='], capture_output=True, text=True).stdout.split()
    if len(o) < 2 and sum(int(x) for x in o) / 2**20 + $1 <= 9.0: sys.exit(0)
    if time.time() - t0 > 3600: print('HOLD ccx slot / RSS', flush=True); sys.exit(3)
    time.sleep(15)
" >> $LOG 2>&1 || { echo "STOP rss_wait $(date -u +%FT%TZ)" >> $LOG; exit 3; }
}
sub() {   # bound, entry h, variants, picks
  echo "== sub $1 eh $2 $3 $4 $(date -u +%FT%TZ)" >> $LOG
  SAX_THERMAL_TAG=v352_NF2b_R4_$1 SAX_ENTRY_H=$2 nice -n 10 $PY $DRV $3 $4 >> $LOG 2>&1
  rc=$?; if [ $rc -ne 0 ]; then echo "STOP rc $rc (sub $1 $2 $3 $4) $(date -u +%FT%TZ)" >> $LOG; exit $rc; fi
}
glob() {   # bound, entry h, states: global S-AX v352r4 solves at that entry h, then nothing else (no post)
  echo "== glob $1 eh $2 $3 $(date -u +%FT%TZ)" >> $LOG
  rss_wait 1.5
  SAX_THERMAL_TAG=v352_NF2b_R4_$1 SAX_ENTRY_H=$2 nice -n 10 $PY $SAXPY solve --level 1 --states $3 >> $LOG 2>&1
  rc=$?; if [ $rc -ne 0 ]; then echo "STOP rc $rc (glob $1 $2 $3) $(date -u +%FT%TZ)" >> $LOG; exit $rc; fi
}
for GV in ${CHAIN_BOUNDS:?set CHAIN_BOUNDS}; do
  sub $GV 0.1 C0,C5,C7,C6,C3n,C4n LC2:B1_19,LC1:B1_19,TB70:TB,TBS:TB
  for EH in 0.2 0.05; do
    glob $GV $EH B1_19,TB
    sub $GV $EH C0,C5,C7,C3n,C4n LC2:B1_19,TBS:TB
  done
  sub $GV 0.1 C0,C5,C7,C3n,C4n TBS:TB_a165,TBS:TB_a150,TBS:TB_a135,TBS:TB_a120,TBS:TB_a105
  sub $GV 0.1 C0,C5,C7 LC2:B1_1,LC2:B1_16,LC2:B1_21.65
done
echo "chain10 done $(date -u +%FT%TZ)" >> $LOG

#!/bin/bash
# chain 11 (2026-10-20, (b) package, lead 14:34Z 'Next as you have it: the (b) package and the abort decision'): T-F2 rev-4 contact
# sub-model at the TB70 load case (58.1 bar blocked + manifold 70 bar, SF 1.5 / 2.0) on the five trial abort states TB_a165 .. TB_a105,
# both bounds, entry h 0.1 (chain 10 ran TB70 only at TB = 175 C; TBS ran at every abort value).  Same driver (v1.1 1fce3b7d1f343be2),
# same global S-AX v352r4 states (trimmed res_sub.npz), no thermal run.  Caps as chain 10: one ccx of mine at a time (sequential),
# <= 2 ccx machine-wide and combined ccx RSS <= 9 GB (driver guard), nice 10, 1 solver thread, no new ccx below 2048 MiB free (HOLD).
set -u
export SAX_CAD=v352r4 SAX_R10=free SAX_TB_ABORTS=165,150,135,120,105 SAX_RES_F32=1 SAX_DECK_GZ=1 SAX_DISK_FLOOR_MB=2048 \
       SAX_CCX_WAIT_S=3600 CON_TIMEOUT_S=900 SUB_DISK_FLOOR_MB=2048 OMP_NUM_THREADS=1
PY=/opt/engine-venv/bin/python
DRV=/home/claude/work/mechanical/v352/contact/sax_contact_tc0203_sub_v352r4.py
LOG=/home/claude/work/mechanical/v352/logs/chain11_tf2r4_tb70.log
cd /tmp/claude-0/-home-claude/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad || exit 9
echo "chain11 start $(date -u +%FT%TZ) pid $$ disk $(df --output=avail -m /home/claude | tail -1) MiB" >> $LOG
for GV in GVLO GVHI; do
  echo "== sub $GV eh 0.1 TB70 aborts $(date -u +%FT%TZ)" >> $LOG
  SAX_THERMAL_TAG=v352_NF2b_R4_$GV SAX_ENTRY_H=0.1 nice -n 10 $PY $DRV C0,C5,C7,C3n,C4n \
      TB70:TB_a165,TB70:TB_a150,TB70:TB_a135,TB70:TB_a120,TB70:TB_a105 >> $LOG 2>&1
  rc=$?; if [ $rc -ne 0 ]; then echo "STOP rc $rc ($GV) $(date -u +%FT%TZ)" >> $LOG; exit $rc; fi
done
echo "chain11 done $(date -u +%FT%TZ) disk $(df --output=avail -m /home/claude | tail -1) MiB" >> $LOG

#!/bin/bash
# rv01_rerun.sh v1.0 (REV-GNC-R1, independent reviewer, 2026-10-13)
# Independent re-runs of GNC rev1 evidence on the reviewer's scratch copy of the rev1 staging (sim6 f9094b63e64f2324,
# run6 35b5c808487b9339; copy verified against MANIFEST_rev1.sha256). One solver process at a time, nice 10,
# NUMBA_NUM_THREADS=1 (CPU shared with Mechanical FEA, Combustion grids and another reviewer).
# Jobs (run sequentially by "all"):
#   bitcheck  m2_bitcheck_v28 v1.5 with EVERY part (A,B,C,D,E,F,G,H,W,X,P,R,S); GNC's v1.5 run covered A-F,P,R,S only
#   st        m2_start_transient arm L400_te on both bases (A1_none, A1J_pc), 500 runs each, part mc only
#   e7        m2_eng07_6v6 arm RR66_EI05 on both bases (A1_none, rbl_B1_lead62_pc_k2), 500 runs each, part run only
# Every GNC output folder is redirected to the reviewer's scratch or to reviews/gnc/rev1; the GNC staging and the GNC
# work area are read only (stored reference tables are read from /home/claude/work/space/out, verified byte-equal to the
# hub-published copies by rv02_compare.py).
set -u
SCR=/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad
C=$SCR/rev1copy
RV=/home/claude/work/shared-fallback/engine/reviews/gnc/rev1
O=$SCR/rv_out
mkdir -p "$O" "$RV/logs"
export NUMBA_NUM_THREADS=1 NUMBA_CACHE_DIR=$SCR/numba_cache_rev1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export GNC_IFACE=/home/claude/work/space/iface_v3c GNC_ACT_RATE=/home/claude/work/space/iface_v3c/actuator_rate_check_v2.json
export GNC_WEB_OUT=$O/web_limit GNC_DC_OUT=$O/web_limit/records GNC_FCT_OUT=$O/fc_thrust GNC_REL_OUT=$O/release_rule \
       GNC_ST_OUT=$O/start_transient GNC_E7_OUT=$O/eng07 GNC_ENG03_OUT=$O/eng03 GNC_TG_OUT=$O/throat GNC_MEST_OUT=$O/mest \
       GNC_MEST2_OUT=$O/mest2 GNC_FF_OUT=$O/fault_f GNC_PB_OUT=$O/purge_bleed
PY="nice -n 10 /opt/engine-venv/bin/python -I $RV/rv00_runner.py"
run() {
  case "$1" in
    bitcheck) GNC_RES=$RV/rv01_bitcheck GNC_BIT_PARTS=A,B,C,D,E,F,G,H,W,X,P,R,S $PY "$C/scripts/m2_bitcheck_v28.py" ;;
    st)       GNC_ST_ARMS=L400_te GNC_ST_PARTS=mc GNC_ST_SPLIT=0/1 $PY "$C/scripts/m2_start_transient.py" ;;
    e7)       GNC_E7_ARMS=RR66_EI05 GNC_E7_PARTS=run GNC_E7_SPLIT=0/1 $PY "$C/scripts/m2_eng07_6v6.py" ;;
  esac
}
for j in ${1:-st e7 bitcheck}; do
  echo "== $j start $(date -u +%FT%TZ)"
  ( time run "$j" ) > "$RV/logs/rv01_$j.log" 2>&1
  echo "== $j exit $? end $(date -u +%FT%TZ)"
done

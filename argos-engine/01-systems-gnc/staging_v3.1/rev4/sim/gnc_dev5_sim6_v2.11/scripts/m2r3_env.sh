# rev2.1 / rev3 run environment (GNC, 2026-10-13); same inputs as rev2 (m2r2_env.sh) unless a later line changes them
export GNC_IFACE=/home/claude/work/space/iface_v3d
export GNC_ACT_RATE=/home/claude/work/space/iface_v3d/actuator_rate_check_v2.json
export GNC_PC_RATCHET=1
export NUMBA_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
PY="/opt/engine-venv/bin/python -I"
export GNC_IFACE_PIN=/home/claude/work/space/gnc_dev29/data/pins/pins_rev2.sha256
export GNC_STRICT=1
export GNC_EL_SUPPLY=/home/claude/work/shared-fallback/engine/06-electronics/results/tvc_supply_budget_v1.json
export GNC_COMB_V2P4=/home/claude/work/shared-fallback/engine/02-combustion/data/v2p4

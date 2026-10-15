# rev2 run environment (GNC, 2026-10-13)
export GNC_IFACE=/home/claude/work/space/iface_v3d
export GNC_ACT_RATE=/home/claude/work/space/iface_v3d/actuator_rate_check_v2.json
export GNC_PC_RATCHET=1
export NUMBA_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
PY=/opt/engine-venv/bin/python
# N4 (REV-GNC-2): strict inputs + sha256 pin list (run6/engine_v2/tailoff fail on unreadable or mismatched input)
export GNC_IFACE_PIN=/home/claude/work/space/gnc_dev29/data/pins/pins_rev2.sha256
export GNC_STRICT=1
# hub copy of the Electronics TVC supply budget (pinned 3ee9d60ad039ed45), not the Electronics workdir
export GNC_EL_SUPPLY=/home/claude/work/shared-fallback/engine/06-electronics/results/tvc_supply_budget_v1.json
# Combustion v2.4 hub tables (coordinator 2026-10-13: pin from the hub)
export GNC_COMB_V2P4=/home/claude/work/shared-fallback/engine/02-combustion/data/v2p4

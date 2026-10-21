# REV-GNC-6 reviewer run environment (staged hub copies only; no work-area reads). Case arms: iface_v351 + pins_rev4_v351.
export GNC_IFACE=/tmp/claude-0/-home-claude/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv6/snap/iface_v351
export GNC_ACT_RATE=/tmp/claude-0/-home-claude/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv6/snap/iface_v351/actuator_rate_check_v2.json
export GNC_IFACE_PIN=/tmp/claude-0/-home-claude/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv6/snap/pins_rev4/pins_rev4_v351.sha256
export GNC_PC_RATCHET=1
export NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export NUMBA_CACHE_DIR=/tmp/claude-0/-home-claude/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv6/numba_cache
export GNC_STRICT=1
export GNC_EL_SUPPLY=/home/claude/work/shared-fallback/engine/06-electronics/results/tvc_supply_budget_v1.json
export GNC_COMB_V2P4=/home/claude/work/shared-fallback/engine/02-combustion/data/v2p4
export GNC_COMB_V2P4A=/home/claude/work/shared-fallback/engine/02-combustion/data/v2p4a
export GNC_FW_CONFIG=/home/claude/work/shared-fallback/engine/06-electronics/firmware/src/core/config.h
export RV_ALLOW=/tmp/claude-0/-home-claude/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad/rv6
PY="/opt/engine-venv/bin/python -I"

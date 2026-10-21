# REV-GNC-7 reviewer run environment: tree and snapshots in /dev/shm/rev_gnc7 only (iface_v351 verified against pins_rev4_v351 cf6d8d010833a274).
export GNC_IFACE=/dev/shm/rev_gnc7/snap/iface_v351
export GNC_ACT_RATE=/dev/shm/rev_gnc7/snap/iface_v351/actuator_rate_check_v2.json
export GNC_IFACE_PIN=/dev/shm/rev_gnc7/snap/pins_rev4/pins_rev4_v351.sha256
export GNC_PC_RATCHET=1
export NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export NUMBA_CACHE_DIR=/dev/shm/rev_gnc7/numba_cache
export GNC_STRICT=1
export GNC_EL_SUPPLY=/home/claude/work/shared-fallback/engine/06-electronics/results/tvc_supply_budget_v1.json
export GNC_E11_MASS=v351
export RV_ALLOW=/dev/shm/rev_gnc7
export PYTHONDONTWRITEBYTECODE=1

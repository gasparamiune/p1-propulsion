#!/bin/bash
# Combustion v2.4: short calculations, one process at a time (second solver slot)
cd /home/claude/work/combustion/src
D=/home/claude/work/combustion/data/v2/v2p4
echo "=== $(date -u +%FT%TZ) meop"; nice -n 5 /opt/engine-venv/bin/python -I meop_basis_v2p4.py $D > /home/claude/work/combustion/logs/meop.log 2>&1; echo rc=$?
echo "=== $(date -u +%FT%TZ) vent"; nice -n 5 /opt/engine-venv/bin/python -I safing_vent_v2p4.py $D > /home/claude/work/combustion/logs/vent.log 2>&1; echo rc=$?
echo "=== $(date -u +%FT%TZ) axial"; nice -n 5 /opt/engine-venv/bin/python -I b1_axial_law_v2p4.py $D > /home/claude/work/combustion/logs/axial.log 2>&1; echo rc=$?
echo "=== $(date -u +%FT%TZ) chain done"

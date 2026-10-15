#!/bin/bash
cd /home/claude/work/combustion/src
echo "=== $(date -u +%FT%TZ) vent" >> ../logs/chain2_v2p4.log
/opt/engine-venv/bin/python -I safing_vent_v2p4.py /home/claude/work/combustion/data/v2/v2p4 >> ../logs/vent.log 2>&1
echo "rc=$?" >> ../logs/chain2_v2p4.log
echo "=== $(date -u +%FT%TZ) meop" >> ../logs/chain2_v2p4.log
/opt/engine-venv/bin/python -I meop_basis_v2p4.py /home/claude/work/combustion/data/v2/v2p4 >> ../logs/meop.log 2>&1
echo "rc=$?" >> ../logs/chain2_v2p4.log
echo "=== $(date -u +%FT%TZ) chain2 done" >> ../logs/chain2_v2p4.log

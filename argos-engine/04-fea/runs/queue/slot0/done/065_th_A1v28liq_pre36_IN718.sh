set -e
cd /home/claude/work/mechanical/engine/04-fea/thermal
# RG-09 (independent GNC review, coordinator 2026-10-13): A1 p99 EARLY-LIGHT record (v2.8 liquid line, engine-on counter 8.528 s > A1 sizing 8.258 s)
# governs peak temperatures; head-end BC generated with Combustion's unchanged run_dispersed_v2p4.py into runs/comb_bcgen (PROVENANCE.txt)
/opt/engine-venv/bin/python -u run_thermal.py --dc DC-A1v28liq --bound hi --level 2.5 --ov D_pre=0.0499 --mat ENG-TC-03=IN718 --tag v11pre36IN > /home/claude/work/mechanical/runs/thermal/DC-A1v28liq_hi_L2.5_v11pre36IN.log 2>&1
/opt/engine-venv/bin/python -u extract_histories.py DC-A1v28liq_hi_SS316L_L2.5_v11pre36IN > /home/claude/work/mechanical/runs/thermal/DC-A1v28liq_hi_L2.5_v11pre36IN_extract.log 2>&1
/opt/engine-venv/bin/python -u seal_table.py DC-A1v28liq_hi_SS316L_L2.5_v11pre36IN > /home/claude/work/mechanical/runs/thermal/DC-A1v28liq_seal.log 2>&1
/opt/engine-venv/bin/python -u tc03_in718_check.py DC-A1v28liq_hi_SS316L_L2.5_v11pre36IN > /home/claude/work/mechanical/runs/thermal/DC-A1v28liq_tc03.log 2>&1
/opt/engine-venv/bin/python -u segment_heat_coast.py DC-A1v28liq_hi_SS316L_L2.5_v11pre36IN > /home/claude/work/mechanical/runs/thermal/DC-A1v28liq_coast.log 2>&1

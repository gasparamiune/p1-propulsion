#!/bin/bash
cd /home/claude/work/mechanical/v351/engine/03-cad/src/calcs
PY=/opt/engine-venv/bin/python
O=/home/claude/work/mechanical/v351/mass
export OMP_NUM_THREADS=1
nice -n 10 $PY -u mass_variant_v351.py $O/m_base.json > $O/m_base.log 2>&1
nice -n 10 $PY -u mass_variant_v351.py $O/m_bl02.json bleed_tap_v351=true > $O/m_bl02.log 2>&1
nice -n 10 $PY -u mass_variant_v351.py $O/m_hk.json bleed_tap_v351=true 'gimbal_bearing="HK0808"' > $O/m_hk.log 2>&1
echo MASS1_DONE >> $O/m_hk.log

# Validation v2.1 (time-matched three-level GCI, temporal bands, v2op) + Fluent package refresh.
cd /home/claude/work/combustion/cfd/own
/opt/engine-venv/bin/python validate_plume.py /home/claude/work/combustion/cfd/validation
echo "validate exit $?"
/opt/engine-venv/bin/python make_fluent_package.py /home/claude/work/combustion/deliver/05-plume-cfd/fluent-crosscheck /home/claude/work/combustion/cfd/validation | tail -n 20
echo "fluent exit $?"

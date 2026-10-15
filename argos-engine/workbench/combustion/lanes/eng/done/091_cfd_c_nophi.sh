cd /home/claude/work/combustion/cfd/own
export NUMBA_NUM_THREADS=1
R=/home/claude/work/combustion/cfd/ownruns
/opt/engine-venv/bin/python run_plume.py $R/c_2s_100_nophi --level 0.5 --nophi --tend 3.0e-3 > $R/c_2s_100_nophi.log 2>&1
tail -1 $R/c_2s_100_nophi.log

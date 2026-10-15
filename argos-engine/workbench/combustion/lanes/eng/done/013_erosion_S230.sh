cd /home/claude/work/combustion/src
mkdir -p ../data/v2/erosion_S230 ../data/v2/erosion_S230_ground
/opt/engine-venv/bin/python erosion_dc.py ../data/v2/dc_g3 ../data/v2/erosion_S230 DC-A1-S230_neqE1e+03_reg1.csv DC-A2-S230_neqE1e+03_reg1.csv DC-B1-S230_neqE1e+03_reg1.csv DC-B2-S230_neqE1e+03_reg1.csv DC-A1-S230_neqE1e+03_reg1.5.csv DC-A1-S230_neqE1e+03_reg0.6.csv
/opt/engine-venv/bin/python erosion_dc.py ../data/v2/engine_S230 ../data/v2/erosion_S230_ground DC-C-S230_ground_reg1.csv DC-D-S230_ground_reg1.csv

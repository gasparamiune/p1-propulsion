"""Sensitivity of reroute_vapour_v2p4 to the segment volume (Combustion v2.4, 2026-10-13).
Mechanical's re-route (coil_reroute_v341, in progress) moves to a convoluted PTFE hose, ID 10-11 mm (model 10.5) instead of the
8.0 mm smooth bore: the hose bore grows from 9.20 to about 15.8 cm3 (convolution volume TO-VERIFY), so V_seg ~50.6 cm3 (ESTIMATE).
Same model, inputs and heat (the budget's 8 mm hose heat is kept: the larger wetted area of a convoluted bore is NOT added).
usage: python -I reroute_vseg_sens_v2p4.py V_SEG_CM3 DATA_V2P4_DIR BUDGET_JSON TRAPS_JSON SERIES_CSV OUT_JSON
"""
import os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import reroute_vapour_v2p4 as RR

if __name__ == '__main__':
    RR.V_SEG = float(sys.argv[1])
    RR.main(*sys.argv[2:7])

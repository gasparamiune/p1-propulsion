#!/usr/bin/env python3
"""REV-ELEC-2: extract the TANK_COLD-after-ARM mechanism from a single S5 run trace (sil mcone <run>).
The ECU's cold decision (engine_ecu.cpp l.577-581) is tmin = min(valid wall TCs, Tsat(P_tank)) < kTankIgnMin_K 288.15 K, with no guard
band; the logged tank_T column is tmax (l.566-568, telemetry). This script recomputes Tsat from the logged plant P_tank with the firmware
table n2o_sat_table.h (linear interpolation as n2o::tsatK) and prints state, MV, P_tank, Tsat, tank_T (tmax) at each state change and
every 0.1 s up to 8 s. The ECU reads P_tank through its own (dispersed) sensor model, so Tsat here is the plant-pressure value.
SIM (author SIL, reviewer re-run); not hardware evidence. Usage: python -I mcone_extract.py <S5_mc_runN.csv> <n2o_sat_table.h>"""
import csv
import re
import sys

src = open(sys.argv[2]).read()
p0 = float(re.search(r'kSatP0_Pa\s*=\s*([0-9.eE+-]+)f', src).group(1))
dp = float(re.search(r'kSatDp_Pa\s*=\s*([0-9.eE+-]+)f', src).group(1))
arr = re.search(r'kTsat_K\[kSatN\]\s*=\s*\{([^}]*)\}', src).group(1)
tab = [float(v.strip().rstrip('f')) for v in arr.split(',') if v.strip()]


def tsat(p):
    if not (p0 <= p <= p0 + (len(tab) - 1) * dp):
        return float('nan')
    i = min(int((p - p0) / dp), len(tab) - 2)
    f = (p - (p0 + i * dp)) / dp
    return tab[i] + f * (tab[i + 1] - tab[i])


rows = list(csv.DictReader(open(sys.argv[1])))
print('t_s state abort mv mv_latch_hw ptank_bar_abs Tsat_fw_table_K tank_T_tmax_K relight_block thr_cmd_N')
prev = None
tmin_ts = (1e9, None)
for r in rows:
    t = float(r['t'])
    if t > 8.0:
        break
    ts = tsat(float(r['ptank']))
    if ts < tmin_ts[0]:
        tmin_ts = (ts, t)
    st = (r['state'], r['abort'], r['relight_block'], r['mv_latch_hw'])
    grid = abs(t * 10 - round(t * 10)) < 1e-6
    if st != prev or grid:
        print('%.3f %s %s %s %s %.4f %.3f %s %s %s%s' % (t, r['state'], r['abort'], r['mv'], r['mv_latch_hw'], float(r['ptank']) / 1e5, ts,
                                                       r['tank_T'], r['relight_block'], r['thr_cmd'], '  <- change' if st != prev else ''))
    prev = st
first = tsat(float(rows[0]['ptank']))
print('Tsat(P_tank) at t=0: %.3f K; minimum to 8 s: %.3f K at t = %.3f s; limit kTankIgnMin_K = 288.15 K (no guard band)' % (first, tmin_ts[0], tmin_ts[1]))

# REV-ELEC-5: A5 residual in the A1 relight RUN [DERIVED on the Mechanical SIM seat history x the DATASHEET typical 0.0248 bar/K].
# Usage: python3 -I a5_residual_calc.py <seat_hist_A1_NF2b.csv> <out.json>
import csv, json, sys
rows = [r for r in csv.DictReader(open(sys.argv[1]))]
t = [float(r['t_s']) for r in rows]; T = [float(r['dT_sensor_K']) for r in rows]   # SIL reads column 2 (dT_sensor_K)
def at(x):
    if x <= t[0]: return T[0]
    for i in range(1, len(t)):
        if t[i] >= x: return T[i-1] + (T[i]-T[i-1]) * (x - t[i-1]) / (t[i]-t[i-1])
    return T[-1]
c1 = 0.0248   # bar/K, k = 1
E0 = 22.211   # A1 relight E0 on the Mechanical axis (S13T)
out = {"tag": "DERIVED on SIM (Mechanical seat history seat_hist_A1_NF2b.csv, column dT_sensor_K, the SIL basis) x 0.0248 bar/K per k",
       "E0_mech_s": E0, "t_end_hist_s": t[-1]}
# seat rise from the relight P0 (E0 + 0.05 s) over the relight RUN, for burn lengths up to the landing 4.59 s
for L in (1.0, 2.3, 4.59):
    dT = at(E0 + 0.05 + L) - at(E0 + 0.05)
    out[f"rise_P0_to_P0+{L}s_K"] = round(dT, 3)
    out[f"growth_k3_bar_{L}s"] = round(3 * c1 * dT, 3)
    out[f"growth_k1_bar_{L}s"] = round(c1 * dT, 3)
# max rate in [E0, E0 + 4.64 s]
mr = 0.0
for i in range(1, len(t)):
    if t[i] >= E0 and t[i-1] <= E0 + 4.64:
        mr = max(mr, abs(T[i]-T[i-1]) / max(1e-9, t[i]-t[i-1]))
out["max_rate_in_relight_Kps"] = round(mr, 3)
# landing floor numbers
pc_floor_abs = 4.36985   # bar abs, eng::kPcFloorAbs_Pa [COMB] 12.5 % stretch floor at 20 C
sp_min_abs = 0.95 * pc_floor_abs
out["pc_floor_abs_bar"] = pc_floor_abs; out["ecu_sp_min_abs_bar"] = round(sp_min_abs, 3)
for e in (0.30, 0.71, 0.99, 1.02):
    out[f"s+1_e{e}_true_at_sp_min_abs_bar"] = round(sp_min_abs - e, 3)
    out[f"s+1_e{e}_true_vs_floor_pct"] = round(100 * (sp_min_abs - e) / pc_floor_abs - 100, 1)
for e in (0.30, 0.71, 0.76):
    out[f"s-1_e{e}_true_at_cap25_abs_bar"] = round(25.0 + e, 2)
    out[f"s-1_e{e}_true_at_fw_abort30_abs_bar"] = round(30.0 + e, 2)
# A3 FLAMEOUT on a BASE_AMB start (P0 = 0) reading low by |e|, closed loop (measured = sp): ratio = sp_g / (sp_g + |e|) < 0.40 when sp_g < |e| / 1.5
for e in (0.77, 1.02, 2.0, 3.8):
    out[f"BASE_AMB_e-{e}_false_FLAMEOUT_if_sp_gauge_below_bar"] = round(e / 1.5, 3)
# A7 RUN_MAP (flight flag only) s+1: measured sp vs hi = 1.3 x true: flag when sp_abs < 1.3 e / 0.3
for e in (0.30, 0.71, 0.99):
    out[f"A7_flag_s+1_e{e}_when_sp_abs_below_bar"] = round(1.3 * e / 0.3, 2)
for e in (0.30, 0.76):
    out[f"A7_flag_s-1_e{e}_when_sp_abs_below_bar"] = round(0.7 * e / 0.3, 2)
json.dump(out, open(sys.argv[2], 'w'), indent=1)
print(json.dumps(out, indent=1))

#!/usr/bin/env python3
# REV-ELEC-3 R3-01 reviewer calculation (DERIVED; inputs read only). Run: python3 -I r3_01_c1_drift_v1.py <out.json>
# C1 Kulite XTL-190SM-2000A thermal zero 1 %FS / 100 F typical [DATASHEET as quoted in pc_transducer_v3.json B_candidates_datasheet.C1]
# times the Mechanical seat-node history (pc_transducer_temperature_v1.json -> monitors.csv, SIM, 20 C start) relative to ARM (t = 0),
# against the v2.11 limits (config.h kPcRezeroMax_Pa 0.30 bar, kIgnBaseCheck_Pa 0.70 / 0.40 bar) and the recorded S13 B-ext
# relight outcome bands (offset at the lift tick E1, where the BASE check reads the pre-lift baseline) (S13_run_log.txt / S13B_ext_bpc1_true_run_log.txt, SIM). k = max/typ coefficient ratio (F-10: MISSING).
import csv, json, sys, hashlib
MJ = '/home/claude/work/mechanical/v351/pc/pc_transducer_temperature_v1.json'
CASE = 'DC-A1dispp99_tg711_hi_SS316L_L2.5_v351_TB1GC'
FS_bar = 137.9                      # C1 2000 psia [DATASHEET]
coef = 0.01 * FS_bar / (100.0 / 1.8)  # 1 %FS per 100 F -> bar/K
def h16(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
mj = json.load(open(MJ)); a = mj[CASE]; mon = a['monitors_csv']
rows = [r for r in csv.reader(l for l in open(mon) if not l.startswith('#'))]
hdr = rows[0]; data = [[float(x) for x in r] for r in rows[1:]]
col = {n: i for i, n in enumerate(hdr)}
def T(name, t):
    i = col[name]; prev = data[0]
    for r in data:
        if r[0] >= t:
            if r[0] == prev[0]: return r[i] - 273.15
            f = (t - prev[0]) / (r[0] - prev[0]); return prev[i] + f * (r[i] - prev[i]) - 273.15
        prev = r
    return data[-1][i] - 273.15
seg = a['segments_s']; t_meco = seg[0][1]; t_rl = seg[1][0]
times = {'ARM_t0': 0.001, 'coast_rezero1_end_MECO+1.4s': t_meco + 1.4, 'purge_cmd_E0-2.9s': t_rl - 2.9,
         'rezero2_block_end_purge-0.05s': t_rl - 2.95, 'relight_E0': t_rl, 'relight_E1_lift_E0+0.045s': t_rl + 0.045, 'relight_light_E0+0.36s': t_rl + 0.36}
nodes = ['T1_head_top_bracket_foot', 'head_bore_N2O']
out = {'script': 'r3_01_c1_drift_v1.py', 'tag': 'DERIVED (SIM thermal history x DATASHEET typical coefficient; k ASSUMED sweep, F-10 MISSING)',
       'inputs': {'mech_json': [MJ, h16(MJ)], 'monitors_csv': [mon, h16(mon)]}, 'coef_typ_bar_per_K': round(coef, 5),
       'timeline_s': {k: round(v, 3) for k, v in times.items()}, 'seat_C': {}, 'shift_vs_ARM_bar_typ': {}, 'k_sweep': {}}
lim = {'rezero_max': 0.30, 'base_default': 0.70, 'base_bpc1': 0.40, 'loss_neg_default': 0.75, 'loss_neg_bpc1': 0.50, 'loss_pos_torch': 1.05}
out['limits_bar'] = lim
for n in nodes:
    out['seat_C'][n] = {k: round(T(n, v), 2) for k, v in times.items()}
    dT = {k: T(n, v) - T(n, times['ARM_t0']) for k, v in times.items()}
    out['shift_vs_ARM_bar_typ'][n] = {k: round(coef * v, 3) for k, v in dT.items()}
    ks = {}
    for k in (1.0, 1.5, 2.0, 3.0):
        s_rz2 = k * coef * dT['rezero2_block_end_purge-0.05s']; s_light = k * coef * dT['relight_E1_lift_E0+0.045s']
        acc = abs(s_rz2) <= lim['rezero_max']
        resid = s_light - s_rz2 if acc else s_light
        ks[str(k)] = {'rezero2_shift_bar': round(s_rz2, 3), 'rezero2_accepted': acc, 'drift_at_E1_base_check_vs_zero_bar': round(resid, 3),
                      'default_build_negative_sign': 'RELIGHT LOST (PC_SENSOR)' if resid >= lim['loss_neg_default'] else ('BASE_AMB band' if resid > lim['base_default'] else 'RUN'),
                      'bpc1_build_negative_sign': 'RELIGHT LOST (PC_SENSOR)' if resid >= lim['loss_neg_bpc1'] else ('BASE_AMB band' if resid > lim['base_bpc1'] else 'RUN'),
                      'positive_sign': 'TORCH_FAULT (torch gate blocked)' if resid >= lim['loss_pos_torch'] else ('BASE_HIGH -> RUN on measured P0' if resid > lim['base_default'] else 'RUN')}
        ks[str(k)]['k_for_rezero2_reject'] = round(lim['rezero_max'] / (coef * dT['rezero2_block_end_purge-0.05s']), 3)
        ks[str(k)]['k_for_loss_default_if_rejected'] = round(lim['loss_neg_default'] / (coef * dT['relight_E1_lift_E0+0.045s']), 3)
        ks[str(k)]['k_for_loss_bpc1_if_rejected'] = round(lim['loss_neg_bpc1'] / (coef * dT['relight_E1_lift_E0+0.045s']), 3)
    out['k_sweep'][n] = ks
# comparator U330 (no auto-zero): shift from the 20 C bench trim; the trim temperature is the ARM temperature only on a 20 C day
out['U330_shift_from_20C_trim_bar_typ'] = {n: {'relight_burn_end': round(coef * (T(n, seg[1][1]) - 20.0), 3)} for n in nodes}
out['U330_band_circuit_bar'] = [31.079, 34.106]
out['note'] = ('ARM-relative shifts assume T0 = 20 C (every Mechanical run starts at 20 C). For a linear conduction model with T0 a common '
               'offset the ARM-relative rise is independent of T0 to first order; the comparator shift is trim-relative and adds coef x (T0 - 20 C).')
json.dump(out, open(sys.argv[1], 'w'), indent=1)
print(json.dumps(out, indent=1))

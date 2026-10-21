#!/usr/bin/env python3
# REV-ELEC-4: first-start timing extract of one reviewer S13T_ONLY CSV between t_from and t_to: E1 (first tick with ign_lift_t > 0),
# plant light (first tick with ignited = 1), E2 (first RUN entry), first abort, TLM b4-b7 transitions, ECU Pc_meas (pcAbsFiltered,
# compensated) at E2 and its max in RUN, plant Pc max. usage: python3 -I first_start_extract.py <csv> <out.json> <t_from> <t_to>
import csv, hashlib, json, sys
p, out_p, t0, t1 = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
b = open(p, 'rb').read(); r = csv.reader(open(p)); h = next(r); ix = {k: i for i, k in enumerate(h)}
d = {'csv': p.split('/')[-1], 'csv_sha16': hashlib.sha256(b).hexdigest()[:16], 'bytes': len(b), 'tag': 'SIM (SIL plant)', 'window_s': [t0, t1],
     'E1_s': None, 'plant_light_s': None, 'E2_s': None, 'first_abort': None, 'state_changes': [], 'tlm_b4_b7_transitions': [],
     'Pc_meas_abs_at_E2_Pa': None, 'Pc_meas_abs_max_in_RUN_Pa': None, 'Pc_plant_abs_max_Pa': None}
prev = None; pfl = None; pcrun = None; pcp = -1e18
for row in r:
    t = float(row[0])
    if t < t0: continue
    if t > t1: break
    st = int(row[ix['state']]); ab = int(row[ix['abort']]); fl = int(row[ix['a7_tlmf']]) & 0xF0; pcm = float(row[ix['Pc_meas']])
    if d['E1_s'] is None and float(row[ix['ign_lift_t']]) > 0: d['E1_s'] = round(t, 4)
    if d['plant_light_s'] is None and int(float(row[ix['ignited']])) == 1: d['plant_light_s'] = round(t, 4)
    if prev is not None and st != prev:
        d['state_changes'].append([round(t, 4), prev, st, ab])
        if st == 4 and d['E2_s'] is None: d['E2_s'] = round(t, 4); d['Pc_meas_abs_at_E2_Pa'] = pcm
    if pfl is not None and fl != pfl:
        for bit in range(4, 8):
            if (fl ^ pfl) & (1 << bit): d['tlm_b4_b7_transitions'].append([round(t, 4), bit, 1 if fl & (1 << bit) else 0])
    prev = st; pfl = fl
    if st == 4: pcrun = pcm if pcrun is None else max(pcrun, pcm)
    if ab and d['first_abort'] is None: d['first_abort'] = [round(t, 4), ab]
    pcp = max(pcp, float(row[ix['Pc']]))
d['Pc_meas_abs_max_in_RUN_Pa'] = pcrun; d['Pc_plant_abs_max_Pa'] = round(pcp, 1)
d['note'] = 'states 3 IGNITION, 4 RUN, 8 ABORT, 0 SAFE, 7 COAST, 5 SHUTDOWN; abort 4 FLAMEOUT, 12 PC_SENSOR, 3 NO_IGNITION, 22 TORCH_FAULT; b4 E2, b5 RISE_NOW, b6 RISE_HELD, b7 RISE_HELD_T'
json.dump(d, open(out_p, 'w'), indent=1); print(json.dumps(d))

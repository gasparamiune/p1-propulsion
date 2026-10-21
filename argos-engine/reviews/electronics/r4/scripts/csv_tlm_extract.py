#!/usr/bin/env python3
# REV-ELEC-4: compact timing extract of one reviewer S13T_ONLY CSV (state changes, E2 = RUN entry, TLM flag bit transitions after t0,
# first abort, ECU compensated filtered Pc (Pc_meas, abs) at E2 and its max in RUN, plant Pc max). Writes a small JSON; the caller
# deletes the CSV afterwards.  usage: python3 -I csv_tlm_extract.py <csv> <out.json> <t_from_s>
import csv, hashlib, json, sys
p, out_p, t0 = sys.argv[1], sys.argv[2], float(sys.argv[3])
b = open(p, 'rb').read()
r = csv.reader(open(p)); h = next(r); ix = {k: i for i, k in enumerate(h)}
d = {'csv': p.split('/')[-1], 'csv_sha16': hashlib.sha256(b).hexdigest()[:16], 'bytes': len(b), 'tag': 'SIM (SIL plant)', 't_from_s': t0,
     'state_changes': [], 'tlm_bit_transitions': [], 'first_abort': None, 'E2_s': None, 'Pc_meas_abs_at_E2_Pa': None,
     'Pc_meas_abs_max_in_RUN_Pa': None, 'Pc_plant_abs_max_Pa': None, 'seat_comp_note': 'Pc_meas = EngineEcu::pcAbsFiltered() (compensated, filtered, abs)'}
prev = None; prevfl = None; pcrun = None; pcp = -1e18
for row in r:
    t = float(row[0])
    if t < t0: continue
    st = int(row[ix['state']]); ab = int(row[ix['abort']]); fl = int(row[ix['a7_tlmf']]); pcm = float(row[ix['Pc_meas']])
    if prev is not None and st != prev:
        d['state_changes'].append([round(t, 4), prev, st, ab])
        if st == 4 and d['E2_s'] is None: d['E2_s'] = round(t, 4); d['Pc_meas_abs_at_E2_Pa'] = pcm
    if prevfl is None: d['tlm_bits_at_t0'] = fl
    elif fl != prevfl:
        for bit in range(8):
            if (fl ^ prevfl) & (1 << bit): d['tlm_bit_transitions'].append([round(t, 4), bit, 1 if fl & (1 << bit) else 0])
    prev = st; prevfl = fl
    if st == 4: pcrun = pcm if pcrun is None else max(pcrun, pcm)
    if ab and d['first_abort'] is None: d['first_abort'] = [round(t, 4), ab]
    pcp = max(pcp, float(row[ix['Pc']]))
d['Pc_meas_abs_max_in_RUN_Pa'] = pcrun; d['Pc_plant_abs_max_Pa'] = round(pcp, 1)
d['note'] = 'states: 3 IGNITION, 4 RUN, 8 ABORT, 0 SAFE; a7_tlmf bits: b0 R2_HOLD-log/b1 DROGUE-log as written by the SIL, b4 E2, b5 RISE_NOW, b6 RISE_HELD, b7 RISE_HELD_T (types.h tlmf); abort 4 FLAMEOUT, 12 PC_SENSOR, 3 NO_IGNITION'
json.dump(d, open(out_p, 'w'), indent=1)
print(json.dumps(d))

#!/usr/bin/env python3
"""REV-ELEC-2: summarize the reviewer R2-hold probe output (PROBE lines of sil_r2probe, R2PROBE=all).
Groups by probe tag, thrust level, report (hold) flag, onset of the Pc loss and frame noise; counts outcomes; lists every DEAD_RELEASED
case with its 100 Hz / 50 Hz frame phase, release time, peak measured force and dead lift. SIM (reviewer probe of the author SIL),
not hardware evidence and not physical approval. Usage: python -I summarize_probe.py <probe_stdout.txt>"""
import collections
import re
import sys

pat = re.compile(r'^PROBE (\S+)\s+F\s+(\d+) rep (\d) onset\s+([\d.\-]+) fo\s+([\d.\-]+) d_app\s+([\d.]+) noise ([\d.]+) seed\s+(\d+) '
                 r'ph100 (\d) ph50 (\d) starve ([\d.]+) drop (\d) \| (\S+)\s+\| rel\s+(\S+) ms br (\d) \| abort_frame\s+(\S+) \| '
                 r'ECU (\S+)\s+(\S+) \| inval\s+(\S+) \| Fmax\s+(\S+) nmax (\d) \| hold\s+(\d+) \(\s*(\S+)\.\.\s*(\S+)\) sp (\S+) \| '
                 r'dead lift (\S+) Fcold (\S+)')
rows = []
for line in open(sys.argv[1]):
    m = pat.match(line)
    if m:
        g = m.groups()
        rows.append(dict(tag=g[0], F=int(g[1]), rep=int(g[2]), onset=float(g[3]), d_app=float(g[5]), noise=float(g[6]), seed=int(g[7]),
                         ph100=int(g[8]), ph50=int(g[9]), starve=float(g[10]), drop=int(g[11]), outcome=g[12], rel=g[13], br=int(g[14]),
                         ecu=g[16], t_ecu=g[17], fmax=float(g[19]), nmax=int(g[20]), hold=int(g[21]), h0=g[22], h1=g[23],
                         lift=g[25], fcold=g[26]))
print(f'PROBE lines parsed: {len(rows)}')
grp = collections.OrderedDict()
for r in rows:
    k = (r['tag'], r['F'], r['rep'], r['onset'], r['noise'], r['d_app'], r['starve'], r['drop'])
    grp.setdefault(k, collections.Counter())[r['outcome']] += 1
print('tag | F N | hold(rep) | onset ms | noise N rms | d_app N | starve s | drop | outcomes')
for k, c in grp.items():
    print(f'{k[0]:14s} | {k[1]:3d} | {k[2]} | {k[3]:5.1f} | {k[4]:.1f} | {k[5]:5.2f} | {k[6]:.3f} | {k[7]} | {dict(c)}')
print('\nDEAD_RELEASED cases (dead engine released by the FC rule):')
for r in rows:
    if r['outcome'] == 'DEAD_RELEASED':
        print(f"  {r['tag']:14s} F {r['F']} onset {r['onset']:.1f} ms noise {r['noise']} seed {r['seed']} ph100 {r['ph100']} ph50 {r['ph50']} "
              f"| release {r['rel']} ms after E2 | Fmax {r['fmax']:.2f} N nmax {r['nmax']} | dead lift {r['lift']} mm Fcold {r['fcold']} N")
print('\nD starve sweep (outcome, release or ECU abort time after E2):')
for r in rows:
    if r['tag'].startswith('D_'):
        print(f"  {r['tag']:14s} starve {r['starve']:.3f} s | {r['outcome']:16s} | rel {r['rel']} ms | ECU {r['ecu']} {r['t_ecu']} ms")
print('\nE dropped DROGUE 0 frame:')
for r in rows:
    if r['tag'].startswith('E_'):
        print(f"  {r['tag']:14s} F {r['F']} drop {r['drop']} | {r['outcome']} rel {r['rel']} ms | hold ticks {r['hold']} ({r['h0']}..{r['h1']} ms after E2) "
              f"at {r['fcold'] if False else ''}setpoint 62.50 N")

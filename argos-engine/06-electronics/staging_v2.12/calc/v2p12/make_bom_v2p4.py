#!/usr/bin/env python3
# Electronics v2.12 (2026-10-21): BOM v2.4 = BOM v2.3 (results/bom_v2p3.csv) with the text of rows 205 and 251 changed (REV-ELEC-3
# R3-05 compensated band; R3-01 option (b): row 205 becomes the C1 seat TC on the TC4 channel). Same 266 rows and line numbers; no price
# entered (TO-QUOTE delivered to Soenderborg, DK-6400). Run: python3 -B -I make_bom_v2p4.py <out.csv>
import csv, hashlib, io, sys
E = '/home/claude/work/electronics'
SRC = E + '/results/bom_v2p3.csv'
def h16(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
src_h = h16(SRC)
rows = list(csv.reader(open(SRC, newline='', encoding='utf-8')))
hdr = rows[0]; ix = {k: i for i, k in enumerate(hdr)}
by = {r[0]: r for r in rows[1:]}
assert len(rows) - 1 == 266 and by['251'][ix['part']].startswith('Kulite XTL-190SM-2000A') and by['205'][ix['refs']] == 'J904'
r = by['205']
r[ix['part']] = 'type K MI thermocouple, grounded junction, 0.5-1.0 mm sheath (TO-SELECT with Mechanical for the C1 boss)'
r[ix['description']] = ('v2.12 C1 SEAT TC (REV-ELEC-3 R3-01 option (b), LEAD 2026-10-21T11:25Z working basis): TC4 channel (MAX31856 U904, J904) '
                        'at the head-top surface by the C1 boss (Mechanical sensor node r 25.875 mm, z = zt); flight use DEFINED (v2.7-v2.11: '
                        'bore-top / manifold TC, CF-3/T1 evidence, flight use TO-DEFINE)')
r[ix['order_key']] = 'type K MI, Class 1; length and termination TO-DEFINE (harness to J904); bonding / clamp at the boss TO-DEFINE with Mechanical'
r[ix['tag']] = 'DESIGN (fw v2.12 option (b); mass about 5 g ASSUMED)'
r[ix['note']] = ('B-PC-1 seat-TC channel row (offset <= 0.3 K after CJTO trim, tau <= 0.25 s); firmware Inputs::tc_bore_K; f3 SEAT_NOREF / '
                 'SEAT_FROZEN on loss; mass about 5 g ASSUMED (not in the mechanical ledger: MISSING)')
r = by['251']
d = r[ix['description']]
old = "compensated 25-80 C as standard (order 20-120 C: 'any 100 F range on request')"
assert d.count(old) == 1
r[ix['description']] = d.replace(old, "compensated 25-80 C as standard; 'any 100 F range on request' (v2.12 R3-05: order the 100 F band 0-55.6 C "
                                 "= 32-132 F, coldest ARM to the hottest flight A1 relight seat 54.7 C; a wider 0-85 C band for the stand relight "
                                 "after B1 (about 78 C at E1) and the thermal-zero MAXIMUM asked in F-10; the v2.3 '20-120 C' order is WITHDRAWN)")
ok = r[ix['order_key']]
assert ok.count('compensated range 20-120 C') == 1
r[ix['order_key']] = ok.replace('compensated range 20-120 C', 'compensated range 0-55.6 C (100 F; or 0-85 C if offered, F-10)')
r[ix['note']] = r[ix['note']] + ('. v2.12: per-serial zero TC (seat coefficient and T_cal) measured at B-PC-1 over 0-85 C (bench plan v5) for '
                                 'the option (b) seat compensation')
for k in ('unit_price', 'currency'):
    assert all(x[ix[k]] in ('',) or x[ix['price_basis']] != 'TO-QUOTE' for x in rows[1:])
buf = io.StringIO(); w = csv.writer(buf, lineterminator='\r\n'); w.writerows(rows)
open(sys.argv[1], 'w', encoding='utf-8', newline='').write(buf.getvalue())
print('bom_v2p4 from bom_v2p3', src_h, '->', sys.argv[1], len(rows) - 1, 'rows; changed rows 205, 251')

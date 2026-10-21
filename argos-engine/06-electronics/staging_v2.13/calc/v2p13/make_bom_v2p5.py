#!/usr/bin/env python3
# Electronics v2.13 (2026-10-21): BOM v2.5 = BOM v2.4 (staging_v2.12/results/bom_v2p4.csv eb6e77dcd4610383) with the REV-ELEC-4 label
# corrections (E4-05 (6), E4-06 (3)-(4)) and the CHANGELOG 264 (4) P_torch move. Rows 1-266 keep their numbers; rows 267-269 are new.
# No price entered (TO-QUOTE delivered to Soenderborg, DK-6400). Run: python3 -B -I make_bom_v2p5.py <bom_v2p4.csv> <out.csv>
import csv, hashlib, io, sys
SRC, OUT = sys.argv[1], sys.argv[2]
assert hashlib.sha256(open(SRC, 'rb').read()).hexdigest()[:16] == 'eb6e77dcd4610383'
rows = list(csv.reader(open(SRC, newline='', encoding='utf-8')))
hdr = rows[0]; ix = {k: i for i, k in enumerate(hdr)}
by = {r[0]: r for r in rows[1:]}
assert len(rows) - 1 == 266
DK = 'TO-QUOTE (DK VAT, shipping and duty to Soenderborg, DK-6400, Denmark)'
# row 187 (E4-06 (3)): TC4 label; the U904 configuration (ITEM 3)
r = by['187']; d = r[ix['description']]
old = 'TC4 bore-top / manifold (firmware v2.7, CF-3/T1 evidence)'
assert d.count(old) == 1
r[ix['description']] = d.replace(old, 'C1 seat TC (TC4, MAX31856 U904, J904)')
r[ix['note']] = (r[ix['note']] + ('; ' if r[ix['note']] else '') +
                 'v2.13: U904 (TC4) configured 50 Hz notch, auto-conversion, AVGSEL <= 2 samples (period <= 0.130 s: DATASHEET 19-7534 Rev 0 tCONV 50 Hz '
                 '98 / 110 ms + 20 ms per extra sample, TO-VERIFY on the PDF; measured at B-TC-1)')
# row 83 (J904 connector label, E4-05 (6))
r = by['83']; d = r[ix['description']]
old = 'type K thermocouple bore-top / manifold (firmware v2.7, CF-3/T1 evidence)'
assert d.count(old) == 1
r[ix['description']] = d.replace(old, 'type K C1 seat TC (TC4, J904; v2.12 option (b) input)')
# row 205 (C1 seat TC): v2.13 checks and the grounded-junction item
r = by['205']
assert r[ix['refs']] == 'J904'
r[ix['note']] = (r[ix['note']] + '. v2.13: f3 SEAT_STEP on a step > 1.5 K per conversion or a reading > 3 K from the 5 K/s-slewed T_c outside the '
                 'light-window hold (bench plan v5.1 B-PC-1 / B-TC-1 TC4 rows); grounded junction vs MAX31856 DS Note 6 (floating TC, BIAS to T-) '
                 'TO-VERIFY (E4-N10); mass 5 g ASSUMED now in the v4.2 mass statement')
r[ix['note']] = r[ix['note']].replace('mass about 5 g ASSUMED (not in the mechanical ledger: MISSING)', 'mass about 5 g ASSUMED (v4.2 mass statement; Mechanical ledger to carry it)')
# rows 81 / 199 / 225: P_torch moves to the C1 family (264 (4))
r = by['81']; d = r[ix['description']]
assert 'torch chamber pressure TE M3234-000005-070BG' in d
r[ix['description']] = d.replace('torch chamber pressure TE M3234-000005-070BG',
                                 'torch chamber pressure: v2.13 (264 (4)) P_torch moves to the C1-family Kulite XTL-190SM-2000A (row 267, bridge output through row 268); '
                                 'this 3-pin amplified-sensor connector is REPLACED by the C1-type bridge connector at schematic v2.6 (NOT drawn); was TE M3234-000005-070BG')
r = by['199']
assert r[ix['qty']] == '2' and r[ix['refs']] == 'J901 (P_torch); B-PC-1 static-level reference'
r[ix['qty']] = '1'; r[ix['refs']] = 'B-PC-1 static-level reference (J901 P_torch until v2.12)'
d = r[ix['description']]; assert d.startswith('P_torch on the torch body port (J901) and the B-PC-1 static-level reference')
r[ix['description']] = d.replace('P_torch on the torch body port (J901) and the B-PC-1 static-level reference',
                                 'B-PC-1 static-level reference (v2.13: no longer P_torch, see row 267)', 1)
r[ix['note']] = (r[ix['note']] + ('; ' if r[ix['note']] else '') +
                                'v2.13 (264 (4)): qty 2 -> 1, P_torch (J901) moves to row 267; the TE M3234-000005-070BG stays as the B-PC-1 static-level reference (and the reserved over-range spare) only')
r = by['225']
assert r[ix['qty']] == '3' and r[ix['description']] == 'M3200 connector code 4 mates (J901 070BG, B-PC-1 reference 070BG, J603 170BG)'
r[ix['qty']] = '2'; r[ix['description']] = 'M3200 connector code 4 mates (B-PC-1 reference 070BG, J603 170BG; the J901 070BG mate dropped at v2.13, 264 (4))'
r[ix['note']] = (r[ix['note']] + ('; ' if r[ix['note']] else '') + 'v2.13: qty 3 -> 2, the J901 070BG mate is no longer needed (264 (4))')
def row(n, section, refs, qty, spare, part, desc, vendor, alt, key, tag, note):
    x = [''] * len(hdr)
    x[ix['line']] = str(n); x[ix['section']] = section; x[ix['refs']] = refs; x[ix['qty']] = str(qty); x[ix['spare_recommended']] = spare
    x[ix['part']] = part; x[ix['description']] = desc; x[ix['vendor']] = vendor; x[ix['vendor_alt']] = alt; x[ix['order_key']] = key
    x[ix['price_basis']] = 'TO-QUOTE'; x[ix['delivered_price_DK6400']] = DK; x[ix['tag']] = tag; x[ix['owner']] = 'Electronics'; x[ix['note']] = note
    return x
rows.append(row(267, 'K v2.13 delta / D vehicle sensors', 'J901 (P_torch)', 1, '1',
                'Kulite XTL-190SM-2000A (ordering code TO-VERIFY with Kulite; same family as row 251)',
                'P_torch on the torch body (264 (4) option 2 ADOPTED): proof 206.8 bar abs [DATASHEET] against the 166.14 bar abs requirement (1.1 x FA1S 151.04 bar abs) [DERIVED]; '
                'the output saturates at the INA333 rail above 146.5 bar abs during FA-1, recovery TO-VERIFY at B-PC-1 / F-12',
                'Kulite Semiconductor (kulite.com) via EU office', '', 'XTL-190SM-2000A, ordering code TO-VERIFY',
                'DATASHEET proof (LEAD 264 (4)); DESIGN',
                're-base of kTorchArmZeroMax_Pa / kPtorchRezeroMax_Pa OPEN (E4-N04: C1-family torch zero shift 0.32 x k / 1.28 x k bar A1 / stand; torch local heat MISSING)'))
rows.append(row(268, 'K v2.13 delta / A ECU PCB', 'P_torch bridge amplifier (ref TO-ASSIGN, schematic v2.6)', 1, '1', 'TI INA333AIDGKR',
                'P_torch bridge amplifier on +5V_SNS (as row 252 for Pc / P_feed / P_mid), G and RG per the C1 chain (pc_transducer_v3 E)',
                'Mouser Electronics (mouser.dk)', 'Digi-Key (digikey.dk)', 'INA333AIDGKR', 'DESIGN', 'schematic v2.6 NOT drawn'))
rows.append(row(269, 'K v2.13 delta / H test stand + bench', 'stand DAQ (C7 bore-top)', 1, '',
                'type K thermocouple, bore-top position (v2.7 CF-3 / T1), stand only',
                'C7 bore-top stand-DAQ TC (CHANGELOG l.55; config.h comment at the seat-TC block): STAND-ONLY channel on the stand DAQ, not on the ECU '
                '(the ECU MAX31856 #4 is the C1 seat TC since v2.12); REV-ELEC-4 E4-06 (4)',
                'TC Ltd (tc.co.uk, UK)', 'Omega Engineering (omega.co.uk)', 'type K; length TO-DEFINE', 'DESIGN', 'bench plan v5.1 stand DAQ thermocouple'))
txt = '\n'.join(','.join(c for c in r) for r in rows)
assert 'bore-top / manifold (firmware v2.7' not in by['187'][ix['description']] + by['83'][ix['description']]
buf = io.StringIO(); w = csv.writer(buf, lineterminator='\r\n'); w.writerows(rows)
open(OUT, 'w', encoding='utf-8', newline='').write(buf.getvalue())
print('bom_v2p5 from bom_v2p4 eb6e77dcd4610383 ->', OUT, len(rows) - 1, 'rows; changed 81, 83, 187, 199 (qty 2 -> 1), 205, 225 (qty 3 -> 2); new 267-269')

"""Assemble REPORT v2.4 (02-combustion) from the published v2.3 REPORT.md and the v2.4 section drafts (Combustion v2.4, 2026-10-13).
The v2.3 text is kept where v2.4 does not change it; blocks in the drafts are applied by heading anchors on the v2.3 text:
  s0_final.txt replaces the title, checkpoint and contents (v2.3 lines before '## 1.'); s2_early APPEND_24; s2_feed_v3.txt (§2.6, §2.7)
  plus s2_8_v341.txt (§2.8) replace v2.3 §2.6; s3 REPLACE_31_DECISION, REPLACE_35_SEAT, REPLACE_36 + INSERT_37; s4 REPLACE_41,
  APPEND_43, APPEND_44, INSERT_46; s5 APPEND_51, REPLACE_54; s6_s8 APPEND_61, APPEND_64, APPEND_8; s6_5 INSERT_65; s7 APPEND_72,
  REPLACE_73 + INSERT_74_77 (APPEND_72 and APPEND_8 are placed at the end of §7.2 and §8 within the same edits); s9_14 REPLACE_9, APPEND_10, APPEND_11 + REPLACE_12, APPEND_13, APPEND_14; one literal substitution in §2.1
  (RC-13 b).  The interface hash is filled in from the published combustion.json v2.4.
usage: python -I build_report_v2p4.py REPORT_v2p3.md DRAFT_DIR IFACE_SHA16 OUT_TXT
"""
import hashlib, os, re, sys
V23_SHA = '59f69506fb5aa935'
src, dd, iface, out = sys.argv[1:5]
raw = open(src).read()
assert hashlib.sha256(raw.encode()).hexdigest()[:16] == V23_SHA, 'v2.3 REPORT.md changed'
L = raw.split('\n')

def blocks(fn):
    t = open(os.path.join(dd, fn)).read()
    b = {m.group(1): m.group(2).split('\n') for m in re.finditer(r'^@@([A-Z0-9_]+)@@\n(.*?)\n@@END@@', t, re.S | re.M)}
    assert b, fn
    return b

def text(fn):
    return open(os.path.join(dd, fn)).read().rstrip('\n').split('\n')

def H(prefix):
    idx = [i for i, l in enumerate(L) if l.startswith(prefix)]
    assert len(idx) == 1, (prefix, idx)
    return idx[0]

def end_of(prefix):
    i = H(prefix); lev = len(prefix) - len(prefix.lstrip('#'))
    for j in range(i + 1, len(L)):
        m = re.match(r'^(#+) ', L[j])
        if m and len(m.group(1)) <= lev:
            return j
    return len(L)

def find_in(prefix, start_text):
    a, b = H(prefix), end_of(prefix)
    idx = [i for i in range(a, b) if L[i].startswith(start_text)]
    assert len(idx) == 1, (prefix, start_text, idx)
    return idx[0]

B3, B4, B5, B68, B7, B9 = (blocks(f) for f in ('s3.txt', 's4.txt', 's5.txt', 's6_s8.txt', 's7.txt', 's9_14.txt'))
B2e, B65 = blocks('s2_early.txt'), blocks('s6_5.txt')
for b, keys in ((B3, {'REPLACE_31_DECISION', 'REPLACE_35_SEAT', 'REPLACE_36', 'INSERT_37'}), (B4, {'REPLACE_41', 'APPEND_43', 'APPEND_44', 'INSERT_46'}),
                (B5, {'APPEND_51', 'REPLACE_54'}), (B68, {'APPEND_61', 'APPEND_64', 'APPEND_8'}), (B7, {'APPEND_72', 'REPLACE_73', 'INSERT_74_77'}),
                (B9, {'REPLACE_9', 'APPEND_10', 'APPEND_11', 'REPLACE_12', 'APPEND_13', 'APPEND_14'}), (B2e, {'APPEND_24'}), (B65, {'INSERT_65'})):
    assert set(b) == keys, (set(b), keys)
E = ['']
ops = [  # (start, end, new_lines) on the v2.3 line array
    (0, H('## 1. '), text('s0_final.txt') + E),
    (end_of('### 2.4 '), end_of('### 2.4 '), B2e['APPEND_24'] + E),
    (H('### 2.6 '), end_of('### 2.6 '), text('s2_feed_v3.txt') + E + text('s2_8_v341.txt') + E),
    (find_in('### 3.1 ', 'Decision (LEAD 2026-10-11'), find_in('### 3.1 ', 'Decision (LEAD 2026-10-11') + 1, B3['REPLACE_31_DECISION']),
    (find_in('### 3.5 ', '**Seat.**'), end_of('### 3.5 '), B3['REPLACE_35_SEAT'] + E),
    (H('### 3.6 '), end_of('### 3.6 '), B3['REPLACE_36'] + E + B3['INSERT_37'] + E),
    (H('### 4.1 '), end_of('### 4.1 '), B4['REPLACE_41'] + E),
    (end_of('### 4.3 '), end_of('### 4.3 '), B4['APPEND_43'] + E),
    (end_of('### 4.4 '), end_of('### 4.4 '), B4['APPEND_44'] + E),
    (H('## 5. '), H('## 5. '), B4['INSERT_46'] + E),
    (end_of('### 5.1 '), end_of('### 5.1 '), B5['APPEND_51'] + E),
    (H('### 5.4 '), end_of('### 5.4 '), B5['REPLACE_54'] + E),
    (end_of('### 6.1 '), end_of('### 6.1 '), B68['APPEND_61'] + E),
    (end_of('### 6.4 '), end_of('### 6.4 '), B68['APPEND_64'] + E + B65['INSERT_65'] + E),
    (H('### 7.3 '), end_of('### 7.3 '), B7['APPEND_72'] + E + B7['REPLACE_73'] + E + B7['INSERT_74_77'] + E),   # APPEND_72 ends §7.2
    (H('## 9. '), end_of('## 9. '), B68['APPEND_8'] + E + B9['REPLACE_9'] + E),   # APPEND_8 ends §8
    (end_of('## 10. '), end_of('## 10. '), B9['APPEND_10'] + E),
    (H('## 12. '), end_of('## 12. '), B9['APPEND_11'] + E + B9['REPLACE_12'] + E),
    (end_of('## 13. '), end_of('## 13. '), B9['APPEND_13'] + E),
    (len(L), len(L), E + B9['APPEND_14']),
]
ops.sort(key=lambda o: (o[0], o[1]))
for (a0, a1, _), (b0, b1, _) in zip(ops, ops[1:]):
    assert a1 <= b0 and not (a0 == b0), ('overlap', a0, a1, b0, b1)
for a, b, new in sorted(ops, key=lambda o: o[0], reverse=True):
    L[a:b] = new
s = '\n'.join(L)
old = 'The requirement is 20 +/- 3 C (ENG-12).'
assert s.count(old) == 1
s = s.replace(old, 'The conditioning requirement is 15-25 C (ENG-12, REQUIREMENTS rev 2; RC-13 b), with the 24 C liquid-line interlock (§2.8) and the arm limits of §7.3.')
assert s.count('@@IFACE_SHA@@') == 1 and re.fullmatch(r'[0-9a-f]{16}', iface)
s = s.replace('@@IFACE_SHA@@', iface)
for o, n in (("### 3.5 Pintle force law, seat and seal (v2.3 review of Mechanical's pintle v2)", "### 3.5 Pintle force law (v2.3 review of Mechanical's pintle v2), seat and seal (v2.4)"),
             ('## 10. Cold-flow and static-fire test plan', '## 10. Cold-flow and static-fire test plan (v2.3 plan with the v2.4 amendments at the end)')):
    assert s.count(o + '\n') == 1, o
    s = s.replace(o + '\n', n + '\n')
assert '@@' not in s, 'unresolved marker'
s = re.sub(r'\n{3,}', '\n\n', s).rstrip('\n') + '\n'
heads = [l for l in s.split('\n') if re.match(r'^#{2,3} ', l)]
open(out, 'w').write(s)
print('ok bytes', len(s.encode()), 'lines', s.count('\n'), 'sha16', hashlib.sha256(s.encode()).hexdigest()[:16])
print('\n'.join(heads))

#!/usr/bin/env python3
"""Case-by-case comparison of the v2.11 SIL record against the v2.10 record (Electronics, 2026-10-21; LEAD 2026-10-20 brief B7).

Reads results/sil_v2p10/<file> and results/sil_v2p11/<file> for every scenario file present in both records, matches cases by name
(with the RENAME map below for cases renamed in v2.11), and lists for every case: pass / expectation in both records, the first abort
cause, and every numeric leaf that changed by more than the tolerance (relative 1e-6 or absolute 1e-9). Summary scenarios (no case
list) are compared leaf by leaf. Writes results/sil_v2p11/compare_v2p10_v2p11.json and .txt. SIM evidence only.
"""
import gzip, hashlib, json, math, os, re, sys
from collections import OrderedDict

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
A = os.path.join(ROOT, 'results', 'sil_v2p10')
B = os.path.join(ROOT, 'results', 'sil_v2p11')
READ = OrderedDict()

def jl(p):
    b = open(p, 'rb').read()
    READ[os.path.relpath(p, ROOT)] = hashlib.sha256(b).hexdigest()[:16]
    return json.loads(re.sub(rb'\bnan\b', b'null', re.sub(rb'-?\binf\b', b'null', b)).decode())

# v2.11 renames (old -> new) with the reason
RENAME = OrderedDict([
    (('S6_aborts.json', 'case_over_temp_455K'), ('case_over_temp_430K', 'Part A: case-TC abort 448.15 -> 423.15 K (LEAD ruling 2026-10-20); the abort case sits 6.85 K above the new limit')),
    (('S6_aborts.json', 'case_445K_in_RUN_no_abort'), ('case_415K_in_RUN_no_abort', 'Part A: no-abort control 8.15 K below the new 423.15 K limit')),
    (('S10_relight_v2p8.json', 'case_TC_445K_in_RUN_no_abort_relight_refused'), ('case_TC_415K_in_RUN_no_abort_relight_refused', 'Part A: 415 K < 423.15 K abort, > 403.15 K relight limit')),
    (('S10_relight_v2p8.json', 'case_TC_455K_in_RUN_abort'), ('case_TC_430K_in_RUN_abort', 'Part A: 430 K > 423.15 K abort')),
    (('S12_bleed.json', 'relight_no_purge_fitted_unpurged_LEAD175'), ('relight_no_purge_flight_refused_UNPURGED_LEAD203_7', 'LEAD 203 (7): a flight RELIGHT without a purge is refused (UNPURGED 16); v2.10 accepted it (LEAD 175)')),
])
FILES = ['S1_mission.json', 'S2_steps.json', 'S3_deep.json', 'S4_hover.json', 'S5_mc.json', 'S6_aborts.json', 'S7_tvc.json',
         'S8_priming.json', 'S9_pc_transducer.json', 'S10_relight_v2p8.json', 'S12_bleed.json',
         'S13/S13_ignition_rule.json', 'S13/S13B_ext_bpc1_false.json', 'S13/S13B_ext_bpc1_true.json', 'S14/S14_v2p10.json',
         'S15/S15_start_mc.json', 'S16/S16_coast206.json', 'S17/S17_r2hold.json', 'probeF/S5_probeF.json',
         # new in v2.11 (no v2.10 counterpart; listed so the record shows them)
         'S10v211_cold_rule.json', 'S6R_in_window_overpressure.json', 'S6C_rc_cost.json', 'S17v2_r2v2_sweep.json']

def flat(o, p='', out=None):
    out = OrderedDict() if out is None else out
    if isinstance(o, dict):
        for k, v in o.items():
            flat(v, p + '/' + str(k), out)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            flat(v, '%s[%d]' % (p, i), out)
    else:
        out[p] = o
    return out

def changed(a, b):
    if isinstance(a, bool) or isinstance(b, bool) or not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        return a != b
    if a is None or b is None:
        return a != b
    return abs(a - b) > max(1e-9, 1e-6 * max(abs(a), abs(b)))

def case_status(c):
    for k in ('pass', 'ok'):
        if k in c:
            return c[k]
    return None

def main():
    res = OrderedDict([('script', 'calc/v2p11/sil_compare_v1.py'), ('a', 'results/sil_v2p10'), ('b', 'results/sil_v2p11'),
                       ('tag', 'SIM (comparison of two SIL records; no hardware evidence)'), ('files', OrderedDict())])
    txt = []
    for f in FILES:
        pa, pb = os.path.join(A, f), os.path.join(B, f)
        if not (os.path.exists(pa) and os.path.exists(pb)):
            res['files'][f] = OrderedDict([('status', 'missing in %s' % ('both' if not os.path.exists(pa) and not os.path.exists(pb) else ('v2.10' if not os.path.exists(pa) else 'v2.11')))])
            txt.append('%-34s %s' % (f, res['files'][f]['status']))
            continue
        ja, jb = jl(pa), jl(pb)
        ent = OrderedDict()
        if f.startswith('S13/S13B_'):
            # S13B cases carry no top-level 'case' key and v2.11 adds the stand location (216 (4)): match by (where, offset, lit) and
            # compare the class counts; the v2.10 'lead_pass' and the v2.11 per-location criteria (fail_v2p11) are both shown
            def key(c):
                return (c.get('where'), round(float(c.get('offset_bar')), 3), int(c.get('lit')))
            ca = OrderedDict((key(c), c) for c in ja['cases'])
            cb = OrderedDict((key(c), c) for c in jb['cases'])
            cnt_a = OrderedDict((x['class'], x['runs']) for x in ja.get('classes', []))
            cnt_b = OrderedDict((x['class'], x['runs']) for x in jb.get('classes', []))
            rows = []
            for k, c in ca.items():
                d = cb.get(k)
                if d is None:
                    rows.append(OrderedDict([('key', list(k)), ('status', 'REMOVED in v2.11')]))
                elif c.get('class') != d.get('class'):
                    rows.append(OrderedDict([('key', list(k)), ('class', [c.get('class'), d.get('class')]),
                                             ('pass', [c.get('lead_pass'), d.get('pass_v2p11')])]))
            new = [list(k) for k in cb if k not in ca]
            ent['runs'] = [ja.get('runs'), jb.get('runs')]
            ent['fail'] = [ja.get('lead_criteria_fail'), jb.get('fail_v2p11_criteria')]
            ent['fail_basis'] = 'v2.10: lead criteria of line 203 (5) as written (lead_criteria_fail); v2.11: per-location criteria of LEAD 216 (4)'
            ent['class_counts'] = OrderedDict((c, [cnt_a.get(c), cnt_b.get(c)]) for c in list(cnt_a) + [c for c in cnt_b if c not in cnt_a])
            ent['cases_matched'] = sum(1 for k in ca if k in cb)
            ent['cases_class_changed'] = rows
            ent['cases_new_v2p11'] = len(new)
            ent['cases_new_locations'] = sorted({k[0] for k in new})
            txt.append('%-34s runs %s->%s; fail %s->%s (basis changed, see json); matched %d, class changed %d, new %d (%s)' % (
                f, ja.get('runs'), jb.get('runs'), ent['fail'][0], ent['fail'][1], ent['cases_matched'], len(rows), len(new),
                ', '.join(ent['cases_new_locations'])))
            for c, (x, y) in ent['class_counts'].items():
                if x != y:
                    txt.append('    class %-28s %s -> %s' % (c, x, y))
            for r in rows:
                txt.append('    %-40s %s' % (r['key'], r.get('status') or ('%s -> %s' % tuple(r['class']))))
        elif isinstance(ja, dict) and isinstance(ja.get('cases'), list) and isinstance(jb.get('cases'), list) and ja['cases'] and 'case' in ja['cases'][0]:
            ca = OrderedDict((c['case'], c) for c in ja['cases'])
            cb = OrderedDict((c['case'], c) for c in jb['cases'])
            rows, n_same, n_chg = [], 0, 0
            renamed_new = {v[0] for (ff, _), v in RENAME.items() if ff == f}
            for name, c in ca.items():
                nb, why = name, None
                if (f, name) in RENAME:
                    nb, why = RENAME[(f, name)]
                if nb not in cb:
                    rows.append(OrderedDict([('case', name), ('status', 'REMOVED in v2.11')]))
                    continue
                d = cb[nb]
                fa_, fb_ = flat(c), flat(d)
                diffs = OrderedDict()
                for k in sorted(set(fa_) | set(fb_)):
                    if k in ('/case',):
                        continue
                    va, vb = fa_.get(k, '(absent)'), fb_.get(k, '(absent)')
                    if changed(va, vb):
                        diffs[k] = [va, vb]
                r = OrderedDict([('case', name if nb == name else '%s -> %s' % (name, nb)), ('pass_v2p10', case_status(c)),
                                 ('pass_v2p11', case_status(d))])
                for k in ('first_abort', 'cause_name', 'abort_name', 'final_state'):
                    if k in c or k in d:
                        r[k] = [c.get(k), d.get(k)]
                if why:
                    r['renamed'] = why
                r['n_changed_leaves'] = len(diffs)
                if diffs:
                    r['changed'] = OrderedDict(list(diffs.items())[:40])
                    n_chg += 1
                else:
                    n_same += 1
                rows.append(r)
            for name in cb:
                if name not in ca and name not in renamed_new:
                    rows.append(OrderedDict([('case', name), ('status', 'NEW in v2.11'), ('pass_v2p11', case_status(cb[name]))] +
                                            [(k, cb[name].get(k)) for k in ('first_abort', 'cause_name', 'abort_name', 'final_state') if k in cb[name]]))
            for k in ('passed', 'total', 'fail'):
                if k in ja or k in jb:
                    ent[k] = [ja.get(k), jb.get(k)]
            ent['cases_identical'] = n_same
            ent['cases_changed'] = n_chg
            ent['cases'] = rows
            txt.append('%-34s cases v2.10 %d / v2.11 %d: identical %d, changed %d, new %d, removed %d; %s' % (
                f, len(ca), len(cb), n_same, n_chg, sum(1 for r in rows if r.get('status') == 'NEW in v2.11'),
                sum(1 for r in rows if r.get('status') == 'REMOVED in v2.11'),
                ' '.join('%s %s->%s' % (k, v[0], v[1]) for k, v in ent.items() if k in ('passed', 'total', 'fail'))))
            for r in rows:
                if r.get('status') or r.get('n_changed_leaves'):
                    txt.append('    %-80s %s' % (r['case'][:80], r.get('status') or ('pass %s->%s, %d leaves changed' % (r['pass_v2p10'], r['pass_v2p11'], r['n_changed_leaves']))))
        else:
            fa_, fb_ = flat(ja), flat(jb)
            diffs = OrderedDict()
            for k in list(fa_.keys()) + [k for k in fb_ if k not in fa_]:
                va, vb = fa_.get(k, '(absent)'), fb_.get(k, '(absent)')
                if changed(va, vb):
                    diffs[k] = [va, vb]
            ent['leaves_v2p10'] = len(fa_)
            ent['leaves_v2p11'] = len(fb_)
            ent['n_changed_leaves'] = len(diffs)
            ent['changed'] = OrderedDict(list(diffs.items())[:400])
            if len(diffs) > 400:
                ent['changed_truncated'] = len(diffs) - 400
            txt.append('%-34s summary: %d / %d leaves, %d changed' % (f, len(fa_), len(fb_), len(diffs)))
        res['files'][f] = ent
    res['files_read_sha256_16'] = READ
    out = os.path.join(B, 'compare_v2p10_v2p11.json')
    with open(out, 'w') as fh:
        json.dump(res, fh, indent=1)
    with open(os.path.join(B, 'compare_v2p10_v2p11.txt'), 'w') as fh:
        fh.write('\n'.join(txt) + '\n')
    print('\n'.join(txt))

if __name__ == '__main__':
    main()

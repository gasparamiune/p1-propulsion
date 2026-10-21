#!/usr/bin/env python3
"""Generated-header provenance check for firmware v2.11 (Electronics, 2026-10-21; copy of calc/v2p10/gen_headers_regen_check.py with
the firmware label, the output name and this docstring changed; method unchanged).

Question: the firmware headers engine_params.h / plant_tables.h / gnc_tables.h / valve_map_table.h were generated from
combustion.json v2.3 and mech_params.h / mech_tables.h from mechanical.json v2. The hub now holds combustion.json v2.4b and
mechanical.json v2.2 (manifest status HISTORICAL). Would a regeneration from the CURRENT interfaces change any value?

Method (no edit of the firmware tree): copy firmware/{tools,src,sil} and the top-level results files into a scratch folder,
run the two generators there, diff each generated header against the firmware tree, and diff the combustion.json leaves the
generator reads (v2.3 as published vs the current file). Output: results/gen_headers_regen_check_v2p10.json.

Tags: every finding here is DERIVED from files; nothing is physical evidence.
"""
import argparse, datetime, difflib, hashlib, json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FW = os.path.join(ROOT, 'firmware')
RES = os.path.join(ROOT, 'results')
HEADERS = {'gen_mech_params.py': ['src/core/mech_params.h', 'sil/mech_tables.h'],
           'gen_tables.py': ['src/core/engine_params.h', 'sil/plant_tables.h', 'sil/gnc_tables.h', 'src/core/valve_map_table.h']}
READ_KEYS = ['operating_points', 'igniter', 'valves_and_actuators', 'gas_path', 'inputs', 'decisions']


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def flat(o, p, out):
    if isinstance(o, dict):
        for k, v in o.items():
            flat(v, p + '.' + k, out)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            flat(v, p + '[%d]' % i, out)
    else:
        out[p] = o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--engine-root', default='/home/claude/work/shared-fallback/engine')
    ap.add_argument('--python', default='/opt/engine-venv/bin/python', help='interpreter with CoolProp/numpy/scipy (gen_tables)')
    ap.add_argument('--scratch', default=None)
    ap.add_argument('--out', default=os.path.join(RES, 'gen_headers_regen_check_v2p11.json'))
    a = ap.parse_args()
    S = a.scratch or tempfile.mkdtemp(prefix='regen_check_')
    if os.path.exists(os.path.join(S, 'firmware')):
        shutil.rmtree(os.path.join(S, 'firmware'))
    os.makedirs(os.path.join(S, 'results'), exist_ok=True)
    for d in ('tools', 'src', 'sil'):
        shutil.copytree(os.path.join(FW, d), os.path.join(S, 'firmware', d))
    for f in os.listdir(RES):
        p = os.path.join(RES, f)
        if os.path.isfile(p) and f.endswith(('.json', '.csv', '.txt')):
            shutil.copy2(p, os.path.join(S, 'results', f))
    env = dict(os.environ, ENGINE_ROOT=a.engine_root)
    out = {'id': 'gen_headers_regen_check', 'version': 'v1', 'date': datetime.date.today().isoformat(), 'owner': 'electronics',
           'firmware': 'v2.11', 'scratch': S, 'generators': {}, 'tag': 'DERIVED (file comparison; no physical meaning)'}
    for gen, hdrs in HEADERS.items():
        r = subprocess.run([a.python, os.path.join('tools', gen), '--engine-root', a.engine_root], cwd=os.path.join(S, 'firmware'),
                           capture_output=True, text=True, env=env)
        g = {'returncode': r.returncode, 'stderr_tail': r.stderr.strip().splitlines()[-1:] if r.stderr.strip() else [],
             'stdout_tail': r.stdout.strip().splitlines()[-1:] if r.stdout.strip() else [], 'headers': {},
             'regenerated': r.returncode == 0,
             'meaning': ('headers regenerated from the current interfaces and compared' if r.returncode == 0 else
                         'GENERATOR FAILED: nothing was regenerated; the header comparison below is copy vs tree and carries no information')}
        for h in hdrs:
            a_lines = open(os.path.join(FW, h)).read().splitlines()
            b_lines = open(os.path.join(S, 'firmware', h)).read().splitlines()
            diff = [l for l in difflib.unified_diff(a_lines, b_lines, lineterm='', n=0) if l[:1] in '+-' and l[:3] not in ('+++', '---')]
            code = [l for l in diff if not l[1:].lstrip().startswith('//')]
            g['headers'][h] = {'sha256_16_tree': sha16(os.path.join(FW, h)), 'sha256_16_regen': sha16(os.path.join(S, 'firmware', h)),
                               'changed_lines': len(diff), 'changed_code_lines': len(code), 'diff': diff[:12]}
        out['generators'][gen] = g
    # combustion leaves read by gen_tables: v2.3 as published vs current
    c23 = os.path.join(a.engine_root, '02-combustion', 'data', 'v2', 'combustion_interface_v2p3_as_published.json')
    cnow = os.path.join(a.engine_root, 'interfaces', 'combustion.json')
    A, B = json.load(open(c23)), json.load(open(cnow))
    cmp_ = {}
    for k in READ_KEYS:
        fa, fb = {}, {}
        flat(A.get(k), k, fa)
        flat(B.get(k), k, fb)
        num = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)
        chg = [x for x in fa if x in fb and fa[x] != fb[x]]
        cmp_[k] = {'leaves_v23': len(fa), 'leaves_now': len(fb), 'changed': len(chg),
                   'changed_numeric': sorted(x for x in chg if num(fa[x]) or num(fb[x])),
                   'changed_text': len([x for x in chg if not (num(fa[x]) or num(fb[x]))]),
                   'removed': sum(1 for x in fa if x not in fb), 'added': sum(1 for x in fb if x not in fa),
                   'added_numeric': sorted(x for x in fb if x not in fa and num(fb[x]))}
    out['combustion_read_keys'] = {'v23': {'file': os.path.relpath(c23, a.engine_root), 'version': A.get('version'), 'sha256_16': sha16(c23)},
                                   'now': {'file': 'interfaces/combustion.json', 'version': B.get('version'), 'sha256_16': sha16(cnow)},
                                   'by_key': cmp_}
    json.dump(out, open(a.out, 'w'), indent=1)
    for gen, g in out['generators'].items():
        print(gen, 'rc', g['returncode'], 'regenerated' if g['regenerated'] else 'NOT REGENERATED', g['stderr_tail'], {h: (v['changed_lines'], v['changed_code_lines']) for h, v in g['headers'].items()})
    print('combustion read keys', {k: (v['changed'], v['removed'], v['added']) for k, v in cmp_.items()})
    print('numeric leaf changes', {k: v['changed_numeric'] for k, v in cmp_.items() if v['changed_numeric']},
          'numeric leaves added', {k: v['added_numeric'][:6] for k, v in cmp_.items() if v['added_numeric']})
    print('->', a.out, sha16(a.out))


if __name__ == '__main__':
    main()

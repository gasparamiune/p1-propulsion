#!/usr/bin/env python3
"""SIL configuration record (Electronics, 2026-10-13, v1; v1.1 same day: several unit-test logs per folder): binds a SIL result folder to the exact firmware configuration that produced it.

REV-GNC-1 RG-13 (required action): "Keep the FSW configuration in a versioned record that is hashed with each result." The ECU firmware
has no run-time or environment switches: every tunable is a compile-time constexpr in src/core/config.h, the SIL-only hooks are
compiled in by -DECU_SIL_TEST_HOOKS (sil build only; test_core and the Teensy build do not define it) and the what-if switches
(SIL_WHATIF_*) are honoured only under that define. This tool records, for one result folder:
  - sha256 of every firmware source, generated header, SIL file, Makefile and generator script, and one tree hash over them;
  - the build flags parsed from the Makefile (CXXFLAGS default, per-target -D flags);
  - the provenance hashes written into each GENERATED header and whether the interface file they name still has that hash today
    (stale-table check against <engine-root>);
  - sha256/16 and size of every result file in the folder, the test_core summary line and the FAIL lines of the run log.
Written after the run: the record states the source mtimes so a source edited after the run is visible (mtime later than the newest
result file). Output: <run>/MANIFEST_v1.json. It is a record, not a verification of the results.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
FW = os.path.normpath(os.path.join(HERE, '..'))


def sha_file(p, n=None):
    h = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    return h if n is None else h[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', required=True, help='SIL result folder, e.g. ../results/sil_v2p8_2')
    ap.add_argument('--version', required=True, help='firmware version string, e.g. v2.8.2')
    ap.add_argument('--engine-root', default=os.environ.get('ENGINE_ROOT', '/home/claude/work/shared-fallback/engine'))
    ap.add_argument('--overwrite', action='store_true', help='replace an existing MANIFEST_v1.json (refused by default)')
    a = ap.parse_args()
    run = os.path.abspath(a.run)
    er = a.engine_root
    # v1.1 guard (2026-10-13 06:11 operator error, see results/sil_v2p8_2/MANIFEST_v1_RECONSTRUCTION_NOTE.txt): a record is
    # written once, right after its run; an existing record is never replaced silently.
    if os.path.exists(os.path.join(run, 'MANIFEST_v1.json')) and not a.overwrite:
        raise SystemExit('refused: %s already holds MANIFEST_v1.json (a record belongs to the tree that produced the run; '
                         'use --overwrite only to re-record the same tree)' % run)

    # ---------------------------------------------------------------- sources
    src = []
    for d, exts in (('src/core', ('.h', '.cpp')), ('sil', ('.h', '.cpp', '.inc')), ('tools', ('.py',))):
        for fn in sorted(os.listdir(os.path.join(FW, d))):
            p = os.path.join(FW, d, fn)
            if os.path.isfile(p) and fn.endswith(exts):
                src.append(os.path.join(d, fn))
    src.append('Makefile')
    files = {}
    for r in src:
        p = os.path.join(FW, r)
        files[r] = {'sha256': sha_file(p), 'bytes': os.path.getsize(p), 'mtime_utc': os.path.getmtime(p)}
    tree = hashlib.sha256('\n'.join(f'{r}:{files[r]["sha256"]}' for r in sorted(files)).encode()).hexdigest()

    # ---------------------------------------------------------------- build flags
    mk = open(os.path.join(FW, 'Makefile'), encoding='utf-8').read()
    m = re.search(r'^CXXFLAGS\s*\?=\s*(.+)$', mk, re.M)
    targets = {}
    for t in ('build/sil', 'build/test_core'):
        mt = re.search(r'^' + re.escape(t) + r':.*\n((?:\t.*\n)+)', mk, re.M)
        if mt:
            targets[t] = {'recipe': [l.strip() for l in mt.group(1).splitlines()],
                          'defines': sorted(set(re.findall(r'-D([A-Za-z0-9_]+)', mt.group(1))))}
    cfg = open(os.path.join(FW, 'src', 'core', 'config.h'), encoding='utf-8').read()
    whatif = sorted(set(re.findall(r'#\s*if(?:def)?\s+.*?(SIL_WHATIF_[A-Z0-9_]+)', cfg)))
    env_switches = sorted(set(re.findall(r'getenv\s*\(\s*"([^"]+)"', ''.join(open(os.path.join(FW, r), encoding='utf-8', errors='replace').read()
                                                                        for r in src if r.startswith('src/core')))))

    # ---------------------------------------------------------------- generated-header provenance and stale check
    known = {'combustion.json': os.path.join(er, 'interfaces', 'combustion.json'), 'gnc.json': os.path.join(er, 'interfaces', 'gnc.json'),
             'mechanical.json': os.path.join(er, 'interfaces', 'mechanical.json'),
             'pintle_mini_servo_v1.json': os.path.join(FW, '..', 'results', 'pintle_mini_servo_v1.json')}
    try:
        C = json.load(open(known['combustion.json'], encoding='utf-8'))
        tm = C['operating_points']['throttle_map_csv']
        known['throttle_map_csv'] = tm if os.path.exists(tm) else os.path.join(er, tm.split('/engine/', 1)[1])
    except (OSError, KeyError, IndexError):
        pass
    gen = {}
    for r in src:
        head = ''.join(open(os.path.join(FW, r), encoding='utf-8', errors='replace').readlines()[:6])
        if 'GENERATED' not in head:
            continue
        refs = []
        # v1.1: the version named in the reference is captured. A reference that names an OLDER version than the interface file
        # now carries (e.g. gnc_tables.h: "gnc.json v1 sha ... (mid-pivot terms, not in v2/v3)") is a deliberate historical source,
        # reported as HISTORICAL, not STALE; a reference without a version, or naming the current version, with another hash is STALE.
        for name, ver, h in re.findall(r'([A-Za-z0-9_.]+(?:\.json|\.csv)?)\s+(?:(v[0-9.]+)\s+)?\(?(?:Electronics,\s+)?sha(?:256)?(?:/16)?\s+([0-9a-f]{16})', head):
            path = known.get(name)
            now = sha_file(path, 16) if path and os.path.exists(path) else None
            ver_now = None
            if now and path.endswith('.json'):
                try:
                    ver_now = json.load(open(path, encoding='utf-8')).get('version')
                except (OSError, ValueError, AttributeError):
                    ver_now = None
            if now == h:
                st = 'current'
            elif not now:
                st = 'not checked (source not mapped)'
            elif ver and ver_now and str(ver_now).split()[0] != ver:
                st = 'HISTORICAL (names %s; the file is now %s)' % (ver, ver_now)
            else:
                st = 'STALE'
            refs.append({'source': name, 'version_named': ver or None, 'sha_at_generation': h, 'sha_now': now,
                         'version_now': ver_now, 'status': st})
        if 'throttle_map_csv' in head:
            mt = re.search(r'throttle_map_csv,\s*sha\s+([0-9a-f]{16})', head)
            if mt and 'throttle_map_csv' in known:
                now = sha_file(known['throttle_map_csv'], 16)
                refs.append({'source': 'throttle_map_csv', 'sha_at_generation': mt.group(1), 'sha_now': now,
                             'status': 'current' if now == mt.group(1) else 'STALE'})
        gen[r] = {'generator_line': head.splitlines()[0][:200], 'refs': refs}

    # ---------------------------------------------------------------- results
    res = {}
    newest = 0.0
    for fn in sorted(os.listdir(run)):
        p = os.path.join(run, fn)
        if os.path.isfile(p) and not fn.startswith('MANIFEST'):
            res[fn] = {'sha256_16': sha_file(p, 16), 'bytes': os.path.getsize(p)}
            newest = max(newest, os.path.getmtime(p))
    edited_after = sorted(r for r in files if files[r]['mtime_utc'] > newest)
    log = os.path.join(run, 'sil_run_log.txt')
    fails = [l.strip()[:300] for l in open(log, encoding='utf-8', errors='replace') if l.rstrip().endswith('FAIL')] if os.path.exists(log) else None
    # v1.1 (2026-10-13, v2.8.3): a run folder can hold several unit-test logs (failed runs kept as evidence, *_runN.txt). The
    # final one is the log without a _runN suffix; every log and its summary line is recorded.
    tc = None
    tc_all = {}
    for fn in res:
        if fn.startswith('test_core'):
            lines = [l.strip() for l in open(os.path.join(run, fn), encoding='utf-8', errors='replace') if re.search(r'\d+ passed', l)]
            tc_all[fn] = lines[-1] if lines else None
    finals = [fn for fn in tc_all if not re.search(r'_run\d+\.', fn)]
    if finals:
        tc = {'file': finals[0], 'summary': tc_all[finals[0]], 'all_logs': tc_all}
    elif tc_all:
        last = sorted(tc_all)[-1]
        tc = {'file': last, 'summary': tc_all[last], 'all_logs': tc_all}
    out = {'id': 'sil_manifest', 'version': 'v1', 'date': '2026-10-13', 'tool': 'firmware/tools/sil_manifest_v1.py',
           'firmware_version': a.version, 'run_folder': os.path.relpath(run, os.path.join(FW, '..')),
           'tree_sha256': tree, 'n_files': len(files), 'files': files,
           'build': {'CXXFLAGS_default': m.group(1).strip() if m else None, 'targets': targets,
                     'whatif_switches_in_config_h': whatif, 'getenv_in_core': env_switches,
                     'note': 'all tunables are constexpr in config.h; SIL-only hooks need -DECU_SIL_TEST_HOOKS (sil target only)'},
           'generated_headers': gen,
           'results': res, 'newest_result_mtime_utc': newest, 'sources_edited_after_newest_result': edited_after,
           'test_core': tc, 'sil_fail_lines': fails}
    body = json.dumps(out, sort_keys=True, separators=(',', ':'))
    out['record_sha256_16'] = hashlib.sha256(body.encode()).hexdigest()[:16]
    with open(os.path.join(run, 'MANIFEST_v1.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1)
    stale = [(r, x['source']) for r, g in gen.items() for x in g['refs'] if x['status'] == 'STALE']
    hist = [(r, x['source'], x.get('version_named')) for r, g in gen.items() for x in g['refs'] if x['status'].startswith('HISTORICAL')]
    print(f"manifest {a.version}: tree {tree[:16]}, {len(files)} source files, {len(res)} result files, test_core: {tc['summary'] if tc else None}; "
          f"FAIL lines {len(fails) if fails is not None else 'n/a'}; generated-header refs {sum(len(g['refs']) for g in gen.values())}, STALE {stale}, HISTORICAL {hist}; "
          f"sources edited after the newest result: {edited_after}; getenv in core: {env_switches}; record {out['record_sha256_16']}")


if __name__ == '__main__':
    main()

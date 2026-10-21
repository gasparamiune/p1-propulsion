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

v1.2 (2026-10-13, v2.10, REV-ELEC-1 RE-21 "record the binary hash for each scenario in the manifest"): optional --bin LABEL=PATH
(sha256 of each executable used), --rebuild LABEL=PATH (a separate rebuild of the CURRENT tree; equality with the run binary shows the
recorded sources produce the binary that ran) and --scenarios FILE (JSON list of {"id", "binary", "command", "outputs": [globs]}), which
binds every result file to the scenario and binary hash that produced it; unmapped files are listed. Result files are now walked
recursively (sub-folders such as S13/ were skipped by v1.1). Sources edited after a binary was built are listed per binary. Without the
new options the v1.1 record is written unchanged except for the recursive walk.

v1.3 (2026-10-13, v2.10 handback): the FAIL-line scan missed failures. v1.0-v1.2 kept only run-log lines ENDING in "FAIL"; the S12
bleed table prints its status in a column ("S12 <case> FAIL abort ..."), so the v2.10 record listed 7 FAIL lines for 11 failed cases.
v1.3 scans every .txt log in the run folder (sub-folders included, unit-test logs excluded) for scenario lines (starting "S<n>") with a
stand-alone FAIL status token, and skips summary counts ("<n> FAIL"). 'sil_fail_lines' keeps the v1.2 rule for continuity;
'sil_fail_lines_v13' holds the new list as {log: [lines]}; 'sil_fail_count_v13' its total.

v1.4 (2026-10-21, v2.11 record, REV-ELEC-2 R2-08): the build-flag record also parses build/test_core_nohooks, and the build note
no longer says the hooks are defined for the sil target only (build/sil, build/sil_bpc1 and build/test_core define ECU_SIL_TEST_HOOKS;
build/test_core_nohooks and the Teensy build do not). The unit-test summary reads the .txt logs only (v2.11 also writes test_core*.json, which v1.3 picked as
the 'final' log with no summary line) and lists every final log. 'record_utc' is the time the record was written ('date' stays the
tool's own date). Record content otherwise unchanged. This tool is not compiled into any binary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time

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
    ap.add_argument('--bin', action='append', default=[], help='v1.2: LABEL=PATH of an executable used by the run (repeatable)')
    ap.add_argument('--rebuild', action='append', default=[], help='v1.2: LABEL=PATH of a rebuild of the current tree (compared with --bin LABEL)')
    ap.add_argument('--scenarios', default=None, help='v1.2: JSON list of {id, binary, command, outputs[globs relative to --run]}')
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
    for t in ('build/sil', 'build/sil_bpc1', 'build/test_core', 'build/test_core_nohooks'):   # v1.4: + test_core_nohooks
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
    oldest = None
    for dp, dns, fns in os.walk(run):   # v1.2: recursive
        dns.sort()
        for fn in sorted(fns):
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, run)
            if os.path.isfile(p) and not fn.startswith('MANIFEST'):
                res[rel] = {'sha256_16': sha_file(p, 16), 'bytes': os.path.getsize(p)}
                newest = max(newest, os.path.getmtime(p))
                oldest = os.path.getmtime(p) if oldest is None else min(oldest, os.path.getmtime(p))
    edited_after = sorted(r for r in files if files[r]['mtime_utc'] > newest)

    # ---------------------------------------------------------------- v1.2 binaries, rebuild check, scenario -> binary map (RE-21)
    bins = {}
    for spec in a.bin:
        lab, _, path = spec.partition('=')
        pa = os.path.abspath(os.path.join(FW, path)) if not os.path.isabs(path) else path
        mt_b = os.path.getmtime(pa)
        bins[lab] = {'path': os.path.relpath(pa, FW), 'sha256': sha_file(pa), 'sha256_16': sha_file(pa, 16), 'bytes': os.path.getsize(pa),
                     'mtime_utc': mt_b, 'built_before_oldest_result': (oldest is None or mt_b <= oldest),
                     'sources_edited_after_build': sorted(r for r in files if files[r]['mtime_utc'] > mt_b)}
    for spec in a.rebuild:
        lab, _, path = spec.partition('=')
        pa = os.path.abspath(os.path.join(FW, path)) if not os.path.isabs(path) else path
        if lab in bins:
            h = sha_file(pa, 16)
            bins[lab]['rebuild_of_current_tree'] = {'path': os.path.relpath(pa, FW), 'sha256_16': h, 'identical': h == bins[lab]['sha256_16']}
    scen = None
    if a.scenarios:
        import fnmatch
        S = json.load(open(a.scenarios, encoding='utf-8'))
        owner = {}
        scen = []
        for s in S:
            hit = sorted(r for r in res if any(fnmatch.fnmatch(r, g) for g in s['outputs']))
            for r in hit:
                owner.setdefault(r, []).append(s['id'])
            b = bins.get(s.get('binary'))
            scen.append({'id': s['id'], 'binary': s.get('binary'), 'binary_sha256_16': b['sha256_16'] if b else None,
                         'command': s.get('command'), 'outputs': s['outputs'], 'n_files': len(hit)})
        for r in res:
            res[r]['scenario'] = owner.get(r)
            res[r]['binary_sha256_16'] = sorted({bins[x['binary']]['sha256_16'] for x in scen if x['id'] in (owner.get(r) or [])
                                                 and x['binary'] in bins}) or None
        scen_unmapped = sorted(r for r in res if not owner.get(r))
        scen_multi = sorted(r for r in res if len(owner.get(r) or []) > 1)
    else:
        scen_unmapped = scen_multi = None
    log = os.path.join(run, 'sil_run_log.txt')
    fails = [l.strip()[:300] for l in open(log, encoding='utf-8', errors='replace') if l.rstrip().endswith('FAIL')] if os.path.exists(log) else None
    # v1.3: status-token rule over every scenario log (see the docstring)
    def _isfail(line):
        t = line.strip()
        return bool(re.match(r'S\d+', t)) and bool(re.search(r'\sFAIL(\s|$)', t)) and not re.search(r'\d+\s+FAIL\b', t)
    fails13 = {}
    for fn in sorted(res):
        if not fn.endswith('.txt') or os.path.basename(fn).startswith('test_core'):
            continue
        hit = [l.strip()[:300] for l in open(os.path.join(run, fn), encoding='utf-8', errors='replace') if _isfail(l)]
        if hit:
            fails13[fn] = hit
    # v1.1 (2026-10-13, v2.8.3): a run folder can hold several unit-test logs (failed runs kept as evidence, *_runN.txt). The
    # final one is the log without a _runN suffix; every log and its summary line is recorded.
    tc = None
    tc_all = {}
    for fn in res:
        if os.path.basename(fn).startswith('test_core') and fn.endswith('.txt'):   # v1.4: logs only (v2.11 also writes test_core*.json)
            lines = [l.strip() for l in open(os.path.join(run, fn), encoding='utf-8', errors='replace') if re.search(r'\d+ passed', l)]
            tc_all[fn] = lines[-1] if lines else None
    finals = [fn for fn in tc_all if not re.search(r'_run\d+\.', fn)]
    if finals:   # v1.4: every final log is listed (v2.11: test_core_log.txt and test_core_nohooks_log.txt)
        tc = {'file': finals[0], 'summary': tc_all[finals[0]], 'all_logs': tc_all, 'final_logs': {fn: tc_all[fn] for fn in finals}}
    elif tc_all:
        last = sorted(tc_all)[-1]
        tc = {'file': last, 'summary': tc_all[last], 'all_logs': tc_all}
    out = {'id': 'sil_manifest', 'version': 'v1', 'date': '2026-10-13', 'tool': 'firmware/tools/sil_manifest_v1.py',
           'record_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),   # v1.4
           'firmware_version': a.version, 'run_folder': os.path.relpath(run, os.path.join(FW, '..')),
           'tree_sha256': tree, 'n_files': len(files), 'files': files,
           'build': {'CXXFLAGS_default': m.group(1).strip() if m else None, 'targets': targets,
                     'whatif_switches_in_config_h': whatif, 'getenv_in_core': env_switches,
                     'note': 'all tunables are constexpr in config.h; the SIL-only hooks need -DECU_SIL_TEST_HOOKS (v1.4: defined for '
                             'build/sil, build/sil_bpc1 and build/test_core; not for build/test_core_nohooks or the Teensy build; see targets)'},
           'generated_headers': gen,
           'results': res, 'newest_result_mtime_utc': newest, 'sources_edited_after_newest_result': edited_after,
           'test_core': tc, 'sil_fail_lines': fails}
    out['sil_fail_lines_v13'] = fails13                                   # v1.3
    out['sil_fail_count_v13'] = sum(len(v) for v in fails13.values())
    if bins or scen is not None:   # v1.2
        out['tool_revision'] = 'v1.4'
        out['binaries'] = bins
        out['scenarios'] = scen
        out['results_unmapped'] = scen_unmapped
        out['results_in_several_scenarios'] = scen_multi
        if a.scenarios:
            out['scenarios_file'] = {'path': os.path.relpath(os.path.abspath(a.scenarios), os.path.join(FW, '..')),
                                     'sha256_16': sha_file(a.scenarios, 16)}
    body = json.dumps(out, sort_keys=True, separators=(',', ':'))
    out['record_sha256_16'] = hashlib.sha256(body.encode()).hexdigest()[:16]
    with open(os.path.join(run, 'MANIFEST_v1.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1)
    stale = [(r, x['source']) for r, g in gen.items() for x in g['refs'] if x['status'] == 'STALE']
    hist = [(r, x['source'], x.get('version_named')) for r, g in gen.items() for x in g['refs'] if x['status'].startswith('HISTORICAL')]
    print(f"manifest {a.version}: tree {tree[:16]}, {len(files)} source files, {len(res)} result files, test_core: {tc['summary'] if tc else None}; "
          f"FAIL lines {len(fails) if fails is not None else 'n/a'} (v1.3 rule: {sum(len(v) for v in fails13.values())}); generated-header refs {sum(len(g['refs']) for g in gen.values())}, STALE {stale}, HISTORICAL {hist}; "
          f"sources edited after the newest result: {edited_after}; getenv in core: {env_switches}; record {out['record_sha256_16']}")
    for lab, b in bins.items():
        rb = b.get('rebuild_of_current_tree')
        print(f"  binary {lab} {b['sha256_16']} built before oldest result {b['built_before_oldest_result']}; sources edited after build "
              f"{b['sources_edited_after_build']}; rebuild of current tree {rb['sha256_16'] + (' identical' if rb['identical'] else ' DIFFERS') if rb else 'not given'}")
    if scen is not None:
        for s in scen:
            print(f"  scenario {s['id']:<14} {s['binary'] or '-':<10} {s['binary_sha256_16'] or '-':<16} files {s['n_files']}")
        print(f"  unmapped result files {len(scen_unmapped)}: {scen_unmapped[:12]}; in several scenarios {len(scen_multi)}")


if __name__ == '__main__':
    main()

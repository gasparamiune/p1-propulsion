#!/usr/bin/env python3
# v2.13 staging file list (no cd): make <dir> <out> <utc> writes SHA256SUMS lines with paths relative to <dir> (the list file itself
# excluded); check <dir> <list> recomputes every listed file and reports mismatches, missing and unlisted files.
import hashlib, os, sys
def h(p):
    s = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): s.update(b)
    return s.hexdigest()
def files(d, skip):
    out = []
    for r, _, fs in os.walk(d):
        for f in fs:
            p = os.path.join(r, f); rel = os.path.relpath(p, d)
            if rel != skip: out.append(rel)
    return sorted(out)
mode, d = sys.argv[1], sys.argv[2]
if mode == 'make':
    out, utc = sys.argv[3], sys.argv[4]
    name = 'SHA256SUMS-v2.13.txt'
    fl = files(d, name)
    hdr = ('# 06-electronics v2.13 STAGED file list, %s (sha256; paths relative to 06-electronics/staging_v2.13/). Staged for the lead to '
           'verify and promote; staging_v2.12/ and interfaces/*.json are unchanged. firmware/ holds only the files changed or added against '
           'v2.11 + the v2.12 overlay (build = staging_v2.11/firmware, then staging_v2.12/firmware over it, then staging_v2.13/firmware over '
           'that; every other firmware file is byte-identical to that base). No report .md: the report text is the Electronics v2.13 handback.\n'
           '# This list identifies bytes only; it is not a verification of any claim.\n') % utc
    with open(out, 'w') as f:
        f.write(hdr)
        for rel in fl: f.write('%s  %s\n' % (h(os.path.join(d, rel)), rel))
    print('listed', len(fl), 'files ->', out)
else:
    lst = sys.argv[3]; bad = 0; seen = set()
    for line in open(lst):
        if line.startswith('#') or not line.strip(): continue
        s, rel = line.rstrip('\n').split('  ', 1); seen.add(rel)
        p = os.path.join(d, rel)
        if not os.path.isfile(p): print('MISSING', rel); bad += 1
        elif h(p) != s: print('MISMATCH', rel); bad += 1
    extra = [r for r in files(d, os.path.basename(lst)) if r not in seen]
    for r in extra: print('UNLISTED', r)
    print('checked', len(seen), 'files; bad', bad, '; unlisted', len(extra))
    sys.exit(1 if bad or extra else 0)

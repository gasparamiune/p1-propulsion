#!/usr/bin/env python3
# REV-ELEC-3: compare the reviewer's re-run outputs (RAM folder) with the staged v2.11 SIL record, file by file (sha256/16);
# a file that differs is compared again with lines naming wall-clock time removed. Run: python3 -I repro_compare_v2p11.py <out.tsv>
import hashlib, os, re, sys
REC = '/home/claude/work/shared-fallback/engine/06-electronics/staging_v2.11/results/sil_v2p11'
RUN = '/dev/shm/rev_elec3/run'
pairs = [('tc', ''), ('all', ''), ('r2v2', ''), ('s6r', ''), ('s6r_b', ''), ('s6c', ''),
         ('rest/S13', 'S13'), ('rest/S14', 'S14'), ('rest/S15', 'S15'), ('rest/S16', 'S16'), ('rest/S17', 'S17'), ('rest/probeF', 'probeF')]
TIME = re.compile(r'(wall|real\s|user\s|sys\s|elapsed|_time|time_s|seconds|\bs wall)', re.I)
def h16(b): return hashlib.sha256(b).hexdigest()[:16]
def strip(b): return b'\n'.join(l for l in b.split(b'\n') if not TIME.search(l.decode('utf-8', 'replace')))
rows = []; n_same = n_masked = n_diff = n_norec = 0
for sub, recsub in pairs:
    d = os.path.join(RUN, sub)
    for f in sorted(os.listdir(d)):
        p = os.path.join(d, f); r = os.path.join(REC, recsub, f)
        if not os.path.isfile(p): continue
        mine = open(p, 'rb').read()
        if not os.path.exists(r):
            rows.append((sub, f, h16(mine), '-', 'NOT_IN_RECORD')); n_norec += 1; continue
        rec = open(r, 'rb').read()
        if mine == rec: st = 'IDENTICAL'; n_same += 1
        elif f.endswith('.gz'):
            import gzip
            st = 'IDENTICAL_DECOMPRESSED' if gzip.decompress(mine) == gzip.decompress(rec) else 'DIFF'
            n_same += st != 'DIFF'; n_diff += st == 'DIFF'
        elif strip(mine) == strip(rec): st = 'IDENTICAL_EXCEPT_TIME_LINES'; n_masked += 1
        else: st = 'DIFF'; n_diff += 1
        rows.append((sub, f, h16(mine), h16(rec), st))
with open(sys.argv[1], 'w') as o:
    o.write('run_folder\tfile\tsha256_16_rerun\tsha256_16_record\tstatus\n')
    for r in rows: o.write('\t'.join(r) + '\n')
    o.write('# identical %d, identical except wall-time lines %d, differ %d, not in record (traces the record does not keep) %d\n' % (n_same, n_masked, n_diff, n_norec))
print(open(sys.argv[1]).read())

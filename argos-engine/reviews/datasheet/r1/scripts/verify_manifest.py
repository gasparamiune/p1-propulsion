#!/opt/engine-venv/bin/python -I
"""REV-DS-1: verify a sha256sum-format manifest (relative paths) without cd.

usage: verify_manifest.py <manifest> [<base_dir>]
Prints counts of OK / FAIL / MISSING and the failing rows.
Read-only on the hub.
"""
import hashlib
import os
import sys


def sha256_file(p, bs=1 << 20):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while True:
            b = f.read(bs)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def main():
    man = sys.argv[1]
    base = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(man))
    ok = fail = miss = 0
    bad = []
    rows = 0
    with open(man, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line.strip():
                continue
            rows += 1
            parts = line.split(None, 1)
            if len(parts) != 2:
                bad.append(('MALFORMED', line))
                fail += 1
                continue
            h, rel = parts
            rel = rel.lstrip('*').strip()
            p = os.path.join(base, rel)
            if not os.path.isfile(p):
                miss += 1
                bad.append(('MISSING', rel))
                continue
            a = sha256_file(p)
            if a == h:
                ok += 1
            else:
                fail += 1
                bad.append(('FAIL', rel, h[:16], a[:16]))
    print(f'manifest={man} rows={rows} ok={ok} fail={fail} missing={miss}')
    for b in bad:
        print('  ', *b)
    return 0 if (fail == 0 and miss == 0) else 1


if __name__ == '__main__':
    sys.exit(main())

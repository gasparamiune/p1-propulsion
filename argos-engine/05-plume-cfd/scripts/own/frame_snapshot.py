"""Analysis snapshot of an own-solver run at an earlier time (Combustion / 05-plume-cfd v2, 2026-10-12).

Frames (frame_NNNN.npz) carry the cell fields only (t, frac, rho, p, T, Y, M, u, v). This writes a final.npz-like file
for post_plume.load_own / validate_plume.analyse: grid arrays and meta from RUN/final.npz, fields from the frame, and
meta t / thrust_exit / mdot_exit / mdot_throat interpolated from RUN/history.csv at the frame time. No conserved state U
is written, so a snapshot cannot be used to restart the solver. gamma and mut are not carried (not used by the
analysis).
Purpose: compare runs at the SAME physical time (validation v2 used the coarse run at 4 ms against 3 ms runs).
usage: python frame_snapshot.py RUN_DIR FRAME_INDEX OUT.npz
"""
from __future__ import annotations
import csv, json, os, sys
import numpy as np


def main(run, k, out):
    f = np.load(os.path.join(run, 'final.npz'), allow_pickle=False)
    fr = np.load(os.path.join(run, f'frame_{k:04d}.npz'), allow_pickle=False)
    meta = json.loads(str(f['meta']))
    t = float(fr['t'])
    rows = list(csv.DictReader(open(os.path.join(run, 'history.csv'))))
    th = np.array([float(r['t_s']) for r in rows])
    def at(col):
        return float(np.interp(t, th, np.array([float(r[col]) for r in rows])))
    meta.update(t=t, thrust_exit=at('thrust_exit_N'), mdot_exit=at('mdot_exit_kgs'), mdot_throat=at('mdot_throat_kgs'),
                snapshot=dict(source_run=os.path.abspath(run), frame=k, t_final_of_run=json.loads(str(f['meta']))['t'],
                              note='fields from the frame, integrals interpolated from history.csv; no U (no restart)'))
    out_fields = {key: fr[key] for key in ('rho', 'p', 'T', 'Y', 'M', 'u', 'v')}
    np.savez_compressed(out, xc=f['xc'], rc=f['rc'], X=f['X'], R=f['R'], region=f['region'],
                        meta=json.dumps(meta, default=float), **out_fields)
    print(out, 't_ms', round(t * 1e3, 4), 'thrust', round(meta['thrust_exit'], 3), 'mdot_throat', round(meta['mdot_throat'], 6))


if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]), sys.argv[3])

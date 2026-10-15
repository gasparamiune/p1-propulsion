"""Write the plume2s structured grid as an ANSYS Fluent 2D ASCII mesh (.msh), axis along x, y = r >= 0, metres.
(Combustion / 05-plume-cfd / fluent-crosscheck v1)

Fluent face convention used (as in OpenFOAM's foamMeshToFluent, which reverses OpenFOAM boundary faces "because in
Fluent all boundary faces point inwards"): for a 2D face n0->n1 the right-hand normal (n1-n0) x z points INTO the
first cell c0 (the 'right' cell); c1 is the other ('left') cell, 0 on boundaries.  The script verifies this
geometrically for every face before writing.  If Fluent nevertheless reports left-handed faces, the TUI command
/mesh/repair-improve/repair-face-handedness repairs them.

usage: python write_fluent_mesh.py LEVEL OUT.msh       (LEVEL 0.5 = coarse 20k cells, 1 = medium 80k cells)
"""
from __future__ import annotations
import os, sys, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plume2s as P


def build(level):
    J, pts, Rbody = P.load_geometry()
    g = P.Grid(pts, Rbody, level=level)
    NI, NJ, Nn, jc, js = g.NI, g.NJ, g.Nn, g.jc, g.js
    fluid = g.region != 3
    # cell numbering (1-based)
    cid = np.zeros((NI, NJ), int)
    cid[fluid] = np.arange(1, fluid.sum() + 1)
    # node usage
    used = np.zeros((NI + 1, NJ + 1), bool)
    for i in range(NI):
        for j in range(NJ):
            if fluid[i, j]:
                used[i:i + 2, j:j + 2] = True
    nid = np.zeros((NI + 1, NJ + 1), int)
    nid[used] = np.arange(1, used.sum() + 1)
    nodes = np.stack([g.X[used], g.R[used]], axis=1)
    zones = {}   # name -> list of (n0, n1, c0, c1)

    def add(z, a, b, c0, c1):
        zones.setdefault(z, []).append((a, b, c0, c1))

    def cell(i, j):
        return cid[i, j] if (0 <= i < NI and 0 <= j < NJ and fluid[i, j]) else 0
    # i-faces: edge (f,j)->(f,j+1) (upward); its right side is +x -> cell (f,j)
    for f in range(NI + 1):
        for j in range(NJ):
            cr = cell(f, j); cl = cell(f - 1, j)
            n0, n1 = nid[f, j], nid[f, j + 1]
            if cr and cl:
                add('interior', n0, n1, cr, cl)
            elif cr or cl:
                if not cr:                         # fluid on the left -> reverse edge so it is c0
                    n0, n1, cr = n1, n0, cl
                if f == 0:
                    z = 'inlet' if j < jc else 'coflow'
                elif f == NI:
                    z = 'outlet'
                else:
                    z = 'base'
                add(z, n0, n1, cr, 0)
    # j-faces: edge (i,f)->(i+1,f) (+x); its right side is -r -> cell (i,f-1)
    for i in range(NI):
        for f in range(NJ + 1):
            cr = cell(i, f - 1); cl = cell(i, f)
            n0, n1 = nid[i, f], nid[i + 1, f]
            if cr and cl:
                add('interior', n0, n1, cr, cl)
            elif cr or cl:
                if not cr:
                    n0, n1, cr = n1, n0, cl
                if f == 0:
                    z = 'axis'
                elif f == NJ:
                    z = 'farfield'
                elif f == jc and i < Nn:
                    z = 'nozzle_wall'
                elif f == js and i < Nn:
                    z = 'body_wall'
                else:
                    raise RuntimeError(f'unclassified j-face {i},{f}')
                add(z, n0, n1, cr, 0)
    return g, nodes, cid, zones


def verify(g, nodes, cid, zones):
    """Right-hand normal (n1-n0) x z must point into c0 and away from c1."""
    fluid = g.region != 3
    cen = np.zeros((cid.max() + 1, 2))
    cen[cid[fluid]] = np.stack([g.xc[fluid], g.rc[fluid]], axis=1)
    bad = 0; nf = 0; count = np.zeros(cid.max() + 1, int)
    for z, F in zones.items():
        for n0, n1, c0, c1 in F:
            p0 = nodes[n0 - 1]; p1 = nodes[n1 - 1]
            t = p1 - p0; n = np.array([t[1], -t[0]]); m = 0.5 * (p0 + p1)
            if np.dot(n, cen[c0] - m) <= 0:
                bad += 1
            if c1 and np.dot(n, cen[c1] - m) >= 0:
                bad += 1
            count[c0] += 1
            if c1:
                count[c1] += 1
            nf += 1
    return dict(faces=nf, bad_orientation=bad, cells_with_not_4_faces=int((count[1:] != 4).sum()))


ZONE_TYPES = {  # name: (bc-type code, fluent zone type)
    'interior': (2, 'interior'), 'inlet': (4, 'pressure-inlet'), 'coflow': (10, 'velocity-inlet'),
    'outlet': (5, 'pressure-outlet'), 'farfield': (5, 'pressure-outlet'), 'axis': (37, 'axis'),
    'nozzle_wall': (3, 'wall'), 'base': (3, 'wall'), 'body_wall': (3, 'wall'),
}


def write(fn, g, nodes, cid, zones, level):
    nn = len(nodes); nc = int(cid.max())
    order = ['interior', 'inlet', 'coflow', 'outlet', 'farfield', 'axis', 'nozzle_wall', 'base', 'body_wall']
    nf = sum(len(zones[z]) for z in order if z in zones)
    with open(fn, 'w') as f:
        f.write(f'(0 "ARGOS-H1 combustion: N2O/ABS hybrid nozzle + plume, 2D axisymmetric, axis = x, units m, '
                f'plume2s grid level {level}, {nc} quad cells")\n')
        f.write('(2 2)\n')
        f.write(f'(10 (0 1 {nn:x} 0 2))\n')
        f.write(f'(12 (0 1 {nc:x} 0 0))\n')
        f.write(f'(13 (0 1 {nf:x} 0 0))\n')
        f.write(f'(10 (1 1 {nn:x} 1 2)(\n')
        for x, y in nodes:
            f.write(f'{x:.10e} {y:.10e}\n')
        f.write('))\n')
        f.write(f'(12 (2 1 {nc:x} 1 3))\n')
        first = 1; zid = 3; ids = {}
        for z in order:
            if z not in zones:
                continue
            F = zones[z]; last = first + len(F) - 1
            bc = ZONE_TYPES[z][0]
            f.write(f'(13 ({zid:x} {first:x} {last:x} {bc:x} 2)(\n')
            for n0, n1, c0, c1 in F:
                f.write(f'{n0:x} {n1:x} {c0:x} {c1:x}\n')
            f.write('))\n')
            ids[z] = zid; first = last + 1; zid += 1
        f.write('(45 (2 fluid fluid)())\n')
        for z, i in ids.items():
            f.write(f'(45 ({i} {ZONE_TYPES[z][1]} {z})())\n')
    return dict(nodes=nn, cells=nc, faces=nf, zone_ids=ids, zone_sizes={z: len(zones[z]) for z in ids})


if __name__ == '__main__':
    level = float(sys.argv[1]); out = sys.argv[2]
    g, nodes, cid, zones = build(level)
    v = verify(g, nodes, cid, zones)
    print(json.dumps(v))
    if v['bad_orientation'] or v['cells_with_not_4_faces']:
        sys.exit('verification failed')
    info = write(out, g, nodes, cid, zones, level)
    print(json.dumps(info))

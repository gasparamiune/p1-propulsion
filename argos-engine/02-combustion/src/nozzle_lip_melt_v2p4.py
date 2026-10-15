"""H19 lip-bore melt time against the lip starting temperature: J1 against J1b (Combustion v2.4, 2026-10-13).

Coordinator question: with J1 the 316L lip bore runs at 342 C in burn (Mechanical j1_check_v1, B1 p99 hi bound; 264 C on A1);
J1b-0.5 (0.5 mm mica behind the carbon-phenolic) brings it to 223 C but puts the mica face at 902 C against its 900 C class.
Is 342 C acceptable for the H19 seal-failure case, i.e. how much shorter is the lip-bore melt time with 5-20 % deposition?

Leak and heat flux as nozzle_joint_v2p4.json (read): leak 0.83-1.10 % of the 100 % flow through the 4 insert vent grooves,
enthalpy flow 8.5-11.4 kW, deposited fraction 5 % or 20 % (ASSUMED bracket) on the 6 mm x 30.5 mm lip bore (575 mm2).
Three readings of the time to melt (316L solidus taken as 1400 C, as recalled; latent heat ignored, so every time is short):
  L1  lumped 1 mm layer, no conduction (the published v2.4 metric; lower bound on the time);
  SI  semi-infinite 316L, constant flux: surface reaches 1400 C at t = pi k rho c (1400 - T0)^2 / (4 q^2);
  FD  1-D finite slab, 6 mm lip, flux on the bore, adiabatic outer face (no loss to the nozzle body: short), k(T) and c(T)
      of 316L (ASSUMED, LITERATURE as recalled): time for the bore surface and for the 1 mm depth to reach 1400 C.
usage: python -I nozzle_lip_melt_v2p4.py NOZZLE_JOINT_JSON OUT_JSON
"""
from __future__ import annotations
import hashlib, json, math, os, sys
sys.dont_write_bytecode = True
import numpy as np

T_MELT = 1400.0
RHO = 7950.0
T0S = (223.0, 264.0, 342.0, 250.0)       # J1b-0.5 B1; J1 A1; J1 B1 p99 hi bound; the v2.4 published basis


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def k316(T):      # W/mK, T in C (ASSUMED fit, as recalled: ~16 at 100 C, ~21 at 500 C, ~26 at 900 C, ~30 at 1300 C)
    return 14.6 + 0.0127 * T


def c316(T):      # J/kgK (ASSUMED fit, as recalled: ~500 at 20 C, ~590 at 600 C, ~640 at 1000 C)
    return 490.0 + 0.155 * T - 2.0e-5 * T ** 2


def fd_slab(q, T0, L=6e-3, n=121, t_end=400.0):
    x = np.linspace(0.0, L, n); dx = x[1] - x[0]
    T = np.full(n, T0)
    t = 0.0; t_surf = None; t_1mm = None
    i1 = int(round(1e-3 / dx))
    while t < t_end:
        k = k316(T); c = c316(T)
        alpha = k / (RHO * c)
        dt = 0.4 * dx * dx / float(alpha.max())
        kf = 0.5 * (k[1:] + k[:-1])
        flux = -kf * (T[1:] - T[:-1]) / dx             # W/m2 between nodes, +x direction
        dT = np.zeros(n)
        dT[0] = (q - flux[0]) / (RHO * c[0] * dx / 2)
        dT[1:-1] = (flux[:-1] - flux[1:]) / (RHO * c[1:-1] * dx)
        dT[-1] = flux[-1] / (RHO * c[-1] * dx / 2)       # adiabatic outer face
        T = T + dt * dT; t += dt
        if t_surf is None and T[0] >= T_MELT:
            t_surf = t
        if T[i1] >= T_MELT:
            t_1mm = t; break
    return t_surf, t_1mm


def main(nj_f, out_f):
    NJ = json.load(open(nj_f)); lp = NJ['leak_path']
    H = lp['enthalpy_flow_W']; A = lp['lip_bore_area_mm2'] * 1e-6
    rows = {}
    for frac in (0.05, 0.20):
        for Hh in H:
            q = frac * Hh / A
            for T0 in T0S:
                rc = RHO * c316(0.5 * (T0 + T_MELT))
                kk = k316(0.5 * (T0 + T_MELT))
                L1 = 8000.0 * 500.0 * 1e-3 * (T_MELT - T0) / q         # the published metric (nozzle_joint_v2p4: rho c 4.0e6)
                SI = math.pi * kk * rc * (T_MELT - T0) ** 2 / (4.0 * q * q)
                ts, t1 = fd_slab(q, T0)
                rows[f'dep{frac:.2f}|H{Hh/1e3:.1f}kW|T0_{T0:.0f}C'] = dict(q_MW_m2=q / 1e6, L1_lumped_1mm_s=L1, SI_surface_s=SI,
                                                                          FD_surface_s=ts, FD_1mm_depth_s=t1)
    for kk_, vv_ in lp['lip_heating'].items():           # reproduce the published 250 C basis
        dep, Hk = kk_.split('_')
        r_ = rows[f'{dep}|{Hk}|T0_250C']
        assert abs(r_['L1_lumped_1mm_s'] - vv_['t_1mm_layer_to_1400C_s']) < 1e-6, (kk_, r_['L1_lumped_1mm_s'], vv_)
    summ = {}
    for T0 in T0S:
        sel = {k: v for k, v in rows.items() if k.endswith(f'T0_{T0:.0f}C')}
        summ[f'T0_{T0:.0f}C'] = {m: [min(v[m] for v in sel.values() if v[m] is not None), max(v[m] for v in sel.values() if v[m] is not None)]
                                 for m in ('L1_lumped_1mm_s', 'SI_surface_s', 'FD_surface_s', 'FD_1mm_depth_s')}
        summ[f'T0_{T0:.0f}C']['FD_1mm_depth_none_within_400s'] = sum(1 for v in sel.values() if v['FD_1mm_depth_s'] is None)
    ratio = {m: [summ['T0_342C'][m][0] / summ['T0_223C'][m][0], summ['T0_342C'][m][1] / summ['T0_223C'][m][1]]
             for m in ('L1_lumped_1mm_s', 'SI_surface_s', 'FD_surface_s', 'FD_1mm_depth_s')}
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/nozzle_lip_melt_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               inputs={'nozzle_joint_v2p4.json': sha16(nj_f), 'Mechanical 04-fea/thermal/j1_check_v1.json (values relayed: lip bore 342 C B1 p99 hi, 264 C A1; J1b-0.5 223 C, mica face 902 C)': 'd9356e0b64401c63'},
               T_melt_C=T_MELT, starting_temperatures_C=dict(J1b_0p5_B1=223.0, J1_A1=264.0, J1_B1_p99_hi=342.0, v2p4_basis=250.0),
               rows=rows, summary_by_T0=summ, ratio_J1_342_over_J1b_223=ratio,
               tags=dict(leak='DERIVED (nozzle_joint_v2p4)', deposition='ASSUMED 5-20 %', properties='316L k(T), c(T) ASSUMED fits, LITERATURE as recalled, TO-VERIFY',
                         model='DERIVED; adiabatic outer face and no latent heat: short (conservative) times'))
    json.dump(out, open(out_f, 'w'), indent=1, default=float)
    for k, v in summ.items():
        print(k, json.dumps(v, default=float))
    print('ratio 342/223', json.dumps(ratio))
    print('wrote', out_f, sha16(out_f))


if __name__ == '__main__':
    main(*sys.argv[1:3])

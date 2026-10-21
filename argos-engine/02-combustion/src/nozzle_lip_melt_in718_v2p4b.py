"""H19 lip melt-time bound for the Inconel 718 TC-09 aft section (Combustion v2.4b, 2026-10-13).

REV-COMB-3 R3-09 and LEAD CHANGELOG line 194 (9): TC-09, which carries the J1 lip, is Inconel 718 since LEAD lines 177 (1)/178
(CAD v3.5).  The v2.4 H19 bound (nozzle_lip_melt_v2p4.py, 316L solidus taken as 1400 C) is recomputed for IN718.
Melting range: 1260-1336 C (2300-2437 F), DATASHEET: Special Metals Corporation, INCONEL alloy 718, publication SMC-045 (Sept 2007),
Table 2 'Physical Constants', read on 2026-10-13 through the session's web-fetch reader from
https://www.specialmetals.com/documents/technical-bulletins/inconel/inconel-alloy-718.pdf (a direct download was refused by the proxy,
so no copy of the PDF is archived: TO-ARCHIVE by the founders/Mechanical).  The same table gives density 0.296 lb/in3 (8193 kg/m3) and
specific heat 435 J/kg C at 21 C, which match Mechanical's materials v1.4 entry (8190 kg/m3; 435 J/kg K at 20 C).  Melt onset is
taken at the solidus (1260 C); the liquidus (1336 C) is given for reference.  Properties: Mechanical's materials database v1.4 (04-fea/materials/materials_v1p4.json, IN718 entry: rho 8190
kg/m3 LITERATURE; k(T) and cp(T) LITERATURE-approx tables to 700 C, extrapolated linearly above 700 C: ASSUMED).
Leak and heat flux unchanged (nozzle_joint_v2p4.json): leak 0.83-1.10 % of the 100 % flow, enthalpy flow 8.5-11.4 kW, deposited fraction
5 % or 20 % (ASSUMED) on the 575 mm2 lip bore.  Three readings as in v2.4 (latent heat ignored, adiabatic outer face: short times):
  L1  lumped 1 mm layer; SI  semi-infinite, constant flux; FD  1-D 6 mm slab with k(T), c(T): surface and 1 mm depth.
Start temperatures: 342 C (the v2.4 basis: J1 lip, B1 p99 hi bound, 316L era), 295 C (Mechanical nozzle_joint_v2p4 relay in
mechanical.json v2.1: J1 lip in flight) and 655 C (REV-MECH-1 RM1-06: TC-09 part maximum on the IN718 FE; a conservative upper start).
Tags: DERIVED on ASSUMED deposition, DATASHEET melting range and LITERATURE-approx properties (Mechanical materials v1.4); not physical
evidence.
usage: python -I nozzle_lip_melt_in718_v2p4b.py NOZZLE_JOINT_JSON MATERIALS_JSON OUT_JSON
"""
from __future__ import annotations
import hashlib, json, math, os, sys
sys.dont_write_bytecode = True
import numpy as np

T_SOL, T_LIQ = 1260.0, 1336.0                    # C, DATASHEET Special Metals SMC-045 (2007) Table 2 (web-fetch read 2026-10-13)
T0S = (295.0, 342.0, 655.0)
EXPECT = {'nozzle_joint_v2p4.json': 'b5f396c7155c06c4', 'materials_v1p4.json': '18aa13a888b1e6f3'}
PUB_316L = dict(L1_lumped_1mm_s=[1.07, 5.70], FD_1mm_depth_s=[6.63, 40.26], T_melt_C=1400.0, T0_C=342.0)


def sha16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


def main(nj_f, mat_f, out_f):
    assert sha16(nj_f) == EXPECT['nozzle_joint_v2p4.json'], sha16(nj_f)
    assert sha16(mat_f) == EXPECT['materials_v1p4.json'], sha16(mat_f)
    M = json.load(open(mat_f))['materials']['IN718']
    RHO = M['rho']['v']
    kT, kv = np.array(M['k']['T_C'], float), np.array(M['k']['v'], float)
    cT, cv = np.array(M['cp']['T_C'], float), np.array(M['cp']['v'], float)
    sk = (kv[-1] - kv[-2]) / (kT[-1] - kT[-2]); sc = (cv[-1] - cv[-2]) / (cT[-1] - cT[-2])

    def k718(T):
        T = np.asarray(T, float)
        return np.where(T <= kT[-1], np.interp(T, kT, kv), kv[-1] + sk * (T - kT[-1]))

    def c718(T):
        T = np.asarray(T, float)
        return np.where(T <= cT[-1], np.interp(T, cT, cv), cv[-1] + sc * (T - cT[-1]))

    def fd_slab(q, T0, T_m, L=6e-3, n=121, t_end=400.0):
        x = np.linspace(0.0, L, n); dx = x[1] - x[0]
        T = np.full(n, T0); t = 0.0; t_surf = None; t_1mm = None
        i1 = int(round(1e-3 / dx))
        while t < t_end:
            k = k718(T); c = c718(T)
            dt = 0.4 * dx * dx / float((k / (RHO * c)).max())
            kf = 0.5 * (k[1:] + k[:-1]); flux = -kf * (T[1:] - T[:-1]) / dx
            dT = np.zeros(n)
            dT[0] = (q - flux[0]) / (RHO * c[0] * dx / 2)
            dT[1:-1] = (flux[:-1] - flux[1:]) / (RHO * c[1:-1] * dx)
            dT[-1] = flux[-1] / (RHO * c[-1] * dx / 2)
            T = T + dt * dT; t += dt
            if t_surf is None and T[0] >= T_m:
                t_surf = t
            if T[i1] >= T_m:
                t_1mm = t; break
        return t_surf, t_1mm

    NJ = json.load(open(nj_f)); lp = NJ['leak_path']
    H = lp['enthalpy_flow_W']; A = lp['lip_bore_area_mm2'] * 1e-6
    rows = {}
    for T_m, lab_m in ((T_SOL, 'solidus'), (T_LIQ, 'liquidus')):
        for frac in (0.05, 0.20):
            for Hh in H:
                q = frac * Hh / A
                for T0 in T0S:
                    Tm_mid = 0.5 * (T0 + T_m)
                    rc = RHO * float(c718(Tm_mid)); kk = float(k718(Tm_mid))
                    L1 = rc * 1e-3 * (T_m - T0) / q
                    SI = math.pi * kk * rc * (T_m - T0) ** 2 / (4.0 * q * q)
                    ts, t1 = fd_slab(q, T0, T_m)
                    rows[f'{lab_m}|dep{frac:.2f}|H{Hh/1e3:.1f}kW|T0_{T0:.0f}C'] = dict(q_MW_m2=q / 1e6, L1_lumped_1mm_s=L1, SI_surface_s=SI,
                                                                                      FD_surface_s=ts, FD_1mm_depth_s=t1)
    summ = {}
    for lab_m in ('solidus', 'liquidus'):
        for T0 in T0S:
            sel = {k: v for k, v in rows.items() if k.startswith(lab_m) and k.endswith(f'T0_{T0:.0f}C')}
            summ[f'{lab_m}|T0_{T0:.0f}C'] = {m: [min(v[m] for v in sel.values() if v[m] is not None), max(v[m] for v in sel.values() if v[m] is not None)]
                                             for m in ('L1_lumped_1mm_s', 'SI_surface_s', 'FD_surface_s', 'FD_1mm_depth_s')}
    out = dict(version='v2.4b', date='2026-10-13', script='02-combustion/src/nozzle_lip_melt_in718_v2p4b.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               request='REV-COMB-3 R3-09; LEAD CHANGELOG line 194 (9): H19 lip-melt bound for IN718',
               inputs={'nozzle_joint_v2p4.json': sha16(nj_f), '04-fea/materials/materials_v1p4.json (Mechanical)': sha16(mat_f)},
               melting_range_C=dict(solidus=T_SOL, liquidus=T_LIQ, F=[2300.0, 2437.0],
                                    tag='DATASHEET: Special Metals Corporation, INCONEL alloy 718, publication SMC-045 (Sept 2007), Table 2 '
                                        '"Melting Range 2300-2437 F / 1260-1336 C"; read 2026-10-13 through the web-fetch reader (summarising) from '
                                        'https://www.specialmetals.com/documents/technical-bulletins/inconel/inconel-alloy-718.pdf; the PDF is not '
                                        'archived (direct download refused by the proxy): TO-ARCHIVE. Same table: density 0.296 lb/in3 = 8193 kg/m3 '
                                        '(materials v1.4: 8190), specific heat 435 J/kg C at 21 C (materials v1.4: 435 at 20 C)'),
               properties=dict(rho_kg_m3=RHO, k_table=dict(T_C=list(kT), v=list(kv)), cp_table=dict(T_C=list(cT), v=list(cv)),
                               extrapolation='linear above 700 C (slope of the last interval): ASSUMED'),
               starting_temperatures_C=dict(v2p4_basis_B1_p99_hi=342.0, J1_lip_in_flight_mechanical_json_v2p1=295.0, TC09_part_max_RM1_06=655.0),
               rows=rows, summary=summ, published_316L_v2p4=PUB_316L,
               tags=dict(leak='DERIVED (nozzle_joint_v2p4)', deposition='ASSUMED 5-20 %', melting='DATASHEET (SMC-045; PDF TO-ARCHIVE)',
                         properties='LITERATURE-approx (Mechanical materials v1.4) + ASSUMED extrapolation above 700 C',
                         model='DERIVED; adiabatic outer face and no latent heat: short (conservative) times'))
    json.dump(out, open(out_f, 'w'), indent=1, default=float)
    for k, v in summ.items():
        print(k, json.dumps({m: [round(x, 3) for x in r] for m, r in v.items()}))
    print('wrote', out_f, sha16(out_f))


if __name__ == '__main__':
    main(*sys.argv[1:4])

"""Head-end thermal boundary conditions and first-cut bounds (Combustion v2.2b, 2026-10-12; lead request for the HV69
pintle-servo mount check: HV69 rated -10..60 C, mount limit 50 C in flight incl. relight).

v2.2b (same day) replaces the first cut (run 1, kept as data/v2/headend_thermal_v2_run1_superseded.json): run 1 had no
surface re-radiation on the hot-gas side, so the 1.6 mm phenolic pre-chamber insulator surface ran away and the forward
case node reached 670-1890 K (above the 6061 solidus: unphysical); the joint to the head was one-way (the case did not
lose the heat it gave the head). v2.2b: (i) radiative exchange on every hot-gas-side surface (emissivity 0.8): injector
face <-> pre-chamber insulator (F 0.65) and <-> grain forward face/port (F 0.35); insulator -> face (F 0.29 by
reciprocity) and -> grain end (F 0.29), grain surface 750 K while burning (ASSUMED ABS pyrolysis surface), 700 K at
shutdown with a 1 s decay; the gas radiation band of thermal_bc_*_v2.csv is the incident (absorbed) gas term;
(ii) two-way joint between the forward case node and the head (4 W/K ASSUMED); (iii) geometry of Mechanical CAD v3.2
(parts_engine.py, read only): TC-10 face insulator disc phenolic 2 mm over r 10.2-26.85 mm, TC-03 seat-insert flange
r 2.75-10.1 mm (17-4PH, bare, lumped with the head), TC-06 pre-chamber insulator 1.6 mm phenolic over x_face 0-0.030 m,
10 mm manifold bore around the 6 mm needle body (N2O annulus D_h 4 mm, 50.3 mm2, wetted bore 10 x 52 mm); head TC-02
mass ~0.44 kg estimated from the CAD dimensions (63.5 x 28 head + 57.2 x 36 plug less bores; DERIVED, Mechanical mass
properties replace it); (iv) energy bookkeeping per path (face, joint, N2O, bay) for flight and soak.

Surfaces: injector face (r 2.75-26.95 mm at x_face 0, 2.26e-3 m2), pre-chamber wall (x_face 0-0.030 m), pintle needle
(17-4PH, 4 mm stem in the PTFE guide, 6 mm body in the manifold bore; tip in the 5.5 mm seat).
Phases from the duty-cycle histories: burn, MECO coast (pintle seated, isolation valve open, chamber vented), relight,
landing burn, post-landing soak to 3600 s (isolation valve closed, trapped liquid relieved to the tank side).

1. BC time series per duty cycle (data/v2/headend_bc_<DC>_v2.csv):
   burn  gas side: h_g(Pc), T_aw(Pc), q_rad band interpolated in log(Pc) between the five thermal_bc_*_v2.csv rows at
         x_face 0 (Bartz at the pre-chamber diameter, Tw 600 K; the CSVs flag Bartz as outside its validity in the
         recirculating pre-chamber -> band x0.5-2). Below the 12.5 % floor h_g ~ Pc^0.8, T_aw held, q_rad ~ Pc.
         T_aw = delivered stagnation temperature = UPPER BOUND for the spray-cooled injector face (the head-end gas
         temperature is UNKNOWN: thermocouple in the face disc at T1). Radiative exchange with the insulator and the
         grain as above (surface temperatures from the bound model, columns of the json; the CSV carries the gas terms).
         N2O side (head manifold, pintle annulus): liquid at the tank liquid temperature of the DC record, Dittus-Boelter
         h_c = 0.023 Re^0.8 Pr^0.4 k/D_h, liquid density/cp from CoolProp, viscosity/conductivity from the CO2
         corresponding-states surrogate of tank_nheq.py (CoolProp has no N2O transport model).
   coast gas side: natural convection h_nc 10 W/m2K (band x0.5-2) to cavity gas taken at the insulator surface
         temperature (upper bound) + the radiative exchange above (grain 700 K at shutdown decaying with 1 s).
         N2O side: static liquid at the tank temperature (isolation valve open), hA 1 W/K (ASSUMED).
   soak  as coast; N2O side vapour only (hA 0.01 W/K): no evaporative credit after the last shutdown (conservative).
2. First-cut bounds (DERIVED; Mechanical thermal FEA with the real head/bonnet/bracket supersedes):
   a. pre-chamber wall stack 1.6 mm phenolic + 3.175 mm 6061 case, gas side as burn while burning (with re-radiation),
      adiabatic otherwise (conservative for the case), back side bay h 10 W/m2K + the joint to the head.
   b. lumped head (0.2 kg low-mass bound / 0.44 kg CAD estimate, c 900 J/kg K) with the face as CAD v3.2 (2 mm disc),
      a 4 mm disc option, or bare (disc lost); disc = 1-D slab with 2000 W/m2K contact to the head; N2O cooling
      hA = h_c(mdot) x 16.3 cm2 during flow, 1 W/K coast, 0.01 W/K soak; bay h 10 W/m2K over 0.01 m2; start 293.15 K.
   NOT modelled: phenolic pyrolysis/char/ablation (no credit: conservative), axial conduction along the 6061 case from
   the hot aft end (TS-2 aft land 493-699 K behind 5 mm phenolic) to the head (fin m 4.5 1/m over 0.27 m, cosh mL 1.8,
   diffusion ~1000 s: a post-landing item for the FEA), temperature gradients inside the head (diffusion time ~60 s
   over 64 mm: the lumped value overstates the head top early in a burn), the head-to-servo path (bonnet, bracket TC-12).
usage: python headend_thermal_v2.py DATA_V2_DIR FIGDIR
"""
from __future__ import annotations
import csv, json, math, os, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import CoolProp.CoolProp as CP

TA = 288.15            # bay / ambient [K]
T_INIT = 293.15        # hardware at the 20 C conditioning temperature [K]
SIG = 5.670374419e-8
A_FACE = math.pi * (0.02695 ** 2 - 0.00275 ** 2)      # whole face, bare variant
A_ANNULUS = math.pi * (0.02685 ** 2 - 0.0102 ** 2)    # TC-10 disc (CAD v3.2)
A_CENTRE = math.pi * (0.0101 ** 2 - 0.00275 ** 2)     # TC-03 seat-insert flange face (bare, lumped with the head)
A_INS = math.pi * 0.0539 * 0.030                      # pre-chamber insulator gas-side area
F_INS, F_GRAIN, EPS = 0.65, 0.35, 0.8                 # face -> insulator, face -> grain end; emissivity
F_IF = A_FACE * F_INS / A_INS                         # insulator -> face (reciprocity, ~0.29)
F_IG = F_IF                                           # insulator -> grain end (symmetry)
T_GRAIN_BURN = 750.0                                  # ABS surface while burning [K] ASSUMED
D_BORE, D_STEM = 0.010, 0.006                         # CAD v3.2 manifold bore / needle body
A_ANN = math.pi / 4 * (D_BORE ** 2 - D_STEM ** 2); DH = D_BORE - D_STEM
A_WET = math.pi * D_BORE * 0.052                      # wetted manifold bore [m2]
HA_COAST, HA_SOAK = 1.0, 0.01
G_JOINT = 4.0
H_BAY, A_EXT = 10.0, 0.01
H_NC = 10.0
T_SOAK = 3600.0
PTS = ('floor12p5', '20pct', '50pct', '75pct', 'max')
CONS = {'bare': None, 'disc2mm': 2.0e-3, 'disc4mm': 4.0e-3}
MASSES = (0.2, 0.44)


def bc_points(ddir):
    rows = []
    for p in PTS:
        fn = os.path.join(ddir, f'thermal_bc_{p}_v2.csv')
        hdr = open(fn).readline()
        Pc = float(hdr.split('Pc=')[1].split(' Pa')[0])
        r = next(csv.DictReader(l for l in open(fn) if not l.startswith('#')))
        lo, hi = [float(v) for v in r['q_rad_band_W_m2'].split('-')]
        rows.append(dict(point=p, Pc=Pc, h=float(r['h_g_Tw600_W_m2K']), Taw=float(r['T_aw_K']), qlo=lo, qhi=hi))
    return rows


class BC:
    def __init__(self, rows):
        self.lp = np.log([r['Pc'] for r in rows]); self.rows = rows
        self.h = np.array([r['h'] for r in rows]); self.T = np.array([r['Taw'] for r in rows])
        self.qlo = np.array([r['qlo'] for r in rows]); self.qhi = np.array([r['qhi'] for r in rows])
        self.Pmin = rows[0]['Pc']

    def __call__(self, Pc):
        if Pc >= self.Pmin:
            l = math.log(Pc)
            return (float(np.interp(l, self.lp, self.h)), float(np.interp(l, self.lp, self.T)),
                    float(np.interp(l, self.lp, self.qlo)), float(np.interp(l, self.lp, self.qhi)))
        s = max(Pc, 1e3) / self.Pmin
        return self.h[0] * s ** 0.8, self.T[0], self.qlo[0] * s, self.qhi[0] * s


# N2O liquid properties: CoolProp EOS (rho, cp) + CO2 corresponding-states transport (as tank_nheq.py)
_TC = CP.PropsSI('Tcrit', 'NitrousOxide'); _TC2 = CP.PropsSI('Tcrit', 'CO2')


def n2o_hc(T, mdot):
    T = min(max(T, 250.0), 300.0)
    rho = CP.PropsSI('D', 'T', T, 'Q', 0, 'NitrousOxide'); cp = CP.PropsSI('C', 'T', T, 'Q', 0, 'NitrousOxide')
    tc = T / _TC * _TC2
    mu = CP.PropsSI('V', 'T', tc, 'Q', 0, 'CO2'); k = CP.PropsSI('L', 'T', tc, 'Q', 0, 'CO2')
    G = mdot / A_ANN; Re = G * DH / mu; Pr = cp * mu / k
    h = 0.023 * Re ** 0.8 * Pr ** 0.4 * k / DH
    return h, dict(rho=rho, cp=cp, mu=mu, k=k, Re=Re, Pr=Pr, v=G / rho)


def tdma(a, b, c, d):
    n = len(b); cp_ = np.zeros(n); dp_ = np.zeros(n)
    cp_[0] = c[0] / b[0]; dp_[0] = d[0] / b[0]
    for k in range(1, n):
        m = b[k] - a[k] * cp_[k - 1]
        cp_[k] = c[k] / m if k < n - 1 else 0.0
        dp_[k] = (d[k] - a[k] * dp_[k - 1]) / m
    x = np.zeros(n); x[-1] = dp_[-1]
    for k in range(n - 2, -1, -1):
        x[k] = dp_[k] - cp_[k] * x[k + 1]
    return x


def rad_lin(Ts, others):
    """Linearised radiative exchange eps*sigma*sum F_i (T_i^4 - T^4) about Ts -> (h_r, T_ref): q = h_r (T_ref - T)."""
    sF = sum(F for F, _ in others)
    if sF <= 0:
        return 0.0, Ts
    hr = 4.0 * EPS * SIG * sF * Ts ** 3
    Tref = (EPS * SIG * sum(F * Ti ** 4 for F, Ti in others) + 3.0 * EPS * SIG * sF * Ts ** 4) / hr
    return hr, Tref


class Slab:
    """1-D slab (layers), implicit; front: h_f (T_f) + q_f [+ linearised radiation], back: h_b (T_b)."""
    def __init__(self, layers):
        xs, ks, rcs = [], [], []
        for L, k, rho, c, n in layers:
            xs += [L / n] * n; ks += [k] * n; rcs += [rho * c] * n
        self.x = np.array(xs); self.k = np.array(ks); self.rc = np.array(rcs)
        self.G = 1.0 / (0.5 * self.x[:-1] / self.k[:-1] + 0.5 * self.x[1:] / self.k[1:])
        self.T = np.full(len(xs), T_INIT)

    def step(self, dt, h_f, T_f, q_f, h_b, T_b, rad=None):
        if rad:
            hr, Tr = rad_lin(float(self.T[0]), rad)
            if h_f + hr > 0:
                T_f = (h_f * T_f + hr * Tr) / (h_f + hr); h_f = h_f + hr
        n = len(self.x); a = np.zeros(n); b = self.rc * self.x / dt; c = np.zeros(n); d = self.rc * self.x / dt * self.T
        b[:-1] += self.G; c[:-1] = -self.G; b[1:] += self.G; a[1:] = -self.G
        if h_f > 0:
            hs = 1.0 / (1.0 / h_f + 0.5 * self.x[0] / self.k[0]); b[0] += hs; d[0] += hs * T_f
        d[0] += q_f
        hb = 1.0 / (1.0 / h_b + 0.5 * self.x[-1] / self.k[-1]); b[-1] += hb; d[-1] += hb * T_b
        self.T = tdma(a, b, c, d)
        return self.T


def phases(t, Pc, mox):
    burning = (mox > 1e-4) & (Pc > 1.5e5)
    idx = np.where(burning)[0]
    segs = []
    if len(idx):
        start = idx[0]; prev = idx[0]
        for i in idx[1:]:
            if i != prev + 1:
                segs.append((start, prev)); start = i
            prev = i
        segs.append((start, prev))
    return burning, segs


def time_grid(t, segs):
    t_last = t[segs[-1][1]]
    g = list(np.arange(t[0], t_last + 1.0, 0.01))
    g += list(np.arange(g[-1] + 0.1, t_last + 60.0, 0.1))
    g += list(np.arange(g[-1] + 0.5, t_last + T_SOAK + 1e-9, 0.5))
    return np.array(g), t_last


def face_flux(Ts, on, hg, Taw, qr, T_ins, Tg, band):
    """Net heat flux into a face surface at Ts [W/m2] (explicit form, used for the lumped bare surfaces)."""
    rad = EPS * SIG * (F_INS * (T_ins ** 4 - Ts ** 4) + F_GRAIN * (Tg ** 4 - Ts ** 4))
    if on:
        return hg * (Taw - Ts) + qr + rad
    return H_NC * band * (T_ins - Ts) + rad


def run_case(d, bcf, band, construction, m_h):
    t = d.t.values; Pc = d.Pc.values; mox = d.mox.values; Tt = d.T_tank.values
    burning, segs = phases(t, Pc, mox)
    tg, t_last = time_grid(t, segs)
    wall = Slab([(1.6e-3, 0.30, 1400.0, 1300.0, 16), (3.175e-3, 167.0, 2700.0, 900.0, 6)])
    th = CONS[construction]
    disc = Slab([(th, 0.30, 1400.0, 1300.0, max(10, int(round(th / 0.2e-3))))]) if th else None
    A_bare = A_FACE if disc is None else A_CENTRE
    Th = T_INIT; mc = m_h * 900.0
    rec = []; t_prev = tg[0]; t_sd = None; nxt = tg[0]; burned = False
    E = {k: 0.0 for k in ('face_flight', 'joint_flight', 'n2o_flight', 'bay_flight', 'face_soak', 'joint_soak', 'n2o_soak', 'bay_soak')}
    for tt in tg[1:]:
        dt = tt - t_prev; t_prev = tt
        i = min(int(np.searchsorted(t, tt)), len(t) - 1)
        on = bool(burning[i]) and tt <= t_last + 1e-9
        flow = bool(mox[i] > 1e-4) and tt <= t_last + 1e-9
        if on:
            h, Taw, qlo, qhi = bcf(Pc[i]); hg = h * band
            qr = {0.5: qlo, 1.0: 0.5 * (qlo + qhi), 2.0: qhi}[band]
            t_sd = None; burned = True; Tg = T_GRAIN_BURN
        else:
            hg, Taw, qr = 0.0, TA, 0.0
            if t_sd is None and burned:
                t_sd = tt
            Tg = TA + (700.0 - TA) * math.exp(-(tt - t_sd) / 1.0) if t_sd is not None else TA
        T_face_s = float(disc.T[0]) if disc is not None else Th
        # a: pre-chamber wall stack; burn: convection + gas radiation + exchange with the face and the grain end;
        #    otherwise adiabatic gas side; back: bay + two-way joint to the head (per unit insulator area)
        hjb = G_JOINT / A_INS
        hb = H_BAY + hjb; Tb = (H_BAY * TA + hjb * Th) / hb
        if on:
            Tw = wall.step(dt, hg, Taw, qr, hb, Tb, rad=[(F_IF, T_face_s), (F_IG, Tg)])
        else:
            Tw = wall.step(dt, 0.0, TA, 0.0, hb, Tb)
        T_ins = float(Tw[0]); T_case = float(Tw[-1])
        # b: head
        Ttank = float(Tt[i]) if np.isfinite(Tt[i]) else T_INIT
        if flow:
            hc, _ = n2o_hc(Ttank, max(float(mox[i]), 1e-3)); hA_n2o = hc * A_WET
        elif tt <= t_last + 1e-9:
            hA_n2o = HA_COAST
        else:
            hA_n2o = HA_SOAK
        Q_face = A_bare * face_flux(Th, on, hg, Taw, qr, T_ins, Tg, band)
        if disc is not None:
            if on:
                Td = disc.step(dt, hg, Taw, qr, 2000.0, Th, rad=[(F_INS, T_ins), (F_GRAIN, Tg)])
            else:
                Td = disc.step(dt, H_NC * band, T_ins, 0.0, 2000.0, Th, rad=[(F_INS, T_ins), (F_GRAIN, Tg)])
            Q_face += A_ANNULUS * 2000.0 * (float(Td[-1]) - Th) / (1 + 2000.0 * 0.5 * disc.x[-1] / disc.k[-1])
        Q_joint = G_JOINT * (T_case - Th); Q_n2o = -hA_n2o * (Th - Ttank); Q_bay = -H_BAY * A_EXT * (Th - TA)
        ph = 'flight' if tt <= t_last + 1e-9 else 'soak'
        E['face_' + ph] += Q_face * dt; E['joint_' + ph] += Q_joint * dt; E['n2o_' + ph] += Q_n2o * dt; E['bay_' + ph] += Q_bay * dt
        Th += (Q_face + Q_joint + Q_n2o + Q_bay) * dt / mc
        if tt >= nxt - 1e-9:
            rec.append(dict(t=tt, on=int(on), flow=int(flow), T_head=Th, T_ins=T_ins, T_case_fwd=T_case,
                            T_disc_surf=float(disc.T[0]) if disc is not None else float('nan'), Q_face_W=Q_face, Q_joint_W=Q_joint))
            nxt = tt + (0.05 if tt <= t_last + 1.0 else 1.0)
    return pd.DataFrame(rec), segs, t, t_last, E


def summarize(h, segs, t, t_last, E):
    t_meco = t[segs[0][1]]; t_rel = t[segs[1][0]] if len(segs) > 1 else None
    fl = h[h.t <= t_last + 1e-9]; so = h[h.t > t_last]
    def at(col, tv):
        return float(np.interp(tv, h.t, h[col]))
    def above(df, col, TK):
        if len(df) < 2:
            return 0.0
        dtt = np.gradient(df.t.values)
        return float(np.sum(dtt[df[col].values > TK]))
    out = dict(t_MECO_s=float(t_meco), t_relight_s=float(t_rel) if t_rel is not None else None, t_last_shutdown_s=float(t_last),
               energy_into_head_J={k: round(v, 0) for k, v in E.items()})
    for col in ('T_head', 'T_case_fwd', 'T_ins', 'T_disc_surf'):
        if h[col].isna().all():
            continue
        out[col] = dict(at_MECO_K=at(col, t_meco), at_relight_K=at(col, t_rel) if t_rel is not None else None,
                        max_in_flight_K=float(fl[col].max()), at_last_shutdown_K=at(col, t_last),
                        soak_peak_K=float(so[col].max()), soak_peak_after_shutdown_s=float(so.t[so[col].idxmax()] - t_last),
                        at_3600s_K=float(h[col].iloc[-1]))
    for TK, lab in ((323.15, '50C'), (333.15, '60C')):
        out[f'T_head_time_above_{lab}_in_flight_s'] = above(fl, 'T_head', TK)
        out[f'T_head_time_above_{lab}_soak_s'] = above(so, 'T_head', TK)
    return out


def main(ddir, figdir):
    os.makedirs(figdir, exist_ok=True)
    rows = bc_points(ddir); bcf = BC(rows)
    dcs = [('DC-A1 gnc v2', 'dc_gncv2wip/DC-A1-S230v2wip_neqE1e+03_reg1.csv'),
           ('DC-A2 gnc v2', 'dc_gncv2wip/DC-A2-S230v2wip_neqE1e+03_reg1.csv'),
           ('DC-B1 gnc v2', 'dc_gncv2wip/DC-B1-S230v2wip_neqE1e+03_reg1.csv'),
           ('DC-A1 gnc v1', 'dc_g3/DC-A1-S230_neqE1e+03_reg1.csv'),
           ('DC-B1 gnc v1', 'dc_g3/DC-B1-S230_neqE1e+03_reg1.csv'),
           ('DC-C ground', 'engine_S230/DC-C-S230_ground_reg1.csv')]
    hc100, pr100 = n2o_hc(293.15, 0.241); hc125, pr125 = n2o_hc(293.15, 0.0365)
    res = dict(version='v2.2b', date='2026-10-12', owner='Combustion',
               purpose='head-end thermal BC for the pintle-servo mount check (lead request 2026-10-12)',
               supersedes='v2.2 run 1 (headend_thermal_v2_run1_superseded.json): no re-radiation, one-way joint -> unphysical case node 670-1890 K',
               geometry=dict(source='Mechanical CAD v3.2 parts_engine.py (read only; Mechanical confirms)',
                             face_m2=A_FACE, disc_annulus_m2=A_ANNULUS, centre_seat_insert_m2=A_CENTRE, insulator_m2=A_INS,
                             view_factors=dict(face_to_insulator=F_INS, face_to_grain_end=F_GRAIN, insulator_to_face=F_IF,
                                               insulator_to_grain_end=F_IG), emissivity=EPS, grain_surface_burning_K=T_GRAIN_BURN,
                             head_mass_kg=dict(values=list(MASSES), note='0.2 low-mass bound; 0.44 = CAD v3.2 TC-02 estimate from dimensions (DERIVED)'),
                             constructions={'bare': 'no face disc (disc lost / not fitted)', 'disc2mm': 'CAD v3.2 TC-10 2 mm phenolic disc',
                                            'disc4mm': '4 mm phenolic disc (option)'}),
               bc_points_x_face0=rows,
               n2o_side=dict(geometry='CAD v3.2 manifold: 10 mm bore around the 6 mm needle body (D_h 4 mm, A 50.3 mm2), wetted bore 10 x 52 mm',
                             formula='h_c = 0.023 Re^0.8 Pr^0.4 k / D_h, Re = (mdot/A) D_h / mu',
                             h_c_100pct_W_m2K=hc100, props_100pct=pr100, h_c_12p5pct_W_m2K=hc125, props_12p5pct=pr125,
                             hA_100pct_W_K=hc100 * A_WET,
                             coast='static liquid at the tank temperature, hA 1 W/K (ASSUMED 1000 W/m2K x 10 cm2)',
                             soak='vapour only, hA 0.01 W/K (no evaporative credit)'),
               coast_soak_gas_side=dict(h_nc_W_m2K=H_NC, band='x0.5-2', T_cavity='insulator surface temperature (upper bound)',
                                        radiation='face <-> insulator (F 0.65), face <-> grain end (F 0.35), emissivity 0.8',
                                        grain_side='700 K at shutdown, 1 s decay (ASSUMED)'),
               pintle_needle=dict(stem_conductance_W_K=18.0 * math.pi / 4 * 0.004 ** 2 / 0.10,
                                  note='17-4PH 4 mm stem over 0.10 m: 2.3e-3 W/K, i.e. < 1 W at 300 K difference: the '
                                       'needle is not a heat path to the servo; its tip takes the injector-face BC and the '
                                       'N2O-side h_c (it sits in the flow)'),
               not_modelled=('phenolic pyrolysis/char/ablation (no credit); axial conduction along the 6061 case from the hot aft '
                             'end (post-landing item for the FEA: fin m 4.5 1/m, cosh mL 1.8, diffusion ~1000 s); gradients inside '
                             'the head (diffusion ~60 s); head-to-servo path (bonnet, bracket TC-12)'),
               cases={})
    figd = {}
    for name, rel in dcs:
        fn = os.path.join(ddir, rel)
        if not os.path.exists(fn):
            print('missing', fn); continue
        d = pd.read_csv(fn, comment='#')
        # BC time series (x1)
        t = d.t.values; Pc = d.Pc.values; mox = d.mox.values
        burning, segs = phases(t, Pc, mox)
        bc_rows = []
        for i in range(0, len(t), 1 if len(t) < 6000 else 2):
            on = bool(burning[i])
            h, Taw, qlo, qhi = bcf(Pc[i]) if on else (0.0, float('nan'), 0.0, 0.0)
            hc = n2o_hc(float(d.T_tank.values[i]), float(mox[i]))[0] if mox[i] > 1e-4 else float('nan')
            bc_rows.append(dict(t_s=t[i], burning=int(on), Pc_Pa=Pc[i], mdot_ox_kg_s=mox[i], T_N2O_liquid_K=d.T_tank.values[i],
                                h_g_face_W_m2K=h, T_aw_upper_K=Taw, q_rad_lo_W_m2=qlo, q_rad_hi_W_m2=qhi, h_c_N2O_W_m2K=hc))
        tag = name.replace(' ', '_').replace('gnc_', 'gnc')
        out_csv = os.path.join(ddir, f'headend_bc_{tag}_v2.csv')
        with open(out_csv, 'w', newline='') as f:
            f.write('# Head-end BC time series v2.2b (x1; apply x0.5-2 to h_g, q_rad picks lo/hi): injector face and pre-chamber '
                    'wall gas side while burning (Bartz at x_face 0 from thermal_bc_*_v2.csv, T_aw = delivered T0 = UPPER '
                    'BOUND; gas radiation = incident term), plus radiative exchange face<->insulator F 0.65 / face<->grain end F 0.35, '
                    'emissivity 0.8, grain 750 K burning; N2O-side h_c on the CAD v3.2 manifold annulus (10/6 mm) during flow; '
                    'outside burns see headend_thermal_v2.json (coast: h_nc 10 W/m2K to the insulator temperature + the same '
                    'radiative exchange, grain 700 K at shutdown decaying 1 s; soak: no N2O credit). Source DC: ' + rel + '. SI units. DERIVED.\n')
            w = csv.DictWriter(f, fieldnames=list(bc_rows[0].keys())); w.writeheader(); w.writerows(bc_rows)
        res['cases'][name] = dict(dc_file=rel, bc_csv=os.path.basename(out_csv), variants={})
        for band in (0.5, 1.0, 2.0):
            for cons in CONS:
                for m_h in MASSES:
                    h, segs_, t_, t_last, E = run_case(d, bcf, band, cons, m_h)
                    key = f'hg_x{band:g}|{cons}|head_{m_h:.2f}kg'
                    res['cases'][name]['variants'][key] = summarize(h, segs_, t_, t_last, E)
                    s = res['cases'][name]['variants'][key]
                    print(name, key, 'head flight max', round(s['T_head']['max_in_flight_K'], 1), 'relight',
                          None if s['T_head']['at_relight_K'] is None else round(s['T_head']['at_relight_K'], 1),
                          'soak peak', round(s['T_head']['soak_peak_K'], 1), 'case fwd flight/soak',
                          round(s['T_case_fwd']['max_in_flight_K'], 1), round(s['T_case_fwd']['soak_peak_K'], 1),
                          'ins max', round(s['T_ins']['max_in_flight_K'], 0), 'E', s['energy_into_head_J'], flush=True)
                    figd[(name, band, cons, m_h)] = h
    json.dump(res, open(os.path.join(ddir, 'headend_thermal_v2.json'), 'w'), indent=1, default=float)
    # figure: head temperature, first 40 s and the soak, A1/A2/B1 gnc v2 + DC-C, CAD disc vs bare, x0.5/1/2, CAD head mass
    names = [n for n, _ in dcs if (n, 1.0, 'bare', MASSES[1]) in figd][:4]
    fig, axs = plt.subplots(2, len(names), figsize=(4.6 * len(names), 7.5), squeeze=False)
    for j, n in enumerate(names):
        for band, ls in ((1.0, '-'), (2.0, '--'), (0.5, ':')):
            for cons, col in (('bare', 'tab:red'), ('disc2mm', 'tab:blue'), ('disc4mm', 'tab:green')):
                hh = figd.get((n, band, cons, MASSES[1]))
                if hh is None:
                    continue
                lab = f'{cons} hg x{band:g}'
                axs[0, j].plot(hh.t, hh.T_head - 273.15, ls=ls, color=col, lw=1, label=lab)
                axs[1, j].plot(hh.t, hh.T_head - 273.15, ls=ls, color=col, lw=1)
        hh = figd[(n, 1.0, 'disc2mm', MASSES[1])]
        axs[0, j].plot(hh.t, hh.T_case_fwd - 273.15, color='0.4', lw=1, label='case at pre-chamber (x1, disc2mm)')
        axs[1, j].plot(hh.t, hh.T_case_fwd - 273.15, color='0.4', lw=1)
        for a in axs[:, j]:
            a.axhline(50, color='k', lw=0.6, ls='-.'); a.axhline(60, color='k', lw=0.6, ls=':'); a.grid(alpha=0.3)
        axs[0, j].set_xlim(0, 40); axs[0, j].set_title(n + f' (head {MASSES[1]:.2f} kg)', fontsize=9, loc='left')
        axs[1, j].set_xscale('log'); axs[1, j].set_xlim(1, T_SOAK + 60); axs[1, j].set_xlabel('t [s]')
        axs[0, j].set_ylabel('T [C]'); axs[1, j].set_ylabel('T [C] (soak, log time)')
    axs[0, 0].legend(fontsize=7)
    fig.suptitle('Head-end lumped bound v2.2b (DERIVED; gas side T_aw = T0 upper bound, no char credit; FEA supersedes). '
                 '50 C mount limit -.-, 60 C HV69 rating ..', fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(figdir, 'headend_thermal_v2.png'), dpi=130); plt.close(fig)
    return res


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

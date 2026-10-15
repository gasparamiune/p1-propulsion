"""Retained vapour at the A1 relight on CAD v3.4.1: the integrated trade (Combustion v2.4, 2026-10-13).

Lead (CHANGELOG 2026-10-13): retained vapour is an integrated trade owned by Combustion: re-route (baseline) + forced-purge bleed
(2 taps, >= 0.8 mm) + PTFE lining (research) + relight attitude.  Coordinator: re-run reroute_vapour on v3.4.1 and give P_abort at
W 0.65 s (LO / HI / ARM-hot, wet and dry) for (1) re-route only, (2) + PTFE lining, (3) + 2-tap purge at 0.8 and 1.0 mm,
(4) + lining + purge, at relight attitudes 0, 2, 4 and 10 deg; purge slip on v3.4.1; the minimal set for P_abort <= 1e-3 at the
p99 attitude (GNC distribution pending).

Inputs (hashes recorded): Mechanical segment_traps_v341_v1 (volumes, 10 deg voxel tilt per direction), drain_pose_v341_v1
(workdir file, neutral-pose path pockets at 0 / 2 / 4 / 10 deg per direction: the hump shape at 2 and 4 deg), bleed_taps_v341_v1
(workdir; residual outside the hose with both taps, buoyancy only); segment_heat_budget_v1 (head-end W(t), needle);
Combustion segment_heat_v341_v2p4 (v3.4.1 route heat, lined and unlined), relight_vapour_order / coast_migration / start_latency /
post_abort_pocket (v2.4 data), GNC A1 coast series (windows, drogue load).

Volumes (barrier / open filter element; Mechanical DERIVED):
  segment 48.23 / 50.04; flow-path retained at 0 deg 12.00 / 13.81 = upstream of the element 4.72 (incl. the 0.52 hose micro-trap)
  + downstream 7.28 / 9.09 (incl. the 4.42 cm3 manifold annulus at the seat, which no tap sweeps: kept as vapour at the lift,
  conservative); dead ends 1.08 = module 1.01 (J602 cavity, MV balance chamber: part of the S1 cap region, do not flow) + head 0.07.
  Hose humps H(theta, az) = flow-path increase over 0 deg: at 10 deg the voxel values per direction; at 2 and 4 deg the neutral
  path-pocket proxy increase scaled by that direction's 10 deg voxel/proxy ratio.
Heat routing: head trap <- head end (FE bore, FD-01, TC-02, TC-04) + needle + riser + 1/2 TEE; hose region (humps) <- hose +
  sleeves + 1/2 TEE + trap overflow (wet); S1 cap <- module + FD-08F + wall line + hump overflow.  Coast-up: bubbles stay where
  they form, S1 vents liquid; drogue load: hose-region bubbles fill the humps first, the rest and the upper bubbles join the cap;
  descent: S1 vents only the expansion (as reroute_vapour_v2p4).
Purge (LEAD: MV open, pintle seated, both taps open, ending before E1; here it ends 0.05 s before E0 so both valves are confirmed
  closed at E0): T4 tap sweeps the downstream crown region, FD-01 tap the upstream front (FD-01 crown, riser, then the hump vapour,
  which the >= 12 g/s column flow carries: Fr check below), then the slug, then the S1 cap, which moves at s times the column
  speed (slip; s from Taylor-bubble drift: C0 1.0 ASSUMED for downward flow, Fr 0.35 vertical and 0.63 shallow-downward,
  LITERATURE as recalled, TO-VERIFY at CF-4).  Slip labels: scons = min(hose downslope, wall line) (conservative at every tilt);
  swall = wall line only (the hose near-horizontal at the design attitude, where an elongated bubble is not slower than the
  liquid); s1.0 and s0.5 brackets.  At 0 and 2 deg all four run at every azimuth; at 4, 10, 20 deg scons everywhere and the
  other three at az 45 (worst hump direction).  Tap fluxes per tap: HEM vapour 15 450, Dyer liquid 56 843
  kg/m2s, Cd 0.70 (purge_sizing_v2p4).  Regrowth from the purge end to E1 (<= 0.21 s) of all head, riser, TEE and hose heat is
  added to the pocket (conservative).
Ignition: the v2.4 200 000-sample E1 -> E2 distribution (seed 2024, assert), pocket purge 0.015555 s/cm3, liquid dead time
  0.023192 s/cm3, conventions 'paused' and 'restart' for short slugs; up to two vapour gaps behind the first liquid.
Tap configurations: both taps (T4 + FD-01, the LEAD form) and the FD-01 tap alone (T4 closed: the downstream crown vapour, up to
  7.3 / 9.1 cm3 with the annulus, stays at the seat), to test whether a single tap is enough for P_abort <= 1e-3.
Specific force for the drift: 1.14 g, the maximum at RELIGHT in GNC relight_attitude_v1 (0.94-1.14 g; SIM).  Design attitude
  (LEAD 2026-10-13): theta <= 2 deg, vent balanced or axial; 0 and 2 deg are the decision cases, 4, 10, 20 deg sensitivity.
usage: python -I retained_vapour_v341_v2p4.py DATA_V2P4_DIR BUDGET_JSON TRAPS_V341_JSON DRAIN_POSE_JSON BLEED_TAPS_JSON SERIES_CSV ATTITUDE_JSON OUT_JSON
"""
from __future__ import annotations
import gzip, hashlib, json, math, os, sys, time
sys.dont_write_bytecode = True
import numpy as np
import pandas as pd
from numba import njit
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import start_latency_v2p4 as SL
import reroute_vapour_v2p4 as RR

DT = 0.01            # coast step
DTP = 0.001          # purge step and heat-array resolution
GATE = 0.16          # E0 -> E1 maximum (torch gate)
T_CLOSE = 0.05       # purge ends 0.05 s before E0 (valves confirmed closed at E0)
W = 0.65
TP = (1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0)
TAPS = ('2tap', 'FD01')     # both taps (T4 + FD-01) or the FD-01 tap alone (T4 closed)
ORIF = (0.8, 1.0)
TILTS = (0.0, 2.0, 4.0, 10.0, 20.0)
DECISION_TILTS = (0.0, 2.0)   # LEAD 2026-10-13 design attitude theta <= 2 deg
AZS = (0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0)
G_V, G_L, CD = 15450.0, 56843.0, 0.70
C0 = 1.0
FR_VERT, FR_SHALLOW = 0.35, 0.63
F_RELIGHT = 1.14 * 9.80665   # m/s2, specific force at the hose station at RELIGHT, max of 500 runs (GNC relight_attitude_v1: 0.94-1.14 g)


def sha16(fn):
    return hashlib.sha256(open(fn, 'rb').read()).hexdigest()[:16]


@njit(cache=False)
def coast(qT, qH, qU, n_steps, k_dl, vpj, lpj, capT, H, Vseg, wet, snap_k):
    """10 ms volume balance; heat arrays at 1 ms (index 10 k + 5 = step midpoint). Returns final state and snapshots."""
    VU = 0.0; VH = 0.0; cap = 0.0; Rh = 0.0; Ru = 0.0; t_full = -1.0; void_dl = 0.0
    ns = snap_k.shape[0]
    snaps = np.zeros((ns, 3))
    for k in range(n_steps):
        for m in range(ns):
            if snap_k[m] == k:
                snaps[m, 0] = VU; snaps[m, 1] = VH; snaps[m, 2] = cap
        i = 10 * k + 5
        qt = qT[i]; qh = qH[i]; qu = qU[i]
        if k < k_dl:
            dV = vpj * qt * DT; room = capT - VU
            if dV <= room:
                VU += dV
            else:
                VU = capT
                if wet:
                    Rh += dV - room
                if t_full < 0:
                    t_full = (k + 0.5) * DT
            Rh += vpj * qh * DT; Ru += vpj * qu * DT
            tot = VU + Rh + Ru
            if tot > Vseg:
                sc = (Vseg - VU) / (Rh + Ru)
                Rh *= sc; Ru *= sc
            continue
        if k == k_dl:
            void_dl = VU + Rh + Ru
            VH = min(H, Rh); cap += (Rh - VH) + Ru; Rh = 0.0; Ru = 0.0
        # head trap
        over = 0.0
        if VU < capT:
            dV = vpj * qt * DT; room = capT - VU
            if dV <= room:
                VU += dV; q_ev = qt
            else:
                VU = capT; frac = room / dV
                over = (dV - room) if wet else 0.0
                q_ev = qt if wet else qt * frac
                if t_full < 0:
                    t_full = (k + 0.5) * DT
        else:
            over = vpj * qt * DT if wet else 0.0
            q_ev = qt if wet else 0.0
        # hose region: humps first
        inflow = vpj * qh * DT + over
        roomH = H - VH
        if inflow <= roomH:
            VH += inflow; Ah = 0.0
        else:
            VH = H; Ah = inflow - roomH
        A = Ah + vpj * qu * DT
        e = (vpj - lpj) * (q_ev + qh + qu)
        X = min(A + cap, e * DT)
        cap = cap + A - X
        if VU + VH + cap > Vseg:
            cap = max(Vseg - VU - VH, 0.0)
    return VU, VH, cap, t_full, snaps, void_dl


@njit(cache=False)
def purge(VU, VH, cap, capfl, capT, DEh, Dfp, FPh, VANN, Vseg, s, Qv, Ql, i0, n, Gd, Gu, qH, qU, vpj, wet, barrier, t4):
    """Bleed taps during the PURGE (MV open, pintle seated).  T4 (if open) vents the downstream crown region first (Ds);
    FD-01 vents the upstream queue from its own crown back to the tank: [U vap][L0 liq][VH vap][S liq][cap vap (flowing part)]
    [tank liq].  Each tap orifice passes vapour at Qv or liquid at Ql (volumetric, per tap); within a 1 ms step the orifice
    time is shared: local regrowth first, then the queue items in order (an item that runs out hands the rest of the step to
    the next one).  Once Ds is clear, T4 draws through the element: in the barrier model (wetted element = capillary barrier) it
    cannot draw upstream vapour and stops at a vapour front; in the open-element model it draws the front item.  With T4 closed
    the downstream regrowth collects at the T4 crown; vapour beyond the downstream volume passes the element to the FD-01 crown.
    Local generation: downstream (Gd) at T4, upstream (Gu + hose qH) at FD-01, the route above the hose (qU) into the cap while
    it exists.  'dry' stops generation only where the local front is vapour (Ds region, FD-01 crown); the liquid-wetted hose
    keeps generating.  Column flow Qcol = (vented - generated) per step = tank inflow; the cap moves at s Qcol, the liquid that
    overtakes it joins the slug ahead (while the cap is not at the front)."""
    VUfp = max(VU - DEh, 0.0)
    D = VUfp * Dfp / FPh
    U = VUfp - D
    Dsc = Dfp - VANN
    Ds = min(D, Dsc); Dann = D - Ds
    trap_full = VU >= capT - 1e-6
    L0 = 0.0 if trap_full else capT - VU
    S = max(Vseg - capT - VH - cap, 0.0)
    q = np.zeros(6)
    q[0] = U; q[1] = L0; q[2] = VH; q[3] = S; q[4] = capfl; q[5] = 1e9
    j = 0
    while j < 5 and q[j] <= 1e-12:
        j += 1
    rem_v = 0.0; rem_l = 0.0
    qmin_VH = 1e9; t_VH_out = -1.0; t_cap_out = -1.0
    ring = np.zeros(10); rsum = 0.0
    if q[2] <= 1e-12:
        t_VH_out = 0.0
    if q[4] <= 1e-12:
        t_cap_out = 0.0
    QvD = Qv * DTP; QlD = Ql * DTP
    for k in range(n):
        ii = i0 + k
        gd = Gd[ii] * vpj; gul = Gu[ii] * vpj; gh = qH[ii] * vpj; gc = qU[ii] * vpj
        v0 = rem_v + rem_l; gen = 0.0
        if j <= 4:
            q[4] += gc * DTP; gen += gc * DTP          # route bubbles above the hose join the cap while it exists
        else:
            gh += gc
        # ---------------- T4 tap (downstream of the element)
        if not t4:
            if wet or Ds <= 1e-12:
                Ds += gd * DTP; gen += gd * DTP
        else:
            tf = 1.0
            if Ds > 1e-12:
                if wet:
                    Ds += gd * DTP; gen += gd * DTP
                take = min(Ds, QvD)
                Ds -= take; rem_v += take; tf -= take / QvD
            else:
                gen += gd * DTP
                fl = gd / Qv
                if fl >= 1.0:
                    Ds += (gd - Qv) * DTP; rem_v += QvD; tf = 0.0
                else:
                    rem_v += gd * DTP; tf = 1.0 - fl
            while tf > 1e-12:
                fv = (j % 2 == 0) and j <= 4
                if fv and barrier:
                    break
                rate = QvD if fv else QlD
                take = min(q[j], rate * tf)
                q[j] -= take
                if fv:
                    rem_v += take
                else:
                    rem_l += take
                tf -= take / rate
                if q[j] <= 1e-12 and j < 5:
                    j += 1
                else:
                    break
        Dmax = Dfp - Dann
        if Ds > Dmax:
            # downstream region full of vapour: the excess passes the element (bubble point exceeded) to the FD-01 crown
            q[0] += Ds - Dmax; Ds = Dmax
            j = 0
        while j < 5 and q[j] <= 1e-12:
            j += 1
        # ---------------- FD-01 tap (upstream crown)
        fv = (j % 2 == 0) and j <= 4
        tf = 1.0
        if fv:
            add = (gul + gh) if wet else gh
            q[j] += add * DTP; gen += add * DTP
        else:
            g = gul + gh
            gen += g * DTP
            f = g / Qv
            if f >= 1.0:
                q[0] += (g - Qv) * DTP; rem_v += QvD; j = 0; tf = 0.0
            else:
                rem_v += g * DTP; tf = 1.0 - f
        while tf > 1e-12:
            fv = (j % 2 == 0) and j <= 4
            rate = QvD if fv else QlD
            take = min(q[j], rate * tf)
            q[j] -= take
            if fv:
                rem_v += take
            else:
                rem_l += take
            tf -= take / rate
            if q[j] <= 1e-12 and j < 5:
                j += 1
            else:
                break
        while j < 5 and q[j] <= 1e-12:
            j += 1
        Qcol = max((rem_v + rem_l - v0 - gen) / DTP, 0.0)
        rsum += Qcol - ring[k % 10]; ring[k % 10] = Qcol
        if j <= 2 and q[2] > 1e-9 and k >= 10:
            if rsum / 10.0 < qmin_VH:
                qmin_VH = rsum / 10.0
        if t_VH_out < 0.0 and j > 2:
            t_VH_out = (k + 1) * DTP
        if t_cap_out < 0.0 and j > 4:
            t_cap_out = (k + 1) * DTP
        # ---------------- cap slip
        if j < 4 and s < 1.0:
            q[3] += (1.0 - s) * Qcol * DTP
    out = np.zeros(13)
    out[0] = Dann; out[1] = Ds
    for m in range(6):
        out[2 + m] = q[m] if m >= j else 0.0
    out[8] = rem_v; out[9] = rem_l; out[10] = qmin_VH; out[11] = t_VH_out; out[12] = t_cap_out
    return out


def sorted_eval(bs, tl, PURGE, DEAD, P1, S1, C1, S2, C2, conv):
    """P(E1 -> E2 > W) for the sequence [P1 vap][S1 liq][C1 vap][S2 liq][C2 vap][tank liq], bs = sorted base (lift + ig + conf)."""
    N = bs.size
    K0, K1, K2 = PURGE * P1, PURGE * C1, PURGE * C2
    t1, t2 = S1 * DEAD, S2 * DEAD

    def cnt(lo, hi, thr):           # # of b in (lo, hi] with b > thr
        a = max(lo, thr)
        if hi <= a:
            return 0
        return int(np.searchsorted(bs, hi, 'right') - np.searchsorted(bs, a, 'right'))
    inf = float('inf')
    B1 = tl + t1
    if conv == 'paused':
        B2 = tl + t1 + t2
        c = cnt(-inf, B1, W - K0) + cnt(B1, B2, W - K0 - K1) + cnt(B2, inf, W - K0 - K1 - K2)
    else:
        B2 = tl + t2
        if B2 > B1:
            c = cnt(-inf, B1, W - K0) + cnt(B1, B2, W - K0 - t1 - K1) + cnt(B2, inf, W - K0 - t1 - K1 - t2 - K2)
        else:
            c = cnt(-inf, B1, W - K0) + cnt(B1, inf, W - K0 - t1 - K1 - t2 - K2)
    return c / N


def vector_eval(base, tl, PURGE, DEAD, P1, S1, C1, S2, C2, conv):
    n = base - tl; t1, t2 = S1 * DEAD, S2 * DEAD
    if conv == 'paused':
        e = base + PURGE * P1 + np.where(n > t1, PURGE * C1, 0.0) + np.where(n > t1 + t2, PURGE * C2, 0.0)
    else:
        e = base + PURGE * P1 + np.where(n > t1, t1 + PURGE * C1 + np.where(n > t2, t2 + PURGE * C2, 0.0), 0.0)
    return float(np.mean(e > W))


def sequence(items):
    """items: list of (phase, volume) from the seat back; merge, drop empties; return P1, S1, C1, S2, C2 (later gaps merged)."""
    seq = []
    for ph, v in items:
        if v <= 1e-9:
            continue
        if seq and seq[-1][0] == ph:
            seq[-1][1] += v
        else:
            seq.append([ph, v])
    if not seq or seq[0][0] != 'v':
        seq.insert(0, ['v', 0.0])
    vals = [x[1] for x in seq] + [0.0] * 5
    P1, S1, C1, S2 = vals[0], vals[1], vals[2], vals[3]
    C2 = sum(vals[4::2]) if len(seq) > 4 else (vals[4] if len(seq) > 4 else 0.0)
    if len(seq) > 5:      # a third gap or more: merge all remaining vapour into C2 and drop the slugs between (conservative)
        C2 = sum(x[1] for x in seq[4:] if x[0] == 'v')
    return P1, S1, C1, S2, C2


def main(d, budget_f, traps_f, pose_f, taps_f, series_f, att_f, out_f):
    t_start = time.time()
    VO = json.load(open(os.path.join(d, 'relight_vapour_order_v2p4.json')))
    MG = json.load(open(os.path.join(d, 'coast_migration_v2p4.json')))
    J = json.load(open(os.path.join(d, 'start_latency_v2p4.json')))
    PA = json.load(open(os.path.join(d, 'post_abort_pocket_v2p4.json')))
    HV = json.load(open(os.path.join(d, 'segment_heat_v341_v2p4.json')))
    B = json.load(open(budget_f)); TR = json.load(open(traps_f)); PO = json.load(open(pose_f)); BT = json.load(open(taps_f)); AT = json.load(open(att_f))
    p = VO['properties']; vpj, lpj = p['vap_cm3_per_J'], p['liq_cm3_per_J']; rho_l, rho_v = p['rho_l'], p['rho_v']
    PURGE = VO['purge_s_per_cm3']; DEAD = VO['liquid_plug_dead_time_s_per_cm3']
    t_meco = float(B['t_meco_s']); T_m = float(B['coast_s'])
    # ------------------------------------------------------------------ volumes
    RS = TR['retained_split_nominal']
    vol = {}
    for m, key in (('barrier', 'MV_closed|barrier|+Z'), ('open', 'MV_closed|open_element|+Z')):
        r = RS[key]
        vol[m] = dict(Vseg=TR['segment_volume_cm3']['MV_closed_barrier_model' if m == 'barrier' else 'MV_closed_element_pores_open'],
                      FP=r['retained_flow_path_cm3'], Up=r['upstream_of_element_flow_path_cm3'], Dn=r['downstream_of_element_flow_path_cm3'],
                      DE=r['retained_dead_end_cm3'])
    lhp = TR['local_high_points']['MV_closed|barrier|vent S1']
    DE_mod = sum(x['own_vol_cm3'] for x in lhp if x['kind'] == 'dead' and x['peak_at'].startswith(('J602', 'balance')))
    VANN = TR['segment_volume_by_primitive_cm3']['TC-03/TC-02/TC-04 manifold bore (annulus around the needle)']
    for m in vol:
        vol[m]['DE_mod'] = DE_mod; vol[m]['DE_head'] = max(vol[m]['DE'] - DE_mod, 0.0); vol[m]['VANN'] = VANN
        assert abs(vol[m]['Up'] + vol[m]['Dn'] - vol[m]['FP']) < 1e-3
    # humps: voxel at 10 deg per direction, proxy-scaled at 2 and 4
    vox10 = {}; vox20 = {}
    for r in TR['tilt_sensitivity']:
        mm = 'barrier' if r['model'] == 'barrier' else 'open'
        if r['tilt_deg'] == 10.0:
            vox10[(mm, float(r['toward_az_deg']))] = r['split']['retained_flow_path_cm3']
        elif r['tilt_deg'] == 20.0:
            vox20[(mm, float(r['toward_az_deg']))] = r['split']['retained_flow_path_cm3']
    prox = {(float(r['tilt_deg']), float(r['toward_az_deg'])): r['neutral']['total_cm3'] for r in PO['rows']}
    p0 = prox[(0.0, 0.0)]
    H = {}
    for m in vol:
        for az in AZS:
            dv10 = vox10[(m, az)] - vol[m]['FP']; dp10 = prox[(10.0, az)] - p0
            k = dv10 / dp10 if dp10 > 0.05 else 1.0
            H[(m, 0.0, az)] = 0.0
            H[(m, 10.0, az)] = max(dv10, 0.0)
            H[(m, 20.0, az)] = max(vox20[(m, az)] - vol[m]['FP'], 0.0)      # voxel directly (no drain-pose proxy at 20 deg)
            for th in (2.0, 4.0):
                H[(m, th, az)] = max(k * (prox[(th, az)] - p0), 0.0)
    # ------------------------------------------------------------------ heat arrays (1 ms from MECO)
    Tw_max = max(sv['window_s'] for sv in MG['series'].values())
    tgrid = np.arange(0.0, Tw_max + 0.6, DTP)
    HE = B['head_end_W_vs_t']['v']
    el = {(r['key'], r['lining_mm']): r for r in HV['elements']}
    heat = {}
    for case in HE:
        fam = case.split('|')[1]
        th_ = np.array(HE[case]['t_s']) - t_meco
        sp = HE[case]['split_W']
        fe_key = [k for k in sp if k.startswith('FE manifold bore')][0]
        f = {nm: RR.series_fn(th_, sp[k]) for nm, k in (('fe', fe_key), ('fd01', 'FD-01'), ('tc02', 'TC-02'), ('tc04', 'TC-04'))}
        E_n = B['needle']['E_J'][0 if fam == 'LO' else 1]
        a_n = E_n / (RR.TAU_NEEDLE * (1 - math.exp(-T_m / RR.TAU_NEEDLE)))
        arr = {nm: np.array([fn(t) for t in tgrid]) for nm, fn in f.items()}
        arr['needle'] = a_n * np.exp(-tgrid / RR.TAU_NEEDLE)
        for lin in (0.0, 1.0):
            ser = {}
            for key in ('module', 'fd08f', 'wall', 'sleeves', 'hose', 'tee', 'riser'):
                r = el.get((key, lin)) or el[(key, 0.0)]
                te = np.array(r['Q_coast_t_s']) - t_meco
                fn = RR.series_fn(te, r['Q_coast_W'][case])
                ser[key] = np.array([fn(t) for t in tgrid])
            Gd = arr['fe'] + arr['tc04'] + 0.5 * arr['tc02'] + arr['needle']
            Gu = arr['fd01'] + 0.5 * arr['tc02'] + ser['riser'] + 0.5 * ser['tee']
            heat[(case, lin)] = dict(qT=Gd + Gu, qH=ser['hose'] + ser['sleeves'] + 0.5 * ser['tee'], qU=ser['module'] + ser['fd08f'] + ser['wall'],
                                     Gd=Gd, Gu=Gu)
    trap_int = getattr(np, 'trapezoid', None) or getattr(np, 'trapz')
    heat_chk = {f'{c}|lin{l}': {k: float(trap_int(v[tgrid <= T_m], tgrid[tgrid <= T_m])) for k, v in hh.items() if k in ('qT', 'qH', 'qU')}
                for (c, l), hh in heat.items()}
    # ------------------------------------------------------------------ ignition distribution
    rws = J['part1_runs']['v']; lifts = J['ignition_lifts']
    pool = [r for r in rws if r['ramp'] == 2500.0 and r['F_cmd'] in (200.0, 500.0) and r['state'] == 'A1_relight'
            and r['frac'] == 0.125 and r.get('loop_K', 0.0) == 15.0]
    N = 200000; rng = np.random.default_rng(2024)
    h = lifts['A1_relight|0.125']['lift_m']; t_lift = SL.T_CMD + h / SL.V_PINTLE + 0.010
    idx = rng.integers(0, len(pool), N)
    tc = np.array([np.nan if q['t_conf_s'] is None else q['t_conf_s'] for q in pool])[idx]
    _ = rng.uniform(0.005, 0.020, N) + rng.uniform(0.02, 0.10, N) + rng.uniform(0.005, 0.030, N)
    ig = rng.uniform(0.05, 0.30, N)
    base = t_lift + ig + tc; base = base[np.isfinite(base)]
    assert abs(float(base.max()) - PA['E1_E2_liquid_s']['max']) < 1e-9
    bs = np.sort(base)
    # evaluator check against the vectorised form
    rng2 = np.random.default_rng(7)
    for _ in range(300):
        P1, S1, C1, S2, C2 = rng2.uniform(0, 20), rng2.choice([0.0, rng2.uniform(0, 15)]), rng2.uniform(0, 15), rng2.choice([0.0, rng2.uniform(0, 15)]), rng2.uniform(0, 10)
        for conv in ('paused', 'restart'):
            a_ = sorted_eval(bs, t_lift, PURGE, DEAD, P1, S1, C1, S2, C2, conv)
            b_ = vector_eval(base, t_lift, PURGE, DEAD, P1, S1, C1, S2, C2, conv)
            assert abs(a_ - b_) < 1e-12, (P1, S1, C1, S2, C2, conv, a_, b_)
    Vzero = (W - float(base.max())) / PURGE
    # ------------------------------------------------------------------ slip from drift
    gp = F_RELIGHT * (rho_l - rho_v) / rho_l
    A_hose = math.pi / 4 * (HV['geometry']['hose_D_mm'] * 1e-3) ** 2; D_hose = HV['geometry']['hose_D_mm'] * 1e-3
    A_wall = math.pi / 4 * 7.747e-3 ** 2
    flows, s_phys = {}, {}
    for o in ORIF:
        A = math.pi / 4 * (o * 1e-3) ** 2
        Qv = CD * A * G_V / rho_v * 1e6; Ql = CD * A * G_L / rho_l * 1e6
        for taps, nt in (('2tap', 2), ('FD01', 1)):
            Qcol_l = nt * Ql * 1e-6
            u_h = Qcol_l / A_hose; u_w = Qcol_l / A_wall
            ud_h = FR_SHALLOW * math.sqrt(gp * D_hose); ud_w = FR_VERT * math.sqrt(gp * 7.747e-3)
            s_h = max(C0 - ud_h / u_h, 0.0); s_w = max(C0 - ud_w / u_w, 0.0)
            key = f'{o}|{taps}'
            s_phys[key] = dict(scons=round(min(s_h, s_w), 3), swall=round(s_w, 3))
            flows[key] = dict(n_taps=nt, Q_vapour_cm3_s_per_tap=Qv, Q_liquid_cm3_s_per_tap=Ql, mdot_vapour_g_s_per_tap=Qv * rho_v * 1e-3,
                              mdot_liquid_g_s_per_tap=Ql * rho_l * 1e-3, liquid_g_s_all_taps=nt * Ql * rho_l * 1e-3,
                              fraction_of_100pct_flow=nt * Ql * rho_l * 1e-3 / 264.08,
                              hose_u_liquid_m_s=u_h, hose_u_drift_shallow_m_s=ud_h, hose_Fr_prime=u_h / math.sqrt(gp * D_hose), s_hose=s_h,
                              wall_u_liquid_m_s=u_w, wall_u_drift_vertical_m_s=ud_w, s_wall=s_w, s_cons=s_phys[key]['scons'],
                              hump_sweep_min_liquid_g_s=ud_h / C0 * A_hose * rho_l * 1e3)
    # ------------------------------------------------------------------ purge-model sanity check (no heat, analytic phases)
    nz = np.zeros(200000)
    Vt = vol['barrier']; capT_ = Vt['FP'] + Vt['DE_head']
    Qv8 = flows['0.8|2tap']['Q_vapour_cm3_s_per_tap']; Ql8 = flows['0.8|2tap']['Q_liquid_cm3_s_per_tap']
    for s_chk in (1.0, 0.7):
        oc = purge(0.0, 5.0, 10.0, 10.0, capT_, Vt['DE_head'], Vt['Dn'], Vt['FP'], Vt['VANN'], Vt['Vseg'], s_chk, Qv8, Ql8, 0, 150000,
                   nz, nz, nz, nz, vpj, True, True, True)
        L0c = capT_; Sc = Vt['Vseg'] - capT_ - 15.0
        t1 = L0c / (2 * Ql8); t2 = 5.0 / Qv8; S_ = Sc + (1 - s_chk) * (L0c + 5.0); t3 = S_ / (2 * Ql8 * s_chk); t4 = 10.0 / Qv8
        assert abs(oc[11] - (t1 + t2)) < 0.002 and abs(oc[12] - (t1 + t2 + t3 + t4)) < 0.004, (s_chk, oc[11], t1 + t2, oc[12], t1 + t2 + t3 + t4)
        # FD-01 alone: liquid at Ql, vapour at Qv, same order
        oc1 = purge(0.0, 5.0, 10.0, 10.0, capT_, Vt['DE_head'], Vt['Dn'], Vt['FP'], Vt['VANN'], Vt['Vseg'], s_chk, Qv8, Ql8, 0, 150000,
                    nz, nz, nz, nz, vpj, True, True, False)
        u1 = L0c / Ql8; u2 = 5.0 / Qv8; S1_ = Sc + (1 - s_chk) * (L0c + 5.0); u3 = S1_ / (Ql8 * s_chk); u4 = 10.0 / Qv8
        assert abs(oc1[11] - (u1 + u2)) < 0.002 and abs(oc1[12] - (u1 + u2 + u3 + u4)) < 0.004, (s_chk, oc1[11], u1 + u2, oc1[12], u1 + u2 + u3 + u4)
    # ------------------------------------------------------------------ runs
    cases = list(HE.keys())
    res = {}
    att = [(0.0, 0.0)] + [(th, az) for th in TILTS[1:] for az in AZS]
    for case in cases:
        for lin in (0.0, 1.0):
            hh = heat[(case, lin)]
            for m in ('barrier', 'open'):
                V = vol[m]
                capT = V['FP'] + V['DE_head']
                for sname, sv in MG['series'].items():
                    Tw = sv['window_s']; t_dl = Tw - sv['t_from_drogue_load_s']
                    n_steps = int(round(Tw / DT)); k_dl = int(round(t_dl / DT))
                    t_end = Tw - T_CLOSE
                    snap_t = [t_end - Tp for Tp in TP]
                    snap_k = np.array([int(round(t / DT)) for t in snap_t], dtype=np.int64)
                    assert k_dl < int(snap_k.min()), 'a purge would start before the drogue load'
                    ig_ = int(round(Tw / DTP)); ng = int(round(GATE / DTP))
                    gT = vpj * float(np.mean(hh['qT'][ig_:ig_ + ng])) * GATE
                    gH = vpj * float(np.mean(hh['qH'][ig_:ig_ + ng])) * GATE
                    gU = vpj * float(np.mean(hh['qU'][ig_:ig_ + ng])) * GATE
                    ie = int(round(t_end / DTP)); nr = int(round((T_CLOSE + GATE) / DTP))
                    regp = vpj * float(np.mean(hh['qT'][ie:ie + nr] + hh['qH'][ie:ie + nr])) * (T_CLOSE + GATE)
                    for (th, az) in att:
                        Hv = H[(m, th, az)]
                        for wet in (True, False):
                            tag = 'wet' if wet else 'dry'
                            VU, VH, cap, t_full, snaps, void_dl = coast(hh['qT'], hh['qH'], hh['qU'], n_steps, k_dl, vpj, lpj, capT, Hv, V['Vseg'], wet, snap_k)
                            # ---- no purge (v2.8 sequence): regrowth from E0 to E1 (gate): trap room first, overflow (wet) and
                            #      hose regrowth join the hump gap, route regrowth joins the cap
                            L0 = max(capT - VU, 0.0)
                            toT = min(gT, L0); ovT = (gT - toT) if wet else 0.0
                            VUfp = max(VU - V['DE_head'], 0.0) + toT; L0 -= toT
                            VHr = VH + ovT + gH; capr = cap + gU
                            S = max(V['Vseg'] - capT - VHr - capr, 0.0)
                            P1, S1, C1, S2, C2 = sequence([('v', VUfp), ('l', L0), ('v', VHr), ('l', S), ('v', max(capr - V['DE_mod'], 0.0))])
                            rec = dict(VU=VU, VH=VH, cap=cap, H=Hv, t_trap_full=t_full, void_at_drogue_load=void_dl, P1=P1, S1=S1, C1=C1, S2=S2, C2=C2,
                                       P_paused=sorted_eval(bs, t_lift, PURGE, DEAD, P1, S1, C1, S2, C2, 'paused'),
                                       P_restart=sorted_eval(bs, t_lift, PURGE, DEAD, P1, S1, C1, S2, C2, 'restart'))
                            res[f'nopurge|lin{lin}|{m}|{case}|{tag}|{th}|{az}|{sname}'] = rec
                            # ---- purge
                            for o in ORIF:
                                for taps in TAPS:
                                    fk = f'{o}|{taps}'
                                    Qv = flows[fk]['Q_vapour_cm3_s_per_tap']; Ql = flows[fk]['Q_liquid_cm3_s_per_tap']
                                    sc, sw = s_phys[fk]['scons'], s_phys[fk]['swall']
                                    if th in DECISION_TILTS or az == 45.0:
                                        slips = (('scons', sc), ('swall', sw), ('s1.0', 1.0), ('s0.5', 0.5))
                                    else:
                                        slips = (('scons', sc),)
                                    for iTp, Tp in enumerate(TP):
                                        VU0, VH0, cap0 = snaps[iTp]
                                        i0 = int(round((t_end - Tp) / DTP)); n = int(round(Tp / DTP))
                                        for slab, s in slips:
                                            o_ = purge(VU0, VH0, cap0, max(cap0 - V['DE_mod'], 0.0), capT, V['DE_head'], V['Dn'], V['FP'], V['VANN'], V['Vseg'],
                                                       s, Qv, Ql, i0, n, hh['Gd'], hh['Gu'], hh['qH'], hh['qU'], vpj, wet, m == 'barrier', taps == '2tap')
                                            r = dict(N2O_g=o_[8] * rho_v * 1e-3 + o_[9] * rho_l * 1e-3, vented_vap_cm3=o_[8], vented_liq_cm3=o_[9],
                                                     annulus_cm3=o_[0], Ds_left_cm3=o_[1], U_left=o_[2], VH_left=o_[4], cap_left=o_[6],
                                                     Qcol_min_while_humps_cm3_s=(o_[10] if o_[10] < 1e8 else None), t_VH_out=o_[11], t_cap_out=o_[12],
                                                     regrowth_cm3=regp)
                                            for lab, ann in (('', o_[0]), ('_annvent', 0.0)):
                                                items = [('v', ann + o_[1] + regp), ('v', o_[2]), ('l', o_[3]), ('v', o_[4]), ('l', o_[5]),
                                                         ('v', o_[6]), ('l', 1.0)]
                                                P1, S1, C1, S2, C2 = sequence(items)
                                                r['seq' + lab] = [P1, S1, C1, S2, C2]
                                                r['P_paused' + lab] = sorted_eval(bs, t_lift, PURGE, DEAD, P1, S1, C1, S2, C2, 'paused')
                                                r['P_restart' + lab] = sorted_eval(bs, t_lift, PURGE, DEAD, P1, S1, C1, S2, C2, 'restart')
                                            r['P1'] = r['seq'][0]
                                            res[f'purge{o}|{taps}|{slab}|Tp{Tp}|lin{lin}|{m}|{case}|{tag}|{th}|{az}|{sname}'] = r
            print(case, 'lin', lin, 'done', round(time.time() - t_start, 1), 's', flush=True)
    # ------------------------------------------------------------------ summaries (max over the five series)
    summ = {}
    for k, r in res.items():
        parts = k.split('|')
        key = '|'.join(parts[:-1])
        s_ = summ.setdefault(key, dict(P_paused=0.0, P_restart=0.0, P1=[1e9, 0.0]))
        s_['P_paused'] = max(s_['P_paused'], r['P_paused']); s_['P_restart'] = max(s_['P_restart'], r['P_restart'])
        s_['P1'] = [min(s_['P1'][0], r['P1']), max(s_['P1'][1], r['P1'])]
        if 'N2O_g' in r:
            for kk in ('N2O_g', 't_cap_out', 't_VH_out', 'cap_left', 'VH_left'):
                v = r[kk]
                s_.setdefault(kk, [1e9, -1e9])
                s_[kk] = [min(s_[kk][0], v), max(s_[kk][1], v)]
            s_['P_paused_annvent'] = max(s_.get('P_paused_annvent', 0.0), r['P_paused_annvent'])
            s_['P_restart_annvent'] = max(s_.get('P_restart_annvent', 0.0), r['P_restart_annvent'])
            qm = r['Qcol_min_while_humps_cm3_s']
            if qm is not None:
                s_['Qcol_min_while_humps_cm3_s'] = min(s_.get('Qcol_min_while_humps_cm3_s', 1e9), qm)
        else:
            for kk in ('VU', 'VH', 'cap', 'C1', 'C2'):
                s_.setdefault(kk, [1e9, -1e9])
                s_[kk] = [min(s_[kk][0], r[kk]), max(s_[kk][1], r[kk])]
    sweep_min_cm3_s = {f'{g_:.2f}': FR_SHALLOW * math.sqrt(g_ * (rho_l - rho_v) / rho_l * D_hose) * A_hose * 1e6 for g_ in (F_RELIGHT, 9.80665)}
    out = dict(version='v2.4', date='2026-10-13', script='02-combustion/src/retained_vapour_v341_v2p4.py', script_sha256_16=sha16(os.path.abspath(__file__)),
               inputs={'segment_heat_v341_v2p4.json': sha16(os.path.join(d, 'segment_heat_v341_v2p4.json')),
                       'relight_vapour_order_v2p4.json': sha16(os.path.join(d, 'relight_vapour_order_v2p4.json')),
                       'coast_migration_v2p4.json': sha16(os.path.join(d, 'coast_migration_v2p4.json')),
                       'start_latency_v2p4.json': sha16(os.path.join(d, 'start_latency_v2p4.json')),
                       'post_abort_pocket_v2p4.json': sha16(os.path.join(d, 'post_abort_pocket_v2p4.json')),
                       'mech_budget': dict(file=budget_f, sha256_16=sha16(budget_f)), 'mech_traps_v341': dict(file=traps_f, sha256_16=sha16(traps_f)),
                       'mech_drain_pose_v341 (workdir)': dict(file=pose_f, sha256_16=sha16(pose_f)),
                       'mech_bleed_taps_v341 (workdir)': dict(file=taps_f, sha256_16=sha16(taps_f)),
                       'gnc_series': dict(file=series_f, sha256_16=sha16(series_f)),
                       'gnc_relight_attitude_v1': dict(file=att_f, sha256_16=sha16(att_f))},
               constants=dict(DT=DT, DTP=DTP, GATE=GATE, T_CLOSE=T_CLOSE, W=W, TP=TP, ORIF=ORIF, C0=C0, FR_VERT=FR_VERT, FR_SHALLOW=FR_SHALLOW,
                              F_RELIGHT=F_RELIGHT, PURGE_s_per_cm3=PURGE, DEAD_s_per_cm3=DEAD, V_zero_abort_cm3=Vzero, t_lift_s=t_lift,
                              hump_sweep_min_column_flow_cm3_s=sweep_min_cm3_s, TAPS=TAPS),
               volumes=vol, humps_cm3={f'{m}|{th}|{az}': v for (m, th, az), v in H.items()}, proxy_neutral=dict((f'{a}|{b}', v) for (a, b), v in prox.items()),
               bleed_taps_summary=BT['summary'], flows=flows, s_phys=s_phys, heat_integrals_J=heat_chk,
               summary_nopurge={k: v for k, v in summ.items() if k.startswith('nopurge')},
               summary_file=os.path.basename(out_f).replace('.json', '_summary.json.gz') + ' (all keys incl. purge; max over the five series)',
               gnc_attitude_at_RELIGHT_deg={k: AT['results'][k]['theta_hose_deg']['at_RELIGHT'] for k in AT['results']},
               gnc_fmag_g_at_RELIGHT={k: AT['results'][k]['fmag_g_hose']['at_RELIGHT'] for k in AT['results']},
               design_attitude='LEAD 2026-10-13: theta <= 2 deg (vent balanced or axial); 0 and 2 deg decision cases; 4, 10, 20 deg sensitivity',
               raw_file=os.path.basename(out_f) + '.raw.json.gz (per series; workdir only; regenerate with this script)',
               tags=dict(model='DERIVED volume balance on Mechanical DERIVED v3.4.1 volumes and Mechanical-method heat (ESTIMATE); GNC SIM windows',
                         ignition='SIM on ASSUMED delays', purge='DERIVED plug flow with cap slip s (drift forms LITERATURE as recalled, TO-VERIFY)',
                         humps='2 and 4 deg from the path-pocket proxy scaled to the 10 deg voxel per direction (Mechanical drain_pose_v341 neutral rows); 10 and 20 deg voxel (segment_traps_v341 tilt_sensitivity)'))
    def rnd(x):
        if isinstance(x, float):
            return float('%.6g' % x)
        if isinstance(x, dict):
            return {k: rnd(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            return [rnd(v) for v in x]
        return x
    with gzip.open(out_f + '.raw.json.gz', 'wt') as fh:
        json.dump(dict(script_sha256_16=out['script_sha256_16'], cases=rnd(res)), fh, separators=(',', ':'))
    sf = out_f.replace('.json', '_summary.json.gz')
    with gzip.open(sf, 'wt') as fh:
        json.dump(dict(script_sha256_16=out['script_sha256_16'], summary=rnd(summ)), fh, separators=(',', ':'))
    out['summary_file_sha256_16'] = sha16(sf)
    json.dump(out, open(out_f, 'w'), indent=1, default=float)
    print('V zero-abort %.3f cm3' % Vzero, 'flows', json.dumps(flows, default=float))
    print('wrote', out_f, sha16(out_f), round(time.time() - t_start, 1), 's')


if __name__ == '__main__':
    main(*sys.argv[1:9])

"""Retention-lip and case temperatures at RELIGHT after the MECO coast, and the post-landing soak (Combustion v2,
2026-10-12). Lead request 2026-10-12 (CHANGELOG 'thermal OI-4/OI-5'): governing thermal-structural cases are
  TS-1 lip / aft-land temperature at RELIGHT after the MECO coast, combined with Pc 25 bar (normal) and 45 bar (MEOP),
  TS-2 post-landing soak peak, unloaded, judged against permanent strength loss of 6061-T6 (over-ageing) for reuse.
This script supplies the temperatures and times only; the allowables and the strength-loss judgement are Mechanical's.

Inputs: S230 duty-cycle histories from grain_q1d v2 (columns t, Pc, mox, OF). Burn segments = (mox > 1e-4) & (Pc > 1.5 bar);
MECO = end of the first segment, relight = start of the second, coast = relight - MECO. The coast is explicit in every DC
CSV (data/v2/dc_g3/*.csv for gnc.json v1 cycles, data/v2/dc_gncv2wip/*.csv for the GNC v2 working-copy preview).
Single-burn cycles (B1, B2) have no relight; only TS-2 applies to them.
Models (unchanged, SIM, sizing check only; Mechanical thermal FEA supersedes):
  insert: nozzle.ThroatInsert through the history (dt 5 ms). During coasts the bore and the retainer are ADIABATIC in this
          model (no radiation or bay loss): conservative for the temperature at relight. Post-landing soak: soakback.insert_soak
          (bore radiation eps*F 0.25, retainer h 15 W/m2K + eps 0.3 radiation over 6.3e-3 m2) for 3600 s so that the time
          at temperature (over-ageing input) is not truncated at 900 s. Retainer = lumped mass (BRACKETS: Al 0.15/0.30/0.60 kg
          c 900, steel 0.30 kg c 500), interface hc 150 / 2000 W/m2K.
  wall:   soakback.wall_stack_dc (phenolic L 1.6/3/5 mm + 3.175 mm 6061, h_g = h_max (Pc/25 bar)^0.8 while burning,
          h_max 920 W/m2K x1 / x2, T_aw 2703 K, adiabatic gas side when not burning, bay h 10 W/m2K, 3600 s soak).
Allowables are NOT applied here: 240 C is the Mechanical v3.1 limit for the aluminium lip at 51 MPa (BN bound) and 192 C
for the aluminium aft land; a steel part needs its own temperature-dependent allowable (lead note 2026-10-12).
Outputs: OUTDIR/soakback_relight_v2.json, OUTDIR/soakback_relight_v2.csv.
usage: python soakback_relight.py OUTDIR DC1.csv [DC2.csv ...]   (paths relative to the CWD)
"""
from __future__ import annotations
import json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nozzle as N
from soakback import insert_soak, wall_stack_dc, TA

T_SOAK = 3600.0                                  # s, post-landing soak window
THRESH_C = (150.0, 200.0, 240.0, 300.0)          # C, time-above thresholds reported for the over-ageing judgement


def segments(t, on):
    seg = []; i = 0; n = len(t)
    while i < n:
        if on[i]:
            j = i
            while j + 1 < n and on[j + 1]:
                j += 1
            seg.append((float(t[i]), float(t[j]), i, j)); i = j + 1
        else:
            i += 1
    return seg


def time_above(ts, Ts, dt_rec):
    """Seconds above each threshold in a soak record (uniform record spacing dt_rec) and whether still above at the end."""
    Ts = np.asarray(Ts)
    out = {}
    for c in THRESH_C:
        k = c + 273.15
        out[f't_above_{c:.0f}C_s'] = float((Ts > k).sum() * dt_rec)
        out[f'above_{c:.0f}C_at_end'] = bool(Ts[-1] > k)
    return out


def main(outdir, files):
    TP = N.ThroatProps()
    rows = []; meta = {}
    for fn in files:
        r = pd.read_csv(fn)
        t = r.t.values; Pc = r.Pc.values; OF = r.OF.values; on = (r.mox.values > 1e-4) & (Pc > 1.5e5)
        seg = segments(t, on)
        name = os.path.basename(fn).replace('.csv', '')
        if not seg:
            meta[name] = dict(source=fn, note='no burn found'); continue
        relight = len(seg) >= 2
        t_meco = seg[0][1] if relight else None
        t_rl = seg[1][0] if relight else None
        i2a, i2b = seg[-1][2], seg[-1][3]                     # landing burn = last segment (single burn for B cycles)
        i_pcmax = i2a + int(np.argmax(Pc[i2a:i2b + 1]))
        t_lb0, t_end = seg[-1][0], seg[-1][1]
        meta[name] = dict(source=fn, burns_s=[[round(a, 3), round(b, 3)] for a, b, _, _ in seg],
                          t_MECO_s=t_meco, t_relight_s=t_rl, coast_s=(round(t_rl - t_meco, 3) if relight else None),
                          t_last_shutdown_s=t_end, Pc_max_landing_burn_Pa=float(Pc[i_pcmax]), t_Pc_max_landing_burn_s=float(t[i_pcmax]),
                          Pc_relight_plus_0p5s_Pa=(float(Pc[min(np.searchsorted(t, t_rl + 0.5), len(t) - 1)]) if relight else None),
                          note=('relight after coast (TS-1 and TS-2)' if relight else 'single burn: no relight (TS-2 only)'))
        # ---------------- insert + retainer ----------------
        for mat, msl, csl in (('Al', 0.15, 900.0), ('Al', 0.30, 900.0), ('Al', 0.60, 900.0), ('steel', 0.30, 500.0)):
            for hc in (2000.0, 150.0):
                ins = N.ThroatInsert(T0=TA, hc=hc, m_sleeve=msl, c_sleeve=csl)
                tn = t[0]; dtb = 5e-3; Ts_meco = Ts_rl = None; Ts_max2 = TA; Pc_at_Tmax = None; T_at_Pcmax = None
                while tn <= t_end + 1e-9:
                    i = min(np.searchsorted(t, tn), len(t) - 1)
                    ins.step(dtb, float(Pc[i]), float(OF[i]) if np.isfinite(OF[i]) else 5.0, TP, bool(on[i]))
                    if relight and Ts_meco is None and tn >= t_meco:
                        Ts_meco = ins.Ts
                    if relight and Ts_rl is None and tn >= t_rl:
                        Ts_rl = ins.Ts
                    if tn >= t_lb0:
                        if ins.Ts >= Ts_max2:
                            Ts_max2 = ins.Ts; Pc_at_Tmax = float(Pc[i])
                        if T_at_Pcmax is None and tn >= t[i_pcmax]:
                            T_at_Pcmax = ins.Ts
                    tn += dtb
                Ts_sd = ins.Ts
                hist = insert_soak(ins, t_soak=T_SOAK)
                pk = max(hist, key=lambda h: h['T_retainer'])
                Tr = [h['T_retainer'] for h in hist]; tr = np.array([h['t_after_shutdown'] for h in hist])
                row = dict(duty_cycle=name, part='retainer_lip', bracket=f'{mat} {msl:.2f} kg', hc_W_m2K=hc,
                           coast_s=(t_rl - t_meco if relight else None),
                           T_at_MECO_K=Ts_meco, T_at_relight_K=Ts_rl, T_at_Pcmax_landing_burn_K=T_at_Pcmax,
                           T_max_landing_burn_K=Ts_max2, Pc_at_Tmax_landing_burn_Pa=Pc_at_Tmax, T_at_last_shutdown_K=Ts_sd,
                           T_post_landing_peak_K=pk['T_retainer'], t_post_peak_after_shutdown_s=pk['t_after_shutdown'],
                           T_900s_K=float(np.interp(900.0, tr, Tr)), T_3600s_K=float(Tr[-1]))
                row.update(time_above(tr, Tr, 1.0))
                rows.append(row)
                print(json.dumps({k: (round(v, 1) if isinstance(v, float) else v) for k, v in row.items()}), flush=True)
        # ---------------- post-chamber wall / aft land ----------------
        for L_ph in (1.6e-3, 3.0e-3, 5.0e-3):
            for fac in (1.0, 2.0):
                hist, t_last = wall_stack_dc(t, Pc, on, 920.0 * fac, 2845.0 * 0.95, L_ph, t_soak=T_SOAK)
                hh = pd.DataFrame(hist)
                at = lambda tq: float(np.interp(tq, hh.t, hh.T_case_outer))
                m2 = (hh.t >= t_lb0) & (hh.t <= t_last)
                post = hh[hh.t >= t_last]
                if m2.any():
                    k2 = hh.T_case_outer[m2].idxmax(); Tmax2 = float(hh.T_case_outer[k2])
                    Pc_at_T = float(np.interp(float(hh.t[k2]), t, Pc))
                else:
                    Tmax2 = Pc_at_T = None
                row = dict(duty_cycle=name, part='case_post_chamber', bracket=f'phenolic {L_ph*1e3:.1f} mm, h_g x{fac:g}', hc_W_m2K=None,
                           coast_s=(t_rl - t_meco if relight else None),
                           T_at_MECO_K=(at(t_meco) if relight else None), T_at_relight_K=(at(t_rl) if relight else None),
                           T_at_Pcmax_landing_burn_K=at(float(t[i_pcmax])), T_max_landing_burn_K=Tmax2, Pc_at_Tmax_landing_burn_Pa=Pc_at_T,
                           T_at_last_shutdown_K=at(t_last), T_post_landing_peak_K=float(post.T_case_outer.max()),
                           t_post_peak_after_shutdown_s=float(post.t[post.T_case_outer.idxmax()] - t_last),
                           T_900s_K=at(t_last + 900.0), T_3600s_K=float(post.T_case_outer.iloc[-1]))
                row.update(time_above(post.t.values, post.T_case_outer.values, 0.5))
                rows.append(row)
                print(json.dumps({k: (round(v, 1) if isinstance(v, float) else v) for k, v in row.items()}), flush=True)
    df = pd.DataFrame(rows)
    hdr = ('# Lip/retainer and post-chamber case temperatures at MECO, at relight after the coast, at the landing-burn Pc maximum, '
           'the landing-burn maximum (with Pc at that instant), at the last shutdown and in a 3600 s post-landing soak with times '
           'above 150/200/240/300 C (SIM lumped/1-D; Combustion v2 2026-10-12). Coasts adiabatic (conservative). Retainer '
           'masses/materials and hc are BRACKETS. No allowable applied (240 C = Al lip at 51 MPa, 192 C = Al aft land; steel '
           'needs its own allowable; reuse = Mechanical over-ageing judgement). SI.\n')
    with open(os.path.join(outdir, 'soakback_relight_v2.csv'), 'w') as f:
        f.write(hdr); df.to_csv(f, index=False, float_format='%.5g')
    json.dump(dict(version='v2', date='2026-10-12', tool='soakback_relight.py', soak_window_s=T_SOAK, thresholds_C=list(THRESH_C),
                   governing_cases='lead CHANGELOG 2026-10-12: TS-1 relight after the MECO coast with Pc 25 bar (normal) and 45 bar '
                                   '(MEOP); TS-2 post-landing soak, unloaded, 6061-T6 over-ageing judgement for reuse (Mechanical)',
                   duty_cycles=meta, rows=rows,
                   notes=['coast duration and relight time are explicit in each DC CSV (burn segments from mox and Pc columns)',
                          'pressure: Pc_relight_plus_0p5s_Pa, Pc_max_landing_burn_Pa per duty cycle; Pc_at_Tmax_landing_burn_Pa per row',
                          'coasts adiabatic in the insert model and the wall model (gas side): temperatures at relight are upper bounds '
                          'for the stated brackets',
                          'times above thresholds are counted over the 3600 s soak only (flag above_*_at_end marks truncation)']),
              open(os.path.join(outdir, 'soakback_relight_v2.json'), 'w'), indent=1, default=float)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:])

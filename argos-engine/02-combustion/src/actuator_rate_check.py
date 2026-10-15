"""Pintle actuator speed check (Combustion v2.2, 2026-10-12; lead request on the HV69 in-line pintle drive).

Question from the lead: does 'full pintle stroke 0.08 s (50 mm/s)' (combustion.json v1/v2.1 valves_and_actuators.
pintle_actuator.full_stroke_time_s) have a basis in combustion physics (start-transient pressure, hard start,
stability)? If not, retire it and defer to the GNC throttle requirement; first check that a 0.25 s full stroke is
acceptable for the start rule (0.10 mm bleed lift + >= 0.3 s isolation-valve ramp).
Origin of the number: combustion.json v1 tag 'DERIVED from ENG-03 (10-90 % thrust <= 100 ms target with ~3 ms chamber
fill + fuel lag)' -> a throttle-response requirement (now gnc.json v2: t10-90 <= 0.15 s, slew >= 2 F_max/s), not a
combustion limit.
Checks with grain_q1d v2 (S230, initial port, baseline tank 3.17 L / 2.00 kg at 20 C, equilibrium tank, nominal law)
at full-stroke times 0.08 s (v1, 50 mm/s), 0.149 s (Electronics physics bound for an in-envelope servo), 0.24 s (HV69 at
MEOP), 0.25 s (lead check value) and 0.40 s (margin case), servo lag 10 ms ASSUMED, constant speed (no load curve):
  1. start transient (model start: torch-to-main delay 0.10 s, pintle straight to the commanded lift): thrust 10/90 %
     times from the command, Pc overshoot over the settled value, max dPc/dt; starts to 12.5/20/50/100 %;
  2. shutdown tail-off against gnc.json v2 shutdown_tail_off '< 10 % thrust within 0.10 s' (REQ ENG-05): time from the
     shutdown command to F < 10 % of the pre-shutdown thrust and to F < 50 N (10 % of F_max), from 100/75/50/25/12.5 %;
  3. start-rule timeline (ignition_v2.json sequence): actuator travel times for the 0.10 mm bleed lift, the return to
     the seat and the ignition lift, against the slots of the sequence; the 2500 N/s ramp vs the actuator speed;
  4. N2O admitted into an unlit chamber before the ignition check at 0.35 s (hard-start inventory) vs actuator speed.
Outputs: OUTDIR/actuator_rate_check_v2.json, FIGDIR/actuator_rate_check_v2.png
usage: python actuator_rate_check.py OUTDIR FIGDIR
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import grain_q1d as Q
from tank import EquilibriumTank

STROKE = 0.004
T_FULL = (0.08, 0.149, 0.24, 0.25, 0.40)
FRACS_SD = (1.0, 0.75, 0.5, 0.25, 0.125)
FRACS_ST = (0.125, 0.2, 0.5, 1.0)
FMAX = 500.0
DT = 2e-4


def tank():
    return EquilibriumTank(3.17e-3, 2.0, 293.15)


def cfg(tf):
    return dict(h_rate=STROKE / tf)


def shutdown_case(frac, tf):
    # command drops just before a 10 ms control instant (0.30 s): the engine sees it at 0.30 s
    t = np.array([0.0, 0.2995, 0.2996, 0.8]); F = np.array([frac * FMAX, frac * FMAX, 0.0, 0.0])
    rec, e = Q.simulate(dict(t=t, F_cmd=F), tank(), cfg=cfg(tf), dt=DT, init_running=True, record_dt=1e-3, t_extra=0.0)
    tr = np.array([r['t'] for r in rec]); Fr = np.array([r['F'] for r in rec]); st = [r['state'] for r in rec]
    hr = np.array([r['h'] for r in rec]); Pr = np.array([r['Pc'] for r in rec])
    i0 = next(i for i, s in enumerate(st) if s in ('shutdown', 'off'))
    t0 = tr[i0]; F0 = float(np.mean(Fr[(tr > 0.2) & (tr < 0.299)])); h0 = float(np.mean(hr[(tr > 0.2) & (tr < 0.299)]))
    def first_below(lim):
        k = np.where((tr >= t0) & (Fr < lim))[0]
        return float(tr[k[0]] - t0) if len(k) else float('nan')
    imp = float(np.trapezoid(Fr[tr >= t0], tr[tr >= t0])) if hasattr(np, 'trapezoid') else float(np.trapz(Fr[tr >= t0], tr[tr >= t0]))
    return dict(frac=frac, full_stroke_s=tf, F_before_N=F0, lift_before_mm=h0 * 1e3, t_to_10pct_of_F_before_s=first_below(0.1 * F0),
                t_to_50N_s=first_below(0.1 * FMAX), tailoff_impulse_Ns=imp,
                trace=dict(t=(tr[(tr >= t0 - 0.02) & (tr <= t0 + 0.4)] - t0).round(4).tolist(),
                           F=Fr[(tr >= t0 - 0.02) & (tr <= t0 + 0.4)].round(2).tolist(),
                           h_mm=(hr[(tr >= t0 - 0.02) & (tr <= t0 + 0.4)] * 1e3).round(4).tolist()))


def start_case(frac, tf):
    t = np.array([0.0, 1.2]); F = np.array([frac * FMAX, frac * FMAX])
    rec, e = Q.simulate(dict(t=t, F_cmd=F), tank(), cfg=cfg(tf), dt=DT, init_running=False, record_dt=1e-3, t_extra=0.0)
    tr = np.array([r['t'] for r in rec]); Fr = np.array([r['F'] for r in rec]); Pr = np.array([r['Pc'] for r in rec])
    Ff = float(np.mean(Fr[tr > 1.0])); Pf = float(np.mean(Pr[tr > 1.0]))
    def first_above(lim):
        k = np.where(Fr >= lim)[0]
        return float(tr[k[0]]) if len(k) else float('nan')
    dP = np.gradient(Pr, tr)
    return dict(frac=frac, full_stroke_s=tf, F_settled_N=Ff, Pc_settled_bar=Pf / 1e5, t10_s=first_above(0.1 * Ff),
                t90_s=first_above(0.9 * Ff), Pc_max_bar=float(Pr.max()) / 1e5,
                Pc_overshoot_pct=100 * (float(Pr.max()) / Pf - 1), dPc_dt_max_bar_s=float(dP.max()) / 1e5,
                trace=dict(t=tr[tr <= 0.8].round(4).tolist(), F=Fr[tr <= 0.8].round(2).tolist(), Pc_bar=(Pr[tr <= 0.8] / 1e5).round(3).tolist()))


def start_rule(tf):
    # 2026-10-12 correction (v2.2a): the ignition_v2.json ramp '<= 2500 N/s' is a CAP; the requirement on the drive is the
    # gnc.json v2 slew >= 2 F_max/s (ENG-03). The first run compared the capability with 2500 N/s ('ramp_required_N_s').
    v = STROKE / tf; lag = 0.010
    ign_lift = (0.207e-3, 0.301e-3)       # 12.5 % and 20 % lifts at 20 C (throttle map, combustion.json v2.1)
    dFdh_100 = 159e3                      # N/m at 100 % (plant fit 159.4 kN/m; dF/dh is larger at every lower thrust point)
    cap = dFdh_100 * v
    return dict(full_stroke_s=tf, speed_mm_s=v * 1e3,
                bleed_lift_0p10mm_s=0.10e-3 / v + lag, return_to_seat_s=0.10e-3 / v + lag,
                ignition_lift_s=[l / v + lag for l in ign_lift],
                slot_bleed_s=0.5, slot_ignition_lift_s=0.23,
                ramp_capability_at_100pct_N_s=cap, ramp_sequence_cap_N_s=2500.0, ramp_min_gnc_v2_N_s=2.0 * FMAX,
                ramp_note='the ignition_v2.json ramp is a cap (<= 2500 N/s, gnc.json engine-model slew); the drive must give '
                          '>= 2 F_max/s (gnc.json v2 ENG-03); dF/dh grows toward the floor, so 100 % is the slowest point',
                ok=bool(0.10e-3 / v + lag < 0.5 and max(ign_lift) / v + lag < 0.23 and cap >= 2.0 * FMAX))


def hard_start_inventory(tf, mdot_cold=0.038):
    """N2O into an unlit chamber between the ignition-lift command (0.12 s) and the ignition check/abort (0.35 s), plus
    the closing ramp; mdot_cold = flow at the 12.5 % lift into a ~1.5 bar chamber (sqrt scaling of the 12.5 % point)."""
    v = STROKE / tf; h = 0.207e-3
    t_open = h / v; t_close = h / v
    m = mdot_cold * ((0.35 - 0.12) - 0.5 * t_open) + 0.5 * mdot_cold * t_close
    return dict(full_stroke_s=tf, N2O_admitted_g=m * 1e3)


def main(outdir, figdir):
    os.makedirs(outdir, exist_ok=True); os.makedirs(figdir, exist_ok=True)
    res = dict(version='v2.2', date='2026-10-12', model='grain_q1d v2 (S230, initial port, baseline tank 3.17 L/2.00 kg 20 C, '
               'equilibrium tank, nominal law); actuator = rate limit (stroke/full-stroke time) + 10 ms first-order lag '
               '(ASSUMED), no load-speed curve; start in the model = torch-to-main delay 0.10 s then straight to the '
               'commanded lift (the ignition-lift + 2500 N/s ramp of ignition_v2.json is not modelled)',
               origin_of_0p08s='combustion.json v1 valves_and_actuators.pintle_actuator.full_stroke_time_s tag: DERIVED from '
               'ENG-03 (10-90 % thrust <= 100 ms target with ~3 ms chamber fill + fuel lag) = throttle-response requirement',
               shutdown=[], start=[], start_rule=[], hard_start=[])
    for tf in T_FULL:
        for fr in FRACS_SD:
            r = shutdown_case(fr, tf); res['shutdown'].append(r)
            print('SD', tf, fr, {k: round(v, 4) for k, v in r.items() if isinstance(v, float)}, flush=True)
        for fr in FRACS_ST:
            r = start_case(fr, tf); res['start'].append(r)
            print('ST', tf, fr, {k: round(v, 4) for k, v in r.items() if isinstance(v, float)}, flush=True)
        res['start_rule'].append(start_rule(tf)); res['hard_start'].append(hard_start_inventory(tf))
    # requirement view: ENG-05 tail-off within 0.10 s (gnc.json v2 shutdown_tail_off)
    tab = {}
    for r in res['shutdown']:
        tab.setdefault(f"{r['full_stroke_s']:.3f}", {})[f"{r['frac']:.3f}"] = dict(
            t_10pct_of_F_before_s=round(r['t_to_10pct_of_F_before_s'], 4), t_50N_s=round(r['t_to_50N_s'], 4))
    res['eng05_tailoff_table'] = tab
    # minimum speed for ENG-05 from 100 %, by bisection on the full-stroke time (both readings)
    def t_sd(tf, key):
        return shutdown_case(1.0, tf)[key]
    lim = {}
    for key in ('t_to_10pct_of_F_before_s', 't_to_50N_s'):
        lo, hi = 0.04, 0.60
        if t_sd(hi, key) <= 0.10:
            lim[key] = hi; continue
        if t_sd(lo, key) > 0.10:
            lim[key] = float('nan'); continue
        for _ in range(14):
            mid = 0.5 * (lo + hi)
            if t_sd(mid, key) <= 0.10:
                lo = mid
            else:
                hi = mid
        lim[key] = lo
    res['max_full_stroke_time_for_ENG05_from_100pct_s'] = lim
    json.dump(res, open(os.path.join(outdir, 'actuator_rate_check_v2.json'), 'w'), indent=1, default=float)
    # figure
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.6))
    cols = dict(zip(T_FULL, ('k', 'tab:blue', 'tab:orange', 'tab:red', 'tab:purple')))
    for r in res['shutdown']:
        if r['frac'] == 1.0:
            axs[0].plot(r['trace']['t'], r['trace']['F'], color=cols[r['full_stroke_s']], label=f"full stroke {r['full_stroke_s']:.3f} s")
    axs[0].axhline(50, color='0.5', ls=':'); axs[0].axvline(0.10, color='0.5', ls='--')
    axs[0].text(0.102, 300, 'ENG-05: < 10 % within 0.10 s', fontsize=8, color='0.3')
    axs[0].set_xlabel('time from the shutdown command [s]'); axs[0].set_ylabel('thrust [N]')
    axs[0].set_title('Shutdown from 100 % (grain_q1d v2, S230)', loc='left', fontsize=10); axs[0].legend(fontsize=8); axs[0].grid(alpha=0.3)
    for r in res['start']:
        if r['frac'] == 1.0:
            axs[1].plot(r['trace']['t'], r['trace']['Pc_bar'], color=cols[r['full_stroke_s']], label=f"full stroke {r['full_stroke_s']:.3f} s")
    axs[1].set_xlabel('time from the start command [s]'); axs[1].set_ylabel('Pc [bar]')
    axs[1].set_title('Start to 100 % (model start: 0.10 s torch-to-main, straight to the lift)', loc='left', fontsize=10)
    axs[1].legend(fontsize=8); axs[1].grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(figdir, 'actuator_rate_check_v2.png'), dpi=130); plt.close(fig)
    print(json.dumps(dict(eng05=tab, limit=lim, start_rule=res['start_rule'], hard_start=res['hard_start']), indent=1, default=float))
    return res


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

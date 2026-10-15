"""Case heating after burnout and soak-back (Combustion v2, brief task 5).

(a) Graphite throat insert -> nozzle retainer ("sleeve"): the insert history is run through the duty cycle with the
    coupled erosion/conduction model (nozzle.ThroatInsert: 1-D radial conduction at the throat station, lumped retainer),
    then continued after the last shutdown for 900 s with no gas-side convection. Losses after shutdown: bore radiation
    to ambient with an effective eps*F = 0.25 (the bore sees the open exit on one side and the warm chamber on the
    other, ASSUMED) and retainer convection + radiation to the bay (h_eff 15 W/m2K over 6.3e-3 m2, ASSUMED).
    Interface conductance graphite -> retainer hc: 2000 W/m2K (bare contact), 500 (thin interlayer / poor contact),
    150 (about 2 mm of phenolic or ceramic paper, k ~0.3 W/mK).  Retainer: 0.15 kg aluminium (c 900) or steel (c 500).
(b) Post-chamber wall stack (gas -> 3 mm phenolic -> 3.175 mm 6061 case -> bay): 1-D transient conduction during a burn
    with the v2 thermal-BC post-chamber row (Bartz, uncertainty factor 0.5-2) and 900 s of soak after shutdown.
    Phenolic charring/ablation is not modelled (it absorbs heat: conservative for the case temperature).
(c) Grain zone: the regressing ABS web carries a thermal layer of thickness kappa/r (~0.1-0.3 mm), so the stored heat
    is ~ rho c dT kappa/r per unit area; the case behind >= 1 mm of residual web is shielded (estimate in the JSON).
Outputs: data/v2/soakback_v2.json, data/v2/soakback_<case>_v2.csv, figs/v2/soakback_v2.png.
usage: python soakback.py DC_DIR OUTDIR FIGDIR file1.csv [file2.csv ...]
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nozzle as N

SIG = 5.670374419e-8
TA = 293.15


def insert_soak(ins, t_soak=900.0, dt=0.05, epsF=0.25, h_bay=15.0, A_ret=6.3e-3, rec=1.0):
    out = []; t = 0.0; nxt = 0.0
    r_in = ins.Rt
    A_bore_per_rad_len = r_in            # per radian per unit length (model convention)
    while t <= t_soak:
        # bore radiation loss as a negative inner-surface flux, retainer loss to the bay
        Tw = float(ins.T[0])
        q_rad = epsF * SIG * (Tw ** 4 - TA ** 4)
        # one implicit conduction step with the gas side 'off' and an imposed radiative loss (explicit flux)
        n = ins.n; r = ins.grid(); rc = 0.5 * (r[1:] + r[:-1]); dr = r[1] - r[0]
        k = N.k_graphite(ins.T); cp = N.cp_graphite(ins.T); rho = N.GRAPHITE['rho']
        kf = 0.5 * (k[1:] + k[:-1]); C = rho * cp * rc * dr / dt
        a = np.zeros(n); b = np.zeros(n); c = np.zeros(n); d = C * ins.T.copy()
        cond = kf * r[1:-1] / dr
        b += C; b[:-1] += cond; c[:-1] = -cond; b[1:] += cond; a[1:] = -cond
        d[0] -= r[0] * q_rad
        b[-1] += r[-1] * ins.hc; d[-1] += r[-1] * ins.hc * ins.Ts
        cp_ = np.zeros(n); dp_ = np.zeros(n); cp_[0] = c[0] / b[0]; dp_[0] = d[0] / b[0]
        for i in range(1, n):
            m = b[i] - a[i] * cp_[i - 1]
            cp_[i] = c[i] / m if i < n - 1 else 0.0
            dp_[i] = (d[i] - a[i] * dp_[i - 1]) / m
        Tn = np.zeros(n); Tn[-1] = dp_[-1]
        for i in range(n - 2, -1, -1):
            Tn[i] = dp_[i] - cp_[i] * Tn[i + 1]
        ins.T = Tn
        q_out = ins.hc * (ins.T[-1] - ins.Ts)
        q_loss = h_bay * A_ret * (ins.Ts - TA) + 0.3 * SIG * A_ret * (ins.Ts ** 4 - TA ** 4)
        ins.Ts += dt * (q_out * 2 * math.pi * ins.Ro * ins.Lax - q_loss) / (ins.m_s * ins.c_s)
        if t >= nxt:
            out.append(dict(t_after_shutdown=t, Tw=float(ins.T[0]), T_back=float(ins.T[-1]), T_retainer=ins.Ts))
            nxt += rec
        t += dt
    return out


def wall_stack(h_g, T_aw, t_burn, t_soak=900.0, L_ph=3e-3, L_al=3.175e-3, h_bay=10.0, n_ph=30, n_al=6):
    """1-D slab: phenolic (k 0.3, rho 1400, c 1300) + 6061 (k 167, rho 2700, c 900); gas side h_g/T_aw during the
    burn, adiabatic after; bay side h_bay."""
    kp, rp, cpp = 0.30, 1400.0, 1300.0; ka, ra, ca = 167.0, 2700.0, 900.0
    x = np.concatenate([np.full(n_ph, L_ph / n_ph), np.full(n_al, L_al / n_al)])
    kk = np.concatenate([np.full(n_ph, kp), np.full(n_al, ka)])
    rc = np.concatenate([np.full(n_ph, rp * cpp), np.full(n_al, ra * ca)])
    n = len(x); T = np.full(n, TA); t = 0.0; dt = 0.01; out = []; nxt = 0.0
    G = np.array([1.0 / (0.5 * x[i] / kk[i] + 0.5 * x[i + 1] / kk[i + 1]) for i in range(n - 1)])
    while t <= t_burn + t_soak:
        on = t <= t_burn
        a = np.zeros(n); b = rc * x / dt; c = np.zeros(n); d = rc * x / dt * T
        b[:-1] += G; c[:-1] = -G; b[1:] += G; a[1:] = -G
        if on:
            hs = 1.0 / (1.0 / h_g + 0.5 * x[0] / kk[0]); b[0] += hs; d[0] += hs * T_aw
        hb = 1.0 / (1.0 / h_bay + 0.5 * x[-1] / kk[-1]); b[-1] += hb; d[-1] += hb * TA
        cp_ = np.zeros(n); dp_ = np.zeros(n); cp_[0] = c[0] / b[0]; dp_[0] = d[0] / b[0]
        for i in range(1, n):
            m = b[i] - a[i] * cp_[i - 1]
            cp_[i] = c[i] / m if i < n - 1 else 0.0
            dp_[i] = (d[i] - a[i] * dp_[i - 1]) / m
        Tn = np.zeros(n); Tn[-1] = dp_[-1]
        for i in range(n - 2, -1, -1):
            Tn[i] = dp_[i] - cp_[i] * Tn[i + 1]
        T = Tn
        if t >= nxt:
            out.append(dict(t=t, T_phenolic_surface=float(T[0]), T_case_inner=float(T[n_ph]), T_case_outer=float(T[-1])))
            nxt += 1.0
        t += dt
    return out


def main(dcdir, outdir, figdir, files):
    TP = N.ThroatProps()
    res = dict(version='v2', date='2026-10-12', insert={}, wall_stack={}, notes=[])
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.5))
    for fn in files:
        r = pd.read_csv(os.path.join(dcdir, fn))
        t = r.t.values; Pc = r.Pc.values; OF = r.OF.values; on = (r.mox.values > 1e-4) & (Pc > 1.5e5)
        i_last = int(np.where(on)[0][-1]) if on.any() else len(t) - 1
        t_end = t[min(i_last + 2, len(t) - 1)]
        m = t <= t_end
        name = fn.replace('.csv', '')
        for hc in (2000.0, 500.0, 150.0):
            for mat, msl, csl in (('Al', 0.15, 900.0), ('steel', 0.15, 500.0)):
                if mat == 'steel' and hc != 2000.0:
                    continue
                ins = N.ThroatInsert(T0=TA, hc=hc, m_sleeve=msl, c_sleeve=csl)
                # run the burn history with this insert (same stepping as N.run_history)
                tn = t[0]; dtb = 5e-3
                while tn <= t_end:
                    i = min(np.searchsorted(t, tn), len(t) - 1)
                    ins.step(dtb, float(Pc[i]), float(OF[i]) if np.isfinite(OF[i]) else 5.0, TP, bool(on[i]))
                    tn += dtb
                Ts_sd = ins.Ts; Tw_sd = float(ins.T[0]); Tavg_sd = float(ins.T.mean())
                hist = insert_soak(ins)
                pk = max(hist, key=lambda h: h['T_retainer'])
                key = f'{name}|hc{hc:.0f}|{mat}'
                res['insert'][key] = dict(t_burn_end_s=float(t_end), Tw_at_shutdown_K=Tw_sd, T_insert_mean_at_shutdown_K=Tavg_sd,
                                          T_retainer_at_shutdown_K=Ts_sd, T_retainer_peak_K=pk['T_retainer'],
                                          t_peak_after_shutdown_s=pk['t_after_shutdown'],
                                          T_retainer_900s_K=hist[-1]['T_retainer'])
                print(key, json.dumps({k: round(v, 1) for k, v in res['insert'][key].items()}), flush=True)
                if mat == 'Al':
                    pd.DataFrame(hist).to_csv(os.path.join(outdir, f'soakback_{name}_hc{hc:.0f}_v2.csv'), index=False, float_format='%.5g')
                    if fn == files[0]:
                        hh = pd.DataFrame(hist)
                        axs[0].plot(hh.t_after_shutdown, hh.T_retainer - 273.15, label=f'retainer (Al 0.15 kg), hc {hc:.0f}')
                        axs[0].plot(hh.t_after_shutdown, hh.Tw - 273.15, ls=':', lw=0.8, label=f'graphite bore, hc {hc:.0f}')
    axs[0].axhline(150, color='k', lw=0.6, ls='--'); axs[0].text(400, 155, '6061-T6 ~150 C (strength loss begins)', fontsize=7)
    axs[0].set_xlabel('time after shutdown [s]'); axs[0].set_ylabel('temperature [C]')
    axs[0].set_title(f'Throat-insert soak-back after {files[0].split("_")[0]} (S230)', fontsize=9); axs[0].legend(fontsize=7); axs[0].grid(alpha=0.3)
    # wall stack in the post-chamber: v2 thermal BC row (post-chamber) at max thrust, burn = longest flight burn
    for t_burn, lab in ((5.83, 'A1 total burn 5.8 s at max-thrust BC'), (20.7, 'B1 20.7 s at max-thrust BC (bounding)')):
        for fac in (1.0, 2.0):
            h = 920.0 * fac; Taw = 2845.0 * 0.95
            hist = wall_stack(h, Taw, t_burn)
            pk = max(hist, key=lambda q: q['T_case_outer'])
            res['wall_stack'][f'{lab}|hgx{fac:g}'] = dict(h_g=h, T_aw=Taw, burn_s=t_burn, T_case_peak_K=pk['T_case_outer'],
                                                         t_peak_s=pk['t'], T_phenolic_surface_max_K=max(q['T_phenolic_surface'] for q in hist))
            hh = pd.DataFrame(hist)
            axs[1].plot(hh.t, hh.T_case_outer - 273.15, label=f'case, {lab}, h_g x{fac:g}')
    axs[1].set_xlabel('time from ignition [s]'); axs[1].set_ylabel('6061 case temperature [C]')
    axs[1].set_title('Post-chamber wall: 3 mm phenolic + 3.175 mm 6061 (no ablation credit)', fontsize=9)
    axs[1].legend(fontsize=7); axs[1].grid(alpha=0.3); axs[1].set_xscale('symlog', linthresh=30)
    fig.tight_layout(); fig.savefig(os.path.join(figdir, 'soakback_v2.png'), dpi=130); plt.close(fig)
    # grain zone estimate
    kappa = 1.2e-7; rho_c = 1000 * 1500
    res['grain_zone'] = {f'r_{r_mm:.2f}mm_s': dict(thermal_layer_mm=kappa / (r_mm * 1e-3) * 1e3,
                                                     stored_heat_kJ_m2=rho_c * 350 * kappa / (r_mm * 1e-3) / 1e3)
                         for r_mm in (0.2, 0.5, 1.0)}
    res['notes'] = ['Insert model: throat-station radial slice representing the 32 mm long insert (0.081 kg); real insert and '
                    'retainer geometry (Mechanical CAD) changes the numbers: use as a sizing check, then FEA.',
                    'Wall stack: h_g 920 W/m2K and T_aw 0.95 x 2845 K from the max-thrust thermal BC post-chamber row '
                    '(Bartz outside validity, factor 0.5-2); x2 case shown.']
    json.dump(res, open(os.path.join(outdir, 'soakback_v2.json'), 'w'), indent=1, default=float)
    return res


def wall_stack_dc(t, Pc, burning, h_max, T_aw, L_ph, t_soak=900.0, L_al=3.175e-3, h_bay=10.0, Pc_max=25.0e5):
    """Same slab as wall_stack, but the gas-side h_g follows the duty cycle: h_g = h_max (Pc/Pc_max)^0.8 while burning
    (Bartz scaling at fixed geometry and c*), adiabatic otherwise; dt 0.01 s in the burn window, 0.1 s in the soak."""
    kp, rp, cpp = 0.30, 1400.0, 1300.0; ka, ra, ca = 167.0, 2700.0, 900.0
    n_ph = max(12, int(round(L_ph / 1e-4))); n_al = 6
    x = np.concatenate([np.full(n_ph, L_ph / n_ph), np.full(n_al, L_al / n_al)])
    kk = np.concatenate([np.full(n_ph, kp), np.full(n_al, ka)])
    rc = np.concatenate([np.full(n_ph, rp * cpp), np.full(n_al, ra * ca)])
    n = len(x); T = np.full(n, TA); out = []
    G = 1.0 / (0.5 * x[:-1] / kk[:-1] + 0.5 * x[1:] / kk[1:])
    t_last = float(t[np.where(burning)[0][-1]]) if burning.any() else float(t[-1])
    tt = float(t[0]); nxt = tt
    while tt <= t_last + t_soak:
        dt = 0.01 if tt <= t_last + 1.0 else 0.1
        i = min(int(np.searchsorted(t, tt)), len(t) - 1)
        on = bool(burning[i]) and tt <= t_last
        a = np.zeros(n); b = rc * x / dt; c = np.zeros(n); d = rc * x / dt * T
        b[:-1] += G; c[:-1] = -G; b[1:] += G; a[1:] = -G
        if on:
            hg = h_max * max(Pc[i] / Pc_max, 1e-6) ** 0.8
            hs = 1.0 / (1.0 / hg + 0.5 * x[0] / kk[0]); b[0] += hs; d[0] += hs * T_aw
        hb = 1.0 / (1.0 / h_bay + 0.5 * x[-1] / kk[-1]); b[-1] += hb; d[-1] += hb * TA
        cp_ = np.zeros(n); dp_ = np.zeros(n); cp_[0] = c[0] / b[0]; dp_[0] = d[0] / b[0]
        for k in range(1, n):
            m = b[k] - a[k] * cp_[k - 1]
            cp_[k] = c[k] / m if k < n - 1 else 0.0
            dp_[k] = (d[k] - a[k] * dp_[k - 1]) / m
        Tn = np.zeros(n); Tn[-1] = dp_[-1]
        for k in range(n - 2, -1, -1):
            Tn[k] = dp_[k] - cp_[k] * Tn[k + 1]
        T = Tn
        if tt >= nxt:
            out.append(dict(t=tt, T_phenolic_surface=float(T[0]), T_case_inner=float(T[n_ph]), T_case_outer=float(T[-1])))
            nxt += 0.5
        tt += dt
    return out, t_last


def main_wall(dcdir, outdir, figdir, files):
    """Post-chamber wall stack over real duty cycles, liner thickness 1.6 (v1 geometry) / 3 / 5 mm, h_g x1 and x2."""
    res = dict(version='v2', date='2026-10-12', model='1-D slab phenolic + 3.175 mm 6061, h_g = 920 (x1, x2) W/m2K '
               '(Pc/25 bar)^0.8 while burning, T_aw 2703 K (0.95 x 2845 K, conservative for S230 T0 2757 K), bay h 10 W/m2K, '
               '900 s soak; no char/pyrolysis credit (conservative); Mechanical FEA with thermal_bc_*_v2.csv supersedes',
               cases={})
    fig, axs = plt.subplots(1, len(files), figsize=(6.5 * len(files), 4.4))
    axs = np.atleast_1d(axs)
    for ax, fn in zip(axs, files):
        r = pd.read_csv(os.path.join(dcdir, fn))
        t = r.t.values; Pc = r.Pc.values; burning = (r.mox.values > 1e-4) & (Pc > 1.5e5)
        name = fn.split('_')[0]
        for L_ph in (1.6e-3, 3.0e-3, 5.0e-3):
            for fac in (1.0, 2.0):
                hist, t_last = wall_stack_dc(t, Pc, burning, 920.0 * fac, 0.95 * 2845.0, L_ph)
                hh = pd.DataFrame(hist)
                pk = hh.loc[hh.T_case_outer.idxmax()]
                key = f'{name}|liner{L_ph * 1e3:.1f}mm|hgx{fac:g}'
                res['cases'][key] = dict(T_case_peak_K=float(pk.T_case_outer), t_peak_s=float(pk.t), t_last_burn_s=t_last,
                                         T_case_at_last_shutdown_K=float(hh.T_case_outer[hh.t <= t_last].iloc[-1]),
                                         T_phenolic_surface_max_K=float(hh.T_phenolic_surface.max()))
                print(key, json.dumps({k: round(v, 1) for k, v in res['cases'][key].items()}), flush=True)
                ax.plot(hh.t, hh.T_case_outer - 273.15, ls='-' if fac == 1 else '--',
                        label=f'liner {L_ph * 1e3:.1f} mm, h_g x{fac:g}')
        ax.axhline(150, color='k', lw=0.6, ls=':'); ax.text(t[0] + 5, 156, '6061-T6 ~150 C', fontsize=7)
        ax.set_xscale('symlog', linthresh=60); ax.set_xlabel('time from cycle start [s]'); ax.set_ylabel('6061 case outer T [C]')
        ax.set_title(f'Post-chamber case over {name} (S230 grain), duty-cycle h_g', fontsize=9); ax.grid(alpha=0.3)
        ax.legend(fontsize=7)
    fig.tight_layout(); fig.savefig(os.path.join(figdir, 'soakback_wall_v2.png'), dpi=130); plt.close(fig)
    json.dump(res, open(os.path.join(outdir, 'soakback_wall_v2.json'), 'w'), indent=1, default=float)
    return res


if __name__ == '__main__':
    if sys.argv[1] == '--wall':
        main_wall(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])
    else:
        main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:])

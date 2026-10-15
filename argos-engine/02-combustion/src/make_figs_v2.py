"""Report figures for 02-combustion v2 that were still missing (Combustion v2, 2026-10-12).

Every curve is read from a v2 data file named in the figure footer; nothing is typed by hand. Figures:
  thermo_cstar_Tc_v2.png      CEA c* and Tc vs O/F (ABS, PETG, 50/50 paraffin-ABS) at Pc 25 and 4 bar
  throttle_map_v2.png         S230 throttle map at P_tank 50 bar, initial port: F(lift), Pc, O/F, dP/Pc; ceiling vs P_tank
  plant_v2.png                fitted valve-lift -> Pc plant: unit step responses and parameters vs throttle
  erosion_v2.png              throat recession and wall temperature over the gnc.json v1 duty cycles (nominal/conservative)
  thermal_bc_v2.png           Bartz q (Tw 600 K) and h_g along the gas path for the five BC points
  stability_v2.png            chug gain margin vs throttle (port 25/38 mm, tau 1/5/10 ms) and dP/Pc
  supercharge_v2.png          tank pressure vs time on DC-A1 v1 for the supercharge options
  nozzle_sep_v2.png           v2 contour and pe/pa vs Schmucker separation pressure ratio over throttle (eps 1.8/2/3)
usage: python make_figs_v2.py DATADIR FIGDIR
"""
from __future__ import annotations
import json, os, sys
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

D, FD = sys.argv[1], sys.argv[2]
V2 = os.path.join(D, 'v2')
os.makedirs(FD, exist_ok=True)


def foot(fig, txt):
    fig.text(0.01, 0.005, txt, fontsize=7, color='0.35', ha='left', va='bottom')


def save(fig, name):
    fig.savefig(os.path.join(FD, name), dpi=150); plt.close(fig); print('wrote', name)


def rd(p):
    return pd.read_csv(p, comment='#')


# ---------------- thermochemistry ----------------
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
for card, ls in (('ABS_TYP_v1', '-'), ('PETG_NOM_v1', '--'), ('PARABS50_v1', ':')):
    t = rd(os.path.join(D, 'thermo', f'{card}_shifting_v1.csv'))
    for pc, col in ((25.0, 'C0'), (4.0, 'C3')):
        s = t[np.isclose(t.Pc_bar, pc)].sort_values('OF')
        ax[0].plot(s.OF, s.cstar_m_s, ls=ls, color=col, label=f'{card.split("_v1")[0]} {pc:g} bar')
        ax[1].plot(s.OF, s.Tc_K, ls=ls, color=col, label=f'{card.split("_v1")[0]} {pc:g} bar')
for a in ax:
    a.axvspan(4.06, 10.43, color='0.9', zorder=0); a.set_xlabel('O/F [-]'); a.grid(alpha=0.3)
ax[0].set_ylabel('c* ideal [m/s]'); ax[1].set_ylabel('Tc [K]'); ax[0].legend(fontsize=7, ncol=2)
ax[0].set_title('CEA shifting equilibrium, N2O gas 298 K'); ax[1].set_title('grey band: S230 operating O/F (12.5-100 %)')
foot(fig, 'data/thermo/{ABS_TYP,PETG_NOM,PARABS50}_v1_shifting_v1.csv (CEA via RocketCEA; ideal, no efficiencies). O/F band from data/v2/nozzle_perf_v2.json')
fig.tight_layout(rect=(0, 0.03, 1, 1)); save(fig, 'thermo_cstar_Tc_v2.png')

# ---------------- throttle map ----------------
tm = rd(os.path.join(V2, 'engine_S230', 'throttle_map_v2.csv'))
s = tm[np.isclose(tm.P_tank_Pa, 5.0e6) & np.isclose(tm.D_port_m, 0.025)].sort_values('frac')
fig, ax = plt.subplots(2, 3, figsize=(13, 7))
ax = ax.ravel()
ax[0].plot(s.lift_m * 1e3, s.F_N, 'o-'); ax[0].set_xlabel('pintle lift [mm]'); ax[0].set_ylabel('F [N]')
ax[1].plot(s.F_N, s.Pc_Pa / 1e5, 'o-'); ax[1].set_xlabel('F [N]'); ax[1].set_ylabel('Pc [bar]')
ax[2].plot(s.F_N, s.OF, 'o-'); ax[2].set_xlabel('F [N]'); ax[2].set_ylabel('O/F [-]')
ax[3].plot(s.F_N, s.dP_over_Pc, 'o-'); ax[3].axhline(0.25, color='r', ls='--', lw=0.8); ax[3].set_xlabel('F [N]'); ax[3].set_ylabel('dP_inj / Pc [-]')
ax[3].set_yscale('log')
ax[4].plot(s.F_N, s.Isp_SL_s, 'o-'); ax[4].set_xlabel('F [N]'); ax[4].set_ylabel('Isp sea level [s]')
for dp in sorted(tm.D_port_m.unique()):
    c = tm[np.isclose(tm.D_port_m, dp) & np.isclose(tm.frac, 1.0)].sort_values('P_tank_Pa')
    ax[5].plot(c.P_tank_Pa / 1e5, c.F_ceiling_N, 'o-', label=f'port {dp*1e3:.0f} mm')
ax[5].axhline(500, color='k', lw=0.8); ax[5].set_xlabel('P_tank [bar]'); ax[5].set_ylabel('thrust ceiling [N]'); ax[5].legend(fontsize=7)
for a in ax:
    a.grid(alpha=0.3)
fig.suptitle('S230 throttle map, P_tank 50 bar, initial port 25 mm (Dyer pintle Cd 0.70, eta_c* 0.92 ASSUMED)')
foot(fig, 'data/v2/engine_S230/throttle_map_v2.csv (SIM grain_q1d v2 quasi-steady map). Red dashed: dP/Pc >= 0.25 stiffness rule.')
fig.tight_layout(rect=(0, 0.03, 1, 0.96)); save(fig, 'throttle_map_v2.png')

# ---------------- plant ----------------
pl = json.load(open(os.path.join(V2, 'engine_S230', 'plant_valve_to_pc_v2.json')))
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
tt = np.linspace(0, 2.0, 2001)
for p in pl:
    y = (1 - p['phi']) * (1 - np.exp(-tt / p['tau_c_s'])) + p['phi'] * (1 - np.exp(-tt / p['tau_f_s']))
    ax[0].plot(tt, y, label=f"{p['frac']*100:.1f} %: tau_c {p['tau_c_s']*1e3:.0f} ms, tau_f {p['tau_f_s']*1e3:.0f} ms, phi {p['phi']:.3f}")
ax[0].set_xscale('log'); ax[0].set_xlim(1e-3, 2); ax[0].set_xlabel('t after lift step [s]'); ax[0].set_ylabel('Pc / (K_h dh) [-]')
ax[0].legend(fontsize=7); ax[0].grid(alpha=0.3, which='both'); ax[0].set_title('fitted unit step response')
fr = [p['frac'] * 100 for p in pl]
ax[1].plot(fr, [p['K_h_Pa_per_m'] * 1e-8 for p in pl], 'o-', label='K_h [bar/mm]')
ax[1].plot(fr, [p['dF_dh_N_per_m'] * 1e-3 / 10 for p in pl], 's-', label='dF/dh [N/mm] / 10')
ax[1].plot(fr, [p['tau_f_s'] * 1e2 for p in pl], '^-', label='tau_f [s] x 100')
ax[1].set_xlabel('throttle [% of 500 N]'); ax[1].legend(fontsize=8); ax[1].grid(alpha=0.3); ax[1].set_title('plant parameters')
foot(fig, 'data/v2/engine_S230/plant_valve_to_pc_v2.json: Pc(s)/h(s) = K_h [(1-phi)/(1+tau_c s) + phi/(1+tau_f s)], fitted to +3 % lift steps of grain_q1d v2 (tank frozen). SIM.')
fig.tight_layout(rect=(0, 0.04, 1, 1)); save(fig, 'plant_v2.png')

# ---------------- erosion ----------------
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
for i, dc in enumerate(('DC-A1', 'DC-A2', 'DC-B1', 'DC-B2')):
    for kind, ls in (('nominal', '-'), ('conservative', '--')):
        p = os.path.join(V2, 'erosion_S230', f'{dc}-S230_neqE1e+03_reg1_throat_{kind}.csv')
        if not os.path.exists(p):
            continue
        e = rd(p)
        ax[0].plot(e.t, e.recession_mm, ls=ls, color=f'C{i}', label=f'{dc} {kind}')
        if kind == 'nominal':
            ax[1].plot(e.t, e.Tw, color=f'C{i}', label=f'{dc} wall (nominal)')
ax[0].set_xlabel('t [s]'); ax[0].set_ylabel('throat radius recession [mm]'); ax[0].legend(fontsize=7); ax[0].grid(alpha=0.3)
ax[1].set_xlabel('t [s]'); ax[1].set_ylabel('throat wall temperature [K]'); ax[1].legend(fontsize=7); ax[1].grid(alpha=0.3)
foot(fig, 'data/v2/erosion_S230/*_throat_{nominal,conservative}.csv (SIM coupled 1-D conduction + semi-global C oxidation kinetics, Rotondi et al. 2024 + NSC; S230 on gnc.json v1 DCs)')
fig.tight_layout(rect=(0, 0.04, 1, 1)); save(fig, 'erosion_v2.png')

# ---------------- thermal BC ----------------
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
for nm, lab in (('max', '100 %'), ('75pct', '75 %'), ('50pct', '50 %'), ('20pct', '20 %'), ('floor12p5', '12.5 %')):
    b = rd(os.path.join(V2, f'thermal_bc_{nm}_v2.csv'))
    ax[0].plot(b.x_face_m * 1e3, b.q_conv_Tw600_W_m2 / 1e6, label=lab)
    ax[1].plot(b.x_face_m * 1e3, b.h_g_Tw600_W_m2K, label=lab)
cont = rd(os.path.join(V2, 'nozzle_contour_v2.csv'))
xt = float(cont.x_face_m[np.argmin(cont.r_m.values)])
for a in ax:
    a.axvline(xt * 1e3, color='k', lw=0.6, ls=':'); a.set_xlabel('x from injector face [mm]'); a.grid(alpha=0.3); a.legend(fontsize=7)
ax[0].set_ylabel('q_conv at Tw 600 K [MW/m2]'); ax[1].set_ylabel('h_g at Tw 600 K [W/m2K]'); ax[1].set_yscale('log')
foot(fig, 'data/v2/thermal_bc_*_v2.csv (DERIVED Bartz 1957 with CEA transport; x0.5-2 band in the chamber/post-chamber). Dotted: throat.')
fig.tight_layout(rect=(0, 0.04, 1, 1)); save(fig, 'thermal_bc_v2.png')

# ---------------- stability ----------------
st = rd(os.path.join(V2, 'stability_v2.csv'))
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
for dp, mk in ((0.025, 'o'), (0.038, 's')):
    g = st[np.isclose(st.D_port_m, dp)].sort_values('frac')
    for tau, ls in (('GM_tau1ms', '-'), ('GM_tau5ms', '--'), ('GM_tau10ms', ':')):
        ax[0].plot(g.frac * 100, g[tau], ls=ls, marker=mk, label=f'port {dp*1e3:.0f} mm, {tau[3:]}')
    ax[1].plot(g.frac * 100, g.dP_over_Pc, marker=mk, label=f'port {dp*1e3:.0f} mm')
ax[0].axhline(1.0, color='r', lw=0.8); ax[0].set_yscale('log'); ax[0].set_xlabel('throttle [%]'); ax[0].set_ylabel('chug gain margin [-]')
ax[0].legend(fontsize=6, ncol=2); ax[0].grid(alpha=0.3, which='both')
ax[1].axhline(0.25, color='r', lw=0.8, ls='--'); ax[1].set_yscale('log'); ax[1].set_xlabel('throttle [%]'); ax[1].set_ylabel('dP_inj / Pc [-]')
ax[1].legend(fontsize=7); ax[1].grid(alpha=0.3, which='both')
foot(fig, 'data/v2/stability_v2.csv (DERIVED double-time-lag feed/chamber model with the hybrid fuel path; tau = combustion time lag). Hybrid LF modes not modelled.')
fig.tight_layout(rect=(0, 0.04, 1, 1)); save(fig, 'stability_v2.png')

# ---------------- supercharge ----------------
sp = rd(os.path.join(V2, 'supercharge_trade_P_v2.csv'))
fig, ax = plt.subplots(figsize=(7.5, 4.2))
for c in sp.columns[1:]:
    ax.plot(sp.t, sp[c] / 1e5, label=c)
ax.set_xlabel('t on DC-A1 (gnc.json v1) [s]'); ax.set_ylabel('tank pressure [bar]'); ax.grid(alpha=0.3); ax.legend(fontsize=7)
foot(fig, 'data/v2/supercharge_trade_P_v2.csv (SIM equilibrium tank; N2 insoluble ASSUMPTION)')
fig.tight_layout(rect=(0, 0.04, 1, 1)); save(fig, 'supercharge_v2.png')

# ---------------- nozzle contour + separation ----------------
npf = rd(os.path.join(V2, 'nozzle_perf_v2.csv'))
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
ax[0].plot(cont.x_face_m * 1e3, cont.r_m * 1e3, 'k-'); ax[0].plot(cont.x_face_m * 1e3, -cont.r_m * 1e3, 'k-')
ax[0].set_aspect('equal'); ax[0].set_xlabel('x from injector face [mm]'); ax[0].set_ylabel('r [mm]'); ax[0].grid(alpha=0.3)
ax[0].set_title(f'v2 contour: Dt {2*cont.r_m.min()*1e3:.3f} mm, De {2*cont.r_m.iloc[-1]*1e3:.3f} mm, '
                f'eps {(cont.r_m.iloc[-1]/cont.r_m.min())**2:.2f}', fontsize=9)
g = npf[npf.grain == 'v2_S230_straight_L230']
for eps, col in ((1.8, 'C2'), (2.0, 'C0'), (3.0, 'C3')):
    h = g[np.isclose(g.eps, eps)].sort_values('frac')
    ax[1].plot(h.frac * 100, h.pe_over_pa, 'o-', color=col, label=f'pe/pa, eps {eps:g}')
    ax[1].plot(h.frac * 100, h.schmucker_psep_over_pa, ':', color=col, label=f'Schmucker psep/pa, eps {eps:g}')
ax[1].axhline(0.4, color='0.5', lw=0.8, ls='--', label='Summerfield 0.4')
ax[1].set_xlabel('throttle [%]'); ax[1].set_ylabel('pressure ratio to ambient [-]'); ax[1].legend(fontsize=6); ax[1].grid(alpha=0.3)
ax[1].set_title('separation when pe/pa falls below psep/pa', fontsize=9)
foot(fig, 'data/v2/nozzle_contour_v2.csv (gas-side wall radii); data/v2/nozzle_perf_v2.csv (CEA shifting; Schmucker/Summerfield criteria). DERIVED.')
fig.tight_layout(rect=(0, 0.04, 1, 1)); save(fig, 'nozzle_sep_v2.png')

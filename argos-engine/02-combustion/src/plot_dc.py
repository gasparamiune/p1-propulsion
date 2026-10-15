"""Figures for the duty-cycle simulations (Combustion v2, task 4): one figure per duty cycle, v1 helical grain vs the
v2 straight-port grain, nominal regression with the x0.6 / x1.5 band.  usage: python plot_dc.py DATADIR FIGDIR
DATADIR holds dc/ (v1 grain) and dc_g2/ (straight port) CSVs written by run_dc.py.
"""
from __future__ import annotations
import glob, json, os, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

DCS = ['DC-A1', 'DC-A2', 'DC-B1', 'DC-B2', 'DC-C', 'DC-D']
LABEL = {'DC-A1': 'A1 flight 300 m, drogue', 'DC-A2': 'A2 flight 300 m, free fall', 'DC-B1': 'B1 hop 100 m',
         'DC-B2': 'B2 hop 50 m', 'DC-C': 'C tethered hover (ground)', 'DC-D': 'D static-fire qualification (ground)'}


def load(fn):
    d = pd.read_csv(fn, comment='#')
    return d


def find(datadir, sub, dc, grain_tag, reg):
    pat = os.path.join(datadir, sub, f'{dc}{grain_tag}_*reg{reg}.csv')
    fs = sorted(glob.glob(pat))
    pref = [f for f in fs if 'neqE1e+03' in f] or [f for f in fs if 'ground' in f] or fs
    return pref[0] if pref else None


def fig_dc(datadir, figdir, dc):
    runs = []
    for subs, tag, name, col in ((('dc',), '', 'v1 helical port L200', 'tab:red'),
                                 (('dc_g3', 'engine_S230'), '-S230', 'v2 straight port L230', 'tab:blue')):
        for reg, lw, ls in (('1', 1.6, '-'), ('0.6', 0.7, ':'), ('1.5', 0.7, '--')):
            fn = None
            for sub in subs:
                fn = fn or find(datadir, sub, dc, tag, reg)
            if fn:
                runs.append((name, reg, col, lw, ls, load(fn)))
    if not runs:
        return None
    fig, axs = plt.subplots(3, 2, figsize=(13, 10), sharex=True)
    ax = axs[0, 0]
    d0 = runs[0][5]
    ax.plot(d0.t, d0.F_cmd, color='k', lw=0.8, label='command (gnc.json duty cycle)')
    for name, reg, col, lw, ls, d in runs:
        ax.plot(d.t, d.F, color=col, lw=lw, ls=ls, label=f'{name}, regression x{reg}')
        if reg == '1':
            ax.plot(d.t, d.F_ceiling.where(d.state == 'run'), color=col, lw=0.6, ls='-.', alpha=0.7)
    ax.set_ylabel('thrust [N] (dash-dot: ceiling)'); ax.legend(fontsize=6.5, ncol=2); ax.grid(alpha=0.3)
    ax = axs[0, 1]
    for name, reg, col, lw, ls, d in runs:
        ax.plot(d.t, d.Pc / 1e5, color=col, lw=lw, ls=ls)
        if reg == '1':
            ax.plot(d.t, d.P_tank / 1e5, color=col, lw=0.8, ls='-.')
            ax.plot(d.t, d.P1 / 1e5, color=col, lw=0.6, ls=(0, (1, 1)))
    ax.set_ylabel('Pc, P1 (dotted), P_tank (dash-dot) [bar]'); ax.grid(alpha=0.3)
    ax = axs[1, 0]
    for name, reg, col, lw, ls, d in runs:
        m = d.state == 'run'
        ax.plot(d.t[m], d.OF[m], color=col, lw=lw, ls=ls)
    ax.set_ylabel('O/F (running)'); ax.set_ylim(0, 15); ax.grid(alpha=0.3)
    ax = axs[1, 1]
    for name, reg, col, lw, ls, d in runs:
        m = d.state == 'run'
        ax.plot(d.t[m], d.Isp[m], color=col, lw=lw, ls=ls)
    ax.set_ylabel('Isp sea level, delivered [s]'); ax.grid(alpha=0.3)
    ax = axs[2, 0]
    for name, reg, col, lw, ls, d in runs:
        ax.plot(d.t, d.w_min * 1e3, color=col, lw=lw, ls=ls)
    ax.axhline(0, color='k', lw=0.8)
    ax.set_ylabel('minimum web [mm] (< 0: burn-through)'); ax.set_xlabel('t [s]'); ax.grid(alpha=0.3)
    ax = axs[2, 1]
    for name, reg, col, lw, ls, d in runs:
        if reg == '1':
            ax.plot(d.t, d.m_liq, color=col, lw=lw, label=f'{name}: liquid N2O [kg]')
            ax.plot(d.t, d.dpc, color=col, lw=0.8, ls='--', label=f'{name}: injector dP/Pc [-]')
    ax.axhline(0.25, color='k', lw=0.6, ls=':')
    ax.set_ylim(0, 8); ax.set_ylabel('liquid N2O [kg], dP/Pc [-] (clipped at 8)'); ax.set_xlabel('t [s]'); ax.legend(fontsize=7); ax.grid(alpha=0.3)
    fig.suptitle(f'{LABEL[dc]}: quasi-1D engine model (grain_q1d v2, non-equilibrium tank E=1000 or ground tank)', fontsize=10)
    fig.tight_layout()
    fn = os.path.join(figdir, f'dc_{dc}_v2.png'); fig.savefig(fn, dpi=110); plt.close(fig)
    return fn


if __name__ == '__main__':
    datadir, figdir = sys.argv[1], sys.argv[2]
    os.makedirs(figdir, exist_ok=True)
    for dc in DCS:
        print(fig_dc(datadir, figdir, dc))

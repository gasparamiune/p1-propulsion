"""RC-05 independent L* and grain burn / residual-web check (reviewer, not the author).

1) Free volume and L*: pre-chamber + initial port + post-chamber cylinders + convergent integrated from the author's
   published gas-path contour (data/v2/nozzle_contour_v2.csv, geometry input only).
2) 0-D grain over the gnc.json v2 duty cycles (F_N histories, 01-systems-gnc/duty_cycles/*_v2.csv):
   - reviewer's own steady engine map: Pc = (mox + mf) eta_c* c*(Pc, O/F)/At, F = (eta_cf Cf_vac - eps pa/Pc) Pc At,
     c* and Cf_vac from RocketCEA (shifting) on a (Pc, O/F) grid with the reviewer's ABS card; eta_c* 0.92, eta_cf 0.975;
     no separation credit, no thermal lag, no tank model (the F history fixes the oxidiser flow).
   - regression r = a G_ox^n, uniform along the port (oxidiser-flux law), rho_f 1000 kg/m3, L 0.230 m, D0 25 mm,
     OD 53.5 mm.  Cases: author law (a 5.77e-5, n 0.5) at x0.6/1.0/1.5, and the author's UNRUN exponent band
     n 0.35 / 0.68 re-anchored to the same point r(300 kg/m2s) = 1.0 mm/s (the author's anchor), at x1.0 and x1.5.
Usage: python -I rc05_grain.py -> rc05_grain.json
"""
import json, math, os, csv, glob
import numpy as np
from scipy.interpolate import RegularGridInterpolator
from rocketcea.cea_obj import add_new_fuel
from rocketcea.cea_obj_w_units import CEA_Obj

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.abspath(os.path.join(HERE, '..', '..'))
G0, PA, EPS = 9.80665, 101325.0, 2.0
DT_THR = 0.013724
AT = math.pi / 4 * DT_THR ** 2
RHO_F, LG, D0, OD = 1000.0, 0.230, 0.025, 0.0535
xA, xB, xS = 0.24, 0.185, 0.575
C = 3 * xA + 4 * xB + 8 * xS; H = 3 * xA + 6 * xB + 8 * xS; N = xA
M = C * 12.011 + H * 1.008 + N * 14.007
add_new_fuel('RV5_ABS', f"fuel RV5_ABS C {C:.5f} H {H:.5f} N {N:.5f} wt%=100.00 h,kj/mol={476.4 * M / 1000:.4f} t(k)=298.15 rho=1.04\n")
CEA = CEA_Obj(oxName='N2O', fuelName='RV5_ABS', pressure_units='bar', cstar_units='m/s', temperature_units='K', isp_units='sec')


def lstar():
    rows = [r for r in csv.reader(open(os.path.join(HUB, '02-combustion/data/v2/nozzle_contour_v2.csv'))) if r and not r[0].startswith('#')]
    hdr = rows[0]; data = np.array([[float(v) for v in r[:3]] for r in rows[1:]])
    x, xt, r = data[:, 0], data[:, 1], data[:, 2]
    conv = xt <= 0
    v_conv = float(np.trapezoid(math.pi * r[conv] ** 2, x[conv]))
    v_pre = math.pi / 4 * 0.0539 ** 2 * 0.030
    v_port = math.pi / 4 * D0 ** 2 * LG
    v_post = math.pi / 4 * 0.0539 ** 2 * (x[0] - 0.260)
    V = v_pre + v_port + v_post + v_conv
    return dict(V_pre=v_pre, V_port=v_port, V_post=v_post, V_conv=v_conv, V_free=V, L_star=V / AT,
                author=dict(V_free=2.846e-4, L_star=1.924))


# ---- engine map tables ----
PCS = np.array([1.2, 1.6, 2.0, 2.5, 3.0, 4.0, 5.0, 6.5, 8.0, 10.0, 13.0, 16.0, 20.0, 25.0, 30.0])
OFS = np.array([1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.5, 14.0, 16.0, 20.0, 25.0])


def build_tables():
    cs = np.zeros((len(PCS), len(OFS))); cf = np.zeros_like(cs)
    for i, p in enumerate(PCS):
        for j, o in enumerate(OFS):
            isp, cst, _ = CEA.get_IvacCstrTc(Pc=p, MR=o, eps=EPS)
            cs[i, j] = cst; cf[i, j] = isp * G0 / cst
    return (RegularGridInterpolator((PCS, OFS), cs, bounds_error=False, fill_value=None),
            RegularGridInterpolator((PCS, OFS), cf, bounds_error=False, fill_value=None))


CS, CF = build_tables()


def fuel_flow(mox, D, a, n):
    G = mox / (math.pi / 4 * D ** 2)
    return RHO_F * math.pi * D * LG * a * G ** n


def thrust_for(mox, D, a, n):
    mf = fuel_flow(mox, D, a, n)
    of = mox / mf
    Pc = 10e5
    for _ in range(60):
        pcb = min(max(Pc / 1e5, PCS[0]), PCS[-1]); ofc = min(max(of, OFS[0]), OFS[-1])
        Pn = (mox + mf) * 0.92 * float(CS([pcb, ofc])[0]) / AT
        if abs(Pn - Pc) < 20:
            break
        Pc = 0.5 * (Pc + Pn)
    pcb = min(max(Pc / 1e5, PCS[0]), PCS[-1]); ofc = min(max(of, OFS[0]), OFS[-1])
    F = (0.975 * float(CF([pcb, ofc])[0]) - EPS * PA / Pc) * Pc * AT
    return F, mf, of, Pc


def mox_for(F, D, a, n):
    lo, hi = 1e-4, 0.6
    if thrust_for(lo, D, a, n)[0] >= F:
        return lo
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        if thrust_for(mid, D, a, n)[0] < F:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-6:
            break
    return 0.5 * (lo + hi)


def load_dc(path):
    t, F = [], []
    with open(path) as f:
        rd = csv.DictReader(f)
        for r in rd:
            t.append(float(r['t_s'])); F.append(float(r['F_N']))
    return np.array(t), np.array(F)


def run_dc(path, a, n, dt=0.005):
    t, F = load_dc(path)
    tg = np.arange(t[0], t[-1], dt)
    Fg = np.interp(tg, t, F)
    D = D0; mf_tot = mo_tot = imp = burn = 0.0
    for Fi in Fg:
        if Fi < 5.0:      # engine off (coast) - below 1 % F_max
            continue
        mo = mox_for(Fi, D, a, n)
        mf = fuel_flow(mo, D, a, n)
        mf_tot += mf * dt; mo_tot += mo * dt; imp += Fi * dt; burn += dt
        D = math.sqrt(D ** 2 + 4 * mf * dt / (math.pi * RHO_F * LG))
        if D >= OD:
            break
    return dict(burn_s=burn, impulse_Ns=imp, ox_kg=mo_tot, fuel_kg=mf_tot, OF_mean=mo_tot / max(mf_tot, 1e-9),
                D_end_mm=D * 1e3, web_end_mm=(OD - D) / 2 * 1e3)


def main():
    out = dict(reviewer='independent reviewer (agent), not the author', date='2026-10-12', lstar=lstar(), dc={})
    L = out['lstar']
    print(f"V_free {L['V_free']*1e6:.1f} cm3 (author 284.6), L* {L['L_star']:.3f} m (author 1.924); parts pre {L['V_pre']*1e6:.1f} port {L['V_port']*1e6:.1f} post {L['V_post']*1e6:.1f} conv {L['V_conv']*1e6:.1f} cm3")
    a0 = 5.77e-5
    laws = {'n0.50': (a0, 0.5)}
    for nn in (0.35, 0.68):
        laws[f'n{nn:.2f}'] = (1.0e-3 / 300.0 ** nn, nn)
    dcdir = os.path.join(HUB, '01-systems-gnc/duty_cycles')
    cases = [('DC-A1', 'DC-A1_full_flight_drogue_fins_300m_v2.csv', [('n0.50', 0.6), ('n0.50', 1.0), ('n0.50', 1.5), ('n0.35', 1.5), ('n0.68', 1.5)]),
             ('DC-A2', 'DC-A2_full_flight_freefall_300m_v2.csv', [('n0.50', 1.0), ('n0.50', 1.5), ('n0.35', 1.5)]),
             ('DC-B1', 'DC-B1_hop_100m_floor20_v2.csv', [('n0.50', 1.0), ('n0.50', 1.5), ('n0.35', 1.0), ('n0.35', 1.5), ('n0.68', 1.0), ('n0.68', 1.5)]),
             ('DC-B2', 'DC-B2_hop_50m_floor20_v2.csv', [('n0.50', 1.0), ('n0.50', 1.5), ('n0.35', 1.5)])]
    for dcn, fn, runs in cases:
        for law, sc in runs:
            a, n = laws[law]
            r = run_dc(os.path.join(dcdir, fn), a * sc, n)
            r.update(law=law, scale=sc, a=a * sc, n=n)
            out['dc'][f'{dcn}|{law}|x{sc}'] = r
            print(f"{dcn} {law} x{sc}: burn {r['burn_s']:.2f} s, I {r['impulse_Ns']:.0f} N s, ox {r['ox_kg']:.3f} kg, fuel {r['fuel_kg']:.3f} kg, "
                  f"O/F {r['OF_mean']:.2f}, D_end {r['D_end_mm']:.2f} mm, web {r['web_end_mm']:.2f} mm")
    json.dump(out, open(os.path.join(HERE, 'rc05_grain.json'), 'w'), indent=1, default=float)


if __name__ == '__main__':
    main()

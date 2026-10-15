"""RC-03b MEOP basis sensitivity (reviewer).  Pintle stuck at full stroke (4 mm), initial port.

Re-uses the reviewer's own Dyer (choked HEM) + n = 0.5 engine closure from rc03_injector.py, and varies the two
inputs that the author's MEOP basis held at values that are not conservative for over-pressure:
  * feed-line loss: author law dp = 2.5 bar (mdot/0.25)^2 (= 270 kPa at 0.26 kg/s, the simulation budget) versus
    the designed hardware (Cv 3 valve + Cv 2.2 filter: 117.1 kPa at 0.26 kg/s, REPORT Table 2.6) and zero;
  * eta_c*: 0.92 nominal versus 0.96 (top of the author's own band 0.85-0.96).
Usage: python -I rc03b_meop_corner.py -> rc03b_meop_corner.json
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import CoolProp.CoolProp as CP
import rc03_injector as R

HERE = os.path.dirname(os.path.abspath(__file__))


def solve(T_C, Cd, line, eta):
    T = 273.15 + T_C
    Pv = CP.PropsSI('P', 'T', T, 'Q', 0, 'NitrousOxide')
    Pc = 32e5; mo = 0.3
    for _ in range(80):
        if line == 'author':
            dpl = 2.5e5 * (mo / 0.25) ** 2
        elif line == 'hardware':
            dpl = 117.1e3 * (mo / 0.26) ** 2
        else:
            dpl = 0.0
        g = R.G_models(T, Pv - dpl, Pc)
        mo_new = Cd * R.area(4.0e-3) * g['G_Dyer_HEMchoked']
        mf = R.KF * math.sqrt(mo_new); of = mo_new / mf
        cstar = R.CEA.get_Cstar(Pc=Pc / 1e5, MR=of)
        Pn = (mo_new + mf) * eta * cstar / R.AT
        if abs(Pn - Pc) < 5 and abs(mo_new - mo) < 1e-6:
            break
        Pc = 0.5 * (Pc + Pn); mo = 0.5 * (mo + mo_new)
    return dict(T_C=T_C, Cd=Cd, line=line, eta_cstar=eta, Pc_bar=Pc / 1e5, mdot_ox=mo, OF=of, dp_line_kPa=dpl / 1e3)


rows = []
for line in ('author', 'hardware', 'zero'):
    for eta in (0.92, 0.96):
        for T_C, Cd in ((20.0, 0.7), (25.0, 0.8), (30.0, 0.8)):
            r = solve(T_C, Cd, line, eta)
            rows.append(r)
            print(f"line {line:8s} eta {eta:.2f} T {T_C:4.1f} C Cd {Cd:.1f}: Pc {r['Pc_bar']:.2f} bar (MEOP 45), mdot_ox {r['mdot_ox']:.4f}, O/F {r['OF']:.2f}, dp_line {r['dp_line_kPa']:.0f} kPa")
json.dump(dict(reviewer='independent reviewer (agent), not the author', date='2026-10-12', rows=rows,
               author_basis=dict(T_C=30.0, Cd=0.8, eta=0.92, line='2.5 bar (mdot/0.25)^2', Pc_bar=42.85)),
          open(os.path.join(HERE, 'rc03b_meop_corner.json'), 'w'), indent=1)

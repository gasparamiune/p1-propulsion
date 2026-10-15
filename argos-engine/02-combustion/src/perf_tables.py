"""CEA performance tables for fast interpolation (Combustion v1).

Builds, for one fuel card, a shifting-equilibrium grid over Pc and O/F:
  c* [m/s], Tc [K], MW_c, gamma_c, and for each area ratio eps in EPS_GRID:
  Pc/Pe, Cf_vac (= Isp_vac*g0/c*), exit Mach and exit gamma.
Separation-aware sea-level Cf uses the Schmucker criterion
  p_sep/p_a = (1.88 M_sep - 1)^(-0.64)        [R. Schmucker, TUM report TB-7/-10/-14, 1973; as
  quoted in G. Hagemann et al., "Advanced rocket nozzles", JPP 14(5) 1998 and Östlund & Muhammad-Klingmann,
  "Supersonic flow separation with application to rocket engine nozzles", Appl. Mech. Rev. 58 (2005)]
and the Summerfield criterion p_sep/p_a ~ 0.4 (Summerfield, Foster & Swan, Jet Propulsion 24, 1954).
After separation the wall pressure downstream is taken = p_a (no recovery credit, conservative for thrust).
"""
from __future__ import annotations
import json, os, sys, time
import numpy as np
from scipy.interpolate import RegularGridInterpolator

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cea_cards

G0 = 9.80665
PA_SL = 101325.0
PC_GRID_BAR = np.array([1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20, 22, 25, 28, 30, 33, 36])
OF_GRID = np.round(np.arange(1.0, 14.01, 0.5), 3)
EPS_GRID = np.array([1.05, 1.2, 1.4, 1.6, 1.8, 2.0, 2.25, 2.5, 2.75, 3.0, 3.5, 4.0, 5.0])


def build(fuel='ABS_TYP_v1', out_dir=None, frozen=0):
    from rocketcea.cea_obj import CEA_Obj
    cea_cards.register_all()
    c = CEA_Obj(oxName='N2O', fuelName=fuel)   # English units object: Pc psia, c* ft/s, T degR
    nP, nO, nE = len(PC_GRID_BAR), len(OF_GRID), len(EPS_GRID)
    cstar = np.zeros((nP, nO)); Tc = np.zeros((nP, nO)); MW = np.zeros((nP, nO)); gam = np.zeros((nP, nO))
    PcPe = np.zeros((nP, nO, nE)); Cfv = np.zeros((nP, nO, nE)); Me = np.zeros((nP, nO, nE)); game = np.zeros((nP, nO, nE))
    t0 = time.time()
    for i, pb in enumerate(PC_GRID_BAR):
        pc_psia = pb * 14.5037738
        for j, of in enumerate(OF_GRID):
            isp_v, cs, tc = c.get_IvacCstrTc(Pc=pc_psia, MR=of, eps=2.0, frozen=frozen)
            cstar[i, j] = cs * 0.3048
            Tc[i, j] = tc / 1.8
            mw, g = c.get_Chamber_MolWt_gamma(Pc=pc_psia, MR=of, eps=2.0)
            MW[i, j] = mw; gam[i, j] = g
            for k, e in enumerate(EPS_GRID):
                ispv = c.get_Isp(Pc=pc_psia, MR=of, eps=e, frozen=frozen)
                PcPe[i, j, k] = c.get_PcOvPe(Pc=pc_psia, MR=of, eps=e, frozen=frozen)
                Cfv[i, j, k] = ispv * G0 / (cs * 0.3048)
                Me[i, j, k] = c.get_MachNumber(Pc=pc_psia, MR=of, eps=e, frozen=frozen)
                _, ge = c.get_exit_MolWt_gamma(Pc=pc_psia, MR=of, eps=e, frozen=frozen)
                game[i, j, k] = ge
    tab = dict(fuel=fuel, frozen=frozen, Pc_bar=PC_GRID_BAR.tolist(), OF=OF_GRID.tolist(), eps=EPS_GRID.tolist(),
               cstar=cstar.tolist(), Tc=Tc.tolist(), MW=MW.tolist(), gamma=gam.tolist(), PcPe=PcPe.tolist(),
               Cf_vac=Cfv.tolist(), Me=Me.tolist(), gamma_e=game.tolist(),
               source=f"CEA via RocketCEA {__import__('rocketcea').__version__}, {'frozen' if frozen else 'shifting'} equilibrium, card {fuel}",
               date='2026-10-11', version='v1')
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        fn = os.path.join(out_dir, f"perf_table_{fuel}_{'frozen' if frozen else 'shifting'}_v1.json")
        json.dump(tab, open(fn, 'w'))
        print('wrote', fn, f'{time.time()-t0:.1f}s')
    return tab


class Perf:
    """Interpolator over a perf table. Inputs Pc [Pa], O/F, eps."""
    def __init__(self, tab):
        if isinstance(tab, str):
            tab = json.load(open(tab))
        self.tab = tab
        P = np.array(tab['Pc_bar']) * 1e5; O = np.array(tab['OF']); E = np.array(tab['eps'])
        self.P, self.O, self.E = P, O, E
        lp = np.log(P)
        kw = dict(bounds_error=False, fill_value=None)
        self._cs = RegularGridInterpolator((lp, O), np.array(tab['cstar']), **kw)
        self._tc = RegularGridInterpolator((lp, O), np.array(tab['Tc']), **kw)
        self._mw = RegularGridInterpolator((lp, O), np.array(tab['MW']), **kw)
        self._g = RegularGridInterpolator((lp, O), np.array(tab['gamma']), **kw)
        self._pcpe = RegularGridInterpolator((lp, O, np.log(E)), np.log(np.array(tab['PcPe'])), **kw)
        self._cfv = RegularGridInterpolator((lp, O, np.log(E)), np.array(tab['Cf_vac']), **kw)
        self._me = RegularGridInterpolator((lp, O, np.log(E)), np.array(tab['Me']), **kw)

    def _pt(self, Pc, OF):
        return np.log(np.clip(Pc, self.P[0], self.P[-1])), np.clip(OF, self.O[0], self.O[-1])

    def cstar(self, Pc, OF):
        return float(self._cs(self._pt(Pc, OF)))

    def Tc(self, Pc, OF):
        return float(self._tc(self._pt(Pc, OF)))

    def gamma(self, Pc, OF):
        return float(self._g(self._pt(Pc, OF)))

    def MW(self, Pc, OF):
        return float(self._mw(self._pt(Pc, OF)))

    def pe_pc(self, Pc, OF, eps):
        lp, of = self._pt(Pc, OF)
        return float(np.exp(-self._pcpe((lp, of, np.log(eps)))))

    def cf_vac(self, Pc, OF, eps):
        lp, of = self._pt(Pc, OF)
        return float(self._cfv((lp, of, np.log(eps))))

    def mach(self, Pc, OF, eps):
        lp, of = self._pt(Pc, OF)
        return float(self._me((lp, of, np.log(eps))))

    def cf_amb(self, Pc, OF, eps, Pa=PA_SL, criterion='schmucker'):
        """Ambient Cf (ideal, before eta_cf). Returns (Cf, eps_sep or None, pe/pa).
        If the wall pressure falls below the separation pressure upstream of the exit, the flow is
        assumed to separate there and the nozzle behaves as one with eps = eps_sep."""
        pe = self.pe_pc(Pc, OF, eps) * Pc
        def psep_ratio(e):
            if criterion == 'summerfield':
                return 0.4
            M = self.mach(Pc, OF, e)
            return (1.88 * M - 1.0) ** -0.64
        if pe / Pa >= psep_ratio(eps):
            return self.cf_vac(Pc, OF, eps) - eps * Pa / Pc, None, pe / Pa
        # find eps_sep by bisection on log eps
        lo, hi = 1.05, eps
        for _ in range(40):
            mid = np.sqrt(lo * hi)
            pw = self.pe_pc(Pc, OF, mid) * Pc
            if pw / Pa >= psep_ratio(mid):
                lo = mid
            else:
                hi = mid
        es = lo
        return self.cf_vac(Pc, OF, es) - es * Pa / Pc, es, pe / Pa


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
    fuels = sys.argv[2].split(',') if len(sys.argv) > 2 else ['ABS_TYP_v1']
    for f in fuels:
        build(f, out_dir=out)

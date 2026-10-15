"""Propellant / tank sizing on the 1-D model (nominal, zero-dispersion flight)."""
import numpy as np
import CoolProp.CoolProp as CP
from . import run1d as r

RHO_L_25C = CP.PropsSI('D', 'T', 298.15, 'Q', 0, 'NitrousOxide')
FILL_MAX = 0.85            # ASSUMED: liquid volume fraction at 25 C (15 % ullage, hydraulic-lock margin)


def tank_volume_for(m_load):
    return m_load / (FILL_MAX * RHO_L_25C)


def size(profile, h_target, floor, reserve=0.20, ballast=0.0, m0=1.6, **kw):
    """Smallest N2O load whose nominal flight lands with usable liquid >= reserve x liquid used.
    Returns dict (or None if the profile does not close below 6 kg of N2O)."""
    def trial(m):
        V = tank_volume_for(m)
        par = r.make_par(profile=profile, h_target=h_target, floor=floor, m_n2o=m, tank_V=V,
                         ballast=ballast, **kw)
        res, rec = r.fly(par)
        resid = 0.03 * m
        usable_left = max(res["m_liq_left"] - resid, 0.0)
        # liquid used = initial liquid - liquid left
        liq0 = rec[0, r.REC_COLS.index("m_n2o_liquid_kg")]
        used = liq0 - res["m_liq_left"]
        ok = (res["landed"] > 0.5 and abs(res["td_v"]) <= 2.0 and res["exhausted"] < 0.5
              and usable_left >= reserve * used)
        return ok, res, rec, V
    lo, hi = 0.3, 6.0
    ok, res, rec, V = trial(hi)
    if not ok:
        return None
    for _ in range(18):
        mid = 0.5 * (lo + hi)
        if trial(mid)[0]:
            hi = mid
        else:
            lo = mid
    ok, res, rec, V = trial(hi)
    out = dict(m_n2o=hi, tank_V=V, **res)
    out["m_liftoff"] = rec[0, r.REC_COLS.index("m_kg")]
    out["impulse"] = float(np.trapezoid(rec[:, r.REC_COLS.index("F_N")], rec[:, 0]))
    return out, rec

"""1-D landing-closure Monte Carlo (first pass; the 6-DOF MC supersedes it for lateral/tilt).

Dispersions (1 sigma unless stated; brief section C.7):
  thrust scale N(1, 0.05); Isp scale N(1, 0.05); ignition delay U(0.2, 0.6) s;
  throttle lag tau x U(0.7, 1.5); dry mass N(1, 0.05); tank temperature U(15, 25) C;
  navigation: altitude bias N(0, 0.05) m, velocity bias N(0, 0.05) m/s (ASSUMED filtered
  LiDAR/GNSS/IMU class); guidance mass-knowledge error N(0, 0.03); accelerometer bias along
  the axis N(0, 0.10) m/s2 (ASSUMED, after pad calibration);
  tail-first axial coefficient x U(0.7, 1.3); drogue CdA x U(0.85, 1.15).
Success (1-D): touchdown with |v_z| <= 2.0 m/s, no propellant exhaustion before touchdown.
"""
import numpy as np
from . import run1d as r
from . import sizing


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    hw = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - hw), min(1.0, c + hw))


def draw(rng, n):
    return dict(
        thrust_scale=rng.normal(1.0, 0.05, n),
        isp_scale=rng.normal(1.0, 0.05, n),
        t_ign=rng.uniform(0.2, 0.6, n),
        tau_f=rng.uniform(0.7, 1.5, n),
        dry_scale=rng.normal(1.0, 0.05, n),
        T0=rng.uniform(288.15, 298.15, n),
        h_bias=rng.normal(0.0, 0.05, n),
        v_bias=rng.normal(0.0, 0.05, n),
        m_est_err=rng.normal(0.0, 0.03, n),
        ca_tf_f=rng.uniform(0.7, 1.3, n),
        drogue_f=rng.uniform(0.85, 1.15, n),
        a_bias=rng.normal(0.0, 0.10, n),
    )


def run_mc(n=500, seed=1, profile=0, h_target=300.0, floor=0.2, m_n2o=1.6, ballast=0.0,
           descent="freefall", drogue_CdA=0.0, tau=0.100 / 2.197, hslam=None, t_ign_est=0.40,
           ign_lo=0.2, ign_hi=0.6, quant=0.01, slew=5.0, kd=0.70, extra=None):
    rng = np.random.default_rng(seed)
    d = draw(rng, n)
    d["t_ign"] = rng.uniform(ign_lo, ign_hi, n) if ign_hi > ign_lo else np.full(n, ign_lo)
    V = sizing.tank_volume_for(m_n2o)
    geo_CA_tf = 1.05
    rows = []
    for i in range(n):
        kw = dict(profile=profile, h_target=h_target, floor=floor, m_n2o=m_n2o, tank_V=V,
                  ballast=ballast, descent=descent, drogue_CdA=drogue_CdA * d["drogue_f"][i],
                  tau=tau * d["tau_f"][i], hslam=hslam, t_ign=d["t_ign"][i], t_ign_est=t_ign_est,
                  thrust_scale=d["thrust_scale"][i], isp_scale=d["isp_scale"][i], T0=d["T0"][i],
                  h_bias=d["h_bias"][i], v_bias=d["v_bias"][i], m_est_err=d["m_est_err"][i],
                  dry_scale=d["dry_scale"][i], CA_tf=geo_CA_tf * d["ca_tf_f"][i], quant=quant,
                  a_bias=d["a_bias"][i],
                  slew=slew, kd=kd)
        if extra:
            kw.update(extra)
        par = r.make_par(**kw)
        res, rec = r.fly(par, rec_dt=0.05, nrec=4000)
        liq0 = rec[0, r.REC_COLS.index("m_n2o_liquid_kg")]
        usable_left = max(res["m_liq_left"] - 0.03 * m_n2o, 0.0)
        ok = bool(res["landed"] > 0.5 and abs(res["td_v"]) <= 2.0 and res["exhausted"] < 0.5)
        rows.append(dict(run=i, ok=ok, td_v=res["td_v"], h_max=res["h_max"], prop_used=res["prop_used"],
                         usable_left=usable_left, margin_frac=usable_left / max(liq0 - res["m_liq_left"], 1e-6),
                         exhausted=res["exhausted"], m_land=res["m_land"], v_ign=res["v_ign"],
                         h_ign=res["h_ign"], burn=res["burn_time"],
                         hslam_used=float(res["hslam_used"]), cut=float(res["cut_before_contact"]),
                         **{k: d[k][i] for k in d}))
    ok = np.array([x["ok"] for x in rows])
    k = int(ok.sum())
    tdv = np.array([x["td_v"] for x in rows])
    summ = dict(n=n, success=k / n, ci95=wilson(k, n), td_v_mean=float(tdv.mean()),
                td_v_std=float(tdv.std()), td_v_p01=float(np.percentile(tdv, 1)),
                td_v_p99=float(np.percentile(tdv, 99)),
                exhausted=float(np.mean([x["exhausted"] for x in rows])),
                margin_p05=float(np.percentile([x["usable_left"] for x in rows], 5)))
    return summ, rows


def sensitivity(rows, keys, metric="td_v", fail_key="ok"):
    """Spearman rank correlation of each dispersion with |metric| and with failure."""
    from scipy.stats import spearmanr
    y = np.abs(np.array([x[metric] for x in rows]))
    f = 1.0 - np.array([float(x[fail_key]) for x in rows])
    out = []
    for k in keys:
        xk = np.array([x[k] for x in rows])
        rho_m = spearmanr(xk, y).statistic
        rho_f = spearmanr(xk, f).statistic if f.std() > 0 else 0.0
        out.append((k, float(rho_m), float(rho_f)))
    out.sort(key=lambda t: -abs(t[1]))
    return out

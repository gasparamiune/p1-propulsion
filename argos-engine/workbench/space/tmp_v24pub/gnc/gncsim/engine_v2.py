"""GNC engine model v2: built from combustion.json (read at run time, never hard-coded).

combustion.json v1 provides a throttle map at the initial port (F -> Pc, mdot_ox, mdot_f, O/F, Isp,
injector inlet pressure P1) for two tank temperatures. With the regression exponent n = 0.5 the
fuel flow does not depend on the port diameter (mdot_f ~ sqrt(mdot_ox)), so the map is used for
every port diameter (combustion's max-thrust case confirms constant O/F 7.76 while the port grows
25 -> 42 mm). The thrust ceiling follows combustion's stability rule Pc <= P1 / 1.25, with the
feed loss P_tank - P1 = K_feed mdot_ox^2 fitted to the map (DERIVED). Pintle-area saturation is
not reached in combustion's max-thrust case (lift 2.65 of 4 mm) and is not modelled.

Returns the same table dictionary as params.engine_tables so sim1d (and sim6) can use either map.
"""
import csv
import json
import os
import numpy as np

IFACE = os.environ.get("GNC_IFACE", "/mnt/project-files/engine/interfaces")  # lead fallback hub during mount outages


def load_combustion(path=os.path.join(IFACE, "combustion.json")):
    with open(path) as f:
        return json.load(f)


def _read_map(csv_path):
    rows = []
    with open(csv_path) as f:
        lines = [ln for ln in f if not ln.startswith("#")]
    for r in csv.DictReader(lines):
        rows.append({k: float(v) if v not in ("", None) else np.nan for k, v in r.items() if k != "limit"})
    return rows


SNAP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "iface_snapshot")


def _map_path(csv_path):
    """Shared-folder path if readable, else the local snapshot copy (network mount outages)."""
    try:
        with open(csv_path) as f:
            f.read(1)
        return csv_path
    except OSError:
        alt = os.path.join(SNAP, os.path.basename(csv_path))
        if os.path.exists(alt):
            return alt
        raise


def combustion_tables(comb=None, F_max=500.0):
    comb = comb or load_combustion()
    op = comb["operating_points"]
    rows = _read_map(_map_path(op["throttle_map_csv"]))
    T0 = rows[0]["T_tank"]
    blk = sorted([r for r in rows if abs(r["T_tank"] - T0) < 1e-6], key=lambda r: r["F"])
    F = np.array([r["F"] for r in blk])
    mox = np.array([r["mox"] for r in blk])
    mf = np.array([r["mf"] for r in blk])
    pc = np.array([r["Pc"] for r in blk])
    isp = np.array([r["Isp"] for r in blk])
    of = np.array([r["OF"] for r in blk])
    # feed loss fit P_tank - P1 = K_feed mdot_ox^2 (least squares over all rows)
    dp = np.array([r["P_tank"] - r["P1"] for r in rows])
    mo = np.array([r["mox"] for r in rows])
    K_feed = float(np.sum(dp * mo ** 2) / np.sum(mo ** 4))
    # dense F grid: monotone PCHIP in log-log between the map points, linear extrapolation in
    # log-log beyond (only used for thrust-scale dispersions up to ~1.2 F_max and down to 0)
    from scipy.interpolate import PchipInterpolator
    lF = np.log(F)

    def fit(y):
        p = PchipInterpolator(lF, np.log(y), extrapolate=False)
        s_lo = (np.log(y[1]) - np.log(y[0])) / (lF[1] - lF[0])
        s_hi = (np.log(y[-1]) - np.log(y[-2])) / (lF[-1] - lF[-2])

        def f(x):
            x = np.atleast_1d(x).astype(float)
            out = np.zeros_like(x)
            lx = np.log(np.maximum(x, 1e-6))
            m = (lx >= lF[0]) & (lx <= lF[-1])
            out[m] = np.exp(p(lx[m]))
            lo = lx < lF[0]
            out[lo] = np.exp(np.log(y[0]) + s_lo * (lx[lo] - lF[0]))
            hi = lx > lF[-1]
            out[hi] = np.exp(np.log(y[-1]) + s_hi * (lx[hi] - lF[-1]))
            out[x <= 0] = 0.0
            return out
        return f
    f_mox, f_mf, f_pc, f_isp = fit(mox), fit(mf), fit(pc), fit(isp)
    grain = comb["gas_path"]["grain"]
    D0 = grain["port"]["initial_diameter_m"]["v"]
    Do = grain["outer_diameter_m"]["v"]
    Dg = np.linspace(D0, Do, 6)
    Fg = np.linspace(0.0, 1.3 * F_max, 66)
    one = np.ones(Dg.size)
    t_mox = np.outer(f_mox(Fg), one)
    t_mf = np.outer(f_mf(Fg), one)
    t_pc = np.outer(f_pc(Fg), one)
    t_isp = np.outer(f_isp(Fg), one)
    t_pc[0, :] = 1.0e5
    # ceiling: largest F with Pc(F) <= (P_tank - K_feed mox(F)^2) / 1.25
    Pg = np.linspace(2.0e6, 7.0e6, 41)
    Ff = np.linspace(1.0, 1.6 * F_max, 3000)
    pcf, mof = f_pc(Ff), f_mox(Ff)
    ceil = np.zeros((Pg.size, Dg.size))
    for i, Pt in enumerate(Pg):
        ok = pcf <= (Pt - K_feed * mof ** 2) / 1.25
        ceil[i, :] = Ff[ok].max() if ok.any() else 0.0
    meta = dict(source="combustion.json " + comb.get("version", "?"), map_csv=op["throttle_map_csv"],
                T_tank_map=T0, K_feed=K_feed, ceiling_rule="Pc <= P1/1.25 (combustion.json thrust_ceiling_rule)",
                grain=dict(L=grain["length_m"]["v"], Do=Do, Dp0=D0, rho=grain["density_kg_m3"]["v"],
                           mass=grain["mass_kg"]["v"]),
                F_pts=F.tolist(), Isp_pts=isp.tolist(), OF_pts=of.tolist(), Pc_pts=pc.tolist())
    return dict(K_inj=np.nan, P_design=np.nan, Dg=Dg, Fg=Fg, mox=t_mox, mf=t_mf, pc=t_pc, isp=t_isp, Pg=Pg,
                ceil=ceil, meta=meta)


# ---------------------------------------------------------------------------------------------------------------
# Relay correction (2026-10-12): combustion v2 performance before combustion.json v2 is published.
# data/relay/engine_correction_v2.json (scripts/m2_engine_relay.py) holds thrust-binned factors k_ox(F), k_f(F) =
# combustion v2 mass flow / this v1 map at the same thrust, from combustion's S230 duty-cycle runs (the runs behind
# the lead's relayed totals). Applied only while the hub still carries the combustion.json version named in the
# correction file; once combustion.json v2 is published its own map replaces the correction.
G0_ = 9.80665
CORR_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "relay",
                         "engine_correction_v2.json")


def load_relay_correction(comb, path=CORR_PATH):
    """Return the correction dict if it exists and applies to this combustion.json version, else None."""
    if not os.path.exists(path):
        return None
    with open(path) as f:
        corr = json.load(f)
    if corr.get("applies_to_combustion_json_version") != comb.get("version"):
        return None
    return corr


def apply_relay(tab, corr):
    """Copy of the engine tables with mdot_ox, mdot_f scaled by the thrust-binned factors (constant beyond the
    anchor range); Isp recomputed; the thrust ceiling is kept (relay: minimum ceiling 548 N > 500 N, and the v1
    ceiling never binds in the 6-DOF flights)."""
    out = dict(tab)
    Fa = np.array(corr["anchors"]["F_N"])
    kox = np.interp(tab["Fg"], Fa, np.array(corr["anchors"]["k_ox"]))
    kf = np.interp(tab["Fg"], Fa, np.array(corr["anchors"]["k_f"]))
    out["mox"] = tab["mox"] * kox[:, None]
    out["mf"] = tab["mf"] * kf[:, None]
    isp = np.zeros_like(tab["isp"])
    m = tab["Fg"] > 0
    isp[m, :] = tab["Fg"][m, None] / ((out["mox"][m, :] + out["mf"][m, :]) * G0_)
    out["isp"] = isp
    meta = dict(tab["meta"])
    meta["relay_correction"] = dict(file=os.path.basename(CORR_PATH), version=corr.get("version"),
                                    anchors=corr["anchors"], source=corr.get("source"))
    meta["source"] = meta.get("source", "") + " + relay correction " + str(corr.get("version"))
    out["meta"] = meta
    return out


def relay_combustion(comb, corr):
    """combustion.json v1 dict with the relayed S230 grain (length, mass, aft end) for the vehicle model."""
    import copy
    c = copy.deepcopy(comb)
    g = c["gas_path"]["grain"]
    gr = corr["grain"]
    g["length_m"] = dict(v=gr["length_m"], tag=gr["tag_length"])
    g["mass_kg"] = dict(v=gr["mass_kg"], tag=gr["tag_mass"])
    if "x_face_end_m" in g:
        g["x_face_end_m"] = dict(v=g["x_face_end_m"]["v"] + gr["length_m"] - comb["gas_path"]["grain"]["length_m"]["v"],
                                 tag="DERIVED v1 aft end + grain growth (relay S230)")
    c["version"] = comb.get("version", "?") + "+relay"
    return c

"""GNC engine model v2: built from combustion.json (read at run time, never hard-coded).

combustion.json v1 provides a throttle map at the initial port (F -> Pc, mdot_ox, mdot_f, O/F, Isp,
injector inlet pressure P1) for two tank temperatures. With the regression exponent n = 0.5 the
fuel flow does not depend on the port diameter (mdot_f ~ sqrt(mdot_ox)), so the map is used for
every port diameter (combustion's max-thrust case confirms constant O/F 7.76 while the port grows
25 -> 42 mm). The thrust ceiling follows combustion's stability rule Pc <= P1 / 1.25, with the
feed loss P_tank - P1 = K_feed mdot_ox^2 fitted to the map (DERIVED). Pintle-area saturation is
not reached in combustion's max-thrust case (lift 2.65 of 4 mm) and is not modelled.

Returns the same table dictionary as params.engine_tables so sim1d (and sim6) can use either map.

combustion.json v2 (2026-10-12) publishes a map on a P_tank x D_port x thrust-fraction grid with the published thrust
ceiling F_ceiling_N = min(stroke 4 mm, injector dP/Pc >= 0.25) per (P_tank, D_port). combustion_tables() recognises the
format from the CSV header: the performance tables (F -> mdot_ox, mdot_f, Pc, Isp, per D_port) come from the tank-pressure
level nearest the N2O saturation pressure at 20 C (the kernel tables are F x D_port; the spread of the map across tank
pressure is recorded in meta), and the ceiling table is the published F_ceiling_N, linear in P_tank between the levels
and linearly extrapolated outside them (DERIVED). The v1 code path is unchanged.
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
    """Shared-folder path if readable, else a copy beside the interface files (GNC_IFACE), else the local snapshot copy
    (network mount outages; hub folders not yet synchronised)."""
    try:
        with open(csv_path) as f:
            f.read(1)
        return csv_path
    except OSError:
        for d in (IFACE, SNAP):
            alt = os.path.join(d, os.path.basename(csv_path))
            if os.path.exists(alt):
                return alt
        raise


def _read_map_any(csv_path):
    """Rows of a throttle-map CSV ('#' lines skipped); numeric columns as float, text columns kept as text."""
    rows = []
    with open(csv_path) as f:
        lines = [ln for ln in f if not ln.startswith("#")]
    for r in csv.DictReader(lines):
        d = {}
        for k, v in r.items():
            try:
                d[k] = float(v) if v not in ("", None) else np.nan
            except ValueError:
                d[k] = v
        rows.append(d)
    return rows


def _loglog_fit(F, y):
    """Monotone PCHIP in log-log between the map points, linear in log-log beyond (as the v1 tables)."""
    from scipy.interpolate import PchipInterpolator
    lF = np.log(F)
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


def combustion_tables_v2map(comb, path, F_max=500.0):
    """Engine tables from the combustion.json v2 map (P_tank_Pa, D_port_m, frac, F_N, Pc_Pa, mdot_ox, mdot_f, OF,
    Isp_SL_s, F_ceiling_N, ...)."""
    import CoolProp.CoolProp as CP
    op = comb["operating_points"]
    rows = [r for r in _read_map_any(path) if np.isfinite(r.get("F_N", np.nan))]
    P_lv = sorted(set(r["P_tank_Pa"] for r in rows))
    D_lv = sorted(set(r["D_port_m"] for r in rows))
    P_sat20 = CP.PropsSI("P", "T", 293.15, "Q", 0, "NitrousOxide")
    Pb = min(P_lv, key=lambda q: abs(q - P_sat20))
    Fg = np.linspace(0.0, 1.3 * F_max, 66)
    Dg = np.array(D_lv, dtype=float)
    t_mox = np.zeros((Fg.size, Dg.size)); t_mf = np.zeros_like(t_mox); t_pc = np.zeros_like(t_mox); t_isp = np.zeros_like(t_mox)
    spread_P = 0.0
    spread_D = 0.0
    ref = None
    for j, D in enumerate(D_lv):
        blk = sorted([r for r in rows if r["P_tank_Pa"] == Pb and r["D_port_m"] == D], key=lambda r: r["F_N"])
        F = np.array([r["F_N"] for r in blk])
        cols = {k: np.array([r[k] for r in blk]) for k in ("mdot_ox", "mdot_f", "Pc_Pa", "Isp_SL_s", "OF")}
        t_mox[:, j] = _loglog_fit(F, cols["mdot_ox"])(Fg)
        t_mf[:, j] = _loglog_fit(F, cols["mdot_f"])(Fg)
        t_pc[:, j] = _loglog_fit(F, cols["Pc_Pa"])(Fg)
        t_isp[:, j] = _loglog_fit(F, cols["Isp_SL_s"])(Fg)
        if ref is None:
            ref = (F, cols)
        else:
            spread_D = max(spread_D, float(np.max(np.abs(cols["mdot_ox"] + cols["mdot_f"] - ref[1]["mdot_ox"] - ref[1]["mdot_f"])
                                                  / (ref[1]["mdot_ox"] + ref[1]["mdot_f"]))))
        for Pq in P_lv:
            b2 = sorted([r for r in rows if r["P_tank_Pa"] == Pq and r["D_port_m"] == D], key=lambda r: r["F_N"])
            if len(b2) == len(blk):
                m2 = np.array([r["mdot_ox"] + r["mdot_f"] for r in b2])
                spread_P = max(spread_P, float(np.max(np.abs(m2 - cols["mdot_ox"] - cols["mdot_f"]) / (cols["mdot_ox"] + cols["mdot_f"]))))
    t_pc[0, :] = 1.0e5
    Pg = np.linspace(2.0e6, 7.0e6, 41)
    ceil = np.zeros((Pg.size, Dg.size))
    for j, D in enumerate(D_lv):
        pts = sorted({(r["P_tank_Pa"], r["F_ceiling_N"]) for r in rows if r["D_port_m"] == D})
        Pp = np.array([a for a, _ in pts]); Fc = np.array([b for _, b in pts])
        c = np.interp(Pg, Pp, Fc)
        lo = Pg < Pp[0]
        c[lo] = Fc[0] + (Fc[1] - Fc[0]) / (Pp[1] - Pp[0]) * (Pg[lo] - Pp[0])
        hi = Pg > Pp[-1]
        c[hi] = Fc[-1] + (Fc[-1] - Fc[-2]) / (Pp[-1] - Pp[-2]) * (Pg[hi] - Pp[-1])
        ceil[:, j] = np.maximum(c, 0.0)
    grain = comb["gas_path"]["grain"]
    F0, c0 = ref
    rule = op.get("thrust_ceiling_rule", {})
    meta = dict(source="combustion.json " + comb.get("version", "?"), map_csv=op["throttle_map_csv"], map_file_used=path,
                map_format="v2: P_tank x D_port x thrust fraction", P_tank_levels_Pa=P_lv, D_port_levels_m=D_lv,
                P_tank_block_for_performance_Pa=Pb, P_sat_20C_Pa=P_sat20,
                performance_spread_across_P_tank=spread_P, performance_spread_across_D_port=spread_D,
                ceiling_rule=(rule.get("v") if isinstance(rule, dict) else str(rule)) or "F_ceiling_N column",
                ceiling_extrapolation="DERIVED linear in P_tank outside the map levels, >= 0",
                grain=dict(L=grain["length_m"]["v"], Do=grain["outer_diameter_m"]["v"], Dp0=grain["port"]["initial_diameter_m"]["v"],
                           rho=grain["density_kg_m3"]["v"], mass=grain["mass_kg"]["v"]),
                F_pts=F0.tolist(), Isp_pts=c0["Isp_SL_s"].tolist(), OF_pts=c0["OF"].tolist(), Pc_pts=c0["Pc_Pa"].tolist())
    return dict(K_inj=np.nan, P_design=np.nan, Dg=Dg, Fg=Fg, mox=t_mox, mf=t_mf, pc=t_pc, isp=t_isp, Pg=Pg, ceil=ceil,
                meta=meta)


def combustion_tables(comb=None, F_max=500.0):
    comb = comb or load_combustion()
    op = comb["operating_points"]
    mpath = _map_path(op["throttle_map_csv"])
    with open(mpath) as f:
        hdr = next((ln for ln in f if not ln.startswith("#")), "")
    if "P_tank_Pa" in hdr and "frac" in hdr and "F_ceiling_N" in hdr:
        return combustion_tables_v2map(comb, mpath, F_max)
    rows = _read_map(mpath)
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


def s230_growth_on_cad_v2(path=CORR_PATH):
    """Engine dry-mass growth of the S230 gas path relative to the CAD v2 engine of mechanical.json v1 (lead relay
    2026-10-12, relay_values.engine_dry_mass_growth_kg), read without the combustion-version check. Used only when the
    published combustion.json v2.x engine is flown on mechanical.json v1 (the attribution run v3a): the S230 engine is
    then physically present while mechanical.json v1 still carries the CAD v2 mass. None if the file is absent."""
    if not os.path.exists(path):
        return None
    with open(path) as f:
        corr = json.load(f)
    return (corr.get("relay_values") or {}).get("engine_dry_mass_growth_kg")


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

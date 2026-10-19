"""m2_rev4_payload v1.1 (GNC rev4, 2026-10-19): PAYLOAD SENSITIVITY - "what weight can we carry?" (founder via the lead,
2026-10-13 18:55Z after CHANGELOG 214; scope restated by the lead on 2026-10-19: apogee loss per kg of payload at +0.5,
+1, +2, +3 kg on the v3.5.1 vehicle with the 2.0 kg tank, and the N2O load / tank length that carries 1 kg and 2 kg to
210 m with the landing still meeting its success criterion; deterministic plus a small Monte Carlo).

Vehicle: massprops v3.5.1 FROZEN (488b47f9d55ff91b) as the P2 arm v351: iface_v351 (derived mechanical.json) + cfg ballast
0.99744 kg at station 0.4426 m (landing mass +1.3672 kg against the v3d ledger), A1 base cfg (FSW-R2, decided release
rule, purge G73, Combustion v2.4 line-state tables), sim6 v2.9-dev (gnc_dev3, the P2 production tree; no file changed).
Tank station (lead integration note 2026-10-13 ~19:05Z): the v3d tank inner bottom at station 0.55 m overlaps the v3.5.1
engine top (0.558 m on RV-1c, pivot 0.203 m). The geometry enters the CG / inertia here (tank tube item, liquid N2O,
P09 valve and P12 ECU are tied to the tank bottom), so EVERY arm of this script flies the tank moved up to 0.58 m (+0.03 m;
inner 0.580-1.024 m at 2.00 kg). Control arm: payload 0 with the moved tank, paired with the P2 v351 table (tank 0.55 m).
Payload: point mass dm at the A05 avionics station, station 1.15 m (ledger item 'A05 avionics (FC, IMU, GNSS, LiDAR,
radio)', vehicle-station frame of the v3d ledger), exact mass (no dry-scale dispersion), fixed station (no airframe
axial-shift dispersion), known to the flight software through the pad weighing like the rest of the vehicle (mest
m_hat(0) = m(0) + mest_w). Its own inertia about its CG is not represented (payload shape unknown: TO-VERIFY by whoever
defines the payload). Implementation: two wrappers installed by this script on gncsim.vehicle (mass_ledger_v3 appends
the payload item 'B01p ...'; reference_geometry_v3 sets tank_z_bot_inner). Part 'check' verifies: payload 0 and tank 0.55
equal the stored P2 table column for column (runs 0-3); payload dm adds exactly dm to the liftoff mass; first moments.
Parts (GNC_PL_PARTS):
  check  the checks above (light)
  det    DETERMINISTIC (nominal flight: no wind, no sensor noise, no gust, nominal dispersions; m2_prop_closure basis)
         on both main bases and both line states: (a) payload dm in {0, 0.5, 1, 2, 3} kg at the fixed 2.00 kg load over the
         apogee grid; the iso-margin apogee h_iso(dm) = the apogee target at which the touchdown liquid margin above the
         80 g dip onset (the line-208 onset) equals the dm 0 margin at 210 m (the 210 m line-208 band), linear interpolation;
         apogee loss per kg = (210 - h_iso) / dm. A second reading matches the margin as a fraction of the N2O used.
         (b) load sweep at 210 m for dm 1 and 2: the iso-margin N2O load (tank volume at 85 % liquid fill at 25 C, tube
         lengthened by the RV-1c ledger rule, tank bottom at 0.58 m); (c) liftoff T/W = 500 N / (m_liftoff g0) and landing
         floor ratio = floor x 500 N / (m_touchdown g0) for every case (rated-thrust basis, as m2_prop_closure).
  mc     SMALL MONTE CARLO, liq line state (the binding state of P2: liq band 210 m, pw 220 m), main bases A1_none +
         A1J_pc, seed 101, runs 0..GNC_PL_N-1 (default 250 per base): payload 0 control at 210 m; dm 0.5 / 1 / 2 / 3 at the
         deterministic iso-margin apogee (rounded down to 5 m) and dm 1 / 2 at 210 m (P at 210 m); dm 1 / 2 at their
         iso-margin load at 210 m. Read against the v3d reference liq|G73|h285 (runs 0..N-1) with the line-208 statistics
         (informational at this N: the band itself needs the full sweep) and against the P2 v351 h210 table (same runs).
  eval   tables -> out/rev4/payload/payload_rev4.json
v1.1 (v1.0 in superseded_rev4/; flights unchanged): the v1.0 MC showed that the deterministic iso-margin apogee is not
the binding limit below ~180 m: with dispersions the drogue-descent / purge-commit / relight timeline (amendment G gate:
quasi-steady descent >= pgg_tdmin + pgg_tqs after deployment, commit pgg_Tc ahead of T_fire) starts the landing burn too low
(h_ign p50 30 m at 155 m apogee, 0.4 m at 115 m). v1.1 adds the relight height, purge-commit source / margin and delay to
the deterministic records, extra MC arms by env GNC_PL_EXTRA ('dm:h[:m];...', e.g. the apogee floor at payload 0), and
per-arm failure modes and relight heights in the evaluation.
SIM (flights) / DERIVED (interpolations, T/W) / ASSUMED (payload as a point mass, tank layout). No hardware data; not
physical approval."""
import csv
import gzip
import hashlib
import json
import math
import os
import sys
import time
from collections import OrderedDict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m2_rev4_p2 as P2  # noqa: E402

F3 = P2.F3
F = P2.F
R = P2.R
s6 = P2.s6

VERSION = "m2_rev4_payload v1.1"
SP = "/home/claude/work/space"
OUT = os.environ.get("GNC_PL_OUT", f"{SP}/out/rev4/payload")
PARTS = [p for p in os.environ.get("GNC_PL_PARTS", "check,det,mc,eval").split(",") if p]
N_MC = int(os.environ.get("GNC_PL_N", "250"))
BASES = P2.BASES
STATES = P2.STATES
Z_PL = 1.15                   # A05 avionics station [m] (ledger v3d item A05)
TANK_Z0 = 0.55                # v3d tank inner bottom [m]
TANK_Z = 0.58                 # lead integration note: tank at about 0.58-1.08 m
G0 = 9.80665
FMAX = 500.0
ONSET_KG = 0.080              # line-208 dip onset (80 g)
H_REQ = 210
DMS = (0.0, 0.5, 1.0, 2.0, 3.0)
H_GRID = (210, 200, 190, 180, 170, 160, 150, 140, 130, 120, 110, 100, 90, 80, 70, 60, 50)
M_GRID = (2.0, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 3.0, 3.2)
V351 = P2.variants()["v351"]
A_IN = math.pi * 0.09525 ** 2 / 4.0      # ledger tank ID 95.25 mm (101.6 x 3.175 tube)

# ------------------------------------------------------------------------------------------ payload / tank wrappers
_L0 = R.veh.mass_ledger_v3
_G0 = R.veh.reference_geometry_v3
SET = dict(dm=0.0, tank_z=None)


def _ledger(*a, **k):
    led = _L0(*a, **k)
    if SET["dm"] > 0.0:
        led.append(dict(name="B01p payload at the A05 avionics station", owner="payload", m=SET["dm"], m_min=SET["dm"],
                        m_max=SET["dm"], z=Z_PL, shape="point", dims=[], gimballed=False,
                        tag="ASSUMED payload point mass (lead payload sensitivity; own inertia not represented)"))
    return led


def _geo(*a, **k):
    g = _G0(*a, **k)
    if SET["tank_z"] is not None:
        g["tank_z_bot_inner"] = SET["tank_z"]
    return g


R.veh.mass_ledger_v3 = _ledger
R.veh.reference_geometry_v3 = _geo


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def setup(dm, tank_z, h, m_n2o=None, base="A1_none", st="liq"):
    SET["dm"] = float(dm)
    SET["tank_z"] = tank_z
    ex = dict(h_target=float(h), ballast=float(V351["ballast_kg"]), ballast_z=float(V351["ballast_z_m"]))
    if m_n2o is not None:
        ex["m_n2o"] = float(m_n2o)
    cfg, m = F.base_cfg(base, st, ex)
    jr = json.load(open(F.TG))["j_ref"]
    F.MV.TG_JREF_DEFAULT = float(jr["A1J" if base.startswith("A1J") else "A1"])
    return cfg


def nominal(dm, tank_z, h, m_n2o=None, base="A1_none", st="liq"):
    cfg = setup(dm, tank_z, h, m_n2o, base, st)
    res, rec, info = R.fly(dict(cfg, noise=False, wind=0.0, gust=False), nrec=10)
    mn = float(cfg["m_n2o"])
    liq = float(res["liq_left"])
    used = mn - liq
    land = float(res["m_land"])
    led = info["ledger"]
    zc = sum(i["m"] * i["z"] for i in led) / sum(i["m"] for i in led)
    return OrderedDict(dm_kg=dm, tank_bottom_m=tank_z if tank_z is not None else TANK_Z0, h_target_m=h, m_n2o_kg=mn,
                       tank_V_L=1e3 * float(info["tank_V"]), tank_inner_top_m=(tank_z or TANK_Z0) + float(info["tank_V"]) / A_IN,
                       m_liftoff_kg=float(info["m_liftoff"]), zcg_liftoff_m=float(info["zcg0"]), I_t0_kgm2=float(info["It0"]),
                       dry_ledger_cg_m=zc, m_touchdown_kg=land, TW_liftoff=FMAX / (float(info["m_liftoff"]) * G0),
                       TW_touchdown=FMAX / (land * G0), floor_ratio_touchdown=float(cfg["floor"]) * FMAX / (land * G0),
                       landed_ok=bool(R.success(res)), exhausted=bool(res["exhausted"] > 0.5), h_max_m=float(res["h_max"]),
                       liq_left_kg=liq, margin_kg=liq - ONSET_KG, margin_frac=(liq - ONSET_KG) / used if used > 0 else None,
                       n2o_out_kg=used, burn_time_s=float(res["burn_time"]), starts=int(res["starts"]),
                       h_ign_m=float(res["h_ign"]), v_ign_ms=float(res["v_ign"]), pgg_src=float(res["pgg_src"]),
                       pgg_mrg_m=float(res["pgg_mrg"]), pgg_dly_s=float(res["pgg_dly"]))


# ------------------------------------------------------------------------------------------------------------ check
def part_check():
    out = OrderedDict()
    # (1) payload 0, tank 0.55: equals the stored P2 table (runs 0-3) column for column
    for base in BASES:
        rows = fly(base, "liq", 0.0, None, 210, None, 0, 4)
        ref = P2.load_rows(os.path.join(P2.OUT, F3.fname(base, "liq|G73|v351|h210") + ".gz"))[:4]
        bad = []
        for r, q in zip(rows, ref):
            for k, v in r.items():
                if k in ("payload_kg", "tank_bottom_m"):
                    continue
                a, b = float(v), float(q[k])
                if not ((np.isnan(a) and np.isnan(b)) or a == b):
                    bad.append([int(r["run"]), k, a, b])
        out[f"repro_{base}"] = dict(n_mismatch=len(bad), first=bad[:5], ok=not bad)
    # (2) mass / first moment bookkeeping (nominal build)
    b0 = R.build(setup(0.0, None, 210))[5]
    b1 = R.build(setup(1.0, None, 210))[5]
    bt = R.build(setup(0.0, TANK_Z, 210))[5]
    dm_lift = b1["m_liftoff"] - b0["m_liftoff"]
    dmom = b1["m_liftoff"] * b1["zcg0"] - b0["m_liftoff"] * b0["zcg0"]
    tank_items = [i for i in b0["ledger"] if i["name"].startswith(("P09", "P11", "P12"))]
    dmt = bt["m_liftoff"] * bt["zcg0"] - b0["m_liftoff"] * b0["zcg0"]
    out["payload_1kg"] = dict(d_liftoff_mass_kg=dm_lift, d_first_moment_kgm=dmom, expected_kgm=1.0 * Z_PL,
                              ok=bool(abs(dm_lift - 1.0) < 1e-9 and abs(dmom - Z_PL) < 1e-6))
    out["tank_move"] = dict(d_liftoff_mass_kg=bt["m_liftoff"] - b0["m_liftoff"], d_first_moment_kgm=dmt,
                            ledger_items_moved=[[i["name"], i["m"]] for i in tank_items],
                            d_cg_liftoff_mm=1e3 * (bt["zcg0"] - b0["zcg0"]),
                            note="first moment change = (tank tube + P09 + P12 + liquid N2O at liftoff) x 0.03 m")
    out["ok"] = all(v.get("ok", True) for v in out.values() if isinstance(v, dict))
    SET["dm"] = 0.0
    SET["tank_z"] = None
    return out


# ------------------------------------------------------------------------------------------------------------- det
def interp_cross(xs, ys, target):
    """x where y crosses target on a piecewise-linear curve (xs ascending in the search order); None if no crossing."""
    for i in range(len(xs) - 1):
        y0, y1 = ys[i] - target, ys[i + 1] - target
        if y0 == 0:
            return xs[i]
        if y0 * y1 < 0:
            return xs[i] + (xs[i + 1] - xs[i]) * y0 / (y0 - y1)
    if ys[-1] == target:
        return xs[-1]
    return None


def part_det():
    t0 = time.time()
    res = OrderedDict(grid_apogee=OrderedDict(), grid_load=OrderedDict(), iso=OrderedDict(), sized=OrderedDict())
    for base in BASES:
        for st in STATES:
            key = f"{base}|{st}"
            ref = nominal(0.0, TANK_Z, H_REQ, None, base, st)
            res["grid_apogee"][key] = OrderedDict()
            for dm in DMS:
                rows = [nominal(dm, TANK_Z, h, None, base, st) for h in H_GRID]
                res["grid_apogee"][key][f"{dm:g}"] = rows
                hs = [r["h_target_m"] for r in rows]                # 210 ... 50 (descending)
                ma = [r["margin_kg"] if r["landed_ok"] else -1.0 for r in rows]
                mf = [r["margin_frac"] if r["landed_ok"] else -1.0 for r in rows]
                h_abs = interp_cross(hs, ma, ref["margin_kg"])
                h_frac = interp_cross(hs, mf, ref["margin_frac"])
                if dm == 0.0:
                    h_abs = h_frac = float(H_REQ)
                res["iso"].setdefault(f"{dm:g}", OrderedDict())[key] = dict(
                    h_iso_abs_m=h_abs, h_iso_frac_m=h_frac,
                    loss_per_kg_abs_m=(None if (h_abs is None or dm == 0) else (H_REQ - h_abs) / dm),
                    loss_per_kg_frac_m=(None if (h_frac is None or dm == 0) else (H_REQ - h_frac) / dm),
                    ref_margin_kg=ref["margin_kg"], ref_margin_frac=ref["margin_frac"],
                    at_210m=[r for r in rows if r["h_target_m"] == H_REQ][0])
            print(f"det {key}: ref margin {1e3 * ref['margin_kg']:.1f} g ({100 * ref['margin_frac']:.2f} %) | " + "; ".join(
                f"dm {dm:g}: h_iso {res['iso'][f'{dm:g}'][key]['h_iso_abs_m']} / {res['iso'][f'{dm:g}'][key]['h_iso_frac_m']}"
                for dm in DMS), flush=True)
            res["grid_load"][key] = OrderedDict()
            for dm in (1.0, 2.0):
                rows = [nominal(dm, TANK_Z, H_REQ, m, base, st) for m in M_GRID]
                res["grid_load"][key][f"{dm:g}"] = rows
                ms_ = [r["m_n2o_kg"] for r in rows]
                ma = [r["margin_kg"] if r["landed_ok"] else -1.0 for r in rows]
                mf = [r["margin_frac"] if r["landed_ok"] else -1.0 for r in rows]
                res["sized"].setdefault(f"{dm:g}", OrderedDict())[key] = dict(
                    m_iso_abs_kg=interp_cross(ms_, ma, ref["margin_kg"]), m_iso_frac_kg=interp_cross(ms_, mf, ref["margin_frac"]))
    # summary over bases and states: the conservative (lowest) apogee and the largest load
    summ = OrderedDict()
    for dm in DMS:
        e = res["iso"][f"{dm:g}"]
        ha = [v["h_iso_abs_m"] for v in e.values()]
        hf = [v["h_iso_frac_m"] for v in e.values()]
        hmin = min([x for x in ha + hf if x is not None], default=None)
        summ[f"{dm:g}"] = dict(h_iso_min_m=hmin, h_iso_abs_range_m=[min(ha), max(ha)] if None not in ha else ha,
                               h_iso_frac_range_m=[min(hf), max(hf)] if None not in hf else hf,
                               apogee_loss_per_kg_m=(None if (hmin is None or dm == 0) else (H_REQ - hmin) / dm),
                               mc_band_m=(None if hmin is None else int(5 * math.floor(hmin / 5.0))),
                               nominal_A1_none_liq_210m=e["A1_none|liq"]["at_210m"])
    sz = OrderedDict()
    for dm in ("1", "2"):
        e = res["sized"][dm]
        vals = [x for v in e.values() for x in (v["m_iso_abs_kg"], v["m_iso_frac_kg"]) if x is not None]
        mx = max(vals) if vals else None
        if mx is not None:
            mx_r = math.ceil(mx * 20.0) / 20.0            # 50 g steps up
            V = R.tank_volume_for(mx_r)
            n = nominal(float(dm), TANK_Z, H_REQ, mx_r, "A1_none", "liq")
            sz[dm] = dict(m_n2o_iso_max_kg=mx, m_n2o_sized_kg=mx_r, tank_V_L=1e3 * V, tank_inner_length_m=V / A_IN,
                          tank_inner_span_m=[TANK_Z, TANK_Z + V / A_IN],
                          tank_tube_length_m=V / A_IN + 0.02,
                          clash_with_A05_station=bool(TANK_Z + V / A_IN > Z_PL - 0.05),
                          nominal_at_sized_load=n)
        else:
            sz[dm] = dict(m_n2o_iso_max_kg=None)
    res["summary_apogee"] = summ
    res["summary_load"] = sz
    res["wall_s"] = round(time.time() - t0, 1)
    SET["dm"] = 0.0
    SET["tank_z"] = None
    return res


# -------------------------------------------------------------------------------------------------------------- mc
def fly(base, st, dm, tank_z, h, m_n2o, lo, hi):
    """m2_rev3_fly.fly body (P2 arm loop) with the payload / tank wrappers set; runs lo..hi-1 of the hi-run draw prefix
    (R.draw is sequential per run: the prefix equals the 500-run draw)."""
    cfg = setup(dm, tank_z, h, m_n2o, base, st)
    D = R.draw(np.random.default_rng(101), max(hi, 1), cfg)
    ms = F.MV.case_specs()["tot_cal_comp"]
    rows = []
    for i in range(lo, hi):
        c, disp = F.MV.run_cfg_case(cfg, D[i], ms, i, "base")
        c.update(F.DEC)
        c.update(F.PURGE["G73"])
        c.update(F.PLAT[""])
        r_ = R.fly(c, disp, nrec=10)[0]
        row = R.flat_row(i, D[i], r_, R.success(r_), cfg)
        row["m_n2o"] = float(cfg["m_n2o"]) if m_n2o is not None else 2.0
        row["mest_kcal"] = float(c.get("mest_kcal", float("nan")))
        if dm > 0 or tank_z is not None:
            row["payload_kg"] = float(dm)
            row["tank_bottom_m"] = float(tank_z if tank_z is not None else TANK_Z0)
        rows.append(row)
    SET["dm"] = 0.0
    SET["tank_z"] = None
    return rows


def arm_name(dm, h, m=None):
    return f"liq|G73|v351|pl{dm:g}|tz58|h{h}" + ("" if m is None else f"|m{m:.2f}")


def mc_arms(det):
    arms = [(0.0, H_REQ, None)]
    sa = det["summary_apogee"]
    for dm in (0.5, 1.0, 2.0, 3.0):
        hb = sa[f"{dm:g}"]["mc_band_m"]
        if hb is not None and hb >= 50:
            arms.append((dm, hb, None))
    arms += [(1.0, H_REQ, None), (2.0, H_REQ, None)]
    for dm in ("1", "2"):
        m = det["summary_load"][dm].get("m_n2o_sized_kg")
        if m is not None:
            arms.append((float(dm), H_REQ, m))
    for tok in [x for x in os.environ.get("GNC_PL_EXTRA", "").split(";") if x.strip()]:
        f_ = tok.split(":")
        arms.append((float(f_[0]), int(f_[1]), (float(f_[2]) if len(f_) > 2 else None)))
    seen, out = set(), []
    for a in arms:
        if a not in seen:
            seen.add(a)
            out.append(a)
    return out


def part_mc(det):
    os.makedirs(os.path.join(OUT, "tables"), exist_ok=True)
    for dm, h, m in mc_arms(det):
        nm = arm_name(dm, h, m)
        for base in BASES:
            p = os.path.join(OUT, "tables", F3.fname(base, nm).replace(".csv", f"_n{N_MC}.csv"))
            if os.path.exists(p + ".gz"):
                print("exists", base, nm, flush=True)
                continue
            t0 = time.time()
            rows = fly(base, "liq", dm, TANK_Z, h, m, 0, N_MC)
            F.M.write_csv(p, rows)
            P2._gz(p)
            ok = np.array([r["ok"] for r in rows]) > 0.5
            liq = 1e3 * np.array([r["liq_left"] for r in rows])
            print(f"{base:8s} {nm:34s}: P {ok.mean():.3f} (80 g onset {np.mean(ok & (liq >= 80.0)):.3f}) exhausted "
                  f"{int(np.sum([r['exhausted'] > 0.5 for r in rows]))} liq p01 {np.percentile(liq, 1):.0f} g "
                  f"({time.time() - t0:.0f} s)", flush=True)


# ------------------------------------------------------------------------------------------------------------ eval
def load(p):
    with gzip.open(p, "rt") as f:
        return list(csv.DictReader(f))


def part_eval(det, chk):
    res = OrderedDict(version=VERSION, date=time.strftime("%Y-%m-%d"), sim=s6.SIM6_VERSION,
                      script=dict(path=os.path.abspath(__file__), sha256_16=sha16(os.path.abspath(__file__))),
                      vehicle="massprops v3.5.1 FROZEN (488b47f9d55ff91b) via iface_v351 + cfg ballast 0.99744 kg at 0.4426 m "
                              "(P2 arm v351), A1 base cfg, tank inner bottom moved 0.55 -> 0.58 m (lead integration note)",
                      payload=dict(station_m=Z_PL, model="point mass, exact, fixed station, weighed (ASSUMED); own inertia "
                                                         "not represented (TO-VERIFY: payload owner)"),
                      criterion=("landing success = sim6 criteria (vz 2.0 m/s, vh 0.5 m/s, tilt 5 deg, rate 10 deg/s, no "
                                 "exhaustion or tip-over) AND touchdown liquid >= 80 g (line-208 dip onset)"),
                      check=chk, deterministic=det, mc=OrderedDict(N_per_base=N_MC, state="liq", arms=OrderedDict()),
                      tags=dict(flights="SIM", iso_margin_interpolation="DERIVED", TW_floor_ratio="DERIVED (rated 500 N)",
                                tank_layout="ASSUMED (ledger tube rule; CAD layout TO-VERIFY by Mechanical)",
                                payload="ASSUMED point mass"))
    for dm, h, m in mc_arms(det):
        nm = arm_name(dm, h, m)
        A, B, C_, Bp = [], [], [], []
        per = OrderedDict()
        for base in BASES:
            p = os.path.join(OUT, "tables", F3.fname(base, nm).replace(".csv", f"_n{N_MC}.csv")) + ".gz"
            if not os.path.exists(p):
                break
            rc = load(p)
            n = len(rc)
            rr = load(P2.ref_table(base, "liq"))[:n]
            rp = load(os.path.join(P2.OUT, F3.fname(base, "liq|G73|v351|h210") + ".gz"))[:n]
            a, _ = P2.outcome(rr, P2.ONSET_L208)
            c, _ = P2.outcome(rc, P2.ONSET_L208)
            q, _ = P2.outcome(rp, P2.ONSET_L208)
            A.append(a); B.append(c); C_.append(q)
            ml = np.array([float(x["m_land"]) for x in rc])
            okc = np.array([float(x["ok"]) > 0.5 for x in rc])
            gv = lambda k: np.array([float(x[k]) for x in rc])  # noqa: E731
            fm = dict(exhausted=int(np.sum(gv("exhausted") > 0.5)), tipover=int(np.sum(gv("tipover") > 0.5)),
                      crash=int(np.sum(gv("crash") > 0.5)), vz_gt_2=int(np.sum(np.abs(gv("td_vz")) > 2.0)),
                      vh_gt_0p5=int(np.sum(gv("td_vh") > 0.5)), tilt_gt_5=int(np.sum(gv("td_tilt") > 5.0)),
                      relight_failed=int(np.sum(gv("relight_ok") < 0.5)), below_80g=int(np.sum(okc & (gv("liq_left") < ONSET_KG))))
            hig = gv("h_ign")
            per[base] = dict(table=dict(path=p, sha256_16=sha16(p)), n=n, P_flown=float(np.mean([float(x["ok"]) > 0.5 for x in rc])),
                             P_80g=float(c.mean()), exhausted=int(np.sum([float(x["exhausted"]) > 0.5 for x in rc])),
                             liq_left_p01_g=float(np.percentile([1e3 * float(x["liq_left"]) for x in rc], 1)),
                             h_max_p50_m=float(np.median([float(x["h_max"]) for x in rc])),
                             m_land_kg=dict(p01=float(np.percentile(ml, 1)), p50=float(np.median(ml)), p99=float(np.percentile(ml, 99))),
                             fail_modes=fm, h_ign_m=dict(p01=float(np.percentile(hig, 1)), p50=float(np.median(hig))),
                             P_h_ign_ge_40m=float(np.mean(okc[hig >= 40.0])) if np.any(hig >= 40.0) else None)
        if len(A) < len(BASES):
            continue
        A, B, C_ = np.concatenate(A), np.concatenate(B), np.concatenate(C_)
        res["mc"]["arms"][nm] = OrderedDict(payload_kg=dm, h_target_m=h, m_n2o_kg=(m if m is not None else 2.0),
                                            per_base=per, vs_v3d_ref_l208=P2.stats(A, B), vs_P2_v351_h210=P2.stats(C_, B))
    p = os.path.join(OUT, "payload_rev4.json")
    json.dump(res, open(p, "w"), indent=1, default=float)
    print("wrote", p, sha16(p), flush=True)
    for nm, e in res["mc"]["arms"].items():
        s, t = e["vs_v3d_ref_l208"], e["vs_P2_v351_h210"]
        print(f"{nm:36s} P80 {s['P_case']:.3f} vs v3d {s['P_ref']:.3f} -{s['lost']}/+{s['gained']} p {s['p_exact']:.3g} UB95 "
              f"{s['ub95_pp']:.2f} | vs v351 h210 {t['P_ref']:.3f} -{t['lost']}/+{t['gained']} p {t['p_exact']:.3g}", flush=True)
    return res


def main():
    os.makedirs(OUT, exist_ok=True)
    print(f"{VERSION}: parts {PARTS}; N {N_MC}; {s6.SIM6_VERSION}; GNC_IFACE {os.environ.get('GNC_IFACE')}", flush=True)
    ok_if, iface, pin = P2._check_iface(dict(iface=V351["iface"], pin=V351["pin"]))
    if not ok_if:
        raise RuntimeError(f"needs GNC_IFACE {V351['iface']} and GNC_IFACE_PIN {V351['pin']}")
    pc = os.path.join(OUT, "payload_check.json")
    pd = os.path.join(OUT, "payload_det.json")
    if "check" in PARTS:
        c = part_check()
        json.dump(c, open(pc, "w"), indent=1, default=float)
        print("check", c["ok"], json.dumps({k: v for k, v in c.items() if k != "ok"}, default=float)[:900], flush=True)
        if not c["ok"]:
            raise RuntimeError("payload check failed")
    if "det" in PARTS:
        d = part_det()
        json.dump(d, open(pd, "w"), indent=1, default=float)
        print("det summary", json.dumps(d["summary_apogee"], default=float)[:3000], flush=True)
        print("det load", json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "nominal_at_sized_load"}
                                      for k, v in d["summary_load"].items()}, default=float), flush=True)
    if "mc" in PARTS:
        part_mc(json.load(open(pd)))
    if "eval" in PARTS:
        part_eval(json.load(open(pd)), json.load(open(pc)) if os.path.exists(pc) else None)


if __name__ == "__main__":
    main()

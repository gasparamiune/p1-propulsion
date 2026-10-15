"""rg03_vertical v1.1 (independent GNC review, 2026-10-13; v1.1 adds the k_thr argument of fly(), default 1.0, v1 results
unchanged, checked by rg08_isp): independent 1-DOF vertical model of the A1 (300 m, nose drogue,
relight) and B1 (continuous-burn hop) nominal flights, for burn time, N2O burned, usable liquid and the +25 % reserve rule.

Independence: own integrator, own equilibrium N2O tank (CoolProp saturation tables, lumped wall), own engine dynamics,
own aero, read directly from the interface data. The guidance laws are re-implemented from their published description
(sim6 v2.7.1-dev lines 830-1110: MECO predictor with throttle-down, drogue at apogee, relight trigger with the planning
value, braking reference + PI, terminal gate; B-profile apex predictor with the floor), because the laws are a design input;
the physics is what is recomputed. Nothing is imported from gncsim.

Inputs (interface set iface_v3c, identical to the hub):
  throttle_map_v2.csv (combustion.json v2.3): F, mdot_ox, mdot_f, F_ceiling vs (P_tank, D_port, thrust fraction); used as
  published (no GNC k_ox / k_f factors). Port growth integrated from mdot_f (uniform port, rho_f 1000 kg/m3 ASSUMED by
  Combustion, L 0.230 m).
  Vehicle (gnc.json v3 reference_vehicle): A1 liftoff 16.0746 kg, B1 15.4246 kg (2.00 kg N2O); S = pi 0.073^2;
  CA nose-first 0.45 (-0.07 engine on), tail-first 1.05 (x (0.5 + 0.5 k_retro) engine on, k_retro 0.5), legs +1.5;
  drogue CdA 0.5 m2 (ASSUMED in gnc.json); foot plane 0.25 m below the aft datum (h = foot height).
  Tank 3.1671 L, T0 293.15 K, wall 0.5 x 1.761 kg x 896 J/kg/K = 789 J/K (author's ASSUMED value; bracketed 0 / 1578 J/K).
  Thrust: first-order tau 0.100/2.197 s, slew 5 F_max/s (author's ASSUMED values), MECO tail-off as a pintle ramp
  (0.25 s full stroke, lead provisional) + chamber lag. Atmosphere rho0 1.225 kg/m3, troposphere law.
Rule: usable = liquid at touchdown - 3 % of the load; closes if usable >= 0.25 x N2O burned (gnc.json v3 rule).
Output: rg03_vertical.json
"""
import csv
import json
import math
import os
import sys

import numpy as np
import CoolProp.CoolProp as CP

HERE = os.path.dirname(os.path.abspath(__file__))
IFACE = os.environ.get("RG_IFACE", "/home/claude/work/space/iface_v3c")
G = 9.80665
FMAX = 500.0
S = math.pi * 0.073 ** 2
V_TANK = 3.1670974974577987e-3
CW_DEF = 0.5 * 1.761 * 896.0
RHO_F, L_GR, D0 = 1000.0, 0.230, 0.025
TAU = 0.100 / 2.197
SLEW = 5.0 * FMAX
TOFF_RATE = FMAX / 0.25
TRAP = 0.03

# ---------------------------------------------------------------- N2O saturation tables
TT = np.arange(240.0, 309.0, 0.05)
FL = "NitrousOxide"
RL = np.array([CP.PropsSI("D", "T", t, "Q", 0, FL) for t in TT])
RV = np.array([CP.PropsSI("D", "T", t, "Q", 1, FL) for t in TT])
UL = np.array([CP.PropsSI("U", "T", t, "Q", 0, FL) for t in TT])
UV = np.array([CP.PropsSI("U", "T", t, "Q", 1, FL) for t in TT])
HL = np.array([CP.PropsSI("H", "T", t, "Q", 0, FL) for t in TT])
PS = np.array([CP.PropsSI("P", "T", t, "Q", 0, FL) for t in TT])


def mix(T, M):
    rl, rv = np.interp(T, TT, RL), np.interp(T, TT, RV)
    v = V_TANK / M
    x = (v - 1.0 / rl) / (1.0 / rv - 1.0 / rl)
    u = np.interp(T, TT, UL) + x * (np.interp(T, TT, UV) - np.interp(T, TT, UL))
    return x, u


class Tank:
    def __init__(self, M, T0, Cw):
        self.M, self.T, self.Cw = M, T0, Cw
        x, u = mix(T0, M)
        self.E = M * u + Cw * T0

    def solve(self):
        T = self.T
        for _ in range(30):
            x, u = mix(T, self.M)
            f = self.M * u + self.Cw * T - self.E
            x2, u2 = mix(T + 1e-3, self.M)
            d = (self.M * u2 + self.Cw * (T + 1e-3) - self.E - f) / 1e-3
            dT = -f / d
            T += dT
            if abs(dT) < 1e-7:
                break
        self.T = T
        return T

    def draw(self, mdot, dt):
        h = float(np.interp(self.T, TT, HL))
        self.M -= mdot * dt
        self.E -= mdot * h * dt
        self.solve()

    @property
    def P(self):
        return float(np.interp(self.T, TT, PS))

    @property
    def liquid(self):
        x, _ = mix(self.T, self.M)
        return (1.0 - x) * self.M


# ---------------------------------------------------------------- engine map (combustion.json v2.3 throttle_map_v2)
def load_map():
    rows = []
    with open(os.path.join(IFACE, "throttle_map_v2.csv")) as f:
        lines = [ln for ln in f if not ln.startswith("#")]
    for r in csv.DictReader(lines):
        rows.append({k: float(v) if v not in ("", None) else float("nan") for k, v in r.items() if k != "ceiling_limit"})
    P = sorted(set(r["P_tank_Pa"] for r in rows))
    D = sorted(set(r["D_port_m"] for r in rows))
    Fr = sorted(set(r["frac"] for r in rows))
    shp = (len(P), len(D), len(Fr))
    ox, fu, fn, ce = (np.full(shp, np.nan) for _ in range(4))
    for r in rows:
        i, j, k = P.index(r["P_tank_Pa"]), D.index(r["D_port_m"]), Fr.index(r["frac"])
        ox[i, j, k], fu[i, j, k], fn[i, j, k], ce[i, j, k] = r["mdot_ox"], r["mdot_f"], r["F_N"], r["F_ceiling_N"]
    return np.array(P), np.array(D), np.array(Fr), ox, fu, fn, ce


MP, MD, MF, MOX, MFU, MFN, MCE = load_map()


def _w(ax, x):
    x = min(max(x, ax[0]), ax[-1])
    i = int(np.searchsorted(ax, x) - 1)
    i = min(max(i, 0), len(ax) - 2)
    return i, (x - ax[i]) / (ax[i + 1] - ax[i])


def tri(tab, P, D, fr):
    i, a = _w(MP, P)
    j, b = _w(MD, D)
    k, c = _w(MF, fr)
    s = 0.0
    for di, wa in ((0, 1 - a), (1, a)):
        for dj, wb in ((0, 1 - b), (1, b)):
            for dk, wc in ((0, 1 - c), (1, c)):
                s += wa * wb * wc * tab[i + di, j + dj, k + dk]
    return s


def flows(F, P, D):
    """mdot_ox, mdot_f at delivered thrust F; below the 12.5 % map edge the flows scale with F (ASSUMED)."""
    fr = F / FMAX
    if fr >= MF[0]:
        return tri(MOX, P, D, fr), tri(MFU, P, D, fr)
    s = max(fr, 0.0) / MF[0]
    return s * tri(MOX, P, D, MF[0]), s * tri(MFU, P, D, MF[0])


def ceiling(P, D):
    return tri(MCE, P, D, 1.0)


def rho_air(h, rho0=1.225):
    return rho0 * (1.0 - 2.2558e-5 * max(h, 0.0)) ** 4.2559


# ---------------------------------------------------------------- flight
def fly(prof, h_target, m_dry, legs_asc, d_ign=0.315, t_est=0.81, Cw=CW_DEF, T0=293.15, m_n2o=2.0, kd=None, slew=SLEW,
        tau=TAU, k_retro=0.5, drogue_cda=0.5, dt=1e-3, t_max=80.0, f_legs=1.0, f_nf=1.0, f_tf=1.0, k_thr=1.0):
    """k_thr (v1.1): delivered thrust per map thrust at the same propellant flow (a C_F c* shortfall, like the 6-DOF
    thrust_scale); the guidance is given an ideal effectiveness estimate (k_hat = k_thr), so the result is the propellant
    cost of the shortfall alone. k_thr = 1.0 reproduces v1 exactly (multiplications by 1.0)."""
    tk = Tank(m_n2o, T0, Cw)
    D = D0
    fuel = 0.0
    burned = 0.0
    h, v = 0.0, 0.0
    F, Fcmd = 0.0, FMAX
    lit, legs, drogue = True, legs_asc, False
    phase, t = 1, 0.0
    floorF = 0.2 * FMAX
    kd = kd if kd is not None else (0.6 if prof == "A" else 0.7)
    vtd, ht, a_term = 1.0, 8.0, 1.5
    kv = 2.0
    ki = 0.6 * kv
    ei = 0.0
    td_on, t_tdn, t_cmd, t_light, F_start, t90 = False, 0.0, None, None, 0.0, None
    toff = False
    Fv = None
    ev_ = dict()
    t_on = 0.0
    imp = 0.0
    hist = []
    burns = []
    on_prev = False
    cda_nom = S * 1.05 * (0.5 + 0.5 * 0.5)
    while t < t_max:
        m = m_dry + tk.M
        rho = rho_air(h)
        # ---------------- guidance (truth states: nominal deterministic flight, no navigation error)
        Fc_av = min(FMAX, ceiling(tk.P, D))
        if phase == 1:                                  # powered ascent
            Fcmd = FMAX
            if v > 0.5:
                if prof == "A":
                    k = 0.5 * rho * S * 0.45 / m
                    Ftd, th = 0.72 * FMAX, 0.25
                    timp = lambda f: f * f / (2.0 * TOFF_RATE) + f * tau
                    if not td_on:
                        a1 = k_thr * Ftd / m - G
                        h1 = h + v * th + 0.5 * a1 * th * th
                        v1 = v + a1 * th + k_thr * timp(Ftd) / m
                        if h1 + math.log(1.0 + k * v1 * v1 / G) / (2 * k) >= h_target:
                            td_on, t_tdn = True, t
                    if td_on:
                        Fcmd = Ftd
                        v1 = v + k_thr * timp(F if F > 1.0 else Ftd) / m
                        hap = h + math.log(1.0 + k * v1 * v1 / G) / (2 * k)
                        if (F <= 0.75 * FMAX or t - t_tdn >= 0.5) and hap >= h_target:
                            phase, lit, toff = 2, False, True
                            ev_.update(t_meco=t, h_meco=h, v_meco=v, F_meco=F, liq_meco=tk.liquid, P_meco=tk.P, T_meco=tk.T,
                                       burned_meco=burned, fuel_meco=fuel)
                else:                                   # B profile: apex predictor with the floor
                    Fd = k_thr * F
                    Fsw = min(floorF + k_thr * slew * tau, Fd)
                    t_ramp = (Fd - Fsw) / (k_thr * slew)
                    dv1 = (0.5 * (Fd + Fsw) / m - G) * t_ramp
                    dv2 = ((Fsw - floorF) / m) * tau + (floorF / m - G) * tau
                    vq = v + dv1 + dv2
                    hq = h + 0.5 * (v + vq) * (t_ramp + tau)
                    mm = m
                    for _ in range(3):
                        geff = max(G - floorF / mm, 0.2)
                        mm = m - 0.5 * (floorF / (140.0 * G)) * (vq / geff)
                    k = 0.5 * rho * S * 0.45 / mm
                    if hq + math.log(1.0 + k * vq * vq / geff) / (2 * k) >= h_target:
                        phase = 2
                        ev_.update(t_meco=t, h_meco=h, v_meco=v, F_meco=F, liq_meco=tk.liquid, P_meco=tk.P, burned_meco=burned)
        if phase in (2, 3):
            if prof == "B":
                Fcmd = floorF / k_thr
                if phase == 2 and v > 0.0:
                    geff = max(G - floorF / m, 0.2)
                    hap_now = h + v * v / (2 * geff)
                    if hap_now < h_target - 0.5:
                        Fcmd = (floorF + m * 0.08 * (h_target - hap_now)) / k_thr
            else:
                Fcmd = 0.0
            if v < 0.0 and phase == 2:
                phase = 3
                ev_.update(t_apo=t, h_apo=h)
                if prof == "A":
                    drogue = True
            if phase == 3:
                ad = max(kd * (k_thr * Fc_av / m - G), a_term + 0.5)
                lag = t_est + 0.05 if prof == "A" else 2.0 * tau
                vt = math.sqrt(vtd * vtd + 2.0 * a_term * ht)
                az = (-0.5 * rho * v * v * (S * (1.05 * f_tf + (1.5 * f_legs if legs else 0.0))) - (0.5 * rho * v * v * drogue_cda if drogue else 0.0)) * (-1.0 if v < 0 else 1.0)
                az = az / m - G if prof == "A" else (k_thr * F - 0.5 * rho * v * v * S * ((1.05 * f_tf * (0.5 + 0.5 * k_retro)) + 1.5 * f_legs) * (1 if v > 0 else -1)) / m - G
                vi = v + az * lag
                hi = h + v * lag + 0.5 * az * lag * lag
                htrig = (vi * vi - vt * vt) / (2.0 * ad) + ht
                if hi <= htrig and vi < 0.0:
                    ev_.update(t_cmd=t, h_cmd=h, v_cmd=v)
                    t_cmd = t
                    if prof == "A":
                        phase, legs = 4, True
                    else:
                        phase = 5
        if phase == 4:
            Fcmd = max(floorF, 0.2 * FMAX)
            F_start = Fcmd
            if t - t_cmd >= d_ign:
                lit, phase, t_light = True, 5, t
                F = 0.05 * FMAX
                ev_.update(t_light=t, h_light=h, v_light=v)
        if phase in (5, 6):
            if drogue and F > 0.5 * floorF:
                drogue = False
                ev_.update(h_drogue_release=h)
            amax = k_thr * Fc_av / m - G
            ad = max(kd * amax, a_term + 0.5)
            vg = math.sqrt(vtd * vtd + 2.0 * a_term * ht)
            hh = max(h, 0.0)
            if h > ht and phase == 5:
                vref = -math.sqrt(vg * vg + 2.0 * ad * (h - ht))
                aref = ad * v / vref
            else:
                if phase == 5:
                    ei = 0.0
                phase = 6
                vref = -math.sqrt(vtd * vtd + 2.0 * a_term * hh)
                aref = a_term * v / vref
            aref = max(aref, 0.0)
            ev = vref - v
            sat_hi = Fcmd >= Fc_av - 1e-9
            sat_lo = Fcmd <= floorF + 1e-9
            if not ((sat_hi and ev > 0) or (sat_lo and ev < 0)):
                ei += ev * dt
            ei = max(min(ei, 3.0 / ki), -3.0 / ki)
            azc = aref + kv * ev + ki * ei
            Tz = m * (G + azc) - 0.5 * 1.2 * cda_nom * v * v
            Fcmd = min(max(Tz / k_thr, floorF), Fc_av)
            if t90 is None and F_start > 0.0 and Fcmd < F_start:
                Fcmd = F_start
        # ---------------- engine
        if lit:
            Fc = min(Fcmd, Fc_av)
            dF = (Fc - F) / tau
            dF = max(min(dF, slew), -slew)
            F = max(F + dF * dt, 0.0)
            if t90 is None and F_start > 0.0 and F >= 0.9 * F_start:
                t90 = t
        elif toff:
            # pintle closing ramp (valve-limited thrust Fv) followed by the first-order chamber lag: impulse F0^2/(2 rate) + F0 tau
            if Fv is None:
                Fv = F
            Fv = max(Fv - TOFF_RATE * dt, 0.0)
            F = max(F + (Fv - F) * dt / tau, 0.0)
            if Fv <= 0.0 and F < 1.0:
                toff, F = False, 0.0
        else:
            F = 0.0
        if F > 1.0:
            mox, mf = flows(F, tk.P, D)
        else:
            mox, mf = 0.0, 0.0
        on = F > 1.0
        imp += k_thr * F * dt
        if int(round(t / dt)) % 100 == 0:
            hist.append([round(t, 3), round(h, 3), round(v, 4), round(F, 3), round(mox, 6), round(mf, 6), round(tk.P, 1), round(tk.liquid, 5), round(m, 5)])
        if on:
            t_on += dt
            if not on_prev:
                burns.append([t, t])
            burns[-1][1] = t
        on_prev = on
        # ---------------- dynamics (foot height h)
        if v >= 0.0:
            CA = 0.45 * f_nf + (-0.07 if F > 1.0 else 0.0)
        else:
            CA = 1.05 * f_tf * ((0.5 + 0.5 * k_retro) if F > 1.0 else 1.0)
        if legs:
            CA += 1.5 * f_legs
        Dg = 0.5 * rho * v * v * (S * CA + (drogue_cda if drogue else 0.0))
        a = (k_thr * F - math.copysign(Dg, v)) / m - G
        if h <= 0.0 and a < 0.0 and phase == 1:
            a = 0.0
        v += a * dt
        h += v * dt
        if mox > 0.0:
            tk.draw(mox, dt)
            burned += mox * dt
            fuel += mf * dt
            D = math.sqrt(D * D + 4.0 * mf * dt / (RHO_F * math.pi * L_GR))
        if tk.liquid <= 0.0:
            ev_["exhausted"] = True
            break
        t += dt
        if phase >= 5 and h <= 0.0:
            ev_.update(td_t=t, td_vz=v)
            break
        if phase == 3 and h <= 0.0:
            ev_.update(crash_t=t, crash_vz=v)
            break
    liq = tk.liquid
    usable = liq - TRAP * m_n2o
    out = dict(prof=prof, h_target=h_target, d_ign=d_ign, t_est=t_est, Cw=Cw, T0=T0, m_liftoff=m_dry + m_n2o,
               n2o_burned=burned, fuel_burned=fuel, liquid_left=liq, vapour_left=tk.M - liq, usable=usable,
               reserve=usable / burned if burned > 0 else float("nan"), closes=bool(usable >= 0.25 * burned and "td_vz" in ev_ and abs(ev_["td_vz"]) <= 2.0),
               thrust_on_s=t_on, burns=[[round(a, 3), round(b, 3)] for a, b in burns], P_end=tk.P, T_end=tk.T, D_port_end=D,
               impulse_Ns=imp, hist_cols=['t', 'h', 'v', 'F', 'mox', 'mf', 'P_tank', 'liquid', 'm'], hist=hist, **ev_)
    return out


def run_all():
    res = {}
    A_dry = 16.0746 - 2.0
    B_dry = 15.4246 - 2.0
    # A1 at the planning value 0.81 s, start delays of the RC-03 tables (liquid min / median / max; full vapour median / max)
    for lab, d in (("liq_min", 0.1257), ("liq_med", 0.3152), ("liq_max", 0.4990), ("vapF_med", 0.6253), ("vapF_max", 0.8090)):
        res[f"A1_plan0.81_{lab}"] = fly("A", 300.0, A_dry, False, d_ign=d, t_est=0.81)
    res["A1_plan0.81_fault1.37"] = fly("A", 300.0, A_dry, False, d_ign=1.37, t_est=0.81)
    res["A1_plan1.41_fault1.37"] = fly("A", 300.0, A_dry, False, d_ign=1.37, t_est=1.41)
    res["A1_plan1.41_liq_min"] = fly("A", 300.0, A_dry, False, d_ign=0.1257, t_est=1.41)
    # wall heat-capacity bracket (ASSUMED 789 J/K): adiabatic fluid and twice the wall
    res["A1_plan0.81_liq_med_Cw0"] = fly("A", 300.0, A_dry, False, d_ign=0.3152, t_est=0.81, Cw=0.0)
    res["A1_plan0.81_liq_med_Cw2x"] = fly("A", 300.0, A_dry, False, d_ign=0.3152, t_est=0.81, Cw=2 * CW_DEF)
    # ENG-03 slew 1000 N/s (2 F_max/s) instead of the 5 F_max/s ASSUMED in the 6-DOF
    res["A1_plan0.81_liq_med_slew2"] = fly("A", 300.0, A_dry, False, d_ign=0.3152, t_est=0.81, slew=2.0 * FMAX)
    # T0 corners of the MC band 15 / 25 C (ENG-12)
    res["A1_plan0.81_liq_med_T15"] = fly("A", 300.0, A_dry, False, d_ign=0.3152, t_est=0.81, T0=288.15)
    res["A1_plan0.81_liq_med_T25"] = fly("A", 300.0, A_dry, False, d_ign=0.3152, t_est=0.81, T0=298.15)
    # CA +/-30 % (gnc.json: ASSUMED +/-30 %; the 6-DOF MC disperses CA_tf only)
    for lab, kw in (("legs1.3", dict(f_legs=1.3)), ("legs0.7", dict(f_legs=0.7)), ("nf1.3", dict(f_nf=1.3)), ("nf0.7", dict(f_nf=0.7))):
        res[f"A1_plan0.81_liq_med_{lab}"] = fly("A", 300.0, A_dry, False, d_ign=0.3152, t_est=0.81, **kw)
        for hb in (62.0, 85.0):
            res[f"B1_{hb:.0f}m_{lab}"] = fly("B", hb, B_dry, True, **kw)
    # B1 tank temperature corners (ENG-12 ARM band 15-24 C, MC 15-25 C)
    for T0_ in (288.15, 297.15, 298.15):
        for hb in (62.0, 85.0):
            res[f"B1_{hb:.0f}m_T{T0_ - 273.15:.0f}"] = fly("B", hb, B_dry, True, T0=T0_)
    # B1 hop, legs fixed from liftoff
    for hb in (62.0, 85.0):
        res[f"B1_{hb:.0f}m"] = fly("B", hb, B_dry, True)
        res[f"B1_{hb:.0f}m_slew2"] = fly("B", hb, B_dry, True, slew=2.0 * FMAX)
        res[f"B1_{hb:.0f}m_Cw0"] = fly("B", hb, B_dry, True, Cw=0.0)
    return res


AUTHOR = {  # author's nominal values (results/relight_v28/relight_v28_nominal.json; results/regband/regband_nominal.json)
    "A1_plan0.81_liq_min": dict(n2o_burned=1.19874, reserve=0.37025, burn_counter_s=7.705, h_cmd=42.911),
    "A1_plan0.81_liq_med": dict(n2o_burned=1.18686, reserve=0.38465, burn_counter_s=7.533, h_cmd=42.911),
    "A1_plan0.81_liq_max": dict(n2o_burned=1.17711, reserve=0.39675, burn_counter_s=7.386, h_cmd=42.911),
    "A1_plan0.81_vapF_med": dict(n2o_burned=1.16972, reserve=0.40595, burn_counter_s=7.276, h_cmd=42.911),
    "A1_plan0.81_vapF_max": dict(n2o_burned=1.15347, reserve=0.42682, burn_counter_s=7.035, h_cmd=42.911),
    "A1_plan0.81_fault1.37": dict(landed=False),
    "A1_plan1.41_fault1.37": dict(reserve=0.42037, burn_counter_s=7.118, h_cmd=55.999),
    "A1_plan1.41_liq_min": dict(n2o_burned=1.23409, reserve=0.32915, burn_counter_s=8.239),
    "B1_85m": dict(n2o_burned=1.29535, reserve=0.26345, burn_counter_s=18.064, h_max=83.71, impulse_Ns=2578.3),
}

if __name__ == "__main__":
    R = run_all()
    for k, r in R.items():
        a = AUTHOR.get(k, {})
        print(f"{k:32s} burned {r['n2o_burned']:.4f} fuel {r['fuel_burned']:.4f} liq {r['liquid_left']:.4f} usable {r['usable']:.4f} "
              f"reserve {100 * r['reserve']:.1f}% on {r['thrust_on_s']:.2f}s td {r.get('td_vz', float('nan')):.2f} "
              f"hcmd {r.get('h_cmd', float('nan')):.1f} hlight {r.get('h_light', float('nan')):.1f} apo {r.get('h_apo', float('nan')):.1f} "
              f"meco {r.get('t_meco', float('nan')):.3f}/{r.get('h_meco', float('nan')):.1f}/{r.get('v_meco', float('nan')):.1f} | author {a}",
              flush=True)
    with open(os.path.join(HERE, "rg03_vertical.json"), "w") as f:
        json.dump(dict(script="rg03_vertical v1", iface=IFACE, results=R, author=AUTHOR), f, indent=1, default=float)

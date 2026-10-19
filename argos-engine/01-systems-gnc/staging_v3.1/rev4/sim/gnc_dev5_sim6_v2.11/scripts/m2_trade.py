"""Descent-attitude trade quantities for gnc.json v2 / REPORT section B (RV-1c, sim6 v2.2 nominal flights + aero.py).

 1. continuous-burn hop: N2O needed for a 300 m apex (deterministic 6-DOF sizing, 20 % reserve) at 12.5 / 20 / 25 %
 2. TVC flip + tail-first aero: tail-first static margin vs nose-flap (drag-flap / grid-fin) area, adverse and nominal
    aero sets, legs stowed / deployed; terminal speed with flaps
 3. N2O cold-gas attitude RCS for the tail-first descent: control moment, thruster force, impulse and vapour mass over
    the nominal A-F descent (aero moment at a held 2 deg / 5 deg off-axis angle), tank cooling by the vapour draw
 4. nose drogue: descent speed under the drogue vs CdA (quasi-steady)
Output: GNC_RES/trade_descent_v2.json (+ CSV of the flap sweep)
Run: nice -n 10 python scripts/m2_trade.py
"""
import csv
import json
import os
import sys
import numpy as np
import CoolProp.CoolProp as CP

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from gncsim import run6 as R, sim6 as s6, vehicle as veh, aero  # noqa: E402

RES = os.environ.get("GNC_RES", "/home/claude/work/space/out/results_v2")
os.makedirs(RES, exist_ok=True)
I = {n: i for i, n in enumerate(s6.REC_NAMES)}
ISP_RCS = (50.0, 40.0, 65.0)     # ASSUMED N2O vapour cold-gas Isp at sea level [s]: nominal, low, high
ADV = dict(k_base_lead=1.0, k_nose_trail=0.5, crossflow=0.75, ca_tf=1.3, k_retro=0.75)
NOM = dict(k_base_lead=0.75, k_nose_trail=0.25, crossflow=1.0, ca_tf=1.0, k_retro=0.5)
Z_FLAP = 1.65                    # ASSUMED flap hinge line just below the nose joint [m]
Z_RCS = 1.60                     # ASSUMED pitch/yaw RCS nozzle station [m]


def size(profile, floor, h, fins=False):
    cfg = R.cfg_of(profile=profile, fins=fins, floor=floor, h_target=h)
    m, res = R.size_load(cfg)
    return dict(profile=profile, floor=floor, h_target=h, closes=m is not None, m_n2o_sized_kg=m,
                prop_used_kg=float(res["prop_used"]) if m is not None else None,
                burn_time_s=float(res["burn_time"]) if m is not None else None,
                tank_V_L=float(R.tank_volume_for(m) * 1e3) if m is not None else None)


def tail_first_margin(geo, zc, unc, flap_area, legs, alphas=(2.0, 5.0, 10.0)):
    g = dict(geo, drogue_CdA=0.0)
    if flap_area > 0:
        g.update(flap_area=flap_area, z_flap=Z_FLAP, flap_cna=2.0, flap_CdA=1.2 * flap_area)
    ap, cp = aero.build_aero_params(g, unc)
    ap[aero.A_LEGS_DEPLOYED] = legs
    ap[aero.A_FLAPS_DEPLOYED] = 1.0 if flap_area > 0 else 0.0
    out = {}
    F = np.zeros(3); M = np.zeros(3)
    for a in alphas:
        # tail-first flight at off-axis angle a: velocity along -z with a +x component
        ar = np.radians(180.0 - a)
        V = 40.0
        aero.aero_forces(np.array([V * np.sin(ar), 0.0, V * np.cos(ar)]), np.zeros(3), 1.2, zc, False, ap, cp, F, M)
        q = 0.5 * 1.2 * V * V
        # restoring if the moment turns the body toward the velocity vector (reduces the off-axis angle):
        # body moving toward +x (and -z): base leads; restoring moment rotates -z toward +x, i.e. M_y < 0
        Cm = M[1] / (q * ap[aero.A_SREF] * ap[aero.A_D])
        Fn = F[0]
        zcp = zc + M[1] / Fn if abs(Fn) > 1e-9 else float("nan")
        out[f"Cm_{a:.0f}deg"] = float(Cm)
        out[f"restoring_{a:.0f}deg"] = bool(M[1] < 0)
        out[f"M_{a:.0f}deg_at_40mps_Nm"] = float(M[1])
    return out, ap


def main():
    src = R.sources()
    comb, el, mech = src["comb"], src["el"], src["mech"]
    out = dict(version="trade_descent v2", sim=s6.SIM6_VERSION, date="2026-10-12")
    # ------------------------------------------------------------ 1. continuous-burn hop to 300 m
    hop = []
    for fl in (0.125, 0.20, 0.25):
        r = size("B", fl, 300.0)
        hop.append(r)
        print("hop300", r, flush=True)
    out["option1_hop_300m"] = hop
    # ------------------------------------------------------------ nominal A-F / A-D flights for speeds and moments
    base = {}
    for prof, fins in (("A-D", True), ("A-F", False)):
        cfg = R.cfg_of(profile=prof, fins=fins, floor=0.20)
        m, _ = R.size_load(cfg)
        res, rec, info = R.fly(R.cfg_of(profile=prof, fins=fins, floor=0.20, m_n2o=m * 1.15, noise=False, wind=0.0,
                                        gust=False, rec_dt=0.01), nrec=12000)
        base[prof] = (res, rec, info, m)
    resF, recF, infoF, mF = base["A-F"]
    geo = veh.reference_geometry_v3(legs="deployable", comb=comb, mech=mech, fins=False)
    zc_desc = float(recF[np.argmax(recF[:, I["phase"]] >= 3), I["zcg"]])
    m_desc = float(recF[np.argmax(recF[:, I["phase"]] >= 3), I["m"]])
    # ------------------------------------------------------------ 2. flaps: tail-first static stability vs area
    S = np.pi * geo["d"] ** 2 / 4
    rows = []
    for Af in (0.0, 0.01, 0.02, 0.03, 0.05, 0.08, 0.12):
        for lab, unc in (("nominal", NOM), ("adverse", ADV)):
            for legs in (0.0, 1.0):
                mg, ap = tail_first_margin(geo, zc_desc, unc, Af, legs)
                CdA_tot = ap[aero.A_CA0_TF] * S + (ap[aero.A_CA_LEGS] * S if legs else 0.0) + 1.2 * Af
                v_t = float(np.sqrt(2 * m_desc * R.G0 / (1.2 * CdA_tot)))
                rows.append(dict(flap_area_m2=Af, aero_set=lab, legs_deployed=int(legs), terminal_speed_mps=v_t, **mg))
    with open(os.path.join(RES, "trade_flaps_v2.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)
    need = {}
    for lab in ("nominal", "adverse"):
        for legs in (0, 1):
            ok = [r["flap_area_m2"] for r in rows if r["aero_set"] == lab and r["legs_deployed"] == legs
                  and r["restoring_2deg"] and r["restoring_5deg"] and r["restoring_10deg"]]
            need[f"{lab}_legs{legs}"] = min(ok) if ok else None
    out["option2_flaps"] = dict(z_flap_m=Z_FLAP, flap_model="normal-force slope 2.0 per flap area + plate crossflow + "
                                "drag 1.2 x area at the flap station (ASSUMED, unvalidated)",
                                m_descent_kg=m_desc, z_cg_descent_m=zc_desc, sweep_csv="trade_flaps_v2.csv",
                                min_area_restoring_2_5_10deg_m2=need, A_ref_m2=S,
                                AF_nominal=dict(v_ign=float(resF["v_ign"]), h_ign=float(resF["h_ign"]),
                                                prop_used=float(resF["prop_used"]), m_n2o_sized=mF))
    print("flaps need", need, flush=True)
    # ------------------------------------------------------------ 3. cold-gas attitude RCS over the A-F descent
    ph = recF[:, I["phase"]]
    t = recF[:, I["t"]]
    sel = (ph >= 3) & (ph <= 4)
    rcs = {}
    for lab, unc in (("nominal", NOM), ("adverse", ADV)):
        ap, cp = aero.build_aero_params(dict(geo, drogue_CdA=0.0), unc)
        for a in (2.0, 5.0):
            Ms = []
            for k in np.where(sel)[0]:
                V = abs(recF[k, I["vz"]])
                if V < 1.0:
                    Ms.append(0.0)
                    continue
                ar = np.radians(180.0 - a)
                F = np.zeros(3); M = np.zeros(3)
                rho = 1.2 * np.exp(-recF[k, I["z"]] / 8500.0)
                aero.aero_forces(np.array([V * np.sin(ar), 0.0, V * np.cos(ar)]), np.zeros(3), rho, recF[k, I["zcg"]],
                                 False, ap, cp, F, M)
                Ms.append(abs(M[1]))
            Ms = np.array(Ms)
            arm = Z_RCS - zc_desc
            dtr = 0.01
            Mmax = float(Ms.max())
            imp_ang = float(np.sum(Ms) * dtr)            # N m s of moment that must be cancelled (held angle)
            imp_lin = imp_ang / arm                      # N s of thruster impulse (one axis, held at angle a)
            rcs[f"{lab}_{a:.0f}deg"] = dict(M_aero_max_Nm=Mmax, thruster_force_min_N=Mmax / arm,
                                            thruster_force_with_margin_2_N=2 * Mmax / arm, arm_m=arm,
                                            angular_impulse_Nms=imp_ang, thruster_impulse_Ns=imp_lin,
                                            vapour_kg_isp50=imp_lin / (ISP_RCS[0] * R.G0),
                                            vapour_kg_isp40=imp_lin / (ISP_RCS[1] * R.G0),
                                            descent_time_s=float(t[sel][-1] - t[sel][0]))
    # tank cooling by vapour withdrawal (equilibrium, latent heat from the liquid + 50 % wall)
    T = 293.15
    hfg = CP.PropsSI("H", "T", T, "Q", 1, "NitrousOxide") - CP.PropsSI("H", "T", T, "Q", 0, "NitrousOxide")
    cpl = CP.PropsSI("C", "T", T, "Q", 0, "NitrousOxide")
    m_liq = float(recF[np.argmax(ph >= 3), I["mliq"]])
    m_tank = [i for i in infoF["ledger"] if i["name"].startswith("P11")][0]["m"]
    heat_cap = m_liq * cpl + 0.5 * m_tank * 896.0
    dPdT = (CP.PropsSI("P", "T", T + 0.5, "Q", 0, "NitrousOxide") - CP.PropsSI("P", "T", T - 0.5, "Q", 0, "NitrousOxide"))
    for k, v in rcs.items():
        dT = v["vapour_kg_isp50"] * hfg / heat_cap
        v["tank_dT_K"] = -dT
        v["tank_dP_Pa"] = -dT * dPdT
    out["option3_rcs"] = dict(z_rcs_m=Z_RCS, isp_assumed_s=ISP_RCS, cases=rcs, h_fg_J_kg=hfg, liquid_kg=m_liq,
                              note="moment needed to HOLD the off-axis angle against the destabilising tail-first aero "
                                   "(adverse/nominal); a limit cycle costs at least this; gust disturbances add to it")
    print("rcs", json.dumps(rcs, indent=0, default=float)[:800], flush=True)
    # ------------------------------------------------------------ 4. drogue: descent speed vs CdA
    resD, recD, infoD, mD = base["A-D"]
    m_land = float(resD["m_land"])
    dro = []
    ap, cp = aero.build_aero_params(dict(geo, drogue_CdA=0.0), NOM)
    for cda in (0.3, 0.4, 0.5, 0.7, 1.0):
        CdA_tot = cda + ap[aero.A_CA0_TF] * S
        dro.append(dict(drogue_CdA_m2=cda, descent_speed_mps=float(np.sqrt(2 * m_land * R.G0 / (1.2 * CdA_tot)))))
    out["option4_drogue"] = dict(m_kg=m_land, table=dro, AD_nominal=dict(v_ign=float(resD["v_ign"]), h_ign=float(resD["h_ign"]),
                                                                        prop_used=float(resD["prop_used"]), m_n2o_sized=mD))
    json.dump(out, open(os.path.join(RES, "trade_descent_v2.json"), "w"), indent=1, default=float)
    print(json.dumps({k: out[k] for k in ("option4_drogue",)}, indent=1, default=float))


if __name__ == "__main__":
    main()

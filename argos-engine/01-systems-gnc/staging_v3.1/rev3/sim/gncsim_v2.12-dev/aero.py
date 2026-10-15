"""All-attitude (0-180 deg) component build-up aerodynamics for the reference airframe.

Body frame: z_b along the vehicle axis toward the nose; stations z [m] from the airframe aft
datum (base plane). v_rel = vehicle velocity relative to air, in body axes.
alpha = angle between +z_b and v_rel (0 = nose-first, 180 = tail/engine-first).

Normal force of each component opposes the local crossflow velocity:
    F_N,i = -q_i S_ref CN_i(alpha_i) * v_c,i/|v_c,i|,  q_i = 0.5 rho |v_loc,i|^2,
    v_loc,i = v_rel + omega x r_i  (gives pitch damping without a separate Cmq).
Component laws (S_ref = pi d^2/4):
 * Leading-end potential (slender-body / Barrowman) lift: CN = CNa_lead sin(a)|cos(a)|.
     nose-first: tangent-ogive nose, CNa = 2.0 at 0.466 L_n from the tip (Barrowman 1967).
     tail-first: blunt base with protruding nozzle leads; CNa = 2 k_base_lead, k in [0.5, 1.0]
     (slender-body upper bound 2; blunt-face separation lowers it; ASSUMED, unvalidated).
 * Trailing-end potential lift: nose-first blunt base -> 0 (separated, Barrowman);
     tail-first trailing ogive -> CNa = -2 k_nose_trail, k in [0, 0.5] (ASSUMED).
 * Viscous crossflow (Allen & Perkins 1951; Jorgensen 1973): CN = eta Cdc (A_plan/S) sin(a)|sin(a)|
     on 12 body segments, eta = 0.65, Cdc = 1.2 (subcritical crossflow Re ~1e5); ASSUMED +/-25 %.
 * Legs (deployed): 4 inclined tubes, crossflow drag on projected area (same law), plus axial drag.
 * Optional fins: Barrowman CNa with body interference, flat-plate crossflow beyond stall.
 * Optional nose flaps (option 2) and nose drogue tether force (option 4).
Axial force: C_A = C_A0,nf cos(a) (a < 90 deg) or C_A0,tf cos(a) (a >= 90 deg), with
legs-deployed and engine-on (plume) corrections. Tail-first values are the least known numbers
in the whole model: only a wind-tunnel, CFD or flight test closes them.
"""
import numpy as np
from numba import njit

# component type codes
LEAD_NOSE, LEAD_BASE, CROSSFLOW, FIN, FLAP = 0, 1, 2, 3, 4

# aero parameter vector layout (filled by build_aero_params)
A_SREF, A_D, A_CA0_NF, A_CA0_TF, A_CA_LEGS, A_CA_ENGON_NF, A_K_RETRO, A_NCOMP, \
    A_DROGUE_CDA, A_DROGUE_Z, A_FLAP_CDA, A_LEGS_DEPLOYED, A_FLAPS_DEPLOYED, A_DROGUE_DEPLOYED, \
    A_FLAP_Z = range(15)
N_APAR = 15
MAXC = 40


def build_aero_params(geo, unc=None):
    """geo: dict of geometry (see params.py). unc: dict of multiplicative uncertainty factors.
    Returns (apar[N_APAR], comp[MAXC, 6]) with comp rows = [type, z, coef_lead, coef_trail, area_ratio, legflag]."""
    u = dict(k_base_lead=0.75, k_nose_trail=0.25, crossflow=1.0, legs=1.0, fins=1.0,
             ca_nf=1.0, ca_tf=1.0, ca_legs=1.0, k_retro=0.5)
    if unc:
        u.update(unc)
    d = geo["d"]
    S = np.pi * d * d / 4.0
    comps = []
    # nose potential lift: leads in nose-first; trails in tail-first
    z_nose_cp = geo["z_tip"] - 0.466 * geo["L_nose"]
    comps.append([LEAD_NOSE, z_nose_cp, 2.0, -2.0 * u["k_nose_trail"], 0.0, 0.0])
    # base potential lift: leads in tail-first (blunt base + nozzle), zero when trailing
    comps.append([LEAD_BASE, geo["z_base"] + 0.5 * d, 2.0 * u["k_base_lead"], 0.0, 0.0, 0.0])
    # body viscous crossflow, 12 segments over the cylinder + nose (nose planform ~ 2/3 d L_n)
    eta, cdc = 0.65, 1.2 * u["crossflow"]
    nseg = 12
    zb = np.linspace(geo["z_base"], geo["z_tip"] - geo["L_nose"], nseg + 1)
    for k in range(nseg):
        dz = zb[k + 1] - zb[k]
        comps.append([CROSSFLOW, 0.5 * (zb[k] + zb[k + 1]), eta * cdc, eta * cdc, d * dz / S, 0.0])
    comps.append([CROSSFLOW, geo["z_tip"] - 0.6 * geo["L_nose"], eta * cdc, eta * cdc,
                  (2.0 / 3.0) * d * geo["L_nose"] / S, 0.0])
    # legs (deployed geometry), crossflow on projected area, flagged so they can be switched
    if geo.get("n_legs", 0) > 0:
        A_leg = geo["n_legs"] * geo["leg_d"] * geo["leg_L"] * 0.7      # mean projected crossflow area
        comps.append([CROSSFLOW, geo["z_leg_aero"], 1.2 * u["legs"], 1.2 * u["legs"], A_leg / S, 1.0])
    # fins (optional), Barrowman with body interference; flat-plate beyond stall
    if geo.get("n_fins", 0) > 0:
        cr, ct, s, xs = geo["fin_cr"], geo["fin_ct"], geo["fin_span"], geo["fin_sweep"]
        nf = geo["n_fins"]
        lm = np.sqrt(s * s + (xs + 0.5 * ct - 0.5 * cr) ** 2)
        cna = (4.0 * nf * (s / d) ** 2) / (1.0 + np.sqrt(1.0 + (2.0 * lm / (cr + ct)) ** 2))
        cna *= 1.0 + (d / 2.0) / (s + d / 2.0)
        cna *= u["fins"]
        # Barrowman fin CP from the root leading edge
        xf = xs * (cr + 2 * ct) / (3 * (cr + ct)) + (cr + ct - cr * ct / (cr + ct)) / 6.0
        z_cp_fin = geo["fin_z_le"] - xf      # fins' root LE station; CP aft of LE (toward base)
        A_plan = nf / 2.0 * (cr + ct) * s * 0.5   # half the fins see crossflow on average
        comps.append([FIN, z_cp_fin, cna, cna * 0.9, A_plan / S, 0.0])
    # nose flaps / grid fins (option 2): stabilising drag + normal force near the top
    if geo.get("flap_area", 0.0) > 0.0:
        comps.append([FLAP, geo["z_flap"], geo["flap_cna"], geo["flap_cna"], geo["flap_area"] / S, 2.0])
    comp = np.zeros((MAXC, 6))
    for i, c in enumerate(comps):
        comp[i, :] = c
    apar = np.zeros(N_APAR)
    apar[A_SREF] = S
    apar[A_D] = d
    apar[A_CA0_NF] = geo["CA0_nf"] * u["ca_nf"]
    apar[A_CA0_TF] = geo["CA0_tf"] * u["ca_tf"]
    apar[A_CA_LEGS] = geo.get("CA_legs", 0.0) * u["ca_legs"]
    apar[A_CA_ENGON_NF] = geo.get("CA_engon_nf", -0.07)       # base-drag relief with plume
    apar[A_K_RETRO] = u["k_retro"]
    apar[A_NCOMP] = len(comps)
    apar[A_DROGUE_CDA] = geo.get("drogue_CdA", 0.0)
    apar[A_DROGUE_Z] = geo.get("z_tip", 2.0)
    apar[A_FLAP_CDA] = geo.get("flap_CdA", 0.0)
    apar[A_LEGS_DEPLOYED] = 0.0
    apar[A_FLAPS_DEPLOYED] = 0.0
    apar[A_DROGUE_DEPLOYED] = 0.0
    apar[A_FLAP_Z] = geo.get("z_flap", geo.get("z_tip", 2.0) - 0.3)
    return apar, comp


@njit(cache=True)
def aero_forces(v_rel, omega, rho, z_cg, engine_on, apar, comp, out_F, out_M):
    """Body-axis aerodynamic force and moment about the CG. v_rel, omega in body axes."""
    S = apar[A_SREF]
    out_F[0] = 0.0; out_F[1] = 0.0; out_F[2] = 0.0
    out_M[0] = 0.0; out_M[1] = 0.0; out_M[2] = 0.0
    V = np.sqrt(v_rel[0] ** 2 + v_rel[1] ** 2 + v_rel[2] ** 2)
    if V < 1e-3:
        return
    legs_on = apar[A_LEGS_DEPLOYED] > 0.5
    flaps_on = apar[A_FLAPS_DEPLOYED] > 0.5
    ncomp = int(apar[A_NCOMP])
    tailfirst_cg = v_rel[2] < 0.0
    for i in range(ncomp):
        typ = int(comp[i, 0]); z = comp[i, 1]
        if comp[i, 5] == 1.0 and not legs_on:
            continue
        if comp[i, 5] == 2.0 and not flaps_on:
            continue
        rz = z - z_cg
        # local velocity: v_rel + omega x r, r = (0, 0, rz)
        vx = v_rel[0] + omega[1] * rz
        vy = v_rel[1] - omega[0] * rz
        vz = v_rel[2]
        Vl = np.sqrt(vx * vx + vy * vy + vz * vz)
        if Vl < 1e-6:
            continue
        vc = np.sqrt(vx * vx + vy * vy)
        if vc < 1e-9:
            continue
        sa = vc / Vl
        ca = vz / Vl
        q = 0.5 * rho * Vl * Vl
        if typ == LEAD_NOSE:
            cn = (comp[i, 2] if ca >= 0.0 else comp[i, 3]) * sa * abs(ca)
        elif typ == LEAD_BASE:
            if ca < 0.0:
                cn = comp[i, 2] * sa * abs(ca)
                if engine_on:
                    cn *= apar[A_K_RETRO]       # plume-dominated retropropulsion (unknown)
            else:
                cn = comp[i, 3] * sa * abs(ca)
        elif typ == CROSSFLOW:
            cn = comp[i, 2] * comp[i, 4] * sa * sa
        elif typ == FIN:
            # linear lift up to ~stall, then flat-plate crossflow
            a = np.arcsin(min(sa, 1.0))
            cl = comp[i, 2] if ca >= 0.0 else comp[i, 3]
            lin = cl * sa * abs(ca)
            cnmax = 1.2 * comp[i, 4]
            plate = 1.2 * comp[i, 4] * sa * sa
            cn = lin if lin < cnmax else cnmax
            if plate > cn:
                cn = plate
        else:  # FLAP (deployed at the top): normal-force slope + crossflow on plate area
            cn = comp[i, 2] * comp[i, 4] * sa * abs(ca) + 1.2 * comp[i, 4] * sa * sa
        f = -q * S * cn / vc
        fx = f * vx
        fy = f * vy
        out_F[0] += fx
        out_F[1] += fy
        # M = r x F, r = (0,0,rz): (-rz*Fy, rz*Fx, 0)
        out_M[0] += -rz * fy
        out_M[1] += rz * fx
    # axial force (at the CG velocity)
    ca = v_rel[2] / V
    qcg = 0.5 * rho * V * V
    if ca >= 0.0:
        CA = apar[A_CA0_NF] + (apar[A_CA_ENGON_NF] if engine_on else 0.0)
    else:
        CA = apar[A_CA0_TF]
        if engine_on:
            CA = apar[A_CA0_TF] * (0.5 + 0.5 * apar[A_K_RETRO])
    if legs_on:
        CA += apar[A_CA_LEGS]
    out_F[2] += -qcg * S * CA * ca
    # nose flaps: extra drag along -v_rel applied at the flap station
    if flaps_on and apar[A_FLAP_CDA] > 0.0:
        fd = -qcg * apar[A_FLAP_CDA] / V
        out_F[0] += fd * v_rel[0]; out_F[1] += fd * v_rel[1]; out_F[2] += fd * v_rel[2]
        rz = apar[A_FLAP_Z] - z_cg
        out_M[0] += -rz * fd * v_rel[1]
        out_M[1] += rz * fd * v_rel[0]
    # nose drogue: tension along -v_rel at the nose tip (quasi-steady, massless canopy)
    if apar[A_DROGUE_DEPLOYED] > 0.5 and apar[A_DROGUE_CDA] > 0.0:
        rz = apar[A_DROGUE_Z] - z_cg
        vx = v_rel[0] + omega[1] * rz
        vy = v_rel[1] - omega[0] * rz
        vz = v_rel[2]
        Vl = np.sqrt(vx * vx + vy * vy + vz * vz)
        if Vl > 1e-6:
            T = 0.5 * rho * Vl * Vl * apar[A_DROGUE_CDA]
            fx = -T * vx / Vl; fy = -T * vy / Vl; fz = -T * vz / Vl
            out_F[0] += fx; out_F[1] += fy; out_F[2] += fz
            out_M[0] += -rz * fy
            out_M[1] += rz * fx


def static_coefficients(apar, comp, z_cg, alpha_deg, engine_on=False, rho=1.225, V=30.0):
    """Python helper: CN, CA, Cm (about z_cg, ref d), x_cp station, for a sweep of alpha."""
    out = []
    F = np.zeros(3); M = np.zeros(3)
    S, d = apar[A_SREF], apar[A_D]
    q = 0.5 * rho * V * V
    for a in np.atleast_1d(alpha_deg):
        ar = np.radians(a)
        v = np.array([V * np.sin(ar), 0.0, V * np.cos(ar)])
        aero_forces(v, np.zeros(3), rho, z_cg, engine_on, apar, comp, F, M)
        CNx = -F[0] / (q * S)            # positive opposing +x crossflow
        CA = -F[2] / (q * S)
        Cm = M[1] / (q * S * d)          # + means nose rotates toward +x (into the wind side)
        zcp = z_cg + (M[1] / F[0]) if abs(F[0]) > 1e-9 else np.nan
        out.append((a, CNx, CA, Cm, zcp))
    return np.array(out)

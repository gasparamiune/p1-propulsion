"""Engine layout: axial stations (mm, engine frame) and the gas-path contour from the parameter set.

Engine frame (CAD, STEP): origin = gimbal pivot (intersection of the two gimbal axes) at neutral,
+Z = engine axis pointing forward (nozzle -> injector), +X = outer gimbal axis (ring pins in the fixed yoke
lugs), +Y = inner gimbal axis (engine-collar pins in the ring).  Millimetres.  CAD v3: the pivot sits at the
mid-burn CG of the gimballed engine; the head mid-plane is z_head_mid above it (iterated by build.py).

Gas path: combustion.json gives x_face (m) measured from the injector face toward the exit;
z = z_face - 1000 * x_face.
"""
from __future__ import annotations
import csv, math
import numpy as np


def mm(P, k):
    return P[k]["v"] * 1000.0


def read_contour(path):
    """Return [(x_face_mm, r_mm, region)] from the combustion contour CSV (comment lines start with #)."""
    rows = []
    import config
    with open(config.shared(path)) as f:
        lines = [ln for ln in f if not ln.startswith("#")]
    for r in csv.DictReader(lines):
        rows.append((float(r["x_face_m"]) * 1e3, float(r["r_m"]) * 1e3, r.get("region", "")))
    return rows


def conical_contour(P, n=60):
    """Placeholder conical convergent + throat arcs + conical divergent when no contour CSV exists.
    Returns [(x_face_mm, r_mm, region)] starting at the end of the post-chamber."""
    rt = mm(P, "Dt") / 2
    re = mm(P, "De") / 2
    rc = mm(P, "D_post") / 2
    th_c = math.radians(P["conv_half_angle_deg"]["v"])
    th_d = math.radians(P["div_half_angle_deg"]["v"])
    Ru = P["rc_up_over_rt"]["v"] * rt
    Rd = P["rc_dn_over_rt"]["v"] * rt
    xu = -Ru * math.sin(th_c)
    ru = rt + Ru * (1 - math.cos(th_c))
    xd = Rd * math.sin(th_d)
    rd = rt + Rd * (1 - math.cos(th_d))
    x_in = xu - (rc - ru) / math.tan(th_c)
    x_ex = xd + (re - rd) / math.tan(th_d)
    x0 = (P["x_grain_end"]["v"] + P["L_post"]["v"]) * 1e3
    pts = [(x_in, rc, "conv_cone")]
    for a in np.linspace(th_c, 0, n // 3):
        pts.append((-Ru * math.sin(a), rt + Ru * (1 - math.cos(a)), "throat_up"))
    for a in np.linspace(0, th_d, n // 3)[1:]:
        pts.append((Rd * math.sin(a), rt + Rd * (1 - math.cos(a)), "throat_down"))
    pts.append((x_ex, re, "div_cone"))
    return [(x0 + (x - x_in), r, g) for x, r, g in pts]


def x_at_r(contour, r_target):
    """First x (convergent side) where the contour radius drops to r_target (linear interpolation)."""
    for (x0, r0, _), (x1, r1, _) in zip(contour[:-1], contour[1:]):
        if r0 >= r_target >= r1 and r0 != r1:
            return x0 + (r0 - r_target) / (r0 - r1) * (x1 - x0)
    raise ValueError(f"radius {r_target} not on the convergent")


def stations(P):
    S = {}
    H0 = mm(P, "z_head_mid")                                         # head mid-plane above the pivot (CG pivot, v3)
    S["head_mid"] = H0
    S["head_top"] = H0 + mm(P, "head_h") / 2
    S["head_bot"] = H0 - mm(P, "head_h") / 2
    S["tube_fwd"] = S["head_bot"] - mm(P, "head_gap")
    S["inj_face"] = S["tube_fwd"] - mm(P, "plug_len_fwd")          # x_face = 0 (gas-side face)
    zf = S["inj_face"]
    z = lambda x_mm: zf - x_mm
    S["z_of_x"] = z
    S["pre_bot"] = z(mm(P, "L_pre"))
    S["grain_top"] = z(mm(P, "x_grain_start"))
    S["grain_bot"] = z(mm(P, "x_grain_end"))
    S["post_bot"] = z(mm(P, "x_grain_end") + mm(P, "L_post"))
    if P["contour_csv"]["v"]:
        cont = read_contour(P["contour_csv"]["v"])
        S["contour_src"] = P["contour_csv"]["v"]
    else:
        cont = conical_contour(P)
        S["contour_src"] = "conical placeholder (layout.conical_contour)"
    # prepend the post-chamber end so the profile starts on the cylinder
    x_post_end = mm(P, "x_grain_end") + mm(P, "L_post")
    if cont[0][0] > x_post_end + 1e-6:
        cont = [(x_post_end, mm(P, "D_post") / 2, "post_chamber_end")] + cont
    S["contour_x"] = cont                                            # [(x_mm, r_mm, region)]
    S["contour"] = [(z(x), r) for x, r, _ in cont]                  # [(z_mm, r_mm)]
    xt = min(cont, key=lambda t: t[1])[0]
    S["throat"] = z(xt)
    S["rt"] = min(r for _, r, _ in cont)
    S["exit"] = z(cont[-1][0])
    S["re"] = cont[-1][1]
    x_ins = x_at_r(cont, mm(P, "insert_r_start"))
    S["insert_top"] = z(x_ins)
    S["x_insert_top"] = x_ins
    # v3.1 (MEOP 45 bar): the insert carries an aft spigot through the closure lip; insert bottom face = lip bottom
    # face = aft-most face of the engine; the lip bears on the insert shoulder through the Grafoil ring
    S["insert_bot"] = S["exit"] - mm(P, "insert_ext_below_exit")
    S["aft_bottom"] = S["insert_bot"]
    S["gasket_t"] = mm(P, "shoulder_gasket_t") if "shoulder_gasket_t" in P else 0.5
    S["nozzle_joint"] = P["nozzle_joint"]["v"] if "nozzle_joint" in P else "MICA"
    if S["nozzle_joint"] in ("J1", "J1B", "J2"):   # J2 (screen, 2026-10-13): the J1 stack geometry with a zirconia hot layer
        # v3.4.1 J1 (Combustion nozzle_joint_v2p4, lead 2026-10-13): lip top -> 0.5 mm flexible-graphite seal (NZ-04) -> 2.0 mm carbon-phenolic
        # hot layer (NZ-03) -> insert shoulder.  The insert bottom stays flush with the lip bottom: the spigot grows by 1.5 mm, the 44 mm body shortens
        # J1B (screen, coordinator 2026-10-13): a mica/vermiculite layer NZ-05 (nz_mica_t) between the seal and the hot layer
        S["nz_seal_t"] = mm(P, "nz_seal_t")
        S["nz_hot_layer_t"] = mm(P, "nz_hot_layer_t")
        S["nz_mica_t"] = mm(P, "nz_mica_t") if S["nozzle_joint"] == "J1B" else 0.0
        S["gasket_t"] = S["nz_seal_t"] + S["nz_mica_t"] + S["nz_hot_layer_t"]
    S["lip_top"] = S["aft_bottom"] + mm(P, "aft_lip_t")
    S["insert_shoulder"] = S["lip_top"] + S["gasket_t"]
    # v3.2 (lead relay 2026-10-12, soak-back / post-chamber wall): the aluminium case ends at the grain's aft face; the
    # post-chamber, convergent and insert sit in a separate high-temperature aft section (316L baseline) screwed onto
    # the case's aft thread.  Its bore steps from the 61.0 post-chamber bore to the insert bore where the convergent
    # insulator keeps >= post_insul_min_t over the steel.
    S["tube_aft"] = S["grain_bot"]                                   # case end face on the post-chamber insulator top
    r_ib = mm(P, "insert_OD") / 2 + mm(P, "insert_sleeve_t")
    S["r_insert_bore"] = r_ib
    t_min = mm(P, "post_insul_min_t") if "post_insul_min_t" in P else 3.0
    S["aft_step"] = z(x_at_r(cont, r_ib - t_min))                    # bore step 61.0 -> insert bore
    S["aft_land_top"] = S["tube_aft"] + mm(P, "aft_land_len")
    S["aft_thread_top"] = S["aft_land_top"] + mm(P, "aft_thread_len")
    S["bolt_z_fwd"] = S["tube_fwd"] - mm(P, "bolt_edge_chamber")
    S["case_len"] = S["tube_fwd"] - S["tube_aft"]
    S["L_pivot_exit"] = -S["exit"]
    S["L_pivot_bottom"] = -S["aft_bottom"]
    S["gas_path_len"] = S["inj_face"] - S["exit"]
    return S


if __name__ == "__main__":
    import sys, json
    sys.path.insert(0, ".")
    import config
    P, _ = config.build()
    S = stations(P)
    print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in S.items()
                      if k not in ("contour", "contour_x", "z_of_x")}, indent=1))

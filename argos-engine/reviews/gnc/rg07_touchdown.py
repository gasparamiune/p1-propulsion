"""rg07_touchdown v1 (independent GNC review, 2026-10-13): rigid-body tip-over energy check of the touchdown criteria
(vh <= 0.5 m/s, body rate <= 10 deg/s, tilt <= 5 deg; run6.CRIT) against the ASSUMED leg geometry.

Model (DERIVED, worst case for tipping): the vehicle lands with horizontal speed vh, body rate w and tilt th all toward the
downhill pivot; the pivot is the line through the two feet either side of the direction of travel (4 legs at 90 deg: lever
r cos 45 deg) or a single foot (lever r); perfectly plastic impact at the pivot with no slip (friction infinite); angular
momentum about the pivot conserved through the impact; the vehicle tips if the post-impact rotational energy exceeds the
potential-energy rise to the vertical over the pivot. Ground slope s adds to the tilt. Leg compression and spring return are
ignored at the impact (the stroke lowers the CG; shown as a bracket with the CG 0.10 m lower).
Inputs: touchdown mass properties gnc vehicle massprops_events_v3d.csv (m 14.767 kg, z_cg 0.6542 m, I_t 4.2608 kg m2);
legs ASSUMED in gnc.json v3 (4 legs, foot radius 0.40 m, foot plane 0.25 m below the aft datum, stroke 0.10 m).
Output: rg07_touchdown.json
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
G = 9.80665
M, ZCG, IT = 14.767, 0.6542, 4.2608
R_FOOT, Z_FOOT, STROKE = 0.40, -0.25, 0.10


def case(vh, w_dps, tilt_deg, slope_deg, pivot="between", h_drop=0.0):
    h = ZCG - Z_FOOT - h_drop                      # CG height above the foot plane
    r = R_FOOT * (math.cos(math.radians(45.0)) if pivot == "between" else 1.0)
    rho = math.hypot(h, r)                         # CG distance from the pivot
    phi_tip = math.atan2(r, h)                     # tilt at which the CG is above the pivot (flat ground)
    th = math.radians(tilt_deg + slope_deg)        # tilt relative to the local vertical, toward the pivot
    w = math.radians(w_dps)
    # CG position relative to the pivot at impact (angle of the pivot->CG line from the vertical = phi_tip - th)
    a = phi_tip - th
    # angular momentum about the pivot: m (r_cg x v) + I w; horizontal vh toward the pivot side at CG height rho cos a
    L = M * vh * rho * math.cos(a) + IT * w
    Ip = IT + M * rho * rho
    ke = L * L / (2.0 * Ip)
    dPE = M * G * rho * (1.0 - math.cos(a)) if a > 0 else 0.0
    return dict(vh=vh, w_dps=w_dps, tilt_deg=tilt_deg, slope_deg=slope_deg, pivot=pivot, h_cg=h, lever=r,
                tip_angle_flat_deg=math.degrees(phi_tip), remaining_deg=math.degrees(a), ke_post_J=ke, pe_to_tip_J=dPE,
                margin=dPE / ke if ke > 0 else float("inf"), tips=bool(ke >= dPE))


def slope_limit(vh, w, tilt, pivot, h_drop=0.0):
    lo, hi = 0.0, 30.0
    if case(vh, w, tilt, 0.0, pivot, h_drop)["tips"]:
        return 0.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if case(vh, w, tilt, mid, pivot, h_drop)["tips"]:
            hi = mid
        else:
            lo = mid
    return lo


def main():
    out = dict(script="rg07_touchdown v1", inputs=dict(m=M, z_cg=ZCG, I_t=IT, r_foot=R_FOOT, z_foot=Z_FOOT, stroke=STROKE), cases=[])
    for pivot in ("between", "over_leg"):
        for hd in (0.0, STROKE):
            for (vh, w, tl) in ((0.5, 10.0, 5.0), (0.5, 0.0, 0.0), (0.0, 10.0, 5.0), (0.3, 5.0, 2.0)):
                c = case(vh, w, tl, 0.0, pivot, hd)
                c["h_drop"] = hd
                c["slope_limit_deg"] = slope_limit(vh, w, tl, pivot, hd)
                out["cases"].append(c)
                print(f"{pivot:8s} drop {hd:.2f} vh {vh} w {w} tilt {tl}: tip angle {c['tip_angle_flat_deg']:.1f} deg, KE {c['ke_post_J']:.2f} J, "
                      f"PE to tip {c['pe_to_tip_J']:.2f} J, margin x{c['margin']:.2f}, ground slope that removes the margin {c['slope_limit_deg']:.1f} deg")
    json.dump(out, open(os.path.join(HERE, "rg07_touchdown.json"), "w"), indent=1)


if __name__ == "__main__":
    main()

"""J-FWD TC-01 near-hole ligament station + TC-02 thread resultant per step, for seat patches and global runs (fea3d 2026-10-20 ~13:00Z;
lead 12:52Z (2): in (b2), and later (b1), per step: the TC-01 ligament station 0.08 mm from the hole wall, the cell Mechanical carries
as information on the sharp geometry and re-rules on the broken edge, and the TC-02 thread-tie resultant, axial and radial).

Station (SIM stress field, DERIVED linearisation; the definition of jfwd_ligament.py's first station, so js5's ligament.json row is the
sharp-geometry reference): the full-wall radial line on the hole-centre plane z = Z_SCREW - shift at the azimuth offset
delta_1 = 5.688 deg from the screw axis (the first of 40 stations from asin(2.76 / 28.627)), each side (- / +), from the bore r 28.627
to the seat surface (spot face: x' 31.313 / cos delta; else the OD); it passes 0.087 mm from the hole wall at the bore and about
0.37 mm at the seat.  Stresses in (r, theta, z); Pm = vM of the mean, Pm+Pb = max vM(mean +- bending) with the linear through-wall
weight (as jfwd_ligament.station).  CLIPPED to the material: the line is sampled at 0.005 mm and only the contiguous run of points
inside the TC-01 elements (best barycentric >= -0.02) is linearised.  On a sharp mesh this is the whole line (identical to
jfwd_ligament); on the broken-edge meshes (s6 / s9: R0.2 at the bore-side hole edge) the line enters the material where it crosses the
R0.2 break, and the start radius, its distance from the hole wall and the clipped length are reported (re-ruling basis on the broken
edge).  In a patch only the patch's own TC-01 elements are searched (the stations lie inside every patch box).
Thread resultant (from shank.json, jfwd_shank 'plane_exact'): the force TC-02 passes into the screw through the bonded thread =
the screw's exact shear-plane resultant (in a patch it includes the prescribed cut-boundary reactions of the screw at x' ~ xcut, i.e.
the thread force beyond the patch carried by the cut): N along the screw axis (= engine-radial at az 18 deg; + = tension),
V_z engine-axial, V_t tangential.
usage: jfwd_lig_station.py JOB -> jfwd/runs/JOB/lig_station.json"""
from __future__ import annotations
import sys, json, math, gzip
from pathlib import Path
import numpy as np

sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import jfwd_sub as JS        # noqa: E402
import jfwd_deck as JD       # noqa: E402
import jfwd_post as JP       # noqa: E402
import jfwd_ligament as JL   # noqa: E402

TOL = -0.02


def delta_1():
    dmin = math.asin((JL.HR + 0.01) / JL.R_IN)
    dmax = math.radians(JS.AZ_SCREW - 0.02)
    return dmin + 0.5 * (dmax - dmin) / 40


def station_clip(loc, S, zc, az, ro, ds=0.005, n=41):
    rs = np.arange(JL.R_IN, ro + 1e-9, ds)
    P = np.column_stack([rs * math.cos(az), rs * math.sin(az), np.full(len(rs), zc)])
    _, _, best = loc.bary(P)
    inside = best >= TOL
    if not inside.any():
        return None
    i0 = int(np.argmax(inside))
    i1 = i0
    while i1 + 1 < len(rs) and inside[i1 + 1]:
        i1 += 1
    r0, r1 = float(rs[i0]), float(rs[i1])
    s = np.linspace(0.0, 1.0, n)
    rr = r0 + s * (r1 - r0)
    Pq = np.column_stack([rr * math.cos(az), rr * math.sin(az), np.full(n, zc)])
    Sv, bq = loc.interp(S, Pq)
    sc = JL.cyl(Sv, np.full(n, az))
    sm = np.trapezoid(sc, s, axis=0)
    sb = 6.0 * np.trapezoid(sc * (0.5 - s)[:, None, None], s, axis=0)
    d = math.radians(abs(math.degrees(az) - JS.AZ_SCREW))
    return {"r_start_mm": round(r0, 4), "r_end_mm": round(r1, 4), "length_mm": round(r1 - r0, 4),
            "d_hole_wall_at_start_mm": round(r0 * math.sin(d) - JL.HR, 4),
            "clipped_mm": round(r0 - JL.R_IN, 4), "n_outside_samples": int((~inside).sum()),
            "Pm": round(JL.vm33(sm), 1), "PmPb": round(max(JL.vm33(sm + sb), JL.vm33(sm - sb)), 1),
            "s_m_rtz": JL.t6(sm), "s_b_rtz": JL.t6(sb), "min_bary_used": round(float(bq.min()), 4)}


def main(job):
    wd = JD.RUNS / job
    meta = json.loads((wd / "meta.json").read_text())
    patch = meta.get("kind") == "seat_submodel"
    tag = meta["mesh"]
    mj = JS.use_mesh(tag)
    shift = mj["shift"]
    m = dict(np.load(JD.OUT / f"model_{tag}.npz", allow_pickle=False))
    X, T, B = m["X"], m["T"], m["B"]
    keep = np.ones(len(T), bool)
    if patch:
        keep = dict(np.load(JD.OUT / f"seat_{meta['seat_tag']}.npz", allow_pickle=False))["keep"]
    loc01 = JP.Locator(X, T[np.nonzero(keep & (B == "TC-01"))[0]])
    frd = wd / f"{job}.frd"
    if frd.exists():
        by = JP.read_frd_steps(frd, len(X))
    else:
        JP.open = lambda p, mode="r", errors=None: gzip.open(str(p) + ".gz", "rt", errors=errors)
        try:
            by = JP.read_frd_steps(frd, len(X))
        finally:
            del JP.open
    sh = json.loads((wd / "shank.json").read_text()) if (wd / "shank.json").exists() else {"steps": {}}
    zc = JS.Z_SCREW - shift
    d1 = delta_1()
    out = {"job": job, "patch": patch, "mesh": tag, "seat": JS.GEO.get("seat"), "brk_r": JS.GEO.get("brk_r", 0.0), "brk_c": JS.GEO.get("brk_c", 0.0),
           "doc": __doc__.split("usage:")[0].strip(), "delta_1_deg": round(math.degrees(d1), 4),
           "d_hole_wall_at_bore_mm": round(JL.R_IN * math.sin(d1) - JL.HR, 4), "steps": {}}
    for k, nm in enumerate(meta["steps"]):
        if (k + 1) not in by or "STRESS" not in by[k + 1]:
            continue
        S = by[k + 1]["STRESS"]
        rec = {}
        for sgn, side in ((-1, "-"), (+1, "+")):
            az = math.radians(JS.AZ_SCREW) + sgn * d1
            ro = JS.r_out(d1, 0.0) if JS.GEO.get("seat") == "spot" else JL.R_OUT
            rec["side" + side] = station_clip(loc01, S, zc, az, ro)
        pe = (sh["steps"].get(nm) or {}).get("plane_exact")
        if pe:
            vv = np.array(pe["V_vec_N"], float)
            rec["TC02_thread_resultant"] = {"N_along_screw_engine_radial_N": pe["N_N"], "V_engine_axial_z_N": pe["V_axial_z_N"],
                                            "V_tangential_N": round(float(np.hypot(vv[0], vv[1])), 1), "V_total_N": pe["V_N"],
                                            "source": "shank.json plane_exact (exact nodal internal forces)"}
        out["steps"][nm] = rec
        a, b = rec["side-"], rec["side+"]
        print(f"{nm:10s} station d{math.degrees(d1):.3f}: - Pm {a and a['Pm']} PmPb {a and a['PmPb']} (start r {a and a['r_start_mm']}, "
              f"{a and a['d_hole_wall_at_start_mm']} mm off the wall) | + Pm {b and b['Pm']} PmPb {b and b['PmPb']} (start r "
              f"{b and b['r_start_mm']}) | thread N {pe and pe['N_N']} Vz {pe and pe['V_axial_z_N']}", flush=True)
    (wd / "lig_station.json").write_text(json.dumps(out, indent=1, default=float))
    print("wrote", wd / "lig_station.json")


if __name__ == "__main__":
    main(sys.argv[1])

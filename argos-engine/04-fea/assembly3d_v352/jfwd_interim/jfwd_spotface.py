"""J-FWD head-seat sensitivity (lead 2026-10-20 06:17Z), [DERIVED] from the js4 FE resultants, NO new runs (fea3d 2026-10-20).
The CAD seat is the cylindrical TC-01 OD R31.75 (the flat button-head face bears along a line).  Candidate: a d10.5 flat spot face on
R31.75, 0.437 mm deep at the screw axis, local wall 3.125 -> 2.69 mm.
Per posted step:
  * head bearing: F_head (exact K u resultant) on (a) the FE line-contact strip (faces with CPRESS > 0; CAD as is) and (b) the full
    flat seat annulus d9.5 / d5.5 (47.12 mm2), against Fty(T) and Fbry(T) = 1.40 Fty(T) (engmat e/D 2 ratio, LITERATURE-approx, conservative);
  * TC-01 hole-region SCL with the wall cut: membrane x k1 = 3.125 / 2.69, bending x k1^2 (same force and moment on the thinner local
    section), Pm and Pm+Pb recombined on the tensors; net-ligament lines at the hole flank (inside the d10.5 seat) and the shear-out lines
    (7.4 mm from the axis, outside the seat: the scaled value is a bound);
  * hole bearing V_bear / (D t), D 5.0 mm (shank), t 3.125 (CAD) and 2.69 mm (seat), against Fbry(T) / Fbru(T) = 1.40 Fty / 1.60 Ftu
    (e/D = 12.0 / 5.5 = 2.18 >= 2: the e/D 2 ratios apply), with the case member SF.
usage: jfwd_spotface.py JOB [partial] -> jfwd/runs/JOB/spotface.json"""
import sys, json, math
import numpy as np
sys.path.insert(0, "/home/claude/work/fea3d/scripts")
import jfwd_deck as JD   # noqa: E402
import jfwd_post as JP   # noqa: E402

T_CAD, T_SEAT = 3.125, 2.69
K1 = T_CAD / T_SEAT
A_ANN = math.pi / 4.0 * (9.5 ** 2 - 5.5 ** 2)
D_SH = 5.0


def main(job, partial):
    global K1
    wd = JD.RUNS / job
    d = json.loads((wd / ("post_partial.json" if partial else "post.json")).read_text())
    spot = d["meta"].get("seat") == "spot"
    # 2026-10-20 08:35Z: on a spot-face mesh (s5: js5 ...) the FE IS the seat: no scaling (K1 = 1), hole bearing at the FE wall 2.688
    walls = (("spot_t2.688", 2.688),) if spot else (("CAD_t3.125", T_CAD), ("seat_t2.69", T_SEAT))
    if spot:
        K1 = 1.0
    out = {"job": job, "tag": ("SIM resultants on the spot-face mesh (FE seat, no scaling)" if spot else "DERIVED from SIM resultants (js4); no new run"),
           "seat": "spot" if spot else "cad", "k1_membrane": K1, "k2_bending": K1 ** 2, "A_annulus_mm2": A_ANN, "steps": {}}
    for st, o in d["steps"].items():
        ce = o.get("contact_exact") or {}
        Fh = ce.get("HEAD_on_screw_along_axis_N")
        Vb = ce.get("BEAR_shear_perp_axis_N")
        T01 = o["TC-01"]["band"]["T_C"]
        Fty, Ftu = JP.tab("AL6061-T6", "Fty", T01), JP.tab("AL6061-T6", "Ftu", T01)
        Fbry, Fbru = 1.40 * Fty, 1.60 * Ftu
        msf = o["case_rule"]["member_SF"] if "case_rule" in o else (1.0, 1.0)
        A_strip = o["contact"]["HEAD"]["area_in_contact_mm2"]
        rec = {"T_TC01_C": T01, "Fty_MPa": round(Fty, 1), "Fbry_MPa": round(Fbry, 1), "member_SF": msf,
               "head_bearing": {"F_head_N": Fh, "strip_area_mm2": A_strip, "strip_avg_MPa": round(Fh / A_strip, 1) if Fh and A_strip else None,
                                "strip_avg_over_Fty": round(Fh / A_strip / Fty, 3) if Fh and A_strip else None,
                                "flat_seat_avg_MPa": round(Fh / A_ANN, 1) if Fh else None,
                                "flat_seat_avg_over_Fty": round(Fh / A_ANN / Fty, 3) if Fh else None,
                                "flat_seat_MS_vs_Fbry": round(Fbry / (Fh / A_ANN) - 1, 3) if Fh else None},
               "SCL_seat": {}, "hole_bearing": {}}
        for nm, v in o["SCL"].items():
            if not nm.startswith("TC01_") or "mid_az" in nm or "sm" not in v:
                continue
            sm, sb = np.array(v["sm"]), np.array(v["sb"])
            Pm2 = float(JP.vm(K1 * sm))
            PmPb2 = float(max(JP.vm(K1 * sm + K1 ** 2 * sb), JP.vm(K1 * sm - K1 ** 2 * sb)))
            rec["SCL_seat"][nm] = {"Pm_CAD": round(v["Pm"], 1), "PmPb_CAD": round(v["PmPb"], 1), "Pm_seat": round(Pm2, 1), "PmPb_seat": round(PmPb2, 1),
                                   "inside_seat": "net_ligament" in nm}
        if Vb is not None:
            for lab, t in walls:
                sbr = Vb / (D_SH * t)
                rec["hole_bearing"][lab] = {"V_N": Vb, "sigma_br_MPa": round(sbr, 1),
                                            "MS_y": round(Fbry / (msf[0] * max(sbr, 1e-9)) - 1, 3), "MS_u": round(Fbru / (msf[1] * max(sbr, 1e-9)) - 1, 3)}
        out["steps"][st] = rec
        hb = rec["head_bearing"]
        print(st, "T01 %.1f Fty %.1f | head F %s strip %s MPa (x%s Fty) flat %s MPa (x%s Fty, MS vs Fbry %s) | hole bearing %s" % (
            T01, Fty, Fh, hb["strip_avg_MPa"], hb["strip_avg_over_Fty"], hb["flat_seat_avg_MPa"], hb["flat_seat_avg_over_Fty"], hb["flat_seat_MS_vs_Fbry"],
            {k: (v["sigma_br_MPa"], v["MS_y"], v["MS_u"]) for k, v in rec["hole_bearing"].items()}))
        for nm, v in rec["SCL_seat"].items():
            print("    ", nm, v)
    (wd / "spotface.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], len(sys.argv) > 2 and sys.argv[2] == "partial")

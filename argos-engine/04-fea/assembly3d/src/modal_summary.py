"""Modal summary for Mechanical (lead 194 period domain) and the ICD-AIRFRAME v2.1 engine-mount modes (fea3d 2026-10-19).

usage: modal_summary.py MODAL_RUN KCHK_RUN [kpose=pose_neutral_c71] [nmax=16]
  MODAL_RUN : results/modal_<run>.json (post_modal.py), mixed-level model
  KCHK_RUN  : results/k_<kchk>.json (post_k.py on a static EAX/EAY run of the SAME mesh) -> Rayleigh check of the rocking modes
  kpose     : results/k_<pose>.json (post_k.py, the production coarse=2 pose model at neutral) -> stiffness actually used by F2/F3
-> results/modal_summary_v351.json, results/tables/modal_v351.md
Tags: f, shapes, shares = SIM (ccx *FREQUENCY, unstressed, T_REF, rigid airframe holes, rigid servo output);
rocking with the servo in series and the Rayleigh check = DERIVED (k_s 58-174 N m/rad per servo ASSUMED, TO-VERIFY bench B-TVC-1;
servo rotor / gear-train reflected inertia NOT included).
"""
from __future__ import annotations
import sys, json, math
from pathlib import Path

RES = Path("/home/claude/work/fea3d/results")
DOF = ["t_x", "t_y", "t_z", "r_x", "r_y", "r_z"]
DESC = {"t_x": "engine lateral X (on the mount)", "t_y": "engine lateral Y (on the mount)", "t_z": "engine axial (thrust path through the gimbal)",
        "r_x": "engine rocking about the outer axis X (alpha, engine + ring)", "r_y": "engine rocking about the inner axis (beta)",
        "r_z": "engine roll about Z (collar / bearings torsion)"}
PATHS = [("pintle_needle_vs_seat_z", "pintle / linkage (needle vs seat, axial)"), ("head_seat_vs_rim_z", "forward closure head (seat vs rim, axial)"),
         ("nozzle_NZ01_vs_J1_lip_z", "nozzle on the J1 lip (NZ-01 vs TC-09 lip, axial)"), ("engine_axial_tz", "engine axial on the mount"),
         ("item_PC_XDCR_ASSUMED_rel_head", "Pc transducer (ASSUMED 26 g) relative to the head"),
         ("item_TORCH_rel_head", "forward equipment: torch"), ("item_RISER_rel_head", "forward equipment: riser"),
         ("item_BLEED_rel_head", "forward equipment: bleed valve"), ("item_FD02_rel_head", "forward equipment: FD-02"),
         ("item_FD04_rel_head", "forward equipment: FD-04"), ("item_PD02_DRIVE_rel_head", "pintle drive (PD-02) relative to the head")]


def dom(row):
    """lead 194 period domain of a response from its modal shares (signed shares of the static response)."""
    b = row["bins"]
    res = row.get("residual_share") or 0.0
    slow = (b["T>20ms"]["share"] or 0.0) + (b["1<T<=20ms"]["share"] or 0.0)
    mid = b["0.1<T<=1ms"]["share"] or 0.0
    return {"share_T_gt_1ms": slow, "share_0.1_1ms": mid, "share_residual_T_lt_Tmin": res,
            "column": ("T > 1 ms dominates: FA1S (DLF 2.0, about 151 bar abs) applies" if slow >= 0.5 else
                       "T > 1 ms share {:.0%}: FA1S on that share, FA1Q (93 / 102 bar) on the rest".format(slow) if slow >= 0.1 else
                       "fast (T <= 1 ms or unresolved residual T < T_min): FA1Q column (93 yield / 102 ult); the 90 bar T <= 0.1 ms column "
                       "only if the residual is shown to be T <= 0.1 ms")}


def main(argv):
    mrun, krun = argv[0], argv[1]
    opts = dict(a.split("=", 1) for a in argv[2:])
    nmax = int(opts.get("nmax", 16))
    md = json.loads((RES / f"modal_{mrun}.json").read_text())
    kc = json.loads((RES / f"k_{krun}.json").read_text())["runs"][0]["axes"]
    kp_f = RES / f"k_{opts.get('kpose', 'pose_neutral_c71')}.json"
    kp = json.loads(kp_f.read_text())["runs"][0]["axes"] if kp_f.exists() else None
    out = {"modal_run": mrun, "model": md["model"], "f_max_Hz": md["f_max_Hz"], "T_min_ms": md["T_min_ms"], "checks": md["checks"],
           "modes": [], "engine_mount_modes": [], "paths": [], "stress_nodes": [], "tags": __doc__.split("Tags:")[1].strip()}
    mass = json.loads((RES.parent / "runs" / mrun / "mass.json").read_text())["group_model_kg"]
    m_mov = sum(v for k, v in mass.items() if k != "fixed")                  # kg on the gimbal (engine + ring + horn)
    allm = md["modes"]
    eff = [(r.get("eff_mass_ccx_t") or [0] * 6) for r in allm]
    ref = [m_mov / 1e3] * 3 + [max(e[i] for e in eff) for i in (3, 4, 5)]   # t | t mm2: rotations normalised by the largest modal value
    out["moving_mass_kg"] = m_mov
    out["effective_mass_sum_note"] = ("per-mode effective masses agree with a lumped-mass recomputation (scratchpad modal_diag/effmass.py, ca2 run); "
                                      "the ccx 'total effective mass' record is not used")
    for r in allm[:nmax]:
        em = r.get("eff_mass_ccx_t") or [0] * 6
        fr = [em[i] / ref[i] if ref[i] > 0 else 0.0 for i in range(6)]
        k = max(range(6), key=lambda i: fr[i])
        rigid = r["engine_rigid_share_of_engine_ke"]
        if rigid >= 0.8 and r["engine_ke_share"] >= 0.8 and fr[k] >= 0.2:
            sec = [i for i in range(6) if i != k and fr[i] >= 0.4 * fr[k]]
            desc = DESC[DOF[k]] + ("".join(f" + {DOF[i]}" for i in sec) if sec else "")
        else:
            k = None
            desc = "local: " + ", ".join(f"{g} {v:.0%}" for g, v in r["top_groups"][:3])
        row = {"mode": r["mode"], "f_Hz": r["f_Hz"], "T_ms": r["T_ms"], "description": desc, "engine_ke_share": r["engine_ke_share"],
               "engine_rigid_share": rigid, "top_groups": r["top_groups"][:3], "eff_fraction_normalised": fr,
               "eff_mass_kg_tx_ty_tz": [x * 1e3 for x in em[:3]], "eff_inertia_kgm2_rx_ry_rz_about_pivot": [x * 1e-3 for x in em[3:]],
               "dominant": DOF[k] if k is not None else None}
        out["modes"].append(row)
    # engine-mount modes: first mode per dominant rigid DOF
    seen = {}
    for r in out["modes"]:
        if r["dominant"] and r["dominant"] not in seen:
            seen[r["dominant"]] = r
    for dof, r in seen.items():
        e = {"dof": dof, "description": r["description"], "mode": r["mode"], "f_FE_rigid_servo_Hz": r["f_Hz"], "T_ms": r["T_ms"]}
        if dof in ("r_x", "r_y"):
            ax = "alpha (outer, X)" if dof == "r_x" else "beta (inner, ring Y)"
            I = r["eff_inertia_kgm2_rx_ry_rz_about_pivot"][0 if dof == "r_x" else 1]
            K_same = kc[ax]["K_FE_engine_Nm_per_rad"]
            e["I_eff_kgm2"] = I
            e["K_static_same_mesh_Nm_per_rad"] = K_same
            e["f_Rayleigh_same_mesh_Hz"] = math.sqrt(K_same / I) / (2 * math.pi)
            if kp:
                Kp = kp[ax]["K_FE_engine_Nm_per_rad"]
                e["K_static_pose_model_Nm_per_rad"] = Kp
                e["f_scaled_to_pose_model_K_Hz"] = r["f_Hz"] * math.sqrt(Kp / K_same)
                for ks in ("58", "174"):
                    Kt = kp[ax]["servo_series"][f"k_s{ks}_engine"]["K_total_Nm_per_rad"]
                    e[f"f_with_servo_k{ks}_Hz_DERIVED"] = r["f_Hz"] * math.sqrt(Kt / K_same)
                    e[f"K_with_servo_k{ks}_Nm_per_rad"] = Kt
        out["engine_mount_modes"].append(e)
    for key, lab in PATHS:
        v = md["functionals"].get(key)
        if not v:
            continue
        out["paths"].append({"functional": key, "path": lab, "governing": v["governing"], "largest_mode": v["largest_mode"],
                             "top_modes": v["top_modes"][:3], **dom(v)})
    for r in md["stress_functionals"]:
        if r["part"] in ("TC-01", "TC-02", "TC-03", "NZ-01", "TC-09", "GM-01", "GM-02", "GM-03"):
            out["stress_nodes"].append({"part": r["part"], "node": r["node"], "tags": r["tags"][:3], "governing": r["governing"], **dom(r)})
    (RES / "modal_summary_v351.json").write_text(json.dumps(out, indent=1, default=float))
    var = json.loads((RES.parent / "runs" / mrun / "model.json").read_text())["variant"]
    lv = var.get("levels") or {}
    lvl = ("every body at level 2" if len(lv) >= 23 else f"level 2: {', '.join(sorted(lv))}; level 1: the rest") if lv else "every body at level 1"
    out["mesh_levels"] = lvl
    L = [f"Modal, CAD v3.5.1, asm v1.2, model {mrun}: {md['model']['n_nodes']} nodes ({lvl}), "
         f"60 modes to {md['f_max_Hz']:.0f} Hz (T_min {md['T_min_ms']:.3f} ms), rigid airframe holes, rigid servo output, unstressed, T_REF. SIM.", "",
         "| mode | f Hz | T ms | shape | engine KE share | engine rigid share | eff. mass kg (x, y, z) | eff. inertia about pivot kg m2 (x, y, z) |",
         "|---|---|---|---|---|---|---|---|"]
    for r in out["modes"]:
        L.append(f"| {r['mode']} | {r['f_Hz']:.1f} | {r['T_ms']:.2f} | {r['description']} | {r['engine_ke_share']:.2f} | {r['engine_rigid_share']:.2f} | "
                 + ", ".join(f"{x:.3f}" for x in r["eff_mass_kg_tx_ty_tz"]) + " | " + ", ".join(f"{x:.4f}" for x in r["eff_inertia_kgm2_rx_ry_rz_about_pivot"]) + " |")
    L += ["", "Engine-mount modes (first mode per engine rigid-body DOF); rocking with the servo output compliance in series (DERIVED):", "",
          "| DOF | mode | f FE, rigid servo Hz | Rayleigh check (static K same mesh) Hz | f at the pose-model K Hz | f with servo k_s 58 / 174 Hz | K used N m/rad |",
          "|---|---|---|---|---|---|---|"]
    for e in out["engine_mount_modes"]:
        if "I_eff_kgm2" in e:
            L.append(f"| {e['description']} | {e['mode']} | {e['f_FE_rigid_servo_Hz']:.1f} | {e['f_Rayleigh_same_mesh_Hz']:.1f} | "
                     f"{e.get('f_scaled_to_pose_model_K_Hz', float('nan')):.1f} | {e.get('f_with_servo_k58_Hz_DERIVED', float('nan')):.1f} / "
                     f"{e.get('f_with_servo_k174_Hz_DERIVED', float('nan')):.1f} | {e['K_static_same_mesh_Nm_per_rad']:.0f} (same mesh), "
                     f"{e.get('K_static_pose_model_Nm_per_rad', float('nan')):.0f} (pose model), servo {e.get('K_with_servo_k58_Nm_per_rad', float('nan')):.0f} / "
                     f"{e.get('K_with_servo_k174_Nm_per_rad', float('nan')):.0f} |")
        else:
            L.append(f"| {e['description']} | {e['mode']} | {e['f_FE_rigid_servo_Hz']:.1f} | - | - | - | - |")
    L += ["", "Load-path periods under chamber pressure (lead 194 domain; shares of the static OP response carried by modes in each band):", "",
          "| path | governing T ms (basis) | share T > 1 ms | share 0.1-1 ms | residual (T < T_min) | FA-1 column |", "|---|---|---|---|---|---|"]
    for p in out["paths"] + [{"path": f"{s['part']} node {s['node']} ({s['tags'][0] if s['tags'] else ''})", **s} for s in out["stress_nodes"]]:
        g = p["governing"]
        gt = f"{g['T_ms']:.3f}" if isinstance(g["T_ms"], float) else g["T_ms"]
        L.append(f"| {p['path']} | {gt} ({g['basis'][:40]}) | {p['share_T_gt_1ms']:+.2f} | {p['share_0.1_1ms']:+.2f} | {p['share_residual_T_lt_Tmin']:+.2f} | {p['column']} |")
    (RES / "tables").mkdir(exist_ok=True)
    (RES / "tables" / "modal_v351.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main(sys.argv[1:])

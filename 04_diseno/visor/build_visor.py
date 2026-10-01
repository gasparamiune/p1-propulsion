#!/usr/bin/env python3
"""build_visor.py — Datos del visor 3D web (04_diseno/visor/).

Lee el CAD (04_diseno/piezas, stl/asm), resultados/manifest.json, sizing.json, estructural.json,
bom.csv e inputs.yaml y escribe:
    04_diseno/visor/mallas.bin    geometría de cada pieza en su marco natural (float32 pos+normal, uint32 índices)
    04_diseno/visor/datos.json    piezas, instancias, marcos cinemáticos, vectores de explosión, textos
La página (index.html) arma la escena con la misma cinemática que verify_parts.py:
    marco HORQUILLA = Pos(xs,0,0)·Rot_z(ψ)·Pos(−xs,0,0) ; marco UNIDAD = HORQUILLA·Pos(px,0,pz)·Rot_y(θ − φ)
Uso: python 04_diseno/visor/build_visor.py
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
D = HERE.parent
ROOT = D.parent
sys.path.insert(0, str(D))
sys.path.insert(0, str(ROOT))

import params as P  # noqa: E402
from build_all import load_parts, loc_matrix  # noqa: E402

SUB_NAMES = {"MNT": "Montaje al espejo y cardán", "HSG": "Cabezal, carcasas y caña", "DRV": "Transmisión y eje",
             "PRP": "Hélice, protector y patín", "STR": "Cola (estructura)", "ELE": "Electrónica y mando",
             "SAF": "Seguridad"}
# desplazamiento de explosión por subsistema [mm, marco BOTE con ψ = φ = 0] + factor de separación interna
EXPLODE = {"MNT": ((-180, 0, 40), 0.5), "HSG": ((0, 0, 260), 0.7), "DRV": ((60, 0, 140), 0.45),
           "PRP": ((260, 0, -160), 0.9), "STR": ((140, 0, -90), 0.4), "ELE": ((0, 0, 220), 0.6),
           "SAF": ((0, 0, 200), 0.6)}
# giro en el modo demo: eje paralelo a X local de la unidad por (y=0, z=z0); relación de giro
SPIN_SHAFT = {"P1-DRV-01", "P1-DRV-06", "P1-DRV-09", "P1-DRV-10", "P1-PRP-03"}
SPIN_MOTOR = {"P1-DRV-04", "P1-DRV-05"}

REVISAR = {
    "P1-MNT-01": ["Medir alto y espesor del espejo real y cargarlos en inputs.yaml (rango 20–65 mm).",
                  "Re-apretar los tornillos de popa antes de cada salida (≤ 2,5 N·m) con placa de reparto A4."],
    "P1-MNT-02": ["Zapata contra el espejo: sin fisuras; Tef-Gel si apoya sobre aluminio."],
    "P1-MNT-04": ["Tuercas cautivas M6: ensayo de arranque P1.3 (≥ 2,1 kN).", "Retén de bola: ajustar 60–130 N en el patín (P5.1)."],
    "P1-MNT-05": ["La cuna toma el empuje: imprimir con el perfil estructural y revisar fisuras alrededor del tubo y del perno de basculación."],
    "P1-DRV-01": ["Tornear SOLO después de comprar y medir la hélice (bore, pasador, retención).",
                  "Montaje desde arriba: rodamiento A → separador → polea → separador → rodamiento B → tuerca."],
    "P1-DRV-02": ["Prensar los bujes igus H370 (Ø18) y probar el ajuste en la probeta P1.2."],
    "P1-DRV-04": ["Contar los imanes del motor real y corregir los polos y el tope de ERPM en el VESC."],
    "P1-DRV-06": ["Re-mandrinar la polea a Ø15 H7 centrando en los dientes (salto ≤ 0,05 mm)."],
    "P1-DRV-07": ["Rodamientos de acero al cromo en zona seca: cambiar por temporada."],
    "P1-PRP-01": ["Holgura punta de pala ↔ aro ≥ 6 mm con la hélice REAL medida."],
    "P1-PRP-02": ["Patín fusible: la probeta del cuello P1.8 debe romper entre 200 y 400 N."],
    "P1-PRP-03": ["Hélice comprada (Minn Kota MKP-32): medir D, paso, bore y pin antes de nada (P0.7)."],
    "P1-PRP-04": ["Pasador de corte 316 Ø2: calibrar con P1.9; cambiar cada 10 h y llevar repuestos."],
    "P1-STR-02": ["Tubo Al 6061-T6 Ø40×3, aislado del eje (bujes igus) y del casco (montaje impreso)."],
    "P1-ELE-01": ["Ensayo T1: caja 30 min a 0,5 m sin agua adentro; O-ring 3,53 mm en cara lijada.",
                  "Montarla alta y a la sombra; el disipador no debe tocar PETG."],
    "P1-ELE-02": ["Disipador comprado con R_th ≤ valor de 02_calculos §5.2."],
    "P1-SAF-01": ["Cordón fail-safe: corte < 1 s en 10/10 intentos (T0) y 200 aperturas sin soldadura (P2.1)."],
}


def mat_color(material: str, process: str) -> str:
    m = material.upper()
    if "PETG" in m:
        return "petg"
    if m.startswith("AL"):
        return "aluminio"
    if "316" in m or "AISI" in m or "440" in m or "52100" in m:
        return "inox"
    if "POM" in m:
        return "pom"
    return "comprado"


def docfirst(mod) -> str:
    d = (mod.__doc__ or "").strip()
    d = d.split("\n\n")[0]
    d = " ".join(x.strip() for x in d.split("\n"))
    import re
    return re.sub(r"^P1-[A-Z]{3}-\d{2}\s*[—-]\s*", "", d)


def mesh_arrays(stl: Path):
    m = trimesh.load_mesh(stl, process=True)
    m.merge_vertices()
    ss = m.smooth_shaded                      # parte vértices en aristas vivas → normales limpias
    pos = np.asarray(ss.vertices, dtype=np.float32)
    nor = np.asarray(ss.vertex_normals, dtype=np.float32)
    idx = np.asarray(ss.faces, dtype=np.uint32).ravel()
    return pos, nor, idx, m


def main():
    p = P.load()
    man = json.loads((ROOT / "resultados" / "manifest.json").read_text(encoding="utf-8"))
    sz = json.loads((ROOT / "resultados" / "sizing.json").read_text(encoding="utf-8"))
    est = json.loads((ROOT / "resultados" / "estructural.json").read_text(encoding="utf-8"))
    bom = list(csv.DictReader(open(ROOT / "bom.csv", encoding="utf-8")))
    man_by = {r["id"]: r for r in man["parts"]}
    mods = {m.META["id"]: m for m in load_parts()}

    xs, px, pz, th = p.swivel_x, p.pivot_x, p.pivot_z, p.theta
    F_yoke = np.eye(4)
    F_unit = np.array(loc_matrix(P.loc_unit(p, 0.0, 0.0)))

    blob = bytearray()
    parts, instances = [], []
    for pid, mod in sorted(mods.items()):
        r = man_by[pid]
        stl = D / "stl" / "asm" / f"{pid}.stl"
        pos, nor, idx, mraw = mesh_arrays(stl)
        off = len(blob)
        for arr in (pos, nor, idx):
            blob += arr.tobytes()
        # marco cinemático real (empírico): fijo al bote, gira con la dirección, o además bascula
        M00 = [np.array(loc_matrix(L)) for L in mod.placements(p, 0.0, 0.0)]
        M20 = [np.array(loc_matrix(L)) for L in mod.placements(p, 20.0, 0.0)]
        M01 = [np.array(loc_matrix(L)) for L in mod.placements(p, 0.0, 10.0)]
        if all(np.allclose(a, b) for a, b in zip(M00, M01)):
            frame = "boat" if all(np.allclose(a, b) for a, b in zip(M00, M20)) else "yoke"
        else:
            frame = "unit"
        F = F_unit if frame == "unit" else F_yoke
        Finv = np.linalg.inv(F)
        sub = pid.split("-")[1]
        ex_w, k_in = EXPLODE.get(sub, ((0, 0, 0), 0.5))
        locs = [np.array(loc_matrix(L)) for L in mod.placements(p, 0.0, 0.0)]
        # validación de la cinemática: placements(ψ, φ) == F(ψ, φ)·local
        psi, phi = 20.0, 10.0
        Ft = np.array(loc_matrix(P.loc_unit(p, psi, phi))) if frame == "unit" else (
            np.array(loc_matrix(P.loc_yoke(p, psi))) if frame == "yoke" else np.eye(4))
        for k, (M, Mt) in enumerate(zip(locs, [np.array(loc_matrix(L)) for L in mod.placements(p, psi, phi)])):
            local = Finv @ M
            assert np.allclose(Ft @ local, Mt, atol=1e-6), f"cinemática distinta en {pid}"
            instances.append({"part": pid, "k": k, "frame": frame, "local": local.round(6).tolist()})
        # centroides en marco BOTE (ψ=φ=0) para la explosión
        c_local = mraw.bounds.mean(axis=0)
        for inst in [i for i in instances if i["part"] == pid]:
            Mw = np.array(locs[inst["k"]])
            inst["c_world"] = (Mw @ np.append(c_local, 1.0))[:3].tolist()
        rows = [x for x in est["rows"] if x["part"].startswith(pid) or pid in x["part"]]
        fs = [x for x in rows if x.get("FS") is not None]
        fs_min = min((x["FS"] for x in fs), default=None)
        bom_rows = [b for b in bom if b.get("ID") == pid]
        parts.append({
            "id": pid, "name": r["name"], "sub": sub, "sub_name": SUB_NAMES.get(sub, sub),
            "desc": r["desc"], "doc": docfirst(mod), "material": r["material"], "process": r["process"],
            "qty": r["qty"], "frame": frame, "color": mat_color(r["material"], r["process"]),
            "mass_g": round(r["mass_g_each"], 1), "print_h": round(r.get("print_hours_each", 0.0), 1),
            "print_bbox": r.get("print_bbox_mm"), "bbox": r.get("bbox_mm"), "orientation": r.get("orientation", "—"),
            "load_case": r.get("load_case", "—"), "checks": r.get("checks", []),
            "fs_rows": [{"caso": x["load_case"], "FS": x["FS"], "obj": x["target"], "ok": x["ok"]} for x in fs],
            "fs_min": fs_min, "files": r.get("files", []), "revisar": REVISAR.get(pid, []),
            "bom": bom_rows[0]["especificacion_minima"] if bom_rows else "",
            "mesh": {"off": off, "nv": int(len(pos)), "ni": int(len(idx))},
            "spin": ("shaft" if pid in SPIN_SHAFT else "motor" if pid in SPIN_MOTOR else None),
        })
        # explosión: subsistema + separación respecto del centroide del subsistema
    for sub in {pp["sub"] for pp in parts}:
        insts = [i for i in instances if i["part"].split("-")[1] == sub]
        cg = np.mean([i["c_world"] for i in insts], axis=0)
        ex_w, k_in = EXPLODE.get(sub, ((0, 0, 0), 0.5))
        for i in insts:
            v_w = np.array(ex_w, dtype=float) + k_in * (np.array(i["c_world"]) - cg)
            F = F_unit if i["frame"] == "unit" else F_yoke
            v_l = np.linalg.inv(F[:3, :3]) @ v_w          # al marco padre (sigue a la cola si se bascula)
            i["explode"] = v_l.round(2).tolist()
    (HERE / "mallas.bin").write_bytes(bytes(blob))

    lay = sz["layout"]
    tr = sz.get("hydrostatics", {})
    inp = p.inp
    datos = {
        "titulo_nombre": "Langhalen",
        "generado": inp["meta"]["date"],
        "kin": {"xs": xs, "px": px, "pz": pz, "theta": th, "steer_max": inp["architecture"]["steer_range_deg"],
                "tilt_max": inp["architecture"]["tilt_range_deg"], "e": p.e, "motor_v": p.motor_v,
                "ratio": sz["selection"]["ratio"]},
        "bote": {"transom_h": inp["boat"]["transom"]["height_mm"], "transom_t": inp["boat"]["transom"]["thickness_mm"],
                 "transom_b": inp["boat"]["transom_beam_m"] * 1000, "beam": inp["boat"]["beam_m"] * 1000,
                 "chine": inp["boat"]["chine_beam_m"] * 1000, "loa": inp["boat"]["loa_m"] * 1000,
                 "side_h": inp["boat"]["side_height_m"] * 1000, "draft": tr.get("draft_m", 0.2) * 1000},
        "resumen": {
            "crucero_kmh": inp["operation"]["cruise_speed_kmh"],
            "autonomia_nom_h": sz["cruise"]["autonomy_nominal_h"], "autonomia_dis_h": sz["cruise"]["autonomy_design_h"],
            "p_crucero_w": sz["cruise"]["design"]["P_bat"], "vmax_kmh": sz["vmax"]["nominal_vnom"]["V_kmh"],
            "vmax_tope_kmh": sz["legal_speed"]["vmax_full_load_with_cap_kmh"], "bollard_n": sz["bollard_fwd"]["T_horiz"],
            "bateria": sz["selection"]["battery_desc"], "e_usable_wh": sz["battery"]["E_usable_wh"],
            "masa_unidad_kg": man["totals"]["unit_mass_kg_cad"], "impreso_kg": man["totals"]["printed_mass_g"] / 1000,
            "horas_impresion": man["totals"]["printed_hours"], "n_piezas": man["totals"]["n_parts"],
            "carga_util_kg": sz["masses"]["payload_kg"], "capacidad_kg": sz["masses"]["capacity_kg"],
        },
        "parts": parts, "instances": [{k: v for k, v in i.items() if k != "c_world"} for i in instances],
    }
    try:
        bomr = json.loads((ROOT / "resultados" / "bom_resumen.json").read_text(encoding="utf-8"))
        datos["resumen"]["costo_eur"] = bomr["total_eur"]
        datos["resumen"]["costo_dkk"] = bomr["total_dkk"]
    except FileNotFoundError:
        pass
    (HERE / "datos.json").write_text(json.dumps(datos, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"visor: {len(parts)} piezas, {len(instances)} instancias, mallas {len(blob)/1e6:.2f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())

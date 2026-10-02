#!/usr/bin/env python3
"""build_visor.py — Datos del visor 3D web del waterjet (04_diseno/visor/).

Lee el CAD (04_diseno/piezas, stl/asm), resultados/{manifest,sizing,estructural,comparacion}.json,
bom.csv e inputs.yaml y escribe:
    mallas.bin / mallas.txt  geometría de cada pieza en su marco natural (float32 pos+normal, uint32 índices;
                             la .txt es la misma en base64 porque los artifacts web no sirven binarios)
    datos.json               piezas, instancias, marcos cinemáticos, explosión, recorrido del agua, textos
    corte_lateral.png        corte por crujía del CAD real (toma, bomba, tren, casco, flotación)
La página (index.html) usa la misma cinemática que verify_parts.py (params.loc_steer / loc_bucket):
    BOQUILLA = J·T(Xp)·Rz(δ)·T(−Xp)            BUCKET = BOQUILLA(δ)·T(Xb,0,Zb)·Ry(β)·T(−Xb,0,−Zb)
    giro del eje = J·Rx(a)·J⁻¹ (eje X del marco JET)
Uso: python 04_diseno/visor/build_visor.py
"""
from __future__ import annotations

import base64
import csv
import json
import re
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

SUB_NAMES = {"INT": "Toma de agua (rejilla y conducto)", "PMP": "Bomba (impulsor, estator, tobera)",
             "DRV": "Tren (eje, sello, rodamientos, acople)", "MOT": "Motor", "STE": "Dirección (boquilla)",
             "REV": "Reversa (bucket)", "CTL": "Mandos de la consola", "ELE": "Electrónica y refrigeración",
             "REF": "Casco (referencia)"}
ORDER = ["INT", "PMP", "DRV", "MOT", "STE", "REV", "ELE", "CTL", "REF"]
# explosión por subsistema [mm, marco BOTE] + separación interna respecto de su centroide
EXPLODE = {"INT": ((0, 0, -260), 0.5), "PMP": ((-260, 0, -40), 0.9), "DRV": ((40, 0, 260), 0.8),
           "MOT": ((260, 0, 300), 0.4), "STE": ((-560, 0, 0), 0.6), "REV": ((-640, 0, 220), 0.6),
           "ELE": ((80, 260, 260), 0.5), "CTL": ((0, 0, 320), 0.5), "REF": ((0, 0, 0), 0.0)}
SPIN = {"P1-DRV-01", "P1-PMP-03", "P1-PMP-04", "P1-PMP-05", "P1-DRV-08"}

REVISAR = {
    "P1-REF-01": ["Es tu casco leído del plano (sin escala única): medir fondo, astilla muerta, espesor, espejo y calado en popa.",
                  "Estabilidad: con 0,80 m de manga y el piloto alto, GM ≈ 0 → hacer el ensayo de escora ANTES de poner el motor."],
    "P1-INT-01": ["Conducto de Al 5083 soldado (no impreso: en PETG no aguanta la fatiga por presión).",
                  "Abertura entera A PROA del impulsor: labio a ~386 mm y tangencia a ~766 mm del espejo.",
                  "Purgar el aire de la chimenea antes de arrancar (tornillo de purga en la tapa)."],
    "P1-INT-02": ["Va enrasada con el fondo, con cama de Sikaflex; 4 espárragos M8 avellanados desde afuera sostienen el soporte de rodamientos."],
    "P1-INT-03": ["Rejilla de 7 pletinas inox con luz de ~16 mm, perfiladas y enrasadas: desmontable desde afuera (4 × M5)."],
    "P1-INT-04": ["Tapa de inspección: sacar algas sin desarmar. La tapa debe quedar ≥ 60 mm sobre la flotación."],
    "P1-PMP-01": ["Carcasa de Al anodizado duro; el agua de refrigeración sale por un puerto G1/8 arriba."],
    "P1-PMP-02": ["Anillo de desgaste inox torneado EN SITIO: holgura de punta 0,3–0,4 mm medida con galgas."],
    "P1-PMP-03": ["Impulsor inox, 5 álabes, CNC 5 ejes (o 316L impreso en metal + torneado del Ø): balancear G6.3.",
                  "Sin chaveta: lo arrastra el pasador de corte."],
    "P1-PMP-05": ["Pasador de corte Al 6061 Ø3,5: fusible si entra una piedra. Llevar 3 de repuesto."],
    "P1-PMP-06": ["Estator de 7 álabes con buje de agua (POM): segundo apoyo del eje."],
    "P1-PMP-08": ["Tobera fija: el chorro sale en el plano del espejo."],
    "P1-PMP-09": ["Placa de espejo con junta NBR: sella el casco y lleva las orejas de la boquilla."],
    "P1-DRV-01": ["Eje 316L Ø20: montar en el orden de 02/06 (todo lo que pasa por el sello mide ≤ Ø20)."],
    "P1-DRV-02": ["Sello mecánico SiC/carbón con cámara de goteo y testigo: si gotea agua por el testigo, cambiar el sello."],
    "P1-DRV-03": ["Pórtico sobre el conducto: lleva TODO el empuje (hasta ~760 N) a la placa base, no al motor."],
    "P1-MOT-01": ["Motor refrigerado por agua: pedir a Maytech la potencia continua real y el caudal de refrigeración."],
    "P1-STE-01": ["Boquilla ±25° con topes mecánicos; cable Ultraflex M66 al volante."],
    "P1-REV-01": ["El bucket es OBLIGATORIO: sin chorro no hay dirección ni freno. Bajarlo solo con el acelerador en 0."],
    "P1-CTL-02": ["Palancas con enclavamiento: el bucket solo se mueve con el acelerador en cero."],
    "P1-CTL-03": ["Kill switch con cordón al chaleco: corta en < 1 s (ensayo de banco 10/10)."],
}


def mat_color(material: str, process: str) -> str:
    m = material.upper()
    if process == "referencia":
        return "casco"
    if "PETG" in m:
        return "petg"
    if m.startswith("AL"):
        return "aluminio"
    if "316" in m or "AISI" in m or "ACERO" in m or "CUAL" in m or "BRONCE" in m:
        return "inox"
    if "POM" in m or "NBR" in m:
        return "pom"
    return "comprado"


def docfirst(mod) -> str:
    d = (mod.__doc__ or "").strip().split("\n\n")[0]
    d = " ".join(x.strip() for x in d.split("\n"))
    return re.sub(r"^P1-[A-Z]{3}-\d{2}\s*[—-]\s*", "", d)


def mesh_arrays(stl: Path):
    m = trimesh.load_mesh(stl, process=True)
    m.merge_vertices()
    ss = m.smooth_shaded
    return (np.asarray(ss.vertices, dtype=np.float32), np.asarray(ss.vertex_normals, dtype=np.float32),
            np.asarray(ss.faces, dtype=np.uint32).ravel(), m)


def detect_frame(mod, p):
    M00 = [np.array(loc_matrix(L)) for L in mod.placements(p, 0.0, 0)]
    M20 = [np.array(loc_matrix(L)) for L in mod.placements(p, 20.0, 0)]
    M01 = [np.array(loc_matrix(L)) for L in mod.placements(p, 0.0, 1)]
    if not all(np.allclose(a, b) for a, b in zip(M00, M01)):
        return "bucket", M00
    if not all(np.allclose(a, b) for a, b in zip(M00, M20)):
        return "steer", M00
    return "boat", M00


def frame_matrix(p, frame, steer=0.0, bucket=0):
    if frame == "steer":
        return np.array(loc_matrix(P.loc_steer(p, steer)))
    if frame == "bucket":
        return np.array(loc_matrix(P.loc_bucket(p, bool(bucket), steer)))
    return np.eye(4)


def water_path(p):
    """Recorrido del agua en el marco BOTE: debajo del casco → rejilla → rampa → cara del impulsor →
    a lo largo del eje hasta la salida de la tobera fija. El chorro (marco JET) lo arma la página."""
    J = np.array(loc_matrix(P.loc_jet(p)))
    pts = [(p.x_tan + 220, 0, -70), (p.x_tan, 0, -35), (0.5 * (p.x_tan + p.x_lip), 0, -8)]
    # rampa: de la abertura a la cara del impulsor (Bezier suave)
    a = np.array([0.5 * (p.x_tan + p.x_lip), 0, 5.0])
    c = np.array([p.x_if + 0.9 * p.D, 0, p.z_if - 10])
    b = np.array([p.x_if, 0, p.z_if])
    for t in np.linspace(0.1, 1.0, 8):
        q = (1 - t) ** 2 * a + 2 * (1 - t) * t * c + t ** 2 * b
        pts.append(tuple(q))
    for X in np.linspace(0.2 * p.D, p.X_noz1, 6):
        pts.append(tuple((J @ np.array([X, 0, 0, 1.0]))[:3]))
    return [list(map(lambda v: round(float(v), 1), q)) for q in pts]


def side_section(p, mods, man_by, out_png: Path, sz):
    """Corte por crujía (y = 0) de todo el ensamblaje en marcha, con cotas de la toma."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    col = {"petg": "#e2601a", "aluminio": "#9fb0ba", "inox": "#5d6b74", "pom": "#d9cfb8", "comprado": "#2f3a40",
           "casco": "#c9d2d6"}
    fig, ax = plt.subplots(figsize=(13, 5.2))
    for pid, mod in sorted(mods.items()):
        r = man_by.get(pid)
        if r is None:
            continue
        m = trimesh.load_mesh(D / "stl" / "asm" / f"{pid}.stl")
        for L in mod.placements(p, 0.0, 0):
            mm = m.copy()
            mm.apply_transform(np.array(loc_matrix(L)))
            try:
                sec = mm.section(plane_origin=[0, 0, 0], plane_normal=[0, 1, 0])
            except Exception:
                sec = None
            if sec is None:
                continue
            c = col[mat_color(r["material"], r["process"])]
            for poly in sec.discrete:
                xz = poly[:, [0, 2]]
                ax.add_patch(Polygon(xz, closed=True, fc=c, ec="#111111", lw=0.4,
                                     alpha=0.45 if r["process"] == "referencia" else 0.95))
    T = sz["hydrostatics"]["draft_m"] * 1000
    ax.axhline(T, color="#1d7486", lw=1.2, ls="--")
    ax.text(0.01, (T + 175) / 735 + 0.012, f"flotación en reposo con {sz['masses']['total_kg']:.0f} kg (calado {T:.0f} mm)",
            transform=ax.transAxes, color="#1d7486", ha="left", fontsize=9)
    for x, lab, dy in ((p.x_if, "cara del impulsor", -105), (p.x_lip, "labio", -150), (p.x_tan, "tangencia de la rampa", -105)):
        ax.annotate(f"{lab}\n{x:.0f} mm", xy=(x, 0), xytext=(x, dy), ha="center", fontsize=8.5,
                    arrowprops=dict(arrowstyle="->", lw=0.8))
    ax.annotate("", xy=(p.x_lip, -40), xytext=(p.x_tan, -40), arrowprops=dict(arrowstyle="<->", lw=1.0, color="#e2601a"))
    ax.text(0.5 * (p.x_lip + p.x_tan), -32, f"abertura con rejilla ({p.L_open:.0f} mm): toda A PROA del impulsor",
            ha="center", fontsize=9, color="#e2601a", weight="bold")
    ax.annotate("espejo (x = 0)", xy=(0, 400), xytext=(-140, 480), fontsize=8.5, arrowprops=dict(arrowstyle="->", lw=0.8))
    ax.text(1400, 470, "← PROA", fontsize=9, color="#56686d", ha="left")
    ax.set_xlim(-480, 1420); ax.set_ylim(-175, 560); ax.set_aspect("equal")
    ax.set_xlabel("x desde el espejo hacia proa [mm]"); ax.set_ylabel("z sobre la quilla [mm]")
    ax.invert_xaxis()
    ax.set_title("Corte por crujía del CAD (proa a la izquierda, popa y chorro a la derecha)", fontsize=10)
    ax.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(out_png, dpi=120); plt.close(fig)


def hull_data(p, sz, ref):
    """Datos del casco completo (2,30 m) para la portada: misma sección que P1-REF-01 + consola,
    volante y piloto. El casco de la portada es ilustrativo (proa dibujada, no medida)."""
    b = p.inp["boat"]
    half = [pt for pt in ref.section_pts(p) if pt[0] >= 0]
    pil = p.inp["masses"]["items"].get("pilot", {})
    return {"loa": b["loa_m"] * 1000, "lwl": b["lwl_m"] * 1000, "half": [list(map(float, pt)) for pt in half],
            "zt": b["transom_height_m"] * 1000, "floor_z": p.floor_z, "t": p.bottom_t,
            "wheel": {"x": p.CTL_wheel_x, "z": p.CTL_wheel_z, "d": p.CTL_wheel_d},
            "console": {"x0": p.CTL_console_x0, "top": p.CTL_console_top},
            "pilot": {"x": pil.get("x_m", 1.38) * 1000, "z": pil.get("z_m", 0.55) * 1000, "kg": pil.get("kg")},
            "draft": sz["hydrostatics"]["draft_m"] * 1000}


def main():
    p = P.load()
    man = json.loads((ROOT / "resultados" / "manifest.json").read_text(encoding="utf-8"))
    sz = json.loads((ROOT / "resultados" / "sizing.json").read_text(encoding="utf-8"))
    est = json.loads((ROOT / "resultados" / "estructural.json").read_text(encoding="utf-8"))
    cmp_p = ROOT / "resultados" / "comparacion.json"
    cmp_ = json.loads(cmp_p.read_text(encoding="utf-8")) if cmp_p.exists() else {}
    bom = list(csv.DictReader(open(ROOT / "bom.csv", encoding="utf-8"))) if (ROOT / "bom.csv").exists() else []
    man_by = {r["id"]: r for r in man["parts"]}
    mods = {m.META["id"]: m for m in load_parts() if m.META["id"] in man_by}

    blob = bytearray()
    parts, instances = [], []
    for pid, mod in sorted(mods.items()):
        r = man_by[pid]
        pos, nor, idx, mraw = mesh_arrays(D / "stl" / "asm" / f"{pid}.stl")
        off = len(blob)
        for arr in (pos, nor, idx):
            blob += arr.tobytes()
        frame, M00 = detect_frame(mod, p)
        F0inv = np.linalg.inv(frame_matrix(p, frame))
        # validación: placements(δ, β) == F(δ, β)·local; si no, pieza con pivote propio (p. ej. palanca
        # del bucket en la consola): se exporta la rotación entre bucket arriba y abajo (eje + punto)
        Mt = [np.array(loc_matrix(L)) for L in mod.placements(p, 17.0, 1)]
        Ft = frame_matrix(p, frame, 17.0, 1)
        c_local = mraw.bounds.mean(axis=0)
        for k, (M, Mx) in enumerate(zip(M00, Mt)):
            local = F0inv @ M
            inst = {"part": pid, "k": k, "frame": frame, "local": local.round(6).tolist(),
                    "c_world": (M @ np.append(c_local, 1.0))[:3].tolist()}
            if not np.allclose(Ft @ local, Mx, atol=1e-5):
                M1 = np.array(loc_matrix(mod.placements(p, 0.0, 1)[k]))
                Ms = np.array(loc_matrix(mod.placements(p, 17.0, 0)[k]))
                if not np.allclose(Ms, M, atol=1e-5):
                    # mecanismo (p. ej. varilla de cable): tabla de poses dirección × bucket, la página interpola
                    S = [-p.steer_max, -p.steer_max / 2, 0.0, p.steer_max / 2, p.steer_max]
                    tab = [[np.array(loc_matrix(mod.placements(p, sv, bv)[k])).round(6).tolist() for sv in S] for bv in (0, 1)]
                    inst.update({"frame": "table", "local": np.eye(4).tolist(), "steers": S, "table": tab})
                    instances.append(inst)
                    continue
                Dm = M1 @ np.linalg.inv(M)
                R, t = Dm[:3, :3], Dm[:3, 3]
                ang = float(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))
                ax = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])
                ax = ax / (np.linalg.norm(ax) or 1.0)
                c = np.linalg.lstsq(np.eye(3) - R, t, rcond=None)[0]
                inst.update({"frame": "own", "local": M.round(6).tolist(), "axis": ax.round(6).tolist(),
                             "angle": ang, "pivot": c.round(3).tolist()})
            instances.append(inst)
        rows = [x for x in est["rows"] if x["part"].startswith(pid) or pid in x["part"]]
        fs = [x for x in rows if x.get("FS") is not None]
        sub = pid.split("-")[1]
        bom_rows = [b for b in bom if pid in (b.get("piezas", "") + b.get("ID", "") + b.get("id", ""))]
        parts.append({
            "id": pid, "name": r["name"], "sub": sub, "sub_name": SUB_NAMES.get(sub, sub),
            "desc": r["desc"], "doc": docfirst(mod), "material": r["material"], "process": r["process"],
            "qty": r["qty"], "frame": frame, "color": mat_color(r["material"], r["process"]),
            "mass_g": round(r["mass_g_each"], 1), "print_h": round(r.get("print_hours_each", 0.0), 1),
            "print_bbox": r.get("print_bbox_mm"), "bbox": r.get("bbox_mm"), "orientation": r.get("orientation", "—"),
            "load_case": r.get("load_case", "—"), "checks": r.get("checks", []),
            "fs_rows": [{"caso": x["load_case"], "FS": x["FS"], "obj": x["target"], "ok": x["ok"]} for x in fs],
            "fs_min": min((x["FS"] for x in fs), default=None), "files": r.get("files", []),
            "revisar": REVISAR.get(pid, []),
            "bom": (bom_rows[0].get("especificacion_minima") or bom_rows[0].get("spec") or "") if bom_rows else "",
            "mesh": {"off": off, "nv": int(len(pos)), "ni": int(len(idx))},
            "spin": pid in SPIN,
        })
    # explosión (vector en el marco del padre: boquilla/bucket siguen a su marco)
    for sub in {pp["sub"] for pp in parts}:
        ins = [i for i in instances if i["part"].split("-")[1] == sub]
        cg = np.mean([i["c_world"] for i in ins], axis=0)
        ex_w, k_in = EXPLODE.get(sub, ((0, 0, 0), 0.5))
        for i in ins:
            v_w = np.array(ex_w, dtype=float) + k_in * (np.array(i["c_world"]) - cg)
            F = frame_matrix(p, i["frame"]) if i["frame"] not in ("own", "table") else np.eye(4)
            i["explode"] = (np.linalg.inv(F[:3, :3]) @ v_w).round(2).tolist()
    (HERE / "mallas.bin").write_bytes(bytes(blob))
    (HERE / "mallas.txt").write_text(base64.b64encode(bytes(blob)).decode("ascii"), encoding="ascii")
    side_section(p, mods, man_by, HERE / "corte_lateral.png", sz)

    inp = p.inp
    pf, en, sel = sz["performance"], sz["energy"], sz["selection"]
    J = np.array(loc_matrix(P.loc_jet(p)))
    datos = {
        "titulo_nombre": "Strålen",
        "generado": inp["meta"]["date"],
        "kin": {"J": J.round(6).tolist(), "Xp": p.X_steer_pivot, "Xb": p.X_bucket_pivot, "Zb": p.Z_bucket_pivot,
                "bucket_down": p.raw.get("bucket_down_deg", 70.0), "steer_max": p.steer_max, "Xnoz": p.X_noz1,
                "Dnoz": p.D_noz},
        "agua": {"path": water_path(p), "draft": sz["hydrostatics"]["draft_m"] * 1000},
        "casco": hull_data(p, sz, mods["P1-REF-01"]),
        "resumen": {
            "vmax_kmh": pf["vmax_cont_kmh"], "vmax_pico_kmh": pf.get("vmax_peak_kmh"),
            "objetivo_kmh": inp["operation"]["top_speed_target_kmh"], "planea": pf["planes"],
            "margen_joroba": pf["hump_margin_min"], "t_planeo_s": pf["t_to_plane_s"],
            "bollard_n": pf["bollard_N"], "t_fondo_min": en["t_top_min"], "t_legal_h": en["t_legal_h"],
            "p_legal_w": pf["legal"]["P_bat"], "masa_total_kg": sz["masses"]["total_kg"],
            "gm_mm": sz["hydrostatics"]["GM_m"] * 1000, "heel_deg": sz["heel_pilot_0p1m_deg"],
            "bateria": sel["battery_desc"], "motor": sel["motor_desc"], "e_usable_wh": en["E_usable_wh"],
            "D_imp": sel["D_imp_mm"], "D_noz": sel["D_noz_mm"],
            "masa_jet_kg": man["totals"]["jet_unit_mass_kg"], "impreso_kg": man["totals"]["printed_mass_g"] / 1000,
            "horas_impresion": man["totals"]["printed_hours"], "n_piezas": man["totals"]["n_parts"],
            "x_lip": p.x_lip, "x_tan": p.x_tan, "x_if": p.x_if,
        },
        "comparacion": {k: cmp_.get(k) for k in ("B_vmax_kmh", "B_hump_margin", "B_jt132_landed_eur_min",
                                                 "B_jt132_landed_eur_max", "B_total_eur_min", "B_total_eur_max",
                                                 "A_jet_mass_kg", "B_jet_mass_kg", "A_total_eur")},
        "parts": parts, "instances": [{k: v for k, v in i.items() if k != "c_world"} for i in instances],
    }
    try:
        bomr = json.loads((ROOT / "resultados" / "bom_resumen.json").read_text(encoding="utf-8"))
        datos["resumen"]["costo_eur"] = bomr["total_eur"]
        datos["resumen"]["costo_dkk"] = bomr["total_dkk"]
    except (FileNotFoundError, KeyError):
        pass
    (HERE / "datos.json").write_text(json.dumps(datos, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"visor: {len(parts)} piezas, {len(instances)} instancias, mallas {len(blob)/1e6:.2f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""P1-DRV-01 — Eje de la bomba, AISI 316 (1.4404) torneado desde barra Ø28 (BOM; R11 §5).

Marco JET (X a popa; estación S = −X). De popa a proa:
  muñón del buje de agua del estator Ø pmp_journal_d f7 (BOMBA, si existe) · ranura DIN 471 de retención
  a popa del impulsor (opcional) · asiento del impulsor Ø20 g6 con agujero transversal del PASADOR DE
  CORTE (2 semipasadores, eje Y, X = pmp_pin_X, Ø H8) · ranura DIN 471-20 del anillo de EMPUJE (+ arandela) contra la nariz
  del impulsor (X = pmp_imp_front_X) · tramo mojado Ø20 h8 (conducto, buje de la toma) · ranura DIN 471
  de respaldo de la cabeza del sello · Ø20 h8 bajo el sello y la linterna · collar Ø26 (≥ da_min) (apoyo de los aros
  interiores) · muñón Ø20 k5 (2 × 7204 BECBP en O) · rosca M20×1 (KM4) con ranura para la MB4 · asiento del
  cubo Rotex 24 Ø20 h6 con chavetero 6 × 3,5 (DIN 6885 A).
Sin bomba con buje (params_bomba ausente): extremo de popa en X_shaft_aft con rosca M16 (tuerca).
Montaje: ver params_tren.py (docstring). Los checks verifican que cada pieza pase por los Ø que debe.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cadlib import box, cyl_y  # noqa: E402
from _drv_geom import cyl_s, stepped, n_crit_rpm  # noqa: E402
from params import loc_jet  # noqa: E402

META = dict(id="P1-DRV-01", name="shaft", desc="Eje Ø20 AISI 316 torneado: impulsor (pasador de corte) → sello → 2×7204 → acople",
            material="AISI 316", process="torneada", qty=1, frame="jet", group="drive",
            load_case="Par T_max del controlador y par de corte del pasador; empuje Fa a punto fijo; velocidad crítica",
            print_rot=(0, 0, 0), solid_frac=1.0, orientation="—",
            allow={"P1-DRV-04": 10.0, "P1-DRV-05": 5.0, "P1-DRV-07": 5.0, "P1-DRV-08": 5.0,
                   "P1-PMP-03": 5.0, "P1-PMP-04": 5.0, "P1-PMP-05": 5.0, "P1-PMP-07": 5.0})


def segments(p):
    """[(s0, s1, Ø, etiqueta)] de popa (S mínimo) a proa — la usan build() y el plano."""
    sd = p.shaft_d
    S_aft = -p.drv_X_aft
    segs = []
    if p.drv_bush:
        S_j = -p.X_shaft_aft
        if p.drv_journal_d < sd - 1e-6:
            segs.append((S_aft, S_j, p.drv_journal_d, f"muñón buje Ø{p.drv_journal_d:g} f7"))
            S_aft = S_j
        else:
            segs.append((S_aft, -p.X_imp1, sd, "muñón buje Ø20 f7"))
            S_aft = -p.X_imp1
    else:
        segs.append((S_aft, -p.X_imp1, p.drv_thread_d, "rosca M16 (tuerca del impulsor)"))
        S_aft = -p.X_imp1
    S_c0 = p.drv_S_brgA - p.drv_collar_l
    segs.append((S_aft, -p.drv_imp_front_X, sd, "asiento impulsor Ø20 g6"))
    segs.append((-p.drv_imp_front_X, S_c0, sd, "tramo mojado / sello Ø20 h8"))
    segs.append((S_c0, p.drv_S_brgA, p.drv_collar_d, f"collar Ø{p.drv_collar_d:g}"))
    segs.append((p.drv_S_brgA, p.drv_S_brgB, sd, "muñón 2×7204 Ø20 k5"))
    S_t1 = p.drv_S_brgB + p.drv_km["mb_t"] + p.drv_km["b"] + 1.0
    segs.append((p.drv_S_brgB, S_t1, sd - 0.1, "rosca M20×1 (KM4)"))
    segs.append((S_t1, p.drv_S_front, sd, "asiento acople Ø20 h6"))
    return segs


def grooves(p):
    """Ranuras DIN 471: [(s0, s1, Ø fondo, etiqueta)]."""
    c = p.drv_circlip
    g = [(-p.drv_thrust_groove[1], -p.drv_thrust_groove[0], c["d2"], "DIN 471 empuje impulsor")]
    if p.drv_bush:
        g.append((-p.drv_aft_groove[1], -p.drv_aft_groove[0], c["d2"], "DIN 471 retención popa (opc.)"))
    g.append((p.drv_S_head_back - c["m"], p.drv_S_head_back, c["d2"], "DIN 471 respaldo cabeza sello"))
    return g


def build(p):
    sd = p.shaft_d
    part = stepped([(a, b, d) for a, b, d, _ in segments(p)])
    for s0, s1, d2, _ in grooves(p):
        part = part - (cyl_s(sd / 2 + 1, s0, s1) - cyl_s(d2 / 2, s0 - 0.1, s1 + 0.1))
    # agujero transversal del pasador de corte (eje Y)
    part = part - cyl_y(p.drv_pin_hole / 2, -sd, sd, x=p.drv_pin_X, z=0.0)
    # ranura de la MB4 en la rosca (+Z)
    km = p.drv_km
    S_t1 = p.drv_S_brgB + km["mb_t"] + km["b"] + 1.0
    part = part - box(-S_t1, -p.drv_S_brgB + 0.5, -km["mb_slot_w"] / 2, km["mb_slot_w"] / 2,
                      sd / 2 - km["mb_slot_t"], sd / 2 + 1)
    # chavetero del cubo del acople (+Z)
    k = p.drv_key
    s_k1 = p.drv_S_front - 0.5
    s_k0 = s_k1 - p.drv_cpl_key_l
    part = part - box(-s_k1, -s_k0, -k["b"] / 2, k["b"] / 2, sd / 2 - k["t1"], sd / 2 + 1)
    return part


def placements(p, steer=0.0, bucket=0):
    return [loc_jet(p)]


def checks(p, part):
    sd = p.shaft_d
    segs = segments(p)
    seal, brg, cpl = p.drv_seal, p.drv_bearing, p.drv_coupling
    # A-08 montabilidad
    aft_of_collar = [d for a, b, d, _ in segs if b <= p.drv_S_brgA - p.drv_collar_l + 1e-6]
    fwd_of_journal = [d for a, b, d, _ in segs if a >= p.drv_S_brgB - 1e-6]
    n_c, info = n_crit_rpm(p)
    n_max = p.sz["mech"]["n_max_rpm"]
    tooth_ok = p.drv_S_front - p.drv_S_cpl0
    return [
        ("un solo sólido", len(part.solids()), 1, "="),
        ("largo total del eje [mm]", p.drv_X_aft + p.drv_S_front, p.drv_shaft_L, "="),
        ("montaje: Ø máx. a popa del collar ≤ Ø agujero del asiento fijo − 1 (la caja del sello entra por popa) [mm]",
         max(aft_of_collar), seal["seat_id"] - 1.0, "<="),
        ("montaje: Ø máx. a popa del collar ≤ Ø interior de la cabeza del sello (entra por popa) [mm]",
         max(aft_of_collar), seal["d"], "<="),
        ("montaje: Ø máx. a popa del collar ≤ Ø del buje de la toma (seal_spigot_d − 2 × 3) [mm]",
         max(aft_of_collar), p.seal_spigot_d - 6.0, "<="),
        ("montaje: Ø máx. a proa del muñón ≤ Ø agujero 7204 (rodamientos entran por proa) [mm]",
         max(fwd_of_journal), brg["d"], "<="),
        ("collar ≥ da_min del 7204 (apoyo del aro interior) [mm]", p.drv_collar_d, brg["da_min"], ">="),
        ("collar ≤ Ø barra (se tornea) [mm]", p.drv_collar_d, p.drv_bar_d, "<="),
        ("laberinto collar ↔ resalte del soporte (holgura radial) [mm]", (p.drv_brg_shoulder_hole - p.drv_collar_d) / 2, 1.0, ">="),
        ("ranuras DIN 471 = las de BOMBA (centro de la delantera) [mm]", sum(p.drv_thrust_groove) / 2, p.raw.get("pmp_circlip_fwd_X", sum(p.drv_thrust_groove) / 2), "="),
        ("ranuras DIN 471 = las de BOMBA (centro de la de popa) [mm]", sum(p.drv_aft_groove) / 2, p.raw.get("pmp_circlip_aft_X", sum(p.drv_aft_groove) / 2), "="),
        ("collar libre de la caja del sello (S_collar0 − S_frente_caja) [mm]",
         p.drv_S_brgA - p.drv_collar_l - p.drv_S_hsg_front, 0.5, ">="),
        ("eje dentro del cubo del acople (encastre) [mm]", tooth_ok, 0.8 * cpl["l_hub_shaft"], ">="),
        ("punta del eje antes de la estrella del acople (luz) [mm]", p.drv_S_cpl_spider0 - p.drv_S_front, 0.5, ">="),
        ("agujero del pasador dentro del asiento del impulsor (margen a popa) [mm]",
         (p.X_imp1 - p.drv_pin_X) - p.drv_pin_hole / 2, 3.0, ">="),
        ("Ø agujero del pasador / Ø eje ≤ 0,25 (Kt del agujero transversal) [—]", p.drv_pin_hole / sd, 0.25, "<="),
        ("velocidad periférica en el sello ≤ v máx. del sello [m/s]",
         math.pi * sd / 1000 * n_max / 60, seal["v_max_ms"], "<="),
        (f"1.ª velocidad crítica / n máx. ≥ 1,3 ({info['model']}; n_crit {n_c:.0f} rpm) [—]",
         n_c / n_max, 1.3, ">="),
    ]

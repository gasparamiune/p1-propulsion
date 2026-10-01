#!/usr/bin/env python3
"""diagrama_cableado.py — Genera diagrama_cableado.svg (svgwrite) del sistema eléctrico de P1.

Valores de los rótulos: calc_electronica.compute() (que lee inputs.yaml y resultados/sizing.json).
Uso: python 04_diseno/electronica/diagrama_cableado.py [--out ruta.svg]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import svgwrite

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import calc_electronica as ce  # noqa: E402

W, H = 1900, 1240
FONT = "Helvetica, Arial, sans-serif"
C_POS, C_NEG, C_PH = "#c0392b", "#1f2d3d", "#8e44ad"
C_CTL, C_5V, C_SIG, C_MECH = "#d35400", "#1e8449", "#1f6fb2", "#7f8c8d"


def n(x, nd=1):
    return f"{x:.{nd}f}".replace(".", ",")


class Sch:
    def __init__(self, dwg):
        self.d = dwg

    def line(self, pts, color, w=2.0, dash=None):
        kw = dict(stroke=color, stroke_width=w, fill="none", stroke_linejoin="round", stroke_linecap="round")
        if dash:
            kw["stroke_dasharray"] = dash
        self.d.add(self.d.polyline(pts, **kw))

    def dot(self, x, y, color):
        self.d.add(self.d.circle((x, y), 4, fill=color))

    def text(self, x, y, s, size=12, anchor="start", weight="normal", color="#1b1b1b", italic=False):
        lines = s.split("\n")
        for i, ln in enumerate(lines):
            self.d.add(self.d.text(ln, insert=(x, y + i * (size + 3)), font_size=size, font_family=FONT,
                                   text_anchor=anchor, font_weight=weight, fill=color,
                                   font_style="italic" if italic else "normal"))

    def box(self, x, y, w, h, title, body="", fill="#ffffff", stroke="#1b1b1b", dash=None, tsize=13):
        kw = dict(fill=fill, stroke=stroke, stroke_width=1.6, rx=6, ry=6)
        if dash:
            kw["stroke_dasharray"] = dash
        self.d.add(self.d.rect((x, y), (w, h), **kw))
        self.text(x + 8, y + 18, title, size=tsize, weight="bold")
        if body:
            self.text(x + 8, y + 36, body, size=11)

    def region(self, x, y, w, h, label, color="#95a5a6", fill="none"):
        self.d.add(self.d.rect((x, y), (w, h), fill=fill, stroke=color, stroke_width=1.4,
                               stroke_dasharray="8,5", rx=10, ry=10))
        self.text(x + 10, y + h - 8, label, size=11, color="#5d6d7e", italic=True)

    def fuse(self, x, y, label, color, w=50):
        self.line([(x - 6, y), (x, y)], color, 3)
        self.d.add(self.d.rect((x, y - 8), (w, 16), fill="#fff", stroke=color, stroke_width=2))
        self.line([(x, y), (x + w, y)], color, 1.2)
        self.text(x + w / 2, y - 14, label, size=11, anchor="middle")

    def fuse_v(self, x, y, label, color, h=46):
        self.d.add(self.d.rect((x - 8, y), (16, h), fill="#fff", stroke=color, stroke_width=2))
        self.line([(x, y), (x, y + h)], color, 1.2)
        self.text(x + 14, y + h / 2 + 4, label, size=11)

    def res_h(self, x, y, label, color, w=50, below=False):
        self.d.add(self.d.rect((x, y - 7), (w, 14), fill="#fff", stroke=color, stroke_width=2))
        self.text(x + w / 2, y + (24 if below else -12), label, size=11, anchor="middle")

    def res_v(self, x, y, label, color, h=46):
        self.d.add(self.d.rect((x - 7, y), (14, h), fill="#fff", stroke=color, stroke_width=2))
        self.text(x + 12, y + h / 2 + 4, label, size=11)

    def sw_no(self, x, y, label, color, w=60):
        """Contacto normalmente abierto (dibujado abierto)."""
        self.dot(x, y, color)
        self.dot(x + w, y, color)
        self.line([(x, y), (x + w - 8, y - 18)], color, 2.5)
        self.text(x + w / 2, y + 22, label, size=11, anchor="middle")

    def sw_nc(self, x, y, label, color, w=60, note=""):
        """Contacto normalmente cerrado (dibujado cerrado, con barra de accionamiento)."""
        self.dot(x, y, color)
        self.dot(x + w, y, color)
        self.line([(x, y), (x + w, y + 0)], color, 2.5)
        self.line([(x + w / 2, y - 3), (x + w / 2, y - 20)], C_MECH, 1.5, dash="3,3")
        self.line([(x + w / 2 - 10, y - 20), (x + w / 2 + 10, y - 20)], C_MECH, 2)
        self.text(x + w / 2, y + 22, label, size=11, anchor="middle")
        if note:
            self.text(x + w / 2, y - 26, note, size=10, anchor="middle", color="#5d6d7e")

    def gnd(self, x, y, color=C_NEG, label="BAT−"):
        self.line([(x, y), (x, y + 10)], color, 2)
        for i, hw in enumerate((10, 6, 2)):
            self.line([(x - hw, y + 10 + 4 * i), (x + hw, y + 10 + 4 * i)], color, 2)
        if label:
            self.text(x + 12, y + 20, label, size=10, color=color)

    def conn(self, x, y, label, color):
        self.d.add(self.d.circle((x, y), 6, fill="#fff", stroke=color, stroke_width=2))
        self.text(x, y - 10, label, size=10, anchor="middle", color="#5d6d7e")

    def opto(self, x, y, name, color_in, color_out):  # noqa: C901
        """Optoacoplador: entrada (LED) arriba-abajo a la izquierda, salida (C,E) a la derecha."""
        self.d.add(self.d.rect((x, y), (80, 56), fill="#fff", stroke="#1b1b1b", stroke_width=1.5, rx=4, ry=4))
        tri = [(x + 12, y + 18), (x + 28, y + 18), (x + 20, y + 32)]
        self.d.add(self.d.polygon(tri, fill="none", stroke=color_in, stroke_width=1.6))
        self.line([(x + 12, y + 32), (x + 28, y + 32)], color_in, 1.6)
        self.line([(x + 20, y), (x + 20, y + 18)], color_in, 1.6)
        self.line([(x + 20, y + 32), (x + 20, y + 56)], color_in, 1.6)
        for k in (0, 8):
            self.line([(x + 34, y + 20 + k), (x + 46, y + 26 + k)], "#7f8c8d", 1.2)
        self.line([(x + 56, y + 14), (x + 56, y + 42)], color_out, 2)
        self.line([(x + 56, y + 22), (x + 80, y + 12)], color_out, 1.6)
        self.line([(x + 56, y + 34), (x + 80, y + 44)], color_out, 1.6)
        self.text(x - 6, y + 32, name, size=11, anchor="end", weight="bold")
        return (x + 80, y + 12), (x + 80, y + 44)  # colector, emisor


def build(out_path: Path) -> Path:
    R = ce.compute()
    m, p, b, o, cab, vv = R["meta"], R["precarga"], R["bobina"], R["optos"], R["cables"], R["vesc_values"]
    dwg = svgwrite.Drawing(str(out_path), size=(f"{W}px", f"{H}px"), viewBox=f"0 0 {W} {H}", profile="full")
    dwg.add(dwg.rect((0, 0), (W, H), fill="#ffffff"))
    s = Sch(dwg)
    cl = R["clase"]
    s.text(30, 40, "P1-J waterjet — Diagrama de cableado: potencia, cadena de emergencia y control", size=22, weight="bold")
    s.text(30, 64, f"{m['battery_desc']} → {m['cells_series']}S LiFePO4, {n(m['v_nom'])} V nominal / {n(m['v_max'])} V carga plena · "
                   f"ESC {m['esc']} · motor {m['motor_desc']} · SISTEMA FLOTANTE: BAT− no se conecta al casco de aluminio",
           size=12, color="#34495e")

    yp, yn, yc = 175, 470, 600
    # ------------------------------------------------------------ regiones
    s.region(35, 95, 330, 330, "Caja(s) de batería estanca(s), sobre la sentina (ISO 13297 8.1)")
    s.region(380, 95, 120, 330, "Consola")
    dwg.add(dwg.polygon([(560, 95), (1550, 95), (1550, 1135), (378, 1135), (378, 520), (560, 520)], fill="none",
                        stroke="#95a5a6", stroke_width=1.4, stroke_dasharray="8,5"))
    s.text(940, 1127, "Zona del controlador: ESC IP65 con caja de agua sobre base elevada P1-ELE-01 + capota P1-ELE-02; "
           "mando y MCU en caja estanca de consola", size=11, color="#5d6d7e", italic=True)
    s.region(770, 548, 210, 127, "Consola: cordón (fuera de la caja)", fill="#ffffff")
    s.region(612, 552, 122, 104, "Consola", fill="#ffffff")
    s.region(55, 975, 315, 160, "Consola: acelerador (hall encapsulado)")
    s.region(1575, 120, 300, 330, "Motor P1-MOT-01 (camisa de agua)")

    # ------------------------------------------------------------ baterías en serie
    s.box(60, 120, 150, 270, f"BAT {m['cells_series']}S LFP", f"{n(m['v_nom'])} V nom.\n{n(m['v_max'])} V cargada\n"
          f"BMS {int(R['vesc_values']['i_bms'])} A\n\n" + "\n".join(m['battery_desc'][i:i + 20] for i in range(0, min(len(m['battery_desc']), 100), 20)),
          fill="#fdf2f0")
    s.line([(210, 150), (210, yp)], C_POS, 4)
    s.text(218, 150, "+", size=16, weight="bold", color=C_POS)
    s.text(218, 380, "−", size=18, weight="bold", color=C_NEG)
    # positivo
    s.line([(210, yp), (264, yp)], C_POS, 4)
    s.fuse(270, yp, f"F1 {cab['fuse_a']:.0f} A", C_POS)
    s.text(295, yp + 26, "≤ 178 mm del borne +\n(7 in; ABYC E-11\nescribe 175 mm)", size=10, anchor="middle", color="#5d6d7e")
    s.line([(320, yp), (405, yp)], C_POS, 4)
    s.sw_no(405, yp, "S1 desconectador", C_POS)
    s.text(435, yp + 36, f"≥ {cab['fuse_a']:.0f} A, ≥ {m['v_max']:.0f} V CC", size=10, anchor="middle", color="#5d6d7e")
    s.line([(465, yp), (640, yp)], C_POS, 4)
    s.dot(520, yp, C_POS)
    s.text(526, yp - 8, "B+", size=11, weight="bold", color=C_POS)
    # K1 + R_pre en paralelo
    s.dot(610, yp, C_POS)
    s.line([(610, yp), (610, 128), (640, 128)], C_POS, 2)
    s.res_h(640, 128, f"R_pre {p['R_ohm']:.0f} Ω ≥ {p['P_rating_W']:.0f} W", C_POS, w=60)
    s.line([(700, 128), (740, 128), (740, yp)], C_POS, 2)
    s.sw_no(650, yp, f"K1 {cl['contactor']}", C_POS, w=70)
    s.text(685, yp + 36, f"contactos NA, ≥ {cab['fuse_a']:.0f} A, corte ≥ {m['v_max']:.0f} V CC", size=10, anchor="middle", color="#5d6d7e")
    s.dot(740, yp, C_POS)
    s.line([(720, yp), (790, yp)], C_POS, 4)
    s.line([(790, yp), (1180, yp)], C_POS, 4)
    s.text(985, yp - 10, f"{cab['dc_mm2']} mm² estañado, terminales M8", size=10, anchor="middle")
    if cl["imd"]:
        s.box(800, 250, 170, 80, "IMD (72 V)", cl["imd_desc"][:30] + "\nB+/B− ↔ casco; alarma\na consola", fill="#fef9e7")
        s.line([(830, yp), (830, 250)], C_POS, 1.5)
        s.line([(860, 330), (860, yn)], C_NEG, 1.5)
    # VESC
    s.box(1180, 120, 240, 300, f"ESC {m['esc']}", f"FW ≥ 5.03, app PPM (Current)\nl_current_max {n(vv['l_current_max'], 0)} A\n"
          f"l_current_min {n(vv['l_current_min'], 0)} A\nl_in_current_max {n(vv['l_in_current_max'], 0)} A\n"
          f"battery_cut {n(vv['l_battery_cut_start'])}/{n(vv['l_battery_cut_end'])} V\nl_max_erpm {vv['l_max_erpm']:.0f}\n"
          f"timeout PPM {vv['timeout_msec']:.0f} ms\nkill: ADC2_HIGH", fill="#eef5fb", tsize=14)
    s.text(1174, yp - 8, "B+", size=11, weight="bold", color=C_POS, anchor="end")
    s.text(1174, 414, "B−", size=11, weight="bold", color=C_NEG, anchor="end")
    # fases y motor
    for i, yy in enumerate((220, 250, 280)):
        s.line([(1420, yy), (1630, yy)], C_PH, 3.5)
        s.d.add(s.d.rect((1500, yy - 7), (18, 14), fill="#fff", stroke=C_PH, stroke_width=1.5))
        s.text(1424, yy - 4, "ABC"[i], size=10, color=C_PH)
    s.text(1430, 304, f"3 × {cab['phase_mm2']} mm² (tramo corto: ESC al costado del motor)", size=10)
    s.d.add(s.d.circle((1700, 250), 62, fill="#f5eef8", stroke=C_PH, stroke_width=2.5))
    s.text(1700, 245, "M", size=26, anchor="middle", weight="bold", color=C_PH)
    s.text(1700, 268, f"{m['motor']}\n{m['motor_kv']:.0f} KV", size=11, anchor="middle")
    s.line([(1420, 380), (1700, 380), (1700, 312)], C_SIG, 1.5, dash="5,4")
    s.text(1430, 374, "sensor de temperatura del bobinado → TEMP del VESC", size=10, color=C_SIG)
    s.text(1590, 345, "agua: bomba → ESC → motor\n→ testigo en el espejo", size=10, color="#5d6d7e")

    # ------------------------------------------------------------ negativo (flotante)
    s.line([(210, 380), (230, 380), (230, yn), (1180, yn), (1180, 420)], C_NEG, 4)
    s.text(600, yn - 8, f"BAT− {cab['dc_mm2']} mm² (sin conexión al casco)", size=11, color=C_NEG)
    s.text(250, yn + 40, "CASCO Al", size=12, weight="bold", color="#7f8c8d", anchor="end")
    s.line([(270, yn), (270, yn + 22)], "#7f8c8d", 1.5, dash="3,3")
    s.line([(260, yn + 8), (280, yn + 20)], C_POS, 2.5)
    s.line([(260, yn + 20), (280, yn + 8)], C_POS, 2.5)
    s.text(40, yn + 60, "NO conectar (ISO 13297 4.1).\nPrueba: BAT−↔casco y BAT−↔eje > 1 MΩ", size=10, color="#5d6d7e")

    # ------------------------------------------------------------ circuito de mando (24 V)
    s.line([(520, yp), (520, yc), (548, yc)], C_CTL, 2.2)
    s.fuse(554, yc, f"F2 {n(b['F2_A'], 0)} A", C_CTL, w=42)
    s.line([(596, yc), (640, yc)], C_CTL, 2.2)
    s.sw_nc(640, yc, "SETA E-stop (NC)", C_CTL, w=60, note="22 mm, IP65+")
    s.line([(700, yc), (800, yc)], C_CTL, 2.2)
    s.dot(740, yc, C_CTL)
    s.text(744, yc - 8, "N1", size=11, weight="bold", color=C_CTL)
    s.conn(800, yc, "J2", C_CTL)
    s.line([(806, yc), (840, yc)], C_CTL, 2.2)
    s.sw_nc(840, yc, "CORDÓN (NC con clip)", C_CTL, w=60, note="cerrado = clip puesto")
    s.line([(900, yc), (940, yc)], C_CTL, 2.2)
    s.conn(946, yc, "J2", C_CTL)
    s.line([(952, yc), (1060, yc)], C_CTL, 2.2)
    s.dot(1010, yc, C_CTL)
    s.text(1014, yc - 8, "N2", size=11, weight="bold", color=C_CTL)
    s.box(1060, yc - 22, 90, 44, "Bobina K1", f"{b['V_nom']:.0f} V", fill="#fef5e7", tsize=11)
    s.line([(1150, yc), (1180, yc)], C_CTL, 2.2)
    s.gnd(1180, yc)
    s.text(1062, yc + 40, "en paralelo: diodo + R (o TVS)\n(apertura 8–20 ms)", size=10, color="#5d6d7e")
    s.line([(1105, yc - 22), (1105, 536), (685, 536), (685, 224)], C_MECH, 1.2, dash="4,4")
    s.text(700, 530, "acción mecánica: bobina → contactos de K1", size=10, color=C_MECH)

    # optos
    s.line([(740, yc), (740, 690)], C_CTL, 1.8)
    s.res_v(740, 690, f"R1 {o['R_U1_ohm'] / 1000:.1f} k 0,5 W".replace(".", ","), C_CTL, h=40)
    s.line([(740, 730), (740, 740)], C_CTL, 1.8)
    cU1, eU1 = s.opto(720, 740, "U1 (seta)", C_CTL, C_SIG)
    s.gnd(740, 796, label="")
    s.line([(1010, yc), (1010, 690)], C_CTL, 1.8)
    s.res_v(1010, 690, f"R2 {o['R_U2U3_ohm'] / 1000:.1f} k 0,5 W".replace(".", ","), C_CTL, h=40)
    s.line([(1010, 730), (1010, 740)], C_CTL, 1.8)
    cU2, eU2 = s.opto(990, 740, "U2 (cordón)", C_CTL, C_SIG)
    s.line([(1010, 796), (1010, 820)], C_CTL, 1.8)
    cU3, eU3 = s.opto(990, 820, "U3 (kill HW)", C_CTL, C_SIG)
    s.gnd(1010, 876, label="")
    s.text(725, 688, f"1N4148 antiparalelo\nen cada LED U1–U3\n(N1/N2 → {n(R['bobina']['V_N2_negativo_V'])} V\nal abrir la bobina)",
           size=10, anchor="end", color=C_CTL)
    s.line([cU1, (840, cU1[1])], C_SIG, 1.6)
    s.text(844, cU1[1] + 4, "→ D3", size=11, color=C_SIG, weight="bold")
    s.line([eU1, (812, eU1[1]), (812, 800)], C_SIG, 1.6)
    s.gnd(812, 800, color=C_SIG, label="")
    s.line([cU2, (1110, cU2[1])], C_SIG, 1.6)
    s.text(1114, cU2[1] + 4, "→ D2", size=11, color=C_SIG, weight="bold")
    s.line([eU2, (1082, eU2[1]), (1082, 800)], C_SIG, 1.6)
    s.gnd(1082, 800, color=C_SIG, label="")

    # ADC2 del VESC: pull-up a 3,3 V; U3 en serie con Q_EN a GND
    s.text(1196, 438, "PPM", size=10, color=C_SIG)
    s.text(1252, 438, "ADC2", size=10, color=C_SIG)
    s.text(1300, 438, "3V3", size=10, color=C_SIG)
    s.text(1340, 438, "GND", size=10, color=C_SIG)
    s.text(1378, 438, "5V: NO conectar", size=10, color=C_POS)
    s.line([(1312, 420), (1312, 470)], C_SIG, 1.5)
    s.res_h(1270, 478, "10 k", C_SIG, w=36, below=True)
    s.line([(1306, 478), (1312, 478), (1312, 470)], C_SIG, 1.5)
    s.line([(1264, 420), (1264, 478), (1270, 478)], C_SIG, 1.5)
    s.line([(1264, 478), (1264, 832), cU3], C_SIG, 1.6)
    s.dot(1264, 478, C_SIG)
    s.line([(1352, 420), (1352, 452)], C_SIG, 1.5)
    s.gnd(1352, 452, color=C_SIG, label="")
    s.text(1276, 520, "pull-up 10 k a 3,3 V\nADC2 > 1,65 V = KILL", size=10, color=C_SIG)
    s.line([eU3, (1120, eU3[1]), (1120, 880)], C_SIG, 1.6)
    s.d.add(s.d.circle((1130, 900), 18, fill="#fff", stroke=C_SIG, stroke_width=1.6))
    s.text(1154, 896, "Q_EN NPN", size=11, weight="bold")
    s.text(1154, 910, "base ← D4 (1 k; 10 k a GND)", size=10, color=C_SIG)
    s.line([(1120, 918), (1120, 935)], C_SIG, 1.6)
    s.gnd(1120, 935, color=C_SIG, label="")
    s.text(1040, 975, "ADC2 a GND solo si U3 (cordón+seta con tensión) Y Q_EN (MCU armado)", size=10, color=C_SIG)

    # PPM
    s.line([(1205, 420), (1205, 1025), (900, 1025)], C_SIG, 1.8)
    s.dot(1205, 1025, C_SIG)
    s.line([(1205, 1040), (1205, 1025)], C_SIG, 1.2)
    s.res_v(1205, 1040, "10 k a GND (sin pulsos si el MCU está en reset)", C_SIG, h=30)
    s.gnd(1205, 1070, color=C_SIG, label="")

    # ------------------------------------------------------------ MCU, DC-DC, hall
    s.line([(520, 560), (470, 560), (470, 600)], C_CTL, 1.8)
    s.dot(520, 560, C_CTL)
    s.fuse_v(470, 600, "F3 1 A", C_CTL, h=46)
    s.line([(470, 646), (470, 905)], C_CTL, 1.8)
    s.box(405, 905, 160, 66, "DC-DC → 5 V", f"{cl['dcdc'][:26]}\n5 V (aguas arriba de K1)", fill="#eafaf1")
    s.gnd(450, 971, label="")
    s.box(660, 900, 240, 185, "Arduino Nano (ATmega328P)", "p1_throttle.ino + throttle_logic.c\nWDT 120 ms · tick 10 ms\n"
          "PPM por Timer1 (OC1A)", fill="#f4f6f7")
    for yy, lab in ((990, "5V"), (1020, "GND"), (1050, "A0")):
        s.text(666, yy + 4, lab, size=10, weight="bold")
    for yy, lab in ((975, "D5 ← bucket"), (990, "D2 ← U2"), (1005, "D3 ← U1"), (1025, "D9 → PPM"), (1045, "D4 → Q_EN"), (1065, "D6 → LED")):
        s.text(894, yy + 4, lab, size=10, weight="bold", anchor="end")
    s.line([(565, 935), (610, 935), (610, 990), (660, 990)], C_5V, 2)
    s.line([(660, 1020), (635, 1020), (635, 1024)], C_NEG, 1.6)
    s.gnd(635, 1024, label="")
    s.text(574, 928, "5 V", size=10, color=C_5V, weight="bold")
    s.line([(610, 990), (610, 1100), (426, 1100)], C_5V, 2)
    s.text(600, 1146, "D2/D3: INPUT_PULLUP + 10 k externo + 100 nF\nA0: 1 k + 100 nF (RC) y 100 k a GND", size=10, color=C_SIG)
    s.line([(426, 1050), (590, 1050), (660, 1050)], C_SIG, 1.8)
    s.dot(590, 1050, C_SIG)
    s.res_v(590, 1056, "100 k", C_SIG, h=26)
    s.line([(590, 1050), (590, 1056)], C_SIG, 1.4)
    s.gnd(590, 1082, color=C_SIG, label="")
    s.line([(426, 1075), (455, 1075)], C_NEG, 1.6)
    s.gnd(455, 1075, label="")
    for yy, lab in ((1050, "OUT"), (1075, "GND"), (1100, "5V")):
        s.conn(420, yy, "", C_SIG)
        s.text(410, yy - 5, lab, size=9, color="#5d6d7e", anchor="end")
    s.text(430, 1030, "J1 IP68 4 polos", size=10, color="#5d6d7e")
    s.box(90, 1005, 230, 100, "Sensor hall lineal", "ratiométrico 5 V (tipo SS49E/A1324)\nimán Ø10×3 en la palanca\n"
          "encapsulado en epoxi; cable redondo\npor prensaestopas M12", fill="#eaf2f8")
    s.text(910, 900, f"Fin de carrera del BUCKET (NC = arriba) → D5:\ncon el bucket abajo el MCU topea el PPM a\n"
           f"{n(vv['reverse_current_frac'], 2)} × l_current_max (P ≤ {n(vv['reverse_power_frac'] * 100, 0)} %)", size=10, color=C_SIG)
    s.line([(320, 1050), (414, 1050)], C_SIG, 1.8)
    s.line([(320, 1075), (414, 1075)], C_NEG, 1.6)
    s.line([(320, 1100), (414, 1100)], C_5V, 1.8)
    s.line([(900, 1065), (940, 1065)], C_SIG, 1.4)
    s.d.add(s.d.circle((950, 1065), 8, fill="#f9e79f", stroke="#7d6608", stroke_width=1.5))
    s.text(964, 1069, "LED de estado (panel)", size=10)

    # ------------------------------------------------------------ leyenda y reglas
    lx, ly = 1580, 520
    s.box(lx, ly, 300, 250, "Leyenda", fill="#fdfefe")
    items = [(C_POS, 4, "Potencia + (" + f"{cab['dc_mm2']} mm²)"), (C_NEG, 4, "Potencia − / BAT− flotante"),
             (C_PH, 3.5, f"Fases ({cab['phase_mm2']} mm²)"), (C_CTL, 2.2, f"Mando (bobina {b['V_nom']:.0f} V, optos)"),
             (C_5V, 2, "5 V lógica"), (C_SIG, 1.8, "Señales (PPM, ADC2, hall, D2/D3)"),
             (C_MECH, 1.2, "Acción mecánica")]
    for i, (c, w_, lab) in enumerate(items):
        yy = ly + 46 + 24 * i
        s.line([(lx + 14, yy), (lx + 64, yy)], c, w_, dash="4,4" if c == C_MECH else None)
        s.text(lx + 74, yy + 4, lab, size=11)
    s.text(lx + 14, ly + 228, "─ ─  región física (caja / caña / consola)", size=10, color="#5d6d7e")
    rx, ry = 1580, 790
    s.box(rx, ry, 300, 340, "Reglas de cableado", fill="#fdfefe")
    rules = ("1. El kill es HARDWARE: cordón + seta en serie\n   con la bobina de K1 (monoestable).\n"
             "2. Cable cortado, conector suelto o F2\n   fundido = bobina sin corriente = K1 abre.\n"
             "3. Redundancia: U3 (hardware) y Q_EN (MCU)\n   en serie mantienen ADC2 a GND; si no,\n   VESC en kill (≤ 10 ms de sondeo).\n"
             "4. Sin PPM → timeout del VESC → rueda libre.\n"
             "5. Encender S1 con el cordón AFUERA y\n   esperar ≥ " + f"{p['wait_s']:.0f} s (precarga por R_pre).\n"
             "6. BAT− NO va al casco: sistema flotante.\n"
             "7. Un cable redondo por prensaestopas;\n   grasa dieléctrica en J1/J2; PCB con\n   barniz conformal (no en conectores).\n"
             "8. 5 V del VESC: NO unir al 5 V del MCU.\n"
             f"9. ERPM: perfil legal {vv['l_max_erpm']:.0f} (5 kn) por defecto.")
    s.text(rx + 12, ry + 40, rules, size=11)
    s.text(30, H - 16, "Generado por 04_diseno/electronica/diagrama_cableado.py desde inputs.yaml + resultados/sizing.json "
                       "(vía calc_electronica.py). Valores con etiqueta en README.md.", size=10, color="#7f8c8d")
    dwg.save(pretty=True)
    return out_path


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE / "diagrama_cableado.svg"))
    a = ap.parse_args(argv)
    p = build(Path(a.out))
    print(f"diagrama_cableado: escrito {p} ({p.stat().st_size / 1024:.1f} kB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

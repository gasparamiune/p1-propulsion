"""Digitise Apple Rubber Seal Design Guide 'Critical Operating Environmental Factors' p. 3 Illustration 5.2 'Extrusion Limit' from the
PDF's vector paths (untrusted input; run with python3 -I, PDF path as the argument).  Mechanical, 2026-10-20.
Curve identity: each hardness curve is a filled band; its fill tint is matched to the legend swatch beside '70 / 80 / 90 Shore A'.
x axis: total diametrical clearance (in.), calibrated on the four vertical grid lines whose labels 0.008 / 0.016 / 0.024 / 0.032 sit
under them; the '0' label sits at the axis corner, 4.6 pt right of the grid-line origin (both calibrations reported below 0.008 in).
y axis: 'Fluid Pressure (psi)'; the 15 labels 100 ... 10,000 are equally spaced (13.0 pt) although their values are not
log-uniform, so the pressure is located between its two neighbouring labels (log and linear interpolation both reported)."""
import sys, json, math
import pdfplumber
import numpy as np

pdf_path = sys.argv[1]
with pdfplumber.open(pdf_path) as pdf:
    p = pdf.pages[2]
    words = p.extract_words()
    curves = p.curves
    rects = p.rects
    lines = p.lines

def bez(p0, p1, p2, p3, n=400):
    t = np.linspace(0.0, 1.0, n)[:, None]
    P = [np.array(q, float) for q in (p0, p1, p2, p3)]
    return ((1 - t) ** 3) * P[0] + 3 * ((1 - t) ** 2) * t * P[1] + 3 * (1 - t) * t * t * P[2] + (t ** 3) * P[3]

def polyline(c):
    out, cur = [], None
    for op in c["path"]:
        if op[0] == "m":
            cur = np.array(op[1], float); out.append(cur[None, :])
        elif op[0] == "l":
            nxt = np.array(op[1], float); out.append(np.vstack([cur, nxt])); cur = nxt
        elif op[0] == "c":
            seg = bez(cur, op[1], op[2], op[3]); out.append(seg); cur = np.array(op[3], float)
    return np.vstack(out)

# legend swatches -> tint -> label
legend = {}
for r in rects:
    if 215 < r["x0"] < 220 and r["x1"] < 232:
        yc = 0.5 * (r["top"] + r["bottom"])
        lab = [w["text"] for w in words if 233 < w["x0"] < 243 and abs(0.5 * (w["top"] + w["bottom"]) - yc) < 3.0]
        legend[str(r["non_stroking_color"])] = (lab[0] + " Shore A") if lab else "?"
bands = {}
for c in curves[:3]:
    bands[legend.get(str(c["non_stroking_color"]), "?")] = {"tint": c["non_stroking_color"], "pts": polyline(c)}
# axes
gx = sorted(l["x0"] for l in lines if abs(l["x0"] - l["x1"]) < 1e-6 and 120 < l["x0"] < 280 and l["bottom"] > 390)
xlab = {w["text"]: 0.5 * (w["x0"] + w["x1"]) for w in words if w["top"] > 399 and w["top"] < 403}
dx = float(np.mean(np.diff(gx)))
x0_grid = gx[0] - dx
x0_corner = 96.42
def x_to_in(x, corner=False):
    if corner and x < gx[0]:
        return 0.008 * (x - x0_corner) / (gx[0] - x0_corner)
    return 0.008 * (x - x0_grid) / dx
ylab = sorted(((float(w["text"].replace(",", "")), 0.5 * (w["top"] + w["bottom"])) for w in words
               if w["x1"] < 93.5 and w["x0"] > 70 and w["text"].replace(",", "").isdigit()), key=lambda a: a[0])
P = np.array([a for a, _ in ylab]); Y = np.array([b for _, b in ylab])
def psi_to_y(psi, mode="log"):
    i = int(np.searchsorted(P, psi)) - 1
    i = max(0, min(i, len(P) - 2))
    f = (math.log(psi / P[i]) / math.log(P[i + 1] / P[i])) if mode == "log" else (psi - P[i]) / (P[i + 1] - P[i])
    return Y[i] + f * (Y[i + 1] - Y[i])
def y_to_psi(y, mode="log"):
    # labels run 100 (bottom, large y) to 10000 (top); find the bracketing pair
    order = np.argsort(Y)
    Ys, Ps = Y[order], P[order]
    i = int(np.searchsorted(Ys, y)) - 1
    i = max(0, min(i, len(Ys) - 2))
    f = (y - Ys[i]) / (Ys[i + 1] - Ys[i])
    if mode == "log":
        return float(Ps[i] * (Ps[i + 1] / Ps[i]) ** f)
    return float(Ps[i] + f * (Ps[i + 1] - Ps[i]))
def band_x_at_y(pts, y):
    xs = []
    for a, b in zip(pts[:-1], pts[1:]):
        if (a[1] - y) * (b[1] - y) <= 0 and abs(b[1] - a[1]) > 1e-9:
            xs.append(a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]))
    return sorted(xs)
def band_y_at_x(pts, x):
    ys = []
    for a, b in zip(pts[:-1], pts[1:]):
        if (a[0] - x) * (b[0] - x) <= 0 and abs(b[0] - a[0]) > 1e-9:
            ys.append(a[1] + (x - a[0]) * (b[1] - a[1]) / (b[0] - a[0]))
    return sorted(ys)

res = {"x_grid_lines_pt": [round(v, 2) for v in gx], "x_labels_centre_pt": {k: round(v, 2) for k, v in xlab.items()},
       "pt_per_0.008in": round(dx, 3), "x_origin_grid_pt": round(x0_grid, 2), "x_axis_corner_pt": x0_corner,
       "y_labels": [[int(a), round(b, 2)] for a, b in ylab], "legend_tints": legend, "bands": {}}
for lab, b in bands.items():
    pts = b["pts"]
    rows = {}
    for psi in (1000.0, 1500.0, 2176.0):
        r = {}
        for mode in ("log", "linear"):
            y = psi_to_y(psi, mode)
            xs = band_x_at_y(pts, y)
            r[mode] = {"y_pt": round(y, 2), "band_x_pt": [round(v, 2) for v in xs],
                       "clearance_in": [round(x_to_in(v), 5) for v in xs], "clearance_mm": [round(25.4 * x_to_in(v), 3) for v in xs]}
        rows[f"{int(psi)}_psi"] = r
    # inverse: pressure at the TC-02 FA1S diametral gap 0.2772 mm
    inv = {}
    for g_mm in (0.2772, 0.156, 0.30):
        x = x0_grid + dx * (g_mm / 25.4) / 0.008
        ys = band_y_at_x(pts, x)
        xc = x0_corner + (gx[0] - x0_corner) * (g_mm / 25.4) / 0.008
        ysc = band_y_at_x(pts, xc) if (g_mm / 25.4) < 0.008 else ys
        inv[f"{g_mm}_mm"] = {"x_pt_grid": round(x, 2), "band_y_pt": [round(v, 2) for v in ys],
                             "psi_log": [round(y_to_psi(v, "log")) for v in ys], "psi_linear": [round(y_to_psi(v, "linear")) for v in ys],
                             "x_pt_corner_calib": round(xc, 2), "psi_log_corner_calib": [round(y_to_psi(v, "log")) for v in ysc]}
    res["bands"][lab] = {"tint": b["tint"], "readings": rows, "pressure_at_gap": inv,
                         "x_range_pt": [round(float(pts[:, 0].min()), 2), round(float(pts[:, 0].max()), 2)],
                         "y_range_pt": [round(float(pts[:, 1].min()), 2), round(float(pts[:, 1].max()), 2)]}
print(json.dumps(res, indent=1))

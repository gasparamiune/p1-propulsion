"""Dump words, lines and curves of one PDF page (untrusted input; run with python3 -I, path as argument)."""
import sys, json
import pdfplumber
pdf_path, pno = sys.argv[1], int(sys.argv[2])
with pdfplumber.open(pdf_path) as pdf:
    p = pdf.pages[pno - 1]
    print("page", pno, "size", p.width, p.height)
    ws = p.extract_words(keep_blank_chars=False, use_text_flow=False)
    for w in ws:
        print("W", round(w["x0"], 2), round(w["top"], 2), round(w["x1"], 2), round(w["bottom"], 2), repr(w["text"]))
    print("n_lines", len(p.lines), "n_curves", len(p.curves), "n_rects", len(p.rects))
    for i, c in enumerate(p.curves):
        pts = c.get("pts") or c.get("points")
        print("C", i, "n", len(pts), "stroke", c.get("stroking_color"), "lw", c.get("linewidth"), "x", round(c["x0"], 1), round(c["x1"], 1), "top", round(c["top"], 1), round(c["bottom"], 1))
    for i, l in enumerate(p.lines):
        print("L", i, round(l["x0"], 2), round(l["top"], 2), round(l["x1"], 2), round(l["bottom"], 2), "lw", l.get("linewidth"), l.get("stroking_color"))

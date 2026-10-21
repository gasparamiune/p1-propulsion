"""Print the point lists of the chart curves and rects on one PDF page (untrusted input; python3 -I, path as argument)."""
import sys
import pdfplumber
pdf_path, pno = sys.argv[1], int(sys.argv[2])
with pdfplumber.open(pdf_path) as pdf:
    p = pdf.pages[pno - 1]
    H = p.height
    for i, c in enumerate(p.curves[:4]):
        pts = c.get("pts")
        print("C", i, [(round(x, 2), round(y, 2)) for x, y in pts])
        if "path" in c:
            print("  path", [(op[0],) + tuple((round(a, 2), round(b, 2)) for a, b in op[1:]) for op in c["path"]])
    for r in p.rects:
        print("R", round(r["x0"], 2), round(r["top"], 2), round(r["x1"], 2), round(r["bottom"], 2), r.get("stroking_color"), r.get("non_stroking_color"), r.get("linewidth"))

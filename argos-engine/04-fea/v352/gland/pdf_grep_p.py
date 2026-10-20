"""Search the extracted text of every page of a PDF for terms (untrusted input; run with python3 -I, path as argument).
Usage: python3 -I pdf_grep_p.py <pdf> <term1> [<term2> ...]  -> prints page, line for each case-insensitive hit."""
import sys
import pdfplumber
pdf_path, terms = sys.argv[1], [t.lower() for t in sys.argv[2:]]
with pdfplumber.open(pdf_path) as pdf:
    print("pages", len(pdf.pages))
    for i, p in enumerate(pdf.pages, 1):
        txt = p.extract_text() or ""
        for ln in txt.splitlines():
            l = ln.lower()
            if any(t in l for t in terms):
                print(f"p{i}: {ln}")

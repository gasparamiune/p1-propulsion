"""Print the extracted text of one PDF page (untrusted input; run with python3 -I, path as argument)."""
import sys
import pdfplumber
pdf_path, pno = sys.argv[1], int(sys.argv[2])
with pdfplumber.open(pdf_path) as pdf:
    print(pdf.pages[pno - 1].extract_text(layout=False))

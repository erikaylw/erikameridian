#!/usr/bin/env python3
from weasyprint import HTML
import sys

html_path = '/home/ubuntu/meridian/sop-kontrol-divisi.html'
pdf_path = '/home/ubuntu/meridian/sop-kontrol-divisi.pdf'

print(f"Generating PDF from {html_path}...")
HTML(filename=html_path).write_pdf(pdf_path)
print(f"PDF generated: {pdf_path}")
print(f"Size: {__import__('os').path.getsize(pdf_path)} bytes")

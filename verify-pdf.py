#!/usr/bin/env python3
"""Verify PDF content: check Chinese chars and key terms."""
import subprocess

pdf_path = '/home/ubuntu/meridian/sop-kontrol-divisi.pdf'
result = subprocess.run(['pdftotext', pdf_path, '-'], capture_output=True, text=True)
text = result.stdout

print(f'Total chars: {len(text)}')
cn_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
print(f'Chinese characters: {cn_chars}')

keywords = ['組織', '行銷部', '審核部', '財務', '催收', 'KPI', 'Marketing', 'Penagihan', 'NPL']
for kw in keywords:
    count = text.count(kw)
    print(f'  "{kw}": found {count}x')

print()
print('First 300 chars:')
print(text[:300])

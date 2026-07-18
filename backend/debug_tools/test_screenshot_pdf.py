#!/usr/bin/env python3
import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.pdf_service import convert_pdf_to_html

async def test():
    pdf_path = Path(__file__).parent.parent / 'temp/test_pdfs/2049322459.pdf'
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    html = await convert_pdf_to_html(pdf_content, zoom_level=150.0)
    
    # Count tables
    table_count = html.count('<table')
    print(f'Tables in HTML: {table_count}')
    
    # Save for inspection
    output = Path(__file__).parent.parent / 'temp/screenshot_pdf_output.html'
    with open(output, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f'Saved to: {output}')
    print(f'HTML size: {len(html):,} bytes')
    
    # Extract table info
    import re
    tables = re.findall(r'<table[^>]*>(.*?)</table>', html, re.DOTALL)
    print(f'\nTable analysis:')
    for idx, table_html in enumerate(tables):
        rows = table_html.count('<tr')
        cols = table_html.count('<col ')
        print(f'  Table {idx + 1}: {rows} rows, {cols} columns')

asyncio.run(test())

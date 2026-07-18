#!/usr/bin/env python3
"""
Debug script to see exactly what column positions are being detected
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from services.pdf_service import convert_pdf_to_html
from bs4 import BeautifulSoup

# Monkey-patch the horizontal detector to print debug info
original_detect = None

def debug_detect_horizontal_table(h_lines, text_elements):
    """Wrapper to add debug output."""
    print("\n" + "="*80)
    print("HORIZONTAL DETECTOR DEBUG")
    print("="*80)
    
    # Print all horizontal lines
    print(f"\nReceived {len(h_lines)} horizontal lines:")
    
    # Group by Y
    y_groups = {}
    for line in h_lines:
        y = round(line.y0, 1)
        if y not in y_groups:
            y_groups[y] = []
        y_groups[y].append(line)
    
    for y in sorted(y_groups.keys())[:10]:
        lines = y_groups[y]
        print(f"\n  Y={y:.1f}px: {len(lines)} line(s)")
        for line in sorted(lines, key=lambda l: l.x0):
            print(f"    X: {line.x0:.1f} → {line.x1:.1f} (length: {line.x1-line.x0:.1f}px)")
    
    # Extract X positions
    all_x = set()
    for line in h_lines:
        all_x.add(line.x0)
        all_x.add(line.x1)
    
    x_positions = sorted(all_x)
    print(f"\nAll X positions from line endpoints ({len(x_positions)} unique):")
    for x in x_positions:
        print(f"  {x:.1f}")
    
    # Call original function
    result = original_detect(h_lines, text_elements)
    
    if result:
        print(f"\nDetected table with {len(result.col_positions)} columns:")
        for i, pos in enumerate(result.col_positions):
            print(f"  Position {i}: {pos:.1f}px")
        
        print(f"\nColumn widths:")
        total_width = result.col_positions[-1] - result.col_positions[0]
        for i in range(len(result.col_positions) - 1):
            width = result.col_positions[i+1] - result.col_positions[i]
            pct = (width / total_width) * 100
            print(f"  Column {i+1}: {width:.1f}px ({pct:.1f}%)")
    
    print("="*80 + "\n")
    
    return result

async def main():
    """Run with debug output."""
    global original_detect
    
    # Monkey-patch the detector
    from services.xml_parser.table_detector.horizontal_detector import detector
    original_detect = detector.detect_horizontal_table
    detector.detect_horizontal_table = debug_detect_horizontal_table
    
    # Process PDF
    pdf_path = Path("./temp/test_pdfs/second-page.pdf")
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    
    print("Processing PDF with debug output...\n")
    html = await convert_pdf_to_html(pdf_bytes, zoom_level=100.0)
    
    # Parse HTML to see final result
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')
    
    if table:
        print("\n" + "="*80)
        print("FINAL HTML OUTPUT")
        print("="*80)
        
        colgroup = table.find('colgroup')
        if colgroup:
            cols = colgroup.find_all('col')
            print(f"\nGenerated {len(cols)} columns in HTML:")
            for i, col in enumerate(cols, 1):
                style = col.get('style', '')
                if 'width:' in style:
                    width = style.split('width:')[1].split('%')[0].strip()
                    print(f"  Column {i}: {width}%")

if __name__ == "__main__":
    asyncio.run(main())

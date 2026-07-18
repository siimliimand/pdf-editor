"""
Row Height Diagnostic Script

This script helps identify the source of the ~2.37px systematic offset
in table row heights by examining:
1. Font sizes and line heights
2. Padding values
3. Border widths
4. Cell content heights
"""
import asyncio
from pathlib import Path
import sys
import re

sys.path.insert(0, '.')

from services.pdf_service import convert_pdf_to_html
from bs4 import BeautifulSoup


async def diagnose_row_heights():
    """Diagnose what's causing the row height offset"""
    
    # Load and process PDF
    pdf_path = Path('./temp/test_pdfs/second-page.pdf')
    if not pdf_path.exists():
        print(f"Error: PDF not found at {pdf_path}")
        return
    
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    print("Processing PDF...")
    html = await convert_pdf_to_html(pdf_content, zoom_level=100.0)
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find the main table
    table = None
    for t in soup.find_all('table'):
        style = t.get('style', '')
        if 'position: absolute' in style:
            table = t
            break
    
    if not table:
        print("Error: Could not find absolute positioned table")
        return
    
    print(f"\n{'='*120}")
    print(f"ROW HEIGHT DIAGNOSTIC")
    print(f"{'='*120}\n")
    
    rows = table.find_all('tr')
    
    for i, row in enumerate(rows[:5]):  # Analyze first 5 rows in detail
        print(f"\n{'─'*120}")
        print(f"ROW {i}")
        print(f"{'─'*120}")
        
        # Row height
        row_style = row.get('style', '')
        h_match = re.search(r'height:\s*([\d.]+)px', row_style)
        row_height = float(h_match.group(1)) if h_match else 0.0
        print(f"Row height: {row_height:.2f}px")
        
        # Analyze each cell
        cells = row.find_all('td')
        for j, cell in enumerate(cells[:3]):  # First 3 cells
            cell_style = cell.get('style', '')
            text = cell.get_text().strip()[:40]
            
            print(f"\n  Cell {j}: '{text}'")
            
            # Extract CSS properties
            props = {
                'padding-top': re.search(r'padding-top:\s*([\d.]+)px', cell_style),
                'padding-bottom': re.search(r'padding-bottom:\s*([\d.]+)px', cell_style),
                'border-top': re.search(r'border-top:\s*([^;]+)', cell_style),
                'border-bottom': re.search(r'border-bottom:\s*([^;]+)', cell_style),
            }
            
            for prop, match in props.items():
                if match:
                    print(f"    {prop}: {match.group(1)}")
            
            # Check spans inside cell
            spans = cell.find_all('span')
            for span in spans[:2]:  # First 2 spans
                span_style = span.get('style', '')
                span_text = span.get_text().strip()[:30]
                
                if span_text:
                    print(f"    Span: '{span_text}'")
                    
                    span_props = {
                        'font-size': re.search(r'font-size:\s*([\d.]+)px', span_style),
                        'line-height': re.search(r'line-height:\s*([\d.]+)', span_style),
                    }
                    
                    for prop, match in span_props.items():
                        if match:
                            print(f"      {prop}: {match.group(1)}")
    
    # Calculate what the row heights SHOULD be based on content
    print(f"\n{'='*120}")
    print(f"HEIGHT CALCULATION ANALYSIS")
    print(f"{'='*120}\n")
    
    print("Analyzing how row heights are calculated...\n")
    
    for i, row in enumerate(rows[:3]):
        row_style = row.get('style', '')
        h_match = re.search(r'height:\s*([\d.]+)px', row_style)
        actual_height = float(h_match.group(1)) if h_match else 0.0
        
        cells = row.find_all('td')
        if not cells:
            continue
        
        # Get first cell with content
        cell = cells[0]
        cell_style = cell.get('style', '')
        
        # Extract padding
        pt_match = re.search(r'padding-top:\s*([\d.]+)px', cell_style)
        pb_match = re.search(r'padding-bottom:\s*([\d.]+)px', cell_style)
        padding_top = float(pt_match.group(1)) if pt_match else 0.0
        padding_bottom = float(pb_match.group(1)) if pb_match else 0.0
        
        # Get font size and line height from span
        span = cell.find('span')
        if span:
            span_style = span.get('style', '')
            fs_match = re.search(r'font-size:\s*([\d.]+)px', span_style)
            lh_match = re.search(r'line-height:\s*([\d.]+)', span_style)
            
            font_size = float(fs_match.group(1)) if fs_match else 12.0
            line_height = float(lh_match.group(1)) if lh_match else 1.0
            
            content_height = font_size * line_height
            calculated_height = padding_top + content_height + padding_bottom
            
            print(f"Row {i}:")
            print(f"  Padding-top: {padding_top:.2f}px")
            print(f"  Font-size: {font_size:.2f}px")
            print(f"  Line-height: {line_height:.2f}")
            print(f"  Content height: {content_height:.2f}px")
            print(f"  Padding-bottom: {padding_bottom:.2f}px")
            print(f"  Calculated total: {calculated_height:.2f}px")
            print(f"  Actual row height: {actual_height:.2f}px")
            print(f"  Difference: {actual_height - calculated_height:+.2f}px")
            print()
    
    # Check if there's a scaling factor issue
    print(f"{'='*120}")
    print(f"POTENTIAL FIXES")
    print(f"{'='*120}\n")
    
    print("Based on the -2.37px average offset across 17 rows:")
    print(f"  Total offset: -2.37 × 17 = -40.29px")
    print(f"  Actual total offset: -18.29px")
    print()
    print("This suggests the issue is cumulative but not linear.")
    print()
    print("Possible solutions:")
    print("  1. Increase line-height slightly (from 0.9 to ~0.95)")
    print("  2. Add small padding-bottom to each row (~0.14px per row)")
    print("  3. Adjust font-size scaling factor")
    print("  4. Check if border widths are being subtracted from row heights")


if __name__ == "__main__":
    asyncio.run(diagnose_row_heights())

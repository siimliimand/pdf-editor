#!/usr/bin/env python3
"""
Analyze column positions detected by the XML parser
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from services.pdf_service import convert_pdf_to_html
from services.vector_parser import parse_vectors
from services.xml_parser.table_detector.coord_utils import cluster_coords
import fitz

async def analyze_column_detection(pdf_path):
    """Analyze how columns are being detected."""
    print("="*80)
    print("Column Detection Analysis")
    print("="*80)
    
    # Read PDF
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    
    # Parse with PyMuPDF to get vectors
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]
    
    # Get page dimensions
    page_rect = page.rect
    print(f"\nPage dimensions: {page_rect.width} x {page_rect.height}")
    
    # Parse vectors
    vectors = parse_vectors(page)
    
    # Filter horizontal lines
    h_lines = [v for v in vectors if v.type == 'line' and abs(v.y1 - v.y0) < 1]
    
    print(f"\nFound {len(h_lines)} horizontal lines")
    
    # Group by Y position
    y_groups = {}
    for line in h_lines:
        y = round(line.y0, 1)
        if y not in y_groups:
            y_groups[y] = []
        y_groups[y].append(line)
    
    print(f"\nHorizontal lines grouped by Y position:")
    for y in sorted(y_groups.keys())[:15]:  # First 15 rows
        lines = y_groups[y]
        print(f"\n  Y={y:.1f}px: {len(lines)} line(s)")
        for line in sorted(lines, key=lambda l: l.x0):
            print(f"    X: {line.x0:.1f} → {line.x1:.1f} (length: {line.x1-line.x0:.1f}px)")
    
    # Extract all X positions from line endpoints
    all_x = set()
    for line in h_lines:
        all_x.add(line.x0)
        all_x.add(line.x1)
    
    x_positions = sorted(all_x)
    print(f"\n{'='*80}")
    print(f"All X positions from line endpoints ({len(x_positions)} unique):")
    print(f"  {[round(x, 1) for x in x_positions]}")
    
    # Cluster them
    clustered_x = cluster_coords(list(all_x))
    print(f"\nClustered X positions ({len(clustered_x)} clusters):")
    print(f"  {[round(x, 1) for x in clustered_x]}")
    
    # Calculate widths
    if len(clustered_x) > 1:
        total_width = clustered_x[-1] - clustered_x[0]
        print(f"\nColumn widths from clustered positions:")
        print(f"  Total width: {total_width:.1f}px")
        
        for i in range(len(clustered_x) - 1):
            width = clustered_x[i+1] - clustered_x[i]
            pct = (width / total_width) * 100
            print(f"  Column {i+1}: {width:.1f}px ({pct:.1f}%)")
    
    # Now let's see what the actual table detector does
    print(f"\n{'='*80}")
    print("Running actual table detection...")
    print("="*80)
    
    html = await convert_pdf_to_html(pdf_bytes, zoom_level=100.0)
    
    # Parse the HTML to see what was generated
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')
    
    if table:
        # Get table position from style
        style = table.get('style', '')
        if 'left:' in style:
            left_str = style.split('left:')[1].split('px')[0].strip()
            table_left = float(left_str)
            print(f"\nTable left position: {table_left:.1f}px")
        
        if 'width:' in style:
            width_str = style.split('width:')[1].split('px')[0].strip()
            table_width = float(width_str)
            print(f"Table width: {table_width:.1f}px")
        
        colgroup = table.find('colgroup')
        if colgroup:
            cols = colgroup.find_all('col')
            print(f"\nGenerated {len(cols)} columns:")
            for i, col in enumerate(cols, 1):
                col_style = col.get('style', '')
                if 'width:' in col_style:
                    width_pct = col_style.split('width:')[1].split('%')[0].strip()
                    actual_px = float(width_pct) / 100 * table_width
                    print(f"  Column {i}: {width_pct}% ({actual_px:.1f}px)")
    
    doc.close()

if __name__ == "__main__":
    pdf_path = Path("./temp/test_pdfs/second-page.pdf")
    asyncio.run(analyze_column_detection(pdf_path))

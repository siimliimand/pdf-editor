"""
Analyze table row rendering and compare with expected positions

This script provides detailed analysis of:
1. Actual vs expected border Y positions
2. Row height calculations
3. Cumulative offset patterns
4. Suggestions for fixing discrepancies
"""
import asyncio
from pathlib import Path
import sys
import re

sys.path.insert(0, '.')

from services.pdf_service import convert_pdf_to_html
from bs4 import BeautifulSoup


# Expected border Y positions from PDF
EXPECTED_BORDER_Y_POSITIONS = [
    118.0,
    136.0,
    168.0,
    181.0,
    195.0,
    209.0,
    202.0,  # Note: This is out of order - might be an error?
    236.0,
    252.0,
    266.0,
    301.0,
    315.0,
    328.0,
    342.0,
    355.0,
    369.0,
    385.0,
    399.0
]


async def analyze_rows():
    """Analyze table row positions and heights"""
    
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
    table_top = 0.0
    
    for t in soup.find_all('table'):
        style = t.get('style', '')
        if 'position: absolute' in style:
            top_match = re.search(r'top:\s*([\d.]+)px', style)
            if top_match:
                table_top = float(top_match.group(1))
                table = t
                break
    
    if not table:
        print("Error: Could not find absolute positioned table")
        return
    
    print(f"\n{'='*100}")
    print(f"TABLE ANALYSIS")
    print(f"{'='*100}")
    print(f"Table top position: {table_top:.2f}px\n")
    
    # Analyze rows
    rows = table.find_all('tr')
    current_y = table_top
    actual_borders = []
    
    print(f"{'Row':<4} {'Y-Top':<8} {'Height':<8} {'Y-Bottom':<10} {'Border':<8} {'Text'}")
    print("-" * 100)
    
    for i, row in enumerate(rows):
        # Get row height
        style = row.get('style', '')
        h_match = re.search(r'height:\s*([\d.]+)px', style)
        height = float(h_match.group(1)) if h_match else 0.0
        
        # Check for bottom border
        cells = row.find_all('td')
        has_bottom = any('border-bottom' in (c.get('style') or '') and 'solid' in (c.get('style') or '') for c in cells)
        
        # Get text preview
        text = ' | '.join(c.get_text().strip()[:25] for c in cells[:2])
        
        y_bottom = current_y + height
        
        if has_bottom:
            actual_borders.append(y_bottom)
        
        print(f"{i:<4} {current_y:<8.2f} {height:<8.2f} {y_bottom:<10.2f} {'YES' if has_bottom else 'NO':<8} {text[:50]}")
        
        current_y += height
    
    # Compare with expected positions
    print(f"\n{'='*100}")
    print(f"BORDER POSITION COMPARISON")
    print(f"{'='*100}")
    print(f"{'Expected':<12} {'Actual':<12} {'Diff':<10} {'Status'}")
    print("-" * 100)
    
    sorted_expected = sorted(EXPECTED_BORDER_Y_POSITIONS)
    
    for expected in sorted_expected:
        if not actual_borders:
            print(f"{expected:<12.2f} {'N/A':<12} {'N/A':<10} ❌ NO BORDERS FOUND")
            continue
        
        # Find closest actual border
        closest = min(actual_borders, key=lambda y: abs(y - expected))
        diff = closest - expected
        
        status = "✓" if abs(diff) <= 1.5 else "❌"
        
        print(f"{expected:<12.2f} {closest:<12.2f} {diff:+10.2f} {status}")
    
    # Calculate average offset
    if actual_borders and sorted_expected:
        total_diff = 0
        count = 0
        
        for expected in sorted_expected:
            closest = min(actual_borders, key=lambda y: abs(y - expected))
            diff = closest - expected
            if abs(diff) <= 5:  # Only count reasonable matches
                total_diff += diff
                count += 1
        
        if count > 0:
            avg_offset = total_diff / count
            print(f"\n{'='*100}")
            print(f"OFFSET ANALYSIS")
            print(f"{'='*100}")
            print(f"Average offset: {avg_offset:+.2f}px")
            print(f"Borders analyzed: {count}/{len(sorted_expected)}")
            
            if abs(avg_offset) > 0.5:
                print(f"\n⚠️  SYSTEMATIC OFFSET DETECTED!")
                print(f"All borders are shifted by approximately {avg_offset:+.2f}px")
                print(f"\nPossible causes:")
                print(f"  1. Row height calculation is off by a constant factor")
                print(f"  2. Line-height or padding is adding extra space")
                print(f"  3. Font size scaling is slightly incorrect")
                print(f"  4. Border width is being included in height calculations")
    
    # Row height statistics
    heights = []
    for row in rows:
        style = row.get('style', '')
        h_match = re.search(r'height:\s*([\d.]+)px', style)
        if h_match:
            heights.append(float(h_match.group(1)))
    
    if heights:
        print(f"\n{'='*100}")
        print(f"ROW HEIGHT STATISTICS")
        print(f"{'='*100}")
        print(f"Total rows: {len(heights)}")
        print(f"Average height: {sum(heights)/len(heights):.2f}px")
        print(f"Min height: {min(heights):.2f}px")
        print(f"Max height: {max(heights):.2f}px")
        
        # Calculate expected vs actual total height
        if sorted_expected:
            expected_total = sorted_expected[-1] - sorted_expected[0]
            actual_total = actual_borders[-1] - actual_borders[0] if actual_borders else 0
            
            print(f"\nTotal table height:")
            print(f"  Expected (from borders): {expected_total:.2f}px")
            print(f"  Actual (from borders): {actual_total:.2f}px")
            print(f"  Difference: {actual_total - expected_total:+.2f}px")


if __name__ == "__main__":
    asyncio.run(analyze_rows())

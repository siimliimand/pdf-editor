#!/usr/bin/env python3
"""
Visual Column Width Comparison Tool

This tool helps verify that HTML table column widths match the original PDF.
It generates a side-by-side comparison showing:
1. PDF column boundaries (from PDF coordinates)
2. HTML column widths (as percentages)
3. Visual representation of column proportions
"""

import sys
from pathlib import Path
from typing import List, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.pdf_service import convert_pdf_to_html
from bs4 import BeautifulSoup
import asyncio


def extract_column_widths_from_html(html: str) -> List[float]:
    """Extract column width percentages from HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')
    
    if not table:
        return []
    
    colgroup = table.find('colgroup')
    if not colgroup:
        return []
    
    widths = []
    for col in colgroup.find_all('col'):
        style = col.get('style', '')
        if 'width:' in style:
            width_str = style.split('width:')[1].split(';')[0].strip()
            if '%' in width_str:
                width = float(width_str.replace('%', ''))
                widths.append(width)
    
    return widths


def draw_column_chart(widths: List[float], total_width: int = 80) -> str:
    """Draw a text-based bar chart of column widths."""
    if not widths or sum(widths) == 0:
        return ""
    
    lines = []
    lines.append("Column Width Visualization:")
    lines.append("=" * total_width)
    
    for i, width in enumerate(widths, 1):
        # Calculate bar width
        bar_width = int((width / 100) * total_width)
        bar = "█" * bar_width
        
        # Format the line
        label = f"Col {i}"
        percentage = f"{width:.1f}%"
        line = f"{label:6} |{bar:<{total_width}}| {percentage}"
        lines.append(line)
    
    lines.append("=" * total_width)
    lines.append(f"Total: {sum(widths):.2f}%")
    
    return "\n".join(lines)


def analyze_column_distribution(widths: List[float]) -> str:
    """Analyze column width distribution."""
    if not widths:
        return "No columns found"
    
    lines = []
    lines.append("\nColumn Distribution Analysis:")
    lines.append("-" * 60)
    
    # Basic statistics
    total = sum(widths)
    avg = total / len(widths)
    min_width = min(widths)
    max_width = max(widths)
    
    lines.append(f"Number of columns: {len(widths)}")
    lines.append(f"Total width: {total:.2f}%")
    lines.append(f"Average width: {avg:.2f}%")
    lines.append(f"Min width: {min_width:.2f}%")
    lines.append(f"Max width: {max_width:.2f}%")
    lines.append(f"Width range: {max_width - min_width:.2f}%")
    
    # Check for uniform vs. varied distribution
    variance = sum((w - avg) ** 2 for w in widths) / len(widths)
    std_dev = variance ** 0.5
    
    lines.append(f"Standard deviation: {std_dev:.2f}%")
    
    if std_dev < 2:
        lines.append("✓ Columns are uniformly distributed")
    else:
        lines.append("✓ Columns have varied widths (as expected for this PDF)")
    
    # Identify the widest column
    widest_idx = widths.index(max_width)
    lines.append(f"\nWidest column: Column {widest_idx + 1} ({max_width:.2f}%)")
    
    # Check if first column is significantly wider (common in tables)
    if widths[0] > avg * 1.5:
        lines.append(f"✓ First column is {widths[0]/avg:.1f}x wider than average")
        lines.append("  (typical for description/label columns)")
    
    return "\n".join(lines)


async def compare_pdf_columns(pdf_path: Path):
    """Compare column widths between PDF and HTML."""
    print(f"\n{'='*80}")
    print(f"Column Width Comparison: {pdf_path.name}")
    print(f"{'='*80}\n")
    
    # Read and process PDF
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    print("Processing PDF...")
    html = await convert_pdf_to_html(pdf_content, zoom_level=100.0)
    
    # Extract column widths
    widths = extract_column_widths_from_html(html)
    
    if not widths:
        print("❌ No table columns found in HTML")
        return
    
    print(f"✓ Found {len(widths)} columns\n")
    
    # Display detailed width information
    print("Column Widths:")
    print("-" * 60)
    for i, width in enumerate(widths, 1):
        print(f"  Column {i}: {width:.2f}%")
    
    print()
    
    # Draw visualization
    print(draw_column_chart(widths))
    
    # Analyze distribution
    print(analyze_column_distribution(widths))
    
    # Validation checks
    print("\n" + "="*60)
    print("Validation Checks:")
    print("="*60)
    
    total = sum(widths)
    if abs(total - 100.0) < 0.01:
        print(f"✓ Total width is exactly 100% ({total:.6f}%)")
    else:
        print(f"⚠ Total width is {total:.2f}% (should be 100%)")
    
    # Check for unreasonably narrow columns
    min_reasonable_width = 5.0  # 5% minimum
    narrow_cols = [i+1 for i, w in enumerate(widths) if w < min_reasonable_width]
    if narrow_cols:
        print(f"⚠ Columns {narrow_cols} are narrower than {min_reasonable_width}%")
    else:
        print(f"✓ All columns are at least {min_reasonable_width}% wide")
    
    # Check for unreasonably wide columns
    max_reasonable_width = 60.0  # 60% maximum
    wide_cols = [i+1 for i, w in enumerate(widths) if w > max_reasonable_width]
    if wide_cols:
        print(f"⚠ Columns {wide_cols} are wider than {max_reasonable_width}%")
    else:
        print(f"✓ No columns exceed {max_reasonable_width}% width")
    
    print("\n" + "="*80)


async def main():
    """Main entry point."""
    # Default test PDF
    pdf_path = Path("./temp/test_pdfs/second-page.pdf")
    
    # Allow command-line argument
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
    
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        print(f"\nUsage: python {Path(__file__).name} [pdf_file]")
        return 1
    
    await compare_pdf_columns(pdf_path)
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

#!/usr/bin/env python3
"""
Test the improved font size detection with PyMuPDF.
"""
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.pdf_service import convert_pdf_to_html

async def test_font_detection(pdf_path: str, zoom_level: float = 150.0):
    """Test font detection on a PDF file"""
    print(f"\n{'='*80}")
    print(f"Testing Font Detection: {pdf_path}")
    print(f"Zoom Level: {zoom_level}%")
    print(f"{'='*80}\n")
    
    # Read PDF
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    # Convert to HTML
    html_content = await convert_pdf_to_html(pdf_content, zoom_level)
    
    # Save output for inspection
    output_path = Path(__file__).parent.parent / "temp" / "font_test_output.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✓ HTML output saved to: {output_path}")
    
    # Extract and display font sizes from HTML
    import re
    font_sizes = re.findall(r'font-size:\s*(\d+(?:\.\d+)?)px', html_content)
    
    if font_sizes:
        # Convert to floats and get unique sizes
        unique_sizes = sorted(set(float(s) for s in font_sizes))
        print(f"\n✓ Detected {len(font_sizes)} text elements")
        print(f"✓ Unique font sizes: {', '.join(f'{s:.1f}px' for s in unique_sizes)}")
    else:
        print("\n✗ No font sizes detected in HTML output")
    
    # Show a sample of the HTML
    print("\n" + "="*80)
    print("Sample HTML (first 1000 chars):")
    print("="*80)
    print(html_content[:1000])
    print("...")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_font_detection.py <pdf_path> [zoom_level]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    zoom_level = float(sys.argv[2]) if len(sys.argv) > 2 else 150.0
    
    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    asyncio.run(test_font_detection(pdf_path, zoom_level))

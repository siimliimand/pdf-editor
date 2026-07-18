"""
Test actual HTML output to verify font sizes in the converted HTML.
"""
import sys
import asyncio
from pathlib import Path
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.pdf_service import convert_pdf_to_html


async def test_html_output(pdf_path: str, zoom: float = 150.0):
    """Test the actual HTML output from the conversion"""
    
    print(f"\n{'='*100}")
    print(f"HTML OUTPUT FONT SIZE TEST")
    print(f"PDF: {Path(pdf_path).name}")
    print(f"Zoom: {zoom}%")
    print(f"{'='*100}\n")
    
    # Read PDF
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    # Convert to HTML
    html_content = await convert_pdf_to_html(pdf_content, zoom)
    
    # Extract font sizes from HTML
    font_size_pattern = r'font-size:\s*(\d+(?:\.\d+)?)px'
    font_sizes = re.findall(font_size_pattern, html_content)
    
    # Extract font families
    font_family_pattern = r'font-family:\s*([^;]+);'
    font_families = re.findall(font_family_pattern, html_content)
    
    # Extract specific text with their styles
    target_texts = [
        "SeoWeb OÜ",
        "Reg nr: 12629973",
        "Staadioni 8, 70",
        "79101 Järvakandi, Raplamaa"
    ]
    
    print("🔍 Searching for target text elements in HTML...\n")
    
    for target in target_texts:
        # Find the span containing this text
        pattern = rf'\u003cspan style="([^"]+)"\u003e[^\u003c]*{re.escape(target)}[^\u003c]*\u003c/span\u003e'
        matches = re.findall(pattern, html_content)
        
        if matches:
            style = matches[0]
            
            # Extract font-size
            size_match = re.search(r'font-size:\s*(\d+(?:\.\d+)?)px', style)
            font_size = size_match.group(1) if size_match else "N/A"
            
            # Extract font-family
            family_match = re.search(r'font-family:\s*([^;]+)', style)
            font_family = family_match.group(1) if family_match else "N/A"
            
            # Extract font-weight
            weight_match = re.search(r'font-weight:\s*(\d+)', style)
            font_weight = weight_match.group(1) if weight_match else "N/A"
            
            print(f"📝 '{target}':")
            print(f"   Font Family: {font_family}")
            print(f"   Font Size:   {font_size} px")
            print(f"   Font Weight: {font_weight}")
            print()
        else:
            print(f"❌ '{target}' not found in HTML")
            print()
    
    # Statistics
    if font_sizes:
        unique_sizes = sorted(set(float(s) for s in font_sizes))
        print(f"\n📊 Font Size Statistics:")
        print(f"   Total elements: {len(font_sizes)}")
        print(f"   Unique sizes: {len(unique_sizes)}")
        print(f"   Size range: {min(unique_sizes):.1f}px - {max(unique_sizes):.1f}px")
        print(f"   All sizes: {', '.join(f'{s:.1f}' for s in unique_sizes)}")
    
    if font_families:
        unique_families = set(font_families)
        print(f"\n🔤 Font Family Statistics:")
        print(f"   Total elements: {len(font_families)}")
        print(f"   Unique families: {len(unique_families)}")
        for family in sorted(unique_families):
            count = font_families.count(family)
            print(f"   - {family}: {count} occurrences")
    
    # Expected values (from PyMuPDF analysis)
    print(f"\n{'='*100}")
    print(f"COMPARISON WITH EXPECTED VALUES")
    print(f"{'='*100}\n")
    
    expected_values = {
        "SeoWeb OÜ": {
            "size_pt": 20.20,
            "expected_px": 20.20 * 1.333 * (zoom / 100),
            "family": "Arial"
        },
        "Reg nr: 12629973": {
            "size_pt": 12.80,
            "expected_px": 12.80 * 1.333 * (zoom / 100),
            "family": "Arial"
        },
        "Staadioni 8, 70": {
            "size_pt": 12.80,
            "expected_px": 12.80 * 1.333 * (zoom / 100),
            "family": "Arial"
        },
        "79101 Järvakandi, Raplamaa": {
            "size_pt": 12.80,
            "expected_px": 12.80 * 1.333 * (zoom / 100),
            "family": "Arial"
        }
    }
    
    print(f"{'Text':<35} {'Expected':<15} {'Actual':<15} {'Diff':<15} {'Status'}")
    print("-" * 100)
    
    for target in target_texts:
        pattern = rf'\u003cspan style="([^"]+)"\u003e[^\u003c]*{re.escape(target)}[^\u003c]*\u003c/span\u003e'
        matches = re.findall(pattern, html_content)
        
        if matches and target in expected_values:
            style = matches[0]
            size_match = re.search(r'font-size:\s*(\d+(?:\.\d+)?)px', style)
            
            if size_match:
                actual_px = float(size_match.group(1))
                expected_px = expected_values[target]["expected_px"]
                diff = actual_px - expected_px
                diff_pct = (diff / expected_px * 100) if expected_px > 0 else 0
                
                status = "✅" if abs(diff) < 1.0 else "❌"
                
                print(f"{target:<35} {expected_px:<15.2f} {actual_px:<15.2f} {diff:+.2f} ({diff_pct:+.1f}%)  {status}")
    
    # Save HTML for inspection
    output_path = Path(__file__).parent.parent / "temp" / "test_font_output.html"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n💾 HTML saved to: {output_path}")
    
    # Conclusion
    print(f"\n{'='*100}")
    print(f"CONCLUSION")
    print(f"{'='*100}\n")
    
    # Check if sizes are correct
    all_correct = True
    for target in target_texts:
        pattern = rf'\u003cspan style="([^"]+)"\u003e[^\u003c]*{re.escape(target)}[^\u003c]*\u003c/span\u003e'
        matches = re.findall(pattern, html_content)
        
        if matches and target in expected_values:
            style = matches[0]
            size_match = re.search(r'font-size:\s*(\d+(?:\.\d+)?)px', style)
            
            if size_match:
                actual_px = float(size_match.group(1))
                expected_px = expected_values[target]["expected_px"]
                if abs(actual_px - expected_px) >= 1.0:
                    all_correct = False
                    break
    
    if all_correct:
        print("✅ Font sizes are CORRECT!")
        print("   PyMuPDF font sizes are being used properly.")
        print("   DPI conversion is working as expected.")
    else:
        print("❌ Font sizes are INCORRECT!")
        print("   Possible issues:")
        print("   1. PyMuPDF fonts not being used (falling back to pdftohtml)")
        print("   2. Missing DPI conversion (1.333 multiplier)")
        print("   3. Incorrect zoom factor application")
        print("\n   Recommended fix:")
        print("   - Check text_parser.py line 63")
        print("   - Ensure: font_size = font_info.font_size * 1.333 * zoom_factor")


if __name__ == "__main__":
    pdf_path = "temp/test_pdfs/1010054315.pdf"
    
    if Path(pdf_path).exists():
        asyncio.run(test_html_output(pdf_path, zoom=150.0))
    else:
        print(f"❌ PDF not found: {pdf_path}")

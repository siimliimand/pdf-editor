"""
Debug script to check if PyMuPDF fonts are being used in text_parser.py
"""
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.pdf_service import convert_pdf_to_html
from services.font_extractor import FontExtractorPyMuPDF


async def debug_font_matching(pdf_path: str, zoom: float = 150.0):
    """Debug font matching between PyMuPDF and pdftohtml"""
    
    print(f"\n{'='*100}")
    print(f"FONT MATCHING DEBUG")
    print(f"PDF: {Path(pdf_path).name}")
    print(f"Zoom: {zoom}%")
    print(f"{'='*100}\n")
    
    # Extract fonts with PyMuPDF
    extractor = FontExtractorPyMuPDF(pdf_path)
    extractor.extract()
    
    target_texts = [
        "SeoWeb OÜ",
        "Reg nr: 12629973",
        "Staadioni 8, 70",
        "79101 Järvakandi, Raplamaa"
    ]
    
    print("🔍 Testing PyMuPDF font matching...\n")
    
    # Test if fonts can be found
    zoom_factor = zoom / 100
    
    for target in target_texts:
        # Try to find the font
        # We need to simulate what text_parser.py does
        # It divides by zoom_factor to convert back to unscaled coordinates
        
        # First, let's see what fonts we have for this text
        found_fonts = []
        if 1 in extractor.pages:
            for font_info in extractor.pages[1]:
                if target in font_info.text:
                    found_fonts.append(font_info)
        
        if found_fonts:
            print(f"✅ '{target}':")
            for font_info in found_fonts:
                print(f"   PyMuPDF Font:")
                print(f"     - Family: {font_info.font_family}")
                print(f"     - Size: {font_info.font_size:.2f} pt")
                print(f"     - Position: ({font_info.bbox[0]:.2f}, {font_info.bbox[1]:.2f})")
                print(f"     - Scaled size (with zoom): {font_info.font_size * zoom_factor:.2f} px")
                print(f"     - With DPI (1.333): {font_info.font_size * 1.333 * zoom_factor:.2f} px")
                print()
        else:
            print(f"❌ '{target}': No PyMuPDF font found")
            print()
    
    # Now let's check what pdftohtml gives us
    import subprocess
    import xml.etree.ElementTree as ET
    
    cmd = [
        "pdftohtml",
        "-xml",
        "-stdout",
        "-hidden",
        "-zoom", str(zoom_factor),
        pdf_path
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    xml_content = result.stdout.decode('utf-8')
    root = ET.fromstring(xml_content)
    
    print("\n📄 pdftohtml coordinates (for matching):\n")
    
    for page in root.findall('page'):
        for text_node in page.findall('text'):
            text = "".join(text_node.itertext()).strip()
            
            for target in target_texts:
                if target in text:
                    top = float(text_node.get('top', 0))
                    left = float(text_node.get('left', 0))
                    height = float(text_node.get('height', 0))
                    
                    print(f"'{target}':")
                    print(f"   pdftohtml coords (scaled):")
                    print(f"     - Top: {top:.2f}, Left: {left:.2f}")
                    print(f"     - Height: {height:.2f}")
                    print(f"   Unscaled coords (for PyMuPDF matching):")
                    print(f"     - Top: {top / zoom_factor:.2f}, Left: {left / zoom_factor:.2f}")
                    print()
                    
                    # Try to match
                    font_info = extractor.find_font_for_text(
                        page_num=1,
                        text=target,
                        top=top / zoom_factor,
                        left=left / zoom_factor,
                        tolerance=10.0
                    )
                    
                    if font_info:
                        print(f"   ✅ PyMuPDF match found!")
                        print(f"     - Font: {font_info.font_family}")
                        print(f"     - Size: {font_info.font_size:.2f} pt")
                        print(f"     - Scaled: {font_info.font_size * zoom_factor:.2f} px")
                        print(f"     - With DPI: {font_info.font_size * 1.333 * zoom_factor:.2f} px")
                    else:
                        print(f"   ❌ No PyMuPDF match found (will use pdftohtml fallback)")
                    print()
    
    # Analysis
    print(f"\n{'='*100}")
    print(f"ANALYSIS")
    print(f"{'='*100}\n")
    
    print("The issue is likely one of the following:\n")
    print("1. ❌ PyMuPDF fonts ARE being matched, but DPI conversion is missing")
    print("   - Current: font_size = font_info.font_size * zoom_factor")
    print("   - Should be: font_size = font_info.font_size * 1.333 * zoom_factor")
    print()
    print("2. ❌ PyMuPDF fonts are NOT being matched (tolerance too small)")
    print("   - Increase tolerance in text_parser.py line 56")
    print()
    print("3. ❌ Font extractor is not being passed to the parser")
    print("   - Check pdf_service.py to ensure font_extractor is passed")
    print()


if __name__ == "__main__":
    pdf_path = "temp/test_pdfs/1010054315.pdf"
    
    if Path(pdf_path).exists():
        asyncio.run(debug_font_matching(pdf_path, zoom=150.0))
    else:
        print(f"❌ PDF not found: {pdf_path}")

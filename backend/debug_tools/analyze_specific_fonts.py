"""
Analyze specific text elements to identify font family and font size issues.
This script focuses on the text visible in the comparison image.
"""
import sys
import fitz  # PyMuPDF
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.font_extractor import FontExtractorPyMuPDF


def analyze_specific_text(pdf_path: str, zoom: float = 1.5):
    """Analyze specific text elements from the PDF"""
    
    # Target texts from the image
    target_texts = [
        "SeoWeb OÜ",
        "Reg nr: 12629973",
        "Staadioni 8, 70",
        "79101 Järvakandi, Raplamaa"
    ]
    
    print(f"\n{'='*100}")
    print(f"DETAILED FONT ANALYSIS FOR SPECIFIC TEXT ELEMENTS")
    print(f"PDF: {Path(pdf_path).name}")
    print(f"Zoom: {zoom}")
    print(f"{'='*100}\n")
    
    # Get PyMuPDF data
    print("1️⃣  PyMuPDF Analysis:")
    print("-" * 100)
    
    extractor = FontExtractorPyMuPDF(pdf_path)
    extractor.extract()
    
    pymupdf_data = {}
    if 1 in extractor.pages:
        for font_info in extractor.pages[1]:
            for target in target_texts:
                if target in font_info.text:
                    pymupdf_data[target] = font_info
                    print(f"Text: '{target}'")
                    print(f"  Font Family: {font_info.font_family}")
                    print(f"  Font Size: {font_info.font_size:.2f} pt")
                    print(f"  Font Weight: {font_info.font_weight}")
                    print(f"  Is Bold: {font_info.is_bold}")
                    print(f"  Position: ({font_info.bbox[0]:.2f}, {font_info.bbox[1]:.2f})")
                    print()
    
    # Get pdftohtml data
    print("\n2️⃣  pdftohtml Analysis:")
    print("-" * 100)
    
    cmd = [
        "pdftohtml",
        "-xml",
        "-stdout",
        "-hidden",
        "-zoom", str(zoom),
        pdf_path
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    xml_content = result.stdout.decode('utf-8')
    root = ET.fromstring(xml_content)
    
    # Build font specs
    fonts = {}
    for page in root.findall('page'):
        for font_node in page.findall('fontspec'):
            fid = font_node.get('id')
            fonts[fid] = {
                'family': font_node.get('family', 'sans-serif'),
                'size': int(font_node.get('size', '12')),
                'color': font_node.get('color', '#000000')
            }
    
    pdftohtml_data = {}
    for page in root.findall('page'):
        for text_node in page.findall('text'):
            text = "".join(text_node.itertext()).strip()
            
            for target in target_texts:
                if target in text:
                    font_id = text_node.get('font', '0')
                    font_spec = fonts.get(font_id, {})
                    
                    pdftohtml_data[target] = {
                        'text': text,
                        'font_id': font_id,
                        'font_family': font_spec.get('family', 'N/A'),
                        'font_size': font_spec.get('size', 0),
                        'height': int(text_node.get('height', '0')),
                        'top': float(text_node.get('top', '0')),
                        'left': float(text_node.get('left', '0'))
                    }
                    
                    print(f"Text: '{target}'")
                    print(f"  Font Family: {font_spec.get('family', 'N/A')}")
                    print(f"  Font Size: {font_spec.get('size', 0)} px")
                    print(f"  Height attribute: {text_node.get('height', '0')} px")
                    print(f"  Position: ({text_node.get('left', '0')}, {text_node.get('top', '0')})")
                    print()
    
    # Comparison
    print("\n3️⃣  Comparison & Analysis:")
    print("-" * 100)
    
    for target in target_texts:
        if target in pymupdf_data and target in pdftohtml_data:
            pm = pymupdf_data[target]
            ph = pdftohtml_data[target]
            
            print(f"\n📝 '{target}':")
            print(f"  {'Source':<15} {'Font Family':<25} {'Font Size':<20} {'Match'}")
            print(f"  {'-'*80}")
            
            # Font family comparison
            pm_family = pm.font_family.split(',')[0].strip('"')
            ph_family = ph['font_family']
            family_match = "✅" if pm_family.lower() == ph_family.lower() else "❌"
            
            print(f"  {'PyMuPDF':<15} {pm_family:<25} {pm.font_size:.2f} pt")
            print(f"  {'pdftohtml':<15} {ph_family:<25} {ph['font_size']} px            {family_match}")
            
            # Font size analysis
            # Expected conversion: pt * 1.333 * zoom = px
            expected_px = pm.font_size * 1.333 * zoom
            actual_px = ph['font_size']
            size_diff = abs(expected_px - actual_px)
            size_match = "✅" if size_diff < 1.0 else "❌"
            
            print(f"\n  Font Size Analysis:")
            print(f"    PyMuPDF:       {pm.font_size:.2f} pt")
            print(f"    Expected px:   {expected_px:.2f} px (at {zoom*100}% zoom)")
            print(f"    pdftohtml px:  {actual_px} px")
            print(f"    Difference:    {size_diff:.2f} px {size_match}")
            print(f"    Height attr:   {ph['height']} px")
            
            # Root cause analysis
            print(f"\n  🔍 Root Cause Analysis:")
            if pm_family.lower() != ph_family.lower():
                print(f"    ⚠️  FONT FAMILY MISMATCH:")
                print(f"        - PDF uses: {pm_family}")
                print(f"        - pdftohtml detects: {ph_family}")
                print(f"        - Solution: Update font mapping to treat '{ph_family}' as '{pm_family}'")
            
            if size_diff >= 1.0:
                print(f"    ⚠️  FONT SIZE MISMATCH:")
                print(f"        - Expected: {expected_px:.2f} px")
                print(f"        - Actual: {actual_px} px")
                print(f"        - Difference: {size_diff:.2f} px ({(size_diff/expected_px*100):.1f}%)")
                
                # Check if it's a rounding issue
                if abs(actual_px - round(expected_px)) < 0.5:
                    print(f"        - Likely cause: Rounding (expected rounds to {round(expected_px)})")
                else:
                    print(f"        - Likely cause: Incorrect font size detection or scaling")
                    print(f"        - Solution: Use PyMuPDF font sizes instead of pdftohtml")
    
    # Summary
    print(f"\n{'='*100}")
    print(f"SUMMARY & RECOMMENDATIONS")
    print(f"{'='*100}\n")
    
    family_issues = []
    size_issues = []
    
    for target in target_texts:
        if target in pymupdf_data and target in pdftohtml_data:
            pm = pymupdf_data[target]
            ph = pdftohtml_data[target]
            
            pm_family = pm.font_family.split(',')[0].strip('"')
            ph_family = ph['font_family']
            
            if pm_family.lower() != ph_family.lower():
                family_issues.append(f"{ph_family} → {pm_family}")
            
            expected_px = pm.font_size * 1.333 * zoom
            actual_px = ph['font_size']
            if abs(expected_px - actual_px) >= 1.0:
                size_issues.append(f"{pm.font_size:.2f}pt → {expected_px:.2f}px (got {actual_px}px)")
    
    print("📋 Issues Found:")
    print()
    
    if family_issues:
        print(f"  ❌ Font Family Mismatches: {len(family_issues)}")
        for issue in set(family_issues):
            print(f"     • {issue}")
        print()
    else:
        print("  ✅ No font family issues")
        print()
    
    if size_issues:
        print(f"  ❌ Font Size Mismatches: {len(size_issues)}")
        for issue in size_issues:
            print(f"     • {issue}")
        print()
    else:
        print("  ✅ No font size issues")
        print()
    
    print("💡 Solutions:")
    print()
    
    if family_issues:
        print("  1. Font Family Fix:")
        print("     • pdftohtml reports 'Helvetica' but PDF actually uses 'Arial'")
        print("     • These are equivalent fonts (Arial is Microsoft's version of Helvetica)")
        print("     • Update extractors/fonts.py to map Helvetica → Arial")
        print("     • Or use PyMuPDF's font detection instead of pdftohtml's")
        print()
    
    if size_issues:
        print("  2. Font Size Fix:")
        print("     • pdftohtml font sizes don't match PyMuPDF's accurate measurements")
        print("     • Current backend already uses PyMuPDF for font size detection")
        print("     • Verify that PyMuPDF font sizes are being used in final HTML")
        print("     • Check text_parser.py to ensure PyMuPDF fonts override pdftohtml")
        print()
    
    if not family_issues and not size_issues:
        print("  ✅ All fonts are correctly detected and converted!")


if __name__ == "__main__":
    # Test with the PDF from the image
    test_pdfs = [
        "temp/test_pdfs/1010054315.pdf",
        "temp/test_pdfs/2049322459.pdf",
    ]
    
    for pdf_path in test_pdfs:
        if Path(pdf_path).exists():
            analyze_specific_text(pdf_path, zoom=1.5)
            break
    else:
        print("❌ No test PDFs found. Please provide a PDF path as argument.")

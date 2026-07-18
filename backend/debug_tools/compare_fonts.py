"""
Compare font properties between PDF and HTML output.
Analyzes both font-family and font-size to identify discrepancies.
"""
import sys
import fitz  # PyMuPDF
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.font_extractor import FontExtractorPyMuPDF


def analyze_pdf_fonts(pdf_path: str, zoom: float = 1.5):
    """Analyze fonts in PDF using PyMuPDF"""
    print(f"\n{'='*80}")
    print(f"PDF FONT ANALYSIS (PyMuPDF)")
    print(f"{'='*80}\n")
    
    extractor = FontExtractorPyMuPDF(pdf_path)
    extractor.extract()
    
    # Analyze first page
    if 1 in extractor.pages:
        fonts = extractor.pages[1]
        
        print(f"{'Text':<40} {'Font Family':<30} {'Size (pt)':<12} {'Weight':<8}")
        print("-" * 90)
        
        for font_info in fonts[:20]:  # First 20 entries
            text_display = font_info.text[:37] + "..." if len(font_info.text) > 40 else font_info.text
            # Extract just the first font name from the stack
            font_family = font_info.font_family.split(',')[0].strip('"')
            print(f"{text_display:<40} {font_family:<30} {font_info.font_size:<12.2f} {font_info.font_weight:<8}")
        
        # Statistics
        unique_families = set(f.font_family.split(',')[0].strip('"') for f in fonts)
        unique_sizes = set(f.font_size for f in fonts)
        
        print(f"\n📊 Statistics:")
        print(f"  Total text elements: {len(fonts)}")
        print(f"  Unique font families: {len(unique_families)}")
        print(f"  Font families: {', '.join(sorted(unique_families))}")
        print(f"  Unique font sizes: {sorted(unique_sizes)}")
        
        return fonts
    
    return []


def analyze_pdftohtml_fonts(pdf_path: str, zoom: float = 1.5):
    """Analyze fonts detected by pdftohtml"""
    print(f"\n{'='*80}")
    print(f"PDFTOHTML FONT ANALYSIS (zoom={zoom})")
    print(f"{'='*80}\n")
    
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
    
    # Extract font specs from page nodes
    print("Font Specifications:")
    print("-" * 80)
    fonts = {}
    
    for page in root.findall('page'):
        for font_node in page.findall('fontspec'):
            fid = font_node.get('id')
            family = font_node.get('family', 'sans-serif')
            size = font_node.get('size', '12')
            color = font_node.get('color', '#000000')
            
            fonts[fid] = {
                'family': family,
                'size': size,
                'color': color
            }
            
            print(f"  Font {fid}: {family}, size={size}px, color={color}")
    
    # Sample text elements
    print(f"\nSample Text Elements:")
    print("-" * 80)
    print(f"{'Text':<40} {'Font ID':<10} {'Size':<12} {'Height':<10} {'Width':<10}")
    print("-" * 80)
    
    count = 0
    for page in root.findall('page'):
        if count >= 20:
            break
            
        for text_node in page.findall('text'):
            if count >= 20:
                break
            
            text = "".join(text_node.itertext()).strip()
            if not text:
                continue
                
            font_id = text_node.get('font', '0')
            height = text_node.get('height', '0')
            width = text_node.get('width', '0')
            
            font_info = fonts.get(font_id, {})
            font_size = font_info.get('size', 'N/A')
            font_family = font_info.get('family', 'N/A')
            
            text_display = text[:37] + "..." if len(text) > 40 else text
            print(f"{text_display:<40} {font_id:<10} {font_size:<12} {height:<10} {width:<10}")
            count += 1
    
    # Statistics
    unique_families = set(f['family'] for f in fonts.values())
    unique_sizes = set(f['size'] for f in fonts.values())
    
    print(f"\n📊 Statistics:")
    print(f"  Total font specs: {len(fonts)}")
    print(f"  Unique font families: {len(unique_families)}")
    print(f"  Font families: {', '.join(sorted(unique_families))}")
    print(f"  Font sizes: {', '.join(sorted(unique_sizes, key=lambda x: float(x)))}")
    
    return fonts


def compare_fonts(pdf_path: str, zoom: float = 1.5):
    """Compare fonts between PyMuPDF and pdftohtml"""
    print(f"\n{'='*80}")
    print(f"FONT COMPARISON ANALYSIS")
    print(f"PDF: {Path(pdf_path).name}")
    print(f"Zoom: {zoom}")
    print(f"{'='*80}")
    
    # Get fonts from both sources
    pymupdf_fonts = analyze_pdf_fonts(pdf_path, zoom)
    pdftohtml_fonts = analyze_pdftohtml_fonts(pdf_path, zoom)
    
    # Analysis
    print(f"\n{'='*80}")
    print(f"COMPARISON RESULTS")
    print(f"{'='*80}\n")
    
    # Font family comparison
    pymupdf_families = set(f.font_family.split(',')[0].strip('"') for f in pymupdf_fonts)
    pdftohtml_families = set(f['family'] for f in pdftohtml_fonts.values())
    
    print("🔤 Font Family Analysis:")
    print("-" * 80)
    print(f"PyMuPDF detected families: {', '.join(sorted(pymupdf_families))}")
    print(f"pdftohtml detected families: {', '.join(sorted(pdftohtml_families))}")
    
    if pymupdf_families != pdftohtml_families:
        print("\n⚠️  FONT FAMILY MISMATCH DETECTED!")
        print(f"  Only in PyMuPDF: {pymupdf_families - pdftohtml_families}")
        print(f"  Only in pdftohtml: {pdftohtml_families - pymupdf_families}")
    else:
        print("\n✅ Font families match!")
    
    # Font size comparison
    pymupdf_sizes = sorted(set(f.font_size for f in pymupdf_fonts))
    pdftohtml_sizes = sorted(set(float(f['size']) for f in pdftohtml_fonts.values()))
    
    print(f"\n📏 Font Size Analysis:")
    print("-" * 80)
    print(f"PyMuPDF detected sizes (pt): {pymupdf_sizes}")
    print(f"pdftohtml detected sizes (px at zoom {zoom}): {pdftohtml_sizes}")
    
    # Calculate expected sizes (pt to px conversion at zoom level)
    # 1 pt = 1.333 px at 100% zoom (96 DPI)
    # At 150% zoom: 1 pt = 1.333 * 1.5 = 2.0 px
    pt_to_px = 1.333 * zoom
    
    print(f"\nExpected conversion (1 pt = {pt_to_px:.3f} px at {zoom*100}% zoom):")
    print("-" * 80)
    
    size_mismatches = []
    for pt_size in pymupdf_sizes:
        expected_px = pt_size * pt_to_px
        # Find closest pdftohtml size
        closest_px = min(pdftohtml_sizes, key=lambda x: abs(x - expected_px))
        diff = abs(closest_px - expected_px)
        
        status = "✅" if diff < 0.5 else "⚠️"
        print(f"  {pt_size:.2f} pt → expected {expected_px:.2f} px, got {closest_px:.2f} px (diff: {diff:.2f} px) {status}")
        
        if diff >= 0.5:
            size_mismatches.append((pt_size, expected_px, closest_px, diff))
    
    if size_mismatches:
        print(f"\n⚠️  FONT SIZE MISMATCHES DETECTED!")
        print(f"  {len(size_mismatches)} size(s) have significant differences (≥0.5px)")
        print("\n  Possible causes:")
        print("    1. Font size scaling issue in conversion")
        print("    2. Incorrect zoom factor application")
        print("    3. Font substitution affecting metrics")
    else:
        print("\n✅ Font sizes match within tolerance!")
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}\n")
    
    issues = []
    if pymupdf_families != pdftohtml_families:
        issues.append("Font family mismatch")
    if size_mismatches:
        issues.append(f"Font size mismatch ({len(size_mismatches)} sizes)")
    
    if issues:
        print("❌ Issues found:")
        for issue in issues:
            print(f"  • {issue}")
        
        print("\n💡 Recommendations:")
        if pymupdf_families != pdftohtml_families:
            print("  • Update font mapping in font_extractor_pymupdf.py")
            print("  • Ensure pdftohtml font names are correctly mapped to CSS fonts")
        if size_mismatches:
            print("  • Verify zoom factor is correctly applied to font sizes")
            print("  • Check if PyMuPDF font sizes need scaling adjustment")
    else:
        print("✅ All checks passed! Fonts match correctly.")


if __name__ == "__main__":
    # Test with a sample PDF
    test_pdfs = [
        "temp/test_pdfs/1010054315.pdf",
        "temp/test_pdfs/2049322459.pdf",
        "temp/test_pdfs/1282161800020.pdf",
    ]
    
    for pdf_path in test_pdfs:
        if Path(pdf_path).exists():
            compare_fonts(pdf_path, zoom=1.5)
            break
    else:
        print("❌ No test PDFs found. Please provide a PDF path as argument.")
        print("Usage: python compare_fonts.py <pdf_path> [zoom]")

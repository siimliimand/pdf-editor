"""
Compare actual rendered sizes between PDF and HTML
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.font_extractor import FontExtractorPyMuPDF

def analyze_sizes(pdf_path: str):
    """Analyze the actual sizes in the PDF"""
    
    print(f"\n{'='*100}")
    print(f"SIZE ANALYSIS")
    print(f"PDF: {Path(pdf_path).name}")
    print(f"{'='*100}\n")
    
    extractor = FontExtractorPyMuPDF(pdf_path)
    extractor.extract()
    
    if 1 not in extractor.pages:
        print("No page 1 found")
        return
    
    fonts = extractor.pages[1]
    
    # Find specific text elements
    target_texts = {
        "SeoWeb OÜ": None,
        "Reg nr: 12629973": None,
        "Staadioni 8, 70": None,
    }
    
    for font_info in fonts:
        for target in target_texts:
            if target in font_info.text:
                target_texts[target] = font_info
                break
    
    print("📏 Font Sizes in PDF (PyMuPDF):")
    print("-" * 100)
    for text, font_info in target_texts.items():
        if font_info:
            print(f"{text:<30} {font_info.font_size:.2f} pt")
    
    print("\n📐 Expected HTML Sizes at 150% zoom:")
    print("-" * 100)
    print("Formula: pt × zoom_factor (WITHOUT DPI conversion)")
    print()
    
    for text, font_info in target_texts.items():
        if font_info:
            # Without DPI conversion (what pdftohtml does)
            size_no_dpi = font_info.font_size * 1.5
            # With DPI conversion (what we're doing now)
            size_with_dpi = font_info.font_size * 1.333 * 1.5
            
            print(f"{text:<30}")
            print(f"  Without DPI (1.5x):     {size_no_dpi:.2f} px")
            print(f"  With DPI (1.333×1.5):   {size_with_dpi:.2f} px")
            print()
    
    print("\n💡 Analysis:")
    print("-" * 100)
    print("If the logo is the SAME size in both PDF and HTML, but text is LARGER in HTML,")
    print("this suggests we should NOT apply the 1.333 DPI multiplier.")
    print()
    print("Reason: pdftohtml already handles the coordinate scaling, and we should")
    print("match its behavior for consistency.")
    print()
    print("The 1.333 multiplier is for converting 72 DPI (PDF standard) to 96 DPI (web standard),")
    print("but pdftohtml may already be doing this internally, or the zoom factor already accounts for it.")

if __name__ == "__main__":
    pdf_path = "temp/test_pdfs/1010054315.pdf"
    
    if Path(pdf_path).exists():
        analyze_sizes(pdf_path)
    else:
        print(f"❌ PDF not found: {pdf_path}")

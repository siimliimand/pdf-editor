#!/usr/bin/env python3
"""
Test the improved font mapping system.
Shows how PDF fonts are mapped to web-safe CSS font stacks.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.font_extractor import FontExtractorPyMuPDF

def test_font_mapping():
    """Test font mapping with real PDFs"""
    
    pdf_files = [
        'temp/test_pdfs/2049322459.pdf',
        'temp/test_pdfs/1010054315.pdf',
        'temp/test_pdfs/1282161800020.pdf',
        'temp/test_pdfs/EUINEE25-95942.pdf'
    ]
    
    print("\n" + "="*80)
    print("FONT MAPPING TEST - PDF to CSS Font Stacks")
    print("="*80)
    
    all_mappings = {}
    
    for pdf_path in pdf_files:
        if not Path(pdf_path).exists():
            continue
            
        print(f"\n📄 {Path(pdf_path).name}")
        print("-"*80)
        
        extractor = FontExtractorPyMuPDF(pdf_path)
        extractor.extract()
        
        # Collect unique font mappings
        font_mappings = {}
        
        for page_num, fonts in extractor.pages.items():
            for font_info in fonts:
                pdf_font = font_info.text[:30] + "..." if len(font_info.text) > 30 else font_info.text
                
                # Get the original font name from the font_info
                # We need to extract it from the PDF again
                import fitz
                doc = fitz.open(pdf_path)
                page = doc[page_num - 1]
                blocks = page.get_text("dict")["blocks"]
                
                for block in blocks:
                    if block.get("type") == 0:
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                if span.get("text", "").strip() == font_info.text:
                                    original_font = span.get("font", "Unknown")
                                    css_font = font_info.font_family
                                    
                                    if original_font not in font_mappings:
                                        font_mappings[original_font] = css_font
                                        all_mappings[original_font] = css_font
                                    break
                doc.close()
                break
        
        # Display mappings for this PDF
        for pdf_font, css_font in sorted(font_mappings.items()):
            print(f"  {pdf_font:<35} → {css_font}")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY - All Unique Font Mappings")
    print("="*80)
    
    for pdf_font, css_font in sorted(all_mappings.items()):
        print(f"  {pdf_font:<35} → {css_font}")
    
    print(f"\n✓ Total unique fonts mapped: {len(all_mappings)}")

if __name__ == "__main__":
    test_font_mapping()

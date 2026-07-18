#!/usr/bin/env python3
"""
Test script to verify that top padding is correctly preserved in HTML output.
This tests the fix for the top padding detection bug.
"""

import sys
import os
# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pathlib import Path
import subprocess
from services.xml_parser import parse_xml_to_html
from services.image_extractor_pymupdf import ImageExtractorPyMuPDF
import re

def test_top_padding_conversion(pdf_path: str):
    """Test that top padding from PDF is preserved in HTML."""
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"Error: PDF not found: {pdf_path}")
        return False
    
    print(f"\n{'='*80}")
    print(f"Testing Top Padding Preservation: {pdf_file.name}")
    print(f"{'='*80}\n")
    
    temp_dir = Path("temp/padding_test")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Extract images
    print("Step 1: Extracting images with PyMuPDF...")
    try:
        extractor = ImageExtractorPyMuPDF(str(pdf_file), temp_dir)
        extractor.extract()
        print(f"✅ Extracted images from {len(extractor.images)} pages")
    except Exception as e:
        print(f"❌ Image extraction failed: {e}")
        return False
    
    # Step 2: Extract XML
    print("\nStep 2: Extracting XML with pdftohtml...")
    cmd = [
        "pdftohtml",
        "-xml",
        "-stdout",
        "-hidden",
        "-zoom", "1.0",
        str(pdf_file.name)
    ]
    
    try:
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=pdf_file.parent,
            timeout=30
        )
        
        if process.returncode != 0:
            print(f"❌ pdftohtml failed: {process.stderr.decode()}")
            return False
        
        xml_content = process.stdout.decode('utf-8')
        print(f"✅ XML extracted ({len(xml_content)} bytes)")
    except Exception as e:
        print(f"❌ XML extraction failed: {e}")
        return False
    
    # Step 3: Parse XML to find expected top padding
    print("\nStep 3: Analyzing expected top padding from XML...")
    import xml.etree.ElementTree as ET
    
    root = ET.fromstring(xml_content)
    page = root.find('page')
    
    if not page:
        print("❌ No page found in XML")
        return False
    
    # Find first element
    all_elements = []
    for text_node in page.findall('text'):
        top = float(text_node.get('top', 0))
        all_elements.append(('text', top))
    
    for img_node in page.findall('image'):
        top = float(img_node.get('top', 0))
        all_elements.append(('image', top))
    
    if not all_elements:
        print("❌ No elements found in XML")
        return False
    
    all_elements.sort(key=lambda x: x[1])
    first_elem_type, expected_top_padding = all_elements[0]
    
    print(f"   First element type: {first_elem_type}")
    print(f"   Expected top padding: {expected_top_padding:.2f}px")
    
    # Step 4: Convert to HTML
    print("\nStep 4: Converting to HTML...")
    try:
        html_output = parse_xml_to_html(
            xml_content,
            temp_dir,
            {},  # No vectors for this test
            extractor.images
        )
        print(f"✅ HTML generated ({len(html_output)} bytes)")
    except Exception as e:
        print(f"❌ HTML generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 5: Verify top padding in HTML
    print("\nStep 5: Verifying top padding in HTML...")
    
    # Save HTML for inspection
    output_file = temp_dir / "output.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_output)
    print(f"   Saved HTML to: {output_file}")
    
    # Find first table or p tag and check its margin-top
    # Look for the first element with margin-top style
    table_match = re.search(r'<table[^>]*style="([^"]+)"', html_output)
    p_match = re.search(r'<p[^>]*style="([^"]+)"', html_output)
    
    actual_margin_top = None
    found_element = None
    
    if table_match:
        style = table_match.group(1)
        margin_match = re.search(r'margin-top:\s*(\d+)px', style)
        if margin_match:
            actual_margin_top = int(margin_match.group(1))
            found_element = 'table'
    
    if actual_margin_top is None and p_match:
        style = p_match.group(1)
        margin_match = re.search(r'margin-top:\s*(\d+)px', style)
        if margin_match:
            actual_margin_top = int(margin_match.group(1))
            found_element = 'p'
    
    if actual_margin_top is None:
        print("❌ Could not find margin-top in HTML output")
        return False
    
    print(f"   Found first <{found_element}> element")
    print(f"   Actual margin-top in HTML: {actual_margin_top}px")
    
    # Step 6: Compare
    print("\nStep 6: Comparison:")
    print(f"   Expected: {expected_top_padding:.2f}px")
    print(f"   Actual:   {actual_margin_top}px")
    
    # Allow small rounding differences
    tolerance = 2
    difference = abs(actual_margin_top - expected_top_padding)
    
    print(f"   Difference: {difference:.2f}px")
    
    if difference <= tolerance:
        print(f"\n✅ SUCCESS: Top padding is correctly preserved (within {tolerance}px tolerance)")
        return True
    else:
        if actual_margin_top == 0:
            print(f"\n❌ FAILURE: Top padding is 0 (BUG DETECTED)")
        else:
            print(f"\n⚠️  WARNING: Top padding differs by {difference:.2f}px")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Use default test PDF
        test_pdf = "temp/test_pdfs/1010054315.pdf"
        if Path(test_pdf).exists():
            print(f"Using default test PDF: {test_pdf}")
            success = test_top_padding_conversion(test_pdf)
            sys.exit(0 if success else 1)
        else:
            print("Usage: python3 test_padding_fix.py <pdf_path>")
            print(f"\nDefault test PDF not found: {test_pdf}")
            sys.exit(1)
    else:
        test_pdf = sys.argv[1]
        success = test_top_padding_conversion(test_pdf)
        sys.exit(0 if success else 1)

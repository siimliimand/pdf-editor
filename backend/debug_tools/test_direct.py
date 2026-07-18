#!/usr/bin/env python3
"""
Direct test of image extraction and position detection.
This bypasses the server and directly tests the core functionality.
"""

import sys
import os
# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pathlib import Path
from services.image_extractor_pymupdf import ImageExtractorPyMuPDF
from services.xml_parser import parse_xml_to_html
import subprocess

def test_direct_extraction(pdf_path):
    """Test image extraction directly."""
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"Error: PDF not found: {pdf_path}")
        return
    
    print(f"\n{'='*80}")
    print(f"Direct Extraction Test: {pdf_file.name}")
    print(f"{'='*80}\n")
    
    # Create temp directory
    temp_dir = Path("temp/direct_test")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Extract images with PyMuPDF
    print("Step 1: Extracting images with PyMuPDF...")
    try:
        extractor = ImageExtractorPyMuPDF(str(pdf_file), temp_dir)
        extractor.extract()
        
        for page_num, images in extractor.images.items():
            print(f"\n  Page {page_num}: {len(images)} images")
            for img_data in images:
                filename, x0, y0, x1, y1, w, h = img_data
                print(f"    - {filename}: pos=({x0:.1f}, {y0:.1f}, {x1:.1f}, {y1:.1f}), size={w}x{h}px")
        
        print("\n✅ PyMuPDF extraction successful")
    except Exception as e:
        print(f"\n❌ PyMuPDF extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 2. Extract XML
    print("\n\nStep 2: Extracting XML with pdftohtml...")
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
            return
        
        xml_content = process.stdout.decode('utf-8')
        print(f"✅ XML extracted ({len(xml_content)} bytes)")
        
    except Exception as e:
        print(f"❌ XML extraction failed: {e}")
        return
    
    # 3. Parse to HTML
    print("\n\nStep 3: Parsing to HTML...")
    print("=" * 80)
    print("DEBUG OUTPUT FROM EXTRACTORS:")
    print("=" * 80)
    
    try:
        html_output = parse_xml_to_html(
            xml_content,
            temp_dir,
            {},  # No vector data for this test
            extractor.images
        )
        
        print("\n" + "=" * 80)
        print(f"✅ HTML generated ({len(html_output)} bytes)")
        
        # Save HTML for inspection
        output_file = temp_dir / "output.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_output)
        
        print(f"📄 Saved to: {output_file}")
        
        # Analyze images in HTML
        import re
        img_tags = re.findall(r'<img[^>]+>', html_output)
        print(f"\n📊 Found {len(img_tags)} image tags in HTML")
        
        for i, tag in enumerate(img_tags, 1):
            # Extract dimensions
            width = re.search(r'width="(\d+)"', tag)
            height = re.search(r'height="(\d+)"', tag)
            if width and height:
                print(f"  Image {i}: {width.group(1)}x{height.group(1)}px")
        
    except Exception as e:
        print(f"\n❌ HTML generation failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 80)
    print("✅ Test completed successfully!")
    print("=" * 80)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Use default test PDF
        test_pdf = "temp/test_pdfs/1010054315.pdf"
        if not Path(test_pdf).exists():
            print("Usage: python3 test_direct.py <pdf_path>")
            print(f"\nDefault test PDF not found: {test_pdf}")
            sys.exit(1)
    else:
        test_pdf = sys.argv[1]
    
    test_direct_extraction(test_pdf)

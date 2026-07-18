"""
Debug script to test image position detection and conversion to HTML.
This script will:
1. Extract images using PyMuPDF
2. Parse XML from pdftohtml
3. Match images and check position alignment
4. Verify image dimensions remain correct
"""

import sys
import os
# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import subprocess
from pathlib import Path
from services.image_extractor_pymupdf import ImageExtractorPyMuPDF
from services.xml_parser.extractors import extract_elements, extract_fonts
import xml.etree.ElementTree as ET

def test_pdf_image_positions(pdf_path: str):
    """Test image position detection for a given PDF."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return
    
    print(f"\n{'='*80}")
    print(f"Testing PDF: {pdf_path.name}")
    print(f"{'='*80}\n")
    
    # Create temp directory for this test
    temp_dir = Path("temp/test_images")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Extract images using PyMuPDF
    print("Step 1: Extracting images using PyMuPDF...")
    extractor = ImageExtractorPyMuPDF(str(pdf_path), temp_dir)
    extractor.extract()
    
    for page_num, images in extractor.images.items():
        print(f"\n  Page {page_num}: Found {len(images)} images")
        for i, img_data in enumerate(images):
            filename, x0, y0, x1, y1, width, height = img_data
            print(f"    Image {i+1}:")
            print(f"      Filename: {filename}")
            print(f"      Position (bottom-up): x0={x0:.2f}, y0={y0:.2f}, x1={x1:.2f}, y1={y1:.2f}")
            print(f"      Display dimensions: {x1-x0:.2f} x {y1-y0:.2f} px")
            print(f"      Natural dimensions: {width} x {height} px")
    
    # 2. Extract XML from pdftohtml
    print("\n\nStep 2: Extracting XML from pdftohtml...")
    cmd = [
        "pdftohtml",
        "-xml",
        "-stdout",
        "-hidden",
        "-zoom", "1.0",
        str(pdf_path.name)
    ]
    
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=pdf_path.parent)
    
    if process.returncode != 0:
        print(f"Error running pdftohtml: {process.stderr.decode()}")
        return
    
    xml_content = process.stdout.decode('utf-8')
    root = ET.fromstring(xml_content)
    
    # 3. Parse XML and check image positions
    print("\n\nStep 3: Parsing XML and matching images...")
    fonts = extract_fonts(root)
    
    for page in root.findall('page'):
        page_num = int(page.get('number'))
        page_width = int(page.get('width'))
        page_height = int(page.get('height'))
        
        print(f"\n  Page {page_num} (size: {page_width} x {page_height}):")
        
        # Get extracted images for this page
        extracted_images = extractor.images.get(page_num, [])
        
        # Find image nodes in XML
        img_nodes = page.findall('image')
        print(f"    XML image nodes: {len(img_nodes)}")
        print(f"    Extracted images: {len(extracted_images)}")
        
        for img_idx, img_node in enumerate(img_nodes):
            top = float(img_node.get('top', 0))
            left = float(img_node.get('left', 0))
            width = float(img_node.get('width', 0))
            height = float(img_node.get('height', 0))
            src = img_node.get('src', '')
            
            print(f"\n    XML Image {img_idx + 1}:")
            print(f"      XML src: {src}")
            print(f"      XML position (top-down): left={left:.2f}, top={top:.2f}")
            print(f"      XML dimensions: {width:.2f} x {height:.2f} px")
            
            # Convert to bottom-up for matching
            xml_y0_bottomup = page_height - top - height
            xml_y1_bottomup = page_height - top
            xml_x0 = left
            xml_x1 = left + width
            
            print(f"      XML position (bottom-up): x0={xml_x0:.2f}, y0={xml_y0_bottomup:.2f}, x1={xml_x1:.2f}, y1={xml_y1_bottomup:.2f}")
            
            # Find matching extracted image
            matched_image = None
            best_overlap = 0.0
            
            for img_data in extracted_images:
                filename, img_x0, img_y0, img_x1, img_y1, actual_width, actual_height = img_data
                
                # Calculate intersection
                inter_x0 = max(xml_x0, img_x0)
                inter_y0 = max(xml_y0_bottomup, img_y0)
                inter_x1 = min(xml_x1, img_x1)
                inter_y1 = min(xml_y1_bottomup, img_y1)
                
                if inter_x1 > inter_x0 and inter_y1 > inter_y0:
                    inter_area = (inter_x1 - inter_x0) * (inter_y1 - inter_y0)
                    
                    xml_area = (xml_x1 - xml_x0) * (xml_y1_bottomup - xml_y0_bottomup)
                    img_area = (img_x1 - img_x0) * (img_y1 - img_y0)
                    
                    overlap = inter_area / min(xml_area, img_area) if min(xml_area, img_area) > 0 else 0
                    
                    if overlap > best_overlap:
                        best_overlap = overlap
                        matched_image = (filename, img_x0, img_y0, img_x1, img_y1, actual_width, actual_height, overlap)
            
            if matched_image:
                filename, img_x0, img_y0, img_x1, img_y1, actual_width, actual_height, overlap = matched_image
                print(f"\n      ✓ MATCHED with {filename} (overlap: {overlap:.2%})")
                print(f"        PyMuPDF position (bottom-up): x0={img_x0:.2f}, y0={img_y0:.2f}, x1={img_x1:.2f}, y1={img_y1:.2f}")
                print(f"        PyMuPDF display size: {img_x1-img_x0:.2f} x {img_y1-img_y0:.2f} px")
                print(f"        PyMuPDF natural size: {actual_width} x {actual_height} px")
                
                # Check position discrepancy
                pos_diff_x = abs(xml_x0 - img_x0)
                pos_diff_y = abs(xml_y0_bottomup - img_y0)
                size_diff_w = abs(width - (img_x1 - img_x0))
                size_diff_h = abs(height - (img_y1 - img_y0))
                
                print(f"\n      Position difference: Δx={pos_diff_x:.2f}px, Δy={pos_diff_y:.2f}px")
                print(f"      Size difference: Δw={size_diff_w:.2f}px, Δh={size_diff_h:.2f}px")
                
                if pos_diff_x > 5 or pos_diff_y > 5:
                    print(f"      ⚠ WARNING: Position mismatch detected!")
                
                if size_diff_w > 5 or size_diff_h > 5:
                    print(f"      ⚠ WARNING: Size mismatch detected!")
                    
                # Show what will be used in HTML
                display_width = img_x1 - img_x0 if (img_x1 - img_x0) > 0 else actual_width
                display_height = img_y1 - img_y0 if (img_y1 - img_y0) > 0 else actual_height
                
                # Convert back to top-down for HTML
                html_top = page_height - img_y1
                html_left = img_x0
                
                print(f"\n      HTML position (top-down): left={html_left:.2f}px, top={html_top:.2f}px")
                print(f"      HTML size: {display_width:.2f} x {display_height:.2f} px")
                
            else:
                print(f"\n      ✗ NO MATCH FOUND - Using XML fallback")
                print(f"        HTML will use: left={left:.2f}px, top={top:.2f}px, size={width:.2f}x{height:.2f}px")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_image_positions.py <path_to_pdf>")
        print("\nSearching for test PDFs...")
        test_pdfs = list(Path("temp/test_pdfs").glob("*.pdf")) if Path("temp/test_pdfs").exists() else []
        if test_pdfs:
            print("\nFound PDFs in temp/test_pdfs/:")
            for i, pdf in enumerate(test_pdfs, 1):
                print(f"  {i}. {pdf.name}")
            print("\nTesting all found PDFs...\n")
            for pdf in test_pdfs:
                test_pdf_image_positions(str(pdf))
        else:
            print("\nNo test PDFs found. Please provide a PDF path.")
    else:
        test_pdf_image_positions(sys.argv[1])

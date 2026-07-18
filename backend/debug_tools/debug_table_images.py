#!/usr/bin/env python3
"""
Debug script to analyze how images are positioned within tables.
This will help identify if table cell boundaries are causing image misalignment.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import subprocess
from pathlib import Path
from services.image_extractor_pymupdf import ImageExtractorPyMuPDF
from services.xml_parser.extractors import extract_elements, extract_fonts
from services.xml_parser.table_detector.detector import TableDetector
import xml.etree.ElementTree as ET

def debug_table_images(pdf_path: str):
    """Debug image positioning within tables for a given PDF."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return
    
    print(f"\n{'='*80}")
    print(f"Debugging Table Images: {pdf_path.name}")
    print(f"{'='*80}\n")
    
    # Create temp directory
    temp_dir = Path("temp/test_images")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Extract images using PyMuPDF
    print("Step 1: Extracting images using PyMuPDF...")
    extractor = ImageExtractorPyMuPDF(str(pdf_path), temp_dir)
    extractor.extract()
    
    all_images = {}
    for page_num, images in extractor.images.items():
        print(f"\n  Page {page_num}: Found {len(images)} images")
        all_images[page_num] = []
        for i, img_data in enumerate(images):
            filename, x0, y0, x1, y1, width, height = img_data
            all_images[page_num].append({
                'filename': filename,
                'x0': x0, 'y0': y0, 'x1': x1, 'y1': y1,
                'width': width, 'height': height
            })
            print(f"    Image {i+1}: {filename}")
            print(f"      Position (bottom-up): x0={x0:.2f}, y0={y0:.2f}, x1={x1:.2f}, y1={y1:.2f}")
    
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
    
    # 3. Detect tables
    print("\n\nStep 3: Detecting tables...")
    fonts = extract_fonts(root)
    
    for page in root.findall('page'):
        page_num = int(page.get('number'))
        page_width = int(page.get('width'))
        page_height = int(page.get('height'))
        
        print(f"\n  Page {page_num} (size: {page_width} x {page_height}):")
        
        # Extract elements
        elements = extract_elements(page, fonts, None)
        
        # Detect tables
        detector = TableDetector(elements, page_width, page_height)
        tables = detector.detect()
        
        print(f"    Detected {len(tables)} table(s)")
        
        # Get images for this page
        page_images = all_images.get(page_num, [])
        
        # Check if any images are inside tables
        for table_idx, table in enumerate(tables):
            print(f"\n    Table {table_idx + 1}:")
            print(f"      Bounds: x0={table.x0:.2f}, y0={table.y0:.2f}, x1={table.x1:.2f}, y1={table.y1:.2f}")
            print(f"      Rows: {len(table.rows)}, Columns: {len(table.column_positions)}")
            
            # Check if any images fall within this table
            images_in_table = []
            for img in page_images:
                # Check if image center is within table bounds
                img_center_x = (img['x0'] + img['x1']) / 2
                img_center_y = (img['y0'] + img['y1']) / 2
                
                if (table.x0 <= img_center_x <= table.x1 and 
                    table.y0 <= img_center_y <= table.y1):
                    images_in_table.append(img)
            
            if images_in_table:
                print(f"\n      ⚠ Found {len(images_in_table)} image(s) inside this table:")
                
                for img in images_in_table:
                    print(f"\n        Image: {img['filename']}")
                    print(f"          Image position (bottom-up): x0={img['x0']:.2f}, y0={img['y0']:.2f}, x1={img['x1']:.2f}, y1={img['y1']:.2f}")
                    
                    # Find which cell this image belongs to
                    img_center_x = (img['x0'] + img['x1']) / 2
                    img_center_y = (img['y0'] + img['y1']) / 2
                    
                    # Convert to top-down for easier comparison
                    img_top = page_height - img['y1']
                    img_bottom = page_height - img['y0']
                    
                    print(f"          Image position (top-down): left={img['x0']:.2f}, top={img_top:.2f}, right={img['x1']:.2f}, bottom={img_bottom:.2f}")
                    
                    # Find the cell
                    found_cell = False
                    for row_idx, row in enumerate(table.rows):
                        for cell in row.cells:
                            # Cell bounds in top-down coordinates
                            cell_top = page_height - cell.y1
                            cell_bottom = page_height - cell.y0
                            cell_left = cell.x0
                            cell_right = cell.x1
                            
                            # Check if image center is in this cell
                            if (cell_left <= img_center_x <= cell_right and
                                cell_top <= img_center_y <= cell_bottom):
                                
                                print(f"\n          ✓ Image is in Row {row_idx + 1}, Cell bounds:")
                                print(f"            Cell (top-down): left={cell_left:.2f}, top={cell_top:.2f}, right={cell_right:.2f}, bottom={cell_bottom:.2f}")
                                print(f"            Cell (bottom-up): x0={cell.x0:.2f}, y0={cell.y0:.2f}, x1={cell.x1:.2f}, y1={cell.y1:.2f}")
                                print(f"            Cell size: {cell.x1 - cell.x0:.2f} x {cell.y1 - cell.y0:.2f} px")
                                
                                # Calculate relative position within cell
                                rel_left = img['x0'] - cell.x0
                                rel_top_bottomup = img['y0'] - cell.y0
                                rel_top_topdown = img_top - cell_top
                                
                                print(f"\n          Relative position within cell:")
                                print(f"            rel_left (from cell start): {rel_left:.2f}px")
                                print(f"            rel_top (bottom-up): {rel_top_bottomup:.2f}px")
                                print(f"            rel_top (top-down): {rel_top_topdown:.2f}px")
                                
                                # Check if position looks wrong
                                if rel_left < 0 or rel_left > (cell.x1 - cell.x0):
                                    print(f"            ⚠ WARNING: Image left position is outside cell bounds!")
                                if rel_top_topdown < 0 or rel_top_topdown > (cell_bottom - cell_top):
                                    print(f"            ⚠ WARNING: Image top position is outside cell bounds!")
                                
                                # Show what HTML will render
                                print(f"\n          HTML will render as:")
                                print(f"            position: absolute;")
                                print(f"            left: {rel_left:.2f}px;")
                                print(f"            top: {rel_top_topdown:.2f}px;")
                                
                                found_cell = True
                                break
                        if found_cell:
                            break
                    
                    if not found_cell:
                        print(f"          ✗ WARNING: Could not find cell containing this image!")
        
        # Check for images NOT in any table
        images_outside_tables = []
        for img in page_images:
            img_center_x = (img['x0'] + img['x1']) / 2
            img_center_y = (img['y0'] + img['y1']) / 2
            
            in_any_table = False
            for table in tables:
                if (table.x0 <= img_center_x <= table.x1 and 
                    table.y0 <= img_center_y <= table.y1):
                    in_any_table = True
                    break
            
            if not in_any_table:
                images_outside_tables.append(img)
        
        if images_outside_tables:
            print(f"\n    Images outside tables: {len(images_outside_tables)}")
            for img in images_outside_tables:
                print(f"      {img['filename']}: position ({img['x0']:.2f}, {img['y0']:.2f})")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_table_images.py <path_to_pdf>")
        print("\nSearching for test PDFs...")
        test_pdfs = list(Path("temp/test_pdfs").glob("*.pdf")) if Path("temp/test_pdfs").exists() else []
        if test_pdfs:
            print("\nFound PDFs in temp/test_pdfs/:")
            for i, pdf in enumerate(test_pdfs, 1):
                print(f"  {i}. {pdf.name}")
            print("\nTesting all found PDFs...\n")
            for pdf in test_pdfs:
                debug_table_images(str(pdf))
        else:
            print("\nNo test PDFs found. Please provide a PDF path.")
    else:
        debug_table_images(sys.argv[1])

#!/usr/bin/env python3
"""
Analyze table detection accuracy by comparing detected dimensions with actual PDF dimensions.
This script helps identify precision issues in table detection.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import fitz  # PyMuPDF
from services.vector_parser import VectorParser
from services.xml_parser.table_detector import TableDetector

def analyze_pdf_table_accuracy(pdf_path: str):
    """
    Analyze how accurately we detect table dimensions from a PDF.
    """
    print(f"\n{'='*80}")
    print(f"Analyzing: {pdf_path}")
    print(f"{'='*80}\n")
    
    # Open PDF with PyMuPDF for ground truth
    doc = fitz.open(pdf_path)
    page = doc[0]
    page_height = page.rect.height
    page_width = page.rect.width
    
    print(f"📄 Page Dimensions: {page_width:.2f} x {page_height:.2f}")
    
    # Get actual table rectangles from PDF (if any)
    # PyMuPDF can detect tables
    tables = page.find_tables()
    
    if tables:
        print(f"\n✅ PyMuPDF detected {len(tables.tables)} table(s)")
        for idx, table in enumerate(tables.tables):
            bbox = table.bbox
            print(f"\n  Table {idx + 1}:")
            print(f"    Position: ({bbox[0]:.2f}, {bbox[1]:.2f}) to ({bbox[2]:.2f}, {bbox[3]:.2f})")
            print(f"    Size: {bbox[2] - bbox[0]:.2f} x {bbox[3] - bbox[1]:.2f}")
            print(f"    Rows: {len(table.rows)}")
            print(f"    Columns: {len(table.header.cells) if table.header else 'N/A'}")
            
            # Show row heights
            if table.rows:
                print(f"\n    Row Heights:")
                for r_idx, row in enumerate(table.rows[:5]):  # First 5 rows
                    if row.cells:
                        # Cells are tuples: (x0, y0, x1, y1, text, type)
                        cell = row.cells[0]
                        height = cell[3] - cell[1]  # y1 - y0
                        print(f"      Row {r_idx + 1}: {height:.2f}px")
                if len(table.rows) > 5:
                    print(f"      ... and {len(table.rows) - 5} more rows")
            
            # Show column widths
            if table.header and table.header.cells:
                print(f"\n    Column Widths:")
                for c_idx, cell in enumerate(table.header.cells):
                    if cell:  # Check if cell is not None
                        width = cell[2] - cell[0]  # x1 - x0
                        print(f"      Column {c_idx + 1}: {width:.2f}px")
    else:
        print("\n⚠️  PyMuPDF found no tables")
    
    # Now test our current vector-based detection
    print(f"\n{'─'*80}")
    print("Testing Current Vector-Based Detection")
    print(f"{'─'*80}\n")
    
    vector_parser = VectorParser(pdf_path)
    vector_parser.parse()
    
    # Get vectors for page 1
    vectors = vector_parser.get_vectors_for_page(1, page_height)
    
    print(f"📊 Vector Analysis:")
    print(f"   Total vectors: {len(vectors)}")
    
    h_lines = [v for v in vectors if v.is_horizontal]
    v_lines = [v for v in vectors if v.is_vertical]
    rects = [v for v in vectors if v.fill and v.width > 5 and v.height > 5]
    
    print(f"   Horizontal lines: {len(h_lines)}")
    print(f"   Vertical lines: {len(v_lines)}")
    print(f"   Filled rectangles: {len(rects)}")
    
    # Detect tables using our current method
    detector = TableDetector(vectors)
    detected_tables = detector.detect([])
    
    print(f"\n🔍 Current Detection Results:")
    print(f"   Detected tables: {len(detected_tables)}")
    
    for idx, table in enumerate(detected_tables):
        print(f"\n  Table {idx + 1}:")
        print(f"    Position: ({table.rect[1]}, {table.rect[0]}) to ({table.rect[3]}, {table.rect[2]})")
        width = table.rect[3] - table.rect[1]
        height = table.rect[2] - table.rect[0]
        print(f"    Size: {width:.2f} x {height:.2f}")
        print(f"    Rows: {len(table.row_positions) - 1}")
        print(f"    Columns: {len(table.col_positions) - 1}")
        
        # Show row heights
        print(f"\n    Row Heights:")
        for r_idx in range(min(5, len(table.row_positions) - 1)):
            row_height = table.row_positions[r_idx + 1] - table.row_positions[r_idx]
            print(f"      Row {r_idx + 1}: {row_height:.2f}px")
        if len(table.row_positions) > 6:
            print(f"      ... and {len(table.row_positions) - 6} more rows")
        
        # Show column widths
        print(f"\n    Column Widths:")
        for c_idx in range(min(5, len(table.col_positions) - 1)):
            col_width = table.col_positions[c_idx + 1] - table.col_positions[c_idx]
            print(f"      Column {c_idx + 1}: {col_width:.2f}px")
        if len(table.col_positions) > 6:
            print(f"      ... and {len(table.col_positions) - 6} more columns")
    
    # Compare if both detected tables
    if tables and detected_tables:
        print(f"\n{'─'*80}")
        print("Accuracy Comparison")
        print(f"{'─'*80}\n")
        
        for idx in range(min(len(tables.tables), len(detected_tables))):
            pymupdf_table = tables.tables[idx]
            our_table = detected_tables[idx]
            
            # Compare dimensions
            pymupdf_bbox = pymupdf_table.bbox
            pymupdf_width = pymupdf_bbox[2] - pymupdf_bbox[0]
            pymupdf_height = pymupdf_bbox[3] - pymupdf_bbox[1]
            
            our_width = our_table.rect[3] - our_table.rect[1]
            our_height = our_table.rect[2] - our_table.rect[0]
            
            width_diff = abs(pymupdf_width - our_width)
            height_diff = abs(pymupdf_height - our_height)
            
            print(f"Table {idx + 1} Comparison:")
            print(f"  Width:  PyMuPDF={pymupdf_width:.2f}px, Ours={our_width:.2f}px, Diff={width_diff:.2f}px")
            print(f"  Height: PyMuPDF={pymupdf_height:.2f}px, Ours={our_height:.2f}px, Diff={height_diff:.2f}px")
            
            if width_diff > 5 or height_diff > 5:
                print(f"  ⚠️  Significant difference detected!")
            else:
                print(f"  ✅ Dimensions match closely")
    
    doc.close()
    print(f"\n{'='*80}\n")

def main():
    # Test with available PDFs
    test_pdfs_dir = Path(__file__).parent.parent / "temp" / "test_pdfs"
    
    if not test_pdfs_dir.exists():
        print(f"❌ Test PDFs directory not found: {test_pdfs_dir}")
        return
    
    pdf_files = list(test_pdfs_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"❌ No PDF files found in {test_pdfs_dir}")
        return
    
    print(f"\n🔬 Table Detection Accuracy Analysis")
    print(f"Found {len(pdf_files)} PDF(s) to analyze\n")
    
    for pdf_path in pdf_files[:3]:  # Analyze first 3 PDFs
        try:
            analyze_pdf_table_accuracy(str(pdf_path))
        except Exception as e:
            print(f"❌ Error analyzing {pdf_path.name}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()

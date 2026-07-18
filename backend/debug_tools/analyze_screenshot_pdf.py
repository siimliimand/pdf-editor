#!/usr/bin/env python3
"""
Analyze the specific PDF from the screenshot to identify table detection issues.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import fitz  # PyMuPDF
from services.vector_parser import VectorParser
from services.xml_parser.table_detector import TableDetector, detect_tables_pymupdf


def analyze_pdf_table_structure(pdf_path: str):
    """Analyze table structure in detail."""
    print(f"\n{'='*80}")
    print(f"Analyzing: {Path(pdf_path).name}")
    print(f"{'='*80}\n")
    
    # Open PDF
    doc = fitz.open(pdf_path)
    page = doc[0]
    page_height = page.rect.height
    page_width = page.rect.width
    
    print(f"📄 Page Dimensions: {page_width:.2f} x {page_height:.2f}\n")
    
    # PyMuPDF table detection
    print("🔍 PyMuPDF Table Detection:")
    print("─" * 80)
    
    tables = page.find_tables()
    
    if tables and tables.tables:
        for idx, table in enumerate(tables.tables):
            bbox = table.bbox
            print(f"\nTable {idx + 1}:")
            print(f"  Position: ({bbox[0]:.2f}, {bbox[1]:.2f}) to ({bbox[2]:.2f}, {bbox[3]:.2f})")
            print(f"  Size: {bbox[2] - bbox[0]:.2f} x {bbox[3] - bbox[1]:.2f}")
            
            # Analyze rows
            if table.rows:
                print(f"\n  Rows ({len(table.rows)}):")
                for r_idx, row in enumerate(table.rows[:10]):  # First 10 rows
                    if row.cells:
                        first_cell = row.cells[0]
                        if first_cell:
                            height = first_cell[3] - first_cell[1]
                            print(f"    Row {r_idx + 1}: height={height:.2f}px, cells={len(row.cells)}")
                            
                            # Show cell contents
                            cell_texts = []
                            for cell in row.cells:
                                if cell and len(cell) > 4:
                                    text = str(cell[4]).strip()[:30]  # First 30 chars
                                    if text:
                                        cell_texts.append(text)
                            
                            if cell_texts:
                                print(f"           Content: {' | '.join(cell_texts)}")
                
                if len(table.rows) > 10:
                    print(f"    ... and {len(table.rows) - 10} more rows")
            
            # Analyze columns
            if table.header and table.header.cells:
                print(f"\n  Columns ({len(table.header.cells)}):")
                for c_idx, cell in enumerate(table.header.cells):
                    if cell:
                        width = cell[2] - cell[0]
                        text = str(cell[4]).strip()[:30] if len(cell) > 4 else ""
                        print(f"    Column {c_idx + 1}: width={width:.2f}px, header=\"{text}\"")
    else:
        print("  No tables detected by PyMuPDF")
    
    # Vector-based detection
    print(f"\n{'─'*80}")
    print("🔍 Vector-Based Table Detection:")
    print("─" * 80)
    
    vector_parser = VectorParser(pdf_path)
    vector_parser.parse()
    vectors = vector_parser.get_vectors_for_page(1, page_height)
    
    h_lines = [v for v in vectors if v.is_horizontal]
    v_lines = [v for v in vectors if v.is_vertical]
    
    print(f"\n  Horizontal lines: {len(h_lines)}")
    print(f"  Vertical lines: {len(v_lines)}")
    
    if h_lines:
        print(f"\n  First 10 horizontal lines:")
        for idx, line in enumerate(h_lines[:10]):
            print(f"    {idx + 1}. Y={line.y0:.2f}, X={line.x0:.2f} to {line.x1:.2f}, width={line.linewidth:.2f}")
    
    if v_lines:
        print(f"\n  First 10 vertical lines:")
        for idx, line in enumerate(v_lines[:10]):
            print(f"    {idx + 1}. X={line.x0:.2f}, Y={line.y0:.2f} to {line.y1:.2f}, width={line.linewidth:.2f}")
    
    # Detect with vector method
    detector = TableDetector(vectors)
    detected_tables = detector.detect([])
    
    print(f"\n  Vector-detected tables: {len(detected_tables)}")
    
    for idx, table in enumerate(detected_tables):
        print(f"\n  Table {idx + 1}:")
        print(f"    Position: ({table.rect[1]:.2f}, {table.rect[0]:.2f}) to ({table.rect[3]:.2f}, {table.rect[2]:.2f})")
        print(f"    Rows: {len(table.row_positions) - 1}")
        print(f"    Columns: {len(table.col_positions) - 1}")
        print(f"    Cells: {len(table.cells)}")
        
        # Show row heights
        print(f"\n    Row heights:")
        for r_idx in range(min(10, len(table.row_positions) - 1)):
            height = table.row_positions[r_idx + 1] - table.row_positions[r_idx]
            print(f"      Row {r_idx + 1}: {height:.2f}px")
        
        # Show column widths
        print(f"\n    Column widths:")
        for c_idx in range(min(10, len(table.col_positions) - 1)):
            width = table.col_positions[c_idx + 1] - table.col_positions[c_idx]
            print(f"      Column {c_idx + 1}: {width:.2f}px")
    
    doc.close()


def main():
    # Look for the PDF from the screenshot
    test_pdfs_dir = Path(__file__).parent.parent / "temp" / "test_pdfs"
    
    # The PDF in the screenshot is named 2049322459.pdf
    target_pdf = test_pdfs_dir / "2049322459.pdf"
    
    if not target_pdf.exists():
        print(f"❌ PDF not found: {target_pdf}")
        print(f"\nAvailable PDFs:")
        for pdf in test_pdfs_dir.glob("*.pdf"):
            print(f"  - {pdf.name}")
        return
    
    analyze_pdf_table_structure(str(target_pdf))


if __name__ == "__main__":
    main()

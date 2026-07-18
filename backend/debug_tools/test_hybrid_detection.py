#!/usr/bin/env python3
"""
Test the full PDF to HTML conversion pipeline with hybrid table detection.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from services.pdf_service import convert_pdf_to_html


async def test_pdf_conversion(pdf_path: str):
    """Test PDF conversion with hybrid table detection."""
    print(f"\n{'='*80}")
    print(f"Testing: {Path(pdf_path).name}")
    print(f"{'='*80}\n")
    
    # Read PDF file
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    # Convert with default zoom (150%)
    print("Converting PDF to HTML (150% zoom)...")
    html_output = await convert_pdf_to_html(pdf_content, zoom_level=150.0)
    
    # Save output for inspection
    output_path = Path(__file__).parent.parent / "temp" / f"test_hybrid_{Path(pdf_path).stem}.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_output)
    
    print(f"✅ Conversion complete!")
    print(f"📄 Output saved to: {output_path}")
    print(f"📊 HTML size: {len(html_output):,} bytes")
    
    # Count tables in output
    table_count = html_output.count('<table')
    print(f"🔍 Tables detected: {table_count}")
    
    return html_output


async def main():
    test_pdfs_dir = Path(__file__).parent.parent / "temp" / "test_pdfs"
    
    if not test_pdfs_dir.exists():
        print(f"❌ Test PDFs directory not found: {test_pdfs_dir}")
        return
    
    # Test with the PDF that has tables
    test_pdf = test_pdfs_dir / "EUINEE25-95942.pdf"
    
    if not test_pdf.exists():
        print(f"❌ Test PDF not found: {test_pdf}")
        # Try first available PDF
        pdf_files = list(test_pdfs_dir.glob("*.pdf"))
        if pdf_files:
            test_pdf = pdf_files[0]
        else:
            print("❌ No PDF files found")
            return
    
    await test_pdf_conversion(str(test_pdf))


if __name__ == "__main__":
    asyncio.run(main())

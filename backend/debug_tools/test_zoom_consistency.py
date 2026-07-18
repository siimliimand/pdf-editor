#!/usr/bin/env python3
"""
Test zoom scaling consistency for tables.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from services.pdf_service import convert_pdf_to_html


async def test_zoom_consistency(pdf_path: str):
    """Test that tables scale proportionally at different zoom levels."""
    print(f"\n{'='*80}")
    print(f"Testing Zoom Consistency: {Path(pdf_path).name}")
    print(f"{'='*80}\n")
    
    # Read PDF file
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    zoom_levels = [100, 150, 200, 300]
    results = {}
    
    for zoom in zoom_levels:
        print(f"\n📊 Testing {zoom}% zoom...")
        html = await convert_pdf_to_html(pdf_content, zoom_level=float(zoom))
        
        # Extract table dimensions from HTML
        import re
        
        # Find all table elements with position and size
        table_pattern = r'<table style="position: absolute; top: ([\d.]+)px; left: ([\d.]+)px;.*?width: ([\d.]+)px;'
        matches = re.findall(table_pattern, html)
        
        if matches:
            for idx, match in enumerate(matches):
                top, left, width = float(match[0]), float(match[1]), float(match[2])
                
                if idx not in results:
                    results[idx] = {}
                
                results[idx][zoom] = {
                    'top': top,
                    'left': left,
                    'width': width
                }
                
                print(f"  Table {idx + 1}: top={top:.2f}px, left={left:.2f}px, width={width:.2f}px")
    
    # Analyze scaling ratios
    print(f"\n{'─'*80}")
    print("Scaling Ratio Analysis")
    print(f"{'─'*80}\n")
    
    for table_idx, zoom_data in results.items():
        print(f"Table {table_idx + 1}:")
        
        if 100 in zoom_data and 150 in zoom_data:
            base = zoom_data[100]
            scaled = zoom_data[150]
            
            expected_ratio = 150 / 100  # 1.5
            
            top_ratio = scaled['top'] / base['top'] if base['top'] > 0 else 0
            left_ratio = scaled['left'] / base['left'] if base['left'] > 0 else 0
            width_ratio = scaled['width'] / base['width'] if base['width'] > 0 else 0
            
            print(f"  100% → 150% (expected ratio: {expected_ratio})")
            print(f"    Top:   {base['top']:.2f}px → {scaled['top']:.2f}px (ratio: {top_ratio:.3f})")
            print(f"    Left:  {base['left']:.2f}px → {scaled['left']:.2f}px (ratio: {left_ratio:.3f})")
            print(f"    Width: {base['width']:.2f}px → {scaled['width']:.2f}px (ratio: {width_ratio:.3f})")
            
            # Check if ratios are correct
            tolerance = 0.01
            if abs(top_ratio - expected_ratio) > tolerance:
                print(f"    ⚠️  Top ratio incorrect! Expected {expected_ratio}, got {top_ratio:.3f}")
            if abs(left_ratio - expected_ratio) > tolerance:
                print(f"    ⚠️  Left ratio incorrect! Expected {expected_ratio}, got {left_ratio:.3f}")
            if abs(width_ratio - expected_ratio) > tolerance:
                print(f"    ⚠️  Width ratio incorrect! Expected {expected_ratio}, got {width_ratio:.3f}")
            
            if (abs(top_ratio - expected_ratio) <= tolerance and 
                abs(left_ratio - expected_ratio) <= tolerance and 
                abs(width_ratio - expected_ratio) <= tolerance):
                print(f"    ✅ Scaling is correct!")
        
        print()
        
        # Check 100% → 200%
        if 100 in zoom_data and 200 in zoom_data:
            base = zoom_data[100]
            scaled = zoom_data[200]
            
            expected_ratio = 200 / 100  # 2.0
            
            top_ratio = scaled['top'] / base['top'] if base['top'] > 0 else 0
            left_ratio = scaled['left'] / base['left'] if base['left'] > 0 else 0
            width_ratio = scaled['width'] / base['width'] if base['width'] > 0 else 0
            
            print(f"  100% → 200% (expected ratio: {expected_ratio})")
            print(f"    Top:   {base['top']:.2f}px → {scaled['top']:.2f}px (ratio: {top_ratio:.3f})")
            print(f"    Left:  {base['left']:.2f}px → {scaled['left']:.2f}px (ratio: {left_ratio:.3f})")
            print(f"    Width: {base['width']:.2f}px → {scaled['width']:.2f}px (ratio: {width_ratio:.3f})")
            
            # Check if ratios are correct
            tolerance = 0.01
            if abs(top_ratio - expected_ratio) > tolerance:
                print(f"    ⚠️  Top ratio incorrect! Expected {expected_ratio}, got {top_ratio:.3f}")
            if abs(left_ratio - expected_ratio) > tolerance:
                print(f"    ⚠️  Left ratio incorrect! Expected {expected_ratio}, got {left_ratio:.3f}")
            if abs(width_ratio - expected_ratio) > tolerance:
                print(f"    ⚠️  Width ratio incorrect! Expected {expected_ratio}, got {width_ratio:.3f}")
            
            if (abs(top_ratio - expected_ratio) <= tolerance and 
                abs(left_ratio - expected_ratio) <= tolerance and 
                abs(width_ratio - expected_ratio) <= tolerance):
                print(f"    ✅ Scaling is correct!")
        
        print()


async def main():
    test_pdfs_dir = Path(__file__).parent.parent / "temp" / "test_pdfs"
    test_pdf = test_pdfs_dir / "EUINEE25-95942.pdf"
    
    if not test_pdf.exists():
        pdf_files = list(test_pdfs_dir.glob("*.pdf"))
        if pdf_files:
            test_pdf = pdf_files[0]
        else:
            print("❌ No PDF files found")
            return
    
    await test_zoom_consistency(str(test_pdf))


if __name__ == "__main__":
    asyncio.run(main())

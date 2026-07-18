#!/usr/bin/env python3
"""Test script to generate HTML for a PDF and save it for inspection."""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pathlib import Path
import asyncio

async def test_pdf_html(pdf_path: str):
    """Generate HTML for a PDF file."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return
    
    print(f"Processing: {pdf_path.name}")
    
    # Read PDF file
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    # Import and call the service
    from services.pdf_service import convert_pdf_to_html
    
    try:
        html_content = await convert_pdf_to_html(pdf_content, zoom_level=100.0)
        
        # Save HTML
        output_path = Path(f"temp/{pdf_path.stem}_test.html")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ HTML saved to: {output_path}")
        print(f"  HTML length: {len(html_content)} chars")
        
        # Search for img tags
        import re
        img_tags = re.findall(r'<img[^>]+>', html_content)
        print(f"  Found {len(img_tags)} img tag(s)")
        
        for idx, img_tag in enumerate(img_tags, 1):
            print(f"\n  Image {idx}:")
            # Extract style
            style_match = re.search(r'style="([^"]+)"', img_tag)
            if style_match:
                style = style_match.group(1)
                # Parse position properties
                left_match = re.search(r'left:\s*([^;]+)', style)
                top_match = re.search(r'top:\s*([^;]+)', style)
                width_match = re.search(r'width:\s*([^;]+)', style)
                height_match = re.search(r'height:\s*([^;]+)', style)
                position_match = re.search(r'position:\s*([^;]+)', style)
                
                if position_match:
                    print(f"    position: {position_match.group(1)}")
                if left_match:
                    print(f"    left: {left_match.group(1)}")
                if top_match:
                    print(f"    top: {top_match.group(1)}")
                if width_match:
                    print(f"    width: {width_match.group(1)}")
                if height_match:
                    print(f"    height: {height_match.group(1)}")
        
        # Check if images are in table cells
        table_imgs = re.findall(r'<td[^>]*>.*?<img[^>]+>.*?</td>', html_content, re.DOTALL)
        if table_imgs:
            print(f"\n  ⚠ {len(table_imgs)} image(s) found inside table cells")
            # Show first table cell with image
            if table_imgs:
                print(f"\n  First table cell with image (truncated):")
                print(f"    {table_imgs[0][:300]}...")
        else:
            print(f"\n  ✓ No images in table cells (positioned absolutely on page)")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_pdf_html.py <path_to_pdf>")
        sys.exit(1)
    
    asyncio.run(test_pdf_html(sys.argv[1]))

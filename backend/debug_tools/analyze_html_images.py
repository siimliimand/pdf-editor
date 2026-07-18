#!/usr/bin/env python3
"""
Simple debug script to generate HTML for PDFs and extract image positioning info.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pathlib import Path
from services.pdf_service import convert_pdf_to_html
import re
import asyncio

async def analyze_html_images(pdf_path: str):
    """Generate HTML and analyze image positioning."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return
    
    print(f"\n{'='*80}")
    print(f"Analyzing: {pdf_path.name}")
    print(f"{'='*80}\n")
    
    # Generate HTML
    print("Generating HTML...")
    html_content, fonts_css, images_dict = await convert_pdf_to_html(str(pdf_path), zoom_level=100.0)
    
    # Find all img tags in the HTML
    img_pattern = r'<img\s+([^>]+)>'
    img_matches = re.findall(img_pattern, html_content)
    
    print(f"\nFound {len(img_matches)} image(s) in HTML\n")
    
    for idx, img_attrs in enumerate(img_matches, 1):
        print(f"Image {idx}:")
        print(f"  Attributes: {img_attrs[:200]}...")  # First 200 chars
        
        # Extract style attribute
        style_match = re.search(r'style="([^"]+)"', img_attrs)
        if style_match:
            style = style_match.group(1)
            print(f"\n  Style properties:")
            
            # Parse style properties
            for prop in style.split(';'):
                prop = prop.strip()
                if prop and any(key in prop for key in ['position', 'left', 'top', 'width', 'height']):
                    print(f"    {prop}")
        
        print()
    
    # Check if images are inside table cells
    table_cell_pattern = r'<td[^>]*>.*?<img[^>]+>.*?</td>'
    table_cell_matches = re.findall(table_cell_pattern, html_content, re.DOTALL)
    
    if table_cell_matches:
        print(f"\nFound {len(table_cell_matches)} image(s) inside table cells\n")
        
        for idx, cell_html in enumerate(table_cell_matches, 1):
            print(f"Table Cell {idx} with image:")
            
            # Extract td style
            td_style_match = re.search(r'<td[^>]*style="([^"]+)"', cell_html)
            if td_style_match:
                print(f"  Cell style: {td_style_match.group(1)[:150]}...")
            
            # Extract img style
            img_style_match = re.search(r'<img[^>]*style="([^"]+)"', cell_html)
            if img_style_match:
                style = img_style_match.group(1)
                print(f"\n  Image style properties:")
                for prop in style.split(';'):
                    prop = prop.strip()
                    if prop and any(key in prop for key in ['position', 'left', 'top', 'width', 'height']):
                        print(f"    {prop}")
            print()
    else:
        print("\nNo images found inside table cells (images are positioned absolutely on page)\n")
    
    # Save HTML for manual inspection
    output_path = Path(f"temp/debug_html_{pdf_path.stem}.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"<style>{fonts_css}</style>\n")
        f.write(html_content)
    
    print(f"HTML saved to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_html_images.py <path_to_pdf>")
        print("\nSearching for test PDFs...")
        test_pdfs = list(Path("temp/test_pdfs").glob("*.pdf")) if Path("temp/test_pdfs").exists() else []
        if test_pdfs:
            print("\nTesting all PDFs:")
            for pdf in test_pdfs:
                asyncio.run(analyze_html_images(str(pdf)))
        else:
            print("\nNo test PDFs found.")
    else:
        asyncio.run(analyze_html_images(sys.argv[1]))

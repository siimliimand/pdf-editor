#!/usr/bin/env python3
"""
Test script to debug top padding detection.
This will help identify if the top padding from PDF edge is being calculated correctly.
"""

import sys
from pathlib import Path
import xml.etree.ElementTree as ET

def analyze_top_padding(xml_path: str):
    """Analyze XML to see where elements start relative to the page top."""
    xml_file = Path(xml_path)
    if not xml_file.exists():
        print(f"Error: XML file not found: {xml_path}")
        return
    
    with open(xml_file, 'r', encoding='utf-8') as f:
        xml_content = f.read()
    
    root = ET.fromstring(xml_content)
    
    print(f"\n{'='*80}")
    print(f"Top Padding Analysis: {xml_file.name}")
    print(f"{'='*80}\n")
    
    for page in root.findall('page'):
        page_number = page.get('number')
        page_width = int(page.get('width'))
        page_height = int(page.get('height'))
        
        print(f"Page {page_number}: {page_width}x{page_height}px")
        print(f"{'-'*80}")
        
        # Collect all text and image elements with their positions
        elements = []
        
        for text_node in page.findall('text'):
            top = float(text_node.get('top', 0))
            left = float(text_node.get('left', 0))
            width = float(text_node.get('width', 0))
            height = float(text_node.get('height', 0))
            text = "".join(text_node.itertext()).strip()[:30]
            
            elements.append({
                'type': 'text',
                'top': top,
                'left': left,
                'width': width,
                'height': height,
                'content': text
            })
        
        for img_node in page.findall('image'):
            top = float(img_node.get('top', 0))
            left = float(img_node.get('left', 0))
            width = float(img_node.get('width', 0))
            height = float(img_node.get('height', 0))
            src = img_node.get('src', '')
            
            elements.append({
                'type': 'image',
                'top': top,
                'left': left,
                'width': width,
                'height': height,
                'content': src
            })
        
        # Sort elements by top position
        elements.sort(key=lambda e: e['top'])
        
        if elements:
            # Find first element
            first_element = elements[0]
            
            print(f"\n  First element on page:")
            print(f"    Type: {first_element['type']}")
            print(f"    Top position: {first_element['top']:.2f}px")
            print(f"    Left position: {first_element['left']:.2f}px")
            print(f"    Size: {first_element['width']:.2f}x{first_element['height']:.2f}px")
            print(f"    Content: {first_element['content']}")
            
            # This is the padding from the top edge!
            top_padding = first_element['top']
            print(f"\n  ⚠️  TOP PADDING FROM PAGE EDGE: {top_padding:.2f}px")
            
            if top_padding == 0:
                print(f"  ❌ WARNING: Top padding is 0! This might be incorrect.")
            elif top_padding > 0:
                print(f"  ✅ Top padding detected: {top_padding:.2f}px should be preserved in HTML")
            
            # Show first 10 elements for context
            print(f"\n  First 10 elements:")
            for i, elem in enumerate(elements[:10]):
                print(f"    {i+1}. [{elem['type']}] top={elem['top']:.2f}px, content={elem['content'][:30]}")
        else:
            print("  No elements found on this page")
        
        print(f"\n{'='*80}\n")

def test_with_pdf(pdf_path: str):
    """Extract XML from PDF and analyze it."""
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"Error: PDF not found: {pdf_path}")
        return
    
    print(f"Extracting XML from: {pdf_file.name}")
    
    import subprocess
    
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
        
        # Save XML for debugging
        temp_dir = Path("temp/debug")
        temp_dir.mkdir(parents=True, exist_ok=True)
        xml_file = temp_dir / "test.xml"
        
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        print(f"✅ XML saved to: {xml_file}\n")
        
        # Analyze it
        analyze_top_padding(str(xml_file))
        
    except Exception as e:
        print(f"❌ XML extraction failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Use default test PDF
        test_pdf = "temp/test_pdfs/1010054315.pdf"
        if Path(test_pdf).exists():
            print(f"Using default test PDF: {test_pdf}\n")
            test_with_pdf(test_pdf)
        else:
            print("Usage: python3 test_top_padding.py <pdf_path_or_xml_path>")
            print("\nNo default test PDF found.")
            sys.exit(1)
    else:
        input_path = sys.argv[1]
        if input_path.endswith('.xml'):
            analyze_top_padding(input_path)
        else:
            test_with_pdf(input_path)

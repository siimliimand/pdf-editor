#!/usr/bin/env python3
"""
Analyze font sizes from PDF to understand pdftohtml vs PyMuPDF font detection.
"""
import sys
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
import fitz  # PyMuPDF

def analyze_pdftohtml_fonts(pdf_path: str, zoom: float = 1.5):
    """Analyze fonts detected by pdftohtml"""
    print(f"\n{'='*80}")
    print(f"PDFTOHTML ANALYSIS (zoom={zoom})")
    print(f"{'='*80}\n")
    
    cmd = [
        "pdftohtml",
        "-xml",
        "-stdout",
        "-hidden",
        "-zoom", str(zoom),
        pdf_path
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    xml_content = result.stdout.decode('utf-8')
    
    root = ET.fromstring(xml_content)
    
    # Extract font specs
    print("Font Specifications:")
    print("-" * 80)
    fonts = {}
    for font_node in root.findall('fontspec'):
        fid = font_node.get('id')
        family = font_node.get('family', 'sans-serif')
        size = font_node.get('size', '12')
        color = font_node.get('color', '#000000')
        
        fonts[fid] = {
            'family': family,
            'size': size,
            'color': color
        }
        
        print(f"Font ID {fid}: family={family}, size={size}px, color={color}")
    
    # Extract text elements and their actual heights
    print("\n\nText Elements (first 20):")
    print("-" * 80)
    print(f"{'Text':<40} {'Font ID':<10} {'Font Size':<12} {'Height':<10} {'Width':<10}")
    print("-" * 80)
    
    count = 0
    for page in root.findall('page'):
        for text_node in page.findall('text'):
            if count >= 20:
                break
            
            text = "".join(text_node.itertext()).strip()
            if not text:
                continue
                
            font_id = text_node.get('font', '0')
            height = text_node.get('height', '0')
            width = text_node.get('width', '0')
            
            font_info = fonts.get(font_id, {})
            font_size = font_info.get('size', 'N/A')
            
            text_display = text[:37] + "..." if len(text) > 40 else text
            print(f"{text_display:<40} {font_id:<10} {font_size:<12} {height:<10} {width:<10}")
            count += 1

def analyze_pymupdf_fonts(pdf_path: str):
    """Analyze fonts detected by PyMuPDF"""
    print(f"\n{'='*80}")
    print(f"PYMUPDF ANALYSIS")
    print(f"{'='*80}\n")
    
    doc = fitz.open(pdf_path)
    
    for page_num in range(min(1, len(doc))):  # First page only
        page = doc[page_num]
        
        print(f"Page {page_num + 1}:")
        print("-" * 80)
        
        # Get text with font information
        blocks = page.get_text("dict")["blocks"]
        
        print(f"{'Text':<40} {'Font':<25} {'Size':<10} {'Flags':<10}")
        print("-" * 80)
        
        count = 0
        for block in blocks:
            if count >= 20:
                break
            if block.get("type") == 0:  # Text block
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if not text:
                            continue
                        
                        font = span.get("font", "Unknown")
                        size = span.get("size", 0)
                        flags = span.get("flags", 0)
                        
                        # Decode flags
                        is_bold = flags & 2**4
                        is_italic = flags & 2**1
                        
                        flag_str = ""
                        if is_bold:
                            flag_str += "B"
                        if is_italic:
                            flag_str += "I"
                        
                        text_display = text[:37] + "..." if len(text) > 40 else text
                        print(f"{text_display:<40} {font:<25} {size:<10.2f} {flag_str:<10}")
                        count += 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_font_sizes.py <pdf_path> [zoom]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    zoom = float(sys.argv[2]) if len(sys.argv) > 2 else 1.5
    
    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    analyze_pdftohtml_fonts(pdf_path, zoom)
    analyze_pymupdf_fonts(pdf_path)

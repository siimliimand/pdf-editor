"""
Test script to verify image position and size handling.
Run this after uploading a PDF to check if images are correctly positioned.
"""

import sys
from pathlib import Path

def analyze_html_output(html_path: str):
    """Analyze generated HTML to check image positioning and sizing."""
    html_file = Path(html_path)
    if not html_file.exists():
        print(f"Error: HTML file not found: {html_path}")
        return
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    import re
    
    # Find all img tags
    img_pattern = r'<img[^>]+>'
    images = re.findall(img_pattern, html_content)
    
    print(f"\n{'='*80}")
    print(f"Analyzing HTML: {html_file.name}")
    print(f"{'='*80}\n")
    print(f"Found {len(images)} images\n")
    
    for i, img_tag in enumerate(images, 1):
        print(f"Image {i}:")
        print(f"  Full tag: {img_tag[:100]}...")
        
        # Extract attributes
        width_match = re.search(r'width="(\d+)"', img_tag)
        height_match = re.search(r'height="(\d+)"', img_tag)
        style_match = re.search(r'style="([^"]+)"', img_tag)
        
        if width_match and height_match:
            width = width_match.group(1)
            height = height_match.group(1)
            print(f"  Dimensions: {width} x {height} px")
        
        if style_match:
            style = style_match.group(1)
            print(f"  Style: {style}")
            
            # Check for size in style
            width_style = re.search(r'width:\s*(\S+)', style)
            height_style = re.search(r'height:\s*(\S+)', style)
            if width_style and height_style:
                print(f"  CSS Size: {width_style.group(1)} x {height_style.group(1)}")
        
        # Check parent container
        img_index = html_content.find(img_tag)
        before = html_content[max(0, img_index-200):img_index]
        
        # Find parent <p> or <td>
        p_match = re.search(r'<(p|td)[^>]*style="([^"]+)"', before)
        if p_match:
            parent_tag = p_match.group(1)
            parent_style = p_match.group(2)
            print(f"  Parent <{parent_tag}> style:")
            
            # Extract positioning from parent
            margin_top = re.search(r'margin-top:\s*(\S+)', parent_style)
            padding_left = re.search(r'padding-left:\s*(\S+)', parent_style)
            
            if margin_top:
                print(f"    margin-top: {margin_top.group(1)}")
            if padding_left:
                print(f"    padding-left: {padding_left.group(1)}")
        
        print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Search for debug HTML files
        debug_html = Path("temp/debug_render.html")
        if debug_html.exists():
            print(f"Using debug HTML: {debug_html}")
            analyze_html_output(str(debug_html))
        else:
            print("Usage: python3 analyze_html.py <path_to_html>")
            print("\nNo debug HTML found. Please provide an HTML file path.")
    else:
        analyze_html_output(sys.argv[1])

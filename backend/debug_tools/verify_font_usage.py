#!/usr/bin/env python3
"""
Verify that correct fonts are being used in HTML output.
Checks that each text element has the appropriate font-family CSS.
"""
import sys
import re
from pathlib import Path
from collections import Counter

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def analyze_html_fonts_detailed(html_path: str):
    """Analyze font families in HTML output"""
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Extract font-family declarations
    font_families = re.findall(r'font-family:\s*([^;]+);', html_content)
    
    # Extract font-size declarations
    font_sizes = re.findall(r'font-size:\s*(\d+(?:\.\d+)?)px', html_content)
    
    # Extract complete style attributes for analysis
    style_patterns = re.findall(r'<span style="([^"]+)">', html_content)
    
    print("\n" + "="*80)
    print(f"DETAILED FONT ANALYSIS: {Path(html_path).name}")
    print("="*80)
    
    # Font family distribution
    if font_families:
        family_counter = Counter(font_families)
        print(f"\n📊 Font Families Used ({len(font_families)} total elements):")
        print("-"*80)
        for family, count in family_counter.most_common():
            percentage = (count / len(font_families)) * 100
            print(f"  {count:3d}x ({percentage:5.1f}%) - {family}")
    
    # Font size distribution
    if font_sizes:
        size_counter = Counter(font_sizes)
        print(f"\n📏 Font Sizes Used ({len(font_sizes)} total elements):")
        print("-"*80)
        unique_sizes = sorted(set(float(s) for s in font_sizes))
        for size in unique_sizes:
            size_str = f"{size:.1f}" if size % 1 else str(int(size))
            count = sum(1 for s in font_sizes if float(s) == size)
            percentage = (count / len(font_sizes)) * 100
            print(f"  {count:3d}x ({percentage:5.1f}%) - {size_str}px")
    
    # Sample text elements with their complete styling
    print(f"\n📝 Sample Text Elements (first 10):")
    print("-"*80)
    
    text_elements = re.findall(r'<span style="([^"]+)">([^<]+)</span>', html_content)
    for i, (style, text) in enumerate(text_elements[:10]):
        # Parse style
        font_size_match = re.search(r'font-size:\s*(\d+(?:\.\d+)?)px', style)
        font_family_match = re.search(r'font-family:\s*([^;]+)', style)
        font_weight_match = re.search(r'font-weight:\s*([^;]+)', style)
        font_style_match = re.search(r'font-style:\s*([^;]+)', style)
        color_match = re.search(r'color:\s*([^;]+)', style)
        
        text_preview = text[:40] + "..." if len(text) > 40 else text
        
        print(f"\n  [{i+1}] \"{text_preview}\"")
        if font_size_match:
            print(f"      Size: {font_size_match.group(1)}px")
        if font_family_match:
            print(f"      Family: {font_family_match.group(1)}")
        if font_weight_match:
            print(f"      Weight: {font_weight_match.group(1)}")
        if font_style_match:
            print(f"      Style: {font_style_match.group(1)}")
        if color_match:
            print(f"      Color: {color_match.group(1)}")
    
    # Verification
    print("\n" + "="*80)
    print("VERIFICATION")
    print("="*80)
    
    issues = []
    
    # Check if all text elements have font-family
    text_count = len(re.findall(r'<span[^>]*>', html_content))
    family_count = len(font_families)
    
    if text_count > family_count:
        issues.append(f"⚠️  {text_count - family_count} text elements missing font-family")
    else:
        print(f"✓ All {text_count} text elements have font-family specified")
    
    # Check if all text elements have font-size
    size_count = len(font_sizes)
    if text_count > size_count:
        issues.append(f"⚠️  {text_count - size_count} text elements missing font-size")
    else:
        print(f"✓ All {text_count} text elements have font-size specified")
    
    # Check for generic fallbacks
    has_fallbacks = all(
        any(fallback in family.lower() for fallback in ['sans-serif', 'serif', 'monospace'])
        for family in font_families
    )
    
    if has_fallbacks:
        print(f"✓ All font families have generic fallbacks")
    else:
        issues.append("⚠️  Some font families missing generic fallbacks")
    
    if issues:
        print("\n⚠️  Issues found:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\n✅ All checks passed!")

if __name__ == "__main__":
    output_path = Path(__file__).parent.parent / "temp" / "font_test_output.html"
    
    if output_path.exists():
        analyze_html_fonts_detailed(str(output_path))
    else:
        print(f"❌ Output file not found: {output_path}")
        print("\nRun this first:")
        print("  python debug_tools/test_font_detection.py temp/test_pdfs/1010054315.pdf 150")

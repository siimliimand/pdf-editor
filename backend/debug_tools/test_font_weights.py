#!/usr/bin/env python3
"""
Test improved font weight detection.
Analyzes font weights in HTML output.
"""
import sys
import re
from pathlib import Path
from collections import Counter

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def analyze_font_weights(html_path: str):
    """Analyze font weights in HTML output"""
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Extract font-weight declarations
    font_weights = re.findall(r'font-weight:\s*(\d+)', html_content)
    
    print("\n" + "="*80)
    print(f"FONT WEIGHT ANALYSIS: {Path(html_path).name}")
    print("="*80)
    
    if font_weights:
        weight_counter = Counter(font_weights)
        
        print(f"\n📊 Font Weights Distribution ({len(font_weights)} total elements):")
        print("-"*80)
        
        # Map weights to names
        weight_names = {
            '100': 'Thin/Hairline',
            '200': 'Extra Light',
            '300': 'Light',
            '400': 'Normal/Regular',
            '500': 'Medium',
            '600': 'Semi Bold',
            '700': 'Bold',
            '800': 'Extra Bold',
            '900': 'Black/Heavy'
        }
        
        for weight in sorted(weight_counter.keys(), key=int):
            count = weight_counter[weight]
            percentage = (count / len(font_weights)) * 100
            name = weight_names.get(weight, 'Unknown')
            print(f"  {weight:>3} ({name:<20}) - {count:3d} elements ({percentage:5.1f}%)")
        
        # Sample elements by weight
        print(f"\n📝 Sample Text by Weight:")
        print("-"*80)
        
        # Extract text with weights
        pattern = r'<span style="[^"]*font-weight:\s*(\d+)[^"]*">([^<]+)</span>'
        matches = re.findall(pattern, html_content)
        
        # Group by weight
        by_weight = {}
        for weight, text in matches:
            if weight not in by_weight:
                by_weight[weight] = []
            if len(by_weight[weight]) < 3:  # Max 3 samples per weight
                by_weight[weight].append(text[:50])
        
        for weight in sorted(by_weight.keys(), key=int):
            name = weight_names.get(weight, 'Unknown')
            print(f"\n  {weight} ({name}):")
            for text in by_weight[weight]:
                print(f"    - \"{text}\"")
    else:
        print("\n❌ No font-weight declarations found in HTML")

if __name__ == "__main__":
    output_path = Path(__file__).parent.parent / "temp" / "font_test_output.html"
    
    if output_path.exists():
        analyze_font_weights(str(output_path))
    else:
        print(f"❌ Output file not found: {output_path}")
        print("\nRun this first:")
        print("  python debug_tools/test_font_detection.py temp/test_pdfs/1010054315.pdf 150")

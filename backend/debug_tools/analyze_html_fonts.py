#!/usr/bin/env python3
"""
Visual comparison of font sizes before and after the improvement.
This script shows the difference in font detection.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def analyze_html_fonts(html_path: str):
    """Analyze font sizes in an HTML file"""
    import re
    
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Extract font sizes
    font_sizes = re.findall(r'font-size:\s*(\d+(?:\.\d+)?)px', html_content)
    
    if font_sizes:
        # Convert to floats and get unique sizes
        unique_sizes = sorted(set(float(s) for s in font_sizes))
        
        print(f"\n📊 Font Size Analysis: {Path(html_path).name}")
        print("="*60)
        print(f"Total text elements: {len(font_sizes)}")
        print(f"Unique font sizes: {len(unique_sizes)}")
        print("\nFont sizes (px):")
        for size in unique_sizes:
            count = font_sizes.count(str(size)) + font_sizes.count(f"{size:.1f}")
            print(f"  {size:6.1f}px - used {count:3d} times")
        
        # Calculate statistics
        sizes_float = [float(s) for s in font_sizes]
        avg_size = sum(sizes_float) / len(sizes_float)
        min_size = min(sizes_float)
        max_size = max(sizes_float)
        
        print(f"\nStatistics:")
        print(f"  Average: {avg_size:.1f}px")
        print(f"  Range: {min_size:.1f}px - {max_size:.1f}px")
        print(f"  Ratio: {max_size/min_size:.2f}x")
    else:
        print(f"\n❌ No font sizes found in {html_path}")

if __name__ == "__main__":
    output_path = Path(__file__).parent.parent / "temp" / "font_test_output.html"
    
    if output_path.exists():
        analyze_html_fonts(str(output_path))
    else:
        print(f"❌ Output file not found: {output_path}")
        print("\nRun this first:")
        print("  python debug_tools/test_font_detection.py temp/test_pdfs/2049322459.pdf 150")

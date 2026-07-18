"""
Test font sizes after removing DPI conversion
"""
import sys
import asyncio
from pathlib import Path
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.pdf_service import convert_pdf_to_html


async def test_sizes(pdf_path: str, zoom: float = 150.0):
    """Test the font sizes in HTML output"""
    
    print(f"\n{'='*100}")
    print(f"FONT SIZE TEST (After removing DPI conversion)")
    print(f"PDF: {Path(pdf_path).name}")
    print(f"Zoom: {zoom}%")
    print(f"{'='*100}\n")
    
    # Read PDF
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    # Convert to HTML
    html_content = await convert_pdf_to_html(pdf_content, zoom)
    
    # Target texts
    target_texts = [
        "SeoWeb OÜ",
        "Reg nr: 12629973",
        "Staadioni 8, 70",
    ]
    
    print("📝 Font Sizes in HTML Output:")
    print("-" * 100)
    
    for target in target_texts:
        pattern = rf'<span style="([^"]+)">[^<]*{re.escape(target)}[^<]*</span>'
        matches = re.findall(pattern, html_content)
        
        if matches:
            style = matches[0]
            size_match = re.search(r'font-size:\s*(\d+(?:\.\d+)?)px', style)
            
            if size_match:
                font_size = float(size_match.group(1))
                print(f"{target:<30} {font_size:.2f} px")
    
    # Expected values (without DPI conversion)
    print(f"\n📐 Expected Sizes (pt × zoom_factor):")
    print("-" * 100)
    
    expected = {
        "SeoWeb OÜ": 20.20 * 1.5,  # 30.30 px
        "Reg nr: 12629973": 12.80 * 1.5,  # 19.20 px
        "Staadioni 8, 70": 12.80 * 1.5,  # 19.20 px
    }
    
    for text, expected_size in expected.items():
        print(f"{text:<30} {expected_size:.2f} px")
    
    # Comparison
    print(f"\n{'='*100}")
    print(f"COMPARISON")
    print(f"{'='*100}\n")
    
    print(f"{'Text':<35} {'Expected':<15} {'Actual':<15} {'Match'}")
    print("-" * 100)
    
    all_match = True
    for target in target_texts:
        pattern = rf'<span style="([^"]+)">[^<]*{re.escape(target)}[^<]*</span>'
        matches = re.findall(pattern, html_content)
        
        if matches:
            style = matches[0]
            size_match = re.search(r'font-size:\s*(\d+(?:\.\d+)?)px', style)
            
            if size_match:
                actual = float(size_match.group(1))
                expected_val = expected[target]
                diff = abs(actual - expected_val)
                match = "✅" if diff < 0.5 else "❌"
                
                if diff >= 0.5:
                    all_match = False
                
                print(f"{target:<35} {expected_val:<15.2f} {actual:<15.2f} {match}")
    
    print(f"\n{'='*100}")
    if all_match:
        print("✅ All font sizes match! Text should now be the same size as in PDF.")
    else:
        print("❌ Font sizes don't match. Further investigation needed.")
    print(f"{'='*100}\n")


if __name__ == "__main__":
    pdf_path = "temp/test_pdfs/1010054315.pdf"
    
    if Path(pdf_path).exists():
        asyncio.run(test_sizes(pdf_path, zoom=150.0))
    else:
        print(f"❌ PDF not found: {pdf_path}")

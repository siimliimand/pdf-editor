
import sys
import os
from pathlib import Path
from PIL import Image

# Add backend to path to import services
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from services.image_extractor_pymupdf import ImageExtractorPyMuPDF
except ImportError:
    print("Could not import ImageExtractorPyMuPDF. Ensure backend dependencies are installed.")
    sys.exit(1)

TEST_PDF_DIR = Path("temp/test_pdfs")
OUTPUT_DIR = Path("temp/debug_output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def analyze_image(img_path):
    try:
        with Image.open(img_path) as img:
            print(f"  Image: {img_path.name}")
            print(f"  Mode: {img.mode}")
            print(f"  Size: {img.size}")
            
            # Check corners for transparency
            width, height = img.size
            corners = [
                (0, 0), (width-1, 0),
                (0, height-1), (width-1, height-1)
            ]
            
            transparent_pixels = 0
            white_pixels = 0
            black_pixels = 0
            
            for x, y in corners:
                try:
                    p = img.getpixel((x, y))
                    if isinstance(p, tuple) and len(p) == 4:
                        if p[3] == 0:
                            transparent_pixels += 1
                        elif p[0] > 240 and p[1] > 240 and p[2] > 240:
                            white_pixels += 1
                        elif p[0] < 10 and p[1] < 10 and p[2] < 10:
                            black_pixels += 1
                except Exception:
                    pass
            
            if transparent_pixels > 0:
                print(f"  SUCCESS: {transparent_pixels} transparent corners detected.")
            elif white_pixels > 0:
                print(f"  Note: {white_pixels} white corners detected (Transparency lost?).")
            elif black_pixels > 0:
                print(f"  WARNING: {black_pixels} black corners detected!")
            else:
                print("  Note: No clear background detected in corners.")
                
    except Exception as e:
        print(f"Failed to analyze {img_path}: {e}")

def run_test():
    files = list(TEST_PDF_DIR.glob("*.pdf"))
    if not files:
        print("No test PDFs found in", TEST_PDF_DIR)
        return

    print(f"Testing image extraction on {len(files)} PDFs...")
    
    for pdf_file in files:
        print(f"\nProcessing {pdf_file.name}...")
        
        # Extract using current service logic
        out_dir = OUTPUT_DIR / pdf_file.stem
        extractor = ImageExtractorPyMuPDF(str(pdf_file), out_dir)
        extractor.extract()
        
        if extractor.images:
            for pagenum, images in extractor.images.items():
                for img_info in images:
                    filename = img_info[0]
                    img_path = out_dir / filename
                    analyze_image(img_path)
        else:
            print("  No images extracted.")

if __name__ == "__main__":
    run_test()

#!/usr/bin/env python3
"""
Test PyMuPDF extractor on the problematic PDFs
"""

import sys
import os
# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pathlib import Path
from services.image_extractor_pymupdf import ImageExtractorPyMuPDF

def test_pymupdf(pdf_path):
    print(f"\n{'='*60}")
    print(f"Testing PyMuPDF on: {pdf_path}")
    print('='*60)
    
    output_dir = Path("temp_pymupdf_output")
    output_dir.mkdir(exist_ok=True)
    
    try:
        extractor = ImageExtractorPyMuPDF(str(pdf_path), output_dir)
        extractor.extract()
        
        print(f"\n✓ Extraction completed!")
        print(f"Found images on {len(extractor.images)} page(s)")
        
        for page_num, images in extractor.images.items():
            print(f"\nPage {page_num}: {len(images)} image(s)")
            for filename, x0, y0, x1, y1, width, height in images:
                print(f"  - {filename}: {width}x{height} at ({x0:.1f}, {y0:.1f})")
                
                # Check if file exists and analyze
                img_path = output_dir / filename
                if img_path.exists():
                    from PIL import Image
                    with Image.open(img_path) as img:
                        print(f"    Mode: {img.mode}, Size: {img.size}")
                        
                        # Check brightness
                        if img.mode in ('RGB', 'RGBA'):
                            import random
                            samples = []
                            for _ in range(20):
                                x = random.randint(0, img.size[0] - 1)
                                y = random.randint(0, img.size[1] - 1)
                                pixel = img.getpixel((x, y))
                                brightness = sum(pixel[:3]) / 3 if img.mode == 'RGBA' else sum(pixel) / 3
                                samples.append(brightness)
                            
                            avg = sum(samples) / len(samples)
                            print(f"    Avg brightness (RGB): {avg:.1f}/255", end="")
                            
                            if img.mode == 'RGBA':
                                alpha_samples = []
                                for _ in range(20):
                                    x = random.randint(0, img.size[0] - 1)
                                    y = random.randint(0, img.size[1] - 1)
                                    pixel = img.getpixel((x, y))
                                    alpha_samples.append(pixel[3])
                                avg_alpha = sum(alpha_samples) / len(alpha_samples)
                                print(f", Avg Alpha: {avg_alpha:.1f}/255")
                                
                                if avg < 50 and avg_alpha > 200:
                                    print(" ⚠️  VERY DARK OPAQUE - REAL BLACK BACKGROUND!")
                                elif avg < 50 and avg_alpha < 50:
                                    print(" ℹ️  Transparent (looks black in raw RGB checks)")
                                elif avg > 200:
                                    print(" ✓ Bright - looks good!")
                            else:
                                print("")
                                if avg < 50:
                                    print(" ⚠️  VERY DARK - BLACK BACKGROUND!")
                else:
                    print(f"    ✗ File not found!")
        
        print(f"\nImages saved to: {output_dir}")
        print(f"Please check the images to verify they don't have black backgrounds.")
        return True
        
    except Exception as e:
        print(f"\n✗ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    pdf1 = Path("temp/test_pdfs/1010054315.pdf")
    pdf2 = Path("temp/test_pdfs/1282161800020.pdf")
    
    success1 = test_pymupdf(pdf1) if pdf1.exists() else False
    success2 = test_pymupdf(pdf2) if pdf2.exists() else False
    
    print(f"\n{'='*60}")
    print(f"PyMuPDF Test Results:")
    print(f"  {pdf1.name}: {'✓ SUCCESS' if success1 else '✗ FAILED'}")
    print(f"  {pdf2.name}: {'✓ SUCCESS' if success2 else '✗ FAILED'}")
    print('='*60)
    
    if success1 and success2:
        print("\n✓ PyMuPDF successfully extracted images from both PDFs!")
        print("  To use PyMuPDF in production, update pdf_service.py:")
        print("  Change: from .image_extractor import ImageExtractor")
        print("  To:     from .image_extractor_pymupdf import ImageExtractorPyMuPDF as ImageExtractor")

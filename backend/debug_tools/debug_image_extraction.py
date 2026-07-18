#!/usr/bin/env python3
"""
Debug script to test image extraction and identify color space issues.

Usage:
    python debug_image_extraction.py <path_to_pdf>

This script will:
1. Extract images using the current ImageExtractor
2. Show detailed information about each image
3. Help identify CMYK conversion issues
"""

import sys
import os
# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pathlib import Path
from services.image_extractor import ImageExtractor
from PIL import Image
import io


def analyze_image(img_path: Path):
    """Analyze an extracted image and print detailed information."""
    try:
        with Image.open(img_path) as img:
            print(f"\n  Image: {img_path.name}")
            print(f"    Mode: {img.mode}")
            print(f"    Size: {img.size}")
            print(f"    Format: {img.format}")
            
            # Check for ICC profile
            has_icc = 'icc_profile' in img.info
            print(f"    Has ICC Profile: {has_icc}")
            
            # Calculate average brightness
            if img.mode in ('RGB', 'RGBA'):
                # Sample pixels to check brightness
                width, height = img.size
                sample_points = [
                    (0, 0),  # Top-left
                    (width-1, 0),  # Top-right
                    (0, height-1),  # Bottom-left
                    (width-1, height-1),  # Bottom-right
                    (width//2, height//2),  # Center
                ]
                
                brightnesses = []
                for x, y in sample_points:
                    pixel = img.getpixel((x, y))
                    if img.mode == 'RGB':
                        brightness = sum(pixel) / 3
                    else:  # RGBA
                        brightness = sum(pixel[:3]) / 3
                    brightnesses.append(brightness)
                
                avg_brightness = sum(brightnesses) / len(brightnesses)
                print(f"    Average Brightness (sample): {avg_brightness:.1f}/255")
                
                if avg_brightness < 50:
                    print(f"    ⚠️  WARNING: Image appears very dark (possibly inverted)")
                elif avg_brightness > 200:
                    print(f"    ✓  Image appears bright (likely correct)")
                else:
                    print(f"    ℹ️  Image has medium brightness")
            
    except Exception as e:
        print(f"  Error analyzing {img_path.name}: {e}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_image_extraction.py <path_to_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    print(f"Analyzing PDF: {pdf_path}")
    print("=" * 60)
    
    # Create temporary output directory
    output_dir = Path("temp_debug_images")
    output_dir.mkdir(exist_ok=True)
    
    try:
        # Extract images
        print("\nExtracting images...")
        extractor = ImageExtractor(pdf_path, output_dir)
        extractor.extract()
        
        # Analyze results
        print(f"\nFound images on {len(extractor.images)} page(s)")
        
        for page_num, images in extractor.images.items():
            print(f"\nPage {page_num}: {len(images)} image(s)")
            
            for img_data in images:
                filename, x0, y0, x1, y1, width, height = img_data
                print(f"\n  Position: ({x0:.1f}, {y0:.1f}) to ({x1:.1f}, {y1:.1f})")
                print(f"  Dimensions: {width}x{height}")
                
                img_path = output_dir / filename
                if img_path.exists():
                    analyze_image(img_path)
        
        print("\n" + "=" * 60)
        print(f"Extracted images saved to: {output_dir}")
        print("Review the images to check for black backgrounds or color issues.")
        
    except Exception as e:
        print(f"\nError during extraction: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

from pathlib import Path
from typing import Tuple, Optional
from PIL import Image
import base64

def process_image(img_path: Path, zoom_factor: float = 1.0) -> Tuple[int, int]:
    """
    Process image to ensure correct color space (RGB/RGBA) and return natural dimensions.
    Fixes CMYK inversion and removes artificial black backgrounds from masked images.
    
    Args:
        img_path: Path to the image file
        zoom_factor: PDF zoom factor (for diagnostic logging)
    """
    try:
        with Image.open(img_path) as img:
            needs_save = False
            original_mode = img.mode
            
            
            # 1. Handle Color Modes & Convert to RGBA (for transparency support)
            if img.mode != 'RGBA':
                if img.mode == 'CMYK':
                    img = img.convert('RGB') # CMYK -> RGB first
                img = img.convert('RGBA')
                needs_save = True
            
            width, height = img.size
            if width > 10 and height > 10:
                # Heuristic: Check borders for black background
                # Check 10 points on each side
                is_black_bg = True
                
                check_points = []
                # Top & Bottom
                for x in range(0, width, max(1, width // 10)):
                    check_points.append((x, 0))
                    check_points.append((x, height - 1))
                # Left & Right
                for y in range(0, height, max(1, height // 10)):
                    check_points.append((0, y))
                    check_points.append((width - 1, y))
                    
                # Threshold for "Black"
                threshold = 50
                
                black_points = 0
                total_points = 0
                transparent_points = 0
                semi_transparent_points = 0
                
                # Sample some pixels for detailed analysis
                sample_pixels = []
                
                for x, y in check_points:
                    if x >= width or y >= height: continue
                    p = img.getpixel((x, y))
                    # p is (R,G,B,A)
                    
                    # Track transparency
                    if p[3] == 0:
                        transparent_points += 1
                    elif p[3] < 255:
                        semi_transparent_points += 1
                    
                    # Track black pixels
                    if p[0] < threshold and p[1] < threshold and p[2] < threshold:
                        black_points += 1
                        if len(sample_pixels) < 5:
                            sample_pixels.append(f"({p[0]},{p[1]},{p[2]},α={p[3]})")
                    
                    total_points += 1
                
                black_percentage = (black_points / total_points) if total_points > 0 else 0
                transparent_percentage = (transparent_points / total_points) if total_points > 0 else 0
                
                # If > 80% of border points are black, assume black background
                if total_points > 0 and black_percentage > 0.8:
                    # Make detecting black pixels transparent
                    datas = img.getdata()
                    new_data = []
                    removed_count = 0
                    for item in datas:
                        # More aggressive: also check alpha channel
                        # If pixel is black AND not already transparent
                        if item[0] < threshold and item[1] < threshold and item[2] < threshold and item[3] > 0:
                            new_data.append((0, 0, 0, 0))
                            removed_count += 1
                        else:
                            new_data.append(item)
                    
                    img.putdata(new_data)
                    needs_save = True
                
            if needs_save:
                # Save optimized as PNG to support transparency
                img.save(img_path, "PNG", quality=95)
                
            return width, height
    except Exception as e:
        return 0, 0

def get_image_data(src: str, images_dir: Optional[Path]) -> str:
    if not images_dir or not src:
        return ""
    
    img_path = images_dir / src
    if img_path.exists():
        try:
            # Images are already processed during extraction (see image_extractor_pymupdf.py)
            # No need to process again here
            
            with open(img_path, "rb") as f:
                data = base64.b64encode(f.read()).decode('utf-8')
                # Determine mime type based on extension
                ext = img_path.suffix.lower()
                mime = 'image/jpeg' # default
                if ext == '.png': mime = 'image/png'
                elif ext == '.gif': mime = 'image/gif'
                elif ext == '.bmp': mime = 'image/bmp'
                
                return f"data:{mime};base64,{data}"
        except Exception:
            return ""
    return ""

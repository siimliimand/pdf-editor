from PIL import Image
import io
import random

def cmyk_to_rgb(img: Image.Image) -> Image.Image:
    """
    Convert CMYK image to RGB with proper color handling.
    Tries multiple approaches to avoid color inversion issues.
    """
    try:
        # Approach 1: Try using ImageCms for proper color profile conversion
        try:
            from PIL import ImageCms
            
            # Try to get embedded ICC profile
            if 'icc_profile' in img.info:
                # Use embedded profile
                input_profile = ImageCms.ImageCmsProfile(io.BytesIO(img.info['icc_profile']))
                output_profile = ImageCms.createProfile('sRGB')
                img = ImageCms.profileToProfile(img, input_profile, output_profile, outputMode='RGB')
                return img
        except Exception as e:
        
        # Approach 2: Mathematical CMYK to RGB conversion (inverted formula for PDF CMYK)
        # PDF CMYK often uses inverted values, so we need to invert before conversion
        try:
            import numpy as np
            
            # Convert to numpy array for faster processing
            cmyk_array = np.array(img, dtype=np.float32) / 255.0
            
            # PDF CMYK is often inverted, so invert it first
            # C, M, Y, K values
            c = 1.0 - cmyk_array[:, :, 0]
            m = 1.0 - cmyk_array[:, :, 1]
            y = 1.0 - cmyk_array[:, :, 2]
            k = 1.0 - cmyk_array[:, :, 3]
            
            # CMYK to RGB conversion formula
            r = 255 * (1.0 - c) * (1.0 - k)
            g = 255 * (1.0 - m) * (1.0 - k)
            b = 255 * (1.0 - y) * (1.0 - k)
            
            # Stack and convert back to uint8
            rgb_array = np.stack([r, g, b], axis=2).astype(np.uint8)
            img = Image.fromarray(rgb_array, mode='RGB')
            return img
        except Exception as e:
        
        # Approach 3: Fallback to PIL's default conversion with inversion check
        img_rgb = img.convert('RGB')
        
        # Check if image appears inverted (heuristic: if most pixels are very dark)
        if is_image_inverted(img_rgb):
            # Invert the image
            from PIL import ImageOps
            img_rgb = ImageOps.invert(img_rgb)
        
        return img_rgb
        
    except Exception as e:
        # Last resort: just use PIL's default
        return img.convert('RGB')

def is_image_inverted(img: Image.Image) -> bool:
    """
    Heuristic to detect if an RGB image appears inverted (too dark).
    Samples pixels and checks average brightness.
    """
    try:
        # Sample 100 random pixels
        width, height = img.size
        sample_size = min(100, width * height)
        
        total_brightness = 0
        for _ in range(sample_size):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            pixel = img.getpixel((x, y))
            # Calculate brightness (average of RGB)
            brightness = sum(pixel) / 3
            total_brightness += brightness
        
        avg_brightness = total_brightness / sample_size
        
        # If average brightness is very low (< 50 out of 255), likely inverted
        return avg_brightness < 50
    except:
        return False

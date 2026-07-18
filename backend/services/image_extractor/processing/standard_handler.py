import io
from PIL import Image
from typing import Optional
from ..converters import cmyk_to_rgb

def handle_standard_image(width: int, height: int, data: bytes, mode: str, bits_per_component: int) -> Optional[bytes]:
    # Calculate expected data size for non-indexed images
    if mode == 'L':
        expected_size = width * height * (bits_per_component // 8)
    elif mode == 'RGB':
        expected_size = width * height * 3 * (bits_per_component // 8)
    elif mode == 'CMYK':
        expected_size = width * height * 4 * (bits_per_component // 8)
    else:
        expected_size = len(data)
        
    if len(data) < expected_size:
        return None
        
    try:
        # Non-indexed image
        img = Image.frombytes(mode, (width, height), data[:expected_size])
        
        # Convert CMYK to RGB with proper handling
        if img.mode == 'CMYK':
            img = cmyk_to_rgb(img)
            
        # Save as PNG
        output = io.BytesIO()
        img.save(output, format='PNG')
        return output.getvalue()
        
    except Exception as e:
        return None

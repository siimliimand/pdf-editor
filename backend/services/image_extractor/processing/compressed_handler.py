import io
from PIL import Image
from typing import Optional
from ..converters import cmyk_to_rgb

def try_handle_compressed(data: bytes, filter_name: str) -> Optional[bytes]:
    if 'DCTDecode' in filter_name or 'JPXDecode' in filter_name:
        try:
            img = Image.open(io.BytesIO(data))
            # Convert CMYK to RGB with proper handling
            if img.mode == 'CMYK':
                img = cmyk_to_rgb(img)
            elif img.mode == 'P':
                img = img.convert('RGBA')
            
            # Save as PNG
            output = io.BytesIO()
            img.save(output, format='PNG')
            return output.getvalue()
        except Exception as e:
            pass
    return None

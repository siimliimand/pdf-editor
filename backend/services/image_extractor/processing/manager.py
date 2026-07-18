from typing import Optional
from pdfminer.layout import LTImage
from .stream_utils import get_image_dimensions, get_stream_data, get_filters, get_colorspace_info
from .compressed_handler import try_handle_compressed
from .indexed_handler import handle_indexed_image
from .standard_handler import handle_standard_image

def extract_image_data(image: LTImage) -> Optional[bytes]:
    """
    Extract image data from LTImage and convert to PNG with correct colors.
    Handles compressed images (FlateDecode, DCTDecode, etc.) and fixes CMYK inversion.
    """
    try:
        stream = image.stream
        
        # Get image properties
        width, height = get_image_dimensions(stream)
        
        if width <= 0 or height <= 0:
            return None
            
        # Get decompressed data (handles FlateDecode, etc.)
        data = get_stream_data(stream)
        
        # Check filter type
        filter_name = get_filters(stream)
        
        # Try to handle as compressed image first (DCT/JPX)
        compressed_result = try_handle_compressed(data, filter_name)
        if compressed_result:
            return compressed_result
            
        # Determine colorspace and appropriate handler
        mode, bits_per_component, is_indexed, colorspace = get_colorspace_info(stream)
        
        if is_indexed:
            return handle_indexed_image(width, height, data, bits_per_component, colorspace)
        else:
            return handle_standard_image(width, height, data, mode, bits_per_component)
            
    except Exception as e:
        return None

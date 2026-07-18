from typing import Any, Tuple, Optional, Union

def get_image_dimensions(stream: Any) -> Tuple[int, int]:
    width = int(stream.get('Width', 0))
    height = int(stream.get('Height', 0))
    return width, height

def get_stream_data(stream: Any) -> bytes:
    try:
        return stream.get_data()
    except:
        return stream.get_rawdata()

def get_filters(stream: Any) -> str:
    filters = stream.get('Filter')
    if not filters:
        return ""
    if isinstance(filters, list):
        return ' '.join([f.name if hasattr(f, 'name') else str(f) for f in filters])
    return filters.name if hasattr(filters, 'name') else str(filters)

def get_colorspace_info(stream: Any) -> Tuple[str, int, bool, Any]:
    colorspace = stream.get('ColorSpace')
    mode = 'RGB'
    bits_per_component = int(stream.get('BitsPerComponent', 8))
    is_indexed = False
    
    if colorspace:
        if isinstance(colorspace, list):
            cs_name = colorspace[0].name if hasattr(colorspace[0], 'name') else str(colorspace[0])
        else:
            cs_name = colorspace.name if hasattr(colorspace, 'name') else str(colorspace)
        
        if 'DeviceGray' in cs_name or 'CalGray' in cs_name:
            mode = 'L'
        elif 'DeviceCMYK' in cs_name:
            mode = 'CMYK'
        elif 'DeviceRGB' in cs_name or 'CalRGB' in cs_name:
            mode = 'RGB'
        elif 'Indexed' in cs_name:
            is_indexed = True
            mode = 'P'
            
    return mode, bits_per_component, is_indexed, colorspace

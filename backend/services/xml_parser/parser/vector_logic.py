from typing import List, Tuple
from ...vector_parser import VectorElement

def process_vectors_for_page(
    page_vectors: List[VectorElement], 
    xml_scale: float, 
    output_scale: float, 
    page_height: float,
    xml_height: float
) -> Tuple[List[VectorElement], List[VectorElement]]:
    """
    Process vectors for a page to produce:
    1. vectors_1x: Vectors at 1x scale (unscaled from PDF coords) for table detection.
    2. converted_vectors: Vectors scaled and flipped for final rendering in HTML.
    
    Args:
        page_vectors: List of VectorElements from the PDF.
        xml_scale: The scale factor of the XML (e.g. 3.0).
        output_scale: Additional scaling factor for output (e.g. 1.66).
        page_height: The target height of the page in HTML pixels.
        xml_height: The original height from XML (before output_scale).
    
    Returns:
        Tuple[List[VectorElement], List[VectorElement]]: (vectors_1x, converted_vectors)
    """
    total_zoom = xml_scale * output_scale
    height_1x = xml_height / xml_scale
    
    converted_vectors = [] # Target scale
    vectors_1x = []        # 1x scale
    
    for v in page_vectors:
            # 1x conversion (Flip Y)
            y0_1x = height_1x - v.y1
            y1_1x = height_1x - v.y0
            
            vectors_1x.append(VectorElement(
                x0=v.x0, y0=y0_1x, x1=v.x1, y1=y1_1x,
                linewidth=v.linewidth, stroke=v.stroke, fill=v.fill,
                color=v.color, dash=v.dash
            ))
    
            # Target conversion (Scale & Flip Y)
            new_y0 = page_height - (v.y1 * total_zoom)
            new_y1 = page_height - (v.y0 * total_zoom)
            
            converted_vectors.append(VectorElement(
                x0=v.x0 * total_zoom, 
                y0=new_y0, 
                x1=v.x1 * total_zoom, 
                y1=new_y1,
                linewidth=v.linewidth * total_zoom, 
                stroke=v.stroke, fill=v.fill,
                color=v.color, dash=v.dash
            ))
            
    return vectors_1x, converted_vectors

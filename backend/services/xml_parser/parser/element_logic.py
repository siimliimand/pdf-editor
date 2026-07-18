import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path

from ..models import FontSpec, TextElement, TableDefinition
from ..extractors import extract_elements

def extract_and_scale_elements(
    page: ET.Element,
    fonts: Dict[str, FontSpec],
    page_extracted_images: List[Tuple],
    images_dir: Optional[Path],
    xml_h: float,
    xml_scale: float,
    output_scale: float,
    font_extractor = None,
    page_number: int = 1,
    font_family_mapping: Dict[str, str] = None
) -> List[Any]:
    
    # Extract Elements
    # Pass xml_scale to scale PyMuPDF coordinates to match XML scale.
    # Then we will apply output_scale to the result.
    elements = extract_elements(
        page, fonts, images_dir, page_extracted_images, int(xml_h), xml_scale, font_extractor, page_number, font_family_mapping
    )
    
    # Apply output_scale to all extracted elements (for zoom > 300%)
    if output_scale != 1.0:
        for el in elements:
            el.top *= output_scale
            el.left *= output_scale
            el.width *= output_scale
            el.height *= output_scale
            # Scale font_size by output_scale for zoom > 300%
            # This ensures fonts continue to scale at high zoom levels
            if isinstance(el, TextElement):
                if hasattr(el, 'font_size'):
                    el.font_size *= output_scale
            if isinstance(el, TableDefinition): 
                el.rect = [x * output_scale for x in el.rect]
                
    return elements

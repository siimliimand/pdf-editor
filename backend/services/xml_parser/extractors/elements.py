import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from ..models import FontSpec, Element
from .image_matcher import extract_image_elements
from .text_parser import extract_text_elements

def extract_elements(
    page_node: ET.Element, 
    fonts: Dict[str, FontSpec], 
    images_dir: Optional[Path] = None, 
    extracted_images: List[Tuple] = None, 
    page_height: int = 0, 
    zoom_factor: float = 1.0,
    font_extractor = None,
    page_number: int = 1,
    font_family_mapping: Dict[str, str] = None
) -> List[Element]:
    """
    Main entry point for extracting elements (images and text) from a PDF page XML node.
    Orchestrates the extraction process by delegating to specific extractors.
    """
    elements: List[Element] = []
    
    # Extract Images
    # Delegates to image_matcher to handle coordinate reconciliation between PyMuPDF and pdftohtml
    image_elements = extract_image_elements(
        page_node=page_node, 
        extracted_images=extracted_images, 
        page_height=page_height, 
        zoom_factor=zoom_factor
    )
    elements.extend(image_elements)

    # Extract Text
    # Delegates to text_parser to handle DFC metadata cleaning and font mapping
    text_elements = extract_text_elements(
        page_node=page_node, 
        fonts=fonts,
        font_extractor=font_extractor,
        page_number=page_number,
        zoom_factor=zoom_factor,
        font_family_mapping=font_family_mapping
    )
    elements.extend(text_elements)
                
    return elements

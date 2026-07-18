import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple, Union
from pathlib import Path

from ...vector_parser import VectorElement
from ..models import FontSpec
from ..extractors import extract_fonts
from .page_logic import process_page

class XMLToHTMLParser:
    def __init__(self, xml_content: str, images_dir: Optional[Path] = None, vectors: Dict[int, List[VectorElement]] = None, extracted_images: Dict[int, List[Tuple]] = None, xml_scale: float = 1.0, output_scale: float = 1.0, font_extractor = None, pdf_path: Optional[str] = None, font_family_mapping: Dict[str, str] = None):
        self.root = ET.fromstring(xml_content)
        self.images_dir = images_dir
        self.vectors = vectors or {}
        self.extracted_images = extracted_images or {}
        self.fonts: Dict[str, FontSpec] = {}
        self.xml_scale = xml_scale       # Scale of the input XML (e.g. 3.0)
        self.output_scale = output_scale # Additional scaling needed (e.g. 1.66 to get from 3.0 to 5.0)
        self.font_extractor = font_extractor  # PyMuPDF font extractor for accurate font sizes
        self.pdf_path = pdf_path  # PDF file path for PyMuPDF table detection
        self.font_family_mapping = font_family_mapping or {} # Mapping from PDF font names to CSS font families

    def parse(self) -> str:
        # Extract fonts primarily
        self.fonts = extract_fonts(self.root, self.font_family_mapping)

        html_parts = []
        
        for page in self.root.findall('page'):
            page_number = page.get('number')
            page_vectors = self.vectors.get(int(page_number), [])
            page_images = self.extracted_images.get(int(page_number), [])
            
            page_html = process_page(
                page=page,
                fonts=self.fonts,
                page_vectors=page_vectors,
                page_extracted_images=page_images,
                images_dir=self.images_dir,
                xml_scale=self.xml_scale,
                output_scale=self.output_scale,
                font_extractor=self.font_extractor,
                page_number=int(page_number),
                pdf_path=self.pdf_path,
                font_family_mapping=self.font_family_mapping
            )
            html_parts.append(page_html)

        return "\n".join(html_parts)

def parse_xml_to_html(xml_content: str, images_dir: Optional[Path] = None, vectors: Dict[int, List[VectorElement]] = None, extracted_images: Dict[int, List[Tuple]] = None, xml_scale: float = 1.0, output_scale: float = 1.0, font_extractor = None, pdf_path: Optional[str] = None, font_family_mapping: Dict[str, str] = None) -> str:
    parser = XMLToHTMLParser(xml_content, images_dir, vectors, extracted_images, xml_scale, output_scale, font_extractor, pdf_path, font_family_mapping)
    return parser.parse()


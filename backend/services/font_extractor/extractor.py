"""
Font extraction using PyMuPDF for accurate font size and style detection.
"""
import fitz  # PyMuPDF
from typing import Dict, List, Optional
from .models import FontInfo
from .utils import color_to_hex, clean_font_family, detect_font_weight_and_style
from .matcher import find_font_for_text

class FontExtractorPyMuPDF:
    """Extract font information from PDF using PyMuPDF"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pages: Dict[int, List[FontInfo]] = {}
        
    def extract(self):
        """Extract font information from all pages"""
        doc = fitz.open(self.pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            self.pages[page_num + 1] = self._extract_page_fonts(page)
            
        doc.close()
        
    def _extract_page_fonts(self, page) -> List[FontInfo]:
        """Extract font information from a single page"""
        fonts = []
        
        # Get blocks directly
        try:
            # Check if page is valid
            blocks = page.get_text("dict")["blocks"]
        except Exception:
            # Handle empty pages or errors
            return []
        
        for block in blocks:
            if block.get("type") == 0:  # Text block
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if not text:
                            continue
                        
                        # Extract font properties
                        font_name = span.get("font", "")
                        size = span.get("size", 12.0)
                        flags = span.get("flags", 0)
                        color_tuple = span.get("color", 0)
                        bbox = span.get("bbox", (0, 0, 0, 0))
                        
                        # Detect weight and style using util
                        font_weight, is_bold, is_italic = detect_font_weight_and_style(font_name, flags)
                        
                        # Convert color to hex
                        color_hex = color_to_hex(color_tuple)
                        
                        # Clean font family name
                        family = clean_font_family(font_name)
                        
                        fonts.append(FontInfo(
                            text=text,
                            font_family=family,
                            font_size=size,
                            is_bold=is_bold,
                            is_italic=is_italic,
                            color=color_hex,
                            bbox=bbox,
                            font_weight=font_weight
                        ))
        
        return fonts
    
    def find_font_for_text(self, page_num: int, text: str, top: float, left: float, 
                          tolerance: float = 5.0) -> Optional[FontInfo]:
        """
        Find the matching font info for a text element based on position and content.
        Delegates to matcher module.
        """
        return find_font_for_text(self.pages, page_num, text, top, left, tolerance)

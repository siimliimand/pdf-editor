import xml.etree.ElementTree as ET
import re
from typing import List, Dict
from ..models import FontSpec, TextElement

def extract_text_elements(page_node: ET.Element, fonts: Dict[str, FontSpec], font_extractor = None, page_number: int = 1, zoom_factor: float = 1.0, font_family_mapping: Dict[str, str] = None) -> List[TextElement]:
    """
    Extracts text elements from the XML page node.
    Handles text cleaning (DFC metadata removal) and font processing (bold/italic detection).
    Uses PyMuPDF font extractor for accurate font sizes when available.
    """
    elements: List[TextElement] = []
    font_family_mapping = font_family_mapping or {}
    
    for text_node in page_node.findall('text'):
        try:
            top = float(text_node.get('top', 0))
            left = float(text_node.get('left', 0))
            width = float(text_node.get('width', 0))
            height = float(text_node.get('height', 0))
            font_id = text_node.get('font', '0')
            
            # Check for embedded tags in text content
            # pdftohtml might put <b>...</b>
            has_bold_tag = False
            has_italic_tag = False
            for child in text_node.iter():
                if child.tag == 'b': has_bold_tag = True
                if child.tag == 'i': has_italic_tag = True
            
            raw_text = "".join(text_node.itertext())
            
            # Clean DFC metadata
            # If the text starts with DFC_, likely technical metadata, ignore the whole node
            if raw_text.strip().startswith('DFC_'):
                continue

            clean_text = re.sub(r'\bDFC_[A-Za-z0-9_]+(?::[^<>\s]*)?', '', raw_text)
            clean_text = clean_text.strip()
            
            if not clean_text:
                continue

            # Try to get accurate font info from PyMuPDF
            font_spec = None
            font_size = height  # Default to pdftohtml height
            
            if font_extractor:
                # Find matching font info from PyMuPDF
                # Coordinates from pdftohtml are already scaled by zoom_factor
                # PyMuPDF coordinates are unscaled, so we need to scale them
                unscaled_top = top / zoom_factor
                unscaled_left = left / zoom_factor
                
                font_info = font_extractor.find_font_for_text(
                    page_num=int(page_number),  # Convert to int (XML returns string)
                    text=clean_text,
                    top=unscaled_top,  # Convert back to unscaled coordinates
                    left=unscaled_left,
                    tolerance=10.0
                )
                
                if font_info:
                    # Use PyMuPDF font information
                    # PyMuPDF returns font size in points (pt)
                    # Scale by zoom_factor to match pdftohtml's coordinate system
                    # Note: We do NOT apply 1.333 DPI conversion because pdftohtml's
                    # zoom factor already handles the scaling correctly, and we need
                    # to match its coordinate system for consistency with images/layout
                    font_size = font_info.font_size * zoom_factor
                    
                    new_top = font_info.bbox[1] * zoom_factor
                    new_left = font_info.bbox[0] * zoom_factor
                    width = (font_info.bbox[2] - font_info.bbox[0]) * zoom_factor
                    height = (font_info.bbox[3] - font_info.bbox[1]) * zoom_factor

                    # Update positioning to match PyMuPDF which is more accurate than pdftohtml
                    if abs(top - new_top) > 0.5 or abs(left - new_left) > 0.5:
                         top = new_top
                         left = new_left
                    
                    # Resolve font family using mapping if available
                    final_family = font_info.font_family
                    if font_info.font_family in font_family_mapping:
                        final_family = font_family_mapping[font_info.font_family]
                    
                    # Create FontSpec from PyMuPDF data
                    font_spec = FontSpec(
                        id=font_id,
                        size=int(font_info.font_size),  # Store original size
                        family=final_family,
                        color=font_info.color,
                        is_bold=has_bold_tag or font_info.is_bold,
                        is_italic=has_italic_tag or font_info.is_italic,
                        font_weight=font_info.font_weight
                    )
            
            # Fallback to pdftohtml fontspec if PyMuPDF didn't find a match
            if not font_spec:
                font_spec = fonts.get(font_id)
                
                # Extract color from text node (overrides fontspec)
                text_color = text_node.get('color')
                
                # Create a modified font spec if tags found or color override
                if font_spec:
                    # pdftohtml fontspec.size is ALREADY SCALED by zoom_factor
                    # Use it directly to match the scaled output
                    font_size = font_spec.size
                    
                    if has_bold_tag or has_italic_tag or text_color:
                        font_spec = FontSpec(
                            id=font_spec.id,
                            size=font_spec.size,  # Already scaled
                            family=font_spec.family,
                            color=text_color if text_color else font_spec.color,
                            is_bold=has_bold_tag or font_spec.is_bold,
                            is_italic=has_italic_tag or font_spec.is_italic,
                            font_weight=font_spec.font_weight if hasattr(font_spec, 'font_weight') else (700 if (has_bold_tag or font_spec.is_bold) else 400)
                        )
                else:
                    # Last resort: create a default FontSpec
                    # height from pdftohtml is ALREADY SCALED by zoom_factor
                    font_size = height
                    
                    text_color = text_node.get('color', '#000000')
                    font_spec = FontSpec(
                        id=font_id,
                        size=int(height),  # Already scaled
                        family='Arial, Helvetica, sans-serif',
                        color=text_color,
                        is_bold=has_bold_tag,
                        is_italic=has_italic_tag,
                        font_weight=700 if has_bold_tag else 400
                    )

            elements.append(TextElement(
                text=clean_text, 
                top=top, 
                left=left, 
                width=width, 
                height=height, 
                font_spec=font_spec, 
                font_size=font_size
            ))
        except ValueError:
            continue
            
    return elements

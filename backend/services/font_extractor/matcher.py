from typing import Dict, List, Optional
from .models import FontInfo

def find_font_for_text(
    pages: Dict[int, List[FontInfo]], 
    page_num: int, 
    text: str, 
    top: float, 
    left: float, 
    tolerance: float = 5.0
) -> Optional[FontInfo]:
    """
    Find the matching font info for a text element based on position and content.
    Uses multiple strategies to match text from pdftohtml with PyMuPDF spans.
    
    Args:
        pages: Dictionary of pages with their font info
        page_num: Page number (1-indexed)
        text: Text content to match
        top: Top position from pdftohtml (unscaled)
        left: Left position from pdftohtml (unscaled)
        tolerance: Position tolerance in points
        
    Returns:
        FontInfo if found, None otherwise
    """
    if page_num not in pages:
        return None
    
    page_fonts = pages[page_num]
    text_clean = text.strip()
    
    if not text_clean:
        return None
    
    # Strategy 1: Exact text match with position proximity
    for font_info in page_fonts:
        if font_info.text == text_clean:
            # Check if positions are close (bbox is x0, y0, x1, y1)
            if (abs(font_info.bbox[0] - left) <= tolerance and 
                abs(font_info.bbox[1] - top) <= tolerance):
                return font_info
    
    # Strategy 2: Partial text match (for cases where text is split differently)
    for font_info in page_fonts:
        if text_clean in font_info.text or font_info.text in text_clean:
            if (abs(font_info.bbox[0] - left) <= tolerance and 
                abs(font_info.bbox[1] - top) <= tolerance):
                return font_info
    
    # Strategy 3: Word-level matching (first word)
    # Sometimes pdftohtml and PyMuPDF split text at different boundaries
    words = text_clean.split()
    if words:
        first_word = words[0]
        for font_info in page_fonts:
            if first_word in font_info.text or font_info.text.startswith(first_word):
                if (abs(font_info.bbox[0] - left) <= tolerance and 
                    abs(font_info.bbox[1] - top) <= tolerance):
                    return font_info
    
    # Strategy 4: Same line matching (Y-coordinate proximity)
    # Find fonts on the same line (within 2pt vertically)
    line_fonts = [
        f for f in page_fonts 
        if abs(f.bbox[1] - top) <= 2.0
    ]
    
    if line_fonts:
        # Find the closest one horizontally
        min_x_distance = float('inf')
        closest_font = None
        
        for font_info in line_fonts:
            x_distance = abs(font_info.bbox[0] - left)
            if x_distance < min_x_distance and x_distance <= tolerance * 2:
                min_x_distance = x_distance
                closest_font = font_info
        
        if closest_font:
            return closest_font
    
    # Strategy 5: Closest match by position (last resort)
    min_distance = float('inf')
    closest_font = None
    
    for font_info in page_fonts:
        distance = ((font_info.bbox[0] - left) ** 2 + 
                   (font_info.bbox[1] - top) ** 2) ** 0.5
        if distance < min_distance and distance <= tolerance * 3:
            min_distance = distance
            closest_font = font_info
    
    return closest_font

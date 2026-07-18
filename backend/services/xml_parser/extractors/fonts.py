import xml.etree.ElementTree as ET
import re
from typing import Dict
from ..models import FontSpec

def extract_fonts(root: ET.Element, font_family_mapping: Dict[str, str] = None) -> Dict[str, FontSpec]:
    fonts: Dict[str, FontSpec] = {}
    font_family_mapping = font_family_mapping or {}
    
    for font_node in root.findall('fontspec'):
        fid = font_node.get('id')
        family = font_node.get('family', 'sans-serif')
        size = int(font_node.get('size', 12))
        color = font_node.get('color', '#000000')
        
        # Check implicit bold/italic from family name if attrs missing
        family_lower = family.lower()
        is_bold = (font_node.get('isBold') == '1')
        is_italic = (font_node.get('isItalic') == '1')
        
        # Italic detection
        if ('italic' in family_lower) or ('oblique' in family_lower):
            is_italic = True

        # Font weight detection (CSS font-weight: 100-900)
        # Match the logic from font_extractor_pymupdf.py for consistency
        font_weight = 400  # Default: normal
        
        # Weight detection from font family name (most specific first)
        if 'black' in family_lower or 'heavy' in family_lower or '900' in family_lower:
            font_weight = 900
            is_bold = True
        elif 'extrabold' in family_lower or 'ultrabold' in family_lower or '800' in family_lower:
            font_weight = 800
            is_bold = True
        elif 'bold' in family_lower or '700' in family_lower:
            # Check if it's semibold/demibold first
            if 'semibold' in family_lower or 'demibold' in family_lower or '600' in family_lower:
                font_weight = 600
                is_bold = True
            else:
                font_weight = 700
                is_bold = True
        elif 'semibold' in family_lower or 'demibold' in family_lower or '600' in family_lower:
            font_weight = 600
            is_bold = True
        elif 'medium' in family_lower or '500' in family_lower:
            font_weight = 500
            is_bold = False  # Medium is not quite bold
        elif 'regular' in family_lower or 'normal' in family_lower or '400' in family_lower:
            font_weight = 400
            is_bold = False
        elif 'light' in family_lower:
            # Check for ultralight/extralight first
            if 'ultralight' in family_lower or 'extralight' in family_lower or '200' in family_lower:
                font_weight = 200
                is_bold = False
            else:
                font_weight = 300
                is_bold = False
        elif 'thin' in family_lower or 'hairline' in family_lower or '100' in family_lower:
            font_weight = 100
            is_bold = False
        elif is_bold:
            # If is_bold flag is set but no weight in name, assume 700
            font_weight = 700

        # Use mapped font family if available (from CSS embedding)
        # This ensures we use the exact family name defined in @font-face
        if family in font_family_mapping:
            clean_family = font_family_mapping[family]
        else:
            clean_family = _get_clean_font_family(family)
        
        fonts[fid] = FontSpec(id=fid, size=size, family=clean_family, color=color, is_bold=is_bold, is_italic=is_italic, font_weight=font_weight)
    return fonts

def _get_clean_font_family(raw_family: str) -> str:
    """Map PDF font names to Web Safe CSS stacks."""
    lower = raw_family.lower()
    
    # Common mappings
    if 'times' in lower: return '"Times New Roman", Times, serif'
    if 'arial' in lower or 'helvetica' in lower: return 'Arial, Helvetica, sans-serif'
    if 'courier' in lower or 'mono' in lower: return '"Courier New", Courier, monospace'
    if 'verdana' in lower: return 'Verdana, Geneva, sans-serif'
    if 'tahoma' in lower: return 'Tahoma, Geneva, sans-serif'
    if 'trebuchet' in lower: return '"Trebuchet MS", Helvetica, sans-serif'
    if 'georgia' in lower: return 'Georgia, serif'
    if 'comic' in lower: return '"Comic Sans MS", cursive, sans-serif'
    
    # Fallback: Clean up name and append generic
    clean = re.sub(r'[\-]?(Bold|Italic|Oblique|Regular|MT|PSMT|PS)+', '', raw_family, flags=re.IGNORECASE)
    clean = clean.strip()
    if not clean: return "sans-serif"
    
    return f"'{clean}', sans-serif"

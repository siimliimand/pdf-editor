import re
from typing import Union, Tuple, List

def color_to_hex(color: Union[int, Tuple[float, float, float], List[float]]) -> str:
    """Convert PyMuPDF color to hex string"""
    if isinstance(color, int):
        # Single integer color value
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF
        return f"#{r:02x}{g:02x}{b:02x}"
    elif isinstance(color, (tuple, list)) and len(color) >= 3:
        # RGB tuple (0-1 range)
        r = int(color[0] * 255)
        g = int(color[1] * 255)
        b = int(color[2] * 255)
        return f"#{r:02x}{g:02x}{b:02x}"
    else:
        return "#000000"  # Default black

def clean_font_family(font_name: str) -> str:
    """
    Map PDF font names to web-safe CSS font stacks.
    Comprehensive mapping for invoice and business document fonts.
    """
    if not font_name:
        return 'sans-serif'
    
    lower = font_name.lower()
    
    # Remove style suffixes for matching (but preserve original for fallback)
    clean = re.sub(r'[-,]?(bold|italic|oblique|regular|medium|light|thin|heavy|black|semibold|extrabold|ultralight)+', '', lower, flags=re.IGNORECASE)
    clean = clean.strip('-,').strip()
    
    # Priority 1: Exact matches for common invoice/business fonts
    # These fonts are frequently used in professional documents
    
    # Roboto family (Google Fonts - very common in modern invoices)
    if 'roboto' in clean:
        return 'Roboto, "Segoe UI", Arial, sans-serif'
    
    # Amazon Ember (Amazon invoices)
    if 'amazonember' in clean or 'amazon' in clean:
        return '"Amazon Ember", "Segoe UI", Arial, sans-serif'
    
    # Open Sans (very popular for web and documents)
    if 'opensans' in clean or 'open sans' in lower:
        return '"Open Sans", "Segoe UI", Arial, sans-serif'
    
    # Lato (popular modern sans-serif)
    if 'lato' in clean:
        return 'Lato, "Segoe UI", Arial, sans-serif'
    
    # Montserrat (modern geometric sans-serif)
    if 'montserrat' in clean:
        return 'Montserrat, "Segoe UI", Arial, sans-serif'
    
    # Source Sans Pro (Adobe)
    if 'sourcesans' in clean or 'source sans' in lower:
        return '"Source Sans Pro", "Segoe UI", Arial, sans-serif'
    
    # Noto Sans (Google - multilingual support)
    if 'notosans' in clean or 'noto sans' in lower:
        return '"Noto Sans", Arial, sans-serif'
    
    # Priority 2: Standard system fonts
    
    # Helvetica/Arial family (most common)
    if 'helvetica' in clean or 'arial' in clean:
        return 'Arial, Helvetica, sans-serif'
    
    # Segoe UI (Windows system font)
    if 'segoe' in clean:
        return '"Segoe UI", Arial, sans-serif'
    
    # Calibri (Microsoft Office default)
    if 'calibri' in clean:
        return 'Calibri, "Segoe UI", Arial, sans-serif'
    
    # Verdana
    if 'verdana' in clean:
        return 'Verdana, Geneva, sans-serif'
    
    # Tahoma
    if 'tahoma' in clean:
        return 'Tahoma, Geneva, sans-serif'
    
    # Trebuchet MS
    if 'trebuchet' in clean:
        return '"Trebuchet MS", Helvetica, sans-serif'
    
    # Priority 3: Serif fonts
    
    # Times New Roman family
    if 'times' in clean:
        return '"Times New Roman", Times, serif'
    
    # Georgia
    if 'georgia' in clean:
        return 'Georgia, serif'
    
    # Garamond
    if 'garamond' in clean:
        return 'Garamond, "Times New Roman", serif'
    
    # Palatino
    if 'palatino' in clean:
        return 'Palatino, "Palatino Linotype", "Times New Roman", serif'
    
    # Priority 4: Monospace fonts
    
    # Courier family
    if 'courier' in clean:
        return '"Courier New", Courier, monospace'
    
    # Consolas
    if 'consolas' in clean:
        return 'Consolas, "Courier New", monospace'
    
    # Monaco
    if 'monaco' in clean:
        return 'Monaco, "Courier New", monospace'
    
    # Any monospace indicator
    if 'mono' in clean:
        return '"Courier New", Courier, monospace'
    
    # Priority 5: Other fonts
    
    # Comic Sans
    if 'comic' in clean:
        return '"Comic Sans MS", cursive, sans-serif'
    
    # Impact
    if 'impact' in clean:
        return 'Impact, "Arial Black", sans-serif'
    
    # Fallback: Use the original font name with generic fallback
    # This preserves the exact font name if it's a web font or system font
    # Remove common suffixes but keep the base name
    original_clean = re.sub(r'[-]?(Bold|Italic|Oblique|Regular|Medium|Light|Thin|Heavy|Black|SemiBold|ExtraBold|UltraLight)+$', '', font_name, flags=re.IGNORECASE)
    original_clean = original_clean.strip('-,').strip()
    
    if original_clean and original_clean.lower() != 'unknown':
        # Determine generic family based on font characteristics
        if any(serif in lower for serif in ['serif', 'times', 'garamond', 'palatino', 'georgia']):
            return f"'{original_clean}', serif"
        elif any(mono in lower for mono in ['mono', 'courier', 'consolas', 'code']):
            return f"'{original_clean}', monospace"
        else:
            return f"'{original_clean}', sans-serif"
    
    return 'sans-serif'

def detect_font_weight_and_style(font_name: str, flags: int) -> Tuple[int, bool, bool]:
    """
    Detect font weight and style (bold/italic) from font name and flags.
    Returns (font_weight, is_bold, is_italic)
    """
    # Decode font flags (PyMuPDF standard)
    # Bit 0 (1): Superscript
    # Bit 1 (2): Italic
    # Bit 2 (4): Serifed
    # Bit 3 (8): Monospaced
    # Bit 4 (16): Bold
    flag_bold = bool(flags & 16)  # Bit 4
    flag_italic = bool(flags & 2)  # Bit 1
    
    # Comprehensive font weight detection from font name
    font_lower = font_name.lower()
    
    # Detect weight from font name
    # CSS font-weight values: 100-900 (100=thin, 400=normal, 700=bold, 900=black)
    font_weight = 400  # Default: normal
    is_bold = flag_bold
    is_italic = flag_italic
    
    # Weight detection priority (most specific first)
    # Check for specific weight names in order from heaviest to lightest
    # This ensures "extrabold" is checked before "bold", etc.
    if 'black' in font_lower or 'heavy' in font_lower or '900' in font_lower:
        font_weight = 900
        is_bold = True
    elif 'extrabold' in font_lower or 'ultrabold' in font_lower or '800' in font_lower:
        font_weight = 800
        is_bold = True
    elif 'bold' in font_lower or '700' in font_lower:
        # Check if it's semibold/demibold first
        if 'semibold' in font_lower or 'demibold' in font_lower or '600' in font_lower:
            font_weight = 600
            is_bold = True
        else:
            font_weight = 700
            is_bold = True
    elif 'semibold' in font_lower or 'demibold' in font_lower or '600' in font_lower:
        font_weight = 600
        is_bold = True
    elif 'medium' in font_lower or '500' in font_lower:
        font_weight = 500
        is_bold = False  # Medium is not quite bold
    elif 'regular' in font_lower or 'normal' in font_lower or '400' in font_lower:
        font_weight = 400
        is_bold = False
    elif 'light' in font_lower:
        # Check for ultralight/extralight first
        if 'ultralight' in font_lower or 'extralight' in font_lower or '200' in font_lower:
            font_weight = 200
            is_bold = False
        else:
            font_weight = 300
            is_bold = False
    elif 'thin' in font_lower or 'hairline' in font_lower or '100' in font_lower:
        font_weight = 100
        is_bold = False
    elif flag_bold:
        # If flag indicates bold but no weight in name, assume 700
        font_weight = 700
        is_bold = True
    
    # Italic detection (more comprehensive)
    if 'italic' in font_lower or 'oblique' in font_lower or 'slant' in font_lower:
        is_italic = True
        
    return font_weight, is_bold, is_italic

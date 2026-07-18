"""
Font Embedder Service

Extracts fonts from PDF files and creates @font-face CSS declarations
for embedding in the generated HTML. This ensures perfect visual fidelity
by using the exact fonts from the PDF.
"""
import pymupdf
import base64
from typing import Dict, List, Tuple
from pathlib import Path
import hashlib


class FontEmbedder:
    """Extracts and embeds fonts from PDF files"""
    
    def __init__(self):
        self.font_cache: Dict[str, str] = {}  # font_name -> base64_data
        self.font_metadata: Dict[str, dict] = {}  # font_name -> metadata
    
    def extract_fonts_from_pdf(self, pdf_path: str) -> Dict[str, bytes]:
        """
        Extract all fonts from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary mapping font names to font file data (bytes)
        """
        doc = pymupdf.open(pdf_path)
        fonts = {}
        
        # Iterate through all pages to find fonts
        for page_num in range(len(doc)):
            page = doc[page_num]
            font_list = page.get_fonts(full=True)
            
            for font_info in font_list:
                # font_info format: (xref, ext, type, basefont, name, encoding, ...)
                xref = font_info[0]
                ext = font_info[1]  # Font file extension (ttf, otf, etc.)
                font_type = font_info[2]  # Font type (TrueType, Type1, etc.)
                basefont = font_info[3]  # Font name (e.g., "Elisa-Regular")
                
                # Skip if we already have this font
                if basefont in fonts:
                    continue
                
                # Extract font data
                try:
                    font_data = doc.extract_font(xref)
                    if font_data and font_data[0]:  # font_data is tuple (basename, ext, type, content)
                        fonts[basefont] = {
                            'data': font_data[3],  # Font file content
                            'ext': font_data[1] or ext,  # File extension
                            'type': font_data[2] or font_type,  # Font type
                            'basename': font_data[0] or basefont,
                        }
                        print(f"✓ Extracted font: {basefont} ({font_data[1] or ext})")
                except Exception as e:
                    print(f"⚠️  Could not extract font {basefont}: {e}")
        
        doc.close()
        return fonts
    
    def font_to_base64(self, font_data: bytes, ext: str) -> str:
        """
        Convert font data to base64 data URI.
        
        Args:
            font_data: Raw font file bytes
            ext: Font file extension (ttf, otf, woff, etc.)
            
        Returns:
            Base64-encoded data URI
        """
        # Determine MIME type
        mime_types = {
            'ttf': 'font/truetype',
            'otf': 'font/opentype',
            'woff': 'font/woff',
            'woff2': 'font/woff2',
        }
        mime_type = mime_types.get(ext.lower(), 'font/truetype')
        
        # Encode to base64
        b64_data = base64.b64encode(font_data).decode('utf-8')
        
        return f"data:{mime_type};base64,{b64_data}"
    
    def get_font_weight_from_name(self, font_name: str) -> int:
        """
        Determine CSS font-weight from font name.
        
        Args:
            font_name: Font family name (e.g., "Elisa-Thin", "Elisa-Regular")
            
        Returns:
            CSS font-weight value (100-900)
        """
        name_lower = font_name.lower()
        
        # Weight detection (same logic as fonts.py)
        if 'black' in name_lower or 'heavy' in name_lower:
            return 900
        elif 'extrabold' in name_lower or 'ultrabold' in name_lower:
            return 800
        elif 'bold' in name_lower:
            if 'semibold' in name_lower or 'demibold' in name_lower:
                return 600
            return 700
        elif 'semibold' in name_lower or 'demibold' in name_lower:
            return 600
        elif 'medium' in name_lower:
            return 500
        elif 'regular' in name_lower or 'normal' in name_lower:
            return 400
        elif 'light' in name_lower:
            if 'ultralight' in name_lower or 'extralight' in name_lower:
                return 200
            return 300
        elif 'thin' in name_lower or 'hairline' in name_lower:
            return 100
        else:
            return 400  # Default
    
    def get_font_style_from_name(self, font_name: str) -> str:
        """
        Determine CSS font-style from font name.
        
        Args:
            font_name: Font family name
            
        Returns:
            CSS font-style value ('normal' or 'italic')
        """
        name_lower = font_name.lower()
        if 'italic' in name_lower or 'oblique' in name_lower:
            return 'italic'
        return 'normal'
    
    def create_font_face_css(self, fonts: Dict[str, dict]) -> str:
        """
        Create @font-face CSS declarations for all fonts.
        
        Args:
            fonts: Dictionary of font data from extract_fonts_from_pdf()
            
        Returns:
            CSS string with @font-face declarations
        """
        css_parts = []
        
        for font_name, font_info in fonts.items():
            font_data = font_info['data']
            ext = font_info['ext']
            
            # Convert to base64
            data_uri = self.font_to_base64(font_data, ext)
            
            # Determine font properties
            weight = self.get_font_weight_from_name(font_name)
            style = self.get_font_style_from_name(font_name)
            
            # Clean font family name (remove weight/style suffixes)
            base_family = font_name.split('-')[0] if '-' in font_name else font_name
            
            # Create @font-face declaration
            css = f"""
@font-face {{
    font-family: '{base_family}';
    src: url('{data_uri}') format('{self._get_font_format(ext)}');
    font-weight: {weight};
    font-style: {style};
    font-display: swap;
}}"""
            css_parts.append(css)
            
            # Store metadata
            self.font_metadata[font_name] = {
                'family': base_family,
                'weight': weight,
                'style': style,
                'ext': ext,
            }
        
        return '\n'.join(css_parts)
    
    def _get_font_format(self, ext: str) -> str:
        """Get CSS font format string from extension"""
        formats = {
            'ttf': 'truetype',
            'otf': 'opentype',
            'woff': 'woff',
            'woff2': 'woff2',
        }
        return formats.get(ext.lower(), 'truetype')
    
    def get_font_family_for_name(self, font_name: str) -> str:
        """
        Get the CSS font-family value for a font name.
        
        Args:
            font_name: Original font name from PDF (e.g., "Elisa-Regular")
            
        Returns:
            CSS font-family value (e.g., 'Elisa')
        """
        # Extract base family name
        base_family = font_name.split('-')[0] if '-' in font_name else font_name
        return f"'{base_family}', sans-serif"
    
    def process_pdf(self, pdf_path: str, use_cache: bool = True) -> Tuple[str, Dict[str, str]]:
        """
        Complete font processing for a PDF file with caching support.
        
        Args:
            pdf_path: Path to PDF file
            use_cache: Whether to use cached fonts (default: True)
            
        Returns:
            Tuple of (css_string, font_family_mapping)
            - css_string: @font-face CSS declarations
            - font_family_mapping: Dict mapping original font names to CSS font-family values
        """
        from .font_cache import get_font_cache
        
        cache = get_font_cache() if use_cache else None
        
        # Extract fonts
        fonts = self.extract_fonts_from_pdf(pdf_path)
        
        if not fonts:
            print("⚠️  No fonts extracted from PDF")
            return "", {}
        
        css_parts = []
        font_mapping = {}
        
        for font_name, font_info in fonts.items():
            font_data = font_info['data']
            
            # Check cache first
            if cache:
                cached = cache.get_cached_font(font_name, font_data)
                if cached:
                    css_parts.append(cached['css'])
                    font_mapping[font_name] = self.get_font_family_for_name(font_name)
                    
                    # Store metadata for this session
                    self.font_metadata[font_name] = {
                        'family': cached['family'],
                        'weight': cached['weight'],
                        'style': cached['style'],
                        'ext': font_info['ext'],
                    }
                    continue
            
            # Not cached, generate CSS
            ext = font_info['ext']
            data_uri = self.font_to_base64(font_data, ext)
            
            weight = self.get_font_weight_from_name(font_name)
            style = self.get_font_style_from_name(font_name)
            base_family = font_name.split('-')[0] if '-' in font_name else font_name
            
            css = f"""
@font-face {{
    font-family: '{base_family}';
    src: url('{data_uri}') format('{self._get_font_format(ext)}');
    font-weight: {weight};
    font-style: {style};
    font-display: swap;
}}"""
            
            css_parts.append(css)
            font_mapping[font_name] = self.get_font_family_for_name(font_name)
            
            # Store metadata
            self.font_metadata[font_name] = {
                'family': base_family,
                'weight': weight,
                'style': style,
                'ext': ext,
            }
            
            # Cache for future use
            if cache:
                cache.cache_font(font_name, font_data, self.font_metadata[font_name], css)
        
        return '\n'.join(css_parts), font_mapping


# Standalone test
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python font_embedder.py <pdf_file>")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    
    print(f"Processing: {pdf_file}")
    print("=" * 80)
    
    embedder = FontEmbedder()
    css, mapping = embedder.process_pdf(pdf_file)
    
    print("\n" + "=" * 80)
    print("FONT MAPPING:")
    print("=" * 80)
    for orig, css_family in mapping.items():
        meta = embedder.font_metadata.get(orig, {})
        print(f"{orig:30} → {css_family:30} (weight: {meta.get('weight', '?')})")
    
    print("\n" + "=" * 80)
    print("CSS OUTPUT:")
    print("=" * 80)
    print(css)
    
    # Save to file
    output_file = Path(pdf_file).stem + "_fonts.css"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(css)
    
    print(f"\n✓ CSS saved to: {output_file}")

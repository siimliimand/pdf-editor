"""
Font Cache Manager

Manages a cache of extracted PDF fonts to avoid re-extracting the same fonts
from multiple PDFs. Fonts are stored with hash-based filenames and reused
when the same font is encountered again.
"""
import hashlib
import json
from pathlib import Path
from typing import Dict, Optional, Tuple
import base64


class FontCache:
    """Manages cached font data and CSS"""
    
    def __init__(self, cache_dir: str = "./fonts_cache"):
        """
        Initialize font cache.
        
        Args:
            cache_dir: Directory to store cached fonts
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Metadata file tracks font info
        self.metadata_file = self.cache_dir / "fonts_metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Load font metadata from cache"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_metadata(self):
        """Save font metadata to cache"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def _get_font_hash(self, font_data: bytes) -> str:
        """Generate hash for font data"""
        return hashlib.sha256(font_data).hexdigest()[:16]
    
    def get_cached_font(self, font_name: str, font_data: bytes) -> Optional[Dict]:
        """
        Check if font is already cached by name.
        
        Args:
            font_name: Name of the font (e.g., "Elisa-Regular")
            font_data: Raw font file bytes
            
        Returns:
            Cached font info dict or None if not cached
        """
        # Sanitize font name for filename
        safe_name = self._sanitize_font_name(font_name)
        css_file = self.cache_dir / f"{safe_name}.css"
        
        # Check if font file exists
        if safe_name in self.metadata and css_file.exists():
            cached_info = self.metadata[safe_name]
            
            # Verify the font data matches (in case of name collision)
            font_hash = self._get_font_hash(font_data)
            if cached_info.get('hash') == font_hash:
                with open(css_file, 'r') as f:
                    css = f.read()
                
                print(f"✓ Using cached font: {font_name}")
                
                return {
                    'hash': font_hash,
                    'name': font_name,
                    'css': css,
                    'weight': cached_info['weight'],
                    'style': cached_info['style'],
                    'family': cached_info['family'],
                }
            else:
                print(f"⚠️  Font name collision detected for {font_name}, re-caching...")
        
        return None
    
    def _sanitize_font_name(self, font_name: str) -> str:
        """Sanitize font name for use as filename"""
        # Replace unsafe characters
        safe = font_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        # Remove any other problematic characters
        safe = ''.join(c for c in safe if c.isalnum() or c in '-_')
        return safe
    
    def cache_font(self, font_name: str, font_data: bytes, font_info: Dict, css: str) -> str:
        """
        Cache a font and its CSS using the font name.
        
        Args:
            font_name: Name of the font (e.g., "Elisa-Regular")
            font_data: Raw font file bytes
            font_info: Font metadata (ext, type, etc.)
            css: Generated @font-face CSS
            
        Returns:
            Sanitized font name (cache key)
        """
        font_hash = self._get_font_hash(font_data)
        safe_name = self._sanitize_font_name(font_name)
        
        # Save CSS file with font name
        css_filename = f"{safe_name}.css"
        css_file = self.cache_dir / css_filename
        
        with open(css_file, 'w', encoding='utf-8') as f:
            f.write(css)
        
        # Update metadata (keyed by sanitized name)
        self.metadata[safe_name] = {
            'name': font_name,
            'hash': font_hash,  # Store hash for verification
            'css_file': css_filename,
            'weight': font_info.get('weight', 400),
            'style': font_info.get('style', 'normal'),
            'family': font_info.get('family', font_name.split('-')[0]),
            'ext': font_info.get('ext', 'ttf'),
        }
        
        self._save_metadata()
        
        print(f"✓ Cached font: {font_name} → {css_filename}")
        
        return safe_name
    
    def get_all_cached_css(self) -> str:
        """Get CSS for all cached fonts (useful for debugging)"""
        css_parts = []
        
        for font_hash, info in self.metadata.items():
            css_file = self.cache_dir / info['css_file']
            if css_file.exists():
                with open(css_file, 'r') as f:
                    css_parts.append(f.read())
        
        return '\n'.join(css_parts)
    
    def clear_cache(self):
        """Clear all cached fonts"""
        for file in self.cache_dir.glob('*.css'):
            file.unlink()
        
        self.metadata = {}
        self._save_metadata()
        
        print("✓ Font cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'total_fonts': len(self.metadata),
            'cache_dir': str(self.cache_dir),
            'fonts': [
                {
                    'safe_name': safe_name,
                    'name': info['name'],
                    'family': info['family'],
                    'weight': info['weight'],
                    'css_file': info['css_file'],
                }
                for safe_name, info in self.metadata.items()
            ]
        }


# Global cache instance
_font_cache = None

def get_font_cache() -> FontCache:
    """Get the global font cache instance"""
    global _font_cache
    if _font_cache is None:
        _font_cache = FontCache()
    return _font_cache

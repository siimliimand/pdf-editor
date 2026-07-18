# Font Embedding System - Usage Guide

## Overview

The font embedding system automatically extracts fonts from PDFs and embeds them in the generated HTML for perfect visual fidelity. Fonts are cached to avoid re-extraction.

## Architecture

### Components

1. **`font_embedder.py`** - Extracts fonts from PDFs and creates @font-face CSS
2. **`font_cache.py`** - Manages cached fonts with readable filenames
3. **`fonts_cache/`** - Directory storing cached font CSS files

### How It Works

```
PDF Upload
    ↓
Extract Fonts (PyMuPDF)
    ↓
Check Cache (by font name + hash)
    ↓
    ├─ Cached? → Use existing CSS
    └─ Not Cached? → Generate CSS → Save to cache
    ↓
Embed in HTML
```

## Cache Structure

```
fonts_cache/
├── Elisa-Regular.css       # Font CSS with embedded base64 data
├── Elisa-Thin.css          # Font CSS with embedded base64 data
└── fonts_metadata.json     # Metadata tracking all cached fonts
```

### Metadata Format

```json
{
  "Elisa-Regular": {
    "name": "Elisa-Regular",
    "hash": "6a960245be08d39b",
    "css_file": "Elisa-Regular.css",
    "weight": 400,
    "style": "normal",
    "family": "Elisa",
    "ext": "ttf"
  }
}
```

## Usage

### Basic Usage

```python
from services.font_embedder import FontEmbedder

embedder = FontEmbedder()
css, font_mapping = embedder.process_pdf('./path/to/file.pdf')

# css: @font-face declarations
# font_mapping: {'Elisa-Regular': '"Elisa", sans-serif', ...}
```

### With Cache Control

```python
# Use cache (default)
css, mapping = embedder.process_pdf('./file.pdf', use_cache=True)

# Skip cache (force re-extraction)
css, mapping = embedder.process_pdf('./file.pdf', use_cache=False)
```

### Cache Management

```python
from services.font_cache import get_font_cache

cache = get_font_cache()

# Get statistics
stats = cache.get_cache_stats()
print(f"Total cached fonts: {stats['total_fonts']}")

# Clear cache
cache.clear_cache()
```

## Benefits

### ✅ Perfect Visual Fidelity
- Uses the **exact fonts** from the PDF
- No font substitution or approximation
- 100% match to original appearance

### ✅ Performance
- Fonts cached after first extraction
- Subsequent PDFs with same fonts reuse cache
- No repeated extraction overhead

### ✅ Readable Cache
- Font files named after font (e.g., `Elisa-Regular.css`)
- Easy to inspect and manage
- Hash verification prevents collisions

### ✅ Automatic Detection
- Font weight automatically detected from name
  - "Thin" → weight 100
  - "Regular" → weight 400
  - "Bold" → weight 700
- Font style detected (italic, oblique)

## Example Output

### Generated CSS

```css
@font-face {
    font-family: 'Elisa';
    src: url('data:font/truetype;base64,AAEAAAAOAIAAAwBg...') format('truetype');
    font-weight: 100;
    font-style: normal;
    font-display: swap;
}

@font-face {
    font-family: 'Elisa';
    src: url('data:font/truetype;base64,AAEAAAAOAIAAAwBg...') format('truetype');
    font-weight: 400;
    font-style: normal;
    font-display: swap;
}
```

### Font Mapping

```python
{
    'Elisa-Thin': '"Elisa", sans-serif',
    'Elisa-Regular': '"Elisa", sans-serif'
}
```

## Integration with PDF Service

To integrate with your PDF processing:

```python
from services.font_embedder import FontEmbedder

def convert_pdf_to_html(pdf_content: bytes, zoom_level: float = 100.0) -> str:
    # Save PDF temporarily
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp.write(pdf_content)
        pdf_path = tmp.name
    
    try:
        # Extract and cache fonts
        embedder = FontEmbedder()
        font_css, font_mapping = embedder.process_pdf(pdf_path)
        
        # Generate HTML (existing logic)
        html_content = generate_html(pdf_path, zoom_level)
        
        # Inject font CSS into HTML
        if font_css:
            html_content = inject_font_css(html_content, font_css)
        
        return html_content
    finally:
        os.unlink(pdf_path)
```

## Testing

### Test Font Extraction

```bash
cd backend
python services/font_embedder.py ./temp/test_pdfs/second-page.pdf
```

### Test Caching

```bash
# First run - extracts and caches
python services/font_embedder.py ./temp/test_pdfs/second-page.pdf

# Second run - uses cache
python services/font_embedder.py ./temp/test_pdfs/second-page.pdf
```

### View Cache

```bash
ls -lh fonts_cache/
cat fonts_cache/fonts_metadata.json
```

## Troubleshooting

### Font Not Extracted

**Problem**: Font appears in PDF but not extracted

**Solution**: Check if font is embedded in PDF:
```python
import pymupdf
doc = pymupdf.open('file.pdf')
fonts = doc[0].get_fonts(full=True)
print(fonts)
```

### Font Name Collision

**Problem**: Two different fonts with same name

**Solution**: System automatically detects via hash and re-caches

### Cache Not Working

**Problem**: Fonts re-extracted every time

**Solution**: Check cache directory permissions and metadata file

## Next Steps

1. ✅ Font extraction working
2. ✅ Caching implemented
3. ⏳ Integrate into `pdf_service.py`
4. ⏳ Update HTML generation to include font CSS
5. ⏳ Test with extension

## Files Modified/Created

- ✅ `services/font_embedder.py` - Font extraction and CSS generation
- ✅ `services/font_cache.py` - Cache management
- ✅ `fonts_cache/` - Cache directory (auto-created)
- ⏳ `services/pdf_service.py` - Integration point

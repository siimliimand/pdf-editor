# PDF to HTML Size Calculation Analysis

This document explains how **page size**, **font size**, and **image size** are calculated during the PDF to HTML conversion process.

---

## 1. Page Size Calculation (841 x 595)

### Source: `pdftohtml` XML Output
The page dimensions (841px height × 595px width) come directly from the `pdftohtml` tool's XML output.

**Location:** `backend/services/pdf_service.py` (Lines 47-54)
```python
cmd = [
    "pdftohtml",
    "-xml",        # Output XML structure
    "-stdout",     # Output to standard output
    "-hidden",
    "-zoom", "1.0", # Scale factor: 1.0 = original size
    "input.pdf"
]
```

### XML Structure
The `pdftohtml` command generates XML with page metadata:

**Example from:** `backend/temp/debug/test.xml` (Line 5)
```xml
<page number="1" position="absolute" top="0" left="0" height="841" width="595">
```

### How it's parsed and used:

**Location:** `backend/services/xml_parser/parser.py` (Lines 27-32)
```python
for page in self.root.findall('page'):
    page_number = page.get('number')
    width = int(page.get('width'))   # 595px
    height = int(page.get('height')) # 841px
    
    html_parts.append(f'<div id="page-{page_number}" class="pdf-page" 
                        style="width: {width}px; height: {height}px; 
                        position: relative; margin: 0 auto 20px auto; 
                        padding: 0px; box-sizing: border-box; 
                        background: white; 
                        box-shadow: 0 0 10px rgba(0,0,0,0.1);">
                      ')
```

### Understanding the dimensions:
- **595 × 841 pixels** corresponds to **A4 paper size** at 72 DPI (standard PDF resolution)
- A4 dimensions in points: 210mm × 297mm = 595pt × 842pt
- The `-zoom` parameter in `pdftohtml` controls the scale:
  - `1.0` = Original size (595 × 841)
  - `1.5` = 1.5x larger (892 × 1261)
  - `2.0` = 2x larger (1190 × 1682)

---

## 2. Font Size Calculation

Font size is calculated from **two sources** and uses the **maximum value** for accuracy:

### Source 1: Font Specification (FontSpec)
**Location:** `backend/services/xml_parser/extractors.py` (Lines 11-45)

```python
def extract_fonts(root: ET.Element) -> Dict[str, FontSpec]:
    fonts: Dict[str, FontSpec] = {}
    for font_node in root.findall('fontspec'):
        fid = font_node.get('id')
        family = font_node.get('family', 'sans-serif')
        size = int(font_node.get('size', 12))  # <-- Font size from PDF
        color = font_node.get('color', '#000000')
        
        # ... bold/italic detection ...
        
        fonts[fid] = FontSpec(
            id=fid, 
            size=size,  # Stored for reference
            family=clean_family, 
            color=color, 
            is_bold=is_bold, 
            is_italic=is_italic
        )
    return fonts
```

**XML Example:**
```xml
<fontspec id="0" size="20" family="Helvetica" color="#000000"/>
<fontspec id="2" size="13" family="Helvetica" color="#000000"/>
<fontspec id="8" size="10" family="Helvetica" color="#000000"/>
```

### Source 2: Text Element Height (ACTUAL SIZE USED)
**Location:** `backend/services/xml_parser/extractors.py` (Lines 227-270)

```python
for text_node in page_node.findall('text'):
    top = float(text_node.get('top', 0))
    left = float(text_node.get('left', 0))
    width = float(text_node.get('width', 0))
    height = float(text_node.get('height', 0))  # <-- This is the actual rendered height
    font_id = text_node.get('font', '0')
    
    # ...
    
    font_spec = fonts.get(font_id)
    font_size = height  # <-- USES HEIGHT AS FONT SIZE (line 253)
    
    elements.append(TextElement(
        text=clean_text,
        top=top,
        left=left,
        width=width,
        height=height,
        font_spec=font_spec,
        font_size=font_size  # <-- This is what gets rendered
    ))
```

**XML Example:**
```xml
<text top="76" left="72" width="116" height="19" font="0">SeoWeb OÜ</text>
<!-- Font size will be 19px (from height), not 20px (from fontspec) -->
```

### Why use height instead of fontspec size?
The `height` attribute represents the **actual rendered height** of the text in the PDF, which accounts for:
- Font rendering variations
- Line spacing
- Vertical alignment
- Actual glyph metrics

This provides **more accurate visual fidelity** than the font specification size.

### How it's rendered in HTML:

**Location:** `backend/services/xml_parser/renderers.py` (Lines 207-212, 259-264)

**For tables:**
```python
for el in cell_elements:
    if isinstance(el, TextElement):
        style = f'font-size: {el.font_size}px;'  # <-- Uses the height value
        if el.font_spec:
            if el.font_spec.is_bold: style += ' font-weight: bold;'
            if el.font_spec.is_italic: style += ' font-style: italic;'
            style += f' color: {el.font_spec.color};'
        content_parts.append(f'<span style="{style}">{el.text}</span>')
```

**For paragraphs:**
```python
for el in sorted_elements:
    if isinstance(el, TextElement):
        style = f'font-size: {el.font_size}px;'  # <-- Uses the height value
        if el.font_spec:
            if el.font_spec.is_bold: style += ' font-weight: bold;'
            if el.font_spec.is_italic: style += ' font-style: italic;'
            style += f' color: {el.font_spec.color};'
            style += f' font-family: {el.font_spec.family};'
        
        parts.append(f'<span style="{style}">{el.text}</span>')
```

---

## 3. Image Size Calculation

Image sizing is a **two-step process** using **PyMuPDF for extraction** and **pdftohtml XML for positioning**.

### Step 1: Extract Images with PyMuPDF
**Location:** `backend/services/image_extractor_pymupdf.py` (Lines 32-112)

```python
def extract(self):
    doc = fitz.open(self.pdf_path)
    
    for page_num, page in enumerate(doc):
        page_images = []
        page_height = page.rect.height  # PDF page height for coordinate conversion
        
        # Get all images on the page
        image_list = page.get_images(full=True)
        
        for img_index, img_info in enumerate(image_list):
            xref = img_info[0]
            native_width = img_info[2]   # <-- Natural image width in pixels
            native_height = img_info[3]  # <-- Natural image height in pixels
            
            # Find where this image is drawn on the page
            rects = page.get_image_rects(xref)
            
            for i, rect in enumerate(rects):
                # Calculate zoom to extract at native resolution
                if rect.width > 0 and rect.height > 0:
                    zoom_x = native_width / rect.width
                    zoom_y = native_height / rect.height
                else:
                    zoom_x = zoom_y = 1
                
                # Render the image with proper zoom
                mat = fitz.Matrix(zoom_x, zoom_y)
                pix = page.get_pixmap(matrix=mat, clip=rect, alpha=True)
                
                # Get actual dimensions
                actual_width = pix.width   # <-- ACTUAL IMAGE WIDTH
                actual_height = pix.height # <-- ACTUAL IMAGE HEIGHT
                
                # Calculate display dimensions from PDF layout
                display_width = rect.x1 - rect.x0   # <-- WIDTH IN PDF (pt)
                display_height = rect.y1 - rect.y0  # <-- HEIGHT IN PDF (pt)
                
                # Store: (filename, x0, y0, x1, y1, actual_width, actual_height)
                page_images.append((
                    filename,
                    rect.x0,     # Left position
                    y0_bu,       # Bottom position (bottom-up coords)
                    rect.x1,     # Right position
                    y1_bu,       # Top position (bottom-up coords)
                    actual_width,   # NATIVE IMAGE WIDTH
                    actual_height   # NATIVE IMAGE HEIGHT
                ))
```

### Step 2: Match with pdftohtml XML positions
**Location:** `backend/services/xml_parser/extractors.py` (Lines 137-224)

```python
def extract_elements(page_node, fonts, images_dir, extracted_images, page_height):
    elements = []
    
    for img_node in page_node.findall('image'):
        # Get position from pdftohtml XML
        top = float(img_node.get('top', 0))
        left = float(img_node.get('left', 0))
        width = float(img_node.get('width', 0))    # <-- pdftohtml's width
        height = float(img_node.get('height', 0))  # <-- pdftohtml's height
        
        # Convert to bottom-up coordinates for matching
        xml_y0_bottomup = page_height - top - height
        xml_y1_bottomup = page_height - top
        xml_x0 = left
        xml_x1 = left + width
        
        # Find matching PyMuPDF image by intersection
        matched_image = None
        best_overlap = 0.0
        
        for img_data in extracted_images:
            filename, img_x0, img_y0, img_x1, img_y1, actual_width, actual_height = img_data
            
            # Calculate intersection area
            inter_x0 = max(xml_x0, img_x0)
            inter_y0 = max(xml_y0_bottomup, img_y0)
            inter_x1 = min(xml_x1, img_x1)
            inter_y1 = min(xml_y1_bottomup, img_y1)
            
            if inter_x1 > inter_x0 and inter_y1 > inter_y0:
                inter_area = (inter_x1 - inter_x0) * (inter_y1 - inter_y0)
                xml_area = (xml_x1 - xml_x0) * (xml_y1_bottomup - xml_y0_bottomup)
                img_area = (img_x1 - img_x0) * (img_y1 - img_y0)
                
                # Intersection over Minimum Area
                overlap = inter_area / min(xml_area, img_area) if min(xml_area, img_area) > 0 else 0
                
                if overlap > 0.5 and overlap > best_overlap:
                    best_overlap = overlap
                    matched_image = img_data
        
        # Use PyMuPDF data if matched
        if matched_image:
            filename, img_x0, img_y0, img_x1, img_y1, actual_width, actual_height = matched_image
            
            # Calculate DISPLAY dimensions from PDF layout (NOT actual pixel size)
            display_width = img_x1 - img_x0   # <-- USED FOR HTML
            display_height = img_y1 - img_y0  # <-- USED FOR HTML
            
            # Convert position back to top-down for HTML
            pymupdf_top = page_height - img_y1
            pymupdf_left = img_x0
            
            elements.append(ImageElement(
                src=filename,
                top=pymupdf_top,
                left=pymupdf_left,
                width=display_width,   # <-- PDF layout width, NOT native width
                height=display_height  # <-- PDF layout height, NOT native height
            ))
```

### How it's rendered in HTML:

**Location:** `backend/services/xml_parser/renderers.py` (Lines 64-65, 214-216, 268-270)

```python
if isinstance(el, ImageElement):
    img_data = get_image_data(el.src, images_dir)
    if img_data:
        # Use exact dimensions for fidelity
        content_parts.append(
            f'<img src="{img_data}" 
                  width="{int(el.width)}"     # <-- Display width from PDF
                  height="{int(el.height)}"   # <-- Display height from PDF
                  style="width: {el.width}px !important; 
                         height: {el.height}px !important; 
                         max-width: 100%; 
                         object-fit: contain; 
                         display: block;" />'
        )
```

### Key Points about Image Sizing:

1. **Native vs Display Size:**
   - `actual_width/height`: The image's **natural pixel dimensions** (e.g., 800×600)
   - `display_width/height`: The **rendered size in the PDF** (e.g., 150×29)

2. **Why two sizes?**
   - PDFs can scale images independently of their native resolution
   - A 1920×1080 image might be displayed at 100×50 in the PDF
   - We extract at **native resolution** for quality
   - We render at **PDF layout size** for accuracy

3. **PyMuPDF Advantages:**
   - Correctly handles CMYK color spaces
   - Preserves transparency (alpha channels)
   - Extracts images at native resolution
   - Provides accurate positioning data

---

## Summary

| Property | Source | Calculation Method | Location |
|----------|--------|-------------------|----------|
| **Page Size** | `pdftohtml` XML | Direct read from `<page>` attributes | `parser.py:29-30` |
| **Font Size** | Text element `height` | Uses rendered text height, not fontspec size | `extractors.py:253` |
| **Image Size** | PyMuPDF + XML matching | PDF layout dimensions, not native pixel size | `extractors.py:191-192` |

---

## Workflow Diagram

```
PDF Upload
    ↓
┌───────────────────────────┐
│ pdftohtml -xml -zoom 1.0  │
└───────────────────────────┘
    ↓
┌───────────────────────────┐
│ XML Output:               │
│ - Page: 595 × 841         │
│ - Fonts: size="20"        │
│ - Text: height="19"       │
│ - Images: width="150"     │
└───────────────────────────┘
    ↓
┌────────────────────────────┐
│ PyMuPDF Image Extraction   │
│ - Native: 800×600px        │
│ - Display: 150×29pt        │
│ - Position: x0,y0,x1,y1    │
└────────────────────────────┘
    ↓
┌────────────────────────────┐
│ XML Parser                 │
│ - Match images by overlap  │
│ - Use text height as size  │
│ - Extract font specs       │
└────────────────────────────┘
    ↓
┌────────────────────────────┐
│ HTML Renderer              │
│ - Page: 595×841 wrapper    │
│ - Text: font-size from h   │
│ - Images: PDF display size │
└────────────────────────────┘
    ↓
HTML Output
```

---

## Configuration Options

### Changing Page Size
To modify the output page size, adjust the `-zoom` parameter in `pdf_service.py`:

```python
cmd = [
    "pdftohtml",
    "-xml",
    "-stdout",
    "-hidden",
    "-zoom", "1.5",  # 1.5x larger: 892 × 1261
    "input.pdf"
]
```

### Font Size Priority
Currently: `text.height` (actual rendered) > `font.size` (specification)

To change priority, modify `extractors.py:253`:
```python
# Current:
font_size = height

# Alternative (use fontspec):
font_size = font_spec.size if font_spec else height
```

### Image Quality
Images are extracted at **native resolution** but displayed at **PDF layout size**.

To change extraction quality, modify `image_extractor_pymupdf.py:65-66`:
```python
# Current: Native resolution
zoom_x = native_width / rect.width
zoom_y = native_height / rect.height

# Alternative: Fixed DPI (e.g., 150 DPI)
zoom_x = zoom_y = 150 / 72  # 72 is default PDF DPI
```

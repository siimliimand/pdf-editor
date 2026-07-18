# Black Background Issue at High Zoom Levels - Root Cause Analysis

## Problem Statement
When PDF zoom level is set to 400% or higher, images in the converted HTML display with black backgrounds. This issue was previously fixed for lower zoom levels but has resurfaced at higher zoom levels.

## Root Cause Analysis

### 1. **Image Extraction Flow**

The image extraction happens in two stages:

#### Stage 1: PyMuPDF Extraction (`image_extractor_pymupdf.py`)
```python
# Lines 62-74
zoom_x = native_width / rect.width
zoom_y = native_height / rect.height
mat = fitz.Matrix(zoom_x, zoom_y)
pix = page.get_pixmap(matrix=mat, clip=rect, alpha=True)
```

**Key Issue**: The extraction zoom matrix is calculated from the image's **native dimensions**, not from the user's selected zoom level. This means:
- At 100% zoom: Image extracted at native resolution
- At 400% zoom: Image still extracted at native resolution
- The extraction quality/rendering is **independent** of user zoom

#### Stage 2: Black Background Removal (`extractors.py`)
```python
# Lines 68-135: process_image() function
# Heuristic: Check if 80% of border pixels are black
# If yes, make all black pixels transparent
```

### 2. **Why It Fails at High Zoom Levels**

The issue is **NOT** in the extraction zoom matrix, but in how PyMuPDF renders images with transparency at different scales:

1. **At Lower Zoom (100-200%)**:
   - PyMuPDF renders the image with proper alpha channel
   - Black background removal heuristic works correctly
   - Border pixels are correctly identified

2. **At Higher Zoom (400%+)**:
   - PyMuPDF may render the image differently due to scaling artifacts
   - The alpha channel might not be properly preserved
   - Black pixels might be introduced during the rendering process
   - The 80% threshold heuristic might fail if black pixels are distributed differently

### 3. **The Real Problem: Rendering vs Extraction**

The confusion comes from mixing two concepts:
- **PDF Zoom Level** (user-selected, affects layout coordinates)
- **Image Extraction Zoom** (PyMuPDF rendering quality)

Currently:
- PDF zoom level: Scales coordinates in XML (handled correctly)
- Image extraction: Uses native resolution (independent of PDF zoom)
- **Missing**: No adjustment for how PyMuPDF renders at different scales

## Why Previous Fix Worked for Lower Zoom

The previous fix likely:
1. Improved the black background detection heuristic
2. Made it work for images rendered at lower scales
3. But didn't account for rendering artifacts at higher scales

## Solutions

### Solution 1: **Improve Black Background Detection** (Recommended)
Make the heuristic more robust to handle different rendering scales:

```python
def process_image(img_path: Path, zoom_factor: float = 1.0) -> Tuple[int, int]:
    """
    Enhanced black background removal that accounts for zoom-level rendering artifacts.
    """
    # 1. More aggressive black pixel detection
    # 2. Check interior pixels, not just borders
    # 3. Use adaptive threshold based on image characteristics
    # 4. Handle semi-transparent black pixels
```

### Solution 2: **Force Consistent Rendering**
Always extract images at a consistent zoom level, regardless of PDF zoom:

```python
# In image_extractor_pymupdf.py
# Always use a fixed high-quality extraction zoom
EXTRACTION_ZOOM = 2.0  # 200% for high quality
mat = fitz.Matrix(EXTRACTION_ZOOM, EXTRACTION_ZOOM)
pix = page.get_pixmap(matrix=mat, clip=rect, alpha=True)
```

### Solution 3: **Use Different Rendering Mode**
Try different PyMuPDF rendering parameters:

```python
# Experiment with different alpha modes
pix = page.get_pixmap(matrix=mat, clip=rect, alpha=False)  # No alpha
# Then manually handle transparency
```

### Solution 4: **Pre-process with Different Color Space**
Extract in RGB first, then convert to RGBA:

```python
pix = page.get_pixmap(matrix=mat, clip=rect, alpha=False, colorspace="rgb")
# Convert to RGBA and handle transparency separately
```

## Recommended Fix Strategy

### Phase 1: Diagnostic (Immediate)
1. Add logging to see actual pixel values at different zoom levels
2. Compare extracted images at 100% vs 400% zoom
3. Identify if black pixels are in alpha channel or RGB channels

### Phase 2: Fix (Based on diagnostics)
1. **If alpha channel issue**: Adjust PyMuPDF rendering parameters
2. **If RGB channel issue**: Improve black background detection heuristic
3. **If scaling artifact**: Use consistent extraction zoom

### Phase 3: Validation
1. Test with multiple PDFs at all zoom levels (50% - 500%)
2. Verify no regression at lower zoom levels
3. Ensure performance is acceptable

## Code Locations

### Files to Modify:
1. **`backend/services/image_extractor_pymupdf.py`**
   - Line 74: PyMuPDF rendering call
   - Lines 62-68: Zoom matrix calculation

2. **`backend/services/xml_parser/extractors.py`**
   - Lines 68-135: `process_image()` function
   - Line 304: Where `process_image()` is called

3. **`backend/services/pdf_service.py`**
   - Line 89: Image extractor initialization
   - Could pass zoom_factor to extractor

## Testing Plan

### Test Cases:
1. ✅ Zoom 100%: Images should have no black background
2. ✅ Zoom 200%: Images should have no black background
3. ❌ Zoom 400%: Images currently have black background (BUG)
4. ❌ Zoom 500%: Images currently have black background (BUG)

### Test PDFs:
- Use existing test PDFs in `./backend/temp/test_pdfs`
- Include PDFs with:
  - Transparent images
  - Images with actual black backgrounds
  - Images with alpha channels
  - CMYK images

## Next Steps

1. **Add diagnostic logging** to understand the exact nature of black pixels
2. **Compare extracted images** at different zoom levels
3. **Implement the most appropriate solution** based on findings
4. **Test thoroughly** across all zoom levels

# Zoom Issue Analysis - PDF Editor Extension

## Problem Statement
Zoom functionality works correctly up to 200%, but at zoom levels above 200% (250%, 300%, 400%, 500%), the converted PDF displays at the same size as 100% zoom level.

## Root Cause Analysis

### How Zoom Currently Works

1. **Frontend (`EditorToolbar.tsx`)**:
   - User selects zoom level (50% - 500%)
   - Triggers `onZoomChange` callback

2. **Hook (`usePdfEditor.ts`)**:
   - Receives zoom change
   - Re-uploads PDF with new zoom level

3. **Backend (`pdf_service.py`)**:
   - Converts zoom percentage to decimal (e.g., 500% → 5.0)
   - Passes `-zoom 5.0` to `pdftohtml` command
   - `pdftohtml` scales ALL coordinates and dimensions by this factor

4. **XML Parser (`parser.py`)**:
   - Reads scaled dimensions from XML
   - Creates page container: `<div style="width: {width}px; height: {height}px;">`
   - At 100% zoom: `width: 840px`
   - At 500% zoom: `width: 4200px` (5x larger)

5. **Image Extraction (`image_extractor_pymupdf.py`)**:
   - **CRITICAL**: PyMuPDF extracts images at **native PDF resolution** (zoom = 1.0)
   - Returns coordinates in native scale

6. **Coordinate Matching (`extractors.py` lines 166-173)**:
   - Scales PyMuPDF coordinates by `zoom_factor` to match XML scale
   - `scaled_img_x0 = img_x0 * zoom_factor`
   - This scaling is **correct** and working as intended

### The Actual Problem

The issue is **NOT** in the backend coordinate scaling - that's working correctly. The problem is in the **frontend rendering**:

1. **RichTextEditor Container** (`RichTextEditor.tsx` line 97):
   ```tsx
   <div className="shadow-lg mx-auto bg-white min-h-screen relative">
   ```
   - Uses `mx-auto` (margin auto) to center content
   - No explicit width constraint

2. **Parent Container** (line 71):
   ```tsx
   <div className="flex-grow overflow-auto custom-scrollbar bg-gray-100 p-4">
   ```
   - Has `overflow-auto` which should enable scrolling
   - Should work correctly

3. **Possible CSS Interference**:
   - The page div has `margin: 0 auto` (line 81 in RichTextEditor.tsx)
   - This centers the page but doesn't constrain width
   - **However**, there might be an implicit max-width from Tailwind or browser defaults

### Testing Hypothesis

The most likely cause is one of these:

**A. CSS Max-Width Constraint**: 
- Some CSS rule is limiting the maximum width of the page container
- When zoom > 200%, the page width exceeds this limit and gets scaled down

**B. Browser Rendering Issue**:
- The browser might be applying automatic scaling when content is too wide
- This is unlikely but possible

**C. Missing Width on Parent**:
- The parent container might not be expanding to accommodate the larger page
- The page div might be constrained by parent width

## Solution

### Fix 1: Ensure Proper Container Width (RECOMMENDED)

Modify `parser.py` to ensure the page container can grow beyond viewport:

```python
# In parser.py, line 33, add min-width to prevent shrinking
html_parts.append(f'<div id="page-{page_number}" class="pdf-page" style="min-width: {width}px; width: {width}px; height: {height}px; position: relative; margin: 0 auto 20px auto; padding: 0px; box-sizing: border-box; background: white; box-shadow: 0 0 10px rgba(0,0,0,0.1);">')
```

### Fix 2: Remove CSS Constraints in RichTextEditor

Modify `RichTextEditor.tsx` to ensure no max-width is applied:

```tsx
/* In the style tag, add: */
div[id^="page"] {
    margin: 0 auto !important;
    background: white;
    max-width: none !important; /* Prevent any max-width constraint */
    width: auto !important; /* Allow natural width from inline styles */
}
```

### Fix 3: Ensure Parent Container Doesn't Constrain

The parent container should allow horizontal scrolling:

```tsx
<div className="flex-grow overflow-auto custom-scrollbar bg-gray-100 p-4" style={{overflowX: 'auto', overflowY: 'auto'}}>
```

## Implementation Plan

1. Add `min-width` to page container in `parser.py`
2. Update CSS in `RichTextEditor.tsx` to prevent width constraints
3. Test with zoom levels: 100%, 200%, 300%, 500%
4. Verify horizontal scrolling works correctly
5. Verify images and text scale proportionally

## Expected Behavior After Fix

- **100% zoom**: Page displays at normal size, centered
- **200% zoom**: Page is 2x larger, horizontal scroll appears if needed
- **500% zoom**: Page is 5x larger, both horizontal and vertical scroll appear
- All content (text, images, tables) scales proportionally
- No content is clipped or hidden

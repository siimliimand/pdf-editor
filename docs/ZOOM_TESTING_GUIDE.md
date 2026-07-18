# Testing Guide: Zoom Functionality Fix

## Changes Made

### 1. Backend (`parser.py`)
- Added `min-width` property to page container
- Ensures the page div maintains its full width even at high zoom levels
- Prevents browser from shrinking the container

### 2. Frontend (`RichTextEditor.tsx`)
- Added `max-width: none !important` to prevent CSS constraints
- Added `width: auto !important` to allow inline styles to take precedence
- Added explicit `overflowX` and `overflowY` styles for proper scrolling

## How to Test

### Step 1: Start the Application
```bash
# Terminal 1 - Backend
cd /home/sim/www/Extensions/PDF-editor/backend
python -m uvicorn main:app --reload

# Terminal 2 - Frontend
cd /home/sim/www/Extensions/PDF-editor/extension
npm run dev
```

### Step 2: Upload a Test PDF
1. Open the extension in your browser
2. Upload any PDF file (preferably one with text and images)

### Step 3: Test Zoom Levels

Test each zoom level and verify the behavior:

| Zoom Level | Expected Behavior |
|------------|-------------------|
| 50% | PDF appears smaller, centered, no scrollbars needed |
| 75% | PDF appears smaller, centered, no scrollbars needed |
| 100% | PDF at normal size, centered, no scrollbars needed |
| 125% | PDF slightly larger, may need scrollbars |
| 150% | PDF 1.5x larger, scrollbars appear if content exceeds viewport |
| 175% | PDF 1.75x larger, scrollbars likely needed |
| 200% | PDF 2x larger, scrollbars needed |
| **250%** | **PDF 2.5x larger, horizontal & vertical scrollbars** |
| **300%** | **PDF 3x larger, horizontal & vertical scrollbars** |
| **400%** | **PDF 4x larger, horizontal & vertical scrollbars** |
| **500%** | **PDF 5x larger, horizontal & vertical scrollbars** |

### Step 4: Verify Specific Behaviors

For zoom levels **above 200%**, check:

✅ **Page Width**: 
- Open browser DevTools (F12)
- Inspect the page div (id="page-1")
- Verify the computed width matches: `base_width * (zoom / 100)`
- Example: If base width is 840px, at 500% zoom it should be 4200px

✅ **Content Scaling**:
- Text should be proportionally larger
- Images should be proportionally larger
- Tables should maintain structure with larger cells
- All spacing should scale proportionally

✅ **Scrolling**:
- Horizontal scrollbar should appear
- Vertical scrollbar should appear if content is tall
- Both scrollbars should work smoothly
- Content should not be clipped

✅ **Centering**:
- The page should remain centered horizontally
- When scrolling horizontally, you should see equal gray space on both sides

### Step 5: Test Edge Cases

1. **Switch Between Zoom Levels**:
   - Go from 100% → 500% → 100%
   - Verify no visual glitches
   - Verify content resets properly

2. **Different PDF Types**:
   - Test with text-only PDF
   - Test with image-heavy PDF
   - Test with tables
   - Test with mixed content

3. **Browser Compatibility**:
   - Test in Chrome
   - Test in Firefox
   - Test in Edge

## Debugging

If zoom still doesn't work above 200%, check:

### 1. Inspect Page Container
```javascript
// In browser console
const page = document.querySelector('[id^="page"]');
console.log('Width:', page.style.width);
console.log('Min-Width:', page.style.minWidth);
console.log('Computed Width:', window.getComputedStyle(page).width);
console.log('Max-Width:', window.getComputedStyle(page).maxWidth);
```

Expected output at 500% zoom (if base is 840px):
```
Width: 4200px
Min-Width: 4200px
Computed Width: 4200px
Max-Width: none
```

### 2. Check Parent Container
```javascript
// In browser console
const parent = document.querySelector('.overflow-auto');
console.log('Overflow-X:', window.getComputedStyle(parent).overflowX);
console.log('Overflow-Y:', window.getComputedStyle(parent).overflowY);
console.log('Width:', window.getComputedStyle(parent).width);
```

Expected output:
```
Overflow-X: auto
Overflow-Y: auto
Width: <viewport width>
```

### 3. Check for CSS Conflicts
```javascript
// In browser console
const page = document.querySelector('[id^="page"]');
const styles = window.getComputedStyle(page);
console.log('All width-related properties:');
console.log('width:', styles.width);
console.log('min-width:', styles.minWidth);
console.log('max-width:', styles.maxWidth);
console.log('box-sizing:', styles.boxSizing);
```

## Success Criteria

✅ Zoom works correctly from 50% to 500%
✅ Content scales proportionally at all zoom levels
✅ Scrollbars appear when content exceeds viewport
✅ No content is clipped or hidden
✅ Page remains centered
✅ Switching between zoom levels works smoothly
✅ Images maintain correct aspect ratio and size
✅ Text remains readable and properly sized

## Rollback

If issues occur, revert these changes:

```bash
cd /home/sim/www/Extensions/PDF-editor
git diff backend/services/xml_parser/parser.py
git diff extension/src/components/RichTextEditor/RichTextEditor.tsx

# To revert:
git checkout backend/services/xml_parser/parser.py
git checkout extension/src/components/RichTextEditor/RichTextEditor.tsx
```

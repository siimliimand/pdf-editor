# Debug Guide: Zoom Display Issue

## Quick Browser Console Check

After uploading a PDF and setting zoom to 300% or 500%, open the browser console (F12) and run these commands:

### 1. Check Page Container Width
```javascript
const page = document.querySelector('[id^="page"]');
console.log('=== PAGE CONTAINER ===');
console.log('Inline width:', page.style.width);
console.log('Inline min-width:', page.style.minWidth);
console.log('Computed width:', window.getComputedStyle(page).width);
console.log('Scroll width:', page.scrollWidth);
console.log('Client width:', page.clientWidth);
```

**Expected at 500% zoom** (if base width is 840px):
- Inline width: `4200px`
- Computed width: `4200px`
- Scroll width: `4200` (number)

### 2. Check ProseMirror Container
```javascript
const prosemirror = document.querySelector('.ProseMirror');
console.log('=== PROSEMIRROR ===');
console.log('Computed width:', window.getComputedStyle(prosemirror).width);
console.log('Scroll width:', prosemirror.scrollWidth);
```

**Expected**: Should be at least as wide as the page container

### 3. Check Font Sizes
```javascript
const spans = document.querySelectorAll('[id^="page"] span');
console.log('=== FONT SIZES (first 5 text elements) ===');
Array.from(spans).slice(0, 5).forEach((span, i) => {
    console.log(`Span ${i}:`, window.getComputedStyle(span).fontSize);
});
```

**Expected at 500% zoom**: Font sizes should be 5x larger than at 100% zoom

### 4. Check Image Sizes
```javascript
const images = document.querySelectorAll('[id^="page"] img');
console.log('=== IMAGE SIZES ===');
Array.from(images).forEach((img, i) => {
    console.log(`Image ${i}:`, {
        width: img.style.width,
        height: img.style.height,
        computedWidth: window.getComputedStyle(img).width
    });
});
```

**Expected at 500% zoom**: Images should be 5x larger than at 100% zoom

### 5. Check for CSS Transforms
```javascript
const page = document.querySelector('[id^="page"]');
let el = page;
console.log('=== CHECKING FOR TRANSFORMS ===');
while (el && el !== document.body) {
    const transform = window.getComputedStyle(el).transform;
    if (transform && transform !== 'none') {
        console.log('Transform found on:', el.className, 'Transform:', transform);
    }
    el = el.parentElement;
}
```

**Expected**: Should show "none" or no transforms

## What to Look For

### If zoom is NOT working:

1. **Page width is correct but content appears small**:
   - Check if there's a CSS transform scaling down
   - Check if font sizes are actually scaled in the HTML
   - Check if there's a parent container constraining size

2. **Page width is NOT correct** (e.g., still 840px at 500% zoom):
   - Backend is not applying zoom correctly
   - Check backend logs for zoom_factor value
   - Verify pdftohtml is receiving correct -zoom parameter

3. **Page width is correct AND font sizes are correct, but still looks small**:
   - Likely a CSS transform or scale being applied
   - Check all parent elements for transforms

## Manual Verification

### Compare 100% vs 500% zoom:

1. Upload PDF at 100% zoom
2. In console, run:
```javascript
const page100 = document.querySelector('[id^="page"]');
const width100 = parseInt(window.getComputedStyle(page100).width);
const fontSize100 = window.getComputedStyle(page100.querySelector('span')).fontSize;
console.log('100% zoom:', {width: width100, fontSize: fontSize100});
```

3. Change zoom to 500%
4. In console, run:
```javascript
const page500 = document.querySelector('[id^="page"]');
const width500 = parseInt(window.getComputedStyle(page500).width);
const fontSize500 = window.getComputedStyle(page500.querySelector('span')).fontSize;
console.log('500% zoom:', {width: width500, fontSize: fontSize500});
console.log('Ratio:', {width: width500/width100, fontSize: parseFloat(fontSize500)/parseFloat(fontSize100)});
```

**Expected ratio**: Both should be ~5.0 (or exactly 5.0)

## Recent Changes Made

1. ✅ Removed `width: auto !important` that was overriding inline styles
2. ✅ Removed wrapper div that might constrain width
3. ✅ Added `width: fit-content` to ProseMirror to allow growth
4. ✅ Kept `max-width: none !important` to prevent constraints
5. ✅ Added `min-width` to page container in backend

## If Still Not Working

If the issue persists after these changes, the problem is likely:

1. **TipTap/ProseMirror is modifying the HTML**: The editor might be stripping or modifying inline styles
2. **Browser zoom is interfering**: Check if browser zoom (Ctrl+/-) is set to something other than 100%
3. **Extension-specific CSS**: Check if there are any extension-specific stylesheets being injected

Run this to check for unexpected stylesheets:
```javascript
Array.from(document.styleSheets).forEach((sheet, i) => {
    try {
        console.log(`Stylesheet ${i}:`, sheet.href || 'inline', sheet.cssRules.length, 'rules');
    } catch(e) {
        console.log(`Stylesheet ${i}: Cannot access (CORS)`);
    }
});
```

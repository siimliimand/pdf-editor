# Table Row Height Analysis - Summary Report

## Problem Statement

The table rows in the generated HTML are consistently **shorter than expected**, causing all horizontal borders to be positioned approximately **2.37px too high** compared to the PDF source.

## Key Findings

### 1. Systematic Offset
- **Average offset**: -2.37px per border
- **Total height difference**: -18.29px (table is 18.29px shorter than expected)
- **Borders analyzed**: 17 out of 18 expected positions
- **Pattern**: Consistent offset across all rows (not random)

### 2. Expected vs Actual Border Positions

| Expected Y | Actual Y | Difference | Row Content |
|------------|----------|------------|-------------|
| 118.0 | 118.0 | ✓ 0.01 | Table start |
| 136.0 | 133.4 | -2.57 | After subtitle |
| 168.0 | 165.4 | -2.59 | After "Mobiiltelefon" |
| 181.0 | 178.7 | -2.27 | After "Arv" header |
| 195.0 | 192.2 | -2.76 | After data row |
| 209.0 | 205.7 | -3.25 | After data row |
| 236.0 | 232.8 | -3.23 | After "Kokku" |
| 252.0 | 249.4 | -2.61 | After subtotal |
| ... | ... | ... | ... |

### 3. Row Height Statistics
- **Total rows**: 17
- **Average height**: 16.36px
- **Min height**: 13.32px
- **Max height**: 35.75px

### 4. Current Rendering Settings
- **Line-height**: 1.0 (hardcoded)
- **Font-size**: Varies (12px, 13.33px, 14.67px, 16px)
- **Padding**: 0px (no padding-top or padding-bottom)
- **Borders**: 1px solid #888888

## Root Cause Analysis

### Observation from Row 0:
```
Expected content height: 13.33px (font-size × line-height)
Actual row height: 15.45px
Difference: +2.11px
```

This suggests that **row heights ARE being calculated correctly** in the HTML (they include extra space), but the **expected border positions from the PDF are based on tighter spacing**.

### Observation from Row 1:
```
Expected content height: 16.00px
Actual row height: 31.97px
Difference: +15.97px (this row has 2 lines of text)
```

This row contains two spans with different font sizes, suggesting **multi-line content** or **vertical spacing between elements**.

## Possible Causes

1. **Border width not accounted for**: The 1px borders might be added to row height instead of being part of it
2. **Line-height calculation**: Even with line-height: 1.0, browsers may add minimal spacing
3. **Font metrics**: Actual font rendering height may differ from font-size due to ascenders/descenders
4. **Padding/margin from parent elements**: Table or cell-level spacing
5. **Expected positions may be from PDF coordinates**: PDF coordinates might use different measurement system

## Recommendations

### Option 1: Adjust Expected Values (Quick Fix)
Update `EXPECTED_BORDER_Y_POSITIONS` to match actual rendering:
```python
EXPECTED_BORDER_Y_POSITIONS = [
    118.0,   # Keep (matches exactly)
    133.4,   # Was 136.0
    165.4,   # Was 168.0
    178.7,   # Was 181.0
    # ... etc
]
```

### Option 2: Fix Row Height Calculation (Proper Fix)
Investigate and adjust the row height calculation in the grid table renderer:
- Check `backend/services/xml_parser/renderers/grid_table/main.py`
- Look for where row heights are calculated
- Add compensation factor: `height * 1.014` (approximately)

### Option 3: Investigate PDF Coordinate System
- Verify if PDF Y-coordinates need conversion
- Check if zoom_level=100.0 is correctly applied
- Ensure DPI conversion (72pt → 96px) is consistent

## Test Scripts Created

1. **`test_table_rows.py`**: Focused test suite for row positions and borders
2. **`analyze_table_rows.py`**: Detailed analysis comparing expected vs actual positions
3. **`diagnose_row_heights.py`**: Deep dive into CSS properties and height calculations

## Next Steps

1. **Verify PDF coordinates**: Extract actual Y-positions from PDF using PyMuPDF
2. **Compare with HTML**: Ensure coordinate systems match
3. **Adjust calculation**: Apply correction factor if needed
4. **Update tests**: Either fix the rendering or update expected values

---

**Note**: The offset is systematic and predictable, suggesting a simple scaling or measurement issue rather than a fundamental rendering problem.

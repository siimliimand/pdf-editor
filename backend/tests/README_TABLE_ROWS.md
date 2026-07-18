# Table Row Testing Scripts

This directory contains focused scripts for analyzing and testing table row rendering in the PDF-to-HTML conversion process.

## Scripts Overview

### 1. `test_table_rows.py` - Main Test Suite
**Purpose**: Pytest-compatible test suite focused exclusively on table row positioning and borders.

**Features**:
- Tests row count
- Validates border positions against expected Y-coordinates
- Analyzes row heights
- Checks border coverage
- Verifies specific important rows (headers, totals, etc.)

**Usage**:
```bash
# Run with pytest
pytest tests/test_table_rows.py -v

# Run standalone
python tests/test_table_rows.py
```

**Expected Output**: Pass/fail for each test with detailed diagnostics

---

### 2. `analyze_table_rows.py` - Position Analysis
**Purpose**: Detailed comparison of expected vs actual border positions.

**Features**:
- Extracts all border Y-positions from rendered HTML
- Compares with expected positions from PDF
- Calculates systematic offset
- Provides row-by-row breakdown
- Shows total height discrepancy

**Usage**:
```bash
python tests/analyze_table_rows.py
```

**Expected Output**:
```
TABLE ANALYSIS
- Row-by-row positions and heights
- Border position comparison table
- Offset analysis (average: -2.37px)
- Row height statistics
```

---

### 3. `diagnose_row_heights.py` - CSS Diagnostic
**Purpose**: Deep dive into CSS properties to identify root cause of height discrepancies.

**Features**:
- Examines font-size, line-height, padding for each row
- Calculates expected vs actual heights
- Identifies which CSS properties contribute to height
- Suggests potential fixes

**Usage**:
```bash
python tests/diagnose_row_heights.py
```

**Expected Output**:
```
ROW HEIGHT DIAGNOSTIC
- Detailed CSS properties for first 5 rows
- Height calculation breakdown
- Potential fixes and recommendations
```

---

### 4. `TABLE_ROW_ANALYSIS.md` - Summary Report
**Purpose**: Comprehensive documentation of findings and recommendations.

**Contents**:
- Problem statement
- Key findings with data tables
- Root cause analysis
- Recommendations (3 options)
- Next steps

---

## Quick Start

To investigate table row issues:

1. **First, run the analysis**:
   ```bash
   python tests/analyze_table_rows.py
   ```
   This shows you the overall offset pattern.

2. **Then, diagnose the cause**:
   ```bash
   python tests/diagnose_row_heights.py
   ```
   This reveals CSS-level details.

3. **Finally, run the tests**:
   ```bash
   python tests/test_table_rows.py
   ```
   This validates against expected positions.

4. **Read the summary**:
   ```bash
   cat tests/TABLE_ROW_ANALYSIS.md
   ```

---

## Key Findings

- **Systematic offset**: All borders are ~2.37px too high
- **Total discrepancy**: Table is 18.29px shorter than expected
- **Pattern**: Consistent across all 17 rows
- **Cause**: Likely font metrics, border handling, or coordinate conversion

---

## Expected Border Y Positions

These positions are from the PDF and represent where horizontal borders should appear:

```python
EXPECTED_BORDER_Y_POSITIONS = [
    118.0,  # Table start
    136.0,  # After subtitle
    168.0,  # After "Mobiiltelefon" header
    181.0,  # After "Arv" column header
    195.0,  # After data row
    209.0,  # After data row
    202.0,  # (Note: out of order - verify)
    236.0,  # After "Kokku" total
    252.0,  # After subtotal
    266.0,  # After section
    301.0,  # Second section start
    315.0,  # After header
    328.0,  # After data row
    342.0,  # After data row
    355.0,  # After data row
    369.0,  # After data row
    385.0,  # After "Kokku" total
    399.0   # Table end
]
```

---

## Test PDF

All scripts use: `./temp/test_pdfs/second-page.pdf` (Elisa invoice)

Make sure this file exists before running the scripts.

---

## Related Files

- `test_elisa_invoice.py` - Original comprehensive test suite
- `backend/services/xml_parser/renderers/grid_table/main.py` - Grid table renderer
- `backend/services/xml_parser/renderers/grid_table/cell.py` - Cell renderer

---

## Contributing

When adding new tests or analysis:

1. Keep scripts focused on specific aspects
2. Use clear, descriptive output
3. Document findings in markdown files
4. Update this README

---

## Troubleshooting

**Q: Tests fail with "PDF not found"**  
A: Ensure `./temp/test_pdfs/second-page.pdf` exists

**Q: All borders show large offsets**  
A: This is expected - see `TABLE_ROW_ANALYSIS.md` for explanation

**Q: How do I fix the offset?**  
A: See "Recommendations" section in `TABLE_ROW_ANALYSIS.md`

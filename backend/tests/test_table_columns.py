"""
Test table column detection for Elisa invoice second-page.pdf

This test verifies that table columns are correctly detected with:
- Correct number of columns (6, not 7)
- Correct column widths (first column should be much wider)
- Proper handling of merged cells/column spanning

Expected structure from PDF (analyzing the table):
- Column 1: Wide column for descriptions (~35% of table width)
- Column 2: "Arv" (count)
- Column 3: "Kestus/Maht (KB)" (duration/volume)
- Column 4: "Summa" (amount)
- Column 5: "Käibemaks" (VAT)
- Column 6: "Summa kokku" (total)

Issues to fix:
1. Extra 7th column detected (should be 6 columns)
2. First column width incorrect (should be ~35%, currently ~14%)
3. Text spanning multiple columns not handled (e.g., "SeoWeb OÜ | Kliendinumber: 20147609...")
"""
import asyncio
import pytest
import pytest_asyncio
from pathlib import Path
import sys
import os

# Add parent directory to path for standalone execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.pdf_service import convert_pdf_to_html
from bs4 import BeautifulSoup
import re


class TestTableColumns:
    """Test suite for table column detection"""
    
    # Expected column count from PDF analysis
    EXPECTED_COLUMN_COUNT = 6
    
    # Expected first column width percentage (from PDF measurements)
    # In PDF: first column is ~178.6px out of ~513px table width = ~35%
    EXPECTED_FIRST_COLUMN_WIDTH_PCT = 35.0
    TOLERANCE_PCT = 3.0  # Allow 3% deviation
    
    @pytest_asyncio.fixture
    async def processed_html(self):
        """Process the test PDF and return HTML"""
        pdf_path = Path("./temp/test_pdfs/second-page.pdf")
        
        if not pdf_path.exists():
            pytest.skip(f"Test PDF not found at {pdf_path}")
        
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        html_content = await convert_pdf_to_html(pdf_content, zoom_level=100.0)
        return html_content
    
    def extract_style_value(self, element, property_name):
        """Extract a specific CSS property from element's style"""
        style = element.get('style', '')
        pattern = rf'{property_name}:\s*([^;]+)'
        match = re.search(pattern, style, re.IGNORECASE)
        return match.group(1).strip() if match else None
    
    # =========================================================================
    # Column Count Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_column_count(self, processed_html):
        """
        Test that the table has exactly 6 columns, not 7.
        
        The PDF has 6 columns:
        1. Description (wide)
        2. Arv (count)
        3. Kestus/Maht (KB)
        4. Summa
        5. Käibemaks
        6. Summa kokku
        """
        soup = BeautifulSoup(processed_html, 'html.parser')
        
        # Find the main table
        tables = soup.find_all('table')
        
        print(f"\nFound {len(tables)} table(s)")
        
        for table_idx, table in enumerate(tables):
            # Check colgroup for column definitions
            colgroup = table.find('colgroup')
            
            if colgroup:
                cols = colgroup.find_all('col')
                col_count = len(cols)
                
                print(f"\nTable {table_idx + 1}:")
                print(f"  Column count: {col_count}")
                print(f"  Expected: {self.EXPECTED_COLUMN_COUNT}")
                
                # Print column widths for debugging
                for i, col in enumerate(cols):
                    width = self.extract_style_value(col, 'width') or self.extract_style_value(col, 'min-width')
                    print(f"  Column {i + 1}: width={width}")
                
                # Main assertion
                assert col_count == self.EXPECTED_COLUMN_COUNT, \
                    f"Table {table_idx + 1} has {col_count} columns, expected {self.EXPECTED_COLUMN_COUNT}"
                
                print(f"  ✓ Column count is correct")
    
    # =========================================================================
    # Column Width Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_first_column_width(self, processed_html):
        """
        Test that the first column is approximately 35% of table width.
        
        In the PDF, the first column (description) is much wider than other columns.
        PDF measurements: ~178.6px out of ~513px = ~35%
        """
        soup = BeautifulSoup(processed_html, 'html.parser')
        
        # Find the main table
        tables = soup.find_all('table')
        
        for table_idx, table in enumerate(tables):
            colgroup = table.find('colgroup')
            
            if colgroup:
                cols = colgroup.find_all('col')
                
                if len(cols) > 0:
                    first_col = cols[0]
                    width_str = self.extract_style_value(first_col, 'width') or \
                                self.extract_style_value(first_col, 'min-width')
                    
                    if width_str and '%' in width_str:
                        width_pct = float(re.sub(r'[^0-9.]', '', width_str))
                        
                        print(f"\nTable {table_idx + 1} - First column:")
                        print(f"  Width: {width_pct}%")
                        print(f"  Expected: ~{self.EXPECTED_FIRST_COLUMN_WIDTH_PCT}%")
                        print(f"  Tolerance: ±{self.TOLERANCE_PCT}%")
                        
                        min_width = self.EXPECTED_FIRST_COLUMN_WIDTH_PCT - self.TOLERANCE_PCT
                        max_width = self.EXPECTED_FIRST_COLUMN_WIDTH_PCT + self.TOLERANCE_PCT
                        
                        assert min_width <= width_pct <= max_width, \
                            f"First column width {width_pct}% is outside expected range [{min_width}%, {max_width}%]"
                        
                        print(f"  ✓ First column width is correct")
    
    # =========================================================================
    # Merged Cell Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_merged_cell_detection(self, processed_html):
        """
        Test that merged cells are properly detected.
        
        The subtitle row "SeoWeb OÜ | Kliendinumber: 20147609 | Arve nr: 2049322459 | Periood: 1. november - 30. november 2025"
        should span all columns (colspan=6).
        """
        soup = BeautifulSoup(processed_html, 'html.parser')
        
        # Find cells containing the subtitle text
        subtitle_text = "SeoWeb OÜ | Kliendinumber"
        
        for td in soup.find_all('td'):
            if subtitle_text in td.get_text():
                colspan = td.get('colspan', '1')
                colspan_int = int(colspan)
                
                print(f"\nSubtitle cell:")
                print(f"  Text: {td.get_text()[:50]}...")
                print(f"  Colspan: {colspan_int}")
                print(f"  Expected: {self.EXPECTED_COLUMN_COUNT}")
                
                # This cell should span all columns
                assert colspan_int == self.EXPECTED_COLUMN_COUNT, \
                    f"Subtitle cell has colspan={colspan_int}, expected {self.EXPECTED_COLUMN_COUNT}"
                
                print(f"  ✓ Merged cell detected correctly")
                break
    
    @pytest.mark.asyncio
    async def test_phone_header_merged_cell(self, processed_html):
        """
        Test that phone header rows have proper column spanning.
        
        The row "Mobiiltelefon: 55526556 | SeoWeb OÜ | Pakett: Äripakett D 1 |"
        should span all columns.
        """
        soup = BeautifulSoup(processed_html, 'html.parser')
        
        phone_text = "Mobiiltelefon: 55526556"
        
        for td in soup.find_all('td'):
            text = td.get_text()
            if phone_text in text and "Pakett" in text:
                colspan = td.get('colspan', '1')
                colspan_int = int(colspan)
                
                print(f"\nPhone header cell:")
                print(f"  Text: {text[:50]}...")
                print(f"  Colspan: {colspan_int}")
                print(f"  Expected: {self.EXPECTED_COLUMN_COUNT}")
                
                # This cell should span all columns
                assert colspan_int == self.EXPECTED_COLUMN_COUNT, \
                    f"Phone header cell has colspan={colspan_int}, expected {self.EXPECTED_COLUMN_COUNT}"
                
                print(f"  ✓ Phone header merged cell detected correctly")
                break
    
    # =========================================================================
    # Column Header Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_column_headers(self, processed_html):
        """
        Test that column headers are in separate cells.
        
        The header row should have individual cells for:
        "Arv", "Kestus/Maht (KB)", "Summa", "Käibemaks", "Summa kokku"
        """
        soup = BeautifulSoup(processed_html, 'html.parser')
        
        expected_headers = ["Arv", "Kestus/Maht (KB)", "Summa", "Käibemaks", "Summa kokku"]
        
        # Find the row containing these headers
        for tr in soup.find_all('tr'):
            cells = tr.find_all('td')
            cell_texts = [cell.get_text().strip() for cell in cells]
            
            # Check if this row contains the header texts
            if "Arv" in cell_texts and "Summa kokku" in cell_texts:
                print(f"\nFound header row:")
                print(f"  Cells: {cell_texts}")
                print(f"  Expected headers: {expected_headers}")
                
                # Check that each header is in its own cell
                for header in expected_headers:
                    found = any(header in text for text in cell_texts)
                    assert found, f"Header '{header}' not found in separate cell"
                    print(f"  ✓ Found header: {header}")
                
                break
    
    # =========================================================================
    # Debug Output
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_print_table_structure(self, processed_html):
        """Print table structure for debugging"""
        soup = BeautifulSoup(processed_html, 'html.parser')
        
        tables = soup.find_all('table')
        print(f"\n{'='*80}")
        print(f"TABLE COLUMN STRUCTURE")
        print(f"{'='*80}")
        
        for table_idx, table in enumerate(tables):
            print(f"\n--- Table {table_idx + 1} ---")
            
            # Print colgroup
            colgroup = table.find('colgroup')
            if colgroup:
                cols = colgroup.find_all('col')
                print(f"Columns: {len(cols)}")
                for i, col in enumerate(cols):
                    width = self.extract_style_value(col, 'width') or \
                            self.extract_style_value(col, 'min-width')
                    print(f"  Col {i + 1}: {width}")
            
            # Print first few rows
            rows = table.find_all('tr')
            for row_idx, row in enumerate(rows[:5]):  # Only first 5 rows
                cells = row.find_all(['td', 'th'])
                print(f"\n  Row {row_idx + 1}:")
                for cell_idx, cell in enumerate(cells):
                    text = cell.get_text().strip()[:40]
                    colspan = cell.get('colspan', '1')
                    print(f"    Cell {cell_idx + 1} (colspan={colspan}): {text}")


# Standalone test runner for manual testing
async def run_manual_test():
    """Run tests manually without pytest"""
    print("=" * 80)
    print("Table Column Detection Test - second-page.pdf")
    print("=" * 80)
    
    test = TestTableColumns()
    
    # Get processed HTML
    pdf_path = Path("./temp/test_pdfs/second-page.pdf")
    if not pdf_path.exists():
        print(f"Error: Test PDF not found at {pdf_path}")
        return
    
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    print("\nProcessing PDF...")
    html_content = await convert_pdf_to_html(pdf_content, zoom_level=100.0)
    
    # Save for inspection
    output_path = Path("./temp/table-columns-test-output.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"HTML saved to: {output_path}")
    
    # Run individual tests
    tests = [
        ("Column Count", test.test_column_count),
        ("First Column Width", test.test_first_column_width),
        ("Merged Cell Detection", test.test_merged_cell_detection),
        ("Phone Header Merged Cell", test.test_phone_header_merged_cell),
        ("Column Headers", test.test_column_headers),
        ("Table Structure", test.test_print_table_structure),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print("\n" + "=" * 80)
        print(f"Test: {test_name}")
        print("=" * 80)
        try:
            await test_func(html_content)
            print(f"✓ PASSED")
            passed += 1
        except (AssertionError, Exception) as e:
            print(f"❌ FAILED: {e}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"Test Summary: {passed} passed, {failed} failed")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_manual_test())

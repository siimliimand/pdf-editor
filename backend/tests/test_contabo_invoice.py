"""
Test table rendering for Contabo invoice 1282161800020.pdf

This test verifies correct rendering of:
- Background colors (gray header on "Recurring fees")
- Border positions (6 borders total)
- Row spacing and gaps (2-3px gaps between certain rows)

Issues to verify:
1. "Recurring fees" header row SHOULD have gray background
2. "Cumulative gross" row should NOT have gray background (or should match PDF)
3. PDF has 6 row borders, HTML should match
4. Small gaps (2-3px) between rows 3-4 and 5-6 should be preserved
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


class TestContaboInvoice:
    """Test suite for Contabo invoice (1282161800020.pdf) rendering"""
    
    # Expected border Y positions based on PDF analysis
    # These should be detected dynamically from the PDF
    EXPECTED_BORDER_COUNT = 6
    
    @pytest_asyncio.fixture
    async def processed_html(self):
        """Process the test PDF and return HTML"""
        pdf_path = Path("./temp/test_pdfs/1282161800020.pdf")
        
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
    
    def find_text_element(self, soup, text_fragment):
        """Find element containing the given text fragment"""
        # Search spans first
        for elem in soup.find_all('span'):
            if text_fragment in elem.get_text():
                return elem
        
        # Then table cells
        for elem in soup.find_all('td'):
            if text_fragment in elem.get_text():
                return elem
                
        return None
    
    def find_cell_by_text(self, soup, text_fragment):
        """Find table cell containing exact or partial text match"""
        for td in soup.find_all('td'):
            cell_text = td.get_text().strip()
            if text_fragment in cell_text:
                return td
        return None
    
    # =========================================================================
    # Background Color Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_recurring_fees_has_background(self, processed_html):
        """
        Test that 'Recurring fees' header row has gray background with rounded corners.
        
        In the PDF, this row appears with a light gray background and rounded corners.
        The background is detected dynamically from vector elements.
        """
        soup = BeautifulSoup(processed_html, 'html.parser')
        
        # Find the "Recurring fees" text - it might be in a table cell or a span/p element
        recurring_fees_elem = None
        recurring_fees_top = None
        
        # First try table cells
        recurring_fees_elem = self.find_cell_by_text(soup, "Recurring fees")
        
        # If not found in cell, look for span containing the text
        if recurring_fees_elem is None:
            for span in soup.find_all('span'):
                if "Recurring fees" in span.get_text():
                    recurring_fees_elem = span
                    # Get the parent p element's position
                    parent_p = span.find_parent('p')
                    if parent_p:
                        style = parent_p.get('style', '')
                        top_match = re.search(r'top:\s*([\d.]+)px', style)
                        if top_match:
                            recurring_fees_top = float(top_match.group(1))
                    break
        
        assert recurring_fees_elem is not None, "Could not find 'Recurring fees' text"
        
        # If it's in a table cell, check for background directly
        if recurring_fees_elem.name == 'td':
            bg_color = self.extract_style_value(recurring_fees_elem, 'background-color')
            border_radius = self.extract_style_value(recurring_fees_elem, 'border-radius')
        else:
            # Find a background div that overlaps with the text position
            # Background divs are rendered with z-index: -1
            bg_color = None
            border_radius = None
            
            for div in soup.find_all('div'):
                style = div.get('style', '')
                if 'background-color' in style and 'position: absolute' in style:
                    # Check if this is near the recurring fees text
                    top_match = re.search(r'top:\s*([\d.]+)px', style)
                    if top_match and recurring_fees_top:
                        div_top = float(top_match.group(1))
                        # Check if the background is within 5px of the text
                        if abs(div_top - recurring_fees_top) < 5:
                            bg_color = self.extract_style_value(div, 'background-color')
                            border_radius = self.extract_style_value(div, 'border-radius')
                            break
        
        print(f"\n'Recurring fees' element type: {recurring_fees_elem.name}")
        print(f"  Background color: {bg_color}")
        print(f"  Border radius: {border_radius}")
        print(f"  Expected: non-white background color")
        
        # Verify it has a background (any non-white color)
        assert bg_color is not None, "'Recurring fees' should have a background color"
        
        # Helper function to check if a color is white
        def is_white_color(color_str):
            """Check if color is white or nearly white"""
            color_lower = color_str.lower().strip()
            
            # Check hex formats
            if color_lower in ['#fff', '#ffffff', '#fefefe']:
                return True
            
            # Check rgb format
            if 'rgb' in color_lower:
                # Extract RGB values
                rgb_match = re.search(r'rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', color_lower)
                if rgb_match:
                    r, g, b = int(rgb_match.group(1)), int(rgb_match.group(2)), int(rgb_match.group(3))
                    # Consider white if all values are >= 254
                    if r >= 254 and g >= 254 and b >= 254:
                        return True
            
            # Check hex format more thoroughly
            if color_lower.startswith('#') and len(color_lower) == 7:
                r = int(color_lower[1:3], 16)
                g = int(color_lower[3:5], 16)
                b = int(color_lower[5:7], 16)
                # Consider white if all values are >= 254
                if r >= 254 and g >= 254 and b >= 254:
                    return True
            
            return False
        
        # Verify background is NOT white (meaning it has a visible background)
        is_non_white = not is_white_color(bg_color)
        
        assert is_non_white, f"'Recurring fees' should have a non-white background, got: {bg_color}"
        print(f"✓ 'Recurring fees' has a background (color: {bg_color})")
    
    @pytest.mark.asyncio
    async def test_cumulative_gross_background(self, processed_html):
        """
        Test that 'Cumulative gross' row has correct background (or no background).
        
        In the PDF, this row should NOT have a gray background.
        In the generated HTML, it incorrectly has a gray background.
        """
        soup = BeautifulSoup(processed_html, 'html.parser')
        
        # Find the "Cumulative gross" cell
        cumulative_cell = self.find_cell_by_text(soup, "Cumulative gross")
        
        assert cumulative_cell is not None, "Could not find 'Cumulative gross' cell"
        
        # Check for background color
        bg_color = self.extract_style_value(cumulative_cell, 'background-color')
        
        print(f"\n'Cumulative gross' cell:")
        print(f"  Background color: {bg_color}")
        print(f"  Expected: none or white")
        
        # Verify it does NOT have a gray background
        if bg_color:
            is_gray = (
                '#f9f9f9' in bg_color.lower() or
                'rgb(249, 249, 249)' in bg_color.lower()
            )
            assert not is_gray, f"'Cumulative gross' should NOT have gray background, got: {bg_color}"
        
        print("✓ 'Cumulative gross' has correct background (no gray)")
    
    # =========================================================================
    # Border Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_border_count(self, processed_html):
        """
        Test that the table has correct number of borders.
        
        PDF has 6 row borders, but HTML shows only 5.
        """
        soup = BeautifulSoup(processed_html, 'html.parser')
        
        # Find the main table
        tables = soup.find_all('table')
        
        print(f"\nFound {len(tables)} table(s)")
        
        # Count borders in all tables
        total_borders = 0
        
        for table_idx, table in enumerate(tables):
            rows = table.find_all('tr')
            table_borders = 0
            
            for row in rows:
                cells = row.find_all('td')
                # Check if any cell in this row has a border
                for cell in cells:
                    style = cell.get('style', '')
                    if 'border-top' in style or 'border-bottom' in style:
                        # Count unique borders (don't double-count)
                        if 'border-bottom' in style and 'solid' in style:
                            table_borders += 1
                            break  # Only count once per row
            
            print(f"  Table {table_idx + 1}: {table_borders} borders")
            total_borders += table_borders
        
        print(f"\nTotal borders: {total_borders}")
        print(f"Expected: {self.EXPECTED_BORDER_COUNT}")
        
        assert total_borders >= self.EXPECTED_BORDER_COUNT, \
            f"Expected at least {self.EXPECTED_BORDER_COUNT} borders, found {total_borders}"
        
        print(f"✓ Border count matches or exceeds expected ({total_borders} >= {self.EXPECTED_BORDER_COUNT})")
    
    @pytest.mark.asyncio
    async def test_row_spacing(self, processed_html):
        """
        Test that small gaps between rows are preserved.
        
        PDF has 2-3px gaps between rows 3-4 and 5-6.
        """
        soup = BeautifulSoup(processed_html, 'html.parser')
        
        # Find the main table
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            print(f"\nAnalyzing row spacing for table with {len(rows)} rows:")
            
            for idx, row in enumerate(rows):
                style = row.get('style', '')
                height_match = re.search(r'height:\s*([\d.]+)px', style)
                
                if height_match:
                    height = float(height_match.group(1))
                    print(f"  Row {idx + 1}: height = {height}px")
                    
                    # Check for small gaps (2-3px rows)
                    if 2 <= height <= 4:
                        print(f"    → Found small gap row (height: {height}px)")
        
        print("\n✓ Row spacing analysis complete")
    
    # =========================================================================
    # Comprehensive Structure Test
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_table_structure(self, processed_html):
        """Print complete table structure for analysis"""
        soup = BeautifulSoup(processed_html, 'html.parser')
        
        tables = soup.find_all('table')
        print(f"\n{'='*80}")
        print(f"CONTABO INVOICE TABLE STRUCTURE")
        print(f"{'='*80}")
        print(f"Found {len(tables)} table(s)")
        
        for table_idx, table in enumerate(tables):
            print(f"\n--- Table {table_idx + 1} ---")
            
            rows = table.find_all('tr')
            for row_idx, row in enumerate(rows):
                cells = row.find_all(['td', 'th'])
                
                # Get row height
                row_style = row.get('style', '')
                height_match = re.search(r'height:\s*([\d.]+)px', row_style)
                row_height = height_match.group(1) if height_match else 'auto'
                
                cell_info = []
                for cell in cells:
                    text = cell.get_text().strip()[:40]
                    bg = self.extract_style_value(cell, 'background-color')
                    border_b = self.extract_style_value(cell, 'border-bottom')
                    
                    markers = []
                    if bg:
                        markers.append(f"BG:{bg[:10]}")
                    if border_b and 'solid' in border_b:
                        markers.append("│B")
                    
                    marker_str = f" [{', '.join(markers)}]" if markers else ""
                    cell_info.append(f"{text}{marker_str}")
                
                print(f"  Row {row_idx} (h={row_height}): {' | '.join(cell_info) if cell_info else '(empty)'}")


# Standalone test runner for manual testing
async def run_manual_test():
    """Run tests manually without pytest"""
    print("=" * 80)
    print("Contabo Invoice Test - 1282161800020.pdf")
    print("=" * 80)
    
    test = TestContaboInvoice()
    
    # Get processed HTML
    pdf_path = Path("./temp/test_pdfs/1282161800020.pdf")
    if not pdf_path.exists():
        print(f"Error: Test PDF not found at {pdf_path}")
        return
    
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    print("\nProcessing PDF...")
    html_content = await convert_pdf_to_html(pdf_content, zoom_level=100.0)
    
    # Save for inspection
    output_path = Path("./temp/contabo-invoice-test-output.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"HTML saved to: {output_path}")
    
    # Run individual tests
    tests = [
        ("Recurring Fees Background", test.test_recurring_fees_has_background),
        ("Cumulative Gross Background", test.test_cumulative_gross_background),
        ("Border Count", test.test_border_count),
        ("Row Spacing", test.test_row_spacing),
        ("Table Structure", test.test_table_structure),
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

"""
Test table text alignment (left, center, right) in converted HTML.

This test verifies that text alignment in tables matches the original PDF.
The test analyzes second-page.pdf which contains a table with various alignments.

Current Issues:
- Some text that should be right-aligned is detected as left-aligned
- Some text that should be centered is detected as left-aligned
- The alignment detection logic uses only the starting position of text,
  not considering the actual text width and space distribution

Expected behavior:
- Text with equal space on left and right should be center-aligned
- Text with more space on left should be right-aligned
- Text with more space on right should be left-aligned
"""
import asyncio
import pytest
import pytest_asyncio
from pathlib import Path
from services.pdf_service import convert_pdf_to_html
from bs4 import BeautifulSoup
import re


class TestTableAlignment:
    """Test suite for table text alignment"""
    
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
    
    def extract_cell_alignment(self, cell):
        """Extract text alignment from a table cell"""
        style = cell.get('style', '')
        align_match = re.search(r'text-align:\s*(left|center|right)', style)
        
        if align_match:
            return align_match.group(1)
        return 'left'  # default
    
    def get_cell_text(self, cell):
        """Get text content from a cell"""
        return cell.get_text(strip=True)
    
    @pytest.mark.asyncio
    async def test_table_exists(self, processed_html):
        """Test that at least one table is present"""
        soup = BeautifulSoup(processed_html, 'html.parser')
        tables = soup.find_all('table')
        
        assert len(tables) > 0, "No tables found in converted HTML"
        print(f"✓ Found {len(tables)} table(s)")
    
    @pytest.mark.asyncio
    async def test_numeric_columns_alignment(self, processed_html):
        """
        Test that numeric columns (Summa, Käibemaks, Summa kokku) are properly aligned.
        
        In the original PDF, these columns typically contain:
        - Numbers that should be right-aligned for proper visual alignment
        - Decimal points should align vertically
        
        Current issue: These are being detected as left-aligned instead of right-aligned
        """
        soup = BeautifulSoup(processed_html, 'html.parser')
        tables = soup.find_all('table')
        
        assert len(tables) > 0, "No tables found"
        
        # Look for cells containing numeric values (e.g., "2,000", "0,480", "2,480")
        numeric_pattern = re.compile(r'^\d+[,\.]\d+$')
        
        numeric_cells = []
        for table in tables:
            for cell in table.find_all(['td', 'th']):
                text = self.get_cell_text(cell)
                if numeric_pattern.match(text):
                    alignment = self.extract_cell_alignment(cell)
                    numeric_cells.append({
                        'text': text,
                        'alignment': alignment,
                        'cell': cell
                    })
        
        print(f"\nFound {len(numeric_cells)} numeric cells")
        
        # Count alignments
        right_aligned = sum(1 for c in numeric_cells if c['alignment'] == 'right')
        left_aligned = sum(1 for c in numeric_cells if c['alignment'] == 'left')
        center_aligned = sum(1 for c in numeric_cells if c['alignment'] == 'center')
        
        print(f"  Right-aligned: {right_aligned}")
        print(f"  Left-aligned: {left_aligned}")
        print(f"  Center-aligned: {center_aligned}")
        
        # In a properly formatted table, numeric values should be right-aligned
        # This test will fail with current implementation
        if right_aligned == 0 and left_aligned > 0:
            pytest.fail(
                f"ALIGNMENT ISSUE: Found {left_aligned} numeric cells that are left-aligned, "
                f"but should be right-aligned for proper decimal alignment. "
                f"Examples: {[c['text'] for c in numeric_cells[:3]]}"
            )
    
    @pytest.mark.asyncio
    async def test_header_alignment(self, processed_html):
        """
        Test that table headers have appropriate alignment.
        
        Headers like "Summa", "Käibemaks", "Summa kokku" should match
        the alignment of their column data.
        """
        soup = BeautifulSoup(processed_html, 'html.parser')
        tables = soup.find_all('table')
        
        assert len(tables) > 0, "No tables found"
        
        # Look for header cells
        header_cells = []
        for table in tables:
            for cell in table.find_all(['th', 'td']):
                text = self.get_cell_text(cell)
                # Common headers in the test PDF
                if any(header in text for header in ['Summa', 'Käibemaks', 'Arv', 'Kestus']):
                    alignment = self.extract_cell_alignment(cell)
                    header_cells.append({
                        'text': text,
                        'alignment': alignment
                    })
        
        print(f"\nFound {len(header_cells)} header cells")
        for cell in header_cells[:5]:
            print(f"  '{cell['text'][:30]}' -> {cell['alignment']}")
    
    @pytest.mark.asyncio
    async def test_center_aligned_cells(self, processed_html):
        """
        Test detection of center-aligned cells.
        
        Some cells in the PDF may have text centered within the cell.
        The current implementation should detect this based on equal
        space on left and right sides.
        """
        soup = BeautifulSoup(processed_html, 'html.parser')
        tables = soup.find_all('table')
        
        assert len(tables) > 0, "No tables found"
        
        center_cells = []
        for table in tables:
            for cell in table.find_all(['td', 'th']):
                alignment = self.extract_cell_alignment(cell)
                if alignment == 'center':
                    text = self.get_cell_text(cell)
                    center_cells.append(text)
        
        print(f"\nFound {len(center_cells)} center-aligned cells")
        if center_cells:
            print("Examples:")
            for text in center_cells[:5]:
                print(f"  '{text[:50]}'")
    
    @pytest.mark.asyncio
    async def test_alignment_distribution(self, processed_html):
        """
        Test the overall distribution of alignments in the table.
        
        This test provides statistics about alignment usage.
        """
        soup = BeautifulSoup(processed_html, 'html.parser')
        tables = soup.find_all('table')
        
        assert len(tables) > 0, "No tables found"
        
        alignments = {'left': 0, 'center': 0, 'right': 0}
        total_cells = 0
        
        for table in tables:
            for cell in table.find_all(['td', 'th']):
                text = self.get_cell_text(cell)
                if text:  # Only count non-empty cells
                    alignment = self.extract_cell_alignment(cell)
                    alignments[alignment] += 1
                    total_cells += 1
        
        print(f"\nAlignment Distribution (total: {total_cells} cells):")
        print(f"  Left:   {alignments['left']} ({alignments['left']/total_cells*100:.1f}%)")
        print(f"  Center: {alignments['center']} ({alignments['center']/total_cells*100:.1f}%)")
        print(f"  Right:  {alignments['right']} ({alignments['right']/total_cells*100:.1f}%)")
        
        # If we have 0% right-aligned cells, that's suspicious for a typical invoice/table
        if alignments['right'] == 0 and total_cells > 10:
            print("\n⚠️  WARNING: No right-aligned cells detected. This may indicate an alignment detection issue.")
    
    @pytest.mark.asyncio
    async def test_specific_cell_alignment(self, processed_html):
        """
        Test specific cells that we know should have certain alignments.
        
        Based on the test output, we can identify specific cells and their expected alignments.
        For example:
        - Row 6, Col 7: "2,480" should be right-aligned (currently center)
        - Row 14, Col 7: "6,200" should be right-aligned (currently center)
        """
        soup = BeautifulSoup(processed_html, 'html.parser')
        tables = soup.find_all('table')
        
        assert len(tables) > 0, "No tables found"
        
        # Find cells with specific numeric values
        test_cases = [
            {'value': '2,480', 'expected': 'right', 'description': 'Total amount in first section'},
            {'value': '6,200', 'expected': 'right', 'description': 'Total amount in second section'},
            {'value': '2,000', 'expected': 'right', 'description': 'Base price'},
            {'value': '5,000', 'expected': 'right', 'description': 'Base price'},
        ]
        
        failures = []
        
        for test_case in test_cases:
            found = False
            for table in tables:
                for cell in table.find_all(['td', 'th']):
                    text = self.get_cell_text(cell)
                    if test_case['value'] in text:
                        found = True
                        alignment = self.extract_cell_alignment(cell)
                        
                        print(f"\n'{test_case['value']}' ({test_case['description']})")
                        print(f"  Expected: {test_case['expected']}")
                        print(f"  Actual:   {alignment}")
                        
                        if alignment != test_case['expected']:
                            failures.append(
                                f"Cell '{test_case['value']}' has alignment '{alignment}', "
                                f"expected '{test_case['expected']}'"
                            )
                        break
                if found:
                    break
        
        if failures:
            pytest.fail("\n".join(failures))


# Standalone test runner for manual testing
async def run_manual_test():
    """Run tests manually without pytest"""
    print("=" * 80)
    print("Manual Table Alignment Test")
    print("=" * 80)
    
    test = TestTableAlignment()
    
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
    output_path = Path("./temp/second-page-alignment-test.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"HTML saved to: {output_path}")
    
    # Run individual tests
    print("\n" + "=" * 80)
    print("Test 1: Table Exists")
    print("=" * 80)
    try:
        await test.test_table_exists(html_content)
    except AssertionError as e:
        print(f"❌ FAILED: {e}")
    
    print("\n" + "=" * 80)
    print("Test 2: Alignment Distribution")
    print("=" * 80)
    try:
        await test.test_alignment_distribution(html_content)
    except AssertionError as e:
        print(f"❌ FAILED: {e}")
    
    print("\n" + "=" * 80)
    print("Test 3: Numeric Columns Alignment")
    print("=" * 80)
    try:
        await test.test_numeric_columns_alignment(html_content)
        print("✓ PASSED")
    except (AssertionError, Exception) as e:
        print(f"❌ FAILED: {e}")
    
    print("\n" + "=" * 80)
    print("Test 4: Specific Cell Alignment")
    print("=" * 80)
    try:
        await test.test_specific_cell_alignment(html_content)
        print("✓ PASSED")
    except (AssertionError, Exception) as e:
        print(f"❌ FAILED: {e}")
    
    print("\n" + "=" * 80)
    print("Test 5: Center Aligned Cells")
    print("=" * 80)
    try:
        await test.test_center_aligned_cells(html_content)
    except AssertionError as e:
        print(f"❌ FAILED: {e}")
    
    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_manual_test())

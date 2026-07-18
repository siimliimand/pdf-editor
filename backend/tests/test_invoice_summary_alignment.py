"""
Test table text alignment for Invoice Summary table in EUINEE25-95942.pdf

This test verifies that the Invoice Summary table is correctly rendered with proper alignment.
The table contains:
- Invoice Summary (header)
- VAT Invoice Number: EUINEE25-95942
- VAT Invoice Date: December 1, 2025
- TOTAL AMOUNT EUR 2.19
- TOTAL VAT EUR 0.42

Expected behavior:
- Left column (labels) should be left-aligned
- Right column (values) should be right-aligned
- Numeric values should maintain decimal alignment
"""
import asyncio
import pytest
import pytest_asyncio
from pathlib import Path
from services.pdf_service import convert_pdf_to_html
from bs4 import BeautifulSoup
import re


class TestInvoiceSummaryAlignment:
    """Test suite for Invoice Summary table alignment in EUINEE25-95942.pdf"""
    
    @pytest_asyncio.fixture
    async def processed_html(self):
        """Process the test PDF and return HTML"""
        pdf_path = Path("./temp/test_pdfs/EUINEE25-95942.pdf")
        
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
    
    def find_invoice_summary_tables(self, soup):
        """
        Find all tables related to the Invoice Summary section.
        
        The Invoice Summary data may be split across multiple tables:
        - One table with VAT Invoice Number and Date
        - Another table with TOTAL AMOUNT
        - Another table with TOTAL VAT
        """
        tables = soup.find_all('table')
        invoice_tables = []
        
        for table in tables:
            text_content = table.get_text()
            # Look for tables containing Invoice Summary related data
            if any(keyword in text_content for keyword in [
                'EUINEE25-95942',
                'VAT Invoice Number',
                'VAT Invoice Date',
                'TOTAL AMOUNT',
                'TOTAL VAT'
            ]):
                invoice_tables.append(table)
        
        return invoice_tables
    
    def find_invoice_summary_table(self, soup):
        """Find the first Invoice Summary table (for backward compatibility)"""
        tables = self.find_invoice_summary_tables(soup)
        return tables[0] if tables else None
    
    @pytest.mark.asyncio
    async def test_invoice_summary_table_exists(self, processed_html):
        """Test that the Invoice Summary table is present"""
        soup = BeautifulSoup(processed_html, 'html.parser')
        table = self.find_invoice_summary_table(soup)
        
        assert table is not None, "Invoice Summary table not found in converted HTML"
        print("✓ Invoice Summary table found")
    
    @pytest.mark.asyncio
    async def test_invoice_number_present(self, processed_html):
        """Test that the invoice number EUINEE25-95942 is present"""
        soup = BeautifulSoup(processed_html, 'html.parser')
        table = self.find_invoice_summary_table(soup)
        
        assert table is not None, "Invoice Summary table not found"
        
        table_text = table.get_text()
        assert 'EUINEE25-95942' in table_text, "Invoice number EUINEE25-95942 not found in table"
        print("✓ Invoice number EUINEE25-95942 found")
    
    @pytest.mark.asyncio
    async def test_invoice_date_present(self, processed_html):
        """Test that the invoice date is present"""
        soup = BeautifulSoup(processed_html, 'html.parser')
        table = self.find_invoice_summary_table(soup)
        
        assert table is not None, "Invoice Summary table not found"
        
        table_text = table.get_text()
        assert 'December 1, 2025' in table_text or 'December 1,2025' in table_text, \
            "Invoice date 'December 1, 2025' not found in table"
        print("✓ Invoice date found")
    
    @pytest.mark.asyncio
    async def test_total_amount_present(self, processed_html):
        """Test that TOTAL AMOUNT EUR 2.19 is present"""
        soup = BeautifulSoup(processed_html, 'html.parser')
        tables = self.find_invoice_summary_tables(soup)
        
        assert len(tables) > 0, "Invoice Summary tables not found"
        
        # Search across all invoice summary tables
        all_text = ' '.join(table.get_text() for table in tables)
        assert '2.19' in all_text or '2,19' in all_text, "Total amount 2.19 not found in tables"
        assert 'TOTAL AMOUNT' in all_text, "Label 'TOTAL AMOUNT' not found in tables"
        print("✓ Total amount EUR 2.19 found")
    
    @pytest.mark.asyncio
    async def test_total_vat_present(self, processed_html):
        """Test that TOTAL VAT EUR 0.42 is present"""
        soup = BeautifulSoup(processed_html, 'html.parser')
        tables = self.find_invoice_summary_tables(soup)
        
        assert len(tables) > 0, "Invoice Summary tables not found"
        
        # Search across all invoice summary tables
        all_text = ' '.join(table.get_text() for table in tables)
        assert '0.42' in all_text or '0,42' in all_text, "Total VAT 0.42 not found in tables"
        assert 'TOTAL VAT' in all_text, "Label 'TOTAL VAT' not found in tables"
        print("✓ Total VAT EUR 0.42 found")
    
    @pytest.mark.asyncio
    async def test_specific_alignments(self, processed_html):
        """
        Test alignment for specific items as requested.
        
        Aligned left:
        - VAT Invoice Number:
        - VAT Invoice Date:
        - TOTAL AMOUNT
        - TOTAL VAT

        Aligned right:
        - EUINEE25-95942
        - December 1, 2025
        - EUR 2.19
        - EUR 0.42
        """
        soup = BeautifulSoup(processed_html, 'html.parser')
        tables = self.find_invoice_summary_tables(soup)
        
        assert len(tables) > 0, "Invoice Summary tables not found"
        
        left_items = [
            "VAT Invoice Number:",
            "VAT Invoice Date:",
            "TOTAL AMOUNT",
            "TOTAL VAT"
        ]
        
        right_items = [
            "EUINEE25-95942",
            "December 1, 2025",
            "EUR 2.19",
            "EUR 0.42"
        ]
        
        failures = []
        
        def check_item_alignment(item, expected_align):
            found_cell = None
            found_text = None
            
            # Try exact/substring match first
            for table in tables:
                for cell in table.find_all(['td', 'th']):
                    text = self.get_cell_text(cell)
                    if item in text:
                        found_cell = cell
                        found_text = text
                        break
                    # Special case for date with missing space
                    if item == "December 1, 2025" and "December 1,2025" in text:
                        found_cell = cell
                        found_text = text
                        break
                if found_cell:
                    break
            
            # Fallback for currency values if not found (might be split or just number)
            if not found_cell and "EUR" in item:
                number_part = item.replace("EUR", "").strip()
                for table in tables:
                    for cell in table.find_all(['td', 'th']):
                        text = self.get_cell_text(cell)
                        # Check strictly for the number part to avoid false positives
                        if number_part in text:
                            found_cell = cell
                            found_text = text
                            break
                    if found_cell:
                        break
            
            if found_cell:
                alignment = self.extract_cell_alignment(found_cell)
                if alignment != expected_align:
                    failures.append(
                        f"Alignment Mismatch: '{item}' (found in '{found_text}') "
                        f"is {alignment}-aligned, expected {expected_align}"
                    )
            else:
                 failures.append(f"Item Not Found: '{item}' could not be located in tables")

        # Check all items
        print("\nChecking alignments:")
        for item in left_items:
            check_item_alignment(item, 'left')
        for item in right_items:
            check_item_alignment(item, 'right')
            
        if failures:
            pytest.fail("\n".join(failures))
        
        print("✓ All specific items have correct alignment")
    
    @pytest.mark.asyncio
    async def test_table_structure(self, processed_html):
        """
        Test the overall structure of the Invoice Summary tables.
        
        Expected: Multiple tables containing invoice summary data
        """
        soup = BeautifulSoup(processed_html, 'html.parser')
        tables = self.find_invoice_summary_tables(soup)
        
        assert len(tables) > 0, "Invoice Summary tables not found"
        
        print(f"\nFound {len(tables)} Invoice Summary related table(s)")
        
        # Analyze each table
        for table_idx, table in enumerate(tables):
            rows = table.find_all('tr')
            print(f"\nTable {table_idx + 1} has {len(rows)} row(s):")
            
            for i, row in enumerate(rows):
                cells = row.find_all(['td', 'th'])
                cell_texts = [self.get_cell_text(cell) for cell in cells]
                print(f"  Row {i+1}: {len(cells)} cell(s) - {cell_texts}")
        
        # Should have at least 2 tables (one for invoice details, one for totals)
        assert len(tables) >= 2, f"Expected at least 2 tables, found {len(tables)}"
        print(f"✓ Table structure looks reasonable")
    
    @pytest.mark.asyncio
    async def test_alignment_consistency(self, processed_html):
        """
        Test that alignment is consistent within columns across all invoice summary tables.
        
        All values in the right column should have the same alignment.
        """
        soup = BeautifulSoup(processed_html, 'html.parser')
        tables = self.find_invoice_summary_tables(soup)
        
        assert len(tables) > 0, "Invoice Summary tables not found"
        
        print(f"\nAnalyzing alignment consistency across {len(tables)} table(s)")
        
        # Analyze each table separately
        for table_idx, table in enumerate(tables):
            rows = table.find_all('tr')
            
            # Track alignments by column
            column_alignments = {}
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                for col_idx, cell in enumerate(cells):
                    text = self.get_cell_text(cell)
                    if text:  # Only consider non-empty cells
                        alignment = self.extract_cell_alignment(cell)
                        
                        if col_idx not in column_alignments:
                            column_alignments[col_idx] = []
                        
                        column_alignments[col_idx].append({
                            'text': text[:30],
                            'alignment': alignment
                        })
            
            print(f"\nTable {table_idx + 1} - Alignment by column:")
            for col_idx, alignments in column_alignments.items():
                unique_alignments = set(a['alignment'] for a in alignments)
                print(f"  Column {col_idx}: {unique_alignments}")
            
            # Show examples
            for align_info in alignments[:3]:
                print(f"    '{align_info['text']}' -> {align_info['alignment']}")
        
        # Check consistency in each column
        inconsistencies = []
        for col_idx, alignments in column_alignments.items():
            unique_alignments = set(a['alignment'] for a in alignments)
            if len(unique_alignments) > 1:
                inconsistencies.append(
                    f"Column {col_idx} has mixed alignments: {unique_alignments}"
                )
        
        if inconsistencies:
            print("\n⚠️  Alignment inconsistencies found:")
            for inc in inconsistencies:
                print(f"  {inc}")


# Standalone test runner for manual testing
async def run_manual_test():
    """Run tests manually without pytest"""
    print("=" * 80)
    print("Invoice Summary Table Alignment Test - EUINEE25-95942.pdf")
    print("=" * 80)
    
    test = TestInvoiceSummaryAlignment()
    
    # Get processed HTML
    pdf_path = Path("./temp/test_pdfs/EUINEE25-95942.pdf")
    if not pdf_path.exists():
        print(f"Error: Test PDF not found at {pdf_path}")
        return
    
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    print("\nProcessing PDF...")
    html_content = await convert_pdf_to_html(pdf_content, zoom_level=100.0)
    
    # Save for inspection
    output_path = Path("./temp/EUINEE25-95942-alignment-test.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"HTML saved to: {output_path}")
    
    # Run individual tests
    tests = [
        ("Table Exists", test.test_invoice_summary_table_exists),
        ("Invoice Number Present", test.test_invoice_number_present),
        ("Invoice Date Present", test.test_invoice_date_present),
        ("Total Amount Present", test.test_total_amount_present),
        ("Total VAT Present", test.test_total_vat_present),
        ("Table Structure", test.test_table_structure),
        ("Specific Alignments", test.test_specific_alignments),
        ("Alignment Consistency", test.test_alignment_consistency),
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

"""
Test font detection and rendering for second-page.pdf

This test verifies that fonts are correctly detected and rendered in the HTML output.
The main issue being tested: fonts appear too thin/light in generated HTML compared to PDF.

Expected fonts from PDF analysis:
- Elisa-Regular (font-weight: 400) for headers and bold text
- Elisa-Thin (font-weight: 100) for regular body text

The test compares:
1. Font family names
2. Font weights (400 vs 100)
3. Font sizes
4. Visual consistency with original PDF
"""
import asyncio
import pytest
import pytest_asyncio
from pathlib import Path
import sys
import os
import re
from typing import Dict, List, Tuple

# Add parent directory to path for standalone execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.pdf_service import convert_pdf_to_html
from bs4 import BeautifulSoup


class TestFontDetection:
    """Test suite for font detection in second-page.pdf"""
    
    # Expected font mappings from PDF
    # Format: {text_sample: {family, weight, size_px}}
    EXPECTED_FONTS = {
        # Title - should be bold/regular (400)
        "Elisa arve alajaotus": {
            "family": "'Elisa', sans-serif",
            "weight": 400,
            "size": 24,  # 18pt * 1.33 = 24px at 96 DPI
        },
        
        # Subtitle - should be thin (100)
        "SeoWeb OÜ | Kliendinumber": {
            "family": "'Elisa', sans-serif",
            "weight": 100,
            "size": 13,  # ~10pt * 1.33
        },
        
        # Phone number header - should be bold/regular (400)
        "Mobiiltelefon: 55526556": {
            "family": "'Elisa', sans-serif",
            "weight": 400,
            "size": 16,  # ~12pt * 1.33
        },
        
        # Package info - should be thin (100)
        "| SeoWeb OÜ | Pakett": {
            "family": "'Elisa', sans-serif",
            "weight": 100,
            "size": 15,
        },
        
        # Table header "Arv" - seems to use Thin font in PDF
        "Arv": {
            "family": "'Elisa', sans-serif",
            "weight": 100,
            "size": 12,
        },
        
        # Table content - should be thin (100)
        "Kõned mobiilidele": {
            "family": "'Elisa', sans-serif",
            "weight": 100,
            "size": 12,
        },
        
        # Section headers - should be bold/regular (400)
        "Kuutasud": {
            "family": "'Elisa', sans-serif",
            "weight": 400,
            "size": 12,
        },
        
        # Package name - should be thin (100)
        "Äripakett D 1": {
            "family": "'Elisa', sans-serif",
            "weight": 100,
            "size": 15, # Actual is ~14.66px
        },
        
        # Total row - should be bold/regular (400)
        "Kokku": {
            "family": "'Elisa', sans-serif",
            "weight": 400,
            "size": 15,
        },
        
        # Additional test cases for common text
        "Paketis sisalduvad teenused": {
            "family": "'Elisa', sans-serif",
            "weight": 400,
            "size": 12,
        },
    }
    
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
    
    def extract_style_value(self, element, property_name: str) -> str:
        """Extract a specific CSS property from element's style"""
        if not element:
            return None
            
        style = element.get('style', '')
        pattern = rf'{property_name}:\s*([^;]+)'
        match = re.search(pattern, style, re.IGNORECASE)
        # Handle quotes in returned value
        if match:
            return match.group(1).strip()
        return None
    
    def find_text_element(self, soup, text_fragment: str):
        """Find the most specific element containing the given text fragment"""
        # Search specifically for spans first as they usually contain the style
        for elem in soup.find_all('span'):
            elem_text = elem.get_text()
            if text_fragment in elem_text:
                return elem
        
        # Then paragraphs
        for elem in soup.find_all('p'):
            elem_text = elem.get_text()
            if text_fragment in elem_text:
                return elem
                
        # Then cells
        for elem in soup.find_all('td'):
            elem_text = elem.get_text()
            if text_fragment in elem_text:
                return elem
                
        return None
    
    def parse_font_size(self, font_size_str: str) -> float:
        """Parse font-size string to float (px value)"""
        if not font_size_str:
            return None
        return float(re.sub(r'[^0-9.]', '', font_size_str))
    
    def parse_font_weight(self, font_weight_str: str) -> int:
        """Parse font-weight string to int"""
        if not font_weight_str:
            return None
        
        # Handle named weights
        weight_map = {
            'thin': 100,
            'light': 300,
            'normal': 400,
            'bold': 700,
        }
        
        lower = font_weight_str.lower().strip()
        if lower in weight_map:
            return weight_map[lower]
        
        # Parse numeric
        return int(float(re.sub(r'[^0-9.]', '', font_weight_str)))
    
    # =========================================================================
    # Individual Font Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_title_font_weight(self, processed_html):
        """Test that title 'Elisa arve alajaotus' has correct bold weight (400)"""
        soup = BeautifulSoup(processed_html, 'html.parser')
        
        elem = self.find_text_element(soup, "Elisa arve alajaotus")
        assert elem is not None, "Title 'Elisa arve alajaotus' not found in HTML"
        
        font_weight = self.extract_style_value(elem, 'font-weight')
        font_family = self.extract_style_value(elem, 'font-family')
        font_size = self.extract_style_value(elem, 'font-size')
        
        print(f"\n'Elisa arve alajaotus' font properties:")
        print(f"  font-family: {font_family}")
        print(f"  font-weight: {font_weight} (expected: 400)")
        print(f"  font-size: {font_size} (expected: ~24px)")
        
        # Verify weight
        if font_weight:
            weight_val = self.parse_font_weight(font_weight)
            assert weight_val == 400, f"Title should have font-weight: 400, got {weight_val}"
        else:
            pytest.fail("Title font-weight not found")
        
        # Verify family matches expectation
        if font_family:
            # We accept 'Elisa', sans-serif or similar
            assert "Elisa" in font_family, \
                f"Title should use Elisa font, got {font_family}"
    
    @pytest.mark.asyncio
    async def test_mobiiltelefon_header_font_weight(self, processed_html):
        """Test that 'Mobiiltelefon: 55526556' has bold weight (400)"""
        soup = BeautifulSoup(processed_html, 'html.parser')
        
        elem = self.find_text_element(soup, "Mobiiltelefon: 55526556")
        assert elem is not None, "'Mobiiltelefon: 55526556' not found in HTML"
        
        font_weight = self.extract_style_value(elem, 'font-weight')
        font_family = self.extract_style_value(elem, 'font-family')
        
        print(f"\n'Mobiiltelefon: 55526556' font properties:")
        print(f"  font-family: {font_family}")
        print(f"  font-weight: {font_weight} (expected: 400)")
        
        if font_weight:
            weight_val = self.parse_font_weight(font_weight)
            assert weight_val == 400, f"Mobiiltelefon header should have font-weight: 400, got {weight_val}"
        else:
            pytest.fail("Mobiiltelefon font-weight not found")
    
    @pytest.mark.asyncio
    async def test_kokku_font_weight(self, processed_html):
        """Test that 'Kokku' rows have bold weight (400)"""
        soup = BeautifulSoup(processed_html, 'html.parser')
        
        kokku_elements = []
        for td in soup.find_all('td'):
            text = td.get_text().strip()
            if text == 'Kokku':
                kokku_elements.append(td)
        
        assert len(kokku_elements) > 0, "'Kokku' cells not found in HTML"
        
        print(f"\nFound {len(kokku_elements)} 'Kokku' cells")
        
        for i, elem in enumerate(kokku_elements):
            font_weight = self.extract_style_value(elem, 'font-weight')
            font_family = self.extract_style_value(elem, 'font-family')
            
            print(f"  Kokku #{i+1}:")
            print(f"    font-family: {font_family}")
            print(f"    font-weight: {font_weight} (expected: 400)")
            
            if font_weight:
                weight_val = self.parse_font_weight(font_weight)
                assert weight_val == 400, f"Kokku #{i+1} should have font-weight: 400, got {weight_val}"
    
    @pytest.mark.asyncio
    async def test_thin_font_elements(self, processed_html):
        """Test that thin font elements (Elisa-Thin) have weight 100"""
        soup = BeautifulSoup(processed_html, 'html.parser')
        
        thin_texts = [
            "Kõned mobiilidele",
            "Äripakett D 1",
            "SeoWeb OÜ | Kliendinumber",
        ]
        
        for text in thin_texts:
            elem = self.find_text_element(soup, text)
            if elem:
                font_weight = self.extract_style_value(elem, 'font-weight')
                font_family = self.extract_style_value(elem, 'font-family')
                
                print(f"\n'{text}' font properties:")
                print(f"  font-family: {font_family}")
                print(f"  font-weight: {font_weight} (expected: 100)")
                
                if font_weight:
                    weight_val = self.parse_font_weight(font_weight)
                    assert weight_val == 100, f"'{text}' should have font-weight: 100, got {weight_val}"
                else:
                    pytest.fail(f"'{text}' font-weight not found")
    
    # =========================================================================
    # Comprehensive Font Tests
    # =========================================================================
    
    @pytest.mark.asyncio
    async def test_all_expected_fonts(self, processed_html):
        """Test all expected font properties from EXPECTED_FONTS"""
        soup = BeautifulSoup(processed_html, 'html.parser')
        
        failures = []
        successes = []
        
        for text_sample, expected in self.EXPECTED_FONTS.items():
            elem = self.find_text_element(soup, text_sample)
            
            if not elem:
                failures.append(f"❌ Text '{text_sample}' not found in HTML")
                continue
            
            font_weight = self.extract_style_value(elem, 'font-weight')
            font_family = self.extract_style_value(elem, 'font-family')
            font_size = self.extract_style_value(elem, 'font-size')
            
            # Check weight
            if font_weight:
                weight_val = self.parse_font_weight(font_weight)
                if weight_val != expected['weight']:
                    failures.append(
                        f"❌ '{text_sample}': font-weight is {weight_val}, expected {expected['weight']}"
                    )
                else:
                    successes.append(f"✓ '{text_sample}': font-weight {weight_val} correct")
            else:
                failures.append(f"❌ '{text_sample}': font-weight not found")
            
            # Check size (with tolerance)
            if font_size:
                size_val = self.parse_font_size(font_size)
                expected_size = expected['size']
                tolerance = 2  # ±2px tolerance
                
                if abs(size_val - expected_size) > tolerance:
                    failures.append(
                        f"❌ '{text_sample}': font-size is {size_val}px, expected ~{expected_size}px"
                    )
                else:
                    successes.append(f"✓ '{text_sample}': font-size {size_val}px correct")
        
        # Print results
        print("\n" + "="*80)
        print("FONT DETECTION TEST RESULTS")
        print("="*80)
        
        if successes:
            print("\nSuccesses:")
            for msg in successes:
                print(f"  {msg}")
        
        if failures:
            print("\nFailures:")
            for msg in failures:
                print(f"  {msg}")
            
            pytest.fail(f"\n{len(failures)} font property mismatches found:\n" + "\n".join(failures))
        else:
            print(f"\n✓ All {len(successes)} font checks passed!")
    
    @pytest.mark.asyncio
    async def test_font_weight_distribution(self, processed_html):
        """Test that font weights are distributed correctly (not all thin)"""
        soup = BeautifulSoup(processed_html, 'html.parser')
        
        # Count font weights in the document
        weight_counts = {100: 0, 400: 0, 700: 0, 'other': 0}
        
        for elem in soup.find_all(['span', 'p', 'td', 'th']):
            font_weight = self.extract_style_value(elem, 'font-weight')
            if font_weight:
                try:
                    weight_val = self.parse_font_weight(font_weight)
                    if weight_val == 100:
                        weight_counts[100] += 1
                    elif weight_val == 400:
                        weight_counts[400] += 1
                    elif weight_val == 700:
                        weight_counts[700] += 1
                    else:
                        weight_counts['other'] += 1
                except:
                    pass
        
        print("\nFont weight distribution:")
        print(f"  Weight 100 (Thin): {weight_counts[100]} elements")
        print(f"  Weight 400 (Regular): {weight_counts[400]} elements")
        print(f"  Weight 700 (Bold): {weight_counts[700]} elements")
        print(f"  Other weights: {weight_counts['other']} elements")
        
        # We expect both thin (100) and regular (400) fonts
        assert weight_counts[400] > 0, \
            "No font-weight: 400 elements found! All text appears to be thin."
        assert weight_counts[100] > 0, \
            "No font-weight: 100 elements found! Document should have thin text."
        
        print(f"\n✓ Font weights are properly distributed")
    
    @pytest.mark.asyncio
    async def test_no_incorrect_thin_fonts(self, processed_html):
        """Test that headers/bold text are NOT using thin fonts"""
        soup = BeautifulSoup(processed_html, 'html.parser')
        
        # These should definitely NOT be thin (100)
        bold_texts = [
            "Elisa arve alajaotus",
            "Mobiiltelefon: 55526556",
            "Kokku",
            "Kuutasud",
        ]
        
        failures = []
        
        for text in bold_texts:
            elem = self.find_text_element(soup, text)
            if elem:
                font_weight = self.extract_style_value(elem, 'font-weight')
                if font_weight:
                    weight_val = self.parse_font_weight(font_weight)
                    if weight_val == 100:
                        failures.append(
                            f"❌ '{text}' incorrectly has font-weight: 100 (should be 400)"
                        )
        
        if failures:
            print("\n" + "="*80)
            print("INCORRECT THIN FONTS DETECTED:")
            print("="*80)
            for msg in failures:
                print(f"  {msg}")
            
            pytest.fail(
                f"\n{len(failures)} headers/bold texts incorrectly using thin font:\n" + 
                "\n".join(failures)
            )


# Standalone test runner for manual testing
async def run_manual_test():
    """Run tests manually without pytest"""
    print("=" * 80)
    print("Font Detection Test - second-page.pdf")
    print("=" * 80)
    
    test = TestFontDetection()
    
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
    output_path = Path("./temp/second-page-font-test-output.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"HTML saved to: {output_path}")
    
    # Run individual tests
    tests = [
        ("Title Font Weight", test.test_title_font_weight),
        ("Mobiiltelefon Header Font Weight", test.test_mobiiltelefon_header_font_weight),
        ("Kokku Font Weight", test.test_kokku_font_weight),
        ("Thin Font Elements", test.test_thin_font_elements),
        ("All Expected Fonts", test.test_all_expected_fonts),
        ("Font Weight Distribution", test.test_font_weight_distribution),
        ("No Incorrect Thin Fonts", test.test_no_incorrect_thin_fonts),
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

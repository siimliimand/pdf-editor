"""
Test table row rendering and border positions for Elisa invoice

This test focuses exclusively on verifying that table rows are rendered
at the correct Y positions with proper borders matching the PDF layout.

Expected border Y positions (from PDF analysis):
These represent horizontal lines that should appear in the rendered HTML.

Features:
- Generates screenshot of rendered HTML for manual measurement
- Analyzes border positions programmatically
- Provides detailed row-by-row breakdown
"""
import asyncio
import pytest
import pytest_asyncio
from pathlib import Path
import sys
import os
import re

# Add parent directory to path for standalone execution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.pdf_service import convert_pdf_to_html
from bs4 import BeautifulSoup

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright not available. Install with: pip install playwright && playwright install")


class TestTableRows:
    """Test suite focused on table row positioning and borders"""
    
    # Expected horizontal border Y-positions from PDF
    # Developer confirmed these are correct - do not modify
    EXPECTED_BORDER_Y_POSITIONS = [
        118.0,
        136.0,
        168.0,
        181.0,
        195.0,
        209.0,
        222.0,
        236.0,
        252.0,
        266.0,
        301.0,
        315.0,
        328.0,
        342.0,
        355.0,
        369.0,
        385.0,
        399.0
    ]
    
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
    
    def extract_table_info(self, html_content):
        """
        Extract table structure with row positions and borders.
        
        Returns:
            dict with:
                - table_top: Y position of table
                - rows: list of dicts with {y_top, y_bottom, height, has_top_border, has_bottom_border, text}
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the main grid table (absolute positioned)
        tables = soup.find_all('table')
        target_table = None
        table_top = 0.0
        
        for table in tables:
            style = table.get('style', '')
            if 'position: absolute' in style:
                top_match = re.search(r'top:\s*([\d.]+)px', style)
                if top_match:
                    table_top = float(top_match.group(1))
                    target_table = table
                    break
        
        if target_table is None:
            return None
        
        rows_info = []
        current_y = table_top
        
        for row in target_table.find_all('tr'):
            # Get row height
            style = row.get('style', '')
            h_match = re.search(r'height:\s*([\d.]+)px', style)
            height = float(h_match.group(1)) if h_match else 0.0
            
            # Check for borders
            cells = row.find_all('td')
            has_top_border = any(
                'border-top' in (c.get('style') or '') and 
                'solid' in (c.get('style') or '') 
                for c in cells
            )
            has_bottom_border = any(
                'border-bottom' in (c.get('style') or '') and 
                'solid' in (c.get('style') or '') 
                for c in cells
            )
            
            # Get row text (first 50 chars)
            row_text = ' | '.join(c.get_text().strip()[:30] for c in cells[:3])
            
            row_info = {
                'y_top': current_y,
                'y_bottom': current_y + height,
                'height': height,
                'has_top_border': has_top_border,
                'has_bottom_border': has_bottom_border,
                'text': row_text
            }
            rows_info.append(row_info)
            
            current_y += height
        
        return {
            'table_top': table_top,
            'rows': rows_info
        }
    
    async def extract_actual_border_positions(self, html_content):
        """
        Use Playwright to extract ACTUAL rendered border positions from the browser.
        This is more accurate than calculating from row heights.
        
        Returns:
            list of Y positions where borders are rendered, or None if Playwright unavailable
        """
        if not PLAYWRIGHT_AVAILABLE:
            print("⚠️  Playwright not available. Cannot extract actual border positions.")
            return None
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page(viewport={'width': 1200, 'height': 800})
                
                # Load HTML
                full_html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin: 0; padding: 0;">
    {html_content}
</body>
</html>"""
                await page.set_content(full_html)
                await page.wait_for_timeout(500)
                
                # Extract border positions using JavaScript
                result = await page.evaluate("""
                    () => {
                        const table = document.querySelector('table[style*="position: absolute"]');
                        if (!table) return {borders: [], tableTop: 0};
                        
                        // Get content area offset (body padding)
                        const contentDiv = document.querySelector('body > div, body');
                        const contentRect = contentDiv.getBoundingClientRect();
                        const contentTop = contentRect.top;
                        
                        const borders = [];
                        const rows = table.querySelectorAll('tr');
                        rows.forEach(row => {
                            const cells = row.querySelectorAll('td');
                            cells.forEach(cell => {
                                const style = cell.getAttribute('style') || '';
                                const rect = cell.getBoundingClientRect();
                                
                                // Check for top border (absolute position relative to content area)
                                if (style.includes('border-top') && style.includes('solid')) {
                                    borders.push({
                                        y: Math.round((rect.top - contentTop) * 100) / 100,
                                        type: 'top'
                                    });
                                }
                                
                                // Check for bottom border (absolute position relative to content area)
                                if (style.includes('border-bottom') && style.includes('solid')) {
                                    borders.push({
                                        y: Math.round((rect.bottom - contentTop) * 100) / 100,
                                        type: 'bottom'
                                    });
                                }
                            });
                        });
                        
                        // Remove duplicates and sort
                        const uniqueY = [...new Set(borders.map(b => b.y))].sort((a, b) => a - b);
                        
                        // Get table top position
                        const tableRect = table.getBoundingClientRect();
                        const tableTop = Math.round((tableRect.top - contentTop) * 100) / 100;
                        
                        return {borders: uniqueY, tableTop: tableTop};
                    }
                """)
                
                await browser.close()
                
                border_positions = result['borders']
                table_top = result['tableTop']
                print(f"  Table top position: {table_top}px")
                
                return border_positions
                
        except Exception as e:
            print(f"❌ Failed to extract border positions: {e}")
            return None

    async def generate_screenshot(self, html_content, output_path="./temp/table-rows-screenshot.png"):
        """
        Generate a screenshot of the rendered HTML for manual measurement.
        
        Args:
            html_content: HTML string to render
            output_path: Path to save screenshot
            
        Returns:
            Path to saved screenshot or None if Playwright not available
        """
        if not PLAYWRIGHT_AVAILABLE:
            print("⚠️  Playwright not available. Skipping screenshot generation.")
            return None
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create a complete HTML document with measurement aids
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            margin: 0;
            padding: 20px;
            background: white;
            font-family: Arial, sans-serif;
        }}
        .measurement-guide {{
            position: fixed;
            left: 0;
            top: 0;
            width: 50px;
            height: 100%;
            background: #f0f0f0;
            border-right: 2px solid #333;
            font-size: 10px;
            z-index: 1000;
        }}
        .measurement-guide .tick {{
            position: absolute;
            left: 0;
            width: 100%;
            height: 1px;
            background: #999;
            font-size: 9px;
            color: #333;
        }}
        .measurement-guide .tick.major {{
            background: #333;
            height: 2px;
        }}
        .measurement-guide .tick span {{
            position: absolute;
            left: 5px;
            top: -6px;
            background: #f0f0f0;
            padding: 0 2px;
        }}
        .content {{
            margin-left: 60px;
            position: relative;
        }}
        /* Highlight borders for visibility */
        table {{
            border-collapse: collapse !important;
        }}
        td {{
            position: relative;
        }}
        /* Add red overlay lines at expected positions */
        .expected-line {{
            position: absolute;
            left: 0;
            right: 0;
            height: 1px;
            background: rgba(255, 0, 0, 0.3);
            z-index: 999;
            pointer-events: none;
        }}
        .expected-line::before {{
            content: attr(data-y);
            position: absolute;
            right: 5px;
            top: -8px;
            font-size: 10px;
            color: red;
            background: white;
            padding: 0 2px;
        }}
    </style>
</head>
<body>
    <div class="measurement-guide">
        <!-- Y-axis ruler -->
    </div>
    <div class="content">
        {html_content}
    </div>
    <script>
        // Add measurement ticks
        const guide = document.querySelector('.measurement-guide');
        for (let y = 0; y <= 500; y += 10) {{
            const tick = document.createElement('div');
            tick.className = 'tick' + (y % 50 === 0 ? ' major' : '');
            tick.style.top = y + 'px';
            if (y % 50 === 0) {{
                tick.innerHTML = '<span>' + y + '</span>';
            }}
            guide.appendChild(tick);
        }}
        
        // Add expected border lines
        const expectedY = {self.EXPECTED_BORDER_Y_POSITIONS};
        const content = document.querySelector('.content');
        expectedY.forEach(y => {{
            const line = document.createElement('div');
            line.className = 'expected-line';
            line.style.top = y + 'px';
            line.setAttribute('data-y', 'Expected: ' + y);
            content.appendChild(line);
        }});
    </script>
</body>
</html>"""
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page(viewport={'width': 1200, 'height': 800})
                
                # Load HTML
                await page.set_content(full_html)
                
                # Wait for rendering
                await page.wait_for_timeout(500)
                
                # Take screenshot
                await page.screenshot(path=str(output_path), full_page=True)
                
                await browser.close()
                
            print(f"✓ Screenshot saved to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Failed to generate screenshot: {e}")
            return None

    
    @pytest.mark.asyncio
    async def test_row_count(self, processed_html):
        """Test that we have the expected number of rows"""
        table_info = self.extract_table_info(processed_html)
        
        if table_info is None:
            pytest.fail("Could not find absolute positioned table")
        
        row_count = len(table_info['rows'])
        print(f"\nFound {row_count} rows in table")
        
        # Elisa invoice should have approximately 17-20 rows
        assert row_count >= 15, f"Too few rows ({row_count}), expected at least 15"
        assert row_count <= 25, f"Too many rows ({row_count}), expected at most 25"
        
        print("✓ Row count is within expected range")
    
    @pytest.mark.asyncio
    async def test_border_positions(self, processed_html):
        """
        Verify that borders exist at the expected Y positions.
        
        This test uses Playwright to extract ACTUAL rendered border positions
        from the browser, accounting for padding, rounding, and rendering quirks.
        """
        # Extract actual browser-rendered border positions
        print("\nExtracting actual border positions from browser rendering...")
        actual_border_y = await self.extract_actual_border_positions(processed_html)
        
        if actual_border_y is None:
            pytest.skip("Playwright not available - cannot extract actual border positions")
        
        print(f"\nFound {len(actual_border_y)} borders in rendered HTML")
        print(f"Expected {len(self.EXPECTED_BORDER_Y_POSITIONS)} borders from PDF")
        
        # Check borders sequentially (in order)
        failures = []
        tolerance = 1.5  # pixels
        
        # Compare borders in order
        max_comparisons = min(len(self.EXPECTED_BORDER_Y_POSITIONS), len(actual_border_y))
        
        print(f"\nSequential border comparison (actual browser rendering):")
        print(f"{'#':<4} {'Expected':<12} {'Actual':<12} {'Diff':<10} {'Status'}")
        print("-" * 60)
        
        for i in range(max_comparisons):
            expected_y = self.EXPECTED_BORDER_Y_POSITIONS[i]
            actual_y = actual_border_y[i]
            diff = actual_y - expected_y
            
            status = "✓" if abs(diff) <= tolerance else "❌"
            
            print(f"{i+1:<4} {expected_y:<12.1f} {actual_y:<12.1f} {diff:+10.2f} {status}")
            
            if abs(diff) > tolerance:
                failures.append(
                    f"Border #{i+1}: Expected Y={expected_y}, Actual Y={actual_y:.1f}, "
                    f"Diff={diff:+.2f}px"
                )
        
        # Check if counts match
        if len(self.EXPECTED_BORDER_Y_POSITIONS) != len(actual_border_y):
            failures.append(
                f"Border count mismatch: Expected {len(self.EXPECTED_BORDER_Y_POSITIONS)}, "
                f"Found {len(actual_border_y)}"
            )
        
        if failures:
            print("\n❌ FAILURES:")
            for failure in failures:
                print(f"  - {failure}")
            pytest.fail(f"\n{len(failures)} border position mismatches:\n" + "\n".join(failures))
        
        print(f"\n✓ All {len(self.EXPECTED_BORDER_Y_POSITIONS)} borders match sequentially!")
    
    @pytest.mark.asyncio
    async def test_row_heights(self, processed_html):
        """
        Analyze row heights to ensure they match PDF proportions.
        """
        table_info = self.extract_table_info(processed_html)
        
        if table_info is None:
            pytest.fail("Could not find absolute positioned table")
        
        print("\nRow Heights Analysis:")
        print(f"{'Row':<5} {'Y-Top':<8} {'Y-Bottom':<10} {'Height':<8} {'Borders':<12} {'Text'}")
        print("-" * 100)
        
        for i, row in enumerate(table_info['rows']):
            borders = []
            if row['has_top_border']:
                borders.append('T')
            if row['has_bottom_border']:
                borders.append('B')
            border_str = '+'.join(borders) if borders else '-'
            
            print(
                f"{i:<5} "
                f"{row['y_top']:<8.1f} "
                f"{row['y_bottom']:<10.1f} "
                f"{row['height']:<8.1f} "
                f"{border_str:<12} "
                f"{row['text'][:50]}"
            )
        
        # Check for suspiciously large or small rows
        heights = [r['height'] for r in table_info['rows']]
        avg_height = sum(heights) / len(heights) if heights else 0
        
        print(f"\nAverage row height: {avg_height:.1f}px")
        print(f"Min height: {min(heights):.1f}px")
        print(f"Max height: {max(heights):.1f}px")
        
        # Most rows should be between 10-30px for this invoice
        reasonable_heights = [h for h in heights if 10 <= h <= 30]
        print(f"Rows with reasonable height (10-30px): {len(reasonable_heights)}/{len(heights)}")
    
    @pytest.mark.asyncio
    async def test_border_coverage(self, processed_html):
        """
        Test that borders are present throughout the table (not just at top/bottom).
        """
        table_info = self.extract_table_info(processed_html)
        
        if table_info is None:
            pytest.fail("Could not find absolute positioned table")
        
        rows_with_borders = sum(
            1 for r in table_info['rows'] 
            if r['has_top_border'] or r['has_bottom_border']
        )
        
        total_rows = len(table_info['rows'])
        coverage = (rows_with_borders / total_rows * 100) if total_rows > 0 else 0
        
        print(f"\nBorder coverage: {rows_with_borders}/{total_rows} rows ({coverage:.1f}%)")
        
        # Most rows should have at least one border in this table
        assert coverage >= 80, f"Border coverage too low ({coverage:.1f}%), expected at least 80%"
        
        print("✓ Good border coverage across table")
    
    @pytest.mark.asyncio
    async def test_specific_row_borders(self, processed_html):
        """
        Test that specific important rows have borders.
        """
        soup = BeautifulSoup(processed_html, 'html.parser')
        
        # Key rows that should have borders
        key_rows = {
            'Mobiiltelefon': 'should have border below',
            'Kokku': 'should have border above and below',
            'Arv': 'header row should have border below'
        }
        
        print("\nChecking key row borders:")
        
        for text, expectation in key_rows.items():
            found = False
            for td in soup.find_all('td'):
                if text in td.get_text():
                    found = True
                    style = td.get('style', '')
                    has_top = 'border-top' in style and 'solid' in style
                    has_bottom = 'border-bottom' in style and 'solid' in style
                    
                    borders = []
                    if has_top:
                        borders.append('top')
                    if has_bottom:
                        borders.append('bottom')
                    
                    border_str = '+'.join(borders) if borders else 'none'
                    print(f"  '{text}': borders={border_str} ({expectation})")
                    break
            
            if not found:
                print(f"  '{text}': NOT FOUND")


# Standalone test runner
async def run_manual_test():
    """Run tests manually without pytest"""
    print("=" * 100)
    print("TABLE ROWS TEST - Elisa Invoice (second-page.pdf)")
    print("=" * 100)
    
    test = TestTableRows()
    
    # Get processed HTML
    pdf_path = Path("./temp/test_pdfs/second-page.pdf")
    if not pdf_path.exists():
        print(f"Error: Test PDF not found at {pdf_path}")
        return
    
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    
    print("\nProcessing PDF...")
    html_content = await convert_pdf_to_html(pdf_content, zoom_level=100.0)
    
    # Save HTML for inspection
    output_path = Path("./temp/table-rows-test-output.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"HTML saved to: {output_path}")
    
    # Generate screenshot with measurement guides
    print("\nGenerating screenshot with measurement guides...")
    screenshot_path = await test.generate_screenshot(html_content)
    if screenshot_path:
        print(f"📸 Screenshot with ruler and expected border lines (in red)")
        print(f"   You can now measure the actual border positions manually!")
    
    # Run tests
    tests = [
        ("Row Count", test.test_row_count),
        ("Border Positions", test.test_border_positions),
        ("Row Heights", test.test_row_heights),
        ("Border Coverage", test.test_border_coverage),
        ("Specific Row Borders", test.test_specific_row_borders),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print("\n" + "=" * 100)
        print(f"Test: {test_name}")
        print("=" * 100)
        try:
            await test_func(html_content)
            print(f"✓ PASSED")
            passed += 1
        except (AssertionError, Exception) as e:
            print(f"❌ FAILED: {e}")
            failed += 1
    
    print("\n" + "=" * 100)
    print(f"Test Summary: {passed} passed, {failed} failed")
    print("=" * 100)


if __name__ == "__main__":
    asyncio.run(run_manual_test())

"""
Debug script to compare specified row heights vs actual rendered heights
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def debug_row_heights():
    pdf_path = Path("./temp/test_pdfs/second-page.pdf")
    
    # Read the generated HTML
    html_path = Path("./temp/table-rows-test-output.html")
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
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
        
        # Extract row height information
        result = await page.evaluate("""
            () => {
                const table = document.querySelector('table[style*="position: absolute"]');
                if (!table) return [];
                
                const rows = table.querySelectorAll('tr');
                const rowData = [];
                
                rows.forEach((row, index) => {
                    const style = row.getAttribute('style') || '';
                    const heightMatch = style.match(/height:\s*([\d.]+)px/);
                    const specifiedHeight = heightMatch ? parseFloat(heightMatch[1]) : 0;
                    
                    const rect = row.getBoundingClientRect();
                    const actualHeight = rect.height;
                    
                    // Get cell padding info
                    const firstCell = row.querySelector('td');
                    const cellStyle = firstCell ? firstCell.getAttribute('style') || '' : '';
                    const paddingMatch = cellStyle.match(/padding:\s*([^;]+)/);
                    
                    // Check for borders
                    const cells = row.querySelectorAll('td');
                    let hasBorder = false;
                    cells.forEach(cell => {
                        const s = cell.getAttribute('style') || '';
                        if (s.includes('border-top') || s.includes('border-bottom')) {
                            hasBorder = true;
                        }
                    });
                    
                    rowData.push({
                        index: index,
                        specifiedHeight: Math.round(specifiedHeight * 100) / 100,
                        actualHeight: Math.round(actualHeight * 100) / 100,
                        diff: Math.round((actualHeight - specifiedHeight) * 100) / 100,
                        hasBorder: hasBorder,
                        padding: paddingMatch ? paddingMatch[1] : 'none'
                    });
                });
                
                return rowData;
            }
        """)
        
        await browser.close()
        
        print("\nRow Height Analysis:")
        print(f"{'Row':<5} {'Specified':<12} {'Actual':<12} {'Diff':<10} {'Border':<8} {'Padding (first 30 chars)'}")
        print("-" * 90)
        
        total_diff = 0
        for row in result:
            padding_str = row['padding'][:30] if row['padding'] != 'none' else 'none'
            border_str = 'Yes' if row['hasBorder'] else 'No'
            print(f"{row['index']:<5} {row['specifiedHeight']:<12.2f} {row['actualHeight']:<12.2f} "
                  f"{row['diff']:+10.2f} {border_str:<8} {padding_str}")
            total_diff += row['diff']
        
        print("-" * 90)
        print(f"Total cumulative difference: {total_diff:.2f}px")
        print(f"Average difference per row: {total_diff / len(result):.2f}px")

if __name__ == "__main__":
    asyncio.run(debug_row_heights())

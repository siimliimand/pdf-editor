"""
Analyze what causes table row expansion in the browser
"""
import asyncio
from playwright.async_api import async_playwright

# Sample row from the provided HTML
html_content = """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin: 0; padding: 0;">
<table style="border-collapse: collapse; table-layout: fixed;">
<tr style="height: 13.5091px;">
<td style="vertical-align: top; box-sizing: border-box; white-space: nowrap; overflow: visible; padding: 2.14294px 135.38px 0px 26.6667px; text-align: left; border-bottom: 1px solid rgb(136, 136, 136);">
<span style="font-size: 12px; line-height: 1; white-space: nowrap; font-weight: 100; color: rgb(0, 0, 0);">Kõned mobiilidele</span>
</td>
</tr>
</table>

<h3>Test variations:</h3>

<!-- Original -->
<h4>1. Original (height: 13.5091px)</h4>
<table style="border-collapse: collapse; table-layout: fixed; width: 400px;">
<tr style="height: 13.5091px; background: #ffe0e0;">
<td style="vertical-align: top; box-sizing: border-box; white-space: nowrap; overflow: visible; padding: 2.14294px 135.38px 0px 26.6667px; text-align: left; border-bottom: 1px solid rgb(136, 136, 136);">
<span style="font-size: 12px; line-height: 1; white-space: nowrap; font-weight: 100; color: rgb(0, 0, 0);">Kõned mobiilidele</span>
</td>
</tr>
</table>

<!-- With line-height: 0 on span -->
<h4>2. With line-height: 0 on span</h4>
<table style="border-collapse: collapse; table-layout: fixed; width: 400px;">
<tr style="height: 13.5091px; background: #e0ffe0;">
<td style="vertical-align: top; box-sizing: border-box; white-space: nowrap; overflow: visible; padding: 2.14294px 135.38px 0px 26.6667px; text-align: left; border-bottom: 1px solid rgb(136, 136, 136);">
<span style="font-size: 12px; line-height: 0; white-space: nowrap; font-weight: 100; color: rgb(0, 0, 0);">Kõned mobiilidele</span>
</td>
</tr>
</table>

<!-- With display: block on span -->
<h4>3. With display: block; height: 12px on span</h4>
<table style="border-collapse: collapse; table-layout: fixed; width: 400px;">
<tr style="height: 13.5091px; background: #e0e0ff;">
<td style="vertical-align: top; box-sizing: border-box; white-space: nowrap; overflow: visible; padding: 2.14294px 135.38px 0px 26.6667px; text-align: left; border-bottom: 1px solid rgb(136, 136, 136);">
<span style="font-size: 12px; line-height: 1; white-space: nowrap; font-weight: 100; color: rgb(0, 0, 0); display: block; height: 12px;">Kõned mobiilidele</span>
</td>
</tr>
</table>

<!-- With padding: 0 on td -->
<h4>4. With padding: 0 on td</h4>
<table style="border-collapse: collapse; table-layout: fixed; width: 400px;">
<tr style="height: 13.5091px; background: #ffffе0;">
<td style="vertical-align: top; box-sizing: border-box; white-space: nowrap; overflow: visible; padding: 0; text-align: left; border-bottom: 1px solid rgb(136, 136, 136);">
<span style="font-size: 12px; line-height: 1; white-space: nowrap; font-weight: 100; color: rgb(0, 0, 0);">Kõned mobiilidele</span>
</td>
</tr>
</table>

<!-- With vertical-align: bottom on td -->
<h4>5. With vertical-align: bottom on td</h4>
<table style="border-collapse: collapse; table-layout: fixed; width: 400px;">
<tr style="height: 13.5091px; background: #ffe0ff;">
<td style="vertical-align: bottom; box-sizing: border-box; white-space: nowrap; overflow: visible; padding: 2.14294px 135.38px 0px 26.6667px; text-align: left; border-bottom: 1px solid rgb(136, 136, 136);">
<span style="font-size: 12px; line-height: 1; white-space: nowrap; font-weight: 100; color: rgb(0, 0, 0);">Kõned mobiilidele</span>
</td>
</tr>
</table>

<!-- With font-size: 0 on td -->
<h4>6. With font-size: 0 on td, font-size: 12px on span</h4>
<table style="border-collapse: collapse; table-layout: fixed; width: 400px;">
<tr style="height: 13.5091px; background: #e0ffff;">
<td style="vertical-align: top; box-sizing: border-box; white-space: nowrap; overflow: visible; padding: 2.14294px 135.38px 0px 26.6667px; text-align: left; border-bottom: 1px solid rgb(136, 136, 136); font-size: 0;">
<span style="font-size: 12px; line-height: 1; white-space: nowrap; font-weight: 100; color: rgb(0, 0, 0);">Kõned mobiilidele</span>
</td>
</tr>
</table>

<!-- With line-height: 1 on td -->
<h4>7. With line-height: 1 on td</h4>
<table style="border-collapse: collapse; table-layout: fixed; width: 400px;">
<tr style="height: 13.5091px; background: #fff0e0;">
<td style="vertical-align: top; box-sizing: border-box; white-space: nowrap; overflow: visible; padding: 2.14294px 135.38px 0px 26.6667px; text-align: left; border-bottom: 1px solid rgb(136, 136, 136); line-height: 1;">
<span style="font-size: 12px; line-height: 1; white-space: nowrap; font-weight: 100; color: rgb(0, 0, 0);">Kõned mobiilidele</span>
</td>
</tr>
</table>

</body>
</html>
"""

async def analyze():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1200, 'height': 1400})
        
        await page.set_content(html_content)
        await page.wait_for_timeout(500)
        
        # Measure each variation
        results = await page.evaluate("""
            () => {
                const tables = document.querySelectorAll('table');
                const measurements = [];
                
                tables.forEach((table, index) => {
                    const tr = table.querySelector('tr');
                    if (!tr) return;
                    
                    const td = tr.querySelector('td');
                    const span = tr.querySelector('span');
                    
                    const trRect = tr.getBoundingClientRect();
                    const tdRect = td ? td.getBoundingClientRect() : null;
                    const spanRect = span ? span.getBoundingClientRect() : null;
                    
                    const style = tr.getAttribute('style') || '';
                    const heightMatch = style.match(/height:\\s*([\\d.]+)px/);
                    const specifiedHeight = heightMatch ? parseFloat(heightMatch[1]) : 0;
                    
                    measurements.push({
                        index: index,
                        specifiedHeight: specifiedHeight,
                        trActualHeight: Math.round(trRect.height * 100) / 100,
                        tdActualHeight: tdRect ? Math.round(tdRect.height * 100) / 100 : 0,
                        spanActualHeight: spanRect ? Math.round(spanRect.height * 100) / 100 : 0,
                        diff: Math.round((trRect.height - specifiedHeight) * 100) / 100
                    });
                });
                
                return measurements;
            }
        """)
        
        await browser.close()
        
        print("\nRow Height Analysis - Testing Different Approaches:")
        print("=" * 100)
        print(f"{'#':<3} {'Specified':<12} {'TR Height':<12} {'TD Height':<12} {'Span Height':<12} {'Diff':<10} {'Description'}")
        print("-" * 100)
        
        descriptions = [
            "Original",
            "line-height: 0 on span",
            "display: block; height: 12px on span",
            "padding: 0 on td",
            "vertical-align: bottom on td",
            "font-size: 0 on td",
            "line-height: 1 on td"
        ]
        
        for i, result in enumerate(results):
            desc = descriptions[i] if i < len(descriptions) else "Unknown"
            print(f"{i:<3} {result['specifiedHeight']:<12.2f} {result['trActualHeight']:<12.2f} "
                  f"{result['tdActualHeight']:<12.2f} {result['spanActualHeight']:<12.2f} "
                  f"{result['diff']:+10.2f} {desc}")
        
        print("=" * 100)
        
        # Find the best solution
        best = min(results, key=lambda x: abs(x['diff']))
        best_idx = results.index(best)
        print(f"\n✓ Best solution: #{best_idx} - {descriptions[best_idx]}")
        print(f"  Difference: {best['diff']:+.2f}px")

if __name__ == "__main__":
    asyncio.run(analyze())

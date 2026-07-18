
import unittest
from backend.services.xml_parser import XMLToHTMLParser, TableRow, TextElement

class TestXMLParserGrid(unittest.TestCase):
    def test_global_column_detection(self):
        # Mock rows with elements aligned in columns
        # Col 1: x=10
        # Col 2: x=100
        # Col 3: x=200
        
        row1 = TableRow(top=10, height=20, elements=[
            TextElement(text="R1C1", top=10, left=10, width=50, height=12, font_spec=None, font_size=12),
            TextElement(text="R1C2", top=10, left=100, width=50, height=12, font_spec=None, font_size=12),
        ])
        
        row2 = TableRow(top=30, height=20, elements=[
            TextElement(text="R2C1", top=30, left=11, width=50, height=12, font_spec=None, font_size=12), # 1px diff
            TextElement(text="R2C3", top=30, left=200, width=50, height=12, font_spec=None, font_size=12),
        ])
        
        parser = XMLToHTMLParser("<root></root>") # Dummy XML
        rows = [row1, row2]
        
        cols = parser._detect_global_columns(rows)
        # Expect clusters around 10, 100, 200
        # 10 and 11 should cluster to ~10
        
        print(f"Detected columns: {cols}")
        self.assertEqual(len(cols), 3)
        self.assertTrue(9 <= cols[0] <= 11)
        self.assertTrue(99 <= cols[1] <= 101)
        self.assertTrue(199 <= cols[2] <= 201)

    def test_render_table_grid(self):
        row1 = TableRow(top=10, height=20, elements=[
            TextElement(text="A", top=10, left=10, width=20, height=10, font_spec=None, font_size=10),
            TextElement(text="B", top=10, left=50, width=20, height=10, font_spec=None, font_size=10)
        ])
        parser = XMLToHTMLParser("<root></root>")
        parser.fonts = {}
        
        html = parser._render_table([row1], margin_top=0)
        print(html)
        self.assertIn("table-layout: fixed", html)
        self.assertIn("width: 20px", html) # Width between 10 and 50 is 40? No, width col 1 is 50-10=40. width col 2?
        # The logic: next_col_left - col_left.
        # Col 1: 10. Col 2: 50.
        # Width 1 = 40.
        # Width 2 (last col) = max_right - 50. Element B width 20 -> max_right 70. Width 2 = 20.
        
        self.assertIn('width: 40px', html) # Col 1
        self.assertIn('width: 20px', html) # Col 2

if __name__ == '__main__':
    unittest.main()

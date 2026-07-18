import unittest
from backend.services.xml_parser.models import TableDefinition, TableCell
from backend.services.xml_parser.renderers import render_grid_table

class TestTableRenderMargin(unittest.TestCase):
    def test_grid_table_margin(self):
        # Create a mock TableDefinition
        # rect = (top, left, bottom, right)
        table = TableDefinition(
            rect=(100, 50, 300, 400), # Left margin should be 50
            row_positions=[100, 200, 300],
            col_positions=[50, 200, 400],
            cells=[
                TableCell(row_idx=0, col_idx=0, row_span=1, col_span=1, text_elements=[], style_top="", style_bottom="", style_left="", style_right=""),
                TableCell(row_idx=0, col_idx=1, row_span=1, col_span=1, text_elements=[], style_top="", style_bottom="", style_left="", style_right=""),
                TableCell(row_idx=1, col_idx=0, row_span=1, col_span=1, text_elements=[], style_top="", style_bottom="", style_left="", style_right=""),
                TableCell(row_idx=1, col_idx=1, row_span=1, col_span=1, text_elements=[], style_top="", style_bottom="", style_left="", style_right="")
            ]
        )
        
        html = render_grid_table(table, block_top=10, images_dir=None)
        
        # Check for left: 50px (absolute positioning)
        self.assertIn("left: 50px", html)
        self.assertIn("top: 100px", html)
        
        # Check total width
        # Col widths: 200-50=150, 400-200=200. Total = 350.
        # table w = 400 - 50 = 350.
        self.assertIn("width: 350px", html)

    def test_legacy_table_margin(self):
        from backend.services.xml_parser.models import TableRow, TextElement
        from backend.services.xml_parser.renderers import render_legacy_table

        # Mock rows
        # Row 1 has elements starting at x=50
        row1 = TableRow(top=10, height=20, elements=[
            TextElement(text="A", top=10, left=50, width=50, height=10, font_spec=None, font_size=10),
            TextElement(text="B", top=10, left=150, width=50, height=10, font_spec=None, font_size=10)
        ])
        
        # render_legacy_table(rows, margin_top, page_vectors, images_dir)
        html = render_legacy_table([row1], block_top=10, page_vectors=[], images_dir=None)
        
        # Min left should be 50
        self.assertIn("left: 50px", html)
        self.assertIn("top: 10px", html)


if __name__ == '__main__':
    unittest.main()

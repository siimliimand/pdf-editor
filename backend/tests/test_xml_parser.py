import unittest
import tempfile
import shutil
import base64
from pathlib import Path
from services.xml_parser import parse_xml_to_html

class TestXMLParser(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_simple_table(self):
        xml = """
        <pdf2xml>
            <page number="1" top="0" left="0" height="1000" width="800">
                <text top="100" left="50" width="100" height="12" font="0">Invoice #123</text>
                
                <!-- Header Row -->
                <text top="150" left="50" width="50" height="10" font="0">Item</text>
                <text top="150" left="200" width="50" height="10" font="0">Price</text>
                
                <!-- Data Row -->
                <text top="170" left="50" width="50" height="10" font="0">Widget</text>
                <text top="170" left="200" width="50" height="10" font="0">$10.00</text>
            </page>
        </pdf2xml>
        """
        html = parse_xml_to_html(xml, self.test_dir)
        
        # Invoice should be text/p
        self.assertIn("Invoice #123", html)
        self.assertIn("<p", html) 
        
        # Table should exist
        self.assertIn("<table", html)
        self.assertIn("Widget", html)
        self.assertIn("$10.00", html)
        
        # We expect a table with 2 rows (Header, Data)
        self.assertGreaterEqual(html.count("<tr"), 2)

    def test_bold_text(self):
        xml = """
        <pdf2xml>
            <!-- Fontspec with bold -->
            <fontspec id="0" size="12" family="Times" color="#000000" isBold="1" />
            <fontspec id="1" size="12" family="Arial-Bold" color="#000000" />
            <page number="1" width="800">
                <text top="100" left="100" width="100" height="12" font="0">This is Bold</text>
                <text top="120" left="100" width="100" height="12" font="1">Also Bold</text>
            </page>
        </pdf2xml>
        """
        html = parse_xml_to_html(xml, self.test_dir)
        self.assertIn("font-weight: bold", html)
        self.assertIn("This is Bold", html)
        self.assertIn("Also Bold", html)

    def test_image_embedding(self):
        # Create a dummy image
        img_name = "test_image.png"
        img_path = self.test_dir / img_name
        with open(img_path, "wb") as f:
            f.write(b"fake_image_content")
            
        xml = f"""
        <pdf2xml>
            <page number="1" width="800">
                <image top="50" left="50" width="100" height="100" src="{img_name}"/>
            </page>
        </pdf2xml>
        """
        html = parse_xml_to_html(xml, self.test_dir)
        
        self.assertIn("<img", html)
        # Check base64 content
        # b64("fake_image_content") = ZmFrZV9pbWFnZV9jb250ZW50
        self.assertIn("ZmFrZV9pbWFnZV9jb250ZW50", html)

    def test_clean_borders(self):
        xml = """
        <pdf2xml>
            <page number="1" width="800">
                <text top="150" left="50" width="50" height="10" font="0">Cell 1</text>
                <text top="150" left="200" width="50" height="10" font="0">Cell 2</text>
            </page>
        </pdf2xml>
        """
        html = parse_xml_to_html(xml, self.test_dir)
        
        # Should not have border: 1px solid
        self.assertNotIn("border: 1px solid", html)
        # Should have border: none
        self.assertIn("border: none", html)

if __name__ == '__main__':
    unittest.main()

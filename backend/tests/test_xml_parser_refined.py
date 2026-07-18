import unittest
from services.xml_parser import parse_xml_to_html

class TestXMLParserRefined(unittest.TestCase):
    def test_mixed_content(self):
        # A mix of header (single col), table (multi col), and footer (single col)
        xml = """
        <pdf2xml>
            <page number="1" top="0" left="0" height="1000" width="800">
                <!-- Header: Address block (Text Block) -->
                <text top="50" left="50" width="200" height="12" font="0">My Company Inc</text>
                <text top="70" left="50" width="200" height="12" font="0">123 Business Rd</text>
                
                <!-- Table Header (Table Block) -->
                <text top="150" left="50" width="50" height="10" font="0">Item</text>
                <text top="150" left="300" width="50" height="10" font="0">Price</text>
                
                <!-- Table Row 1 -->
                <text top="170" left="50" width="50" height="10" font="0">Widget Alpha</text>
                <text top="170" left="300" width="50" height="10" font="0">$10.00</text>
                
                <!-- Footer (Text Block) -->
                <text top="300" left="50" width="300" height="10" font="0">Thank you for your business!</text>
                
                <!-- Hidden DFC Data (Should be removed) -->
                <text top="400" left="0" width="0" height="0" font="0">DFC_BEGINRECORDS</text>
            </page>
        </pdf2xml>
        """
        html = parse_xml_to_html(xml)
        
        print(html)
        
        # 1. Header should be paragraphs (Text Block)
        self.assertIn("My Company Inc", html)
        # Check that it is NOT inside a TD (simple check: if it's text block, it shouldn't be wrapped in td immediately)
        # Or better: check that we switch from P to Table
        
        # 2. Table content should be in table
        self.assertIn("<table", html)
        self.assertIn("Widget Alpha", html)
        
        # 3. Footer should be paragraph
        self.assertIn("Thank you for your business!", html)
        
        # 4. DFC data should be gone
        self.assertNotIn("DFC_BEGINRECORDS", html)
        
        # Check structure count
        # Should have at least one table and some p tags
        self.assertIn("<p ", html)
        self.assertIn("<table", html)

if __name__ == '__main__':
    unittest.main()

import unittest
from backend.services.xml_parser.parser import XMLToHTMLParser

class TestPageDimensions(unittest.TestCase):
    def test_page_height_rendered(self):
        # Mock XML with specific dimensions
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
        <pages>
            <page id="1" bbox="0.000,0.000,595.000,842.000" rotate="0" width="595" height="842" number="1">
            </page>
        </pages>
        """
        
        parser = XMLToHTMLParser(xml_content)
        html = parser.parse()
        
        # We expect the output div to have height or min-height set to 842px
        # Current implementation likely lacks this.
        print(html)
        self.assertIn('height: 842px', html)

if __name__ == '__main__':
    unittest.main()

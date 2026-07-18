from typing import List
import fitz  # PyMuPDF

from ...models import TableDefinition
from .grid import extract_grid_positions
from .cells import create_cells

class PyMuPDFTableDetector:
    """
    Table detector using PyMuPDF's find_tables() method.
    Provides more accurate table detection than vector-based approach.
    """
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = None
    
    def __enter__(self):
        self.doc = fitz.open(self.pdf_path)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.doc:
            self.doc.close()
    
    def detect_tables(self, page_num: int, page_height: float) -> List[TableDefinition]:
        """
        Detect tables on a specific page using PyMuPDF.
        
        Args:
            page_num: Page number (1-indexed)
            page_height: Page height for coordinate conversion
            
        Returns:
            List of TableDefinition objects
        """
        if not self.doc:
            self.doc = fitz.open(self.pdf_path)
        
        # PyMuPDF uses 0-indexed pages
        page = self.doc[page_num - 1]
        
        # Find tables using PyMuPDF
        tables = page.find_tables()
        
        if not tables or not tables.tables:
            return []
        
        result = []
        
        for table in tables.tables:
            # Get table bounding box
            bbox = table.bbox  # (x0, y0, x1, y1)
            
            # Convert coordinates from PyMuPDF (bottom-up) to our system (top-down)
            # PyMuPDF: y=0 at bottom, increases upward
            # Our system: y=0 at top, increases downward
            table_left = bbox[0]
            table_top = page_height - bbox[3]  # y1 becomes top
            table_right = bbox[2]
            table_bottom = page_height - bbox[1]  # y0 becomes bottom
            
            # Extract row and column positions
            row_positions, col_positions = extract_grid_positions(
                table, page_height
            )
            
            # Create cells with border information
            cells = create_cells(table, row_positions, col_positions, page_height)
            
            result.append(TableDefinition(
                rect=(table_top, table_left, table_bottom, table_right),
                row_positions=row_positions,
                col_positions=col_positions,
                cells=cells
            ))
        
        return result

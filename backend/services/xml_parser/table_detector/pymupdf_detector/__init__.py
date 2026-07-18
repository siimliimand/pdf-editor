"""
PyMuPDF-based table detector for accurate table detection.
Uses PyMuPDF's built-in table detection which provides exact cell boundaries.
"""

from typing import List
from ...models import TableDefinition
from .core import PyMuPDFTableDetector


def detect_tables_pymupdf(
    pdf_path: str, 
    page_num: int, 
    page_height: float
) -> List[TableDefinition]:
    """
    Convenience function to detect tables using PyMuPDF.
    
    Args:
        pdf_path: Path to PDF file
        page_num: Page number (1-indexed)
        page_height: Page height for coordinate conversion
        
    Returns:
        List of TableDefinition objects
    """
    with PyMuPDFTableDetector(pdf_path) as detector:
        return detector.detect_tables(page_num, page_height)

__all__ = ["PyMuPDFTableDetector", "detect_tables_pymupdf"]

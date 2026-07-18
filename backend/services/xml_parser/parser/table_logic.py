import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path

from ...vector_parser import VectorElement
from ..models import FontSpec, TextElement, TableDefinition
from ..table_detector import TableDetector
from ..extractors import extract_elements

def detect_page_tables(
    page: ET.Element,
    fonts: Dict[str, FontSpec],
    vectors_1x: List[VectorElement],
    page_extracted_images: List[Tuple],
    images_dir: Optional[Path],
    xml_scale: float,
    output_scale: float,
    xml_h: float,
    pdf_path: Optional[str],
    font_extractor = None,
    page_number: int = 1
) -> Tuple[List[TableDefinition], str]:
    
    grid_tables = []
    detection_method = "none"
    
    # Try PyMuPDF detection first if PDF path is available
    if pdf_path:
        try:
            from ..table_detector import detect_tables_pymupdf
            import fitz  # PyMuPDF
            
            # CRITICAL: Get the ACTUAL PDF page height (not scaled XML height)
            # xml_h is already scaled by xml_scale, so using it causes double-scaling
            # We need the original PDF page height for correct coordinate conversion
            doc = fitz.open(pdf_path)
            pdf_page = doc[int(page_number) - 1]
            actual_pdf_height = pdf_page.rect.height
            doc.close()
            
            pymupdf_tables = detect_tables_pymupdf(
                pdf_path, 
                int(page_number), 
                actual_pdf_height  # Use actual PDF height, not xml_h
            )
            
            if pymupdf_tables:
                # Scale PyMuPDF tables to target size
                # PyMuPDF returns coordinates in original PDF space (1x)
                # We need to scale to match the requested zoom level
                total_zoom = xml_scale * output_scale
                
                # Import empty column remover
                from ..table_detector.empty_column_remover import remove_empty_columns
                
                for t in pymupdf_tables:
                    # Remove empty columns BEFORE scaling
                    col_positions_clean, cells_clean = remove_empty_columns(
                        t.col_positions, t.cells,
                        len(t.row_positions)-1, len(t.col_positions)-1
                    )
                    
                    scaled_rect = tuple(x * total_zoom for x in t.rect)
                    scaled_rows = [y * total_zoom for y in t.row_positions]
                    scaled_cols = [x * total_zoom for x in col_positions_clean]
                    
                    grid_tables.append(TableDefinition(
                        rect=scaled_rect,
                        row_positions=scaled_rows,
                        col_positions=scaled_cols,
                        cells=cells_clean
                    ))
                
                detection_method = "pymupdf"
        
        except Exception as e:
            # Will fall back to vector detection
            pass
    
    # Fall back to vector-based detection if PyMuPDF didn't find tables
    if not grid_tables:
        # Extract text elements BEFORE table detection for horizontal-only tables
        # We need 1x scale elements for detection, then we'll scale them later
        elements_1x = extract_elements(
            page, fonts, images_dir, page_extracted_images, int(xml_h), xml_scale, font_extractor, page_number
        )
        text_elements_1x = [e for e in elements_1x if isinstance(e, TextElement)]
        
        detector = TableDetector(vectors_1x)
        grid_tables_1x = detector.detect(text_elements=text_elements_1x)
        
        # Scale detected tables to target size
        total_zoom = xml_scale * output_scale
        
        for t in grid_tables_1x:
            scaled_rect = tuple(x * total_zoom for x in t.rect)
            scaled_rows = [y * total_zoom for y in t.row_positions]
            scaled_cols = [x * total_zoom for x in t.col_positions]
            
            grid_tables.append(TableDefinition(
                rect=scaled_rect,
                row_positions=scaled_rows,
                col_positions=scaled_cols,
                cells=t.cells
            ))
        
        detection_method = "vector"
            
    return grid_tables, detection_method

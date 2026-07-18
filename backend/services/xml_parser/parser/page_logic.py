import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path

from ...vector_parser import VectorElement
from ..models import FontSpec, TextElement, TableDefinition
from ..table_detector.table_utils import trim_table
from ..flow_processor import group_into_rows, segment_rows, assign_elements_to_table

from .vector_logic import process_vectors_for_page
from .block_logic import merge_and_sort_blocks
from .rendering_logic import render_page_blocks
from .table_logic import detect_page_tables
from .element_logic import extract_and_scale_elements

def process_page(
    page: ET.Element,
    fonts: Dict[str, FontSpec],
    page_vectors: List[VectorElement],
    page_extracted_images: List[Tuple],
    images_dir: Optional[Path],
    xml_scale: float,
    output_scale: float,
    font_extractor = None,
    page_number: int = 1,
    pdf_path: Optional[str] = None,
    font_family_mapping: Dict[str, str] = None
) -> str:
    """
    Process a single XML page and return its HTML representation.
    """
    page_number = page.get('number')
    
    # Apply output_scale to the dimensions from XML
    # parser.py: width = int(float(page.get('width')) * self.output_scale)
    width = int(float(page.get('width')) * output_scale)
    height = int(float(page.get('height')) * output_scale)
    
    xml_h = float(page.get('height'))
    
    # Start HTML part for page
    html_parts = []
    html_parts.append(f'<div id="page-{page_number}" class="pdf-page" style="min-width: {width}px; width: {width}px; height: {height}px; position: relative; margin: 0 auto 20px auto; padding: 0px; box-sizing: border-box; background: white; box-shadow: 0 0 10px rgba(0,0,0,0.1);">')
    
    # Process Vectors
    # We pass the TARGET page height which is 'height' (scaled by output_scale) ??
    # Wait, in parser.py: 
    # new_y0 = height - (v.y1 * total_zoom) where height was the scaled height.
    # So yes, pass 'height'.
    vectors_1x, converted_vectors = process_vectors_for_page(
        page_vectors, xml_scale, output_scale, float(height), xml_h
    )
    
    # 1. Detect Tables
    grid_tables, detection_method = detect_page_tables(
        page, fonts, vectors_1x, page_extracted_images, images_dir,
        xml_scale, output_scale, xml_h, pdf_path, font_extractor, page_number
    )
    
    # 2. Extract Elements
    elements = extract_and_scale_elements(
        page, fonts, page_extracted_images, images_dir, xml_h,
        xml_scale, output_scale, font_extractor, page_number, font_family_mapping
    )


    # 3. Assign Elements to Grid Tables
    assigned_ids = set()
    
    for i, t in enumerate(grid_tables):
        assigned = assign_elements_to_table(t, elements)
        for el in assigned:
            assigned_ids.add(id(el))
            
        # Trim empty rows from top/bottom to fix visual alignment
        # This is CRITICAL because removing text above table (like "Elisa...")
        # leaves empty rows that still overlap with that text visually.
        grid_tables[i] = trim_table(t)
        
        # Merge full-width rows (after text assignment)
        # This handles rows where first cell has text and rest are empty
        from ..table_detector.cell_merger import merge_full_width_rows
        num_rows = len(t.row_positions) - 1
        num_cols = len(t.col_positions) - 1
        grid_tables[i].cells = merge_full_width_rows(grid_tables[i].cells, num_rows, num_cols)
            
    # 4. Separate remaining elements
    remaining_elements = [e for e in elements if id(e) not in assigned_ids]
    
    # 5. Group remaining elements into rows (Text Flow)
    # Pass output_scale to make row grouping scale-aware (fixes row splitting at high zoom)
    rows = group_into_rows(remaining_elements, scale=output_scale)
    text_blocks = segment_rows(rows) # Returns ('TEXT', [rows]) or ('TABLE', [rows])
    
    # Count tables before merging
    table_count_before = sum(1 for block_type, _ in text_blocks if block_type == 'TABLE')
    
    # 5.5. Merge adjacent legacy tables (NEW - fixes fragmentation)
    from ..flow_processor import merge_legacy_tables
    text_blocks = merge_legacy_tables(text_blocks, scale=output_scale)
    
    # Count tables after merging
    table_count_after = sum(1 for block_type, _ in text_blocks if block_type == 'TABLE')
    
    
    # 5.6. Merge adjacent grid tables (NEW - fixes fragmentation)
    if len(grid_tables) > 1:
        from ..flow_processor import merge_adjacent_tables
        grid_count_before = len(grid_tables)
        grid_tables = merge_adjacent_tables(grid_tables)
    
    # 6. Merge Grid Tables and Text Blocks by Y-position
    all_blocks = merge_and_sort_blocks(grid_tables, text_blocks)
    
    # 7. Render Sequence
    block_html_parts = render_page_blocks(all_blocks, images_dir, converted_vectors, output_scale)
    html_parts.extend(block_html_parts)
    
    html_parts.append('</div>')
    
    return "\n".join(html_parts)

from typing import List, Dict, Any, Optional
from pathlib import Path
from ...vector_parser import VectorElement
from ..models import TableDefinition
from ..renderers import render_grid_table, render_legacy_table, render_text_block

def render_page_blocks(
    all_blocks: List[Dict[str, Any]], 
    images_dir: Optional[Path], 
    converted_vectors: List[VectorElement],
    scale: float = 1.0
) -> List[str]:
    """
    Render a list of sorted blocks into HTML parts using absolute positioning.
    
    Args:
        all_blocks: Sorted list of blocks.
        images_dir: Directory for images.
        converted_vectors: Converted vectors for legacy table rendering.
        scale: Scale factor for zoom (default 1.0)
        
    Returns:
        List[str]: List of HTML strings.
    """
    html_parts = []
    
    for block in all_blocks:
        b_type = block['type']
        current_top = block['top']
        
        if b_type == 'GRID':
            table_def = block['obj']
            html_parts.append(render_grid_table(table_def, current_top, images_dir))
            
        else: # LEGACY
            sub_type, rows_list = block['obj']
            if sub_type == 'TABLE':
                html_parts.append(render_legacy_table(rows_list, current_top, converted_vectors, images_dir, scale))
            else:
                html_parts.append(render_text_block(rows_list, current_top, images_dir, converted_vectors))
            
    return html_parts

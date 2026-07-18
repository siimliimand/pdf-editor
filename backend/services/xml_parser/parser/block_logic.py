from typing import List, Dict, Any, Tuple
from ..models import TableDefinition, TableRow

def merge_and_sort_blocks(
    grid_tables: List[TableDefinition], 
    text_blocks: List[Tuple[str, List[TableRow]]]
) -> List[Dict[str, Any]]:
    """
    Merge grid tables and text blocks into a single list of blocks sorted by vertical position.
    
    Args:
        grid_tables: List of detected grid tables.
        text_blocks: List of text blocks (type, rows).
    
    Returns:
        List[Dict[str, Any]]: Sorted blocks. Each block is a dict with 'type', 'obj', 'top'.
    """
    all_blocks = []
    
    for t in grid_tables:
        all_blocks.append({
            'type': 'GRID',
            'obj': t,
            'top': t.rect[0] if t.rect else 0 # rect is (y0, x0, y1, x1)? No, usually (top, left, bottom, right) or similar.
                                              # In parser.py: 'top': t.rect[0]
                                              # Let's verify t.rect definition. 
        })
        
    for b_type, b_rows in text_blocks:
        if b_rows:
            all_blocks.append({
                'type': 'LEGACY',
                'obj': (b_type, b_rows),
                'top': b_rows[0].top
            })
    
    # Sort by top position
    all_blocks.sort(key=lambda x: x['top'])
    
    return all_blocks

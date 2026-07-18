from typing import List, Tuple
from ...models import TableDefinition, TableRow, TableCell


def should_merge_tables(table1: TableDefinition, table2: TableDefinition, max_gap: float = 30.0) -> bool:
    """
    Determine if two tables should be merged based on their positions and structure.
    
    Args:
        table1: First table (should be above table2)
        table2: Second table (should be below table1)
        max_gap: Maximum vertical gap between tables to consider merging (default 30px)
        
    Returns:
        True if tables should be merged, False otherwise
    """
    # Check if tables are vertically adjacent
    # table.rect = (top, left, bottom, right)
    table1_bottom = table1.rect[2]
    table2_top = table2.rect[0]
    
    vertical_gap = table2_top - table1_bottom
    
    # If gap is too large, don't merge
    if vertical_gap > max_gap:
        return False
    
    # Check horizontal overlap
    table1_left = table1.rect[1]
    table1_right = table1.rect[3]
    table2_left = table2.rect[1]
    table2_right = table2.rect[3]
    
    # Calculate overlap
    overlap_left = max(table1_left, table2_left)
    overlap_right = min(table1_right, table2_right)
    overlap_width = overlap_right - overlap_left
    
    # Require at least 50% horizontal overlap
    table1_width = table1_right - table1_left
    table2_width = table2_right - table2_left
    min_width = min(table1_width, table2_width)
    
    if overlap_width < min_width * 0.5:
        return False
    
    return True


def merge_tables(table1: TableDefinition, table2: TableDefinition) -> TableDefinition:
    """
    Merge two tables into one.
    
    Args:
        table1: First table (top)
        table2: Second table (bottom)
        
    Returns:
        Merged TableDefinition
    """
    # Combine rectangles
    merged_top = min(table1.rect[0], table2.rect[0])
    merged_left = min(table1.rect[1], table2.rect[1])
    merged_bottom = max(table1.rect[2], table2.rect[2])
    merged_right = max(table1.rect[3], table2.rect[3])
    
    merged_rect = (merged_top, merged_left, merged_bottom, merged_right)
    
    # Combine row positions (remove duplicates, keep sorted)
    merged_rows = sorted(list(set(table1.row_positions + table2.row_positions)))
    
    # Combine column positions (remove duplicates, keep sorted)
    merged_cols = sorted(list(set(table1.col_positions + table2.col_positions)))
    
    # Combine cells
    # Need to re-index cells based on new row/col positions
    merged_cells = []
    
    # Add cells from table1
    for cell in table1.cells:
        # Find new row index
        old_row_start = table1.row_positions[cell.row_idx]
        new_row_idx = merged_rows.index(old_row_start)
        
        # Find new col index
        old_col_start = table1.col_positions[cell.col_idx]
        new_col_idx = merged_cols.index(old_col_start)
        
        # Create new cell with updated indices
        merged_cells.append(TableCell(
            row_idx=new_row_idx,
            col_idx=new_col_idx,
            row_span=cell.row_span,
            col_span=cell.col_span,
            text_elements=cell.text_elements,
            style_top=cell.style_top,
            style_bottom=cell.style_bottom,
            style_left=cell.style_left,
            style_right=cell.style_right,
            background_color=cell.background_color
        ))
    
    # Add cells from table2
    for cell in table2.cells:
        # Find new row index
        old_row_start = table2.row_positions[cell.row_idx]
        new_row_idx = merged_rows.index(old_row_start)
        
        # Find new col index
        old_col_start = table2.col_positions[cell.col_idx]
        new_col_idx = merged_cols.index(old_col_start)
        
        # Create new cell with updated indices
        merged_cells.append(TableCell(
            row_idx=new_row_idx,
            col_idx=new_col_idx,
            row_span=cell.row_span,
            col_span=cell.col_span,
            text_elements=cell.text_elements,
            style_top=cell.style_top,
            style_bottom=cell.style_bottom,
            style_left=cell.style_left,
            style_right=cell.style_right,
            background_color=cell.background_color
        ))
    
    return TableDefinition(
        rect=merged_rect,
        row_positions=merged_rows,
        col_positions=merged_cols,
        cells=merged_cells
    )

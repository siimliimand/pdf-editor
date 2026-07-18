from ..models import TableDefinition

def trim_table(table: TableDefinition) -> TableDefinition:
    """
    Remove empty rows from the top and bottom of the table.
    Updates the table rect and row indices.
    """
    # Find active rows (rows with text)
    active_rows = set()
    for cell in table.cells:
        if cell.text_elements:
            # Mark this row and any spanned rows as active
            for r in range(cell.row_idx, cell.row_idx + cell.row_span):
                active_rows.add(r)
    
    if not active_rows:
        return table
        
    num_rows = len(table.row_positions) - 1
    
    # Find start index
    start_idx = 0
    while start_idx < num_rows and start_idx not in active_rows:
        start_idx += 1
        
    # Find end index
    end_idx = num_rows - 1
    while end_idx >= 0 and end_idx not in active_rows:
        end_idx -= 1
        
    # If no trimming needed
    if start_idx == 0 and end_idx == num_rows - 1:
        return table
        
    # Create new row positions
    new_row_positions = table.row_positions[start_idx : end_idx + 2]
    
    # Filter and update cells
    new_cells = []
    for cell in table.cells:
        # Calculate intersection of cell with the new range [start_idx, end_idx]
        cell_start = cell.row_idx
        cell_end = cell.row_idx + cell.row_span # Exclusive
        
        # Kept range is [start_idx, end_idx + 1)
        kept_start = start_idx
        kept_end = end_idx + 1
        
        # Intersection
        overlap_start = max(cell_start, kept_start)
        overlap_end = min(cell_end, kept_end)
        
        if overlap_start < overlap_end:
            # We have overlap
            new_row_idx = overlap_start - kept_start
            new_row_span = overlap_end - overlap_start
            
            # Create a copy or update in place? Models seem mutable.
            # Updating in place is safer for reference consistency if needed, 
            # but safer to create new object if we want to avoid side effects.
            # However, looking at the code style, simple update seems intended.
            # BUT we must handle the case where we might process the same object twice? 
            # No, table.cells should be unique objects.
            
            cell.row_idx = new_row_idx
            cell.row_span = new_row_span
            new_cells.append(cell)
            
    # Update rect
    new_rect = (
        new_row_positions[0],  # top
        table.rect[1],         # left
        new_row_positions[-1], # bottom
        table.rect[3]          # right
    )
    
    return TableDefinition(
        rect=new_rect,
        row_positions=new_row_positions,
        col_positions=table.col_positions,
        cells=new_cells
    )

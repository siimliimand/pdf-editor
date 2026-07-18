from typing import List
from ...models import TableCell

def create_cells(
    table, 
    row_positions: List[float], 
    col_positions: List[float],
    page_height: float
) -> List[TableCell]:
    """
    Create TableCell objects from PyMuPDF table data.
    """
    cells = []
    
    # Create a mapping of (row_idx, col_idx) -> cell data
    all_rows = []
    if table.header:
        all_rows.append(table.header)
    if table.rows:
        all_rows.extend(table.rows)
    
    for row_idx, row in enumerate(all_rows):
        if not row.cells:
            continue
        
        col_idx = 0
        for cell in row.cells:
            if not cell:
                col_idx += 1
                continue
            
            # cell is tuple: (x0, y0, x1, y1, text, type)
            x0, y0, x1, y1 = cell[0], cell[1], cell[2], cell[3]
            
            # Convert Y coordinates
            cell_top = page_height - y1
            cell_bottom = page_height - y0
            
            # Find row and column indices
            try:
                r_idx = row_positions.index(cell_top)
                c_idx = col_positions.index(x0)
            except ValueError:
                # Cell position doesn't match grid - find closest
                r_idx = min(range(len(row_positions)), 
                           key=lambda i: abs(row_positions[i] - cell_top))
                c_idx = min(range(len(col_positions)), 
                           key=lambda i: abs(col_positions[i] - x0))
            
            # Calculate spans
            try:
                r_end_idx = row_positions.index(cell_bottom)
                c_end_idx = col_positions.index(x1)
            except ValueError:
                r_end_idx = min(range(len(row_positions)), 
                               key=lambda i: abs(row_positions[i] - cell_bottom))
                c_end_idx = min(range(len(col_positions)), 
                               key=lambda i: abs(col_positions[i] - x1))
            
            row_span = max(1, r_end_idx - r_idx)
            col_span = max(1, c_end_idx - c_idx)
            
            # Create cell with basic border (PyMuPDF doesn't provide border details)
            # We'll use simple solid borders for now
            cells.append(TableCell(
                row_idx=r_idx,
                col_idx=c_idx,
                row_span=row_span,
                col_span=col_span,
                text_elements=[],  # Will be filled later
                style_top="1px solid #000",
                style_bottom="1px solid #000",
                style_left="1px solid #000",
                style_right="1px solid #000"
            ))
            
            col_idx += col_span
    
    return cells

from typing import List, Dict, Optional, Tuple
from ..models import TableCell

def merge_full_width_rows(cells: List[TableCell], num_rows: int, num_cols: int) -> List[TableCell]:
    """
    Merge cells in rows where first cell has text and all other cells are empty.
    This handles full-width rows like headers and subtitles.
    
    Args:
        cells: List of table cells
        num_rows: Number of rows in the grid
        num_cols: Number of columns in the grid
        
    Returns:
        List of cells with full-width rows merged
    """
    # Group cells by row
    rows = {}
    for cell in cells:
        if cell.row_idx not in rows:
            rows[cell.row_idx] = []
        rows[cell.row_idx].append(cell)
    
    merged_cells = []
    for row_idx in range(num_rows):
        row_cells = sorted(rows.get(row_idx, []), key=lambda c: c.col_idx)
        
        if not row_cells:
            continue
        
        # Check if this is a full-width row:
        # - First cell (col 0) has text
        # - All other cells are empty
        # - All cells in the row are present (no merged cells yet)
        if len(row_cells) == num_cols and row_cells[0].col_idx == 0:
            first_cell = row_cells[0]
            other_cells = row_cells[1:]
            
            first_has_text = len(first_cell.text_elements) > 0
            others_empty = all(len(c.text_elements) == 0 for c in other_cells)
            
            if first_has_text and others_empty:
                # Merge into single cell spanning all columns
                merged_cell = TableCell(
                    row_idx=first_cell.row_idx,
                    col_idx=0,
                    row_span=1,
                    col_span=num_cols,
                    text_elements=first_cell.text_elements,
                    style_top=first_cell.style_top,
                    style_bottom=first_cell.style_bottom,
                    style_left=first_cell.style_left,
                    style_right=row_cells[-1].style_right,  # Use last cell's right border
                    background_color=first_cell.background_color
                )
                merged_cells.append(merged_cell)
                continue
        
        # Keep cells as-is
        merged_cells.extend(row_cells)
    
    return merged_cells

def merge_cells(cells: List[TableCell], num_rows: int, num_cols: int) -> List[TableCell]:
    """
    Merges cells based on missing borders.
    """
    # Create grid for easy access
    grid = {}
    for c in cells:
        grid[(c.row_idx, c.col_idx)] = c
        
    # 2. Horizontal Merge (Robust)
    for r in range(num_rows):
        c = 0
        while c < num_cols - 1:
            cell = grid.get((r, c))
            if not cell or cell.row_span == 0: 
                c += 1
                continue
            
            # Look ahead
            k = 1
            while c + k < num_cols:
                next_cell = grid.get((r, c+k))
                if not next_cell or next_cell.row_span == 0:
                    break
                
                no_right = not cell.style_right
                no_left = not next_cell.style_left
                
                if no_right and no_left:
                    # Merge next_cell into cell
                    cell.col_span += next_cell.col_span
                    cell.style_right = next_cell.style_right
                    
                    # Mark next_cell as removed
                    next_cell.col_span = 0
                    next_cell.row_span = 0
                    
                    k += 1
                else:
                    break
            c += k

    # 3. Vertical Merge
    for c in range(num_cols):
        r = 0
        while r < num_rows - 1:
            cell = grid.get((r, c))
            if not cell or cell.row_span == 0:
                r += 1
                continue
            
            # Look down
            k = 1
            while r + k < num_rows:
                next_cell = grid.get((r+k, c))
                if not next_cell or next_cell.row_span == 0:
                    break
                    
                # Only merge if col_spans match
                if cell.col_span != next_cell.col_span:
                    break
                
                no_bottom = not cell.style_bottom
                no_top = not next_cell.style_top
                
                if no_bottom and no_top:
                    cell.row_span += next_cell.row_span
                    cell.style_bottom = next_cell.style_bottom
                    
                    next_cell.row_span = 0
                    next_cell.col_span = 0
                    k += 1
                else:
                    break
            r += k
            
    # Return only active cells
    active_cells = [c for c in cells if c.row_span > 0 and c.col_span > 0]
    return active_cells



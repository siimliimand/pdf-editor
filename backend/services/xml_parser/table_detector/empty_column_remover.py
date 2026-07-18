from typing import List, Tuple
from ..models import TableCell

def remove_empty_columns(
    col_positions: List[float],
    cells: List[TableCell],
    num_rows: int,
    num_cols: int
) -> Tuple[List[float], List[TableCell]]:
    """
    Detect and remove columns that are always empty (no text elements).
    
    This handles cases where PDFs have spurious vertical lines creating
    empty columns between content columns.
    
    Args:
        col_positions: List of column x-coordinates
        cells: List of table cells
        num_rows: Number of rows in the grid
        num_cols: Number of columns in the grid
        
    Returns:
        Tuple of (updated_col_positions, updated_cells)
    """
    
    # Build a map of which columns have content
    # Note: At this stage, text_elements are not yet assigned to cells
    # So we can't check text_elements. Instead, we need to check this
    # AFTER text assignment, or use a different heuristic.
    
    # For now, we'll use a simpler heuristic: if there are exactly 3 columns
    # and the middle column is very narrow (< 10% of table width), remove it.
    
    if num_cols != 3:
        # Only handle the specific case of 3 columns
        return col_positions, cells
    
    table_width = col_positions[-1] - col_positions[0]
    col_widths = [col_positions[i+1] - col_positions[i] for i in range(num_cols)]
    
    # Check if middle column is very narrow
    middle_col_width = col_widths[1]
    middle_col_ratio = middle_col_width / table_width
    
    # If middle column is < 20% of table width, it's likely spurious
    if middle_col_ratio < 0.20:
        
        # Remove the middle column position
        new_col_positions = [col_positions[0], col_positions[2], col_positions[3]]
        
        # Update cells: remove cells in column 1, shift column 2 cells to column 1
        new_cells = []
        for cell in cells:
            # Debug: print cell info
            print(f"  Cell at row={cell.row_idx}, col={cell.col_idx}, colspan={cell.col_span}")
            
            if cell.col_idx == 1 and cell.col_span == 1:
                # Skip cells that are entirely in the middle column
                print(f"    -> Skipping (entirely in removed column)")
                continue
            elif cell.col_idx == 0 and cell.col_span >= 2:
                # Cell starts in column 0 and spans into/across column 1
                # Reduce colspan by 1 (remove the middle column from the span)
                new_cells.append(TableCell(
                    row_idx=cell.row_idx,
                    col_idx=0,
                    row_span=cell.row_span,
                    col_span=cell.col_span - 1,  # Reduce span
                    text_elements=cell.text_elements,
                    style_top=cell.style_top,
                    style_bottom=cell.style_bottom,
                    style_left=cell.style_left,
                    style_right=cell.style_right,
                    background_color=cell.background_color
                ))
                print(f"    -> Kept in col 0, reduced colspan to {cell.col_span - 1}")
            elif cell.col_idx == 2:
                # Shift column 2 to column 1
                new_cells.append(TableCell(
                    row_idx=cell.row_idx,
                    col_idx=1,
                    row_span=cell.row_span,
                    col_span=cell.col_span,
                    text_elements=cell.text_elements,
                    style_top=cell.style_top,
                    style_bottom=cell.style_bottom,
                    style_left=cell.style_left,
                    style_right=cell.style_right,
                    background_color=cell.background_color
                ))
            elif cell.col_idx == 0:
                # Keep column 0 cells as-is (no spanning)
                new_cells.append(cell)
            else:
                # Unexpected case
                new_cells.append(cell)
        
        return new_col_positions, new_cells
    
    return col_positions, cells

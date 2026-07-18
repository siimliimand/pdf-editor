from typing import List, Tuple

def extract_grid_positions(table, page_height: float) -> Tuple[List[float], List[float]]:
    """
    Extract row and column positions from PyMuPDF table.
    
    Returns:
        Tuple of (row_positions, col_positions)
    """
    row_positions = []
    col_positions = []
    
    # Get unique row positions (Y coordinates)
    # PyMuPDF table.rows contains row data
    if table.rows:
        for row in table.rows:
            if row.cells:
                # Get Y-coordinates from first cell
                cell = row.cells[0]
                if cell:
                    # cell is tuple: (x0, y0, x1, y1, text, type)
                    y0 = cell[1]
                    y1 = cell[3]
                    
                    # Convert to top-down coordinates
                    top = page_height - y1
                    bottom = page_height - y0
                    
                    if top not in row_positions:
                        row_positions.append(top)
                    if bottom not in row_positions:
                        row_positions.append(bottom)
    
    # Get unique column positions (X coordinates)
    if table.header and table.header.cells:
        for cell in table.header.cells:
            if cell:
                x0 = cell[0]
                x1 = cell[2]
                
                if x0 not in col_positions:
                    col_positions.append(x0)
                if x1 not in col_positions:
                    col_positions.append(x1)
    
    # Also check all rows for column positions
    if table.rows:
        for row in table.rows:
            if row.cells:
                for cell in row.cells:
                    if cell:
                        x0 = cell[0]
                        x1 = cell[2]
                        
                        if x0 not in col_positions:
                            col_positions.append(x0)
                        if x1 not in col_positions:
                            col_positions.append(x1)
    
    # Sort positions
    row_positions.sort()
    col_positions.sort()
    
    return row_positions, col_positions

from typing import List, Tuple
from ..models import TableCell
from ...vector_parser import VectorElement
from .coord_utils import cluster_coords
from .line_utils import find_line, format_border



def build_grid(group: List[VectorElement], relevant_v_lines: List[VectorElement]) -> Tuple[List[float], List[float], List[TableCell]]:
    """
    Build table grid from vector lines.
    Now preserves float precision for sub-pixel accuracy.
    """
    
    # Define Table Boundaries
    t_left = min(l.x0 for l in group)
    t_right = max(l.x1 for l in group)
    
    # Construct Grid
    # Horizontal positions (Y) - keep as float for precision
    row_positions = sorted(list(set(l.y0 for l in group)))
    # Consolidate close positions
    row_positions = cluster_coords(row_positions)
    
    # Vertical positions (X) - get from vertical lines AND horizontal line endpoints
    # Some PDFs define columns via vertical lines, others via horizontal line segments
    col_x_from_v_lines = set(v.x0 for v in relevant_v_lines)
    
    # Extract column boundaries from horizontal line segment endpoints
    # This handles PDFs that define columns by breaking horizontal lines at column positions
    col_x_from_h_segments = set()
    for l in group:
        col_x_from_h_segments.add(l.x0)  # Line start
        col_x_from_h_segments.add(l.x1)  # Line end
    
    # Combine both sources
    all_col_x = col_x_from_v_lines | col_x_from_h_segments
    col_positions = sorted(list(all_col_x))
    
    col_positions = cluster_coords(col_positions)
    
    # Ensure we have external boundaries if missing (sometimes border is thick rect)
    if not any(abs(c - t_left) < 5 for c in col_positions): 
        col_positions.insert(0, t_left)
    if not any(abs(c - t_right) < 5 for c in col_positions): 
        col_positions.append(t_right)
    col_positions.sort()
    
    # Filter out spurious columns by removing positions that create very narrow columns
    # This is critical for PDFs that have small line segments creating extra column boundaries
    table_width = col_positions[-1] - col_positions[0]
    min_column_width = table_width * 0.028  # Minimum 2.8% of table width
    
    # Check each adjacent pair of positions to see if they form a valid column
    col_positions_filtered = [col_positions[0]]  # Always keep the first position (left edge)
    
    for i in range(1, len(col_positions)):
        prev_pos = col_positions_filtered[-1]
        curr_pos = col_positions[i]
        column_width = curr_pos - prev_pos
        
        # If this creates a very narrow column, skip this position
        if column_width < min_column_width:
            # Special case: if this is the last position (right edge), 
            # remove the previous position instead of skipping this one
            if i == len(col_positions) - 1:
                col_positions_filtered.pop()  # Remove the previous position
                col_positions_filtered.append(curr_pos)  # Add this one (right edge)
            continue
        
        col_positions_filtered.append(curr_pos)
    
    col_positions = col_positions_filtered
    
    # Create Cells
    cells = []
    for r_i in range(len(row_positions) - 1):
        y_start = row_positions[r_i]
        y_end = row_positions[r_i+1]
        
        for c_i in range(len(col_positions) - 1):
            x_start = col_positions[c_i]
            x_end = col_positions[c_i+1]
            
            # Find borders for this cell
            # Top Border
            b_top = find_line(group, y_start, x_start, x_end, 'H')
            b_bottom = find_line(group, y_end, x_start, x_end, 'H')
            b_left = find_line(relevant_v_lines, x_start, y_start, y_end, 'V')
            b_right = find_line(relevant_v_lines, x_end, y_start, y_end, 'V')
            
            # Apply all detected borders - PDF has horizontal lines at every row boundary
            style_top = format_border(b_top)
            style_bottom = format_border(b_bottom)
            style_left = format_border(b_left)
            style_right = format_border(b_right)
            
            cells.append(TableCell(
                row_idx=r_i, col_idx=c_i, row_span=1, col_span=1,
                text_elements=[],
                style_top=style_top, style_bottom=style_bottom,
                style_left=style_left, style_right=style_right
            ))
            
    return row_positions, col_positions, cells

from typing import List, Optional
from ....vector_parser import VectorElement
from ...models import TextElement, TableDefinition, TableCell
from ..column_inference import infer_columns_from_text
from ..coord_utils import cluster_coords
from ..line_utils import find_line, format_border



def detect_horizontal_table(
    h_lines: List[VectorElement],
    text_elements: List[TextElement]
) -> Optional[TableDefinition]:
    """
    Detect a table from horizontal lines only, inferring columns from text.
    
    Args:
        h_lines: List of horizontal line vectors (already grouped into a table region)
        text_elements: All text elements on the page
        
    Returns:
        TableDefinition if a valid table is detected, None otherwise
    """
    if len(h_lines) < 2:
        return None
    
    # Define table boundaries
    t_top = min(l.y0 for l in h_lines)
    t_bottom = max(l.y0 for l in h_lines)
    t_left = min(l.x0 for l in h_lines)
    t_right = max(l.x1 for l in h_lines)
    
    
    # Build row positions from horizontal lines first
    row_positions = sorted(list(set(l.y0 for l in h_lines)))
    row_positions = cluster_coords(row_positions)
    
    
    # Find text elements within table bounds
    # Crucial: Filter by BOTH horizontal AND vertical boundaries  
    # Only include text that's between the row lines (not just horizontal margins)
    texts_in_table = []
    # Expand capture bounds significantly to catch hanging columns (like "Summa" or totals)
    # The vertical bounds are strict (row lines), but horizontal bounds should be generous
    padding_x = 300.0
    margin = 5.0
    
    for el in text_elements:
        # Check strict vertical bounds (must be within the row lines)
        vert_match = row_positions[0] - margin <= el.top <= row_positions[-1] + margin
        
        # Check expanded horizontal bounds
        horiz_match = t_left - padding_x <= el.left <= t_right + padding_x
        
        if vert_match and horiz_match:
            texts_in_table.append(el)
    
    
    if not texts_in_table:
        return None
        
    # RESIZE TABLE BOUNDS to include the text we found
    # This ensures that columns inferred from this text are considered "inside" the table
    text_left = min(el.left for el in texts_in_table)
    text_right = max(el.left + el.width for el in texts_in_table)
    
    # Union of line bounds and text bounds
    t_left = min(t_left, text_left)
    t_right = max(t_right, text_right)
    
    
    # Extract column positions from horizontal line segment endpoints
    # This is how PDFs typically define column boundaries - by breaking horizontal lines
    col_x_positions = set()
    for l in h_lines:
        col_x_positions.add(l.x0)  # Line segment start
        col_x_positions.add(l.x1)  # Line segment end
    
    col_positions_lines = sorted(list(col_x_positions))
    
    col_positions_lines = cluster_coords(col_positions_lines)
    
    # Filter out spurious columns by removing positions that create very narrow columns
    # This fixes the issue where small line segments create extra columns
    table_width = t_right - t_left
    min_column_width = table_width * 0.028  # Minimum 2.8% of table width (filters 2.76% spurious column)
        
    # Check each adjacent pair of positions to see if they form a valid column
    col_positions_filtered = [col_positions_lines[0]]  # Always keep the first position (left edge)
    
    for i in range(1, len(col_positions_lines)):
        prev_pos = col_positions_filtered[-1]
        curr_pos = col_positions_lines[i]
        column_width = curr_pos - prev_pos
        
        # If this creates a very narrow column, skip this position
        if column_width < min_column_width:
            # Special case: if this is the last position (right edge), 
            # remove the previous position instead of skipping this one
            if i == len(col_positions_lines) - 1:
                col_positions_filtered.pop()  # Remove the previous position
                col_positions_filtered.append(curr_pos)  # Add this one (right edge)
            continue
        
        col_positions_filtered.append(curr_pos)
    
    col_positions_lines = col_positions_filtered
    
    # Use line-based columns if we found explicit dividers (more than just start/end)
    if len(col_positions_lines) > 2:
        col_positions = col_positions_lines
    else:
        # Fallback to text inference if lines don't define columns
        # This handles tables that have full-width rows but rely on whitespace for columns
        col_positions = infer_columns_from_text(texts_in_table, t_left, t_right)
    
    # Ensure we have at least 2 rows and 2 columns
    if len(row_positions) < 2 or len(col_positions) < 2:
        return None
    
    # Create cells
    cells = []
    for r_i in range(len(row_positions) - 1):
        y_start = row_positions[r_i]
        y_end = row_positions[r_i + 1]
        
        for c_i in range(len(col_positions) - 1):
            x_start = col_positions[c_i]
            x_end = col_positions[c_i + 1]
            
            # Find borders for this cell
            # Horizontal borders: look for lines at y_start and y_end
            b_top = find_line(h_lines, y_start, x_start, x_end, 'H')
            b_bottom = find_line(h_lines, y_end, x_start, x_end, 'H')
            
            # Vertical borders: none (no vertical lines)
            # But we can add subtle borders for visual clarity
            b_left = None
            b_right = None
            
            # Format borders - apply all detected horizontal lines
            style_top = format_border(b_top)
            style_bottom = format_border(b_bottom)
            
            # Add light vertical borders for column separation
            # Use a subtle gray border to show column boundaries
            # REMOVED: PDF doesn't have vertical lines, so we shouldn't add them if we want "exact match"
            style_left = None 
            style_right = None
            
            cells.append(TableCell(
                row_idx=r_i,
                col_idx=c_i,
                row_span=1,
                col_span=1,
                text_elements=[],
                style_top=style_top,
                style_bottom=style_bottom,
                style_left=style_left,
                style_right=style_right
            ))
    
    # Create table definition
    table = TableDefinition(
        rect=(t_top, t_left, t_bottom, t_right),
        row_positions=row_positions,
        col_positions=col_positions,
        cells=cells
    )
    
    
    return table

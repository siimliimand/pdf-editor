from typing import List
from ..models import TableCell
from ...vector_parser import VectorElement

def match_backgrounds(cells: List[TableCell], row_positions: List[int], col_positions: List[int], rects: List[VectorElement]):
    """
    Matches background rectangles to table cells.
    Modifies cells in-place to add background color.
    
    Improved algorithm that prioritizes Y-position alignment and filters out
    backgrounds that are primarily outside the table boundaries.
    """
    # Calculate table boundaries
    if not row_positions or not col_positions:
        return
    
    table_top = row_positions[0]
    table_bottom = row_positions[-1]
    table_left = col_positions[0]
    table_right = col_positions[-1]

    
    # Filter rects to only those that are primarily within table bounds
    # A rect is "primarily within" if its center is inside the table
    valid_rects = []
    for r in rects:
        rect_center_y = (r.y0 + r.y1) / 2
        rect_center_x = (r.x0 + r.x1) / 2
        
        # Check if center is within table bounds (with small tolerance)
        tolerance = 5  # pixels
        is_valid = (table_top - tolerance <= rect_center_y <= table_bottom + tolerance and
                   table_left - tolerance <= rect_center_x <= table_right + tolerance)
        
        if is_valid:
            valid_rects.append(r)
    
    for cell in cells:
        cell_x_start = col_positions[cell.col_idx]
        cell_x_end = col_positions[min(cell.col_idx + cell.col_span, len(col_positions)-1)]
        cell_y_start = row_positions[cell.row_idx]
        cell_y_end = row_positions[min(cell.row_idx + cell.row_span, len(row_positions)-1)]
        
        cell_area = (cell_x_end - cell_x_start) * (cell_y_end - cell_y_start)
        if cell_area <= 0: continue
        
        cell_height = cell_y_end - cell_y_start
        cell_y_center = (cell_y_start + cell_y_end) / 2
        
        # Find overlapping rect with best Y-alignment
        best_match = None
        best_score = 0.0
        
        for r in valid_rects:  # Use filtered rects
            # Intersect rect with cell
            ix0 = max(r.x0, cell_x_start)
            iy0 = max(r.y0, cell_y_start)
            ix1 = min(r.x1, cell_x_end)
            iy1 = min(r.y1, cell_y_end)
            
            if ix1 > ix0 and iy1 > iy0:
                overlap_area = (ix1 - ix0) * (iy1 - iy0)
                overlap_ratio = overlap_area / cell_area
                
                # Only consider rects with significant overlap (>50%)
                if overlap_ratio > 0.5:
                    # Calculate Y-alignment score
                    rect_height = r.y1 - r.y0
                    rect_y_center = (r.y0 + r.y1) / 2
                    
                    # Y-center distance (normalized by cell height)
                    y_distance = abs(cell_y_center - rect_y_center) / max(cell_height, 1)
                    
                    # Height similarity (how close are the heights)
                    height_ratio = min(cell_height, rect_height) / max(cell_height, rect_height, 1)
                    
                    # Combined score: prioritize Y-alignment and height similarity
                    # Higher overlap ratio, closer Y-centers, and similar heights = better match
                    y_alignment_score = 1.0 - min(y_distance, 1.0)  # 0-1, higher is better
                    score = (overlap_ratio * 0.4) + (y_alignment_score * 0.4) + (height_ratio * 0.2)
                    
                    if score > best_score:
                        best_score = score
                        best_match = r
        
        if best_match:
            cell.background_color = best_match.color

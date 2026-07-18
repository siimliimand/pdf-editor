from typing import List
from ..models import TableDefinition, Element, TextElement, ImageElement

def assign_elements_to_table(table: TableDefinition, elements: List[Element]) -> List[Element]:
    """
    Assigns text elements to the cells of the table using overlap-based matching.
    Returns the list of elements that were assigned to the table.
    """
    assigned_elements = []
    t_top, t_left, t_bottom, t_right = table.rect
    
    # Add margin for horizontal boundaries only
    h_margin = 10.0
    
    # For vertical boundaries, use stricter filtering for top
    # This prevents text above the table from being included
    top_margin = 0.0  # Strict: text must be at or below table top
    bottom_margin = 10.0  # Allow slight extension below table
    
    for el in elements:
        if isinstance(el, (TextElement, ImageElement)):
            # Strict top boundary check - element must start at or below table top
            # Allow margin for left/right/bottom
            if not (el.top < t_top - top_margin or  # Element is above table
                    el.top > t_bottom + bottom_margin or  # Element starts below table
                    el.left + el.width < t_left - h_margin or  # Element is left of table
                    el.left > t_right + h_margin):  # Element is right of table
                
                # Find best matching cell based on overlap area
                best_cell = None
                max_overlap = 0.0
                
                # Calculate element area for overlap percentage
                el_area = el.width * el.height
                
                for cell in table.cells:
                    try:
                        y_start = table.row_positions[cell.row_idx]
                        y_end = table.row_positions[cell.row_idx + 1]
                        x_start = table.col_positions[cell.col_idx]
                        x_end = table.col_positions[cell.col_idx + 1]
                        
                        # Calculate overlap area
                        overlap_left = max(el.left, x_start)
                        overlap_right = min(el.left + el.width, x_end)
                        overlap_top = max(el.top, y_start)
                        overlap_bottom = min(el.top + el.height, y_end)
                        
                        if overlap_right > overlap_left and overlap_bottom > overlap_top:
                            overlap_area = (overlap_right - overlap_left) * (overlap_bottom - overlap_top)
                            
                            if overlap_area > max_overlap:
                                max_overlap = overlap_area
                                best_cell = cell
                    
                    except IndexError:
                        pass
                
                # Assign to best matching cell if overlap is significant
                # Use a lower threshold (20%) to allow text that spans multiple columns
                # Priority is given to cells with the highest overlap
                if best_cell is not None and max_overlap > 0:
                    overlap_percentage = max_overlap / el_area if el_area > 0 else 0
                    if overlap_percentage >= 0.20:  # At least 20% overlap required
                        best_cell.text_elements.append(el)
                        assigned_elements.append(el)
    
    return assigned_elements

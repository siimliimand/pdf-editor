from typing import List
from ...models import TextElement

def group_text_by_row(text_elements: List[TextElement], tolerance: float = 5.0) -> List[List[TextElement]]:
    """
    Group text elements into rows based on Y-position.
    
    Args:
        text_elements: Text elements to group
        tolerance: Maximum Y-distance to consider elements in the same row
        
    Returns:
        List of rows, where each row is a list of text elements
    """
    if not text_elements:
        return []
    
    # Sort by Y position
    sorted_elements = sorted(text_elements, key=lambda el: el.top)
    
    rows = []
    current_row = [sorted_elements[0]]
    
    for el in sorted_elements[1:]:
        # Check if element is in the same row as the last element
        if abs(el.top - current_row[-1].top) <= tolerance:
            current_row.append(el)
        else:
            # New row
            rows.append(current_row)
            current_row = [el]
    
    if current_row:
        rows.append(current_row)
    
    return rows

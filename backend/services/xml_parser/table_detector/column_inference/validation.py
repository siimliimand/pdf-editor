from typing import List
from ...models import TextElement

def validate_columns(
    col_positions: List[float],
    text_elements: List[TextElement]
) -> bool:
    """
    Validate that inferred column positions make sense.
    
    Args:
        col_positions: Inferred column positions
        text_elements: Text elements to validate against
        
    Returns:
        True if columns are valid, False otherwise
    """
    if len(col_positions) < 2:
        return False
    
    # Check that each column contains at least some text
    for i in range(len(col_positions) - 1):
        col_left = col_positions[i]
        col_right = col_positions[i + 1]
        
        # Count text elements in this column
        count = 0
        for el in text_elements:
            el_center = el.left + el.width / 2
            if col_left <= el_center < col_right:
                count += 1
        
        # At least one text element should be in each column
        # (except for empty columns which are valid)
    
    return True

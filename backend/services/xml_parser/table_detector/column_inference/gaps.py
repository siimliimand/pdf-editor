from typing import List
from ...models import TextElement

def find_gaps_in_row(row_elements: List[TextElement], min_gap: float = 15.0) -> List[float]:
    """
    Find significant horizontal gaps between text elements in a row.
    
    Args:
        row_elements: Text elements in a single row
        min_gap: Minimum gap size to consider as a column boundary (default 15px - reduced for better narrow column detection)
        
    Returns:
        List of X-positions where gaps occur (potential column boundaries)
    """
    if len(row_elements) < 2:
        return []
    
    # Sort by X position
    sorted_elements = sorted(row_elements, key=lambda el: el.left)
    
    # Calculate adaptive min_gap based on text element widths
    # Use median width as a baseline - gaps should be significantly larger than typical text
    widths = [el.width for el in sorted_elements]
    if widths:
        median_width = sorted(widths)[len(widths) // 2]
        # Gap should be at least 70% of median text width, but at least 15px (reduced from 20px)
        # This balances between detecting real columns and avoiding false boundaries
        adaptive_min_gap = max(min_gap, median_width * 0.7)
    else:
        adaptive_min_gap = min_gap
    
    gaps = []
    for i in range(len(sorted_elements) - 1):
        current_el = sorted_elements[i]
        next_el = sorted_elements[i + 1]
        
        # Calculate gap between right edge of current and left edge of next
        gap_start = current_el.left + current_el.width
        gap_end = next_el.left
        gap_size = gap_end - gap_start
        
        # If gap is significant, record the midpoint as a potential column boundary
        if gap_size >= adaptive_min_gap:
            boundary = (gap_start + gap_end) / 2
            gaps.append(boundary)
    
    return gaps

from typing import List, Dict, Tuple, Set
from ..models import TableRow, Element, TextElement
import statistics


ROW_TOLERANCE = 2

def group_into_rows(elements: List[Element], scale: float = 1.0) -> List[TableRow]:
    """
    Group elements into rows based on their vertical position.
    
    Args:
        elements: List of elements to group
        scale: Scale factor for zoom (adjusts tolerance for higher zoom levels)
    
    Returns:
        List of TableRow objects
    """
    sorted_elements = sorted(elements, key=lambda x: x.top)
    rows: List[TableRow] = []
    if not sorted_elements:
        return rows

    # Scale the tolerance for higher zoom levels
    # At 175% zoom (scale=1.75), tolerance becomes 3.5px instead of 2px
    scaled_tolerance = ROW_TOLERANCE * scale
    
    current_row_elements = [sorted_elements[0]]
    current_row_top = sorted_elements[0].top
    
    for el in sorted_elements[1:]:
        if abs(el.top - current_row_top) <= scaled_tolerance:
            current_row_elements.append(el)
        else:
            row_height = max((e.height for e in current_row_elements), default=12)
            rows.append(TableRow(top=current_row_top, height=row_height, elements=current_row_elements))
            
            current_row_elements = [el]
            current_row_top = el.top
    
    if current_row_elements:
            row_height = max((e.height for e in current_row_elements), default=12)
            rows.append(TableRow(top=current_row_top, height=row_height, elements=current_row_elements))
            
    # Calculate line heights
    _calculate_line_heights(rows)
    return rows

def _calculate_line_heights(rows: List[TableRow]):
    """
    Detects line height based on spacing between consecutive rows.
    Updates row.approx_line_height in-place.
    """
    if not rows:
        return

    # default fallback
    DEFAULT_LH = 1.1 
    
    for i in range(len(rows)):
        current_row = rows[i]
        
        # Get dominant font size for current row
        text_els = [e for e in current_row.elements if isinstance(e, TextElement)]
        if not text_els:
            continue
            
        avg_font_size = sum(e.font_size for e in text_els) / len(text_els)
        if avg_font_size == 0: continue
        
        # Try to match with next row
        next_row = rows[i+1] if i < len(rows) - 1 else None
        
        spacing_ratio = None
        
        if next_row:
            # Check if next row is part of same block (physically close)
            vertical_dist = next_row.top - current_row.top
            
            # Heuristic: if distance is between 0.8 and 2.5 times font size, assume it's a line break
            if 0.8 * avg_font_size < vertical_dist < 2.5 * avg_font_size:
                # Also check horizontal overlap to ensure it's not a different column
                curr_left = min(e.left for e in current_row.elements)
                curr_right = max(e.left + e.width for e in current_row.elements)
                next_left = min(e.left for e in next_row.elements)
                next_right = max(e.left + e.width for e in next_row.elements)
                
                overlap = max(0, min(curr_right, next_right) - max(curr_left, next_left))
                if overlap > 0:
                     spacing_ratio = vertical_dist / avg_font_size

        # If we found a ratio from the next line, use it.
        # If not (last line or isolated), try to use the PREVIOUS line's ratio if available
        # (Assuming paragraph consistency)
        if spacing_ratio:
            current_row.approx_line_height = round(spacing_ratio, 2)
        elif i > 0 and abs(rows[i-1].approx_line_height - 1.0) > 0.01: 
             # Use previous row's LH if it was calculated (and not default 1.0)
             # But wait, we initialized default to 1.0 in model.
             # We should check if previous row was "connected" to this one.
             prev_row = rows[i-1]
             vertical_dist = current_row.top - prev_row.top
             prev_text_els = [e for e in prev_row.elements if isinstance(e, TextElement)]
             if prev_text_els:
                 prev_size = sum(e.font_size for e in prev_text_els) / len(prev_text_els)
                 if 0.8 * prev_size < vertical_dist < 2.5 * prev_size:
                      current_row.approx_line_height = prev_row.approx_line_height
             else:
                  current_row.approx_line_height = DEFAULT_LH
        else:
             current_row.approx_line_height = DEFAULT_LH


def segment_rows(rows: List[TableRow]) -> List[Tuple[str, List[TableRow]]]:
    blocks = []
    if not rows:
        return blocks
        
    current_type = 'TABLE' if rows[0].is_multi_column else 'TEXT'
    current_rows = [rows[0]]
    
    for row in rows[1:]:
        row_type = 'TABLE' if row.is_multi_column else 'TEXT'
        
        if row_type == current_type:
            current_rows.append(row)
        else:
            blocks.append((current_type, current_rows))
            current_type = row_type
            current_rows = [row]
    
    if current_rows:
        blocks.append((current_type, current_rows))
        
    return blocks

def detect_row_spacing(rows: List[TableRow]) -> Dict[int, float]:
    spacing = {}
    if len(rows) < 2:
        return spacing
    
    for i in range(1, len(rows)):
        gap = rows[i].top - (rows[i-1].top + rows[i-1].height)
        spacing[i] = gap
    
    return spacing

def detect_header_rows(rows: List[TableRow]) -> Set[int]:
    headers = set()
    if not rows:
        return headers
    
    all_font_sizes = []
    for row in rows:
        for el in row.elements:
            if isinstance(el, TextElement):
                all_font_sizes.append(el.font_size)
    
    avg_font_size = sum(all_font_sizes) / len(all_font_sizes) if all_font_sizes else 12
    
    for i, row in enumerate(rows):
        text_els = [e for e in row.elements if isinstance(e, TextElement)]
        if not text_els:
            continue
        
        bold_count = sum(1 for e in text_els if e.font_spec and e.font_spec.is_bold)
        all_bold = bold_count == len(text_els) if text_els else False
        
        row_avg_size = sum(e.font_size for e in text_els) / len(text_els)
        is_larger = row_avg_size > avg_font_size * 1.1
        
        if all_bold or is_larger:
            headers.add(i)
    
    return headers

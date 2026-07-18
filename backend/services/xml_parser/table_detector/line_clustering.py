from typing import List
from ...vector_parser import VectorElement

def is_valid_table_group(group: List[VectorElement]) -> bool:
    """
    Validate if a group of horizontal lines forms a valid table.
    A valid table should have at least 2 lines (top and bottom).
    """
    return len(group) >= 2

def has_vertical_continuity(current_group: List[VectorElement], new_line: VectorElement, vertical_lines: List[VectorElement]) -> bool:
    """
    Check if vertical lines continue between current group and new line.
    This helps determine if they belong to the same table.
    """
    if not current_group:
        return False
    
    # Get Y-range of current group
    group_top = min(l.y0 for l in current_group)
    group_bottom = max(l.y0 for l in current_group)
    
    # Get X-range of current group and new line
    group_left = min(l.x0 for l in current_group)
    group_right = max(l.x1 for l in current_group)
    line_left = new_line.x0
    line_right = new_line.x1
    
    # Check if there are vertical lines that span from group to new line
    for v in vertical_lines:
        # Check if vertical line is within X-range
        if (group_left - 5 < v.x0 < group_right + 5) or (line_left - 5 < v.x0 < line_right + 5):
            # Check if it spans from group to new line
            if v.y0 <= group_bottom + 5 and v.y1 >= new_line.y0 - 5:
                return True
    
    return False

def cluster_horizontal_lines(horizontal_lines: List[VectorElement], vertical_lines: List[VectorElement]) -> List[List[VectorElement]]:
    """
    Cluster horizontal lines into groups based on vertical proximity and continuity.
    """
    if not horizontal_lines: return []
    
    sorted_h = sorted(horizontal_lines, key=lambda v: v.y0)
    current_group = []
    groups = []
    
    for line in sorted_h:
        if not current_group:
            current_group.append(line)
            continue
        
        last_line = current_group[-1]
        gap = line.y0 - last_line.y0
        
        # Improved table separation logic
        # Gap > 60px likely indicates a new table (increased from 30px to prevent fragmentation)
        # Gap < 80px keeps lines in same table (increased for tables with larger row spacing)
        if gap > 60:
            # Large gap - likely a new table
            # Validate current group before finalizing
            if is_valid_table_group(current_group):
                groups.append(current_group)
            current_group = [line]
        elif gap < 80:  # Increased from 50px to match larger table spacing
            # Small gap - same table
            current_group.append(line)
        else:
            # Medium gap (30-50px) - check vertical line continuity
            # If vertical lines continue, it's same table; otherwise new table
            has_continuity = has_vertical_continuity(current_group, line, vertical_lines)
            if has_continuity:
                current_group.append(line)
            else:
                if is_valid_table_group(current_group):
                    groups.append(current_group)
                current_group = [line]
    
    if current_group and is_valid_table_group(current_group):
        groups.append(current_group)
        
    return groups

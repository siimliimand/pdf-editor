from typing import List
from ....vector_parser import VectorElement


def cluster_horizontal_lines(
    h_lines: List[VectorElement],
    max_gap: float = 30.0
) -> List[List[VectorElement]]:
    """
    Cluster horizontal lines into potential table regions.
    
    Args:
        h_lines: All horizontal lines on the page
        max_gap: Maximum vertical gap between lines to consider them part of the same table
        
    Returns:
        List of line groups, where each group represents a potential table
    """
    if not h_lines:
        return []
    
    # Sort lines by Y position
    sorted_lines = sorted(h_lines, key=lambda l: l.y0)
    
    groups = []
    current_group = [sorted_lines[0]]
    
    for i in range(1, len(sorted_lines)):
        line = sorted_lines[i]
        last_line = current_group[-1]
        gap = line.y0 - last_line.y0
        
        if gap <= max_gap:
            # Same table
            current_group.append(line)
        else:
            # New table
            if len(current_group) >= 2:  # Need at least 2 lines for a table
                groups.append(current_group)
            current_group = [line]
    
    # Don't forget the last group
    if len(current_group) >= 2:
        groups.append(current_group)
    
    return groups

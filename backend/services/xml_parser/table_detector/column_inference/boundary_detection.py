from typing import List
from ...models import TextElement
from .clustering import cluster_x_positions

def detect_column_boundaries(
    text_elements: List[TextElement],
    table_left: float,
    table_right: float,
    min_gap: float = 10.0
) -> List[float]:
    """
    Detect column boundaries from text element positions.
    
    Args:
        text_elements: Text elements within the table region
        table_left: Left boundary of the table
        table_right: Right boundary of the table
        min_gap: Minimum gap between columns to consider them separate
        
    Returns:
        Sorted list of column positions (X coordinates)
    """
    if not text_elements:
        return [table_left, table_right]
    
    # Cluster X positions
    clusters = cluster_x_positions(text_elements, tolerance=5.0)
    
    # Calculate average position for each cluster
    cluster_positions = []
    for cluster in clusters:
        avg_pos = sum(pos for _, pos in cluster) / len(cluster)
        cluster_positions.append(avg_pos)
    
    # Sort positions
    cluster_positions.sort()
    
    # Identify column boundaries by finding gaps
    col_positions = [table_left]
    
    for i in range(len(cluster_positions) - 1):
        current = cluster_positions[i]
        next_pos = cluster_positions[i + 1]
        gap = next_pos - current
        
        # If there's a significant gap, it's likely a column boundary
        if gap >= min_gap:
            # Add boundary at the midpoint of the gap
            boundary = (current + next_pos) / 2
            if boundary not in col_positions:
                col_positions.append(boundary)
    
    # Ensure table boundaries are included
    if table_right not in col_positions:
        col_positions.append(table_right)
    
    col_positions.sort()
    return col_positions

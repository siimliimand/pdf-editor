from typing import List
from ...models import TextElement
from .gaps import find_gaps_in_row

def aggregate_column_boundaries(
    rows: List[List[TextElement]], 
    table_left: float, 
    table_right: float,
    tolerance: float = 5.0
) -> List[float]:
    """
    Aggregate column boundaries from all rows and cluster them.
    Focus on boundaries that appear consistently across multiple rows.
    
    Args:
        rows: List of rows, where each row is a list of text elements
        table_left: Left boundary of the table
        table_right: Right boundary of the table
        tolerance: Clustering tolerance for boundary positions
        
    Returns:
        Sorted list of column boundary positions
    """
    if not rows:
        return [table_left, table_right]
    
    # Collect boundaries from each row separately
    row_gap_boundaries = []
    row_left_edges = []
    
    for row in rows:
        # Get gaps (more reliable for column detection)
        gaps = find_gaps_in_row(row, min_gap=20.0)
        row_gap_boundaries.append(gaps)
        
        # Also collect left edges
        left_edges = [el.left for el in row]
        row_left_edges.append(left_edges)
    
    # Prioritize gap-based boundaries
    # Only use left edges if we don't have enough gap boundaries
    all_gap_boundaries = []
    for gaps in row_gap_boundaries:
        all_gap_boundaries.extend(gaps)
    
    all_left_edges = []
    for edges in row_left_edges:
        all_left_edges.extend(edges)
    
    # If we have gap boundaries, prioritize them
    # Otherwise fall back to left edges
    if all_gap_boundaries:
        primary_boundaries = all_gap_boundaries
        secondary_boundaries = all_left_edges
    else:
        primary_boundaries = all_left_edges
        secondary_boundaries = []
    
    if not primary_boundaries:
        return [table_left, table_right]
    
    # Cluster primary boundaries
    primary_boundaries.sort()
    clusters = []
    current_cluster = [primary_boundaries[0]]
    
    for boundary in primary_boundaries[1:]:
        if abs(boundary - current_cluster[-1]) <= tolerance:
            current_cluster.append(boundary)
        else:
            clusters.append(current_cluster)
            current_cluster = [boundary]
    
    if current_cluster:
        clusters.append(current_cluster)
    
    # Filter clusters based on consistency across rows
    # A cluster is valid if it appears in at least 15% of rows, or 1 row if we have very few rows
    # RELAXED: Lowered threshold to ensure we keep boundaries from detailed unique rows
    min_row_appearances = max(1, int(len(rows) * 0.15))
    
    consistent_boundaries = []
    for cluster in clusters:
        avg_pos = sum(cluster) / len(cluster)
        
        # Count how many rows have a gap boundary near this position
        row_count = 0
        for gaps in row_gap_boundaries:
            if any(abs(g - avg_pos) <= tolerance for g in gaps):
                row_count += 1
        
        # Keep if it appears in enough rows
        if row_count >= min_row_appearances:
            consistent_boundaries.append(avg_pos)
    
    # If we didn't find enough boundaries from gaps, try left edges
    # But still require consistency
    if len(consistent_boundaries) < 2 and secondary_boundaries:
        secondary_boundaries.sort()
        sec_clusters = []
        current_cluster = [secondary_boundaries[0]]
        
        for boundary in secondary_boundaries[1:]:
            if abs(boundary - current_cluster[-1]) <= tolerance:
                current_cluster.append(boundary)
            else:
                sec_clusters.append(current_cluster)
                current_cluster = [boundary]
        
        if current_cluster:
            sec_clusters.append(current_cluster)
        
        for cluster in sec_clusters:
            avg_pos = sum(cluster) / len(cluster)
            
            # Count across all rows
            row_count = 0
            for edges in row_left_edges:
                if any(abs(e - avg_pos) <= tolerance for e in edges):
                    row_count += 1
            
            if row_count >= min_row_appearances:
                if avg_pos not in consistent_boundaries:
                    consistent_boundaries.append(avg_pos)
    
    # Build final column positions
    col_positions = [table_left]
    
    # Add consistent boundaries that are within table bounds
    consistent_boundaries.sort()
    for pos in consistent_boundaries:
        if table_left + 10 < pos < table_right - 10:
            col_positions.append(pos)
    
    # Add table right boundary
    if table_right not in col_positions:
        col_positions.append(table_right)
    
    col_positions.sort()
    
    # Remove duplicate positions
    col_positions = list(dict.fromkeys(col_positions))
    
    return col_positions

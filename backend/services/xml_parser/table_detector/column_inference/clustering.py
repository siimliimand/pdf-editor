from typing import List, Tuple
from ...models import TextElement

def cluster_x_positions(text_elements: List[TextElement], tolerance: float = 5.0) -> List[List[float]]:
    """
    Cluster X positions (left edges) of text elements.
    
    Args:
        text_elements: List of text elements to analyze
        tolerance: Maximum distance between positions to consider them the same cluster
        
    Returns:
        List of clusters, where each cluster is a list of X positions
    """
    if not text_elements:
        return []
    
    # Collect all left and right edges
    positions = []
    for el in text_elements:
        positions.append(('left', el.left))
        positions.append(('right', el.left + el.width))
    
    # Sort by position
    positions.sort(key=lambda x: x[1])
    
    # Cluster positions
    clusters = []
    current_cluster = [positions[0]]
    
    for i in range(1, len(positions)):
        edge_type, pos = positions[i]
        _, last_pos = current_cluster[-1]
        
        if abs(pos - last_pos) <= tolerance:
            # Same cluster
            current_cluster.append(positions[i])
        else:
            # New cluster
            clusters.append(current_cluster)
            current_cluster = [positions[i]]
    
    if current_cluster:
        clusters.append(current_cluster)
    
    return clusters

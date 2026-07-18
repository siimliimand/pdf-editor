from typing import List

def cluster_coords(coords: List[float], tolerance=1.0) -> List[float]:
    """
    Cluster coordinates that are close together.
    Reduced tolerance from 4px to 1px for better precision.
    Now preserves float precision instead of converting to int.
    """
    if not coords: return []
    coords.sort()
    clusters = []
    current = [coords[0]]
    for x in coords[1:]:
        if x - current[-1] <= tolerance:
            current.append(x)
        else:
            # Keep as float for sub-pixel precision
            clusters.append(sum(current)/len(current))
            current = [x]
    clusters.append(sum(current)/len(current))
    return clusters

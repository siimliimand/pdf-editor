from typing import List, Optional
from ...vector_parser import VectorElement

def find_line(lines: List[VectorElement], pos: float, range_start: float, range_end: float, orientation: str) -> Optional[VectorElement]:
    """
    Find a line at a specific position.
    Reduced tolerance from 5px to 3px for better border detection accuracy.
    """
    # pos is Y for H lines, X for V lines
    # range is X for H lines, Y for V lines
    tolerance = 3  # Reduced from 5px for better matching accuracy
    matches = []
    
    for l in lines:
        if orientation == 'H':
            # Check Y matches pos
            if abs(l.y0 - pos) < tolerance:
                # Check overlap in X
                overlap = min(l.x1, range_end) - max(l.x0, range_start)
                if overlap > (range_end - range_start) * 0.5: # 50% coverage
                    matches.append(l)
        else:
            if abs(l.x0 - pos) < tolerance:
                overlap = min(l.y1, range_end) - max(l.y0, range_start)
                if overlap > (range_end - range_start) * 0.5:
                        matches.append(l)
    
    # Prioritize thicker lines if multiple matches
    if matches:
        return max(matches, key=lambda line: line.linewidth)
    return None

def format_border(vector: Optional[VectorElement]) -> str:
    if not vector: return ""
    width = max(1, int(vector.linewidth))
    color = vector.color if vector.color != "#000000" else "#888888"  # Use softer grey for black lines
    return f"{width}px solid {color}"

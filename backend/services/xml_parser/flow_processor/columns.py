from typing import List, Tuple, Dict
from ..models import TableRow, TextElement

def detect_global_columns(rows: List[TableRow]) -> List[int]:
    """
    Detect column positions by clustering text element positions.
    Handles both left-aligned (cluster by left edge) and right-aligned (cluster by right edge) text.
    """
    all_lefts = []
    all_rights = []
    
    for row in rows:
        for el in row.elements:
            if isinstance(el, TextElement):
                all_lefts.append(el.left)
                all_rights.append(el.left + el.width)
    
    if not all_lefts:
        return []
    
    # Cluster left edges (for left-aligned text)
    all_lefts.sort()
    left_clusters = []
    current_cluster = [all_lefts[0]]
    
    for x in all_lefts[1:]:
        if x - current_cluster[-1] <= 2: 
            current_cluster.append(x)
        else:
            avg = sum(current_cluster) / len(current_cluster)
            left_clusters.append(int(avg))
            current_cluster = [x]
    
    if current_cluster:
        avg = sum(current_cluster) / len(current_cluster)
        left_clusters.append(int(avg))
    
    # Cluster right edges (for right-aligned text)
    all_rights.sort()
    right_clusters = []
    current_cluster = [all_rights[0]]
    
    for x in all_rights[1:]:
        if x - current_cluster[-1] <= 2:
            current_cluster.append(x)
        else:
            avg = sum(current_cluster) / len(current_cluster)
            right_clusters.append(int(avg))
            current_cluster = [x]
    
    if current_cluster:
        avg = sum(current_cluster) / len(current_cluster)
        right_clusters.append(int(avg))
    
    # Merge left and right clusters
    # If multiple right edges cluster together, they likely represent a right-aligned column
    # We need to remove the individual left positions and replace with the leftmost one
    all_positions = set(left_clusters)
    right_aligned_left_positions = set()  # Track which left positions are part of right-aligned columns
    
    # For each right cluster, check if multiple text elements align to it
    for right_pos in right_clusters:
        # Find all text elements that end near this position
        aligned_elements = []
        for row in rows:
            for el in row.elements:
                if isinstance(el, TextElement):
                    if abs((el.left + el.width) - right_pos) <= 2:
                        aligned_elements.append(el)
        
        # If multiple elements align to this right edge, it's a right-aligned column
        if len(aligned_elements) >= 2:
            # Track all the left positions of these elements
            for el in aligned_elements:
                right_aligned_left_positions.add(int(el.left))
            
            # Use the leftmost start position of these elements as the column start
            min_left = min(el.left for el in aligned_elements)
            all_positions.add(int(min_left))
    
    # Remove individual left positions that are part of right-aligned columns
    # Keep only the leftmost position for each right-aligned column
    for left_pos in list(all_positions):
        if left_pos in right_aligned_left_positions:
            # Check if this is NOT the leftmost position for any right-aligned column
            is_leftmost = False
            for right_pos in right_clusters:
                aligned_elements = []
                for row in rows:
                    for el in row.elements:
                        if isinstance(el, TextElement):
                            if abs((el.left + el.width) - right_pos) <= 2:
                                aligned_elements.append(el)
                
                if len(aligned_elements) >= 2:
                    min_left = min(el.left for el in aligned_elements)
                    if abs(left_pos - min_left) < 1:
                        is_leftmost = True
                        break
            
            # If not the leftmost, remove it
            if not is_leftmost:
                all_positions.discard(left_pos)
    
    # Sort unique column positions
    sorted_positions = sorted(list(all_positions))
    
    if not sorted_positions:
        return []
        
    # Post-process to merge indented columns
    # If columns are close (< 50px) and no row has content in BOTH, they are likely the same column with indentation
    merged_columns = [sorted_positions[0]]
    
    for next_pos in sorted_positions[1:]:
        curr_pos = merged_columns[-1]
        diff = next_pos - curr_pos
        
        should_merge = False
        if diff < 50:
            # Check for overlap in rows
            # Two columns effectively overlap if a row has content starting at BOTH positions
            has_overlap = False
            for row in rows:
                has_curr = False
                has_next = False
                for el in row.elements:
                    if isinstance(el, TextElement):
                        # Use a small tolerance for exact alignment
                        if abs(el.left - curr_pos) <= 5:
                            has_curr = True
                        if abs(el.left - next_pos) <= 5:
                            has_next = True
                
                if has_curr and has_next:
                    has_overlap = True
                    break
            
            # If they don't overlap in any row, they are likely the same column (indented)
            if not has_overlap:
                should_merge = True
        
        if not should_merge:
            merged_columns.append(next_pos)
            
    return merged_columns

def detect_cell_padding(row: TableRow, col_definitions: List[int], max_right: int) -> Tuple[int, int]:
    text_elements = [e for e in row.elements if isinstance(e, TextElement)]
    if not text_elements:
        return (0, 0)
    
    h_paddings = []
    for el in text_elements:
        for i, col_left in enumerate(col_definitions):
            next_col_left = col_definitions[i+1] if i + 1 < len(col_definitions) else max_right
            if col_left - 5 <= el.left < next_col_left:
                left_padding = el.left - col_left
                if left_padding > 0:
                    h_paddings.append(left_padding)
                break
    
    h_pad = int(sum(h_paddings) / len(h_paddings)) if h_paddings else 0
    h_pad = min(h_pad, 10)
    
    avg_font_size = sum(e.font_size for e in text_elements) / len(text_elements)
    v_pad = max(2, int(avg_font_size * 0.15))
    
    return (h_pad, v_pad)

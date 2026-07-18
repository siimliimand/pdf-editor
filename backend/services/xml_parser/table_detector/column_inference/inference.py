from typing import List
from ...models import TextElement
from .rows import group_text_by_row
from .aggregation import aggregate_column_boundaries

def infer_columns_from_text(
    text_elements: List[TextElement],
    table_left: float,
    table_right: float
) -> List[float]:
    """
    Infer column positions from text element alignment.
    
    This is the main entry point for column inference.
    Uses an improved strategy: analyze horizontal gaps between text elements
    row-by-row, focusing on the most common row structure (data rows).
    
    Args:
        text_elements: Text elements within the table region
        table_left: Left boundary of the table
        table_right: Right boundary of the table
        
    Returns:
        Sorted list of column positions
    """
    if not text_elements:
        return [table_left, table_right]
    
    
    # Group text elements into rows
    rows = group_text_by_row(text_elements, tolerance=5.0)
    
    if not rows:
        return [table_left, table_right]
    
    for i, row in enumerate(rows):
        row_text = " | ".join([f"'{el.text}'" for el in row])
    
    # SPECIAL CASE: Detect classic 2-column table pattern
    # This pattern has:
    # - Most rows have exactly 2 elements (data rows)
    # - May have header rows with 1 element (spanning header)
    # - First element is left-aligned (small left margin)
    # - Second element is right-aligned (small right margin)
    table_width = table_right - table_left
    rows_with_2_elements = [row for row in rows if len(row) == 2]
    rows_with_1_element = [row for row in rows if len(row) == 1]
    
    print(f"[COLUMN INFERENCE] Total rows: {len(rows)}, 2-elem rows: {len(rows_with_2_elements)}, 1-elem rows: {len(rows_with_1_element)}")
    
    # IMPROVED: Lower threshold to 20% and account for single-element header rows
    # A table is likely 2-column if:
    # - At least 20% of rows have 2 elements (was 30%)
    # - OR at least 2 rows have 2 elements AND there are 1-element rows (likely headers)
    is_likely_2_column = (
        len(rows_with_2_elements) >= max(2, len(rows) * 0.2) or
        (len(rows_with_2_elements) >= 2 and len(rows_with_1_element) >= 1)
    )
    
    print(f"[COLUMN INFERENCE] is_likely_2_column: {is_likely_2_column}")
    
    if is_likely_2_column:
        # Check if this is a left-aligned + right-aligned pattern
        left_aligned_count = 0
        right_aligned_count = 0
        
        for row in rows_with_2_elements:
            sorted_row = sorted(row, key=lambda el: el.left)
            left_el, right_el = sorted_row[0], sorted_row[1]
            
            # Check if left element is left-aligned (margin < 15% of table width)
            left_margin = left_el.left - table_left
            
            # Check if right element is right-aligned (right edge within 15% of table right)
            right_edge = right_el.left + right_el.width
            right_margin = table_right - right_edge
            
            if left_margin < table_width * 0.15:  # Left element is left-aligned
                left_aligned_count += 1
            if right_margin < table_width * 0.15:  # Right element is right-aligned
                right_aligned_count += 1
        
        print(f"[COLUMN INFERENCE] left_aligned: {left_aligned_count}/{len(rows_with_2_elements)}, right_aligned: {right_aligned_count}/{len(rows_with_2_elements)}")
        
        # If majority of 2-element rows have left+right alignment pattern,
        # this is a simple 2-column table - just create one column boundary
        if left_aligned_count >= len(rows_with_2_elements) * 0.5 and \
           right_aligned_count >= len(rows_with_2_elements) * 0.5:
            # Find the column boundary - gap between left and right elements
            # Use the average gap midpoint
            gap_midpoints = []
            for row in rows_with_2_elements:
                sorted_row = sorted(row, key=lambda el: el.left)
                left_el, right_el = sorted_row[0], sorted_row[1]
                gap_start = left_el.left + left_el.width
                gap_end = right_el.left
                gap_midpoints.append((gap_start + gap_end) / 2)
            
            avg_midpoint = sum(gap_midpoints) / len(gap_midpoints)
            
            print(f"[COLUMN INFERENCE] ✓ Detected 2-column table, boundary at {avg_midpoint}")
            return [table_left, avg_midpoint, table_right]
        else:
            print(f"[COLUMN INFERENCE] ✗ Alignment check failed, falling through to multi-column detection")
    
    # Find the most common row structure (number of elements per row)
    # This helps us focus on data rows and ignore header/footer rows
    row_sizes = {}
    for row in rows:
        size = len(row)
        row_sizes[size] = row_sizes.get(size, 0) + 1
    
    # Get the most common row size
    if row_sizes:
        # Sort sizes by frequency (descending)
        sorted_sizes = sorted(row_sizes.items(), key=lambda x: x[1], reverse=True)
        
        # IMPROVED LOGIC: Prioritize the row size with the MOST columns, 
        # provided it appears with sufficient frequency (e.g. at least 20-30% of max freq or >= 2 rows)
        # This prevents 2-column sub-headers from hiding the 5-column data rows.
        
        # Find max frequency to use as baseline
        max_freq = sorted_sizes[0][1]
        
        target_size = None
        
        # Sort by size (descending) to check largest tables first
        sizes_desc = sorted(row_sizes.keys(), reverse=True)
        
        for size in sizes_desc:
            if size <= 1:
                continue
                
            freq = row_sizes[size]
            
            # If this large row size appears enough times, valid candidate
            # Criteria: At least 2 occurrences OR (if only 1) it's a significant portion of rows
            # RELAXED: Allow even 1 occurrence if it's the largest size and > 2 columns
            # This ensures we catch the "header" or "data" row even if it's unique
            is_frequent_enough = freq >= 2 or (freq >= 1 and freq >= len(rows) * 0.1) or (freq >= 1 and size >= 3)
            
            if is_frequent_enough:
                target_size = size
                break
        
        # Fallback to most common size if no complex row found
        if not target_size:
            for size, count in sorted_sizes:
                if size > 1:
                    target_size = size
                    break
        
        if target_size:
            # Include all rows that have close to this number of columns (or more)
            # This handles cases where a column might be empty/merged in some rows
            # RELAXED: Allow target_size - 2 to catch rows with multiple empty cells
            limit = max(2, target_size - 2)
            data_rows = [row for row in rows if len(row) >= limit]
        else:
            most_common_size = sorted_sizes[0][0]
            data_rows = [row for row in rows if len(row) == most_common_size]
    else:
        data_rows = rows
    
    # Aggregate column boundaries from data rows
    col_positions = aggregate_column_boundaries(data_rows, table_left, table_right, tolerance=5.0)
    
    # Validate: ensure we have at least 2 positions (1 column)
    if len(col_positions) < 2:
        col_positions = [table_left, table_right]
    
    
    return col_positions

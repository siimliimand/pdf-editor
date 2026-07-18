from typing import List, Tuple


def merge_legacy_tables(text_blocks: List[tuple], scale: float = 1.0) -> List[tuple]:
    """
    Merge legacy tables (text-flow based) that should be combined.
    
    Args:
        text_blocks: List of (type, data) tuples where type is 'TEXT' or 'TABLE'
        scale: Scale factor for zoom (adjusts gap threshold for higher zoom levels)
        
    Returns:
        List of merged blocks
    """
    if not text_blocks:
        return []
    
    merged_blocks = []
    i = 0
    merge_count = 0
    
    # Scale the gap threshold for higher zoom levels
    # At 175% zoom (scale=1.75), threshold becomes 52.5px instead of 30px
    gap_threshold = 30 * scale
    
    while i < len(text_blocks):
        block_type, block_data = text_blocks[i]
        
        if block_type != 'TABLE':
            # Not a table, just add it
            merged_blocks.append((block_type, block_data))
            i += 1
            continue
        
        # This is a table, check if we should merge with next tables
        current_rows = list(block_data)  # Make a copy
        i += 1
        merged_this_table = 0
        
        # Look ahead for adjacent tables
        while i < len(text_blocks):
            next_type, next_data = text_blocks[i]
            
            if next_type != 'TABLE':
                break
            
            # Check if tables are adjacent
            if current_rows and next_data:
                last_row = current_rows[-1]
                first_next_row = next_data[0]
                
                # Calculate vertical gap
                gap = first_next_row.top - (last_row.top + last_row.height)
                
                
                # If gap is small, merge (using scale-aware threshold)
                if gap < gap_threshold:
                    current_rows.extend(next_data)
                    i += 1
                    merged_this_table += 1
                    merge_count += 1
                else:
                    break
            else:
                break
        
        
        # Add merged table
        merged_blocks.append(('TABLE', current_rows))
    
    
    return merged_blocks

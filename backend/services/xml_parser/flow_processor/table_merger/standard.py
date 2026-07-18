from typing import List
from ...models import TableDefinition
from .core import should_merge_tables, merge_tables


def merge_adjacent_tables(tables: List[TableDefinition]) -> List[TableDefinition]:
    """
    Merge tables that are vertically adjacent and have compatible structures.
    
    Args:
        tables: List of table definitions
        
    Returns:
        List of merged table definitions
    """
    if not tables:
        return []
    
    # Sort tables by vertical position (top to bottom)
    sorted_tables = sorted(tables, key=lambda t: t.rect[0])
    
    merged = []
    current_table = sorted_tables[0]
    
    for next_table in sorted_tables[1:]:
        if should_merge_tables(current_table, next_table):
            # Merge current with next
            current_table = merge_tables(current_table, next_table)
        else:
            # Can't merge, save current and move to next
            merged.append(current_table)
            current_table = next_table
    
    # Don't forget the last table
    merged.append(current_table)
    
    return merged

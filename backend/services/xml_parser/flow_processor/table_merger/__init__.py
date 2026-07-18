from .core import should_merge_tables, merge_tables
from .standard import merge_adjacent_tables
from .legacy import merge_legacy_tables

__all__ = [
    'should_merge_tables',
    'merge_tables',
    'merge_adjacent_tables',
    'merge_legacy_tables',
]

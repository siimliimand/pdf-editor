from typing import List
from ...vector_parser import VectorElement
from ..models import TextElement, TableDefinition
from .grid_builder import build_grid
from .cell_merger import merge_cells
from .background_matcher import match_backgrounds
from .line_clustering import cluster_horizontal_lines

class TableDetector:
    def __init__(self, vectors: List[VectorElement]):
        self.vectors = vectors
        self.horizontal_lines = [v for v in vectors if v.is_horizontal]
        self.vertical_lines = [v for v in vectors if v.is_vertical]
        self.rects = [v for v in vectors if v.fill and v.width > 5 and v.height > 5]

    def detect(self, text_elements: List[TextElement]) -> List[TableDefinition]:
        """
        Detects tables based on intersecting vector lines (grid).
        """
        # Strategy:
        # 1. Find potential table areas by clustering horizontal and vertical lines.
        # 2. Construct a grid from intersecting lines.
        # 3. Map text elements to grid cells. (This part seems to be handled outside or just returning structure?)
        # The return type is List[TableDefinition], which has cells. 
        # But cell.text_elements are empty in the original code? 
        # Yes: cells.append(TableCell(..., text_elements=[], ...))

        tables = []
        
        # 1. Cluster Horizontal Lines to find vertical regions
        # 1. Cluster Horizontal Lines to find vertical regions
        groups = cluster_horizontal_lines(self.horizontal_lines, self.vertical_lines)
        
        # Process groups into Tables
        for group in groups:
            if len(group) < 2: continue # Need at least top and bottom
            
            # Define Table Boundaries to filter vertical lines
            t_top = min(l.y0 for l in group)
            t_bottom = max(l.y0 for l in group)
            t_left = min(l.x0 for l in group)
            t_right = max(l.x1 for l in group)
            
            # Find vertical lines that intersect this Y-range
            relevant_v_lines = [v for v in self.vertical_lines 
                                if (v.y0 < t_bottom + 5 and v.y1 > t_top - 5) and 
                                   (t_left - 5 < v.x0 < t_right + 5)]
            
            # Check for INTERNAL vertical lines
            # If we only have vertical lines at the very edges (borders), we shouldn't treat this as a grid table
            # because we'll miss the internal text columns.
            has_internal_v_lines = False
            if relevant_v_lines:
                # Group vertical lines by X position
                v_x_coords = sorted(list(set(v.x0 for v in relevant_v_lines)))
                if len(v_x_coords) > 2:
                    # Check if any line is significantly inside the table
                    # (more than 10px from edges)
                    internal_lines = [x for x in v_x_coords if t_left + 10 < x < t_right - 10]
                    if internal_lines:
                        has_internal_v_lines = True
            
            # If no vertical lines OR only border lines, try horizontal-only detection
            if not relevant_v_lines or not has_internal_v_lines:
                reason = "No vertical lines" if not relevant_v_lines else "Only border vertical lines (no internal dividers)"
                
                from .horizontal_detector import detect_horizontal_table
                # Pass text_elements so column inference can work properly
                h_table = detect_horizontal_table(group, text_elements)
                if h_table:
                    tables.append(h_table)
                continue
            
            # Construct Grid
            row_positions, col_positions, cells = build_grid(group, relevant_v_lines)
            
            # Remove empty columns (e.g., spurious middle columns from vertical lines)
            from .empty_column_remover import remove_empty_columns
            col_positions, cells = remove_empty_columns(
                col_positions, cells, 
                len(row_positions)-1, len(col_positions)-1
            )
            
            # Merge Cells
            cells = merge_cells(cells, len(row_positions)-1, len(col_positions)-1)

            # Assign Background Colors
            match_backgrounds(cells, row_positions, col_positions, self.rects)

            # Use grid boundaries for the table rect
            # Or use the original group boundaries?
            # Using grid boundaries ensures consistency.
            if not row_positions or not col_positions: continue
            
            # Keep as float for sub-pixel precision
            rect_top = row_positions[0]
            rect_bottom = row_positions[-1]
            rect_left = col_positions[0]
            rect_right = col_positions[-1]

            tables.append(TableDefinition(
                rect=(rect_top, rect_left, rect_bottom, rect_right),
                row_positions=row_positions,
                col_positions=col_positions,
                cells=cells
            ))
            
        return tables

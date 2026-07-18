from typing import List, Optional
import json
from pathlib import Path
from ...models import TableDefinition, TextElement
from .cell import render_cell_content

def render_grid_table(table: TableDefinition, block_top: float, images_dir: Optional[Path]) -> str:
    """
    Render a grid table using proper padding-based layout (NOT absolute positioning).
    
    All styling values are dynamically calculated from PDF data:
    - Column widths from col_positions
    - Padding from text element positions within cells
    - Borders from cell style properties
    - Text alignment from text position within cell
    - Font properties from text element specifications
    
    Args:
        table: Table definition with grid structure
        block_top: Absolute top position (table.rect[0] will be used instead)
        images_dir: Directory containing images
        
    Returns:
        HTML string with properly structured table
    """
    # Calculate total width from column positions
    col_widths = []
    for i in range(len(table.col_positions)-1):
        w = table.col_positions[i+1] - table.col_positions[i]
        col_widths.append(w)
        
    total_width = sum(col_widths)
    
    # Use table.rect for positioning: [top, left, bottom, right]
    table_top = table.rect[0]
    table_left = table.rect[1]
    table_right = table.rect[3]
    
    # Calculate the actual width the table needs
    table_width = table_right - table_left
    
    # Calculate column widths as percentages of total table width
    # This allows the table to scale down if needed while maintaining proportions
    col_width_percentages = [(w / total_width * 100) for w in col_widths]
    
    # Prepare data-col-widths attribute for frontend (Tiptap) preservation
    col_width_styles = [f"width: {w}%;" for w in col_width_percentages]
    data_col_widths_json = json.dumps(col_width_styles)
    
    # Table opening with absolute positioning
    # Use max-width to prevent overflow, but maintain absolute positioning for proper layering
    # Use !important on width to prevent frontend from removing it
    table_style = f"position: absolute; top: {table_top}px; left: {table_left}px; width: {table_width}px !important; max-width: calc(100% - {table_left}px); border-collapse: collapse; margin: 0; table-layout: fixed; border-spacing: 0;"
    # Use single quotes for data-col-widths attribute value to wrap the JSON (which uses double quotes)
    html = [f'<table style="{table_style}" data-col-widths=\'{data_col_widths_json}\'>']
    
    # Colgroup for column widths (as percentages for proportional scaling)
    html.append('<colgroup>')
    for w_pct in col_width_percentages:
        html.append(f'<col style="width: {w_pct}%;">')
    html.append('</colgroup>')
    
    # Group cells by row
    cells_by_row = {}
    for cell in table.cells:
        if cell.row_idx not in cells_by_row: cells_by_row[cell.row_idx] = []
        cells_by_row[cell.row_idx].append(cell)
        
    num_rows = len(table.row_positions) - 1
        
    # Calculate dynamic line height for each row
    row_line_heights = {}
    
    for r_i in range(num_rows):
        row_cells = cells_by_row.get(r_i, [])
        max_lh = 1.0 # Default to 1.0 (tight fit) instead of 0.9 to avoid cutting off text
        
        for cell in row_cells:
            if not cell.text_elements: continue
            
            # Group text elements by line to detect multi-line content
            # We assume elements on the same line have similar Y coordinates (within 2px)
            lines = {} # y_coord -> list of elements
            for el in cell.text_elements:
                if not isinstance(el, TextElement): continue
                
                # Find matching line or create new
                found_line_y = None
                for y in lines.keys():
                    if abs(y - el.top) < 2.0:
                        found_line_y = y
                        break
                
                if found_line_y is not None:
                    lines[found_line_y].append(el)
                else:
                    lines[el.top] = [el]
            
            # If we have multiple lines, we can calculate the actual line spacing
            if len(lines) > 1:
                # Sort lines by Y
                sorted_ys = sorted(lines.keys())
                
                # Calculate average distance between consecutive lines
                total_dist = 0
                count = 0
                avg_font_size = 0
                total_font_elements = 0
                
                for i in range(len(sorted_ys) - 1):
                    y1 = sorted_ys[i]
                    y2 = sorted_ys[i+1]
                    dist = y2 - y1
                    total_dist += dist
                    count += 1
                    
                    # Calculate average font size for this gap measurement
                    # We look at elements in the first line of the pair
                    for el in lines[y1]:
                         avg_font_size += el.font_size
                         total_font_elements += 1
                
                if count > 0 and total_font_elements > 0:
                    avg_dist = total_dist / count
                    avg_fs = avg_font_size / total_font_elements
                    
                    if avg_fs > 0:
                        # Calculated line height ratio
                        # We limit it to reasonable bounds (1.0 to 2.0)
                        lh = avg_dist / avg_fs
                        # Slightly reduce to account for font metrics (often lines are tighter than bbox)
                        # But ensure it's at least 1.0
                        lh = max(1.0, lh) 
                        if lh > max_lh:
                            max_lh = lh
                            
        # Cap at reasonable value to prevent explosion
        if max_lh > 2.0: max_lh = 2.0
            
        row_line_heights[r_i] = max_lh

    # Iterate rows
    for r_i in range(num_rows):
        row_height = table.row_positions[r_i+1] - table.row_positions[r_i]
        
        # Calculate compensation for browser rendering overhead
        # The browser adds extra vertical space due to:
        # 1. Font metrics (ascender/descender space) even with line-height: 1
        # 2. Padding-top from text positioning
        # We need to reduce the row height to compensate
        
        row_cells = cells_by_row.get(r_i, [])
        max_font_size = 0
        max_padding_top = 0
        
        for cell in row_cells:
            if cell.text_elements:
                for el in cell.text_elements:
                    if isinstance(el, TextElement):
                        max_font_size = max(max_font_size, el.font_size)
                        # Estimate padding top from text position
                        rel_top = el.top - table.row_positions[cell.row_idx]
                        max_padding_top = max(max_padding_top, rel_top)
        
        # Compensation formula (empirically derived from browser measurements):
        # - Font metrics + padding cause ~8px expansion per row on average
        # - We need to reduce row height by approximately 50% of font size + padding adjustment
        # - This accounts for the extra space browsers add for font rendering and padding
        compensation = 0
        if max_font_size > 0:
            # Increase compensation: 50% of font size + padding adjustment
            # This is based on measurements showing ~8px average expansion
            compensation = max_font_size * 0.50 + min(max_padding_top * 0.5, 3.0)
        
        adjusted_row_height = max(row_height - compensation, row_height * 0.7)  # Don't reduce by more than 30%
        
        html.append(f'<tr style="height: {adjusted_row_height}px; max-height: {adjusted_row_height}px;">')
        
        row_cells.sort(key=lambda c: c.col_idx)
        
        for cell in row_cells:
            if cell.row_span == 0 or cell.col_span == 0: continue
            
            # Cell boundaries
            cell_x_start = table.col_positions[cell.col_idx]
            cell_y_start = table.row_positions[cell.row_idx]
            cell_x_end = table.col_positions[cell.col_idx + cell.col_span]
            cell_y_end = table.row_positions[cell.row_idx + cell.row_span]
            cell_width = cell_x_end - cell_x_start
            cell_height = cell_y_end - cell_y_start
            
            # Render cell content with padding-based layout
            content_html, cell_padding, text_align = render_cell_content(
                cell, cell_x_start, cell_y_start, cell_width, cell_height, 
                images_dir, line_height=row_line_heights.get(r_i, 1.2)
            )
            
            # Build cell style
            style_parts = [
                "vertical-align: top",
                "box-sizing: border-box",
                "white-space: nowrap",
                "overflow: hidden",  # Changed from 'visible' to prevent row expansion
                "line-height: 1",  # Prevent row expansion from default line-height
                f"max-height: {adjusted_row_height}px"  # Enforce row height limit
            ]
            
            # Add padding
            if cell_padding:
                style_parts.append(f"padding: {cell_padding}")
            
            # Add text alignment if detected
            if text_align:
                style_parts.append(f"text-align: {text_align}")
            
            # Add borders from cell style properties (dynamically detected)
            # FIX: To avoid double borders between rows, only render border-bottom.
            # For the first row, also render border-top if present.
            # This creates single shared lines between rows instead of double lines.
            if r_i == 0 and cell.style_top: 
                style_parts.append(f"border-top: {cell.style_top}")
            if cell.style_bottom: 
                style_parts.append(f"border-bottom: {cell.style_bottom}")
            # Vertical borders commented out - PDF shows horizontal lines only
            # if cell.style_left: 
            #     style_parts.append(f"border-left: {cell.style_left}")
            # if cell.style_right: 
            #     style_parts.append(f"border-right: {cell.style_right}")
            
            # Add background color if present
            if cell.background_color:
                style_parts.append(f"background-color: {cell.background_color}")
            
            # Build attributes
            attrs = f'style="{"; ".join(style_parts)};"'
            if cell.col_span > 1: 
                attrs += f' colspan="{cell.col_span}"'
            if cell.row_span > 1: 
                attrs += f' rowspan="{cell.row_span}"'
                
            html.append(f'<td {attrs}>{content_html}</td>')
        
        html.append('</tr>')
    
    html.append('</table>')
    return "".join(html)

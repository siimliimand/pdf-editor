from typing import List, Optional
import re
from pathlib import Path
from ..models import TableRow, TextElement, ImageElement
from ...vector_parser import VectorElement, BorderGroup
from ..extractors import get_image_data
from ..flow_processor import detect_global_columns, detect_header_rows, detect_cell_padding
from .text_block import render_text_block

def render_legacy_table(rows: List[TableRow], block_top: float, page_vectors: List[VectorElement], images_dir: Optional[Path], scale: float = 1.0) -> str:
    """
    Render a legacy table (detected from text flow) using absolute positioning.
    
    Args:
        rows: List of table rows
        block_top: Absolute top position (will use min row.top instead)
        page_vectors: Vector elements for border detection
        images_dir: Directory containing images
        scale: Scale factor for zoom (default 1.0)
        
    Returns:
        HTML string with absolutely positioned table
    """
    col_definitions = detect_global_columns(rows)
    if not col_definitions:
            return render_text_block(rows, block_top, images_dir)
            
    page_vectors = page_vectors or []

    min_left = min(col_definitions)
    max_right = 0
    min_top = min(row.top for row in rows) if rows else 0
    max_bottom = max(row.top + row.height for row in rows) if rows else 0
    
    for row in rows:
        for el in row.elements:
            if isinstance(el, TextElement):
                r = el.left + el.width
                if r > max_right: max_right = r
            elif isinstance(el, ImageElement):
                r = el.left + el.width
                if r > max_right: max_right = r
    
    # Expand bounds based on table lines (vectors)
    if page_vectors:
        for v in page_vectors:
            if v.is_horizontal:
                # Check if vector is within the vertical range of the table (with tolerance)
                v_y = (v.y0 + v.y1) / 2
                if min_top - 5 <= v_y <= max_bottom + 5:
                    if v.x0 < min_left:
                        min_left = v.x0
                    if v.x1 > max_right:
                        max_right = v.x1

    # Ensure min_left is in col_definitions if it was expanded
    # Ensure min_left is in col_definitions if it was expanded
    if col_definitions and min_left < col_definitions[0] - 1:
        # Check if difference is substantial or just a small extension (e.g. line slightly longer than text)
        if col_definitions[0] - min_left < 50:
            # Snap table start to text start to avoid creating an empty narrow column
            min_left = col_definitions[0]
        else:
            # Insert a new column start for the extended content
            col_definitions.insert(0, min_left)

    total_width = max_right - min_left
    if total_width <= 0: total_width = 100 

    header_indices = detect_header_rows(rows)
    
    # Detect borders from vector elements
    table_border_style = ""
    
    if page_vectors:
        # Import VectorParser to use detect_border_groups
        from ...vector_parser import VectorParser
        parser = VectorParser("")  # Create instance just to use the method
        borders = parser.detect_border_groups(page_vectors, tolerance=10.0)
        
        # Find border that overlaps with this table
        for border in borders:
            # Check if border overlaps with table bounds
            overlap_x = min(border.x1, max_right) - max(border.x0, min_left)
            overlap_y = min(border.y1, max_bottom) - max(border.y0, min_top)
            
            if overlap_x > 0 and overlap_y > 0:
                # Calculate overlap ratio
                border_area = border.width * border.height
                table_area = total_width * (max_bottom - min_top)
                overlap_area = overlap_x * overlap_y
                
                # If significant overlap (>50% of border or >30% of table), apply border
                if overlap_area > border_area * 0.5 or overlap_area > table_area * 0.3:
                    # Apply scale to border width and radius
                    border_width = max(1, int(border.border_width * scale))
                    scaled_radius = border.border_radius * scale
                    border_radius_style = f" border-radius: {scaled_radius}px;" if scaled_radius > 0 else ""
                    # Add padding for inner spacing when border has rounded corners
                    # Use padding instead of border-spacing to avoid row overlap issues at high zoom
                    # Calculate based on unscaled radius to keep padding consistent, then cap at 8px
                    inner_padding = min(8, max(5, int(border.border_radius * 0.6)))
                    table_border_style = f" border: {border_width}px solid {border.border_color};{border_radius_style} padding: {inner_padding}px;"
                    break
    
    # Determine border-collapse mode: must use 'separate' for border-radius to work
    border_collapse_mode = "separate" if "border-radius" in table_border_style else "collapse"
    # Use !important on width to prevent frontend from removing it
    table_style = f"position: absolute; top: {min_top}px; left: {min_left}px; width: {total_width}px !important; max-width: calc(100% - {min_left}px); border-collapse: {border_collapse_mode}; margin: 0; table-layout: fixed; box-sizing: border-box;{table_border_style}"
    print(f"[LEGACY TABLE] Rendering table with width={total_width}px, left={min_left}px, cols={len(col_definitions)}")
    html = [f'<table style="{table_style}">']
    html.append('<colgroup>')
    
    for i, col_left in enumerate(col_definitions):
        next_col_left = col_definitions[i+1] if i + 1 < len(col_definitions) else max_right
        width = next_col_left - col_left
        if width < 0: width = 0
        html.append(f'<col style="width: {width}px;">')
    html.append('</colgroup>')
    
    for row_idx, row in enumerate(rows):
        html.append('<tr>')
        sorted_elements = sorted(row.elements, key=lambda e: e.left)
        
        is_header = row_idx in header_indices
        
        h_pad, v_pad = detect_cell_padding(row, col_definitions, max_right)
        
        border_top_style = ""
        border_bottom_style = ""
        
        row_top_y = row.top
        row_bottom_y = row.top + row.height
        
        for v in page_vectors:
            if v.is_horizontal:
                line_y = (v.y0 + v.y1) / 2
                
                if abs(line_y - row_top_y) < 4:
                    width = max(1, int(v.linewidth))
                    border_top_style = f"border-top: {width}px solid #333;" 
                    
                if abs(line_y - row_bottom_y) < 4:
                    width = max(1, int(v.linewidth))
                    border_bottom_style = f"border-bottom: {width}px solid #333;"
        
        current_col_idx = 0
        while current_col_idx < len(col_definitions):
            col_left = col_definitions[current_col_idx]
            next_col_left = col_definitions[current_col_idx+1] if current_col_idx + 1 < len(col_definitions) else max_right
            col_width = next_col_left - col_left
            
            cell_elements = []
            
            for el in sorted_elements:
                if el.left >= col_left - 5 and el.left < next_col_left - 5:
                    cell_elements.append(el)
            
            colspan = 1
            if cell_elements:
                max_el_width = max(e.width for e in cell_elements) if isinstance(cell_elements[0], (TextElement, ImageElement)) else 0
                temp_width = col_width
                temp_idx = current_col_idx + 1
                while temp_width < max_el_width - 5 and temp_idx < len(col_definitions):
                        next_c_l = col_definitions[temp_idx]
                        next_next_c_l = col_definitions[temp_idx+1] if temp_idx+1 < len(col_definitions) else max_right
                        temp_width += (next_next_c_l - next_c_l)
                        colspan += 1
                        temp_idx += 1
            
            # Detect text alignment by comparing space on left vs right of text
            text_align = None
            text_elements_in_cell = [el for el in cell_elements if isinstance(el, TextElement)]
            
            if text_elements_in_cell and col_width > 0:
                # Calculate average space distribution across all text elements
                total_space_left = 0
                total_space_right = 0
                
                text_content = " ".join([el.text for el in text_elements_in_cell]).strip()
                
                for el in text_elements_in_cell:
                    space_left = el.left - col_left
                    space_right = col_width - (space_left + el.width)
                    total_space_left += space_left
                    total_space_right += space_right
                
                avg_space_left = total_space_left / len(text_elements_in_cell)
                avg_space_right = total_space_right / len(text_elements_in_cell)
                
                # Use 2px threshold for precise alignment detection
                THRESHOLD = 2
                
                # Heuristic for numeric/monetary values:
                # If cell contains digits but NO lowercase letters (e.g. "EUR 2.19", "123.45", "ID-123"),
                # it's likely a number/amount/code which usually benefits from right alignment.
                is_numeric_like = bool(re.search(r'\d', text_content)) and not bool(re.search(r'[a-z]', text_content))
                
                # Check for date-like strings (e.g. "December 1, 2025")
                months = ['january', 'february', 'march', 'april', 'may', 'june', 
                         'july', 'august', 'september', 'october', 'november', 'december']
                is_date_like = bool(re.search(r'\d', text_content)) and any(m in text_content.lower() for m in months)
                
                if is_numeric_like or is_date_like:
                    # Logic for numeric-like content (prefer right alignment)
                    # If there is significant space on the right, it's likely left-aligned.
                    # We use a threshold of 15px to allow for some padding/imprecision on the right
                    # while catching cases where text is clearly left-aligned in a wider column.
                    if avg_space_right > avg_space_left + 15:
                        text_align = "left"
                    else:
                        # Otherwise, for numeric content, we prefer right alignment.
                        # This handles cases where:
                        # 1. Text is centered (balanced spaces)
                        # 2. Text is right-aligned (more space on left)
                        # 3. Text is tight in column but has small padding on right (common in single-row columns)
                        text_align = "right"
                else:
                    # Standard logic for text
                    # Check if text fills the cell (both spaces very small)
                    if avg_space_left < THRESHOLD and avg_space_right < THRESHOLD:
                        text_align = "left"  # Default for full-width text
                    # Check if spaces are approximately equal (centered)
                    elif abs(avg_space_left - avg_space_right) < THRESHOLD:
                        text_align = "center"
                    # Check which side has more space
                    elif avg_space_left > avg_space_right + THRESHOLD:
                        text_align = "right"  # More space on left = right-aligned
                    elif avg_space_right > avg_space_left + THRESHOLD:
                        text_align = "left"   # More space on right = left-aligned
            
            content_parts = []
            for el in cell_elements:
                if isinstance(el, TextElement):
                    if text_align:
                        # Use flow layout for aligned cells to allow proper editing/responsiveness
                        # This removes the fixed absolute positioning which causes issues with alignment
                        style = (
                            f'position: relative; '
                            f'font-size: {el.font_size}px; '
                            f'line-height: 1; '
                            f'white-space: nowrap; '
                            f'margin-right: 4px; '  # Add small spacing between elements
                        )
                    else:
                        # Use absolute positioning for unaligned/complex layouts
                        # Calculate relative positioning
                        rel_left = el.left - col_left
                        rel_top = el.top - row.top
                        
                        style = (
                            f'position: absolute; '
                            f'left: {rel_left}px; '
                            f'top: {rel_top}px; '
                            f'font-size: {el.font_size}px; '
                            f'line-height: 1; '
                            f'white-space: nowrap; '
                        )
                    
                    if el.font_spec:
                        style += f' font-weight: {el.font_spec.font_weight};'
                        if el.font_spec.is_italic: style += ' font-style: italic;'
                        style += f' color: {el.font_spec.color};'
                        style += f' font-family: {el.font_spec.family};'
                    content_parts.append(f'<span style="{style}">{el.text}</span>')
                    
                elif isinstance(el, ImageElement):
                    img_data = get_image_data(el.src, images_dir)
                    if img_data:
                        rel_left = el.left - col_left
                        rel_top = el.top - row.top
                        style = (
                            f'position: absolute; '
                            f'left: {rel_left}px; '
                            f'top: {rel_top}px; '
                            f'width: {el.width}px !important; '
                            f'height: {el.height}px !important; '
                            f'object-fit: contain; '
                            f'max-width: 100%; '
                            f'max-height: 100%;'
                        )
                        content_parts.append(f'<img src="{img_data}" width="{int(el.width)}" height="{int(el.height)}" style="{style}" />')
            
            content = "".join(content_parts)
            
            # Ensure cell has height to accommodate absolute children
            # Use detected padding to preserve indentation (crucial for merged columns)
            td_style = f'position: relative; height: {row.height}px; padding: 0 0 0 {h_pad}px; vertical-align: top; overflow: visible; box-sizing: border-box;'
            
            # Add text alignment if detected
            if text_align:
                td_style += f' text-align: {text_align};'
            
            if border_top_style: td_style += f" {border_top_style}"
            if border_bottom_style: td_style += f" {border_bottom_style}"
            
            # Dynamic Background Detection from Vectors
            # Check for filled rectangles that overlap this cell/row
            bg_color = None
            if page_vectors:
                cell_left = col_left
                # Calculate cell width accounting for colspan
                cell_width = col_width
                if colspan > 1:
                     # Add widths of spanned columns
                     temp_idx = current_col_idx + 1
                     current_w = col_width
                     for _ in range(colspan - 1):
                         if temp_idx < len(col_definitions):
                             n_left = col_definitions[temp_idx]
                             nn_left = col_definitions[temp_idx+1] if temp_idx + 1 < len(col_definitions) else max_right
                             current_w += (nn_left - n_left)
                             temp_idx += 1
                     cell_width = current_w
                     
                cell_right = cell_left + cell_width
                cell_top = row.top
                cell_bottom = row.top + row.height
                cell_area = (cell_right - cell_left) * (cell_bottom - cell_top)
                
                best_overlap = 0.0
                
                for v in page_vectors:
                    if v.fill and v.color and v.color != "#ffffff":
                        # Check overlap
                        ix0 = max(v.x0, cell_left)
                        iy0 = max(v.y0, cell_top)
                        ix1 = min(v.x1, cell_right)
                        iy1 = min(v.y1, cell_bottom)
                        
                        if ix1 > ix0 and iy1 > iy0:
                            overlap_area = (ix1 - ix0) * (iy1 - iy0)
                            overlap_ratio = overlap_area / cell_area if cell_area > 0 else 0
                            
                            vector_area = (v.x1 - v.x0) * (v.y1 - v.y0)
                            vector_covered_ratio = overlap_area / vector_area if vector_area > 0 else 0
                            
                            if overlap_ratio > 0.3 or vector_covered_ratio > 0.5:
                                if overlap_area > best_overlap:
                                    best_overlap = overlap_area
                                    bg_color = v.color


            if bg_color:
                td_style += f' background-color: {bg_color};'
            elif is_header and not bg_color:
                 # Optional: Keep a default for headers ONLY if we trust detection, 
                 # but for now disable it to fix the Contabo issue.
                 # td_style += ' background-color: #f9f9f9;'
                 pass
            
            if colspan > 1:
                    html.append(f'<td colspan="{colspan}" style="{td_style}">{content}</td>')
            else:
                    html.append(f'<td style="{td_style}">{content}</td>')
            
            current_col_idx += colspan
            
        html.append('</tr>')
    html.append('</table>')
    return "".join(html)

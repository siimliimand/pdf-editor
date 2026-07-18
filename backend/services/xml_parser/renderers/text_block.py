from typing import List, Optional
from pathlib import Path
from ..models import TableRow, TextElement, ImageElement
from ..extractors import get_image_data
from ...vector_parser import VectorElement

def find_horizontal_lines_near_text(rows: List[TableRow], vectors: List[VectorElement], tolerance: float = 5.0) -> List[tuple]:
    """
    Find horizontal lines (from PDF vectors) that are near individual text rows.
    Returns list of (y_position, left, right, color, linewidth) tuples for full-width lines.
    
    Lines are detected:
    1. Near each row's top position (border above text)
    2. Near each row's bottom position (border below text)
    """
    if not rows or not vectors:
        return []
    
    # Get all significant Y positions from rows
    row_positions = set()
    for row in rows:
        row_positions.add(row.top)  # Top of row
        row_positions.add(row.top + row.height)  # Bottom of row
    
    # Calculate text X bounds for full-width check
    min_x = float('inf')
    max_x = float('-inf')
    
    for row in rows:
        for el in row.elements:
            if isinstance(el, TextElement):
                min_x = min(min_x, el.left)
                max_x = max(max_x, el.left + el.width)
    
    if min_x == float('inf'):
        return []
    
    text_width = max_x - min_x
    lines = []
    seen_y = set()  # Avoid duplicate lines at same Y
    
    for v in vectors:
        if not v.is_horizontal:
            continue
        
        line_y = v.y0
        line_width = v.x1 - v.x0
        
        # Only consider full-width lines (spans most of the text width or page width)
        if line_width < max(text_width * 0.8, 400):  # At least 80% of text width or 400px
            continue
        
        # Check if line is near any row position
        for row_y in row_positions:
            if abs(line_y - row_y) < tolerance:
                if round(line_y, 1) not in seen_y:
                    lines.append((line_y, v.x0, v.x1, v.color, v.linewidth))
                    seen_y.add(round(line_y, 1))
                break
    
    return lines

def find_backgrounds_near_text(rows: List[TableRow], vectors: List[VectorElement]) -> List[tuple]:
    """
    Find filled background rectangles that overlap with text rows.
    Returns list of (top, left, width, height, color, border_radius) tuples.
    """
    if not rows or not vectors:
        return []
    
    # Calculate bounding box of all text in this block
    min_x = float('inf')
    max_x = float('-inf')
    min_y = float('inf')
    max_y = float('-inf')
    
    has_text = False
    for row in rows:
        min_y = min(min_y, row.top)
        max_y = max(max_y, row.top + row.height)
        for el in row.elements:
            if isinstance(el, TextElement):
                min_x = min(min_x, el.left)
                max_x = max(max_x, el.left + el.width)
                has_text = True
    
    if not has_text:
        return []
    
    # Expand bounds slightly to catch overlapping backgrounds
    min_x -= 5
    max_x += 5
    min_y -= 5
    max_y += 5
    
    block_area = (max_x - min_x) * (max_y - min_y)
    backgrounds = []
    
    for v in vectors:
        if v.fill and v.color and v.color != "#ffffff":
            # Check overlap with block bounds
            ix0 = max(v.x0, min_x)
            iy0 = max(v.y0, min_y)
            ix1 = min(v.x1, max_x)
            iy1 = min(v.y1, max_y)
            
            if ix1 > ix0 and iy1 > iy0:
                # If vector overlaps with this text block
                # Check individual rows for more precise matching
                for row in rows:
                    r_y0 = row.top - 2
                    r_y1 = row.top + row.height + 2
                    
                    ry_ix0 = max(v.y0, r_y0)
                    ry_ix1 = min(v.y1, r_y1)
                    
                    if ry_ix1 > ry_ix0:
                        # Significant vertical overlap with a row
                        # Include border_radius from vector
                        border_radius = getattr(v, 'border_radius', 0.0)
                        backgrounds.append((v.y0, v.x0, v.width, v.height, v.color, border_radius))
                        break
    
    return backgrounds

def render_text_block(rows: List[TableRow], block_top: float, images_dir: Optional[Path], page_vectors: List[VectorElement] = None) -> str:
    """
    Render a text block using absolute positioning for precise coordinate mapping.
    
    Args:
        rows: List of table rows to render
        block_top: Absolute top position of this block (not used with absolute positioning)
        images_dir: Directory containing images
        page_vectors: List of vector elements for border detection
        
    Returns:
        HTML string with absolutely positioned elements
    """
    html = []
    if not rows: return ""
    
    # Wrap in a container div with absolute positioning
    html.append('<div style="position: absolute; width: 100%; height: 100%; pointer-events: none;">')
    
    page_vectors = page_vectors or []
    
    # Render background rectangles
    backgrounds = find_backgrounds_near_text(rows, page_vectors)
    for bg_top, bg_left, bg_width, bg_height, bg_color, bg_radius in backgrounds:
        radius_style = f" border-radius: {bg_radius}px;" if bg_radius > 0 else ""
        html.append(f'<div style="position: absolute; top: {bg_top}px; left: {bg_left}px; width: {bg_width}px; height: {bg_height}px; background-color: {bg_color};{radius_style}"></div>')
    
    # Render horizontal divider lines near text
    h_lines = find_horizontal_lines_near_text(rows, page_vectors)
    for line_y, left, right, color, linewidth in h_lines:
        lw = max(1, int(linewidth))
        html.append(f'<div style="position: absolute; top: {line_y}px; left: {left}px; width: {right - left}px; height: 0; border-top: {lw}px solid {color}; pointer-events: none;"></div>')
    
    # Collect all images to render separately
    images_to_render = []
    
    for row in rows:
        text_parts = []
        sorted_elements = sorted(row.elements, key=lambda e: e.left)
        
        for el in sorted_elements:
                if isinstance(el, TextElement):
                    style = f'font-size: {el.font_size}px;'
                    if el.font_spec:
                        # Use numeric font-weight for better precision
                        style += f' font-weight: {el.font_spec.font_weight};'
                        if el.font_spec.is_italic: style += ' font-style: italic;'
                        style += f' color: {el.font_spec.color};'
                        style += f' font-family: {el.font_spec.family};'
                    
                    text_parts.append(f'<span style="{style}">{el.text}</span>')
                elif isinstance(el, ImageElement):
                    # Collect images for separate rendering
                    images_to_render.append(el)
        
        # Only render paragraph if there's text content
        if text_parts:
            line_content = " ".join(text_parts)
            indent = sorted_elements[0].left if sorted_elements else 0
            
            # Use absolute positioning with exact PDF coordinates
            # Adjust top to compensate for line-height expansion (half-leading)
            # Shift = (Font * (LH - 1)) / 2
            # Text is pushed down by this amount, so we move the box UP by this amount to keep text static.
            # Find first TextElement for font size
            primary_font_size = 12
            for el in sorted_elements:
                 if hasattr(el, 'font_size'):
                     primary_font_size = el.font_size
                     break
            line_height = getattr(row, 'approx_line_height', 1.0)
            
            # Cap unreasonable line heights for safety
            if line_height < 0.7: line_height = 1.0
            if line_height > 3.0: line_height = 3.0
            
            top_adjustment = (primary_font_size * (line_height - 1.0)) / 2
            final_top = row.top - top_adjustment
            
            html.append(f'<p style="position: absolute; top: {final_top:.2f}px; left: {indent}px; margin: 0; line-height: {line_height}; pointer-events: auto;">{line_content}</p>')
    
    # Render images separately with absolute positioning
    for img_el in images_to_render:
        img_data = get_image_data(img_el.src, images_dir)
        if img_data:
            # Position image absolutely at its exact coordinates
            img_style = (
                f'position: absolute; '
                f'left: {img_el.left}px; '
                f'top: {img_el.top}px; '
                f'width: {img_el.width}px !important; '
                f'height: {img_el.height}px !important; '
                f'max-width: 100%; '
                f'object-fit: contain; '
                f'pointer-events: auto;'
            )
            html.append(f'<img src="{img_data}" width="{int(img_el.width)}" height="{int(img_el.height)}" style="{img_style}" />')
        
    html.append('</div>')
    return "".join(html)


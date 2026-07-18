from typing import Optional, Tuple
from pathlib import Path
from ...models import TextElement, ImageElement, TableCell
from ...extractors import get_image_data

def render_cell_content(cell: TableCell, cell_x_start: float, cell_y_start: float, 
                       cell_width: float, cell_height: float, 
                       images_dir: Optional[Path], line_height: float = 0.9) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Render cell content and calculate padding/alignment.
    
    Returns:
        (content_html, padding_css, text_align)
    """
    if not cell.text_elements and not any(isinstance(el, ImageElement) for el in cell.text_elements):
        return "", None, None
    
    content_parts = []
    min_left = float('inf')
    min_top = float('inf')
    max_right = 0
    max_bottom = 0
    
    # Collect all text elements and calculate bounds
    text_elements = []
    for el in cell.text_elements:
        if isinstance(el, TextElement):
            text_elements.append(el)
            rel_left = el.left - cell_x_start
            rel_top = el.top - cell_y_start
            rel_right = rel_left + el.width  # Use actual text width from PDF
            rel_bottom = rel_top + el.font_size
            
            min_left = min(min_left, rel_left)
            min_top = min(min_top, rel_top)
            max_right = max(max_right, rel_right)
            max_bottom = max(max_bottom, rel_bottom)
    
    # Calculate padding from text positions
    padding_top = min_top if min_top != float('inf') else 0
    padding_left = min_left if min_left != float('inf') else 0
    padding_bottom = 0 # Do not enforce bottom padding to avoid row expansion
    padding_right = cell_width - max_right if max_right > 0 else 0
    
    # Adjust padding_top for line-height > 1.0 (baseline preservation)
    # Default line height for calculation if not provided
    # line_height = 1.2
    
    # If font size is available, adjust top padding
    if text_elements:
         avg_font_size = sum(e.font_size for e in text_elements) / len(text_elements)
         # Shift up by half-leading: (font * (LH - 1)) / 2
         shift = (avg_font_size * (line_height - 1.0)) / 2
         padding_top -= shift
         # Also reduce bottom padding to accommodate bottom half-leading expansion
         # The CSS text block expands both up and down by half-leading.
         padding_bottom -= shift
    
    # Ensure non-negative padding
    padding_top = max(0, padding_top)
    padding_left = max(0, padding_left)
    padding_bottom = max(0, padding_bottom)
    padding_right = max(0, padding_right)
    
    padding_css = f"{padding_top}px {padding_right}px {padding_bottom}px {padding_left}px"
    
    # Detect text alignment based on space distribution
    # Calculate space on left vs right of text to determine alignment
    text_align = None
    if text_elements and cell_width > 0:
        # Calculate average space distribution across all text elements
        total_space_left = 0
        total_space_right = 0
        
        for el in text_elements:
            space_left = el.left - cell_x_start
            space_right = cell_width - (space_left + el.width)  # Use actual text width
            total_space_left += space_left
            total_space_right += space_right
        
        avg_space_left = total_space_left / len(text_elements)
        avg_space_right = total_space_right / len(text_elements)
        
        # Use 2px threshold for precise alignment detection
        THRESHOLD = 2
        
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
    
    # Render text elements as spans with font styling
    for el in cell.text_elements:
        if isinstance(el, TextElement):
            style_parts = [
                f"font-size: {el.font_size}px",
                f"line-height: {line_height}",
                "white-space: nowrap"
            ]
            
            # Add font properties from PDF
            if el.font_spec:
                style_parts.append(f"font-weight: {el.font_spec.font_weight}")
                if el.font_spec.is_italic:
                    style_parts.append("font-style: italic")
                style_parts.append(f"color: {el.font_spec.color}")
                style_parts.append(f"font-family: {el.font_spec.family}")
            
            content_parts.append(f'<span style="{"; ".join(style_parts)};">{el.text}</span>')
            
        elif isinstance(el, ImageElement):
            # Images still need positioning - keep them absolutely positioned within cell
            img_data = get_image_data(el.src, images_dir)
            if img_data:
                rel_left = el.left - cell_x_start
                rel_top = el.top - cell_y_start
                
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
    
    content_html = "".join(content_parts)
    return content_html, padding_css, text_align

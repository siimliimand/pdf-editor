from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTPage, LTLine, LTRect, LTCurve, LTFigure

@dataclass
class VectorElement:
    x0: float
    y0: float
    x1: float
    y1: float
    linewidth: float
    stroke: bool
    fill: bool
    color: str = "#000000"  # Hex color for stroke or fill
    fill_color: str = "#000000"  # Fill color (separate from stroke)
    dash: Optional[List[int]] = None
    border_radius: float = 0.0  # Rounded corners (if detected)

    @property
    def width(self):
        return abs(self.x1 - self.x0)

    @property
    def height(self):
        return abs(self.y1 - self.y0)
    
    @property
    def is_horizontal(self):
        # Allow slight height for thick lines
        return self.height <= max(2.0, self.linewidth * 1.5) and self.width > 5

    @property
    def is_vertical(self):
        # Allow slight width for thick lines
        return self.width <= max(2.0, self.linewidth * 1.5) and self.height > 5

@dataclass
class BorderGroup:
    """Represents a detected border composed of multiple vector elements"""
    x0: float  # Left edge
    y0: float  # Top edge
    x1: float  # Right edge
    y1: float  # Bottom edge
    border_width: float
    border_color: str
    border_radius: float = 0.0
    
    @property
    def width(self):
        return abs(self.x1 - self.x0)
    
    @property
    def height(self):
        return abs(self.y1 - self.y0)


class VectorParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pages: Dict[int, List[VectorElement]] = {}

    def parse(self):
        """Extracts vector elements from all pages."""
        for page_layout in extract_pages(self.pdf_path):
            page_num = page_layout.pageid
            vectors = []
            self._extract_vectors_recursive(page_layout, vectors)
            self.pages[page_num] = vectors
            
    def _extract_vectors_recursive(self, element, vectors: List[VectorElement]):
         # Only interested in Lines and Rects (which are Curves in pdfminer sometimes)
        if isinstance(element, (LTLine, LTRect, LTCurve)):
            # Helper to Convert Color
            def get_color_hex(color_tuple):
                if not color_tuple: return "#000000"
                # Handle simplified color space (r, g, b) or (gray,)
                try:
                    if len(color_tuple) == 3:
                        r, g, b = color_tuple
                        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
                    elif len(color_tuple) == 1:
                        c = int(color_tuple[0]*255)
                        return f"#{c:02x}{c:02x}{c:02x}"
                    elif len(color_tuple) == 4: # CYMK
                         # Naive conversion or just ignore
                         return "#000000"
                except:
                    pass
                return "#000000"

            stroke_color = "#000000"
            fill_color = "#000000"
            
            # Extract stroking color (for lines/borders)
            if hasattr(element, 'stroking_color') and element.stroking_color:
                stroke_color = get_color_hex(element.stroking_color)
            
            # Extract non-stroking color (for fills)
            if hasattr(element, 'non_stroking_color') and element.non_stroking_color:
                fill_color = get_color_hex(element.non_stroking_color)
            
            # For filled elements, use fill_color as the primary color
            # For stroked elements, use stroke_color
            is_filled = getattr(element, 'fill', False)
            is_stroked = getattr(element, 'stroke', False)
            
            # Primary color: use fill_color if filled, otherwise stroke_color
            primary_color = fill_color if is_filled else stroke_color
            
            # Detect rounded corners from path data
            # PDFs represent rounded rectangles using Bezier curves ('c' commands)
            border_radius = 0.0
            original_path = getattr(element, 'original_path', None)
            if original_path:
                # Count curve commands - 'c' is Bezier curve
                curve_count = sum(1 for cmd in original_path if cmd and cmd[0] == 'c')
                if curve_count >= 4:  # Typically 4 corners = 4 curves
                    # Estimate border radius from curve segments
                    # Look at the first curve command's control point distance
                    for cmd in original_path:
                        if cmd and cmd[0] == 'c' and len(cmd) >= 7:
                            # cmd = ('c', x1, y1, x2, y2, x3, y3)
                            # Approximate radius as distance of first control point
                            x1, y1 = cmd[1], cmd[2]
                            x3, y3 = cmd[5], cmd[6]
                            # Use magnitude of curve control as rough estimate
                            border_radius = max(abs(x3 - x1), abs(y3 - y1)) / 2
                            border_radius = min(border_radius, 20.0)  # Cap at reasonable value
                            break
            
            # Identify dash style? (pdfminer often doesn't expose this easily on LT objects, skipping for now)

            # Determine coordinates
            # LTLine has x0,y0,x1,y1
            # LTRect/LTCurve has x0,y0,x1,y1 bounding box
            
            vectors.append(VectorElement(
                x0=element.x0, y0=element.y0, 
                x1=element.x1, y1=element.y1,
                linewidth=getattr(element, 'linewidth', 1.0),
                stroke=is_stroked, 
                fill=is_filled,
                color=primary_color,  # Primary color (fill if filled, stroke otherwise)
                fill_color=fill_color,  # Explicit fill color
                border_radius=border_radius,  # Rounded corners
            ))

        # Recurse into containers
        if isinstance(element, LTFigure) or hasattr(element, '__iter__'):
            try:
                for child in element:
                    self._extract_vectors_recursive(child, vectors)
            except:
                pass

    def get_vectors_for_page(self, page_num: int, page_height: float) -> List[VectorElement]:
        """
        Returns vectors for a page with coordinates converted to Top-Down (y=0 at top).
        pdftohtml XML: y increases downwards.
        pdfminer: y increases upwards.
        
        New Y = PageHeight - Old Y
        """
        raw_vectors = self.pages.get(page_num, [])
        converted = []
        for v in raw_vectors:
            # Flip Y axis
            # old_y0 is bottom, old_y1 is top
            # new_y0 (top) = height - old_y1
            # new_y1 (bottom) = height - old_y0
            
            new_y0 = page_height - v.y1
            new_y1 = page_height - v.y0
            
            converted.append(VectorElement(
                x0=v.x0, y0=new_y0,
                x1=v.x1, y1=new_y1,
                linewidth=v.linewidth,
                stroke=v.stroke,
                fill=v.fill,
                color=v.color,
                fill_color=v.fill_color,
                dash=v.dash,
                border_radius=v.border_radius
            ))
        return converted

    def detect_border_groups(self, vectors: List[VectorElement], tolerance: float = 10.0) -> List[BorderGroup]:
        """
        Detect groups of stroked vectors that form rectangular borders with rounded corners.
        
        Args:
            vectors: List of vector elements to analyze
            tolerance: Maximum distance between connected elements (pixels)
            
        Returns:
            List of detected BorderGroup objects
        """
        borders = []
        
        # Filter to only stroked elements (potential border segments)
        stroked = [v for v in vectors if v.stroke and not v.fill]
        
        # Group vectors by proximity and color
        used = set()
        
        for i, v1 in enumerate(stroked):
            if i in used:
                continue
                
            # Find all vectors that could be part of the same border
            group = [v1]
            group_indices = {i}
            
            # Keep expanding the group
            changed = True
            while changed:
                changed = False
                for j, v2 in enumerate(stroked):
                    if j in group_indices or j in used:
                        continue
                    
                    # Check if v2 is close to any vector in the group
                    # and has similar color and line width
                    for v_group in group:
                        if (v2.color.lower() == v_group.color.lower() and
                            abs(v2.linewidth - v_group.linewidth) < 0.5):
                            
                            # Check if endpoints are close
                            close = False
                            for p1 in [(v_group.x0, v_group.y0), (v_group.x1, v_group.y1)]:
                                for p2 in [(v2.x0, v2.y0), (v2.x1, v2.y1)]:
                                    dist = ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**0.5
                                    if dist < tolerance:
                                        close = True
                                        break
                                if close:
                                    break
                            
                            if close:
                                group.append(v2)
                                group_indices.add(j)
                                changed = True
                                break
            
            # If we have at least 4 elements (could form a rectangle), analyze as potential border
            if len(group) >= 4:
                # Calculate bounding box
                min_x = min(min(v.x0, v.x1) for v in group)
                max_x = max(max(v.x0, v.x1) for v in group)
                min_y = min(min(v.y0, v.y1) for v in group)
                max_y = max(max(v.y0, v.y1) for v in group)
                
                # Calculate border radius from curve segments
                border_radius = 0.0
                for v in group:
                    # Curves that are small and connect horizontal/vertical lines are likely corners
                    if not v.is_horizontal and not v.is_vertical:
                        # Estimate radius from the curve's size
                        curve_size = max(v.width, v.height)
                        if curve_size < 20:  # Reasonable corner size
                            border_radius = max(border_radius, curve_size)
                
                # Use the first element's properties for border style
                border_width = group[0].linewidth
                border_color = group[0].color
                
                borders.append(BorderGroup(
                    x0=min_x,
                    y0=min_y,
                    x1=max_x,
                    y1=max_y,
                    border_width=border_width,
                    border_color=border_color,
                    border_radius=border_radius
                ))
                
                # Mark these vectors as used
                used.update(group_indices)
        
        return borders

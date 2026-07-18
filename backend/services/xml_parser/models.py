from dataclasses import dataclass
from typing import List, Dict, Optional, Union, Tuple

@dataclass
class FontSpec:
    id: str
    size: int
    family: str
    color: str
    is_bold: bool
    is_italic: bool
    font_weight: int = 400  # CSS font-weight (100-900)

@dataclass
class TextElement:
    text: str
    top: float
    left: float
    width: float
    height: float
    font_spec: Optional[FontSpec]
    font_size: float

@dataclass
class ImageElement:
    src: str
    top: float
    left: float
    width: float
    height: float

Element = Union[TextElement, ImageElement]

@dataclass
class TableRow:
    top: int
    height: int
    elements: List[Element]
    approx_line_height: float = 1.0
    
    @property
    def is_multi_column(self) -> bool:
        # A row is multi-column if it has more than 1 element
        # AND those elements are separated by some gap (to avoid splitting words)
        text_elements = [e for e in self.elements if isinstance(e, TextElement)]
        if len(text_elements) <= 1:
            return False
        
        # Check gaps
        sorted_els = sorted(text_elements, key=lambda e: e.left)
        for i in range(len(sorted_els) - 1):
             # If elements overlap or are very close, they are one column (a sentence)
             # If gap is significant, it's a table column
            gap = sorted_els[i+1].left - (sorted_els[i].left + sorted_els[i].width)
            if gap > 15: # Increased threshold slightly
                return True
        return False

@dataclass
class TableCell:
    row_idx: int
    col_idx: int
    row_span: int
    col_span: int
    text_elements: List[Union[TextElement, ImageElement]]
    # Border Styles (e.g. "1px solid #000")
    style_top: str = ""
    style_bottom: str = ""
    style_left: str = ""
    style_right: str = ""
    background_color: Optional[str] = None

@dataclass
class TableDefinition:
    rect: Tuple[float, float, float, float] # top, left, bottom, right (now float for precision)
    row_positions: List[float] # Y-coordinates (now float for precision)
    col_positions: List[float] # X-coordinates (now float for precision)
    cells: List[TableCell]

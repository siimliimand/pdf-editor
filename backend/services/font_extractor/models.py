from dataclasses import dataclass
from typing import Tuple

@dataclass
class FontInfo:
    """Font information extracted from PDF"""
    text: str
    font_family: str
    font_size: float  # In points (unscaled)
    is_bold: bool
    is_italic: bool
    color: str  # Hex color
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    font_weight: int = 400  # CSS font-weight (100-900)

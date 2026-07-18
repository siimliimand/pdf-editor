"""
Alternative Image Extractor using PyMuPDF (fitz)

This is a more robust alternative to pdfminer.six for image extraction.
PyMuPDF has better native support for PDF rendering and color space handling.

To use this implementation:
1. Install PyMuPDF: pip install PyMuPDF
2. Replace ImageExtractor import in pdf_service.py with this class
"""

from typing import Dict, List, Tuple
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import io


class ImageExtractorPyMuPDF:
    """
    Extract images from PDF using PyMuPDF (fitz).
    Better color handling and transparency support than pdfminer.six.
    """
    
    def __init__(self, pdf_path: str, output_dir: Path):
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True, parents=True)
        # Store extracted images: {page_num: [(filename, x0, y0, x1, y1, width, height)]}
        self.images: Dict[int, List[Tuple[str, float, float, float, float, int, int]]] = {}
        
    def extract(self):
        """
        Extract all images from the PDF using Render-Crop strategy.
        This renders the visible page area for each image, guaranteeing visual fidelity.
        """
        doc = fitz.open(self.pdf_path)
        
        for page_num, page in enumerate(doc):
            page_images = []
            page_height = page.rect.height
            
            # Get all images on the page
            image_list = page.get_images(full=True)
            
            for img_index, img_info in enumerate(image_list):
                try:
                    xref = img_info[0]
                    # img_info: (xref, smask, width, height, bpc, colorspace, alt_colorspace, name, filter, referencer)
                    native_width = img_info[2]
                    native_height = img_info[3]
                    
                    # Find where this image is drawn on the page
                    rects = page.get_image_rects(xref)
                    
                    if not rects:
                        # Image is present in objects but not displayed (e.g. hidden mask)
                        continue
                        
                    # Extract each instance of the image
                    for i, rect in enumerate(rects):
                        # Calculate matrix to match native resolution
                        # This ensures we get the highest quality extraction
                        if rect.width > 0 and rect.height > 0:
                            zoom_x = native_width / rect.width
                            zoom_y = native_height / rect.height
                        else:
                            zoom_x = zoom_y = 1
                            
                        # render-crop: render just the clip of the image
                        # Render with alpha=True to preserve transparency.
                        # We trust PyMuPDF to handle SMasks correctly.
                        mat = fitz.Matrix(zoom_x, zoom_y)
                        pix = page.get_pixmap(matrix=mat, clip=rect, alpha=True)
                        
                        # Save image as PNG
                        filename = f"page{page_num + 1}_img{img_index}_{i}.png"
                        filepath = self.output_dir / filename
                        pix.save(filepath)
                        
                        # CRITICAL: Process image immediately after extraction
                        # This removes black backgrounds BEFORE any zoom-related artifacts
                        # Import here to avoid circular dependency
                        from .xml_parser.extractors import process_image
                        actual_width, actual_height = process_image(filepath, zoom_factor=1.0)
                        
                        # If process_image failed, use pixmap dimensions
                        if actual_width == 0 or actual_height == 0:
                            actual_width = pix.width
                            actual_height = pix.height
                        
                        # Convert coordinates to Bottom-Up (for xml_parser/extractors.py compatibility)
                        # PyMuPDF is Top-Left origin.
                        # y0 (bottom edge in bottom-up) = page_height - y1 (bottom edge in top-down)
                        # y1 (top edge in bottom-up) = page_height - y0 (top edge in top-down)
                        y0_bu = page_height - rect.y1
                        y1_bu = page_height - rect.y0
                        
                        # Store image info matching the expected format
                        # (filename, x0, y0, x1, y1, width, height)
                        page_images.append((
                            filename,
                            rect.x0,    # x0
                            y0_bu,      # y0 (bottom-up)
                            rect.x1,    # x1
                            y1_bu,      # y1 (bottom-up)
                            actual_width,
                            actual_height
                        ))
                    
                except Exception as e:
                    continue
            
            if page_images:
                self.images[page_num + 1] = page_images
        
        doc.close()
    
    def get_images_for_page(self, page_num: int) -> List[Tuple[str, float, float, float, float, int, int]]:
        """Get all images for a specific page."""
        return self.images.get(page_num, [])


# Example usage in pdf_service.py:
"""
# Replace this:
from .image_extractor import ImageExtractor

# With this:
from .image_extractor_pymupdf import ImageExtractorPyMuPDF as ImageExtractor

# The rest of the code remains the same
"""

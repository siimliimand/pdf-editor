from typing import Dict, List, Tuple
from pathlib import Path
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTImage, LTFigure
from PIL import Image
import io

from .processor import extract_image_data

class ImageExtractor:
    """
    Extract images directly from PDF using pdfminer.six.
    This bypasses pdftohtml's broken image extraction which loses color profiles and dimensions.
    """
    
    def __init__(self, pdf_path: str, output_dir: Path):
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True, parents=True)
        # Store extracted images: {page_num: [(filename, x0, y0, x1, y1, width, height)]}
        self.images: Dict[int, List[Tuple[str, float, float, float, float, int, int]]] = {}
        
    def extract(self):
        """Extract all images from the PDF."""
        for page_num, page_layout in enumerate(extract_pages(self.pdf_path), start=1):
            page_images = []
            self._extract_images_recursive(page_layout, page_images, page_num)
            if page_images:
                self.images[page_num] = page_images
    
    def _extract_images_recursive(self, element, images: list, page_num: int):
        """Recursively extract images from PDF layout elements."""
        if isinstance(element, LTImage):
            try:
                # Extract the image data
                img_data = extract_image_data(element)
                if img_data:
                    # Generate filename
                    img_count = len(images)
                    filename = f"page{page_num}_img{img_count}.png"
                    filepath = self.output_dir / filename
                    
                    # Save the image
                    with open(filepath, 'wb') as f:
                        f.write(img_data)
                    
                    # Get actual image dimensions
                    with Image.open(io.BytesIO(img_data)) as img:
                        actual_width, actual_height = img.size
                    
                    # Store: (filename, x0, y0, x1, y1, actual_width, actual_height)
                    images.append((
                        filename,
                        element.x0,
                        element.y0,
                        element.x1,
                        element.y1,
                        actual_width,
                        actual_height
                    ))
            except Exception as e:
        
        # Recurse into containers
        if isinstance(element, LTFigure) or hasattr(element, '__iter__'):
            try:
                for child in element:
                    self._extract_images_recursive(child, images, page_num)
            except:
                pass

    def get_images_for_page(self, page_num: int) -> List[Tuple[str, float, float, float, float, int, int]]:
        """Get all images for a specific page."""
        return self.images.get(page_num, [])

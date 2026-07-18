import xml.etree.ElementTree as ET
from typing import List, Tuple, Optional
from ..models import ImageElement

def extract_image_elements(
    page_node: ET.Element, 
    extracted_images: List[Tuple], 
    page_height: int, 
    zoom_factor: float
) -> List[ImageElement]:
    """
    Extracts image elements from the XML page node.
    Matches XML image positions with high-fidelity PyMuPDF extracted images via coordinate intersection.
    """
    elements: List[ImageElement] = []
    
    # Use directly extracted images instead of pdftohtml's broken ones
    extracted_images = extracted_images or []
    
    # Extract Images - match XML positions with directly extracted images
    for img_node in page_node.findall('image'):
        try:
            top = float(img_node.get('top', 0))
            left = float(img_node.get('left', 0))
            width = float(img_node.get('width', 0))
            height = float(img_node.get('height', 0))
            
            # Convert top-down coordinates to bottom-up for matching
            # pdfminer uses bottom-up (y0 at bottom), pdftohtml uses top-down (y0 at top)
            xml_y0_bottomup = page_height - top - height
            xml_y1_bottomup = page_height - top
            xml_x0 = left
            xml_x1 = left + width
            
            # Find matching extracted image by intersection
            matched_image = None
            best_overlap = 0.0
            
            for img_data in extracted_images:
                filename, img_x0, img_y0, img_x1, img_y1, actual_width, actual_height = img_data
                
                # CRITICAL FIX: Scale PyMuPDF coordinates to match XML zoom level
                # PyMuPDF extracts at native resolution (zoom=1.0)
                # XML coordinates are scaled by pdftohtml's -zoom parameter
                # We need to scale PyMuPDF coords to match: scaled = native * zoom_factor
                scaled_img_x0 = img_x0 * zoom_factor
                scaled_img_y0 = img_y0 * zoom_factor
                scaled_img_x1 = img_x1 * zoom_factor
                scaled_img_y1 = img_y1 * zoom_factor
                
                # Calculate intersection using scaled coordinates
                inter_x0 = max(xml_x0, scaled_img_x0)
                inter_y0 = max(xml_y0_bottomup, scaled_img_y0)
                inter_x1 = min(xml_x1, scaled_img_x1)
                inter_y1 = min(xml_y1_bottomup, scaled_img_y1)
                
                has_intersection = inter_x1 > inter_x0 and inter_y1 > inter_y0
                
                if has_intersection:
                    inter_area = (inter_x1 - inter_x0) * (inter_y1 - inter_y0)
                    
                    # Calculate Union (approximate using areas)
                    xml_area = (xml_x1 - xml_x0) * (xml_y1_bottomup - xml_y0_bottomup)
                    img_area = (scaled_img_x1 - scaled_img_x0) * (scaled_img_y1 - scaled_img_y0)
                    
                    # Use Intersection over Minimum Area to handle containment
                    overlap = inter_area / min(xml_area, img_area) if min(xml_area, img_area) > 0 else 0
                    
                    if overlap > 0.5 and overlap > best_overlap:
                        best_overlap = overlap
                        matched_image = img_data
            
            # Use matched image data if found
            if matched_image:
                filename, img_x0, img_y0, img_x1, img_y1, actual_width, actual_height = matched_image
                
                # Scale PyMuPDF coordinates to match XML zoom for display
                scaled_img_x0 = img_x0 * zoom_factor
                scaled_img_y0 = img_y0 * zoom_factor
                scaled_img_x1 = img_x1 * zoom_factor
                scaled_img_y1 = img_y1 * zoom_factor
                
                # Calculate display dimensions from scaled PDF layout (float precision)
                display_width = scaled_img_x1 - scaled_img_x0
                display_height = scaled_img_y1 - scaled_img_y0
                
                # Convert PyMuPDF position from bottom-up back to top-down for HTML
                # PyMuPDF: y0 is at bottom, y1 is at top (bottom-up)
                # HTML: top is measured from page top (top-down)
                # HTML top = page_height - PyMuPDF y1 (scaled)
                pymupdf_top = page_height - scaled_img_y1
                pymupdf_left = scaled_img_x0
                
                # Use PyMuPDF's scaled position and dimensions for accurate placement
                elements.append(ImageElement(
                    src=filename,
                    top=pymupdf_top,
                    left=pymupdf_left,
                    width=display_width if display_width > 0 else actual_width * zoom_factor,
                    height=display_height if display_height > 0 else actual_height * zoom_factor
                ))
            elif width > 0 and height > 0:
                # Fallback: No coordinate match found
                # Try to use any available PyMuPDF image (better than pdftohtml's broken images)
                if extracted_images:
                    # Use the first extracted image with XML positioning
                    # This is better than using pdftohtml's image which has black backgrounds
                    first_img = extracted_images[0]
                    filename, img_x0, img_y0, img_x1, img_y1, actual_width, actual_height = first_img
                    
                    elements.append(ImageElement(
                        src=filename,
                        top=top,  # Use XML position
                        left=left,
                        width=width,
                        height=height
                    ))
                else:
                    # Last resort: use pdftohtml's image
                    src = img_node.get('src', '')
                    if src:
                        elements.append(ImageElement(src=src, top=top, left=left, width=width, height=height))
                    
        except ValueError:
            continue
            
    return elements

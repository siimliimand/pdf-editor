import shutil
import re
import uuid
import subprocess
import aiofiles
from pathlib import Path
from typing import Tuple, Dict, Optional, Any

TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

def verify_pdftohtml_tool():
    """Verify that pdftohtml is installed and available in PATH."""
    if not shutil.which("pdftohtml"):
        raise RuntimeError("pdftohtml tool not found in PATH")

async def convert_pdf_to_html(pdf_content: bytes, zoom_level: float = 100.0) -> str:
    """
    Saves the PDF content to a temporary file, runs pdftohtml,
    and returns the generated HTML content with embedded fonts.
    
    Args:
        pdf_content: The PDF file content as bytes
        zoom_level: Zoom percentage (50-500), default 150
    """
    # Create a unique directory for this request to avoid collisions
    request_id = str(uuid.uuid4())
    request_temp_dir = TEMP_DIR / request_id
    request_temp_dir.mkdir(exist_ok=True)

    try:
        input_path = request_temp_dir / "input.pdf"

        # 1. Save uploaded file
        await _save_input_pdf(input_path, pdf_content)

        # 2. Extract and cache fonts FIRST (before pdftohtml)
        font_css, font_mapping = _extract_font_css(input_path)

        # 3. Calculate zoom factors
        requested_zoom_factor, pdftohtml_xml_scale = _calculate_zoom_factors(zoom_level)

        # 4. Run pdftohtml conversion
        xml_content = _run_pdftohtml(request_temp_dir, "input.pdf", pdftohtml_xml_scale)

        # 5. Extract images
        extracted_images = _extract_images(input_path, request_temp_dir)

        # 6. Extract fonts details
        extracted_fonts = _extract_fonts_details(input_path)

        # 7. Parse Vectors
        vector_data = _parse_vectors(input_path)

        # 8. Prepare XML for table detection (1.0x scale)
        xml_content_for_tables, table_detection_scale = _ensure_table_detection_xml(
            request_temp_dir, "input.pdf", xml_content, pdftohtml_xml_scale
        )

        # 9. Parse XML to semantic HTML Table
        html_content = _generate_html_content(
            xml_content_for_tables,
            request_temp_dir,
            vector_data,
            extracted_images,
            table_detection_scale,
            requested_zoom_factor,
            extracted_fonts,
            input_path,
            font_mapping
        )

        # 10. Inject font CSS
        if font_css:
            html_content = _inject_font_css(html_content, font_css)

        return html_content

    finally:
        # Cleanup
        shutil.rmtree(request_temp_dir, ignore_errors=True)


async def _save_input_pdf(input_path: Path, content: bytes):
    """Save the bytes content to the specified path asynchronously."""
    async with aiofiles.open(input_path, 'wb') as out_file:
        await out_file.write(content)


def _extract_font_css(input_path: Path) -> Tuple[str, Dict[str, Any]]:
    """Extract font CSS and mapping from the PDF."""
    try:
        from .font_embedder import FontEmbedder
        embedder = FontEmbedder()
        return embedder.process_pdf(str(input_path), use_cache=True)
    except Exception as e:
        print(f"⚠️  Font extraction failed: {e}")
        return "", {}


def _calculate_zoom_factors(zoom_level: float) -> Tuple[float, float]:
    """Calculate the requested zoom factor and the scale for pdftohtml XML generation."""
    # Apply standard DPI conversion (72 pt -> 96 px)
    requested_zoom_factor = (zoom_level / 100.0) * (96.0 / 72.0)
    
    # pdftohtml limits zoom to roughly 3.0 (300%)
    pdftohtml_xml_scale = min(requested_zoom_factor, 3.0)
    
    return requested_zoom_factor, pdftohtml_xml_scale


def _run_pdftohtml(working_dir: Path, input_filename: str, scale: float) -> str:
    """Run pdftohtml tool and return the XML output."""
    cmd = [
        "pdftohtml",
        "-xml",
        "-stdout",
        "-hidden",
        "-zoom", str(scale),
        input_filename
    ]
    
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=working_dir)

    if process.returncode != 0:
        error_msg = process.stderr.decode()
        raise Exception(f"PDF conversion failed: {error_msg}")

    return process.stdout.decode('utf-8')


def _extract_images(input_path: Path, output_dir: Path) -> Dict[str, Any]:
    """Extract images using PyMuPDF or fallback to pdfminer."""
    try:
        try:
            from .image_extractor_pymupdf import ImageExtractorPyMuPDF as ImageExtractor
        except ImportError:
            # Fallback
            from .image_extractor import ImageExtractor
        
        img_extractor = ImageExtractor(str(input_path), output_dir)
        img_extractor.extract()
        return img_extractor.images
    except Exception:
        return {}


def _extract_fonts_details(input_path: Path) -> Optional[Any]:
    """Extract font details using PyMuPDF."""
    from .font_extractor import FontExtractorPyMuPDF
    try:
        font_extractor = FontExtractorPyMuPDF(str(input_path))
        font_extractor.extract()
        return font_extractor
    except Exception:
        return None


def _parse_vectors(input_path: Path) -> Dict[str, Any]:
    """Parse vector graphics (lines/rects) from the PDF."""
    from .vector_parser import VectorParser
    try:
        vector_parser = VectorParser(str(input_path))
        vector_parser.parse()
        return vector_parser.pages
    except Exception:
        return {}


def _ensure_table_detection_xml(
    working_dir: Path, 
    input_filename: str, 
    current_xml: str, 
    current_scale: float
) -> Tuple[str, float]:
    """
    Ensure we have XML at 1.0x scale for table detection.
    Returns (xml_content, scale).
    """
    if current_scale == 1.0:
        return current_xml, 1.0
        
    try:
        # Run again at 1.0x
        xml_1x = _run_pdftohtml(working_dir, input_filename, 1.0)
        return xml_1x, 1.0
    except Exception:
        # Fallback to current if failed
        return current_xml, current_scale


def _generate_html_content(
    xml_content: str,
    temp_dir: Path,
    vector_data: Dict,
    extracted_images: Dict,
    table_scale: float,
    requested_zoom_factor: float,
    extracted_fonts: Any,
    input_path: Path,
    font_mapping: Dict
) -> str:
    """Parse XML and generate the final HTML."""
    from .xml_parser import parse_xml_to_html
    
    return parse_xml_to_html(
        xml_content,  # Use 1.0x XML for table detection
        temp_dir, 
        vector_data, 
        extracted_images, 
        table_scale,  # Scale used for table detection
        requested_zoom_factor / table_scale,  # Additional scale to reach requested zoom
        extracted_fonts,
        str(input_path),
        font_mapping
    )


def _inject_font_css(html_content: str, font_css: str) -> str:
    """
    Inject font CSS into HTML content.
    
    Adds a <style> tag with @font-face declarations at the beginning of the HTML.
    """
    # Wrap font CSS in style tag
    style_tag = f"""<style>
/* Embedded PDF Fonts */
{font_css}
</style>
"""
    
    # Find the first div or body tag and inject before it
    # Look for the first opening tag
    import re
    match = re.search(r'<(div|body|html)', html_content, re.IGNORECASE)
    
    if match:
        insert_pos = match.start()
        html_content = html_content[:insert_pos] + style_tag + html_content[insert_pos:]
    else:
        # Fallback: prepend to content
        html_content = style_tag + html_content
    
    return html_content


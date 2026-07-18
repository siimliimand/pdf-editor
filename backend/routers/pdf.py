from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from services.pdf_service import convert_pdf_to_html
from typing import Optional

router = APIRouter()

@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    zoom: Optional[str] = Form("100")
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        # Parse zoom level
        try:
            zoom_level = float(zoom)
            # Validate zoom range (50% to 500%)
            if zoom_level < 50 or zoom_level > 500:
                zoom_level = 100.0
        except (ValueError, TypeError):
            zoom_level = 100.0
        
        content = await file.read()
        html_content = await convert_pdf_to_html(content, zoom_level)
        return JSONResponse(content={"html": html_content})

    except Exception as e:
        # If the error is ours (e.g. conversion failed), we might want to return 500.
        # Ideally, we'd have custom exceptions in service so we can decide status code.
        # But for now 500 is safe for generic exceptions.
        raise HTTPException(status_code=500, detail=str(e))


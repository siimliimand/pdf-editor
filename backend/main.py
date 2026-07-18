from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import pdf, health
from services.pdf_service import verify_pdftohtml_tool

app = FastAPI()

# Configure CORS
origins = [
    "*"  # Allow all origins for now, strict down later if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Ensure pdftohtml is available
    verify_pdftohtml_tool()

app.include_router(pdf.router)
app.include_router(health.router)

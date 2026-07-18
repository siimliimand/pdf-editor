## Why

The PDF Editor project has a working implementation but lacks formal OpenSpec documentation. Creating comprehensive specs based on the existing code will establish a baseline for future development, enable better onboarding, and provide a contract for testing and validation.

## What Changes

- Create formal OpenSpec specifications for all existing components and capabilities
- Document the current architecture, APIs, and data flows as executable specifications
- Establish a baseline for future feature development and regression testing

## Capabilities

### New Capabilities
- `pdf-upload-conversion`: PDF file upload and server-side conversion to semantic HTML
- `font-extraction-embedding`: Font extraction from PDFs and CSS @font-face embedding
- `image-extraction`: Image extraction from PDFs and embedding as base64 data
- `vector-graphics-parsing`: Vector element parsing and rendering
- `table-detection`: Table structure detection and grid-based rendering
- `rich-text-editing`: Tiptap-based rich text editor with PDF-aware extensions
- `chrome-extension-integration`: Chrome Manifest V3 extension with service worker

### Modified Capabilities

(No existing specs to modify - this is initial documentation)

## Impact

- All backend services (FastAPI, pdftohtml integration, PyMuPDF, pdfminer)
- All frontend components (React, Tiptap editor, Chrome extension APIs)
- API contract (POST /upload endpoint)
- Data stores (font cache, temp files, Chrome storage)
- External dependencies (Poppler, PyMuPDF, pdfminer.six)
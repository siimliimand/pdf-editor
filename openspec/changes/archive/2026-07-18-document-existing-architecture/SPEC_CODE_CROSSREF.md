# Specification-to-Code Cross-Reference

This document maps each OpenSpec specification to the implementing code files.

## 1. pdf-upload-conversion

| Requirement | Code File | Function/Class |
|-------------|-----------|----------------|
| PDF file upload endpoint | `backend/routers/pdf.py` | `upload_pdf()` |
| PDF to HTML conversion pipeline | `backend/services/pdf_service.py` | `convert_pdf_to_html()` |
| Temporary file management | `backend/services/pdf_service.py` | `TEMP_DIR`, UUID-based directories |

## 2. font-extraction-embedding

| Requirement | Code File | Function/Class |
|-------------|-----------|----------------|
| Font extraction from PDF | `backend/services/font_embedder.py` | `FontEmbedder.extract_fonts_from_pdf()` |
| Font caching | `backend/services/font_cache.py` | `get_font_cache()`, SHA-256 hashing |
| Font-face CSS generation | `backend/services/font_embedder.py` | `FontEmbedder.create_font_face_css()` |
| Font metadata extraction | `backend/services/font_embedder.py` | `FontEmbedder.get_font_weight_from_name()`, `get_font_style_from_name()` |

## 3. image-extraction

| Requirement | Code File | Function/Class |
|-------------|-----------|----------------|
| Image extraction from PDF | `backend/services/image_extractor_pymupdf.py` | `ImageExtractorPyMuPDF` |
| Image embedding in HTML | `backend/services/xml_parser/` | Base64 encoding in renderers |

## 4. vector-graphics-parsing

| Requirement | Code File | Function/Class |
|-------------|-----------|----------------|
| Vector element parsing | `backend/services/vector_parser.py` | `VectorParser.parse()` |
| Vector element data | `backend/services/vector_parser.py` | `VectorElement` dataclass |
| Vector rendering in HTML | `backend/services/xml_parser/renderers/` | SVG/CSS rendering |

## 5. table-detection

| Requirement | Code File | Function/Class |
|-------------|-----------|----------------|
| Table structure detection | `backend/services/xml_parser/table_detector/` | Line clustering, cell merging |
| Table rendering | `backend/services/xml_parser/renderers/` | Grid table renderer |
| Table detection at 1.0x zoom | `backend/services/pdf_service.py` | `_ensure_table_detection_xml()` |

## 6. rich-text-editing

| Requirement | Code File | Function/Class |
|-------------|-----------|----------------|
| Tiptap editor integration | `extension/src/components/RichTextEditor/RichTextEditor.tsx` | `RichTextEditor` component |
| Custom Tiptap extensions | `extension/src/components/RichTextEditor/extensions.ts` | Div, Span, ExtendedParagraph, Table extensions |
| Editor toolbar | `extension/src/components/EditorToolbar.tsx` | Zoom controls, file name display |

## 7. chrome-extension-integration

| Requirement | Code File | Function/Class |
|-------------|-----------|----------------|
| Chrome extension manifest | `extension/public/manifest.json` | Manifest V3 configuration |
| Service worker | `extension/src/service_worker.ts` | `chrome.action.onClicked` listener |
| Editor tab management | `extension/src/service_worker.ts` | `chrome.tabs.create()` |
| Chrome storage integration | `extension/src/util.ts` | Chrome storage helpers |

## Cross-Cutting Concerns

| Concern | Code Files |
|---------|------------|
| State management | `extension/src/hooks/usePdfEditor.ts` |
| API client | `extension/src/services/pdfService.ts` |
| XML parsing engine | `backend/services/xml_parser/` |
| Data models | `backend/services/xml_parser/models.py` |

---

*Last updated: 2026-07-18*

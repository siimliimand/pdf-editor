# Project History: PDF Editor

## What This Project Is

A browser-based PDF editor built as a Chrome extension with a Python/FastAPI backend. It allows users to view, edit, and annotate PDF documents directly in their browser, with features including text editing, zoom control, image extraction, font embedding, and vector element parsing.

The project is split into two main components:
- **extension/** — A React + TypeScript Chrome extension using Vite, Tailwind CSS v4, and Tiptap (rich text editor). Builds into a packaged `.zip` for Chrome Web Store distribution.
- **backend/** — A FastAPI (Python) server that handles PDF-to-HTML conversion using `pdftohtml`, with support for zoom levels, font extraction/embedding, image extraction (via PyMuPDF), and XML/vector parsing.

## Key Decisions Already Made

1. **FastAPI over Flask/Django** — The backend uses FastAPI with async handlers, suggesting a preference for modern async Python and automatic OpenAPI docs.
2. **pdftohtml as core conversion** — The backend shells out to `pdftohtml` (Poppler tool) for PDF-to-HTML conversion, rather than using a pure-Python library like PyPDF2. This gives better layout fidelity but adds a system dependency.
3. **Tiptap for rich text editing** — The extension uses Tiptap (ProseMirror-based) for in-browser text editing of converted PDF content, with extensions for tables, images, links, color, underline, and text styles.
4. **Tailwind CSS v4 with Vite plugin** — Uses `@tailwindcss/vite` (v4) rather than PostCSS, indicating a move to the newer Tailwind architecture.
5. **Chrome extension architecture** — The extension has an `editor.html`, `options.html`, a service worker (`service_worker.ts`), and builds to `dist/` then zips for distribution.
6. **Zoom handled server-side** — Zoom level is passed as a parameter to the backend, which renders the PDF at the requested zoom before returning HTML.
7. **Font embedding pipeline** — A dedicated service handles font extraction, caching, and embedding to ensure text renders correctly across platforms.
8. **Image extraction via PyMuPDF** — Separate from the main pdftohtml pipeline, images are extracted using PyMuPDF for better quality.
9. **Vector parsing** — A dedicated service parses vector elements (lines, curves, shapes) from the PDF XML output.
10. **CORS wide open** — Currently allows all origins (`*`), flagged for future tightening.

## Known Tech Debt and Constraints

- **CORS wildcard** — `allow_origins=["*"]` is noted as temporary; needs restriction before production.
- **No authentication** — The backend has no auth layer; any client can upload PDFs.
- **No rate limiting** — Upload endpoint has no size or frequency limits beyond file content type check.
- **System dependency on pdftohtml** — Requires Poppler utilities installed on the server.
- **Test infrastructure exists but is minimal** — `backend/tests/` directory exists with analysis docs but limited automated test coverage visible.
- **No CI/CD pipeline visible** — No GitHub Actions or similar configured in the repo root.
- **docs/ folder is debug-oriented** — Contains zoom and black background debugging analysis, not user-facing documentation.
- **Two separate git repos** — `backend/.git/` and `extension/.git/` exist as independent repos, plus the root may be its own. This monorepo structure may cause issues with tools expecting a single git root.

## Current State

The project is functional with a working backend that converts PDFs to HTML and a Chrome extension frontend for viewing and editing. Recent development focus has been on:
- Zoom feature implementation and testing (multiple analysis docs in `docs/`)
- Black background rendering fix (multiple analysis/fix docs)
- Table row handling in the editor
- Font embedding reliability

The codebase is at an early-to-mid stage — core features work, but there's no packaging, deployment automation, or comprehensive test suite yet.

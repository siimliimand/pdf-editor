## 1. Project Setup

- [x] 1.1 Create ts-backend/ directory structure (src/services, src/routers, src/models, src/utils) <!-- agent: basic-engineer.build, depends_on: [], touches: [ts-backend/**] -->
- [x] 1.2 Initialize package.json with dependencies (pdf.js, hono, lru-cache, @cloudflare/workers-types) <!-- agent: basic-engineer.build, depends_on: [1.1], touches: [ts-backend/package.json] -->
- [x] 1.3 Create tsconfig.json with strict mode, Workers target <!-- agent: basic-engineer.build, depends_on: [1.1], touches: [ts-backend/tsconfig.json] -->
- [x] 1.4 Create wrangler.toml with Workers config, R2 binding, dev config <!-- agent: basic-engineer.build, depends_on: [1.2], touches: [ts-backend/wrangler.toml] -->
- [x] 1.5 Create src/index.ts Hono app entry point with CORS and routes <!-- agent: basic-engineer.build, depends_on: [1.2], touches: [ts-backend/src/index.ts] -->

## 2. Data Models

- [x] 2.1 Create src/models/types.ts with TypeScript interfaces (FontSpec, TextElement, ImageElement, VectorElement, TableCell, TableDefinition, TableRow) <!-- agent: basic-engineer.build, depends_on: [1.1], touches: [ts-backend/src/models/types.ts] -->
- [x] 2.2 Create src/models/constants.ts with all pipeline constants (zoom limits, tolerances, font mappings) <!-- agent: basic-engineer.build, depends_on: [2.1], touches: [ts-backend/src/models/constants.ts] -->

## 3. Core PDF Service

- [x] 3.1 Create src/services/pdf-service.ts orchestrator (equivalent to pdf_service.py) — handles request lifecycle: parse PDF → extract fonts → extract images → parse vectors → detect tables → generate HTML <!-- agent: basic-engineer.build, depends_on: [2.1], touches: [ts-backend/src/services/pdf-service.ts] -->
- [x] 3.2 Implement request ID generation and in-memory temp buffer management (no filesystem) <!-- agent: basic-engineer.build, depends_on: [3.1], touches: [ts-backend/src/services/pdf-service.ts] -->

## 4. Font Extraction & Embedding

- [x] 4.1 Create src/services/font-extractor.ts — extract font metadata from pdf.js page fonts (name, weight, flags, encoding) <!-- agent: basic-engineer.build, depends_on: [2.1], touches: [ts-backend/src/services/font-extractor.ts] -->
- [x] 4.2 Create src/services/font-embedder.ts — generate base64 @font-face CSS from extracted fonts, with font name → CSS family mapping <!-- agent: basic-engineer.build, depends_on: [4.1], touches: [ts-backend/src/services/font-embedder.ts] -->
- [x] 4.3 Create src/services/font-cache.ts — LRU in-memory cache with optional R2 persistence, SHA-256 hash keys <!-- agent: basic-engineer.build, depends_on: [4.2], touches: [ts-backend/src/services/font-cache.ts] -->
- [x] 4.4 Implement font weight detection from name heuristics (bold→700, light→300, etc.) <!-- agent: basic-engineer.build, depends_on: [4.1], touches: [ts-backend/src/services/font-extractor.ts] -->

## 5. Image Extraction

- [x] 5.1 Create src/services/image-extractor.ts — extract images from pdf.js page operations, handle CMYK→RGB conversion, transparency <!-- agent: basic-engineer.build, depends_on: [2.1], touches: [ts-backend/src/services/image-extractor.ts] -->
- [x] 5.2 Implement image position matching — map pdf.js image positions to text coordinates for correct HTML placement <!-- agent: basic-engineer.build, depends_on: [5.1], touches: [ts-backend/src/services/image-extractor.ts] -->

## 6. Vector Graphics Parsing

- [x] 6.1 Create src/services/vector-parser.ts — extract vector elements from pdf.js path commands (moveTo, lineTo, curveTo, rectangle) <!-- agent: basic-engineer.build, depends_on: [2.1], touches: [ts-backend/src/services/vector-parser.ts] -->
- [x] 6.2 Implement coordinate conversion (pdf.js uses top-down, match Python version's flip logic) <!-- agent: basic-engineer.build, depends_on: [6.1], touches: [ts-backend/src/services/vector-parser.ts] -->
- [x] 6.3 Implement VectorElement properties: is_horizontal, is_vertical, width, height, dash detection <!-- agent: basic-engineer.build, depends_on: [6.2], touches: [ts-backend/src/services/vector-parser.ts] -->

## 7. Table Detection

- [x] 7.1 Create src/services/table-detector.ts — main table detection orchestrator with 3 strategies <!-- agent: basic-engineer.build, depends_on: [6.1], touches: [ts-backend/src/services/table-detector.ts] -->
- [x] 7.2 Implement vector-based grid table detection (cluster H/V lines, build grid, merge cells) <!-- agent: basic-engineer.build, depends_on: [7.1], touches: [ts-backend/src/services/table-detector.ts] -->
- [x] 7.3 Implement horizontal-line-only table detection (infer columns from text gaps) <!-- agent: basic-engineer.build, depends_on: [7.2], touches: [ts-backend/src/services/table-detector.ts] -->
- [x] 7.4 Implement table merging (adjacent tables within threshold, legacy table gap merging) <!-- agent: basic-engineer.build, depends_on: [7.1], touches: [ts-backend/src/services/table-merger.ts] -->

## 8. HTML Rendering

- [x] 8.1 Create src/services/html-renderer.ts — render page blocks to HTML (grid tables, legacy tables, text blocks) <!-- agent: basic-engineer.build, depends_on: [7.1, 4.2], touches: [ts-backend/src/services/html-renderer.ts] -->
- [x] 8.2 Implement grid table renderer with colgroup widths and data-col-widths attribute <!-- agent: basic-engineer.build, depends_on: [8.1], touches: [ts-backend/src/services/renderers/grid-table.ts] -->
- [x] 8.3 Implement text block renderer with absolute positioning and background colors <!-- agent: basic-engineer.build, depends_on: [8.1], touches: [ts-backend/src/services/renderers/text-block.ts] -->
- [x] 8.4 Implement legacy table renderer for absolute-positioned tables <!-- agent: basic-engineer.build, depends_on: [8.1], touches: [ts-backend/src/services/renderers/legacy-table.ts] -->
- [x] 8.5 Implement per-cell rendering: padding calculation, alignment detection, font styles, inline images <!-- agent: basic-engineer.build, depends_on: [8.2], touches: [ts-backend/src/services/renderers/cell-renderer.ts] -->

## 9. API Routes

- [x] 9.1 Create src/routers/pdf.ts — POST /upload endpoint with multipart parsing, zoom validation, error handling <!-- agent: basic-engineer.build, depends_on: [3.1], touches: [ts-backend/src/routers/pdf.ts] -->
- [x] 9.2 Create src/routers/health.ts — GET /health endpoint <!-- agent: basic-engineer.fast, depends_on: [1.5], touches: [ts-backend/src/routers/health.ts] -->

## 10. Cloudflare Deployment

- [x] 10.1 Configure R2 bucket binding in wrangler.toml for font cache <!-- agent: basic-engineer.build, depends_on: [1.4], touches: [ts-backend/wrangler.toml] -->
- [x] 10.2 Implement R2 font cache adapter (read/write/delete) in font-cache.ts <!-- agent: basic-engineer.build, depends_on: [4.3, 10.1], touches: [ts-backend/src/services/font-cache.ts] -->
- [x] 10.3 Add wrangler dev script and verify local development works <!-- agent: basic-engineer.fast, depends_on: [9.1], touches: [ts-backend/package.json] -->

## 11. Testing & Validation

- [x] 11.1 Create test PDFs and expected HTML outputs for comparison <!-- agent: basic-engineer.build, depends_on: [9.1], touches: [ts-backend/tests/**] -->
- [x] 11.2 Implement side-by-side comparison tool: Python output vs TypeScript output <!-- agent: basic-engineer.build, depends_on: [11.1], touches: [ts-backend/tests/compare.ts] -->
- [x] 11.3 Run comparison on key test cases and fix discrepancies <!-- agent: basic-engineer.build, depends_on: [11.2], touches: [ts-backend/src/**/*.ts] -->
- [x] 11.4 Verify all 15 test PDFs produce equivalent HTML output <!-- agent: basic-engineer.build, depends_on: [11.3], touches: [] -->

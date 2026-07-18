/**
 * PDF Service — Orchestrator for PDF-to-HTML conversion.
 *
 * Handles the full request lifecycle:
 *   parse PDF → extract fonts → extract images → parse vectors → detect tables → generate HTML
 *
 * All temporary data lives in memory (no filesystem). Each request is keyed by a UUID.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface FontData {
  fontName: string;
  fontFamily: string;
  fontWeight: string;
  fontStyle: string;
  src?: string; // data-URI or URL for @font-face
}

export interface ExtractedImage {
  id: string;
  width: number;
  height: number;
  data: Uint8Array;
  mimeType: string;
}

export interface VectorPath {
  d: string; // SVG path data
  fill?: string;
  stroke?: string;
  strokeWidth?: number;
}

export interface TableRegion {
  x: number;
  y: number;
  width: number;
  height: number;
  rows: number;
  cols: number;
  cells: TableCell[][];
}

export interface TableCell {
  x: number;
  y: number;
  width: number;
  height: number;
  content: string;
}

export interface PdfParseResult {
  totalPages: number;
  pages: PageData[];
}

export interface PageData {
  pageNumber: number;
  width: number;
  height: number;
  textItems: TextItem[];
  fonts: FontData[];
  images: ExtractedImage[];
  vectors: VectorPath[];
  tables: TableRegion[];
}

export interface TextItem {
  str: string;
  transform: [number, number, number, number, number, number];
  width: number;
  height: number;
  fontName: string;
}

export interface ConversionOptions {
  zoomLevel?: number;
}

export interface ConversionResult {
  html: string;
  requestId: string;
}

// ---------------------------------------------------------------------------
// Request Buffer Manager (Task 3.2)
// ---------------------------------------------------------------------------

/**
 * Per-request temporary data store.
 *
 * Cloudflare Workers have no writable filesystem, so all intermediate data
 * (parsed PDF, extracted images, fonts, vectors) lives in memory keyed by
 * request ID.
 */
class RequestBufferManager {
  private buffers = new Map<string, RequestBuffer>();

  /**
   * Allocate a new buffer for a request and return its ID.
   */
  create(requestId: string): RequestBuffer {
    const buffer: RequestBuffer = {
      requestId,
      pdfBytes: null,
      parseResult: null,
      fonts: [],
      images: [],
      vectors: [],
      tables: [],
      html: null,
    };
    this.buffers.set(requestId, buffer);
    return buffer;
  }

  /**
   * Retrieve the buffer for a request (or undefined if already cleaned up).
   */
  get(requestId: string): RequestBuffer | undefined {
    return this.buffers.get(requestId);
  }

  /**
   * Remove all data associated with a request. Safe to call multiple times.
   */
  cleanup(requestId: string): void {
    const buffer = this.buffers.get(requestId);
    if (!buffer) return;

    // Null out references so GC can collect large blobs sooner.
    buffer.pdfBytes = null;
    buffer.parseResult = null;
    buffer.fonts = [];
    buffer.images = [];
    buffer.vectors = [];
    buffer.tables = [];
    buffer.html = null;

    this.buffers.delete(requestId);
  }

  /**
   * Number of active requests (useful for diagnostics / memory pressure).
   */
  get activeCount(): number {
    return this.buffers.size;
  }
}

export interface RequestBuffer {
  requestId: string;
  pdfBytes: Uint8Array | null;
  parseResult: PdfParseResult | null;
  fonts: FontData[];
  images: ExtractedImage[];
  vectors: VectorPath[];
  tables: TableRegion[];
  html: string | null;
}

// Singleton — Workers are single-process, so a module-level Map is fine.
const bufferManager = new RequestBufferManager();

// ---------------------------------------------------------------------------
// Helpers (Task 3.2)
// ---------------------------------------------------------------------------

/**
 * Generate a request ID. Uses the Web Crypto API available in Workers.
 */
export function generateRequestId(): string {
  return crypto.randomUUID();
}

/**
 * Convenience: clean up a request's buffer after processing.
 */
export function cleanupRequest(requestId: string): void {
  bufferManager.cleanup(requestId);
}

// ---------------------------------------------------------------------------
// Stub service functions (Task 3.1)
//
// Each stub returns an empty result. The actual implementations will be wired
// in by their respective tasks (font-extractor, image-extractor, etc.).
// ---------------------------------------------------------------------------

/** Stub: parse the PDF with pdf.js. */
async function parsePdf(
  _pdfBytes: Uint8Array,
  _options?: ConversionOptions,
): Promise<PdfParseResult> {
  // TODO: Implement with pdfjs-dist (Task 4.x)
  return { totalPages: 0, pages: [] };
}

/** Stub: extract font CSS and mappings from parsed data. */
function extractFonts(_parseResult: PdfParseResult): FontData[] {
  // TODO: Implement (Task 5.x)
  return [];
}

/** Stub: extract embedded images. */
function extractImages(_parseResult: PdfParseResult): ExtractedImage[] {
  // TODO: Implement (Task 6.x)
  return [];
}

/** Stub: parse vector paths (SVG overlays). */
function parseVectors(_parseResult: PdfParseResult): VectorPath[] {
  // TODO: Implement (Task 7.x)
  return [];
}

/** Stub: detect table regions. */
function detectTables(_parseResult: PdfParseResult): TableRegion[] {
  // TODO: Implement (Task 8.x)
  return [];
}

/** Stub: generate the final HTML string from all extracted data. */
function generateHtml(
  _parseResult: PdfParseResult,
  _fonts: FontData[],
  _images: ExtractedImage[],
  _vectors: VectorPath[],
  _tables: TableRegion[],
  _zoomLevel: number,
): string {
  // TODO: Implement (Task 9.x)
  return '';
}

/** Stub: inject @font-face CSS rules into the HTML. */
function injectFontCss(html: string, fonts: FontData[]): string {
  if (fonts.length === 0) return html;

  const fontFaces = fonts
    .map(
      (f) =>
        `@font-face { font-family: '${f.fontFamily}'; font-weight: ${f.fontWeight}; font-style: ${f.fontStyle}; src: ${f.src ?? 'local()'}; }`,
    )
    .join('\n');

  const styleTag = `<style>\n${fontFaces}\n</style>`;

  // Insert before </head> if present, otherwise prepend.
  const headClose = html.indexOf('</head>');
  if (headClose !== -1) {
    return html.slice(0, headClose) + styleTag + '\n' + html.slice(headClose);
  }
  return styleTag + '\n' + html;
}

// ---------------------------------------------------------------------------
// Orchestrator (Task 3.1)
// ---------------------------------------------------------------------------

/**
 * Convert a PDF to an HTML representation.
 *
 * This is the main entry point. It orchestrates the full pipeline:
 *   1. Generate request ID + allocate buffer
 *   2. Parse PDF (pdf.js)
 *   3. Extract fonts, images, vectors
 *   4. Detect tables
 *   5. Generate HTML
 *   6. Inject font CSS
 *   7. Clean up buffer
 *   8. Return HTML
 */
export async function convertPdfToHtml(
  pdfBytes: Uint8Array,
  options: ConversionOptions = {},
): Promise<ConversionResult> {
  const zoomLevel = options.zoomLevel ?? 100.0;
  const requestId = generateRequestId();
  const buffer = bufferManager.create(requestId);

  try {
    // Store raw PDF bytes in buffer.
    buffer.pdfBytes = pdfBytes;

    // 1. Parse PDF.
    const parseResult = await parsePdf(pdfBytes, { zoomLevel });
    buffer.parseResult = parseResult;

    // 2. Extract font data.
    const fonts = extractFonts(parseResult);
    buffer.fonts = fonts;

    // 3. Extract images.
    const images = extractImages(parseResult);
    buffer.images = images;

    // 4. Parse vectors.
    const vectors = parseVectors(parseResult);
    buffer.vectors = vectors;

    // 5. Detect tables.
    const tables = detectTables(parseResult);
    buffer.tables = tables;

    // 6. Generate HTML.
    let html = generateHtml(parseResult, fonts, images, vectors, tables, zoomLevel);
    buffer.html = html;

    // 7. Inject @font-face CSS.
    html = injectFontCss(html, fonts);
    buffer.html = html;

    return { html, requestId };
  } finally {
    // Always clean up, even if the pipeline throws.
    bufferManager.cleanup(requestId);
  }
}

/**
 * PDF Service — Orchestrator for PDF-to-HTML conversion.
 *
 * Handles the full request lifecycle using real pdf.js and service modules:
 *   parse PDF → extract fonts → extract images → parse vectors → detect tables → render HTML
 *
 * All temporary data lives in memory (no filesystem). Each request is keyed by a UUID.
 */

import { getDocument } from "pdfjs-dist";
import type { PDFDocumentProxy, PDFPageProxy, TextItem } from "pdfjs-dist/types/src/display/api";

import type {
  FontSpec,
  TextElement,
  ImageElement,
  VectorElement,
  TableDefinition,
} from "../models/types";
import { ZOOM } from "../models/constants";

import { extractFontsFromPdfjsDoc } from "./font-extractor";
import { extractImagesFromPage } from "./image-extractor";
import { extractVectorsFromPage } from "./vector-parser";
import { detectTables as detectTablesFromVectors } from "./table-detector";
import { renderPageToHtml } from "./html-renderer";
import { mergeAdjacentTables } from "./table-merger";
import { mapImagesToPagePositions } from "./image-position";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ExtractedImage {
  id: string;
  width: number;
  height: number;
  data: Uint8Array;
  mimeType: string;
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

  create(requestId: string): RequestBuffer {
    const buffer: RequestBuffer = {
      requestId,
      pdfBytes: null,
      doc: null,
      fonts: [],
      images: [],
      vectors: [],
      tables: [],
      html: null,
    };
    this.buffers.set(requestId, buffer);
    return buffer;
  }

  get(requestId: string): RequestBuffer | undefined {
    return this.buffers.get(requestId);
  }

  cleanup(requestId: string): void {
    const buffer = this.buffers.get(requestId);
    if (!buffer) return;

    buffer.pdfBytes = null;
    buffer.doc = null;
    buffer.fonts = [];
    buffer.images = [];
    buffer.vectors = [];
    buffer.tables = [];
    buffer.html = null;

    this.buffers.delete(requestId);
  }

  get activeCount(): number {
    return this.buffers.size;
  }
}

export interface RequestBuffer {
  requestId: string;
  pdfBytes: Uint8Array | null;
  doc: PDFDocumentProxy | null;
  fonts: FontSpec[];
  images: ExtractedImage[];
  vectors: VectorElement[];
  tables: TableDefinition[];
  html: string | null;
}

// Singleton — Workers are single-process, so a module-level Map is fine.
const bufferManager = new RequestBufferManager();

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

export function generateRequestId(): string {
  return crypto.randomUUID();
}

export function cleanupRequest(requestId: string): void {
  bufferManager.cleanup(requestId);
}

// ---------------------------------------------------------------------------
// Text extraction (pdf.js TextItem → TextElement)
// ---------------------------------------------------------------------------

/**
 * Convert pdf.js TextItems into TextElement objects for the HTML renderer.
 *
 * pdf.js TextItems contain raw string + transform matrix.  We derive
 * position (top, left), dimensions (width, height), and font metadata
 * from the transform matrix and font name.
 */
function extractTextElements(
  items: Array<TextItem>,
  styles: Record<string, { fontFamily?: string; fontSize?: number; fontWeight?: number }>,
  fonts: FontSpec[],
): TextElement[] {
  const fontById = new Map<string, FontSpec>();
  for (const f of fonts) {
    fontById.set(f.id, f);
  }

  const elements: TextItem[] = [];
  for (const item of items) {
    if (!("str" in item) || !item.str) continue;
    elements.push(item as TextItem);
  }

  const textElements: TextElement[] = [];

  for (const item of elements) {
    const [, , , , tx, ty] = item.transform;
    const fontSpec = fontById.get(item.fontName) ?? null;

    textElements.push({
      type: "text",
      text: item.str,
      top: ty,
      left: tx,
      width: item.width,
      height: item.height,
      font_spec: fontSpec,
      font_size: item.height,
    });
  }

  return textElements;
}

// ---------------------------------------------------------------------------
// Orchestrator
// ---------------------------------------------------------------------------

/**
 * Convert a PDF to an HTML representation.
 *
 * Pipeline:
 *   1. Parse PDF with pdf.js → PDFDocumentProxy
 *   2. Extract fonts (document-wide deduplication)
 *   3. For each page: extract images, vectors, text
 *   4. Detect tables from vectors + text
 *   5. Map images to page positions
 *   6. Render each page to HTML
 *   7. Assemble multi-page output
 *   8. Inject @font-face CSS
 *   9. Clean up and return
 */
export async function convertPdfToHtml(
  pdfBytes: Uint8Array,
  options: ConversionOptions = {},
): Promise<ConversionResult> {
  const zoomLevel = options.zoomLevel ?? ZOOM.DEFAULT;
  const requestId = generateRequestId();
  const buffer = bufferManager.create(requestId);

  try {
    buffer.pdfBytes = pdfBytes;

    // 1. Parse PDF with pdf.js.
    const loadingTask = getDocument({ data: pdfBytes });
    const doc = await loadingTask.promise;
    buffer.doc = doc;

    // 2. Extract fonts (all pages, deduplicated).
    const fonts = await extractFontsFromPdfjsDoc(doc);
    buffer.fonts = fonts;

    // 3. Process each page.
    const pageHtmls: string[] = [];

    for (let pageNum = 1; pageNum <= doc.numPages; pageNum++) {
      const page = await doc.getPage(pageNum);
      const viewport = page.getViewport({ scale: 1.0 });
      const pageWidth = viewport.width;
      const pageHeight = viewport.height;

      // 3a. Extract images.
      const images = await extractImagesFromPage(page, pageNum);

      // 3b. Extract vectors.
      const vectors = await extractVectorsFromPage(page, pageNum);

      // 3c. Extract text content for table detection and rendering.
      const textContent = await page.getTextContent();
      const textItems = textContent.items as TextItem[];
      const textElements = extractTextElements(textItems, textContent.styles as Record<string, { fontFamily?: string; fontSize?: number; fontWeight?: number }>, fonts);

      // 4. Detect tables from vectors + text.
      let tables = detectTablesFromVectors(vectors, textElements);
      tables = mergeAdjacentTables(tables);

      // 5. Map images to page positions.
      const imageElements = mapImagesToPagePositions(
        images,
        images.map((img) => ({ id: img.id, ctm: [1, 0, 0, 1, 0, 0] as [number, number, number, number, number, number] })),
        pageWidth,
        pageHeight,
      );

      // Collect all extracted data for diagnostics.
      buffer.images.push(...images);
      buffer.vectors.push(...vectors);
      buffer.tables.push(...tables);

      // 6. Render page to HTML.
      const pageHtml = renderPageToHtml({
        textElements,
        images: imageElements,
        tables,
        vectors,
        pageWidth,
        pageHeight,
        zoomLevel,
        fontMapping: new Map(fonts.map((f) => [f.id, f.family])),
      });

      pageHtmls.push(pageHtml);
    }

    // 7. Assemble multi-page HTML.
    const pagesContent = pageHtmls
      .map((html) => {
        // Extract just the inner content from each page's full HTML.
        const bodyStart = html.indexOf('<div class="page-container">');
        const bodyEnd = html.lastIndexOf("</div>");
        if (bodyStart !== -1 && bodyEnd !== -1) {
          return html.slice(bodyStart, bodyEnd + "</div>".length);
        }
        return html;
      })
      .join("\n");

    const fullHtml =
      `<!DOCTYPE html>\n` +
      `<html lang="en">\n` +
      `<head>\n` +
      `  <meta charset="UTF-8" />\n` +
      `  <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n` +
      `  <style>\n` +
      `    * { margin: 0; padding: 0; box-sizing: border-box; }\n` +
      `    body { position: relative; background: #f0f0f0; }\n` +
      `    .page-container {\n` +
      `      position: relative;\n` +
      `      overflow: hidden;\n` +
      `      background: white;\n` +
      `      margin: 10px auto;\n` +
      `    }\n` +
      `  </style>\n` +
      `</head>\n` +
      `<body>\n` +
      `${pagesContent}\n` +
      `</body>\n` +
      `</html>`;

    // 8. Inject @font-face CSS from embedded fonts.
    // Font embedding (base64 data URIs) is handled by the font-embedder module
    // when raw font bytes are available. Here we inject any font metadata that
    // was already embedded in FontSpec objects (e.g., from font-embedder output).
    let html = fullHtml;
    if (fonts.length > 0) {
      const fontFaces = fonts
        .map(
          (f) =>
            `@font-face {\n  font-family: '${f.family}';\n  font-weight: ${f.font_weight};\n  font-style: ${f.is_italic ? "italic" : "normal"};\n  font-display: swap;\n}`,
        )
        .join("\n");

      if (fontFaces) {
        const styleTag = `<style>\n${fontFaces}\n</style>`;
        const headClose = html.indexOf("</head>");
        if (headClose !== -1) {
          html = html.slice(0, headClose) + styleTag + "\n" + html.slice(headClose);
        } else {
          html = styleTag + "\n" + html;
        }
      }
    }

    buffer.html = html;
    return { html, requestId };
  } finally {
    // Always clean up, even if the pipeline throws.
    bufferManager.cleanup(requestId);
  }
}

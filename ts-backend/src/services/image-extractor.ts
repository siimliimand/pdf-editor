/**
 * Image Extractor — Extract embedded images from a PDF page via pdf.js.
 *
 * Strategy:
 *   1. Walk the page's operator list for `paintImageXObject` operations.
 *   2. Track the Current Transform Matrix (CTM) to derive each image's
 *      position and rendered size on the page.
 *   3. Pull decoded pixel data from `page.commonObjs`.
 *   4. Encode as PNG bytes (handles CMYK→RGB conversion implicitly —
 *      pdf.js decodes CMYK images to RGB/A in the canvas pipeline).
 *   5. Return `ExtractedImage[]` for downstream HTML generation.
 *
 * Cloudflare Workers constraints:
 *   - No native canvas / ImageBitmap.  We rely on pdf.js internal decoding
 *     via `commonObjs`, which gives us raw pixel arrays.
 *   - PNG encoding is done manually (no external lib).  Deflate compression
 *     uses the Workers-native `CompressionStream` API.
 */

import { OPS } from 'pdfjs-dist';
import type { PDFPageProxy } from 'pdfjs-dist';
import type { ExtractedImage } from './pdf-service';

// ---------------------------------------------------------------------------
// Internal types
// ---------------------------------------------------------------------------

/** 6-element PDF transform matrix [a, b, c, d, e, f]. */
type TransformMatrix = [number, number, number, number, number, number];

/** Decoded image data as returned by pdf.js `commonObjs`. */
interface PdfJsImageData {
  data: Uint8ClampedArray | Uint8Array;
  width: number;
  height: number;
  kind: number; // ImageKind.RGB_24BPP | RGBA_32BPP
}

// ---------------------------------------------------------------------------
// ImageKind — match pdf.js constants (avoids importing the full enum).
// ---------------------------------------------------------------------------

const IMAGE_KIND = {
  RGB_24BPP: 2,
  RGBA_32BPP: 3,
} as const;

// ---------------------------------------------------------------------------
// PNG encoder (minimal, no dependencies)
// ---------------------------------------------------------------------------

/** IEEE CRC-32 lookup table, pre-computed. */
const CRC_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) {
      c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    }
    table[n] = c;
  }
  return table;
})();

function crc32(data: Uint8Array): number {
  let crc = 0xffffffff;
  for (let i = 0; i < data.length; i++) {
    crc = CRC_TABLE[(crc ^ data[i]) & 0xff] ^ (crc >>> 8);
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function u32be(n: number): Uint8Array {
  return new Uint8Array([(n >>> 24) & 0xff, (n >>> 16) & 0xff, (n >>> 8) & 0xff, n & 0xff]);
}

function chunk(type: string, data: Uint8Array): Uint8Array {
  const typeBytes = new TextEncoder().encode(type);
  const len = u32be(data.length);
  const body = new Uint8Array(typeBytes.length + data.length + 4);
  body.set(typeBytes, 0);
  body.set(data, typeBytes.length);
  const crcPayload = new Uint8Array(typeBytes.length + data.length);
  crcPayload.set(typeBytes, 0);
  crcPayload.set(data, typeBytes.length);
  const crc = u32be(crc32(crcPayload));
  body.set(crc, typeBytes.length + data.length);

  // Full output: length(4) + type(4) + data + crc(4)
  const out = new Uint8Array(4 + 4 + data.length + 4);
  out.set(len, 0);
  out.set(typeBytes, 4);
  out.set(data, 8);
  out.set(crc, 8 + data.length);
  return out;
}

/** Deflate a buffer using the Workers-native CompressionStream. */
async function deflate(data: Uint8Array): Promise<Uint8Array> {
  const cs = new CompressionStream('deflate');
  const writer = cs.writable.getWriter();
  // Ensure we pass an ArrayBuffer-backed view (CompressionStream rejects
  // SharedArrayBuffer-backed Uint8Array).
  const buf = new ArrayBuffer(data.byteLength);
  new Uint8Array(buf).set(data);
  writer.write(buf);
  writer.close();

  const reader = cs.readable.getReader();
  const chunks: Uint8Array[] = [];
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
  }

  let totalLen = 0;
  for (const c of chunks) totalLen += c.length;
  const result = new Uint8Array(totalLen);
  let offset = 0;
  for (const c of chunks) {
    result.set(c, offset);
    offset += c.length;
  }
  return result;
}

/**
 * Encode raw RGBA pixel data into a PNG file (Uint8Array).
 *
 * @param rgba  Raw RGBA bytes (4 bytes per pixel, row-major).
 * @param width Image width in pixels.
 * @param height Image height in pixels.
 */
async function encodePng(
  rgba: Uint8Array,
  width: number,
  height: number,
): Promise<Uint8Array> {
  // PNG signature
  const signature = new Uint8Array([137, 80, 78, 71, 13, 10, 26, 10]);

  // IHDR: width(4) + height(4) + bitDepth(1) + colorType(1) + compression(1) + filter(1) + interlace(1)
  const ihdrData = new Uint8Array(13);
  ihdrData.set(u32be(width), 0);
  ihdrData.set(u32be(height), 4);
  ihdrData[8] = 8; // bit depth
  ihdrData[9] = 6; // color type: RGBA
  ihdrData[10] = 0; // compression: deflate
  ihdrData[11] = 0; // filter: adaptive
  ihdrData[12] = 0; // interlace: none

  // Raw scanlines: each row gets a leading filter byte (0 = None)
  const rawLen = height * (1 + width * 4);
  const raw = new Uint8Array(rawLen);
  let srcOff = 0;
  let dstOff = 0;
  for (let y = 0; y < height; y++) {
    raw[dstOff++] = 0; // filter: None
    raw.set(rgba.subarray(srcOff, srcOff + width * 4), dstOff);
    srcOff += width * 4;
    dstOff += width * 4;
  }

  const compressed = await deflate(raw);

  const ihdr = chunk('IHDR', ihdrData);
  const idat = chunk('IDAT', compressed);
  const iend = chunk('IEND', new Uint8Array(0));

  const png = new Uint8Array(
    signature.length + ihdr.length + idat.length + iend.length,
  );
  let off = 0;
  for (const part of [signature, ihdr, idat, iend]) {
    png.set(part, off);
    off += part.length;
  }
  return png;
}

// ---------------------------------------------------------------------------
// Color-space conversion helpers
// ---------------------------------------------------------------------------

/**
 * CMYK → RGB per ISO 3664 (simple formula, no ICC profiles).
 * Input: interleaved CMYK bytes (4 per pixel).  Output: RGB bytes (3 per pixel).
 */
function cmykToRgb(cmyk: Uint8Array): Uint8Array {
  const rgb = new Uint8Array((cmyk.length / 4) * 3);
  for (let i = 0, j = 0; i < cmyk.length; i += 4, j += 3) {
    const c = cmyk[i] / 255;
    const m = cmyk[i + 1] / 255;
    const y = cmyk[i + 2] / 255;
    const k = cmyk[i + 3] / 255;
    rgb[j] = Math.round(255 * (1 - c) * (1 - k));
    rgb[j + 1] = Math.round(255 * (1 - m) * (1 - k));
    rgb[j + 2] = Math.round(255 * (1 - y) * (1 - k));
  }
  return rgb;
}

/**
 * Ensure pixel data is RGBA.  Returns a new Uint8Array if conversion is
 * needed, or the original buffer when it is already RGBA.
 */
function ensureRgba(
  data: Uint8ClampedArray | Uint8Array,
  width: number,
  height: number,
  kind: number,
): Uint8Array {
  const pixelCount = width * height;

  if (kind === IMAGE_KIND.RGBA_32BPP && data.length === pixelCount * 4) {
    return new Uint8Array(data.buffer, data.byteOffset, data.byteLength);
  }

  if (kind === IMAGE_KIND.RGB_24BPP && data.length === pixelCount * 3) {
    const rgba = new Uint8Array(pixelCount * 4);
    for (let i = 0, j = 0; i < pixelCount; i++, j += 4) {
      rgba[j] = data[i * 3];
      rgba[j + 1] = data[i * 3 + 1];
      rgba[j + 2] = data[i * 3 + 2];
      rgba[j + 3] = 255; // fully opaque
    }
    return rgba;
  }

  // CMYK (4 bytes per pixel, no alpha): convert to RGB then expand to RGBA.
  if (data.length === pixelCount * 4 && kind !== IMAGE_KIND.RGBA_32BPP) {
    const rgb = cmykToRgb(new Uint8Array(data.buffer, data.byteOffset, data.byteLength));
    const rgba = new Uint8Array(pixelCount * 4);
    for (let i = 0, j = 0; i < pixelCount; i++, j += 4) {
      rgba[j] = rgb[i * 3];
      rgba[j + 1] = rgb[i * 3 + 1];
      rgba[j + 2] = rgb[i * 3 + 2];
      rgba[j + 3] = 255;
    }
    return rgba;
  }

  // Unknown layout — return raw data and let the caller deal with it.
  return new Uint8Array(data.buffer, data.byteOffset, data.byteLength);
}

// ---------------------------------------------------------------------------
// Transform helpers
// ---------------------------------------------------------------------------

/**
 * Multiply two 3×3 affine matrices (stored as 6-element [a,b,c,d,e,f]).
 *
 *   | a1 b1 0 |   | a2 b2 0 |
 *   | c1 d1 0 | × | c2 d2 0 |
 *   | e1 f1 1 |   | e2 f2 1 |
 */
function multiplyMatrix(
  [a1, b1, c1, d1, e1, f1]: TransformMatrix,
  [a2, b2, c2, d2, e2, f2]: TransformMatrix,
): TransformMatrix {
  return [
    a1 * a2 + b1 * c2,
    a1 * b2 + b1 * d2,
    c1 * a2 + d1 * c2,
    c1 * b2 + d1 * d2,
    e1 * a2 + f1 * c2 + e2,
    e1 * b2 + f1 * d2 + f2,
  ];
}

/** Identity matrix. */
const IDENTITY: TransformMatrix = [1, 0, 0, 1, 0, 0];

/**
 * Compute the bounding box of a rectangle [0, 0, w, h] after applying the
 * given transform.  Returns { left, top, width, height } in page units.
 */
function transformBoundingBox(
  m: TransformMatrix,
  w: number,
  h: number,
): { left: number; top: number; width: number; height: number } {
  // Four corners of the image in local space.
  const corners = [
    [0, 0],
    [w, 0],
    [0, h],
    [w, h],
  ];

  const xs: number[] = [];
  const ys: number[] = [];

  for (const [x, y] of corners) {
    // Apply matrix: x' = a*x + c*y + e,  y' = b*x + d*y + f
    xs.push(m[0] * x + m[2] * y + m[4]);
    ys.push(m[1] * x + m[3] * y + m[5]);
  }

  const left = Math.min(...xs);
  const top = Math.min(...ys);
  return {
    left,
    top,
    width: Math.max(...xs) - left,
    height: Math.max(...ys) - top,
  };
}

// ---------------------------------------------------------------------------
// Operator-list walker
// ---------------------------------------------------------------------------

interface ImagePlacement {
  objId: string;
  bbox: { left: number; top: number; width: number; height: number };
}

/**
 * Walk the page's operator list and collect every `paintImageXObject` (and
 * `paintInlineImageXObject`) occurrence together with the CTM-derived
 * bounding box.
 */
function collectImagePlacements(
  fnArray: number[],
  argsArray: unknown[][],
): ImagePlacement[] {
  const placements: ImagePlacement[] = [];

  // Maintain a stack of saved CTMs for `save`/`restore` pairs.
  const ctmStack: TransformMatrix[] = [];
  let ctm: TransformMatrix = [...IDENTITY];

  for (let i = 0; i < fnArray.length; i++) {
    const op = fnArray[i];
    const args = argsArray[i];

    switch (op) {
      case OPS.save:
        ctmStack.push([...ctm]);
        break;

      case OPS.restore:
        ctm = ctmStack.pop() ?? [...IDENTITY];
        break;

      case OPS.transform: {
        const t = args as unknown as TransformMatrix;
        ctm = multiplyMatrix(ctm, t);
        break;
      }

      case OPS.paintImageXObject:
      case OPS.paintInlineImageXObject: {
        // args[0] is the image object ID string.
        const objId = args[0] as string;

        // The image's intrinsic dimensions are not directly available here,
        // so we store a placeholder bbox that will be filled in later once
        // we resolve the image object from commonObjs.
        placements.push({ objId, bbox: { left: 0, top: 0, width: 0, height: 0 } });

        // Tag the placement index so we can back-fill dimensions later.
        const idx = placements.length - 1;

        // We defer the dimension back-fill to the async extraction phase
        // because commonObjs.get() may require resolving a promise.
        // Store the current CTM snapshot for later use.
        (placements[idx] as ImagePlacement & { ctm?: TransformMatrix }).ctm = [...ctm];
        break;
      }

      // paintImageMaskXObject uses the same image data but as a mask —
      // skip these as they are not visual images.
      default:
        break;
    }
  }

  return placements;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Extract all embedded images from a single PDF page.
 *
 * Returns an array of `ExtractedImage` objects, each containing:
 *   - `id`       — unique identifier (`page-N_img-M`)
 *   - `width`    — rendered width in PDF points
 *   - `height`   — rendered height in PDF points
 *   - `data`     — raw PNG bytes
 *   - `mimeType` — `"image/png"`
 */
export async function extractImagesFromPage(
  page: PDFPageProxy,
  pageNumber: number,
): Promise<ExtractedImage[]> {
  const operatorList = await page.getOperatorList();
  const rawPlacements = collectImagePlacements(
    operatorList.fnArray,
    operatorList.argsArray,
  );

  if (rawPlacements.length === 0) return [];

  const results: ExtractedImage[] = [];
  let imgIndex = 0;

  for (const placement of rawPlacements) {
    try {
      // Resolve the decoded image data from pdf.js object store.
      const imageData = await resolveImageData(page, placement.objId);
      if (!imageData) continue;

      const { width: imgW, height: imgH } = imageData;

      // Back-fill bbox using the actual image dimensions and the stored CTM.
      const ctm =
        (placement as ImagePlacement & { ctm?: TransformMatrix }).ctm ?? IDENTITY;
      const bbox = transformBoundingBox(ctm, imgW, imgH);

      // Skip zero-size images.
      if (bbox.width <= 0 || bbox.height <= 0) continue;

      // Ensure pixel data is RGBA, then encode as PNG.
      const rgba = ensureRgba(imageData.data, imgW, imgH, imageData.kind);
      const pngBytes = await encodePng(rgba, imgW, imgH);

      results.push({
        id: `page-${pageNumber}_img-${imgIndex}`,
        width: bbox.width,
        height: bbox.height,
        data: pngBytes,
        mimeType: 'image/png',
      });

      imgIndex++;
    } catch {
      // Skip images that fail to resolve or encode — they are typically
      // malformed XObjects or unsupported color spaces.
      continue;
    }
  }

  return results;
}

// ---------------------------------------------------------------------------
// Helpers exported for testing / external use
// ---------------------------------------------------------------------------

/**
 * Resolve a pdf.js image XObject from the page's `commonObjs` store.
 *
 * Returns `null` if the object is missing or cannot be decoded.
 */
export async function resolveImageData(
  page: PDFPageProxy,
  objId: string,
): Promise<PdfJsImageData | null> {
  return new Promise((resolve) => {
    try {
      page.commonObjs.get(objId, (data: PdfJsImageData | undefined) => {
        if (
          data &&
          data.data &&
          data.width > 0 &&
          data.height > 0
        ) {
          resolve(data);
        } else {
          resolve(null);
        }
      });
    } catch {
      resolve(null);
    }
  });
}

/**
 * Render a single image XObject to PNG bytes.
 *
 * Useful when you have an image object ID and want to encode it outside of
 * the full page extraction flow (e.g. for selective extraction).
 *
 * @param page     The pdf.js page that owns the image.
 * @param objId    The image object ID (as found in the operator list).
 * @returns        PNG bytes and dimensions, or `null` if resolution fails.
 */
export async function renderImageXObjectToPng(
  page: PDFPageProxy,
  objId: string,
): Promise<{
  data: Uint8Array;
  width: number;
  height: number;
  mimeType: string;
} | null> {
  const imageData = await resolveImageData(page, objId);
  if (!imageData) return null;

  const rgba = ensureRgba(
    imageData.data,
    imageData.width,
    imageData.height,
    imageData.kind,
  );
  const pngBytes = await encodePng(rgba, imageData.width, imageData.height);

  return {
    data: pngBytes,
    width: imageData.width,
    height: imageData.height,
    mimeType: 'image/png',
  };
}

/**
 * Render a clip region of a PDF page to PNG bytes.
 *
 * This mirrors the Python "render-crop" strategy: render the full page at
 * a given scale, then crop to the desired rectangle.  Useful for extracting
 * images that are composites or for achieving pixel-perfect fidelity.
 *
 * NOTE: Requires a canvas context.  In Cloudflare Workers you must supply
 * an `OffscreenCanvas` or equivalent.  Returns `null` if rendering fails.
 */
export async function renderPageClipToPng(
  page: PDFPageProxy,
  clip: { x: number; y: number; width: number; height: number },
  scale: number = 2,
): Promise<{
  data: Uint8Array;
  width: number;
  height: number;
  mimeType: string;
} | null> {
  try {
    const viewport = page.getViewport({ scale });

    // OffscreenCanvas is available in Cloudflare Workers.
    const canvas = new OffscreenCanvas(
      Math.ceil(viewport.width),
      Math.ceil(viewport.height),
    );
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    await page.render({
      canvasContext: ctx as unknown as CanvasRenderingContext2D,
      viewport,
    }).promise;

    // Read pixels for the clip region.
    const sx = Math.max(0, Math.floor(clip.x * scale));
    const sy = Math.max(0, Math.floor(clip.y * scale));
    const sw = Math.min(
      Math.ceil(clip.width * scale),
      canvas.width - sx,
    );
    const sh = Math.min(
      Math.ceil(clip.height * scale),
      canvas.height - sy,
    );

    if (sw <= 0 || sh <= 0) return null;

    const imageData = ctx.getImageData(sx, sy, sw, sh);
    const pngBytes = await encodePng(
      new Uint8Array(imageData.data.buffer),
      sw,
      sh,
    );

    return {
      data: pngBytes,
      width: sw,
      height: sh,
      mimeType: 'image/png',
    };
  } catch {
    return null;
  }
}

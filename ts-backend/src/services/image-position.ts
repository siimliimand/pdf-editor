/**
 * Image Position Mapper — map extracted images to page coordinates for HTML.
 *
 * The image extractor (image-extractor.ts) resolves CTM-derived bounding boxes
 * but only stores rendered width/height in ExtractedImage.  This module re-derives
 * the position (top, left) from the stored CTM and produces ImageElement objects
 * ready for HTML placement.
 *
 * Coordinate system:
 *   pdf.js uses top-down coordinates (y=0 at top), matching HTML — no flip needed.
 */

import type { ExtractedImage } from './pdf-service';
import type { ImageElement } from '../models/types';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** 6-element PDF transform matrix [a, b, c, d, e, f]. */
type TransformMatrix = [number, number, number, number, number, number];

export interface ImageTransform {
  id: string;
  ctm: TransformMatrix;
}

// ---------------------------------------------------------------------------
// Transform helpers (duplicated from image-extractor to keep modules decoupled)
// ---------------------------------------------------------------------------

/**
 * Compute the bounding box of a rectangle [0, 0, w, h] after applying the
 * given CTM.  Returns { left, top, width, height } in page units.
 *
 * CTM layout: [a, b, c, d, e, f]
 *   x' = a*x + c*y + e
 *   y' = b*x + d*y + f
 */
function transformBoundingBox(
  m: TransformMatrix,
  w: number,
  h: number,
): { left: number; top: number; width: number; height: number } {
  const corners = [
    [0, 0],
    [w, 0],
    [0, h],
    [w, h],
  ];

  const xs: number[] = [];
  const ys: number[] = [];

  for (const [x, y] of corners) {
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
// Base64 encoding (no Buffer/require — Workers-safe)
// ---------------------------------------------------------------------------

const BASE64_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';

function uint8ArrayToBase64(bytes: Uint8Array): string {
  let binary = '';
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  // btoa is available in Cloudflare Workers.
  return btoa(binary);
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Map extracted images to their page positions using CTM transforms.
 *
 * @param images           Images produced by `extractImagesFromPage`.
 * @param imageTransforms  CTM recorded per image during operator-list walking.
 *                         Each entry's `id` must match the `ExtractedImage.id`.
 * @param pageWidth        Page width in PDF points.
 * @param pageHeight       Page height in PDF points (unused currently, reserved
 *                         for future bottom-up→top-down conversion if needed).
 * @returns                `ImageElement[]` with top/left/width/height and a
 *                         base64 data-URI src.
 */
export function mapImagesToPagePositions(
  images: ExtractedImage[],
  imageTransforms: ImageTransform[],
  _pageWidth: number,
  _pageHeight: number,
): ImageElement[] {
  const transformById = new Map<string, TransformMatrix>();
  for (const t of imageTransforms) {
    transformById.set(t.id, t.ctm);
  }

  const elements: ImageElement[] = [];

  for (const img of images) {
    const ctm = transformById.get(img.id);

    let left: number;
    let top: number;
    let width: number;
    let height: number;

    if (ctm) {
      // Re-derive the bounding box from the CTM and the *pixel* dimensions.
      // The CTM encodes the full scale + translate, so the rendered size is
      // `CTM applied to (pixelWidth, pixelHeight)` — which is exactly what
      // transformBoundingBox computes.
      //
      // However, img.width/height from the extractor are already the
      // *rendered* (post-transform) dimensions.  We therefore need the
      // *pixel* dimensions to re-apply the CTM.  Since the extractor doesn't
      // store them, we fall back to using the CTM directly with a unit
      // rectangle and scale by the ratio of rendered/pixel sizes.
      //
      // Simpler approach: the extractor already stores the rendered bbox
      // dimensions in img.width/height.  The CTM's translate components
      // (e, f) give the origin of the image rectangle.  For axis-aligned
      // images (the common case — b=c=0), this is exact:
      //
      //   left = e
      //   top  = f
      //   width  = a * pixelWidth   (≈ img.width when b=c=0)
      //   height = d * pixelHeight  (≈ img.height when b=c=0)
      //
      // For non-axis-aligned images we compute the full bounding box.

      const hasSkew = ctm[1] !== 0 || ctm[2] !== 0;

      if (!hasSkew) {
        // Fast path: axis-aligned — direct extraction from CTM components.
        left = ctm[4]; // e — translate X
        top = ctm[5];  // f — translate Y
        width = img.width;
        height = img.height;
      } else {
        // Slow path: skewed/rotated — compute the bounding box of the unit
        // rectangle transformed by the CTM, then scale to rendered dimensions.
        // The unit bbox gives us the *direction* of the bounding box; the
        // actual size is img.width × img.height (as stored by the extractor).
        const unitBbox = transformBoundingBox(ctm, 1, 1);
        // Scale the unit bbox proportionally so its area matches the rendered area.
        const unitArea = Math.abs(unitBbox.width * unitBbox.height);
        if (unitArea > 0) {
          const scale = Math.sqrt((img.width * img.height) / unitArea);
          left = unitBbox.left * scale;
          top = unitBbox.top * scale;
          width = unitBbox.width * scale;
          height = unitBbox.height * scale;
        } else {
          left = ctm[4];
          top = ctm[5];
          width = img.width;
          height = img.height;
        }
      }
    } else {
      // No CTM available — place at origin with rendered dimensions.
      left = 0;
      top = 0;
      width = img.width;
      height = img.height;
    }

    // Clamp to non-negative (floating-point noise can produce tiny negatives).
    left = Math.max(0, left);
    top = Math.max(0, top);
    width = Math.max(0, width);
    height = Math.max(0, height);

    const src = `data:${img.mimeType};base64,${uint8ArrayToBase64(img.data)}`;

    elements.push({
      type: 'image',
      src,
      top,
      left,
      width,
      height,
    });
  }

  return elements;
}

/**
 * Convenience: convert a single ExtractedImage + its CTM into an ImageElement.
 */
export function mapSingleImageToPosition(
  image: ExtractedImage,
  ctm: TransformMatrix | null,
  _pageWidth: number,
  _pageHeight: number,
): ImageElement {
  return mapImagesToPagePositions(
    [image],
    ctm ? [{ id: image.id, ctm }] : [],
    _pageWidth,
    _pageHeight,
  )[0];
}

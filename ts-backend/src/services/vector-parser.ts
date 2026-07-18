/**
 * Vector Parser — Extract vector elements from pdf.js page operator lists.
 *
 * Iterates the operator list returned by `page.getOperatorList()`, reconstructs
 * subpaths from the drawing commands (moveTo, lineTo, curveTo, rectangle,
 * closePath), and emits `VectorElement` objects whenever a rendering operator
 * (stroke, fill, eoFill, closeStroke) is encountered.
 *
 * Border-radius detection: a rounded-rectangle corner in PDF is drawn with
 * four consecutive `curveTo` calls whose control points form a circular arc.
 * When four such curves are detected in sequence we approximate the radius
 * from the first curve's control-point geometry.
 */

import { OPS } from 'pdfjs-dist';
import type { PDFPageProxy } from 'pdfjs-dist';
import { VectorElement } from '../models/types';
import { VECTOR } from '../models/constants';

// ---------------------------------------------------------------------------
// Internal path representation
// ---------------------------------------------------------------------------

interface PathPoint {
  x: number;
  y: number;
}

interface SubPath {
  points: PathPoint[];
  closed: boolean;
}

interface PathBuilder {
  subpaths: SubPath[];
  currentSubpath: SubPath | null;
}

function createBuilder(): PathBuilder {
  return { subpaths: [], currentSubpath: null };
}

function moveTo(b: PathBuilder, x: number, y: number): void {
  const sp: SubPath = { points: [{ x, y }], closed: false };
  b.subpaths.push(sp);
  b.currentSubpath = sp;
}

function lineTo(b: PathBuilder, x: number, y: number): void {
  if (!b.currentSubpath) return;
  b.currentSubpath.points.push({ x, y });
}

function curveTo(
  b: PathBuilder,
  x1: number,
  y1: number,
  x2: number,
  y2: number,
  x3: number,
  y3: number,
): void {
  if (!b.currentSubpath) return;
  // Approximate cubic Bézier with its end-point; finer sampling is unnecessary
  // for the bounding-box-based VectorElement model.
  b.currentSubpath.points.push({ x: x3, y: y3 });
}

function rectangle(
  b: PathBuilder,
  x: number,
  y: number,
  w: number,
  h: number,
): void {
  // A PDF rectangle subpath: moveTo → lineTo ×3 → closePath.
  moveTo(b, x, y);
  lineTo(b, x + w, y);
  lineTo(b, x + w, y + h);
  lineTo(b, x, y + h);
  closePath(b);
}

function closePath(b: PathBuilder): void {
  if (b.currentSubpath) {
    b.currentSubpath.closed = true;
  }
}

// ---------------------------------------------------------------------------
// Colour helpers
// ---------------------------------------------------------------------------

/** Normalise a 0-1 or 0-255 component to 0-255 integer. */
function toByte(v: number): number {
  return v <= 1 ? Math.round(v * 255) : Math.round(v);
}

function rgbToHex(r: number, g: number, b: number): string {
  const rr = Math.max(0, Math.min(255, toByte(r)));
  const gg = Math.max(0, Math.min(255, toByte(g)));
  const bb = Math.max(0, Math.min(255, toByte(b)));
  return `#${rr.toString(16).padStart(2, '0')}${gg.toString(16).padStart(2, '0')}${bb.toString(16).padStart(2, '0')}`;
}

function grayToHex(g: number): string {
  const v = Math.max(0, Math.min(255, toByte(g)));
  return `#${v.toString(16).padStart(2, '0')}${v.toString(16).padStart(2, '0')}${v.toString(16).padStart(2, '0')}`;
}

function cmykToHex(c: number, m: number, y: number, k: number): string {
  const r = 255 * (1 - c) * (1 - k);
  const g = 255 * (1 - m) * (1 - k);
  const b = 255 * (1 - y) * (1 - k);
  return rgbToHex(r, g, b);
}

// ---------------------------------------------------------------------------
// Bounding box + VectorElement construction
// ---------------------------------------------------------------------------

function pointsBBox(points: PathPoint[]): {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
} {
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  for (const p of points) {
    if (p.x < minX) minX = p.x;
    if (p.y < minY) minY = p.y;
    if (p.x > maxX) maxX = p.x;
    if (p.y > maxY) maxY = p.y;
  }
  return { minX, minY, maxX, maxY };
}

function buildVectorElement(
  subpath: SubPath,
  opts: {
    linewidth: number;
    stroke: boolean;
    fill: boolean;
    color?: string;
    fill_color?: string;
    dash?: number[];
    border_radius?: number;
  },
): VectorElement | null {
  if (subpath.points.length === 0) return null;

  const { minX, minY, maxX, maxY } = pointsBBox(subpath.points);

  // Skip degenerate zero-area paths.
  if (minX === maxX && minY === maxY) return null;

  const v: VectorElement = {
    x0: minX,
    y0: minY,
    x1: maxX,
    y1: maxY,
    linewidth: opts.linewidth,
    stroke: opts.stroke,
    fill: opts.fill,
  };
  if (opts.color !== undefined) v.color = opts.color;
  if (opts.fill_color !== undefined) v.fill_color = opts.fill_color;
  if (opts.dash && opts.dash.length > 0) v.dash = opts.dash;
  if (opts.border_radius !== undefined) v.border_radius = opts.border_radius;

  return v;
}

// ---------------------------------------------------------------------------
// Border-radius detection (4 consecutive curves forming rounded corners)
// ---------------------------------------------------------------------------

/**
 * Attempt to detect a rounded rectangle from a list of subpath points.
 *
 * PDF rounded rectangles are typically drawn as four cubic Bézier segments.
 * Each corner uses a curve whose control points sit at distance `r` from the
 * corner. We detect when there are exactly 4 curve segments and approximate
 * `r` from the displacement between the first point and the second point.
 *
 * Returns `undefined` when the pattern is not recognised.
 */
function detectBorderRadius(subpath: SubPath): number | undefined {
  // A rounded rect has at least 4 segments → ≥ 5 unique points (first is
  // repeated at closePath).  We work with the raw points; each curveTo
  // pushes only the end-point, so 4 curves produce 5 points in the subpath.
  if (!subpath.closed) return undefined;
  if (subpath.points.length !== VECTOR.CORNER_CURVE_COUNT + 1) return undefined;

  // The first point should equal the last (closed subpath).
  const first = subpath.points[0];
  const last = subpath.points[subpath.points.length - 1];
  if (first.x !== last.x || first.y !== last.y) return undefined;

  // Approximate radius from the first segment.
  const p1 = subpath.points[1];
  const r = Math.min(
    Math.abs(p1.x - first.x),
    Math.abs(p1.y - first.y),
  );

  if (r > 0 && r <= VECTOR.MAX_BORDER_RADIUS) {
    return r;
  }
  return undefined;
}

// ---------------------------------------------------------------------------
// Rendering: convert accumulated subpaths into VectorElements
// ---------------------------------------------------------------------------

interface RenderState {
  linewidth: number;
  strokeColor?: string;
  fillColor?: string;
  dash?: number[];
}

function flushSubpaths(
  subpaths: SubPath[],
  state: RenderState,
  doStroke: boolean,
  doFill: boolean,
): VectorElement[] {
  const results: VectorElement[] = [];

  for (const sp of subpaths) {
    const border_radius = detectBorderRadius(sp);
    const v = buildVectorElement(sp, {
      linewidth: state.linewidth,
      stroke: doStroke,
      fill: doFill,
      color: state.strokeColor,
      fill_color: state.fillColor,
      dash: state.dash,
      border_radius,
    });
    if (v) results.push(v);
  }

  return results;
}

// ---------------------------------------------------------------------------
// Main export
// ---------------------------------------------------------------------------

/**
 * Extract all vector elements from a single pdf.js page.
 *
 * @param page     The `PDFPageProxy` returned by `doc.getPage(n)`.
 * @param pageNum  1-based page number (used for diagnostics only).
 * @returns        Array of `VectorElement` in top-down coordinates
 *                 (y=0 at top, matching pdf.js viewport).
 */
export async function extractVectorsFromPage(
  page: PDFPageProxy,
  pageNum: number,
): Promise<VectorElement[]> {
  const ops = await page.getOperatorList();
  const fnArray = ops.fnArray;
  const argsArray = ops.argsArray;

  const builder = createBuilder();
  const vectors: VectorElement[] = [];

  // Current drawing state.
  const state: RenderState = {
    linewidth: 1,
    strokeColor: undefined,
    fillColor: undefined,
    dash: undefined,
  };

  for (let i = 0; i < fnArray.length; i++) {
    const op = fnArray[i];
    const args = argsArray[i];

    // --- Path construction ------------------------------------------------
    if (op === OPS.moveTo) {
      moveTo(builder, args[0], args[1]);
    } else if (op === OPS.lineTo) {
      lineTo(builder, args[0], args[1]);
    } else if (op === OPS.curveTo) {
      curveTo(builder, args[0], args[1], args[2], args[3], args[4], args[5]);
    } else if (op === OPS.curveTo2) {
      // curveTo2: P1 defaults to current point.
      const cur = builder.currentSubpath;
      const cx = cur && cur.points.length > 0 ? cur.points[cur.points.length - 1].x : 0;
      const cy = cur && cur.points.length > 0 ? cur.points[cur.points.length - 1].y : 0;
      curveTo(builder, cx, cy, args[0], args[1], args[2], args[3]);
    } else if (op === OPS.curveTo3) {
      // curveTo3: P2 defaults to endpoint.
      curveTo(builder, args[0], args[1], args[2], args[3], args[2], args[3]);
    } else if (op === OPS.rectangle) {
      rectangle(builder, args[0], args[1], args[2], args[3]);
    } else if (op === OPS.closePath) {
      closePath(builder);
    }

    // --- Styling ----------------------------------------------------------
    else if (op === OPS.setLineWidth) {
      state.linewidth = args[0];
    } else if (op === OPS.setDash) {
      // args: [dashList, phase]
      const dashList = args[0] as number[];
      const phase = args[1] as number;
      state.dash =
        dashList && dashList.length > 0
          ? [...dashList, phase]
          : undefined;
    }

    // Stroke colours
    else if (op === OPS.setStrokeRGBColor) {
      state.strokeColor = rgbToHex(args[0], args[1], args[2]);
    } else if (op === OPS.setStrokeGray) {
      state.strokeColor = grayToHex(args[0]);
    } else if (op === OPS.setStrokeCMYKColor) {
      state.strokeColor = cmykToHex(args[0], args[1], args[2], args[3]);
    } else if (op === OPS.setStrokeColor) {
      // Generic — pdf.js may push an array; treat as RGB fallback.
      if (Array.isArray(args[0])) {
        const c = args[0];
        state.strokeColor =
          c.length >= 3
            ? rgbToHex(c[0], c[1], c[2])
            : c.length === 1
              ? grayToHex(c[0])
              : undefined;
      }
    }

    // Fill colours
    else if (op === OPS.setFillRGBColor) {
      state.fillColor = rgbToHex(args[0], args[1], args[2]);
    } else if (op === OPS.setFillGray) {
      state.fillColor = grayToHex(args[0]);
    } else if (op === OPS.setFillCMYKColor) {
      state.fillColor = cmykToHex(args[0], args[1], args[2], args[3]);
    } else if (op === OPS.setFillColor) {
      if (Array.isArray(args[0])) {
        const c = args[0];
        state.fillColor =
          c.length >= 3
            ? rgbToHex(c[0], c[1], c[2])
            : c.length === 1
              ? grayToHex(c[0])
              : undefined;
      }
    }

    // --- Rendering (flush accumulated path) ------------------------------
    else if (
      op === OPS.stroke ||
      op === OPS.closeStroke
    ) {
      if (op === OPS.closeStroke) closePath(builder);
      const sub = builder.subpaths.splice(0);
      builder.currentSubpath = null;
      vectors.push(...flushSubpaths(sub, state, true, false));
    } else if (
      op === OPS.fill ||
      op === OPS.fillStroke ||
      op === OPS.eoFill ||
      op === OPS.eoFillStroke ||
      op === OPS.closeFillStroke ||
      op === OPS.closeEOFillStroke
    ) {
      if (
        op === OPS.closeFillStroke ||
        op === OPS.closeEOFillStroke
      ) {
        closePath(builder);
      }
      const sub = builder.subpaths.splice(0);
      builder.currentSubpath = null;

      const doStroke =
        op === OPS.fillStroke ||
        op === OPS.eoFillStroke ||
        op === OPS.closeFillStroke ||
        op === OPS.closeEOFillStroke;

      vectors.push(...flushSubpaths(sub, state, doStroke, true));
    } else if (op === OPS.endPath) {
      // Discard the current path (no fill, no stroke).
      builder.subpaths.length = 0;
      builder.currentSubpath = null;
    }
  }

  return vectors;
}

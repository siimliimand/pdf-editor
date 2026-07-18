import type { VectorElement } from '../models/types';

const ZOOM = {
  PDF_POINT_TO_CSS_PX: 96 / 72,
};

export function flipYCoordinate(y: number, pageHeight: number): number {
  return pageHeight - y;
}

export function pdfPointToCssPixels(points: number): number {
  return points * ZOOM.PDF_POINT_TO_CSS_PX;
}

export function normalizeVectorCoordinates(
  v: VectorElement,
  pageHeight: number,
): VectorElement {
  let y0 = v.y0;
  let y1 = v.y1;
  if (y0 > y1) {
    [y0, y1] = [y1, y0];
  }
  return { ...v, y0, y1 };
}

export interface FontSpec {
  id: string;
  size: number;
  family: string;
  color: string;
  is_bold: boolean;
  is_italic: boolean;
  font_weight?: number;
}

export interface TextElement {
  type: "text";
  text: string;
  top: number;
  left: number;
  width: number;
  height: number;
  font_spec: FontSpec | null;
  font_size: number;
}

export interface ImageElement {
  type: "image";
  src: string;
  top: number;
  left: number;
  width: number;
  height: number;
}

export type Element = TextElement | ImageElement;

export interface VectorElement {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
  linewidth: number;
  stroke: boolean;
  fill: boolean;
  color?: string;
  fill_color?: string;
  dash?: number[];
  border_radius?: number;
}

export function getVectorWidth(v: VectorElement): number {
  return Math.abs(v.x1 - v.x0);
}

export function getVectorHeight(v: VectorElement): number {
  return Math.abs(v.y1 - v.y0);
}

export function isHorizontalVector(v: VectorElement): boolean {
  const h = getVectorHeight(v);
  const w = getVectorWidth(v);
  return h <= Math.max(2.0, v.linewidth * 1.5) && w > 5;
}

export function isVerticalVector(v: VectorElement): boolean {
  const w = getVectorWidth(v);
  const h = getVectorHeight(v);
  return w <= Math.max(2.0, v.linewidth * 1.5) && h > 5;
}

export interface TableRow {
  top: number;
  height: number;
  elements: Element[];
  approx_line_height?: number;
}

export interface TableCell {
  row_idx: number;
  col_idx: number;
  row_span: number;
  col_span: number;
  text_elements: Element[];
  style_top?: string;
  style_bottom?: string;
  style_left?: string;
  style_right?: string;
  background_color?: string | null;
}

export interface TableDefinition {
  rect: { top: number; left: number; bottom: number; right: number };
  row_positions: number[];
  col_positions: number[];
  cells: TableCell[];
}

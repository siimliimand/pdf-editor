/**
 * HTML Renderer — Convert extracted page data to HTML string.
 *
 * Takes text elements, images, table definitions, and vectors, and produces
 * a complete HTML page that preserves the PDF layout using absolute positioning.
 *
 * All coordinates are scaled by the zoom level before rendering.
 */

import type {
  TextElement,
  ImageElement,
  TableDefinition,
  TableCell,
  VectorElement,
} from "../models/types";
import { ZOOM } from "../models/constants";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface RenderPageOptions {
  textElements: TextElement[];
  images: ImageElement[];
  tables: TableDefinition[];
  vectors: VectorElement[];
  pageWidth: number;
  pageHeight: number;
  zoomLevel: number;
  fontMapping: Map<string, string>;
}

interface SortableElement {
  type: "text" | "image" | "table" | "vector";
  top: number;
  left: number;
  data: TextElement | ImageElement | TableDefinition | VectorElement;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function scale(value: number, zoomLevel: number): number {
  const factor = zoomLevel / ZOOM.DEFAULT;
  return value * factor;
}

// ---------------------------------------------------------------------------
// Element sorting
// ---------------------------------------------------------------------------

function collectSortableElements(options: RenderPageOptions): SortableElement[] {
  const items: SortableElement[] = [];

  for (const el of options.textElements) {
    items.push({ type: "text", top: el.top, left: el.left, data: el });
  }

  for (const el of options.images) {
    items.push({ type: "image", top: el.top, left: el.left, data: el });
  }

  for (const table of options.tables) {
    items.push({
      type: "table",
      top: table.rect.top,
      left: table.rect.left,
      data: table,
    });
  }

  for (const v of options.vectors) {
    items.push({
      type: "vector",
      top: Math.min(v.y0, v.y1),
      left: Math.min(v.x0, v.x1),
      data: v,
    });
  }

  // Sort by top, then left for correct visual ordering.
  items.sort((a, b) => {
    if (a.top !== b.top) return a.top - b.top;
    return a.left - b.left;
  });

  return items;
}

// ---------------------------------------------------------------------------
// Text rendering
// ---------------------------------------------------------------------------

function renderTextElement(
  el: TextElement,
  zoomLevel: number,
  fontMapping: Map<string, string>,
): string {
  const top = scale(el.top, zoomLevel);
  const left = scale(el.left, zoomLevel);
  const width = scale(el.width, zoomLevel);
  const height = scale(el.height, zoomLevel);

  const styles: string[] = [
    "position: absolute",
    `top: ${top.toFixed(2)}px`,
    `left: ${left.toFixed(2)}px`,
    `width: ${width.toFixed(2)}px`,
    `height: ${height.toFixed(2)}px`,
    "overflow: hidden",
    "white-space: nowrap",
    "line-height: 1",
  ];

  if (el.font_spec) {
    const spec = el.font_spec;
    const family = fontMapping.get(spec.id) || spec.family;
    const fontSize = scale(spec.size, zoomLevel);

    styles.push(`font-family: '${escapeHtml(family)}', sans-serif`);
    styles.push(`font-size: ${fontSize.toFixed(2)}px`);
    styles.push(`color: ${spec.color}`);

    if (spec.is_bold || (spec.font_weight && spec.font_weight >= 700)) {
      styles.push("font-weight: bold");
    } else if (spec.font_weight) {
      styles.push(`font-weight: ${spec.font_weight}`);
    }

    if (spec.is_italic) {
      styles.push("font-style: italic");
    }
  } else {
    // Fallback: use font_size from the element directly.
    const fontSize = scale(el.font_size, zoomLevel);
    styles.push(`font-size: ${fontSize.toFixed(2)}px`);
  }

  const styleAttr = styles.join("; ");
  const text = escapeHtml(el.text);

  return `<div style="${styleAttr}">${text}</div>`;
}

/**
 * Render a standalone text block with absolute positioning and background color.
 *
 * Used for text blocks that appear outside of tables — positioned absolutely
 * on the page with optional background fill for highlight/annotation effects.
 *
 * @param el - The text element to render.
 * @param zoomLevel - Zoom multiplier.
 * @param fontMapping - Font ID to CSS family name mapping.
 * @param backgroundColor - Optional background color for the text block.
 * @returns HTML string for the positioned text block.
 */
export function renderTextBlock(
  el: TextElement,
  zoomLevel: number,
  fontMapping: Map<string, string>,
  backgroundColor?: string | null,
): string {
  const top = scale(el.top, zoomLevel);
  const left = scale(el.left, zoomLevel);
  const width = scale(el.width, zoomLevel);
  const height = scale(el.height, zoomLevel);

  const styles: string[] = [
    "position: absolute",
    `top: ${top.toFixed(2)}px`,
    `left: ${left.toFixed(2)}px`,
    `width: ${width.toFixed(2)}px`,
    `height: ${height.toFixed(2)}px`,
    "overflow: hidden",
    "white-space: pre-wrap",
    "line-height: 1.2",
  ];

  if (backgroundColor) {
    styles.push(`background-color: ${backgroundColor}`);
  }

  if (el.font_spec) {
    const spec = el.font_spec;
    const family = fontMapping.get(spec.id) || spec.family;
    const fontSize = scale(spec.size, zoomLevel);

    styles.push(`font-family: '${escapeHtml(family)}', sans-serif`);
    styles.push(`font-size: ${fontSize.toFixed(2)}px`);
    styles.push(`color: ${spec.color}`);

    if (spec.is_bold || (spec.font_weight && spec.font_weight >= 700)) {
      styles.push("font-weight: bold");
    } else if (spec.font_weight) {
      styles.push(`font-weight: ${spec.font_weight}`);
    }

    if (spec.is_italic) {
      styles.push("font-style: italic");
    }
  } else {
    const fontSize = scale(el.font_size, zoomLevel);
    styles.push(`font-size: ${fontSize.toFixed(2)}px`);
  }

  const styleAttr = styles.join("; ");
  const text = escapeHtml(el.text);

  return `<div style="${styleAttr}">${text}</div>`;
}

// ---------------------------------------------------------------------------
// Image rendering
// ---------------------------------------------------------------------------

function renderImageElement(el: ImageElement, zoomLevel: number): string {
  const top = scale(el.top, zoomLevel);
  const left = scale(el.left, zoomLevel);
  const width = scale(el.width, zoomLevel);
  const height = scale(el.height, zoomLevel);

  const styles = [
    "position: absolute",
    `top: ${top.toFixed(2)}px`,
    `left: ${left.toFixed(2)}px`,
    `width: ${width.toFixed(2)}px`,
    `height: ${height.toFixed(2)}px`,
  ];

  const styleAttr = styles.join("; ");
  return `<img src="${el.src}" style="${styleAttr}" alt="embedded image" />`;
}

// ---------------------------------------------------------------------------
// Vector rendering (SVG-based)
// ---------------------------------------------------------------------------

function renderVectorElement(v: VectorElement, zoomLevel: number): string {
  const top = scale(Math.min(v.y0, v.y1), zoomLevel);
  const left = scale(Math.min(v.x0, v.x1), zoomLevel);
  const width = scale(Math.abs(v.x1 - v.x0), zoomLevel);
  const height = scale(Math.abs(v.y1 - v.y0), zoomLevel);

  const styles = [
    "position: absolute",
    `top: ${top.toFixed(2)}px`,
    `left: ${left.toFixed(2)}px`,
    `width: ${width.toFixed(2)}px`,
    `height: ${height.toFixed(2)}px`,
    "pointer-events: none",
  ];

  const svgWidth = width.toFixed(2);
  const svgHeight = height.toFixed(2);

  let pathD: string;
  if (v.border_radius !== undefined && v.border_radius > 0) {
    // Rounded rectangle path.
    const r = scale(v.border_radius, zoomLevel);
    const rx = Math.min(r, width / 2);
    const ry = Math.min(r, height / 2);
    pathD = `M ${rx} 0 L ${width - rx} 0 Q ${width} 0 ${width} ${ry} L ${width} ${height - ry} Q ${width} ${height} ${width - rx} ${height} L ${rx} ${height} Q 0 ${height} 0 ${height - ry} L 0 ${ry} Q 0 0 ${rx} 0 Z`;
  } else {
    pathD = `M 0 0 L ${svgWidth} 0 L ${svgWidth} ${svgHeight} L 0 ${svgHeight} Z`;
  }

  const strokeColor = v.color || "#000000";
  const fillColor = v.fill_color || "none";
  const strokeWidth = scale(v.linewidth, zoomLevel).toFixed(2);

  const strokeAttr = v.stroke
    ? `stroke="${strokeColor}" stroke-width="${strokeWidth}"`
    : 'stroke="none"';
  const fillAttr = v.fill ? `fill="${fillColor}"` : 'fill="none"';

  let dashAttr = "";
  if (v.dash && v.dash.length > 0) {
    const scaledDash = v.dash.map((d) => scale(d, zoomLevel).toFixed(2)).join(" ");
    dashAttr = ` stroke-dasharray="${scaledDash}"`;
  }

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${svgWidth}" height="${svgHeight}" viewBox="0 0 ${svgWidth} ${svgHeight}"><path d="${pathD}" ${strokeAttr} ${fillAttr}${dashAttr} /></svg>`;

  return `<div style="${styles.join("; ")}">${svg}</div>`;
}

// ---------------------------------------------------------------------------
// Table rendering
// ---------------------------------------------------------------------------

/**
 * Determine if a table can be rendered as a proper grid table.
 *
 * Grid tables use native <table> with <colgroup>. They require regular column
 * positions and row positions. Tables with irregular or missing positions
 * should fall back to legacy (absolute-positioned div) rendering.
 */
function isGridTable(table: TableDefinition): boolean {
  if (table.col_positions.length < 2 || table.row_positions.length < 2) {
    return false;
  }

  // Check that row_positions are monotonically increasing.
  for (let i = 1; i < table.row_positions.length; i++) {
    if (table.row_positions[i] <= table.row_positions[i - 1]) return false;
  }

  // Check that col_positions are monotonically increasing.
  for (let i = 1; i < table.col_positions.length; i++) {
    if (table.col_positions[i] <= table.col_positions[i - 1]) return false;
  }

  return true;
}

// ---------------------------------------------------------------------------
// Per-cell rendering helpers
// ---------------------------------------------------------------------------

interface CellBounds {
  top: number;
  left: number;
  bottom: number;
  right: number;
  width: number;
  height: number;
}

/**
 * Compute cell bounds from row/col positions and spans.
 *
 * Uses the table's row_positions and col_positions arrays plus the cell's
 * row_span / col_span to derive the absolute top/left/bottom/right of a cell
 * in PDF coordinate space.
 */
function getTableCellBounds(
  cell: TableCell,
  rowPositions: number[],
  colPositions: number[],
  tableRect: { top: number; left: number; bottom: number; right: number },
): CellBounds {
  const cellTop =
    cell.row_idx < rowPositions.length
      ? rowPositions[cell.row_idx]
      : tableRect.top;

  const cellLeft =
    cell.col_idx < colPositions.length
      ? colPositions[cell.col_idx]
      : tableRect.left;

  // Determine bottom from row span.
  let cellBottom = tableRect.bottom;
  if (cell.row_span > 0) {
    const endRowIdx = Math.min(
      cell.row_idx + cell.row_span,
      rowPositions.length,
    );
    if (endRowIdx < rowPositions.length) {
      cellBottom = rowPositions[endRowIdx];
    }
  }

  // Determine right from col span.
  let cellRight = tableRect.right;
  if (cell.col_span > 0) {
    const endColIdx = Math.min(
      cell.col_idx + cell.col_span,
      colPositions.length,
    );
    if (endColIdx < colPositions.length) {
      cellRight = colPositions[endColIdx];
    }
  }

  return {
    top: cellTop,
    left: cellLeft,
    bottom: cellBottom,
    right: cellRight,
    width: cellRight - cellLeft,
    height: cellBottom - cellTop,
  };
}

/**
 * Detect horizontal text alignment for the text elements in a cell.
 *
 * Compares the horizontal positions of text elements relative to cell bounds:
 * - "left":  text starts within 15% of cell left
 * - "right": text ends within 15% of cell right
 * - "center": text is roughly centered (within 25% of center)
 * - "left" by default
 */
function detectTextAlignment(
  textElements: (TextElement | ImageElement)[],
  cellBounds: CellBounds,
): "left" | "right" | "center" {
  if (textElements.length === 0) return "left";

  const textEls = textElements.filter((el): el is TextElement => el.type === "text");
  if (textEls.length === 0) return "left";

  const cellWidth = cellBounds.right - cellBounds.left;
  if (cellWidth <= 0) return "left";

  // Use the last text element (often the most representative for alignment).
  const lastEl = textEls[textEls.length - 1];
  const elRight = lastEl.left + lastEl.width;
  const marginFromLeft = lastEl.left - cellBounds.left;
  const marginFromRight = cellBounds.right - elRight;

  const tolerance = cellWidth * 0.15;
  const centerTolerance = cellWidth * 0.25;
  const centerPos = cellBounds.left + cellWidth / 2;
  const elCenter = lastEl.left + lastEl.width / 2;

  if (marginFromRight <= tolerance && marginFromLeft > tolerance) {
    return "right";
  }
  if (marginFromLeft <= tolerance) {
    return "left";
  }
  if (Math.abs(elCenter - centerPos) <= centerTolerance) {
    return "center";
  }

  return "left";
}

/**
 * Calculate cell padding from the first text element's position.
 *
 * Preserves the PDF's visual spacing by deriving padding from the gap between
 * the cell boundary and the first text element. Falls back to a sensible
 * default (2px 4px) when no text elements exist.
 */
function calculateCellPadding(
  textElements: readonly (TextElement | ImageElement)[],
  cellBounds: CellBounds,
): { top: number; left: number; bottom: number; right: number } {
  const defaultPadding = { top: 2, left: 4, bottom: 2, right: 4 };

  const firstText = textElements.find((el): el is TextElement => el.type === "text");
  if (!firstText) return defaultPadding;

  const paddingTop = Math.max(0, firstText.top - cellBounds.top);
  const paddingLeft = Math.max(0, firstText.left - cellBounds.left);

  // Bottom/right padding: use the last text element.
  const lastText = [...textElements]
    .reverse()
    .find((el): el is TextElement => el.type === "text");
  let paddingBottom = defaultPadding.bottom;
  let paddingRight = defaultPadding.right;

  if (lastText) {
    paddingBottom = Math.max(
      0,
      cellBounds.bottom - (lastText.top + lastText.height),
    );
    paddingRight = Math.max(
      0,
      cellBounds.right - (lastText.left + lastText.width),
    );
  }

  return {
    top: Math.min(paddingTop, cellBounds.height * 0.3),
    left: Math.min(paddingLeft, cellBounds.width * 0.3),
    bottom: Math.min(paddingBottom, cellBounds.height * 0.3),
    right: Math.min(paddingRight, cellBounds.width * 0.3),
  };
}

/**
 * Render a single text element as an inline <span> within a cell.
 *
 * Unlike the page-level renderTextElement (which uses absolute positioning),
 * this renders text as inline flow content with per-element font styling.
 * Each span retains its own font_spec attributes.
 */
function renderCellTextSpan(
  el: TextElement,
  zoomLevel: number,
  fontMapping: Map<string, string>,
): string {
  const styles: string[] = ["white-space: nowrap", "line-height: 1.2"];

  if (el.font_spec) {
    const spec = el.font_spec;
    const family = fontMapping.get(spec.id) || spec.family;
    const fontSize = scale(spec.size, zoomLevel);

    styles.push(`font-family: '${escapeHtml(family)}', sans-serif`);
    styles.push(`font-size: ${fontSize.toFixed(2)}px`);
    styles.push(`color: ${spec.color}`);

    if (spec.is_bold || (spec.font_weight && spec.font_weight >= 700)) {
      styles.push("font-weight: bold");
    } else if (spec.font_weight) {
      styles.push(`font-weight: ${spec.font_weight}`);
    }

    if (spec.is_italic) {
      styles.push("font-style: italic");
    }
  } else {
    const fontSize = scale(el.font_size, zoomLevel);
    styles.push(`font-size: ${fontSize.toFixed(2)}px`);
  }

  const styleAttr = styles.join("; ");
  return `<span style="${styleAttr}">${escapeHtml(el.text)}</span>`;
}

/**
 * Render a single image element as an inline <img> within a cell.
 *
 * Positions the image relative to the cell using absolute positioning,
 * offset from the cell's origin.
 */
function renderCellImage(
  el: ImageElement,
  cellBounds: CellBounds,
  zoomLevel: number,
): string {
  // Compute offset from cell origin.
  const offsetY = el.top - cellBounds.top;
  const offsetX = el.left - cellBounds.left;
  const imgTop = scale(offsetY, zoomLevel);
  const imgLeft = scale(offsetX, zoomLevel);
  const imgWidth = scale(el.width, zoomLevel);
  const imgHeight = scale(el.height, zoomLevel);

  const styles = [
    "position: absolute",
    `top: ${imgTop.toFixed(2)}px`,
    `left: ${imgLeft.toFixed(2)}px`,
    `width: ${imgWidth.toFixed(2)}px`,
    `height: ${imgHeight.toFixed(2)}px`,
  ];

  return `<img src="${el.src}" style="${styles.join("; ")}" alt="embedded image" />`;
}

/**
 * Render a cell with per-cell padding, alignment detection, per-element font
 * styles, and inline image support.
 *
 * The cell is rendered as a `<td>` with:
 * - Padding calculated from the first text element's position relative to
 *   cell bounds, preserving the PDF's visual spacing.
 * - Text alignment detected from text element positions (left/right/center).
 * - Each text element rendered as an inline `<span>` retaining its own
 *   font spec (family, size, color, bold, italic).
 * - Images rendered inline with absolute positioning relative to the cell.
 */
function renderCell(
  cell: TableCell,
  zoomLevel: number,
  fontMapping: Map<string, string>,
  table?: TableDefinition,
): string {
  const attrs: string[] = [];

  // HTML rowspan/colspan attributes.
  if (cell.row_span > 1) {
    attrs.push(`rowspan="${cell.row_span}"`);
  }
  if (cell.col_span > 1) {
    attrs.push(`colspan="${cell.col_span}"`);
  }

  // Compute cell bounds if table context is available.
  let cellBounds: CellBounds | null = null;
  if (table) {
    cellBounds = getTableCellBounds(
      cell,
      table.row_positions,
      table.col_positions,
      table.rect,
    );
  }

  // Border styles.
  const borderStyles: string[] = [];
  if (cell.style_top) borderStyles.push(`border-top: ${cell.style_top}`);
  if (cell.style_bottom)
    borderStyles.push(`border-bottom: ${cell.style_bottom}`);
  if (cell.style_left) borderStyles.push(`border-left: ${cell.style_left}`);
  if (cell.style_right)
    borderStyles.push(`border-right: ${cell.style_right}`);

  // Background color.
  if (cell.background_color) {
    borderStyles.push(`background-color: ${cell.background_color}`);
  }

  // Vertical alignment.
  borderStyles.push("vertical-align: top");

  // Calculate padding from text element positions.
  if (cellBounds) {
    const padding = calculateCellPadding(cell.text_elements, cellBounds);
    borderStyles.push(
      `padding: ${padding.top.toFixed(1)}px ${padding.right.toFixed(1)}px ${padding.bottom.toFixed(1)}px ${padding.left.toFixed(1)}px`,
    );
  } else {
    borderStyles.push("padding: 2px 4px");
  }

  // Detect text alignment.
  if (cellBounds) {
    const alignment = detectTextAlignment(cell.text_elements, cellBounds);
    borderStyles.push(`text-align: ${alignment}`);
  }

  // Position relative so absolutely-positioned images are contained.
  borderStyles.push("position: relative");
  borderStyles.push("overflow: hidden");

  const styleAttr =
    borderStyles.length > 0 ? ` style="${borderStyles.join("; ")}"` : "";
  const attrStr = attrs.length > 0 ? ` ${attrs.join(" ")}` : "";

  // Render text elements as inline spans, images inline.
  const innerContent = cell.text_elements
    .map((el) => {
      if (el.type === "text") {
        return renderCellTextSpan(el, zoomLevel, fontMapping);
      }
      if (el.type === "image") {
        return cellBounds
          ? renderCellImage(el, cellBounds, zoomLevel)
          : "";
      }
      return "";
    })
    .join("\n");

  return `<td${attrStr}${styleAttr}>${innerContent}</td>`;
}

/**
 * Render a table as a proper grid using <table>, <colgroup>, and <col>.
 *
 * Produces a positioned container div with:
 * - <colgroup> with <col> elements sized from col_positions
 * - <tr> rows built from row_positions
 * - <td> cells with colspan/rowspan, border styles, and background colors
 * - data-col-widths attribute for frontend JS consumption
 *
 * @param table - The table definition to render.
 * @param zoomLevel - Zoom multiplier.
 * @param fontMapping - Font ID to CSS family name mapping.
 * @returns HTML string for the grid table.
 */
export function renderGridTable(
  table: TableDefinition,
  zoomLevel: number,
  fontMapping: Map<string, string>,
): string {
  const top = scale(table.rect.top, zoomLevel);
  const left = scale(table.rect.left, zoomLevel);
  const width = scale(table.rect.right - table.rect.left, zoomLevel);
  const height = scale(table.rect.bottom - table.rect.top, zoomLevel);

  const containerStyles = [
    "position: absolute",
    `top: ${top.toFixed(2)}px`,
    `left: ${left.toFixed(2)}px`,
    `width: ${width.toFixed(2)}px`,
    `height: ${height.toFixed(2)}px`,
    "border-collapse: collapse",
  ];

  // Compute column widths from col_positions.
  const colWidths: number[] = [];
  for (let i = 0; i < table.col_positions.length; i++) {
    const colStart = table.col_positions[i];
    const colEnd =
      i < table.col_positions.length - 1
        ? table.col_positions[i + 1]
        : table.rect.right;
    colWidths.push(scale(colEnd - colStart, zoomLevel));
  }

  // Build row data structure from cells.
  const numRows = table.row_positions.length;
  const numCols = table.col_positions.length;
  const grid: (TableCell | null)[][] = Array.from({ length: numRows }, () =>
    Array(numCols).fill(null),
  );

  for (const cell of table.cells) {
    if (cell.row_idx < numRows && cell.col_idx < numCols) {
      grid[cell.row_idx][cell.col_idx] = cell;
    }
  }

  // Build colgroup.
  const colgroupCols = colWidths
    .map((w) => `<col style="width: ${w.toFixed(2)}px" />`)
    .join("\n      ");
  const colgroup = `<colgroup>\n      ${colgroupCols}\n    </colgroup>`;

  // Build rows.
  const rows: string[] = [];
  for (let r = 0; r < numRows; r++) {
    const cells: string[] = [];
    for (let c = 0; c < numCols; c++) {
      const cell = grid[r][c];
      if (cell) {
        cells.push(renderCell(cell, zoomLevel, fontMapping, table));
      } else {
        cells.push("<td></td>");
      }
    }
    rows.push(`    <tr>\n      ${cells.join("\n      ")}\n    </tr>`);
  }

  // Data attribute for column widths (used by frontend JS).
  const colWidthsAttr = colWidths.map((w) => w.toFixed(2)).join(",");

  return (
    `<div style="${containerStyles.join("; ")}" data-col-widths="${colWidthsAttr}">\n` +
    `    <table style="width: 100%; height: 100%; border-collapse: collapse">\n` +
    `      ${colgroup}\n` +
    `      ${rows.join("\n")}\n` +
    `    </table>\n` +
    `  </div>`
  );
}

/**
 * Render a table using legacy absolute-positioned divs (no <table> element).
 *
 * Used for tables that can't be rendered as proper grids — e.g., tables with
 * irregular positioning, merged cells that don't align to a grid, or tables
 * extracted from non-tabular layouts. Each cell becomes an absolutely positioned
 * div within a container.
 *
 * @param table - The table definition to render.
 * @param zoomLevel - Zoom multiplier.
 * @param fontMapping - Font ID to CSS family name mapping.
 * @returns HTML string for the legacy table.
 */
export function renderLegacyTable(
  table: TableDefinition,
  zoomLevel: number,
  fontMapping: Map<string, string>,
): string {
  const top = scale(table.rect.top, zoomLevel);
  const left = scale(table.rect.left, zoomLevel);
  const width = scale(table.rect.right - table.rect.left, zoomLevel);
  const height = scale(table.rect.bottom - table.rect.top, zoomLevel);

  const containerStyles = [
    "position: absolute",
    `top: ${top.toFixed(2)}px`,
    `left: ${left.toFixed(2)}px`,
    `width: ${width.toFixed(2)}px`,
    `height: ${height.toFixed(2)}px`,
  ];

  const renderedCells: string[] = [];

  for (const cell of table.cells) {
    // Compute cell position from row/col indices and positions.
    const cellBounds = getTableCellBounds(
      cell,
      table.row_positions,
      table.col_positions,
      table.rect,
    );

    const cellStyles: string[] = [
      "position: absolute",
      `top: ${scale(cellBounds.top, zoomLevel).toFixed(2)}px`,
      `left: ${scale(cellBounds.left, zoomLevel).toFixed(2)}px`,
      `width: ${scale(cellBounds.width, zoomLevel).toFixed(2)}px`,
      `height: ${scale(cellBounds.height, zoomLevel).toFixed(2)}px`,
      "overflow: hidden",
    ];

    // Border styles.
    if (cell.style_top) cellStyles.push(`border-top: ${cell.style_top}`);
    if (cell.style_bottom)
      cellStyles.push(`border-bottom: ${cell.style_bottom}`);
    if (cell.style_left) cellStyles.push(`border-left: ${cell.style_left}`);
    if (cell.style_right)
      cellStyles.push(`border-right: ${cell.style_right}`);

    // Background color.
    if (cell.background_color) {
      cellStyles.push(`background-color: ${cell.background_color}`);
    }

    // Calculate padding from text element positions.
    const padding = calculateCellPadding(cell.text_elements, cellBounds);
    cellStyles.push(
      `padding: ${padding.top.toFixed(1)}px ${padding.right.toFixed(1)}px ${padding.bottom.toFixed(1)}px ${padding.left.toFixed(1)}px`,
    );

    // Detect text alignment.
    const alignment = detectTextAlignment(cell.text_elements, cellBounds);
    cellStyles.push(`text-align: ${alignment}`);

    // Position relative so absolutely-positioned images are contained.
    cellStyles.push("position: relative");

    // Render text elements as inline spans, images inline.
    const innerContent = cell.text_elements
      .map((el) => {
        if (el.type === "text") {
          return renderCellTextSpan(el, zoomLevel, fontMapping);
        }
        if (el.type === "image") {
          return renderCellImage(el, cellBounds, zoomLevel);
        }
        return "";
      })
      .join("\n");

    renderedCells.push(
      `<div style="${cellStyles.join("; ")}">${innerContent}</div>`,
    );
  }

  return (
    `<div style="${containerStyles.join("; ")}">\n` +
    `    ${renderedCells.join("\n    ")}\n` +
    `  </div>`
  );
}

/**
 * Render a table — delegates to grid or legacy based on table structure.
 *
 * @param table - The table definition to render.
 * @param zoomLevel - Zoom multiplier.
 * @param fontMapping - Font ID to CSS family name mapping.
 * @returns HTML string for the table.
 */
function renderTable(
  table: TableDefinition,
  zoomLevel: number,
  fontMapping: Map<string, string>,
): string {
  if (isGridTable(table)) {
    return renderGridTable(table, zoomLevel, fontMapping);
  }
  return renderLegacyTable(table, zoomLevel, fontMapping);
}

// ---------------------------------------------------------------------------
// Main export
// ---------------------------------------------------------------------------

/**
 * Render a single page to HTML.
 *
 * Orchestrates the rendering of all extracted page data (text, images, tables,
 * vectors) into a complete HTML string with absolute positioning to preserve
 * the original PDF layout.
 *
 * @param options - All extracted data for a single page plus rendering config.
 * @returns Complete HTML string for the page.
 */
export function renderPageToHtml(options: RenderPageOptions): string {
  const {
    pageWidth,
    pageHeight,
    zoomLevel,
    fontMapping,
  } = options;

  const scaledWidth = scale(pageWidth, zoomLevel);
  const scaledHeight = scale(pageHeight, zoomLevel);

  const elements = collectSortableElements(options);

  const renderedElements: string[] = [];
  for (const item of elements) {
    switch (item.type) {
      case "text":
        renderedElements.push(
          renderTextElement(item.data as TextElement, zoomLevel, fontMapping),
        );
        break;
      case "image":
        renderedElements.push(
          renderImageElement(item.data as ImageElement, zoomLevel),
        );
        break;
      case "table":
        renderedElements.push(
          renderTable(item.data as TableDefinition, zoomLevel, fontMapping),
        );
        break;
      case "vector":
        renderedElements.push(
          renderVectorElement(item.data as VectorElement, zoomLevel),
        );
        break;
    }
  }

  const pageContent = renderedElements.join("\n  ");

  return (
    `<!DOCTYPE html>\n` +
    `<html lang="en">\n` +
    `<head>\n` +
    `  <meta charset="UTF-8" />\n` +
    `  <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n` +
    `  <style>\n` +
    `    * { margin: 0; padding: 0; box-sizing: border-box; }\n` +
    `    body { position: relative; }\n` +
    `    .page-container {\n` +
    `      position: relative;\n` +
    `      width: ${scaledWidth.toFixed(2)}px;\n` +
    `      height: ${scaledHeight.toFixed(2)}px;\n` +
    `      overflow: hidden;\n` +
    `      background: white;\n` +
    `    }\n` +
    `  </style>\n` +
    `</head>\n` +
    `<body>\n` +
    `  <div class="page-container">\n` +
    `  ${pageContent}\n` +
    `  </div>\n` +
    `</body>\n` +
    `</html>`
  );
}

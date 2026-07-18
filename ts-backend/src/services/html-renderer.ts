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

function renderCell(
  cell: TableCell,
  zoomLevel: number,
  fontMapping: Map<string, string>,
): string {
  const styles: string[] = [];

  if (cell.row_span > 1) {
    styles.push(`row-span: ${cell.row_span}`);
  }
  if (cell.col_span > 1) {
    styles.push(`col-span: ${cell.col_span}`);
  }

  // Border styles.
  if (cell.style_top) styles.push(`border-top: ${cell.style_top}`);
  if (cell.style_bottom) styles.push(`border-bottom: ${cell.style_bottom}`);
  if (cell.style_left) styles.push(`border-left: ${cell.style_left}`);
  if (cell.style_right) styles.push(`border-right: ${cell.style_right}`);

  // Background color.
  if (cell.background_color) {
    styles.push(`background-color: ${cell.background_color}`);
  }

  // Vertical alignment for text content.
  styles.push("vertical-align: top");
  styles.push("padding: 2px 4px");

  const styleAttr = styles.length > 0 ? ` style="${styles.join("; ")}"` : "";

  // Render text elements within the cell.
  const innerContent = cell.text_elements
    .map((el) => {
      if (el.type === "text") {
        return renderTextElement(el, zoomLevel, fontMapping);
      }
      if (el.type === "image") {
        return renderImageElement(el, zoomLevel);
      }
      return "";
    })
    .join("\n");

  return `<td${styleAttr}>${innerContent}</td>`;
}

function renderTable(
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
        cells.push(renderCell(cell, zoomLevel, fontMapping));
      } else {
        // Empty cell placeholder.
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

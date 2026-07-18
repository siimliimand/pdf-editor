import type {
  VectorElement,
  Element,
  TableDefinition,
  TableCell,
} from '../models/types';
import {
  isHorizontalVector,
  isVerticalVector,
  getVectorWidth,
  getVectorHeight,
} from '../models/types';
import { TABLE_DETECTION } from '../models/constants';

// ---------------------------------------------------------------------------
// Internal types
// ---------------------------------------------------------------------------

interface LineCluster {
  hLines: VectorElement[];
  top: number;
  bottom: number;
  left: number;
  right: number;
}

// ---------------------------------------------------------------------------
// Classification
// ---------------------------------------------------------------------------

function classifyVectors(vectors: VectorElement[]): {
  horizontalLines: VectorElement[];
  verticalLines: VectorElement[];
  filledRects: VectorElement[];
} {
  const horizontalLines: VectorElement[] = [];
  const verticalLines: VectorElement[] = [];
  const filledRects: VectorElement[] = [];

  for (const v of vectors) {
    if (isHorizontalVector(v)) {
      horizontalLines.push(v);
    } else if (isVerticalVector(v)) {
      verticalLines.push(v);
    } else if (
      v.fill &&
      getVectorWidth(v) > TABLE_DETECTION.MIN_LINE_LENGTH &&
      getVectorHeight(v) > TABLE_DETECTION.MIN_LINE_LENGTH
    ) {
      filledRects.push(v);
    }
  }

  return { horizontalLines, verticalLines, filledRects };
}

// ---------------------------------------------------------------------------
// Clustering
// ---------------------------------------------------------------------------

function clusterHorizontalLines(
  hLines: VectorElement[],
  vLines: VectorElement[],
): LineCluster[] {
  if (hLines.length === 0) return [];

  const sorted = [...hLines].sort((a, b) => a.y0 - b.y0);
  const clusters: LineCluster[] = [];
  let currentGroup: VectorElement[] = [sorted[0]];

  for (let i = 1; i < sorted.length; i++) {
    const line = sorted[i];
    const lastLine = currentGroup[currentGroup.length - 1];
    const gap = line.y0 - lastLine.y0;

    if (gap > 80) {
      if (currentGroup.length >= 2) {
        clusters.push(buildCluster(currentGroup));
      }
      currentGroup = [line];
    } else if (gap <= 60) {
      currentGroup.push(line);
    } else {
      if (hasVerticalContinuity(currentGroup, line, vLines)) {
        currentGroup.push(line);
      } else {
        if (currentGroup.length >= 2) {
          clusters.push(buildCluster(currentGroup));
        }
        currentGroup = [line];
      }
    }
  }

  if (currentGroup.length >= 2) {
    clusters.push(buildCluster(currentGroup));
  }

  return clusters;
}

function buildCluster(lines: VectorElement[]): LineCluster {
  let top = Infinity;
  let bottom = -Infinity;
  let left = Infinity;
  let right = -Infinity;

  for (const l of lines) {
    if (l.y0 < top) top = l.y0;
    if (l.y0 > bottom) bottom = l.y0;
    if (l.x0 < left) left = l.x0;
    if (l.x1 > right) right = l.x1;
  }

  return { hLines: lines, top, bottom, left, right };
}

function hasVerticalContinuity(
  currentGroup: VectorElement[],
  newLine: VectorElement,
  vLines: VectorElement[],
): boolean {
  if (currentGroup.length === 0) return false;

  const groupTop = Math.min(...currentGroup.map((l) => l.y0));
  const groupBottom = Math.max(...currentGroup.map((l) => l.y0));
  const groupLeft = Math.min(...currentGroup.map((l) => l.x0));
  const groupRight = Math.max(...currentGroup.map((l) => l.x1));

  for (const v of vLines) {
    const vX = v.x0;
    const inGroupX = vX >= groupLeft - 5 && vX <= groupRight + 5;
    const inLineX = vX >= newLine.x0 - 5 && vX <= newLine.x1 + 5;

    if (inGroupX || inLineX) {
      if (v.y0 <= groupBottom + 5 && v.y1 >= newLine.y0 - 5) {
        return true;
      }
    }
  }

  return false;
}

// ---------------------------------------------------------------------------
// Vertical line analysis
// ---------------------------------------------------------------------------

function findRelevantVerticalLines(
  cluster: LineCluster,
  vLines: VectorElement[],
): VectorElement[] {
  return vLines.filter(
    (v) =>
      v.y0 < cluster.bottom + 5 &&
      v.y1 > cluster.top - 5 &&
      cluster.left - 5 < v.x0 &&
      v.x0 < cluster.right + 5,
  );
}

function hasInternalVerticalLines(
  cluster: LineCluster,
  relevantVLines: VectorElement[],
): boolean {
  if (relevantVLines.length === 0) return false;

  const xCoords = [
    ...new Set(relevantVLines.map((v) => v.x0)),
  ].sort((a, b) => a - b);

  if (xCoords.length <= 2) return false;

  const EDGE_THRESHOLD = 10;
  return xCoords.some(
    (x) => x > cluster.left + EDGE_THRESHOLD && x < cluster.right - EDGE_THRESHOLD,
  );
}

// ---------------------------------------------------------------------------
// Detection strategies (stubs — delegated to separate modules)
// ---------------------------------------------------------------------------

function buildGrid(
  cluster: LineCluster,
  relevantVLines: VectorElement[],
): { row_positions: number[]; col_positions: number[]; cells: TableCell[] } {
  const row_positions = [...new Set(cluster.hLines.map((l) => l.y0))].sort(
    (a, b) => a - b,
  );

  const colXFromV = new Set(relevantVLines.map((v) => v.x0));
  const colXFromH = new Set<number>();
  for (const l of cluster.hLines) {
    colXFromH.add(l.x0);
    colXFromH.add(l.x1);
  }

  const allColX = [...colXFromV].concat([...colXFromH]);
  const col_positions = [...new Set(allColX)].sort((a, b) => a - b);

  if (!col_positions.includes(cluster.left)) col_positions.unshift(cluster.left);
  if (!col_positions.includes(cluster.right)) col_positions.push(cluster.right);
  col_positions.sort((a, b) => a - b);

  const cells: TableCell[] = [];
  for (let r = 0; r < row_positions.length - 1; r++) {
    for (let c = 0; c < col_positions.length - 1; c++) {
      cells.push({
        row_idx: r,
        col_idx: c,
        row_span: 1,
        col_span: 1,
        text_elements: [],
      });
    }
  }

  return { row_positions, col_positions, cells };
}

function mergeCells(
  cells: TableCell[],
  numRows: number,
  numCols: number,
): TableCell[] {
  return cells.filter((c) => c.row_span > 0 && c.col_span > 0);
}

function detectHorizontalTable(
  cluster: LineCluster,
  textElements: Element[],
): TableDefinition | null {
  if (cluster.hLines.length < 2) return null;

  const row_positions = [...new Set(cluster.hLines.map((l) => l.y0))].sort(
    (a, b) => a - b,
  );

  if (row_positions.length < 2) return null;

  const PADDING_X = 300;
  const MARGIN = 5;
  const textsInTable: Element[] = [];

  for (const el of textElements) {
    if (el.type !== 'text') continue;

    const vertMatch =
      el.top >= row_positions[0] - MARGIN &&
      el.top <= row_positions[row_positions.length - 1] + MARGIN;
    const horizMatch =
      el.left >= cluster.left - PADDING_X &&
      el.left <= cluster.right + PADDING_X;

    if (vertMatch && horizMatch) {
      textsInTable.push(el);
    }
  }

  if (textsInTable.length === 0) return null;

  let tableLeft = cluster.left;
  let tableRight = cluster.right;
  for (const el of textsInTable) {
    if (el.type !== 'text') continue;
    if (el.left < tableLeft) tableLeft = el.left;
    if (el.left + el.width > tableRight) tableRight = el.left + el.width;
  }

  const colEndpoints = new Set<number>();
  for (const l of cluster.hLines) {
    colEndpoints.add(l.x0);
    colEndpoints.add(l.x1);
  }
  const col_positions = [...colEndpoints].sort((a, b) => a - b);

  if (col_positions.length <= 2) {
    return null;
  }

  if (row_positions.length < 2 || col_positions.length < 2) return null;

  const cells: TableCell[] = [];
  for (let r = 0; r < row_positions.length - 1; r++) {
    for (let c = 0; c < col_positions.length - 1; c++) {
      cells.push({
        row_idx: r,
        col_idx: c,
        row_span: 1,
        col_span: 1,
        text_elements: [],
      });
    }
  }

  return {
    rect: {
      top: row_positions[0],
      left: col_positions[0],
      bottom: row_positions[row_positions.length - 1],
      right: col_positions[col_positions.length - 1],
    },
    row_positions,
    col_positions,
    cells,
  };
}

// ---------------------------------------------------------------------------
// Main orchestrator
// ---------------------------------------------------------------------------

/**
 * Detect tables in a page by analyzing vector lines and text elements.
 *
 * Strategy 1 (grid): clusters horizontal lines, finds intersecting vertical
 * lines, and builds a grid from their intersections.
 *
 * Strategy 2 (horizontal-only): when no internal vertical lines exist,
 * infers columns from horizontal line segment endpoints and text positions.
 *
 * @param vectors      Vector elements extracted from the page.
 * @param textElements Text elements extracted from the page.
 * @returns            Array of detected table definitions.
 */
export function detectTables(
  vectors: VectorElement[],
  textElements: Element[],
): TableDefinition[] {
  const { horizontalLines, verticalLines, filledRects } =
    classifyVectors(vectors);

  const clusters = clusterHorizontalLines(horizontalLines, verticalLines);
  const tables: TableDefinition[] = [];

  for (const cluster of clusters) {
    const relevantVLines = findRelevantVerticalLines(cluster, verticalLines);
    const hasInternal = hasInternalVerticalLines(cluster, relevantVLines);

    if (relevantVLines.length > 0 && hasInternal) {
      const { row_positions, col_positions, cells } = buildGrid(
        cluster,
        relevantVLines,
      );

      const mergedCells = mergeCells(
        cells,
        row_positions.length - 1,
        col_positions.length - 1,
      );

      if (row_positions.length === 0 || col_positions.length === 0) continue;

      tables.push({
        rect: {
          top: row_positions[0],
          left: col_positions[0],
          bottom: row_positions[row_positions.length - 1],
          right: col_positions[col_positions.length - 1],
        },
        row_positions,
        col_positions,
        cells: mergedCells,
      });
    } else {
      const hTable = detectHorizontalTable(cluster, textElements);
      if (hTable) {
        tables.push(hTable);
      }
    }
  }

  return tables;
}

import type { TableDefinition, TableCell } from "../models/types";
import { TABLE_DETECTION } from "../models/constants";

function xRangesOverlap(a: TableDefinition, b: TableDefinition): boolean {
  return a.rect.left < b.rect.right && b.rect.left < a.rect.right;
}

function mergeTwoTables(top: TableDefinition, bottom: TableDefinition): TableDefinition {
  const mergedColPositions = Array.from(
    new Set([...top.col_positions, ...bottom.col_positions]),
  ).sort((a, b) => a - b);

  const mergedRowPositions = Array.from(
    new Set([...top.row_positions, ...bottom.row_positions]),
  ).sort((a, b) => a - b);

  const mergedCells: TableCell[] = [];

  for (const cells of [top.cells, bottom.cells]) {
    for (const cell of cells) {
      mergedCells.push({ ...cell });
    }
  }

  return {
    rect: {
      top: top.rect.top,
      left: Math.min(top.rect.left, bottom.rect.left),
      bottom: bottom.rect.bottom,
      right: Math.max(top.rect.right, bottom.rect.right),
    },
    row_positions: mergedRowPositions,
    col_positions: mergedColPositions,
    cells: mergedCells,
  };
}

export function mergeAdjacentTables(tables: TableDefinition[]): TableDefinition[] {
  if (tables.length < 2) return tables;

  const sorted = [...tables].sort((a, b) => a.rect.top - b.rect.top);

  let merged = true;
  while (merged) {
    merged = false;
    const result: TableDefinition[] = [];

    for (let i = 0; i < sorted.length; i++) {
      if (result.length === 0) {
        result.push(sorted[i]);
        continue;
      }

      const prev = result[result.length - 1];
      const curr = sorted[i];

      const verticalGap = curr.rect.top - prev.rect.bottom;
      const withinThreshold = verticalGap < TABLE_DETECTION.CELL_MERGE_THRESHOLD;
      const horizontallyOverlapping = xRangesOverlap(prev, curr);

      if (withinThreshold && horizontallyOverlapping) {
        result[result.length - 1] = mergeTwoTables(prev, curr);
        merged = true;
      } else {
        result.push(curr);
      }
    }

    sorted.length = 0;
    sorted.push(...result);
  }

  return sorted;
}

import * as fs from "node:fs";
import * as path from "node:path";

const FIXTURES_DIR = path.resolve(import.meta.dirname, "fixtures");

/**
 * Load a test PDF from the fixtures directory.
 */
export function loadFixturePdf(filename: string): Uint8Array {
  const filePath = path.join(FIXTURES_DIR, filename);
  if (!fs.existsSync(filePath)) {
    throw new Error(`Fixture not found: ${filePath}`);
  }
  return new Uint8Array(fs.readFileSync(filePath));
}

/**
 * Load an expected HTML fixture for golden-file comparison.
 */
export function loadExpectedHtml(filename: string): string {
  const filePath = path.join(FIXTURES_DIR, "expected", filename);
  if (!fs.existsSync(filePath)) {
    throw new Error(`Expected HTML fixture not found: ${filePath}`);
  }
  return fs.readFileSync(filePath, "utf-8");
}

/**
 * Normalize HTML for comparison by collapsing whitespace and stripping
 * insignificant differences.
 */
export function normalizeHtml(html: string): string {
  // Split by tags, strip whitespace from text parts, rejoin
  const parts = html.split(/(<[^>]+>)/);
  return parts
    .map((p) => (p.startsWith("<") ? p : p.trim()))
    .join("")
    .replace(/\s+/g, " ")
    .trim();
}

/**
 * Compare two HTML strings after normalization.
 * Returns null if equal, or a diff string describing the differences.
 */
export function compareHtml(actual: string, expected: string): string | null {
  const normActual = normalizeHtml(actual);
  const normExpected = normalizeHtml(expected);

  if (normActual === normExpected) {
    return null;
  }

  const maxLen = Math.max(normActual.length, normExpected.length);
  const sampleLen = 200;
  const diffLines = [
    `HTML output differs (${normActual.length} vs ${normExpected.length} chars)`,
    `--- actual (first ${sampleLen})`,
    normActual.slice(0, sampleLen),
    `--- expected (first ${sampleLen})`,
    normExpected.slice(0, sampleLen),
  ];
  return diffLines.join("\n");
}

/**
 * Run the conversion pipeline on a PDF buffer.
 *
 * Currently a stub that documents the intended flow:
 *   1. Parse PDF with pdfjs-dist
 *   2. Extract fonts, images, vectors per page
 *   3. Detect tables
 *   4. Render HTML
 *
 * Replace with real imports once the pipeline is wired.
 */
export async function runConversion(pdfBytes: Uint8Array): Promise<string> {
  // TODO: Replace with real pipeline import once available
  // import { PdfService } from "../src/services/pdf-service";
  // const service = new PdfService();
  // return service.convertToHtml(pdfBytes);

  throw new Error(
    "runConversion is a stub — wire up the real conversion pipeline",
  );
}

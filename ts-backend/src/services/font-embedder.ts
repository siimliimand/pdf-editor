/**
 * Font Embedder — Convert extracted fonts to base64 data-URI @font-face CSS.
 *
 * Takes FontSpec metadata (from font-extractor) and raw font bytes,
 * producing a CSS string with @font-face declarations and a mapping
 * from original font names to CSS font-family values.
 */

import type { FontSpec } from "../models/types";
import {
  getFontWeightFromName,
  getFontStyleFromName,
  extractFontFamilyFromName,
} from "./font-extractor";

// ---------------------------------------------------------------------------
// MIME / format helpers
// ---------------------------------------------------------------------------

const MIME_MAP: Record<string, string> = {
  ttf: "font/truetype",
  otf: "font/opentype",
  woff: "font/woff",
  woff2: "font/woff2",
};

const FORMAT_MAP: Record<string, string> = {
  ttf: "truetype",
  otf: "opentype",
  woff: "woff",
  woff2: "woff2",
};

/**
 * Return the CSS `format()` value for a given file extension.
 */
export function getFontFormat(ext: string): string {
  return FORMAT_MAP[ext.toLowerCase()] ?? "truetype";
}

/**
 * Convert raw font bytes + extension into a `data:` URI with base64 encoding.
 */
export function fontToBase64(data: Uint8Array, ext: string): string {
  const mime = MIME_MAP[ext.toLowerCase()] ?? "font/truetype";

  // Uint8Array → binary string → base64
  let binary = "";
  for (let i = 0; i < data.length; i++) {
    binary += String.fromCharCode(data[i]);
  }
  const b64 = btoa(binary);

  return `data:${mime};base64,${b64}`;
}

// ---------------------------------------------------------------------------
// Main embedder
// ---------------------------------------------------------------------------

export interface EmbedResult {
  /** Complete @font-face CSS string (may be empty if no fonts provided). */
  css: string;
  /**
   * Mapping from each FontSpec.id (raw pdf.js name) to the CSS font-family
   * value that should be used in element styles.
   */
  mapping: Map<string, string>;
}

/**
 * Build @font-face CSS from extracted fonts and their raw bytes.
 *
 * @param fonts       - FontSpec[] produced by font-extractor
 * @param fontDataMap - Map from FontSpec.id → raw font bytes (Uint8Array)
 * @param ext         - Font file extension (default "ttf")
 * @returns An EmbedResult containing the CSS string and name mapping.
 */
export function embedFontsToCss(
  fonts: FontSpec[],
  fontDataMap: Map<string, Uint8Array>,
  ext = "ttf",
): EmbedResult {
  const mapping = new Map<string, string>();
  const cssParts: string[] = [];

  for (const font of fonts) {
    const data = fontDataMap.get(font.id);
    if (!data) continue;

    const family = extractFontFamilyFromName(font.id);
    const weight = font.font_weight ?? getFontWeightFromName(font.id);
    const style = font.is_italic ? "italic" : getFontStyleFromName(font.id);
    const dataUri = fontToBase64(data, ext);
    const format = getFontFormat(ext);

    cssParts.push(
      `@font-face {\n  font-family: '${family}';\n  src: url('${dataUri}') format('${format}');\n  font-weight: ${weight};\n  font-style: ${style};\n  font-display: swap;\n}`,
    );

    mapping.set(font.id, family);
  }

  return {
    css: cssParts.join("\n"),
    mapping,
  };
}

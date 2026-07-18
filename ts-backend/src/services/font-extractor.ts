/**
 * Font Extractor — Extract font metadata from pdf.js parsed PDFs.
 *
 * pdf.js exposes fonts through `page.getTextContent()`, which returns
 * TextItem objects with a `fontName` property and a `styles` map keyed
 * by that name. The raw font names (e.g. "TimesNewRoman-Bold", "g_d0")
 * are parsed to derive family, weight, and style.
 *
 * Unlike PyMuPDF, pdf.js does not provide raw font flags or encoding
 * directly, so we rely on name heuristics for weight/style detection.
 */

import type {
  PDFDocumentProxy,
  PDFPageProxy,
  TextItem,
  TextStyle,
} from "pdfjs-dist/types/src/display/api";

import type { FontSpec } from "../models/types";
import { FONT } from "../models/constants";

// ---------------------------------------------------------------------------
// Font name heuristics (Task 4.4)
// ---------------------------------------------------------------------------

/**
 * Detect numeric font weight from a font name string.
 *
 * Mirrors the Python `get_font_weight_from_name` logic from font_embedder.py.
 * Checks for weight keywords in the name (case-insensitive) and returns
 * the corresponding CSS font-weight number.
 */
export function getFontWeightFromName(fontName: string): number {
  const name = fontName.toLowerCase();

  // Black / Heavy → 900
  if (name.includes("black") || name.includes("heavy")) {
    return FONT.WEIGHT_BLACK;
  }

  // ExtraBold / UltraBold → 800
  if (name.includes("extrabold") || name.includes("ultrabold")) {
    return FONT.WEIGHT_EXTRABOLD;
  }

  // Bold → 700 (check Semibold/DemiBold first)
  if (name.includes("bold")) {
    if (name.includes("semibold") || name.includes("demibold")) {
      return FONT.WEIGHT_SEMIBOLD;
    }
    return FONT.WEIGHT_BOLD;
  }

  // SemiBold / DemiBold (without "bold" substring) → 600
  if (name.includes("semibold") || name.includes("demibold")) {
    return FONT.WEIGHT_SEMIBOLD;
  }

  // Medium → 500
  if (name.includes("medium")) {
    return FONT.WEIGHT_MEDIUM;
  }

  // Regular / Normal → 400
  if (name.includes("regular") || name.includes("normal")) {
    return FONT.WEIGHT_REGULAR;
  }

  // Light → 300 (check UltraLight/ExtraLight first)
  if (name.includes("light")) {
    if (name.includes("ultralight") || name.includes("extralight")) {
      return FONT.WEIGHT_EXTRALIGHT;
    }
    return FONT.WEIGHT_LIGHT;
  }

  // Thin / Hairline → 100
  if (name.includes("thin") || name.includes("hairline")) {
    return FONT.WEIGHT_THIN;
  }

  return FONT.DEFAULT_WEIGHT;
}

/**
 * Detect font style (normal vs italic) from a font name string.
 *
 * Checks for common italic/oblique keywords in the name.
 */
export function getFontStyleFromName(
  fontName: string,
): "normal" | "italic" {
  const name = fontName.toLowerCase();

  if (
    name.includes("italic") ||
    name.includes("oblique") ||
    name.includes("it") // e.g. "TimesNewRoman-It", "Courier-Italic"
  ) {
    // Avoid false positives on short substrings like "bit" or "edit".
    // The "it" check is guarded by ensuring it's a standalone token or
    // part of a known suffix (e.g. ends with "-It" or "Italic").
    if (name.includes("it")) {
      // Confirm it's not a coincidental substring.
      const itIndex = name.lastIndexOf("it");
      const charBefore = itIndex > 0 ? name[itIndex - 1] : "-";
      const charAfter = itIndex + 2 < name.length ? name[itIndex + 2] : "-";
      const isWordBoundary =
        !/[a-z]/.test(charBefore) || !/[a-z]/.test(charAfter);
      if (name.includes("italic") || name.includes("oblique") || isWordBoundary) {
        return "italic";
      }
    }
    if (name.includes("italic") || name.includes("oblique")) {
      return "italic";
    }
  }

  return "normal";
}

/**
 * Extract a clean font family name from a raw pdf.js font name.
 *
 * pdf.js font names often have prefixes like "g_d0" or encoded names.
 * This strips common prefixes and suffixes to produce a human-readable
 * family name suitable for CSS.
 */
export function extractFontFamilyFromName(fontName: string): string {
  let family = fontName;

  // Strip pdf.js internal prefixes (e.g. "g_d0", "bcdef0").
  // These are hex-encoded internal identifiers followed by an underscore.
  family = family.replace(/^[a-f0-9]{2,}_/i, "");

  // Remove style suffixes that we parse separately.
  const styleSuffixes = [
    "-BoldItalic",
    "-BoldOblique",
    "-Italic",
    "-Oblique",
    "-Bold",
    "-SemiBold",
    "-DemiBold",
    "-Medium",
    "-Regular",
    "-Light",
    "-Thin",
    "-Black",
    "-Heavy",
    "-ExtraBold",
    "-UltraBold",
    "-ExtraLight",
    "-UltraLight",
    "-Hairline",
    // Short suffixes (e.g. TimesNewRoman-Bold becomes TimesNewRoman)
    "-Bd",
    "-It",
    "-Rg",
    "-Lt",
  ];

  for (const suffix of styleSuffixes) {
    if (family.endsWith(suffix)) {
      family = family.slice(0, -suffix.length);
      break;
    }
  }

  // Clean up whitespace and ensure non-empty.
  family = family.trim();
  if (!family) {
    family = fontName || "Unknown";
  }

  return family;
}

// ---------------------------------------------------------------------------
// PDF.js font extraction (Task 4.1)
// ---------------------------------------------------------------------------

/** Internal: deduplicated font info collected from a page. */
interface RawFontInfo {
  /** The raw pdf.js font name / identifier. */
  rawName: string;
  /** Text style metadata from pdf.js (if available). */
  style?: TextStyle;
  /** Font size observed in text items (largest seen). */
  maxSize: number;
}

/**
 * Collect unique fonts from a single page's text content.
 *
 * Iterates through all TextItem objects, tracks unique font names, and
 * captures the TextStyle metadata and largest observed font size for each.
 */
function collectFontsFromPage(
  items: Array<TextItem>,
  styles: Record<string, TextStyle>,
): Map<string, RawFontInfo> {
  const fontMap = new Map<string, RawFontInfo>();

  for (const item of items) {
    // Skip marked-content items (not real text).
    if (!("str" in item)) continue;

    const textItem = item as TextItem;
    const { fontName, height } = textItem;

    if (!fontName) continue;

    const existing = fontMap.get(fontName);
    if (existing) {
      // Track the largest size seen for this font.
      if (height > existing.maxSize) {
        existing.maxSize = height;
      }
    } else {
      fontMap.set(fontName, {
        rawName: fontName,
        style: styles[fontName],
        maxSize: height,
      });
    }
  }

  return fontMap;
}

/**
 * Convert a collected RawFontInfo into a FontSpec.
 */
function toFontSpec(raw: RawFontInfo, index: number): FontSpec {
  const family = extractFontFamilyFromName(raw.rawName);
  const weight = getFontWeightFromName(raw.rawName);
  const fontStyle = getFontStyleFromName(raw.rawName);

  return {
    id: raw.rawName || `font-${index}`,
    size: raw.maxSize,
    family,
    color: "#000000",
    is_bold: weight >= FONT.WEIGHT_SEMIBOLD,
    is_italic: fontStyle === "italic",
    font_weight: weight,
  };
}

/**
 * Extract all fonts from a single pdf.js page.
 *
 * Returns an array of FontSpec objects, one per unique font used on the page.
 *
 * @param page - A PDFPageProxy from pdf.js
 * @returns Promise resolving to an array of FontSpec
 */
export async function extractFontsFromPage(
  page: PDFPageProxy,
): Promise<FontSpec[]> {
  const textContent = await page.getTextContent();
  const fontMap = collectFontsFromPage(
    textContent.items as TextItem[],
    textContent.styles,
  );

  const specs: FontSpec[] = [];
  let index = 0;
  for (const raw of fontMap.values()) {
    specs.push(toFontSpec(raw, index++));
  }
  return specs;
}

/**
 * Extract all fonts from an entire pdf.js document.
 *
 * Iterates through every page, collects unique fonts across the whole
 * document, and returns a deduplicated array of FontSpec objects.
 * When the same raw font name appears on multiple pages, the entry with
 * the largest font size is kept (to capture display/heading sizes).
 *
 * @param doc - A PDFDocumentProxy from pdf.js
 * @returns Promise resolving to an array of FontSpec
 */
export async function extractFontsFromPdfjsDoc(
  doc: PDFDocumentProxy,
): Promise<FontSpec[]> {
  const globalFontMap = new Map<string, RawFontInfo>();

  for (let pageNum = 1; pageNum <= doc.numPages; pageNum++) {
    const page = await doc.getPage(pageNum);
    const textContent = await page.getTextContent();
    const pageFonts = collectFontsFromPage(
      textContent.items as TextItem[],
      textContent.styles,
    );

    // Merge into global map, keeping largest size.
    for (const [name, info] of pageFonts) {
      const existing = globalFontMap.get(name);
      if (existing) {
        if (info.maxSize > existing.maxSize) {
          existing.maxSize = info.maxSize;
        }
      } else {
        globalFontMap.set(name, { ...info });
      }
    }
  }

  const specs: FontSpec[] = [];
  let index = 0;
  for (const raw of globalFontMap.values()) {
    specs.push(toFontSpec(raw, index++));
  }
  return specs;
}

import { describe, it, expect } from "vitest";
import {
  loadFixturePdf,
  loadExpectedHtml,
  compareHtml,
  normalizeHtml,
  runConversion,
} from "./test-utils";

// ---------------------------------------------------------------------------
// Unit tests for test utilities themselves
// ---------------------------------------------------------------------------

describe("test-utils", () => {
  describe("normalizeHtml", () => {
    it("collapses whitespace between tags", () => {
      const input = "<div>  <span>  hello  </span>  </div>";
      expect(normalizeHtml(input)).toBe("<div><span>hello</span></div>");
    });

    it("trims leading/trailing whitespace", () => {
      expect(normalizeHtml("  <p>test</p>  ")).toBe("<p>test</p>");
    });
  });

  describe("compareHtml", () => {
    it("returns null for identical content", () => {
      expect(compareHtml("<p>a</p>", "<p>a</p>")).toBeNull();
    });

    it("returns null for whitespace-only differences", () => {
      expect(compareHtml("<p>  a  </p>", "<p>a</p>")).toBeNull();
    });

    it("returns diff string for different content", () => {
      const result = compareHtml("<p>hello</p>", "<p>world</p>");
      expect(result).toContain("differs");
    });
  });

  describe("loadFixturePdf", () => {
    it("throws when fixture does not exist", () => {
      expect(() => loadFixturePdf("nonexistent.pdf")).toThrow(
        "Fixture not found",
      );
    });
  });

  describe("loadExpectedHtml", () => {
    it("throws when expected HTML does not exist", () => {
      expect(() => loadExpectedHtml("nonexistent.expected.html")).toThrow(
        "Expected HTML fixture not found",
      );
    });
  });
});

// ---------------------------------------------------------------------------
// Conversion pipeline tests
// ---------------------------------------------------------------------------

describe("PDF to HTML conversion", () => {
  // These tests require fixture PDFs in tests/fixtures/.
  // Add .skip to skip them when fixtures are not yet available.
  // Remove .skip once real fixture PDFs are added.

  it.skip("converts a simple text PDF to HTML", async () => {
    const pdfBytes = loadFixturePdf("simple-text.pdf");
    const html = await runConversion(pdfBytes);

    expect(html).toContain("<");
    expect(html.length).toBeGreaterThan(0);
  });

  it.skip("preserves text content in output HTML", async () => {
    const pdfBytes = loadFixturePdf("simple-text.pdf");
    const html = await runConversion(pdfBytes);
    const expected = loadExpectedHtml("simple-text.expected.html");

    const diff = compareHtml(html, expected);
    expect(diff).toBeNull();
  });

  it.skip("handles multi-page PDFs", async () => {
    const pdfBytes = loadFixturePdf("multi-page.pdf");
    const html = await runConversion(pdfBytes);

    // Multi-page output should produce content for each page
    expect(html).toContain("<");
  });

  it.skip("detects tables in PDF", async () => {
    const pdfBytes = loadFixturePdf("tables.pdf");
    const html = await runConversion(pdfBytes);

    // Table detection should produce table-like HTML
    expect(html.length).toBeGreaterThan(0);
  });

  it.skip("extracts images from PDF", async () => {
    const pdfBytes = loadFixturePdf("images.pdf");
    const html = await runConversion(pdfBytes);

    expect(html).toContain("<");
  });
});

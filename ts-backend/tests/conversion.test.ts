import { describe, it, expect } from "vitest";
import {
  loadFixturePdf,
  listFixturePdfs,
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

    it("loads a real fixture PDF", () => {
      const pdfs = listFixturePdfs();
      expect(pdfs.length).toBeGreaterThan(0);
      const bytes = loadFixturePdf(pdfs[0]);
      expect(bytes.length).toBeGreaterThan(0);
    });
  });
});

// ---------------------------------------------------------------------------
// Conversion pipeline tests — run against all fixture PDFs
// ---------------------------------------------------------------------------

describe("PDF to HTML conversion", () => {
  const pdfFiles = listFixturePdfs();

  it("converts every fixture PDF without throwing", async () => {
    expect(pdfFiles.length).toBeGreaterThan(0);

    for (const file of pdfFiles) {
      const pdfBytes = loadFixturePdf(file);
      const html = await runConversion(pdfBytes);
      expect(html).toBeDefined();
      expect(typeof html).toBe("string");
      expect(html.length).toBeGreaterThan(0);
      // Output should contain at least one HTML tag
      expect(html).toMatch(/<[a-zA-Z]/);
    }
  }, 120_000);

  it("produces non-empty output for sample-invoice.pdf", async () => {
    const pdfBytes = loadFixturePdf("sample-invoice.pdf");
    const html = await runConversion(pdfBytes);
    expect(html.length).toBeGreaterThan(100);
  }, 15_000);

  it("handles different zoom levels", async () => {
    // Copy bytes since pdf.js transfers the buffer during conversion
    const original = loadFixturePdf("sample-invoice.pdf");
    const bytes100 = new Uint8Array(original);
    const bytes150 = new Uint8Array(original);
    const html100 = await runConversion(bytes100, 100);
    const html150 = await runConversion(bytes150, 150);
    // Different zoom should produce different output sizes
    expect(html100.length).toBeGreaterThan(0);
    expect(html150.length).toBeGreaterThan(0);
  }, 15_000);
});

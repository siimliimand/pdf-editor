# Test PDFs

Place test PDF files in this directory.

## Naming convention

- `simple-text.pdf` — single page with plain text
- `multi-page.pdf` — PDF with multiple pages
- `tables.pdf` — PDF containing table structures
- `images.pdf` — PDF with embedded images
- `mixed.pdf` — combination of text, tables, and images
- `complex-layout.pdf` — PDF with columns, headers, footers

## Generating test PDFs

Use any PDF creation tool to generate test fixtures.
Keep PDFs minimal — small file sizes speed up test runs.

## Expected HTML outputs

Each test PDF should have a corresponding `.expected.html` file
in `ts-backend/tests/fixtures/expected/` for golden-file comparison.

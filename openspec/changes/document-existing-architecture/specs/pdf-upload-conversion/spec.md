---
version: 1.0.0
lastReviewed: 2026-07-18
status: validated
---

## ADDED Requirements

### Requirement: PDF file upload endpoint
The system SHALL provide a POST /upload endpoint that accepts PDF files and returns semantic HTML representation.

#### Scenario: Successful PDF upload
- **WHEN** client sends a multipart/form-data POST request to /upload with a valid PDF file and zoom parameter (as percentage, e.g. 100 = 100%)
- **THEN** system returns JSON response with html field containing semantic HTML representation of the PDF

#### Scenario: Invalid file type
- **WHEN** client sends a POST request to /upload with a non-PDF file
- **THEN** system returns HTTP 400 error with message indicating invalid file type

#### Scenario: Missing zoom parameter
- **WHEN** client sends a POST request to /upload without zoom parameter
- **THEN** system uses default zoom value of 100 (percentage)

#### Scenario: Invalid zoom value
- **WHEN** client sends a POST request to /upload with zoom value outside 50-500 range
- **THEN** system uses default zoom value of 100 (percentage)

### Requirement: PDF to HTML conversion pipeline
The system SHALL convert PDF files to semantic HTML through a multi-step pipeline.

#### Scenario: Complete conversion pipeline
- **WHEN** system receives a valid PDF file
- **THEN** system performs the following steps in order:
  1. Saves PDF to temporary directory
  2. Extracts and caches fonts
  3. Calculates zoom factors
  4. Runs pdftohtml to generate XML
  5. Extracts images
  6. Parses vector elements
  7. Detects table structures
  8. Converts XML to semantic HTML
  9. Injects font-face CSS
  10. Cleans up temporary files

#### Scenario: Zoom level handling
- **WHEN** system receives a zoom parameter (as percentage, e.g. 100 = 100%)
- **THEN** system calculates DPI scaling factor (percentage to 96px conversion) and caps at 3.0x maximum

#### Scenario: Table detection at non-standard zoom
- **WHEN** zoom level is not 1.0
- **THEN** system runs pdftohtml twice: once at requested zoom for rendering, once at 1.0x for table detection

### Requirement: Temporary file management
The system SHALL manage temporary files with UUID-based isolation.

#### Scenario: Temp directory creation
- **WHEN** system processes a PDF upload
- **THEN** system creates a unique temporary directory using UUID for the request

#### Scenario: Temp directory cleanup
- **WHEN** system completes PDF processing or encounters an error
- **THEN** system removes the temporary directory and all its contents
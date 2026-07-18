---
version: 1.0.0
lastReviewed: 2026-07-18
status: validated
---

## ADDED Requirements

### Requirement: Image extraction from PDF
The system SHALL extract images from PDF files using PyMuPDF's render-crop strategy.

#### Scenario: Image extraction
- **WHEN** system processes a PDF file
- **THEN** system extracts images by rendering page areas at native resolution and cropping to image boundaries

#### Scenario: Image format
- **WHEN** system extracts images from PDF
- **THEN** system saves images as PNG format with high quality

### Requirement: Image embedding in HTML
The system SHALL embed extracted images as base64 data URIs in the HTML output.

#### Scenario: Base64 encoding
- **WHEN** system includes images in HTML output
- **THEN** system base64-encodes image data and embeds as data URI in img src attribute

#### Scenario: Image positioning
- **WHEN** system renders images in HTML
- **THEN** system positions images according to their original coordinates in the PDF
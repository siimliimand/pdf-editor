## ADDED Requirements

### Requirement: Font extraction from PDF
The system SHALL extract font information from PDF files using PyMuPDF.

#### Scenario: Font extraction
- **WHEN** system processes a PDF file
- **THEN** system extracts font data including font name, weight, style, and character maps

#### Scenario: Font metadata extraction
- **WHEN** system extracts fonts from a PDF
- **THEN** system determines font weight (normal, bold) and style (normal, italic) from font metadata

### Requirement: Font caching
The system SHALL cache extracted fonts using SHA-256 hash-based verification.

#### Scenario: Cache hit
- **WHEN** system encounters a font with SHA-256 hash matching a cached font
- **THEN** system reuses the cached font CSS without re-extraction

#### Scenario: Cache miss
- **WHEN** system encounters a font with SHA-256 hash not in cache
- **THEN** system extracts font, generates CSS, and stores in cache with JSON metadata

#### Scenario: Cache storage
- **WHEN** system caches a font
- **THEN** system stores font CSS file and JSON metadata in fonts_cache directory

### Requirement: Font-face CSS generation
The system SHALL generate @font-face CSS rules for extracted fonts.

#### Scenario: Base64 encoding
- **WHEN** system generates font-face CSS
- **THEN** system base64-encodes font data and embeds as data URI in CSS

#### Scenario: CSS injection
- **WHEN** system completes HTML conversion
- **THEN** system injects generated font-face CSS into the HTML output
## Context

The PDF Editor is a working Chrome extension + FastAPI backend system for viewing and editing PDFs in the browser. The system converts PDFs to semantic HTML using Poppler's pdftohtml, extracts fonts/images/vectors using PyMuPDF and pdfminer, and renders the result in a Tiptap-based rich text editor.

**Current state:**
- Fully functional PDF upload and conversion pipeline
- Chrome extension with upload UI and editor interface
- Font embedding via base64 data URIs
- Table detection and grid-based rendering
- Vector graphics parsing and rendering
- No formal documentation or specifications

**Constraints:**
- Backend runs on localhost:8085 (hardcoded)
- Requires Poppler utilities installed on system
- Chrome extension only (not web app)
- No authentication or rate limiting

## Goals / Non-Goals

**Goals:**
- Create comprehensive OpenSpec specifications for all existing capabilities
- Document API contracts, data flows, and component interfaces
- Establish baseline for future development and testing
- Enable team onboarding and knowledge transfer

**Non-Goals:**
- Refactor or modify existing implementation
- Add new features or capabilities
- Change architecture or technology stack
- Implement testing or CI/CD (separate proposal)

## Decisions

### 1. Specification Granularity
**Decision:** Create separate specs for each major capability (upload, fonts, images, vectors, tables, editor, extension)

**Rationale:** Each capability has distinct API contracts, data flows, and requirements. Separate specs enable targeted testing and future modification without affecting other components.

**Alternatives considered:**
- Single monolithic spec: Rejected - too coarse for testing and maintenance
- Per-file specs: Rejected - too granular, many internal files don't need public specs

### 2. API-First Documentation
**Decision:** Document API contracts before implementation details

**Rationale:** The POST /upload endpoint is the primary interface between frontend and backend. Documenting this first establishes the contract and enables parallel development/testing.

**Alternatives considered:**
- Implementation-first: Rejected - leads to documentation that doesn't match actual behavior
- Simultaneous: Rejected - too complex for initial documentation effort

### 3. Data Flow Focus
**Decision:** Emphasize data transformations (PDF → XML → HTML) over component internals

**Rationale:** The conversion pipeline is the core value proposition. Documenting transformations enables understanding of edge cases, performance characteristics, and testing strategies.

**Alternatives considered:**
- Component-focused: Rejected - doesn't capture the end-to-end flow
- File-focused: Rejected - too low-level for system understanding

## Risks / Trade-offs

### Risk: Documentation Drift
**Impact:** Specifications may not match implementation as code evolves
**Mitigation:** 
- Create specs from working code (not aspirational design)
- Include version references and last-tested dates
- Establish review process for code changes

### Risk: Over-Specification
**Impact:** Too much detail makes specs brittle and hard to maintain
**Mitigation:**
- Focus on public interfaces and contracts
- Avoid internal implementation details
- Use "should" not "must" for non-critical behaviors

### Risk: Incomplete Coverage
**Impact:** Missing specs for edge cases or error handling
**Mitigation:**
- Start with happy-path scenarios
- Add edge cases incrementally
- Include error handling in each capability spec

### Trade-off: Completeness vs. Maintenance
**Decision:** Prioritize completeness over perfect maintainability
**Rationale:** Initial documentation effort is high but provides immediate value. Can be refined later based on usage patterns.

## Migration Plan

1. **Phase 1: Core API Spec** - Document POST /upload endpoint contract
2. **Phase 2: Conversion Pipeline** - Document PDF → HTML transformation steps
3. **Phase 3: Frontend Components** - Document React/Tiptap integration
4. **Phase 4: Chrome Integration** - Document extension-specific behaviors
5. **Phase 5: Cross-cutting Concerns** - Document caching, error handling, security

**Rollback:** Specs are documentation-only, no code changes to rollback.

## Open Questions

1. **Testing Strategy:** Should specs include test cases or remain descriptive?
2. **Versioning:** How to handle spec versions as implementation evolves?
3. **Tooling:** Which spec format (OpenAPI, Gherkin, custom) best fits this project?
4. **Review Process:** Who reviews and approves spec changes?
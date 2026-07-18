---
design_tokens:
  colors:
    palette:
      primary:
        blue-50: "#eff6ff"
        blue-100: "#dbeafe"
        blue-500: "#3b82f6"
        blue-600: "#2563eb"
      neutral:
        gray-50: "#f9fafb"
        gray-100: "#f3f4f6"
        gray-200: "#e5e7eb"
        gray-300: "#d1d5db"
        gray-400: "#9ca3af"
        gray-500: "#6b7280"
        gray-600: "#4b5563"
        gray-700: "#374151"
        gray-800: "#1f2937"
      semantic:
        error:
          light: "#fee2e2"
          base: "#ef4444"
          dark: "#dc2626"
          text: "#991b1b"
        success:
          base: "#22c55e"
        white: "#ffffff"
        black: "#000000"
    semantic_mapping:
      background: gray-100
      surface: white
      text-primary: gray-800
      text-secondary: gray-500
      text-muted: gray-400
      border: gray-200
      border-strong: gray-300
      accent: blue-500
      accent-hover: blue-600
      error-bg: red-50
      error-text: red-600
      error-border: red-100

  typography:
    families:
      sans: system UI, -apple-system, sans-serif
    scales:
      heading-lg: { size: 1.875rem, weight: 700, line_height: 2.25rem }
      heading-md: { size: 1.25rem, weight: 600, line_height: 1.75rem }
      body: { size: 0.875rem, weight: 400, line_height: 1.25rem }
      body-sm: { size: 0.75rem, weight: 400, line_height: 1rem }
      label: { size: 0.875rem, weight: 500, line_height: 1.25rem }

  spacing:
    scale:
      xs: 0.25rem
      sm: 0.5rem
      md: 1rem
      lg: 1.5rem
      xl: 2rem
      "2xl": 3rem

  radii:
    sm: 0.25rem
    md: 0.375rem
    lg: 0.5rem
    xl: 0.75rem

  shadows:
    sm: "0 1px 2px 0 rgb(0 0 0 / 0.05)"
    md: "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)"

  motion:
    durations:
      fast: 150ms
      normal: 200ms
    easings:
      default: ease-in-out

  layout:
    container:
      max_width: 42rem
    toolbar:
      height: auto
      sticky: top-0
    editor:
      min_height: 500px
    upload_zone:
      height: 16rem

  borders:
    dashed:
      style: dashed
      width: 2px
    solid:
      style: solid
      width: 1px
---

# Design System

## Visual Identity

PDF Editor follows a clean, minimal design language typical of productivity tools. The interface is built entirely with Tailwind CSS utility classes — no custom CSS variables, design tokens files, or component library. The visual system is implicit in the utility class usage across components.

**Overall feel:** Functional and unobtrusive. The UI stays out of the way of the PDF content, using neutral grays for chrome and blue for interactive accents.

## Color System

The palette is Tailwind's default with no customization:

- **Backgrounds:** `bg-gray-100` for page, `bg-white` for surfaces and cards
- **Text:** `text-gray-800` primary, `text-gray-500` secondary, `text-gray-400` muted/placeholder
- **Borders:** `border-gray-200` default, `border-gray-300` stronger, `border-dashed` for upload zones
- **Interactive accent:** `blue-500`/`blue-600` for active states, hover states, focus rings
- **Error state:** `red-50` background, `red-600` text/buttons, `red-700` dark text
- **Active toolbar button:** `bg-blue-100 text-blue-600` (bold, italic, underline, link)

No dark mode. No theme switching. All colors are Tailwind defaults with no overrides.

## Typography

No custom fonts. Uses the system font stack via Tailwind defaults:
- Headings: `text-3xl font-bold` (upload title), `text-xl font-semibold` (editor header)
- Body: `text-sm` (most content), `text-xs` (meta/hint text)
- Labels: `text-sm font-medium` (buttons, toolbar)
- Editor content: ProseMirror/Tiptap renders with inline styles from the PDF conversion

## Component Patterns

### Upload View
- Centered card (`max-w-2xl mx-auto`) with white background and `rounded-xl shadow-md`
- Drag-and-drop zone: `h-64`, dashed border, color transitions on drag state
- Error feedback: inline red alert box below the upload zone

### Editor View
- Full-height layout (`h-[calc(100vh-4rem)]`) with flex column
- Top toolbar: file name + zoom controls + close button, `flex justify-between`
- Content area: `border-2 border-dashed border-gray-300 rounded-lg bg-white`
- Zoom controls: pill-shaped container with minus/plus buttons and dropdown select
- Close button: `text-red-600 bg-red-50 hover:bg-red-100`

### Rich Text Editor
- Sticky toolbar at top (`sticky top-0 z-50 shadow-sm`)
- Toolbar groups separated by `border-r border-gray-200`
- Icon buttons: `p-1.5 rounded hover:bg-gray-100` with `text-gray-600` default, `text-blue-600` when active
- Editor content area: `bg-gray-100` with `p-4` padding
- ProseMirror: transparent background, `bg-white` applied via CSS to page divs

### Loading State
- Full-overlay with white background and centered spinner (`animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600`)

### Error State
- Centered card with `bg-red-50 p-6 rounded-lg max-w-md`
- Retry button: `bg-red-600 text-white rounded hover:bg-red-700`

## Interaction Patterns

- **Drag and drop:** Visual feedback via border color (`blue-500`) and background (`blue-50`) change on hover
- **Zoom:** Discrete steps [50, 75, 100, 125, 150, 175, 200, 250, 300, 400, 500] via dropdown or +/- buttons
- **Toolbar activation:** Active formatting states shown with `bg-blue-100 text-blue-600` highlight
- **Transitions:** `transition-colors duration-200 ease-in-out` on interactive elements

## Layout Philosophy

- **Fixed toolbar, scrollable content** — toolbar stays visible while PDF pages scroll
- **Content-first** — the PDF rendering area takes all available vertical space
- **No sidebar** — single-panel layout, all controls in the top toolbar
- **Responsive basics** — `container mx-auto` for centering, but no mobile breakpoints defined

## Design Constraints

- **No custom CSS variables or tokens** — everything is Tailwind utility classes
- **No component library** (no shadcn, MUI, etc.) — all components are hand-built
- **No animation library** — only Tailwind's built-in `animate-spin`
- **Inline styles from PDF** — the editor must preserve inline styles from the backend HTML, which can override Tailwind classes
- **ProseMirror content** — editor styling is constrained by ProseMirror's DOM model

<!-- Last updated: 2026-07-18T00:00:00Z -->

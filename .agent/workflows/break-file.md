---
description: Decomposes a monolithic file into a modular, hierarchical directory structure following the Single Responsibility Principle.
---

# Workflow: Break Monolithic File

**ID:** `refactor_break_file`

## 1. Analysis Phase
- **Action:** Read and analyze the content of `{{input_file}}`.
- **Goal:** Understand the responsibilities and dependencies within the file.
- **Checklist:**
    - Identify distinct classes, interfaces, types, and functions.
    - Group items by domain logic (e.g., data fetching, UI rendering, math utilities, API schemas).
    - Map internal dependencies (what calls what) and shared state.
    - **Context Check:** Determine if the file belongs to the **Backend** (Python/FastAPI) or **Extension** (TypeScript/React).

## 2. Architecture Design
- **Action:** Propose a directory structure *before* writing any code.
- **Guidelines:**
    - **Backend (Python):**
        - `routers/`: API route definitions.
        - `services/`: Business logic.
        - `models/`: Database models.
        - `schemas/`: Pydantic models/Data structures.
        - `utils/`: Helper functions.
    - **Extension (TypeScript/React):**
        - `components/`: UI components (PascalCase).
        - `hooks/`: Custom React hooks (camelCase, start with `use`).
        - `services/`: API calls, background scripts.
        - `utils/`: Helper functions.
        - `types/`: Type definitions and interfaces.
- **Output:** Create a comprehensive plan listing the new files to be created and which existing code goes into them.

## 3. Extraction & Modularization
- **Action:** Create the folder structure and write the new files.
- **Rules:**
    - **Size Limit:** Ensure every generated file is **under 300 lines** of code. If a module is larger, break it down further.
    - **Naming:**
        - Python: `snake_case` for modules/files and functions, `PascalCase` for classes.
        - TypeScript: `PascalCase` for components, `camelCase` for functions/hooks/instances.
    - **Imports:**
        - Ensure all necessary imports are present in the new files.
        - Use relative imports where appropriate for internal module references, but prefer absolute imports for clarity if moving significantly.
    - **Init Files:** For Python, create `__init__.py` files if creating new directories to make them packages.

## 4. Refactoring Original Entry Point
- **Action:** Replace the content of `{{input_file}}` (or the file that replaces it) with imports/exports to expose the new functionality, or update references in the codebase to point to the new locations.
- **Goal:** Maintain backward compatibility if `{{input_file}}` was a main entry point, OR fully deprecate it by updating all callers.

## 5. Dependency Resolution & Verification
- **Action:** Update all imports in the project that referenced `{{input_file}}`.
- **Verification:**
    - Run `grep_search` to find any remaining references to the old file path/content.
    - Perform a syntax check (e.g., attempt to run the server or build the extension if feasible, or just review the logic).
    - Ensure no circular dependencies were introduced.

## 6. Cleanup
- **Action:** Delete the original `{{input_file}}` if it's no longer needed and all logic has been moved.

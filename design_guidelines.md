# design_guidelines.md

## 1. CustomTkinter Design Tokens
Since this is a desktop app using `CustomTkinter`, CSS is not applicable. Design tokens are mapped to Python kwargs.
*   **Theme Mode:** `Dark` (Forced to prevent OS-level light/dark inconsistencies).
*   **Color Palette:**
    *   Background (App): `#242424`
    *   Background (Cards/Frames): `#2B2B2B`
    *   Primary Accent (Buttons/Progress): `#1F6AA5` (Standard CTk Blue)
    *   Hover Accent: `#144870`
    *   Error/Alert Text: `#CF6679`
    *   Success Text: `#4CAF50`
    *   Main Text: `#DCE4EE`
*   **Typography:**
    *   Font Family: System default sans-serif (`Roboto`, `Segoe UI`, or `San Francisco`).
    *   Header: `("Segoe UI", 18, "bold")`
    *   Body: `("Segoe UI", 13, "normal")`
    *   Code/Log: `("Consolas", 12, "normal")` (Monospace for status log).
*   **Border Radius:** 
    *   Buttons & Entries: `6px`
    *   Frames: `10px`

## 2. Layout Architecture
*   **Root Window:** Fixed size or non-resizable (e.g., `800x600`) to prevent layout breaking.
*   **Grid System:** Utilizing Tkinter's `.grid()` geometry manager.
    *   Padding (`padx`, `pady`): Universal `10px` between elements, `20px` from window edges.
*   **Sections:** Divided using `CTkFrame` widgets to group logical clusters (Auth Frame, Date Frame, File Frame).

## 3. Reusable Component Guidelines
*   **Primary Action Buttons (Execute):** Must use the Primary Accent color. Must transition to a "Disabled" state (greyed out) during async execution.
*   **Secondary Action Buttons (File Pickers):** Outline style or lighter background to separate visual hierarchy from the main Execute button.
*   **Data Inputs (Dates/Tokens):** Must include clear placeholder text (e.g., `placeholder_text="YYYY-MM-DD"`). Passwords must use `show="*"` parameter.
*   **Status Badges/Logs:** The log text box must auto-scroll to the bottom upon new insertions (`textbox.see("end")`).

## 4. Accessibility & Interaction Checklists
*   [ ] **Keyboard Navigation:** Tab-order must logically flow from Top (Token) -> Middle (Dates/Files) -> Bottom (Execute).
*   [ ] **Feedback:** Buttons must visually depress or change hover state when clicked.
*   [ ] **Thread Blocking:** The main UI thread MUST NOT freeze. All API calls must utilize `.after()` loops or `asyncio` event loops mapped to Tkinter.


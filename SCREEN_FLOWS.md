# SCREEN_FLOWS.md

## 1. Route Map and Screen Hierarchy
Because this is a local desktop utility, it utilizes a Single-Window Architecture rather than traditional web routing.
*   **Main Window (Root)**
    *   Auth Section (Top)
    *   Configuration Section (Middle)
    *   Execution & Status Section (Bottom)

## 2. Detailed Breakdown per Screen
**Screen: Main Application Window**
*   **Purpose:** The sole interface for configuring and executing the batch job.
*   **Key Components:**
    *   `TokenEntry (CTkEntry, password masked)`: Input for GitHub PAT.
    *   `SaveTokenCheckbox (CTkCheckBox)`: Toggles saving to Windows Credential Manager.
    *   `DatePickerStart (CTkEntry/Combobox)`: ISO date input (YYYY-MM-DD).
    *   `DatePickerEnd (CTkEntry/Combobox)`: ISO date input (YYYY-MM-DD).
    *   `FileSelectorBtn (CTkButton)`: Opens native OS file dialog for `.md` input.
    *   `OutputSelectorBtn (CTkButton)`: Opens native OS folder dialog for output destination.
    *   `ExecuteBtn (CTkButton)`: Triggers the async ingestion and API queue.
    *   `ProgressBar (CTkProgressBar)`: Real-time visual indicator of batch completion.
    *   `StatusLog (CTkTextbox)`: Read-only scrollable text area for real-time console feedback.

## 3. Multi-Step User Flows
**Flow A: Initial Onboarding & Authentication**
1. User launches the executable.
2. System queries OS `keyring`. If empty, the Token field remains blank.
3. User pastes their GitHub PAT and checks "Save Token".
4. System validates the token length/format, saves it to `keyring`, and updates UI state.

**Flow B: Batch Execution**
1. User inputs Start Date and End Date.
2. User clicks "Select Input File" -> Selects `BSIT-3C.md`.
3. User clicks "Select Output Folder" -> Selects Desktop.
4. User clicks "Process".
5. UI disables all inputs to prevent state mutation during execution.
6. `ProgressBar` initializes based on the length of the deduplicated user list.
7. `StatusLog` appends real-time events (e.g., "Fetching user1...", "Cached user2...", "Rate limit pausing...").
8. Upon completion, UI re-enables, and a native OS popup confirms "File saved to Desktop."


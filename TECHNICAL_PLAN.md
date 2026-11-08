# TECHNICAL_PLAN.md

## 1. Technical Architecture & Directory Structure
The application follows a modular Model-View-Controller (MVC) architecture, separating the UI, core API logic, data parsing, and secure local storage.

github_commit_tracker/
├── main.py                 # Application entry point
├── gui/
│   ├── __init__.py
│   ├── app.py              # Main CustomTkinter window/layout
│   └── components.py       # Reusable UI widgets
├── core/
│   ├── __init__.py
│   ├── parser.py           # Regex text extraction & deduplication logic
│   ├── github_api.py       # Async HTTP client with concurrency limiter
│   └── output_writer.py    # Text file generation & error logging
├── db/
│   ├── __init__.py
│   └── cache.py            # SQLite wrapper for API response caching
├── security/
│   ├── __init__.py
│   └── auth_manager.py     # OS Credential Manager integration (keyring)
├── models/
│   ├── __init__.py
│   └── schemas.py          # Dataclasses for Student and Result objects
├── requirements.txt
└── README.md

## 2. Module Scaffolding Breakdown
*   **`gui.app`:** Manages the main event loop. Contains simple YYYY-MM-DD Start/End date pickers, a PAT input (with a "Save to OS" toggle), file/folder selectors, and a real-time progress indicator.
*   **`security.auth_manager`:** Utilizes the Python `keyring` library to securely store and retrieve the GitHub PAT using the native Windows Credential Locker.
*   **`core.parser`:** Reads `.md` files, uses Regex to extract GitHub URLs/usernames, strips query parameters/paths, and strictly drops duplicate usernames into a `set` to ensure data cleanliness.
*   **`core.github_api`:** Utilizes `asyncio` and `aiohttp`. Extracts only the `total_count` field from the GitHub Search API payload (no pagination needed). Implements a semaphore to limit outbound requests to 5 at a time.
*   **`db.cache`:** Local SQLite database. Intercepts network calls to check if the exact user and YYYY-MM-DD range was queried recently to save rate limits.
*   **`core.output_writer`:** 
    *   Writes successful results (including 0 commits) formatted strictly as `[name]-=-[commits]-=-[link]`.
    *   Writes accounts with issues formatted as `[name]-=-PROBLEM WITH ACCOUNT-=-[link]`.
    *   Appends detailed error traces (e.g., 404 Not Found, 403 Rate Limit) to a separate `errors.log` file.

## 3. Database Entities & Data Structures
**Entity: StudentRecord** (In-Memory)
*   `username`: string (Sanitized and deduplicated username)
*   `profile_url`: string (Reconstructed URL: https://github.com/{username})

**Entity: ApiCache** (SQLite Table)
*   `id`: Primary Key
*   `username`: Varchar (Indexed)
*   `start_date`: Date (YYYY-MM-DD)
*   `end_date`: Date (YYYY-MM-DD)
*   `commit_count`: Integer
*   `fetched_at`: DateTime

**Entity: ProcessingResult** (In-Memory)
*   `username`: string
*   `commit_count`: integer (Can be 0)
*   `profile_url`: string
*   `status`: enum (SUCCESS, NOT_FOUND, RATE_LIMITED, FORMAT_ERROR)
*   `error_detail`: string (Null if successful)

## 4. Data Flow Strategy
1.  **State & Auth:** GUI loads. `auth_manager` attempts to retrieve the saved PAT from the OS Credential Manager. User selects dates (YYYY-MM-DD) and `.md` file.
2.  **Ingestion & Deduplication:** Background thread passes the `.md` file to `core.parser`. Regex identifies users, normalizes them to lowercase, and adds them to a Python `set` to instantly destroy duplicates.
3.  **API Querying (Async Semaphore):**
    *   Iterates through deduplicated records.
    *   Queries `db.cache`. On miss, queues an async GitHub API request.
    *   Concurrency limiter restricts active outbound requests to 5 at a time.
4.  **Output Generation:** 
    *   Valid results (including 0 commits) are mapped to the primary `.txt` file.
    *   Failed results trigger the "PROBLEM WITH ACCOUNT" string in the `.txt` and push the explicit `error_detail` to `errors.log`.

## 5. Assumptions & Out of Scope
*   **File Formats:** Direct parsing of `.xlsx` and `.docx` is out of scope. Input relies entirely on manually converted `.md` text files.
*   **Commit Visibility:** The application will strictly count public repository commits. Private commits are out of scope.
*   **Data Depth:** The application will only fetch the numerical `total_count` of commits. Extracting commit messages, repository names, or code diffs is out of scope.

## 6. Testing Strategy
*   **Unit Testing (`core.parser`):** Create a test suite passing in mock strings featuring the known anomalies (e.g., `user?tab=overview`, `user/repo`, email addresses) to ensure the Regex correctly isolates the raw username.
*   **Mock Integration Testing (`core.github_api`):** Use `aioresponses` to mock the GitHub API payloads to ensure the script properly handles 200 (Success), 403 (Rate Limit), and 404 (Not Found) status codes without actually hitting the live GitHub servers.

## 7. Deployment & Packaging
*   Code will be developed in a strict Python `venv`.
*   Upon completion, `PyInstaller` will be used to compile the application into a single `.exe` executable for Windows. This allows the tool to run natively without requiring VSCode or Python to be installed on the host machine.

## 8. Sequenced Implementation Backlog
*   **Phase 0:** Environment Setup, venv, and package installation (`customtkinter`, `aiohttp`, `keyring`).
*   **Phase 1:** Implement `security.auth_manager` and `core.parser` (including deduplication logic).
*   **Phase 2:** Build async HTTP client (`core.github_api`) with the 5-request semaphore and strict `total_count` extraction.
*   **Phase 3:** Set up SQLite database (`db.cache`) to intercept redundant network calls.
*   **Phase 4:** Implement `core.output_writer` to route successes to `.txt` and failures to `.txt` + `errors.log`.
*   **Phase 5:** Build `CustomTkinter` UI, bind to core logic, and manage thread handoffs.
*   **Phase 6:** Run test suite and package with `PyInstaller`.

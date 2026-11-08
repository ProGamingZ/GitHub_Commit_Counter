# SYSTEM_DESIGN.md

## 1. Real-World Business Workflow vs. Target Digitized Flow
**Real-World Workflow:** An instructor manually collects GitHub usernames from student submissions, opens a web browser, navigates to each profile, filters the contribution graph by specific assignment dates, manually counts the commits, and records the score in a spreadsheet. This is highly prone to human error, visually fatiguing, and scales poorly for classes of 40+ students.
**Target Digitized Flow:** The instructor provides a raw text/markdown file of student submissions, selects a Start and End date, and clicks "Process." The application automatically parses the document, sanitizes the links, deduplicates users, batches asynchronous requests to the GitHub API, and outputs a formatted, machine-readable `.txt` file ready for final grading, along with an error log for invalid accounts.

## 2. Core Tech Stack Overview
*   **Language:** Python 3.11+ (Strictly typed via `typing` module)
*   **GUI Framework:** `CustomTkinter` (Modern, dark-mode native desktop UI)
*   **Concurrency & Network:** `asyncio` and `aiohttp` (Asynchronous I/O for concurrent API requests)
*   **Local Storage:** `sqlite3` (Built-in SQLite for caching API responses)
*   **Security:** `keyring` (OS-level Credential Manager integration for token storage)
*   **Data Parsing:** `re` (Regular expressions for text extraction)

## 3. Database Schema
**Database:** SQLite (`cache.db`)
**Table:** `ApiCache`

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique row identifier. |
| `username` | VARCHAR | NOT NULL | Sanitized GitHub username. |
| `start_date` | DATE | NOT NULL | YYYY-MM-DD format. |
| `end_date` | DATE | NOT NULL | YYYY-MM-DD format. |
| `commit_count` | INTEGER | NOT NULL | Extracted `total_count` from API. |
| `fetched_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Timestamp for cache invalidation. |

**Indexes:**
*   `idx_user_dates`: Composite index on `(username, start_date, end_date)` for O(1) cache lookups.

## 4. Business Rules, Invariants, and Edge-Case Handling
*   **Rule 1 (Deduplication):** A single input file may contain the same user multiple times. The system MUST deduplicate the parsing queue using a mathematical `set` to prevent duplicate network calls and duplicate lines in the final output.
*   **Rule 2 (Private Commits):** The system strictly counts public commits. Private repository commits are ignored to maintain a standardized grading baseline.
*   **Rule 3 (Rate Limiting):** Outbound requests must be throttled via an asyncio.Semaphore(5) combined with a 1-second micro-delay between live network calls. If GitHub's secondary abuse limit is triggered, the system initiates a maximum 3-attempt exponential backoff based on the Retry-After header.
*   **Rule 4 (Zero-Commit Accounts):** Accounts returning a `total_count` of 0 are valid academic submissions and MUST be logged in the success file as `[name]-=-0-=-[link]`.
*   **Edge Case (Invalid Identifiers):** Emails, real names, or malformed URLs will bypass API querying entirely, fail fast, and route directly to `errors.log`.
*   **Edge Case (404 Not Found):** If a user deleted their account or changed their username, the API returns 404. This is logged in `errors.log` and outputs as `PROBLEM WITH ACCOUNT` in the main `.txt`.

## 5. Unresolved Business/Domain Questions
| Question | Impact | Current Assumption / Status |
| :--- | :--- | :--- |
| Cache Expiration Policy | How long should a cached API response live before forcing a fresh network call? | Currently assuming infinite cache for a given date range since past commits rarely change retrospectively. |
| Cross-Platform Distribution | MacOS vs. Windows execution. | Assuming primary target is Windows `.exe` via PyInstaller. |


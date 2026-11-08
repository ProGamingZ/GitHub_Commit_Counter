# API.md

## 1. Environment Variable References
No `.env` file is used for security and portability reasons.
*   **Authentication:** The GitHub Personal Access Token (PAT) is stored in the native OS Credential Manager under the service name `GitHubCommitTracker_App`.
*   **Retrieval:** `keyring.get_password("GitHubCommitTracker_App", "user_pat")`

## 2. Endpoints (External Integrations)
This application acts as an API *Client*, not a Server.

### Method: GET
**Path:** `https://api.github.com/search/commits`
**Description:** Fetches the total commit count for a specific author within a date range across all public repositories.
**Source File Mapping:** `core/github_api.py`

**Query Parameters:**
*   `q`: `author:{username}+committer-date:{start_date}..{end_date}`
*   `per_page`: `1` (We only need the header/metadata, not the payload body, optimizing bandwidth).

**Required Headers:**
*   `Accept`: `application/vnd.github.v3+json`
*   `Authorization`: `Bearer {PAT}`
*   `X-GitHub-Api-Version`: `2022-11-28`

## 3. Mutating Side Effects Checklist
Since this is a client app, mutations refer to local disk operations resulting from API queries.
*   **Local Caching (SQL INSERT):** Upon a `200 OK` response from GitHub, the `username`, `dates`, and `total_count` are INSERTED into `db/cache.db`.
*   **File System (WRITE):** Upon batch completion, two files are created/overwritten in the target directory:
    *   `{timestamp}_results.txt`
    *   `{timestamp}_errors.log`

## 4. Known Issues and Maintenance Rules
*   **GitHub Rate Limits (403):** Even with a PAT (5,000 req/hr), the Search API is subject to secondary abuse limits if concurrent requests are made too rapidly.
    *   *Maintenance Rule:* The application must respect the Retry-After header if a 403 is received. The API client enforces a max-3 retry loop that executes await asyncio.sleep() for the required duration (or a 60-second default fallback) before re-queueing the user.
*   **Pagination Limitations:** The Search API `total_count` is accurate up to 1,000 results. If a student somehow surpasses 1,000 commits in a single assignment period, the API may cap the reported number. This is a known GitHub limitation but functionally irrelevant for standard academic grading scales.


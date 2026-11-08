# GitHub Commit Tracker
A local desktop utility for instructors to batch-check student GitHub commit counts.

## Features
* Secure native OS token storage via `keyring`.
* Async HTTP requests with concurrency limits.
* Built-in SQLite caching to prevent GitHub API rate limits.

## How to Run
1. Clone the repository and activate your virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python main.py`
4. Paste your GitHub PAT into the UI and configure your batch job.
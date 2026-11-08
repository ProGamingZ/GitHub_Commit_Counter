import re
from typing import List, Set
from models.schemas import StudentRecord

def parse_markdown_file(file_path: str) -> List[StudentRecord]:
    """
    Reads a markdown file, extracts GitHub usernames, strips query parameters,
    and returns a deduplicated list of StudentRecord objects.
    """
    # Regex to extract username from URLs like https://github.com/username
    # Automatically ignores subpaths (/repo) or queries (?tab=overview)
    github_regex = re.compile(r'(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9-]+)(?:[/?\s]|$)')
    
    unique_usernames: Set[str] = set()
    records: List[StudentRecord] = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        # In a later phase, this will be routed to the UI or errors.log
        print(f"Error reading file: {e}")
        return []

    # Find all regex matches in the document
    matches = github_regex.findall(content)

    for username in matches:
        # Normalize to lowercase to ensure strict deduplication
        normalized_user = username.strip().lower()
        
        # Rule 1: Deduplication using a mathematical set
        if normalized_user not in unique_usernames:
            unique_usernames.add(normalized_user)
            
            # Reconstruct clean URL
            profile_url = f"https://github.com/{normalized_user}"
            records.append(StudentRecord(username=normalized_user, profile_url=profile_url))
            
    return records
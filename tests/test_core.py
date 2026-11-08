import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import aiohttp
import re
from unittest.mock import patch, mock_open, AsyncMock

from core.parser import parse_markdown_file
from core.github_api import fetch_commit_count
from models.schemas import Status

# --- Unit Testing (core.parser) ---
def test_parser_regex_and_deduplication():
    """Tests the regex extraction, deduplication, and anomaly bypassing."""
    mock_md_content = """
    Valid user: https://github.com/student1
    Duplicate user: https://github.com/student1
    Query param anomaly: https://github.com/student2?tab=overview
    Subpath anomaly: https://github.com/student3/assignment-repo
    Invalid identifier (email): test@github.com
    """
    
    with patch("builtins.open", mock_open(read_data=mock_md_content)):
        records = parse_markdown_file("dummy.md")
        
        assert len(records) == 3
        usernames = [r.username for r in records]
        
        assert "student1" in usernames
        assert "student2" in usernames
        assert "student3" in usernames
        assert "test" not in usernames 

# --- Mock Integration Testing (core.github_api) ---
@pytest.mark.asyncio
@patch('aiohttp.ClientSession.get')
async def test_github_api_responses(mock_get):
    """Uses unittest.mock to test API payloads and status handling without live network calls."""
    async with aiohttp.ClientSession() as session:
        
        # 1. Test 200 (Success)
        mock_response_200 = AsyncMock()
        mock_response_200.status = 200
        mock_response_200.json.return_value = {"total_count": 15}
        mock_get.return_value.__aenter__.return_value = mock_response_200
        
        res_success = await fetch_commit_count(session, "user1", "2023-01-01", "2023-01-31", "token")
        assert res_success.status == Status.SUCCESS
        assert res_success.commit_count == 15
        
        # 2. Test 403 (Rate Limit)
        mock_response_403 = AsyncMock()
        mock_response_403.status = 403
        mock_response_403.headers = {"Retry-After": "60"}
        mock_get.return_value.__aenter__.return_value = mock_response_403
        
        res_rate_limit = await fetch_commit_count(session, "user2", "2023-01-01", "2023-01-31", "token")
        assert res_rate_limit.status == Status.RATE_LIMITED
        assert res_rate_limit.error_detail is not None  # Fixes the Linter Type Error
        assert "60s" in res_rate_limit.error_detail
        
        # 3. Test 404 (Not Found)
        mock_response_404 = AsyncMock()
        mock_response_404.status = 404
        mock_get.return_value.__aenter__.return_value = mock_response_404
        
        res_not_found = await fetch_commit_count(session, "user3", "2023-01-01", "2023-01-31", "token")
        assert res_not_found.status == Status.NOT_FOUND
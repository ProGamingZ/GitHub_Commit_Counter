import asyncio
import aiohttp
from models.schemas import ProcessingResult, Status

# Rule 3: Throttle outbound requests to prevent triggering GitHub's secondary abuse limits
SEMAPHORE = asyncio.Semaphore(5)

async def fetch_commit_count(
    session: aiohttp.ClientSession, 
    username: str, 
    start_date: str, 
    end_date: str, 
    token: str,
    max_retries: int = 3
) -> ProcessingResult:
    """
    Fetches the total commit count, with an automatic retry-backoff for 403 Rate Limits.
    """
    url = "https://api.github.com/search/commits"
    profile_url = f"https://github.com/{username}"
    
    params = {
        "q": f"author:{username} committer-date:{start_date}..{end_date}",
        "per_page": "1"
    }
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    async with SEMAPHORE:
        for attempt in range(max_retries):
            try:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return ProcessingResult(
                            username=username,
                            commit_count=data.get("total_count", 0),
                            profile_url=profile_url,
                            status=Status.SUCCESS
                        )
                    elif response.status == 403:
                        # Suggestion 1: Retry-Backoff Mechanism
                        retry_after = response.headers.get("Retry-After")
                        delay = int(retry_after) if retry_after and retry_after.isdigit() else 60
                        
                        if attempt < max_retries - 1:
                            await asyncio.sleep(delay)
                            continue  # Loop back and try again
                        else:
                            return ProcessingResult(
                                username=username,
                                commit_count=0,
                                profile_url=profile_url,
                                status=Status.RATE_LIMITED,
                                error_detail=f"403 Rate Limited. Exhausted {max_retries} retries."
                            )
                    elif response.status == 404 or response.status == 422:
                        return ProcessingResult(
                            username=username,
                            commit_count=0,
                            profile_url=profile_url,
                            status=Status.NOT_FOUND,
                            error_detail=f"HTTP {response.status}: Account not found or invalid"
                        )
                    else:
                        return ProcessingResult(
                            username=username,
                            commit_count=0,
                            profile_url=profile_url,
                            status=Status.FORMAT_ERROR,
                            error_detail=f"HTTP {response.status}: Unexpected API error"
                        )
            except Exception as e:
                return ProcessingResult(
                    username=username,
                    commit_count=0,
                    profile_url=profile_url,
                    status=Status.FORMAT_ERROR,
                    error_detail=f"Network Exception: {str(e)}"
                )
        # Add this fallback return to satisfy the linter
        return ProcessingResult(
            username=username,
            commit_count=0,
            profile_url=profile_url,
            status=Status.FORMAT_ERROR,
            error_detail="Failed to fetch data: Max retries exhausted or invalid loop execution."
        )
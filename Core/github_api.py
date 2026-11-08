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
    token: str
) -> ProcessingResult:
    """
    Fetches the total commit count for a specific author within a date range across all public repositories.
    """
    url = "https://api.github.com/search/commits"
    profile_url = f"https://github.com/{username}"
    
    # Format strictly according to API documentation
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
        try:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    # Extract only the total_count field
                    total_count = data.get("total_count", 0)
                    return ProcessingResult(
                        username=username,
                        commit_count=total_count,
                        profile_url=profile_url,
                        status=Status.SUCCESS
                    )
                elif response.status == 403:
                    # Maintenance Rule: Respect the Retry-After header if a 403 is received
                    retry_after = response.headers.get("Retry-After", "Unknown")
                    return ProcessingResult(
                        username=username,
                        commit_count=0,
                        profile_url=profile_url,
                        status=Status.RATE_LIMITED,
                        error_detail=f"403 Rate Limited. Retry-After: {retry_after}s"
                    )
                elif response.status == 404 or response.status == 422:
                    # 404 Not Found or 422 Unprocessable Entity due to invalid username formatting
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
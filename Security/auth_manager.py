import keyring
from keyring.errors import PasswordDeleteError

# Hardcoded service credentials per the API guidelines
SERVICE_NAME = "GitHubCommitTracker_App"
ACCOUNT_NAME = "user_pat"

def save_token(token: str) -> None:
    """Saves the GitHub PAT to the native OS Credential Locker."""
    keyring.set_password(SERVICE_NAME, ACCOUNT_NAME, token)

def get_token() -> str | None:
    """Retrieves the GitHub PAT from the native OS Credential Locker."""
    return keyring.get_password(SERVICE_NAME, ACCOUNT_NAME)

def delete_token() -> None:
    """Removes the GitHub PAT from the OS Credential Locker (for logout/reset)."""
    try:
        keyring.delete_password(SERVICE_NAME, ACCOUNT_NAME)
    except PasswordDeleteError:
        pass
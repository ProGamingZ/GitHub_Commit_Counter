from dataclasses import dataclass
from enum import Enum
from typing import Optional

class Status(Enum):
    SUCCESS = "SUCCESS"
    NOT_FOUND = "NOT_FOUND"
    RATE_LIMITED = "RATE_LIMITED"
    FORMAT_ERROR = "FORMAT_ERROR"

@dataclass
class StudentRecord:
    username: str
    profile_url: str

@dataclass
class ProcessingResult:
    username: str
    commit_count: int
    profile_url: str
    status: Status
    error_detail: Optional[str] = None
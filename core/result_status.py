from enum import Enum


class ResultStatus(str, Enum):
    PASSED = "Passed"
    FAILED = "Failed"
    BLOCKED = "Blocked"
    ACCESS_RESTRICTED = "Access Restricted"
    INCONCLUSIVE = "Inconclusive"
    TIMEOUT = "Timeout"
    NEEDS_REVIEW = "Needs Review"

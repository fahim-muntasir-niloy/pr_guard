from pydantic import BaseModel, ConfigDict
from typing import Literal, List, Optional


ReviewEvent = Literal["APPROVE", "REQUEST_CHANGES", "COMMENT"]
Severity = Literal["blocker", "major", "minor", "nit"]


class InlineComment(BaseModel):
    """
    Inline PR review comment for GitHub's Reviews API.
    """

    model_config = ConfigDict(extra="forbid")

    path: str
    position: int  # diff hunk index (1-based, mandatory for Reviews API)
    side: Literal["LEFT", "RIGHT"] = "RIGHT"  # which side of the diff
    body: str  # explanation (no code here)
    severity: Severity  # internal severity tracking
    suggestion: Optional[str] = None  # raw code suggestion


class GitHubPRReview(BaseModel):
    """
    Payload directly mappable to GitHub's PR Review API.
    """

    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"additionalProperties": False}
    )

    event: ReviewEvent
    body: str  # top-level review comment
    comments: List[InlineComment]

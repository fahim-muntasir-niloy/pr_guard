from pydantic import BaseModel, ConfigDict, Field
from typing import Literal, List, Optional


ReviewEvent = Literal["APPROVE", "REQUEST_CHANGES", "COMMENT"]
Severity = Literal["blocker", "major", "minor", "nit"]


class InlineComment(BaseModel):
    """
    Inline PR review comment for GitHub's Reviews API.
    Uses modern line + side approach (position is deprecated).
    """

    model_config = ConfigDict(extra="forbid")

    path: str
    line: int  # absolute line number in the changed file
    side: Literal["LEFT", "RIGHT"] = "RIGHT"  # LEFT for deletions, RIGHT for additions
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
    comments: list[InlineComment]
    commit_id: Optional[str] = Field(
        default=None, description="SHA of the commit (anchors line+side resolution)"
    )

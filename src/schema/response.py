from pydantic import BaseModel, ConfigDict
from typing import Literal, Optional, List


Severity = Literal["blocker", "major", "minor", "nit"]
Verdict = Literal["Approve", "Request Changes", "Comment"]


class DiffHunk(BaseModel):
    """
    Represents a GitHub-style diff hunk.
    """
    model_config = ConfigDict(extra="forbid")

    old_range: str   # e.g. "-12,6"
    new_range: str   # e.g. "+12,9"
    diff: str        # raw diff text with +++ / --- / @@


class InlineReviewComment(BaseModel):
    """
    A single inline review comment tied to a diff.
    """
    model_config = ConfigDict(extra="forbid")

    file_path: str
    line_number: int                # line number in the NEW file
    severity: Severity
    message: str                    # concise, actionable feedback
    suggestion: Optional[str] = None
    diff_hunk: Optional[DiffHunk]   # required when commenting inline


class FileReview(BaseModel):
    """
    Review summary for a single changed file.
    """
    model_config = ConfigDict(extra="forbid")

    file_path: str
    change_type: Literal["added", "modified", "deleted"]
    intent: str                     # what this change is trying to do
    risk_level: Literal["low", "medium", "high"]
    inline_comments: List[InlineReviewComment]


class PRSummary(BaseModel):
    """
    High-level PR understanding.
    """
    model_config = ConfigDict(extra="forbid")

    overview: str                   # 2–4 sentences, no fluff
    main_changes: List[str]         # bullet-style key changes
    risks: List[str]                # empty if none


class pr_agent_response(BaseModel):
    """
    Final PR review payload.
    """
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"additionalProperties": False}
    )

    summary: PRSummary
    files: List[FileReview]
    verdict: Verdict
    blocking_issues_count: int
    overall_comment: str            # appears as top-level GitHub review comment

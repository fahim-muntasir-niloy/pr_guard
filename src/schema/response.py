from pydantic import BaseModel, ConfigDict
from typing import Literal


class line_change(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"additionalProperties": False}
    )
    line_number: int
    line_content: str
    action_required: str

class file_change(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"additionalProperties": False}
    )
    file_name: str
    line_changes: list[line_change]

class pr_agent_response(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"additionalProperties": False}
    )
    file_changes: list[file_change]
    verdict: Literal["Approve", "Request Changes", "Comment"]
    comment: str
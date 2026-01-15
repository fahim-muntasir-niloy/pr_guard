from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class NoInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"additionalProperties": False}
    )


class ListFilesInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"additionalProperties": False}
    )
    path: str = Field(description="Directory path to list (default: current dir)")
    max_depth: int = Field(description="Maximum recursion depth")


class ReadFileInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"additionalProperties": False}
    )
    file_path: str = Field(description="The path of the file to read")


class GitDiffInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"additionalProperties": False}
    )
    base: Optional[str] = Field(
        description="Base branch/commit. Defaults to main/master."
    )
    head: str = Field(description="Head branch/commit. Defaults to HEAD.")


class GitLogInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"additionalProperties": False}
    )
    limit: int = Field(description="Number of commits to show")


class SearchCodeInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"additionalProperties": False}
    )
    pattern: str = Field(description="The string or pattern to search for")
    path: str = Field(description="Directory to search in")


class ListChangedFilesInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"additionalProperties": False}
    )
    base: Optional[str] = Field(
        description="Base branch/commit. Defaults to main/master."
    )
    head: str = Field(description="Head branch/commit. Defaults to HEAD.")


class GHCreatePRInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"additionalProperties": False}
    )
    title: str = Field(description="The title of the pull request")
    body: str = Field(
        description="""Description of the pull request. 
    Make the description only from the latest commits in this current PR, 
    not from the older commits."""
    )
    base: Optional[str] = Field(description="The branch into which the PR is merged.")
    head: Optional[str] = Field(
        description="The branch that contains the changes. Defaults to current branch."
    )
    draft: bool = Field(
        default=False, description="Whether to create the PR as a draft"
    )


class GHViewPRInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"additionalProperties": False}
    )
    pr_number: Optional[int] = Field(
        description="The PR number to view. If not provided, views the current branch's PR."
    )


class GHCommandInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"additionalProperties": False}
    )
    command: str = Field(description="The GitHub CLI command to execute")


class GitCommandInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"additionalProperties": False}
    )
    command: str = Field(description="The Git CLI command to execute")

from typing import List, Optional, Type
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

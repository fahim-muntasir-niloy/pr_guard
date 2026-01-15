from typing import List, Optional, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., description="Message to send to the AI assistant")
    thread_id: Optional[str] = Field(
        None, description="Optional thread ID to maintain conversation state"
    )


class GitStatus(BaseModel):
    branch: str = Field(..., description="Current git branch")
    last_commit: str = Field(..., description="Last commit hash and subject")


class StatusResponse(BaseModel):
    git: Any = Field(..., description="Git repository status")
    openai_api_key: str = Field(..., description="Status of the OpenAI API key")
    langsmith_api_key: str = Field(..., description="Status of the LangSmith API key")
    langsmith_tracing: bool = Field(
        ..., description="Whether LangSmith tracing is enabled"
    )


class TreeResponse(BaseModel):
    path: str = Field(..., description="The path listed")
    tree: str = Field(..., description="The directory structure in tree format")


class ChangedFilesResponse(BaseModel):
    base: str = Field(..., description="Base reference")
    head: str = Field(..., description="Head reference")
    files: List[str] = Field(..., description="List of changed file paths")


class DiffResponse(BaseModel):
    base: str = Field(..., description="Base reference")
    head: str = Field(..., description="Head reference")
    diff: str = Field(..., description="Git diff content")


class CommitInfo(BaseModel):
    hash: str = Field(..., description="Short commit hash")
    author: str = Field(..., description="Author name")
    date: str = Field(..., description="Commit date")
    subject: str = Field(..., description="Commit message subject")


class LogResponse(BaseModel):
    limit: int = Field(..., description="Number of commits returned")
    log: List[CommitInfo] = Field(..., description="List of commit logs")


class CatResponse(BaseModel):
    path: str = Field(..., description="File path")
    content: str = Field(..., description="File content")

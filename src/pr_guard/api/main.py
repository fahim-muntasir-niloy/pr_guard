from fastapi.responses import StreamingResponse, JSONResponse
from fastapi import Request
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pr_guard.api.utils import review_event_generator, chat_event_generator
from pr_guard.schema.api_schema import (
    ChatRequest,
    ChatPullRequest,
    StatusResponse,
    TreeResponse,
    ChangedFilesResponse,
    DiffResponse,
    LogResponse,
    CatResponse,
)
from pr_guard.cli.logging_config import setup_logger

app = FastAPI(
    title="PR Guard API",
    description="API for AI-powered Pull Request Reviewer and Guard",
    version="0.1.0",
)


@app.on_event("startup")
async def startup_event():
    setup_logger()

    """Setup environment variables on startup."""
    from pr_guard.cli.utils import setup_env

    setup_env()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def app_exception_handler(request: Request, exc: Exception):
    logger = setup_logger()
    logger.error(f"{exc.__class__.__name__}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )


@app.get(
    "/status",
    response_model=StatusResponse,
    tags=["General"],
    summary="Get environment and repository status",
    description="Returns the current git branch, last commit, and configuration status for API keys.",
)
async def status():
    import subprocess
    from pr_guard.config import settings
    import os

    status_data = {}
    try:
        branch = (
            subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
            .decode()
            .strip()
        )
        last_commit = (
            subprocess.check_output(["git", "log", "-1", "--format=%h %s"])
            .decode()
            .strip()
        )
        status_data["git"] = {"branch": branch, "last_commit": last_commit}
    except Exception:
        status_data["git"] = "Not a git repo or git not found"

    status_data["openai_api_key"] = (
        "Configured" if settings.OPENAI_API_KEY else "Missing"
    )
    status_data["langsmith_api_key"] = (
        "Configured" if settings.LANGSMITH_API_KEY else "Missing"
    )
    status_data["langsmith_tracing"] = os.getenv("LANGSMITH_TRACING") == "true"

    return status_data


@app.get(
    "/tree",
    response_model=TreeResponse,
    tags=["Repository"],
    summary="Visualize project structure",
    description="Returns a tree-like visualization of the project's directory structure.",
)
async def tree(
    path: str = Query(".", description="Path to list (defaults to project root)"),
):
    from pr_guard.utils.tool_utils import _list_files_tree

    output = await _list_files_tree(path=path)
    return {"path": path, "tree": output}


@app.get(
    "/changed",
    response_model=ChangedFilesResponse,
    tags=["Git"],
    summary="List changed files",
    description="Lists the files that have changed between two git references.",
)
async def changed(
    base: str = Query("master", description="Base branch or commit"),
    head: str = Query("HEAD", description="Head branch or commit"),
):
    from pr_guard.utils.tool_utils import _list_changed_files_between_branches

    files = await _list_changed_files_between_branches(base=base, head=head)
    return {
        "base": base,
        "head": head,
        "files": files.splitlines() if files.strip() else [],
    }


@app.get(
    "/diff",
    response_model=DiffResponse,
    tags=["Git"],
    summary="Get git diff",
    description="Returns the unified git diff between two references.",
)
async def diff(
    base: str = Query("master", description="Base branch or commit"),
    head: str = Query("HEAD", description="Head branch or commit"),
):
    from pr_guard.utils.tool_utils import _get_git_diff_between_branches

    diff_content = await _get_git_diff_between_branches(base=base, head=head)
    return {"base": base, "head": head, "diff": diff_content}


@app.get(
    "/log",
    response_model=LogResponse,
    tags=["Git"],
    summary="Show commit log",
    description="Returns a list of recent commits with hash, author, date, and subject.",
)
async def log(
    limit: int = Query(10, description="Number of commits to retrieve", ge=1),
):
    from pr_guard.utils.tool_utils import _get_git_log

    log_content = await _get_git_log(limit=limit)
    return {"limit": limit, "log": log_content}


@app.get(
    "/cat",
    response_model=CatResponse,
    tags=["Repository"],
    summary="Read file content",
    description="Reads and returns the content of a specific file in the repository.",
)
async def cat(path: str = Query(..., description="File path relative to project root")):
    from pr_guard.utils.tool_utils import _read_file_cat

    content = await _read_file_cat(file_path=path)
    if content.startswith("Error:"):
        raise HTTPException(status_code=404, detail=content)
    return {"path": path, "content": content}


@app.post(
    "/review",
    tags=["AI"],
    summary="Trigger AI code review (Streaming)",
    description="Starts a streaming AI code review process. Yields tool calls and eventually the full review report as SSE events.",
)
async def review():
    from pr_guard.agent import init_review_agent

    agent = await init_review_agent()
    return StreamingResponse(
        review_event_generator(agent), media_type="text/event-stream"
    )


@app.post(
    "/chat",
    tags=["AI"],
    summary="Chat with PR Guard (Streaming)",
    description="""Starts a streaming chat session with the PR Guard assistant. 
    Yields tokens and tool calls as SSE events.""",
)
async def chat(request: ChatRequest):
    import uuid
    from pr_guard.agent import chat_agent

    thread_id = request.thread_id or str(uuid.uuid4())
    agent = await chat_agent()
    return StreamingResponse(
        chat_event_generator(agent, request.message, thread_id),
        media_type="text/event-stream",
    )


@app.post(
    "/one-click-pr",
    tags=["GitHub"],
    summary="Create a new pull request directly by one-tap",
    description="Creates a new pull request on GitHub.",
)
async def one_click_pr(request: ChatPullRequest):
    import uuid
    from pr_guard.agent import one_click_pr_agent

    user_instructions = request.user_instructions
    base = request.base
    head = request.head

    message = f"""
    You are an automated GitHub Pull Request generator.

    Your task is to create a new pull request based ONLY on the provided commit history.

    Rules:
    - Take into account the user instructions provided -> {user_instructions}.
    - First check if there is already a PR open between {base} and {head}. If so, respond with the existing PR details only.
    - Take pull in both {base} and {head} branches
    - Summarize only the commits included in this pull request.
    - Ignore any commits that happened before the last merge commit.
    - Do not invent changes or features.
    - Be concise and technical.
    - Use clear bullet points for changes.
    - If no meaningful changes exist, say so explicitly.

    Output format:
    Title: <short, descriptive PR title>
    PR url: <url to the pull request>

    PR description:
    - <bullet point summary of changes>

    Breaking changes:
    - <bullet point summary of breaking changes>

    Do not include explanations, disclaimers, or markdown outside this format.
    """
    agent = await one_click_pr_agent()
    return StreamingResponse(
        chat_event_generator(agent, message, thread_id=str(uuid.uuid4())),
        media_type="text/event-stream",
    )

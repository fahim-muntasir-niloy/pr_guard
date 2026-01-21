from fastapi.responses import StreamingResponse, JSONResponse
from fastapi import Request
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pr_guard.api.utils import (
    review_event_generator,
    chat_event_generator,
    pr_event_generator,
)
from pr_guard.schema.api_schema import (
    ChatRequest,
    ChatPullRequest,
    StatusResponse,
    TreeResponse,
    ChangedFilesResponse,
    DiffResponse,
    LogResponse,
    CatResponse,
    ConfigRequest,
    ConfigResponse,
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

    status_code = 500
    message = "Internal server error"
    error_type = exc.__class__.__name__

    # Specific AI provider error handling
    if "RateLimitError" in error_type or "insufficient_quota" in str(exc).lower():
        status_code = 429
        message = (
            "OpenAI Quota Exceeded. Please check your billing/usage limits at "
            "https://platform.openai.com/account/billing"
        )
    elif "AuthenticationError" in error_type or "api_key" in str(exc).lower():
        status_code = 401
        message = (
            "Invalid API Key. Please verify your OPENAI_API_KEY in the environment."
        )
    elif isinstance(exc, HTTPException):
        status_code = exc.status_code
        message = exc.detail

    return JSONResponse(
        status_code=status_code,
        content={
            "error": message,
            "type": error_type,
            "details": str(exc) if status_code != 500 else None,
        },
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
    status_data["xai_api_key"] = "Configured" if settings.XAI_API_KEY else "Missing"
    status_data["anthropic_api_key"] = (
        "Configured" if settings.ANTHROPIC_API_KEY else "Missing"
    )
    status_data["google_api_key"] = (
        "Configured" if settings.GOOGLE_API_KEY else "Missing"
    )
    status_data["llm_provider"] = settings.LLM_PROVIDER
    status_data["llm_model"] = settings.LLM_MODEL
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
    Create a Pull Request with the following details:
    - Base branch: {base or "automatic detection"}
    - Head branch: {head or "current branch"}
    - User instructions: {user_instructions if user_instructions else "None"}

    Remember to only include changes from the {head} branch relative to the {base} branch, 
    focusing on commits since the last merge.
    """
    agent = await one_click_pr_agent()
    return StreamingResponse(
        pr_event_generator(agent, message),
        media_type="text/event-stream",
    )


@app.get(
    "/branches",
    tags=["Git"],
    summary="List git branches",
    description="Returns a list of all local and remote git branches.",
)
async def list_branches():
    from pr_guard.utils.git_utils import _run_git_command

    try:
        raw = _run_git_command(["branch", "-a"])
        branches = set()
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            # Remove * for current branch
            clean_name = line.replace("* ", "").strip()
            # Remove remotes/origin/ prefix to get clean names
            if clean_name.startswith("remotes/origin/"):
                clean_name = clean_name.replace("remotes/origin/", "")

            if "->" not in clean_name:
                branches.add(clean_name)

        return {"branches": sorted(list(branches))}
    except Exception:
        return {"branches": ["master", "main", "HEAD"]}


@app.post(
    "/config",
    response_model=ConfigResponse,
    tags=["General"],
    summary="Update PR Guard configuration",
    description="Updates the provider, model, and API keys in the .env file.",
)
async def update_config(request: ConfigRequest):
    from pr_guard.cli.utils import update_env_file

    if request.llm_provider:
        update_env_file("LLM_PROVIDER", request.llm_provider)
    if request.llm_model:
        update_env_file("LLM_MODEL", request.llm_model)
    if request.openai_api_key:
        update_env_file("OPENAI_API_KEY", request.openai_api_key)
    if request.xai_api_key:
        update_env_file("XAI_API_KEY", request.xai_api_key)
    if request.anthropic_api_key:
        update_env_file("ANTHROPIC_API_KEY", request.anthropic_api_key)
    if request.google_api_key:
        update_env_file("GOOGLE_API_KEY", request.google_api_key)

    return {
        "status": "success",
        "message": "Configuration updated successfully. Please restart the server for changes to take effect.",
    }

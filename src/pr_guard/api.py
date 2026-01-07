from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pr_guard.tools import (
    _list_files_tree,
    _list_changed_files_between_branches,
    _read_file_cat,
    _get_git_diff_between_branches,
    _get_git_log,
)
from pr_guard.agent import init_agent
import os

app = FastAPI(
    title="PR Guard API",
    description="Backend API for PR Guard - AI Powered Code Reviewer",
    version="0.2.1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "0.2.1"}


@app.get("/file_tree")
async def file_tree(path: str = "."):
    return await _list_files_tree(path=path)


@app.get("/file/{path:path}")
async def read_file(path: str):
    base_dir = os.path.abspath(os.getcwd())
    abs_path = os.path.abspath(os.path.join(base_dir, path))
    if not (abs_path == base_dir or abs_path.startswith(base_dir + os.sep)):
        raise HTTPException(
            status_code=403, detail="Access outside repository is not allowed."
        )
    content = await _read_file_cat(file_path=abs_path)
    if content.startswith("Error:"):
        # Avoid leaking full server path in error message
        raise HTTPException(status_code=400, detail=f"Error reading path: {path}")
    return {"path": path, "content": content}


@app.get("/changed_files")
async def changed_files(base: str = "master", head: str = "HEAD"):
    return await _list_changed_files_between_branches(base=base, head=head)


@app.get("/diff")
async def git_diff(base: str = "master", head: str = "HEAD"):
    return await _get_git_diff_between_branches(base=base, head=head)


@app.get("/log")
async def git_log(limit: int = 10):
    return await _get_git_log(limit=limit)


@app.get("/config")
async def get_config():
    from pr_guard.config import settings

    return {
        "project_name": "PR Guard",
        "openai_api_key_set": bool(settings.OPENAI_API_KEY),
        "langsmith_api_key_set": bool(settings.LANGSMITH_API_KEY),
        "github_token_set": bool(settings.GITHUB_TOKEN),
        "langsmith_tracing": os.getenv("LANGSMITH_TRACING", "false"),
    }


@app.get("/status")
async def get_status():
    import subprocess

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
        return {"branch": branch, "last_commit": last_commit, "ready": True}
    except Exception as e:
        return {"ready": False, "error": str(e)}


@app.post("/review")
async def review_pr():
    try:
        agent = await init_agent()
        res = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": "Execute a pre-merge code review for the latest git commits.",
                    }
                ]
            }
        )
        return res["structured_response"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Serve Landing Page
@app.get("/")
async def read_index():
    index_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "web", "index.html"
    )
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Landing page not found. Please check web/index.html"}


# Optional: Mount static files if you add images/css files
# app.mount("/static", StaticFiles(directory="web"), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("pr_guard.api:app", host="0.0.0.0", port=8000, reload=True)

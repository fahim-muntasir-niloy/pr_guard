from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.tools import list_files_tree, list_changed_files

app = FastAPI(
    title="PR Guard",
    description="PR Guard is a tool to review pull requests.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/file_tree/{path}")
async def file_tree(path: str = "."):
    return await list_files_tree(path=path)

@app.get("/changed_files")
@app.get("/changed_files/{base}")
@app.get("/changed_files/{base}/{head}")
async def changed_files(base: str = None, head: str = "HEAD"):
    """
    Returns files changed between base and head.
    Defaults to master...HEAD if no parameters are provided.
    """
    return await list_changed_files(base=base, head=head)

# @app.post("/review")
# async def review_pr():
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pr_guard.tools import list_files_tree, list_changed_files_between_branches

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


@app.get("/changed_files/{base}/{head}")
async def changed_files(base: str = "master", head: str = "dev"):
    return await list_changed_files_between_branches(base=base, head=head)


# @app.post("/review")
# async def review_pr():

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

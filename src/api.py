from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.tools import list_files_tree

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
async def list_files_tree(path: str = "."):
    return list_files_tree.invoke({"path": path})

# @app.post("/review")
# async def review_pr():
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

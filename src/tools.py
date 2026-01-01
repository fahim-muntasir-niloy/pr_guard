import os
import subprocess
from typing import List, Optional
from langchain.tools import tool
from src.utils.git_utils import _run_git_command, get_default_branch

@tool
def list_files_tree(path: str = ".", max_depth: int = 3) -> str:
    """
    Returns the directory structure of the specified path in a tree-like format.
    Use this to understand the project structure.
    """
    output = []
    ignored = {".git", "__pycache__", "node_modules", ".venv", "venv"}

    def _build_tree(current_path: str, prefix: str = "", depth: int = 0):
        if depth > max_depth:
            return
        
        try:
            items = sorted(os.listdir(current_path))
        except Exception as e:
            output.append(f"{prefix}[Error reading {current_path}: {e}]")
            return

        for i, item in enumerate(items):
            if item in ignored:
                continue
            
            full_path = os.path.join(current_path, item)
            is_last = (i == len(items) - 1)
            connector = "└── " if is_last else "├── "
            
            output.append(f"{prefix}{connector}{item}")
            
            if os.path.isdir(full_path):
                extension = "    " if is_last else "│   "
                _build_tree(full_path, prefix + extension, depth + 1)

    output.append(path)
    _build_tree(path)
    return "\n".join(output)

@tool
def read_file_cat(file_path: str) -> str:
    """
    Reads the content of a specific file.
    Use this to see the implementation details of a file.
    """
    if not os.path.exists(file_path):
        return f"Error: File '{file_path}' not found."
    
    if os.path.isdir(file_path):
        return f"Error: '{file_path}' is a directory. Use list_files_tree instead."

    # Safety check: Avoid reading very large files (e.g., > 1MB)
    try:
        if os.path.getsize(file_path) > 1_000_000:
            return f"Error: File '{file_path}' is too large to read (> 1MB)."
        
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool
def list_git_branches() -> str:
    """
    Returns the list of git branches.
    Use this to see the available branches.
    and get the default branch name
    """
    return _run_git_command(["branch", "-a"])

@tool
def get_git_diff(base: Optional[str] = None, head: str = "HEAD") -> str:
    """
    Returns the git diff between two branches or commits.
    Use this to see what exact changes were made in a PR.
    """
    if base is None:
        base = get_default_branch()
    return _run_git_command(["diff", f"{base}...{head}"])

@tool
def get_git_log(limit: int = 10) -> str:
    """
    Returns the recent git commit log.
    Use this to understand the history of changes.
    """
    return _run_git_command(["log", f"-n {limit}", "--oneline", "--graph", "--all"])

@tool
def search_code_grep(pattern: str, path: str = ".") -> str:
    """
    Searches for a pattern in the codebase.
    Use this to find references to functions, classes, or specific strings.
    """
    # Using python's os.walk instead of grep for cross-platform compatibility
    results = []
    ignored_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv"}
    
    try:
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line_num, line in enumerate(f, 1):
                            if pattern in line:
                                results.append(f"{file_path}:{line_num}: {line.strip()}")
                except Exception:
                    continue # Skip files that can't be read
    except Exception as e:
        return f"Error searching: {str(e)}"
    
    if not results:
        return f"No matches found for '{pattern}'."
    
    return "\n".join(results[:50]) # Limit to 50 results

@tool
def list_changed_files(base: Optional[str] = None, head: str = "HEAD") -> str:
    """
    Lists the files that have changed between two git references (e.g., base...head).
    If base is not provided, it defaults to master/main.
    If this returns blank, it may mean you are already on the base branch. 
    In that case, use get_last_commit_info to see the latest changes.
    """
    if base is None:
        base = get_default_branch()
    return _run_git_command(["diff", "--name-only", f"{base}...{head}"])

@tool
def get_last_commit_info() -> str:
    """
    Returns the changed files and the diff of the latest commit (HEAD~1...HEAD).
    Use this if list_changed_files is empty or you want to review the very last change on the current branch.
    """
    files = _run_git_command(["diff", "--name-only", "HEAD~1", "HEAD"])
    diff = _run_git_command(["diff", "HEAD~1", "HEAD"])
    return f"Changed Files in latest commit:\n{files}\n\nDiff of latest commit:\n{diff}"


TOOLS = [
    list_files_tree,
    read_file_cat,
    list_git_branches,
    get_git_diff,
    get_git_log,
    search_code_grep,
    list_changed_files,
    get_last_commit_info,
]
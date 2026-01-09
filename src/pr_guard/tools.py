import os
from typing import Optional
from langchain.tools import tool
from pr_guard.utils.git_utils import (
    _run_git_command,
    _run_shell_command,
    get_default_branch,
    _split_command,
)
from pr_guard.schema.tool_schema import (
    ListFilesInput,
    NoInput,
    ReadFileInput,
    GitDiffInput,
    GitLogInput,
    SearchCodeInput,
    ListChangedFilesInput,
    GHCreatePRInput,
    GHViewPRInput,
    GHCommandInput,
)


async def _list_files_tree(path: str = ".", max_depth: int = 3) -> str:
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
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "

            output.append(f"{prefix}{connector}{item}")

            if os.path.isdir(full_path):
                extension = "    " if is_last else "│   "
                _build_tree(full_path, prefix + extension, depth + 1)

    output.append(path)
    _build_tree(path)
    return "\n".join(output)


@tool(args_schema=ListFilesInput)
async def list_files_tree(path: str = ".", max_depth: int = 3) -> str:
    """
    Returns the directory structure of the specified path in a tree-like format.
    Use this to understand the project structure.
    """
    return await _list_files_tree(path=path, max_depth=max_depth)


async def _read_file_cat(file_path: str) -> str:
    if not os.path.exists(file_path):
        return f"Error: File '{file_path}' not found."

    if os.path.isdir(file_path):
        return f"Error: '{file_path}' is a directory. Use list_files_tree instead."

    try:
        if os.path.getsize(file_path) > 1_000_000:
            return f"Error: File '{file_path}' is too large to read (> 1MB)."

        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool(args_schema=ReadFileInput)
async def read_file_cat(file_path: str) -> str:
    """
    Reads the content of a specific file.
    Use this to see the implementation details of a file.
    """
    return await _read_file_cat(file_path=file_path)


@tool(args_schema=NoInput)
async def list_git_branches() -> str:
    """
    Returns the list of git branches.
    Use this to see the available branches and get the default branch name.
    """
    return _run_git_command(["branch", "-a"])


async def _get_git_diff_between_branches(
    base: Optional[str] = None, head: str = "HEAD"
) -> str:
    if base is None:
        base = get_default_branch()
    return _run_git_command(["diff", f"{base}...{head}"])


@tool(args_schema=GitDiffInput)
async def get_git_diff_between_branches(
    base: Optional[str] = None, head: str = "HEAD"
) -> str:
    """
    Returns the git diff between two branches or commits (base...head).
    Use this to see what exact changes were made in a PR.
    """
    return await _get_git_diff_between_branches(base=base, head=head)


async def _get_git_log(limit: int = 5) -> str:
    return _run_git_command(["log", "-n", str(limit), "--oneline", "--graph", "--all"])


@tool(args_schema=GitLogInput)
async def get_git_log(limit: int = 5) -> str:
    """
    Returns the recent git commit log.
    Use this to understand the history of changes.
    """
    return await _get_git_log(limit=limit)


@tool(args_schema=SearchCodeInput)
async def search_code_grep(pattern: str, path: str = ".") -> str:
    """
    Searches for a pattern in the codebase.
    Use this to find references to functions, classes, or specific strings.
    """
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
                                results.append(
                                    f"{file_path}:{line_num}: {line.strip()}"
                                )
                except Exception:
                    continue
    except Exception as e:
        return f"Error searching: {str(e)}"

    if not results:
        return f"No matches found for '{pattern}'."

    return "\n".join(results[:50])


async def _list_changed_files_between_branches(
    base: Optional[str] = None, head: Optional[str] = "HEAD"
) -> str:
    if base is None:
        base = get_default_branch()
    return _run_git_command(["diff", "--name-only", f"{base}...{head}"])


@tool(args_schema=ListChangedFilesInput)
async def list_changed_files_between_branches(
    base: Optional[str] = None, head: Optional[str] = "HEAD"
) -> str:
    """
    Lists the files that have changed between two git references (e.g., base...head).
    If base is not provided, it defaults to master/main.
    """
    return await _list_changed_files_between_branches(base=base, head=head)


@tool(args_schema=NoInput)
async def get_last_commit_info() -> str:
    """
    Returns the changed files and the diff of the latest commit (HEAD~1...HEAD).
    Use this to review the very last change on the current branch.
    """
    files = _run_git_command(["diff", "--name-only", "HEAD~1", "HEAD"])
    diff = _run_git_command(["diff", "HEAD~1", "HEAD"])
    return f"Changed Files in latest commit:\n{files}\n\nDiff of latest commit:\n{diff}"


@tool(args_schema=NoInput)
async def get_list_of_changed_files() -> dict[str, list[str]]:
    """
    Returns the changed files list of the latest commit (HEAD~1...HEAD).
    Use this to review the changed files of the current branch.
    """
    files = _run_git_command(["diff", "--name-only", "HEAD~1", "HEAD"])
    return {"files": files.splitlines()}


@tool(args_schema=ReadFileInput)
async def get_diff_of_single_file(file_path: str) -> str:
    """
    Returns the diff of the latest commit (HEAD~1...HEAD) for a specific file.
    Each line of the diff (including headers) is prefixed with its absolute [position: N].
    GitHub's Review API requires this 'position' for inline comments.
    """
    diff = _run_git_command(["diff", "HEAD~1", "HEAD", "--", file_path])
    if not diff:
        return "[position: 1] No changes found for this file."

    lines = diff.splitlines()
    marked_lines = []
    for i, line in enumerate(lines, 1):
        marked_lines.append(f"[position: {i}] {line}")

    return "\n".join(marked_lines)


@tool(args_schema=GHCreatePRInput)
async def gh_pr_create(
    title: str,
    body: str,
    base: Optional[str] = None,
    head: Optional[str] = None,
    draft: bool = False,
) -> str:
    """
    Creates a GitHub Pull Request using the 'gh' CLI.
    """
    cmd = ["gh", "pr", "create", "--title", title, "--body", body]
    if base:
        cmd.extend(["--base", base])
    if head:
        cmd.extend(["--head", head])
    if draft:
        cmd.append("--draft")

    return _run_shell_command(cmd)


@tool(args_schema=GHViewPRInput)
async def gh_pr_view(pr_number: Optional[int] = None) -> str:
    """
    Views a GitHub Pull Request using the 'gh' CLI.
    If pr_number is not provided, it views the PR for the current branch.
    """
    cmd = ["gh", "pr", "view"]
    if pr_number:
        cmd.append(str(pr_number))

    return _run_shell_command(cmd)


@tool(args_schema=GHCommandInput)
async def execute_github_command(command: str) -> str:
    """
    Executes a GitHub CLI command.
    commands will start with gh
    """
    cmd = _split_command(command)
    return _run_shell_command(cmd)


TOOLS = [
    cmd = _split_command(command)
    if not cmd or cmd[0] != "gh":
        return "Error: only 'gh' commands are allowed"
    return _run_shell_command(cmd)
    get_diff_of_single_file,
    list_files_tree,
    read_file_cat,
    list_git_branches,
    get_git_diff_between_branches,
    get_git_log,
    search_code_grep,
    list_changed_files_between_branches,
    gh_pr_create,
    gh_pr_view,
    execute_github_command,
]

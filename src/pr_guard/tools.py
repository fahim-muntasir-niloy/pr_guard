import json
from typing import Optional
from langchain.tools import tool
from pr_guard.utils.git_utils import (
    _run_git_command,
    _run_shell_command,
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
from pr_guard.utils.tool_utils import (
    _get_review_range,
    _list_files_tree,
    _read_file_cat,
    _get_git_diff_between_branches,
    _get_git_log,
    _list_changed_files_between_branches,
    _search_code_grep,
    _build_code,
)


@tool(args_schema=ListFilesInput)
async def list_files_tree(path: str = ".", max_depth: int = 3) -> str:
    """
    Returns the directory structure of the specified path in a tree-like format.
    Use this to understand the project structure.
    """
    return await _list_files_tree(path=path, max_depth=max_depth)


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


@tool(args_schema=GitDiffInput)
async def get_git_diff_between_branches(
    base: Optional[str] = None, head: str = "HEAD"
) -> str:
    """
    Returns the git diff between two branches or commits (base...head).
    Use this to see what exact changes were made in a PR.
    """
    return await _get_git_diff_between_branches(base=base, head=head)


@tool(args_schema=GitLogInput)
async def get_git_log(limit: int = 5) -> str:
    """
    Returns the recent git commit log.
    Use this to understand the history of changes.
    """
    logs = await _get_git_log(limit=limit)
    return json.dumps(logs, indent=4)


@tool(args_schema=SearchCodeInput)
async def search_code_grep(pattern: str, path: str = ".") -> str:
    """
    Searches for a pattern in the codebase.
    Use this to find references to functions, classes, or specific strings.
    """
    return await _search_code_grep(pattern=pattern, path=path)


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
    Returns the changed files and the diff of the current PR or last commit.
    Use this to review the recent changes.
    """
    base, head = _get_review_range()
    files = _run_git_command(["diff", "--name-only", f"{base}...{head}"])
    diff = _run_git_command(["diff", f"{base}...{head}"])
    return f"Changed Files:\n{files}\n\nDiff:\n{diff}"


@tool(args_schema=NoInput)
async def get_list_of_changed_files() -> dict[str, list[str]]:
    """
    Returns the list of files changed in the current PR or since the last commit.
    Use this to identify which files need review.
    """
    base, head = _get_review_range()
    files = _run_git_command(["diff", "--name-only", f"{base}...{head}"])
    return {"files": files.splitlines()}


@tool(args_schema=ReadFileInput)
async def get_diff_of_single_file(file_path: str) -> str:
    """
    Returns the unified diff for a specific file in the current PR range.
    Each line of the diff (including metadata and headers) is prefixed with its
    1-indexed [position: N] marker. GitHub's Reviews API requires this position.
    """
    base, head = _get_review_range()
    # Use unified diff to match GitHub's expectations
    diff = _run_git_command(["diff", f"{base}...{head}", "--", file_path])
    if not diff:
        return "[position: 1] No changes found for this file."

    lines = diff.splitlines()
    marked_lines = []
    for i, line in enumerate(lines, 1):
        marked_lines.append(f"[position: {i}] {line}")

    return "\n".join(marked_lines)


@tool(args_schema=NoInput)
async def build_code() -> str:
    """
    Automatically detects the project type and attempts to build the code.
    Returns the build output or error message if the build fails.
    Use this to verify if the changes break the build.
    """
    return await _build_code()


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
    Always ask for the branch names of base and head,
    if not clearly provided.
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
    if not cmd or cmd[0] != "gh":
        return "Error: only 'gh' commands are allowed"
    return _run_shell_command(cmd)


TOOLS = [
    get_list_of_changed_files,
    get_diff_of_single_file,
    build_code,
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

import os
import json
import glob
from typing import Optional
from pr_guard.utils.git_utils import (
    _run_git_command,
    get_default_branch,
)


def _get_review_range() -> tuple[str, str]:
    """
    Determines the git range to use for reviews.
    In CI, it uses GITHUB_BASE_REF and GITHUB_HEAD_REF.
    Locally, it defaults to master...HEAD or HEAD~1...HEAD.
    """
    base = os.getenv("GITHUB_BASE_REF")
    head = os.getenv("GITHUB_HEAD_REF") or "HEAD"

    if base:
        # In GitHub Actions, we typically need to reference the origin
        # unless it's explicitly checked out.
        return f"origin/{base}", head

    # Check if we are on a branch and master/main exists
    default = get_default_branch()
    current = _run_git_command(["rev-parse", "--abbrev-ref", "HEAD"]).strip()

    if current != default and "Error" not in current:
        return f"origin/{default}" if "Error" not in _run_git_command(
            ["rev-parse", "--verify", default]
        ) else default, head

    return "HEAD~1", "HEAD"


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


async def _get_git_diff_between_branches(
    base: Optional[str] = None, head: str = "HEAD"
) -> str:
    if base is None:
        base = get_default_branch()
    return _run_git_command(["diff", f"{base}...{head}"])


async def _get_git_log(limit: int = 5) -> list[dict]:
    log_format = '{"hash": "%h", "parents": "%p", "author": "%an", "date": "%as", "subject": "%s"}'
    # Use --all to include commits from all branches, including merge PRs
    output = _run_git_command(
        ["log", f"-n{limit}", "--all", f"--pretty=format:{log_format}"]
    )
    try:
        commits = []
        for line in output.splitlines():
            if not line.strip():
                continue
            commit = json.loads(line)
            # Convert space-separated parents to a list
            commit["parents"] = (
                commit["parents"].split() if commit.get("parents") else []
            )
            commits.append(commit)
        return commits
    except Exception as e:
        return [{"error": f"Error parsing git log to JSON: {e}"}]


async def _list_changed_files_between_branches(
    base: Optional[str] = None, head: Optional[str] = "HEAD"
) -> str:
    if base is None:
        base = get_default_branch()
    return _run_git_command(["diff", "--name-only", f"{base}...{head}"])


async def _test_project_build() -> dict:
    """
    Attempts to build the detected project and returns a structured result.
    """
    from pr_guard.utils.git_utils import _run_command

    # helper to run command and return dict-friendly result
    def run(cmd):
        return _run_command(cmd)

    # Node.js
    if os.path.isfile("package.json"):
        install = run(["npm", "install"])
        if install.returncode != 0:
            return {
                "success": False,
                "tool": "node",
                "log": install.stderr or install.stdout,
            }

        try:
            with open("package.json", encoding="utf-8") as f:
                pkg = json.load(f)

            if "build" not in pkg.get("scripts", {}):
                return {
                    "success": True,  # Still a success if no build step is needed
                    "tool": "node",
                    "log": "No build script in package.json, skipping build.",
                }

            build = run(["npm", "run", "build"])
            return {
                "success": build.returncode == 0,
                "tool": "node",
                "log": build.stdout if build.returncode == 0 else build.stderr,
            }
        except Exception as e:
            return {
                "success": False,
                "tool": "node",
                "log": f"Error reading package.json: {e}",
            }

    # Go
    if os.path.isfile("go.mod"):
        res = run(["go", "build", "./..."])
        return {
            "success": res.returncode == 0,
            "tool": "go",
            "log": res.stdout if res.returncode == 0 else res.stderr,
        }

    # Rust
    if os.path.isfile("Cargo.toml"):
        res = run(["cargo", "build"])
        return {
            "success": res.returncode == 0,
            "tool": "rust",
            "log": res.stdout if res.returncode == 0 else res.stderr,
        }

    # Python
    if any(
        os.path.isfile(f) for f in ("pyproject.toml", "requirements.txt", "setup.py")
    ):
        res = run(["uv", "sync"])
        return {
            "success": res.returncode == 0,
            "tool": "python",
            "log": res.stdout if res.returncode == 0 else res.stderr,
        }

    # .NET
    if glob.glob("*.sln") or glob.glob("*.csproj"):
        res = run(["dotnet", "build"])
        return {
            "success": res.returncode == 0,
            "tool": ".net",
            "log": res.stdout if res.returncode == 0 else res.stderr,
        }

    return {
        "success": False,
        "tool": None,
        "log": "No supported build environment detected (package.json, go.mod, Cargo.toml, pyproject.toml, .sln, etc.)",
    }


async def _build_code() -> str:
    """
    Automatically detects the project type and attempts to build the code.
    Returns the build output or error message if the build fails as a string.
    """
    res = await _test_project_build()
    status = "✅ Build Successful" if res["success"] else "❌ Build Failed"
    tool_info = f"({res['tool']})" if res["tool"] else ""

    return f"{status} {tool_info}:\n{res['log']}"

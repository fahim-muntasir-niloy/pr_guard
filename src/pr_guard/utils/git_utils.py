import subprocess
from typing import List


def _run_git_command(command: List[str], cwd: str = ".") -> str:
    """Helper to run git commands safely."""
    try:
        result = subprocess.run(
            ["git"] + command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if result.returncode != 0:
            return f"Error running git command: {result.stderr}"
        return result.stdout
    except Exception as e:
        return f"Error: {str(e)}"


def get_default_branch(cwd: str = ".") -> str:
    """Detects the default branch (master or main)."""
    # Try to find which one exists locally
    for branch in ["main", "master"]:
        out = _run_git_command(["rev-parse", "--verify", branch], cwd=cwd)
        if "Error" not in out:
            return branch
    return "master"  # Fallback

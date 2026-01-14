import subprocess
from typing import List
import shlex


def _run_command(command: List[str], cwd: str = ".") -> subprocess.CompletedProcess:
    """Run a command and return the full result object."""
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def _run_shell_command(command: List[str], cwd: str = ".") -> str:
    """Helper to run shell commands safely, returning stdout or an error string."""
    try:
        result = _run_command(command, cwd=cwd)
        if result.returncode != 0:
            return f"Error running command: {result.stderr or result.stdout}"
        return result.stdout
    except Exception as e:
        return f"Error: {str(e)}"


def _run_git_command(command: List[str], cwd: str = ".") -> str:
    """Helper to run git commands safely."""
    return _run_shell_command(["git"] + command, cwd=cwd)


def get_default_branch(cwd: str = ".") -> str:
    """Detects the default branch (master or main)."""
    # Try to find which one exists locally
    for branch in ["main", "master"]:
        out = _run_git_command(["rev-parse", "--verify", branch], cwd=cwd)
        if "Error" not in out:
            return branch
    return "master"  # Fallback


def _split_command(command: str) -> List[str]:
    args = shlex.split(command)
    return args

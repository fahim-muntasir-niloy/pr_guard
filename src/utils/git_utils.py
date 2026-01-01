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
            check=False
        )
        if result.returncode != 0:
            return f"Error running git command: {result.stderr}"
        return result.stdout
    except Exception as e:
        return f"Error: {str(e)}"

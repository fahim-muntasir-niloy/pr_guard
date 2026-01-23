import os
import json
import subprocess
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from pr_guard.cli.utils.terminal import console
from pr_guard.config import settings
from pr_guard.utils.tool_utils import (
    _list_files_tree,
    _get_git_diff_between_branches,
    _get_git_log,
    _list_changed_files_between_branches,
    _read_file_cat,
)


async def run_tree(path: str = "."):
    output = await _list_files_tree(path=path)
    console.print(Panel(output, title=f"📁 Project Tree: {path}", border_style="blue"))


async def run_changed(base: str = "master", head: str = "HEAD"):
    files = await _list_changed_files_between_branches(base=base, head=head)
    if not files.strip():
        console.print("[yellow]No files have changed.[/yellow]")
        return

    table = Table(title=f"📝 Changed Files: {base}...{head}", show_header=True)
    table.add_column("File Path", style="green")
    for file in files.splitlines():
        table.add_row(file)
    console.print(table)


async def run_diff(base: str = "master", head: str = "HEAD"):
    diff_content = await _get_git_diff_between_branches(base=base, head=head)
    syntax = Syntax(diff_content, "diff", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=f"🔍 Diff: {base}...{head}", expand=True))


async def run_log(limit: int = 10):
    log_data = await _get_git_log(limit=limit)
    log_content = json.dumps(log_data, indent=4)
    console.print(Panel(log_content, title="📜 Git Log", border_style="cyan"))


def run_status():
    table = Table(
        title="🛡️ PR Guard Status", show_header=True, header_style="bold magenta"
    )
    table.add_column("Component", style="cyan")
    table.add_column("Value", style="white")

    try:
        branch = (
            subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
            .decode()
            .strip()
        )
        last_commit = (
            subprocess.check_output(["git", "log", "-1", "--format=%h %s"])
            .decode()
            .strip()
        )
        table.add_row("Git Branch", branch)
        table.add_row("Last Commit", last_commit)
    except Exception:
        table.add_row("Git", "[red]Not a git repo or git not found[/red]")

    table.add_row(
        "OpenAI API Key",
        "[green]Configured[/green]"
        if settings.OPENAI_API_KEY
        else "[red]Missing[/red]",
    )
    table.add_row(
        "LangSmith Tracing",
        "[green]Enabled[/green]" if settings.LANGSMITH_API_KEY else "Disabled",
    )

    console.print(table)


async def run_cat(path: str):
    content = await _read_file_cat(file_path=path)
    if content.startswith("Error:"):
        console.print(f"[red]{content}[/red]")
        return

    ext = os.path.splitext(path)[1].lstrip(".") or "txt"
    syntax = Syntax(content, ext, theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title=f"📄 {path}"))

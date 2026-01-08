import typer
import asyncio
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
import os

from pr_guard.cli.utils import (
    run_review,
    chat_loop,
    check_gh_cli,
    console,
)
from pr_guard.tools import (
    _list_files_tree,
    _get_git_diff_between_branches,
    _get_git_log,
    _list_changed_files_between_branches,
    _read_file_cat,
)
from pr_guard.config import settings

app = typer.Typer(
    name="pr-guard",
    help="🛡️  AI-powered Pull Request Reviewer and Guard.",
    add_completion=False,
    rich_markup_mode="rich",
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False, "--version", "-v", help="Show version and exit"
    ),
):
    """
    🛡️  AI-powered Pull Request Reviewer and Guard.
    """
    if version:
        import importlib.metadata

        try:
            ver = importlib.metadata.version("pr-guard")
            console.print(f"PR Guard version: [bold cyan]{ver}[/bold cyan]")
        except importlib.metadata.PackageNotFoundError:
            console.print("PR Guard version: [bold cyan]0.2.1[/bold cyan] (local)")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        # Default to chat
        if check_gh_cli():
            asyncio.run(chat_loop())
        else:
            console.print(
                "[red]GitHub CLI integration is required for chat. Please resolve the issues above.[/red]"
            )


@app.command()
def review(
    plain: bool = typer.Option(
        False, "--plain", help="Output plain Markdown without styling."
    ),
):
    """
    🤖 [bold green]Review[/bold green] the current git changes.
    """
    asyncio.run(run_review(plain=plain))


@app.command()
def chat():
    """
    💬 [bold cyan]Chat[/bold cyan] interactively with PR Guard.
    """
    if check_gh_cli():
        asyncio.run(chat_loop())
    else:
        console.print(
            "[red]GitHub CLI integration is required for chat. Please resolve the issues above.[/red]"
        )


@app.command()
def tree(path: str = typer.Argument(".", help="Path to list")):
    """
    📁 [bold yellow]Tree[/bold yellow] view of the project structure.
    """

    async def _run():
        output = await _list_files_tree(path=path)
        console.print(
            Panel(output, title=f"📁 Project Tree: {path}", border_style="blue")
        )

    asyncio.run(_run())


@app.command()
def changed(
    base: str = typer.Option("master", "--base", "-b", help="Base branch"),
    head: str = typer.Option("HEAD", "--head", "-h", help="Head branch/commit"),
):
    """
    📝 [bold magenta]List[/bold magenta] files that have changed between refs.
    """

    async def _run():
        files = await _list_changed_files_between_branches(base=base, head=head)
        if not files.strip():
            console.print("[yellow]No files have changed.[/yellow]")
            return

        table = Table(title=f"📝 Changed Files: {base}...{head}", show_header=True)
        table.add_column("File Path", style="green")
        for file in files.splitlines():
            table.add_row(file)
        console.print(table)

    asyncio.run(_run())


@app.command()
def diff(
    base: str = typer.Option("master", "--base", "-b", help="Base branch"),
    head: str = typer.Option("HEAD", "--head", "-h", help="Head branch/commit"),
):
    """
    Show the git diff between two branches.
    """

    async def _run():
        diff_content = await _get_git_diff_between_branches(base=base, head=head)
        syntax = Syntax(diff_content, "diff", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title=f"🔍 Diff: {base}...{head}", expand=True))

    asyncio.run(_run())


@app.command()
def log(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of commits to show"),
):
    """
    Show the recent git commit log.
    """

    async def _run():
        log_content = await _get_git_log(limit=limit)
        console.print(Panel(log_content, title="📜 Git Log", border_style="cyan"))

    asyncio.run(_run())


@app.command()
def status():
    """
    🛡️  [bold cyan]Status[/bold cyan] of the environment and repository.
    """
    import subprocess

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
        "[green]Enabled[/green]"
        if os.getenv("LANGSMITH_TRACING") == "true"
        else "Disabled",
    )

    console.print(table)


@app.command()
def cat(path: str = typer.Argument(..., help="File path to read")):
    """
    Read and display a file with syntax highlighting.
    """

    async def _run():
        content = await _read_file_cat(file_path=path)
        if content.startswith("Error:"):
            console.print(f"[red]{content}[/red]")
            return

        ext = os.path.splitext(path)[1].lstrip(".") or "txt"
        syntax = Syntax(content, ext, theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title=f"📄 {path}"))

    asyncio.run(_run())


@app.command()
def version():
    """
    Show the version of PR Guard.
    """
    import importlib.metadata

    try:
        ver = importlib.metadata.version("pr-guard")
        console.print(f"PR Guard version: [bold cyan]{ver}[/bold cyan]")
    except importlib.metadata.PackageNotFoundError:
        console.print("PR Guard version: [bold cyan]0.2.1[/bold cyan] (local)")


if __name__ == "__main__":
    app()

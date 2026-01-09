import typer
import asyncio

from pr_guard.cli.utils import (
    run_review,
    chat_loop,
    check_gh_cli,
    console,
    run_init,
    run_tree,
    run_changed,
    run_diff,
    run_log,
    run_status,
    run_cat,
    run_version,
)

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
        run_version()
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
def init():
    """
    🚀 [bold green]Initialize[/bold green] GitHub Actions for automated PR review.
    """
    asyncio.run(run_init())


@app.command()
def review(
    plain: bool = typer.Option(
        False, "--plain", help="Output plain Markdown without styling."
    ),
    github: bool = typer.Option(
        False, "--github", help="Post review comments to GitHub PR."
    ),
):
    """
    🤖 [bold green]Review[/bold green] the current git changes.
    """
    asyncio.run(run_review(plain=plain, github=github))


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
    asyncio.run(run_tree(path=path))


@app.command()
def changed(
    base: str = typer.Option("master", "--base", "-b", help="Base branch"),
    head: str = typer.Option("HEAD", "--head", "-h", help="Head branch/commit"),
):
    """
    📝 [bold magenta]List[/bold magenta] files that have changed between refs.
    """
    asyncio.run(run_changed(base=base, head=head))


@app.command()
def diff(
    base: str = typer.Option("master", "--base", "-b", help="Base branch"),
    head: str = typer.Option("HEAD", "--head", "-h", help="Head branch/commit"),
):
    """
    Show the git diff between two branches.
    """
    asyncio.run(run_diff(base=base, head=head))


@app.command()
def log(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of commits to show"),
):
    """
    Show the recent git commit log.
    """
    asyncio.run(run_log(limit=limit))


@app.command()
def status():
    """
    🛡️  [bold cyan]Status[/bold cyan] of the environment and repository.
    """
    run_status()


@app.command()
def cat(path: str = typer.Argument(..., help="File path to read")):
    """
    Read and display a file with syntax highlighting.
    """
    asyncio.run(run_cat(path=path))


@app.command()
def version():
    """
    Show the version of PR Guard.
    """
    run_version()


if __name__ == "__main__":
    app()

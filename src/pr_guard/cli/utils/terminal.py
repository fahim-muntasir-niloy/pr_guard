import os
import subprocess
from rich.console import Console
from rich.table import Table

console = Console()


def show_cli_help():
    """
    Displays the CLI help menu with a premium look.
    """
    table = Table(
        title="🛡️ PR Guard Commands",
        border_style="cyan",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Command", style="bold green")
    table.add_column("Description", style="white")

    commands = [
        ("init", "Initialize GitHub Actions for automated PR review."),
        ("review", "Review current git changes with AI analysis."),
        ("chat", "Interactive assistant (default mode)."),
        ("pr", "Create a one-click pull request."),
        ("tree", "Visualize project directory structure."),
        ("changed", "List files changed between references."),
        ("diff", "Show git diff with syntax highlighting."),
        ("log", "Display recent git commit history."),
        ("status", "Check environment and repo status."),
        ("cat", "Read file content with highlighting."),
        ("version", "Display current PR Guard version."),
    ]

    for cmd, desc in commands:
        table.add_row(cmd, desc)

    console.print("\n")
    console.print(table)
    console.print(
        "\n[dim]Type [bold cyan]'exit'[/bold cyan] or [bold cyan]'quit'[/bold cyan] to leave the chat.[/dim]\n"
    )


def check_gh_cli():
    """
    Checks if GitHub CLI is installed and authenticated.
    If not, guides the user through installation and login.
    """
    try:
        subprocess.run(["gh", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print("[yellow]GitHub CLI (gh) not found.[/yellow]")
        install = console.input("Would you like to install GitHub CLI? (y/n): ")
        if install.lower() == "y":
            console.print("Please install GitHub CLI from: https://cli.github.com/")
            return False
        else:
            return False

    try:
        result = subprocess.run(
            ["gh", "auth", "status"], capture_output=True, text=True
        )
        if (
            "Logged in to github.com" not in result.stdout
            and "Logged in to github.com" not in result.stderr
        ):
            console.print("[yellow]You are not logged in to GitHub CLI.[/yellow]")
            login = console.input("Would you like to run 'gh auth login' now? (y/n): ")
            if login.lower() == "y":
                subprocess.run(["gh", "auth", "login"], check=True)
            else:
                return False
    except subprocess.CalledProcessError:
        console.print("[red]Error checking GitHub CLI status.[/red]")
        return False

    return True


def run_version():
    import importlib.metadata

    try:
        ver = importlib.metadata.version("pr-guard")
        console.print(f"PR Guard version: [bold cyan]{ver}[/bold cyan]")
    except importlib.metadata.PackageNotFoundError:
        console.print("PR Guard version: [bold cyan]0.2.1[/bold cyan] (local)")


def run_serve(host: str = "127.0.0.1", port: int = 8000):
    """
    🚀 Start the FastAPI server.
    """
    import uvicorn
    from pr_guard.api.main import app

    console.print(
        f"\n[bold green]🚀 Starting PR Guard API server at http://{host}:{port}[/bold green]"
    )
    console.print("[dim]Press Ctrl+C to stop the server[/dim]\n")

    uvicorn.run(app, host=host, port=port)

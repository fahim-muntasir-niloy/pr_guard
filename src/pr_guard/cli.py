from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.live import Live
from rich.markdown import Markdown
from rich.console import Group
from rich.text import Text
from pr_guard.agent import init_agent
from pr_guard.config import settings
from pr_guard.tools import (
    _list_files_tree,
    _get_git_diff_between_branches,
    _get_git_log,
    _list_changed_files_between_branches,
    _read_file_cat,
)
import os
import json
import asyncio
import typer

app = typer.Typer(
    name="pr-guard",
    help="🛡️  AI-powered Pull Request Reviewer and Guard.",
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console()


def setup_env():
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
    os.environ["LANGSMITH_PROJECT"] = "pr-agent"


async def run_review(plain: bool = False):
    if not plain:
        console.print(
            Panel(
                "[bold blue]🛡️ PR Guard[/bold blue] - [dim]Advanced AI Code Reviewer[/dim]",
                expand=False,
                border_style="blue",
            )
        )
    try:
        setup_env()

        status_manager = (
            console.status(
                "[bold green]🧠 Agent is analyzing changes...", spinner="dots"
            )
            if not plain
            else asyncio.Event()
        )

        async def _run():
            agent = await init_agent()

            res = await agent.ainvoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": "Execute a full code review for the latest git commits. Call the tools needed to understand the scope and diff.",
                        }
                    ]
                }
            )

            # Extract the structured response
            review_data = res["structured_response"]
            review_dict = review_data.model_dump()

            if plain:
                print(json.dumps(review_dict, indent=4))
                return

            # --- BEUTIFUL RICH REPORT ---
            event = review_dict.get("event", "COMMENT")
            event_color = (
                "green"
                if event == "APPROVE"
                else "red"
                if event == "REQUEST_CHANGES"
                else "yellow"
            )

            console.print("\n")
            console.print(
                Panel(
                    f"[bold {event_color}]{event}[/bold {event_color}]\n\n{review_dict.get('body', '')}",
                    title="🏁 Review Result",
                    border_style=event_color,
                    padding=(1, 2),
                )
            )

            if not review_dict.get("comments"):
                console.print(
                    "\n✨ [bold green]No issues found! Your code looks great.[/bold green]"
                )
                return

            console.print(
                f"\n[bold]🔍 Found {len(review_dict['comments'])} items to address:[/bold]\n"
            )

            for comment in review_dict["comments"]:
                severity = comment.get("severity", "nit").lower()
                sev_color = (
                    "red"
                    if severity == "blocker"
                    else "orange3"
                    if severity == "major"
                    else "yellow"
                    if severity == "minor"
                    else "dim"
                )

                # File and Line info
                info = f"[bold cyan]{comment['path']}[/bold cyan] : [bold white]Line {comment.get('line', '?')}[/bold white]"
                sev_badge = f"[{sev_color}]▐ {severity.upper()}[/{sev_color}]"

                body_panel = Panel(
                    f"{comment['body']}",
                    title=f"{sev_badge} {info}",
                    title_align="left",
                    border_style=sev_color,
                    padding=(0, 1),
                )
                console.print(body_panel)

                if comment.get("suggestion"):
                    syntax = Syntax(
                        comment["suggestion"],
                        os.path.splitext(comment["path"])[1].lstrip(".") or "python",
                        theme="monokai",
                        line_numbers=True,
                        line_range=(1, len(comment["suggestion"].splitlines())),
                    )
                    console.print(
                        Panel(
                            syntax,
                            title="💡 Suggested Fix",
                            border_style="green",
                            dim=True,
                        )
                    )
                console.print("")

        if not plain:
            with status_manager:
                await _run()
        else:
            await _run()

    except Exception as e:
        if not plain:
            console.print(f"\n[red]❌ Error:[/red] {e}")
        else:
            print(f"Error: {e}")
        raise typer.Exit(code=1)


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


async def run_comment():
    setup_env()
    agent = await init_agent()

    inputs = {
        "messages": [
            {
                "role": "user",
                "content": (
                    "Execute a pre-merge code review for the latest git commits.\n\n"
                    "**Output Requirements:**\n"
                    "- Use `### 📄 File: filename` for each file.\n"
                    "- Use `> [!IMPORTANT]` or `> [!NOTE]` for severity.\n"
                    "- ALWAYS wrap diffs in ```diff ... ``` blocks.\n"
                    "- Output ONLY valid Markdown meant for a GitHub comment."
                ),
            }
        ]
    }

    full_content = ""
    current_step = "initializing"

    # We'll use a Live display to show the progress
    with Live(auto_refresh=True, console=console) as live:

        def get_renderable():
            # Create a nice group of components
            step_text = Text.assemble(
                (" ⚙️  Current Step: ", "bold yellow"),
                (f"{current_step}", "cyan blink"),
            )

            md = Markdown(full_content or "_Waiting for content..._")

            return Panel(
                Group(
                    step_text,
                    Text(""),  # spacer
                    md,
                ),
                title="🛡️ [bold blue]PR Guard Streaming Review[/bold blue]",
                border_style="blue",
                padding=(1, 2),
            )

        live.update(get_renderable())

        async for mode, chunk in agent.astream(
            inputs, stream_mode=["updates", "messages"]
        ):
            if mode == "updates":
                for node_name, _ in chunk.items():
                    current_step = node_name
                    live.update(get_renderable())

            elif mode == "messages":
                msg_chunk, _ = chunk
                if msg_chunk.content:
                    full_content += msg_chunk.content
                    live.update(get_renderable())

    return full_content


@app.command()
def comment():
    """
    💬 [bold blue]Comment[/bold blue] on the current git changes in GitHub (Streaming).
    """
    asyncio.run(run_comment())


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
def summary():
    """
    📋 [bold green]Summary[/bold green] of the current PR changes.
    """

    async def _run():
        setup_env()
        with console.status("[bold green]Calculating summary...", spinner="arc"):
            agent = await init_agent()
            res = await agent.ainvoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": "Provide a high-level summary of the changes in this PR. List key files and the main intent of the modifications.",
                        }
                    ]
                }
            )
            console.print("\n")
            console.print(
                Panel(
                    res["messages"][-1].content,
                    title="📋 PR Summary",
                    border_style="green",
                    padding=(1, 2),
                )
            )

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

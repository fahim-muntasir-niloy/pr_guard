import os
import json
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.table import Table
from rich.text import Text
from rich.live import Live
from pr_guard.agent import init_review_agent, chat_agent
from pr_guard.config import settings
import uuid
from langchain.messages import AIMessageChunk
from pr_guard.utils.github_utils import post_github_review, build_github_review_payload
from pr_guard.tools import (
    _list_files_tree,
    _get_git_diff_between_branches,
    _get_git_log,
    _list_changed_files_between_branches,
    _read_file_cat,
)

console = Console()


def setup_env():
    if settings.LANGSMITH_API_KEY:
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
        os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGSMITH_PROJECT"] = "pr-agent"


def token_processor(token) -> str:
    """Safely extract a text token from various possible token formats."""
    try:
        # List of dicts: take the first item's text/content
        if isinstance(token, list) and token:
            first = token[0]
            if isinstance(first, dict):
                return first.get("text") or first.get("content") or ""
            # first element might be a string
            if isinstance(first, str):
                return first

        # Dict-like object
        if isinstance(token, dict):
            return token.get("text") or token.get("content") or ""

        # Plain string
        if isinstance(token, str):
            return token

        # Fallback: try attribute access (safe)
        if hasattr(token, "text"):
            return getattr(token, "text") or ""
        if hasattr(token, "content"):
            return getattr(token, "content") or ""

    except Exception:
        return ""

    return ""


async def run_review(plain: bool = False, github: bool = False):
    console.print("\n")
    console.print(
        "[bold blue]🛡️ PR Guard[/bold blue] - [dim]Advanced AI Code Reviewer[/dim]"
    )
    console.print("\n")
    setup_env()

    agent = await init_review_agent()

    # Track the result for the final report
    final_structured_res = None

    # Use modern astream with "updates" mode
    async for chunk in agent.astream(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Execute a full code review for the latest git commits. Call the tools needed to understand the scope and diff.",
                }
            ]
        },
        stream_mode="updates",
    ):
        for node_name, update in chunk.items():
            # 1. Stream the "Steps" (Detect tool calls in the message history)
            if "messages" in update:
                last_msg = update["messages"][-1]
                # Check for tool calls in the message
                if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                    for tc in last_msg.tool_calls:
                        # Format the arguments as a clean string
                        args_json = json.dumps(tc["args"])

                        if not plain:
                            console.print(
                                f"🔧 [bold dim]Calling tool:[/bold dim] [cyan]{tc['name']}[/cyan]"
                            )
                            console.print(f"[dim]   Input: {args_json}[/dim]")
                        else:
                            print(f"Calling tool: {tc['name']} with {args_json}")

            # 2. Capture the structured response if this node provides it
            if "structured_response" in update:
                final_structured_res = update["structured_response"]

    if not final_structured_res:
        return

    # --- REPORT DATA ---
    review_dict = final_structured_res.model_dump()

    # --- GITHUB POSTING ---
    if github:
        repo = os.getenv("GITHUB_REPOSITORY")
        pr_number = os.getenv("GITHUB_PR_NUMBER")
        token = os.getenv("GITHUB_TOKEN")

        if not all([repo, pr_number, token]):
            console.print(
                "[red]Error: GITHUB_REPOSITORY, GITHUB_PR_NUMBER, and GITHUB_TOKEN must be set for --github mode.[/red]"
            )
            return

        review_payload, file_comments = build_github_review_payload(review_dict)
        await post_github_review(
            repo=repo,
            pr_number=int(pr_number),
            token=token,
            review_payload=review_payload,
            file_comments=file_comments,
        )
        console.print("[bold green]✅ Review posted to GitHub![/bold green]")
        return

    # --- BEUTIFUL RICH REPORT ---

    if plain:
        print(json.dumps(review_dict, indent=4))
        return

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

        info = f"[bold cyan]{comment['path']}[/bold cyan]"
        sev_badge = f"[{sev_color}]▐ {severity.upper()}[/{sev_color}]"

        console.print(
            Panel(
                f"{comment['body']}",
                title=f"{sev_badge} {info}",
                title_align="left",
                border_style=sev_color,
                padding=(0, 1),
            )
        )

        if comment.get("suggestion"):
            syntax = Syntax(
                comment["suggestion"],
                os.path.splitext(comment["path"])[1].lstrip(".") or "python",
                theme="monokai",
                line_numbers=True,
            )
            console.print(Panel(syntax, title="💡 Suggested Fix", border_style="green"))
        console.print("")


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


async def run_init():
    """
    🚀 Initialize GitHub Actions for automated PR review.
    """
    workflow_path = ".github/workflows/pr_review.yml"
    os.makedirs(os.path.dirname(workflow_path), exist_ok=True)

    workflow_content = """name: PR Review Guard

on:
  pull_request:
    types: [opened, synchronize, reopened]
    branches:
      - master
      - main

jobs:
  review:
    runs-on: ubuntu-latest

    permissions:
      contents: read
      pull-requests: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          python-version: '3.13'

      - name: Run PR Guard Review
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          LANGSMITH_API_KEY: ${{ secrets.LANGSMITH_API_KEY }} # Optional
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPOSITORY: ${{ github.repository }}
          GITHUB_PR_NUMBER: ${{ github.event.pull_request.number }}
          GITHUB_BASE_REF: ${{ github.base_ref }}
          GITHUB_HEAD_REF: ${{ github.head_ref }}
        run: uvx --from git+https://github.com/fahim-muntasir-niloy/pr_guard.git pr-guard review --github
"""

    if os.path.exists(workflow_path):
        console.print(
            f"[yellow]Workflow file already exists at {workflow_path}[/yellow]"
        )
        import typer

        overwrite = typer.confirm("Do you want to overwrite it?")
        if not overwrite:
            console.print("[red]Aborted.[/red]")
            return

    with open(workflow_path, "w") as f:
        f.write(workflow_content)

    console.print(f"[bold green]✅ Successfully created {workflow_path}[/bold green]")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("1. Push this file to your repository.")
    console.print(
        "2. Ensure [bold]OPENAI_API_KEY[/bold] is added to your GitHub Secrets."
    )
    console.print("3. PR Guard will now automatically review your PRs!")


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
    log_content = await _get_git_log(limit=limit)
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
        "[green]Enabled[/green]"
        if os.getenv("LANGSMITH_TRACING") == "true"
        else "Disabled",
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


def run_version():
    import importlib.metadata

    try:
        ver = importlib.metadata.version("pr-guard")
        console.print(f"PR Guard version: [bold cyan]{ver}[/bold cyan]")
    except importlib.metadata.PackageNotFoundError:
        console.print("PR Guard version: [bold cyan]0.2.1[/bold cyan] (local)")


async def chat_loop():
    """
    Premium interactive chat loop with the PR Guard agent and real-time streaming.
    """
    setup_env()
    thread_id = str(uuid.uuid4())
    agent = await chat_agent()

    welcome_text = Text.assemble(
        ("🛡️ ", "bold blue"),
        ("PR Guard Interactive Assistant", "bold white"),
        ("\nYour futuristic codebase companion", "dim italic"),
    )

    console.print("\n")
    console.print(Panel(welcome_text, border_style="blue", padding=(1, 2)))
    console.print(
        "[dim]How can I help you today? (Type [bold cyan]'help'[/bold cyan] for commands)[/dim]\n"
    )

    while True:
        try:
            user_input = console.input("[bold blue]❯ [/bold blue]")

            if user_input.lower() in ["exit", "quit"]:
                console.print("\n[bold blue]Bye! Keep on coding![/bold blue] 🚀")
                break

            if user_input.lower() == "review":
                await run_review()
                continue

            if user_input.lower() == "init":
                await run_init()
                continue

            if user_input.lower().startswith("tree"):
                parts = user_input.split(maxsplit=1)
                path = parts[1] if len(parts) > 1 else "."
                await run_tree(path)
                continue

            if user_input.lower().startswith("changed"):
                # Simple parsing for chat
                parts = user_input.split()
                base = "master"
                head = "HEAD"
                if len(parts) > 1:
                    base = parts[1]
                if len(parts) > 2:
                    head = parts[2]
                await run_changed(base, head)
                continue

            if user_input.lower().startswith("diff"):
                parts = user_input.split()
                base = "master"
                head = "HEAD"
                if len(parts) > 1:
                    base = parts[1]
                if len(parts) > 2:
                    head = parts[2]
                await run_diff(base, head)
                continue

            if user_input.lower().startswith("log"):
                parts = user_input.split()
                limit = 10
                if len(parts) > 1 and parts[1].isdigit():
                    limit = int(parts[1])
                await run_log(limit)
                continue

            if user_input.lower() == "status":
                run_status()
                continue

            if user_input.lower().startswith("cat"):
                parts = user_input.split(maxsplit=1)
                if len(parts) > 1:
                    await run_cat(parts[1])
                else:
                    console.print("[red]Please specify a file path.[/red]")
                continue

            if user_input.lower() == "version":
                run_version()
                continue

            if user_input.lower() == "help":
                show_cli_help()
                continue

            if not user_input.strip():
                continue

            full_response = ""
            with Live(
                "[bold cyan]Thinking...",
                console=console,
                refresh_per_second=5,
                vertical_overflow="visible",
            ) as live:
                async for chunk in agent.astream(
                    {"messages": [{"role": "user", "content": user_input}]},
                    stream_mode=["updates", "messages"],
                    config={"configurable": {"thread_id": thread_id}},
                ):
                    # Unpack the stream_mode tuple: (stream_mode_name, data)
                    stream_mode_name, data = chunk

                    if stream_mode_name == "updates":
                        # Process state updates (tool calls, transitions)
                        for step_name, step_data in data.items():
                            if step_data is None:
                                continue
                            messages = step_data.get("messages", [])
                            if messages:
                                latest_msg = messages[-1]
                                # Check for tool calls to update the status spinner
                                if (
                                    hasattr(latest_msg, "tool_calls")
                                    and latest_msg.tool_calls
                                ):
                                    for tool_call in latest_msg.tool_calls:
                                        live.update(
                                            f"[bold dim]🔧 Executing tool:[/bold dim] [cyan]{tool_call.get('name')}[/cyan]"
                                        )

                    elif stream_mode_name == "messages":
                        # msg is an AIMessageChunk, ToolMessage, etc.
                        msg, metadata = data

                        # Filter: Only process content if it's coming from the AI/LLM
                        # This automatically skips ToolMessages (tool output)
                        if isinstance(msg, AIMessageChunk) and msg.content:
                            token = token_processor(msg.content)
                            if token:
                                full_response += token
                                live.update(Markdown(full_response))

            console.print("\n")

        except KeyboardInterrupt:
            console.print("\n[bold blue]Shutting down...[/bold blue]")
            break
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {e}")


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
            # In a real scenario, we might try to install it based on OS,
            # but for now, we'll guide the user.
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

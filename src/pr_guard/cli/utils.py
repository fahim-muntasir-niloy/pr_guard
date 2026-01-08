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

console = Console()


def setup_env():
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


async def run_review(plain: bool = False):
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

    # --- BEUTIFUL RICH REPORT ---
    review_dict = final_structured_res.model_dump()

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

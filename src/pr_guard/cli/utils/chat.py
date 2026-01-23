import uuid
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.markdown import Markdown
from langchain.messages import AIMessageChunk
from pr_guard.agent import chat_agent
from pr_guard.cli.utils.terminal import console, show_cli_help, run_version
from pr_guard.cli.utils.env import setup_env
import json


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
                from pr_guard.cli.utils.review import run_review

                await run_review()
                continue

            if user_input.lower() == "init":
                from pr_guard.cli.utils.init_setup import run_init

                await run_init()
                continue

            if user_input.lower().startswith("tree"):
                from pr_guard.cli.utils.repo import run_tree

                parts = user_input.split(maxsplit=1)
                path = parts[1] if len(parts) > 1 else "."
                await run_tree(path)
                continue

            if user_input.lower().startswith("changed"):
                from pr_guard.cli.utils.repo import run_changed

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
                from pr_guard.cli.utils.repo import run_diff

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
                from pr_guard.cli.utils.repo import run_log

                parts = user_input.split()
                limit = 10
                if len(parts) > 1 and parts[1].isdigit():
                    limit = int(parts[1])
                await run_log(limit)
                continue

            if user_input.lower() == "status":
                from pr_guard.cli.utils.repo import run_status

                run_status()
                continue

            if user_input.lower().startswith("cat"):
                from pr_guard.cli.utils.repo import run_cat

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
                                        args_json = json.dumps(
                                            tool_call.get("args", {})
                                        )
                                        console.print(
                                            f"🔧 [bold dim]Executing tool:[/bold dim] [cyan]{tool_call.get('name')}[/cyan]"
                                        )
                                        console.print(
                                            f"[dim]   Input: {args_json}[/dim]"
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
